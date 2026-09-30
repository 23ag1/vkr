import api from './client';

export interface Session {
  id: string;
  user_id: string;
  module_id: string | null;
  title: string;
}

export interface MessageSource {
  id: string;
  title: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: { documents: MessageSource[] } | null;
}

export const getSessions = () => api.get<{ data: Session[] }>('/mentor/sessions');
export const createSession = (title = 'Новый чат') =>
  api.post<{ data: Session }>('/mentor/sessions', { title });
export const getMessages = (sessionId: string) =>
  api.get<{ data: Message[] }>(`/mentor/sessions/${sessionId}/messages`);
export const sendMessage = (sessionId: string, content: string) =>
  api.post<{ data: Message }>(`/mentor/sessions/${sessionId}/messages`, { content });
