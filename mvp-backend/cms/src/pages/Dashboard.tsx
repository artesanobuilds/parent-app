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
        <span className="text-gray-400 text-sm">Loading...</span>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-8 text-center text-gray-500">
        Failed to load dashboard data.
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex gap-3">
          <Link
            to="/articles/new"
            className="rounded-lg bg-[#C9A84C] px-4 py-2 text-sm font-medium text-white hover:bg-[#B8973F] transition-colors"
          >
            New Article
          </Link>
          <Link
            to="/community/new"
            className="rounded-lg border border-[#C9A84C] px-4 py-2 text-sm font-medium text-[#C9A84C] hover:bg-[#C9A84C]/5 transition-colors"
          >
            New Post
          </Link>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-3 gap-6 mb-10">
        <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
          <p className="text-sm font-medium text-gray-500 mb-1">Articles</p>
          <p className="text-3xl font-bold text-[#C9A84C]">{stats.articles}</p>
        </div>
        <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
          <p className="text-sm font-medium text-gray-500 mb-1">Community Posts</p>
          <p className="text-3xl font-bold text-[#C9A84C]">{stats.community_posts}</p>
        </div>
        <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
          <p className="text-sm font-medium text-gray-500 mb-1">Categories</p>
          <p className="text-3xl font-bold text-[#C9A84C]">{stats.categories}</p>
        </div>
      </div>

      {/* Breakdowns */}
      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Articles by Category</h2>
          {Object.keys(stats.articles_by_category).length === 0 ? (
            <p className="text-sm text-gray-400">No data yet</p>
          ) : (
            <ul className="space-y-2">
              {Object.entries(stats.articles_by_category).map(([cat, count]) => (
                <li key={cat} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{cat}</span>
                  <span className="font-medium text-gray-900">{count}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-100">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Posts by Category</h2>
          {Object.keys(stats.posts_by_category).length === 0 ? (
            <p className="text-sm text-gray-400">No data yet</p>
          ) : (
            <ul className="space-y-2">
              {Object.entries(stats.posts_by_category).map(([cat, count]) => (
                <li key={cat} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{cat}</span>
                  <span className="font-medium text-gray-900">{count}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
