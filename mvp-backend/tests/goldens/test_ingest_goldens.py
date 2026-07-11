"""Ingest extraction goldens (Phase 5 corpus gate) — live-LLM, opt-in like the
COS goldens: RUN_INGEST_GOLDENS=1.

The 12 fixtures under tests/fixtures/school/ are the plan's binding corpus
gate for the V4 door. Assertions are DELIBERATELY coarse (min item count +
which event kinds must appear + must-not-hallucinate on the noise fixture) —
extraction wording varies run to run; the taxonomy signal is what's pinned.
Every prod miss becomes a new fixture in its fix PR (corpus = flywheel).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# app.ingest.extract doesn't load_dotenv (the server does) — do it here so
# the live-LLM opt-in run finds OPENAI_API_KEY like the cos goldens do.
from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_ROOT / ".env")

RUN = os.environ.get("RUN_INGEST_GOLDENS") == "1"
pytestmark = pytest.mark.skipif(
    not RUN, reason="live-LLM ingest goldens; opt in with RUN_INGEST_GOLDENS=1"
)

FIXTURES = BACKEND_ROOT / "tests" / "fixtures" / "school"

# fixture stem -> (min_items, {event kinds that MUST appear}, {activity types that must appear})
EXPECT = {
    "01-picture-day-flyer": (1, {"picture_day"}, {"school_event"}),
    "02-permission-slip": (1, {"permission_slip"}, {"school_event"}),
    "03-fee-notice": (1, {"fee"}, {"school_event"}),
    "04-pta-newsletter-multi": (3, {"picture_day", "fundraiser", "permission_slip"}, {"school_event"}),
    "05-spirit-day": (1, {"spirit_day"}, {"school_event"}),
    "06-fundraiser": (1, {"fundraiser"}, {"school_event"}),
    "07-welcome-letter-camp": (1, set(), {"camp"}),
    "08-ambiguous-date": (1, set(), set()),      # honest scoping: kind may vary
    "09-photo-style-flyer": (1, set(), {"school_event"}),
    "11-multi-kid-sports": (1, set(), {"extracurricular"}),
    "12-conference-signup": (1, set(), {"school_event"}),
}


@pytest.mark.parametrize("stem", sorted(EXPECT))
def test_fixture_extraction(stem):
    from app.ingest.extract import extract_items_from_text

    text = (FIXTURES / f"{stem}.txt").read_text()
    items = extract_items_from_text(text, source_hint="fixture", cost_user="ingest-golden")
    min_items, kinds, types = EXPECT[stem]
    assert len(items) >= min_items, f"{stem}: got {len(items)} item(s)"
    got_kinds = {(i.event_kind or "").strip().lower() for i in items}
    assert kinds <= got_kinds, f"{stem}: kinds {kinds} not in {got_kinds}"
    got_types = {(i.activity_type or "").strip().lower() for i in items}
    assert types <= got_types, f"{stem}: types {types} not in {got_types}"
    # Provenance: at least one item must carry a verbatim-ish source snippet.
    assert any((i.source_snippet or "").strip() for i in items), f"{stem}: no snippet"


def test_noise_fixture_does_not_hallucinate():
    """The nut-free/lost-tooth note contains NO activity — extraction must not
    invent one with a date or amount (empty items, or items with no dates and
    no amount_due, are both acceptable)."""
    from app.ingest.extract import extract_items_from_text

    text = (FIXTURES / "10-lost-tooth-noise.txt").read_text()
    items = extract_items_from_text(text, source_hint="fixture", cost_user="ingest-golden")
    for item in items:
        assert not item.dates, f"hallucinated dates: {item.dates}"
        assert item.amount_due is None, f"hallucinated amount: {item.amount_due}"
