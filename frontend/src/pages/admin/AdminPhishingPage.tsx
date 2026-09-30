import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getTemplates, createTemplate, deleteTemplate,
  getCampaigns, createCampaign, launchCampaign, completeCampaign, getCampaignResults,
  Template,
} from '../../api/phishing';
import { getUsers } from '../../api/users';
import { FormField, inputCls } from '../../components/ui/FormInput';
import { ErrorState } from '../../components/ui/ErrorState';

type Tab = 'templates' | 'campaigns';

export default function AdminPhishingPage() {
  const [tab, setTab] = useState<Tab>('campaigns');

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Фишинг</h1>
      <div className="flex gap-1 mb-6 border-b border-gray-800">
        {(['campaigns', 'templates'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm transition-colors border-b-2 -mb-px ${
              tab === t ? 'border-blue-500 text-white' : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            {t === 'campaigns' ? 'Кампании' : 'Шаблоны'}
          </button>
        ))}
      </div>
      {tab === 'campaigns' ? <CampaignsTab /> : <TemplatesTab />}
    </div>
  );
}

interface TemplateForm {
  name: string;
  subject: string;
  body_html: string;
  difficulty: string;
}

const EMPTY_TEMPLATE: TemplateForm = { name: '', subject: '', body_html: '', difficulty: 'easy' };

function TemplatesTab() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<TemplateForm>(EMPTY_TEMPLATE);

  const { data: res, isError, refetch } = useQuery({ queryKey: ['templates'], queryFn: getTemplates });
  const templates = res?.data.data ?? [];

  const createMut = useMutation({
    mutationFn: () => createTemplate(form as Omit<Template, 'id'>),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['templates'] });
      setForm(EMPTY_TEMPLATE);
      setShowForm(false);
    },
  });
  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteTemplate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['templates'] }),
  });

  function f(key: keyof TemplateForm) {
    return {
      value: form[key],
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
        setForm(prev => ({ ...prev, [key]: e.target.value })),
    };
  }

  return (
    <div>
      <div className="flex justify-end mb-4">
        <button
          onClick={() => setShowForm(s => !s)}
          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
        >
          {showForm ? 'Отмена' : 'Создать шаблон'}
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-4">
          <div className="grid gap-3">
            <FormField label="Название"><input {...f('name')} className={inputCls} /></FormField>
            <FormField label="Тема письма"><input {...f('subject')} className={inputCls} /></FormField>
            <FormField label="Тело (HTML)">
              <textarea {...f('body_html')} rows={4} className={inputCls} />
            </FormField>
            <FormField label="Сложность">
              <select {...f('difficulty')} className={inputCls}>
                <option value="easy">Низкая</option>
                <option value="medium">Средняя</option>
                <option value="hard">Высокая</option>
              </select>
            </FormField>
          </div>
          <button
            onClick={() => createMut.mutate()}
            disabled={!form.name || createMut.isPending}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
          >
            Создать
          </button>
        </div>
      )}

      <div className="grid gap-2">
        {isError && <ErrorState onRetry={() => refetch()} message="Не удалось загрузить шаблоны" />}
        {!isError && templates.map(t => (
          <div key={t.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex justify-between items-center">
            <div>
              <p className="text-sm font-medium">{t.name}</p>
              <p className="text-xs text-gray-400 mt-0.5">{t.subject} · {t.difficulty}</p>
            </div>
            <button onClick={() => deleteMut.mutate(t.id)} className="text-xs text-red-400 hover:text-red-300 transition-colors">
              Удалить
            </button>
          </div>
        ))}
        {!isError && templates.length === 0 && <p className="text-gray-500 text-sm">Нет шаблонов</p>}
      </div>
    </div>
  );
}

interface CampaignForm {
  name: string;
  templateId: string;
  selectedUsers: string[];
}

const EMPTY_CAMPAIGN: CampaignForm = { name: '', templateId: '', selectedUsers: [] };

function CampaignsTab() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<CampaignForm>(EMPTY_CAMPAIGN);
  const [viewCampaign, setViewCampaign] = useState<string | null>(null);

  const { data: campRes, isError: campError, refetch: refetchCampaigns } = useQuery({ queryKey: ['campaigns'], queryFn: getCampaigns });
  const { data: tmplRes } = useQuery({ queryKey: ['templates'], queryFn: getTemplates });
  const { data: usersRes } = useQuery({ queryKey: ['users'], queryFn: getUsers });
  const { data: resultsRes } = useQuery({
    queryKey: ['campaign-results', viewCampaign],
    queryFn: () => getCampaignResults(viewCampaign!),
    enabled: !!viewCampaign,
  });

  const campaigns = campRes?.data.data ?? [];
  const templates = tmplRes?.data.data ?? [];
  const users = usersRes?.data.data ?? [];
  const results = resultsRes?.data.data ?? [];
  const userMap = Object.fromEntries(users.map(u => [u.id, u.full_name]));

  const createMut = useMutation({
    mutationFn: () => createCampaign(form.name, form.templateId, form.selectedUsers),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['campaigns'] });
      setForm(EMPTY_CAMPAIGN);
      setShowForm(false);
    },
  });
  const launchMut = useMutation({
    mutationFn: (id: string) => launchCampaign(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['campaigns'] }),
  });
  const completeMut = useMutation({
    mutationFn: (id: string) => completeCampaign(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['campaigns'] }),
  });

  function toggleUser(id: string) {
    setForm(prev => ({
      ...prev,
      selectedUsers: prev.selectedUsers.includes(id)
        ? prev.selectedUsers.filter(u => u !== id)
        : [...prev.selectedUsers, id],
    }));
  }

  return (
    <div>
      <div className="flex justify-end mb-4">
        <button
          onClick={() => setShowForm(s => !s)}
          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
        >
          {showForm ? 'Отмена' : 'Создать кампанию'}
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-4">
          <div className="grid gap-3">
            <FormField label="Название">
              <input value={form.name} onChange={e => setForm(prev => ({ ...prev, name: e.target.value }))} className={inputCls} />
            </FormField>
            <FormField label="Шаблон">
              <select value={form.templateId} onChange={e => setForm(prev => ({ ...prev, templateId: e.target.value }))} className={inputCls}>
                <option value="">Выберите шаблон</option>
                {templates.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </FormField>
            <div>
              <label className="text-xs text-gray-400 block mb-2">Получатели</label>
              <div className="max-h-40 overflow-y-auto grid gap-1">
                {users.map(u => (
                  <label key={u.id} className="flex items-center gap-2 cursor-pointer text-sm text-gray-300">
                    <input
                      type="checkbox"
                      checked={form.selectedUsers.includes(u.id)}
                      onChange={() => toggleUser(u.id)}
                      className="accent-blue-500"
                    />
                    {u.full_name} <span className="text-gray-500 text-xs">{u.email}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
          <button
            onClick={() => createMut.mutate()}
            disabled={!form.name || !form.templateId || form.selectedUsers.length === 0 || createMut.isPending}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
          >
            Создать
          </button>
        </div>
      )}

      <div className="grid gap-3">
        {campError && <ErrorState onRetry={() => refetchCampaigns()} message="Не удалось загрузить кампании" />}
        {!campError && campaigns.map(c => (
          <div key={c.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <p className="text-sm font-medium">{c.name}</p>
                <CampaignStatusBadge status={c.status} />
              </div>
              <div className="flex gap-2">
                {c.status === 'draft' && (
                  <button onClick={() => launchMut.mutate(c.id)} className="text-xs text-blue-400 hover:text-blue-300 transition-colors">
                    Запустить
                  </button>
                )}
                {c.status === 'active' && (
                  <button onClick={() => completeMut.mutate(c.id)} className="text-xs text-yellow-400 hover:text-yellow-300 transition-colors">
                    Завершить
                  </button>
                )}
                <button
                  onClick={() => setViewCampaign(prev => prev === c.id ? null : c.id)}
                  className="text-xs text-gray-400 hover:text-white transition-colors"
                >
                  Результаты
                </button>
              </div>
            </div>

            {viewCampaign === c.id && (
              <div className="mt-3 pt-3 border-t border-gray-800">
                {results.length === 0 ? (
                  <p className="text-xs text-gray-500">Нет данных</p>
                ) : (
                  <div className="grid gap-1">
                    {results.map(r => (
                      <div key={r.id} className="flex gap-4 text-xs text-gray-400">
                        <span className="truncate w-32">{userMap[r.user_id] ?? r.user_id.slice(0, 8)}</span>
                        <span className={r.clicked_at ? 'text-red-400' : 'text-gray-500'}>
                          {r.clicked_at ? 'Кликнул' : 'Не кликнул'}
                        </span>
                        <span className={r.reported_at ? 'text-green-400' : ''}>
                          {r.reported_at ? 'Сообщил' : ''}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {!campError && campaigns.length === 0 && <p className="text-gray-500 text-sm">Нет кампаний</p>}
      </div>
    </div>
  );
}

type CampaignStatus = 'draft' | 'active' | 'completed';

const campaignCls: Record<CampaignStatus, string> = {
  draft: 'text-gray-400',
  active: 'text-blue-400',
  completed: 'text-green-400',
};
const campaignLabel: Record<CampaignStatus, string> = {
  draft: 'Черновик',
  active: 'Активна',
  completed: 'Завершена',
};

function CampaignStatusBadge({ status }: { status: string }) {
  const s = status as CampaignStatus;
  return <span className={`text-xs ${campaignCls[s] ?? 'text-gray-400'}`}>{campaignLabel[s] ?? status}</span>;
}
