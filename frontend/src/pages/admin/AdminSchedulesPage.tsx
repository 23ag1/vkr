import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSchedules, createSchedule, deleteSchedule, triggerSchedule } from '../../api/schedules';
import { getModules } from '../../api/modules';
import { ErrorState } from '../../components/ui/ErrorState';

const CADENCES = ['monthly', 'quarterly', 'annual'];
const CADENCE_LABEL: Record<string, string> = { monthly: 'Ежемесячно', quarterly: 'Ежеквартально', annual: 'Ежегодно' };
const ALL_ROLES = ['employee', 'manager', 'security_specialist'];

export default function AdminSchedulesPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ action: 'assign_module', cadence: 'quarterly', module_id: '', target_roles: ['employee'] });
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null);

  const { data: schedRes, isError, refetch } = useQuery({ queryKey: ['schedules'], queryFn: getSchedules });
  const schedules = schedRes?.data.data ?? [];

  const { data: modRes } = useQuery({ queryKey: ['modules-all'], queryFn: () => getModules() });
  const modules = modRes?.data.data ?? [];

  const createMut = useMutation({
    mutationFn: () => createSchedule({
      action: form.action,
      cadence: form.cadence,
      module_id: form.module_id || undefined,
      target_roles: form.target_roles,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['schedules'] }); setShowForm(false); },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteSchedule(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['schedules'] }),
  });

  const triggerMut = useMutation({
    mutationFn: (id: string) => triggerSchedule(id),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['schedules'] });
      setTriggerMsg(`Назначено: ${res.data.data.assigned} пользователей`);
      setTimeout(() => setTriggerMsg(null), 4000);
    },
  });

  function toggleRole(role: string) {
    setForm(f => ({
      ...f,
      target_roles: f.target_roles.includes(role)
        ? f.target_roles.filter(r => r !== role)
        : [...f.target_roles, role],
    }));
  }

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold mb-1">Расписания обучения</h1>
          <p className="text-sm text-gray-400">Автоматическое назначение модулей по расписанию</p>
        </div>
        <button
          onClick={() => setShowForm(v => !v)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
        >
          + Новое расписание
        </button>
      </div>

      {triggerMsg && (
        <div className="mb-4 px-4 py-2 bg-green-900/40 border border-green-700 rounded-lg text-sm text-green-300">
          {triggerMsg}
        </div>
      )}

      {showForm && (
        <div className="bg-gray-900 border border-gray-700 rounded-xl p-5 mb-6">
          <h2 className="text-sm font-medium mb-4">Новое расписание</h2>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Модуль</label>
              <select
                value={form.module_id}
                onChange={e => setForm(f => ({ ...f, module_id: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white"
              >
                <option value="">— выберите модуль —</option>
                {modules.map(m => (
                  <option key={m.id} value={m.id}>{m.title}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Периодичность</label>
              <select
                value={form.cadence}
                onChange={e => setForm(f => ({ ...f, cadence: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white"
              >
                {CADENCES.map(c => <option key={c} value={c}>{CADENCE_LABEL[c]}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Роли</label>
              <div className="flex flex-wrap gap-2">
                {ALL_ROLES.map(role => (
                  <button
                    key={role}
                    type="button"
                    onClick={() => toggleRole(role)}
                    className={`px-3 py-1 rounded-full text-xs border transition-colors ${
                      form.target_roles.includes(role)
                        ? 'bg-blue-600 border-blue-500 text-white'
                        : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500'
                    }`}
                  >
                    {role}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => createMut.mutate()}
                disabled={!form.module_id || createMut.isPending}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm disabled:opacity-50 transition-colors"
              >
                Создать
              </button>
              <button
                onClick={() => setShowForm(false)}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {isError && <ErrorState onRetry={() => refetch()} message="Не удалось загрузить расписания" />}

      {!isError && schedules.length === 0 && !showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
          <p className="text-gray-400 text-sm">Нет активных расписаний</p>
        </div>
      )}

      <div className="space-y-2">
        {!isError && schedules.map(s => (
          <div key={s.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">{CADENCE_LABEL[s.cadence] ?? s.cadence} — {s.action}</p>
                {s.target_roles.length > 0 && (
                  <p className="text-xs text-gray-500 mt-0.5">Роли: {s.target_roles.join(', ')}</p>
                )}
                {s.last_triggered_at && (
                  <p className="text-xs text-gray-600 mt-0.5">
                    Последний запуск: {new Date(s.last_triggered_at).toLocaleDateString('ru-RU')}
                  </p>
                )}
              </div>
              <div className="flex gap-2 shrink-0">
                <button
                  onClick={() => triggerMut.mutate(s.id)}
                  disabled={triggerMut.isPending}
                  className="text-xs px-3 py-1.5 bg-green-800 hover:bg-green-700 rounded-lg text-green-300 transition-colors disabled:opacity-50"
                >
                  Запустить
                </button>
                <button
                  onClick={() => deleteMut.mutate(s.id)}
                  className="text-xs px-3 py-1.5 bg-gray-700 hover:bg-red-800 rounded-lg text-gray-400 hover:text-red-300 transition-colors"
                >
                  Удалить
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
