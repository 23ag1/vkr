import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSessions, createSession, getMessages, sendMessage } from '../../api/mentor';
import ChatThread, { type ChatBubble } from '../../components/chat/ChatThread';
import ChatInput from '../../components/chat/ChatInput';
import { ErrorState } from '../../components/ui/ErrorState';

const LAST_SESSION_KEY = 'mentor_last_session';

export default function MentorPage() {
  const qc = useQueryClient();
  const [sessionId, setSessionId] = useState<string | null>(
    () => localStorage.getItem(LAST_SESSION_KEY),
  );
  const [input, setInput] = useState('');

  const { data: sessRes, isError: sessError, refetch: refetchSessions } = useQuery({ queryKey: ['sessions'], queryFn: getSessions });
  const sessions = sessRes?.data.data ?? [];

  // Restore active session after reload: keep stored one if still valid,
  // otherwise fall back to the most recent session.
  useEffect(() => {
    if (sessions.length === 0) return;
    const stillValid = sessionId && sessions.some(s => s.id === sessionId);
    if (!stillValid) setSessionId(sessions[0].id);
  }, [sessions, sessionId]);

  // Persist the active session so it survives a page refresh.
  useEffect(() => {
    if (sessionId) localStorage.setItem(LAST_SESSION_KEY, sessionId);
  }, [sessionId]);

  const { data: msgRes, isError: msgError, refetch: refetchMessages } = useQuery({
    queryKey: ['messages', sessionId],
    queryFn: () => getMessages(sessionId!),
    enabled: !!sessionId,
    refetchInterval: false,
  });
  const messages = msgRes?.data.data ?? [];

  const bubbles: ChatBubble[] = messages.map(m => ({
    key: m.id,
    side: m.role === 'user' ? 'right' : 'left',
    content: m.content,
    bubbleClassName: `max-w-[75%] ${
      m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-200'
    }`,
    footer:
      m.role === 'assistant' && m.sources?.documents && m.sources.documents.length > 0 ? (
        <div className="max-w-[75%] mt-1 flex flex-wrap gap-1 px-1">
          {m.sources.documents.map(doc => (
            <span
              key={doc.id}
              className="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-400 border border-gray-600"
              title={doc.title}
            >
              📄 {doc.title}
            </span>
          ))}
        </div>
      ) : undefined,
  }));

  const newSessionMut = useMutation({
    mutationFn: () => createSession(),
    onSuccess: ({ data }) => {
      setSessionId(data.data.id);
      qc.invalidateQueries({ queryKey: ['sessions'] });
    },
  });

  const sendMut = useMutation({
    mutationFn: (text: string) => sendMessage(sessionId!, text),
    onSuccess: () => {
      setInput('');
      qc.invalidateQueries({ queryKey: ['messages', sessionId] });
      qc.invalidateQueries({ queryKey: ['sessions'] });
    },
  });

  function handleSend() {
    if (!input.trim() || !sessionId) return;
    sendMut.mutate(input.trim());
  }

  return (
    <div className="flex h-[calc(100vh-2rem)] gap-4">
      <div className="w-52 shrink-0 flex flex-col gap-2">
        <button
          onClick={() => newSessionMut.mutate()}
          disabled={newSessionMut.isPending}
          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-xs font-medium disabled:opacity-50 transition-colors"
        >
          Новый чат
        </button>
        <div className="flex flex-col gap-1 overflow-y-auto">
          {sessError && (
            <ErrorState
              onRetry={() => refetchSessions()}
              message="Не удалось загрузить сессии"
              className="p-3"
            />
          )}
          {!sessError && sessions.map(s => (
            <button
              key={s.id}
              onClick={() => setSessionId(s.id)}
              className={`text-left px-3 py-2 rounded-lg text-xs transition-colors ${
                sessionId === s.id
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
            >
              {s.title || `Сессия ${s.id.slice(0, 6)}`}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        {!sessionId ? (
          <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">
            Выберите или создайте сессию
          </div>
        ) : msgError ? (
          <div className="flex-1 flex items-center justify-center p-4">
            <ErrorState
              onRetry={() => refetchMessages()}
              message="Не удалось загрузить сообщения"
              className="w-full max-w-sm"
            />
          </div>
        ) : (
          <>
            <ChatThread
              className="flex-1 overflow-y-auto p-4 space-y-3"
              messages={bubbles}
              loading={sendMut.isPending}
            />
            <ChatInput
              value={input}
              onChange={setInput}
              onSend={handleSend}
              placeholder="Задайте вопрос..."
              disabled={sendMut.isPending}
              variant="sm"
              className="p-3 border-t border-gray-800"
            />
          </>
        )}
      </div>
    </div>
  );
}
