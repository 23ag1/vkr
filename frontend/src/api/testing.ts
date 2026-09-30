import api from './client';

export interface Question {
  id: string;
  module_id: string;
  text: string;
  options: string[];
}

export interface AnswerFeedback {
  is_correct: boolean;
  explanation: string;
  correct_index: number;
}

export const generateQuestion = (module_id: string) =>
  api.post<{ data: Question }>('/testing/generate', { module_id });
export const submitAnswer = (question_id: string, selected_index: number) =>
  api.post<{ data: AnswerFeedback }>('/testing/answer', { question_id, selected_index });
