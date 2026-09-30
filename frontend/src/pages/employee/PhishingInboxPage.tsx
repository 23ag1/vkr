import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getMyInbox, reportPhishing, trackClick, InboxItem } from '../../api/phishing';

const DIFFICULTY_LABEL: Record<string, string> = {
  easy: 'Низкая',
  medium: 'Средняя',
  hard: 'Высокая',
};

const DIFFICULTY_CLS: Record<string, string> = {
  easy: 'text-green-400 bg-green-900/30',
  medium: 'text-yellow-400 bg-yellow-900/30',
  hard: 'text-red-400 bg-red-900/30',
};

export default function PhishingInboxPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState<InboxItem | null>(null);
  const [clickedTokens, setClickedTokens] = useState<Set<string>>(new Set());

  const { data: res, isLoading } = useQuery({
    queryKey: ['phishing-inbox'],
    queryFn: getMyInbox,
  });
  const items = res?.data.data ?? [];

  const reportMut = useMutation({
    mutationFn: (token: string) => reportPhishing(token),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['phishing-inbox'] }),
  });

  function handleClick(item: InboxItem) {
    trackClick(item.tracking_token);
    setClickedTokens(prev => new Set([...prev, item.tracking_token]));
  }

  const active = items.filter(i => i.campaign_status === 'active');
  const past = items.filter(i => i.campaign_status !== 'active');

  return (
    <div className="max-w-3xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold mb-1">Симуляция фишинга</h1>
        <p className="text-sm text-gray-400">
          Тренировка распознавания фишинговых писем. Получив подозрительное сообщение — сообщи о нём, не переходи по ссылкам.
        </p>
      </div>

      {isLoading && <p className="text-gray-500 text-sm">Загрузка...</p>}

      {!isLoading && items.length === 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center">
          <p className="text-gray-400 text-sm">Нет активных фишинговых кампаний</p>
          <p className="text-gray-600 text-xs mt-1">Администратор запустит кампанию — она появится здесь</p>
        </div>
      )}

      {active.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Активные ({active.length})</h2>
          <div className="grid gap-2">
            {active.map(item => (
              <InboxCard
                key={item.id}
                item={item}
                wasClicked={clickedTokens.has(item.tracking_token)}
                onOpen={() => setOpen(item)}
                onReport={() => reportMut.mutate(item.tracking_token)}
                reporting={reportMut.isPending}
              />
            ))}
          </div>
        </div>
      )}

      {past.length > 0 && (
        <div>
          <h2 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Завершённые ({past.length})</h2>
          <div className="grid gap-2">
            {past.map(item => (
              <InboxCard
                key={item.id}
                item={item}
                wasClicked={clickedTokens.has(item.tracking_token)}
                onOpen={() => setOpen(item)}
                onReport={() => reportMut.mutate(item.tracking_token)}
                reporting={reportMut.isPending}
              />
            ))}
          </div>
        </div>
      )}

      {open && (
        <EmailModal
          item={open}
          wasClicked={clickedTokens.has(open.tracking_token)}
          onClose={() => setOpen(null)}
          onClickLink={() => handleClick(open)}
          onReport={() => { reportMut.mutate(open.tracking_token); setOpen(null); }}
          reporting={reportMut.isPending}
        />
      )}
    </div>
  );
}

interface CardProps {
  item: InboxItem;
  wasClicked: boolean;
  onOpen: () => void;
  onReport: () => void;
  reporting: boolean;
}

function InboxCard({ item, wasClicked, onOpen, onReport, reporting }: CardProps) {
  const didClick = wasClicked || !!item.clicked_at;
  const didReport = !!item.reported_at;

  return (
    <div className={`bg-gray-900 border rounded-xl p-4 transition-colors ${
      didReport ? 'border-green-800' : didClick ? 'border-red-800' : 'border-gray-800'
    }`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-xs text-gray-500">IT-Security</span>
            <span className={`text-xs px-1.5 py-0.5 rounded ${DIFFICULTY_CLS[item.difficulty] ?? 'text-gray-400 bg-gray-800'}`}>
              {DIFFICULTY_LABEL[item.difficulty] ?? item.difficulty}
            </span>
          </div>
          <p className="text-sm font-medium truncate">{item.subject}</p>
          <p className="text-xs text-gray-500 mt-0.5">{item.campaign_name}</p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {didReport
            ? <span className="text-xs text-green-400">Сообщено</span>
            : didClick
            ? <span className="text-xs text-red-400">Клик</span>
            : null}
          <button onClick={onOpen} className="text-xs text-blue-400 hover:text-blue-300 transition-colors">
            Открыть
          </button>
          {!didReport && item.campaign_status === 'active' && (
            <button
              onClick={onReport}
              disabled={reporting}
              className="text-xs text-gray-400 hover:text-green-400 transition-colors disabled:opacity-50"
            >
              Сообщить
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface ModalProps {
  item: InboxItem;
  wasClicked: boolean;
  onClose: () => void;
  onClickLink: () => void;
  onReport: () => void;
  reporting: boolean;
}

function EmailModal({ item, wasClicked, onClose, onClickLink, onReport, reporting }: ModalProps) {
  const didClick = wasClicked || !!item.clicked_at;
  const didReport = !!item.reported_at;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-2xl max-h-[85vh] flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="px-6 py-4 border-b border-gray-800 flex items-start justify-between">
          <div>
            <p className="text-xs text-gray-500 mb-0.5">От: security-team@corp-it.ru</p>
            <p className="font-medium">{item.subject}</p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors ml-4 shrink-0">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* Hidden tracking pixel — fires when modal mounts, records opened_at */}
          <img src={`/phishing/track/${item.tracking_token}/open`} alt="" width={1} height={1} className="hidden" />
          {/* Email body rendered as plain text (NOT as raw HTML for XSS safety) */}
          <div className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
            {item.body_html.replace(/<[^>]+>/g, '')}
          </div>

          {/* Simulated link */}
          <div className="mt-4 p-3 bg-gray-800 rounded-lg border border-gray-700">
            <p className="text-xs text-gray-500 mb-2">Ссылка в письме:</p>
            <button
              onClick={onClickLink}
              className="text-sm text-blue-400 underline hover:text-blue-300 transition-colors"
            >
              http://corp-login.ru/verify-account?token=xK9mP2
            </button>
          </div>
        </div>

        {/* Feedback banners */}
        {didClick && !didReport && (
          <div className="mx-6 mb-4 p-3 bg-red-900/30 border border-red-700 rounded-lg">
            <p className="text-sm text-red-300 font-medium mb-0.5">Вы перешли по ссылке!</p>
            <p className="text-xs text-red-400">
              В реальной атаке это могло привести к краже данных или заражению устройства.
              Всегда проверяйте адрес отправителя и домен ссылки перед переходом.
            </p>
          </div>
        )}
        {didReport && (
          <div className="mx-6 mb-4 p-3 bg-green-900/30 border border-green-700 rounded-lg">
            <p className="text-sm text-green-300 font-medium mb-0.5">Отлично! Вы распознали фишинг</p>
            <p className="text-xs text-green-400">
              Сообщение передано в службу безопасности. Именно так и нужно реагировать на подозрительные письма.
            </p>
          </div>
        )}

        <div className="px-6 py-4 border-t border-gray-800 flex gap-2">
          {!didReport && item.campaign_status === 'active' && (
            <button
              onClick={onReport}
              disabled={reporting}
              className="px-4 py-2 bg-green-700 hover:bg-green-600 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
            >
              {reporting ? 'Отправка...' : 'Сообщить о подозрительном письме'}
            </button>
          )}
          <button onClick={onClose} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors">
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
}
