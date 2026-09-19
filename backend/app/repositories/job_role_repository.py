import uuid

from sqlalchemy.orm import Session

from app.models.job_role import JobRole


class JobRoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[JobRole]:
        return self.db.query(JobRole).order_by(JobRole.title).all()

    def get_by_id(self, job_role_id: uuid.UUID) -> JobRole | None:
        return self.db.get(JobRole, job_role_id)

    def get_by_title(self, title: str) -> JobRole | None:
        return self.db.query(JobRole).filter(JobRole.title == title).first()

    def create(self, job_role: JobRole) -> JobRole:
        self.db.add(job_role)
        self.db.commit()
        self.db.refresh(job_role)
        return job_role

    def update(self, job_role: JobRole) -> JobRole:
        self.db.commit()
        self.db.refresh(job_role)
        return job_role
