import api from './client';

export const adminAsk = (question: string) =>
  api.post<{ data: string }>('/admin/llm/ask', { question });
