import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.enums import AuditAction
from app.database.session import get_db
from app.models.department import Department
from app.models.user import User
from app.schemas.catalog import DepartmentCreateRequest, DepartmentResponse, DepartmentUpdateRequest
from app.services.audit_service import log_action

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=list[DepartmentResponse])
def list_departments(
    module: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Department)
    if module:
        query = query.filter(Department.module == module)
    return query.order_by(Department.name).all()


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    department = Department(
        name=payload.name.strip(),
        module=payload.module,
        description=payload.description,
        contact_email=payload.contact_email,
    )
    db.add(department)
    db.flush()
    log_action(
        db, actor_id=current_user.id, action=AuditAction.CREATE, entity_type="Department",
        entity_id=str(department.id), after_value={"name": department.name, "module": department.module.value},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(department)
    return department


@router.patch("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Department not found")

    before = {"name": department.name, "description": department.description, "contact_email": department.contact_email}
    if payload.name is not None:
        department.name = payload.name.strip()
    if payload.description is not None:
        department.description = payload.description
    if payload.contact_email is not None:
        department.contact_email = payload.contact_email

    log_action(
        db, actor_id=current_user.id, action=AuditAction.UPDATE, entity_type="Department",
        entity_id=str(department.id), before_value=before,
        after_value={"name": department.name, "description": department.description, "contact_email": department.contact_email},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(department)
    return department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(
    department_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    department = db.get(Department, department_id)
    if department is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Department not found")

    log_action(
        db, actor_id=current_user.id, action=AuditAction.DELETE, entity_type="Department",
        entity_id=str(department.id), before_value={"name": department.name},
        ip_address=request.client.host if request.client else None,
    )
    db.delete(department)
    db.commit()
