"""School-event taxonomy: event_kind → typed task-chain template (vertical
expansion Phase 5 — the plan's FIRST config→strategy promotion: V4 task
chains are structurally different per kind, so each kind gets a builder
function; the registry stays a plain dict of those builders).

The chains are deliberately minimal and DEDUPED against what the extractor
already produced (a permission-slip email usually yields a `forms_required`
entry too — the chain must not double it). materialize() owns the merge; this
module only says what a kind implies.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

# (title, kind, due_date) — the shape materialize() feeds into add_todo.
TodoSpec = Tuple[str, str, Optional[str]]

EVENT_KINDS = frozenset({
    "permission_slip", "fee", "spirit_day", "picture_day", "fundraiser", "general",
})


def _first_date(extracted: Any) -> Optional[str]:
    dates = getattr(extracted, "dates", None) or []
    return dates[0] if dates else None


def _name(extracted: Any) -> str:
    return (getattr(extracted, "activity_name", None)
            or getattr(extracted, "provider", None) or "school event")


def _permission_slip(e: Any) -> List[TodoSpec]:
    return [(f"Sign and return the permission slip for {_name(e)}", "form", _first_date(e))]


def _fee(e: Any) -> List[TodoSpec]:
    amount = getattr(e, "amount_due", None)
    title = (f"Pay the ${amount:g} fee for {_name(e)}" if amount is not None
             else f"Pay the fee for {_name(e)}")
    return [(title, "payment", getattr(e, "payment_due_date", None) or _first_date(e))]


def _picture_day(e: Any) -> List[TodoSpec]:
    date = _first_date(e)
    when = f" ({date})" if date else ""
    return [(f"Picture day{when} — order form and outfit ready", "action", date)]


def _spirit_day(e: Any) -> List[TodoSpec]:
    date = _first_date(e)
    when = f" ({date})" if date else ""
    return [(f"Spirit day{when} — outfit sorted the night before", "action", date)]


def _fundraiser(e: Any) -> List[TodoSpec]:
    return [(f"Decide on the {_name(e)} fundraiser (in or out)", "action", _first_date(e))]


def _general(e: Any) -> List[TodoSpec]:
    return []


_CHAIN_BUILDERS: Dict[str, Callable[[Any], List[TodoSpec]]] = {
    "permission_slip": _permission_slip,
    "fee": _fee,
    "picture_day": _picture_day,
    "spirit_day": _spirit_day,
    "fundraiser": _fundraiser,
    "general": _general,
}


def chain_for(extracted: Any) -> List[TodoSpec]:
    """The task chain an event_kind implies (empty for unknown/None kinds —
    unknown kinds degrade to nothing extra, never crash)."""
    kind = (getattr(extracted, "event_kind", None) or "").strip().lower()
    builder = _CHAIN_BUILDERS.get(kind)
    return builder(extracted) if builder else []
