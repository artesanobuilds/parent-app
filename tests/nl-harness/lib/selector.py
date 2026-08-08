"""
Selective execution: map changed-file paths -> affected flow specs.

Used by CI to decide which subset of flows to run on each push. The map is
hand-maintained; when in doubt, fall back to running all tier-1 flows.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SPECS_ROOT = REPO_ROOT / "tests" / "nl-harness" / "specs"


# `*` means "every flow" (e.g. storage / server.py changes touch everything).
#
# EVERY key must be a path that really exists, and every value a spec that really
# exists. Three keys here were phantoms for months — `app/auth_service.py`,
# `app/profiling_service.py` and `app/cms.py` do not exist (the real modules are
# `auth.py`/`auth_router.py`, `profiling.py`, and the CMS routes live in
# `server.py`), so auth, profiling and CMS changes routed NOTHING. A fourth,
# `app/community.py`, pointed at a flow deleted with the public board. Both
# failure modes are silent: the selector just returns a smaller set and CI goes
# green having tested less than it claims. `test_selector_map_integrity.py` now
# fails on either, so this map cannot rot again.
MODULE_DEPENDENCY_MAP: dict[str, list[str]] = {
    # Broad touches — server.py + storage + migrations affect everything
    "mvp-backend/app/server.py": ["*"],
    "mvp-backend/app/duckdb_storage.py": ["*"],
    "mvp-backend/app/migrations.py": ["*"],

    # Auth surface
    "mvp-backend/app/auth.py": ["parent-onboarding-happy-path", "auth-pairing-code",
                                "cross-family-isolation", "session-logout-and-delete"],
    "mvp-backend/app/auth_router.py": ["parent-onboarding-happy-path",
                                       "session-logout-and-delete"],
    "mvp-backend/app/auth_pairing.py": ["auth-pairing-code"],
    "mvp-backend/app/auth_providers.py": ["auth-pairing-code",
                                          "parent-onboarding-happy-path"],
    "mvp-backend/app/auth_login_google.py": ["auth-pairing-code"],
    "mvp-backend/app/admin_auth.py": ["admin-token-gating"],
    "mvp-backend/app/rate_limit.py": ["auth-pairing-code",
                                      "parent-onboarding-happy-path"],

    # Profile + onboarding surface
    "mvp-backend/app/profiling.py": ["parent-onboarding-happy-path",
                                     "profile-avatar-upload",
                                     "session-logout-and-delete"],
    "mvp-backend/app/prompt_synthesis.py": ["parent-onboarding-happy-path", "kid-agent-lifecycle"],
    "mvp-backend/app/onboarding_agent.py": ["parent-onboarding-happy-path"],
    "mvp-backend/app/onboarding_warmup.py": ["onboarding-warmup-first-run"],
    "mvp-backend/app/blobs/": ["profile-avatar-upload"],

    # Content surface
    "mvp-backend/app/content.py": ["library-browse-and-tag-filter",
                                   "saved-items-lifecycle",
                                   "parquet-snapshot-integrity",
                                   "onboarding-warmup-first-run",
                                   "voice-convai-parent-cards"],

    # Kid-agent surface
    "mvp-backend/app/kid_agent_service.py": ["kid-agent-lifecycle"],
    "mvp-backend/app/kid_agent.py": ["kid-agent-lifecycle",
                                     "voice-convai-kid-moderation"],
    "mvp-backend/app/moderation.py": ["kid-agent-lifecycle",
                                      "voice-convai-kid-moderation"],
    "mvp-backend/app/agent.py": ["kid-agent-lifecycle", "cos-chat-power-tools",
                                 "onboarding-warmup-first-run"],
    "mvp-backend/app/thread_repair.py": ["cos-chat-power-tools",
                                         "voice-convai-parent-cards"],

    # Voice surface
    "mvp-backend/app/convai_endpoint.py": ["voice-convai-kid-moderation"],
    "mvp-backend/app/parent_convai_endpoint.py": ["voice-convai-parent-cards"],

    # Legal + consent live entirely in `server.py` (already `*`) — there is no
    # `app/legal.py` or `app/consent.py`, and adding one as a key would be a
    # fourth phantom. What CAN change independently is the published document
    # text, which is what the acceptance gate versions against.
    "mvp-backend/parent-dashboard/docs/privacy-and-data.md": [
        "legal-acceptance-lifecycle"
    ],

    # Circle surface (beta-v1 sprint 2) — replaces the public board and 1:1 DMs,
    # both retired in migration v21.
    "mvp-backend/app/circle.py": ["circle-conversation-lifecycle"],
    "mvp-backend/app/household.py": ["circle-conversation-lifecycle"],

    # Planner / chief-of-staff surface. The board payload is a cross-surface
    # contract (iOS decodes fit_score / fit_reason / todos / overlaps), so
    # anything shaping it re-runs the planner flow.
    "mvp-backend/app/cos/lifecycle.py": ["planner-match-and-overlap",
                                         "extracurricular-fall-signup",
                                         "registration-watch", "trip-week"],
    "mvp-backend/app/cos/planning.py": ["planner-match-and-overlap", "trip-week"],
    "mvp-backend/app/cos/router.py": ["planner-match-and-overlap",
                                      "cos-chat-power-tools", "cos-quick-outings",
                                      "extracurricular-fall-signup", "trip-week",
                                      "registration-watch"],
    "mvp-backend/app/cos/tools.py": ["cos-chat-power-tools", "cos-quick-outings",
                                     "extracurricular-fall-signup", "trip-week"],
    "mvp-backend/app/cos/agent.py": ["cos-chat-power-tools", "cos-quick-outings"],
    "mvp-backend/app/cos/prompt.py": ["cos-chat-power-tools", "cos-quick-outings"],
    "mvp-backend/app/cos/outings.py": ["cos-quick-outings"],
    "mvp-backend/app/cos/verticals.py": ["extracurricular-fall-signup", "trip-week",
                                         "cos-chat-power-tools"],
    "mvp-backend/app/cos/export.py": ["parquet-snapshot-integrity"],

    # Research / discovery surface
    "mvp-backend/app/research/graph.py": ["cos-chat-power-tools", "research-dedup",
                                          "research-openai-outage",
                                          "planner-match-and-overlap"],
    "mvp-backend/app/research/worker.py": ["concurrent-enqueue-resilience",
                                           "research-worker-saturation",
                                           "research-backoff-recovery",
                                           "research-dedup"],
    "mvp-backend/app/research/router.py": ["cos-chat-power-tools",
                                           "concurrent-enqueue-resilience",
                                           "research-dedup",
                                           "cross-family-isolation"],
    "mvp-backend/app/research/geo.py": ["discovery-geo-coverage"],

    # Ingest surface
    "mvp-backend/app/ingest/": ["school-flyer-chain"],

    # Watchlist surface
    "mvp-backend/app/watchlist/": ["registration-watch"],

    # Saved items
    "mvp-backend/app/summary.py": ["onboarding-warmup-first-run"],

    # The harness itself: any change to flow_context / client / personas
    # re-runs everything (those are the substrate)
    "tests/nl-harness/lib/": ["*"],
}


def _all_specs() -> list[tuple[str, int]]:
    """Return list of (spec_name, tier) discovered under specs/."""
    out: list[tuple[str, int]] = []
    for spec_path in SPECS_ROOT.rglob("*.flow.yml"):
        with open(spec_path) as fh:
            doc = yaml.safe_load(fh) or {}
        spec = doc.get("spec") or {}
        name = spec.get("name")
        tier = int(spec.get("tier", 99))
        if name:
            out.append((name, tier))
    return out


def all_tier1_flow_names() -> set[str]:
    return {name for name, tier in _all_specs() if tier == 1}


def all_flow_names() -> set[str]:
    return {name for name, _ in _all_specs()}


def select_flows(changed_files: Iterable[str]) -> set[str]:
    """
    Union the flows touched by `changed_files` with all tier-1 flows.
    A path matches a map key if `changed_file.startswith(key)`.
    The wildcard `*` resolves to all flow names.
    """
    affected: set[str] = set()
    tier1 = all_tier1_flow_names()
    all_flows = all_flow_names()

    for changed in changed_files:
        for prefix, flows in MODULE_DEPENDENCY_MAP.items():
            if changed.startswith(prefix):
                if "*" in flows:
                    affected.update(all_flows)
                else:
                    affected.update(flows)

    # tier-1 always runs
    affected.update(tier1)
    return affected
