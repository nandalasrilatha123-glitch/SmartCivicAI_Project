import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ModuleCode
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Department(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Each department is tied to exactly one of the four modules and is the
    unit that complaints get routed to (e.g. "School Infrastructure Wing",
    "District Agriculture Office", "Primary Health Center Admin", "Traffic
    Police Division").
    """
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    module: Mapped[ModuleCode] = mapped_column(Enum(ModuleCode, name="module_code"), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    officers: Mapped[list["User"]] = relationship(back_populates="department", foreign_keys="User.department_id")
    complaints: Mapped[list["Complaint"]] = relationship(back_populates="department")
