from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, status
from typing import Dict, Any

from app.api.routes.auth_dep import get_current_user
from app.services.resume_service import ResumeService, process_resume_background
from app.schemas.resume import (
    ResumeUploadResponse, ResumeStatusResponse,
    MarketFit, Roadmap, Critique, ErrorResponse
)

router = APIRouter(prefix="/resumes", tags=["Resumes"])

@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload Resume (PDF/DOCX)",
    responses={
        202: {
            "description": "Resume accepted for asynchronous parsing and scoring.",
            "content": {
                "application/json": {
                    "example": {
                        "resume_id": "res_a1b2c3d4e5",
                        "filename": "resume.pdf",
                        "status": "uploaded",
                        "message": "Resume uploaded successfully. Processing started in background."
                    }
                }
            }
        },
        422: {"model": ErrorResponse, "description": "Validation error (invalid file extension or size exceeds limit)"},
        401: {"model": ErrorResponse, "description": "Unauthorized access token"}
    }
)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    FR-001 & NFR-005: Validates PDF/DOCX resume file type & size, stores securely in per-user isolated directory,
    creates resume record, and initiates background processing pipeline immediately.
    """
    user_id = current_user.get("sub", "default_user")
    record = await ResumeService.save_and_initiate_upload(file, user_id)

    # Launch background parsing pipeline asynchronously
    background_tasks.add_task(process_resume_background, record["resume_id"], user_id)

    return ResumeUploadResponse(
        resume_id=record["resume_id"],
        filename=record["filename"],
        status=record["status"],
        message="Resume uploaded successfully. Processing started in background."
    )

@router.get(
    "/{id}",
    response_model=ResumeStatusResponse,
    summary="Get Resume Processing Status",
    responses={
        200: {
            "description": "Current processing status.",
            "content": {
                "application/json": {
                    "example": {
                        "resume_id": "res_a1b2c3d4e5",
                        "status": "ready",
                        "updated_at": "2026-10-03T18:00:00Z"
                    }
                }
            }
        },
        404: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def get_resume_status(id: str, current_user: dict = Depends(get_current_user)):
    """Returns the background processing pipeline status for the given resume."""
    user_id = current_user.get("sub")
    return ResumeService.get_status(id, user_id)

@router.get(
    "/{id}/analysis",
    summary="Get Parsed Resume and Score Result",
    responses={
        200: {
            "description": "Shared contract for ParsedResume and ScoreResult.",
            "content": {
                "application/json": {
                    "example": {
                        "parsed_resume": {
                            "resume_id": "res_a1b2c3d4e5",
                            "name": "Akshat Agarwal",
                            "email": "akshat@example.com",
                            "education": [{"degree": "B.Tech CSE DS", "institution": "SKIT Jaipur", "year": 2027}],
                            "experience": [{"title": "Backend Developer Intern", "company": "TechCorp Solutions", "start": "May 2025", "end": "August 2025", "bullets": ["Built APIs"]}],
                            "skills": [{"name": "Python", "type": "explicit", "confidence": 0.98, "evidence": "Used in API development"}],
                            "sections": {"education": "B.Tech CSE DS"},
                            "raw_text": "Akshat Agarwal..."
                        },
                        "score_result": {
                            "resume_id": "res_a1b2c3d4e5",
                            "target_role": "Full Stack Data Engineer / Backend Developer",
                            "ats_score": 86,
                            "breakdown": {"keyword_match": 88.0, "semantic_similarity": 85.0, "section_completeness": 90.0, "formatting": 88.0, "experience_relevance": 84.0, "quantified_impact": 82.0},
                            "skill_gap": {"matched": ["Python", "FastAPI"], "missing": [{"skill": "Kubernetes", "demand_pct": 78.5}], "weak": ["SQL Indexing Optimization"], "trending": ["ChromaDB", "LightGBM"]}
                        }
                    }
                }
            }
        },
        404: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def get_resume_analysis(id: str, current_user: dict = Depends(get_current_user)):
    """Returns ParsedResume and ATS ScoreResult contract."""
    user_id = current_user.get("sub")
    return ResumeService.get_parsed_and_score(id, user_id)

@router.get(
    "/{id}/market-fit",
    response_model=MarketFit,
    summary="Get Market Fit & Salary Prediction",
    responses={
        200: {
            "description": "MarketFit response following shared JSON contract.",
            "content": {
                "application/json": {
                    "example": {
                        "resume_id": "res_a1b2c3d4e5",
                        "fit_score": 88,
                        "salary_min": 10.5,
                        "salary_max": 16.5,
                        "currency": "INR",
                        "unit": "LPA",
                        "top_factors": ["High demand for Python & FastAPI developers in Indian tech startups"]
                    }
                }
            }
        },
        404: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def get_market_fit(id: str, current_user: dict = Depends(get_current_user)):
    """FR-004: Returns market-fit score and predicted salary range in INR LPA."""
    user_id = current_user.get("sub")
    return ResumeService.get_market_fit(id, user_id)

@router.get(
    "/{id}/roadmap",
    response_model=Roadmap,
    summary="Get Personalized Learning Roadmap",
    responses={
        200: {
            "description": "Roadmap response following shared JSON contract.",
            "content": {
                "application/json": {
                    "example": {
                        "resume_id": "res_a1b2c3d4e5",
                        "target_role": "Backend & AI Data Systems Engineer",
                        "phases": [
                            {
                                "phase": "Phase 1: Microservice Containerization",
                                "weeks": 2,
                                "skills": ["Docker", "Docker Compose"],
                                "resources": [{"title": "Docker Official Docs", "url": "https://docs.docker.com", "type": "documentation"}],
                                "project": "Containerize FastAPI microservices",
                                "linked_gap_skill": "Docker"
                            }
                        ]
                    }
                }
            }
        },
        404: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def get_roadmap(id: str, current_user: dict = Depends(get_current_user)):
    """FR-005: Returns personalized learning roadmap tailored to detected skill gaps."""
    user_id = current_user.get("sub")
    return ResumeService.get_roadmap(id, user_id)

@router.get(
    "/{id}/critique",
    response_model=Critique,
    summary="Get Multi-Agent Recruiter Persona Critique",
    responses={
        200: {
            "description": "Critique response following shared JSON contract.",
            "content": {
                "application/json": {
                    "example": {
                        "resume_id": "res_a1b2c3d4e5",
                        "agents": [
                            {
                                "persona": "Recruiter",
                                "score": 85,
                                "verdict": "Strong technical background, but experience descriptions could emphasize business metrics more clearly.",
                                "strengths": ["Clear skills section", "Relevant degree"],
                                "concerns": ["Bullet points focus on tasks rather than quantified outcomes"],
                                "rewrites": [{"before": "Developed APIs", "after": "Designed 15+ production REST APIs serving 50k requests daily"}]
                            }
                        ],
                        "merged": {
                            "verdict": "Highly promising engineering candidate.",
                            "consensus_score": 86,
                            "agreements": ["Strong FastAPI foundation"],
                            "disagreements": ["Recruiter vs Manager priorities"]
                        }
                    }
                }
            }
        },
        404: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def get_critique(id: str, current_user: dict = Depends(get_current_user)):
    """FR-005: Returns multi-agent recruiter-persona critique and actionable bullet rewrites."""
    user_id = current_user.get("sub")
    return ResumeService.get_critique(id, user_id)
