import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.employee_skill import EmployeeSkill
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.employee_skill_repository import EmployeeSkillRepository
from app.repositories.skill_repository import SkillRepository
from app.schemas.employee_skill import EmployeeSkillCreate, EmployeeSkillUpdate


class EmployeeSkillService:
    def __init__(self, db: Session):
        self.repo = EmployeeSkillRepository(db)
        self.employee_repo = EmployeeRepository(db)
        self.skill_repo = SkillRepository(db)

    def list_skills(self, employee_id: uuid.UUID) -> list[EmployeeSkill]:
        if self.employee_repo.get_by_id(employee_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        return self.repo.list_for_employee(employee_id)

    def add_skill(self, employee_id: uuid.UUID, payload: EmployeeSkillCreate) -> EmployeeSkill:
        if self.employee_repo.get_by_id(employee_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        if self.skill_repo.get_by_id(payload.skill_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Skill does not exist")
        if self.repo.get(employee_id, payload.skill_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee already has this skill")

        employee_skill = EmployeeSkill(employee_id=employee_id, **payload.model_dump())
        return self.repo.create(employee_skill)

    def update_skill(self, employee_id: uuid.UUID, skill_id: uuid.UUID, payload: EmployeeSkillUpdate) -> EmployeeSkill:
        employee_skill = self.repo.get(employee_id, skill_id)
        if employee_skill is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee does not have this skill")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(employee_skill, field, value)
        return self.repo.update(employee_skill)

    def remove_skill(self, employee_id: uuid.UUID, skill_id: uuid.UUID) -> None:
        employee_skill = self.repo.get(employee_id, skill_id)
        if employee_skill is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee does not have this skill")
        self.repo.delete(employee_skill)
