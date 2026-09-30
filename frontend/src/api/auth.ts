import api from './client';
import type { UserRole } from './users';

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  mfa_required?: boolean;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  department_id: string | null;
  diagnostic_completed_at: string | null;
}

export const login = (email: string, password: string) =>
  api.post<{ data: TokenResponse }>('/auth/login', { email, password });

export const mfaComplete = (temp_token: string, code: string) =>
  api.post<{ data: TokenResponse }>('/auth/mfa/complete', { temp_token, code });

export const mfaSetup = () =>
  api.post<{ data: { secret: string; otpauth_uri: string } }>('/auth/mfa/setup');

export const mfaVerify = (code: string) =>
  api.post<{ data: { mfa_enabled: boolean } }>('/auth/mfa/verify', { code });

export const getMe = () => api.get<{ data: UserProfile }>('/auth/me');
