import api from './client';

export interface Template {
  id: string;
  name: string;
  subject: string;
  body_html: string;
  difficulty: string;
}

export interface Campaign {
  id: string;
  name: string;
  template_id: string;
  status: string;
  created_by: string | null;
}

export interface RecipientResult {
  id: string;
  user_id: string;
  tracking_token: string;
  clicked_at: string | null;
  reported_at: string | null;
}

export const getTemplates = () => api.get<{ data: Template[] }>('/phishing/templates');
export const createTemplate = (body: Omit<Template, 'id'>) =>
  api.post<{ data: Template }>('/phishing/templates', body);
export const deleteTemplate = (id: string) => api.delete(`/phishing/templates/${id}`);

export const getCampaigns = () => api.get<{ data: Campaign[] }>('/phishing/campaigns');
export const createCampaign = (name: string, template_id: string, user_ids: string[]) =>
  api.post<{ data: Campaign }>('/phishing/campaigns', { name, template_id, user_ids });
export const launchCampaign = (id: string) =>
  api.post<{ data: Campaign }>(`/phishing/campaigns/${id}/launch`);
export const completeCampaign = (id: string) =>
  api.post<{ data: Campaign }>(`/phishing/campaigns/${id}/complete`);
export const getCampaignResults = (id: string) =>
  api.get<{ data: RecipientResult[] }>(`/phishing/campaigns/${id}/results`);

export interface InboxItem {
  id: string;
  tracking_token: string;
  clicked_at: string | null;
  reported_at: string | null;
  created_at: string;
  campaign_name: string;
  campaign_status: string;
  subject: string;
  body_html: string;
  difficulty: string;
}

export const getMyInbox = () =>
  api.get<{ data: InboxItem[] }>('/phishing/my-inbox');

export const reportPhishing = (token: string) =>
  api.post<{ data: null }>(`/phishing/report/${token}`);

// Uses fetch (not api client) — public endpoint has no /api prefix and expects GET
export const trackClick = (token: string) =>
  fetch(`/phishing/track/${token}/click`).catch(() => {});
