import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Article } from '../../types';

interface ArticlePreviewProps {
  article: Partial<Article>;
}

export default function ArticlePreview({ article }: ArticlePreviewProps) {
  return (
    <div className="font-sans">
      {/* Emoji banner — photo/saffron tile, ink/onPhoto-dark for the emoji */}
      <div className="flex items-center justify-center h-[140px] bg-photo-saffron">
        <span className="text-[64px] leading-none">
          {article.emoji || '📄'}
        </span>
      </div>

      {/* Content area */}
      <div className="bg-elevated px-500 py-600 min-h-[400px]">
        {/* Category badge */}
        {article.category && (
          <span className="inline-block rounded-pill px-400 py-100 mb-400 bg-accent text-ink-on-photo-light text-label font-semibold">
            {article.category}
          </span>
        )}

        {/* Eyebrow — kicker · age range · read time, joining only the parts that
            are set, exactly as the app builds it. Mirrors the iOS reader so the
            editor can see whether the line reads well before publishing. */}
        {[article.kicker, article.age_range, article.read_time]
          .filter((part) => part && part.trim() !== '').length > 0 && (
          <p className="text-body-sm font-bold uppercase tracking-wide text-ink-muted mb-300">
            {[article.kicker, article.age_range, article.read_time]
              .filter((part) => part && part.trim() !== '')
              .join(' · ')}
          </p>
        )}

        {/* Title — font-display per Hearth spec */}
        <h1 className="font-display text-display-sm text-ink-primary mb-300">
          {article.title || 'Untitled Article'}
        </h1>

        {/* Subtitle */}
        {article.subtitle && (
          <p className="text-body-lg text-ink-muted mb-400">
            {article.subtitle}
          </p>
        )}

        {/* Author + read time — mono caption */}
        <div className="flex items-center gap-300 mb-500 font-mono text-caption-mono text-ink-muted">
          {article.author && <span>{article.author}</span>}
          {article.author && article.read_time && (
            <span className="text-ink-placeholder">·</span>
          )}
          {article.read_time && <span>{article.read_time}</span>}
        </div>

        {/* Divider */}
        <div className="h-px bg-hairline mb-500" />

        {/* Markdown body */}
        {article.content && (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => (
                  <h1 className="font-display text-title-lg text-ink-primary mt-500 mb-300">
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 className="font-display text-title-md text-ink-primary mt-400 mb-300">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-body-md font-semibold text-ink-primary mt-400 mb-200">
                    {children}
                  </h3>
                ),
                p: ({ children }) => (
                  <p className="mb-400 text-body-lg text-ink-secondary">
                    {children}
                  </p>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc pl-500 mb-400 space-y-200">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal pl-500 mb-400 space-y-200">
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li className="text-body-md text-ink-secondary">
                    {children}
                  </li>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-accent pl-400 italic text-ink-muted my-400">
                    {children}
                  </blockquote>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold text-ink-primary">
                    {children}
                  </strong>
                ),
              }}
            >
              {article.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
