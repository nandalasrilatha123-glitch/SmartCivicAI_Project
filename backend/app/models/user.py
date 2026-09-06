import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import LanguageCode, UserRole
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.CITIZEN)
    preferred_language: Mapped[LanguageCode] = mapped_column(
        Enum(LanguageCode, name="language_code", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
        default=LanguageCode.EN,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Only relevant when role == OFFICER
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    department: Mapped["Department"] = relationship(back_populates="officers", foreign_keys=[department_id])

    complaints: Mapped[list["Complaint"]] = relationship(back_populates="citizen", foreign_keys="Complaint.citizen_id")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="actor")

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"
