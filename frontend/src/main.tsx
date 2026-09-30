import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider, MutationCache } from '@tanstack/react-query';
import App from './App';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Toaster } from './components/ui/Toaster';
import { addToast } from './store/toast';
import { getErrorMessage } from './lib/errorMessage';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
  // Global handler: every failed mutation surfaces a toast, including future ones.
  // A mutation can opt out (e.g. when it renders its own inline error) by setting
  // meta.suppressGlobalError, avoiding a duplicate error surface.
  mutationCache: new MutationCache({
    onError: (error, _vars, _ctx, mutation) => {
      if (mutation.meta?.suppressGlobalError) return;
      addToast(getErrorMessage(error), 'error');
    },
  }),
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* Toaster sits outside the boundary so toasts survive a render-crash fallback. */}
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
    <Toaster />
  </StrictMode>,
);
