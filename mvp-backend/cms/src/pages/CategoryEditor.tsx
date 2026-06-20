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
    parent_id: null,
  });
  const [allCategories, setAllCategories] = useState<Category[]>([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(isEditing);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    // Always load the full list so the parent dropdown has options,
    // for both new and existing categories.
    getCategories()
      .then((cats) => {
        setAllCategories(cats);
        if (isEditing && id) {
          const found = cats.find((c) => c.id === id);
          if (found) {
            setFormData(found);
          } else {
            toast.error('Category not found');
            navigate('/categories');
          }
        }
      })
      .catch(() => {
        if (isEditing) {
          toast.error('Failed to load category');
          navigate('/categories');
        }
      })
      .finally(() => setLoading(false));
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
        <span className="text-ink-muted text-body-sm">Loading...</span>
      </div>
    );
  }

  return (
    <div className="p-800 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-700">
        <h1 className="font-display text-display-sm text-ink-primary">
          {isEditing ? 'Edit Category' : 'New Category'}
        </h1>
        <div className="flex gap-400">
          {isEditing && (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="rounded-md border border-error bg-elevated px-500 py-300 text-title-md font-medium text-error hover:bg-error-tint transition-colors duration-fast"
            >
              Delete
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-md bg-accent px-700 py-300 text-title-md font-medium text-ink-on-photo-light hover:bg-accent-press transition-colors duration-fast disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>

      <CategoryForm
        category={formData}
        onChange={setFormData}
        onSave={handleSave}
        saving={saving}
        allCategories={allCategories}
      />

      {/* Delete confirmation dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-xl bg-elevated p-700 shadow-e3">
            <h2 className="text-title-lg font-semibold text-ink-primary mb-200">
              Delete Category
            </h2>
            <p className="text-body-sm text-ink-muted mb-700">
              Are you sure you want to delete this category? This may affect
              articles and posts that use it.
            </p>
            <div className="flex justify-end gap-400">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="rounded-md border border-hairline bg-elevated px-500 py-300 text-title-md font-medium text-ink-primary hover:bg-sober transition-colors duration-fast"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="rounded-md border border-error bg-elevated px-500 py-300 text-title-md font-medium text-error hover:bg-error-tint transition-colors duration-fast"
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
