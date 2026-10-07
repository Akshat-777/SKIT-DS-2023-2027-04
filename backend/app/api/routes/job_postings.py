from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.routes.auth_dep import get_current_user
from app.db.repositories import JobPostingRepository
from app.schemas.crud_schemas import (
    JobPostingResponse, JobPostingCreate, JobPostingUpdate, PaginatedResponse, PaginationMeta
)

router = APIRouter(prefix="/job-postings", tags=["Job Postings"])

@router.get(
    "",
    response_model=PaginatedResponse[JobPostingResponse],
    summary="List Job Postings (Pagination, Filtering, Sorting)"
)
def list_job_postings(
    role: Optional[str] = Query(None, description="Filter by target role"),
    skill: Optional[str] = Query(None, description="Filter by skill required"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    start_date: Optional[datetime] = Query(None, description="Filter postings on or after ISO datetime"),
    end_date: Optional[datetime] = Query(None, description="Filter postings on or before ISO datetime"),
    sort_by: str = Query("posted_at", description="Field to sort by: posted_at, title, salary_max"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    postings, total = JobPostingRepository.list_job_postings(
        db,
        role=role,
        skill=skill,
        company=company,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResponse(
        items=postings,
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )

@router.post(
    "",
    response_model=JobPostingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Job Posting"
)
def create_job_posting(
    payload: JobPostingCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    posting = JobPostingRepository.create(
        db,
        title=payload.title,
        company=payload.company,
        target_role=payload.target_role,
        skills=payload.skills,
        location=payload.location,
        experience=payload.experience,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        currency=payload.currency,
        unit=payload.unit,
        description=payload.description,
        source=payload.source,
        posted_at=payload.posted_at
    )
    return posting

@router.get(
    "/{id}",
    response_model=JobPostingResponse,
    summary="Get Job Posting by ID"
)
def get_job_posting(id: str, db: Session = Depends(get_db)):
    posting = JobPostingRepository.get_by_id(db, id)
    if not posting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_POSTING_NOT_FOUND", "message": f"Job posting '{id}' not found."}
        )
    return posting

@router.put(
    "/{id}",
    response_model=JobPostingResponse,
    summary="Update Job Posting"
)
def update_job_posting(
    id: str,
    payload: JobPostingUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated = JobPostingRepository.update(db, id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_POSTING_NOT_FOUND", "message": f"Job posting '{id}' not found."}
        )
    return updated

@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Job Posting"
)
def delete_job_posting(
    id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = JobPostingRepository.delete(db, id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_POSTING_NOT_FOUND", "message": f"Job posting '{id}' not found."}
        )
    return {"message": f"Job posting '{id}' deleted successfully."}
