"""
Codebase-invariant guard: a design spec must declare its own coverage.

Why this test exists
--------------------
2026-08-08. `docs/design/beta-v1-sprint1.md` was committed with the header
"This file is the source of truth for the build — do not re-read Figma" while
containing **13 of the page's 31 screens**. The Figma page fetch had been
shallow (`GET /v1/files/:key/nodes?ids=<PAGE id>` returns child names with no
nested content), so 18 screens were never read — including `Onboarding - 2`,
which was then "built to measured values" against nothing at all.

The failure wasn't the missing data. It was that **the doc asserted authority it
didn't have**, and its own "do not re-read Figma" line stopped anyone checking.
A spec that silently covers a subset is worse than no spec.

The invariant
-------------
Every design spec under `docs/design/` must:
  1. contain a `## Coverage` section, and
  2. list, in that section, every Figma node id that appears as a `FRAME` in the
     body — so a reader can compare declared coverage against actual content
     without opening Figma.

This cannot verify the spec against Figma itself (no network, no token in CI).
What it CAN enforce is that the file's own claim matches its own contents, which
is exactly the gap that let a 42%-complete file pass as authoritative.

Pure-Python, no network, no app import — it just reads the markdown.
"""
from __future__ import annotations

import pathlib
import re

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DESIGN_DIR = REPO_ROOT / "docs" / "design"

# `FRAME <name> — `<node id>` — <w>x<h>` — the shape the local walker emits.
FRAME_RE = re.compile(r"^FRAME\s+(?P<name>.*?)\s+—\s+`(?P<nid>[0-9]+:[0-9]+)`\s+—", re.M)
# A Figma node id as it appears anywhere in prose/tables, e.g. `754:4317`.
NODE_ID_RE = re.compile(r"`([0-9]+:[0-9]+)`")


def _specs() -> list[pathlib.Path]:
    return sorted(DESIGN_DIR.glob("*.md")) if DESIGN_DIR.is_dir() else []


def test_there_is_at_least_one_design_spec():
    assert _specs(), f"no design specs found under {DESIGN_DIR}"


@pytest.mark.parametrize("spec", _specs(), ids=lambda p: p.name)
def test_the_spec_declares_a_coverage_section(spec: pathlib.Path):
    text = spec.read_text(encoding="utf-8")
    if not FRAME_RE.search(text):
        pytest.skip(f"{spec.name} carries no measured FRAME blocks")
    assert re.search(r"^##\s+Coverage", text, re.M), (
        f"{spec.name} contains measured frames but no '## Coverage' section. A "
        f"spec that doesn't state what it covers WILL be read as complete — "
        f"that is exactly how a 13-of-31 extract passed as the source of truth."
    )


@pytest.mark.parametrize("spec", _specs(), ids=lambda p: p.name)
def test_every_extracted_frame_is_listed_in_coverage(spec: pathlib.Path):
    text = spec.read_text(encoding="utf-8")
    frames = {m.group("nid"): m.group("name").strip() for m in FRAME_RE.finditer(text)}
    if not frames:
        pytest.skip(f"{spec.name} carries no measured FRAME blocks")

    head = text.split("---\n\n", 1)[0]
    declared = set(NODE_ID_RE.findall(head))

    missing = {nid: nm for nid, nm in frames.items() if nid not in declared}
    assert not missing, (
        f"{spec.name}: {len(missing)} extracted frame(s) are NOT listed in the "
        f"coverage header, so the header understates what the file holds: "
        f"{sorted(missing.items())[:5]}"
    )


@pytest.mark.parametrize("spec", _specs(), ids=lambda p: p.name)
def test_coverage_does_not_claim_frames_it_lacks(spec: pathlib.Path):
    """The inverse, and the one that actually caught the original bug: an id
    listed in the coverage TABLE with no measured block behind it."""
    text = spec.read_text(encoding="utf-8")
    frames = {m.group("nid") for m in FRAME_RE.finditer(text)}
    if not frames:
        pytest.skip(f"{spec.name} carries no measured FRAME blocks")

    head = text.split("---\n\n", 1)[0]
    # Only ids inside the coverage TABLE rows are a coverage claim; ids
    # mentioned in prose ("see 754:4311") are references, not claims.
    claimed = set()
    for line in head.splitlines():
        if line.startswith("|") and line.count("|") >= 3:
            claimed.update(NODE_ID_RE.findall(line))

    phantom = claimed - frames
    assert not phantom, (
        f"{spec.name}: the coverage table claims {sorted(phantom)} but no "
        f"measured FRAME block for them exists in the file. Either extract them "
        f"or remove the row — a claimed-but-absent frame is what made the first "
        f"sprint-1 spec dangerous."
    )
