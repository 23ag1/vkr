import api from './client';

export const BRIEFING_TYPES = ['none', 'introductory', 'primary', 'repeated', 'extraordinary'] as const;
export type BriefingType = typeof BRIEFING_TYPES[number];

export const BRIEFING_LABEL: Record<string, string> = {
  none: 'Без инструктажа',
  introductory: 'Вводный',
  primary: 'Первичный',
  repeated: 'Повторный',
  extraordinary: 'Внеплановый',
};

export interface Module {
  id: string;
  title: string;
  description: string;
  content_md: string;
  target_roles: string[];
  order_index: number;
  is_published: boolean;
  briefing_type: BriefingType;
}

export const getModules = () => api.get<{ data: Module[] }>('/modules');
export const getModule = (id: string) => api.get<{ data: Module }>(`/modules/${id}`);
export const createModule = (body: Omit<Module, 'id' | 'is_published'>) =>
  api.post<{ data: Module }>('/modules', body);
export const updateModule = (id: string, body: Partial<Module>) =>
  api.put<{ data: Module }>(`/modules/${id}`, body);
export const publishModule = (id: string) =>
  api.post<{ data: Module }>(`/modules/${id}/publish`);
export const deleteModule = (id: string) => api.delete(`/modules/${id}`);
