import uuid

from sqlalchemy.orm import Session

from app.models.department import Department


class DepartmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self, include_inactive: bool = False) -> list[Department]:
        query = self.db.query(Department)
        if not include_inactive:
            query = query.filter(Department.is_active.is_(True))
        return query.order_by(Department.name).all()

    def get_by_id(self, department_id: uuid.UUID) -> Department | None:
        return self.db.get(Department, department_id)

    def get_by_name(self, name: str) -> Department | None:
        return self.db.query(Department).filter(Department.name == name).first()

    def create(self, department: Department) -> Department:
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        return department

    def update(self, department: Department) -> Department:
        self.db.commit()
        self.db.refresh(department)
        return department
