import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getModules, createModule, updateModule, publishModule, deleteModule, Module, BRIEFING_TYPES, BRIEFING_LABEL } from '../../api/modules';
import { getUsers } from '../../api/users';
import { assignModule } from '../../api/learning';
import { FormInput, inputCls } from '../../components/ui/FormInput';
import { ErrorState } from '../../components/ui/ErrorState';

const ALL_ROLES = ['employee', 'manager', 'admin', 'security_specialist'];

interface FormState {
  title: string;
  description: string;
  content_md: string;
  order_index: string;
  target_roles: string[];
  briefing_type: string;
}

const EMPTY: FormState = { title: '', description: '', content_md: '', order_index: '0', target_roles: [], briefing_type: 'none' };

function moduleToForm(m: Module): FormState {
  return {
    title: m.title,
    description: m.description,
    content_md: m.content_md,
    order_index: String(m.order_index),
    target_roles: m.target_roles,
    briefing_type: m.briefing_type ?? 'none',
  };
}

export default function AdminModulesPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState<FormState>(EMPTY);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [assignTarget, setAssignTarget] = useState<string | null>(null);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [assignError, setAssignError] = useState<string | null>(null);

  const { data: res, isError, refetch } = useQuery({ queryKey: ['modules'], queryFn: getModules });
  const { data: usersRes } = useQuery({ queryKey: ['users'], queryFn: getUsers });
  const modules = res?.data.data ?? [];
  const users = usersRes?.data.data ?? [];

  const saveMut = useMutation({
    mutationFn: () =>
      editingId
        ? updateModule(editingId, {
            title: form.title,
            description: form.description,
            content_md: form.content_md,
            target_roles: form.target_roles,
            order_index: Number(form.order_index),
            briefing_type: form.briefing_type as Module['briefing_type'],
          })
        : createModule({
            title: form.title,
            description: form.description,
            content_md: form.content_md,
            target_roles: form.target_roles,
            order_index: Number(form.order_index),
            briefing_type: form.briefing_type as Module['briefing_type'],
          }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['modules'] });
      setForm(EMPTY);
      setEditingId(null);
      setShowForm(false);
    },
  });

  const publishMut = useMutation({
    mutationFn: (id: string) => publishModule(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['modules'] }),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteModule(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['modules'] }),
  });

  const assignMut = useMutation({
    mutationFn: async () => {
      const targets = selectedUsers;
      const results = await Promise.allSettled(
        targets.map(uid => assignModule(uid, assignTarget!))
      );
      const failedUsers = targets.filter((_, i) => results[i].status === 'rejected');
      return { total: targets.length, failedUsers };
    },
    onSuccess: ({ total, failedUsers }) => {
      // Refresh the learning path so a self-assigned module appears without a
      // reload. (Cross-session admin→employee live update is out of scope:
      // the prototype has no realtime push — see CLAUDE.md known constraints.)
      qc.invalidateQueries({ queryKey: ['my-path'] });
      if (failedUsers.length > 0) {
        // Keep only the failed users selected so a retry doesn't re-assign
        // the ones that already succeeded (avoids duplicate assignments).
        setSelectedUsers(failedUsers);
        setAssignError(`Не удалось назначить: ${failedUsers.length} из ${total}. Остальные назначены.`);
      } else {
        setAssignTarget(null);
        setSelectedUsers([]);
        setAssignError(null);
      }
    },
    onError: () => setAssignError('Не удалось назначить модуль. Попробуйте ещё раз.'),
    // Inline error is shown in the modal — suppress the global error toast.
    meta: { suppressGlobalError: true },
  });

  function openEdit(m: Module) {
    setForm(moduleToForm(m));
    setEditingId(m.id);
    setShowForm(true);
  }

  function openNew() {
    setForm(EMPTY);
    setEditingId(null);
    setShowForm(true);
  }

  function closeForm() {
    setForm(EMPTY);
    setEditingId(null);
    setShowForm(false);
  }

  function field(key: 'title' | 'description' | 'content_md' | 'order_index') {
    return {
      value: form[key] as string,
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
        setForm(prev => ({ ...prev, [key]: e.target.value })),
    };
  }

  function toggleUser(id: string) {
    setSelectedUsers(prev =>
      prev.includes(id) ? prev.filter(u => u !== id) : [...prev, id]
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold">Модули</h1>
        <button
          onClick={showForm ? closeForm : openNew}
          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
        >
          {showForm ? 'Отмена' : 'Создать'}
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
          <h2 className="font-medium mb-4 text-sm">{editingId ? 'Редактировать модуль' : 'Новый модуль'}</h2>
          <div className="grid gap-3">
            <FormInput label="Название" {...field('title')} />
            <FormInput label="Описание" {...field('description')} />
            <div>
              <label className="text-xs text-gray-400 block mb-1">Содержимое (Markdown)</label>
              <textarea {...field('content_md')} rows={10} className={inputCls} />
            </div>
            <FormInput label="Порядок" type="number" {...field('order_index')} />
            <div>
              <label className="text-xs text-gray-400 block mb-1">Целевые роли (пусто = базовый для всех)</label>
              <div className="flex gap-3 flex-wrap">
                {ALL_ROLES.map(r => (
                  <label key={r} className="flex items-center gap-1.5 text-sm text-gray-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={form.target_roles.includes(r)}
                      onChange={() => setForm(prev => ({
                        ...prev,
                        target_roles: prev.target_roles.includes(r)
                          ? prev.target_roles.filter(x => x !== r)
                          : [...prev.target_roles, r],
                      }))}
                      className="accent-blue-500"
                    />
                    {r}
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Вид инструктажа (ФСТЭК №21)</label>
              <select
                value={form.briefing_type}
                onChange={e => setForm(prev => ({ ...prev, briefing_type: e.target.value }))}
                className={inputCls}
              >
                {BRIEFING_TYPES.map(bt => (
                  <option key={bt} value={bt}>{BRIEFING_LABEL[bt]}</option>
                ))}
              </select>
            </div>
          </div>
          <button
            onClick={() => saveMut.mutate()}
            disabled={!form.title || saveMut.isPending}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
          >
            {saveMut.isPending ? 'Сохранение...' : editingId ? 'Сохранить' : 'Создать'}
          </button>
        </div>
      )}

      {/* Assign modal */}
      {assignTarget && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => { if (!assignMut.isPending) { setAssignTarget(null); setAssignError(null); } }}>
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
            <h2 className="font-medium mb-4">Назначить модуль сотрудникам</h2>
            {assignError && (
              <p role="alert" className="mb-3 text-xs text-red-400 bg-red-900/20 border border-red-900/40 rounded-lg px-3 py-2">{assignError}</p>
            )}
            <div className="max-h-60 overflow-y-auto grid gap-1.5 mb-4">
              {users.map(u => (
                <label key={u.id} className="flex items-center gap-2 cursor-pointer text-sm text-gray-300 hover:text-white">
                  <input
                    type="checkbox"
                    checked={selectedUsers.includes(u.id)}
                    onChange={() => toggleUser(u.id)}
                    className="accent-blue-500"
                  />
                  <span>{u.full_name}</span>
                  <span className="text-gray-500 text-xs ml-auto">{u.email}</span>
                </label>
              ))}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => { setAssignError(null); assignMut.mutate(); }}
                disabled={selectedUsers.length === 0 || assignMut.isPending}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
              >
                {assignMut.isPending ? 'Назначение...' : `Назначить (${selectedUsers.length})`}
              </button>
              <button onClick={() => { setAssignTarget(null); setAssignError(null); }} disabled={assignMut.isPending} className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm disabled:opacity-50 transition-colors">
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-3">
        {isError && <ErrorState onRetry={() => refetch()} message="Не удалось загрузить модули" />}
        {!isError && modules.map(m => (
          <div key={m.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="font-medium text-sm">{m.title}</p>
                  {m.is_published
                    ? <span className="text-xs text-green-400 bg-green-900/30 px-2 py-0.5 rounded-full">Опубликован</span>
                    : <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">Черновик</span>}
                  {m.target_roles.length === 0
                    ? <span className="text-xs text-blue-400 bg-blue-900/20 px-2 py-0.5 rounded-full">Базовый</span>
                    : m.target_roles.map(r => (
                        <span key={r} className="text-xs text-purple-400 bg-purple-900/20 px-2 py-0.5 rounded-full">{r}</span>
                      ))}
                  {m.briefing_type && m.briefing_type !== 'none' && (
                    <span className="text-xs text-orange-400 bg-orange-900/20 px-2 py-0.5 rounded-full">{BRIEFING_LABEL[m.briefing_type]}</span>
                  )}
                </div>
                <p className="text-xs text-gray-400 mt-0.5 truncate">{m.description}</p>
                <p className="text-xs text-gray-600 mt-0.5">{m.content_md.length} символов контента</p>
              </div>
              <div className="flex items-center gap-3 ml-4 shrink-0">
                <button onClick={() => { setAssignTarget(m.id); setSelectedUsers([]); setAssignError(null); }} className="text-xs text-blue-400 hover:text-blue-300 transition-colors">
                  Назначить
                </button>
                <button onClick={() => openEdit(m)} className="text-xs text-gray-400 hover:text-white transition-colors">
                  Изменить
                </button>
                {!m.is_published && (
                  <button onClick={() => publishMut.mutate(m.id)} className="text-xs text-yellow-400 hover:text-yellow-300 transition-colors">
                    Опубликовать
                  </button>
                )}
                <button onClick={() => deleteMut.mutate(m.id)} className="text-xs text-red-400 hover:text-red-300 transition-colors">
                  Удалить
                </button>
              </div>
            </div>
          </div>
        ))}
        {!isError && modules.length === 0 && <p className="text-gray-500 text-sm">Нет модулей</p>}
      </div>
    </div>
  );
}
