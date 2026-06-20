import type { Category } from '../../types';

interface CategoryFormProps {
  category: Partial<Category>;
  onChange: (category: Partial<Category>) => void;
  onSave: () => void;
  saving: boolean;
  allCategories?: Category[];
}

export default function CategoryForm({
  category,
  onChange,
  onSave,
  saving,
  allCategories = [],
}: CategoryFormProps) {
  const isEditing = !!category.id && category.id.length > 0;

  const field = (key: keyof Category, value: string) => {
    onChange({ ...category, [key]: value });
  };

  const handleParentChange = (value: string) => {
    // Empty string in <select> means top-level → store null so the API
    // explicitly clears the parent on update.
    onChange({ ...category, parent_id: value === '' ? null : value });
  };

  // Only top-level categories (parent_id null/undefined) can be parents —
  // this caps hierarchy depth at 2. Also exclude self.
  const parentOptions = allCategories.filter(
    (c) =>
      (c.parent_id === null || c.parent_id === undefined) &&
      c.id !== category.id,
  );

  const labelClass = 'block text-body-sm font-medium text-ink-secondary mb-200';
  const inputClass =
    'w-full rounded-md border border-strong bg-elevated px-400 py-300 text-body-md text-ink-primary placeholder:text-ink-placeholder shadow-e0 focus:border-accent focus:ring-1 focus:ring-accent outline-none';

  return (
    <form
      className="space-y-600"
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
          className={`${inputClass} ${isEditing ? 'bg-hairline cursor-not-allowed' : ''}`}
          value={category.id ?? ''}
          disabled={isEditing}
          onChange={(e) => field('id', e.target.value)}
          placeholder="unique-category-id"
        />
      </div>

      {/* Name + Emoji row */}
      <div className="grid grid-cols-4 gap-500">
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

      {/* Parent category */}
      <div>
        <label className={labelClass}>Parent category</label>
        <select
          className={inputClass}
          value={category.parent_id ?? ''}
          onChange={(e) => handleParentChange(e.target.value)}
        >
          <option value="">— None (top-level) —</option>
          {parentOptions.map((opt) => (
            <option key={opt.id} value={opt.id}>
              {opt.emoji ? `${opt.emoji} ` : ''}
              {opt.name}
            </option>
          ))}
        </select>
        <p className="mt-200 text-caption-mono font-mono text-ink-muted">
          Only top-level categories can be selected as a parent (max 2 levels).
        </p>
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
      <div className="pt-300">
        <button
          type="submit"
          disabled={saving}
          className="inline-flex items-center rounded-md bg-accent px-500 py-300 text-title-md font-medium text-ink-on-photo-light shadow-e1 hover:bg-accent-press transition-colors duration-fast disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save Category'}
        </button>
      </div>
    </form>
  );
}
