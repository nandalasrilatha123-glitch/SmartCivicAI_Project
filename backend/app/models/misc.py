import uuid

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AuditAction, ModuleCode, NotificationType
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    complaint_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=True)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType, name="notification_type"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="notifications")


class Feedback(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "feedback"

    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), unique=True, nullable=False)
    citizen_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    complaint: Mapped["Complaint"] = relationship(back_populates="feedback")


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, name="audit_action"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "Complaint", "User"
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    before_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    actor: Mapped["User | None"] = relationship(back_populates="audit_logs")


class PredictionResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Stores output of the predictive-analytics pipeline (volume forecasts,
    hotspot predictions). `is_demo_data` must be True whenever the model
    was trained on seeded/synthetic history rather than real complaints.
    """
    __tablename__ = "prediction_results"

    prediction_type: Mapped[str] = mapped_column(String(50), nullable=False)  # volume_forecast | hotspot | priority_trend
    module: Mapped[ModuleCode | None] = mapped_column(Enum(ModuleCode, name="prediction_module_code"), nullable=True)
    target_date: Mapped[str | None] = mapped_column(String(10), nullable=True)  # ISO date the prediction is FOR
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)  # forecast series / hotspot coordinates etc.
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "xgboost_v1", "sklearn_linreg", "demo_heuristic"
    model_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # e.g. {"mae": 2.1, "r2": 0.84}
    is_demo_data: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
