import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { generateQuestion, submitAnswer } from '../../api/testing';
import type { Question, AnswerFeedback } from '../../api/testing';

const SESSION_SIZE = 10;

type Phase = 'idle' | 'question' | 'feedback' | 'result';

interface SessionState {
  total: number;
  correct: number;
  question: Question | null;
  feedback: AnswerFeedback | null;
  selected: number | null;
  phase: Phase;
}

const INIT: SessionState = {
  total: 0,
  correct: 0,
  question: null,
  feedback: null,
  selected: null,
  phase: 'idle',
};

export default function TestingPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const moduleId = searchParams.get('module_id') ?? '';
  const [s, setS] = useState<SessionState>(INIT);

  const genMut = useMutation({
    mutationFn: () => generateQuestion(moduleId),
    onSuccess: ({ data }) =>
      setS(prev => ({ ...prev, question: data.data, feedback: null, selected: null, phase: 'question' })),
  });

  const submitMut = useMutation({
    mutationFn: (idx: number) => submitAnswer(s.question!.id, idx),
    onSuccess: ({ data }) =>
      setS(prev => ({
        ...prev,
        feedback: data.data,
        correct: prev.correct + (data.data.is_correct ? 1 : 0),
        total: prev.total + 1,
        phase: 'feedback',
      })),
  });

  function startSession() {
    setS({ ...INIT, phase: 'question' });
    genMut.mutate();
  }

  function nextQuestion() {
    if (s.total >= SESSION_SIZE) {
      setS(prev => ({ ...prev, phase: 'result' }));
    } else {
      genMut.mutate();
    }
  }

  function submitSelected() {
    if (s.selected === null) return;
    submitMut.mutate(s.selected);
  }

  if (!moduleId) {
    return (
      <div className="max-w-xl">
        <h1 className="text-2xl font-semibold mb-4">Тестирование</h1>
        <p className="text-yellow-400 text-sm">Выбери модуль на странице обучения, чтобы начать тест.</p>
        <button onClick={() => navigate('/modules')} className="mt-4 text-sm text-blue-400 hover:text-blue-300">
          ← К модулям
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Тестирование</h1>
        {s.phase !== 'idle' && s.phase !== 'result' && (
          <span className="text-sm text-gray-400">
            {s.total} / {SESSION_SIZE} вопросов · {s.correct} правильно
          </span>
        )}
      </div>

      {/* Progress bar */}
      {s.phase !== 'idle' && s.phase !== 'result' && (
        <div className="h-1.5 bg-gray-800 rounded-full mb-6">
          <div
            className="h-1.5 bg-blue-500 rounded-full transition-all"
            style={{ width: `${(s.total / SESSION_SIZE) * 100}%` }}
          />
        </div>
      )}

      {/* Idle */}
      {s.phase === 'idle' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <p className="text-gray-300 mb-2">Сессия: <span className="text-white font-medium">{SESSION_SIZE} вопросов</span></p>
          <p className="text-sm text-gray-400 mb-6">
            GPT генерирует разные типы вопросов: сценарии, определения, лучшие практики, распознавание угроз.
            Каждая сессия уникальна.
          </p>
          <button
            onClick={startSession}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
          >
            Начать тест
          </button>
        </div>
      )}

      {/* Loading */}
      {(genMut.isPending) && s.phase === 'question' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center text-gray-400 text-sm">
          Генерация вопроса...
        </div>
      )}

      {/* Question */}
      {s.phase === 'question' && !genMut.isPending && s.question && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <p className="font-medium mb-5 leading-snug">{s.question.text}</p>
          <div className="grid gap-2 mb-5">
            {s.question.options.map((opt, i) => (
              <button
                key={i}
                onClick={() => setS(prev => ({ ...prev, selected: i }))}
                className={`text-left px-4 py-3 rounded-lg border text-sm transition-colors ${
                  s.selected === i
                    ? 'border-blue-500 bg-blue-900/30 text-white'
                    : 'border-gray-700 bg-gray-800 text-gray-300 hover:border-gray-500'
                }`}
              >
                <span className="text-gray-500 mr-2">{String.fromCharCode(65 + i)}.</span>
                {opt}
              </button>
            ))}
          </div>
          <button
            onClick={submitSelected}
            disabled={s.selected === null || submitMut.isPending}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-40 transition-colors"
          >
            {submitMut.isPending ? 'Проверка...' : 'Ответить'}
          </button>
        </div>
      )}

      {/* Feedback */}
      {s.phase === 'feedback' && s.feedback && s.question && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <div className={`flex items-center gap-2 text-lg font-semibold mb-4 ${s.feedback.is_correct ? 'text-green-400' : 'text-red-400'}`}>
            <span>{s.feedback.is_correct ? '✓' : '✗'}</span>
            <span>{s.feedback.is_correct ? 'Правильно' : 'Неправильно'}</span>
          </div>

          {/* Show all options with highlight */}
          <div className="grid gap-2 mb-4">
            {s.question.options.map((opt, i) => {
              const isCorrect = i === s.feedback!.correct_index;
              const isSelected = i === s.selected;
              let cls = 'border-gray-700 bg-gray-800 text-gray-500';
              if (isCorrect) cls = 'border-green-600 bg-green-900/20 text-green-300';
              else if (isSelected && !isCorrect) cls = 'border-red-600 bg-red-900/20 text-red-300';
              return (
                <div key={i} className={`px-4 py-3 rounded-lg border text-sm ${cls}`}>
                  <span className="mr-2 opacity-60">{String.fromCharCode(65 + i)}.</span>
                  {opt}
                </div>
              );
            })}
          </div>

          {s.feedback.explanation && (
            <p className="text-sm text-gray-300 leading-relaxed bg-gray-800 rounded-lg p-4 mb-5">
              {s.feedback.explanation}
            </p>
          )}

          <button
            onClick={nextQuestion}
            disabled={genMut.isPending}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-40 transition-colors"
          >
            {genMut.isPending ? 'Загрузка...' : s.total >= SESSION_SIZE ? 'Результаты' : `Следующий вопрос (${s.total}/${SESSION_SIZE})`}
          </button>
        </div>
      )}

      {/* Result */}
      {s.phase === 'result' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-4xl font-bold mb-2">
            {s.correct} / {SESSION_SIZE}
          </p>
          <p className="text-2xl font-semibold mb-1">
            {Math.round((s.correct / SESSION_SIZE) * 100)}%
          </p>
          <p className={`text-sm mb-6 ${
            s.correct / SESSION_SIZE >= 0.7 ? 'text-green-400' : 'text-yellow-400'
          }`}>
            {s.correct / SESSION_SIZE >= 0.9
              ? 'Отлично! Материал освоен.'
              : s.correct / SESSION_SIZE >= 0.7
              ? 'Хорошо. Рекомендуем повторить материал.'
              : 'Нужно повторить модуль перед следующей попыткой.'}
          </p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={startSession}
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
            >
              Пройти ещё раз
            </button>
            <button
              onClick={() => navigate('/modules')}
              className="px-5 py-2.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
            >
              К модулям
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
