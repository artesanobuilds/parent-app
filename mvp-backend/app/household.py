"""Household members + Circle (beta-v1 Phase 1).

Circle stops being an anonymous discussion board and becomes *your actual
people*: co-parent, spouse, nanny, grandparent, neighbour — the people who
work with you. This module owns that roster.

Three decisions worth knowing before editing:

1. **Own table, linked to `caregivers`.** Members live in `household_members`,
   not in the pre-existing `caregivers` table, because `caregivers` is
   PLAN-scoped state that `reset_plan()` wipes — and this roster is the
   authorization source for DM scoping. "Start over" on the activity board
   must not change who a parent is allowed to message. The two are wired
   together instead: creating a member with a logistics-capable role mirrors a
   `caregivers` row and stores its id on the member, so a nanny is entered once
   and shows up in the Chief-of-Staff logistics roster. The member is the
   source of truth; the mirror follows it (and dies with it).

2. **Children are NOT here.** `kind` is a discriminator and `GET /household`
   projects the existing `FamilyProfile.children` into a member-shaped
   envelope so the client renders one roster — but the kid's storage stays on
   its existing profile path. Writes with `kind="child"` / `role="child"` are
   rejected, pointing at `/profile/kids/*`. Migrating children would drag the
   kid-agent, the crisis-lock flow and the onboarding seed contract with it.

3. **Keyed by the stable id.** `display_name` is editable and never a key
   (CLAUDE.md). The one place a name is still a key is the *child* projection,
   which inherits that from `FamilyProfile.children` — flagged, not fixed.

Attributes are role-scoped: everyone gets Likes / Dislikes / Challenges /
Excels at / Goals, and **"Co-Parent goals" exists only on `co_parent`**. The
scoping is enforced server-side on write (unknown keys for the role are
rejected) as well as reflected on read.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import authorize_user_match, current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/household", tags=["household"])


# --------------------------------------------------------------------------- #
# Vocabulary
# --------------------------------------------------------------------------- #

MEMBER_KINDS = ("adult", "child")

# The roles the design frames carry ("Family roll" in the Figma is a typo for
# role). `child` is listed so the client can render it, but it is not writable
# through this surface — see the module docstring.
MEMBER_ROLES = (
    "me", "spouse", "co_parent", "child",
    "nanny", "grandparent", "neighbour", "other",
)

ROLE_LABELS = {
    "me": "Me",
    "spouse": "Spouse",
    "co_parent": "Co-Parent",
    "child": "Child",
    "nanny": "Nanny",
    "grandparent": "Grandparent",
    "neighbour": "Neighbour",
    "other": "Other",
}

# Roles that get a mirrored `caregivers` row (they can cover drop-off/pickup).
# A child never does, and an unclaimed contact-only role could be added later.
LOGISTICS_ROLES = ("me", "spouse", "co_parent", "nanny", "grandparent",
                   "neighbour", "other")

# member role -> caregivers.role (that column's own enum:
# parent|nanny|therapist|family_friend|other).
_CAREGIVER_ROLE = {
    "me": "parent",
    "spouse": "parent",
    "co_parent": "parent",
    "nanny": "nanny",
    "grandparent": "family_friend",
    "neighbour": "family_friend",
    "other": "other",
}

# The "More about {name}" disclosure list. Every role gets the common set;
# ROLE_ATTRIBUTES adds role-only ones on top.
COMMON_ATTRIBUTES = ("likes", "dislikes", "challenges", "excels_at", "goals")
ROLE_ATTRIBUTES: Dict[str, tuple] = {
    "co_parent": ("co_parent_goals",),
}

ATTRIBUTE_LABELS = {
    "likes": "Likes",
    "dislikes": "Dislikes",
    "challenges": "Challenges",
    "excels_at": "Excels at",
    "goals": "Goals for {name}",
    "co_parent_goals": "Co-Parent goals",
}

# Light input hardening: these are free-text lists a parent types.
MAX_ATTRIBUTE_ITEMS = 50
MAX_ATTRIBUTE_CHARS = 500
MAX_NAME_CHARS = 120


def allowed_attributes(role: str) -> tuple:
    """The attribute keys valid for `role`. Co-Parent goals ONLY on co_parent."""
    return COMMON_ATTRIBUTES + ROLE_ATTRIBUTES.get(role, ())


def attribute_fields(role: str, display_name: str) -> List[Dict[str, str]]:
    """The disclosure rows the sheet renders, in order, already labelled."""
    return [
        {"key": key,
         "label": ATTRIBUTE_LABELS[key].replace("{name}", display_name or "them")}
        for key in allowed_attributes(role)
    ]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _storage():
    # Imported lazily: app.server imports this module, and TestClient teardown
    # rebinds server.storage_backend (see tests/test_onboarding_seed_contract).
    from app.server import storage_backend

    return storage_backend


def _validate_role(role: str) -> str:
    if role not in MEMBER_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"unknown role '{role}' (expected one of {', '.join(MEMBER_ROLES)})",
        )
    if role == "child":
        raise HTTPException(
            status_code=400,
            detail="children are not household members — use /profile/kids/* "
                   "(they are projected read-only into GET /household)",
        )
    return role


def _validate_kind(kind: str) -> str:
    if kind not in MEMBER_KINDS:
        raise HTTPException(status_code=400, detail=f"unknown kind '{kind}'")
    if kind == "child":
        raise HTTPException(
            status_code=400,
            detail="children are not household members — use /profile/kids/*",
        )
    return kind


def _clean_attributes(role: str, raw: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Coerce + role-scope the attribute bag. Rejects keys that don't belong to
    the role (so "Co-Parent goals on the nanny" is a 400, not silent data)."""
    if not raw:
        return {}
    allowed = set(allowed_attributes(role))
    unknown = sorted(k for k in raw if k not in allowed)
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"attributes {unknown} are not available for role '{role}' "
                   f"(allowed: {', '.join(sorted(allowed))})",
        )
    out: Dict[str, List[str]] = {}
    for key, value in raw.items():
        if value is None:
            items: List[Any] = []
        elif isinstance(value, list):
            items = value
        else:
            items = [value]
        cleaned = [
            str(v).strip()[:MAX_ATTRIBUTE_CHARS]
            for v in items[:MAX_ATTRIBUTE_ITEMS]
            if v is not None and str(v).strip()
        ]
        out[key] = cleaned
    return out


def _slug(name: str) -> str:
    parts = re.sub(r"[^A-Za-z0-9 ]+", " ", name or "").split()
    if not parts:
        return "Member"
    return parts[0][:1].upper() + parts[0][1:].lower()


def _issue_mvp_username(user_id: str, display_name: str, taken: set) -> str:
    """Issue the member's MVP name locally (`mvpNanny`-style, per the Figma).

    Unique WITHIN the household only — global/domain allocation belongs to the
    shadow-email slice, which owns real inbound routing."""
    base = f"mvp{_slug(display_name)}"
    candidate, n = base, 1
    while candidate.lower() in taken:
        n += 1
        candidate = f"{base}{n}"
    return candidate


def _mirror_caregiver(storage, user_id: str, *, display_name: str, role: str,
                      email: Optional[str]) -> Optional[str]:
    """Create the linked `caregivers` row so the member also exists in the
    Chief-of-Staff logistics roster. Non-fatal: a caregiver mirror failing must
    not lose the member the parent just typed in."""
    if role not in LOGISTICS_ROLES:
        return None
    try:
        return storage.add_caregiver(
            user_id,
            name=display_name,
            role=_CAREGIVER_ROLE.get(role, "other"),
            contact={"email": email} if email else None,
            notes="Linked to a Circle member — edit the member, not this row.",
        )
    except Exception:
        logger.warning("[household] caregiver mirror failed (non-fatal)", exc_info=True)
        return None


def _member_out(row: Dict[str, Any], *, circle: set, presign: bool = True) -> Dict[str, Any]:
    """The wire shape iOS decodes. Every key is ALWAYS present (Codable is
    strict — one missing/mistyped field empties the whole list)."""
    role = row.get("role") or "other"
    display_name = row.get("display_name") or ""
    stored = row.get("attributes") or {}
    attributes = {key: list(stored.get(key) or []) for key in allowed_attributes(role)}
    member_user_id = row.get("member_user_id")

    avatar_url = None
    avatar_key = row.get("avatar_key")
    if presign and avatar_key:
        try:
            from app import blobs
            avatar_url = blobs.presign_get(avatar_key)
        except Exception:
            avatar_url = None

    return {
        "id": row.get("id"),
        "user_id": row.get("user_id"),
        "kind": row.get("kind") or "adult",
        "display_name": display_name,
        "role": role,
        "role_label": ROLE_LABELS.get(role, role),
        "relation": row.get("relation"),
        "mvp_username": row.get("mvp_username"),
        "email": row.get("email"),
        "avatar_key": avatar_key,
        "avatar_url": avatar_url,
        "member_user_id": member_user_id,
        "linked": member_user_id is not None,
        "in_circle": member_user_id is not None and member_user_id in circle,
        "attributes": attributes,
        "attribute_fields": attribute_fields(role, display_name),
        "notes": row.get("notes"),
        "caregiver_id": row.get("caregiver_id"),
        "editable": True,
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def _child_out(name: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    """Read-only projection of an existing kid into the member envelope.

    The seam: the kid's data still lives in FamilyProfile.children and is
    edited through /profile/kids/*. `id` is a synthetic `child:<name>` handle,
    NOT a stable id — children inherit name-as-key from their existing store,
    which this phase deliberately does not migrate."""
    return {
        "id": f"child:{name}",
        "user_id": None,
        "kind": "child",
        "display_name": name,
        "role": "child",
        "role_label": ROLE_LABELS["child"],
        "relation": None,
        "mvp_username": None,
        "email": None,
        "avatar_key": profile.get("avatar_key"),
        "avatar_url": profile.get("avatar_url"),
        "member_user_id": None,
        "linked": False,
        "in_circle": False,
        "attributes": {
            "likes": list(profile.get("interests") or []),
            "dislikes": [],
            "challenges": list(profile.get("challenges") or []),
            "excels_at": list(profile.get("strengths") or []),
            "goals": [],
        },
        "attribute_fields": attribute_fields("child", name),
        "notes": None,
        "caregiver_id": None,
        "editable": False,
        "editable_via": f"/profile/kids/{name}",
        "created_at": None,
        "updated_at": None,
    }


def _owned_member(member_id: str, user_id: str) -> Dict[str, Any]:
    """Fetch a member the caller owns. A member belonging to someone else is a
    404, never a 403 — a 403 would confirm the id exists (the
    ``authorize_user_match(resource=True)`` convention)."""
    member = _storage().get_household_member(member_id)
    if member is None or member.get("user_id") != user_id:
        raise HTTPException(status_code=404, detail="member not found")
    return member


# --------------------------------------------------------------------------- #
# Request bodies
# --------------------------------------------------------------------------- #


class MemberCreate(BaseModel):
    # Optional for parity with the app's other POST bodies. NEVER used for
    # scoping — the owner is always the bearer token's user.
    user_id: Optional[str] = None
    display_name: str
    role: str = "other"
    relation: Optional[str] = None
    mvp_username: Optional[str] = None
    email: Optional[str] = None
    member_user_id: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    link_caregiver: bool = True


class MemberPatch(BaseModel):
    user_id: Optional[str] = None
    display_name: Optional[str] = None
    role: Optional[str] = None
    relation: Optional[str] = None
    mvp_username: Optional[str] = None
    email: Optional[str] = None
    member_user_id: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class MemberAvatarAttach(BaseModel):
    key: str


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #


@router.get("/roles")
def household_roles():
    """The role catalog + the role-scoped attribute rows each one renders.
    Lets the client build the member sheet without hard-coding the matrix."""
    return {
        "roles": [
            {
                "key": role,
                "label": ROLE_LABELS[role],
                "kind": "child" if role == "child" else "adult",
                "writable": role != "child",
                "attributes": attribute_fields(role, "{name}"),
            }
            for role in MEMBER_ROLES
        ],
        "kinds": list(MEMBER_KINDS),
    }


@router.get("")
def get_household(user_id: str = Depends(current_user)):
    """The Profile hub: the Circle roster plus a READ-ONLY projection of the
    kids, so one screen renders one list. Children are edited through
    /profile/kids/* — see the module docstring for why the seam is here."""
    from app.profiling import profiling_service

    storage = _storage()
    circle = set(storage.circle_peer_ids(user_id))
    members = [_member_out(m, circle=circle) for m in storage.list_household_members(user_id)]
    family = profiling_service.get_family_profile(user_id)
    children = [
        _child_out(name, profile or {})
        for name, profile in (family.get("children") or {}).items()
    ]
    return {
        "members": members,
        "children": children,
        "counts": {"members": len(members), "children": len(children),
                   "circle": len(circle)},
    }


@router.get("/members")
def list_members(user_id: str = Depends(current_user)):
    storage = _storage()
    circle = set(storage.circle_peer_ids(user_id))
    return {"members": [_member_out(m, circle=circle)
                        for m in storage.list_household_members(user_id)]}


@router.post("/members")
def create_member(body: MemberCreate, user_id: str = Depends(current_user)):
    if body.user_id is not None:
        authorize_user_match(authenticated=user_id, claimed=body.user_id)
    display_name = (body.display_name or "").strip()[:MAX_NAME_CHARS]
    if not display_name:
        raise HTTPException(status_code=400, detail="display_name is required")
    role = _validate_role(body.role)
    if body.member_user_id is not None and body.member_user_id == user_id:
        raise HTTPException(status_code=400, detail="you can't add yourself as a linked account")
    attributes = _clean_attributes(role, body.attributes)

    storage = _storage()
    existing = storage.list_household_members(user_id)
    taken = {(m.get("mvp_username") or "").lower() for m in existing}
    mvp_username = (body.mvp_username or "").strip() or _issue_mvp_username(
        user_id, display_name, taken
    )
    if mvp_username.lower() in taken:
        raise HTTPException(status_code=409, detail="that MVP name is already used in your household")

    caregiver_id = (
        _mirror_caregiver(storage, user_id, display_name=display_name,
                          role=role, email=body.email)
        if body.link_caregiver else None
    )
    member_id = storage.add_household_member(
        user_id,
        display_name=display_name,
        role=role,
        kind="adult",
        relation=(body.relation or None),
        mvp_username=mvp_username,
        email=(body.email or None),
        member_user_id=(body.member_user_id or None),
        attributes=attributes,
        notes=(body.notes or None),
        caregiver_id=caregiver_id,
    )
    circle = set(storage.circle_peer_ids(user_id))
    return {"member": _member_out(storage.get_household_member(member_id), circle=circle)}


@router.get("/members/{member_id}")
def get_member(member_id: str, user_id: str = Depends(current_user)):
    member = _owned_member(member_id, user_id)
    circle = set(_storage().circle_peer_ids(user_id))
    return {"member": _member_out(member, circle=circle)}


@router.patch("/members/{member_id}")
def patch_member(member_id: str, body: MemberPatch, user_id: str = Depends(current_user)):
    """Partial update. Only keys the client actually sent are touched, so a
    Basics-only save can't blank the attributes the coach learned (the
    `test_saving_basics_does_not_wipe_learned_fields` rule). Sending an
    explicit null CLEARS that field."""
    if body.user_id is not None:
        authorize_user_match(authenticated=user_id, claimed=body.user_id)
    member = _owned_member(member_id, user_id)
    sent = body.model_dump(exclude_unset=True, exclude={"user_id"})
    storage = _storage()

    role = member.get("role") or "other"
    if "role" in sent:
        role = _validate_role(sent["role"])

    fields: Dict[str, Any] = {}
    if "display_name" in sent:
        display_name = (sent["display_name"] or "").strip()[:MAX_NAME_CHARS]
        if not display_name:
            raise HTTPException(status_code=400, detail="display_name cannot be empty")
        fields["display_name"] = display_name
    if "role" in sent:
        fields["role"] = role
    for key in ("relation", "email", "notes"):
        if key in sent:
            fields[key] = (sent[key] or None)
    if "mvp_username" in sent:
        wanted = (sent["mvp_username"] or "").strip()
        if wanted:
            taken = {
                (m.get("mvp_username") or "").lower()
                for m in storage.list_household_members(user_id)
                if m.get("id") != member_id
            }
            if wanted.lower() in taken:
                raise HTTPException(status_code=409,
                                    detail="that MVP name is already used in your household")
        fields["mvp_username"] = wanted or None
    if "member_user_id" in sent:
        linked = (sent["member_user_id"] or None)
        if linked == user_id:
            raise HTTPException(status_code=400,
                                detail="you can't add yourself as a linked account")
        fields["member_user_id"] = linked

    # A role change re-scopes the attribute bag: keys that no longer belong to
    # the role are dropped rather than left as invisible orphans.
    if "attributes" in sent:
        merged = _clean_attributes(role, sent["attributes"])
        fields["attributes_json"] = merged or None
    elif "role" in sent:
        kept = {k: v for k, v in (member.get("attributes") or {}).items()
                if k in allowed_attributes(role)}
        fields["attributes_json"] = kept or None

    storage.update_household_member(member_id, fields)

    # Keep the mirrored caregivers row in step — the member is the source of
    # truth, so a rename here renames there (never the other way round).
    caregiver_id = member.get("caregiver_id")
    if caregiver_id and ("display_name" in fields or "role" in fields):
        try:
            storage.update_caregiver(
                caregiver_id,
                name=fields.get("display_name"),
                role=_CAREGIVER_ROLE.get(role) if "role" in fields else None,
            )
        except Exception:
            logger.warning("[household] caregiver mirror update failed", exc_info=True)

    circle = set(storage.circle_peer_ids(user_id))
    return {"member": _member_out(storage.get_household_member(member_id), circle=circle)}


@router.delete("/members/{member_id}")
def delete_member(member_id: str, user_id: str = Depends(current_user)):
    """Remove a member. The mirrored caregivers row and any logistics
    assignment that pointed at it go too (CLAUDE.md: deletes cascade), and the
    member's photo is deleted from blob storage rather than orphaned."""
    member = _owned_member(member_id, user_id)
    counts = _storage().delete_household_member(member_id)
    avatar_key = member.get("avatar_key")
    if avatar_key:
        try:
            from app import blobs
            blobs.delete(avatar_key)
        except Exception:
            logger.warning("[household] avatar cleanup failed (non-fatal)", exc_info=True)
    return {"ok": True, "deleted": counts}


# --------------------------------------------------------------------------- #
# Agent context
# --------------------------------------------------------------------------- #
# Not a route — the merged parent agent (app/agent.py) renders the roster into
# its system prompt so the coach knows who is in the family and the Circle.
# Deliberately a compact TEXT block, not JSON: the family profile next to it is
# already JSON, and a second nested blob reads as raw data the model dumps back.


# The roster is a per-user, mutable part of the prompt, so it is bounded: a
# pathological roster must not blow the context or the prompt cache.
PROMPT_MAX_MEMBERS = 20
PROMPT_MAX_ATTRIBUTE_ITEMS = 6


def _member_prompt_line(row: Dict[str, Any]) -> str:
    role = row.get("role") or "other"
    name = (row.get("display_name") or "").strip() or "Unnamed"
    bits: List[str] = [ROLE_LABELS.get(role, role)]
    relation = (row.get("relation") or "").strip()
    if relation:
        bits.append(relation)
    if row.get("member_user_id"):
        bits.append("has their own MVP account")
    line = f"- {name} ({', '.join(bits)})"

    stored = row.get("attributes") or {}
    details: List[str] = []
    for key in allowed_attributes(role):
        values = [str(v).strip() for v in (stored.get(key) or []) if str(v).strip()]
        if not values:
            continue
        label = ATTRIBUTE_LABELS[key].replace("{name}", name)
        details.append(f"{label}: {', '.join(values[:PROMPT_MAX_ATTRIBUTE_ITEMS])}")
    notes = (row.get("notes") or "").strip()
    if notes:
        details.append(f"Notes: {notes}")
    if details:
        line += "\n  " + "\n  ".join(details)
    return line


def household_context_for_prompt(user_id: str) -> str:
    """The Circle roster as prompt text, or "" when the parent has no members.

    Never raises: a storage hiccup must degrade the agent's context, not fail
    the turn that was trying to use it. Emails are deliberately INCLUDED — the
    draft-email and email-sync tools need the co-parent's/nanny's address, and
    the merged agent is the surface that uses it.
    """
    try:
        rows = _storage().list_household_members(user_id)
    except Exception:  # noqa: BLE001
        logger.warning("[household] prompt context unavailable", exc_info=True)
        return ""
    if not rows:
        return ""
    lines = [
        "The people in this family and their Circle (the parent's own roster — "
        "use their names naturally; never dump this list back at them):"
    ]
    lines += [_member_prompt_line(r) for r in rows[:PROMPT_MAX_MEMBERS]]
    if len(rows) > PROMPT_MAX_MEMBERS:
        lines.append(f"- (+{len(rows) - PROMPT_MAX_MEMBERS} more)")
    return "\n".join(lines)


@router.post("/members/{member_id}/avatar")
def attach_member_avatar(member_id: str, body: MemberAvatarAttach,
                         user_id: str = Depends(current_user)):
    """Attach an uploaded photo (the full-bleed hero on the member sheet).

    avatar_key is NOT settable through create/patch, exactly as on parent and
    kid profiles: a client-writable key would let one family presign another
    family's photo. The key's `u/{user_id}/` prefix must be the caller's."""
    from app import blobs

    member = _owned_member(member_id, user_id)
    if not blobs.is_configured():
        raise HTTPException(status_code=503, detail="blob storage is not configured")
    if not blobs.key_belongs_to(body.key, user_id):
        raise HTTPException(status_code=403, detail="key does not belong to this account")
    if blobs.head(body.key) is None:
        raise HTTPException(status_code=404, detail="no uploaded object at that key")

    storage = _storage()
    old = member.get("avatar_key")
    storage.update_household_member(member_id, {"avatar_key": body.key})
    if old and old != body.key:
        try:
            blobs.delete(old)
        except Exception:
            logger.warning("[household] old avatar delete failed", exc_info=True)
    circle = set(storage.circle_peer_ids(user_id))
    return {"member": _member_out(storage.get_household_member(member_id), circle=circle)}
