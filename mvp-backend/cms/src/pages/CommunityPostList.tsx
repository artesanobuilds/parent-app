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
    <div className="p-800 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-700">
        <h1 className="font-display text-display-sm text-ink-primary">Community Posts</h1>
        <Link
          to="/community/new"
          className="rounded-md bg-accent px-500 py-300 text-title-md font-medium text-ink-on-photo-light hover:bg-accent-press transition-colors duration-fast"
        >
          New Post
        </Link>
      </div>

      {/* Filters */}
      <div className="flex gap-500 mb-700">
        <input
          type="text"
          placeholder="Search by title..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 rounded-md border border-hairline bg-elevated px-500 py-300 text-body-md text-ink-primary placeholder:text-ink-placeholder focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="rounded-md border border-hairline bg-elevated px-500 py-300 text-body-md text-ink-primary focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
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
        <div className="text-center py-1000 text-ink-muted text-body-sm">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-1000 text-ink-muted text-body-sm">No posts found.</div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-hairline bg-elevated">
          <table className="w-full text-body-md">
            <thead>
              <tr className="border-b border-hairline bg-canvas text-left text-label font-semibold uppercase tracking-wider text-ink-muted">
                <th className="px-500 py-400 w-16">Initials</th>
                <th className="px-500 py-400">Name</th>
                <th className="px-500 py-400">Title</th>
                <th className="px-500 py-400">Category</th>
                <th className="px-500 py-400 w-20">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {filtered.map((post) => (
                <tr
                  key={post.id}
                  className="hover:bg-canvas transition-colors duration-fast"
                >
                  <td className="px-500 py-400">
                    <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-accent-tint text-body-sm font-semibold text-accent">
                      {post.initials}
                    </span>
                  </td>
                  <td className="px-500 py-400 text-ink-secondary">{post.name}</td>
                  <td className="px-500 py-400">
                    <Link
                      to={`/community/${post.id}`}
                      className="font-medium text-ink-primary hover:text-accent transition-colors duration-fast"
                    >
                      {post.title}
                    </Link>
                  </td>
                  <td className="px-500 py-400 text-ink-muted">{post.category}</td>
                  <td className="px-500 py-400">
                    <Link
                      to={`/community/${post.id}`}
                      className="text-accent hover:text-accent-press font-medium transition-colors duration-fast"
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
