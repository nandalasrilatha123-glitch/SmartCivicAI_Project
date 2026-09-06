import uuid

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ImageAnalysisStatus, ModuleCode, PriorityLevel
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AIAnalysis(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Parent record for one complaint's full multi-agent AI run. Individual
    agent outputs live in AIClassification / AIPriority / AIRouting so each
    stage's confidence and admin-override state can be tracked independently.
    """
    __tablename__ = "ai_analysis"

    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False, default="demo")  # demo | anthropic | openai
    detected_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    entities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # extracted entities (place names, dates, etc.)
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    citizen_response_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # auto-generated ack message
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    requires_admin_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    workflow_trace: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # ordered list of agent steps for audit/debug
    raw_error: Mapped[str | None] = mapped_column(Text, nullable=True)  # populated if a stage fell back to demo mode due to an error

    complaint: Mapped["Complaint"] = relationship(back_populates="ai_analysis")
    classification: Mapped["AIClassification | None"] = relationship(back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    priority_assessment: Mapped["AIPriority | None"] = relationship(back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    routing: Mapped["AIRouting | None"] = relationship(back_populates="analysis", uselist=False, cascade="all, delete-orphan")


class AIClassification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_classification"

    analysis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_analysis.id", ondelete="CASCADE"), unique=True, nullable=False)
    predicted_module: Mapped[ModuleCode] = mapped_column(Enum(ModuleCode, name="ai_predicted_module"), nullable=False)
    predicted_category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    module_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    category_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_overridden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overridden_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    analysis: Mapped["AIAnalysis"] = relationship(back_populates="classification")


class AIPriority(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_priority"

    analysis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_analysis.id", ondelete="CASCADE"), unique=True, nullable=False)
    predicted_priority: Mapped[PriorityLevel] = mapped_column(Enum(PriorityLevel, name="ai_predicted_priority"), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_overridden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overridden_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    analysis: Mapped["AIAnalysis"] = relationship(back_populates="priority_assessment")


class AIRouting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_routing"

    analysis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ai_analysis.id", ondelete="CASCADE"), unique=True, nullable=False)
    predicted_department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_overridden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overridden_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    analysis: Mapped["AIAnalysis"] = relationship(back_populates="routing")


class CVAnalysis(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Computer-vision result for one complaint image. Modular by design:
    `detected_objects` stores whatever class list the active model
    (demo heuristic or a real YOLOv8 .pt) produces, so new modules/classes
    can be added without a schema change.
    """
    __tablename__ = "cv_analysis"

    image_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaint_images.id", ondelete="CASCADE"), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(30), nullable=False, default="demo")  # demo | yolo
    detected_objects: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{label, confidence, bbox}]
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # max confidence across detections
    status: Mapped[ImageAnalysisStatus] = mapped_column(
        Enum(ImageAnalysisStatus, name="image_analysis_status"), nullable=False, default=ImageAnalysisStatus.NOT_ANALYZED
    )

    image: Mapped["ComplaintImage"] = relationship(back_populates="cv_analysis")
