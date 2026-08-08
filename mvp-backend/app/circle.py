"""Circle conversations + invites (beta-v1 Phase 1).

The anonymous community board is gone. Circle is now *your actual people*, and
this module owns the threads you have with them.

Three decisions worth knowing before editing:

1. **A new model, not a widened DM.** The retired `dm_conversations` table was
   structurally 1:1 — a UNIQUE index on the canonically ordered participant
   pair — so a third participant had nowhere to go. Circle threads get their
   own tables with an explicit participant list. (The DM tables were dropped in
   migration v21; this module is their only successor.)

2. **ONE guard.** Every route below funnels through `_conversation_or_404`.
   Scoping that lives in more than one place is scoping that eventually
   diverges — and this is the surface where divergence means one family reads
   another's thread. Failure is 404, never 403: a 403 confirms the conversation
   exists.

3. **Mutual links only.** Adding a participant who already has an MVP account
   requires that account to be in the owner's Circle per
   `storage.circle_peer_ids` — which is mutual by construction. Without that
   rule, anyone could type a stranger's `user_id` into their own roster, add
   them to a thread, and read whatever they replied. An UNCLAIMED member (no
   account yet) may be added freely, because an unclaimed participant row has
   `user_id IS NULL` and matches nobody until they claim an invite.

Claiming an invite is what turns a one-sided roster entry into a real mutual
link: it binds `household_members.member_user_id` on BOTH sides and fills in
the pending `circle_participants.user_id` rows for that member.
"""
from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/circle", tags=["circle"])

# The invite link's base. It lives here and ONLY here, so changing it is one env
# var rather than a grep across three surfaces.
#
# Default = the Railway host the whole app already runs on, pointing at the
# dashboard SPA (Vite `base: '/dashboard/'`, BrowserRouter `basename="/dashboard"`),
# which is what actually serves the claim page. Deliberately NOT
# `share.mvparent.ai` as the sprint-2 mockup draws: that domain is unregistered,
# so every link minted against it would be dead on arrival. The vanity domain
# (`most-valuable-parent.com` is owned; `mvparent.ai` is not) is a product
# decision that can land later by setting the env var — no code change, because
# this is read at call time.
#
# An invite link is IRREVERSIBLE once a parent forwards it, so the default has to
# be a host that resolves today rather than one that might later.
INVITE_BASE_URL_ENV = "CIRCLE_INVITE_BASE_URL"
DEFAULT_INVITE_BASE_URL = (
    "https://mvp-backend-production-8678.up.railway.app/dashboard/invite"
)

INVITE_TTL_DAYS = 14

MAX_TITLE_CHARS = 200
MAX_BODY_CHARS = 8000
MAX_PARTICIPANTS = 25


def invite_base_url() -> str:
    """Read at call time (not import time) so a deploy can change it without a
    code change, and so tests can monkeypatch the env."""
    return (os.getenv(INVITE_BASE_URL_ENV) or DEFAULT_INVITE_BASE_URL).rstrip("/")


def _storage():
    # Lazy: app.server imports this module, and TestClient teardown rebinds
    # server.storage_backend (see tests/test_household_members.py).
    from app.server import storage_backend

    return storage_backend


def _display_name(user_id: Optional[str]) -> Optional[str]:
    if not user_id:
        return None
    from app.server import _display_name_for_user

    try:
        return _display_name_for_user(user_id)
    except Exception:  # noqa: BLE001
        logger.warning("[circle] display name lookup failed", exc_info=True)
        return None


def _initials(name: str) -> str:
    words = (name or "").strip().split()
    return "".join(w[0].upper() for w in words[:2]) if words else "?"


def _track(event: str, user_id: str, props: Optional[Dict[str, Any]] = None) -> None:
    """Fire-and-forget product analytics. Circle carries private family
    conversation, so ONLY the lifecycle fact is captured — never a title, body,
    participant list, or count of who is in the thread (see
    app/analytics/events.py's allowlist + denylist)."""
    try:
        from app.analytics import capture

        capture(event, user_id, props or {})
    except Exception:  # noqa: BLE001
        logger.debug("[circle] analytics capture failed (non-fatal)", exc_info=True)


def _self_member_id(user_id: str) -> str:
    """The owner's own participant handle. A parent has no `household_members`
    row for themselves, so the participant key is synthesized from the stable
    account id (never from a display name — CLAUDE.md)."""
    return f"self:{user_id}"


# --------------------------------------------------------------------------- #
# Request bodies
# --------------------------------------------------------------------------- #


class ConversationCreate(BaseModel):
    title: str
    body: Optional[str] = None
    member_ids: List[str] = []


class ConversationPatch(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None


class MessageCreate(BaseModel):
    body: str


class ParticipantsAdd(BaseModel):
    member_ids: List[str] = []


class InviteCreate(BaseModel):
    member_id: Optional[str] = None


# --------------------------------------------------------------------------- #
# Wire shapes — every key ALWAYS present (iOS Codable is strict: one missing or
# mistyped field empties the whole list).
# --------------------------------------------------------------------------- #


def _participant_out(row: Dict[str, Any], member_index: Dict[str, Dict[str, Any]],
                     owner_user_id: str) -> Dict[str, Any]:
    member = member_index.get(row.get("member_id") or "")
    name = (member or {}).get("display_name") or ""
    if not name:
        # Owner (no roster row for yourself) or a member owned by someone else.
        name = _display_name(row.get("user_id")) or "A parent"
    return {
        "user_id": row.get("user_id"),
        "member_id": row.get("member_id"),
        "display_name": name,
        "initials": _initials(name),
    }


def _conversation_out(conv: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    storage = _storage()
    conv_id = conv["id"]
    owner_user_id = conv["owner_user_id"]

    participants = storage.list_circle_participants(conv_id)
    # Names come from the OWNER's roster — the owner is the one who typed them
    # in, and a participant who is not yet an account has no other source.
    member_index = {
        m["id"]: m for m in storage.list_household_members(owner_user_id)
    }
    stats = storage.circle_message_stats(conv_id)
    starter_name = _display_name(owner_user_id) or "A parent"

    return {
        "id": conv_id,
        "title": conv.get("title") or "",
        "body": conv.get("body") or "",
        "owner_user_id": owner_user_id,
        "created_at": conv.get("created_at"),
        "last_reply_at": conv.get("last_reply_at"),
        "reply_count": stats["reply_count"],
        "last_reply_from": stats["last_reply_from"],
        "starter_name": starter_name,
        "starter_is_me": owner_user_id == user_id,
        "unread": storage.circle_unread_count(conv_id, user_id),
        "participants": [
            _participant_out(p, member_index, owner_user_id) for p in participants
        ],
    }


def _message_out(row: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    name = row.get("author_name") or "A parent"
    return {
        "id": row.get("id"),
        "user_id": row.get("user_id"),
        "author_name": name,
        "initials": row.get("initials") or _initials(name),
        "body": row.get("body") or "",
        "created_at": row.get("created_at"),
        "is_me": row.get("user_id") == user_id,
    }


# --------------------------------------------------------------------------- #
# The guard — the single trust boundary
# --------------------------------------------------------------------------- #


def _conversation_or_404(conversation_id: str, user_id: str) -> Dict[str, Any]:
    """Participant guard. Every /circle/conversations* route funnels through
    this, so scoping cannot be bypassed by calling a different route.

    Membership is a `circle_participants` row whose `user_id` IS this caller —
    an unclaimed row (user_id NULL) grants nothing. 404 rather than 403 so the
    response does not confirm the conversation exists."""
    storage = _storage()
    conv = storage.get_circle_conversation(conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if storage.get_circle_participant(conversation_id, user_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


def _owned_conversation_or_404(conversation_id: str, user_id: str) -> Dict[str, Any]:
    """Owner-only actions (edit / delete / add participants) still go through
    the participant guard FIRST, so a non-participant learns nothing."""
    conv = _conversation_or_404(conversation_id, user_id)
    if conv["owner_user_id"] != user_id:
        raise HTTPException(status_code=403, detail="only the owner can do that")
    return conv


def _resolve_members(member_ids: List[str], user_id: str) -> List[Dict[str, Any]]:
    """Turn the client's member ids into addable participants.

    Two rules, both load-bearing:
      • The member row must belong to the CALLER — you can only invite people
        from your own roster.
      • If that member already has an MVP account, the link must be MUTUAL
        (`circle_peer_ids`). Otherwise adding a stranger's user_id to your own
        roster would let you read whatever they replied.
    """
    storage = _storage()
    if len(member_ids) > MAX_PARTICIPANTS:
        raise HTTPException(status_code=400,
                            detail=f"at most {MAX_PARTICIPANTS} participants")
    circle = set(storage.circle_peer_ids(user_id))
    out: List[Dict[str, Any]] = []
    for member_id in member_ids:
        member = storage.get_household_member(member_id)
        if member is None or member.get("user_id") != user_id:
            raise HTTPException(status_code=404, detail=f"member {member_id} not found")
        linked = member.get("member_user_id")
        if linked and linked not in circle:
            raise HTTPException(
                status_code=403,
                detail=f"{member.get('display_name') or 'that member'} has not "
                       "accepted your Circle invite yet — the link has to be "
                       "mutual before you can add them to a conversation",
            )
        out.append(member)
    return out


# --------------------------------------------------------------------------- #
# Conversation routes
# --------------------------------------------------------------------------- #


@router.get("/conversations")
def list_conversations(user_id: str = Depends(current_user)):
    convs = _storage().list_circle_conversations_for_user(user_id)
    return {"conversations": [_conversation_out(c, user_id) for c in convs]}


@router.post("/conversations")
def create_conversation(body: ConversationCreate, user_id: str = Depends(current_user)):
    title = (body.title or "").strip()[:MAX_TITLE_CHARS]
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    members = _resolve_members(list(body.member_ids or []), user_id)

    storage = _storage()
    conv_id = storage.create_circle_conversation(
        user_id, title=title, body=(body.body or "").strip()[:MAX_BODY_CHARS] or None
    )
    storage.add_circle_participant(
        conv_id, member_id=_self_member_id(user_id), user_id=user_id, role="owner"
    )
    for member in members:
        storage.add_circle_participant(
            conv_id, member_id=member["id"], user_id=member.get("member_user_id")
        )
    _track("circle_conversation_started", user_id, {"source": "circle"})
    return _conversation_out(storage.get_circle_conversation(conv_id), user_id)


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str, user_id: str = Depends(current_user)):
    conv = _conversation_or_404(conversation_id, user_id)
    messages = _storage().list_circle_messages(conversation_id)
    return {
        "conversation": _conversation_out(conv, user_id),
        "messages": [_message_out(m, user_id) for m in messages],
    }


@router.patch("/conversations/{conversation_id}")
def patch_conversation(conversation_id: str, body: ConversationPatch,
                       user_id: str = Depends(current_user)):
    _owned_conversation_or_404(conversation_id, user_id)
    sent = body.model_dump(exclude_unset=True)
    fields: Dict[str, Any] = {}
    if "title" in sent:
        title = (sent["title"] or "").strip()[:MAX_TITLE_CHARS]
        if not title:
            raise HTTPException(status_code=400, detail="title cannot be empty")
        fields["title"] = title
    if "body" in sent:
        fields["body"] = (sent["body"] or "").strip()[:MAX_BODY_CHARS] or None
    storage = _storage()
    storage.update_circle_conversation(conversation_id, fields)
    return _conversation_out(storage.get_circle_conversation(conversation_id), user_id)


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, user_id: str = Depends(current_user)):
    _owned_conversation_or_404(conversation_id, user_id)
    _storage().delete_circle_conversation(conversation_id)
    return {"ok": True}


@router.post("/conversations/{conversation_id}/messages")
def post_message(conversation_id: str, body: MessageCreate,
                 user_id: str = Depends(current_user)):
    _conversation_or_404(conversation_id, user_id)
    text = (body.body or "").strip()[:MAX_BODY_CHARS]
    if not text:
        raise HTTPException(status_code=400, detail="body is required")
    name = _display_name(user_id) or "A parent"
    row = _storage().add_circle_message(
        conversation_id, user_id=user_id, body=text,
        author_name=name, initials=_initials(name),
    )
    _track("circle_message_sent", user_id)
    return _message_out(row, user_id)


@router.post("/conversations/{conversation_id}/participants")
def add_participants(conversation_id: str, body: ParticipantsAdd,
                     user_id: str = Depends(current_user)):
    _owned_conversation_or_404(conversation_id, user_id)
    members = _resolve_members(list(body.member_ids or []), user_id)
    storage = _storage()
    for member in members:
        storage.add_circle_participant(
            conversation_id, member_id=member["id"],
            user_id=member.get("member_user_id"),
        )
    return _conversation_out(storage.get_circle_conversation(conversation_id), user_id)


@router.post("/conversations/{conversation_id}/read")
def mark_read(conversation_id: str, user_id: str = Depends(current_user)):
    _conversation_or_404(conversation_id, user_id)
    _storage().mark_circle_conversation_read(conversation_id, user_id)
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Invites — how a Circle link becomes mutual
# --------------------------------------------------------------------------- #


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _invite_expired(invite: Dict[str, Any]) -> bool:
    expires = _parse_ts(invite.get("expires_at"))
    return bool(expires and expires <= datetime.now(timezone.utc))


@router.post("/invites")
def create_invite(body: InviteCreate, user_id: str = Depends(current_user)):
    """Mint a share link. `member_id` binds the invite to a roster row, so
    claiming it links that specific person; an open invite (no member_id)
    creates the roster row at claim time."""
    storage = _storage()
    member_id = body.member_id or None
    if member_id is not None:
        member = storage.get_household_member(member_id)
        if member is None or member.get("user_id") != user_id:
            raise HTTPException(status_code=404, detail="member not found")
    token = secrets.token_urlsafe(24)
    invite = storage.create_invite_token(
        user_id, member_id=member_id, token=token, ttl_days=INVITE_TTL_DAYS
    )
    return {
        "token": token,
        "url": f"{invite_base_url()}/{token}",
        "expires_at": invite.get("expires_at"),
    }


@router.get("/invites/{token}")
def preview_invite(token: str):
    """Unauthenticated preview — the invitee has no account yet. Deliberately
    thin: who invited you, roughly what household, and the kids' first names.
    No user ids, no emails, no roster."""
    from app.profiling import profiling_service

    storage = _storage()
    invite = storage.get_invite_token(token)
    if invite is None:
        raise HTTPException(status_code=404, detail="invite not found")

    inviter = invite["user_id"]
    inviter_name = _display_name(inviter) or "A parent"
    try:
        snapshot = profiling_service.export_snapshot().get(inviter) or {}
    except Exception:  # noqa: BLE001
        snapshot = {}
    kids = list((snapshot.get("children") or {}).keys())
    if len(kids) > 3:
        kids_label = ", ".join(kids[:3]) + f" +{len(kids) - 3}"
    else:
        kids_label = ", ".join(kids)

    return {
        "inviter_name": inviter_name,
        "household_label": f"{inviter_name.split()[0]}'s household" if inviter_name else "",
        "kids_label": kids_label,
        "expired": _invite_expired(invite),
        "claimed": invite.get("claimed_by") is not None,
    }


@router.post("/invites/{token}/claim")
def claim_invite(token: str, user_id: str = Depends(current_user)):
    """Bind the link on BOTH sides — this is the only way a Circle link becomes
    mutual without the invitee re-typing the inviter into their own roster.

      • the inviter's roster row gets `member_user_id = <claimer>`
      • the claimer gets a reciprocal roster row pointing back at the inviter
      • pending `circle_participants` rows for that member get their user_id

    After this, `circle_peer_ids` returns each for the other and every thread
    they were added to becomes readable — and not one moment before.
    """
    storage = _storage()
    invite = storage.get_invite_token(token)
    if invite is None:
        raise HTTPException(status_code=404, detail="invite not found")
    if _invite_expired(invite):
        raise HTTPException(status_code=410, detail="this invite has expired")
    if invite.get("claimed_by") and invite["claimed_by"] != user_id:
        raise HTTPException(status_code=409, detail="this invite was already used")

    inviter = invite["user_id"]
    if inviter == user_id:
        raise HTTPException(status_code=400, detail="you can't claim your own invite")

    member_id = invite.get("member_id")
    claimer_name = _display_name(user_id) or "A parent"
    if member_id:
        member = storage.get_household_member(member_id)
        if member is None or member.get("user_id") != inviter:
            raise HTTPException(status_code=404, detail="invite target no longer exists")
    else:
        # Open invite: the roster row is created now, from the claimer's own
        # account name (the inviter never typed one in).
        member_id = storage.add_household_member(
            inviter, display_name=claimer_name, role="other", kind="adult",
            notes="Joined through a Circle invite link.",
        )
    storage.update_household_member(member_id, {"member_user_id": user_id})

    # The reciprocal side. Idempotent: if the claimer already has a row
    # pointing at the inviter, reuse it rather than duplicating the person.
    reciprocal = storage.find_household_member_by_account(user_id, inviter)
    if reciprocal is None:
        inviter_name = _display_name(inviter) or "A parent"
        storage.add_household_member(
            user_id, display_name=inviter_name, role="other", kind="adult",
            member_user_id=inviter,
            notes="Linked through a Circle invite link.",
        )

    storage.bind_circle_participant_account(member_id, user_id)
    storage.claim_invite_token(token, user_id)
    return {"ok": True, "member_id": member_id, "inviter_user_id": inviter}
