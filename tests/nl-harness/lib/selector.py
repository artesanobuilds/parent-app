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
MODULE_DEPENDENCY_MAP: dict[str, list[str]] = {
    # Broad touches — server.py + storage + migrations affect everything
    "mvp-backend/app/server.py": ["*"],
    "mvp-backend/app/duckdb_storage.py": ["*"],
    "mvp-backend/app/migrations.py": ["*"],

    # Auth + onboarding surface
    "mvp-backend/app/auth_service.py": ["parent-onboarding-happy-path"],
    "mvp-backend/app/profiling_service.py": ["parent-onboarding-happy-path"],
    "mvp-backend/app/prompt_synthesis.py": ["parent-onboarding-happy-path", "kid-agent-lifecycle"],

    # Content surface
    "mvp-backend/app/content.py": ["library-browse-and-tag-filter"],

    # Kid-agent surface
    "mvp-backend/app/kid_agent_service.py": ["kid-agent-lifecycle"],
    "mvp-backend/app/moderation.py": ["kid-agent-lifecycle"],
    "mvp-backend/app/agent.py": ["kid-agent-lifecycle"],

    # CMS surface
    "mvp-backend/app/cms.py": ["admin-token-gating", "library-browse-and-tag-filter"],

    # Community surface
    "mvp-backend/app/community.py": ["community-post-and-reply"],

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
