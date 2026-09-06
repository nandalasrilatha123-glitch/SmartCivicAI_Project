import datetime as dt
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.enums import ComplaintStatus
from app.models.complaint import Complaint, ComplaintStatusHistory

_MODULE_PREFIX = {
    "GOVERNMENT_SCHOOLS": "SCH",
    "AGRICULTURE": "AGR",
    "HEALTHCARE": "HLT",
    "TRAFFIC": "TRF",
}

# Statuses a complaint may legally move to from a given current status.
# ESCALATED and REQUIRES_ADMIN_REVIEW can be reached from almost anywhere
# (an officer/system can escalate or flag for review at any point);
# RESOLVED/REJECTED are terminal but can still be reopened by an admin
# back to IN_PROGRESS if a citizen disputes the resolution.
_ALLOWED_TRANSITIONS: dict[ComplaintStatus, set[ComplaintStatus]] = {
    ComplaintStatus.NEW: {ComplaintStatus.PENDING, ComplaintStatus.REQUIRES_ADMIN_REVIEW, ComplaintStatus.REJECTED},
    ComplaintStatus.REQUIRES_ADMIN_REVIEW: {ComplaintStatus.PENDING, ComplaintStatus.ASSIGNED, ComplaintStatus.REJECTED},
    ComplaintStatus.PENDING: {ComplaintStatus.ASSIGNED, ComplaintStatus.ESCALATED, ComplaintStatus.REJECTED},
    ComplaintStatus.ASSIGNED: {ComplaintStatus.IN_PROGRESS, ComplaintStatus.ESCALATED, ComplaintStatus.REJECTED},
    ComplaintStatus.IN_PROGRESS: {ComplaintStatus.RESOLVED, ComplaintStatus.ESCALATED, ComplaintStatus.REJECTED},
    ComplaintStatus.ESCALATED: {ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED},
    ComplaintStatus.RESOLVED: {ComplaintStatus.IN_PROGRESS},
    ComplaintStatus.REJECTED: set(),
}


def generate_complaint_number(db: Session, module_code: str) -> str:
    year = dt.date.today().year
    prefix = _MODULE_PREFIX.get(module_code, "GEN")
    count_this_year = (
        db.query(func.count(Complaint.id))
        .filter(Complaint.complaint_number.like(f"{prefix}-{year}-%"))
        .scalar()
        or 0
    )
    sequence = count_this_year + 1
    candidate = f"{prefix}-{year}-{sequence:06d}"
    # Guard against a race on the sequence number (unlikely in demo use, but cheap to check)
    while db.query(Complaint.id).filter(Complaint.complaint_number == candidate).first() is not None:
        sequence += 1
        candidate = f"{prefix}-{year}-{sequence:06d}"
    return candidate


def is_transition_allowed(current: ComplaintStatus, target: ComplaintStatus) -> bool:
    if current == target:
        return True
    return target in _ALLOWED_TRANSITIONS.get(current, set())


def change_status(
    db: Session,
    complaint: Complaint,
    new_status: ComplaintStatus,
    changed_by_id: uuid.UUID | None,
    note: str | None = None,
) -> ComplaintStatusHistory:
    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        changed_by_id=changed_by_id,
        from_status=complaint.status,
        to_status=new_status,
        note=note,
    )
    db.add(history)
    complaint.status = new_status
    db.flush()
    return history
