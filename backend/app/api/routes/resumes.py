from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, status, Query, HTTPException, Request, Response
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.routes.auth_dep import get_current_user
from app.services.resume_service import ResumeService, process_resume_background
from app.db.repositories import ResumeRepository
from app.schemas.resume import (
    ResumeUploadResponse, ResumeStatusResponse, AnalyzeResumeRequest,
    ScoreResult, MarketFit, Roadmap, Critique, ErrorResponse
)
from app.schemas.crud_schemas import ResumeResponse, PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/resumes", tags=["Resumes"])

@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload Resume (PDF/DOCX)",
    responses={
        202: {"description": "Resume accepted for asynchronous parsing and scoring."},
        422: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"}
    }
)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """FR-001 & NFR-005: Validates file, stores securely, creates DB record, initiates background processing."""
    user_id = current_user.get("sub", "default_user")
    record = await ResumeService.save_and_initiate_upload(file, user_id, db=db)

    # Launch background parsing pipeline — pass saved_file_path so the NLP parser can read the file
    background_tasks.add_task(
        process_resume_background,
        record["resume_id"],
        user_id,
        record["saved_file_path"],
    )

    return ResumeUploadResponse(
        resume_id=record["resume_id"],
        filename=record["filename"],
        status=record["status"],
        message="Resume uploaded successfully. Processing started in background."
    )

@router.get(
    "",
    response_model=PaginatedResponse[ResumeResponse],
    summary="List Current User Resumes"
)
def list_resumes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists current user's non-deleted resumes with pagination and status filtering."""
    user_id = current_user.get("sub")
    resumes, total = ResumeRepository.list_user_resumes(db, user_id=user_id, page=page, page_size=page_size, status=status_filter)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResponse(
        items=resumes,
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )

@router.get(
    "/{id}",
    response_model=ResumeStatusResponse,
    summary="Get Resume Processing Status",
    responses={
        200: {"description": "Current processing status."},
        404: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
def get_resume_status(
    id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns background processing status. Enforces ownership check."""
    user_id = current_user.get("sub")
    return ResumeService.get_status(id, user_id, db=db)

@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Soft Delete Resume (Privacy)"
)
def soft_delete_resume(
    id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft deletes resume record and creates audit log event."""
    user_id = current_user.get("sub")
    success = ResumeRepository.soft_delete(db, resume_id=id, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESUME_NOT_FOUND", "message": f"Resume '{id}' not found or access denied."}
        )
    return {"message": f"Resume '{id}' soft deleted successfully."}

@router.delete(
    "/{id}/hard",
    status_code=status.HTTP_200_OK,
    summary="Hard Delete Resume & Purge Physical File (NFR-004 Privacy)"
)
def hard_delete_resume(
    id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Permanently deletes resume DB record, purges stored file from disk, and logs deletion audit event."""
    user_id = current_user.get("sub")
    success = ResumeRepository.hard_delete(db, resume_id=id, user_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESUME_NOT_FOUND", "message": f"Resume '{id}' not found or access denied."}
        )
    return {"message": f"Resume '{id}' and associated file permanently deleted."}

@router.post(
    "/{id}/analyze",
    response_model=ScoreResult,
    status_code=status.HTTP_200_OK,
    summary="Analyze Resume with Recruiter-Grade ATS Scoring & Skill Gap",
    responses={
        200: {"model": ScoreResult, "description": "Analysis completed and ScoreResult returned."},
        404: {"model": ErrorResponse, "description": "Resume not found."},
        409: {"model": ErrorResponse, "description": "Resume parsing in progress."},
        422: {"model": ErrorResponse, "description": "Target role not found in role taxonomy or validation error."},
        502: {"model": ErrorResponse, "description": "Scoring service unavailable or circuit breaker open."},
        504: {"model": ErrorResponse, "description": "Scoring service timeout."},
    }
)
async def analyze_resume(
    id: str,
    payload: AnalyzeResumeRequest,
    response: Response,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    FR-003: Loads ParsedResume from PostgreSQL, validates role taxonomy,
    queries Aryan's scoring service via resilient HTTP client, caches result in Redis/Memory (TTL 1h),
    stores ScoreResult in analyses table, and returns it.
    Exposes X-Cache ('HIT' / 'MISS') and X-Response-Time-Ms headers.
    """
    user_id = current_user.get("sub")
    request_id = getattr(request.state, "request_id", None)
    score_result, is_cache_hit, latency_ms = await ResumeService.analyze_resume(
        resume_id=id,
        target_role=payload.target_role,
        user_id=user_id,
        db=db,
        request_id=request_id
    )
    response.headers["X-Cache"] = "HIT" if is_cache_hit else "MISS"
    response.headers["X-Response-Time-Ms"] = f"{latency_ms:.2f}"
    return score_result

@router.get(
    "/{id}/analysis",
    summary="Get Latest Stored Resume Analysis",
    responses={
        200: {"description": "Latest stored ScoreResult and ParsedResume."},
        404: {"model": ErrorResponse, "description": "Analysis or resume not found."}
    }
)
def get_resume_analysis(
    id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the latest stored analysis result for this resume."""
    user_id = current_user.get("sub")
    return ResumeService.get_latest_analysis(id, user_id, db=db)

@router.get(
    "/{id}/market-fit",
    response_model=MarketFit,
    summary="Get Market Fit & Salary Prediction"
)
def get_market_fit(
    id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("sub")
    return ResumeService.get_market_fit(id, user_id, db=db)

@router.get(
    "/{id}/roadmap",
    response_model=Roadmap,
    summary="Get Personalized Learning Roadmap"
)
def get_roadmap(
    id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("sub")
    return ResumeService.get_roadmap(id, user_id, db=db)

@router.get(
    "/{id}/critique",
    response_model=Critique,
    summary="Get Multi-Agent Recruiter Persona Critique"
)
def get_critique(
    id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("sub")
    return ResumeService.get_critique(id, user_id, db=db)
