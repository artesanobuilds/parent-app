import type { CommunityPost } from '../../types';

interface CommunityCardPreviewProps {
  post: Partial<CommunityPost>;
}

export default function CommunityCardPreview({ post }: CommunityCardPreviewProps) {
  const initials = post.initials || (post.name ? post.name.slice(0, 2).toUpperCase() : '??');

  return (
    <div
      className="bg-white rounded-xl shadow-sm"
      style={{
        padding: 12,
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif",
      }}
    >
      {/* Author row */}
      <div className="flex items-center gap-2 mb-2">
        {/* Gold avatar circle */}
        <div
          className="flex-shrink-0 flex items-center justify-center rounded-full"
          style={{
            width: 32,
            height: 32,
            backgroundColor: '#C9A84C',
          }}
        >
          <span
            className="text-white"
            style={{ fontSize: 12, fontWeight: 700 }}
          >
            {initials}
          </span>
        </div>

        <span
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: '#212123',
          }}
        >
          {post.name || 'Anonymous'}
        </span>
      </div>

      {/* Title */}
      <p
        className="mb-1"
        style={{
          fontSize: 15,
          fontWeight: 600,
          color: '#212123',
          lineHeight: 1.3,
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
          style={{
            fontSize: 13,
            color: '#999999',
            lineHeight: 1.4,
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
