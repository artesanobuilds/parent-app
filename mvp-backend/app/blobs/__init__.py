"""Blob storage on Railway Storage Buckets (S3-compatible), for profile photos
and (later) ingest images.

Env-gated no-op like app.push: a complete no-op until the BLOB_* vars are set,
so local dev and tests never touch a real bucket — and, deliberately, a dev box
CANNOT reach prod photos (the prod bucket is attached only to the prod
service). Railway injects generic names (BUCKET, ACCESS_KEY_ID, ...); map them
to the BLOB_* aliases in Railway variable refs to avoid collisions.

Buckets are private-only: every read is a presigned GET minted at request time
(store the KEY, never a presigned URL — a stored URL bakes in an expiry and
leaks a capability into the parquet snapshots). Railway buckets have no
prefix-delete and no lifecycle rules, so delete_all() lists + batch-deletes,
and orphan cleanup is an app-level concern (roadmap).
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Mirrors the ingest allowlist (app/ingest/router.py) — one image policy.
ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB

_EXT_FOR_MIME = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/heic": "heic",
    "image/heif": "heif",
}

ALLOWED_KINDS = ("avatar", "ingest")

_client_cache: Optional[Any] = None


def is_configured() -> bool:
    return bool(
        os.getenv("BLOB_BUCKET")
        and os.getenv("BLOB_ACCESS_KEY_ID")
        and os.getenv("BLOB_SECRET_ACCESS_KEY")
        and os.getenv("BLOB_ENDPOINT")
    )


def bucket_name() -> Optional[str]:
    return os.getenv("BLOB_BUCKET")


def _presign_ttl() -> int:
    try:
        return int(os.getenv("BLOB_PRESIGN_TTL_S", "900"))
    except ValueError:
        return 900


def _client():
    """Lazy boto3 client so the dependency is only touched when configured."""
    global _client_cache
    if _client_cache is None:
        import boto3

        _client_cache = boto3.client(
            "s3",
            endpoint_url=os.getenv("BLOB_ENDPOINT"),
            region_name=os.getenv("BLOB_REGION", "auto"),
            aws_access_key_id=os.getenv("BLOB_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("BLOB_SECRET_ACCESS_KEY"),
        )
    return _client_cache


def reset_client_for_tests() -> None:
    global _client_cache
    _client_cache = None


def new_key(*, user_id: str, kind: str, content_type: str) -> str:
    """Server-derived object key. The user_id prefix is the ownership boundary:
    attach endpoints verify it and delete_all() sweeps it. NEVER accept a
    client-supplied key."""
    if kind not in ALLOWED_KINDS:
        raise ValueError(f"unknown blob kind: {kind}")
    ext = _EXT_FOR_MIME.get(content_type, "bin")
    return f"u/{user_id}/{kind}/{uuid.uuid4().hex}.{ext}"


def key_belongs_to(key: str, user_id: str) -> bool:
    return key.startswith(f"u/{user_id}/")


def presign_put(key: str, content_type: str) -> str:
    return _client().generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket_name(), "Key": key, "ContentType": content_type},
        ExpiresIn=_presign_ttl(),
    )


def presign_get(key: str) -> Optional[str]:
    if not is_configured():
        return None
    try:
        return _client().generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name(), "Key": key},
            ExpiresIn=_presign_ttl(),
        )
    except Exception:
        logger.exception("[blobs] presign_get failed for %s", key)
        return None


def head(key: str) -> Optional[Dict[str, Any]]:
    """Object metadata, or None if it doesn't exist."""
    try:
        resp = _client().head_object(Bucket=bucket_name(), Key=key)
        return {"size": resp.get("ContentLength", 0), "content_type": resp.get("ContentType")}
    except Exception:
        return None


def delete(key: str) -> None:
    if not is_configured():
        return
    try:
        _client().delete_object(Bucket=bucket_name(), Key=key)
    except Exception:
        logger.exception("[blobs] delete failed for %s", key)


def delete_all(prefix: str) -> int:
    """Delete every object under a prefix (list + batch-delete — Railway
    buckets have no native prefix delete). Returns the count removed. Used by
    delete_family so the data-deletion promise covers photos."""
    if not is_configured():
        return 0
    deleted = 0
    try:
        client = _client()
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket_name(), Prefix=prefix):
            keys: List[Dict[str, str]] = [
                {"Key": obj["Key"]} for obj in page.get("Contents", [])
            ]
            if keys:
                client.delete_objects(Bucket=bucket_name(), Delete={"Objects": keys})
                deleted += len(keys)
    except Exception:
        logger.exception("[blobs] delete_all failed for prefix %s", prefix)
    return deleted
