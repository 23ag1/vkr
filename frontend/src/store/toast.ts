import { create } from 'zustand';

export type ToastVariant = 'error' | 'success' | 'info';

export interface Toast {
  id: string;
  message: string;
  variant: ToastVariant;
}

interface ToastState {
  toasts: Toast[];
  addToast: (message: string, variant?: ToastVariant) => string;
  removeToast: (id: string) => void;
}

const MAX_TOASTS = 5;

let counter = 0;
const nextId = () => `toast-${++counter}`;

export const useToastStore = create<ToastState>(set => ({
  toasts: [],
  addToast: (message, variant = 'info') => {
    const id = nextId();
    // Immutable append, capped to the newest MAX_TOASTS so a burst of failures
    // can't flood the screen. Never mutate the existing array.
    set(state => ({
      toasts: [...state.toasts.slice(-(MAX_TOASTS - 1)), { id, message, variant }],
    }));
    return id;
  },
  removeToast: id =>
    set(state => ({ toasts: state.toasts.filter(t => t.id !== id) })),
}));

// Imperative helper for use outside React (e.g. react-query MutationCache).
export const addToast = (message: string, variant: ToastVariant = 'info') =>
  useToastStore.getState().addToast(message, variant);
