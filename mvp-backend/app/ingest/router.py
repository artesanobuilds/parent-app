"""
Multimodal ingestion API (Phase 3): paste text or upload a photo, get back the
structured extraction plus the pending activity / to-dos / calendar entries it
spawned.

Follows the app's conventions: `current_user` resolves the bearer token,
`authorize_user_match` blocks cross-user access, `enforce` rate-limits. Storage
is imported lazily inside handlers to avoid an import cycle with app.server.
"""
from __future__ import annotations

import base64
import binascii
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.auth import current_user, authorize_user_match
from app.rate_limit import enforce as rate_limit_enforce

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])

# Vision images add cost and DuckDB blobs aren't stored — cap upload size.
_MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB
_ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}


def _storage():
    from app.server import storage_backend

    return storage_backend


def _kids_from_profile(user_id: str) -> List[Dict[str, Any]]:
    from app.research.router import _location_and_kids_from_profile

    _, kids = _location_and_kids_from_profile(user_id)
    return kids


class IngestTextRequest(BaseModel):
    user_id: str
    text: str
    source: str = "paste"  # paste|imessage|forward|gmail
    subject: Optional[str] = None
    sender: Optional[str] = None


def _materialize_response(
    storage: Any, user_id: str, artifact_id: str, extracted: Any, created: Dict[str, Any]
) -> Dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "extract_status": "extracted",
        "extracted": extracted.model_dump(),
        "created": created,
    }


@router.post("/text")
def ingest_text(req: IngestTextRequest, user_id: str = Depends(current_user)):
    """Paste an email / forwarded iMessage → structured extraction + pending
    activity/to-dos/calendar. Single LLM call → 'chat' rate bucket."""
    authorize_user_match(authenticated=user_id, claimed=req.user_id)
    rate_limit_enforce(user_id, "chat")
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is empty")

    from app.ingest import extract as ingest_extract

    storage = _storage()
    artifact_id = storage.insert_ingest_artifact(
        user_id,
        source=req.source,
        media_type="text",
        subject=req.subject,
        sender=req.sender,
        raw_text=req.text,
    )
    try:
        extracted = ingest_extract.extract_from_text(
            req.text, source_hint=req.source, cost_user=user_id
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[ingest/text] extraction failed: %s", exc)
        storage.update_ingest_extraction(artifact_id, extract_status="failed")
        raise HTTPException(status_code=502, detail="extraction failed")

    created = ingest_extract.materialize(
        storage, user_id, artifact_id, extracted, kids=_kids_from_profile(user_id)
    )
    return _materialize_response(storage, user_id, artifact_id, extracted, created)


@router.post("/image")
async def ingest_image(
    user_id_form: str = Form(..., alias="user_id"),
    source: str = Form("photo"),
    caption: Optional[str] = Form(None),
    file: UploadFile = File(...),
    user_id: str = Depends(current_user),
):
    """Upload a flyer / signed-form / screenshot photo → vision extraction +
    pending activity/to-dos/calendar. Single vision call → 'chat' rate bucket."""
    authorize_user_match(authenticated=user_id, claimed=user_id_form)
    rate_limit_enforce(user_id, "chat")

    mime = (file.content_type or "").lower()
    if mime not in _ALLOWED_IMAGE_MIME:
        raise HTTPException(
            status_code=415, detail=f"unsupported image type: {mime or 'unknown'}"
        )
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="empty file")
    if len(raw) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="image too large (max 8 MB)")

    try:
        image_b64 = base64.b64encode(raw).decode("ascii")
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="could not encode image")

    from app.ingest import extract as ingest_extract

    storage = _storage()
    artifact_id = storage.insert_ingest_artifact(
        user_id,
        source=source,
        media_type="image",
        subject=file.filename,
    )
    try:
        extracted = ingest_extract.extract_from_image(
            image_b64, mime_type=mime, caption=caption, cost_user=user_id
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[ingest/image] vision extraction failed: %s", exc)
        storage.update_ingest_extraction(artifact_id, extract_status="failed")
        raise HTTPException(status_code=502, detail="extraction failed")

    created = ingest_extract.materialize(
        storage, user_id, artifact_id, extracted, kids=_kids_from_profile(user_id)
    )
    return _materialize_response(storage, user_id, artifact_id, extracted, created)


@router.get("/artifacts")
def list_artifacts(
    status: Optional[str] = None,
    user_id: str = Depends(current_user),
):
    return {"artifacts": _storage().list_ingest_artifacts(user_id, status=status)}


@router.get("/artifacts/{artifact_id}")
def get_artifact(artifact_id: str, user_id: str = Depends(current_user)):
    artifact = _storage().get_ingest_artifact(artifact_id, user_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="artifact not found")
    return artifact
