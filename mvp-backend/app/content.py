"""Content library service for MVP.

Queries content from DuckDB storage and provides methods to search articles
and community posts by category or keyword. Also exposes a compact summary
suitable for injection into the AI agent's system prompt.
"""

import random
from typing import Any, Dict, List, Optional

from app.duckdb_storage import DuckDBStorage

_storage: Optional[DuckDBStorage] = None


def init(storage: DuckDBStorage) -> None:
    """Initialize with the shared DuckDBStorage instance."""
    global _storage
    _storage = storage


def _db() -> DuckDBStorage:
    if _storage is None:
        raise RuntimeError("content service not initialized — call content.init(storage) first")
    return _storage


def get_categories() -> List[Dict]:
    return _db().get_categories()


def get_articles(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50,
) -> List[Dict]:
    return _db().get_articles(category=category, tag=tag, limit=limit)


def get_article(article_id: str) -> Optional[Dict]:
    """Return a single article by ID, including full content."""
    return _db().get_article(article_id)


def get_community_posts(category: Optional[str] = None, limit: int = 50) -> List[Dict]:
    return _db().get_community_posts(category=category, limit=limit)


def search_content(query: str, limit: int = 10) -> Dict[str, List[Dict]]:
    """Keyword search across articles and community posts using DuckDB ILIKE."""
    return {
        "articles": _db().search_articles(query, limit=limit),
        "community_posts": _db().search_community_posts(query, limit=limit),
    }


def get_relevant_content(topic: str, limit: int = 5) -> Dict[str, List[Dict]]:
    """Return content relevant to a topic, using per-word ILIKE matching in DuckDB."""
    words = [w for w in topic.lower().split() if len(w) > 2]

    if words:
        articles = _db().score_articles_by_words(words, limit=limit)
        posts = _db().score_posts_by_words(words, limit=limit)
    else:
        articles = []
        posts = []

    # Fallback to random if no keyword matches
    if not articles:
        all_articles = _db().get_articles(limit=100)
        articles = random.sample(all_articles, min(limit, len(all_articles)))
    if not posts:
        all_posts = _db().get_community_posts(limit=100)
        posts = random.sample(all_posts, min(limit, len(all_posts)))

    return {"articles": articles, "community_posts": posts}


def get_community_post(post_id: str) -> Optional[Dict]:
    return _db().get_community_post(post_id)


def create_article(data: Dict) -> Dict:
    return _db().create_article(data)


def update_article(article_id: str, data: Dict) -> Optional[Dict]:
    return _db().update_article(article_id, data)


def delete_article(article_id: str) -> bool:
    return _db().delete_article(article_id)


def create_community_post(data: Dict) -> Dict:
    return _db().create_community_post(data)


def update_community_post(post_id: str, data: Dict) -> Optional[Dict]:
    return _db().update_community_post(post_id, data)


def delete_community_post(post_id: str) -> bool:
    return _db().delete_community_post(post_id)


def get_replies_for_post(post_id: str, limit: int = 100) -> List[Dict]:
    return _db().get_replies_for_post(post_id, limit=limit)


def create_reply(data: Dict) -> Dict:
    return _db().create_reply(data)


def get_reply_counts(post_ids: List[str]) -> Dict[str, int]:
    return _db().get_reply_counts(post_ids)


def create_category(data: Dict) -> Dict:
    return _db().create_category(data)


def update_category(category_id: str, data: Dict) -> Optional[Dict]:
    return _db().update_category(category_id, data)


def delete_category(category_id: str) -> bool:
    return _db().delete_category(category_id)


def get_content_stats() -> Dict:
    return _db().get_content_stats()


def export_content_parquet() -> None:
    _db().export_content_parquet()


def content_catalog_for_prompt() -> str:
    """Return a compact content catalog string for the AI agent system prompt."""
    categories = _db().get_categories()
    all_articles = _db().get_articles(limit=100)
    all_posts = _db().get_community_posts(limit=100)

    lines = ["Available MVP content library (recommend relevant items inline with markdown links):"]
    lines.append("")
    for cat in categories:
        lines.append(f"## {cat['emoji']} {cat['name']}")
        cat_articles = [a for a in all_articles if a["category"] == cat["id"]]
        for a in cat_articles:
            lines.append(f"- [{a['title']}](mvp://library/{a['id']}) — {a['subtitle']}")
        lines.append("")

    lines.append("## Community discussions (suggest when relevant):")
    for p in all_posts[:10]:
        lines.append(f"- [{p['title']}](mvp://community/{p['id']}) by {p['name']}")

    return "\n".join(lines)
