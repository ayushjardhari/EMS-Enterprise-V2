import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.user import UserRole
from app.schemas.department import DepartmentCreate, DepartmentOut, DepartmentUpdate
from app.services.department_service import DepartmentService

router = APIRouter(prefix="/api/v1/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentOut])
def list_departments(include_inactive: bool = False, db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return DepartmentService(db).list_departments(include_inactive=include_inactive)


@router.post("", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
):
    return DepartmentService(db).create_department(payload)


@router.put("/{department_id}", response_model=DepartmentOut)
def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
):
    return DepartmentService(db).update_department(department_id, payload)


@router.patch("/{department_id}/deactivate", response_model=DepartmentOut)
def deactivate_department(
    department_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.HR)),
):
    return DepartmentService(db).deactivate_department(department_id)
