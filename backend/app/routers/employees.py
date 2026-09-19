import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_roles
from app.models.employee import AvailabilityStatus, EmploymentStatus
from app.models.user import UserRole
from app.schemas.common import Page
from app.schemas.document import DocumentOut
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeListItem,
    EmployeeProfileOut,
    EmployeeStatusUpdate,
    EmployeeUpdate,
)
from app.schemas.employee_project import EmployeeProjectCreate, EmployeeProjectOut
from app.schemas.employee_skill import EmployeeSkillCreate, EmployeeSkillOut, EmployeeSkillUpdate
from app.services.document_service import DocumentService
from app.services.employee_project_service import EmployeeProjectService
from app.services.employee_service import EmployeeService
from app.services.employee_skill_service import EmployeeSkillService

router = APIRouter(prefix="/api/v1/employees", tags=["employees"])

HR_ADMIN = require_roles(UserRole.ADMIN, UserRole.HR)


@router.get("", response_model=Page[EmployeeListItem])
def list_employees(
    search: str | None = None,
    department_id: uuid.UUID | None = None,
    job_role_id: uuid.UUID | None = None,
    employment_status: EmploymentStatus | None = None,
    availability_status: AvailabilityStatus | None = None,
    page: int = 1,
    limit: int = 25,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    items, total = EmployeeService(db).search_employees(
        search=search,
        department_id=department_id,
        job_role_id=job_role_id,
        employment_status=employment_status,
        availability_status=availability_status,
        page=page,
        limit=limit,
    )
    return Page(items=items, total=total, page=page, limit=limit)


@router.get("/{employee_id}", response_model=EmployeeProfileOut)
def get_employee(employee_id: uuid.UUID, db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return EmployeeService(db).get_employee_profile(employee_id)


@router.post("", response_model=EmployeeProfileOut, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db), _: object = Depends(HR_ADMIN)):
    employee = EmployeeService(db).create_employee(payload)
    return EmployeeService(db).get_employee_profile(employee.id)


@router.put("/{employee_id}", response_model=EmployeeProfileOut)
def update_employee(
    employee_id: uuid.UUID, payload: EmployeeUpdate, db: Session = Depends(get_db), _: object = Depends(HR_ADMIN)
):
    EmployeeService(db).update_employee(employee_id, payload)
    return EmployeeService(db).get_employee_profile(employee_id)


@router.patch("/{employee_id}/status", response_model=EmployeeProfileOut)
def update_employee_status(
    employee_id: uuid.UUID, payload: EmployeeStatusUpdate, db: Session = Depends(get_db), _: object = Depends(HR_ADMIN)
):
    EmployeeService(db).set_employment_status(employee_id, payload.employment_status)
    return EmployeeService(db).get_employee_profile(employee_id)


# --- Employee skills ---

@router.get("/{employee_id}/skills", response_model=list[EmployeeSkillOut])
def list_employee_skills(employee_id: uuid.UUID, db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return EmployeeSkillService(db).list_skills(employee_id)


@router.post("/{employee_id}/skills", response_model=EmployeeSkillOut, status_code=status.HTTP_201_CREATED)
def add_employee_skill(
    employee_id: uuid.UUID, payload: EmployeeSkillCreate, db: Session = Depends(get_db), _: object = Depends(HR_ADMIN)
):
    return EmployeeSkillService(db).add_skill(employee_id, payload)


@router.put("/{employee_id}/skills/{skill_id}", response_model=EmployeeSkillOut)
def update_employee_skill(
    employee_id: uuid.UUID,
    skill_id: uuid.UUID,
    payload: EmployeeSkillUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(HR_ADMIN),
):
    return EmployeeSkillService(db).update_skill(employee_id, skill_id, payload)


@router.delete("/{employee_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee_skill(
    employee_id: uuid.UUID, skill_id: uuid.UUID, db: Session = Depends(get_db), _: object = Depends(HR_ADMIN)
):
    EmployeeSkillService(db).remove_skill(employee_id, skill_id)


# --- Employee projects ---

@router.get("/{employee_id}/projects", response_model=list[EmployeeProjectOut])
def list_employee_projects(employee_id: uuid.UUID, db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return EmployeeProjectService(db).list_for_employee(employee_id)


@router.post("/{employee_id}/projects", response_model=EmployeeProjectOut, status_code=status.HTTP_201_CREATED)
def add_employee_project(
    employee_id: uuid.UUID,
    payload: EmployeeProjectCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.HR, UserRole.MANAGER)),
):
    return EmployeeProjectService(db).add_project(employee_id, payload)


# --- Employee documents ---

@router.get("/{employee_id}/documents", response_model=list[DocumentOut])
def list_employee_documents(employee_id: uuid.UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return DocumentService(db).list_documents(employee_id, user)


@router.post("/{employee_id}/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_employee_document(
    employee_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return DocumentService(db).upload_document(employee_id, file, user)


# --- Employee 360: Leave ---

@router.get("/{employee_id}/leave")
def get_employee_leave(
    employee_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from datetime import date

    from fastapi import HTTPException
    from sqlalchemy import select

    from app.models.employee import Employee
    from app.models.hr import LeaveBalance, LeaveRequest, LeaveType

    employee = db.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    # Employees may only see their own leave information.
    if (
        current_user.user_role == UserRole.EMPLOYEE
        and current_user.employee_id != employee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this employee's leave information",
        )

    year = date.today().year

    balances = db.execute(
        select(LeaveBalance, LeaveType)
        .join(
            LeaveType,
            LeaveType.id == LeaveBalance.leave_type_id,
        )
        .where(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.year == year,
        )
        .order_by(LeaveType.name)
    ).all()

    requests = db.execute(
        select(LeaveRequest, LeaveType)
        .join(
            LeaveType,
            LeaveType.id == LeaveRequest.leave_type_id,
        )
        .where(
            LeaveRequest.employee_id == employee_id,
        )
        .order_by(LeaveRequest.created_at.desc())
    ).all()

    return {
        "year": year,
        "balances": [
            {
                "id": str(balance.id),
                "leave_type_id": str(leave_type.id),
                "type": leave_type.name,
                "allocated_days": float(balance.allocated_days),
                "used_days": float(balance.used_days),
                "remaining_days": max(
                    float(balance.allocated_days)
                    - float(balance.used_days),
                    0,
                ),
            }
            for balance, leave_type in balances
        ],
        "requests": [
            {
                "id": str(request.id),
                "type": leave_type.name,
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "days": float(request.days),
                "reason": request.reason,
                "status": request.status,
                "created_at": request.created_at,
            }
            for request, leave_type in requests
        ],
    }


# --- Employee 360: Payroll ---

@router.get("/{employee_id}/payroll")
def get_employee_payroll(
    employee_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from fastapi import HTTPException
    from sqlalchemy import select

    from app.models.employee import Employee
    from app.models.hr import PayrollRecord, PayrollRun, SalaryProfile

    employee = db.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    # HR/Admin can view employee payroll.
    # An employee can view only their own payroll.
    if (
        current_user.user_role not in (UserRole.ADMIN, UserRole.HR)
        and current_user.employee_id != employee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this employee's payroll",
        )

    salary = db.scalar(
        select(SalaryProfile).where(
            SalaryProfile.employee_id == employee_id
        )
    )

    payroll_rows = db.execute(
        select(PayrollRecord, PayrollRun)
        .join(
            PayrollRun,
            PayrollRun.id == PayrollRecord.payroll_run_id,
        )
        .where(
            PayrollRecord.employee_id == employee_id,
        )
        .order_by(PayrollRun.period.desc())
    ).all()

    return {
        "salary": (
            None
            if salary is None
            else {
                "basic_salary": float(salary.basic_salary),
                "housing_allowance": float(
                    salary.housing_allowance
                ),
                "transport_allowance": float(
                    salary.transport_allowance
                ),
                "other_allowance": float(
                    salary.other_allowance
                ),
                "effective_from": salary.effective_from.isoformat(),
            }
        ),
        "records": [
            {
                "id": str(record.id),
                "period": payroll_run.period,
                "basic": float(record.basic_salary),
                "allowances": float(record.allowances),
                "bonus": float(record.bonus),
                "deductions": float(record.deductions),
                "gross": float(record.gross_salary),
                "net": float(record.net_salary),
                "status": record.status,
            }
            for record, payroll_run in payroll_rows
        ],
    }


# --- Employee 360: Activity ---

@router.get("/{employee_id}/activity")
def get_employee_activity(
    employee_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from fastapi import HTTPException
    from sqlalchemy import select

    from app.models.employee import Employee
    from app.models.hr import AuditLog

    employee = db.get(Employee, employee_id)

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    if (
        current_user.user_role == UserRole.EMPLOYEE
        and current_user.employee_id != employee_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this employee's activity",
        )

    logs = db.scalars(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "EMPLOYEE",
            AuditLog.entity_id == str(employee_id),
        )
        .order_by(AuditLog.created_at.desc())
        .limit(50)
    ).all()

    return [
        {
            "id": str(log.id),
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "created_at": log.created_at,
        }
        for log in logs
    ]