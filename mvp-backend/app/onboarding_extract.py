"""
Pre-account onboarding extraction (Heisman sprint-01, step 04).

The parent hands the coach a real-world scrap — freeform text, a dictated
transcript, or a photo of a flyer — BEFORE an account exists, and gets back
structured {who, what, when, where} activity cards for the "Check my work"
screen. Everything here is deliberately STATELESS: no user_id, no DB rows, no
blob writes. The client keeps the result in its onboarding draft and seeds it
through /profile/seed after account creation, so there is nothing server-side
to expire or clean up.

Auth model — scoped anonymous token, NOT an account:
  POST /onboarding/anon-session (IP rate-limited, "auth" class) mints a
  short-lived HS256 JWT whose payload carries `scope=onboarding_extract` and
  an `aid` correlation id but NO `sub` claim. `app.auth.current_user` resolves
  users via `sub`, so this token can never authenticate against any user
  endpoint — the scope check here is the only door it opens.

Abuse posture: per-session AND per-IP "extract" buckets (see rate_limit.py),
hard size caps, kill switch ONBOARDING_EXTRACT_ENABLED, one [COST][LLM] line
per call via cost_config (user=anon:<aid> so spend is greppable).
"""
from __future__ import annotations

import base64
import logging
import os
import time
import uuid
from typing import List, Optional

import jwt
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.auth import _jwt_secret  # one signing secret for the whole app
from app.rate_limit import enforce as rate_limit_enforce

logger = logging.getLogger(__name__)

router = APIRouter()

_JWT_ALG = "HS256"
_SCOPE = "onboarding_extract"
_SESSION_TTL_SECONDS = int(os.getenv("ONBOARDING_EXTRACT_SESSION_TTL_MIN", "60")) * 60

_MAX_TEXT_CHARS = 8_000
_MAX_IMAGE_BYTES = 8 * 1024 * 1024  # decoded size
_ALLOWED_MEDIA_TYPES = {"image/jpeg", "image/png", "image/heic", "image/webp"}


def _enabled() -> bool:
    return os.getenv("ONBOARDING_EXTRACT_ENABLED", "1").lower() in ("1", "true", "yes")


# ── Anonymous session token ──────────────────────────────────────────────────

def mint_anon_session_token() -> tuple[str, int]:
    """Return (jwt, expires_in_seconds). No `sub` — see module docstring."""
    now = int(time.time())
    payload = {
        "scope": _SCOPE,
        "aid": uuid.uuid4().hex,
        "iat": now,
        "exp": now + _SESSION_TTL_SECONDS,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=_JWT_ALG), _SESSION_TTL_SECONDS


def _decode_anon_session_token(token: str) -> Optional[str]:
    """Return the session's `aid` when the token is valid + correctly scoped."""
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[_JWT_ALG])
    except jwt.PyJWTError:
        return None
    if payload.get("scope") != _SCOPE:
        return None
    aid = payload.get("aid")
    return aid if isinstance(aid, str) and aid else None


# ── Models ───────────────────────────────────────────────────────────────────

class AnonSessionResponse(BaseModel):
    token: str
    expires_in: int


class ExtractRequest(BaseModel):
    text: Optional[str] = None
    image_b64: Optional[str] = None
    media_type: Optional[str] = None  # required alongside image_b64


class ExtractedActivity(BaseModel):
    who: str = Field(description="The person the activity is for — a child's first name if stated, else 'your kid' / 'you'.")
    what: str = Field(description="The activity, short noun phrase, e.g. 'Swim lessons'.")
    when: str = Field(description="Human schedule, e.g. 'Tuesdays · 4:15 pm'. Empty string if the source doesn't say.")
    where: str = Field(description="Venue/location as written, e.g. 'Northgate Aquatic Center'. Empty string if absent.")
    notes: str = Field(default="", description="One short clause of extra load-bearing detail (price, deadline, what to bring). Empty if none.")


class _Extraction(BaseModel):
    """Structured-output schema for the model."""
    activities: List[ExtractedActivity] = Field(
        description="Every distinct scheduled activity/commitment found in the input. Empty when the input contains none.")


class ExtractResponse(BaseModel):
    activities: List[ExtractedActivity]


_SYSTEM_PROMPT = (
    "You extract structured family-logistics data for a parenting app's onboarding. "
    "The input is a real-world scrap a parent received — a group-text message, an email, "
    "or a photographed flyer/schedule. Pull out every distinct activity or commitment as "
    "{who, what, when, where, notes}. Rules: copy names, times, and venues as written — "
    "never invent a detail the source doesn't contain; leave a field an empty string when "
    "the source is silent. 'who' is the child's first name when stated. Ignore ads, "
    "boilerplate, and anything that isn't a schedulable commitment. If the input has no "
    "extractable activities, return an empty list."
)


# ── Routes ───────────────────────────────────────────────────────────────────

def _client_ip(request: Request) -> str:
    from app.server import client_ip_for
    return client_ip_for(request)


@router.post("/onboarding/anon-session", response_model=AnonSessionResponse)
def create_anon_session(request: Request) -> AnonSessionResponse:
    if not _enabled():
        raise HTTPException(status_code=503, detail="extraction disabled")
    # Same class as token issuance: unauthenticated mint endpoints share the
    # hard per-IP "auth" budget.
    rate_limit_enforce(f"ip:{_client_ip(request)}", "auth")
    token, expires_in = mint_anon_session_token()
    return AnonSessionResponse(token=token, expires_in=expires_in)


@router.post("/onboarding/extract", response_model=ExtractResponse)
def extract(
    body: ExtractRequest,
    request: Request,
    authorization: str = Header(default=""),
) -> ExtractResponse:
    if not _enabled():
        raise HTTPException(status_code=503, detail="extraction disabled")

    token = authorization.removeprefix("Bearer ").strip()
    aid = _decode_anon_session_token(token) if token else None
    if aid is None:
        raise HTTPException(status_code=401, detail="valid anon session token required")

    # Per-session and per-IP budgets both apply.
    rate_limit_enforce(f"anon:{aid}", "extract")
    rate_limit_enforce(f"ip:{_client_ip(request)}", "extract")

    text = (body.text or "").strip()
    if len(text) > _MAX_TEXT_CHARS:
        raise HTTPException(status_code=413, detail=f"text over {_MAX_TEXT_CHARS} chars")

    image_bytes: Optional[bytes] = None
    media_type = (body.media_type or "").strip().lower()
    if body.image_b64:
        if media_type not in _ALLOWED_MEDIA_TYPES:
            raise HTTPException(status_code=422, detail=f"media_type must be one of {sorted(_ALLOWED_MEDIA_TYPES)}")
        try:
            image_bytes = base64.b64decode(body.image_b64, validate=True)
        except Exception:
            raise HTTPException(status_code=422, detail="image_b64 is not valid base64")
        if len(image_bytes) > _MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail=f"image over {_MAX_IMAGE_BYTES} bytes")

    if not text and image_bytes is None:
        raise HTTPException(status_code=422, detail="provide text and/or image_b64")

    user_content: list = []
    if text:
        user_content.append({"type": "text", "text": text})
    if image_bytes is not None:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{media_type};base64,{body.image_b64}"},
        })

    from app.agent import llm
    from app.cost_logging import cost_config

    try:
        result = llm.with_structured_output(_Extraction).invoke(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            config=cost_config("onboarding_extract", user=f"anon:{aid}"),
        )
    except Exception:
        logger.exception("[extract] model call failed (aid=%s)", aid)
        raise HTTPException(status_code=502, detail="extraction failed — try again")

    activities = list(getattr(result, "activities", []) or [])
    logger.info("[extract] aid=%s text_chars=%d image=%s activities=%d",
                aid, len(text), image_bytes is not None, len(activities))
    return ExtractResponse(activities=activities)
