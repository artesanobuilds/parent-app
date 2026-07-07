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


def build_board(
    activities: List[Dict[str, Any]],
    todos: List[Dict[str, Any]],
    *,
    gmail_connected: bool = False,
) -> Dict[str, Any]:
    """Group activities into board stages, joining each with its open to-dos and
    computed next_step. This one payload drives BOTH clients (iOS + web) so the
    grouping/CTA logic never forks per surface."""
    open_by_activity: Dict[str, List[Dict[str, Any]]] = {}
    for t in todos:
        if (t.get("status") or "open") != "open":
            continue
        aid = t.get("activity_id")
        if aid:
            open_by_activity.setdefault(aid, []).append(t)

    sections: Dict[str, List[Dict[str, Any]]] = {s["key"]: [] for s in STAGES}
    for a in activities:
        open_todos = _sort_todos(open_by_activity.get(a["id"], []))
        step = next_step(a, open_todos)
        entry = dict(a)
        entry["open_todos"] = open_todos
        entry["next_step"] = step
        # A registered camp with no contact email can't be watched — surface it
        # so the client can ask for the email instead of silently not tracking.
        status = (a.get("status") or "").strip().lower()
        contact_email = ((a.get("contact") or {}).get("email") or "").strip()
        entry["watchable"] = bool(contact_email)
        entry["watching"] = bool(gmail_connected and contact_email and status in WATCHED)
        sections[step["stage"]].append(entry)

    return {
        "stages": [
            {**s, "activities": sections[s["key"]]}
            for s in STAGES
        ],
        "gmail_connected": gmail_connected,
    }


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
      connected, so watching starts the moment the parent registers;
    - seed baseline to-dos aimed at the right actor: a typed `payment` to-do
      when the price is known, and — only when Gmail is NOT connected — a
      "forward the confirmation" to-do (when it IS connected the system does
      the watching; the user shouldn't get a to-do for the machine's job).

    Idempotent: re-entering WATCHED doesn't double-seed. Never raises — a
    failed nicety must not break the status change itself.
    """
    result = {"seeded": [], "sync_enqueued": False}
    aid = activity.get("id")
    name = activity.get("name") or "this activity"
    try:
        existing = [t for t in storage.list_todos(user_id) if t.get("activity_id") == aid]
        kinds = {(t.get("kind") or "task") for t in existing}
        connected = gmail_connected(storage, user_id)

        price = activity.get("price_amount")
        if price is not None and "payment" not in kinds:
            storage.add_todo(
                user_id,
                title=f"Pay ${price:g} for {name}",
                kid_name=activity.get("kid_name"),
                activity_id=aid,
                kind="payment",
                detail="Added when you marked this registered — check it off once paid.",
                source="cos_agent",
            )
            result["seeded"].append("payment")

        has_confirm_todo = any("confirmation" in (t.get("title") or "").lower() for t in existing)
        if not connected and not has_confirm_todo:
            storage.add_todo(
                user_id,
                title=f"Forward or paste {name}'s confirmation email",
                kid_name=activity.get("kid_name"),
                activity_id=aid,
                kind="action",
                detail="Gmail isn't connected, so I can't watch for it automatically — "
                       "paste it in and I'll pull out dates, payments, and forms.",
                source="cos_agent",
            )
            result["seeded"].append("action")

        if connected:
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
    return result
