import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getScenarios, startSimulation, sendTurn, type TurnResult } from '../../api/socialEng';
import ChatThread, { type ChatBubble } from '../../components/chat/ChatThread';
import ChatInput from '../../components/chat/ChatInput';

interface Turn {
  role: 'attacker' | 'user';
  text: string;
  score?: number;
  feedback?: string;
}

export default function SocialEngPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [scenarioTitle, setScenarioTitle] = useState('');
  const [history, setHistory] = useState<Turn[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [totalScore, setTotalScore] = useState<number | null>(null);

  const { data: scenariosRes } = useQuery({ queryKey: ['sim-scenarios'], queryFn: getScenarios });
  const scenarios = scenariosRes?.data.data ?? [];

  async function handleStart(scenarioId: string, title: string) {
    setLoading(true);
    try {
      const res = await startSimulation(scenarioId);
      const { session_id, content } = res.data.data;
      setSessionId(session_id);
      setScenarioTitle(title);
      setHistory([{ role: 'attacker', text: content }]);
      setTotalScore(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleSend() {
    if (!input.trim() || !sessionId || loading) return;
    const msg = input.trim();
    setInput('');
    setHistory(h => [...h, { role: 'user', text: msg }]);
    setLoading(true);
    try {
      const res = await sendTurn(sessionId, msg);
      const turn: TurnResult = res.data.data;
      setHistory(h => [...h, {
        role: 'attacker',
        text: turn.content,
        score: turn.score,
        feedback: turn.feedback,
      }]);
      setTotalScore(turn.score);
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setSessionId(null);
    setHistory([]);
    setInput('');
    setTotalScore(null);
    setScenarioTitle('');
  }

  const scoreColor = totalScore === null ? '' :
    totalScore >= 75 ? 'text-green-400' :
    totalScore >= 40 ? 'text-yellow-400' : 'text-red-400';

  if (!sessionId) {
    return (
      <div className="max-w-2xl">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold mb-1">Симуляция социальной инженерии</h1>
          <p className="text-sm text-gray-400">
            Потренируйтесь противостоять атакам злоумышленников в безопасной среде.
            AI сыграет роль атакующего — ваша задача не поддаться манипуляциям.
          </p>
        </div>

        <div className="grid gap-3">
          {scenarios.map(s => (
            <button
              key={s.id}
              onClick={() => handleStart(s.id, s.title)}
              disabled={loading}
              className="text-left bg-gray-900 border border-gray-800 rounded-xl p-5 hover:bg-gray-800 hover:border-gray-700 transition-colors disabled:opacity-50"
            >
              <p className="font-medium mb-1">{s.title}</p>
              <p className="text-sm text-gray-400">{s.description}</p>
            </button>
          ))}
        </div>
      </div>
    );
  }

  const bubbles: ChatBubble[] = history.map((turn, i) => ({
    key: String(i),
    side: turn.role === 'user' ? 'right' : 'left',
    content: turn.text,
    bubbleClassName: `max-w-[85%] whitespace-pre-wrap ${
      turn.role === 'user'
        ? 'bg-blue-600 text-white'
        : 'bg-gray-800 text-gray-200 border border-red-900/40'
    }`,
    header: (
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-xs text-gray-600">
          {turn.role === 'attacker' ? 'Атакующий' : 'Вы'}
        </span>
        {turn.score !== undefined && (
          <span className={`text-xs font-medium ${
            turn.score >= 75 ? 'text-green-400' : turn.score >= 40 ? 'text-yellow-400' : 'text-red-400'
          }`}>
            {turn.score}/100
          </span>
        )}
      </div>
    ),
    footer: turn.feedback ? (
      <p className="text-xs text-gray-500 mt-1 max-w-[85%] italic">{turn.feedback}</p>
    ) : undefined,
  }));

  return (
    <div className="max-w-2xl flex flex-col h-[calc(100vh-4rem)]">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h1 className="text-lg font-semibold">{scenarioTitle}</h1>
          <p className="text-xs text-gray-500">Не давайте конфиденциальную информацию и сообщайте о подозрительных запросах</p>
        </div>
        <div className="flex items-center gap-3">
          {totalScore !== null && (
            <span className={`text-sm font-semibold ${scoreColor}`}>
              Оценка: {totalScore}/100
            </span>
          )}
          <button
            onClick={handleReset}
            className="text-xs text-gray-400 hover:text-white transition-colors"
          >
            Сменить сценарий
          </button>
        </div>
      </div>

      <ChatThread
        className="flex-1 overflow-y-auto bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3 mb-3"
        messages={bubbles}
        loading={loading}
        loadingBubbleClassName="bg-gray-800 text-gray-400 border border-red-900/40"
      />

      <ChatInput
        value={input}
        onChange={setInput}
        onSend={handleSend}
        placeholder="Ваш ответ..."
        disabled={loading}
      />
    </div>
  );
}
