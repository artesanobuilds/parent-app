import type { CommunityPost, Category } from '../../types';

interface CommunityPostFormProps {
  post: Partial<CommunityPost>;
  categories: Category[];
  onChange: (post: Partial<CommunityPost>) => void;
  onSave: () => void;
  saving: boolean;
}

function deriveInitials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w[0].toUpperCase())
    .slice(0, 2)
    .join('');
}

export default function CommunityPostForm({
  post,
  categories,
  onChange,
  onSave,
  saving,
}: CommunityPostFormProps) {
  const isEditing = !!post.id && post.id.length > 0;

  const field = (key: keyof CommunityPost, value: string) => {
    const updated: Partial<CommunityPost> = { ...post, [key]: value };
    // Auto-derive initials from name when initials field is empty
    if (key === 'name' && (!post.initials || post.initials === deriveInitials(post.name ?? ''))) {
      updated.initials = deriveInitials(value);
    }
    onChange(updated);
  };

  const labelClass = 'block text-sm font-medium text-gray-700 mb-1';
  const inputClass =
    'w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none';

  return (
    <form
      className="space-y-5"
      onSubmit={(e) => {
        e.preventDefault();
        onSave();
      }}
    >
      {/* ID */}
      <div>
        <label className={labelClass}>ID</label>
        <input
          type="text"
          className={`${inputClass} ${isEditing ? 'bg-gray-100 cursor-not-allowed' : ''}`}
          value={post.id ?? ''}
          disabled={isEditing}
          onChange={(e) => field('id', e.target.value)}
          placeholder="unique-post-id"
        />
      </div>

      {/* Category */}
      <div>
        <label className={labelClass}>Category</label>
        <select
          className={inputClass}
          value={post.category ?? ''}
          onChange={(e) => field('category', e.target.value)}
        >
          <option value="">Select a category</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.emoji} {cat.name}
            </option>
          ))}
        </select>
      </div>

      {/* Name + Initials row */}
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2">
          <label className={labelClass}>Name</label>
          <input
            type="text"
            className={inputClass}
            value={post.name ?? ''}
            onChange={(e) => field('name', e.target.value)}
            placeholder="Author name"
          />
        </div>
        <div>
          <label className={labelClass}>Initials</label>
          <input
            type="text"
            className={`${inputClass} text-center`}
            value={post.initials ?? ''}
            onChange={(e) => field('initials', e.target.value)}
            placeholder="AB"
            maxLength={3}
          />
        </div>
      </div>

      {/* Title */}
      <div>
        <label className={labelClass}>Title</label>
        <input
          type="text"
          className={inputClass}
          value={post.title ?? ''}
          onChange={(e) => field('title', e.target.value)}
          placeholder="Post title"
        />
      </div>

      {/* Preview */}
      <div>
        <label className={labelClass}>Preview</label>
        <textarea
          className={`${inputClass} resize-y`}
          rows={4}
          value={post.preview ?? ''}
          onChange={(e) => field('preview', e.target.value)}
          placeholder="Preview text shown in the feed"
        />
      </div>

      {/* Save */}
      <div className="pt-2">
        <button
          type="submit"
          disabled={saving}
          className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save Post'}
        </button>
      </div>
    </form>
  );
}
