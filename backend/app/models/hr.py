import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.types import GUID as UUID
from app.db.base import Base

class LeaveType(Base):
    __tablename__ = 'leave_types'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    annual_days: Mapped[Decimal] = mapped_column(Numeric(5,1), nullable=False, default=12)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

class LeaveBalance(Base):
    __tablename__ = 'leave_balances'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    leave_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('leave_types.id', ondelete='CASCADE'), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    allocated_days: Mapped[Decimal] = mapped_column(Numeric(5,1), nullable=False)
    used_days: Mapped[Decimal] = mapped_column(Numeric(5,1), nullable=False, default=0)
    __table_args__ = (UniqueConstraint('employee_id','leave_type_id','year', name='uq_leave_balance'),)

class LeaveRequest(Base):
    __tablename__ = 'leave_requests'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    leave_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('leave_types.id'), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days: Mapped[Decimal] = mapped_column(Numeric(5,1), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='PENDING', index=True)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class SalaryProfile(Base):
    __tablename__ = 'salary_profiles'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), unique=True, nullable=False)
    basic_salary: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    housing_allowance: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False, default=0)
    transport_allowance: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False, default=0)
    other_allowance: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False, default=0)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)

class PayrollRun(Base):
    __tablename__ = 'payroll_runs'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period: Mapped[str] = mapped_column(String(7), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='DRAFT')
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class PayrollRecord(Base):
    __tablename__ = 'payroll_records'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payroll_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('payroll_runs.id', ondelete='CASCADE'), nullable=False)
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    basic_salary: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    allowances: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False, default=0)
    bonus: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False, default=0)
    deductions: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False, default=0)
    gross_salary: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    net_salary: Mapped[Decimal] = mapped_column(Numeric(12,2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='PENDING')
    __table_args__ = (UniqueConstraint('payroll_run_id','employee_id', name='uq_payroll_employee_run'),)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
