import type { Category } from '../../types';

interface CategoryFormProps {
  category: Partial<Category>;
  onChange: (category: Partial<Category>) => void;
  onSave: () => void;
  saving: boolean;
}

export default function CategoryForm({
  category,
  onChange,
  onSave,
  saving,
}: CategoryFormProps) {
  const isEditing = !!category.id && category.id.length > 0;

  const field = (key: keyof Category, value: string) => {
    onChange({ ...category, [key]: value });
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
          value={category.id ?? ''}
          disabled={isEditing}
          onChange={(e) => field('id', e.target.value)}
          placeholder="unique-category-id"
        />
      </div>

      {/* Name + Emoji row */}
      <div className="grid grid-cols-4 gap-4">
        <div className="col-span-3">
          <label className={labelClass}>Name</label>
          <input
            type="text"
            className={inputClass}
            value={category.name ?? ''}
            onChange={(e) => field('name', e.target.value)}
            placeholder="Category name"
          />
        </div>
        <div>
          <label className={labelClass}>Emoji</label>
          <input
            type="text"
            className={`${inputClass} text-center`}
            value={category.emoji ?? ''}
            onChange={(e) => field('emoji', e.target.value)}
            placeholder="📚"
            maxLength={4}
          />
        </div>
      </div>

      {/* Description */}
      <div>
        <label className={labelClass}>Description</label>
        <textarea
          className={`${inputClass} resize-y`}
          rows={3}
          value={category.description ?? ''}
          onChange={(e) => field('description', e.target.value)}
          placeholder="What this category covers"
        />
      </div>

      {/* Save */}
      <div className="pt-2">
        <button
          type="submit"
          disabled={saving}
          className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save Category'}
        </button>
      </div>
    </form>
  );
}
