import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from app.db.types import GUID as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JobRole(Base):
    """Job title, e.g. 'Backend Developer' — distinct from the auth UserRole enum."""
    __tablename__ = "job_roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    employees: Mapped[list["Employee"]] = relationship(back_populates="job_role")
