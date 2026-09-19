import { api } from "./api";
import type { CurrentUser } from "../types";

export const authService = {
  login: (email: string, password: string) =>
    api.post<{ access_token: string; token_type: string }>("/auth/login", { email, password }),
  me: () => api.get<CurrentUser>("/auth/me"),
};
