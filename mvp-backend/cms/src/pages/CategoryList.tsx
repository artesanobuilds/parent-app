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
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Categories</h1>
        <Link
          to="/categories/new"
          className="rounded-lg bg-[#C9A84C] px-4 py-2 text-sm font-medium text-white hover:bg-[#B8973F] transition-colors"
        >
          New Category
        </Link>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400 text-sm">Loading...</div>
      ) : categories.length === 0 ? (
        <div className="text-center py-12 text-gray-400 text-sm">No categories found.</div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                <th className="px-4 py-3 w-12"></th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Description</th>
                <th className="px-4 py-3 w-20">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {categories.map((category) => (
                <tr
                  key={category.id}
                  className="hover:bg-gray-50/50 transition-colors"
                >
                  <td className="px-4 py-3 text-lg">{category.emoji}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {category.name}
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {category.description}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/categories/${category.id}`}
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
