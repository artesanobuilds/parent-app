// API client for the parent dashboard. Attaches the closed-beta bearer token
// (see src/auth/store.ts). Dev: vite proxies /auth /research /cos to :8904.
import { getToken, getUserId } from '../auth/store';
import type {
  AuthTokenResponse,
  Candidate,
  CalendarEntry,
  FamilyProfile,
  PlanSummary,
  ResearchProgress,
  ResearchRun,
  ResearchRunStatus,
  Todo,
  TrackedActivity,
} from '../types';

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  const token = getToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (init?.body) headers.set('Content-Type', 'application/json');
  const res = await fetch(path, { ...init, headers });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function uid(): string {
  const u = getUserId();
  if (!u) throw new Error('Not authenticated');
  return u;
}

// ── Auth ────────────────────────────────────────────────────────────
export async function issueToken(userId: string): Promise<AuthTokenResponse> {
  const res = await fetch('/auth/issue-token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!res.ok) throw new Error(`Sign-in failed (${res.status})`);
  return (await res.json()) as AuthTokenResponse;
}

// ── Profile ─────────────────────────────────────────────────────────
export const getProfile = () => api<FamilyProfile>('/profile');

// Partial-update the parent profile (snake_case keys → values; lists replaced).
export const updateProfile = (fields: Record<string, unknown>) =>
  api<FamilyProfile>('/profile', {
    method: 'PATCH',
    body: JSON.stringify({ user_id: uid(), ...fields }),
  });

// Partial-update (or create) a child profile.
export const updateKid = (name: string, fields: Record<string, unknown>) =>
  api<FamilyProfile>(`/profile/kids/${encodeURIComponent(name)}`, {
    method: 'PATCH',
    body: JSON.stringify({ user_id: uid(), ...fields }),
  });

// Remove a child profile.
export const deleteKid = (name: string) =>
  api<FamilyProfile>(`/profile/kids/${encodeURIComponent(name)}`, {
    method: 'DELETE',
  });

// ── Discovery ───────────────────────────────────────────────────────
export const createResearchRun = (
  params?: Record<string, unknown>,
  location?: Record<string, unknown>,
) =>
  api<{ run_id: string; status: string }>('/research/runs', {
    method: 'POST',
    body: JSON.stringify({
      user_id: uid(),
      params: params ?? {},
      ...(location ? { location } : {}),
    }),
  });

export const getResearchRun = (id: string) =>
  api<ResearchRunStatus>(`/research/runs/${id}`);

export const listResearchRuns = () =>
  api<{ runs: ResearchRun[] }>('/research/runs').then((r) => r.runs);

export const getCandidates = (id: string) =>
  api<{ candidates: Candidate[] }>(`/research/runs/${id}/candidates`).then(
    (r) => r.candidates,
  );

// Live discovery progress over SSE — the client holds ONE connection instead of
// polling /research/runs/{id} every 2s. `onProgress` fires per frame; resolves on
// the terminal frame / [DONE]. Mirrors streamCosChat (fetch + reader so we can send
// the Bearer header — EventSource can't). Caller reconciles the final state.
export interface ResearchStreamFrame {
  status: string;
  progress?: ResearchProgress;
  candidate_count?: number;
  error?: string | null;
}
export async function streamResearchRun(
  id: string,
  onProgress: (frame: ResearchStreamFrame) => void,
): Promise<void> {
  const res = await fetch(`/research/runs/${id}/stream`, {
    headers: { Authorization: `Bearer ${getToken() ?? ''}` },
  });
  if (!res.ok || !res.body) throw new Error(`Stream failed (${res.status})`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      if (!line.startsWith('data:')) continue;
      const data = line.slice(5).trim();
      if (data === '[DONE]') return;
      try {
        const ev = JSON.parse(data) as Partial<ResearchStreamFrame> & { type?: string };
        if (ev.status) {
          onProgress({
            status: ev.status,
            progress: ev.progress,
            candidate_count: ev.candidate_count,
            error: ev.error,
          });
        }
      } catch {
        /* ignore non-JSON keepalives */
      }
    }
  }
}

// ── Chief-of-staff plan ─────────────────────────────────────────────
export const getActivities = () =>
  api<{ activities: TrackedActivity[] }>('/cos/activities').then((r) => r.activities);

// Pin/save an activity. Defaults to the "exploring" shortlist (R1). Pass
// candidate_id when saving a discovery candidate so it links back.
export const trackActivity = (body: {
  name: string;
  candidate_id?: string;
  kid_name?: string | null;
  provider?: string | null;
  status?: string;
  price_amount?: number | null;
  signup_url?: string | null;
}) =>
  api<{ id: string }>('/cos/activities/track', {
    method: 'POST',
    body: JSON.stringify({ user_id: uid(), status: 'exploring', ...body }),
  });

// Un-track an activity (un-pin from the Exploring shortlist).
export const deleteActivity = (id: string) =>
  api<{ id: string; deleted: boolean }>(`/cos/activities/${id}`, { method: 'DELETE' });

export const getTodos = (status?: string) =>
  api<{ todos: Todo[] }>(`/cos/todos${status ? `?status=${status}` : ''}`).then(
    (r) => r.todos,
  );

export const addTodo = (title: string) =>
  api<{ id: string }>('/cos/todos', {
    method: 'POST',
    body: JSON.stringify({ user_id: uid(), title }),
  });

export const patchTodo = (id: string, status: string) =>
  api<{ id: string }>(`/cos/todos/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ user_id: uid(), status }),
  });

export const getCalendar = (weekStart?: string) =>
  api<{ entries: CalendarEntry[] }>(
    `/cos/calendar${weekStart ? `?week_start=${weekStart}` : ''}`,
  ).then((r) => r.entries ?? []);

export const getPlanSummary = () => api<PlanSummary>('/cos/plan/summary');

// ── Plan export / share ─────────────────────────────────────────────
export type ShareScope = 'full' | 'logistics' | 'therapy';

export interface ShareLink {
  token: string;
  scope: ShareScope;
  url: string;
}

export interface ShareLinkRecord {
  scope: ShareScope;
  label: string | null;
  created_at: string | null;
  expires_at: string | null;
  revoked: boolean;
}

// Download the family plan as an .xlsx. Uses a raw fetch (not api(), which
// JSON-parses) so we can read the streamed blob, but reuses the same bearer auth.
export async function downloadPlanXlsx(): Promise<void> {
  const headers = new Headers();
  const token = getToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const res = await fetch('/cos/plan/export.xlsx', { headers });
  if (!res.ok) throw new Error(`Export failed (${res.status})`);
  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  try {
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = 'family-plan.xlsx';
    document.body.appendChild(a);
    a.click();
    a.remove();
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

// Mint a public read-only share link for the plan at the given scope.
export const createShareLink = (scope: ShareScope, label?: string) =>
  api<ShareLink>('/cos/plan/share', {
    method: 'POST',
    body: JSON.stringify({ user_id: uid(), scope, ...(label ? { label } : {}) }),
  });

// List previously-minted share links.
export const getShareLinks = () =>
  api<{ shares: ShareLinkRecord[] }>('/cos/plan/shares').then((r) => r.shares);

// ── Chief-of-staff chat (SSE) ───────────────────────────────────────
export async function streamCosChat(
  message: string,
  threadId: string,
  onToken: (t: string) => void,
): Promise<void> {
  const res = await fetch('/cos/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getToken() ?? ''}`,
    },
    body: JSON.stringify({ user_id: uid(), thread_id: threadId, message }),
  });
  if (!res.ok || !res.body) throw new Error(`Chat failed (${res.status})`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      if (!line.startsWith('data:')) continue;
      const data = line.slice(5).trim();
      if (data === '[DONE]') return;
      try {
        const ev = JSON.parse(data) as { type?: string; content?: string };
        if (ev.type === 'token' && ev.content) onToken(ev.content);
      } catch {
        /* ignore non-JSON keepalives */
      }
    }
  }
}
