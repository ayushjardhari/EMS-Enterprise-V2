export type UserRole = "ADMIN" | "HR" | "MANAGER" | "EMPLOYEE";
export type EmploymentStatus = "ACTIVE" | "INACTIVE" | "ON_LEAVE";
export type AvailabilityStatus = "AVAILABLE" | "PARTIALLY_AVAILABLE" | "UNAVAILABLE";
export type ProficiencyLevel = "BEGINNER" | "INTERMEDIATE" | "ADVANCED" | "EXPERT";
export type ProjectStatus = "PLANNED" | "ACTIVE" | "ON_HOLD" | "COMPLETED";

export interface CurrentUser {
  id: string;
  email: string;
  user_role: UserRole;
  employee_id: string | null;
}

export interface LeaveBalanceEntry {
  id: string;
  leave_type_id: string;
  type: string;
  allocated_days: number;
  used_days: number;
  remaining_days: number;
}

export interface LeaveRequestEntry {
  id: string;
  type: string;
  start_date: string;
  end_date: string;
  days: number;
  reason: string | null;
  status: string;
  created_at: string;
}

export interface EmployeeLeave {
  year: number;
  balances: LeaveBalanceEntry[];
  requests: LeaveRequestEntry[];
}

export interface EmployeePayrollSalary {
  basic_salary: number;
  housing_allowance: number;
  transport_allowance: number;
  other_allowance: number;
  effective_from: string;
}

export interface PayrollRecordEntry {
  id: string;
  period: string;
  basic: number;
  allowances: number;
  bonus: number;
  deductions: number;
  gross: number;
  net: number;
  status: string;
}

export interface EmployeePayroll {
  salary: EmployeePayrollSalary | null;
  records: PayrollRecordEntry[];
}

export interface EmployeeActivity {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  details: string | null;
  created_at: string;
}

export interface Department {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface JobRole {
  id: string;
  title: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface Skill {
  id: string;
  name: string;
  category: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmployeeListItem {
  id: string;
  employee_code: string;
  full_name: string;
  email: string;
  department: Department;
  job_role: JobRole;
  employment_status: EmploymentStatus;
  availability_status: AvailabilityStatus;
  joining_date: string;
}

export interface EmployeeSkillEntry {
  id: string;
  skill: Skill;
  proficiency_level: ProficiencyLevel;
  years_of_experience: number;
}

export interface Project {
  id: string;
  project_code: string;
  project_name: string;
  description: string | null;
  department_id: string;
  status: ProjectStatus;
  start_date: string;
  end_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmployeeProjectEntry {
  id: string;
  project: Project;
  project_role: string;
  start_date: string;
  end_date: string | null;
}

export interface EmployeeProfile extends EmployeeListItem {
  phone: string | null;
  location: string | null;
  profile_info: string | null;
  created_at: string;
  updated_at: string;
  skills: EmployeeSkillEntry[];
  projects: EmployeeProjectEntry[];
}

export interface Attendance {
  id: string;
  employee_id: string;
  attendance_date: string;
  check_in: string | null;
  check_out: string | null;
  status: string;
  work_hours: number | null;
  notes: string | null;
}

export interface Document {
  id: string;
  employee_id: string;
  filename: string;
  file_type: string;
  uploaded_at: string;
  extraction_status: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

export interface DashboardSummary {
  total_employees: number;
  active_employees: number;
  available_employees: number;
  total_departments: number;
  active_projects: number;
  recently_added_employees: EmployeeListItem[];
}
