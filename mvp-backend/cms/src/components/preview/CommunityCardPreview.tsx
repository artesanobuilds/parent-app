import type { CommunityPost } from '../../types';

interface CommunityCardPreviewProps {
  post: Partial<CommunityPost>;
}

export default function CommunityCardPreview({ post }: CommunityCardPreviewProps) {
  const initials = post.initials || (post.name ? post.name.slice(0, 2).toUpperCase() : '??');

  return (
    <div className="bg-elevated rounded-lg shadow-e1 p-400 font-sans">
      {/* Author row */}
      <div className="flex items-center gap-300 mb-300">
        {/* Accent avatar circle */}
        <div className="flex-shrink-0 flex items-center justify-center rounded-pill bg-accent w-[32px] h-[32px]">
          <span className="text-ink-on-photo-light text-body-sm font-semibold">
            {initials}
          </span>
        </div>

        <span className="text-body-sm font-semibold text-ink-primary">
          {post.name || 'Anonymous'}
        </span>
      </div>

      {/* Title */}
      <p
        className="mb-200 text-body-md font-semibold text-ink-primary"
        style={{
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
        }}
      >
        {post.title || 'Untitled Post'}
      </p>

      {/* Preview text */}
      {post.preview && (
        <p
          className="text-body-sm text-ink-muted"
          style={{
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {post.preview}
        </p>
      )}
    </div>
  );
}
