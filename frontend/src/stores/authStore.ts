import { create } from 'zustand';
import { User } from '../types';
import api from '../services/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<any>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true });
    try {
      const response = await api.login(email, password);

      if (response.requires_mfa) {
        set({ isLoading: false });
        return { requires_mfa: true };
      }

      localStorage.setItem('access_token', response.access_token);
      set({
        user: response.user,
        isAuthenticated: true,
        isLoading: false,
      });
      return { success: true };
    } catch (error: any) {
      set({ isLoading: false });
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  },

  register: async (data: any) => {
    set({ isLoading: true });
    try {
      await api.register(data);
      set({ isLoading: false });
    } catch (error: any) {
      set({ isLoading: false });
      throw new Error(error.response?.data?.detail || 'Registration failed');
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    set({
      user: null,
      isAuthenticated: false,
    });
  },

  checkAuth: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isAuthenticated: false, user: null });
      return;
    }

    try {
      const user = await api.getCurrentUser();
      set({
        user,
        isAuthenticated: true,
      });
    } catch (error) {
      localStorage.removeItem('access_token');
      set({
        user: null,
        isAuthenticated: false,
      });
    }
  },
}));
