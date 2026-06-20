import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { issueToken } from '../api';
import { clearSession, getToken, getUserId, setSession } from './store';

interface AuthState {
  token: string | null;
  userId: string | null;
  isAuthed: boolean;
  login: (userId: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getToken());
  const [userId, setUserId] = useState<string | null>(() => getUserId());

  const login = useCallback(async (id: string) => {
    const trimmed = id.trim();
    const res = await issueToken(trimmed);
    setSession(res.token, res.user_id);
    setToken(res.token);
    setUserId(res.user_id);
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setToken(null);
    setUserId(null);
  }, []);

  const value = useMemo<AuthState>(
    () => ({ token, userId, isAuthed: !!token, login, logout }),
    [token, userId, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
  return ctx;
}
