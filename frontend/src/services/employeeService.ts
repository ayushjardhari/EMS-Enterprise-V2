import { api } from "./api";

import type {
  Document,
  EmployeeActivity,
  EmployeeLeave,
  EmployeeListItem,
  EmployeePayroll,
  EmployeeProfile,
  EmployeeProjectEntry,
  EmployeeSkillEntry,
  EmploymentStatus,
  Page,
} from "../types";

export interface EmployeeSearchParams {
  search?: string;
  department_id?: string;
  job_role_id?: string;
  employment_status?: string;
  availability_status?: string;
  page?: number;
  limit?: number;
}

function toQueryString(params: object): string {
  const usable = Object.entries(params as Record<string, unknown>).filter(
    ([, v]) => v !== undefined && v !== "" && v !== null
  );

  if (usable.length === 0) return "";

  return (
    "?" +
    usable
      .map(
        ([k, v]) =>
          `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`
      )
      .join("&")
  );
}

export const employeeService = {
  // Employees
  search: (params: EmployeeSearchParams) =>
    api.get<Page<EmployeeListItem>>(
      `/employees${toQueryString(params)}`
    ),

  getById: (id: string) =>
    api.get<EmployeeProfile>(`/employees/${id}`),

  create: (payload: object) =>
    api.post<EmployeeProfile>("/employees", payload),

  update: (id: string, payload: object) =>
    api.put<EmployeeProfile>(`/employees/${id}`, payload),

  setStatus: (
    id: string,
    employment_status: EmploymentStatus
  ) =>
    api.patch<EmployeeProfile>(
      `/employees/${id}/status`,
      { employment_status }
    ),

  // Skills
  listSkills: (employeeId: string) =>
    api.get<EmployeeSkillEntry[]>(
      `/employees/${employeeId}/skills`
    ),

  addSkill: (employeeId: string, payload: object) =>
    api.post<EmployeeSkillEntry>(
      `/employees/${employeeId}/skills`,
      payload
    ),

  removeSkill: (employeeId: string, skillId: string) =>
    api.delete<void>(
      `/employees/${employeeId}/skills/${skillId}`
    ),

  // Projects
  listProjects: (employeeId: string) =>
    api.get<EmployeeProjectEntry[]>(
      `/employees/${employeeId}/projects`
    ),

  addProject: (employeeId: string, payload: object) =>
    api.post<EmployeeProjectEntry>(
      `/employees/${employeeId}/projects`,
      payload
    ),

  // Documents
  listDocuments: (employeeId: string) =>
    api.get<Document[]>(
      `/employees/${employeeId}/documents`
    ),

  uploadDocument: (employeeId: string, file: File) =>
    api.upload<Document>(
      `/employees/${employeeId}/documents`,
      file
    ),

  deleteDocument: (documentId: string) =>
    api.delete<void>(
      `/documents/${documentId}`
    ),

  // Employee 360 — Leave
  getLeave: (employeeId: string) =>
    api.get<EmployeeLeave>(
      `/employees/${employeeId}/leave`
    ),

  // Employee 360 — Leave Requests
  createLeaveRequest: (payload: {
    leave_type_id: string;
    start_date: string;
    end_date: string;
    reason?: string;
  }) => api.post("/leave/requests", payload),

  // Employee 360 — Leave Types
  listLeaveTypes: () =>
    api.get<Array<{
      id: string;
      name: string;
      annual_days: number;
      is_active: boolean;
    }>>("/leave/types"),

  // Employee 360 — Payroll
  getPayroll: (employeeId: string) =>
    api.get<EmployeePayroll>(
      `/employees/${employeeId}/payroll`
    ),

  // Employee 360 — Audit / Activity
  getActivity: (employeeId: string) =>
    api.get<EmployeeActivity[]>(
      `/employees/${employeeId}/activity`
    ),
};