import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';

interface AuthContextValue {
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Previously the app read `localStorage.getItem('token')` directly inside
 * App.tsx's render body. That value isn't reactive - React has no way of
 * knowing it changed - so after a successful login the screen stayed on
 * the login page until a manual refresh, because nothing ever told React
 * to re-render. This context wraps the token in real state so login/logout
 * actually update the UI, and also reacts to the axios 401 interceptor
 * (see api/client.ts) which dispatches 'auth:logout' when a token expires.
 */
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));

  const login = useCallback((newToken: string) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setToken(null);
  }, []);

  useEffect(() => {
    const handleAuthLogout = () => setToken(null);
    window.addEventListener('auth:logout', handleAuthLogout);
    return () => window.removeEventListener('auth:logout', handleAuthLogout);
  }, []);

  return (
    <AuthContext.Provider value={{ token, isAuthenticated: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
