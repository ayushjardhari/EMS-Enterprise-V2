import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.project import Project, ProjectStatus


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self, status: ProjectStatus | None = None) -> list[Project]:
        query = self.db.query(Project).options(joinedload(Project.department))
        if status:
            query = query.filter(Project.status == status)
        return query.order_by(Project.created_at.desc()).all()

    def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        return self.db.query(Project).options(joinedload(Project.department)).filter(Project.id == project_id).first()

    def count_active(self) -> int:
        return self.db.query(Project).filter(Project.status == ProjectStatus.ACTIVE).count()

    def count_all(self) -> int:
        return self.db.query(Project).count()

    def next_project_code(self) -> str:
        return f"PRJ-{self.count_all() + 1:05d}"

    def create(self, project: Project) -> Project:
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def update(self, project: Project) -> Project:
        self.db.commit()
        self.db.refresh(project)
        return project
