import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getCategories,
  createCategory,
  updateCategory,
  deleteCategory,
} from '../api';
import type { Category } from '../types';
import { toast } from '../components/shared/Toast';
import CategoryForm from '../components/editors/CategoryForm';

export function CategoryEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditing = id !== 'new' && Boolean(id);

  const [formData, setFormData] = useState<Partial<Category>>({
    name: '',
    emoji: '',
    description: '',
  });
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(isEditing);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (isEditing && id) {
      getCategories()
        .then((cats) => {
          const found = cats.find((c) => c.id === id);
          if (found) {
            setFormData(found);
          } else {
            toast.error('Category not found');
            navigate('/categories');
          }
        })
        .catch(() => {
          toast.error('Failed to load category');
          navigate('/categories');
        })
        .finally(() => setLoading(false));
    }
  }, [id, isEditing, navigate]);

  const handleSave = async () => {
    if (!formData.name) {
      toast.error('Name is required');
      return;
    }

    setSaving(true);
    try {
      if (isEditing && id) {
        await updateCategory(id, formData);
        toast.success('Category updated');
      } else {
        await createCategory(formData as Category);
        toast.success('Category created');
      }
      navigate('/categories');
    } catch (err) {
      toast.error('Failed to save category');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    try {
      await deleteCategory(id);
      toast.success('Category deleted');
      navigate('/categories');
    } catch {
      toast.error('Failed to delete category');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="text-gray-400 text-sm">Loading...</span>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {isEditing ? 'Edit Category' : 'New Category'}
        </h1>
        <div className="flex gap-3">
          {isEditing && (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="rounded-lg border border-red-200 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
            >
              Delete
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-lg bg-[#C9A84C] px-6 py-2 text-sm font-medium text-white hover:bg-[#B8973F] transition-colors disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      <CategoryForm category={formData} onChange={setFormData} onSave={handleSave} saving={saving} />

      {/* Delete confirmation dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Delete Category
            </h2>
            <p className="text-sm text-gray-500 mb-6">
              Are you sure you want to delete this category? This may affect
              articles and posts that use it.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
