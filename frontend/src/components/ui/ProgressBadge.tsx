type ProgressStatus = 'not_started' | 'in_progress' | 'completed';

const badgeCls: Record<ProgressStatus, string> = {
  not_started: 'bg-gray-700 text-gray-300',
  in_progress: 'bg-blue-900 text-blue-300',
  completed: 'bg-green-900 text-green-300',
};

const textCls: Record<ProgressStatus, string> = {
  not_started: 'text-gray-400',
  in_progress: 'text-blue-400',
  completed: 'text-green-400',
};

const labels: Record<ProgressStatus, string> = {
  not_started: 'Не начат',
  in_progress: 'В процессе',
  completed: 'Завершён',
};

interface Props {
  status: string;
  variant?: 'badge' | 'text';
}

export function ProgressBadge({ status, variant = 'badge' }: Props) {
  const s = (status as ProgressStatus) in labels ? (status as ProgressStatus) : 'not_started';
  if (variant === 'text') {
    return <span className={`text-xs ${textCls[s]}`}>{labels[s]}</span>;
  }
  return (
    <span className={`text-xs px-2 py-1 rounded-full shrink-0 ml-4 ${badgeCls[s]}`}>
      {labels[s]}
    </span>
  );
}
