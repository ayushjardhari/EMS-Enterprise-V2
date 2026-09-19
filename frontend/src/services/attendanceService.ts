import { api } from "./api";
import type { Attendance } from "../types";

export const attendanceService = {
  list: () => api.get<Attendance[]>("/attendance"),
  listForEmployee: (employeeId: string) => api.get<Attendance[]>(`/attendance/employee/${employeeId}`),
  checkIn: () => api.post<Attendance>("/attendance/check-in"),
  checkOut: () => api.post<Attendance>("/attendance/check-out"),
};
