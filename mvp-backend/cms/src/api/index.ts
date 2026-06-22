import type { Article, Category, CommunityPost, ContentStats } from '../types';

const API = '';

// Admin token for /cms/* writes. Read once at module load.
const ADMIN_TOKEN: string = (() => {
  const t = import.meta.env.VITE_ADMIN_TOKEN as string | undefined;
  if (!t) {
    console.warn(
      '[cms/api] VITE_ADMIN_TOKEN is not set; /cms/* requests will be sent with an empty X-Admin-Token and will fail with 401.',
    );
    return '';
  }
  return t;
})();

function withAdminHeaders(init?: RequestInit): RequestInit {
  const headers = new Headers(init?.headers ?? {});
  headers.set('X-Admin-Token', ADMIN_TOKEN);
  if (init?.body !== undefined && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  return { ...init, headers };
}

async function fetchJSON<T>(url: string, init?: RequestInit, retries = 3): Promise<T> {
  const finalInit = url.startsWith('/cms/') || url.includes(`${API}/cms/`)
    ? withAdminHeaders(init)
    : init;
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
    const body = await res.text();
    lastError = new Error(`${res.status}: ${body}`);
    if (res.status < 500 && res.status !== 429) {
      throw lastError;
    }
  }
  throw lastError;
}

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

// Community Posts
export const getCommunityPosts = (category?: string) =>
  fetchJSON<CommunityPost[]>(`${API}/content/community${category ? `?category=${category}` : ''}`);
export const getCommunityPost = (id: string) => fetchJSON<CommunityPost>(`${API}/cms/community-posts/${id}`);
export const createCommunityPost = (data: CommunityPost) =>
  fetchJSON<CommunityPost>(`${API}/cms/community-posts`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
export const updateCommunityPost = (id: string, data: Partial<CommunityPost>) =>
  fetchJSON<CommunityPost>(`${API}/cms/community-posts/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
export const deleteCommunityPost = (id: string) =>
  fetchJSON<{ deleted: boolean }>(`${API}/cms/community-posts/${id}`, { method: 'DELETE' });

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
