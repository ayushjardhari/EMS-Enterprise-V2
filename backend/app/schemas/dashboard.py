from pydantic import BaseModel

from app.schemas.employee import EmployeeListItem


class DashboardSummary(BaseModel):
    total_employees: int
    active_employees: int
    available_employees: int
    total_departments: int
    active_projects: int
    recently_added_employees: list[EmployeeListItem]
