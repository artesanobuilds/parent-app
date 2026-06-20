"""Chief-of-Staff API: interactive chat + CRUD for the activity-planning model.

Follows the app's conventions (cf. ``app/research/router.py``): ``current_user``
resolves the bearer token, ``authorize_user_match`` blocks cross-user access,
``rate_limit_enforce`` throttles chat, and storage is imported lazily inside
handlers to avoid an import cycle with ``app.server``.

The chat endpoint streams SSE with the exact envelope shape of
``app.server.generate_stream`` (``{"type":"token","content":...}`` frames
terminated by ``data: [DONE]``) so existing clients can reuse their parser.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from app.auth import current_user, authorize_user_match
from app.rate_limit import enforce as rate_limit_enforce
from app.cos import planning
from app.cos.agent import get_cos_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cos", tags=["chief-of-staff"])


def _storage():
    from app.server import storage_backend

    return storage_backend


# --------------------------------------------------------------------------- #
# Chat (SSE)
# --------------------------------------------------------------------------- #


class CosChatRequest(BaseModel):
    user_id: str
    message: str
    thread_id: str = "default"


async def _cos_chat_stream(user_id: str, thread_id: str, message: str):
    """SSE generator mirroring app.server.generate_stream's envelope."""
    storage = _storage()
    storage.append_cos_message(user_id, thread_id=thread_id, role="user", content=message)

    agent = get_cos_agent(user_id)
    memory_key = f"cos:{user_id}:{thread_id}"
    config = {"configurable": {"thread_id": memory_key}}
    assistant_buffer = ""

    try:
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            version="v1",
        ):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    assistant_buffer += content
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            elif kind == "on_tool_start":
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': event['name']})}\n\n"
            elif kind == "on_tool_end":
                yield f"data: {json.dumps({'type': 'tool_end', 'tool': event['name']})}\n\n"

        yield "data: [DONE]\n\n"
        if assistant_buffer:
            storage.append_cos_message(
                user_id, thread_id=thread_id, role="assistant", content=assistant_buffer
            )
    except Exception as exc:
        logger.error(f"[cos] stream error: {exc}")
        yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"


@router.post("/chat")
async def cos_chat(req: CosChatRequest, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=req.user_id)
    rate_limit_enforce(user_id, "chat")
    return StreamingResponse(
        _cos_chat_stream(user_id, req.thread_id, req.message),
        media_type="text/event-stream",
    )


@router.get("/messages")
def cos_messages(thread_id: str = "default", user_id: str = Depends(current_user)):
    return {"messages": _storage().get_cos_messages(user_id, thread_id=thread_id)}


# --------------------------------------------------------------------------- #
# Tracked activities
# --------------------------------------------------------------------------- #


class TrackActivityBody(BaseModel):
    user_id: str
    name: str
    kid_name: Optional[str] = None
    candidate_id: Optional[str] = None
    provider: Optional[str] = None
    week_start: Optional[str] = None
    status: str = "interested"
    pending_reason: Optional[str] = None
    price_amount: Optional[float] = None
    price_status: str = "tbd"
    signup_url: Optional[str] = None
    notes: Optional[str] = None
    decision_rationale: Optional[str] = None


class TrackActivityPatch(BaseModel):
    user_id: str
    status: Optional[str] = None
    pending_reason: Optional[str] = None
    price_amount: Optional[float] = None
    price_status: Optional[str] = None
    signup_url: Optional[str] = None
    week_start: Optional[str] = None
    notes: Optional[str] = None
    decision_rationale: Optional[str] = None


@router.post("/activities/track")
def track_activity(body: TrackActivityBody, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    payload = body.model_dump(exclude={"user_id"})
    activity_id = _storage().track_activity(user_id, **payload)
    return {"id": activity_id}


@router.get("/activities")
def list_activities(status: Optional[str] = None, user_id: str = Depends(current_user)):
    return {"activities": _storage().list_tracked_activities(user_id, status=status)}


@router.patch("/activities/{activity_id}")
def patch_activity(
    activity_id: str, body: TrackActivityPatch, user_id: str = Depends(current_user)
):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    storage = _storage()
    existing = storage.get_tracked_activity(activity_id)
    if not existing:
        raise HTTPException(status_code=404, detail="tracked activity not found")
    authorize_user_match(authenticated=user_id, claimed=existing["user_id"])
    fields = body.model_dump(exclude={"user_id"}, exclude_none=True)
    storage.update_tracked_activity(activity_id, **fields)
    return {"id": activity_id, "activity": storage.get_tracked_activity(activity_id)}


# --------------------------------------------------------------------------- #
# Calendar
# --------------------------------------------------------------------------- #


class CalendarBody(BaseModel):
    user_id: str
    title: str
    kid_name: Optional[str] = None
    activity_id: Optional[str] = None
    week_start: Optional[str] = None
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    all_day: bool = False
    location_text: Optional[str] = None
    kind: str = "camp"
    status: str = "confirmed"


class CalendarPatch(BaseModel):
    user_id: str
    title: Optional[str] = None
    kid_name: Optional[str] = None
    week_start: Optional[str] = None
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    all_day: Optional[bool] = None
    location_text: Optional[str] = None
    kind: Optional[str] = None
    status: Optional[str] = None


class CalendarDelete(BaseModel):
    user_id: str


@router.get("/calendar")
def list_calendar(
    week_start: Optional[str] = None,
    kid_name: Optional[str] = None,
    user_id: str = Depends(current_user),
):
    return {
        "entries": _storage().list_calendar_entries(
            user_id, week_start=week_start, kid_name=kid_name
        )
    }


@router.post("/calendar")
def add_calendar(body: CalendarBody, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    payload = body.model_dump(exclude={"user_id"})
    entry_id = _storage().add_calendar_entry(user_id, source="manual", **payload)
    return {"id": entry_id}


def _require_owned_calendar(storage, entry_id: str, user_id: str) -> Dict[str, Any]:
    entry = storage.get_calendar_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="calendar entry not found")
    authorize_user_match(authenticated=user_id, claimed=entry["user_id"])
    return entry


@router.patch("/calendar/{entry_id}")
def patch_calendar(
    entry_id: str, body: CalendarPatch, user_id: str = Depends(current_user)
):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    storage = _storage()
    _require_owned_calendar(storage, entry_id, user_id)
    fields = body.model_dump(exclude={"user_id"}, exclude_none=True)
    storage.update_calendar_entry(entry_id, **fields)
    return {"id": entry_id, "entry": storage.get_calendar_entry(entry_id)}


@router.delete("/calendar/{entry_id}")
def delete_calendar(
    entry_id: str, body: CalendarDelete, user_id: str = Depends(current_user)
):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    storage = _storage()
    _require_owned_calendar(storage, entry_id, user_id)
    storage.delete_calendar_entry(entry_id)
    return {"id": entry_id, "deleted": True}


# --------------------------------------------------------------------------- #
# Recurring appointments
# --------------------------------------------------------------------------- #


class RecurringBody(BaseModel):
    user_id: str
    title: str
    kid_name: Optional[str] = None
    provider_name: Optional[str] = None
    weekday: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    transporter: Optional[str] = None
    notes: Optional[str] = None


class RecurringDelete(BaseModel):
    user_id: str


@router.get("/recurring")
def list_recurring(user_id: str = Depends(current_user)):
    return {"recurring": _storage().list_recurring_appointments(user_id)}


@router.post("/recurring")
def add_recurring(body: RecurringBody, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    payload = body.model_dump(exclude={"user_id"})
    appt_id = _storage().add_recurring_appointment(user_id, **payload)
    return {"id": appt_id}


@router.delete("/recurring/{appt_id}")
def delete_recurring(
    appt_id: str, body: RecurringDelete, user_id: str = Depends(current_user)
):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    storage = _storage()
    owned = any(a["id"] == appt_id for a in storage.list_recurring_appointments(user_id))
    if not owned:
        raise HTTPException(status_code=404, detail="recurring appointment not found")
    storage.delete_recurring_appointment(appt_id)
    return {"id": appt_id, "deleted": True}


# --------------------------------------------------------------------------- #
# Caregivers
# --------------------------------------------------------------------------- #


class CaregiverBody(BaseModel):
    user_id: str
    name: str
    role: str = "other"
    contact: Optional[str] = None
    default_availability: Optional[str] = None
    notes: Optional[str] = None


class CaregiverPatch(BaseModel):
    user_id: str
    name: Optional[str] = None
    role: Optional[str] = None
    contact: Optional[str] = None
    default_availability: Optional[str] = None
    notes: Optional[str] = None


@router.get("/caregivers")
def list_caregivers(user_id: str = Depends(current_user)):
    return {"caregivers": _storage().list_caregivers(user_id)}


@router.post("/caregivers")
def add_caregiver(body: CaregiverBody, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    payload = body.model_dump(exclude={"user_id"})
    caregiver_id = _storage().add_caregiver(user_id, **payload)
    return {"id": caregiver_id}


@router.patch("/caregivers/{caregiver_id}")
def patch_caregiver(
    caregiver_id: str, body: CaregiverPatch, user_id: str = Depends(current_user)
):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    storage = _storage()
    owned = any(c["id"] == caregiver_id for c in storage.list_caregivers(user_id))
    if not owned:
        raise HTTPException(status_code=404, detail="caregiver not found")
    fields = body.model_dump(exclude={"user_id"}, exclude_none=True)
    storage.update_caregiver(caregiver_id, **fields)
    return {"id": caregiver_id}


# --------------------------------------------------------------------------- #
# Logistics
# --------------------------------------------------------------------------- #


class LogisticsBody(BaseModel):
    user_id: str
    task: str
    week_start: Optional[str] = None
    kid_name: Optional[str] = None
    calendar_entry_id: Optional[str] = None
    caregiver_id: Optional[str] = None
    status: str = "tbd"
    notes: Optional[str] = None


class LogisticsPatch(BaseModel):
    user_id: str
    task: Optional[str] = None
    week_start: Optional[str] = None
    kid_name: Optional[str] = None
    caregiver_id: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


@router.get("/logistics")
def list_logistics(week_start: Optional[str] = None, user_id: str = Depends(current_user)):
    return {
        "logistics": _storage().list_logistics_assignments(user_id, week_start=week_start)
    }


@router.post("/logistics")
def add_logistics(body: LogisticsBody, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    payload = body.model_dump(exclude={"user_id"})
    assignment_id = _storage().add_logistics_assignment(user_id, **payload)
    return {"id": assignment_id}


@router.patch("/logistics/{assignment_id}")
def patch_logistics(
    assignment_id: str, body: LogisticsPatch, user_id: str = Depends(current_user)
):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    storage = _storage()
    owned = any(
        a["id"] == assignment_id for a in storage.list_logistics_assignments(user_id)
    )
    if not owned:
        raise HTTPException(status_code=404, detail="logistics assignment not found")
    fields = body.model_dump(exclude={"user_id"}, exclude_none=True)
    storage.update_logistics_assignment(assignment_id, **fields)
    return {"id": assignment_id}


# --------------------------------------------------------------------------- #
# To-dos
# --------------------------------------------------------------------------- #


class TodoBody(BaseModel):
    user_id: str
    title: str
    kid_name: Optional[str] = None
    activity_id: Optional[str] = None
    kind: str = "task"
    detail: Optional[str] = None
    due_date: Optional[str] = None
    status: str = "open"


class TodoPatch(BaseModel):
    user_id: str
    title: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    detail: Optional[str] = None
    kind: Optional[str] = None
    kid_name: Optional[str] = None


@router.get("/todos")
def list_todos(status: Optional[str] = None, user_id: str = Depends(current_user)):
    return {"todos": _storage().list_todos(user_id, status=status)}


@router.post("/todos")
def add_todo(body: TodoBody, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    payload = body.model_dump(exclude={"user_id"})
    todo_id = _storage().add_todo(user_id, source="manual", **payload)
    return {"id": todo_id}


@router.patch("/todos/{todo_id}")
def patch_todo(todo_id: str, body: TodoPatch, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=body.user_id)
    storage = _storage()
    owned = any(t["id"] == todo_id for t in storage.list_todos(user_id))
    if not owned:
        raise HTTPException(status_code=404, detail="todo not found")
    fields = body.model_dump(exclude={"user_id"}, exclude_none=True)
    storage.update_todo(todo_id, **fields)
    return {"id": todo_id}


# --------------------------------------------------------------------------- #
# Plan summary
# --------------------------------------------------------------------------- #


@router.get("/plan/summary")
def plan_summary(weeks: Optional[str] = None, user_id: str = Depends(current_user)):
    from app.profiling import profiling_service

    storage = _storage()
    fam = profiling_service.get_family_profile(user_id) or {}
    kids: List[Dict[str, Any]] = []
    for name, prof in (fam.get("children") or {}).items():
        prof = prof or {}
        kids.append({"name": prof.get("name") or name, "age": prof.get("age")})

    week_list = [w.strip() for w in weeks.split(",") if w.strip()] if weeks else []

    return planning.build_plan_summary(
        tracked=storage.list_tracked_activities(user_id),
        calendar_entries=storage.list_calendar_entries(user_id),
        recurring=storage.list_recurring_appointments(user_id),
        logistics=storage.list_logistics_assignments(user_id),
        kids=kids,
        weeks=week_list,
    )
