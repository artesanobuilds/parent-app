"""Admin (CMS) endpoints for the email-sync agent: force-run, schedule config,
recent runs. All behind the operator `require_admin_token` gate."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cms/email-sync", tags=["email-sync"])

_SCHEDULE_KEY = "email_sync_schedule"
_DEFAULT_SCHEDULE = {"enabled": False, "hour": 6, "tz": "America/Los_Angeles"}


def _storage():
    from app.server import storage_backend

    return storage_backend


from app.admin_auth import require_admin_token  # shared operator gate (header or CMS cookie)


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
    Gmail account, then wake the worker."""
    storage = _storage()
    if user_id:
        targets = [user_id]
    else:
        targets = [a["user_id"] for a in storage.list_connected_email_accounts()]
    if not targets:
        raise HTTPException(status_code=400, detail="no connected Gmail accounts to sync")

    ids = [storage.create_email_sync_run(user_id=u, trigger="manual") for u in targets]
    try:
        from app.email_sync.worker import email_sync_worker

        if email_sync_worker is not None:
            email_sync_worker.notify()
    except Exception:  # noqa: BLE001
        logger.exception("[email-sync] notify failed")
    return {"enqueued": len(ids), "run_ids": ids}


@router.get("/runs")
def list_runs(limit: int = 50, _: None = Depends(require_admin_token)):
    return {"runs": _storage().list_email_sync_runs(limit=limit)}
