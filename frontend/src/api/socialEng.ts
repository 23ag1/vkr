import api from './client';

export interface Scenario {
  id: string;
  title: string;
  description: string;
}

export interface TurnResult {
  content: string;
  score: number;
  feedback: string;
}

export interface StartResult {
  session_id: string;
  content: string;
  scenario: string;
}

export const getScenarios = () =>
  api.get<{ data: Scenario[] }>('/social-eng/scenarios');
export const startSimulation = (scenario_id: string) =>
  api.post<{ data: StartResult }>('/social-eng/start', { scenario_id });
export const sendTurn = (session_id: string, message: string) =>
  api.post<{ data: TurnResult }>(`/social-eng/sessions/${session_id}/turn`, { message });
