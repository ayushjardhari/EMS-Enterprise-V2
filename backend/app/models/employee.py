import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, func
from app.db.types import GUID as UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EmploymentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ON_LEAVE = "ON_LEAVE"


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    PARTIALLY_AVAILABLE = "PARTIALLY_AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Human-readable business key, separate from the internal surrogate PK above.
    employee_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)
    profile_info: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True)
    job_role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_roles.id"), nullable=False, index=True)

    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    employment_status: Mapped[EmploymentStatus] = mapped_column(
        Enum(EmploymentStatus, name="employment_status"), default=EmploymentStatus.ACTIVE, nullable=False, index=True
    )
    availability_status: Mapped[AvailabilityStatus] = mapped_column(
        Enum(AvailabilityStatus, name="availability_status"), default=AvailabilityStatus.AVAILABLE, nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    department: Mapped["Department"] = relationship(back_populates="employees")
    job_role: Mapped["JobRole"] = relationship(back_populates="employees")
    user: Mapped["User | None"] = relationship(back_populates="employee", uselist=False, foreign_keys="User.employee_id")
    skills: Mapped[list["EmployeeSkill"]] = relationship(back_populates="employee", cascade="all, delete-orphan")
    projects: Mapped[list["EmployeeProject"]] = relationship(back_populates="employee", cascade="all, delete-orphan")
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="employee", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="employee", cascade="all, delete-orphan")
