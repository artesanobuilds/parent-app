import type { Article } from '../../types';

interface ArticleCardPreviewProps {
  article: Partial<Article>;
}

export default function ArticleCardPreview({ article }: ArticleCardPreviewProps) {
  return (
    <div className="flex items-center gap-400 bg-elevated rounded-lg shadow-e1 p-400 font-sans">
      {/* Emoji square — accent-tint backdrop */}
      <div className="flex-shrink-0 flex items-center justify-center rounded-lg bg-accent-tint w-[56px] h-[56px]">
        <span className="text-[28px] leading-none">
          {article.emoji || '📄'}
        </span>
      </div>

      {/* Text content */}
      <div className="flex-1 min-w-0">
        <p className="truncate text-body-md font-semibold text-ink-primary">
          {article.title || 'Untitled Article'}
        </p>
        {article.subtitle && (
          <p
            className="mt-100 text-body-sm text-ink-muted"
            style={{
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {article.subtitle}
          </p>
        )}
      </div>
    </div>
  );
}
