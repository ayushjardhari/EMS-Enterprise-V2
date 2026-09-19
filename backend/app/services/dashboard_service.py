from sqlalchemy.orm import Session

from app.models.employee import AvailabilityStatus, EmploymentStatus
from app.repositories.department_repository import DepartmentRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.dashboard import DashboardSummary
from app.schemas.employee import EmployeeListItem


class DashboardService:
    def __init__(self, db: Session):
        self.employee_repo = EmployeeRepository(db)
        self.department_repo = DepartmentRepository(db)
        self.project_repo = ProjectRepository(db)

    def get_summary(self) -> DashboardSummary:
        recent = self.employee_repo.recent(limit=5)
        return DashboardSummary(
            total_employees=self.employee_repo.count_all(),
            active_employees=self.employee_repo.count_by_employment_status(EmploymentStatus.ACTIVE),
            available_employees=self.employee_repo.count_by_availability_status(AvailabilityStatus.AVAILABLE),
            total_departments=len(self.department_repo.list_all()),
            active_projects=self.project_repo.count_active(),
            recently_added_employees=[EmployeeListItem.model_validate(e) for e in recent],
        )
