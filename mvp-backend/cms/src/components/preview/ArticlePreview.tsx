import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Article } from '../../types';

interface ArticlePreviewProps {
  article: Partial<Article>;
}

export default function ArticlePreview({ article }: ArticlePreviewProps) {
  return (
    <div
      style={{
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif",
      }}
    >
      {/* Emoji banner */}
      <div
        className="flex items-center justify-center"
        style={{
          height: 140,
          background: 'linear-gradient(180deg, #C9A84C 0%, #B8973F 100%)',
        }}
      >
        <span className="text-[64px] leading-none">
          {article.emoji || '📄'}
        </span>
      </div>

      {/* Content area */}
      <div className="bg-white px-4 py-5 min-h-[400px]">
        {/* Category badge */}
        {article.category && (
          <span
            className="inline-block rounded-full px-3 py-1 mb-3"
            style={{
              backgroundColor: '#C9A84C',
              color: '#FFFFFF',
              fontSize: 12,
              fontWeight: 600,
            }}
          >
            {article.category}
          </span>
        )}

        {/* Title */}
        <h1
          className="mb-2"
          style={{
            fontSize: 22,
            fontWeight: 700,
            color: '#212123',
            lineHeight: 1.3,
          }}
        >
          {article.title || 'Untitled Article'}
        </h1>

        {/* Subtitle */}
        {article.subtitle && (
          <p
            className="mb-3"
            style={{ fontSize: 15, color: '#999999', lineHeight: 1.4 }}
          >
            {article.subtitle}
          </p>
        )}

        {/* Author + read time */}
        <div
          className="flex items-center gap-2 mb-4"
          style={{ fontSize: 12, color: '#999999' }}
        >
          {article.author && <span>{article.author}</span>}
          {article.author && article.read_time && (
            <span className="text-gray-300">·</span>
          )}
          {article.read_time && <span>{article.read_time}</span>}
        </div>

        {/* Divider */}
        <div className="h-px bg-gray-200 mb-4" />

        {/* Markdown body */}
        {article.content && (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => (
                  <h1 className="text-lg font-bold text-[#212123] mt-4 mb-2">
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-base font-bold text-[#212123] mt-3 mb-2">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-sm font-semibold text-[#212123] mt-3 mb-1">
                    {children}
                  </h3>
                ),
                p: ({ children }) => (
                  <p
                    className="mb-3"
                    style={{ fontSize: 15, lineHeight: 1.6, color: '#333' }}
                  >
                    {children}
                  </p>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal pl-5 mb-3 space-y-1">
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li style={{ fontSize: 14, lineHeight: 1.5, color: '#333' }}>
                    {children}
                  </li>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-[#C9A84C] pl-3 italic text-gray-600 my-3">
                    {children}
                  </blockquote>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold text-[#212123]">
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
