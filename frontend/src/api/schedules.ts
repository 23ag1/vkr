import api from './client';

export interface Schedule {
  id: string;
  action: string;
  cadence: string;
  module_id: string | null;
  target_roles: string[];
  is_active: boolean;
  last_triggered_at: string | null;
  created_at: string;
}

export interface ScheduleCreate {
  action: string;
  cadence: string;
  module_id?: string;
  target_roles: string[];
}

export const getSchedules = () => api.get<{ data: Schedule[] }>('/schedules/');
export const createSchedule = (body: ScheduleCreate) =>
  api.post<{ data: Schedule }>('/schedules/', body);
export const deleteSchedule = (id: string) => api.delete(`/schedules/${id}`);
export const triggerSchedule = (id: string) =>
  api.post<{ data: { assigned: number; action: string } }>(`/schedules/${id}/trigger`);
