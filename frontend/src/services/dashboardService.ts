import { api } from "./api";
import type { DashboardSummary } from "../types";

export const dashboardService = {
  getSummary: () => api.get<DashboardSummary>("/dashboard/summary"),
};
