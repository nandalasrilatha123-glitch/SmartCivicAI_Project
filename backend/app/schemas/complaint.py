import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ComplaintStatus, LanguageCode, ModuleCode, PriorityLevel


class ComplaintCreateRequest(BaseModel):
    module: ModuleCode
    category_id: uuid.UUID | None = None
    description: str = Field(min_length=10, max_length=5000)
    original_language: LanguageCode
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    address: str | None = Field(default=None, max_length=500)

    @field_validator("description")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Complaint description cannot be empty")
        return v.strip()


class ComplaintStatusUpdateRequest(BaseModel):
    status: ComplaintStatus
    note: str | None = Field(default=None, max_length=1000)


class ComplaintAssignRequest(BaseModel):
    department_id: uuid.UUID | None = None
    assigned_officer_id: uuid.UUID | None = None


class ComplaintOverrideRequest(BaseModel):
    """Admin override of AI-predicted module/category/priority/department (spec §28)."""
    module: ModuleCode | None = None
    category_id: uuid.UUID | None = None
    priority: PriorityLevel | None = None
    department_id: uuid.UUID | None = None


class ComplaintResolveRequest(BaseModel):
    officer_remarks: str = Field(min_length=3, max_length=2000)


class FeedbackCreateRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ComplaintImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_path: str
    original_filename: str


class ComplaintStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    from_status: ComplaintStatus | None
    to_status: ComplaintStatus
    note: str | None
    created_at: datetime


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    complaint_number: str
    citizen_id: uuid.UUID
    module: ModuleCode
    category_id: uuid.UUID | None
    original_language: LanguageCode
    original_text: str
    translated_text: str | None
    summary: str | None
    latitude: float | None
    longitude: float | None
    address: str | None
    department_id: uuid.UUID | None
    assigned_officer_id: uuid.UUID | None
    priority: PriorityLevel
    status: ComplaintStatus
    officer_remarks: str | None
    resolution_proof_path: str | None
    is_demo_data: bool
    created_at: datetime
    updated_at: datetime
    images: list[ComplaintImageResponse] = []


class ComplaintListItemResponse(BaseModel):
    """Lighter-weight shape for list/table views."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    complaint_number: str
    module: ModuleCode
    priority: PriorityLevel
    status: ComplaintStatus
    original_language: LanguageCode
    summary: str | None
    address: str | None
    department_id: uuid.UUID | None
    assigned_officer_id: uuid.UUID | None
    created_at: datetime


class PaginatedComplaints(BaseModel):
    items: list[ComplaintListItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
