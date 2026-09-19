import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.project import ProjectStatus
from app.models.user import UserRole
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(status_filter: ProjectStatus | None = None, db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return ProjectService(db).list_projects(status_=status_filter)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return ProjectService(db).get_project(project_id)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.HR, UserRole.MANAGER)),
):
    return ProjectService(db).create_project(payload)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.HR, UserRole.MANAGER)),
):
    return ProjectService(db).update_project(project_id, payload)
