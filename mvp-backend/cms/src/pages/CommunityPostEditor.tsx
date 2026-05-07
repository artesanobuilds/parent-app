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
        <span className="text-gray-400 text-sm">Loading...</span>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      {/* Left: Form */}
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-2xl">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-2xl font-bold text-gray-900">
              {isEditing ? 'Edit Post' : 'New Post'}
            </h1>
            <div className="flex gap-3">
              <button
                onClick={() => navigate('/community')}
                className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
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
      <div className="w-[380px] shrink-0 border-l border-gray-200 bg-gray-100 overflow-y-auto">
        <div className="sticky top-0 z-10 bg-gray-100 px-4 pt-4 pb-2">
          <div className="flex rounded-lg bg-white border border-gray-200 p-0.5">
            <button
              onClick={() => setPreviewMode('detail')}
              className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                previewMode === 'detail'
                  ? 'bg-[#C9A84C] text-white'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Detail
            </button>
            <button
              onClick={() => setPreviewMode('card')}
              className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                previewMode === 'card'
                  ? 'bg-[#C9A84C] text-white'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Card
            </button>
          </div>
        </div>
        <div className="px-4 pb-4">
          <PhoneFrame>
            {previewMode === 'detail' ? (
              <CommunityPostPreview post={previewData} />
            ) : (
              <div className="p-4 bg-[#1C1C1E]">
                <CommunityCardPreview post={previewData} />
              </div>
            )}
          </PhoneFrame>
        </div>
      </div>

      {/* Delete confirmation dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Delete Post
            </h2>
            <p className="text-sm text-gray-500 mb-6">
              Are you sure you want to delete this post? This action cannot be
              undone.
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
