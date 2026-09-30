import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
} from 'recharts';
import { getOverview, getDepartments, getMaturity } from '../../api/analytics';

type Tab = 'overview' | 'departments' | 'maturity';

export default function AdminAnalyticsPage() {
  const [tab, setTab] = useState<Tab>('overview');

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Аналитика</h1>
      <div className="flex gap-1 mb-6 border-b border-gray-800">
        {(['overview', 'departments', 'maturity'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t
                ? 'border-blue-500 text-white'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            {t === 'overview' ? 'Обзор' : t === 'departments' ? 'По подразделениям' : 'Зрелость SANS'}
          </button>
        ))}
      </div>
      {tab === 'overview' ? <OverviewTab /> : tab === 'departments' ? <DepartmentsTab /> : <MaturityTab />}
    </div>
  );
}

function OverviewTab() {
  const { data: res } = useQuery({ queryKey: ['analytics-overview'], queryFn: getOverview });
  const ov = res?.data.data;

  const barData = ov
    ? [
        { name: 'Завершаемость', value: Math.round(ov.completion_rate * 100), color: '#3B82F6' },
        { name: 'Ср. балл', value: Math.round(ov.avg_score * 100), color: '#3B82F6' },
        { name: 'Откр. фишинг', value: Math.round((ov.phishing_open_rate ?? 0) * 100), color: '#F59E0B' },
        { name: 'Клики фишинг', value: Math.round(ov.phishing_click_rate * 100), color: '#EF4444' },
        { name: 'Сабмит фишинг', value: Math.round((ov.phishing_submit_rate ?? 0) * 100), color: '#DC2626' },
        { name: 'Репорт фишинг', value: Math.round((ov.phishing_report_rate ?? 0) * 100), color: '#10B981' },
      ]
    : [];

  if (!ov) return <p className="text-gray-500 text-sm">Загрузка данных...</p>;

  return (
    <div>
      <div className="grid grid-cols-2 gap-3 mb-8 sm:grid-cols-4">
        <Stat label="Всего сотрудников" value={ov.total_users} />
        <Stat label="Завершаемость" value={`${Math.round(ov.completion_rate * 100)}%`} />
        <Stat label="Средний балл" value={ov.avg_score > 0 ? `${Math.round(ov.avg_score * 100)}%` : '—'} />
        <Stat label="Клики фишинг" value={`${Math.round(ov.phishing_click_rate * 100)}%`} />
        <Stat label="Открыли фишинг" value={`${Math.round((ov.phishing_open_rate ?? 0) * 100)}%`} />
        <Stat label="Ввели данные" value={`${Math.round((ov.phishing_submit_rate ?? 0) * 100)}%`} />
        <Stat label="Сообщили" value={`${Math.round((ov.phishing_report_rate ?? 0) * 100)}%`} />
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-sm font-medium mb-4">Ключевые показатели (%)</h2>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={barData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" tick={{ fill: '#9CA3AF', fontSize: 11 }} />
            <YAxis domain={[0, 100]} tick={{ fill: '#9CA3AF', fontSize: 12 }} />
            <Tooltip
              contentStyle={{ background: '#1F2937', border: '1px solid #374151', borderRadius: 8 }}
              labelStyle={{ color: '#F9FAFB' }}
              formatter={(v: number) => [`${v}%`]}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {barData.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function DepartmentsTab() {
  const { data: res, isLoading } = useQuery({
    queryKey: ['analytics-departments'],
    queryFn: getDepartments,
  });
  const depts = res?.data.data ?? [];

  if (isLoading) return <p className="text-gray-500 text-sm">Загрузка...</p>;
  if (depts.length === 0) return <p className="text-gray-500 text-sm">Нет данных по подразделениям</p>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs text-gray-500 uppercase tracking-wide border-b border-gray-800">
            <th className="text-left py-2 pr-4">Подразделение</th>
            <th className="text-right py-2 px-4">Сотрудников</th>
            <th className="text-right py-2 px-4">Завершаемость</th>
            <th className="text-right py-2 px-4">Средний балл</th>
            <th className="text-right py-2 pl-4">Клики фишинг</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {depts.map(dept => (
            <tr key={dept.id} className="hover:bg-gray-900/50 transition-colors">
              <td className="py-3 pr-4 font-medium">{dept.name}</td>
              <td className="py-3 px-4 text-right text-gray-400">{dept.total_users}</td>
              <td className="py-3 px-4 text-right">
                <Rate value={dept.completion_rate} high="#10B981" low="#EF4444" />
              </td>
              <td className="py-3 px-4 text-right">
                <Rate value={dept.avg_score} high="#10B981" low="#EF4444" />
              </td>
              <td className="py-3 pl-4 text-right">
                <Rate value={dept.phishing_click_rate} high="#EF4444" low="#10B981" invert />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MaturityTab() {
  const { data: res, isLoading } = useQuery({ queryKey: ['analytics-maturity'], queryFn: getMaturity });
  const m = res?.data.data;

  if (isLoading || !m) return <p className="text-gray-500 text-sm">Загрузка...</p>;

  const levelColors = ['', '#EF4444', '#F59E0B', '#3B82F6', '#8B5CF6', '#10B981'];
  const color = levelColors[m.level] ?? '#6B7280';

  return (
    <div className="space-y-6">
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-medium text-gray-400">Уровень зрелости (SANS)</h2>
          <span className="text-xs text-gray-500">Оценка: {m.score}/100</span>
        </div>
        <div className="flex items-baseline gap-3 mb-1">
          <span className="text-5xl font-bold" style={{ color }}>{m.level}</span>
          <span className="text-xl font-semibold text-white">{m.label}</span>
        </div>
        <p className="text-sm text-gray-400">{m.description}</p>

        <div className="mt-4 h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all"
            style={{ width: `${m.score}%`, background: color }}
          />
        </div>

        <div className="flex justify-between mt-1 text-xs text-gray-600">
          {[1, 2, 3, 4, 5].map(l => (
            <span key={l} style={{ color: l === m.level ? color : undefined }}>{l}</span>
          ))}
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-sm font-medium mb-3">Индикаторы зрелости</h3>
        <div className="space-y-2">
          {m.indicators.map((ind, i) => (
            <div key={i} className="flex items-center gap-3">
              <span className={`text-sm ${ind.met ? 'text-green-400' : 'text-red-400'}`}>
                {ind.met ? '✓' : '✗'}
              </span>
              <span className={`text-sm ${ind.met ? 'text-gray-200' : 'text-gray-500'}`}>
                {ind.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Rate({ value, high, low, invert = false }: { value: number; high: string; low: string; invert?: boolean }) {
  const pct = Math.round(value * 100);
  const color = invert ? (pct > 20 ? high : low) : (pct >= 70 ? high : low);
  return <span style={{ color }}>{pct}%</span>;
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-2xl font-semibold">{value}</p>
      <p className="text-xs text-gray-400 mt-1">{label}</p>
    </div>
  );
}
