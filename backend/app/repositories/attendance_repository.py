import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance


class AttendanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_for_employee_date(self, employee_id: uuid.UUID, attendance_date: date):
        return self.db.scalar(
            select(Attendance).where(
                Attendance.employee_id == employee_id,
                Attendance.attendance_date == attendance_date,
            )
        )

    def list_for_employee(self, employee_id: uuid.UUID):
        return list(
            self.db.scalars(
                select(Attendance)
                .where(Attendance.employee_id == employee_id)
                .order_by(Attendance.attendance_date.desc())
            ).all()
        )

    def list_all(self):
        return list(self.db.scalars(select(Attendance).order_by(Attendance.attendance_date.desc())).all())

    def create(self, attendance: Attendance):
        self.db.add(attendance)
        self.db.commit()
        self.db.refresh(attendance)
        return attendance
