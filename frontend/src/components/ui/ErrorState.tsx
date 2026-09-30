interface ErrorStateProps {
  /** Re-runs the failed query. Wrap a TanStack Query `refetch` as `() => refetch()`. */
  onRetry: () => void;
  message?: string;
  className?: string;
}

/**
 * Distinct error UI for failed data loads: a red card with a Retry button.
 * Intentionally NOT styled like the muted gray empty state, so an API failure
 * is never mistaken for "no data".
 *
 * Takes a fixed contextual `message` ("Не удалось загрузить модули") rather than
 * the raw query error: for a load failure the *what* is more useful than a bare
 * "Request failed with status code 500". Server-provided error detail is surfaced
 * elsewhere — mutation failures route through getErrorMessage() + the toaster.
 */
export function ErrorState({
  onRetry,
  message = 'Не удалось загрузить данные',
  className = '',
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={`bg-red-900/20 border border-red-800/50 rounded-xl p-5 text-center ${className}`}
    >
      <p className="text-sm text-red-300 mb-3">{message}</p>
      <button
        onClick={onRetry}
        className="px-3 py-1.5 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium text-white transition-colors"
      >
        Повторить
      </button>
    </div>
  );
}
