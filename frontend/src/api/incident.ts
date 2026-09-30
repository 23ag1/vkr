import api from './client';

export const reportIncident = (description: string) =>
  api.post<{ data: { incident_id: string; guidance: string } }>('/incident/report', { description });
