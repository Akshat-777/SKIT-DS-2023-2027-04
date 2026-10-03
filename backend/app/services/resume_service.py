import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings
from app.schemas.resume import (
    ParsedResume, ScoreResult, MarketFit, Roadmap, Critique,
    EducationItem, ExperienceItem, SkillItem, ScoreBreakdown, SkillGap, MissingSkillItem,
    RoadmapPhase, ResourceItem, AgentCritique, MergedCritique, RewriteItem
)

# In-memory status & result store for uploaded resumes
# Key: resume_id, Value: dict containing status, metadata, user_id, and cached analysis
RESUME_STORE: Dict[str, Dict[str, Any]] = {}

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".doc"
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}

async def process_resume_background(resume_id: str, user_id: str):
    """
    Simulates asynchronous pipeline processing (OCR/Parsing -> Embedding -> ML Scoring).
    Updates status step-by-step: uploaded -> extracting -> parsing -> scoring -> ready.
    """
    try:
        # Step 1: Extracting text / OCR
        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "extracting"
            RESUME_STORE[resume_id]["updated_at"] = datetime.utcnow().isoformat()
        await asyncio.sleep(0.5)

        # Step 2: NLP Parsing & NER
        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "parsing"
            RESUME_STORE[resume_id]["updated_at"] = datetime.utcnow().isoformat()
        await asyncio.sleep(0.5)

        # Step 3: ML Scoring & Market Intelligence
        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "scoring"
            RESUME_STORE[resume_id]["updated_at"] = datetime.utcnow().isoformat()
        await asyncio.sleep(0.5)

        # Step 4: Final Ready State
        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "ready"
            RESUME_STORE[resume_id]["updated_at"] = datetime.utcnow().isoformat()
    except Exception as e:
        if resume_id in RESUME_STORE:
            RESUME_STORE[resume_id]["status"] = "failed"
            RESUME_STORE[resume_id]["error"] = str(e)
            RESUME_STORE[resume_id]["updated_at"] = datetime.utcnow().isoformat()

class ResumeService:
    @staticmethod
    async def save_and_initiate_upload(file: UploadFile, user_id: str) -> Dict[str, Any]:
        """
        Validates, saves the file in per-user isolated storage, initiates background task, and returns initial status.
        """
        filename = file.filename or "uploaded_resume.pdf"
        ext = os.path.splitext(filename)[1].lower()

        # 1. Extension and Content-Type Validation
        if ext not in ALLOWED_EXTENSIONS and file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "INVALID_FILE_TYPE", "message": f"Unsupported file extension '{ext}'. Only PDF and DOCX files are allowed."}
            )

        # 2. File Size Validation
        content = await file.read()
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "FILE_TOO_LARGE", "message": f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB."}
            )

        # 3. Secure Per-User File Storage (NFR-004 Privacy Isolation)
        user_dir = os.path.join(settings.STORAGE_PATH, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)

        resume_id = f"res_{uuid.uuid4().hex[:10]}"
        safe_filename = f"{resume_id}{ext}"
        saved_file_path = os.path.join(user_dir, safe_filename)

        with open(saved_file_path, "wb") as f:
            f.write(content)

        # 4. Store state record
        now_str = datetime.utcnow().isoformat()
        record = {
            "resume_id": resume_id,
            "user_id": user_id,
            "filename": filename,
            "saved_file_path": saved_file_path,
            "status": "uploaded",
            "created_at": now_str,
            "updated_at": now_str
        }
        RESUME_STORE[resume_id] = record

        return record

    @staticmethod
    def get_status(resume_id: str, user_id: str) -> Dict[str, Any]:
        record = RESUME_STORE.get(resume_id)
        if not record or record.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "RESUME_NOT_FOUND", "message": f"Resume record with ID '{resume_id}' was not found."}
            )
        return {
            "resume_id": record["resume_id"],
            "status": record["status"],
            "updated_at": record["updated_at"]
        }

    @staticmethod
    def get_parsed_and_score(resume_id: str, user_id: str) -> Dict[str, Any]:
        record = RESUME_STORE.get(resume_id)
        if not record or record.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "RESUME_NOT_FOUND", "message": f"Resume with ID '{resume_id}' was not found."}
            )

        parsed_resume = ParsedResume(
            resume_id=resume_id,
            name="Akshat Agarwal",
            email="akshat@example.com",
            education=[
                EducationItem(degree="B.Tech Computer Science & Data Science", institution="SKIT Jaipur", year=2027)
            ],
            experience=[
                ExperienceItem(
                    title="Backend Developer Intern",
                    company="TechCorp Solutions",
                    start="May 2025",
                    end="August 2025",
                    bullets=[
                        "Developed 12+ RESTful APIs using Python FastAPI and PostgreSQL",
                        "Optimized database query response time by 35%"
                    ]
                )
            ],
            skills=[
                SkillItem(name="Python", type="explicit", confidence=0.98, evidence="Used in API development"),
                SkillItem(name="FastAPI", type="explicit", confidence=0.95, evidence="Built RESTful APIs"),
                SkillItem(name="PostgreSQL", type="explicit", confidence=0.90, evidence="Optimized database queries"),
                SkillItem(name="Docker", type="implicit", confidence=0.82, evidence="Inferred from microservices setup")
            ],
            sections={"education": "B.Tech CSE DS", "experience": "Backend Developer Intern"},
            raw_text="Akshat Agarwal... B.Tech CSE (DS)... SKIT Jaipur... Python, FastAPI, PostgreSQL..."
        )

        score_result = ScoreResult(
            resume_id=resume_id,
            target_role="Full Stack Data Engineer / Backend Developer",
            ats_score=86,
            breakdown=ScoreBreakdown(
                keyword_match=88.0,
                semantic_similarity=85.0,
                section_completeness=90.0,
                formatting=88.0,
                experience_relevance=84.0,
                quantified_impact=82.0
            ),
            skill_gap=SkillGap(
                matched=["Python", "FastAPI", "PostgreSQL", "REST APIs"],
                missing=[
                    MissingSkillItem(skill="Kubernetes", demand_pct=78.5),
                    MissingSkillItem(skill="Apache Kafka", demand_pct=65.0)
                ],
                weak=["SQL Indexing Optimization"],
                trending=["ChromaDB", "LangChain", "LightGBM"]
            )
        )

        return {
            "parsed_resume": parsed_resume.model_dump(),
            "score_result": score_result.model_dump()
        }

    @staticmethod
    def get_market_fit(resume_id: str, user_id: str) -> MarketFit:
        record = RESUME_STORE.get(resume_id)
        if not record or record.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "RESUME_NOT_FOUND", "message": f"Resume with ID '{resume_id}' was not found."}
            )

        return MarketFit(
            resume_id=resume_id,
            fit_score=88,
            salary_min=10.5,
            salary_max=16.5,
            currency="INR",
            unit="LPA",
            top_factors=[
                "High demand for Python & FastAPI developers in Indian tech startups",
                "Strong foundational coursework in CSE Data Science at SKIT Jaipur",
                "Demonstrated API integration experience"
            ]
        )

    @staticmethod
    def get_roadmap(resume_id: str, user_id: str) -> Roadmap:
        record = RESUME_STORE.get(resume_id)
        if not record or record.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "RESUME_NOT_FOUND", "message": f"Resume with ID '{resume_id}' was not found."}
            )

        return Roadmap(
            resume_id=resume_id,
            target_role="Backend & AI Data Systems Engineer",
            phases=[
                RoadmapPhase(
                    phase="Phase 1: Microservice Containerization",
                    weeks=2,
                    skills=["Docker", "Docker Compose"],
                    resources=[
                        ResourceItem(title="Docker Official Docs", url="https://docs.docker.com", type="documentation")
                    ],
                    project="Containerize FastAPI and Node.js Auth Service with docker-compose",
                    linked_gap_skill="Docker"
                ),
                RoadmapPhase(
                    phase="Phase 2: Event Streaming & Message Queues",
                    weeks=3,
                    skills=["Apache Kafka", "Redis"],
                    resources=[
                        ResourceItem(title="Kafka Quickstart Guide", url="https://kafka.apache.org/quickstart", type="documentation")
                    ],
                    project="Implement async resume processing pipeline using Redis queue",
                    linked_gap_skill="Apache Kafka"
                )
            ]
        )

    @staticmethod
    def get_critique(resume_id: str, user_id: str) -> Critique:
        record = RESUME_STORE.get(resume_id)
        if not record or record.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "RESUME_NOT_FOUND", "message": f"Resume with ID '{resume_id}' was not found."}
            )

        return Critique(
            resume_id=resume_id,
            agents=[
                AgentCritique(
                    persona="Recruiter",
                    score=85,
                    verdict="Strong technical background, but experience descriptions could emphasize business metrics more clearly.",
                    strengths=["Clear skills section", "Relevant degree in CSE Data Science"],
                    concerns=["Bullet points focus on tasks rather than quantified outcomes"],
                    rewrites=[
                        RewriteItem(
                            before="Developed RESTful APIs using Python FastAPI",
                            after="Designed and executed 15+ production REST APIs using FastAPI, serving 50k+ active requests daily with 99.9% uptime"
                        )
                    ]
                ),
                AgentCritique(
                    persona="Hiring Manager",
                    score=88,
                    verdict="Good backend exposure. Ready for junior-to-mid engineering roles after containerization practice.",
                    strengths=["Solid knowledge of PostgreSQL and FastAPI architecture"],
                    concerns=["Needs more exposure to cloud deployment (AWS/Docker)"],
                    rewrites=[
                        RewriteItem(
                            before="Optimized database query response time by 35%",
                            after="Refactored PostgreSQL indexing strategies, reducing median API latency by 35% across 100k records"
                        )
                    ]
                )
            ],
            merged=MergedCritique(
                verdict="Highly promising engineering candidate with actionable improvements for quantified impact.",
                consensus_score=86,
                agreements=["Strong FastAPI foundation", "Solid academic background at SKIT"],
                disagreements=["Recruiter prioritized bullet metrics while Manager prioritized cloud infrastructure skills"]
            )
        )
