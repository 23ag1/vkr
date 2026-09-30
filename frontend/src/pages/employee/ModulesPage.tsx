import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getModules } from '../../api/modules';
import { getMyPath } from '../../api/learning';
import { ProgressBadge } from '../../components/ui/ProgressBadge';
import { ErrorState } from '../../components/ui/ErrorState';

export default function ModulesPage() {
  const { data: modRes, isError: modError, refetch: refetchModules } = useQuery({ queryKey: ['modules'], queryFn: getModules });
  const { data: pathRes, isError: pathError, refetch: refetchPath } = useQuery({ queryKey: ['my-path'], queryFn: getMyPath });

  // A my-path failure would silently render every card with the wrong progress
  // badge, so treat either query failing as a load error for the whole list.
  const isError = modError || pathError;
  const modules = modRes?.data.data ?? [];
  const progressMap = Object.fromEntries(
    (pathRes?.data.data ?? []).map(p => [p.module_id, p])
  );

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">Модули обучения</h1>
      <div className="grid gap-4">
        {isError && (
          <ErrorState
            onRetry={() => { refetchModules(); refetchPath(); }}
            message="Не удалось загрузить модули"
          />
        )}
        {!isError && modules.map(m => {
          const p = progressMap[m.id];
          return (
            <Link
              key={m.id}
              to={`/modules/${m.id}`}
              className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-600 transition-colors flex items-center justify-between"
            >
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="font-medium text-white">{m.title}</p>
                  {m.target_roles.length === 0 && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-gray-700 text-gray-400">Базовый</span>
                  )}
                </div>
                <p className="text-sm text-gray-400 mt-1">{m.description}</p>
              </div>
              <ProgressBadge status={p?.status ?? 'not_started'} />
            </Link>
          );
        })}
        {!isError && modules.length === 0 && (
          <p className="text-gray-500">Нет доступных модулей</p>
        )}
      </div>
    </div>
  );
}
