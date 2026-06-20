import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getCommunityPost,
  getCategories,
  createCommunityPost,
  updateCommunityPost,
  deleteCommunityPost,
} from '../api';
import type { CommunityPost, Category } from '../types';
import { toast } from '../components/shared/Toast';
import CommunityPostForm from '../components/editors/CommunityPostForm';
import PhoneFrame from '../components/preview/PhoneFrame';
import CommunityPostPreview from '../components/preview/CommunityPostPreview';
import CommunityCardPreview from '../components/preview/CommunityCardPreview';

type PreviewMode = 'detail' | 'card';

export function CommunityPostEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditing = Boolean(id);

  const [formData, setFormData] = useState<Partial<CommunityPost>>({
    name: '',
    initials: '',
    title: '',
    preview: '',
    category: '',
  });
  const [categories, setCategories] = useState<Category[]>([]);
  const [previewData, setPreviewData] = useState<Partial<CommunityPost>>(formData);
  const [previewMode, setPreviewMode] = useState<PreviewMode>('detail');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(isEditing);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    getCategories()
      .then(setCategories)
      .catch(() => toast.error('Failed to load categories'));

    if (id) {
      getCommunityPost(id)
        .then((post) => {
          setFormData(post);
          setPreviewData(post);
        })
        .catch(() => {
          toast.error('Failed to load post');
          navigate('/community');
        })
        .finally(() => setLoading(false));
    }
  }, [id, navigate]);

  const handleChange = useCallback((data: Partial<CommunityPost>) => {
    setFormData(data);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setPreviewData({ ...data });
    }, 300);
  }, []);

  const handleSave = async () => {
    if (!formData.title || !formData.name) {
      toast.error('Title and name are required');
      return;
    }

    setSaving(true);
    try {
      if (isEditing && id) {
        await updateCommunityPost(id, formData);
        toast.success('Post updated');
      } else {
        await createCommunityPost(formData as CommunityPost);
        toast.success('Post created');
      }
      navigate('/community');
    } catch (err) {
      toast.error('Failed to save post');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    try {
      await deleteCommunityPost(id);
      toast.success('Post deleted');
      navigate('/community');
    } catch {
      toast.error('Failed to delete post');
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
    <div className="flex h-full">
      {/* Left: Form */}
      <div className="flex-1 overflow-y-auto p-800">
        <div className="max-w-2xl">
          <div className="flex items-center justify-between mb-700">
            <h1 className="font-display text-display-sm text-ink-primary">
              {isEditing ? 'Edit Post' : 'New Post'}
            </h1>
            <div className="flex gap-400">
              <button
                onClick={() => navigate('/community')}
                className="rounded-md border border-hairline bg-elevated px-500 py-300 text-title-md font-medium text-ink-primary hover:bg-sober transition-colors duration-fast"
              >
                Cancel
              </button>
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

          <CommunityPostForm
            post={formData}
            categories={categories}
            onChange={handleChange}
            onSave={handleSave}
            saving={saving}
          />
        </div>
      </div>

      {/* Right: Preview */}
      <div className="w-[380px] shrink-0 border-l border-hairline bg-canvas overflow-y-auto">
        <div className="sticky top-0 z-10 bg-canvas px-500 pt-500 pb-300">
          <div className="flex rounded-md bg-elevated border border-hairline p-100">
            <button
              onClick={() => setPreviewMode('detail')}
              className={`flex-1 rounded-md px-400 py-200 text-body-sm font-medium transition-colors duration-fast ${
                previewMode === 'detail'
                  ? 'bg-accent text-ink-on-photo-light'
                  : 'text-ink-muted hover:text-ink-primary'
              }`}
            >
              Detail
            </button>
            <button
              onClick={() => setPreviewMode('card')}
              className={`flex-1 rounded-md px-400 py-200 text-body-sm font-medium transition-colors duration-fast ${
                previewMode === 'card'
                  ? 'bg-accent text-ink-on-photo-light'
                  : 'text-ink-muted hover:text-ink-primary'
              }`}
            >
              Card
            </button>
          </div>
        </div>
        <div className="px-500 pb-500">
          <PhoneFrame>
            {previewMode === 'detail' ? (
              <CommunityPostPreview post={previewData} />
            ) : (
              <div className="p-500 bg-canvas">
                <CommunityCardPreview post={previewData} />
              </div>
            )}
          </PhoneFrame>
        </div>
      </div>

      {/* Delete confirmation dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-xl bg-elevated p-700 shadow-e3">
            <h2 className="text-title-lg font-semibold text-ink-primary mb-200">
              Delete Post
            </h2>
            <p className="text-body-sm text-ink-muted mb-700">
              Are you sure you want to delete this post? This action cannot be
              undone.
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
