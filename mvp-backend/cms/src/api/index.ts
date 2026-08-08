import type { Article, Category, ContentStats } from '../types';

const API = '';

// Admin auth: an HttpOnly session cookie minted by POST /admin/session (see
// pages/Login.tsx). The old scheme baked VITE_ADMIN_TOKEN into this bundle at
// build time — i.e. shipped the operator secret to every visitor's browser.
// The cookie is invisible to JS; we just send credentials + the CSRF marker.
function withAdminHeaders(init?: RequestInit): RequestInit {
  const headers = new Headers(init?.headers ?? {});
  headers.set('X-Requested-With', 'cms');
  if (init?.body !== undefined && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  return { ...init, headers, credentials: 'same-origin' };
}

function redirectToLogin(): void {
  // basename is /cms (see main.tsx); preserve where the user was.
  const here = window.location.pathname + window.location.search;
  window.location.assign(`/cms/login?from=${encodeURIComponent(here)}`);
}

async function fetchJSON<T>(url: string, init?: RequestInit, retries = 3): Promise<T> {
  const isAdmin = url.startsWith('/cms/') || url.includes(`${API}/cms/`);
  const finalInit = isAdmin ? withAdminHeaders(init) : init;
  let lastError: Error = new Error('Request failed');
  for (let attempt = 0; attempt <= retries; attempt++) {
    if (attempt > 0) {
      await new Promise<void>(resolve => setTimeout(resolve, 2 ** (attempt - 1) * 200));
    }
    let res: Response;
    try {
      res = await fetch(url, finalInit);
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
      continue;
    }
    if (res.ok) {
      return res.json();
    }
    if (res.status === 401 && isAdmin && !window.location.pathname.endsWith('/login')) {
      redirectToLogin();
    }
    const body = await res.text();
    lastError = new Error(`${res.status}: ${body}`);
    if (res.status < 500 && res.status !== 429) {
      throw lastError;
    }
  }
  throw lastError;
}

// Session (CMS login/logout)
export async function createSession(token: string): Promise<void> {
  const res = await fetch(`${API}/admin/session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({ token }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(res.status === 401 ? 'Invalid admin token' : `${res.status}: ${body}`);
  }
}

export const destroySession = () =>
  fetch(`${API}/admin/session`, { method: 'DELETE', credentials: 'same-origin' }).then(() => undefined);

// Categories
export const getCategories = () => fetchJSON<Category[]>(`${API}/content/categories`);
export const createCategory = (data: Category) =>
  fetchJSON<Category>(`${API}/cms/categories`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
export const updateCategory = (id: string, data: Partial<Category>) =>
  fetchJSON<Category>(`${API}/cms/categories/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
export const deleteCategory = (id: string) =>
  fetchJSON<{ deleted: boolean }>(`${API}/cms/categories/${id}`, { method: 'DELETE' });

// Articles
export const getArticles = (category?: string) =>
  fetchJSON<Article[]>(`${API}/content/articles${category ? `?category=${category}` : ''}`);
export const getArticle = (id: string) => fetchJSON<Article>(`${API}/content/articles/${id}`);
export const createArticle = (data: Article) =>
  fetchJSON<Article>(`${API}/cms/articles`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
export const updateArticle = (id: string, data: Partial<Article>) =>
  fetchJSON<Article>(`${API}/cms/articles/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
export const deleteArticle = (id: string) =>
  fetchJSON<{ deleted: boolean }>(`${API}/cms/articles/${id}`, { method: 'DELETE' });

// Stats & Export
export const getStats = () => fetchJSON<ContentStats>(`${API}/cms/stats`);
export const exportParquet = () =>
  fetchJSON<{ exported: boolean }>(`${API}/cms/export-parquet`, { method: 'POST' });

// Email Sync (R3) — admin agent control
export interface EmailSyncSchedule {
  enabled: boolean;
  hour: number; // 0-23
  tz: string;
}
export interface EmailSyncItem {
  sender: string | null;
  subject: string | null;
  received_at?: string | null;
  matched: string | null; // activity name, or null if unmatched
  action: string; // ingested | skipped_duplicate | extract_failed
  created?: { calendar: number; todos: number };
  error?: string;
}
export interface EmailSyncDetail {
  account_email: string | null;
  query: string | null;
  note: string | null;
  items: EmailSyncItem[];
}
export interface EmailSyncRun {
  id: string;
  user_id: string;
  status: string; // queued|running|done|failed
  trigger: string; // manual|scheduled
  messages_seen: number;
  activities_touched: number;
  error: string | null;
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  progress?: { phase?: string; detail?: EmailSyncDetail } | null;
}

export const getEmailSyncConfig = () =>
  fetchJSON<EmailSyncSchedule>(`${API}/cms/email-sync/config`);

export const putEmailSyncConfig = (cfg: EmailSyncSchedule) =>
  fetchJSON<EmailSyncSchedule>(`${API}/cms/email-sync/config`, {
    method: 'PUT',
    body: JSON.stringify(cfg),
  });

export const runEmailSyncNow = () =>
  fetchJSON<{ enqueued: number; run_ids: string[] }>(`${API}/cms/email-sync/run`, {
    method: 'POST',
  });

export const getEmailSyncRuns = () =>
  fetchJSON<{ runs: EmailSyncRun[] }>(`${API}/cms/email-sync/runs`).then((r) => r.runs);

// Calendar Sync (R4 part 2) — two-way Google Calendar sync admin control
export interface CalendarSyncSchedule {
  enabled: boolean;
  hour: number; // 0-23
  tz: string;
}
export interface CalendarSyncPushItem {
  title: string;
  start?: string | null;
  action: string; // created | updated | push_failed
  error?: string;
}
export interface CalendarSyncPullItem {
  title: string;
  start?: string | null;
  action: string; // imported | updated
}
export interface CalendarSyncDetail {
  account_email: string | null;
  note: string | null;
  pushed_items: CalendarSyncPushItem[];
  pulled_items: CalendarSyncPullItem[];
}
export interface CalendarSyncRun {
  id: string;
  user_id: string;
  status: string; // queued|running|done|failed
  trigger: string; // manual|scheduled
  pushed: number;
  pulled: number;
  error: string | null;
  created_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  progress?: { phase?: string; detail?: CalendarSyncDetail } | null;
}

export const getCalendarSyncConfig = () =>
  fetchJSON<CalendarSyncSchedule>(`${API}/cms/calendar-sync/config`);

export const putCalendarSyncConfig = (cfg: CalendarSyncSchedule) =>
  fetchJSON<CalendarSyncSchedule>(`${API}/cms/calendar-sync/config`, {
    method: 'PUT',
    body: JSON.stringify(cfg),
  });

export const runCalendarSyncNow = () =>
  fetchJSON<{ enqueued: number; run_ids: string[] }>(`${API}/cms/calendar-sync/run`, {
    method: 'POST',
  });

export const getCalendarSyncRuns = () =>
  fetchJSON<{ runs: CalendarSyncRun[] }>(`${API}/cms/calendar-sync/runs`).then((r) => r.runs);

// ── Legal documents (versioned publish; see /cms/legal endpoints) ──────────

export interface LegalDoc {
  id: string;
  slug: string;
  version: string;
  title: string;
  body_md: string;
  effective_date: string | null;
  requires_reacceptance: boolean;
  published_at: string | null;
  published_by: string | null;
  is_current: boolean;
}

export interface LegalOverviewEntry {
  slug: string;
  current: LegalDoc | null;
  draft: LegalDoc | null;
  version_count: number;
}

export const getLegalOverview = () =>
  fetchJSON<{ documents: LegalOverviewEntry[] }>(`${API}/cms/legal`).then((r) => r.documents);

export const getLegalVersions = (slug: string) =>
  fetchJSON<{ versions: LegalDoc[] }>(`${API}/cms/legal/${slug}/versions`).then((r) => r.versions);

export const putLegalDraft = (slug: string, title: string, body_md: string) =>
  fetchJSON<LegalDoc>(`${API}/cms/legal/${slug}/draft`, {
    method: 'PUT',
    body: JSON.stringify({ title, body_md }),
  });

export const deleteLegalDraft = (slug: string) =>
  fetchJSON<{ deleted: boolean }>(`${API}/cms/legal/${slug}/draft`, { method: 'DELETE' });

export const publishLegal = (
  slug: string,
  payload: { version: string; effective_date?: string; requires_reacceptance: boolean },
) =>
  fetchJSON<LegalDoc>(`${API}/cms/legal/${slug}/publish`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
