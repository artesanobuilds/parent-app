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
  /** Eyebrow label above the headline, e.g. "WE TRIED IT". */
  kicker: string;
  /** Eyebrow age band, e.g. "Ages 3–7". */
  age_range: string;
  summary: string;
  tags: string[];
  content?: string;
}

export interface ContentStats {
  articles: number;
  categories: number;
  articles_by_category: Record<string, number>;
}
