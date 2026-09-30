import api from './client';

export interface AppSettings {
  question_prompt: string;
  explanation_prompt: string;
  model: string;
}

export const getSettings = () =>
  api.get<{ data: AppSettings }>('/admin/settings/');

export const updateSettings = (body: Partial<AppSettings>) =>
  api.patch<{ data: AppSettings }>('/admin/settings/', body);
