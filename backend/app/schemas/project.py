import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    project_name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    department_id: uuid.UUID
    status: ProjectStatus = ProjectStatus.PLANNED
    start_date: date
    end_date: date | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    department_id: uuid.UUID | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectOut(ProjectBase):
    id: uuid.UUID
    project_code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
