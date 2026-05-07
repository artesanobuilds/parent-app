import { useEffect } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Markdown } from 'tiptap-markdown';
import type { Article, Category } from '../../types';

interface ArticleFormProps {
  article: Partial<Article>;
  categories: Category[];
  onChange: (article: Partial<Article>) => void;
  onSave: () => void;
  saving: boolean;
}

export default function ArticleForm({
  article,
  categories,
  onChange,
  onSave,
  saving,
}: ArticleFormProps) {
  const isEditing = !!article.id && article.id.length > 0;

  const editor = useEditor({
    extensions: [StarterKit, Markdown],
    content: article.content || '',
    onUpdate: ({ editor }) => {
      const md = (editor.storage as { markdown?: { getMarkdown: () => string } }).markdown?.getMarkdown() ?? editor.getText();
      onChange({ ...article, content: md });
    },
  });

  // Sync editor content when article.content changes externally
  useEffect(() => {
    if (editor && article.content !== undefined) {
      const current = (editor.storage as { markdown?: { getMarkdown: () => string } }).markdown?.getMarkdown() ?? editor.getText();
      if (current !== article.content) {
        editor.commands.setContent(article.content);
      }
    }
  }, [article.content, editor]);

  const field = (
    key: keyof Article,
    value: string | string[] | undefined,
  ) => {
    onChange({ ...article, [key]: value });
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
          value={article.id ?? ''}
          disabled={isEditing}
          onChange={(e) => field('id', e.target.value)}
          placeholder="unique-article-id"
        />
      </div>

      {/* Category */}
      <div>
        <label className={labelClass}>Category</label>
        <select
          className={inputClass}
          value={article.category ?? ''}
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

      {/* Title */}
      <div>
        <label className={labelClass}>Title</label>
        <input
          type="text"
          className={inputClass}
          value={article.title ?? ''}
          onChange={(e) => field('title', e.target.value)}
          placeholder="Article title"
        />
      </div>

      {/* Subtitle */}
      <div>
        <label className={labelClass}>Subtitle</label>
        <input
          type="text"
          className={inputClass}
          value={article.subtitle ?? ''}
          onChange={(e) => field('subtitle', e.target.value)}
          placeholder="Short subtitle"
        />
      </div>

      {/* Emoji + Author + Read Time row */}
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className={labelClass}>Emoji</label>
          <input
            type="text"
            className={`${inputClass} text-center`}
            value={article.emoji ?? ''}
            onChange={(e) => field('emoji', e.target.value)}
            placeholder="📖"
            maxLength={4}
          />
        </div>
        <div>
          <label className={labelClass}>Author</label>
          <input
            type="text"
            className={inputClass}
            value={article.author ?? 'MVP Editorial'}
            onChange={(e) => field('author', e.target.value)}
            placeholder="MVP Editorial"
          />
        </div>
        <div>
          <label className={labelClass}>Read Time</label>
          <input
            type="text"
            className={inputClass}
            value={article.read_time ?? ''}
            onChange={(e) => field('read_time', e.target.value)}
            placeholder="5 min read"
          />
        </div>
      </div>

      {/* Summary */}
      <div>
        <label className={labelClass}>Summary</label>
        <textarea
          className={`${inputClass} resize-y`}
          rows={3}
          value={article.summary ?? ''}
          onChange={(e) => field('summary', e.target.value)}
          placeholder="Brief summary of the article"
        />
      </div>

      {/* Tags */}
      <div>
        <label className={labelClass}>Tags (comma-separated)</label>
        <input
          type="text"
          className={inputClass}
          value={(article.tags ?? []).join(', ')}
          onChange={(e) =>
            field(
              'tags',
              e.target.value.split(',').map((t) => t.trim()),
            )
          }
          placeholder="parenting, toddlers, sleep"
        />
      </div>

      {/* Content (TipTap editor) */}
      <div>
        <label className={labelClass}>Content</label>
        <div className="rounded-md border border-gray-300 overflow-hidden">
          <EditorContent
            editor={editor}
            className="prose prose-sm max-w-none min-h-[300px] px-4 py-3 focus-within:ring-1 focus-within:ring-indigo-500 focus-within:border-indigo-500"
          />
        </div>
      </div>

      {/* Save */}
      <div className="pt-2">
        <button
          type="submit"
          disabled={saving}
          className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save Article'}
        </button>
      </div>
    </form>
  );
}
