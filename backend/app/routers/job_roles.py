import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.user import UserRole
from app.schemas.job_role import JobRoleCreate, JobRoleOut, JobRoleUpdate
from app.services.job_role_service import JobRoleService

router = APIRouter(prefix="/api/v1/roles", tags=["job-roles"])


@router.get("", response_model=list[JobRoleOut])
def list_job_roles(db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return JobRoleService(db).list_job_roles()


@router.post("", response_model=JobRoleOut, status_code=status.HTTP_201_CREATED)
def create_job_role(
    payload: JobRoleCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
):
    return JobRoleService(db).create_job_role(payload)


@router.put("/{job_role_id}", response_model=JobRoleOut)
def update_job_role(
    job_role_id: uuid.UUID,
    payload: JobRoleUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
):
    return JobRoleService(db).update_job_role(job_role_id, payload)
