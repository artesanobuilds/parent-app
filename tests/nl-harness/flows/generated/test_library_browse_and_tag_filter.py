# flows/generated/test_library_browse_and_tag_filter.py
#
# @generated_from: specs/tier-1/library-browse-and-tag-filter.flow.yml
# @generated_at: 2026-05-31T15:00:00Z
# @modules: content
# @promoted_by: (none -- awaiting review)
#
import pytest

pytestmark = [pytest.mark.tier1, pytest.mark.readonly_safe]


def test_browse_categories_then_articles_with_filters(flow_ctx):
    # ── Step 1: categories list, shape includes parent_id (nullable) ─
    cats_resp = flow_ctx.get("/content/categories")
    assert cats_resp.status_code == 200, cats_resp.text
    cats = cats_resp.json()
    assert isinstance(cats, list) and len(cats) >= 1, "expected >=1 category"
    for cat in cats:
        assert "id" in cat and "name" in cat, f"category missing id/name: {cat}"
        # parent_id may be absent on legacy DBs that haven't run the v4 migration.
        # When present, must be a string or null. When absent, that's a regression
        # against the Phase 0 work and we flag it.
        assert "parent_id" in cat, (
            "category response missing `parent_id` — Phase 0 migration may not have "
            f"applied. Run `pytest -k taxonomy` against a fresh DB. Category: {cat}"
        )
        assert cat["parent_id"] is None or isinstance(cat["parent_id"], str), \
            f"parent_id must be null or string, got {cat['parent_id']!r}"

    # ── Step 2: full article list ───────────────────────────────────
    arts_resp = flow_ctx.get("/content/articles")
    assert arts_resp.status_code == 200, arts_resp.text
    articles = arts_resp.json()
    assert isinstance(articles, list) and len(articles) >= 1, "expected >=1 article"
    for art in articles:
        for key in ("id", "category", "title"):
            assert key in art, f"article missing {key!r}: {art}"
        # tags is expected as a list (possibly empty)
        assert isinstance(art.get("tags", []), list), \
            f"article.tags must be a list, got {type(art.get('tags'))!r}"

    # ── Step 3: category filter narrows results correctly ───────────
    first_cat_id = cats[0]["id"]
    cat_filter_resp = flow_ctx.get("/content/articles", params={"category": first_cat_id})
    assert cat_filter_resp.status_code == 200
    cat_filtered = cat_filter_resp.json()
    assert isinstance(cat_filtered, list)
    for art in cat_filtered:
        assert art["category"] == first_cat_id, (
            f"category={first_cat_id} filter leaked article from "
            f"category={art['category']!r}"
        )

    # ── Step 4: tag filter narrows correctly when tag is real ───────
    # Find an article that has at least one tag; if none, skip the tag-specific
    # invariants but still verify the unknown-tag behavior below.
    article_with_tag = next(
        (a for a in articles if isinstance(a.get("tags"), list) and a["tags"]),
        None,
    )
    if article_with_tag is not None:
        sample_tag = article_with_tag["tags"][0]
        tag_resp = flow_ctx.get("/content/articles", params={"tag": sample_tag})
        assert tag_resp.status_code == 200
        tag_filtered = tag_resp.json()
        assert isinstance(tag_filtered, list) and len(tag_filtered) >= 1, \
            f"tag={sample_tag!r} filter returned empty list but {article_with_tag['id']} has the tag"
        for art in tag_filtered:
            assert sample_tag in art.get("tags", []), \
                f"tag={sample_tag} filter leaked article without that tag: {art['id']}"

        # ── Step 5: composing category + tag is AND, not OR ─────────
        both_resp = flow_ctx.get(
            "/content/articles",
            params={"category": article_with_tag["category"], "tag": sample_tag},
        )
        assert both_resp.status_code == 200
        both = both_resp.json()
        for art in both:
            assert art["category"] == article_with_tag["category"]
            assert sample_tag in art.get("tags", [])

    # ── Step 6: unknown tag returns [] with 200 (not 404) ───────────
    unknown_resp = flow_ctx.get(
        "/content/articles",
        params={"tag": "this-tag-definitely-does-not-exist-12345"},
    )
    assert unknown_resp.status_code == 200, unknown_resp.text
    assert unknown_resp.json() == [], \
        f"expected [] for unknown tag, got {unknown_resp.json()!r}"

    # ── Step 7: article detail loads the same shape with content ────
    target = articles[0]
    detail_resp = flow_ctx.get(f"/content/articles/{target['id']}")
    assert detail_resp.status_code == 200, detail_resp.text
    detail = detail_resp.json()
    for key in ("id", "category", "title"):
        assert key in detail
    # `content` is optional on list view but expected on detail.
    # We don't assert non-empty — some test fixtures may have empty content —
    # but the key should be present.
    assert "content" in detail, "detail view should include `content` field"
