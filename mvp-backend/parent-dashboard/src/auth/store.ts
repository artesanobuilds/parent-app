// Dashboard auth store. Phase 2: the backend issues a JWT access token + a
// rotating refresh token via Sign in with Google (web redirect) or a pairing
// code minted in the mobile app. Legacy /auth/issue-token still works for
// existing sessions during the migration.

const TOKEN_KEY = 'pd_token';        // access token (JWT) or legacy opaque token
const REFRESH_KEY = 'pd_refresh';    // rotating refresh token (v1 only)
const USER_KEY = 'pd_user_id';
const ANALYTICS_KEY = 'pd_analytics_id';  // opaque id for analytics (never the user_id)

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function getUserId(): string | null {
  return localStorage.getItem(USER_KEY);
}

export function getAnalyticsId(): string | null {
  return localStorage.getItem(ANALYTICS_KEY);
}

/** Store a v1 session (access + refresh + opaque analytics id). */
export function setV1Session(access: string, refresh: string, userId: string, analyticsId?: string): void {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
  localStorage.setItem(USER_KEY, userId);
  if (analyticsId) localStorage.setItem(ANALYTICS_KEY, analyticsId);
}

/** Update just the tokens after a refresh (keeps userId). */
export function updateTokens(access: string, refresh: string): void {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

/** Legacy: opaque token, no refresh. */
export function setSession(token: string, userId: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.setItem(USER_KEY, userId);
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem(ANALYTICS_KEY);
}
