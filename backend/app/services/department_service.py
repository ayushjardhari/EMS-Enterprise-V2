from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.department import Department
from app.repositories.department_repository import DepartmentRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class DepartmentService:
    def __init__(self, db: Session):
        self.repo = DepartmentRepository(db)

    def list_departments(self, include_inactive: bool = False) -> list[Department]:
        return self.repo.list_all(include_inactive=include_inactive)

    def get_department(self, department_id) -> Department:
        department = self.repo.get_by_id(department_id)
        if department is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
        return department

    def create_department(self, payload: DepartmentCreate) -> Department:
        if self.repo.get_by_name(payload.name):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department name already exists")
        department = Department(**payload.model_dump())
        return self.repo.create(department)

    def update_department(self, department_id, payload: DepartmentUpdate) -> Department:
        department = self.get_department(department_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(department, field, value)
        return self.repo.update(department)

    def deactivate_department(self, department_id) -> Department:
        department = self.get_department(department_id)
        department.is_active = False
        return self.repo.update(department)
