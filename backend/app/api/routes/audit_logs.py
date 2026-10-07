from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.routes.auth_dep import get_current_user
from app.models.models import AuditLog
from app.schemas.crud_schemas import AuditLogResponse, PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get(
    "",
    response_model=PaginatedResponse[AuditLogResponse],
    summary="List Audit Logs (Privacy & Compliance Tracking)"
)
def list_audit_logs(
    target_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.get("sub")
    q = db.query(AuditLog).filter(AuditLog.user_id == user_id)
    if target_type:
        q = q.filter(AuditLog.target_type == target_type)
    total = q.count()
    logs = q.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PaginatedResponse(
        items=logs,
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )
