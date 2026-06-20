"""
Re-map community posts that still reference deleted legacy categories onto
the Phase 1 taxonomy. Mirrors `remap_articles.py` but for posts:
  - PUT /cms/community-posts/{id} with a new top-level parent category
  - Community posts don't carry tags today, so we only update `category`
  - Posts already pointing at a current category are left alone (idempotent)

Run:
  BASE_URL=http://localhost:8904 \
  ADMIN_TOKEN=dev-admin \
  OPENAI_API_KEY=... \
  python mvp-backend/tools/taxonomy/remap_community_posts.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from taxonomy import TAXONOMY, all_top_level_ids  # noqa: E402


def _taxonomy_block() -> str:
    lines = []
    for parent, children in TAXONOMY:
        kid_slugs = ", ".join(c.id for c in children)
        lines.append(f"- {parent.id} ({parent.name}): {kid_slugs}")
    return "\n".join(lines)


SYSTEM_PROMPT = (
    "You are a content taxonomy classifier. You map parenting community posts "
    "onto a fixed taxonomy. You ALWAYS respond with valid JSON, nothing else."
)


def build_prompt(post: dict) -> str:
    return f"""Classify this community post into the parent-app taxonomy.

TAXONOMY (top-level parent slug → children slugs):
{_taxonomy_block()}

POST:
title  : {post.get('title', '')!r}
preview: {post.get('preview', '')!r}
name   : {post.get('name', '')!r}

Return JSON:
{{ "category": "<one top-level parent slug>" }}

Rules:
- "category" MUST be one of the top-level parent slugs above.
- Pick the single best home for the post's topic.
- Respond with ONLY the JSON object, no prose."""


def classify(post: dict, *, model: str) -> str:
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(post)},
        ],
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content or "{}"
    body = json.loads(raw)
    return body.get("category", "")


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
    tops = set(all_top_level_ids())

    with httpx.Client(base_url=base_url, headers=headers, timeout=60.0) as client:
        posts = client.get("/content/community").json()
        # Only remap posts whose category isn't already a valid new top-level
        to_remap = [p for p in posts if p.get("category") not in tops]
        already = len(posts) - len(to_remap)
        print(f"community posts: total={len(posts)} need_remap={len(to_remap)} already_valid={already}")
        print()

        succeeded = 0
        failures: list[tuple[str, str]] = []
        distribution: dict[str, int] = {}

        for i, post in enumerate(to_remap, 1):
            pid = post["id"]
            old_cat = post.get("category")
            try:
                new_cat = classify(post, model=model)
            except Exception as exc:
                failures.append((pid, f"openai: {exc}"))
                continue
            if new_cat not in tops:
                failures.append((pid, f"invalid category {new_cat!r}"))
                continue

            put = client.put(
                f"/cms/community-posts/{pid}",
                json={"category": new_cat},
            )
            if put.status_code != 200:
                failures.append((pid, f"PUT {put.status_code}: {put.text[:200]}"))
                continue

            succeeded += 1
            distribution[new_cat] = distribution.get(new_cat, 0) + 1
            print(f"  [{i:2}/{len(to_remap)}] {pid:25} {old_cat!r:25} → {new_cat!r}")

        print()
        print(f"remapped: {succeeded}/{len(to_remap)}")
        for pid, reason in failures[:20]:
            print(f"  FAILED {pid}: {reason}")

        print()
        print("distribution across new parents:")
        for cat_id in all_top_level_ids():
            n = distribution.get(cat_id, 0)
            bar = "█" * n
            print(f"  {cat_id:25} {n:3} {bar}")

    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
