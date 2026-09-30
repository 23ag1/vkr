import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getModule } from '../../api/modules';
import { getMyPath, updateProgress } from '../../api/learning';
import { ProgressBadge } from '../../components/ui/ProgressBadge';
import { ErrorState } from '../../components/ui/ErrorState';

export default function ModuleViewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: modRes, isError, refetch } = useQuery({
    queryKey: ['module', id],
    queryFn: () => getModule(id!),
    enabled: !!id,
  });
  const { data: pathRes, isLoading: pathLoading } = useQuery({
    queryKey: ['my-path'],
    queryFn: getMyPath,
  });

  const module = modRes?.data.data;
  const progress = (pathRes?.data.data ?? []).find(p => p.module_id === id);

  const startMut = useMutation({
    mutationFn: (progressId: string) => updateProgress(progressId, 'in_progress'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['my-path'] }),
  });

  const completeMut = useMutation({
    mutationFn: (progressId: string) => updateProgress(progressId, 'completed'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['my-path'] });
      navigate('/modules');
    },
  });

  // 'my-path' is settled only once the query has fetched at least once; until then
  // a missing `progress` means "still loading", not "not assigned".
  const pathSettled = !pathLoading && pathRes !== undefined;

  if (isError) {
    return (
      <div className="max-w-3xl">
        <ErrorState onRetry={() => refetch()} message="Не удалось загрузить модуль" />
      </div>
    );
  }
  if (!module) return <div className="text-gray-400">Загрузка...</div>;

  return (
    <div className="max-w-3xl">
      <button
        onClick={() => navigate('/modules')}
        className="text-sm text-gray-400 hover:text-white mb-4 transition-colors"
      >
        ← Назад
      </button>
      <h1 className="text-2xl font-semibold mb-2">{module.title}</h1>
      <p className="text-gray-400 mb-6 text-sm">{module.description}</p>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6 whitespace-pre-wrap text-sm text-gray-300 leading-relaxed">
        {module.content_md || 'Содержимое модуля отсутствует.'}
      </div>

      <div className="flex gap-3">
        {!pathSettled && (
          <span className="text-gray-400 text-sm self-center">Загрузка статуса...</span>
        )}
        {pathSettled && !progress && (
          <span className="text-yellow-400 text-sm font-medium self-center">
            Этот модуль вам не назначен — обратитесь к администратору.
          </span>
        )}
        {progress?.status === 'not_started' && (
          <button
            onClick={() => startMut.mutate(progress.id)}
            disabled={startMut.isPending}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
          >
            Начать
          </button>
        )}
        {progress?.status === 'in_progress' && (
          <>
            <button
              onClick={() => completeMut.mutate(progress.id)}
              disabled={completeMut.isPending}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
            >
              Завершить модуль
            </button>
            <button
              onClick={() => navigate(`/testing?module_id=${id}`)}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
            >
              Пройти тест
            </button>
          </>
        )}
        {progress?.status === 'completed' && (
          <span className="self-center">
            <ProgressBadge status="completed" variant="text" />
          </span>
        )}
      </div>
    </div>
  );
}
