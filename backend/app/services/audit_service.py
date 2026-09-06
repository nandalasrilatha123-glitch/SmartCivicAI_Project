import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.enums import AuditAction
from app.models.misc import AuditLog


def log_action(
    db: Session,
    *,
    actor_id: uuid.UUID | None,
    action: AuditAction,
    entity_type: str,
    entity_id: str | None = None,
    before_value: dict[str, Any] | None = None,
    after_value: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_value=before_value,
        after_value=after_value,
        ip_address=ip_address,
    )
    db.add(entry)
    db.flush()
    return entry
