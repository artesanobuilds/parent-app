"""Chief-of-Staff agent tools.

Each tool is built by a ``_make_*_tool(user_id)`` factory that closes over the
authenticated ``user_id`` (the same pattern as ``app/agent.py._make_parent_tool``)
so the LLM can never address another user's data. Every tool calls a storage
method (imported lazily from ``app.server`` to avoid an import cycle) and returns
a SHORT human-readable confirmation string — tools never raise on normal input;
a missing referenced id yields an error-ish string instead.

The agent reads current plan state ONLY through ``GetPlanSnapshot`` /
``SearchActivities`` so the system prompt can stay stable and cacheable.
"""
from __future__ import annotations

import logging
from typing import Optional

from langchain.tools import tool

from app.cos import planning
from app.cost_logging import cost_config, new_workflow_id

logger = logging.getLogger(__name__)


def _storage():
    # Late import: app.server builds storage at module load, importing it at the
    # top would create a cycle (server imports the cos router which imports this).
    from app.server import storage_backend

    return storage_backend


def _tool_error(tool_name: str, exc: Exception, user_id: str) -> str:
    """Log + (gated) Sentry-capture a tool failure, then return a short string the
    agent can relay. Tools never raise — they degrade to an explanation."""
    logger.warning("[cos_tool] %s failed: %s", tool_name, exc)
    try:
        from app.observability import capture_exception

        capture_exception(exc, feature="cos", tool=tool_name, user=user_id)
    except Exception:  # observability must never break a tool
        pass
    return f"{tool_name} hit an error: {exc}"


def _kids_for(user_id: str) -> list[dict]:
    """Return ``[{"name", "age", ...}]`` for the user's children from the profile."""
    from app.profiling import profiling_service

    fam = profiling_service.get_family_profile(user_id) or {}
    kids: list[dict] = []
    for name, prof in (fam.get("children") or {}).items():
        prof = prof or {}
        kids.append({"name": prof.get("name") or name, "age": prof.get("age")})
    return kids


def _results_to_text(results: Any) -> str:
    """Flatten a TavilySearch result (dict with 'results', a list, or a string)
    into plain text the extractor can read."""
    items = []
    if isinstance(results, dict):
        items = results.get("results") or []
    elif isinstance(results, list):
        items = results
    else:
        return str(results)
    parts: list[str] = []
    for r in items:
        if isinstance(r, dict):
            parts.append(
                "\n".join(
                    str(r.get(k))
                    for k in ("title", "url", "content")
                    if r.get(k)
                )
            )
        else:
            parts.append(str(r))
    return "\n\n".join(parts) or str(results)


_HELP_TEXT = """\
I'm your Chief of Staff — I run the logistics of your kids' camps, classes, and activities so you don't have to hold it all in your head. Here's what I can do:

DISCOVER & SAVE
• Start a web search for new camps/activities near you ("find art camps for Ceiba") — say the word and I'll kick one off.
• Look up a camp you already signed up for and save it to your plan with all its details ("I registered for Camp Galileo and Steve & Kate's").
• Search the options we've already discovered.

DECIDE
• Lay your shortlist side-by-side (cost, age-fit, schedule clashes, who competes with whom) and help you pick — then record the decision and the why.

TRACK & ORGANIZE
• Keep every activity's status explicit (exploring → signed up → confirmed → declined), update or remove any of them.
• Build your week-by-week calendar and a running to-do / follow-ups list (signups, payments, forms, emails).
• Track caregivers and who's covering drop-off/pickup — and flag coverage gaps, time conflicts, and age-eligibility issues before you commit.
• Keep a running cost picture (confirmed total + what's still TBD).

KNOW YOUR FAMILY
• Pull up what we know about your kids (ages, interests, fit) to tailor recommendations.

DRAFT
• Write an email to an organizer for you to review and send (I never send it myself).

Just tell me what you need in plain language — e.g. "what's left to do this week?", "are we covered for the week of July 6?", "help me decide between these two camps", or "save the three camps I signed up for"."""


# --------------------------------------------------------------------------- #
# Tracked activities
# --------------------------------------------------------------------------- #


def _make_track_activity_tool(user_id: str):
    @tool
    def TrackActivity(
        name: str,
        kid_name: Optional[str] = None,
        status: str = "exploring",
        week_start: Optional[str] = None,
        price_amount: Optional[float] = None,
        price_status: str = "tbd",
        signup_url: Optional[str] = None,
        provider: Optional[str] = None,
        candidate_id: Optional[str] = None,
        notes: Optional[str] = None,
        decision_rationale: Optional[str] = None,
    ) -> str:
        """Track a camp/class/activity the parent is considering or has committed to.

        Default status is "exploring" (on the shortlist, considering — not yet
        decided). Keep the decision explicit via ``status`` ("exploring",
        "pending_eligibility", "signed_up", "confirmed", "declined"). Move items
        off "exploring" once the parent settles. ``price_status`` is "tbd" or
        "confirmed". Returns a short confirmation including the new id.
        """
        try:
            activity_id = _storage().track_activity(
                user_id,
                name=name,
                kid_name=kid_name,
                candidate_id=candidate_id,
                provider=provider,
                week_start=week_start,
                status=status,
                price_amount=price_amount,
                price_status=price_status,
                signup_url=signup_url,
                notes=notes,
                decision_rationale=decision_rationale,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[cos_tool] TrackActivity failed: %s", exc)
            return f"Could not track '{name}': {exc}"
        who = f" for {kid_name}" if kid_name else ""
        return f"Tracked '{name}'{who} as {status} (id={activity_id})."

    return TrackActivity


# --------------------------------------------------------------------------- #
# Calendar
# --------------------------------------------------------------------------- #


def _make_add_to_calendar_tool(user_id: str):
    @tool
    def AddToCalendar(
        title: str,
        kid_name: Optional[str] = None,
        week_start: Optional[str] = None,
        start_ts: Optional[str] = None,
        end_ts: Optional[str] = None,
        all_day: bool = False,
        location_text: Optional[str] = None,
        kind: str = "camp",
        status: str = "confirmed",
        activity_id: Optional[str] = None,
    ) -> str:
        """Add an entry to the family calendar (a camp week, class, appointment).

        ``kind`` of camp/class/program counts as activity coverage for a kid's
        week. Timestamps are ISO-8601. Returns a short confirmation.
        """
        try:
            entry_id = _storage().add_calendar_entry(
                user_id,
                title=title,
                kid_name=kid_name,
                activity_id=activity_id,
                week_start=week_start,
                start_ts=start_ts,
                end_ts=end_ts,
                all_day=all_day,
                location_text=location_text,
                kind=kind,
                status=status,
                source="cos_agent",
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[cos_tool] AddToCalendar failed: %s", exc)
            return f"Could not add '{title}' to the calendar: {exc}"
        when = f" week of {week_start}" if week_start else ""
        return f"Added '{title}'{when} to the calendar (id={entry_id})."

    return AddToCalendar


# --------------------------------------------------------------------------- #
# Recurring appointments
# --------------------------------------------------------------------------- #


def _make_add_recurring_tool(user_id: str):
    @tool
    def AddRecurringAppointment(
        title: str,
        kid_name: Optional[str] = None,
        provider_name: Optional[str] = None,
        weekday: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        transporter: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Record a recurring weekly commitment (e.g. therapy, lessons).

        ``weekday`` is 0=Mon..6=Sun; ``start_time``/``end_time`` are "HH:MM".
        These feed time-conflict detection against the calendar.
        """
        try:
            appt_id = _storage().add_recurring_appointment(
                user_id,
                title=title,
                kid_name=kid_name,
                provider_name=provider_name,
                weekday=weekday,
                start_time=start_time,
                end_time=end_time,
                transporter=transporter,
                notes=notes,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[cos_tool] AddRecurringAppointment failed: %s", exc)
            return f"Could not add recurring '{title}': {exc}"
        return f"Added recurring appointment '{title}' (id={appt_id})."

    return AddRecurringAppointment


# --------------------------------------------------------------------------- #
# Caregivers
# --------------------------------------------------------------------------- #


def _make_add_caregiver_tool(user_id: str):
    @tool
    def AddCaregiver(
        name: str,
        role: str = "other",
        contact: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Add a caregiver (nanny, grandparent, co-parent, sitter) to the roster.

        ``role`` is a short label like "nanny"/"grandparent"/"co_parent".
        Caregivers can then be assigned to logistics tasks.
        """
        try:
            caregiver_id = _storage().add_caregiver(
                user_id, name=name, role=role, contact=contact, notes=notes
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[cos_tool] AddCaregiver failed: %s", exc)
            return f"Could not add caregiver '{name}': {exc}"
        return f"Added caregiver '{name}' ({role}) (id={caregiver_id})."

    return AddCaregiver


# --------------------------------------------------------------------------- #
# Logistics
# --------------------------------------------------------------------------- #


def _make_assign_logistics_tool(user_id: str):
    @tool
    def AssignLogistics(
        task: str,
        week_start: Optional[str] = None,
        kid_name: Optional[str] = None,
        caregiver_id: Optional[str] = None,
        calendar_entry_id: Optional[str] = None,
        status: str = "tbd",
        notes: Optional[str] = None,
    ) -> str:
        """Assign a logistics task (dropoff/pickup/transport/attend) to a caregiver.

        Set ``status="gap"`` to explicitly flag an uncovered slot, "assigned"
        when a caregiver covers it, or "tbd" while undecided. A row with no
        caregiver and status not "assigned" surfaces as a coverage gap.
        """
        try:
            assignment_id = _storage().add_logistics_assignment(
                user_id,
                task=task,
                week_start=week_start,
                kid_name=kid_name,
                calendar_entry_id=calendar_entry_id,
                caregiver_id=caregiver_id,
                status=status,
                notes=notes,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[cos_tool] AssignLogistics failed: %s", exc)
            return f"Could not assign logistics '{task}': {exc}"
        flag = " (COVERAGE GAP)" if status == "gap" else ""
        return f"Logged logistics '{task}' as {status}{flag} (id={assignment_id})."

    return AssignLogistics


# --------------------------------------------------------------------------- #
# To-dos / follow-ups
# --------------------------------------------------------------------------- #


def _make_add_todo_tool(user_id: str):
    @tool
    def AddTodo(
        title: str,
        kid_name: Optional[str] = None,
        due_date: Optional[str] = None,
        kind: str = "task",
        detail: Optional[str] = None,
        activity_id: Optional[str] = None,
    ) -> str:
        """Add a to-do / follow-up (e.g. "email Camp Tule about the waitlist").

        ``due_date`` is an ISO date. ``kind`` is a short label like
        "task"/"signup"/"payment"/"email". Returns the new todo id.
        """
        try:
            todo_id = _storage().add_todo(
                user_id,
                title=title,
                kid_name=kid_name,
                activity_id=activity_id,
                kind=kind,
                detail=detail,
                due_date=due_date,
                source="cos_agent",
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[cos_tool] AddTodo failed: %s", exc)
            return f"Could not add to-do '{title}': {exc}"
        return f"Added to-do '{title}' (id={todo_id})."

    return AddTodo


def _make_complete_todo_tool(user_id: str):
    @tool
    def CompleteTodo(todo_id: str) -> str:
        """Mark a to-do as done by its id."""
        try:
            _storage().update_todo(todo_id, status="done")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[cos_tool] CompleteTodo failed: %s", exc)
            return f"Could not complete to-do {todo_id}: {exc}"
        return f"Marked to-do {todo_id} done."

    return CompleteTodo


def _make_update_todo_tool(user_id: str):
    @tool
    def UpdateTodo(
        todo_id: str,
        title: Optional[str] = None,
        status: Optional[str] = None,
        due_date: Optional[str] = None,
        detail: Optional[str] = None,
        kind: Optional[str] = None,
    ) -> str:
        """Update fields on an existing to-do. Send only the fields to change."""
        fields = {
            k: v
            for k, v in {
                "title": title,
                "status": status,
                "due_date": due_date,
                "detail": detail,
                "kind": kind,
            }.items()
            if v is not None
        }
        if not fields:
            return "Nothing to update — provide at least one field."
        try:
            _storage().update_todo(todo_id, **fields)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[cos_tool] UpdateTodo failed: %s", exc)
            return f"Could not update to-do {todo_id}: {exc}"
        return f"Updated to-do {todo_id}: {', '.join(fields)}."

    return UpdateTodo


# --------------------------------------------------------------------------- #
# Discovery search (read-only)
# --------------------------------------------------------------------------- #


def _make_search_activities_tool(user_id: str):
    @tool
    def SearchActivities(
        kid_name: Optional[str] = None, category: Optional[str] = None
    ) -> str:
        """Search already-discovered activity candidates for this family.

        Optionally filter by ``kid_name`` and ``category``. Returns a compact,
        numbered list with provider, age window, price, and signup link.
        """
        try:
            candidates = _storage().list_candidates(
                user_id=user_id, kid_name=kid_name, category=category
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[cos_tool] SearchActivities failed: %s", exc)
            return f"Could not search activities: {exc}"
        if not candidates:
            return "No matching activity candidates found."
        lines = []
        for i, c in enumerate(candidates[:15], 1):
            ages = ""
            if c.get("age_min") is not None or c.get("age_max") is not None:
                lo = c.get("age_min")
                hi = c.get("age_max")
                ages = f" ages {lo if lo is not None else '?'}-{hi if hi is not None else '?'}"
            price = f" {c['price_text']}" if c.get("price_text") else ""
            prov = f" @ {c['provider']}" if c.get("provider") else ""
            url = f" {c['signup_url']}" if c.get("signup_url") else ""
            lines.append(f"{i}. {c.get('name')}{prov}{ages}{price}{url}")
        return "\n".join(lines)

    return SearchActivities


# --------------------------------------------------------------------------- #
# Plan snapshot (the agent's read path into current state)
# --------------------------------------------------------------------------- #


def _make_plan_snapshot_tool(user_id: str):
    @tool
    def GetPlanSnapshot() -> str:
        """Read the family's CURRENT plan: tracked activities, open to-dos,
        upcoming calendar, cost picture, time conflicts, and coverage gaps.

        ALWAYS call this before answering "what's my plan" / "what's left" /
        "are we covered" questions — it is the agent's source of truth.
        """
        storage = _storage()
        try:
            tracked = storage.list_tracked_activities(user_id)
            calendar = storage.list_calendar_entries(user_id)
            recurring = storage.list_recurring_appointments(user_id)
            logistics = storage.list_logistics_assignments(user_id)
            todos = storage.list_todos(user_id, status="open")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[cos_tool] GetPlanSnapshot failed: %s", exc)
            return f"Could not read plan state: {exc}"

        summary = planning.build_plan_summary(
            tracked=tracked,
            calendar_entries=calendar,
            recurring=recurring,
            logistics=logistics,
            kids=_kids_for(user_id),
        )
        cost = summary["cost"]
        out: list[str] = []

        # Tracked activities (pending vs confirmed explicit)
        if tracked:
            out.append("Tracked activities:")
            for t in tracked:
                who = f" [{t['kid_name']}]" if t.get("kid_name") else ""
                price = (
                    f" ${t['price_amount']:g}"
                    if t.get("price_amount") is not None
                    else ""
                )
                out.append(
                    f"  - {t.get('name')}{who} — {t.get('status')}{price}"
                    f" (id={t.get('id')})"
                )
        else:
            out.append("Tracked activities: none yet.")

        # Cost
        out.append(
            f"Cost: ${cost['confirmed_total']:g} confirmed across "
            f"{cost['item_count']} item(s); {cost['tbd_count']} price(s) TBD."
        )

        # Upcoming calendar
        if calendar:
            out.append("Calendar:")
            for e in calendar[:12]:
                who = f" [{e['kid_name']}]" if e.get("kid_name") else ""
                wk = f" week {e['week_start']}" if e.get("week_start") else ""
                out.append(
                    f"  - {e.get('title')}{who} ({e.get('kind')}){wk}"
                    f" (id={e.get('id')})"
                )
        else:
            out.append("Calendar: empty.")

        # Open to-dos
        if todos:
            out.append("Open to-dos:")
            for td in todos:
                due = f" due {td['due_date']}" if td.get("due_date") else ""
                out.append(f"  - {td.get('title')}{due} (id={td.get('id')})")
        else:
            out.append("Open to-dos: none.")

        # Conflicts
        if summary["conflicts"]:
            out.append("Time conflicts:")
            for c in summary["conflicts"]:
                out.append(f"  - {c.get('detail')}")

        # Coverage gaps
        if summary["coverage_gaps"]:
            out.append("Coverage gaps:")
            for g in summary["coverage_gaps"]:
                who = f" [{g['kid_name']}]" if g.get("kid_name") else ""
                wk = f" week {g['week_start']}" if g.get("week_start") else ""
                out.append(f"  - {g.get('task')}{who}{wk}: {g.get('reason')}")

        # Pending eligibility
        if summary["pending_eligibility"]:
            out.append("Pending age-eligibility decisions:")
            for p in summary["pending_eligibility"]:
                out.append(f"  - {p.get('name')} (id={p.get('id')})")

        return "\n".join(out)

    return GetPlanSnapshot


def _make_compare_activities_tool(user_id: str):
    @tool
    def CompareActivities() -> str:
        """Tabulate the SHORTLIST (activities still being considered — status
        exploring/interested/pending/waitlisted) side-by-side to help the parent
        DECIDE: price, age-eligibility, week, location/hours, and which options
        COMPETE (same kid + same week ⇒ they can't pick both).

        Call this when the parent wants to choose between camps, triage their
        options, or "help me decide". Use the result to walk the tradeoffs, then
        record decisions with TrackActivity (status "confirmed"/"signed_up" for
        picks, "declined" for the rest) including a decision_rationale.
        """
        storage = _storage()
        try:
            tracked = storage.list_tracked_activities(user_id)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("[cos_tool] CompareActivities failed: %s", exc)
            return f"Could not read the shortlist: {exc}"

        cmp = planning.compare_activities(tracked, kids=_kids_for(user_id))
        rows = cmp["items"]
        if not rows:
            return (
                "The shortlist is empty — nothing in 'exploring' or other "
                "undecided states to compare yet. Pin some candidates first."
            )

        out: list[str] = [
            f"Shortlist ({cmp['count']} option(s) to decide; "
            f"${cmp['total_if_all_selected']:g} if all chosen):"
        ]
        for r in rows:
            who = f" [{r['kid_name']}]" if r.get("kid_name") else ""
            price = (
                f" ${r['price_amount']:g} ({r.get('price_status')})"
                if r.get("price_amount") is not None
                else " price TBD"
            )
            week = f" wk {r['week_start']}" if r.get("week_start") else ""
            where = f" @ {r['location']}" if r.get("location") else ""
            elig = "" if r.get("eligible") else f" ⚠ {r.get('eligibility_reason')}"
            competes = (
                f" — competes with: {', '.join(r['competes_with'])}"
                if r.get("competes_with")
                else ""
            )
            out.append(
                f"  - {r.get('name')}{who} ({r.get('status')}){price}{week}{where}"
                f"{elig}{competes} (id={r.get('id')})"
            )
        return "\n".join(out)

    return CompareActivities


# --------------------------------------------------------------------------- #
# Eligibility check
# --------------------------------------------------------------------------- #


def _make_check_eligibility_tool(user_id: str):
    @tool
    def CheckEligibility(
        activity_name: str,
        kid_name: str,
        kid_age: float,
        age_min: Optional[float] = None,
        age_max: Optional[float] = None,
    ) -> str:
        """Check whether a kid's age fits an activity's age window.

        Returns a short eligibility verdict + reason.
        """
        result = planning.check_eligibility(
            {"name": activity_name, "age_min": age_min, "age_max": age_max},
            {"name": kid_name, "age": kid_age},
        )
        verb = "Eligible" if result["eligible"] else "Not eligible"
        return f"{verb}: {result['reason']}."

    return CheckEligibility


# --------------------------------------------------------------------------- #
# Email drafting (human-in-the-loop — NEVER sends)
# --------------------------------------------------------------------------- #


def _make_draft_email_tool(user_id: str):
    @tool
    def DraftEmail(
        intent: str, to: Optional[str] = None, subject: Optional[str] = None
    ) -> str:
        """Draft an email to an organizer/provider for the parent to review.

        This NEVER sends anything (human-in-the-loop): it only returns a draft
        body the parent can copy, edit, and send themselves. ``intent`` is what
        the parent wants to accomplish (e.g. "ask Camp Tule about the waitlist").
        """
        subject_line = subject or f"Re: {intent}"
        recipient = to or "[organizer]"
        body = (
            f"To: {recipient}\n"
            f"Subject: {subject_line}\n\n"
            f"Hi,\n\n"
            f"I'm reaching out regarding {intent}. Could you let me know the next "
            f"steps and any details I should be aware of (dates, availability, "
            f"cost, and how to confirm a spot)?\n\n"
            f"Thank you for your help — I appreciate it.\n\n"
            f"Best,\n"
            f"[Your name]"
        )
        return "DRAFT (not sent — review and send yourself):\n\n" + body

    return DraftEmail


# --------------------------------------------------------------------------- #
# Camp lookup-and-save (do what the UI does: research a named camp + track it)
# --------------------------------------------------------------------------- #


def _make_lookup_and_save_camp_tool(user_id: str):
    @tool
    def LookupAndSaveCamp(
        camp_name: str,
        kid_name: Optional[str] = None,
        url: Optional[str] = None,
        status: str = "signed_up",
        note: Optional[str] = None,
    ) -> str:
        """Look up a specific camp/class — typically one the parent ALREADY signed
        up for — fetch its details from the web, and SAVE it to the plan as if it
        had been tracked through the app UI.

        Use this when the parent gives you camps they've registered for ("I signed
        up for Camp Galileo and Steve & Kate's"). Call it ONCE per camp. Default
        ``status`` is "signed_up" (already registered) — use "confirmed" if they
        say it's locked in, or "exploring" if they're only considering it. Pass
        ``url`` when the parent gives a link. First reuses an already-discovered
        candidate if one matches (no web spend); otherwise it searches the web,
        extracts the details, and tracks it.
        """
        storage = _storage()

        # 1) Reuse an already-discovered candidate by name (free — no web call).
        try:
            candidates = storage.list_candidates(user_id=user_id)
        except Exception:  # noqa: BLE001 — fall through to web lookup
            candidates = []
        low = (camp_name or "").lower().strip()
        match = None
        for c in candidates:
            nm = (c.get("name") or "").lower()
            if low and (low in nm or nm in low):
                match = c
                break
        if match:
            try:
                activity_id = storage.track_activity(
                    user_id,
                    name=match.get("name") or camp_name,
                    kid_name=kid_name or match.get("kid_name"),
                    candidate_id=match.get("id"),
                    provider=match.get("provider"),
                    status=status,
                    price_amount=match.get("price_amount"),
                    price_status="confirmed" if match.get("price_amount") is not None else "tbd",
                    signup_url=match.get("signup_url"),
                    notes=note,
                )
            except Exception as exc:
                return _tool_error("LookupAndSaveCamp", exc, user_id)
            return (
                f"Saved '{match.get('name') or camp_name}' as {status} "
                f"(matched one of your discovered options, id={activity_id})."
            )

        # 2) Targeted web lookup → structured extraction → track. NEW SPEND PATH:
        # cost-log the Tavily search + the extraction LLM call under feature=cos.
        try:
            from langchain_tavily import TavilySearch
            from app.ingest.extract import extract_from_text

            query = url or f"{camp_name} kids camp registration details schedule price location"
            search = TavilySearch(max_results=5, search_depth="advanced")
            results = search.invoke(
                {"query": query},
                config=cost_config(
                    "cos", workflow=new_workflow_id(), user=user_id, search_depth="advanced"
                ),
            )
            extracted = extract_from_text(
                _results_to_text(results),
                source_hint=f"web lookup for {camp_name}",
                cost_user=user_id,
            )
        except Exception as exc:
            return _tool_error("LookupAndSaveCamp", exc, user_id)

        signup = url or next((l.url for l in extracted.links if l.url), None)
        details = {
            "hours": extracted.hours,
            "schedule_text": extracted.schedule_text,
            "dates": extracted.dates,
            "location": extracted.location,
            "age_min": extracted.age_min,
            "age_max": extracted.age_max,
        }
        try:
            activity_id = storage.track_activity(
                user_id,
                name=extracted.activity_name or camp_name,
                kid_name=kid_name or extracted.kid_fit,
                provider=extracted.provider,
                status=status,
                price_amount=extracted.amount_due,
                price_status="confirmed" if extracted.amount_due is not None else "tbd",
                signup_url=signup,
                contact=extracted.contact.model_dump() if extracted.contact else None,
                details=details,
                notes=note,
            )
        except Exception as exc:
            return _tool_error("LookupAndSaveCamp", exc, user_id)

        bits = []
        if extracted.provider:
            bits.append(extracted.provider)
        if extracted.location:
            bits.append(extracted.location)
        if extracted.amount_due is not None:
            bits.append(f"${extracted.amount_due:g}")
        extra = f" ({'; '.join(bits)})" if bits else ""
        return (
            f"Looked up and saved '{extracted.activity_name or camp_name}' as "
            f"{status}{extra} (id={activity_id})."
        )

    return LookupAndSaveCamp


# --------------------------------------------------------------------------- #
# Update / untrack tracked activities (shortlist parity with the UI)
# --------------------------------------------------------------------------- #


def _make_update_activity_tool(user_id: str):
    @tool
    def UpdateActivity(
        activity_id: str,
        status: Optional[str] = None,
        price_amount: Optional[float] = None,
        price_status: Optional[str] = None,
        signup_url: Optional[str] = None,
        week_start: Optional[str] = None,
        notes: Optional[str] = None,
        decision_rationale: Optional[str] = None,
    ) -> str:
        """Update fields on an existing tracked activity — e.g. move it
        exploring→signed_up/confirmed/declined, set the price, add a signup link,
        or set the week. Send only the fields to change. ALWAYS include
        ``decision_rationale`` when you change ``status`` (decision log)."""
        storage = _storage()
        existing = storage.get_tracked_activity(activity_id)
        if not existing:
            return f"No tracked activity with id {activity_id}."
        if existing.get("user_id") != user_id:
            return "That activity doesn't belong to this account."
        fields = {
            k: v
            for k, v in {
                "status": status,
                "price_amount": price_amount,
                "price_status": price_status,
                "signup_url": signup_url,
                "week_start": week_start,
                "notes": notes,
                "decision_rationale": decision_rationale,
            }.items()
            if v is not None
        }
        if not fields:
            return "Nothing to update — provide at least one field."
        try:
            storage.update_tracked_activity(activity_id, **fields)
        except Exception as exc:
            return _tool_error("UpdateActivity", exc, user_id)
        return f"Updated '{existing.get('name')}': {', '.join(fields)} (id={activity_id})."

    return UpdateActivity


def _make_untrack_activity_tool(user_id: str):
    @tool
    def UntrackActivity(activity_id: str) -> str:
        """Permanently remove a tracked activity from the plan (un-pin from the
        shortlist, or delete one added by mistake). Prefer
        UpdateActivity(status="declined") when the parent decided against it but
        wants it on the record."""
        storage = _storage()
        existing = storage.get_tracked_activity(activity_id)
        if not existing:
            return f"No tracked activity with id {activity_id}."
        if existing.get("user_id") != user_id:
            return "That activity doesn't belong to this account."
        try:
            storage.delete_tracked_activity(activity_id)
        except Exception as exc:
            return _tool_error("UntrackActivity", exc, user_id)
        return f"Removed '{existing.get('name')}' (id={activity_id})."

    return UntrackActivity


# --------------------------------------------------------------------------- #
# Kick off a discovery run from chat
# --------------------------------------------------------------------------- #


def _make_start_discovery_tool(user_id: str):
    @tool
    def StartDiscovery(
        focus: Optional[str] = None, radius_miles: Optional[int] = None
    ) -> str:
        """Kick off a background web-discovery run to find NEW camps/activities for
        the family near their saved location. Use when the parent wants you to go
        find options ("find art camps for Ceiba", "what swim classes are near us").
        Optional ``focus`` biases what to surface (category / which kid / vibe);
        ``radius_miles`` limits distance. Returns once queued — finds stream onto
        the Discover tab; afterwards use SearchActivities to read them."""
        storage = _storage()
        from app.profiling import profiling_service

        fam = profiling_service.get_family_profile(user_id) or {}
        parent = fam.get("parent") or {}
        location = {
            "postal_code": parent.get("postal_code"),
            "country": parent.get("country"),
        }
        if not location.get("postal_code"):
            return (
                "I can't start discovery without your ZIP/postal code — add it in "
                "Settings → Profile first, then ask me again."
            )
        kids = []
        for name, prof in (fam.get("children") or {}).items():
            prof = prof or {}
            kids.append(
                {
                    "name": prof.get("name") or name,
                    "age": prof.get("age"),
                    "grade_band": prof.get("grade_band"),
                    "interests": prof.get("interests") or [],
                }
            )
        params: dict = {}
        if focus:
            params["focus"] = focus
        if radius_miles:
            params["radius_miles"] = radius_miles
        try:
            result = storage.enqueue_research_run(
                user_id=user_id, location=location, kids=kids, params=params
            )
        except Exception as exc:
            return _tool_error("StartDiscovery", exc, user_id)
        try:
            from app.research.worker import research_worker

            if research_worker is not None:
                research_worker.notify()
        except Exception:  # noqa: BLE001 — worker wake is best-effort
            pass
        if result.get("deduped"):
            return (
                f"A discovery run is already in progress (id={result['run_id']}). "
                "New finds appear on the Discover tab."
            )
        return (
            f"Started a discovery run (id={result['run_id']}). New camps will appear "
            "on the Discover tab as they're found — ask me to search them after."
        )

    return StartDiscovery


# --------------------------------------------------------------------------- #
# Kids info + help (read-only)
# --------------------------------------------------------------------------- #


def _make_get_kids_info_tool(user_id: str):
    @tool
    def GetKidsInfo() -> str:
        """Return what we know about the parent's kids — name, age, grade band,
        interests, and notable constraints — to tailor recommendations and fit.
        Call this when reasoning about which activities suit which kid."""
        from app.profiling import profiling_service

        fam = profiling_service.get_family_profile(user_id) or {}
        kids = fam.get("children") or {}
        if not kids:
            return (
                "No kids on file yet. The parent can add them in Settings → Profile "
                "(or tell you and you can note it)."
            )
        out: list[str] = []
        for key, p in kids.items():
            p = p or {}
            name = p.get("name") or key
            bits: list[str] = []
            age = p.get("age")
            if age is not None:
                try:
                    bits.append(f"age {float(age):g}")
                except (TypeError, ValueError):
                    pass
            if p.get("grade_band"):
                bits.append(str(p["grade_band"]))
            if p.get("interests"):
                bits.append("interests: " + ", ".join(p["interests"]))
            if p.get("temperament"):
                bits.append(f"temperament: {p['temperament']}")
            out.append(f"- {name}" + (f" — {'; '.join(bits)}" if bits else ""))
        return "Kids:\n" + "\n".join(out)

    return GetKidsInfo


def _make_help_tool(user_id: str):
    @tool
    def Help() -> str:
        """List everything you (the Chief of Staff) can do. Call this whenever the
        parent asks "help", "what can you do", "how does this work", or otherwise
        seems unsure where to start."""
        return _HELP_TEXT

    return Help


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #


def build_cos_tools(user_id: str) -> list:
    """Return the full Chief-of-Staff toolset bound to ``user_id``."""
    return [
        _make_track_activity_tool(user_id),
        _make_add_to_calendar_tool(user_id),
        _make_add_recurring_tool(user_id),
        _make_add_caregiver_tool(user_id),
        _make_assign_logistics_tool(user_id),
        _make_add_todo_tool(user_id),
        _make_complete_todo_tool(user_id),
        _make_update_todo_tool(user_id),
        _make_search_activities_tool(user_id),
        _make_plan_snapshot_tool(user_id),
        _make_compare_activities_tool(user_id),
        _make_check_eligibility_tool(user_id),
        _make_draft_email_tool(user_id),
        # Power-tools: do what the UI does (2026-06-28)
        _make_lookup_and_save_camp_tool(user_id),
        _make_update_activity_tool(user_id),
        _make_untrack_activity_tool(user_id),
        _make_start_discovery_tool(user_id),
        _make_get_kids_info_tool(user_id),
        _make_help_tool(user_id),
    ]
