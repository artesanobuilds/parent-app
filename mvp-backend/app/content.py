"""Content library service for MVP.

Loads the content library JSON and provides methods to query articles and
community posts by category or keyword. Also exposes a compact summary
suitable for injection into the AI agent's system prompt.
"""

import json
import os
import random
from typing import Any, Dict, List, Optional

_DIR = os.path.dirname(os.path.abspath(__file__))
_LIBRARY_PATH = os.path.join(_DIR, "content_library.json")

_data: Dict[str, Any] = {}


def _load():
    global _data
    if not _data:
        with open(_LIBRARY_PATH, "r") as f:
            _data = json.load(f)
    return _data


def get_categories() -> List[Dict]:
    return _load()["categories"]


def get_articles(category: Optional[str] = None, limit: int = 50) -> List[Dict]:
    articles = _load()["library_articles"]
    if category:
        articles = [a for a in articles if a["category"] == category]
    # Strip full content from list responses for performance
    return [{k: v for k, v in a.items() if k != "content"} for a in articles[:limit]]


def get_article(article_id: str) -> Optional[Dict]:
    """Return a single article by ID, including full content."""
    for article in _load()["library_articles"]:
        if article["id"] == article_id:
            return article
    return None


def get_community_posts(category: Optional[str] = None, limit: int = 50) -> List[Dict]:
    posts = _load()["community_posts"]
    if category:
        posts = [p for p in posts if p["category"] == category]
    return posts[:limit]


def search_content(query: str, limit: int = 10) -> Dict[str, List[Dict]]:
    """Simple keyword search across articles and community posts."""
    query_lower = query.lower()
    data = _load()

    matching_articles = []
    for article in data["library_articles"]:
        searchable = f"{article['title']} {article['subtitle']} {article['summary']} {' '.join(article.get('tags', []))}".lower()
        if query_lower in searchable:
            matching_articles.append(article)

    matching_posts = []
    for post in data["community_posts"]:
        searchable = f"{post['title']} {post['preview']}".lower()
        if query_lower in searchable:
            matching_posts.append(post)

    return {
        "articles": matching_articles[:limit],
        "community_posts": matching_posts[:limit],
    }


def get_relevant_content(topic: str, limit: int = 5) -> Dict[str, List[Dict]]:
    """Return content relevant to a topic, using keyword matching and tag overlap."""
    topic_words = set(topic.lower().split())
    data = _load()

    def score_article(a: Dict) -> int:
        text = f"{a['title']} {a['subtitle']} {' '.join(a.get('tags', []))}".lower()
        return sum(1 for w in topic_words if w in text)

    def score_post(p: Dict) -> int:
        text = f"{p['title']} {p['preview']}".lower()
        return sum(1 for w in topic_words if w in text)

    scored_articles = [(score_article(a), a) for a in data["library_articles"]]
    scored_posts = [(score_post(p), p) for p in data["community_posts"]]

    scored_articles.sort(key=lambda x: x[0], reverse=True)
    scored_posts.sort(key=lambda x: x[0], reverse=True)

    # Return top matches, falling back to random if no keyword matches
    articles = [a for s, a in scored_articles if s > 0][:limit]
    posts = [p for s, p in scored_posts if s > 0][:limit]

    if not articles:
        articles = random.sample(data["library_articles"], min(limit, len(data["library_articles"])))
    if not posts:
        posts = random.sample(data["community_posts"], min(limit, len(data["community_posts"])))

    return {"articles": articles, "community_posts": posts}


def content_catalog_for_prompt() -> str:
    """Return a compact content catalog string for the AI agent system prompt."""
    data = _load()
    lines = ["Available MVP content library (recommend relevant items inline with markdown links):"]
    lines.append("")
    for cat in data["categories"]:
        lines.append(f"## {cat['emoji']} {cat['name']}")
        cat_articles = [a for a in data["library_articles"] if a["category"] == cat["id"]]
        for a in cat_articles:
            lines.append(f"- [{a['title']}](mvp://library/{a['id']}) — {a['subtitle']}")
        lines.append("")

    lines.append("## Community discussions (suggest when relevant):")
    for p in data["community_posts"][:10]:
        lines.append(f"- [{p['title']}](mvp://community/{p['id']}) by {p['name']}")

    return "\n".join(lines)
