import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import ModuleCode


class DepartmentCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    module: ModuleCode
    description: str | None = None
    contact_email: EmailStr | None = None


class DepartmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    contact_email: EmailStr | None = None


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    module: ModuleCode
    description: str | None
    contact_email: str | None
    created_at: datetime


class CategoryCreateRequest(BaseModel):
    module_id: uuid.UUID
    name_en: str = Field(min_length=2, max_length=100)
    name_te: str = Field(min_length=2, max_length=100)
    name_hi: str = Field(min_length=2, max_length=100)
    keywords: str | None = Field(default=None, max_length=500)


class CategoryUpdateRequest(BaseModel):
    name_en: str | None = Field(default=None, min_length=2, max_length=100)
    name_te: str | None = Field(default=None, min_length=2, max_length=100)
    name_hi: str | None = Field(default=None, min_length=2, max_length=100)
    keywords: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    module_id: uuid.UUID
    name_en: str
    name_te: str
    name_hi: str
    keywords: str | None
    is_active: bool


class ModuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: ModuleCode
    name_en: str
    name_te: str
    name_hi: str
    icon: str | None
    is_active: bool
    categories: list[CategoryResponse] = []
