import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.employee_project import EmployeeProject


class EmployeeProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_employee(self, employee_id: uuid.UUID) -> list[EmployeeProject]:
        return (
            self.db.query(EmployeeProject)
            .options(joinedload(EmployeeProject.project))
            .filter(EmployeeProject.employee_id == employee_id)
            .all()
        )

    def list_for_project(self, project_id: uuid.UUID) -> list[EmployeeProject]:
        return (
            self.db.query(EmployeeProject)
            .options(joinedload(EmployeeProject.employee))
            .filter(EmployeeProject.project_id == project_id)
            .all()
        )

    def get(self, employee_id: uuid.UUID, project_id: uuid.UUID) -> EmployeeProject | None:
        return (
            self.db.query(EmployeeProject)
            .filter(EmployeeProject.employee_id == employee_id, EmployeeProject.project_id == project_id)
            .first()
        )

    def create(self, employee_project: EmployeeProject) -> EmployeeProject:
        self.db.add(employee_project)
        self.db.commit()
        self.db.refresh(employee_project)
        return employee_project
