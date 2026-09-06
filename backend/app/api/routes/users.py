import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.enums import AuditAction, UserRole
from app.core.security import hash_password
from app.database.session import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.admin import PaginatedUsers, UserStatusUpdateRequest
from app.schemas.auth import OfficerCreateRequest, UserResponse
from app.services.audit_service import log_action

router = APIRouter(prefix="/users", tags=["User Management (Admin)"])


@router.get("", response_model=PaginatedUsers)
def list_users(
    role: UserRole | None = None,
    is_active: bool | None = None,
    department_id: uuid.UUID | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if department_id:
        query = query.filter(User.department_id == department_id)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(User.full_name.ilike(like), User.email.ilike(like)))

    total = query.count()
    items = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedUsers(
        items=items, total=total, page=page, page_size=page_size, total_pages=max(1, math.ceil(total / page_size))
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.post("/officers", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_officer(
    payload: OfficerCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

    department = db.get(Department, payload.department_id)
    if department is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Department not found")

    officer = User(
        full_name=payload.full_name.strip(),
        email=payload.email.lower(),
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=UserRole.OFFICER,
        department_id=department.id,
        preferred_language=payload.preferred_language,
    )
    db.add(officer)
    db.flush()

    log_action(
        db, actor_id=admin.id, action=AuditAction.CREATE, entity_type="User", entity_id=str(officer.id),
        after_value={"email": officer.email, "role": "OFFICER", "department_id": str(department.id)},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(officer)
    return officer


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.id == admin.id and not payload.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot deactivate your own account")

    before = user.is_active
    user.is_active = payload.is_active

    log_action(
        db, actor_id=admin.id, action=AuditAction.UPDATE, entity_type="User", entity_id=str(user.id),
        before_value={"is_active": before}, after_value={"is_active": payload.is_active},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(user)
    return user
