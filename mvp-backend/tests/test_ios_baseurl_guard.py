"""
Codebase-invariant guard: ONE source of truth for the iOS backend URL.

Why this test exists
--------------------
A shipped bug: an iOS networking call had a hardcoded
`?? "http://127.0.0.1:8904"` fallback instead of resolving the URL via
`ServerConfiguration.defaultURL`. On a real-device fresh install — where the
`chat.base_url` UserDefault isn't set yet — that fallback POSTed to the
*phone's own* localhost, silently dropping the user's onboarding data. It was
invisible in the simulator (localhost there reaches the dev backend) and only
surfaced once a real user on a real device hit it.

The invariant
-------------
No Swift file under `mvp/MVP/` may contain a hardcoded backend-URL literal
(`127.0.0.1:8904`, `localhost:8904`, or the prod host `mvp-backend-production`)
EXCEPT `ServerConfiguration.swift`, which is the single legitimate home for
those literals (it defines `localURL`, `productionURL`, `defaultURL`). Test
files (`*Test*` / `*Tests*`) are also exempt. Everything else must resolve the
base URL through `ServerConfiguration.defaultURL`.

Pure-Python, no network, no app import — it just reads the Swift sources.
"""
from __future__ import annotations

import pathlib

import pytest

# This test lives at <repo>/mvp-backend/tests/test_ios_baseurl_guard.py, so the
# repo root is two parents up from this file.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SWIFT_DIR = REPO_ROOT / "mvp" / "MVP"

# The forbidden hardcoded backend-URL literals.
FORBIDDEN_LITERALS = ("127.0.0.1:8904", "localhost:8904", "mvp-backend-production")

# The single file allowed to define those literals.
ALLOWED_FILENAME = "ServerConfiguration.swift"


def _is_exempt(path: pathlib.Path) -> bool:
    """A Swift file is exempt if it's the canonical config file or a test file."""
    name = path.name
    return name == ALLOWED_FILENAME or "Test" in name


def test_single_source_of_truth_for_backend_url() -> None:
    if not SWIFT_DIR.is_dir():
        pytest.skip(
            f"iOS Swift sources not present at {SWIFT_DIR} "
            "(backend-only checkout); nothing to guard."
        )

    violations: list[tuple[str, int, str]] = []

    for swift_file in sorted(SWIFT_DIR.rglob("*.swift")):
        if _is_exempt(swift_file):
            continue

        rel = swift_file.relative_to(REPO_ROOT).as_posix()
        text = swift_file.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if any(literal in line for literal in FORBIDDEN_LITERALS):
                violations.append((rel, lineno, line.strip()))

    if violations:
        detail = "\n".join(
            f"  {rel}:{lineno}: {line}" for rel, lineno, line in violations
        )
        raise AssertionError(
            "Hardcoded backend-URL literal(s) found outside "
            f"{ALLOWED_FILENAME}:\n{detail}\n\n"
            "Resolve the backend base URL via `ServerConfiguration.defaultURL` "
            "instead of hardcoding a host. A hardcoded localhost fallback on a "
            "real-device fresh install silently posts to the phone's own "
            "localhost and loses user data."
        )
