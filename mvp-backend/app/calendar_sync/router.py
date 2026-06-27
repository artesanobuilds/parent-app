"""Admin (CMS) endpoints for the two-way calendar-sync agent: force-run,
schedule config, recent runs. All behind the operator `require_admin_token`
gate. Mirrors `app/email_sync/router.py`."""
from __future__ import annotations

import hmac
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cms/calendar-sync", tags=["calendar-sync"])

_SCHEDULE_KEY = "calendar_sync_schedule"
_DEFAULT_SCHEDULE = {"enabled": False, "hour": 6, "tz": "America/Los_Angeles"}


def _storage():
    from app.server import storage_backend

    return storage_backend


def require_admin_token(x_admin_token: Optional[str] = Header(default=None)) -> None:
    """Self-contained operator gate (mirrors app.server.require_admin_token —
    defined locally to avoid an import cycle since the router is included before
    server.py finishes defining its own copy)."""
    expected = os.getenv("ADMIN_TOKEN")
    if not expected:
        raise HTTPException(status_code=503, detail="admin endpoints disabled (ADMIN_TOKEN not set)")
    if not x_admin_token or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="invalid or missing admin token")


class ScheduleConfig(BaseModel):
    enabled: bool = False
    hour: int = Field(6, ge=0, le=23)
    tz: str = "America/Los_Angeles"


@router.get("/config")
def get_config(_: None = Depends(require_admin_token)):
    cfg = _storage().get_agent_config(_SCHEDULE_KEY) or _DEFAULT_SCHEDULE
    return cfg


@router.put("/config")
def put_config(body: ScheduleConfig, _: None = Depends(require_admin_token)):
    _storage().set_agent_config(_SCHEDULE_KEY, body.model_dump())
    return body.model_dump()


@router.post("/run")
def run_now(user_id: Optional[str] = None, _: None = Depends(require_admin_token)):
    """Force a manual sync: enqueue a run for `user_id`, or for every connected
    Google Calendar account, then wake the worker."""
    storage = _storage()
    if user_id:
        targets = [user_id]
    else:
        targets = [a["user_id"] for a in storage.list_connected_calendar_accounts()]
    if not targets:
        raise HTTPException(status_code=400, detail="no connected Google Calendar accounts to sync")

    ids = [storage.create_calendar_sync_run(user_id=u, trigger="manual") for u in targets]
    try:
        from app.calendar_sync.worker import calendar_sync_worker

        if calendar_sync_worker is not None:
            calendar_sync_worker.notify()
    except Exception:  # noqa: BLE001
        logger.exception("[calendar-sync] notify failed")
    return {"enqueued": len(ids), "run_ids": ids}


@router.get("/runs")
def list_runs(limit: int = 50, _: None = Depends(require_admin_token)):
    return {"runs": _storage().list_calendar_sync_runs(limit=limit)}
