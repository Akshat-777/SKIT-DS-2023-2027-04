from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.routes.auth_dep import get_current_user
from app.db.repositories import AnalysisRepository, ResumeRepository
from app.schemas.crud_schemas import AnalysisResponse, AnalysisCreate, PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/analyses", tags=["Analyses"])

@router.post(
    "",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Analysis Record"
)
def create_analysis(
    payload: AnalysisCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("sub")
    resume = ResumeRepository.get_by_id(db, payload.resume_id)
    if not resume or resume.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESUME_NOT_FOUND", "message": f"Resume '{payload.resume_id}' not found."}
        )
    if resume.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Access denied."}
        )

    analysis = AnalysisRepository.create(
        db,
        resume_id=payload.resume_id,
        target_role=payload.target_role,
        ats_score=payload.ats_score,
        breakdown=payload.breakdown,
        skill_gap=payload.skill_gap
    )
    return analysis

@router.get(
    "/{id}",
    response_model=AnalysisResponse,
    summary="Get Analysis by ID"
)
def get_analysis(
    id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("sub")
    analysis = AnalysisRepository.get_by_id(db, id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ANALYSIS_NOT_FOUND", "message": f"Analysis '{id}' not found."}
        )

    resume = ResumeRepository.get_by_id(db, analysis.resume_id)
    if resume and resume.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Access denied."}
        )
    return analysis

@router.get(
    "/resume/{resume_id}",
    response_model=AnalysisResponse,
    summary="Get Latest Analysis for Resume"
)
def get_resume_analysis(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("sub")
    resume = ResumeRepository.get_by_id(db, resume_id)
    if not resume or resume.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESUME_NOT_FOUND", "message": f"Resume '{resume_id}' not found."}
        )
    if resume.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Access denied."}
        )

    analysis = AnalysisRepository.get_latest_by_resume_id(db, resume_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ANALYSIS_NOT_FOUND", "message": f"No analysis found for resume '{resume_id}'."}
        )
    return analysis

@router.get(
    "",
    response_model=PaginatedResponse[AnalysisResponse],
    summary="List Analyses (Paginated)"
)
def list_analyses(
    resume_id: Optional[str] = Query(None),
    target_role: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items, total = AnalysisRepository.list_analyses(db, resume_id=resume_id, target_role=target_role, page=page, page_size=page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )
