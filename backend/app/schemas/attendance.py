import uuid
from datetime import date, datetime
from decimal import Decimal

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    ON_LEAVE = "ON_LEAVE"
    HALF_DAY = "HALF_DAY"
    LATE = "LATE"
    WORK_FROM_HOME = "WORK_FROM_HOME"


class AttendanceCreate(BaseModel):
    employee_id: uuid.UUID
    attendance_date: date | None = None
    status: AttendanceStatus = AttendanceStatus.PRESENT
    notes: str | None = Field(default=None, max_length=500)


class AttendanceOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    attendance_date: date
    check_in: datetime | None
    check_out: datetime | None
    status: str
    work_hours: Decimal | None
    notes: str | None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("work_hours")
    def serialize_work_hours(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None
