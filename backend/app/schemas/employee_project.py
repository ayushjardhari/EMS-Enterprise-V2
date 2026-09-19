import uuid
from datetime import date

from pydantic import BaseModel, Field

from app.schemas.project import ProjectOut


class EmployeeProjectCreate(BaseModel):
    project_id: uuid.UUID
    project_role: str = Field(min_length=1, max_length=150)
    start_date: date
    end_date: date | None = None


class EmployeeProjectOut(BaseModel):
    id: uuid.UUID
    project: ProjectOut
    project_role: str
    start_date: date
    end_date: date | None

    class Config:
        from_attributes = True
