'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { getApiBase } from '@/lib/apiBase';

interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_verified?: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string, opts?: { redirectTo?: string | null }) => Promise<void>;
  register: (email: string, password: string, firstName: string, lastName: string) => Promise<void>;
  logout: () => void;
  getToken: () => string | null;
  authFetch: (url: string, options?: RequestInit) => Promise<Response>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'jobscale_token';
const USER_KEY = 'jobscale_user';
const LEGACY_TOKEN_KEY = 'token';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const loadUser = async () => {
      const legacyToken = localStorage.getItem(LEGACY_TOKEN_KEY);
      if (legacyToken && !localStorage.getItem(TOKEN_KEY)) {
        localStorage.setItem(TOKEN_KEY, legacyToken);
        localStorage.removeItem(LEGACY_TOKEN_KEY);
      }

      const token = localStorage.getItem(TOKEN_KEY);

      if (token) {
        try {
          const storedUser = localStorage.getItem(USER_KEY);
          if (storedUser) {
            setUser(JSON.parse(storedUser));
          }
          await verifyToken(token);
        } catch (error) {
          console.error('Failed to load user:', error);
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(USER_KEY);
          setUser(null);
        }
      }
      setLoading(false);
    };

    loadUser();
  }, []);

  async function verifyToken(token: string) {
    const apiBase = getApiBase();
    try {
      const response = await fetch(`${apiBase}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) throw new Error('Token invalid');

      const userData = await response.json();
      setUser(userData);
      localStorage.setItem(USER_KEY, JSON.stringify(userData));
    } catch (error) {
      throw error;
    }
  }

  function syncTokenToExtension(token: string | null) {
    try {
      if (typeof window !== 'undefined' && (window as any).chrome?.runtime?.sendMessage) {
        if (token) {
          (window as any).chrome.runtime.sendMessage({ action: 'setToken', token });
        } else {
          (window as any).chrome.runtime.sendMessage({ action: 'clearToken' });
        }
      }
    } catch (e) {
      // Extension not installed
    }
  }

  async function login(email: string, password: string, opts?: { redirectTo?: string | null }) {
    const apiBase = getApiBase();

    const response = await fetch(`${apiBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    localStorage.setItem(TOKEN_KEY, data.access_token);
    syncTokenToExtension(data.access_token);

    const meRes = await fetch(`${apiBase}/auth/me`, {
      headers: { 'Authorization': `Bearer ${data.access_token}` },
    });

    if (meRes.ok) {
      const userData = await meRes.json();
      setUser(userData);
      localStorage.setItem(USER_KEY, JSON.stringify(userData));
    }

    const next = opts?.redirectTo?.trim();
    const dest = next && next.startsWith('/') && !next.startsWith('//') ? next : '/dashboard';
    router.push(dest);
  }

  async function register(email: string, password: string, firstName: string, lastName: string) {
    const apiBase = getApiBase();

    const response = await fetch(`${apiBase}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, first_name: firstName, last_name: lastName }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    const loginRes = await fetch(`${apiBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
    });

    if (!loginRes.ok) throw new Error('Auto-login failed');

    const loginData = await loginRes.json();
    localStorage.setItem(TOKEN_KEY, loginData.access_token);
    syncTokenToExtension(loginData.access_token);

    const meRes = await fetch(`${apiBase}/auth/me`, {
      headers: { 'Authorization': `Bearer ${loginData.access_token}` },
    });

    if (meRes.ok) {
      const userData = await meRes.json();
      setUser(userData);
      localStorage.setItem(USER_KEY, JSON.stringify(userData));
    }

    router.push('/quick-start');
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(LEGACY_TOKEN_KEY);
    syncTokenToExtension(null);
    setUser(null);
    router.push('/login');
  }

  function getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  async function authFetch(pathOrUrl: string, options: RequestInit = {}): Promise<Response> {
    const token = localStorage.getItem(TOKEN_KEY);
    const headers = new Headers(options.headers || {});
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
      headers.set('Content-Type', 'application/json');
    }
    let target = pathOrUrl;
    if (!pathOrUrl.startsWith('http://') && !pathOrUrl.startsWith('https://')) {
      const base = getApiBase().replace(/\/$/, '');
      if (pathOrUrl.startsWith('/api/v1')) {
        target = `${base}${pathOrUrl.slice('/api/v1'.length)}`;
      } else {
        target = `${base}${pathOrUrl.startsWith('/') ? pathOrUrl : `/${pathOrUrl}`}`;
      }
    }
    const response = await fetch(target, { ...options, headers });
    // Handle expired/invalid tokens globally so users get redirected to login
    // instead of seeing silent failures on protected pages.
    if (response.status === 401 && typeof window !== 'undefined') {
      const currentPath = window.location.pathname;
      const isProtected = !['/login', '/register', '/', '/terms', '/privacy', '/contact'].includes(currentPath)
        && !currentPath.startsWith('/billing/');
      if (isProtected) {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        localStorage.removeItem(LEGACY_TOKEN_KEY);
        syncTokenToExtension(null);
        setUser(null);
        // Redirect to login with a return path so the user can resume after re-auth
        const returnUrl = encodeURIComponent(currentPath);
        router.push(`/login?next=${returnUrl}&reason=expired`);
      }
    }
    return response;
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, getToken, authFetch }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
