import api from './client';

export interface Progress {
  id: string;
  user_id: string;
  module_id: string;
  status: 'not_started' | 'in_progress' | 'completed';
  score: number | null;
  completed_at: string | null;
}

export const getMyPath = () => api.get<{ data: Progress[] }>('/learning/my');
export const updateProgress = (id: string, status: string, score?: number) =>
  api.patch<{ data: Progress }>(`/learning/${id}/progress`, { status, score });
export const assignModule = (user_id: string, module_id: string) =>
  api.post<{ data: Progress }>('/learning/assign', { user_id, module_id });
