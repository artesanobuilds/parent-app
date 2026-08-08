"""Content library service for MVP.

Queries content from DuckDB storage and provides methods to search articles by
category or keyword. Also exposes a compact summary suitable for injection into
the AI agent's system prompt.

The community board is GONE (beta-v1 sprint 2): its `community_posts` /
`post_replies` tables were dropped in migration v21 and Circle conversations
(app/circle.py) are the successor surface. There is exactly one kind of library
content now — the article.
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


def search_content(query: str, limit: int = 10) -> Dict[str, List[Dict]]:
    """Keyword search across articles using DuckDB ILIKE."""
    return {"articles": _db().search_articles(query, limit=limit)}


def get_relevant_content(topic: str, limit: int = 5) -> Dict[str, List[Dict]]:
    """Return content relevant to a topic, using per-word ILIKE matching in DuckDB."""
    words = [w for w in topic.lower().split() if len(w) > 2]

    articles = _db().score_articles_by_words(words, limit=limit) if words else []

    # Fallback to random if no keyword matches
    if not articles:
        all_articles = _db().get_articles(limit=100)
        articles = random.sample(all_articles, min(limit, len(all_articles)))

    return {"articles": articles}


# ── "For you" ranked library feed ────────────────────────────────────
# The whole library, stack-ranked per family — NOT the categorical browse.
FOR_YOU_DEFAULT_LIMIT = 20
FOR_YOU_MAX_LIMIT = 100
# Candidate pool = the whole library; this only bounds a pathological table.
FOR_YOU_LIBRARY_CAP = 500


def get_for_you_articles(
    words: List[str],
    limit: int = FOR_YOU_DEFAULT_LIMIT,
    offset: int = 0,
) -> Dict[str, Any]:
    """Return the WHOLE library ordered by overlap with `words`, paginated.

    Unlike `get_relevant_content` this never truncates to the matches:
    `score_articles_by_words` has `HAVING score > 0`, so an empty word bag (a
    brand-new family) or one that matches nothing would yield ZERO rows. The
    scored matches lead, then the rest of the library tops the list up — the
    surface is never blank on first open, which is the whole point of the feed.

    Item shape is exactly `get_articles`' (via a by-id lookup into the unranked
    list, so there is one source of truth for the payload) — the iOS Codable
    layer is strict and a divergent shape empties the entire list.
    """
    db = _db()
    limit = max(1, min(int(limit), FOR_YOU_MAX_LIMIT))
    offset = max(0, int(offset))

    library = db.get_articles(limit=FOR_YOU_LIBRARY_CAP)
    by_id = {a["id"]: a for a in library}

    ranked: List[Dict] = []
    if words:
        for match in db.score_articles_by_words(words, limit=FOR_YOU_LIBRARY_CAP):
            article = by_id.get(match["id"])
            if article is not None:
                ranked.append(article)

    seen = {a["id"] for a in ranked}
    ordered = ranked + [a for a in library if a["id"] not in seen]

    return {
        "items": ordered[offset : offset + limit],
        "total": len(ordered),
        "limit": limit,
        "offset": offset,
        "ranked": bool(ranked),
    }


# Age band → words that actually appear in library copy. The band itself comes
# from app.prompt_synthesis._age_band so "which band is this kid in" has exactly
# one owner. "unknown" maps to nothing — a missing age adds no signal.
_FOR_YOU_AGE_BAND_WORDS = {
    "toddler": ["toddler"],
    "early": ["preschool", "kindergarten"],
    "middle": ["elementary"],
    "tween": ["tween"],
    "teen": ["teen"],
}

# Words too common in parenting copy to discriminate — they'd match nearly
# every article and flatten the ranking back to library order.
_FOR_YOU_STOPWORDS = {
    "the", "and", "for", "with", "but", "not", "our", "out", "are", "was",
    "that", "this", "from", "them", "they", "their", "have", "has", "had",
    "into", "about", "when", "what", "who", "why", "how", "all", "any", "can",
    "get", "got", "too", "very", "just", "more", "most", "less", "than",
    "kid", "kids", "child", "children", "parent", "parents", "parenting",
}

# Each word becomes a CASE branch in the scoring SQL — bound so a chatty
# profile can't build a pathological query.
_FOR_YOU_MAX_WORDS = 24


def for_you_word_bag(family: Dict[str, Any]) -> List[str]:
    """Flatten a family profile into the ranking word bag.

    Parent `stressors` + `goals` + `household_structure`, and per child
    `challenges` + `interests` + an age-band term. Phrases are split into
    words because the scorer ILIKEs each word against title/subtitle/tags.
    Returns [] for a profile with nothing in it — the caller must still
    produce a non-empty feed.

    Lives here (not in app/server) because BOTH consumers need it and one of
    them is the agent: `GET /content/for-you` ranks the feed with it, and the
    merged parent agent ranks the catalog shortlist it recommends from. Putting
    it in server.py would make app/agent.py import app.server — a cycle.
    """
    from app.prompt_synthesis import _age_band

    parent = (family or {}).get("parent") or {}
    children = (family or {}).get("children") or {}

    phrases: List[Any] = []
    phrases.extend(parent.get("stressors") or [])
    phrases.extend(parent.get("goals") or [])
    if parent.get("household_structure"):
        phrases.append(parent["household_structure"])
    for child in (children or {}).values():
        child = child or {}
        phrases.extend(child.get("challenges") or [])
        phrases.extend(child.get("interests") or [])
        age = child.get("age")
        if isinstance(age, (int, float)) and not isinstance(age, bool):
            phrases.extend(_FOR_YOU_AGE_BAND_WORDS.get(_age_band(float(age)), []))

    words: List[str] = []
    seen: set = set()
    for phrase in phrases:
        if not isinstance(phrase, str):
            continue
        for raw in phrase.lower().replace("/", " ").replace("-", " ").split():
            # Strip punctuation AND the ILIKE wildcards (% _) so a profile
            # value can never widen its own match.
            token = "".join(c for c in raw if c.isalnum())
            if len(token) <= 2 or token in _FOR_YOU_STOPWORDS or token in seen:
                continue
            seen.add(token)
            words.append(token)
            if len(words) >= _FOR_YOU_MAX_WORDS:
                return words
    return words


# How many ranked articles the coach gets handed per turn. The Library is no
# longer a browsable surface, so the coach IS the discovery path — but a long
# list crowds out the conversation, and the full catalog is already in the
# static half of the prompt for anything off this shortlist.
FOR_YOU_PROMPT_LIMIT = 8


def for_you_prompt_lines(words: List[str], limit: int = FOR_YOU_PROMPT_LIMIT) -> str:
    """The top of `GET /content/for-you`'s ranking, as prompt text.

    Same ranking function the feed uses, so what the coach reaches for first
    and what the "For you" list shows are the same order — one ranker, two
    surfaces. Returns "" when the profile carries no signal (the coach then
    falls back to the full catalog), and never raises.
    """
    if not words:
        return ""
    try:
        feed = get_for_you_articles(words, limit=max(1, limit))
    except Exception:  # noqa: BLE001
        return ""
    if not feed.get("ranked") or not feed.get("items"):
        return ""
    lines = [
        "Best library matches for THIS family right now (there is no browsable "
        "Library in the app any more — you are how these reach the parent, so "
        "offer one when it genuinely fits):"
    ]
    for a in feed["items"]:
        subtitle = (a.get("subtitle") or "").strip()
        tail = f" — {subtitle}" if subtitle else ""
        lines.append(f"- [{a['title']}](mvp://library/{a['id']}){tail}")
    return "\n".join(lines)


def create_article(data: Dict) -> Dict:
    return _db().create_article(data)


def update_article(article_id: str, data: Dict) -> Optional[Dict]:
    return _db().update_article(article_id, data)


def delete_article(article_id: str) -> bool:
    return _db().delete_article(article_id)


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
    """Return a compact content catalog string for the AI agent system prompt.

    LIBRARY ONLY. The public community board is retired (beta-v1 Phase 1) and
    the `mvp://community/{id}` citations went with it — the coach must never
    emit a link scheme no client routes, which is exactly the bug
    tests/test_coach_citation_contract.py exists to prevent. The
    `community_posts` table itself was dropped in migration v21.
    """
    categories = _db().get_categories()
    all_articles = _db().get_articles(limit=100)

    lines = ["Available MVP content library (recommend relevant items inline with markdown links):"]
    lines.append("")
    for cat in categories:
        lines.append(f"## {cat['emoji']} {cat['name']}")
        cat_articles = [a for a in all_articles if a["category"] == cat["id"]]
        for a in cat_articles:
            lines.append(f"- [{a['title']}](mvp://library/{a['id']}) — {a['subtitle']}")
        lines.append("")

    return "\n".join(lines)
