from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.routes.auth_dep import get_current_user
from app.db.repositories import ParsedEntitiesRepository, ResumeRepository
from app.schemas.crud_schemas import ParsedEntitiesResponse, ParsedEntitiesUpdate

router = APIRouter(prefix="/parsed-entities", tags=["Parsed Entities"])

@router.get(
    "/{resume_id}",
    response_model=ParsedEntitiesResponse,
    summary="Get Parsed Entities for Resume"
)
def get_parsed_entities(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("sub")
    resume = ResumeRepository.get_by_id(db, resume_id)
    if not resume or resume.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "RESUME_NOT_FOUND", "message": f"Resume '{resume_id}' not found."})
    if resume.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "FORBIDDEN", "message": "Access denied."})

    pe = ParsedEntitiesRepository.get_by_resume_id(db, resume_id)
    if not pe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "PARSED_ENTITIES_NOT_FOUND", "message": f"No parsed entities for resume '{resume_id}'."})
    return pe

@router.put(
    "/{resume_id}",
    response_model=ParsedEntitiesResponse,
    summary="Update Parsed Entities for Resume"
)
def update_parsed_entities(
    resume_id: str,
    payload: ParsedEntitiesUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("sub")
    resume = ResumeRepository.get_by_id(db, resume_id)
    if not resume or resume.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "RESUME_NOT_FOUND", "message": f"Resume '{resume_id}' not found."})
    if resume.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "FORBIDDEN", "message": "Access denied."})

    data = payload.model_dump(exclude_unset=True)
    pe = ParsedEntitiesRepository.create_or_update(
        db,
        resume_id=resume_id,
        name=data.get("name"),
        email=data.get("email"),
        education=data.get("education"),
        experience=data.get("experience"),
        skills=data.get("skills"),
        sections=data.get("sections"),
        raw_text=data.get("raw_text")
    )
    return pe
