import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.employee import AvailabilityStatus, EmploymentStatus
from app.schemas.department import DepartmentOut
from app.schemas.employee_project import EmployeeProjectOut
from app.schemas.employee_skill import EmployeeSkillOut
from app.schemas.job_role import JobRoleOut


class EmployeeBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=150)
    profile_info: str | None = Field(default=None, max_length=2000)
    department_id: uuid.UUID
    job_role_id: uuid.UUID
    joining_date: date
    availability_status: AvailabilityStatus = AvailabilityStatus.AVAILABLE


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    location: str | None = Field(default=None, max_length=150)
    profile_info: str | None = Field(default=None, max_length=2000)
    department_id: uuid.UUID | None = None
    job_role_id: uuid.UUID | None = None
    joining_date: date | None = None
    availability_status: AvailabilityStatus | None = None


class EmployeeStatusUpdate(BaseModel):
    employment_status: EmploymentStatus


class EmployeeListItem(BaseModel):
    """Slim shape for list/table views — avoids shipping nested skills/projects for every row."""
    id: uuid.UUID
    employee_code: str
    full_name: str
    email: EmailStr
    department: DepartmentOut
    job_role: JobRoleOut
    employment_status: EmploymentStatus
    availability_status: AvailabilityStatus
    joining_date: date

    class Config:
        from_attributes = True


class EmployeeOut(EmployeeListItem):
    phone: str | None
    location: str | None
    profile_info: str | None
    created_at: datetime
    updated_at: datetime


class EmployeeProfileOut(EmployeeOut):
    """Full profile view: basic info + skills + projects, as used on the Employee Profile page."""
    skills: list[EmployeeSkillOut] = []
    projects: list[EmployeeProjectOut] = []
