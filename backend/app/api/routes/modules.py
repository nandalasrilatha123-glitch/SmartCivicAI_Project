import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_admin
from app.core.enums import AuditAction
from app.database.session import get_db
from app.models.module import Category, Module
from app.schemas.catalog import (
    CategoryCreateRequest,
    CategoryResponse,
    CategoryUpdateRequest,
    ModuleResponse,
)
from app.services.audit_service import log_action

router = APIRouter(tags=["Modules & Categories"])


@router.get("/modules", response_model=list[ModuleResponse])
def list_modules(db: Session = Depends(get_db)):
    """Public: needed to populate the citizen complaint-submission form."""
    return (
        db.query(Module)
        .options(joinedload(Module.categories))
        .filter(Module.is_active.is_(True))
        .order_by(Module.name_en)
        .all()
    )


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    module = db.get(Module, payload.module_id)
    if module is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Module not found")

    category = Category(
        module_id=module.id,
        name_en=payload.name_en.strip(),
        name_te=payload.name_te.strip(),
        name_hi=payload.name_hi.strip(),
        keywords=payload.keywords,
    )
    db.add(category)
    db.flush()
    log_action(
        db, actor_id=current_user.id, action=AuditAction.CREATE, entity_type="Category",
        entity_id=str(category.id), after_value={"name_en": category.name_en, "module": module.code.value},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")

    before = {"name_en": category.name_en, "is_active": category.is_active, "keywords": category.keywords}
    for field_name in ("name_en", "name_te", "name_hi", "keywords", "is_active"):
        value = getattr(payload, field_name)
        if value is not None:
            setattr(category, field_name, value.strip() if isinstance(value, str) else value)

    log_action(
        db, actor_id=current_user.id, action=AuditAction.UPDATE, entity_type="Category",
        entity_id=str(category.id), before_value=before,
        after_value={"name_en": category.name_en, "is_active": category.is_active, "keywords": category.keywords},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")

    log_action(
        db, actor_id=current_user.id, action=AuditAction.DELETE, entity_type="Category",
        entity_id=str(category.id), before_value={"name_en": category.name_en},
        ip_address=request.client.host if request.client else None,
    )
    db.delete(category)
    db.commit()
