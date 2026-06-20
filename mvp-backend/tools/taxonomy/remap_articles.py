"""
LLM-assisted re-map of every existing article onto the Phase 1 taxonomy.

For each article we ask GPT to pick:
  - One TOP-LEVEL parent category (iOS Library browses parents today; the
    99 children exist in the DB for Phase 3 hierarchical UX but don't drive
    article filtering yet).
  - One CHILD category id from the same parent — recorded as a tag, so the
    sub-topic survives in `articles.tags` and is available for `?tag=` filters.
  - 2-4 additional tags from the controlled vocabulary (age band, format,
    voice/inspiration, concern, identity).

We PUT /cms/articles/{id} with the new category + merged tags. Existing
tags are preserved (deduped + union'd with the LLM's suggestions).

Run:
  BASE_URL=http://localhost:8904 \
  ADMIN_TOKEN=dev-admin \
  OPENAI_API_KEY=... \
  python mvp-backend/tools/taxonomy/remap_articles.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from taxonomy import (  # noqa: E402
    TAXONOMY,
    TAG_VOCABULARY,
    all_top_level_ids,
    all_child_ids,
    flat_tag_list,
)


def _taxonomy_block_for_prompt() -> str:
    """Render the full new taxonomy as a compact prompt block."""
    lines = []
    for parent, children in TAXONOMY:
        kid_slugs = ", ".join(c.id for c in children)
        lines.append(f"- {parent.id} ({parent.name}): {kid_slugs}")
    return "\n".join(lines)


def _tag_block_for_prompt() -> str:
    return "\n".join(
        f"  {axis}: {', '.join(values)}"
        for axis, values in TAG_VOCABULARY.items()
    )


SYSTEM_PROMPT = """You are a content taxonomy classifier. You map parenting articles onto a
fixed taxonomy. You ALWAYS respond with valid JSON matching the requested schema, nothing else."""


def build_user_prompt(article: dict) -> str:
    title = article.get("title", "")
    subtitle = article.get("subtitle", "")
    summary = article.get("summary", "")
    content = article.get("content") or ""
    content_excerpt = content[:1200] if content else ""
    return f"""Classify the following article into the parent-app taxonomy.

TAXONOMY (top-level parent slug → children slugs):
{_taxonomy_block_for_prompt()}

TAG VOCABULARY (closed set — only use values from this list):
{_tag_block_for_prompt()}

ARTICLE:
title: {title!r}
subtitle: {subtitle!r}
summary: {summary!r}
content_excerpt: {content_excerpt!r}

Return JSON with this exact shape:
{{
  "category": "<one top-level parent slug>",
  "child_category": "<one child slug under that parent, or null if none fits>",
  "tags": ["<tag>", "<tag>", "..."]
}}

Rules:
- "category" MUST be one of the top-level parent slugs.
- "child_category" MUST be one of that parent's children, or null. Do NOT pick a
  child from a different parent.
- "tags" must be 2 to 4 entries, each drawn from the TAG VOCABULARY above.
- Include the age_band tag whenever the article's audience is age-specific.
- Include a format tag when the format is obvious (recipe, deep-dive, etc.).
- Prefer fewer, sharper tags over many vague ones.

Respond with ONLY the JSON object, no prose."""


def classify_with_openai(article: dict, *, model: str) -> dict:
    """Returns {'category': ..., 'child_category': ..., 'tags': [...]}.
    Raises on hard error; caller decides whether to skip."""
    from openai import OpenAI
    client = OpenAI()
    # NOTE: gpt-5.5 only accepts the default temperature (1.0); we used to
    # set 0.2 for determinism but the API rejects it. Reproducibility comes
    # from the closed-set tag vocabulary + post-call validation instead.
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(article)},
        ],
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content or "{}"
    return json.loads(raw)


def validate_classification(c: dict) -> tuple[bool, str]:
    """Returns (ok, reason)."""
    cat = c.get("category")
    if cat not in all_top_level_ids():
        return False, f"category {cat!r} is not a top-level parent"
    child = c.get("child_category")
    if child is not None:
        if child not in all_child_ids():
            return False, f"child_category {child!r} is not a known child id"
        # Verify the child actually belongs to the chosen parent
        from taxonomy import TAXONOMY as T
        parent_to_children = {p.id: {x.id for x in kids} for p, kids in T}
        if child not in parent_to_children.get(cat, set()):
            return False, f"child {child!r} does not belong to parent {cat!r}"
    tags = c.get("tags") or []
    if not isinstance(tags, list) or not tags:
        return False, "tags must be a non-empty list"
    allowed = set(flat_tag_list())
    bad = [t for t in tags if t not in allowed]
    if bad:
        return False, f"tags include unknown values: {bad}"
    return True, ""


def merge_tags(existing: list[str] | None, llm_tags: list[str], child_slug: str | None) -> list[str]:
    """Union + dedupe. Include the child category slug as a tag so the
    sub-topic survives in articles.tags (queryable via /content/articles?tag=)."""
    out: list[str] = []
    seen: set[str] = set()
    for t in (existing or []):
        if t and t not in seen:
            out.append(t)
            seen.add(t)
    for t in llm_tags:
        if t not in seen:
            out.append(t)
            seen.add(t)
    if child_slug and child_slug not in seen:
        out.append(child_slug)
        seen.add(child_slug)
    return out


def main() -> int:
    base_url = os.getenv("BASE_URL", "http://localhost:8904").rstrip("/")
    admin_token = os.getenv("ADMIN_TOKEN")
    if not admin_token:
        print("ADMIN_TOKEN not set", file=sys.stderr)
        return 2
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set", file=sys.stderr)
        return 2
    model = os.getenv("REMAP_MODEL", "gpt-5.5")

    headers = {"X-Admin-Token": admin_token, "Content-Type": "application/json"}
    failures: list[tuple[str, str]] = []
    succeeded = 0
    distribution: dict[str, int] = {}

    with httpx.Client(base_url=base_url, headers=headers, timeout=60.0) as client:
        articles = client.get("/content/articles").json()
        print(f"remapping {len(articles)} articles with model={model}…")
        print()

        for i, art in enumerate(articles, 1):
            art_id = art["id"]
            old_cat = art.get("category")
            try:
                full = client.get(f"/content/articles/{art_id}").json()
            except Exception as exc:
                failures.append((art_id, f"fetch: {exc}"))
                continue

            try:
                c = classify_with_openai(full, model=model)
            except Exception as exc:
                failures.append((art_id, f"openai: {exc}"))
                continue

            ok, reason = validate_classification(c)
            if not ok:
                failures.append((art_id, f"validation: {reason} (got {c})"))
                continue

            new_cat = c["category"]
            child = c.get("child_category")
            merged_tags = merge_tags(full.get("tags"), c["tags"], child)

            put = client.put(
                f"/cms/articles/{art_id}",
                json={"category": new_cat, "tags": merged_tags},
            )
            if put.status_code != 200:
                failures.append((art_id, f"PUT {put.status_code}: {put.text[:200]}"))
                continue

            succeeded += 1
            distribution[new_cat] = distribution.get(new_cat, 0) + 1
            print(
                f"  [{i:2}/{len(articles)}] {art_id:35} "
                f"{old_cat!r:25} → {new_cat!r:25} "
                f"+{len(merged_tags)} tags"
            )

    print()
    print(f"remapped : {succeeded}/{len(articles)}")
    print(f"failed   : {len(failures)}")
    for aid, reason in failures[:20]:
        print(f"  {aid:35} {reason}")
    print()
    print("distribution across new top-level parents:")
    for cat_id in all_top_level_ids():
        n = distribution.get(cat_id, 0)
        bar = "█" * n
        print(f"  {cat_id:25} {n:3} {bar}")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
