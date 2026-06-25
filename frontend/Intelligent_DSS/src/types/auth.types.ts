export type UserRole = "admin" | "healthcare_worker";

export interface User {
  worker_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  clinic_name?: string | null;
  is_active: boolean;
  last_login_at?: string | null;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  refresh_expires_in: number;
  user: User;
}

export type AuthTokens = LoginResponse;

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  clinic_name?: string;
}
