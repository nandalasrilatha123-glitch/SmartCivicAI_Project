import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ModuleCode
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Module(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    The four fixed civic modules. Rows are seeded once; admin can rename
    display labels/icons but the underlying `code` enum stays fixed as
    required by the project spec (Schools / Agriculture / Healthcare / Traffic).
    """
    __tablename__ = "modules"

    code: Mapped[ModuleCode] = mapped_column(Enum(ModuleCode, name="module_code_unique"), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_te: Mapped[str] = mapped_column(String(100), nullable=False)
    name_hi: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    categories: Mapped[list["Category"]] = relationship(back_populates="module", cascade="all, delete-orphan")


class Category(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Admin-editable complaint categories, scoped to a module."""
    __tablename__ = "categories"

    module_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_te: Mapped[str] = mapped_column(String(100), nullable=False)
    name_hi: Mapped[str] = mapped_column(String(100), nullable=False)
    keywords: Mapped[str | None] = mapped_column(String(500), nullable=True)  # comma-separated, used by demo AI classifier
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    module: Mapped["Module"] = relationship(back_populates="categories")
    complaints: Mapped[list["Complaint"]] = relationship(back_populates="category")
