import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.employee import AvailabilityStatus, Employee, EmploymentStatus


class EmployeeRepository:
    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        return self.db.query(Employee).options(
            joinedload(Employee.department), joinedload(Employee.job_role)
        )

    def search(
        self,
        *,
        search: str | None,
        department_id: uuid.UUID | None,
        job_role_id: uuid.UUID | None,
        employment_status: EmploymentStatus | None,
        availability_status: AvailabilityStatus | None,
        page: int,
        limit: int,
    ) -> tuple[list[Employee], int]:
        query = self._base_query()

        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(Employee.full_name.ilike(like), Employee.email.ilike(like), Employee.employee_code.ilike(like))
            )
        if department_id:
            query = query.filter(Employee.department_id == department_id)
        if job_role_id:
            query = query.filter(Employee.job_role_id == job_role_id)
        if employment_status:
            query = query.filter(Employee.employment_status == employment_status)
        if availability_status:
            query = query.filter(Employee.availability_status == availability_status)

        total = query.count()
        items = query.order_by(Employee.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        return items, total

    def get_by_id(self, employee_id: uuid.UUID) -> Employee | None:
        return self._base_query().filter(Employee.id == employee_id).first()

    def get_profile_by_id(self, employee_id: uuid.UUID) -> Employee | None:
        return (
            self.db.query(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.job_role),
                selectinload(Employee.skills),
                selectinload(Employee.projects),
            )
            .filter(Employee.id == employee_id)
            .first()
        )

    def get_by_email(self, email: str) -> Employee | None:
        return self.db.query(Employee).filter(Employee.email == email).first()

    def count_by_employment_status(self, status_: EmploymentStatus) -> int:
        return self.db.query(Employee).filter(Employee.employment_status == status_).count()

    def count_by_availability_status(self, status_: AvailabilityStatus) -> int:
        return self.db.query(Employee).filter(Employee.availability_status == status_).count()

    def count_all(self) -> int:
        return self.db.query(Employee).count()

    def recent(self, limit: int = 5) -> list[Employee]:
        return self._base_query().order_by(Employee.created_at.desc()).limit(limit).all()

    def create(self, employee: Employee) -> Employee:
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def update(self, employee: Employee) -> Employee:
        self.db.commit()
        self.db.refresh(employee)
        return employee

    def next_employee_code(self) -> str:
        count = self.count_all()
        return f"EMP-{count + 1:05d}"
