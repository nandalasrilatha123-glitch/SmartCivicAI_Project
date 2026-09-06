import math
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.ai.pipeline import run_ai_pipeline
from app.api.deps import get_current_user, require_admin, require_citizen, require_officer
from app.core.config import settings
from app.core.enums import (
    AuditAction,
    ComplaintStatus,
    LanguageCode,
    ModuleCode,
    NotificationType,
    PriorityLevel,
    UserRole,
)
from app.cv.cv_service import analyze_and_store
from app.database.session import get_db
from app.models.complaint import Complaint, ComplaintImage
from app.models.department import Department
from app.models.misc import Feedback, Notification
from app.models.user import User
from app.notifications import email_service
from app.schemas.complaint import (
    ComplaintAssignRequest,
    ComplaintImageResponse,
    ComplaintListItemResponse,
    ComplaintOverrideRequest,
    ComplaintResolveRequest,
    ComplaintResponse,
    ComplaintStatusHistoryResponse,
    ComplaintStatusUpdateRequest,
    FeedbackCreateRequest,
    PaginatedComplaints,
)
from app.services.audit_service import log_action
from app.services.complaint_service import change_status, generate_complaint_number, is_transition_allowed
from app.services.upload_service import validate_and_save_image

router = APIRouter(prefix="/complaints", tags=["Complaints"])


def _get_complaint_or_404(db: Session, complaint_id: uuid.UUID) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Complaint not found")
    return complaint


def _assert_can_view(complaint: Complaint, user: User) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.CITIZEN and complaint.citizen_id == user.id:
        return
    if user.role == UserRole.OFFICER and complaint.department_id == user.department_id and user.department_id is not None:
        return
    raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this complaint")


def _notify(db: Session, user_id: uuid.UUID, complaint_id: uuid.UUID, ntype: NotificationType, title: str, message: str) -> None:
    db.add(Notification(user_id=user_id, complaint_id=complaint_id, type=ntype, title=title, message=message))


def _citizen_view_url(complaint_id) -> str:
    return f"{settings.FRONTEND_ORIGIN}/complaints/{complaint_id}"


def _admin_view_url(complaint_id) -> str:
    return f"{settings.FRONTEND_ORIGIN}/admin/complaints/{complaint_id}"


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def submit_complaint(
    request: Request,
    module: ModuleCode = Form(...),
    category_id: uuid.UUID | None = Form(default=None),
    description: str = Form(..., min_length=10, max_length=5000),
    original_language: LanguageCode = Form(...),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    address: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_citizen),
):
    if not description.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Complaint description cannot be empty")

    complaint = Complaint(
        complaint_number=generate_complaint_number(db, module.value),
        citizen_id=current_user.id,
        module=module,
        category_id=category_id,
        original_language=original_language,
        original_text=description.strip(),
        latitude=latitude,
        longitude=longitude,
        address=address,
        priority=PriorityLevel.MEDIUM,
        status=ComplaintStatus.NEW,
    )
    db.add(complaint)
    db.flush()

    if image is not None and image.filename:
        relative_path, original_filename, size_bytes = validate_and_save_image(image, subfolder="complaints")
        image_record = ComplaintImage(
            complaint_id=complaint.id,
            file_path=relative_path,
            original_filename=original_filename,
            file_size_bytes=size_bytes,
        )
        db.add(image_record)
        db.flush()
        analyze_and_store(db, image_record)

    # Run the (demo-mode) multi-agent AI pipeline synchronously — it's fast
    # rule-based logic, no network calls, so no need for a background job yet.
    run_ai_pipeline(db, complaint)

    change_status(db, complaint, complaint.status, changed_by_id=current_user.id, note="Complaint submitted")

    _notify(
        db, current_user.id, complaint.id, NotificationType.NEW_COMPLAINT,
        "Complaint registered", f"Your complaint {complaint.complaint_number} has been registered.",
    )
    if complaint.status == ComplaintStatus.REQUIRES_ADMIN_REVIEW:
        admins = db.query(User).filter(User.role == UserRole.ADMIN, User.is_active.is_(True)).all()
        for admin in admins:
            _notify(
                db, admin.id, complaint.id, NotificationType.ADMIN_REVIEW_REQUIRED,
                "Complaint requires review", f"Complaint {complaint.complaint_number} has low AI confidence and needs manual review.",
            )

    log_action(
        db, actor_id=current_user.id, action=AuditAction.CREATE, entity_type="Complaint",
        entity_id=str(complaint.id), after_value={"complaint_number": complaint.complaint_number, "module": module.value},
        ip_address=request.client.host if request.client else None,
    )

    db.commit()
    db.refresh(complaint)

    # spec §13: notify ADMIN_EMAIL whenever a new complaint is registered.
    # Never allowed to fail the request — send_email swallows its own errors.
    email_service.send_new_complaint_admin_email(
        complaint=complaint,
        department_name=complaint.department.name if complaint.department else None,
        citizen_email=current_user.email,
        view_url=_admin_view_url(complaint.id),
    )

    return complaint


@router.get("", response_model=PaginatedComplaints)
def list_complaints(
    module: ModuleCode | None = None,
    status_filter: ComplaintStatus | None = Query(default=None, alias="status"),
    priority: PriorityLevel | None = None,
    department_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    language: LanguageCode | None = None,
    search: str | None = Query(default=None, description="Matches complaint number or description"),
    date_from: str | None = None,
    date_to: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_desc: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Complaint)

    # --- role-based scoping ---
    if current_user.role == UserRole.CITIZEN:
        query = query.filter(Complaint.citizen_id == current_user.id)
    elif current_user.role == UserRole.OFFICER:
        if current_user.department_id is None:
            return PaginatedComplaints(items=[], total=0, page=page, page_size=page_size, total_pages=0)
        query = query.filter(Complaint.department_id == current_user.department_id)
    # ADMIN: no scoping

    if module:
        query = query.filter(Complaint.module == module)
    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    if priority:
        query = query.filter(Complaint.priority == priority)
    if department_id:
        query = query.filter(Complaint.department_id == department_id)
    if category_id:
        query = query.filter(Complaint.category_id == category_id)
    if language:
        query = query.filter(Complaint.original_language == language)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Complaint.complaint_number.ilike(like), Complaint.original_text.ilike(like)))
    if date_from:
        query = query.filter(Complaint.created_at >= date_from)
    if date_to:
        query = query.filter(Complaint.created_at <= date_to)

    total = query.count()
    query = query.order_by(Complaint.created_at.desc() if sort_desc else Complaint.created_at.asc())
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedComplaints(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(complaint_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    complaint = _get_complaint_or_404(db, complaint_id)
    _assert_can_view(complaint, current_user)
    return complaint


@router.get("/{complaint_id}/history", response_model=list[ComplaintStatusHistoryResponse])
def get_complaint_history(complaint_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    complaint = _get_complaint_or_404(db, complaint_id)
    _assert_can_view(complaint, current_user)
    return complaint.status_history


@router.post("/{complaint_id}/images", response_model=ComplaintImageResponse, status_code=status.HTTP_201_CREATED)
def add_complaint_image(
    complaint_id: uuid.UUID,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    complaint = _get_complaint_or_404(db, complaint_id)
    _assert_can_view(complaint, current_user)

    relative_path, original_filename, size_bytes = validate_and_save_image(image, subfolder="complaints")
    record = ComplaintImage(
        complaint_id=complaint.id, file_path=relative_path, original_filename=original_filename, file_size_bytes=size_bytes,
    )
    db.add(record)
    db.flush()
    analyze_and_store(db, record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/{complaint_id}/accept", response_model=ComplaintResponse)
def accept_complaint(
    complaint_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_officer),
):
    """Officer self-assigns a complaint that's already routed to their department but has no officer yet."""
    complaint = _get_complaint_or_404(db, complaint_id)

    if complaint.department_id != current_user.department_id or current_user.department_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This complaint is not routed to your department")
    if complaint.assigned_officer_id is not None and complaint.assigned_officer_id != current_user.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "This complaint has already been accepted by another officer")

    complaint.assigned_officer_id = current_user.id
    if complaint.status in (ComplaintStatus.PENDING, ComplaintStatus.REQUIRES_ADMIN_REVIEW):
        change_status(db, complaint, ComplaintStatus.ASSIGNED, changed_by_id=current_user.id, note="Accepted by officer")

    log_action(
        db, actor_id=current_user.id, action=AuditAction.UPDATE, entity_type="Complaint",
        entity_id=str(complaint.id), after_value={"assigned_officer_id": str(current_user.id)},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(complaint)
    return complaint


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
def update_status(
    complaint_id: uuid.UUID,
    payload: ComplaintStatusUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_officer),
):
    complaint = _get_complaint_or_404(db, complaint_id)
    _assert_can_view(complaint, current_user)

    if not is_transition_allowed(complaint.status, payload.status):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot move complaint from {complaint.status.value} to {payload.status.value}",
        )

    before_status = complaint.status
    change_status(db, complaint, payload.status, changed_by_id=current_user.id, note=payload.note)

    notif_type = {
        ComplaintStatus.RESOLVED: NotificationType.COMPLAINT_RESOLVED,
        ComplaintStatus.ESCALATED: NotificationType.COMPLAINT_ESCALATED,
    }.get(payload.status, NotificationType.STATUS_CHANGED)

    _notify(
        db, complaint.citizen_id, complaint.id, notif_type,
        f"Complaint {complaint.complaint_number} status updated",
        f"Your complaint status changed from {before_status.value} to {payload.status.value}.",
    )

    log_action(
        db, actor_id=current_user.id, action=AuditAction.STATUS_CHANGE, entity_type="Complaint",
        entity_id=str(complaint.id), before_value={"status": before_status.value}, after_value={"status": payload.status.value},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(complaint)

    email_service.send_status_change_email(
        complaint=complaint, citizen_email=complaint.citizen.email, language=complaint.original_language.value,
        note=payload.note, view_url=_citizen_view_url(complaint.id),
    )

    return complaint


@router.patch("/{complaint_id}/assign", response_model=ComplaintResponse)
def assign_complaint(
    complaint_id: uuid.UUID,
    payload: ComplaintAssignRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    complaint = _get_complaint_or_404(db, complaint_id)

    before = {"department_id": str(complaint.department_id) if complaint.department_id else None,
              "assigned_officer_id": str(complaint.assigned_officer_id) if complaint.assigned_officer_id else None}

    if payload.department_id is not None:
        department = db.get(Department, payload.department_id)
        if department is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Department not found")
        complaint.department_id = department.id

    officer_email = None
    if payload.assigned_officer_id is not None:
        officer = db.get(User, payload.assigned_officer_id)
        if officer is None or officer.role != UserRole.OFFICER:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "assigned_officer_id must reference an existing officer")
        complaint.assigned_officer_id = officer.id
        officer_email = officer.email
        _notify(
            db, officer.id, complaint.id, NotificationType.COMPLAINT_ASSIGNED,
            "New complaint assigned to you", f"Complaint {complaint.complaint_number} has been assigned to you.",
        )

    if complaint.status in (ComplaintStatus.PENDING, ComplaintStatus.REQUIRES_ADMIN_REVIEW):
        change_status(db, complaint, ComplaintStatus.ASSIGNED, changed_by_id=current_user.id, note="Assigned by admin")

    log_action(
        db, actor_id=current_user.id, action=AuditAction.UPDATE, entity_type="Complaint",
        entity_id=str(complaint.id), before_value=before,
        after_value={"department_id": str(complaint.department_id) if complaint.department_id else None,
                     "assigned_officer_id": str(complaint.assigned_officer_id) if complaint.assigned_officer_id else None},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(complaint)

    if officer_email:
        email_service.send_complaint_assigned_email(complaint=complaint, officer_email=officer_email, view_url=_admin_view_url(complaint.id))

    return complaint


@router.patch("/{complaint_id}/override", response_model=ComplaintResponse)
def override_ai_decision(
    complaint_id: uuid.UUID,
    payload: ComplaintOverrideRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin override of AI predictions — every field changed is separately audit-logged (spec §28)."""
    complaint = _get_complaint_or_404(db, complaint_id)
    ip = request.client.host if request.client else None

    if payload.module is not None and payload.module != complaint.module:
        before, complaint.module = complaint.module.value, payload.module
        log_action(db, actor_id=current_user.id, action=AuditAction.AI_OVERRIDE_MODULE, entity_type="Complaint",
                   entity_id=str(complaint.id), before_value={"module": before}, after_value={"module": payload.module.value}, ip_address=ip)
        if complaint.ai_analysis and complaint.ai_analysis.classification:
            complaint.ai_analysis.classification.is_overridden = True
            complaint.ai_analysis.classification.overridden_by_id = current_user.id

    if payload.category_id is not None and payload.category_id != complaint.category_id:
        before = str(complaint.category_id) if complaint.category_id else None
        complaint.category_id = payload.category_id
        log_action(db, actor_id=current_user.id, action=AuditAction.AI_OVERRIDE_CATEGORY, entity_type="Complaint",
                   entity_id=str(complaint.id), before_value={"category_id": before}, after_value={"category_id": str(payload.category_id)}, ip_address=ip)
        if complaint.ai_analysis and complaint.ai_analysis.classification:
            complaint.ai_analysis.classification.is_overridden = True
            complaint.ai_analysis.classification.overridden_by_id = current_user.id

    if payload.priority is not None and payload.priority != complaint.priority:
        before, complaint.priority = complaint.priority.value, payload.priority
        log_action(db, actor_id=current_user.id, action=AuditAction.AI_OVERRIDE_PRIORITY, entity_type="Complaint",
                   entity_id=str(complaint.id), before_value={"priority": before}, after_value={"priority": payload.priority.value}, ip_address=ip)
        if complaint.ai_analysis and complaint.ai_analysis.priority_assessment:
            complaint.ai_analysis.priority_assessment.is_overridden = True
            complaint.ai_analysis.priority_assessment.overridden_by_id = current_user.id

    if payload.department_id is not None and payload.department_id != complaint.department_id:
        before = str(complaint.department_id) if complaint.department_id else None
        complaint.department_id = payload.department_id
        log_action(db, actor_id=current_user.id, action=AuditAction.AI_OVERRIDE_DEPARTMENT, entity_type="Complaint",
                   entity_id=str(complaint.id), before_value={"department_id": before}, after_value={"department_id": str(payload.department_id)}, ip_address=ip)
        if complaint.ai_analysis and complaint.ai_analysis.routing:
            complaint.ai_analysis.routing.is_overridden = True
            complaint.ai_analysis.routing.overridden_by_id = current_user.id

    if complaint.status == ComplaintStatus.REQUIRES_ADMIN_REVIEW:
        change_status(db, complaint, ComplaintStatus.PENDING, changed_by_id=current_user.id, note="Reviewed and corrected by admin")

    db.commit()
    db.refresh(complaint)
    return complaint


@router.post("/{complaint_id}/resolve", response_model=ComplaintResponse)
def resolve_complaint(
    complaint_id: uuid.UUID,
    payload: ComplaintResolveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_officer),
):
    complaint = _get_complaint_or_404(db, complaint_id)
    _assert_can_view(complaint, current_user)

    if not is_transition_allowed(complaint.status, ComplaintStatus.RESOLVED):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Cannot resolve a complaint in status {complaint.status.value}")

    complaint.officer_remarks = payload.officer_remarks.strip()
    change_status(db, complaint, ComplaintStatus.RESOLVED, changed_by_id=current_user.id, note=payload.officer_remarks)

    _notify(
        db, complaint.citizen_id, complaint.id, NotificationType.COMPLAINT_RESOLVED,
        f"Complaint {complaint.complaint_number} resolved",
        "Your complaint has been marked resolved. Please share your feedback.",
    )
    log_action(
        db, actor_id=current_user.id, action=AuditAction.STATUS_CHANGE, entity_type="Complaint",
        entity_id=str(complaint.id), after_value={"status": "RESOLVED"}, ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(complaint)

    email_service.send_status_change_email(
        complaint=complaint, citizen_email=complaint.citizen.email, language=complaint.original_language.value,
        note="Please share your feedback once you've had a chance to check.", view_url=_citizen_view_url(complaint.id),
    )

    return complaint


@router.post("/{complaint_id}/resolution-proof", response_model=ComplaintImageResponse, status_code=status.HTTP_201_CREATED)
def upload_resolution_proof(
    complaint_id: uuid.UUID,
    proof: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_officer),
):
    complaint = _get_complaint_or_404(db, complaint_id)
    _assert_can_view(complaint, current_user)

    relative_path, _original, _size = validate_and_save_image(proof, subfolder="resolutions")
    complaint.resolution_proof_path = relative_path
    db.commit()
    return ComplaintImageResponse(id=complaint.id, file_path=relative_path, original_filename=proof.filename or "proof")


@router.post("/{complaint_id}/feedback", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    complaint_id: uuid.UUID,
    payload: FeedbackCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_citizen),
):
    complaint = _get_complaint_or_404(db, complaint_id)
    if complaint.citizen_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only give feedback on your own complaints")
    if complaint.status != ComplaintStatus.RESOLVED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Feedback can only be submitted after a complaint is resolved")
    if complaint.feedback is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Feedback has already been submitted for this complaint")

    feedback = Feedback(complaint_id=complaint.id, citizen_id=current_user.id, rating=payload.rating, comment=payload.comment)
    db.add(feedback)
    db.commit()
    return {"success": True, "message": "Thank you for your feedback"}
