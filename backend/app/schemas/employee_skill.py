import uuid

from pydantic import BaseModel, Field

from app.models.employee_skill import ProficiencyLevel
from app.schemas.skill import SkillOut


class EmployeeSkillCreate(BaseModel):
    skill_id: uuid.UUID
    proficiency_level: ProficiencyLevel
    years_of_experience: float = Field(ge=0, le=60)


class EmployeeSkillUpdate(BaseModel):
    proficiency_level: ProficiencyLevel | None = None
    years_of_experience: float | None = Field(default=None, ge=0, le=60)


class EmployeeSkillOut(BaseModel):
    id: uuid.UUID
    skill: SkillOut
    proficiency_level: ProficiencyLevel
    years_of_experience: float

    class Config:
        from_attributes = True
