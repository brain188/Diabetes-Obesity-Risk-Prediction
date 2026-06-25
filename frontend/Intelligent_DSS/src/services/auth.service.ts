import api from "@/lib/api";
import type { LoginResponse, LoginRequest, RegisterRequest, User } from "@/types/auth.types";

export const authService = {
  login: (data: LoginRequest) =>
    api.post<LoginResponse>("/auth/login", data).then((r) => r.data),

  register: (data: RegisterRequest) =>
    api.post<User>("/auth/register", data).then((r) => r.data),

  logout: () => api.post("/auth/logout").then((r) => r.data),

  refresh: (refresh_token: string) =>
    api.post<LoginResponse>("/auth/refresh", { refresh_token }).then((r) => r.data),

  me: () => api.get<User>("/auth/profile").then((r) => r.data),

  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post("/auth/change-password", data).then((r) => r.data),

  listUsers: () =>
    api.get<User[]>("/auth/users").then((r) => r.data),
};
