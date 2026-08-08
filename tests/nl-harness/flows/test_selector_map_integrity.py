# flows/test_selector_map_integrity.py
#
# Not a flow — a guard on the selector itself. Runs with no backend.
#
# `MODULE_DEPENDENCY_MAP` decides which flows CI runs for a given diff. Both ways
# it can rot are SILENT: a key naming a file that doesn't exist never matches, and
# a value naming a deleted spec never resolves. Either way the selector returns a
# smaller set and CI passes having tested less than it reports.
#
# This actually happened. `app/auth_service.py`, `app/profiling_service.py` and
# `app/cms.py` were keys for months and none of those files exist (the real
# modules are `auth.py`/`auth_router.py`, `profiling.py`, and the CMS routes live
# in `server.py`) — so auth, profiling and CMS changes routed nothing. A fourth
# key, `app/community.py`, pointed at a flow deleted with the public board.
#
import sys
from pathlib import Path

import pytest

HARNESS_ROOT = Path(__file__).resolve().parents[1]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from lib.selector import (  # noqa: E402
    MODULE_DEPENDENCY_MAP,
    REPO_ROOT,
    _all_specs,
)

pytestmark = pytest.mark.tier1


def test_every_mapped_path_exists():
    """A key that names no real file silently routes nothing."""
    missing = [key for key in MODULE_DEPENDENCY_MAP if not (REPO_ROOT / key).exists()]
    assert not missing, (
        "selector keys point at files that do not exist, so changes to the real "
        f"module run no flows: {missing}"
    )


def test_every_referenced_spec_exists():
    """A value that names a deleted spec silently routes nothing."""
    names = {name for name, _ in _all_specs()}
    referenced = {
        spec
        for specs in MODULE_DEPENDENCY_MAP.values()
        for spec in specs
        if spec != "*"
    }
    dead = sorted(referenced - names)
    assert not dead, f"selector references specs that no longer exist: {dead}"


def test_every_spec_is_reachable_from_some_file():
    """Every spec must be routed by at least one path.

    An unrouted spec only ever runs via the always-run tier-1 set — so an
    unrouted TIER-2 spec effectively never runs on a normal push, which is
    indistinguishable from having deleted it.
    """
    names = {name for name, _ in _all_specs()}
    referenced = {
        spec
        for specs in MODULE_DEPENDENCY_MAP.values()
        for spec in specs
        if spec != "*"
    }
    unrouted = sorted(names - referenced)
    assert not unrouted, (
        "these specs are not routed by any file path, so a targeted CI run will "
        f"never select them: {unrouted}"
    )


def test_every_spec_has_a_generated_test():
    """A spec with no generated test is documentation, not coverage."""
    generated = HARNESS_ROOT / "flows" / "generated"
    orphans = []
    for name, _tier in _all_specs():
        if not (generated / f"test_{name.replace('-', '_')}.py").exists():
            orphans.append(name)
    assert not orphans, (
        f"specs with no generated test — they assert nothing: {orphans}"
    )
