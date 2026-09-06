import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.enums import AuditAction, UserRole
from app.schemas.auth import UserResponse


class UserStatusUpdateRequest(BaseModel):
    is_active: bool


class PaginatedUsers(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID | None
    action: AuditAction
    entity_type: str
    entity_id: str | None
    before_value: dict | None
    after_value: dict | None
    ip_address: str | None
    created_at: datetime


class PaginatedAuditLogs(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
