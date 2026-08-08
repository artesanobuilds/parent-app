# flows/generated/test_parquet_snapshot_integrity.py
#
# @generated_from: specs/tier-1/parquet-snapshot-integrity.flow.yml
# @generated_at: 2026-05-31T15:30:00Z
# @modules: data_export, content, cms
# @promoted_by: (none -- awaiting review)
#
# Regression guard for the May 2026 column-drift bug where migration v4
# added categories.parent_id but the categories.parquet snapshot still had
# four columns. The bootstrap UPSERT raised a `Binder Error` and silently
# skipped — on a fresh deploy the categories table would have come up empty.
#
# A *true* fresh-DB simulation lives at
#   mvp-backend/tests/test_bootstrap_drift_tolerance.py
# (hermetic; no running backend needed; the bullseye for this class of bug).
#
# This file is the FLOW-LEVEL guard against the same regression: it asserts
# the live API reflects a populated bootstrap and that the snapshot/export
# round-trip preserves the data the iOS app sees.
import pytest

pytestmark = [pytest.mark.tier1, pytest.mark.readonly_safe]


# The subset of BOOTSTRAP_TABLES we can directly probe via the public/admin
# API. The hermetic unit test covers the full list at the storage layer.
# Pair: (parquet_filename, public_path, what_to_assert)
PROBABLE_PARQUETS = [
    "articles.parquet",
    "categories.parquet",
    # community_posts / post_replies were dropped with the public board in the
    # beta-v1 sprint-2 Circle redesign (migration v21) — they are no longer in
    # BOOTSTRAP_TABLES, so they must NOT appear in the export manifest.
    "mvp.parquet",
    # operator-side tables; not exposed via public reads but should still
    # appear in the admin /data/export manifest:
    "kid_agent_configs.parquet",
    "kid_messages.parquet",
    "kid_credentials.parquet",
    "kid_agent_crisis_locks.parquet",
    "moderation_events.parquet",
    "consent_records.parquet",
    "daily_summaries.parquet",
    "audit_events.parquet",
    "auth_tokens.parquet",
]


def test_categories_endpoint_is_populated_and_carries_parent_id(flow_ctx):
    """
    Direct guard against the original bug: categories must not come up empty,
    and the parent_id key (added by migration v4) must be present on every
    row — proving the column survived the storage round-trip.
    """
    resp = flow_ctx.get("/content/categories")
    assert resp.status_code == 200, resp.text
    cats = resp.json()
    assert isinstance(cats, list), f"expected list, got {type(cats).__name__}"
    assert len(cats) >= 1, (
        "categories endpoint returned 0 rows. If you're testing against a "
        "fresh deploy, this is the bug: a column drift in the snapshot "
        "parquet caused the bootstrap to silently skip. Check the backend "
        "boot logs for `WARNING:app.duckdb_storage:[duckdb] bootstrap of "
        "categories from categories.parquet skipped`."
    )
    for cat in cats:
        assert "parent_id" in cat, (
            f"category row missing `parent_id` key (added by migration v4). "
            f"Either the migration didn't apply or the response model dropped "
            f"the field. Row: {cat}"
        )
        assert cat["parent_id"] is None or isinstance(cat["parent_id"], str), \
            f"parent_id must be null or string; got {cat['parent_id']!r}"


def test_articles_endpoint_is_populated(flow_ctx):
    """Articles bootstrap is non-empty (same regression class as categories)."""
    resp = flow_ctx.get("/content/articles")
    assert resp.status_code == 200, resp.text
    articles = resp.json()
    assert isinstance(articles, list)
    assert len(articles) >= 1, (
        "articles endpoint returned 0 rows. Check bootstrap warnings in the "
        "backend log."
    )


def test_admin_export_lists_every_expected_parquet(flow_ctx, admin):
    """
    Admin POST /cms/export-parquet writes content parquets; GET /data/export
    writes every bootstrap-table parquet and returns checksums. The manifest
    must include every name in PROBABLE_PARQUETS — a missing entry means a
    table is silently absent from snapshots and a fresh deploy would lose it.
    """
    # Trigger the content-parquet refresh first (idempotent, same effect as
    # the CMS' "export" button).
    refresh = flow_ctx.post("/cms/export-parquet", as_=admin)
    assert refresh.status_code == 200, refresh.text

    export = flow_ctx.get("/data/export", as_=admin)
    assert export.status_code == 200, export.text
    body = export.json()
    assert "checksums" in body, f"missing `checksums` key: {body}"
    manifest = body["checksums"]
    assert isinstance(manifest, dict)

    missing = [p for p in PROBABLE_PARQUETS if p not in manifest]
    assert not missing, (
        f"these tables are not being exported to parquet: {missing}. A fresh "
        f"deploy that rehydrates from /data/* would come up missing them. "
        f"Got manifest keys: {sorted(manifest.keys())}"
    )

    # Every checksum is a 32-char md5 hex (sanity)
    for name, csum in manifest.items():
        assert isinstance(csum, str) and len(csum) == 32, (
            f"checksum for {name} looks malformed: {csum!r}"
        )


def test_categories_survive_admin_reexport_roundtrip(flow_ctx, admin):
    """
    Snapshot/restore round-trip: capture the categories before the admin
    export, run the export, fetch again, and verify shape + parent_id
    preserved. This catches a regression where the export path drops a
    column that the migration added.
    """
    before = flow_ctx.get("/content/categories").json()
    assert isinstance(before, list) and len(before) >= 1
    before_ids = sorted(c["id"] for c in before)
    before_parent_ids = {c["id"]: c.get("parent_id") for c in before}

    # Force a fresh export
    refresh = flow_ctx.post("/cms/export-parquet", as_=admin)
    assert refresh.status_code == 200

    after = flow_ctx.get("/content/categories").json()
    after_ids = sorted(c["id"] for c in after)
    after_parent_ids = {c["id"]: c.get("parent_id") for c in after}

    assert before_ids == after_ids, \
        f"category set changed after re-export: {set(before_ids) ^ set(after_ids)}"
    assert before_parent_ids == after_parent_ids, (
        "parent_id values mutated across the export round-trip. Diff: "
        f"{ {k: (before_parent_ids[k], after_parent_ids[k]) for k in before_parent_ids if before_parent_ids[k] != after_parent_ids.get(k)} }"
    )
