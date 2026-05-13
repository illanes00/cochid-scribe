'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

interface User {
  email: string;
  name?: string;
  display_name?: string;
  role?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  authenticated: boolean;
  refresh: () => Promise<void>;
  loginWithSSO: () => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  authenticated: false,
  refresh: async () => {},
  loginWithSSO: () => {},
  logout: async () => {},
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

  function loginWithSSO() {
    if (typeof window === 'undefined') return;
    // Authentik OIDC login lives at /api/auth/login (NOT /api/v1/auth/...).
    window.location.href = '/api/auth/login';
  }

  async function logout() {
    try {
      await fetch(`${API_BASE}/api/v1/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } finally {
      setUser(null);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        authenticated: !!user,
        refresh,
        loginWithSSO,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
