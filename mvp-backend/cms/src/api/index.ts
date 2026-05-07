import type { Article, Category, CommunityPost, ContentStats } from '../types';

const API = '';

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
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
