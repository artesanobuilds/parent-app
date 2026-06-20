// Closed-beta auth store. The backend has NO password auth — it mints opaque
// bearer tokens bound to a user_id (see app/server.py /auth/issue-token).
//
// NOTE: real email/password (or Apple Sign-In) auth is a later step. For the
// closed beta the parent simply enters the same user_id the mobile app uses;
// we POST it to /auth/issue-token and keep the returned token in localStorage.

const TOKEN_KEY = 'pd_token';
const USER_KEY = 'pd_user_id';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUserId(): string | null {
  return localStorage.getItem(USER_KEY);
}

export function setSession(token: string, userId: string): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, userId);
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
