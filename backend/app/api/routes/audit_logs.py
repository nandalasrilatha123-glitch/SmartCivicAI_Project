import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.enums import AuditAction
from app.database.session import get_db
from app.models.misc import AuditLog
from app.schemas.admin import PaginatedAuditLogs

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs (Admin)"])


@router.get("", response_model=PaginatedAuditLogs)
def list_audit_logs(
    entity_type: str | None = None,
    action: AuditAction | None = None,
    actor_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AuditLog.action == action)
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)

    total = query.count()
    items = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedAuditLogs(
        items=items, total=total, page=page, page_size=page_size, total_pages=max(1, math.ceil(total / page_size))
    )
