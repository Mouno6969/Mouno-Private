import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiClient, getToken, setToken as persistToken, clearToken } from '../lib/apiClient';
import type { MeResponse, TelegramStats } from '../types';

interface User {
  username: string;
  telegram_id: string | null;
  telegram_stats?: TelegramStats | null;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, token: string, telegram_id: string | null) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(getToken());
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
    setUser(null);
  }, []);

  // Centralized 401 handling: apiClient dispatches this when a request is
  // rejected as unauthorized, so we log the user out from one place.
  useEffect(() => {
    const onUnauthorized = () => logout();
    window.addEventListener('auth:unauthorized', onUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', onUnauthorized);
  }, [logout]);

  useEffect(() => {
    let active = true;
    const fetchUser = async () => {
      if (token) {
        try {
          const res = await apiClient.get<MeResponse>('/api/me');
          if (active) {
            setUser({
              username: res.data.username,
              telegram_id: res.data.telegram_id,
              telegram_stats: res.data.telegram_stats,
            });
          }
        } catch {
          // apiClient already surfaced a toast / handled 401.
          if (active) logout();
        }
      }
      if (active) setLoading(false);
    };
    fetchUser();
    return () => {
      active = false;
    };
  }, [token, logout]);

  const login = (username: string, newToken: string, telegram_id: string | null) => {
    persistToken(newToken);
    setTokenState(newToken);
    setUser({ username, telegram_id });
  };

  const refreshUser = async () => {
    if (!token) return;
    try {
      const res = await apiClient.get<MeResponse>('/api/me');
      setUser({
        username: res.data.username,
        telegram_id: res.data.telegram_id,
        telegram_stats: res.data.telegram_stats,
      });
    } catch {
      /* apiClient handles error feedback */
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, refreshUser, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
