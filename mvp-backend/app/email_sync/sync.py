"""Per-user Gmail sync — the unit of work the R3 daemon runs."""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

_REGISTERED = ("confirmed", "signed_up")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_SYNC_WINDOW = "newer_than:14d"


def _kids_for(user_id: str) -> List[Dict[str, Any]]:
    from app.profiling import profiling_service

    fam = profiling_service.get_family_profile(user_id) or {}
    return [
        {"name": (p or {}).get("name") or name, "age": (p or {}).get("age")}
        for name, p in (fam.get("children") or {}).items()
    ]


def _match_tokens(contact: Optional[Dict[str, Any]]) -> Set[str]:
    """Lowercased email + domain a sender must match to belong to this activity."""
    email = ((contact or {}).get("email") or "").strip().lower()
    tokens: Set[str] = set()
    if email and "@" in email:
        tokens.add(email)
        tokens.add(email.split("@", 1)[1])
    return tokens


def _sender_tokens(sender: Optional[str]) -> Set[str]:
    m = _EMAIL_RE.search(sender or "")
    if not m:
        return set()
    addr = m.group(0).lower()
    return {addr, addr.split("@", 1)[1]}


def run_email_sync(
    storage: Any,
    user_id: str,
    *,
    provider: Any = None,
    on_progress: Optional[Any] = None,
) -> Dict[str, Any]:
    """Sync one user's Gmail against their registered camps. Returns
    `{messages_seen, activities_touched, detail}` where `detail` records the
    search (the Gmail query + accounts) and per-message results — surfaced in the
    CMS run-detail view. `provider` may be injected for tests."""
    detail: Dict[str, Any] = {
        "account_email": None,
        "query": None,
        "note": None,
        "items": [],
    }
    acct = storage.get_integration_account(user_id, "google", "email")
    if not acct or acct.get("status") != "connected":
        detail["note"] = "no connected Gmail account"
        return {"messages_seen": 0, "activities_touched": 0, "detail": detail}
    detail["account_email"] = acct.get("account_email")

    # Build the per-activity match tokens (email/domain → activity id) + names.
    registered = [
        a for a in storage.list_tracked_activities(user_id)
        if (a.get("status") or "") in _REGISTERED
    ]
    names = {a["id"]: a.get("name") for a in registered}
    matchers: List[Tuple[str, Set[str]]] = [
        (a["id"], _match_tokens(a.get("contact"))) for a in registered
    ]
    matchers = [(aid, toks) for aid, toks in matchers if toks]
    if not matchers:
        detail["note"] = (
            "no registered camps with a contact email to search "
            f"({len(registered)} registered activit(y/ies))"
        )
        storage.mark_integration_synced(acct["id"])
        return {"messages_seen": 0, "activities_touched": 0, "detail": detail}

    if provider is None:
        provider = _build_provider(acct)

    all_tokens = sorted({t for _, toks in matchers for t in toks})
    query = f"from:({' OR '.join(all_tokens)}) {_SYNC_WINDOW}"
    detail["query"] = query

    kids = _kids_for(user_id)
    from app.ingest import extract as ingest_extract

    messages_seen = 0
    touched_activities: Set[str] = set()
    for msg in provider.list_messages(query=query, max_results=50):
        if not msg.id:
            continue
        # Idempotency: skip already-ingested messages.
        if storage.get_ingest_artifact_by_external(user_id, msg.id):
            detail["items"].append({
                "sender": msg.sender, "subject": msg.subject,
                "matched": None, "action": "skipped_duplicate",
            })
            continue

        full = provider.fetch_message(msg.id)
        body = full.body_text or full.snippet or ""
        activity_id = _match_message(full.sender, matchers)

        artifact_id = storage.insert_ingest_artifact(
            user_id,
            source="gmail",
            media_type="text",
            subject=full.subject,
            sender=full.sender,
            received_at=full.received_at,
            raw_text=body,
            external_id=msg.id,
        )
        messages_seen += 1
        item: Dict[str, Any] = {
            "sender": full.sender, "subject": full.subject,
            "received_at": full.received_at,
            "matched": names.get(activity_id) if activity_id else None,
        }
        try:
            extracted = ingest_extract.extract_from_text(
                body, source_hint="gmail", cost_user=user_id
            )
            made = ingest_extract.materialize(
                storage, user_id, artifact_id, extracted,
                kids=kids, link_activity_id=activity_id,
            )
            if activity_id:
                touched_activities.add(activity_id)
            item["action"] = "ingested"
            item["created"] = {
                "calendar": len(made.get("calendar_ids") or []),
                "todos": len(made.get("todo_ids") or []),
            }
        except Exception as exc:  # noqa: BLE001 — one bad email shouldn't abort the run
            logger.warning("[email-sync] extract/materialize failed for %s: %s", msg.id, exc)
            storage.update_ingest_extraction(artifact_id, extract_status="failed")
            item["action"] = "extract_failed"
            item["error"] = str(exc)[:200]
        detail["items"].append(item)

        if on_progress:
            try:
                on_progress(messages_seen)
            except Exception:  # noqa: BLE001
                pass

    if messages_seen == 0 and not detail["note"]:
        detail["note"] = "no new emails from your camps in the last 14 days"
    storage.mark_integration_synced(acct["id"])
    return {
        "messages_seen": messages_seen,
        "activities_touched": len(touched_activities),
        "detail": detail,
    }


def _match_message(sender: Optional[str], matchers: List[Tuple[str, Set[str]]]) -> Optional[str]:
    stoks = _sender_tokens(sender)
    if not stoks:
        return None
    for activity_id, toks in matchers:
        if stoks & toks:
            return activity_id
    return None


def _build_provider(acct: Dict[str, Any]) -> Any:
    from app.integrations.base import OAuthCredentials
    from app.integrations.crypto import decrypt_token
    from app.integrations.registry import get_email_provider

    creds = OAuthCredentials(
        refresh_token=decrypt_token(acct["encrypted_refresh_token"]),
        scopes=(acct.get("scopes") or "").split(),
        account_email=acct.get("account_email"),
        client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    )
    return get_email_provider("google", creds)
