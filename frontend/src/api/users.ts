import api from './client';

export type UserRole = 'employee' | 'admin' | 'manager' | 'security_specialist';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  department_id: string | null;
}

export const getUsers = () => api.get<{ data: User[]; meta: { total: number } }>('/users');
export const createUser = (body: { email: string; password: string; full_name: string; role: string }) =>
  api.post<{ data: User }>('/users', body);
export const deactivateUser = (id: string) => api.delete<{ data: User }>(`/users/${id}`);
