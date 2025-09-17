// Auth Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  roles: string[];
  permissions: string[];
  verified: boolean;
}

export interface LoginResponse {
  access_token: string;
  user: User;
}

export interface RefreshResponse {
  access_token: string;
}

export interface SignupResponse {
  id: string;
  email: string;
  full_name: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface VerifyEmailRequest {
  email: string;
}

export interface GoogleOAuthStartResponse {
  auth_url: string;
  state: string;
}

// Error Types
export interface ApiErrorDetail {
  message: string;
  score?: number;
  feedback?: string[];
}

export interface ApiErrorResponse {
  detail: string | ApiErrorDetail;
}

// User Profile Types
export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  roles: string[];
  permissions: string[];
  email_verified_at?: string;
  created_at: string;
  updated_at: string;
}

// Admin Types
export interface Role {
  id: string;
  slug: string;
  permissions: string[];
}

export interface CreateRoleRequest {
  slug: string;
  permissions: string[];
}

// Common API Response wrapper
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  ok: boolean;
}