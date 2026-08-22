"""Single source of truth for the activity lifecycle.

The parent-facing model is 4 legible stages — Considering → To register →
Registered → All set — with "register"/"pay" surfaced as the card's NEXT ACTION
(driven by typed to-dos), not as extra statuses. Backend `status` stays a small
enum; the granular "what's needed" rides `todo_items.kind` (payment|form|action).

Before this module, three call sites each hardcoded their own status grouping
(`planning._UNDECIDED_STATUSES`, `email_sync._REGISTERED`, `export._confirmedish`)
and had already drifted. Every grouping now imports from here.

Stage map (see the plan's "Activity Lifecycle" section):
  considering   exploring | interested | reference     → CTA "We'll do it"
  to_register   planned  (decided, not yet registered) → CTA "Register"
  registered    signed_up | confirmed, ≥1 open to-do   → CTA = top open to-do
  all_set       done, or signed_up/confirmed w/ 0 open → collapsed
  blocked       pending_eligibility | waitlisted       → CTA resolve reason
  declined      declined (hidden)                      → CTA "Reconsider"

Email/to-do tracking turns ON when a status enters WATCHED (signed_up/confirmed)
— the same trigger R3's email-sync always used.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app import observability as obs
from app.cos.verticals import get_profile, normalize_activity_type

# ── The status groups ────────────────────────────────────────────────

CONSIDERING = frozenset({"exploring", "interested", "reference"})
PLANNED = frozenset({"planned"})
WATCHED = frozenset({"signed_up", "confirmed"})  # email tracking is on
DONE = frozenset({"done"})
BLOCKED = frozenset({"pending_eligibility", "waitlisted"})
DECLINED = frozenset({"declined"})

# R2 triage compares what's not yet settled. `planned` is decided ("we'll do
# it") so it does NOT belong here.
UNDECIDED = CONSIDERING | BLOCKED

# Treated as committed spend / "locked in" for the workbook export.
COMMITTED = WATCHED | DONE

# Every status the system knows (free-TEXT column; unknown values degrade to
# considering rather than vanishing).
ALL_STATUSES = CONSIDERING | PLANNED | WATCHED | DONE | BLOCKED | DECLINED

# Board sections in display order, with the one-line "what this means" blurb
# both clients render under the header (the self-documenting ask).
STAGES: List[Dict[str, str]] = [
    {"key": "considering", "title": "Considering",
     "blurb": "Saved ideas — decide yes or no when you're ready."},
    {"key": "to_register", "title": "To register",
     "blurb": "You said yes — next step is signing up."},
    {"key": "registered", "title": "Registered · needs action",
     "blurb": "Signed up. These still have a to-do (payment, forms)."},
    {"key": "all_set", "title": "All set",
     "blurb": "Registered and nothing left to do."},
    {"key": "blocked", "title": "Waiting / blocked",
     "blurb": "Something needs confirming before these can move."},
    {"key": "declined", "title": "Not doing",
     "blurb": "Passed on these — restore anytime."},
]


def stage_for(status: Optional[str], open_todo_count: int = 0) -> str:
    """Map a backend status (+ open-todo count) to the board stage key."""
    s = (status or "").strip().lower()
    if s in PLANNED:
        return "to_register"
    if s in WATCHED:
        return "registered" if open_todo_count > 0 else "all_set"
    if s in DONE:
        return "all_set"
    if s in BLOCKED:
        return "blocked"
    if s in DECLINED:
        return "declined"
    return "considering"  # exploring/interested/reference + unknown values


def entered_watched(old_status: Optional[str], new_status: Optional[str]) -> bool:
    """True when a status change crosses INTO the watched group — the moment
    email tracking + baseline to-dos should switch on."""
    old = (old_status or "").strip().lower()
    new = (new_status or "").strip().lower()
    return new in WATCHED and old not in WATCHED


def entered_declined(old_status: Optional[str], new_status: Optional[str]) -> bool:
    """True when a status change crosses INTO declined (a Pass) — the moment the
    activity's open to-dos should be dismissed."""
    old = (old_status or "").strip().lower()
    new = (new_status or "").strip().lower()
    return new in DECLINED and old not in DECLINED


def next_step(activity: Dict[str, Any], open_todos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The ONE next action for an activity's card. Labels state their consequence
    (the self-documenting rule) so a first-timer can predict what a tap does.

    Returns {stage, action, label, hint} (+ todo_id / url where relevant).
    action ∈ plan | register | mark_registered | complete_todo | resolve | restore | none
    """
    stage = stage_for(activity.get("status"), len(open_todos))
    name = activity.get("name") or "this activity"

    if stage == "considering":
        return {
            "stage": stage, "action": "plan", "label": "We'll do it",
            "hint": "Moves it to your To-register list.",
        }
    if stage == "to_register":
        url = activity.get("signup_url")
        if url:
            return {
                "stage": stage, "action": "register", "label": "Register", "url": url,
                "hint": "Opens the signup page — then mark it registered and "
                        f"I'll watch {name}'s emails for confirmations and payment reminders.",
            }
        return {
            "stage": stage, "action": "mark_registered", "label": "Mark registered",
            "hint": f"Once registered I'll watch {name}'s emails for "
                    "confirmations and payment reminders.",
        }
    if stage == "registered":
        top = open_todos[0]
        return {
            "stage": stage, "action": "complete_todo",
            "label": top.get("title") or "Finish the next step",
            "todo_id": top.get("id"),
            "hint": "Tap when it's done — the activity moves to All set once "
                    "nothing is left.",
        }
    if stage == "blocked":
        reason = activity.get("pending_reason")
        return {
            "stage": stage, "action": "resolve",
            "label": reason or "Confirm what's blocking this",
            "hint": "Resolve this, then decide or register as usual.",
        }
    if stage == "declined":
        return {
            "stage": stage, "action": "restore", "label": "Reconsider",
            "hint": "Puts it back under Considering.",
        }
    return {"stage": stage, "action": "none", "label": "", "hint": ""}


# ── format_when: the ONE date renderer ───────────────────────────────
# Both clients render this string VERBATIM (the plan's rule) so date display
# logic never forks per surface. Two shapes in Phase 2: week_block and
# recurring_weekly; later phases extend this function, not the clients.

_RRULE_DAY_LABELS = {
    "MO": "Mondays", "TU": "Tuesdays", "WE": "Wednesdays", "TH": "Thursdays",
    "FR": "Fridays", "SA": "Saturdays", "SU": "Sundays",
}

_MONTH_ABBR = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _short_date(iso: Optional[str]) -> Optional[str]:
    if not iso:
        return None
    try:
        from datetime import date
        d = date.fromisoformat(str(iso)[:10])
        return f"{_MONTH_ABBR[d.month]} {d.day}"
    except Exception:
        return None


def _friendly_time(hhmm: Optional[str]) -> Optional[str]:
    if not hhmm:
        return None
    try:
        from datetime import datetime
        t = datetime.strptime(hhmm, "%H:%M")
        out = t.strftime("%I:%M %p").lstrip("0")
        return out
    except Exception:
        return None


def _window_line(window: Dict[str, Any]) -> str:
    """'Registration opens Aug 12 · watching' (+ estimated hedge)."""
    short = _short_date(window.get("opens_at"))
    when = f"opens {short}" if short else "window watched"
    hedge = " (date unconfirmed)" if window.get("confidence") == "estimated" else ""
    return f"Registration {when}{hedge} · watching"


def format_when(activity: Dict[str, Any]) -> Optional[str]:
    """One human 'when' string for an activity card, decided by the DATA shape
    (an rrule row renders recurring even while its vertical profile is still
    degrading to camp). Returns None when the activity has no dates yet."""
    rrule = (activity.get("rrule") or "").strip().upper()
    if rrule:
        parts = {
            kv.split("=", 1)[0]: kv.split("=", 1)[1]
            for kv in rrule.split(";") if "=" in kv
        }
        day = _RRULE_DAY_LABELS.get((parts.get("BYDAY") or "").split(",")[0])
        bits = [day or "Weekly"]
        t = _friendly_time(activity.get("recur_time"))
        if t:
            bits.append(t)
        until = _short_date(activity.get("end_date"))
        if until:
            bits.append(f"through {until}")
        return " ".join(bits)
    start = activity.get("start_date")
    end = activity.get("end_date")
    # single_date (school events): one day is that DAY, not a week block.
    if start and end and str(start)[:10] == str(end)[:10]:
        return _short_date(start)
    # date_range (trips): the profile decides — the same start/end data shape
    # means "week block" for a camp but "Jun 14 – Jun 18" for a trip.
    if (start and end
            and get_profile(activity.get("activity_type")).date_model == "date_range"):
        return f"{_short_date(start)} – {_short_date(end)}"
    anchor = activity.get("week_start") or start
    short = _short_date(anchor)
    return f"Week of {short}" if short else None


def _sort_todos(todos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Open to-dos, most urgent first: dated before undated, then payment/form
    before generic tasks."""
    kind_rank = {"payment": 0, "form": 1, "action": 2, "task": 3}
    return sorted(
        todos,
        key=lambda t: (
            t.get("due_date") is None,
            str(t.get("due_date") or ""),
            kind_rank.get((t.get("kind") or "task"), 3),
        ),
    )


def overlaps_by_activity(conflicts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Project the flat `activity_overlap` conflicts onto each activity id.

    `detect_time_conflicts` emits one row per overlapping PAIR (a/b). The card
    and detail screens need "what does THIS activity collide with", so each pair
    is indexed under both ids with the other side's name and a rendered range —
    the same server-renders-the-string rule as `format_when`, so the clients
    never format a date.
    """
    out: Dict[str, List[Dict[str, Any]]] = {}
    for c in conflicts or []:
        if c.get("type") != "activity_overlap":
            continue
        rng = _overlap_range_label(c.get("overlap_start"), c.get("overlap_end"))
        for own, other_id, other_name in (
            (c.get("activity_a_id"), c.get("activity_b_id"), c.get("activity_b_name")),
            (c.get("activity_b_id"), c.get("activity_a_id"), c.get("activity_a_name")),
        ):
            if not own:
                continue
            out.setdefault(own, []).append(
                {"activity_id": other_id, "name": other_name, "range": rng}
            )
    return out


def _overlap_range_label(start: Optional[str], end: Optional[str]) -> str:
    """"Aug 15–17" / "Aug 28 – Sep 2" from two ISO dates."""
    from datetime import date as _date

    def _p(v: Optional[str]) -> Optional[_date]:
        try:
            return _date.fromisoformat(v) if v else None
        except (TypeError, ValueError):
            return None

    s, e = _p(start), _p(end)
    if not s:
        return ""
    if not e or s == e:
        return s.strftime("%b %-d")
    if s.month == e.month:
        return f"{s.strftime('%b %-d')}–{e.strftime('%-d')}"
    return f"{s.strftime('%b %-d')} – {e.strftime('%b %-d')}"


def build_board(
    activities: List[Dict[str, Any]],
    todos: List[Dict[str, Any]],
    *,
    gmail_connected: bool = False,
    registration_windows: Optional[List[Dict[str, Any]]] = None,
    conflicts: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Group activities into board stages, joining each with its open to-dos and
    computed next_step. This one payload drives BOTH clients (iOS + web) so the
    grouping/CTA logic never forks per surface."""
    open_by_activity: Dict[str, List[Dict[str, Any]]] = {}
    all_by_activity: Dict[str, List[Dict[str, Any]]] = {}
    for t in todos:
        aid = t.get("activity_id")
        if aid:
            # `done` is a derived convenience for the clients' "Still to do"
            # checklist, which renders completed items struck through. The
            # authoritative value stays `status`; this is a projection of it so
            # neither client has to know the status vocabulary.
            entry_t = dict(t)
            entry_t["done"] = (entry_t.get("status") or "open") != "open"
            all_by_activity.setdefault(aid, []).append(entry_t)
            if not entry_t["done"]:
                open_by_activity.setdefault(aid, []).append(entry_t)

    # Watching registration windows, joined by activity (Phase 4): the card
    # shows "Registration opens Aug 12 · watching" with confidence labeled —
    # automated behavior is never invisible.
    window_by_activity: Dict[str, Dict[str, Any]] = {}
    for w in registration_windows or []:
        if (w.get("status") == "watching") and w.get("activity_id"):
            window_by_activity.setdefault(w["activity_id"], w)

    overlap_index = overlaps_by_activity(conflicts or [])

    sections: Dict[str, List[Dict[str, Any]]] = {s["key"]: [] for s in STAGES}
    for a in activities:
        open_todos = _sort_todos(open_by_activity.get(a["id"], []))
        all_todos = all_by_activity.get(a["id"], [])
        step = next_step(a, open_todos)
        entry = dict(a)
        entry["open_todos"] = open_todos
        entry["all_todos"] = all_todos
        # Sprint-2 "Still to do" checklist reads `todos` (open AND completed);
        # `open_todos` stays open-only because next_step and the existing
        # follow-ups list depend on that meaning.
        entry["todos"] = all_todos
        entry["overlaps"] = overlap_index.get(a["id"], [])
        entry["next_step"] = step
        # Canonical vertical for the card chip; NULL/unknown degrades to camp
        # (pre-v16 rows, surprising LLM arguments) — same posture as stage_for.
        entry["activity_type"] = normalize_activity_type(a.get("activity_type"))
        # One server-rendered date string; clients show it verbatim.
        entry["when"] = format_when(a)
        window = window_by_activity.get(a["id"])
        entry["registration_window"] = (
            {
                "id": window.get("id"),
                "opens_at": window.get("opens_at"),
                # Server-rendered line, clients show verbatim (format_when rule).
                "line": _window_line(window),
                "confidence": window.get("confidence"),
                "source": window.get("source"),
            }
            if window else None
        )
        # A registered camp with no contact email can't be watched — surface it
        # so the client can ask for the email instead of silently not tracking.
        status = (a.get("status") or "").strip().lower()
        contact_email = ((a.get("contact") or {}).get("email") or "").strip()
        entry["watchable"] = bool(contact_email)
        entry["watching"] = bool(gmail_connected and contact_email and status in WATCHED)
        # A saved candidate's ages/schedule/price-text/location/category ride
        # in details_json (no dedicated columns) — lift them to top-level
        # keys so clients don't need to know about the details envelope.
        # Missing on onboarding-seeded "Considering" suggestions, which have
        # no candidate to copy from — that's the honest, expected case.
        details = a.get("details") or {}
        for key in ("age_min", "age_max", "schedule_text", "price_text", "location_text", "city", "category"):
            if details.get(key) is not None:
                entry[key] = details[key]
        sections[step["stage"]].append(entry)

    return {
        "stages": [
            {**s, "activities": sections[s["key"]]}
            for s in STAGES
        ],
        "gmail_connected": gmail_connected,
    }


def _status_group(status: Optional[str]) -> str:
    """The lifecycle group a status belongs to — the funnel unit for telemetry
    (deliberately NOT stage_for, whose registered/all_set split depends on
    open-todo count and would make the product funnel noisy)."""
    s = (status or "").strip().lower()
    if s in PLANNED:
        return "to_register"
    if s in WATCHED:
        return "registered"
    if s in DONE:
        return "done"
    if s in BLOCKED:
        return "blocked"
    if s in DECLINED:
        return "declined"
    return "considering"


def _capture(event: str, user_id: str, props: Dict[str, Any]) -> None:
    """Fire-and-forget PostHog capture (same posture as server._track)."""
    try:
        from app.analytics import capture
        capture(event, user_id, props)
    except Exception:  # noqa: BLE001 — analytics must never break a mutation
        pass


def _observe_transition(user_id: str, activity: Dict[str, Any], new_status: str) -> None:
    """One place emits both telemetry channels for a status change:
    Grafana counter (system health) + PostHog event (the per-vertical
    Considering→All-set funnel, the product's core loop)."""
    to_stage = _status_group(new_status)
    atype = normalize_activity_type(activity.get("activity_type"))
    obs.count("cos.lifecycle.transition", to_stage=to_stage, activity_type=atype)
    _capture("activity_stage_advanced", user_id,
             {"to_stage": to_stage, "activity_type": atype})


# ── The one status write path ────────────────────────────────────────
# Before these two functions, the "fire on_enter_watched/on_enter_declined
# when a status crosses" obligation was re-implemented at ~7 call sites
# (tools, router, ingest) and only stayed correct by review. Every status
# write now routes through transition() / on_created() so a new side effect
# (registry to-do seeds, watchlist auto-create) lands in exactly one place.


def transition(
    storage: Any,
    user_id: str,
    activity_id: str,
    new_status: str,
    *,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Update an activity's status (plus any other patch fields in the same
    write) and fire the crossing side effects. Returns the updated activity,
    or None when the id doesn't exist. The status write itself is NOT
    best-effort — storage errors propagate; only the side-effect hooks are
    swallow-safe (they never raise by design)."""
    existing = storage.get_tracked_activity(activity_id)
    if not existing:
        return None
    patch = dict(extra_fields or {})
    patch["status"] = new_status
    storage.update_tracked_activity(activity_id, **patch)
    updated = storage.get_tracked_activity(activity_id)
    if updated:
        _observe_transition(user_id, updated, new_status)
        old_status = existing.get("status")
        if entered_watched(old_status, new_status):
            on_enter_watched(storage, user_id, updated)
        elif entered_declined(old_status, new_status):
            on_enter_declined(storage, user_id, updated)
        _maybe_watch_registration(storage, user_id, updated)
    return updated


def on_created(storage: Any, user_id: str, activity_id: str, status: Optional[str]) -> None:
    """Creating an activity directly in a watched status (e.g. "save the camp
    I already registered for") is also a registration — fire the same side
    effects as a transition into WATCHED. Never raises."""
    try:
        activity = storage.get_tracked_activity(activity_id)
        if activity:
            _maybe_watch_registration(storage, user_id, activity)
    except Exception:  # noqa: BLE001 — best-effort side effects
        pass
    if (status or "").strip().lower() not in WATCHED:
        return
    try:
        activity = storage.get_tracked_activity(activity_id)
        if activity:
            on_enter_watched(storage, user_id, activity)
    except Exception:  # noqa: BLE001 — best-effort side effects
        import logging
        logging.getLogger(__name__).exception(
            "[lifecycle] on_created side effects failed"
        )
        obs.count("cos.lifecycle.hook_error", hook="on_created")


def _maybe_watch_registration(storage: Any, user_id: str, activity: Dict[str, Any]) -> None:
    """Auto-create a registration window for watch-capable activities carrying
    a known open date (Phase 4). Delegates to the watchlist's one write path;
    best-effort by design."""
    try:
        from app.watchlist.service import maybe_watch_from_activity
        maybe_watch_from_activity(storage, user_id, activity)
    except Exception:  # noqa: BLE001
        pass


# ── Transition side effects ──────────────────────────────────────────

def gmail_connected(storage: Any, user_id: str) -> bool:
    try:
        acct = storage.get_integration_account(user_id, "google", "email")
        return bool(acct and acct.get("status") == "connected")
    except Exception:
        return False


def on_enter_watched(storage: Any, user_id: str, activity: Dict[str, Any]) -> Dict[str, Any]:
    """Run once when an activity crosses into WATCHED (registered):

    - enqueue an email-sync run NOW (not at the daily tick) when Gmail is
      connected AND the vertical has the `email_sync` capability, so watching
      starts the moment the parent registers;
    - seed baseline to-dos aimed at the right actor: a typed `payment` to-do
      when the price is known, and — only when Gmail is NOT connected — a
      "forward the confirmation" to-do (when it IS connected the system does
      the watching; the user shouldn't get a to-do for the machine's job).

    The seeding CONDITIONALS live here (code); the vertical registry supplies
    only the to-do WORDING + the capability booleans — the plan's binding
    split. Idempotent: re-entering WATCHED doesn't double-seed. Never raises —
    a failed nicety must not break the status change itself.
    """
    result = {"seeded": [], "sync_enqueued": False}
    aid = activity.get("id")
    name = activity.get("name") or "this activity"
    profile = get_profile(activity.get("activity_type"))
    wording = profile.todo_wording
    try:
        existing = [t for t in storage.list_todos(user_id) if t.get("activity_id") == aid]
        kinds = {(t.get("kind") or "task") for t in existing}
        connected = gmail_connected(storage, user_id)

        price = activity.get("price_amount")
        if price is not None and "payment" not in kinds:
            storage.add_todo(
                user_id,
                title=wording.payment_title.format(name=name, price=f"{price:g}"),
                kid_name=activity.get("kid_name"),
                activity_id=aid,
                kind="payment",
                detail=wording.payment_detail,
                source="cos_agent",
            )
            result["seeded"].append("payment")

        has_confirm_todo = any("confirmation" in (t.get("title") or "").lower() for t in existing)
        if not connected and not has_confirm_todo:
            storage.add_todo(
                user_id,
                title=wording.confirm_title.format(name=name),
                kid_name=activity.get("kid_name"),
                activity_id=aid,
                kind="action",
                detail=wording.confirm_detail,
                source="cos_agent",
            )
            result["seeded"].append("action")

        # Vertical-declared unconditional prep to-dos (e.g. a trip's packing
        # list). Idempotent by rendered title — kinds legitimately collide.
        existing_titles = {(t.get("title") or "") for t in existing}
        for extra in wording.extras:
            title = extra.title.format(name=name)
            if title in existing_titles:
                continue
            storage.add_todo(
                user_id,
                title=title,
                kid_name=activity.get("kid_name"),
                activity_id=aid,
                kind=extra.kind,
                detail=extra.detail,
                source="cos_agent",
            )
            result["seeded"].append(extra.kind)

        if connected and profile.email_sync:
            storage.create_email_sync_run(user_id=user_id, trigger="activity_registered")
            result["sync_enqueued"] = True
            try:
                from app.email_sync.worker import email_sync_worker
                if email_sync_worker is not None:
                    email_sync_worker.notify()
            except Exception:  # worker not running (tests) — the daily tick covers it
                pass
    except Exception:  # noqa: BLE001 — best-effort side effects
        import logging
        logging.getLogger(__name__).exception("[lifecycle] on_enter_watched side effects failed")
        obs.count("cos.lifecycle.hook_error", hook="on_enter_watched")
    return result


def on_enter_declined(storage: Any, user_id: str, activity: Dict[str, Any]) -> Dict[str, Any]:
    """Run once when an activity is passed (declined): dismiss its open to-dos so
    an abandoned plan doesn't leave zombie "Pay $X" items in Follow-ups.
    Deliberately NOT undone by Reconsider — those to-dos belonged to the
    abandoned plan. Never raises."""
    dismissed = []
    aid = activity.get("id")
    try:
        for t in storage.list_todos(user_id, status="open"):
            if t.get("activity_id") == aid:
                storage.update_todo(t["id"], status="dismissed")
                dismissed.append(t["id"])
    except Exception:  # noqa: BLE001 — best-effort side effects
        import logging
        logging.getLogger(__name__).exception("[lifecycle] on_enter_declined side effects failed")
        obs.count("cos.lifecycle.hook_error", hook="on_enter_declined")
    return {"dismissed_todos": dismissed}
