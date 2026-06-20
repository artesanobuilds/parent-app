import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getCategories } from '../api';
import type { Category } from '../types';
import { toast } from '../components/shared/Toast';

export function CategoryList() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCategories()
      .then(setCategories)
      .catch(() => toast.error('Failed to load categories'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-800 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-700">
        <h1 className="font-display text-display-sm text-ink-primary">Categories</h1>
        <Link
          to="/categories/new"
          className="rounded-md bg-accent px-500 py-300 text-title-md font-medium text-ink-on-photo-light hover:bg-accent-press transition-colors duration-fast"
        >
          New Category
        </Link>
      </div>

      {loading ? (
        <div className="text-center py-1000 text-ink-muted text-body-sm">Loading...</div>
      ) : categories.length === 0 ? (
        <div className="text-center py-1000 text-ink-muted text-body-sm">No categories found.</div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-hairline bg-elevated">
          <table className="w-full text-body-md">
            <thead>
              <tr className="border-b border-hairline bg-canvas text-left text-label font-semibold uppercase tracking-wider text-ink-muted">
                <th className="px-500 py-400 w-12"></th>
                <th className="px-500 py-400">Name</th>
                <th className="px-500 py-400">Description</th>
                <th className="px-500 py-400 w-20">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline">
              {categories.map((category) => (
                <tr
                  key={category.id}
                  className="hover:bg-canvas transition-colors duration-fast"
                >
                  <td className="px-500 py-400 text-lg">{category.emoji}</td>
                  <td className="px-500 py-400 font-medium text-ink-primary">
                    {category.name}
                  </td>
                  <td className="px-500 py-400 text-ink-muted">
                    {category.description}
                  </td>
                  <td className="px-500 py-400">
                    <Link
                      to={`/categories/${category.id}`}
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
