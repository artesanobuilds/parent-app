"""
Discovery API: trigger a research run, poll its status, list candidates.

Follows the app's conventions: `current_user` resolves the bearer token,
`authorize_user_match` blocks cross-user access, `enforce` rate-limits. Storage
and the worker are imported lazily inside handlers to avoid an import cycle with
app.server (same pattern as app.auth / app.kid_agent).
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth import current_user, authorize_user_match
from app.rate_limit import enforce as rate_limit_enforce

router = APIRouter(prefix="/research", tags=["research"])


class ResearchRunRequest(BaseModel):
    user_id: str
    location: Optional[Dict[str, Any]] = None  # {postal_code, country, radius_km}; defaults from profile
    params: Optional[Dict[str, Any]] = None     # season, categories, max_candidates, ...


def _storage():
    from app.server import storage_backend
    return storage_backend


def _location_and_kids_from_profile(user_id: str):
    """Default the run's location + kid snapshots from the family profile."""
    from app.profiling import profiling_service

    fam = profiling_service.get_family_profile(user_id) or {}
    parent = fam.get("parent") or {}
    location = {"postal_code": parent.get("postal_code"), "country": parent.get("country")}

    kids: List[Dict[str, Any]] = []
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
    return location, kids


def _require_owned_run(storage, run_id: str, user_id: str) -> Dict[str, Any]:
    run = storage.get_research_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="research run not found")
    authorize_user_match(authenticated=user_id, claimed=run["user_id"], resource=True)
    return run


@router.post("/runs")
def create_run(req: ResearchRunRequest, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=req.user_id)
    rate_limit_enforce(user_id, "research")

    storage = _storage()
    default_location, kids = _location_and_kids_from_profile(user_id)
    location = req.location or default_location

    # Atomic dedupe-or-create: if this parent already has a run in flight
    # (queued or running), reuse it instead of stacking another behind it — a
    # double-tap just resumes the same run. The check+insert is one transaction
    # so two simultaneous submits can't both create (no wasted duplicate spend).
    result = storage.enqueue_research_run(
        user_id=user_id, location=location, kids=kids, params=req.params or {}
    )
    if result["deduped"]:
        return {"run_id": result["run_id"], "status": result["status"], "deduped": True}

    # New run: wake the background worker so it picks it up immediately (it also
    # polls, so a missing/not-yet-started worker just means a short delay).
    from app.research.worker import research_worker
    if research_worker is not None:
        research_worker.notify()

    try:
        from app.analytics import capture
        capture("research_run_started", user_id)
    except Exception:
        pass
    return {"run_id": result["run_id"], "status": "queued"}


@router.get("/runs")
def list_runs(user_id: str = Depends(current_user)):
    return {"runs": _storage().list_research_runs(user_id)}


@router.get("/runs/{run_id}")
def get_run(run_id: str, user_id: str = Depends(current_user)):
    run = _require_owned_run(_storage(), run_id, user_id)
    return {
        "run_id": run["id"],
        "status": run["status"],
        "progress": run.get("progress") or {},
        "candidate_count": run.get("candidate_count", 0),
        "error": run.get("error"),
    }


# Stream interval / cap (env-tunable). Server-side tail of progress_json — the
# client holds ONE connection instead of polling every 2s.
_STREAM_INTERVAL_S = 1.0
_STREAM_MAX_TICKS = 600  # ~10 min ceiling so a wedged run can't hold forever


@router.get("/runs/{run_id}/stream")
async def stream_run(run_id: str, user_id: str = Depends(current_user)):
    """SSE: stream a run's progress so clients don't poll. Tails progress_json and
    emits a frame whenever it changes, then a terminal `final` frame + `[DONE]`.
    The `GET /runs/{run_id}` poll endpoint stays for fallback/back-compat."""
    storage = _storage()
    _require_owned_run(storage, run_id, user_id)  # ownership check before streaming (raises 404/403)

    async def _gen():
        last_payload = None
        for _ in range(_STREAM_MAX_TICKS):
            run = storage.get_research_run(run_id)
            if not run:
                yield f"data: {json.dumps({'type': 'error', 'content': 'run not found'})}\n\n"
                return
            payload = {
                "type": "progress",
                "status": run["status"],
                "progress": run.get("progress") or {},
                "candidate_count": run.get("candidate_count", 0),
            }
            if payload != last_payload:
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                last_payload = payload
            if run["status"] in ("done", "failed", "canceled"):
                yield (
                    "data: "
                    + json.dumps({
                        "type": "final",
                        "status": run["status"],
                        "candidate_count": run.get("candidate_count", 0),
                        "error": run.get("error"),
                    }, ensure_ascii=False)
                    + "\n\n"
                )
                yield "data: [DONE]\n\n"
                return
            await asyncio.sleep(_STREAM_INTERVAL_S)
        # Hit the ceiling without terminating — let the client fall back to polling.
        yield f"data: {json.dumps({'type': 'timeout'})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")


def _fit_kids(candidate: Dict[str, Any], kids: List[Dict[str, Any]]) -> List[str]:
    """Which of the family's kids fit this activity, by age. Deterministic and
    more reliable than the agent's single best-guess kid_name — a camp can fit
    multiple kids (e.g. ages 4-10 fits both an 8yo and a 4yo)."""
    amin = candidate.get("age_min")
    amax = candidate.get("age_max")
    # No age bounds to check → defer to the agent's pick, else everyone.
    if amin is None and amax is None:
        kn = candidate.get("kid_name")
        return [kn] if kn else [k["name"] for k in kids if k.get("name")]
    fits: List[str] = []
    for k in kids:
        name = k.get("name")
        age = k.get("age")
        if not name or age is None:
            continue
        try:
            age = float(age)
        except (TypeError, ValueError):
            continue
        if amin is not None and age < amin:
            continue
        if amax is not None and age > amax:
            continue
        fits.append(name)
    # Nothing matched by age but the agent named a kid → trust it as a fallback.
    if not fits and candidate.get("kid_name"):
        fits = [candidate["kid_name"]]
    return fits


@router.get("/runs/{run_id}/candidates")
def run_candidates(
    run_id: str,
    kid_name: Optional[str] = None,
    category: Optional[str] = None,
    user_id: str = Depends(current_user),
):
    storage = _storage()
    _require_owned_run(storage, run_id, user_id)
    candidates = storage.list_candidates(run_id=run_id, kid_name=kid_name, category=category)
    _, kids = _location_and_kids_from_profile(user_id)
    for c in candidates:
        c["fit_kids"] = _fit_kids(c, kids)
    return {"candidates": candidates}


@router.post("/runs/{run_id}/cancel")
def cancel_run(run_id: str, user_id: str = Depends(current_user)):
    storage = _storage()
    run = _require_owned_run(storage, run_id, user_id)
    if run["status"] in ("queued", "running"):
        storage.update_research_run(
            run_id, status="canceled", progress={"phase": "canceled"}, finished=True
        )
    return {"run_id": run_id, "status": "canceled"}
