import { create } from 'zustand';
import type { UserProfile } from '../api/auth';

interface AuthState {
  user: UserProfile | null;
  setUser: (user: UserProfile | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>(set => ({
  user: null,
  setUser: user => set({ user }),
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null });
  },
}));
