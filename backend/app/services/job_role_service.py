from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.job_role import JobRole
from app.repositories.job_role_repository import JobRoleRepository
from app.schemas.job_role import JobRoleCreate, JobRoleUpdate


class JobRoleService:
    def __init__(self, db: Session):
        self.repo = JobRoleRepository(db)

    def list_job_roles(self) -> list[JobRole]:
        return self.repo.list_all()

    def get_job_role(self, job_role_id) -> JobRole:
        job_role = self.repo.get_by_id(job_role_id)
        if job_role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job role not found")
        return job_role

    def create_job_role(self, payload: JobRoleCreate) -> JobRole:
        if self.repo.get_by_title(payload.title):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job role title already exists")
        return self.repo.create(JobRole(**payload.model_dump()))

    def update_job_role(self, job_role_id, payload: JobRoleUpdate) -> JobRole:
        job_role = self.get_job_role(job_role_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(job_role, field, value)
        return self.repo.update(job_role)
