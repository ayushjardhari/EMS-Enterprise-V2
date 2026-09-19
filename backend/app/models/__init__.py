"""
Importing this package registers every model on Base.metadata — needed
for Alembic autogeneration and for Base.metadata.create_all() in tests.

This lives here (not in db/base.py) specifically to avoid a circular
import: models import Base FROM db.base, so db.base cannot also import
the models at module scope.
"""
from app.models.department import Department  # noqa: F401
from app.models.job_role import JobRole  # noqa: F401
from app.models.skill import Skill  # noqa: F401
from app.models.employee import Employee  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.employee_skill import EmployeeSkill  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.employee_project import EmployeeProject  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.attendance import Attendance  # noqa: F401
from app.models.hr import LeaveType, LeaveBalance, LeaveRequest, SalaryProfile, PayrollRun, PayrollRecord, AuditLog  # noqa: F401
