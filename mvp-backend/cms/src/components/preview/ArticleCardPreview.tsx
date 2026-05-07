import type { Article } from '../../types';

interface ArticleCardPreviewProps {
  article: Partial<Article>;
}

export default function ArticleCardPreview({ article }: ArticleCardPreviewProps) {
  return (
    <div
      className="flex items-center gap-3 bg-white rounded-xl shadow-sm"
      style={{
        padding: 12,
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif",
      }}
    >
      {/* Emoji square */}
      <div
        className="flex-shrink-0 flex items-center justify-center rounded-xl"
        style={{
          width: 56,
          height: 56,
          backgroundColor: '#F5F0E5',
        }}
      >
        <span className="text-[28px] leading-none">
          {article.emoji || '📄'}
        </span>
      </div>

      {/* Text content */}
      <div className="flex-1 min-w-0">
        <p
          className="truncate"
          style={{
            fontSize: 15,
            fontWeight: 600,
            color: '#212123',
            lineHeight: 1.3,
          }}
        >
          {article.title || 'Untitled Article'}
        </p>
        {article.subtitle && (
          <p
            className="mt-0.5"
            style={{
              fontSize: 13,
              color: '#999999',
              lineHeight: 1.3,
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
