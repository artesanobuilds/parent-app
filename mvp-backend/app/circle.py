"""Circle conversations + invites (beta-v1 Phase 1).

The anonymous community board is gone. Circle is now *your actual people*, and
this module owns the threads you have with them.

Five decisions worth knowing before editing:

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

4. **TWO doors into that link, ONE binding.** Sprint 2 adds the email path
   ("if that person already exists in the system, no need to invite them"), so
   the mutual link can now be established by claiming an invite OR by accepting
   a request. Both call `_bind_mutual_link` — the single implementation of "we
   are now peers". A second copy of that block is a second thing that can
   drift, on the one surface where drift means a stranger in your thread.

5. **The email lookup is not an oracle.** `POST /circle/contacts` returns the
   IDENTICAL body and status whether the email belongs to an MVP user or to
   nobody, so it cannot be used to enumerate the user base. A match creates a
   PENDING `circle_requests` row and NOTHING else — no participant row, no peer
   entry, no read access. Only the recipient's accept binds the link.

Claiming an invite (or accepting a request) is what turns a one-sided roster
entry into a real mutual link: it binds `household_members.member_user_id` on
BOTH sides and fills in the pending `circle_participants.user_id` rows for that
member.
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
from app.rate_limit import enforce

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


class ContactAdd(BaseModel):
    """Add someone to your Circle by email. `display_name` is only ever used
    for the requester's OWN roster row — it never overwrites what the other
    person calls themselves."""
    email: str
    display_name: Optional[str] = None


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
    enforce(user_id, "config")
    convs = _storage().list_circle_conversations_for_user(user_id)
    return {"conversations": [_conversation_out(c, user_id) for c in convs]}


@router.post("/conversations")
def create_conversation(body: ConversationCreate, user_id: str = Depends(current_user)):
    # A new thread is a message send in disguise (it carries the opening post),
    # so it draws on the message bucket, not config.
    enforce(user_id, "message")
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
    enforce(user_id, "config")
    conv = _conversation_or_404(conversation_id, user_id)
    messages = _storage().list_circle_messages(conversation_id)
    return {
        "conversation": _conversation_out(conv, user_id),
        "messages": [_message_out(m, user_id) for m in messages],
    }


@router.patch("/conversations/{conversation_id}")
def patch_conversation(conversation_id: str, body: ConversationPatch,
                       user_id: str = Depends(current_user)):
    enforce(user_id, "config")
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
    enforce(user_id, "config")
    _owned_conversation_or_404(conversation_id, user_id)
    _storage().delete_circle_conversation(conversation_id)
    return {"ok": True}


@router.post("/conversations/{conversation_id}/messages")
def post_message(conversation_id: str, body: MessageCreate,
                 user_id: str = Depends(current_user)):
    enforce(user_id, "message")
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
    enforce(user_id, "config")
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
    enforce(user_id, "config")
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


def _bind_mutual_link(
    holder_user_id: str,
    other_user_id: str,
    *,
    member_id: Optional[str],
    holder_note: str,
    other_note: str,
) -> str:
    """THE binding. The single implementation of "these two accounts are now
    Circle peers", called by both doors into the link (claiming an invite and
    accepting a request). Returns the holder-side member id.

    `holder_user_id` is the side that already has (or should have) a roster row
    for the other person — the inviter, or the requester. Three writes, and
    `circle_peer_ids` returns each for the other only once ALL of them land:

      • the holder's roster row gets `member_user_id = other_user_id`
        (created now if `member_id` is None — an open invite, or a request whose
        roster row was deleted before it was answered)
      • the other side gets a reciprocal roster row pointing back
      • pending `circle_participants` rows for that member get their user_id,
        so threads the holder already created become readable at this moment

    There must be exactly ONE copy of this. Two would be two things that can
    drift, on the surface where drift means a stranger reads a family's thread.
    """
    storage = _storage()
    other_name = _display_name(other_user_id) or "A parent"
    if not member_id:
        member_id = storage.add_household_member(
            holder_user_id, display_name=other_name, role="other", kind="adult",
            notes=holder_note,
        )
    storage.update_household_member(member_id, {"member_user_id": other_user_id})

    # The reciprocal side. Idempotent: if the other party already has a row
    # pointing at the holder, reuse it rather than duplicating the person.
    reciprocal = storage.find_household_member_by_account(other_user_id, holder_user_id)
    if reciprocal is None:
        holder_name = _display_name(holder_user_id) or "A parent"
        storage.add_household_member(
            other_user_id, display_name=holder_name, role="other", kind="adult",
            member_user_id=holder_user_id,
            notes=other_note,
        )

    storage.bind_circle_participant_account(member_id, other_user_id)
    return member_id


@router.post("/invites")
def create_invite(body: InviteCreate, user_id: str = Depends(current_user)):
    """Mint a share link. `member_id` binds the invite to a roster row, so
    claiming it links that specific person; an open invite (no member_id)
    creates the roster row at claim time."""
    enforce(user_id, "config")
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
    enforce(user_id, "config")
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
    if member_id:
        member = storage.get_household_member(member_id)
        if member is None or member.get("user_id") != inviter:
            raise HTTPException(status_code=404, detail="invite target no longer exists")

    # The binding lives in ONE place, shared with request-accept below (an open
    # invite passes member_id=None and the helper creates the roster row from
    # the claimer's own account name — the inviter never typed one in).
    member_id = _bind_mutual_link(
        inviter, user_id, member_id=member_id,
        holder_note="Joined through a Circle invite link.",
        other_note="Linked through a Circle invite link.",
    )
    storage.claim_invite_token(token, user_id)
    return {"ok": True, "member_id": member_id, "inviter_user_id": inviter}


# --------------------------------------------------------------------------- #
# Contacts by email — the silent request
# --------------------------------------------------------------------------- #
# "If you type in an email address and that person already exists in the system,
# no need to invite them — just pull them from the system. A nanny could already
# be in someone else's circle."
#
# Pulling them in still requires their consent, and looking for them must not
# tell you whether they exist. Hence: ONE response shape for every outcome, and
# a match creates a PENDING request rather than a link.


# The response for POST /circle/contacts, byte-identical on every path. It is a
# module constant precisely so no future branch can accidentally enrich one
# side of the fork ("...and here's their name!") and turn the endpoint into an
# enumeration oracle. If this ever needs to carry more, it has to carry the
# same more on all five paths (matched, no-match, self, already-a-peer,
# duplicate-pending).
_CONTACT_ACK = {"status": "sent"}

MAX_EMAIL_CHARS = 320  # RFC-ish local@domain ceiling; bounds the lookup key


def _notify_circle_request(to_user_id: str, from_user_id: str) -> None:
    """Tell the recipient someone asked to join their Circle. Env-gated APNs
    (app/push), reusing the device-verified channel; fire-and-forget on a
    daemon thread so a slow APNs call never holds the request open — and so the
    matched path doesn't become measurably slower than the no-match one."""
    import threading

    from app import push

    if not push.is_enabled():
        return
    asker = _display_name(from_user_id) or "A parent"
    threading.Thread(
        target=lambda: push.send_push(
            storage=_storage(),
            user_id=to_user_id,
            title="Someone wants to join your Circle",
            body=f"{asker} asked to connect. Tap to accept or decline.",
            data={"type": "circle_request", "from_user_id": from_user_id},
        ),
        daemon=True,
    ).start()


@router.post("/contacts")
def add_contact(body: ContactAdd, user_id: str = Depends(current_user)):
    """Add someone to your Circle by email.

    The response is `{"status": "sent"}` with a 200 on EVERY path — matched,
    unmatched, yourself, already a peer, duplicate. That is the security
    property: a caller cannot use this route to learn whether an email belongs
    to an MVP user. Do not add a branch that returns anything else.

    Matched  -> a PENDING circle_requests row + a local roster row (so the
                contacts list shows the pending contact) + a push to them.
                No peer link, no participant row, no read access.
    No match -> today's invite-token path, unchanged.
    """
    enforce(user_id, "config")
    storage = _storage()

    email = (body.email or "").strip().lower()[:MAX_EMAIL_CHARS]
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="a valid email is required")
    display_name = (body.display_name or "").strip()[:120] or None

    # Exactly one hit, or nothing. Zero and many are the SAME outcome (see
    # storage.find_account_by_email) — an ambiguous email must never auto-link.
    match = storage.find_account_by_email(email)

    if match and match != user_id:
        already_peer = match in set(storage.circle_peer_ids(user_id))
        pending = storage.find_pending_circle_request(
            from_user_id=user_id, to_user_id=match
        )
        # Both are silent no-ops: re-asking someone who already accepted, or
        # asking twice, must not stack rows — and must not be distinguishable
        # from a first ask by the response.
        if not already_peer and pending is None:
            # The requester's own roster row, created UP FRONT so the contacts
            # list can render the pending contact. It carries no
            # member_user_id, so it grants nothing until the accept binds it
            # (a linked-but-not-mutual row is just an address book entry —
            # circle_peer_ids requires both directions).
            member_id = storage.add_household_member(
                user_id,
                display_name=display_name or (_display_name(match) or "A parent"),
                role="other", kind="adult", email=email,
                notes="Circle request sent — waiting on them to accept.",
            )
            storage.create_circle_request(
                from_user_id=user_id, to_user_id=match, from_member_id=member_id,
            )
            _notify_circle_request(match, user_id)
        return dict(_CONTACT_ACK)

    if match == user_id:
        # Your own email. Silent no-op — not even a 400, because a 400 here
        # would tell an attacker which email is theirs vs. merely unknown.
        return dict(_CONTACT_ACK)

    # No match (or an ambiguous one): mint an invite link exactly as before.
    # A roster row so the contacts list shows who was invited, then the token.
    member_id = storage.add_household_member(
        user_id, display_name=display_name or email.split("@")[0],
        role="other", kind="adult", email=email,
        notes="Invited to MVP — waiting on them to join.",
    )
    token = secrets.token_urlsafe(24)
    storage.create_invite_token(
        user_id, member_id=member_id, token=token, ttl_days=INVITE_TTL_DAYS
    )
    # Deliberately NOT returned: an invite URL in the response body is present
    # on one branch and absent on the other, which is exactly the tell this
    # endpoint exists to avoid. The client fetches the link from
    # POST /circle/invites when it wants something to share.
    return dict(_CONTACT_ACK)


# --------------------------------------------------------------------------- #
# Requests — the consent step
# --------------------------------------------------------------------------- #


def _request_out(row: Dict[str, Any]) -> Dict[str, Any]:
    """Wire shape. Every key ALWAYS present (iOS Codable is strict). The
    requester's NAME is included — the recipient has to know who is asking to
    decide — but never their email or anything else about their household."""
    from_user_id = row.get("from_user_id") or ""
    name = _display_name(from_user_id) or "A parent"
    return {
        "id": row.get("id"),
        "from_user_id": from_user_id,
        "from_name": name,
        "initials": _initials(name),
        "status": row.get("status") or "pending",
        "created_at": row.get("created_at"),
    }


def _inbound_request_or_404(request_id: str, user_id: str) -> Dict[str, Any]:
    """Existence check FIRST, then ownership — the `_conversation_or_404`
    pattern. A third party gets the same 404 for "no such request" and "not
    yours", so they learn nothing about requests between other people."""
    request = _storage().get_circle_request(request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="request not found")
    if request.get("to_user_id") != user_id:
        raise HTTPException(status_code=404, detail="request not found")
    return request


@router.get("/requests")
def list_requests(user_id: str = Depends(current_user)):
    """My pending INBOUND requests — the ones I can act on."""
    enforce(user_id, "config")
    rows = _storage().list_circle_requests_for_user(user_id, status="pending")
    return {"requests": [_request_out(r) for r in rows]}


@router.post("/requests/{request_id}/accept")
def accept_request(request_id: str, user_id: str = Depends(current_user)):
    """Consent. THIS is the moment the link becomes mutual — through the same
    `_bind_mutual_link` that claiming an invite runs, so there is exactly one
    code path for "we are now peers"."""
    enforce(user_id, "config")
    storage = _storage()
    request = _inbound_request_or_404(request_id, user_id)
    if request.get("status") != "pending":
        raise HTTPException(status_code=409, detail="this request was already answered")

    requester = request["from_user_id"]
    member_id = request.get("from_member_id")
    if member_id:
        member = storage.get_household_member(member_id)
        # The requester may have deleted the roster row while waiting. Passing
        # None re-creates it rather than binding someone else's row.
        if member is None or member.get("user_id") != requester:
            member_id = None

    _bind_mutual_link(
        requester, user_id, member_id=member_id,
        holder_note="Circle request accepted.",
        other_note="Joined their Circle.",
    )
    storage.set_circle_request_status(request_id, "accepted")
    return {"ok": True, "status": "accepted", "from_user_id": requester}


@router.post("/requests/{request_id}/decline")
def decline_request(request_id: str, user_id: str = Depends(current_user)):
    """Refusal. Establishes NOTHING — no roster binding on either side. The row
    is kept (not deleted) so the requester's pending contact resolves and a
    re-ask isn't blocked by the duplicate-pending guard."""
    enforce(user_id, "config")
    request = _inbound_request_or_404(request_id, user_id)
    if request.get("status") != "pending":
        raise HTTPException(status_code=409, detail="this request was already answered")
    _storage().set_circle_request_status(request_id, "declined")
    return {"ok": True, "status": "declined", "from_user_id": request["from_user_id"]}
