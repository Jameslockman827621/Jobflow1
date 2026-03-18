'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: number;
  email: string;
  is_active: boolean;
  is_verified?: boolean;
  first_name?: string;
  last_name?: string;
}

interface RegisterData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  getToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'jobscale_token';
const USER_KEY = 'jobscale_user';
const LEGACY_TOKEN_KEY = 'token';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Load user from localStorage on mount
  useEffect(() => {
    const loadUser = async () => {
      // Migrate from legacy "token" key if present
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
    const apiBase = process.env.NEXT_PUBLIC_API_URL ||
      (process.env.NEXT_PUBLIC_BACKEND_URL ? `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1` : null) ||
      '/api/v1';
    try {
      const response = await fetch(`${apiBase}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Token invalid');
      }

      const userData = await response.json();
      setUser(userData);
      localStorage.setItem(USER_KEY, JSON.stringify(userData));
    } catch (error) {
      throw error;
    }
  }

  async function login(email: string, password: string) {
    const apiBase = process.env.NEXT_PUBLIC_API_URL ||
      (process.env.NEXT_PUBLIC_BACKEND_URL ? `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1` : null) ||
      '/api/v1';

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

    // Fetch user from /me (backend login only returns token)
    const meRes = await fetch(`${apiBase}/auth/me`, {
      headers: { Authorization: `Bearer ${data.access_token}` },
    });
    if (meRes.ok) {
      const userData = await meRes.json();
      localStorage.setItem(USER_KEY, JSON.stringify(userData));
      setUser(userData);
    }

    router.push('/dashboard');
  }

  async function register(data: RegisterData) {
    const apiBase = process.env.NEXT_PUBLIC_API_URL ||
      (process.env.NEXT_PUBLIC_BACKEND_URL ? `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1` : null) ||
      '/api/v1';

    const response = await fetch(`${apiBase}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    // Backend register doesn't return token - auto-login
    const loginRes = await fetch(`${apiBase}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: data.email, password: data.password }),
    });

    if (!loginRes.ok) throw new Error('Login after registration failed');

    const loginData = await loginRes.json();
    localStorage.setItem(TOKEN_KEY, loginData.access_token);

    const meRes = await fetch(`${apiBase}/auth/me`, {
      headers: { Authorization: `Bearer ${loginData.access_token}` },
    });
    if (meRes.ok) {
      const userData = await meRes.json();
      localStorage.setItem(USER_KEY, JSON.stringify(userData));
      setUser(userData);
    }

    router.push('/onboarding');
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(LEGACY_TOKEN_KEY);
    setUser(null);
    router.push('/login');
  }

  function getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        getToken,
      }}
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
