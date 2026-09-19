import { api } from "./api";
import type { Project } from "../types";

export const projectService = {
  list: (statusFilter?: string) => api.get<Project[]>(`/projects${statusFilter ? `?status_filter=${statusFilter}` : ""}`),
  getById: (id: string) => api.get<Project>(`/projects/${id}`),
  create: (payload: object) => api.post<Project>("/projects", payload),
  update: (id: string, payload: object) => api.put<Project>(`/projects/${id}`, payload),
};
