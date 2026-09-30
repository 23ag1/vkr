import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Top-level error boundary. Catches render-time throws anywhere in the tree
 * and shows a recoverable fallback instead of a blank white screen.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Surface for debugging — never silently swallow. Dev only, so production
    // doesn't leak component stacks to the browser console.
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught a render error:', error, info.componentStack);
    }
  }

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-gray-900 px-4 text-center text-gray-100">
          <h1 className="text-xl font-semibold">Что-то пошло не так</h1>
          <p className="max-w-md text-sm text-gray-400">
            Произошла непредвиденная ошибка. Попробуйте перезагрузить страницу.
          </p>
          <button
            type="button"
            onClick={this.handleReload}
            className="rounded-lg bg-blue-700 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600"
          >
            Перезагрузить
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
