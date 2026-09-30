import api from './client';

export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export const getAuditLogs = (params?: {
  user_id?: string;
  action?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  limit?: number;
}) => api.get<{ data: AuditLog[] }>('/audit', { params });

export const exportAuditCsv = (params?: {
  user_id?: string;
  action?: string;
  date_from?: string;
  date_to?: string;
}) =>
  api.get('/audit/export', {
    params: { ...params, format: 'csv' },
    responseType: 'blob',
  });
