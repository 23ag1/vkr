import { useEffect } from 'react';
import { useToastStore } from '../../store/toast';
import type { Toast, ToastVariant } from '../../store/toast';

const AUTO_DISMISS_MS = 5000;

const variantCls: Record<ToastVariant, string> = {
  error: 'bg-red-900 border-red-700 text-red-100',
  success: 'bg-green-900 border-green-700 text-green-100',
  info: 'bg-blue-900 border-blue-700 text-blue-100',
};

function ToastItem({ toast }: { toast: Toast }) {
  const removeToast = useToastStore(s => s.removeToast);

  useEffect(() => {
    const timer = setTimeout(() => removeToast(toast.id), AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [toast.id, removeToast]);

  return (
    <div
      role="alert"
      className={`flex items-start gap-3 rounded-lg border px-4 py-3 shadow-lg ${variantCls[toast.variant]}`}
    >
      <span className="flex-1 text-sm break-words">{toast.message}</span>
      <button
        type="button"
        aria-label="Закрыть"
        onClick={() => removeToast(toast.id)}
        className="shrink-0 text-lg leading-none opacity-70 hover:opacity-100"
      >
        ×
      </button>
    </div>
  );
}

export function Toaster() {
  const toasts = useToastStore(s => s.toasts);
  if (toasts.length === 0) return null;
  return (
    <div className="fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2 px-4 sm:px-0">
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  );
}
