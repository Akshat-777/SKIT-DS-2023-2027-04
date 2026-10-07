from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.routes.auth_dep import get_current_user
from app.db.repositories import SkillRepository
from app.schemas.crud_schemas import SkillResponse, SkillCreate, SkillUpdate, PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/skills", tags=["Master Skills"])

@router.get(
    "",
    response_model=PaginatedResponse[SkillResponse],
    summary="List Master Skills (Paginated & Filtered)"
)
def list_skills(
    query: Optional[str] = Query(None, alias="q"),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    skills, total = SkillRepository.list_skills(db, query_str=query, category=category, page=page, page_size=page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=skills,
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )

@router.post(
    "",
    response_model=SkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Master Skill"
)
def create_skill(
    payload: SkillCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = SkillRepository.get_by_name(db, payload.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "SKILL_ALREADY_EXISTS", "message": f"Skill '{payload.name}' already exists."}
        )
    return SkillRepository.create(
        db,
        name=payload.name,
        category=payload.category,
        description=payload.description,
        aliases=payload.aliases
    )

@router.get(
    "/{id}",
    response_model=SkillResponse,
    summary="Get Skill by ID"
)
def get_skill(id: str, db: Session = Depends(get_db)):
    skill = SkillRepository.get_by_id(db, id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SKILL_NOT_FOUND", "message": f"Skill '{id}' not found."}
        )
    return skill

@router.put(
    "/{id}",
    response_model=SkillResponse,
    summary="Update Master Skill"
)
def update_skill(
    id: str,
    payload: SkillUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated = SkillRepository.update(db, id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SKILL_NOT_FOUND", "message": f"Skill '{id}' not found."}
        )
    return updated

@router.delete(
    "/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Master Skill"
)
def delete_skill(
    id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = SkillRepository.delete(db, id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SKILL_NOT_FOUND", "message": f"Skill '{id}' not found."}
        )
    return {"message": f"Skill '{id}' deleted successfully."}
