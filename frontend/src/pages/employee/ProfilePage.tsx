import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '../../store/auth';
import { getUserProfile } from '../../api/analytics';
import { getMyPath } from '../../api/learning';
import { getModules } from '../../api/modules';
import { ProgressBadge } from '../../components/ui/ProgressBadge';
import { ErrorState } from '../../components/ui/ErrorState';
import type { UserRole } from '../../api/users';

const ROLE_LABEL: Record<UserRole, string> = {
  employee: 'Сотрудник',
  admin: 'Администратор',
  manager: 'Менеджер',
  security_specialist: 'Специалист ИБ',
};

export default function ProfilePage() {
  const user = useAuthStore(s => s.user);

  const { data: profileRes, isError: profileError, refetch: refetchProfile } = useQuery({
    queryKey: ['profile', user?.id],
    queryFn: () => getUserProfile(user!.id),
    enabled: !!user,
  });
  const { data: pathRes, isError: pathError, refetch: refetchPath } = useQuery({
    queryKey: ['my-path'],
    queryFn: getMyPath,
    enabled: !!user,
  });
  const { data: modRes, isError: modError, refetch: refetchModules } = useQuery({
    queryKey: ['modules'],
    queryFn: getModules,
  });

  // All three feed the displayed content; any failure means we'd show partial
  // or mislabelled data (raw UUIDs, zeroed stats), so surface one load error.
  const loadError = profileError || pathError || modError;
  const profile = profileRes?.data.data;
  const path = pathRes?.data.data ?? [];
  const moduleMap = Object.fromEntries(
    (modRes?.data.data ?? []).map(m => [m.id, m.title])
  );
  const completed = path.filter(p => p.status === 'completed');

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold mb-6">Мой профиль</h1>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-4 flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-lg font-semibold shrink-0">
          {user?.full_name?.charAt(0) ?? '?'}
        </div>
        <div>
          <p className="font-medium">{user?.full_name}</p>
          <p className="text-sm text-gray-400 mt-0.5">{user?.email}</p>
          <p className="text-xs text-gray-500 mt-0.5">
            {user?.role ? ROLE_LABEL[user.role] : ''}
          </p>
        </div>
      </div>

      {loadError && (
        <ErrorState
          onRetry={() => { refetchProfile(); refetchPath(); refetchModules(); }}
          message="Не удалось загрузить данные профиля"
        />
      )}

      {!loadError && (
        <>
      <div className="grid grid-cols-3 gap-3 mb-6">
        <Stat label="Завершено модулей" value={profile?.modules_completed ?? 0} />
        <Stat
          label="Средний балл"
          value={profile && profile.avg_score > 0 ? `${Math.round(profile.avg_score)}%` : '—'}
        />
        <Stat label="Кликов фишинг" value={profile?.phishing_clicks ?? 0} />
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="font-medium mb-3 text-sm">Прогресс обучения</h2>
        {path.length === 0 ? (
          <p className="text-gray-500 text-sm">Модули не назначены</p>
        ) : (
          <div className="divide-y divide-gray-800">
            {path.map(p => (
              <div key={p.id} className="flex justify-between items-center py-2 text-sm">
                <span className="text-gray-200">
                  {moduleMap[p.module_id] ?? p.module_id}
                </span>
                <ProgressBadge status={p.status} variant="text" />
              </div>
            ))}
          </div>
        )}
        <p className="text-xs text-gray-500 mt-3">
          {completed.length} / {path.length} модулей завершено
        </p>
      </div>
      </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-2xl font-semibold">{value}</p>
      <p className="text-xs text-gray-400 mt-1">{label}</p>
    </div>
  );
}
