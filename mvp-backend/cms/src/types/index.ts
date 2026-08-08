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

export interface ContentStats {
  articles: number;
  categories: number;
  articles_by_category: Record<string, number>;
}
