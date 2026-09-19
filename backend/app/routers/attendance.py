import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.attendance import AttendanceCreate, AttendanceOut
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/api/v1/attendance", tags=["attendance"])


@router.get("", response_model=list[AttendanceOut])
def list_attendance(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return AttendanceService(db).list_for_user(user)


@router.get("/employee/{employee_id}", response_model=list[AttendanceOut])
def employee_attendance(employee_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return AttendanceService(db).list_for_employee(employee_id, user)


@router.post("/check-in", response_model=AttendanceOut)
def check_in(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return AttendanceService(db).check_in(user)


@router.post("/check-out", response_model=AttendanceOut)
def check_out(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return AttendanceService(db).check_out(user)


@router.post("", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
def create_attendance(
    data: AttendanceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.HR, UserRole.MANAGER)),
):
    return AttendanceService(db).create(data.employee_id, data.attendance_date, data.status, data.notes)
