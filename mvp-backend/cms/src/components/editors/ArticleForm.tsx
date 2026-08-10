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
      <div className="grid grid-cols-3 gap-500">
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

      {/* Eyebrow — renders above the headline in the app as
          "KICKER · AGE RANGE · READ TIME", joining only the parts that are set.
          Leaving either blank is fine; the app never shows a stray separator. */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className={labelClass}>Kicker</label>
          <input
            type="text"
            className={inputClass}
            value={article.kicker ?? ''}
            onChange={(e) => field('kicker', e.target.value)}
            placeholder="WE TRIED IT"
          />
        </div>
        <div>
          <label className={labelClass}>Age Range</label>
          <input
            type="text"
            className={inputClass}
            value={article.age_range ?? ''}
            onChange={(e) => field('age_range', e.target.value)}
            placeholder="Ages 3–7"
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
        <div className="rounded-md border border-strong overflow-hidden bg-elevated">
          <EditorContent
            editor={editor}
            className="prose prose-sm max-w-none min-h-[300px] px-500 py-400 focus-within:ring-1 focus-within:ring-accent focus-within:border-accent"
          />
        </div>
      </div>

      {/* Save */}
      <div className="pt-300">
        <button
          type="submit"
          disabled={saving}
          className="inline-flex items-center rounded-md bg-accent px-500 py-300 text-title-md font-medium text-ink-on-photo-light shadow-e1 hover:bg-accent-press transition-colors duration-fast disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save Article'}
        </button>
      </div>
    </form>
  );
}
