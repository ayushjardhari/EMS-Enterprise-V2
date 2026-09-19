import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.schemas.attendance import AttendanceStatus
from app.models.user import User, UserRole
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.employee_repository import EmployeeRepository


class AttendanceService:
    def __init__(self, db: Session):
        self.repo = AttendanceRepository(db)
        self.employee_repo = EmployeeRepository(db)
        self.db = db

    @staticmethod
    def _hours(check_in: datetime | None, check_out: datetime | None) -> Decimal | None:
        if not check_in or not check_out:
            return None
        seconds = (check_out - check_in).total_seconds()
        return Decimal(str(round(seconds / 3600, 2)))

    def list_for_user(self, user: User):
        if user.user_role == UserRole.EMPLOYEE:
            if not user.employee_id:
                return []
            return self.repo.list_for_employee(user.employee_id)
        return self.repo.list_all()

    def list_for_employee(self, employee_id: uuid.UUID, user: User):
        if user.user_role == UserRole.EMPLOYEE and user.employee_id != employee_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own attendance")
        if self.employee_repo.get_by_id(employee_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        return self.repo.list_for_employee(employee_id)

    def check_in(self, user: User):
        if not user.employee_id:
            raise HTTPException(status_code=400, detail="Your account is not linked to an employee")
        today = date.today()
        attendance = self.repo.get_for_employee_date(user.employee_id, today)
        if attendance and attendance.check_in:
            raise HTTPException(status_code=409, detail="You have already checked in today")
        now = datetime.now(timezone.utc)
        if attendance is None:
            attendance = Attendance(employee_id=user.employee_id, attendance_date=today, check_in=now, status="PRESENT")
            self.db.add(attendance)
        else:
            attendance.check_in = now
            attendance.status = "PRESENT"
        self.db.commit()
        self.db.refresh(attendance)
        return attendance

    def check_out(self, user: User):
        if not user.employee_id:
            raise HTTPException(status_code=400, detail="Your account is not linked to an employee")
        attendance = self.repo.get_for_employee_date(user.employee_id, date.today())
        if not attendance or not attendance.check_in:
            raise HTTPException(status_code=400, detail="You must check in before checking out")
        if attendance.check_out:
            raise HTTPException(status_code=409, detail="You have already checked out today")
        attendance.check_out = datetime.now(timezone.utc)
        attendance.work_hours = self._hours(attendance.check_in, attendance.check_out)
        self.db.commit()
        self.db.refresh(attendance)
        return attendance

    def create(self, employee_id: uuid.UUID, attendance_date: date | None, status_: AttendanceStatus, notes: str | None):
        attendance_date = attendance_date or date.today()
        if self.employee_repo.get_by_id(employee_id) is None:
            raise HTTPException(status_code=404, detail="Employee not found")
        if self.repo.get_for_employee_date(employee_id, attendance_date):
            raise HTTPException(status_code=409, detail="Attendance already exists for this date")
        return self.repo.create(Attendance(employee_id=employee_id, attendance_date=attendance_date, status=status_.value, notes=notes))
