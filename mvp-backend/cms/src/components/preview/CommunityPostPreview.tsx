import type { CommunityPost } from '../../types';

interface CommunityPostPreviewProps {
  post: Partial<CommunityPost>;
}

export default function CommunityPostPreview({ post }: CommunityPostPreviewProps) {
  const initials = post.initials || (post.name ? post.name.slice(0, 2).toUpperCase() : '??');

  return (
    <div className="bg-elevated px-500 py-600 font-sans">
      {/* Author row */}
      <div className="flex items-center gap-400 mb-500">
        {/* Accent avatar circle */}
        <div className="flex-shrink-0 flex items-center justify-center rounded-pill bg-accent w-[48px] h-[48px]">
          <span className="text-ink-on-photo-light text-title-md font-semibold">
            {initials}
          </span>
        </div>

        {/* Name + category */}
        <div className="flex-1 min-w-0">
          <p className="text-body-md font-semibold text-ink-primary">
            {post.name || 'Anonymous'}
          </p>
          {post.category && (
            <span className="inline-block rounded-pill px-300 py-100 mt-100 bg-accent text-ink-on-photo-light text-label font-semibold">
              {post.category}
            </span>
          )}
        </div>
      </div>

      {/* Title — font-display per Hearth */}
      {post.title && (
        <h2 className="font-display text-title-lg text-ink-primary mb-300">
          {post.title}
        </h2>
      )}

      {/* Body / preview text */}
      {post.preview && (
        <p className="text-body-md text-ink-secondary">
          {post.preview}
        </p>
      )}
    </div>
  );
}
