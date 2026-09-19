import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.employee_project import EmployeeProject
from app.repositories.employee_project_repository import EmployeeProjectRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.employee_project import EmployeeProjectCreate


class EmployeeProjectService:
    def __init__(self, db: Session):
        self.repo = EmployeeProjectRepository(db)
        self.employee_repo = EmployeeRepository(db)
        self.project_repo = ProjectRepository(db)

    def list_for_employee(self, employee_id: uuid.UUID) -> list[EmployeeProject]:
        if self.employee_repo.get_by_id(employee_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        return self.repo.list_for_employee(employee_id)

    def add_project(self, employee_id: uuid.UUID, payload: EmployeeProjectCreate) -> EmployeeProject:
        if self.employee_repo.get_by_id(employee_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        if self.project_repo.get_by_id(payload.project_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project does not exist")
        if self.repo.get(employee_id, payload.project_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee is already on this project")

        employee_project = EmployeeProject(employee_id=employee_id, **payload.model_dump())
        return self.repo.create(employee_project)
