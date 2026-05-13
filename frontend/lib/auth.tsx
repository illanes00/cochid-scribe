'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from 'react';
import { authApi } from '@/lib/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

interface User {
  email: string;
  name?: string;
  role?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  authenticated: boolean;
  refresh: () => Promise<void>;
  loginToWorkspace: (password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  authenticated: false,
  refresh: async () => {},
  loginToWorkspace: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    return fetch(`${API_BASE}/api/v1/auth/me`, { credentials: 'include' })
      .then((r) => r.json())
      .then((data) => {
        setUser(data.authenticated ? data.user : null);
      })
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }

  async function loginToWorkspace(password: string) {
    await authApi.workspaceLogin(password);
    await refresh();
  }

  useEffect(() => {
    fetch(`${API_BASE}/api/v1/auth/me`, { credentials: 'include' })
      .then((r) => r.json())
      .then((data) => {
        setUser(data.authenticated ? data.user : null);
      })
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, authenticated: !!user, refresh, loginToWorkspace }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
