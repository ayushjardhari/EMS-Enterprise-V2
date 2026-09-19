import { api } from "./api";
import type { JobRole } from "../types";

export const jobRoleService = {
  list: () => api.get<JobRole[]>("/roles"),
  create: (payload: { title: string; description?: string }) => api.post<JobRole>("/roles", payload),
  update: (id: string, payload: Partial<{ title: string; description: string }>) =>
    api.put<JobRole>(`/roles/${id}`, payload),
};
