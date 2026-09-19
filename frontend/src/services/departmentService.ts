import { api } from "./api";
import type { Department } from "../types";

export const departmentService = {
  list: (includeInactive = false) => api.get<Department[]>(`/departments?include_inactive=${includeInactive}`),
  create: (payload: { name: string; description?: string }) => api.post<Department>("/departments", payload),
  update: (id: string, payload: Partial<{ name: string; description: string; is_active: boolean }>) =>
    api.put<Department>(`/departments/${id}`, payload),
  deactivate: (id: string) => api.patch<Department>(`/departments/${id}/deactivate`, {}),
};
