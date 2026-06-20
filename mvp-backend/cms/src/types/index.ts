export interface Category {
  id: string;
  name: string;
  emoji: string;
  description: string;
  parent_id?: string | null;
}

export interface Article {
  id: string;
  category: string;
  title: string;
  subtitle: string;
  emoji: string;
  author: string;
  read_time: string;
  summary: string;
  tags: string[];
  content?: string;
}

export interface CommunityPost {
  id: string;
  category: string;
  initials: string;
  name: string;
  title: string;
  preview: string;
  user_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ContentStats {
  articles: number;
  community_posts: number;
  categories: number;
  articles_by_category: Record<string, number>;
  posts_by_category: Record<string, number>;
}
