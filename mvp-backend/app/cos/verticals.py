"""Vertical taxonomy + profile registry for tracked activities.

The five-vertical expansion ("one agent, five entry doors" — see the plan
`one-agent-five-doors`) types every tracked activity with an `activity_type`.
This module is the single source of truth for that taxonomy AND the
per-vertical configuration (`VerticalProfile` / `REGISTRY`).

The registry is DATA-ONLY by design (a binding rule from the plan's critic
review): labels, wording templates, capability booleans, door copy. Behavioral
conditionals ("seed a payment to-do when price is known") stay in code —
`lifecycle.on_enter_watched` reads wording from here but owns the logic.
Structural divergence promotes to a strategy function only on the SECOND real
occurrence, never speculatively.

Profiles are registered in the phase that ships their vertical: camp (V1) and
outing (V3, built) today; extracurricular lands with Phase 3, school_event
with Phase 5, trip with Phase 6. A canonical type with no registered profile
degrades to the camp profile — mirroring how `lifecycle.stage_for` degrades
unknown statuses — so pre-registration rows never crash anything.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

CAMP = "camp"
EXTRACURRICULAR = "extracurricular"
OUTING = "outing"
SCHOOL_EVENT = "school_event"
TRIP = "trip"

ACTIVITY_TYPES = frozenset({CAMP, EXTRACURRICULAR, OUTING, SCHOOL_EVENT, TRIP})

DEFAULT_ACTIVITY_TYPE = CAMP

# Discovery candidates carry a free-text `category` (camp|class|program|event|
# weekend, uncontrolled). Map it to a canonical activity_type when the parent
# tracks a candidate, so the LLM-facing default never overrides what the
# candidate already tells us.
_CATEGORY_TO_TYPE = {
    "camp": CAMP,
    "class": EXTRACURRICULAR,
    "program": EXTRACURRICULAR,
    "sport": EXTRACURRICULAR,
    "weekend": OUTING,
    "event": OUTING,
}

# calendar_entries.kind for entries derived from an activity of a given type.
KIND_FOR_TYPE = {
    CAMP: "camp",
    EXTRACURRICULAR: "class",
    OUTING: "event",
    SCHOOL_EVENT: "event",
    TRIP: "camp",  # placeholder until Phase 6 adds the date_range model
}


def normalize_activity_type(value: Optional[str]) -> str:
    """Canonical activity_type, degrading unknown/NULL to the default."""
    v = (value or "").strip().lower()
    return v if v in ACTIVITY_TYPES else DEFAULT_ACTIVITY_TYPE


def derive_from_category(category: Optional[str]) -> str:
    """activity_type for a discovery candidate's free-text category."""
    c = (category or "").strip().lower()
    for token, atype in _CATEGORY_TO_TYPE.items():
        if token in c:
            return atype
    return DEFAULT_ACTIVITY_TYPE


# ── VerticalProfile registry ─────────────────────────────────────────


@dataclass(frozen=True)
class TodoWording:
    """Templates for the baseline to-dos seeded when an activity is registered.

    `{name}` = activity name; `{price}` = pre-formatted amount (no `$`).
    The camp templates must render EXACTLY the strings the lifecycle tests
    lock — wording lives here, the seeding conditionals stay in lifecycle.
    """

    payment_title: str
    payment_detail: str
    confirm_title: str
    confirm_detail: str


@dataclass(frozen=True)
class Door:
    """Copy for one entry door in the "Plan something" disclosure (Phase 3 UI)
    and the `GET /cos/verticals` payload."""

    title: str
    subtitle: str
    starter_prompt: str


@dataclass(frozen=True)
class VerticalProfile:
    key: str
    label: str
    chip_label: str
    # week_block | recurring_weekly | single_date | date_range | none.
    # Declarative until Phase 2 wires the date write path; "none" = the
    # vertical's items are ephemeral (outings) and don't own dates.
    date_model: str
    provides_coverage: bool
    todo_wording: TodoWording
    # Query template appended after the activity name in LookupAndSaveActivity.
    research_focus: str
    door: Door
    # Named capabilities (booleans, never stringly-typed sets — critic rule).
    email_sync: bool
    registration_watch: bool
    ingest_taxonomy: bool
    # PostHog flag gating the DOOR's visibility only (the one place flags may
    # touch verticals). None = always visible; also the fail-open set.
    flag: Optional[str] = None
    # nl-harness spec (relative to tests/nl-harness/specs/) covering this
    # vertical — existence is asserted by the registry-invariant tests.
    harness_spec: str = ""


REGISTRY: Dict[str, VerticalProfile] = {
    CAMP: VerticalProfile(
        key=CAMP,
        label="Camps & breaks",
        chip_label="Camp",
        date_model="week_block",
        provides_coverage=True,
        todo_wording=TodoWording(
            payment_title="Pay ${price} for {name}",
            payment_detail="Added when you marked this registered — check it off once paid.",
            confirm_title="Forward or paste {name}'s confirmation email",
            confirm_detail=(
                "Gmail isn't connected, so I can't watch for it automatically — "
                "paste it in and I'll pull out dates, payments, and forms."
            ),
        ),
        research_focus="kids camp registration details schedule price location",
        door=Door(
            title="Camps & school breaks",
            subtitle="Find options, decide, register — I'll watch the rest.",
            starter_prompt="Help me plan camps for the next school break.",
        ),
        email_sync=True,
        registration_watch=True,
        ingest_taxonomy=False,
        harness_spec="tier-1/cos-chat-power-tools.flow.yml",
    ),
    OUTING: VerticalProfile(
        key=OUTING,
        label="Outings",
        chip_label="Outing",
        date_model="none",  # ephemeral suggestions; saved only via AddToCalendar
        provides_coverage=False,
        todo_wording=TodoWording(
            payment_title="Pay ${price} for {name}",
            payment_detail="Added when you saved this — check it off once paid.",
            confirm_title="Forward or paste {name}'s confirmation email",
            confirm_detail=(
                "Gmail isn't connected, so I can't watch for it automatically — "
                "paste it in and I'll pull out dates, payments, and forms."
            ),
        ),
        research_focus="family outing details hours location cost",
        door=Door(
            title="Weekend outings",
            subtitle="Quick ideas for a free day — nothing saved unless you say so.",
            starter_prompt="What can we do with the kids this weekend?",
        ),
        email_sync=False,
        registration_watch=False,
        ingest_taxonomy=False,
        harness_spec="tier-1/cos-quick-outings.flow.yml",
    ),
}


def get_profile(activity_type: Optional[str]) -> VerticalProfile:
    """The profile for an activity_type; canonical-but-unregistered types
    (e.g. `extracurricular` before Phase 3) and NULL/unknown degrade to camp."""
    return REGISTRY.get(normalize_activity_type(activity_type), REGISTRY[DEFAULT_ACTIVITY_TYPE])


def default_doors() -> List[VerticalProfile]:
    """The fail-open door set: registered profiles with no gating flag."""
    return [p for p in REGISTRY.values() if p.flag is None]
