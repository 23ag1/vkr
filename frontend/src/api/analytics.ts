import api from './client';

export interface Overview {
  total_users: number;
  completion_rate: number;
  avg_score: number;
  phishing_open_rate: number;
  phishing_click_rate: number;
  phishing_submit_rate: number;
  phishing_report_rate: number;
}

export interface UserProfile {
  user_id: string;
  modules_completed: number;
  avg_score: number;
  phishing_clicks: number;
}

export interface DeptMetrics {
  id: string;
  name: string;
  total_users: number;
  completion_rate: number;
  avg_score: number;
  phishing_click_rate: number;
}

export interface MaturityIndicator {
  label: string;
  met: boolean;
}

export interface Maturity {
  level: number;
  score: number;
  label: string;
  description: string;
  indicators: MaturityIndicator[];
}

export interface BriefingStat {
  briefing_type: string;
  completed: number;
  total: number;
}

export const getOverview = () => api.get<{ data: Overview }>('/analytics/overview');
export const getUserProfile = (id: string) =>
  api.get<{ data: UserProfile }>(`/analytics/users/${id}`);
export const getDepartments = () => api.get<{ data: DeptMetrics[] }>('/analytics/departments');
export const getMaturity = () => api.get<{ data: Maturity }>('/analytics/maturity');
export const getBriefings = () => api.get<{ data: BriefingStat[] }>('/analytics/briefings');
