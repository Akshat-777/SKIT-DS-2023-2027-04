"""
CareerLens Resume Service
Orchestrates the full pipeline:
  upload → text extraction / OCR → cleanup → NER parsing → skill extraction → ATS scoring → DB persistence
Integrates Aishani's parsing pipeline (FR-001, FR-002) and Aryan's scoring service (FR-003).
"""

import os
import uuid
import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.repositories import (
    ResumeRepository, ParsedEntitiesRepository, AnalysisRepository,
    RoleTaxonomyRepository, create_audit_log, UserRepository
)
from app.schemas.resume import (
    ParsedResume, ScoreResult, MarketFit, Roadmap, Critique,
    EducationItem, ExperienceItem, SkillItem, ScoreBreakdown,
    SkillGap, MissingSkillItem, RoadmapPhase, ResourceItem,
    AgentCritique, MergedCritique, RewriteItem
)
from app.services.nlp_parser import parse_resume
from app.services.scorer import (
    infer_target_role,
    compute_ats_score,
    compute_skill_gap,
    compute_market_fit,
    compute_roadmap,
    compute_critique,
)
from app.services.cache_service import cache_service
from app.services.scoring_client import scoring_client, ScoringClientError

logger = logging.getLogger("careerlens.resume_service")

# In-memory status store (used when DB is unavailable)
RESUME_STORE: Dict[str, Dict[str, Any]] = {}

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


# ── Pipeline Orchestration (FR-001, FR-002) ────────────────────────────────────

async def process_resume_background(
    resume_id: str,
    user_id: str,
    file_path: str,
    original_filename: Optional[str] = None,
    db: Optional[Session] = None
):
    """
    FR-001 & FR-002: Orchestrates Aishani's NLP services in order:
      1. extract/OCR: Extract text from PDF/DOCX with OCR fallback for scans
      2. cleanup: Fix OCR errors, normalize unicode, standardize bullets & dates
      3. NER parse: Extract name, email, education, experience, skills
      4. skill extraction: Explicit and implicit skill detection
      5. section and experience-quality parse: Detect sections, bullets, dates
      6. skill depth: Assign confidence & evidence
      7. Persist ParsedResume in PostgreSQL and update status (extracting -> parsing -> scoring -> ready)
    On failure at any step, stores the failed step and a user-friendly error message.
    """
    from app.db.database import SessionLocal
    bg_db = SessionLocal()
    current_step = "extract/OCR"
    loop = asyncio.get_event_loop()

    try:
        filename = original_filename or os.path.basename(file_path)
        logger.info(f"[{resume_id}] Starting ingestion pipeline for {filename}")

        # ── Step 1: extract/OCR ──────────────────────────────────────────────
        current_step = "extract/OCR"
        ResumeRepository.update_status(bg_db, resume_id, "extracting")
        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "extracting"
            RESUME_STORE[resume_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

        ocr_used = False
        raw_text = ""

        try:
            from careerlens.ingest.extractor import process_resume as ingest_process
            extraction_res = await loop.run_in_executor(None, ingest_process, file_path, filename)
            raw_text = extraction_res.get("text", "")
            ocr_used = (extraction_res.get("method") == "ocr")
            if extraction_res.get("warnings"):
                logger.warning(f"[{resume_id}] Extraction warnings: {extraction_res['warnings']}")
        except Exception as ingest_err:
            logger.warning(f"[{resume_id}] Ingest extractor error ({ingest_err}), falling back to direct parse.")
            raw_text = ""

        # Fallback if extractor yielded empty text
        if not raw_text.strip():
            fallback_parsed = await loop.run_in_executor(None, parse_resume, file_path)
            raw_text = fallback_parsed.get("raw_text", "")

        if not raw_text.strip():
            raise ValueError("No extractable text found in resume. Ensure the PDF/DOCX is not blank or corrupt.")

        ResumeRepository.update_status(bg_db, resume_id, "extracting", ocr_used=ocr_used)
        logger.info(f"[{resume_id}] Extracted {len(raw_text)} chars (ocr_used={ocr_used})")

        # ── Step 2: cleanup ──────────────────────────────────────────────────
        current_step = "cleanup"
        ResumeRepository.update_status(bg_db, resume_id, "parsing")
        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "parsing"
            RESUME_STORE[resume_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

        cleaned_text = raw_text
        try:
            from careerlens.nlp.cleaner import (
                clean_ocr_errors, normalize_unicode, fix_hyphenation,
                standardize_bullets, standardize_dates
            )
            cleaned_text, _ = normalize_unicode(cleaned_text)
            if ocr_used:
                cleaned_text, _ = clean_ocr_errors(cleaned_text)
            cleaned_text, _ = fix_hyphenation(cleaned_text)
            cleaned_text, _ = standardize_bullets(cleaned_text)
            cleaned_text, _ = standardize_dates(cleaned_text)
        except Exception as clean_err:
            logger.warning(f"[{resume_id}] Non-critical text cleaner error: {clean_err}")

        # ── Step 3, 4, 5, 6: NER, Skills, Sections, Depth ────────────────────
        current_step = "NER parse"
        parsed = await loop.run_in_executor(None, parse_resume, file_path)
        # Ensure cleaned text is retained
        parsed["raw_text"] = cleaned_text

        # ── Step 7: Persist ParsedResume ─────────────────────────────────────
        current_step = "persist ParsedResume"
        ParsedEntitiesRepository.create_or_update(
            bg_db,
            resume_id=resume_id,
            name=parsed["name"],
            email=parsed["email"],
            education=parsed["education"],
            experience=parsed["experience"],
            skills=parsed["skills"],
            sections=parsed["sections"],
            raw_text=parsed["raw_text"],
        )

        # ── Step 8: Baseline Scoring & Status Updates ────────────────────────
        current_step = "scoring"
        ResumeRepository.update_status(bg_db, resume_id, "scoring")
        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "scoring"
            RESUME_STORE[resume_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

        target_role = infer_target_role(parsed["skills"], parsed["raw_text"])
        ats_result = compute_ats_score(
            parsed["skills"], parsed["education"], parsed["experience"],
            parsed["sections"], parsed["raw_text"], target_role
        )
        skill_gap = compute_skill_gap(parsed["skills"], parsed["raw_text"], target_role)

        # Store baseline initial analysis
        AnalysisRepository.create(
            bg_db,
            resume_id=resume_id,
            target_role=target_role,
            ats_score=ats_result["ats_score"],
            breakdown=ats_result["breakdown"],
            skill_gap=skill_gap,
        )

        # ── Step 9: Mark Ready ───────────────────────────────────────────────
        current_step = "ready"
        ResumeRepository.update_status(bg_db, resume_id, "ready", ocr_used=ocr_used)
        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "ready"
            RESUME_STORE[resume_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(
            f"[{resume_id}] Pipeline completed successfully: role='{target_role}', ATS={ats_result['ats_score']}"
        )

    except Exception as e:
        logger.exception(f"[{resume_id}] Pipeline failed at step '{current_step}': {e}")
        user_friendly_msg = f"Failed at {current_step}: {str(e)}"
        try:
            ResumeRepository.update_status(
                bg_db,
                resume_id=resume_id,
                status="failed",
                failed_step=current_step,
                error_message=user_friendly_msg
            )
        except Exception as db_err:
            logger.error(f"[{resume_id}] Could not record failure status in DB: {db_err}")

        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "failed"
            RESUME_STORE[resume_id]["failed_step"] = current_step
            RESUME_STORE[resume_id]["error_message"] = user_friendly_msg
            RESUME_STORE[resume_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
    finally:
        bg_db.close()


# ── Resume Service Class ───────────────────────────────────────────────────────

class ResumeService:

    @staticmethod
    async def save_and_initiate_upload(
        file: UploadFile,
        user_id: str,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Validates file, saves to per-user isolated storage, creates DB record,
        invalidates any old cache for this resume, and prepares background task.
        """
        filename = file.filename or "uploaded_resume.pdf"
        ext = os.path.splitext(filename)[1].lower()

        # 1. Extension / MIME validation
        if ext not in ALLOWED_EXTENSIONS and file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "INVALID_FILE_TYPE",
                    "message": f"Unsupported file extension '{ext}'. Only PDF and DOCX files are accepted.",
                },
            )

        # 2. File-size validation
        content = await file.read()
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "FILE_TOO_LARGE",
                    "message": f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
                },
            )

        # 3. Per-user isolated storage (NFR-004 privacy)
        user_dir = os.path.join(settings.STORAGE_PATH, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        resume_id = f"res_{uuid.uuid4().hex[:10]}"
        safe_filename = f"{resume_id}{ext}"
        saved_file_path = os.path.join(user_dir, safe_filename)
        with open(saved_file_path, "wb") as f:
            f.write(content)

        # 4. Invalidate any existing cache for this resume ID
        cache_service.invalidate_resume(resume_id)

        # 5. Ensure user row exists in DB
        if db:
            existing_user = UserRepository.get_by_id(db, user_id)
            if not existing_user:
                UserRepository.create(
                    db,
                    name=f"User {user_id}",
                    email=f"{user_id}_{uuid.uuid4().hex[:6]}@internal.careerlens.ai",
                    password_hash="sso_managed",
                    user_id=user_id,
                )

            db_resume = ResumeRepository.create(
                db,
                user_id=user_id,
                file_name=filename,
                file_type=ext.replace(".", ""),
                file_path=saved_file_path,
            )
            resume_id = db_resume.id

        now_str = datetime.now(timezone.utc).isoformat()
        record = {
            "resume_id": resume_id,
            "user_id": user_id,
            "filename": filename,
            "saved_file_path": saved_file_path,
            "status": "uploaded",
            "created_at": now_str,
            "updated_at": now_str,
        }
        RESUME_STORE[resume_id] = record
        return record

    @staticmethod
    def get_status(resume_id: str, user_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """Returns processing status along with failed_step and error_message if failed."""
        if db:
            db_resume = ResumeRepository.get_by_id(db, resume_id)
            if not db_resume or db_resume.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"code": "RESUME_NOT_FOUND", "message": f"Resume '{resume_id}' not found."},
                )
            if db_resume.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "FORBIDDEN", "message": "Access denied. You do not own this resume."},
                )
            create_audit_log(db, user_id, "RESUME_VIEW_STATUS", "RESUME", resume_id)
            return {
                "resume_id": db_resume.id,
                "status": db_resume.status,
                "updated_at": db_resume.updated_at.isoformat(),
                "failed_step": db_resume.failed_step,
                "error_message": db_resume.error_message,
            }

        record = RESUME_STORE.get(resume_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "RESUME_NOT_FOUND", "message": f"Resume '{resume_id}' not found."},
            )
        if record.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Access denied."},
            )
        return {
            "resume_id": record["resume_id"],
            "status": record["status"],
            "updated_at": record["updated_at"],
            "failed_step": record.get("failed_step"),
            "error_message": record.get("error_message"),
        }

    # ── Analysis Endpoints (Aryan's Scoring Service Integration) ───────────────

    @staticmethod
    async def analyze_resume(
        resume_id: str,
        target_role: str,
        user_id: str,
        db: Session,
        request_id: Optional[str] = None
    ) -> Tuple[ScoreResult, bool, float]:
        """
        FR-003: Loads ParsedResume from PostgreSQL, validates role taxonomy,
        checks Redis/InMemory cache (TTL 1h), invokes Aryan's scoring service via scoring_client,
        stores ScoreResult in analyses table, and returns:
          (score_result: ScoreResult, is_cache_hit: bool, elapsed_ms: float)
        """
        start_time = time.perf_counter()

        # 1. Fetch resume and verify ownership
        db_resume = ResumeRepository.get_by_id(db, resume_id)
        if not db_resume or db_resume.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "RESUME_NOT_FOUND", "message": f"Resume '{resume_id}' not found."}
            )
        if db_resume.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Access denied. You do not own this resume."}
            )

        # 2. Verify resume status (must be 'ready' or 'parsed')
        if db_resume.status in ["uploaded", "extracting", "parsing"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "RESUME_NOT_READY",
                    "message": f"Resume parsing is still in progress (current status: '{db_resume.status}'). Please wait and retry."
                }
            )
        elif db_resume.status == "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "RESUME_PARSE_FAILED",
                    "message": f"Resume processing previously failed at step '{db_resume.failed_step or 'unknown'}': {db_resume.error_message or 'Corrupt file or unreadable text'}"
                }
            )

        # 3. Validate target_role against Role Taxonomy
        if not RoleTaxonomyRepository.is_valid_role(db, target_role):
            known = RoleTaxonomyRepository.KNOWN_ROLES
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "INVALID_TARGET_ROLE",
                    "message": f"Target role '{target_role}' does not exist in the role taxonomy. Available roles include: {', '.join(known[:6])}."
                }
            )

        # 4. Load ParsedResume from PostgreSQL
        pe = ParsedEntitiesRepository.get_by_resume_id(db, resume_id)
        if not pe or not pe.raw_text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "PARSE_NOT_READY",
                    "message": "Parsed resume content is missing. Please re-upload your resume."
                }
            )

        parsed_resume = ParsedResume(
            resume_id=resume_id,
            name=pe.name or "Candidate",
            email=pe.email or "",
            education=[EducationItem(**e) for e in (pe.education or [])[:5]],
            experience=[ExperienceItem(**e) for e in (pe.experience or [])[:6]],
            skills=[SkillItem(**s) for s in (pe.skills or [])[:30]],
            sections=pe.sections or {},
            raw_text=pe.raw_text or "",
        )

        # 5. Check Cache (hash of resume text + target_role + market data version)
        cached_result, is_hit = cache_service.get_cached_score(
            resume_text=pe.raw_text,
            target_role=target_role
        )
        if is_hit and cached_result:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"[{request_id or 'internal'}] Cache HIT for resume={resume_id}, role='{target_role}' "
                f"({elapsed_ms:.2f}ms)"
            )
            return cached_result, True, elapsed_ms

        logger.info(
            f"[{request_id or 'internal'}] Cache MISS for resume={resume_id}, role='{target_role}'. Invoking scoring service."
        )

        # 6. Call Aryan's Scoring Service via scoring_client
        try:
            score_result = await scoring_client.score_resume(
                parsed_resume=parsed_resume,
                target_role=target_role,
                request_id=request_id
            )
        except ScoringClientError as sce:
            logger.error(f"[{request_id or 'internal'}] Scoring client error: {sce.code} - {sce.message}")
            raise HTTPException(
                status_code=sce.status_code,
                detail={"code": sce.code, "message": sce.message}
            )

        # 7. Persist ScoreResult in analyses table
        AnalysisRepository.create(
            db=db,
            resume_id=resume_id,
            target_role=target_role,
            ats_score=score_result.ats_score,
            breakdown=score_result.breakdown.model_dump(),
            skill_gap=score_result.skill_gap.model_dump(),
        )

        # 8. Store in Cache (1 hour TTL)
        cache_service.set_cached_score(
            resume_text=pe.raw_text,
            target_role=target_role,
            result=score_result,
            resume_id=resume_id
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"[{request_id or 'internal'}] Analysis complete for resume={resume_id}, role='{target_role}' "
            f"in {elapsed_ms:.2f}ms (score={score_result.ats_score})"
        )
        return score_result, False, elapsed_ms

    @staticmethod
    def get_latest_analysis(resume_id: str, user_id: str, db: Session) -> Dict[str, Any]:
        """
        Returns the latest stored analysis result for the given resume.
        Compatible with both ScoreResult contract and legacy parsed_resume/score_result response.
        """
        db_resume = ResumeRepository.get_by_id(db, resume_id)
        if not db_resume or db_resume.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "RESUME_NOT_FOUND", "message": f"Resume '{resume_id}' not found."}
            )
        if db_resume.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Access denied. You do not own this resume."}
            )

        analysis = AnalysisRepository.get_latest_by_resume_id(db, resume_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ANALYSIS_NOT_FOUND",
                    "message": f"No analysis found for resume '{resume_id}'. Trigger POST /resumes/{resume_id}/analyze first."
                }
            )

        pe = ParsedEntitiesRepository.get_by_resume_id(db, resume_id)
        parsed_dict = {
            "resume_id": resume_id,
            "name": pe.name if pe else "Candidate",
            "email": pe.email if pe else "",
            "education": pe.education if pe else [],
            "experience": pe.experience if pe else [],
            "skills": pe.skills if pe else [],
            "sections": pe.sections if pe else {},
            "raw_text": (pe.raw_text or "")[:2000] if pe else "",
        }

        score_result_dict = {
            "resume_id": analysis.resume_id,
            "target_role": analysis.target_role,
            "ats_score": int(round(analysis.ats_score)),
            "breakdown": analysis.breakdown,
            "skill_gap": analysis.skill_gap,
        }

        return {
            **score_result_dict,
            "score_result": score_result_dict,
            "parsed_resume": parsed_dict,
        }

    # ── Legacy Endpoints & Other Modules ──────────────────────────────────────

    @staticmethod
    def _load_parsed_entities(resume_id: str, user_id: str, db: Optional[Session]) -> Dict[str, Any]:
        """Load parsed entities from DB or raise a clear error."""
        ResumeService.get_status(resume_id, user_id, db)

        if db:
            pe = ParsedEntitiesRepository.get_by_resume_id(db, resume_id)
            if pe:
                return {
                    "name": pe.name or "Candidate",
                    "email": pe.email or "",
                    "education": pe.education or [],
                    "experience": pe.experience or [],
                    "skills": pe.skills or [],
                    "sections": pe.sections or {},
                    "raw_text": pe.raw_text or "",
                }

        record = RESUME_STORE.get(resume_id)
        if record and record.get("saved_file_path") and os.path.exists(record["saved_file_path"]):
            return parse_resume(record["saved_file_path"])

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PARSE_NOT_READY", "message": "Resume parsing is still in progress or failed. Please wait and retry."},
        )

    @staticmethod
    def get_parsed_and_score(resume_id: str, user_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """Fetches latest stored analysis or computes baseline."""
        if db:
            try:
                return ResumeService.get_latest_analysis(resume_id, user_id, db)
            except HTTPException:
                pass

        parsed = ResumeService._load_parsed_entities(resume_id, user_id, db)
        target_role = infer_target_role(parsed["skills"], parsed["raw_text"])

        ats_result = compute_ats_score(
            parsed["skills"], parsed["education"], parsed["experience"],
            parsed["sections"], parsed["raw_text"], target_role
        )
        skill_gap = compute_skill_gap(parsed["skills"], parsed["raw_text"], target_role)

        parsed_resume = ParsedResume(
            resume_id=resume_id,
            name=parsed["name"],
            email=parsed["email"],
            education=[EducationItem(**e) for e in parsed["education"][:4]],
            experience=[ExperienceItem(**e) for e in parsed["experience"][:5]],
            skills=[SkillItem(**s) for s in parsed["skills"][:20]],
            sections=parsed["sections"],
            raw_text=parsed["raw_text"][:2000],
        )

        score_result = ScoreResult(
            resume_id=resume_id,
            target_role=target_role,
            ats_score=ats_result["ats_score"],
            breakdown=ScoreBreakdown(**ats_result["breakdown"]),
            skill_gap=SkillGap(
                matched=skill_gap["matched"],
                missing=[MissingSkillItem(**m) for m in skill_gap["missing"]],
                weak=skill_gap["weak"],
                trending=skill_gap["trending"],
            ),
        )

        return {
            "resume_id": resume_id,
            "target_role": target_role,
            "ats_score": ats_result["ats_score"],
            "breakdown": ats_result["breakdown"],
            "skill_gap": skill_gap,
            "parsed_resume": parsed_resume.model_dump(),
            "score_result": score_result.model_dump(),
        }

    @staticmethod
    def get_market_fit(resume_id: str, user_id: str, db: Optional[Session] = None) -> MarketFit:
        parsed = ResumeService._load_parsed_entities(resume_id, user_id, db)
        target_role = infer_target_role(parsed["skills"], parsed["raw_text"])
        ats_result = compute_ats_score(
            parsed["skills"], parsed["education"], parsed["experience"],
            parsed["sections"], parsed["raw_text"], target_role
        )
        mf = compute_market_fit(
            ats_result["ats_score"], parsed["skills"],
            parsed["experience"], parsed["education"], target_role
        )
        return MarketFit(resume_id=resume_id, **mf)

    @staticmethod
    def get_roadmap(resume_id: str, user_id: str, db: Optional[Session] = None) -> Roadmap:
        parsed = ResumeService._load_parsed_entities(resume_id, user_id, db)
        target_role = infer_target_role(parsed["skills"], parsed["raw_text"])
        skill_gap = compute_skill_gap(parsed["skills"], parsed["raw_text"], target_role)
        roadmap_data = compute_roadmap(skill_gap["missing"], target_role, resume_id)

        return Roadmap(
            resume_id=resume_id,
            target_role=roadmap_data["target_role"],
            phases=[
                RoadmapPhase(
                    phase=p["phase"],
                    weeks=p["weeks"],
                    skills=p["skills"],
                    resources=[ResourceItem(**r) for r in p["resources"]],
                    project=p["project"],
                    linked_gap_skill=p["linked_gap_skill"],
                )
                for p in roadmap_data["phases"]
            ],
        )

    @staticmethod
    def get_critique(resume_id: str, user_id: str, db: Optional[Session] = None) -> Critique:
        parsed = ResumeService._load_parsed_entities(resume_id, user_id, db)
        target_role = infer_target_role(parsed["skills"], parsed["raw_text"])
        ats_result = compute_ats_score(
            parsed["skills"], parsed["education"], parsed["experience"],
            parsed["sections"], parsed["raw_text"], target_role
        )
        critique_data = compute_critique(
            parsed["skills"], parsed["experience"],
            parsed["sections"], ats_result["ats_score"], resume_id
        )

        return Critique(
            resume_id=critique_data["resume_id"],
            agents=[
                AgentCritique(
                    persona=a["persona"],
                    score=a["score"],
                    verdict=a["verdict"],
                    strengths=a["strengths"],
                    concerns=a["concerns"],
                    rewrites=[RewriteItem(**rw) for rw in a["rewrites"]],
                )
                for a in critique_data["agents"]
            ],
            merged=MergedCritique(**critique_data["merged"]),
        )
