from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, status, Query, HTTPException
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.routes.auth_dep import get_current_user
from app.services.resume_service import ResumeService, process_resume_background
from app.db.repositories import ResumeRepository
from app.schemas.resume import (
    ResumeUploadResponse, ResumeStatusResponse,
    MarketFit, Roadmap, Critique, ErrorResponse
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

    # Launch background parsing pipeline (opens its own DB session internally)
    background_tasks.add_task(process_resume_background, record["resume_id"], user_id)

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

@router.get(
    "/{id}/analysis",
    summary="Get Parsed Resume and Score Result"
)
def get_resume_analysis(
    id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("sub")
    return ResumeService.get_parsed_and_score(id, user_id, db=db)

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
