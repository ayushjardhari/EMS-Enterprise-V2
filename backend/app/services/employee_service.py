import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.employee import AvailabilityStatus, Employee, EmploymentStatus
from app.repositories.department_repository import DepartmentRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.job_role_repository import JobRoleRepository
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    def __init__(self, db: Session):
        self.repo = EmployeeRepository(db)
        self.department_repo = DepartmentRepository(db)
        self.job_role_repo = JobRoleRepository(db)

    def search_employees(
        self,
        *,
        search: str | None = None,
        department_id: uuid.UUID | None = None,
        job_role_id: uuid.UUID | None = None,
        employment_status: EmploymentStatus | None = None,
        availability_status: AvailabilityStatus | None = None,
        page: int = 1,
        limit: int = 25,
    ):
        return self.repo.search(
            search=search,
            department_id=department_id,
            job_role_id=job_role_id,
            employment_status=employment_status,
            availability_status=availability_status,
            page=page,
            limit=limit,
        )

    def get_employee(self, employee_id: uuid.UUID) -> Employee:
        employee = self.repo.get_by_id(employee_id)
        if employee is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        return employee

    def get_employee_profile(self, employee_id: uuid.UUID) -> Employee:
        employee = self.repo.get_profile_by_id(employee_id)
        if employee is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        return employee

    def _validate_references(self, department_id: uuid.UUID | None, job_role_id: uuid.UUID | None) -> None:
        if department_id and self.department_repo.get_by_id(department_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department does not exist")
        if job_role_id and self.job_role_repo.get_by_id(job_role_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job role does not exist")

    def create_employee(self, payload: EmployeeCreate) -> Employee:
        self._validate_references(payload.department_id, payload.job_role_id)
        if self.repo.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An employee with this email already exists")

        employee = Employee(employee_code=self.repo.next_employee_code(), **payload.model_dump())
        return self.repo.create(employee)

    def update_employee(self, employee_id: uuid.UUID, payload: EmployeeUpdate) -> Employee:
        employee = self.get_employee(employee_id)
        data = payload.model_dump(exclude_unset=True)
        self._validate_references(data.get("department_id"), data.get("job_role_id"))
        for field, value in data.items():
            setattr(employee, field, value)
        return self.repo.update(employee)

    def set_employment_status(self, employee_id: uuid.UUID, employment_status: EmploymentStatus) -> Employee:
        employee = self.get_employee(employee_id)
        employee.employment_status = employment_status
        return self.repo.update(employee)
