import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus
from app.repositories.department_repository import DepartmentRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: Session):
        self.repo = ProjectRepository(db)
        self.department_repo = DepartmentRepository(db)

    def list_projects(self, status_: ProjectStatus | None = None) -> list[Project]:
        return self.repo.list_all(status=status_)

    def get_project(self, project_id: uuid.UUID) -> Project:
        project = self.repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    def create_project(self, payload: ProjectCreate) -> Project:
        if self.department_repo.get_by_id(payload.department_id) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department does not exist")
        project = Project(project_code=self.repo.next_project_code(), **payload.model_dump())
        return self.repo.create(project)

    def update_project(self, project_id: uuid.UUID, payload: ProjectUpdate) -> Project:
        project = self.get_project(project_id)
        data = payload.model_dump(exclude_unset=True)
        if data.get("department_id") and self.department_repo.get_by_id(data["department_id"]) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department does not exist")
        for field, value in data.items():
            setattr(project, field, value)
        return self.repo.update(project)
