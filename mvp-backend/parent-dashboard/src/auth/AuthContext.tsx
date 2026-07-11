import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { exchangeLoginCode, issueToken, pairingLogin } from '../api';
import { identify, resetAnalytics } from '../analytics';
import {
  clearSession,
  getToken,
  getUserId,
  setSession,
  setV1Session,
} from './store';

interface AuthState {
  token: string | null;
  userId: string | null;
  isAuthed: boolean;
  /** Legacy: sign in by typing the user_id (kept for existing sessions). */
  login: (userId: string) => Promise<void>;
  /** Complete a Google web-redirect sign-in from its one-time login_code. */
  loginWithCode: (code: string) => Promise<void>;
  /** Sign in with a pairing code minted in the mobile app. */
  loginWithPairing: (code: string) => Promise<void>;
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

  const loginWithCode = useCallback(async (code: string) => {
    const s = await exchangeLoginCode(code);
    setV1Session(s.access_token, s.refresh_token, s.user_id, s.analytics_id);
    setToken(s.access_token);
    setUserId(s.user_id);
    identify(s.analytics_id);
  }, []);

  const loginWithPairing = useCallback(async (code: string) => {
    const s = await pairingLogin(code);
    setV1Session(s.access_token, s.refresh_token, s.user_id, s.analytics_id);
    setToken(s.access_token);
    setUserId(s.user_id);
    identify(s.analytics_id);
  }, []);

  const logout = useCallback(() => {
    clearSession();
    resetAnalytics();
    setToken(null);
    setUserId(null);
  }, []);

  const value = useMemo<AuthState>(
    () => ({ token, userId, isAuthed: !!token, login, loginWithCode, loginWithPairing, logout }),
    [token, userId, login, loginWithCode, loginWithPairing, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
  return ctx;
}
