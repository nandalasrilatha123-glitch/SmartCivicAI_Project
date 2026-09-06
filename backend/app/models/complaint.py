import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ComplaintStatus, LanguageCode, ModuleCode, PriorityLevel
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Complaint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "complaints"

    complaint_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)  # e.g. SCA-2026-000123

    citizen_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    module: Mapped[ModuleCode] = mapped_column(Enum(ModuleCode, name="complaint_module_code"), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)

    # --- Multilingual complaint text (original text is NEVER overwritten) ---
    original_language: Mapped[LanguageCode] = mapped_column(
        Enum(LanguageCode, name="complaint_language_code", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
    )
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    translated_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # normalized English translation
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI-generated summary

    # --- Location (primary, denormalized for fast dashboard/map queries) ---
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # --- Routing / workflow ---
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    assigned_officer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    priority: Mapped[PriorityLevel] = mapped_column(Enum(PriorityLevel, name="priority_level"), nullable=False, default=PriorityLevel.MEDIUM)
    status: Mapped[ComplaintStatus] = mapped_column(Enum(ComplaintStatus, name="complaint_status"), nullable=False, default=ComplaintStatus.NEW)

    officer_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_proof_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_demo_data: Mapped[bool] = mapped_column(default=False, nullable=False)

    # --- Relationships ---
    citizen: Mapped["User"] = relationship(back_populates="complaints", foreign_keys=[citizen_id])
    assigned_officer: Mapped["User | None"] = relationship(foreign_keys=[assigned_officer_id])
    category: Mapped["Category | None"] = relationship(back_populates="complaints")
    department: Mapped["Department | None"] = relationship(back_populates="complaints")

    images: Mapped[list["ComplaintImage"]] = relationship(back_populates="complaint", cascade="all, delete-orphan")
    location_detail: Mapped["ComplaintLocation | None"] = relationship(
        back_populates="complaint", uselist=False, cascade="all, delete-orphan"
    )
    status_history: Mapped[list["ComplaintStatusHistory"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan", order_by="ComplaintStatusHistory.created_at"
    )
    ai_analysis: Mapped["AIAnalysis | None"] = relationship(back_populates="complaint", uselist=False, cascade="all, delete-orphan")
    feedback: Mapped["Feedback | None"] = relationship(back_populates="complaint", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Complaint {self.complaint_number} status={self.status}>"


class ComplaintImage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "complaint_images"

    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    complaint: Mapped["Complaint"] = relationship(back_populates="images")
    cv_analysis: Mapped["CVAnalysis | None"] = relationship(back_populates="image", uselist=False, cascade="all, delete-orphan")


class ComplaintLocation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Extended geo metadata beyond the denormalized lat/lng on Complaint --
    used for hotspot clustering (geohash) and reverse-geocoded address parts.
    """
    __tablename__ = "complaint_locations"

    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), unique=True, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geohash: Mapped[str | None] = mapped_column(String(12), index=True, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)

    complaint: Mapped["Complaint"] = relationship(back_populates="location_detail")


class ComplaintStatusHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "complaint_status_history"

    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    from_status: Mapped[ComplaintStatus | None] = mapped_column(Enum(ComplaintStatus, name="status_history_from"), nullable=True)
    to_status: Mapped[ComplaintStatus] = mapped_column(Enum(ComplaintStatus, name="status_history_to"), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    complaint: Mapped["Complaint"] = relationship(back_populates="status_history")
    changed_by: Mapped["User | None"] = relationship()
