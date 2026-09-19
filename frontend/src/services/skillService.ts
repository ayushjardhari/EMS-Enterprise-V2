import { api } from "./api";
import type { Skill } from "../types";

export const skillService = {
  list: () => api.get<Skill[]>("/skills"),
  create: (payload: { name: string; category?: string }) => api.post<Skill>("/skills", payload),
  update: (id: string, payload: Partial<{ name: string; category: string }>) => api.put<Skill>(`/skills/${id}`, payload),
};
