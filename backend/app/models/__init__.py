"""
Import every model module here so that Base.metadata is fully populated
before Alembic autogenerate or Base.metadata.create_all() runs.
"""
from app.models.ai import AIAnalysis, AIClassification, AIPriority, AIRouting, CVAnalysis  # noqa: F401
from app.models.complaint import (  # noqa: F401
    Complaint,
    ComplaintImage,
    ComplaintLocation,
    ComplaintStatusHistory,
)
from app.models.department import Department  # noqa: F401
from app.models.misc import AuditLog, Feedback, Notification, PredictionResult  # noqa: F401
from app.models.module import Category, Module  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = [
    "User",
    "Department",
    "Module",
    "Category",
    "Complaint",
    "ComplaintImage",
    "ComplaintLocation",
    "ComplaintStatusHistory",
    "AIAnalysis",
    "AIClassification",
    "AIPriority",
    "AIRouting",
    "CVAnalysis",
    "Notification",
    "Feedback",
    "AuditLog",
    "PredictionResult",
]
