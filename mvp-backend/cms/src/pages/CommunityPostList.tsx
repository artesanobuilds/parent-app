import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getCommunityPosts, getCategories } from '../api';
import type { CommunityPost, Category } from '../types';
import { toast } from '../components/shared/Toast';

export function CommunityPostList() {
  const [posts, setPosts] = useState<CommunityPost[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchPosts = (category?: string) => {
    setLoading(true);
    getCommunityPosts(category || undefined)
      .then(setPosts)
      .catch(() => toast.error('Failed to load community posts'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    getCategories()
      .then(setCategories)
      .catch(() => toast.error('Failed to load categories'));
    fetchPosts();
  }, []);

  useEffect(() => {
    fetchPosts(categoryFilter);
  }, [categoryFilter]);

  const filtered = posts.filter((p) =>
    p.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Community Posts</h1>
        <Link
          to="/community/new"
          className="rounded-lg bg-[#C9A84C] px-4 py-2 text-sm font-medium text-white hover:bg-[#B8973F] transition-colors"
        >
          New Post
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <input
          type="text"
          placeholder="Search by title..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm focus:border-[#C9A84C] focus:outline-none focus:ring-1 focus:ring-[#C9A84C]"
        />
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm focus:border-[#C9A84C] focus:outline-none focus:ring-1 focus:ring-[#C9A84C]"
        >
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c.id} value={c.name}>
              {c.emoji} {c.name}
            </option>
          ))}
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-center py-12 text-gray-400 text-sm">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-gray-400 text-sm">No posts found.</div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                <th className="px-4 py-3 w-16">Initials</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3 w-20">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {filtered.map((post) => (
                <tr
                  key={post.id}
                  className="hover:bg-gray-50/50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[#C9A84C]/10 text-xs font-semibold text-[#C9A84C]">
                      {post.initials}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700">{post.name}</td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/community/${post.id}`}
                      className="font-medium text-gray-900 hover:text-[#C9A84C] transition-colors"
                    >
                      {post.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{post.category}</td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/community/${post.id}`}
                      className="text-[#C9A84C] hover:text-[#B8973F] font-medium transition-colors"
                    >
                      Edit
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
