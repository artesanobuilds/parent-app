import type { CommunityPost } from '../../types';

interface CommunityPostPreviewProps {
  post: Partial<CommunityPost>;
}

export default function CommunityPostPreview({ post }: CommunityPostPreviewProps) {
  const initials = post.initials || (post.name ? post.name.slice(0, 2).toUpperCase() : '??');

  return (
    <div
      className="bg-white px-4 py-5"
      style={{
        fontFamily:
          "-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif",
      }}
    >
      {/* Author row */}
      <div className="flex items-center gap-3 mb-4">
        {/* Gold avatar circle */}
        <div
          className="flex-shrink-0 flex items-center justify-center rounded-full"
          style={{
            width: 48,
            height: 48,
            backgroundColor: '#C9A84C',
          }}
        >
          <span
            className="text-white"
            style={{ fontSize: 16, fontWeight: 700 }}
          >
            {initials}
          </span>
        </div>

        {/* Name + category */}
        <div className="flex-1 min-w-0">
          <p
            style={{
              fontSize: 15,
              fontWeight: 600,
              color: '#212123',
              lineHeight: 1.3,
            }}
          >
            {post.name || 'Anonymous'}
          </p>
          {post.category && (
            <span
              className="inline-block rounded-full px-2 py-0.5 mt-1"
              style={{
                backgroundColor: '#C9A84C',
                color: '#FFFFFF',
                fontSize: 11,
                fontWeight: 600,
              }}
            >
              {post.category}
            </span>
          )}
        </div>
      </div>

      {/* Title */}
      {post.title && (
        <h2
          className="mb-2"
          style={{
            fontSize: 17,
            fontWeight: 700,
            color: '#212123',
            lineHeight: 1.3,
          }}
        >
          {post.title}
        </h2>
      )}

      {/* Body / preview text */}
      {post.preview && (
        <p
          style={{
            fontSize: 15,
            color: '#333333',
            lineHeight: 1.5,
          }}
        >
          {post.preview}
        </p>
      )}
    </div>
  );
}
