import api from './client';

export interface DiagnosticQuestion {
  id: string;
  topic: string;
  text: string;
  options: string[];
}

export interface DiagnosticStartResponse {
  session_id: string;
  question: DiagnosticQuestion;
}

export interface DiagnosticAnswerResponse {
  is_correct: boolean;
  finished: boolean;
  question: DiagnosticQuestion | null;
  profile: Record<string, number> | null;
}

export const startDiagnostic = () =>
  api.post<{ data: DiagnosticStartResponse }>('/diagnostic/start');

export const submitDiagnosticAnswer = (body: {
  session_id: string;
  question_id: string;
  topic: string;
  selected_index: number;
}) => api.post<{ data: DiagnosticAnswerResponse }>('/diagnostic/answer', body);
