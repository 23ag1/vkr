import { useState } from 'react';
import { adminAsk } from '../../api/adminLlm';
import ChatThread, { type ChatBubble } from '../../components/chat/ChatThread';
import ChatInput from '../../components/chat/ChatInput';

interface Turn {
  role: 'user' | 'assistant';
  text: string;
}

const QUICK_QUESTIONS = [
  'Каков текущий уровень риска программы?',
  'Какие подразделения требуют внимания?',
  'Как интерпретировать показатель кликов фишинга?',
  'Какие модули стоит назначить приоритетно?',
];

export default function AdminLlmPage() {
  const [history, setHistory] = useState<Turn[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const bubbles: ChatBubble[] = history.map((turn, i) => ({
    key: String(i),
    side: turn.role === 'user' ? 'right' : 'left',
    content: turn.text,
    bubbleClassName: `max-w-[80%] whitespace-pre-wrap ${
      turn.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-200'
    }`,
  }));

  async function send(question: string) {
    if (!question.trim() || loading) return;
    setInput('');
    setHistory(h => [...h, { role: 'user', text: question }]);
    setLoading(true);
    try {
      const res = await adminAsk(question);
      setHistory(h => [...h, { role: 'assistant', text: res.data.data }]);
    } catch {
      setHistory(h => [...h, { role: 'assistant', text: 'Ошибка при обращении к LLM.' }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl flex flex-col h-[calc(100vh-4rem)]">
      <div className="mb-4">
        <h1 className="text-2xl font-semibold mb-1">AI-советник администратора</h1>
        <p className="text-sm text-gray-400">
          Задайте вопрос о программе информационной безопасности — ответ основан на текущих метриках.
        </p>
      </div>

      {history.length === 0 && (
        <div className="grid grid-cols-2 gap-2 mb-4">
          {QUICK_QUESTIONS.map(q => (
            <button
              key={q}
              onClick={() => send(q)}
              className="text-left px-4 py-3 bg-gray-900 border border-gray-800 rounded-xl text-xs text-gray-300 hover:bg-gray-800 hover:border-gray-700 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      <ChatThread
        className="flex-1 overflow-y-auto bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3 mb-3"
        messages={bubbles}
        loading={loading}
      />

      <ChatInput
        value={input}
        onChange={setInput}
        onSend={() => send(input)}
        placeholder="Задайте вопрос о программе ИБ..."
        disabled={loading}
      />
    </div>
  );
}
