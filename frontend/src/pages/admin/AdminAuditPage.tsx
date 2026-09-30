import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getAuditLogs, exportAuditCsv, type AuditLog } from '../../api/audit';

const ACTION_LABELS: Record<string, string> = {
  login: 'Вход',
  module_completed: 'Модуль завершён',
  test_answer_submitted: 'Ответ на тест',
  phishing_clicked: 'Клик по фишингу',
  phishing_reported: 'Фишинг отмечен',
  document_uploaded: 'Документ загружен',
  user_created: 'Пользователь создан',
  user_deactivated: 'Пользователь деактивирован',
  settings_changed: 'Настройки изменены',
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' });
}

export default function AdminAuditPage() {
  const [action, setAction] = useState('');
  const [page, setPage] = useState(1);

  const { data: res, isLoading } = useQuery({
    queryKey: ['audit', action, page],
    queryFn: () => getAuditLogs({ action: action || undefined, page, limit: 50 }),
  });

  const logs: AuditLog[] = res?.data.data ?? [];

  async function handleExport() {
    const resp = await exportAuditCsv({ action: action || undefined });
    const url = URL.createObjectURL(new Blob([resp.data as BlobPart]));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'audit_log.csv';
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Журнал аудита</h1>
        <button
          onClick={handleExport}
          className="text-sm px-4 py-1.5 rounded bg-gray-800 text-gray-300 hover:bg-gray-700 transition-colors"
        >
          Экспорт CSV
        </button>
      </div>

      <div className="mb-4 flex gap-3">
        <select
          value={action}
          onChange={e => { setAction(e.target.value); setPage(1); }}
          className="bg-gray-900 border border-gray-700 text-sm rounded px-3 py-1.5 text-gray-300"
        >
          <option value="">Все события</option>
          {Object.entries(ACTION_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-400">
              <th className="px-4 py-3 text-left font-medium">Время</th>
              <th className="px-4 py-3 text-left font-medium">Событие</th>
              <th className="px-4 py-3 text-left font-medium">Пользователь</th>
              <th className="px-4 py-3 text-left font-medium">IP</th>
              <th className="px-4 py-3 text-left font-medium">Детали</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-gray-500">Загрузка...</td></tr>
            )}
            {!isLoading && logs.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-6 text-center text-gray-500">Нет записей</td></tr>
            )}
            {logs.map(log => (
              <tr key={log.id} className="border-b border-gray-800 hover:bg-gray-800/40">
                <td className="px-4 py-3 text-gray-400 whitespace-nowrap">{formatDate(log.created_at)}</td>
                <td className="px-4 py-3 text-white">{ACTION_LABELS[log.action] ?? log.action}</td>
                <td className="px-4 py-3 text-gray-400 font-mono text-xs">{log.user_id?.slice(0, 8) ?? '—'}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">{log.ip_address ?? '—'}</td>
                <td className="px-4 py-3 text-gray-500 text-xs font-mono">
                  {log.details ? JSON.stringify(log.details) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex gap-3 mt-4">
        <button
          disabled={page <= 1}
          onClick={() => setPage(p => p - 1)}
          className="text-sm px-3 py-1 rounded bg-gray-800 text-gray-400 disabled:opacity-40 hover:bg-gray-700"
        >
          ← Назад
        </button>
        <span className="text-sm text-gray-500 py-1">Стр. {page}</span>
        <button
          disabled={logs.length < 50}
          onClick={() => setPage(p => p + 1)}
          className="text-sm px-3 py-1 rounded bg-gray-800 text-gray-400 disabled:opacity-40 hover:bg-gray-700"
        >
          Вперёд →
        </button>
      </div>
    </div>
  );
}
