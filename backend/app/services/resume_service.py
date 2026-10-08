"""
CareerLens Resume Service
Orchestrates the full pipeline:
  upload → text extraction → NLP parsing → ATS scoring → DB persistence
All results are derived from the user's actual resume file, not hardcoded.
"""

import os
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.repositories import (
    ResumeRepository, ParsedEntitiesRepository, AnalysisRepository,
    create_audit_log, UserRepository
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

logger = logging.getLogger("careerlens.resume_service")

# In-memory status store (used when DB is unavailable)
RESUME_STORE: Dict[str, Dict[str, Any]] = {}

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc",
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


async def process_resume_background(resume_id: str, user_id: str, file_path: str, db: Optional[Session] = None):
    """
    Real asynchronous NLP pipeline.
    Opens its own DB session (the request session is closed by the time background tasks run).
    """
    from app.db.database import SessionLocal
    bg_db = SessionLocal()
    try:
        # ── Step 1: Text extraction ──────────────────────────────────────────
        logger.info(f"[{resume_id}] Starting text extraction from {file_path}")
        ResumeRepository.update_status(bg_db, resume_id, "extracting")
        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "extracting"
            RESUME_STORE[resume_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Run the CPU-bound NLP parser in a thread pool so we don't block the event loop
        loop = asyncio.get_event_loop()
        parsed = await loop.run_in_executor(None, parse_resume, file_path)
        logger.info(f"[{resume_id}] Text extracted: {len(parsed['raw_text'])} chars")

        # ── Step 2: NLP parsing & NER ────────────────────────────────────────
        ResumeRepository.update_status(bg_db, resume_id, "parsing")
        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "parsing"
            RESUME_STORE[resume_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

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

        # ── Step 3: ML Scoring ───────────────────────────────────────────────
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

        AnalysisRepository.create(
            bg_db,
            resume_id=resume_id,
            target_role=target_role,
            ats_score=ats_result["ats_score"],
            breakdown=ats_result["breakdown"],
            skill_gap=skill_gap,
        )

        # ── Step 4: Mark ready ───────────────────────────────────────────────
        ResumeRepository.update_status(bg_db, resume_id, "ready")
        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "ready"
            RESUME_STORE[resume_id]["updated_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"[{resume_id}] Pipeline complete. ATS={ats_result['ats_score']}, role={target_role!r}")

    except Exception as e:
        logger.exception(f"[{resume_id}] Pipeline failed: {e}")
        try:
            ResumeRepository.update_status(bg_db, resume_id, "failed")
        except Exception:
            pass
        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "failed"
            RESUME_STORE[resume_id]["error"] = str(e)
            RESUME_STORE[resume_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
    finally:
        bg_db.close()


class ResumeService:

    @staticmethod
    async def save_and_initiate_upload(
        file: UploadFile,
        user_id: str,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Validates file, saves to per-user isolated storage, creates DB record,
        and returns the initial status dict (file_path included for background task).
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

        # 4. Ensure user row exists in DB (JWT sub → DB user.id)
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
        return {"resume_id": record["resume_id"], "status": record["status"], "updated_at": record["updated_at"]}

    # ── Analysis endpoints ────────────────────────────────────────────────────

    @staticmethod
    def _load_parsed_entities(resume_id: str, user_id: str, db: Optional[Session]) -> Dict[str, Any]:
        """Load parsed entities from DB or raise a clear error."""
        ResumeService.get_status(resume_id, user_id, db)  # ownership check

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

        # Fall back to re-parsing the file from RESUME_STORE
        record = RESUME_STORE.get(resume_id)
        if record and record.get("saved_file_path") and os.path.exists(record["saved_file_path"]):
            return parse_resume(record["saved_file_path"])

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PARSE_NOT_READY", "message": "Resume parsing is still in progress or failed. Please wait and retry."},
        )

    @staticmethod
    def get_parsed_and_score(resume_id: str, user_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
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
