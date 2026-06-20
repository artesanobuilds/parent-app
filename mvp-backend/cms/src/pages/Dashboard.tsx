import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getStats } from '../api';
import type { ContentStats } from '../types';
import { toast } from '../components/shared/Toast';

export function Dashboard() {
  const [stats, setStats] = useState<ContentStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch((err) => {
        toast.error('Failed to load stats');
        console.error(err);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="text-ink-muted text-body-sm">Loading...</span>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-800 text-center text-ink-muted">
        Failed to load dashboard data.
      </div>
    );
  }

  return (
    <div className="p-800 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-800">
        <h1 className="font-display text-display-sm text-ink-primary">Dashboard</h1>
        <div className="flex gap-400">
          <Link
            to="/articles/new"
            className="rounded-md bg-accent px-500 py-300 text-title-md font-medium text-ink-on-photo-light hover:bg-accent-press transition-colors duration-fast"
          >
            New Article
          </Link>
          <Link
            to="/community/new"
            className="rounded-md border border-accent px-500 py-300 text-title-md font-medium text-accent hover:bg-accent-tint transition-colors duration-fast"
          >
            New Post
          </Link>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-3 gap-600 mb-1000">
        <div className="rounded-lg bg-elevated p-600 border border-hairline">
          <p className="text-body-sm font-medium text-ink-muted mb-200">Articles</p>
          <p className="font-display text-display-sm text-accent">{stats.articles}</p>
        </div>
        <div className="rounded-lg bg-elevated p-600 border border-hairline">
          <p className="text-body-sm font-medium text-ink-muted mb-200">Community Posts</p>
          <p className="font-display text-display-sm text-accent">{stats.community_posts}</p>
        </div>
        <div className="rounded-lg bg-elevated p-600 border border-hairline">
          <p className="text-body-sm font-medium text-ink-muted mb-200">Categories</p>
          <p className="font-display text-display-sm text-accent">{stats.categories}</p>
        </div>
      </div>

      {/* Breakdowns */}
      <div className="grid grid-cols-2 gap-600">
        <div className="rounded-lg bg-elevated p-600 border border-hairline">
          <h2 className="text-title-md font-semibold text-ink-secondary mb-500">Articles by Category</h2>
          {Object.keys(stats.articles_by_category).length === 0 ? (
            <p className="text-body-sm text-ink-muted">No data yet</p>
          ) : (
            <ul className="space-y-300">
              {Object.entries(stats.articles_by_category).map(([cat, count]) => (
                <li key={cat} className="flex items-center justify-between text-body-md">
                  <span className="text-ink-secondary">{cat}</span>
                  <span className="font-medium text-ink-primary">{count}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-lg bg-elevated p-600 border border-hairline">
          <h2 className="text-title-md font-semibold text-ink-secondary mb-500">Posts by Category</h2>
          {Object.keys(stats.posts_by_category).length === 0 ? (
            <p className="text-body-sm text-ink-muted">No data yet</p>
          ) : (
            <ul className="space-y-300">
              {Object.entries(stats.posts_by_category).map(([cat, count]) => (
                <li key={cat} className="flex items-center justify-between text-body-md">
                  <span className="text-ink-secondary">{cat}</span>
                  <span className="font-medium text-ink-primary">{count}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
