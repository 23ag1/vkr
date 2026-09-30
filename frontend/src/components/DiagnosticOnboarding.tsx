import { useState } from 'react';
import { startDiagnostic, submitDiagnosticAnswer, type DiagnosticQuestion } from '../api/diagnostic';
import { useAuthStore } from '../store/auth';
import { getMe } from '../api/auth';

const TOPIC_LABELS: Record<string, string> = {
  phishing: 'Фишинг',
  passwords: 'Пароли',
  pii: 'Персональные данные',
  incident_response: 'Инциденты',
  social_engineering: 'Социальная инженерия',
};

const TOTAL = 10;

export default function DiagnosticOnboarding({ onComplete }: { onComplete: () => void }) {
  const setUser = useAuthStore(s => s.setUser);

  const [phase, setPhase] = useState<'intro' | 'question' | 'done'>('intro');
  const [sessionId, setSessionId] = useState('');
  const [question, setQuestion] = useState<DiagnosticQuestion | null>(null);
  const [answered, setAnswered] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [feedback, setFeedback] = useState<{ correct: boolean } | null>(null);
  const [profile, setProfile] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleStart() {
    setLoading(true);
    const res = await startDiagnostic();
    setSessionId(res.data.data.session_id);
    setQuestion(res.data.data.question);
    setPhase('question');
    setLoading(false);
  }

  async function handleAnswer(idx: number) {
    if (!question || feedback || loading) return;
    setSelected(idx);
    setLoading(true);

    const res = await submitDiagnosticAnswer({
      session_id: sessionId,
      question_id: question.id,
      topic: question.topic,
      selected_index: idx,
    });
    const data = res.data.data;

    setFeedback({ correct: data.is_correct });

    setTimeout(async () => {
      if (data.finished) {
        setProfile(data.profile);
        setPhase('done');
        const meRes = await getMe();
        setUser(meRes.data.data);
      } else if (data.question) {
        setQuestion(data.question);
        setAnswered(a => a + 1);
        setSelected(null);
        setFeedback(null);
      }
      setLoading(false);
    }, 1000);
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg p-6">
        {phase === 'intro' && (
          <div>
            <h2 className="text-xl font-semibold mb-3">Добро пожаловать!</h2>
            <p className="text-gray-400 text-sm mb-2">
              Прежде чем начать обучение, пройдите короткую диагностику знаний. Это займёт около 5 минут.
            </p>
            <p className="text-gray-500 text-sm mb-6">
              По результатам система автоматически подберёт нужные модули обучения.
            </p>
            <button
              onClick={handleStart}
              disabled={loading}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 rounded-xl text-sm font-medium disabled:opacity-50 transition-colors"
            >
              {loading ? 'Загрузка...' : 'Начать диагностику'}
            </button>
          </div>
        )}

        {phase === 'question' && question && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs text-gray-500">
                Вопрос {answered + 1} из {TOTAL}
              </span>
              <span className="text-xs text-blue-400 bg-blue-900/30 px-2 py-0.5 rounded-full">
                {TOPIC_LABELS[question.topic] ?? question.topic}
              </span>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-1.5 mb-5">
              <div
                className="bg-blue-500 h-1.5 rounded-full transition-all"
                style={{ width: `${(answered / TOTAL) * 100}%` }}
              />
            </div>
            <p className="text-sm font-medium mb-4">{question.text}</p>
            <div className="grid gap-2">
              {question.options.map((opt, i) => {
                const isSelected = selected === i;
                const showCorrect = feedback !== null;
                let cls = 'w-full text-left px-4 py-3 rounded-xl text-sm border transition-colors ';
                if (!showCorrect) {
                  cls += isSelected
                    ? 'border-blue-500 bg-blue-900/30 text-white'
                    : 'border-gray-700 bg-gray-800/50 text-gray-300 hover:border-gray-500';
                } else if (isSelected) {
                  cls += feedback!.correct
                    ? 'border-green-500 bg-green-900/30 text-white'
                    : 'border-red-500 bg-red-900/30 text-white';
                } else {
                  cls += 'border-gray-700 bg-gray-800/50 text-gray-500';
                }
                return (
                  <button key={i} className={cls} onClick={() => handleAnswer(i)} disabled={!!feedback || loading}>
                    {opt}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {phase === 'done' && profile && (
          <div>
            <h2 className="text-xl font-semibold mb-2">Диагностика завершена</h2>
            <p className="text-gray-400 text-sm mb-4">
              Ваш профиль компетенций:
            </p>
            <div className="grid gap-2 mb-5">
              {Object.entries(profile).map(([topic, score]) => (
                <div key={topic}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">{TOPIC_LABELS[topic] ?? topic}</span>
                    <span className={score >= 0.5 ? 'text-green-400' : 'text-red-400'}>
                      {Math.round(score * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full transition-all ${score >= 0.5 ? 'bg-green-500' : 'bg-red-500'}`}
                      style={{ width: `${score * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <p className="text-gray-500 text-xs mb-4">
              Модули по слабым темам назначены автоматически.
            </p>
            <button
              onClick={onComplete}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 rounded-xl text-sm font-medium transition-colors"
            >
              Перейти к обучению
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
