import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.employee_skill import EmployeeSkill


class EmployeeSkillRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_employee(self, employee_id: uuid.UUID) -> list[EmployeeSkill]:
        return (
            self.db.query(EmployeeSkill)
            .options(joinedload(EmployeeSkill.skill))
            .filter(EmployeeSkill.employee_id == employee_id)
            .all()
        )

    def get(self, employee_id: uuid.UUID, skill_id: uuid.UUID) -> EmployeeSkill | None:
        return (
            self.db.query(EmployeeSkill)
            .filter(EmployeeSkill.employee_id == employee_id, EmployeeSkill.skill_id == skill_id)
            .first()
        )

    def create(self, employee_skill: EmployeeSkill) -> EmployeeSkill:
        self.db.add(employee_skill)
        self.db.commit()
        self.db.refresh(employee_skill)
        return employee_skill

    def update(self, employee_skill: EmployeeSkill) -> EmployeeSkill:
        self.db.commit()
        self.db.refresh(employee_skill)
        return employee_skill

    def delete(self, employee_skill: EmployeeSkill) -> None:
        self.db.delete(employee_skill)
        self.db.commit()
