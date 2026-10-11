"""
DuckDB + Parquet storage backend.

Stores user data as JSON blobs in a DuckDB database backed by parquet files.
Also stores content library tables (categories, articles).
Drop-in replacement for LocalFileStorage — same StorageBackend interface.
"""

import json
import logging
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import duckdb


def _parse_legal_frontmatter(text: str) -> tuple:
    """Parse the simple `--- key: value ---` frontmatter used by the legal
    markdown seeds (same convention as parent-dashboard/docs). Returns
    (meta dict, body). Tolerates a missing block: everything becomes body."""
    meta: Dict[str, str] = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].strip().splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    meta[key.strip()] = value.strip()
            return meta, text[end + 4 :].lstrip("\n")
    return meta, text


class _BufferedResult:
    """Holds eagerly-fetched rows so callers can chain .fetchone()/.fetchall()
    after the connection lock has been released."""

    __slots__ = ("_rows", "_i")

    def __init__(self, rows: List[Any]):
        self._rows = rows
        self._i = 0

    def fetchone(self):
        if self._i < len(self._rows):
            row = self._rows[self._i]
            self._i += 1
            return row
        return None

    def fetchall(self):
        rest = self._rows[self._i:]
        self._i = len(self._rows)
        return rest


class _ThreadSafeConn:
    """
    Serializes access to a DuckDB connection (B-8). DuckDB connections are not
    thread-safe, and FastAPI runs sync routes in a threadpool while async routes
    run on the event loop — concurrent execute()s on one connection can corrupt
    state or interleave writes. Every execute holds an RLock across execute +
    eager fetch, returning a buffered result so the lock is released before the
    caller chains .fetchone()/.fetchall(). The connection is only ever used via
    .execute()/.close() in this module, so this proxy is a complete surface.
    """

    def __init__(self, con: "duckdb.DuckDBPyConnection"):
        self._con = con
        self._lock = threading.RLock()
        self._transaction_depth = 0
        self._rollback_only = False

    def execute(self, sql: str, params: Optional[list] = None) -> _BufferedResult:
        with self._lock:
            rel = self._con.execute(sql, params) if params is not None else self._con.execute(sql)
            try:
                rows = rel.fetchall()
            except Exception:
                # Statements without a result set (some DDL) — nothing to buffer.
                rows = []
            return _BufferedResult(rows)

    @contextmanager
    def transaction(self):
        """
        Hold the connection lock across a BEGIN/COMMIT so a multi-statement
        transaction is both atomic AND isolated — no other thread can execute
        against the shared connection (and thus join the implicit DuckDB
        transaction) while this block runs. RLock is reentrant, so the inner
        execute() calls re-acquire it fine. Rolls back on any exception.
        """
        with self._lock:
            outer = self._transaction_depth == 0
            if outer:
                self._con.execute("BEGIN TRANSACTION")
                self._rollback_only = False
            self._transaction_depth += 1
            try:
                yield self
                if outer:
                    if self._rollback_only:
                        raise RuntimeError("Nested transaction failed; refusing partial commit")
                    self._con.execute("COMMIT")
            except BaseException:
                self._rollback_only = True
                if outer:
                    self._con.execute("ROLLBACK")
                raise
            finally:
                self._transaction_depth -= 1

    def close(self) -> None:
        with self._lock:
            self._con.close()

from app.storage import StorageBackend

logger = logging.getLogger(__name__)

# ── Family cascade table partition ──────────────────────────────────────────
# Every table swept by a plain `DELETE ... WHERE user_id = ?` in the family
# cascade, in the order the original delete ran them. `delete_family` uses the
# whole list; `reset_family` (wipe the data, KEEP the sign-in) skips the
# identity subset and legal_acceptances. One shared list means the two
# cascades cannot drift when a new user-keyed table is added — add it HERE.
FAMILY_CASCADE_TABLES: List[str] = [
    "agent_operation_receipts",
    "agent_runs",
    "kid_agent_crisis_locks",
    "kid_agent_configs",
    "kid_credentials",
    "moderation_events",
    "auth_tokens",
    "refresh_tokens",
    "auth_identities",
    "user_accounts",
    "push_device_tokens",
    "share_tokens",
    "daily_summaries",
    "consent_records",
    "user_data",
    # Activity-planning / chief-of-staff tables — all keyed by user_id.
    # Account deletion must wipe these too (privacy), and this lets a
    # test-user purge fully clean up research runs etc.
    "research_runs",
    "activity_candidates",
    "tracked_activities",
    "calendar_entries",
    "recurring_appointments",
    "caregivers",
    "logistics_assignments",
    "todo_items",
    "ingest_artifacts",
    "cos_messages",
    "integration_accounts",
    "email_sync_runs",
    "calendar_sync_runs",
    "registration_windows",  # window_notifications cascade runs first
    # Legal ACCEPTANCES are user audit state and go with the family on DELETE.
    # legal_documents (the policies themselves) deliberately survive.
    "legal_acceptances",
    "saved_items",
    # First-run warm-up job rows + the coach nudges they produced.
    "onboarding_warmup_runs",
    "coach_nudges",
    # Household members / Circle. Deleting the family removes my roster; the
    # reciprocal rows OTHER families hold that point at me are swept
    # separately (they carry my user_id in member_user_id, not user_id).
    "household_members",
]

# The sign-in identity: the rows that make "this Apple/Google account is this
# user_id" true. `reset_family` keeps these so a tester can wipe their family
# data and re-run onboarding on the SAME account.
FAMILY_IDENTITY_TABLES: frozenset = frozenset({
    "auth_tokens",
    "refresh_tokens",
    "auth_identities",
    "user_accounts",
})

# Reset additionally keeps legal_acceptances — the testers already accepted
# the terms; a data reset does not un-accept them.
FAMILY_RESET_SKIP_TABLES: frozenset = FAMILY_IDENTITY_TABLES | {"legal_acceptances"}


class DuckDBStorage(StorageBackend):
    """
    DuckDB-backed implementation of StorageBackend.

    Tables:
        user_data(user_id, name, data, updated_at)
        categories(id, name, emoji, description)
        articles(id, category, title, subtitle, emoji, author, read_time, kicker, age_range,
                 summary, tags, content, created_at, updated_at)
    """

    DDL = """
    CREATE TABLE IF NOT EXISTS user_data (
        user_id  TEXT NOT NULL,
        name     TEXT NOT NULL,
        data     JSON NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT now(),
        PRIMARY KEY (user_id, name)
    );
    """

    CONTENT_DDL = """
    CREATE TABLE IF NOT EXISTS categories (
        id          TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        emoji       TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        parent_id   TEXT  -- soft self-ref to categories.id (Phase 0), NULL = top-level
    );

    CREATE TABLE IF NOT EXISTS articles (
        id          TEXT PRIMARY KEY,
        category    TEXT NOT NULL,
        title       TEXT NOT NULL,
        subtitle    TEXT NOT NULL DEFAULT '',
        emoji       TEXT NOT NULL DEFAULT '',
        author      TEXT NOT NULL DEFAULT 'MVP Editorial',
        read_time   TEXT NOT NULL DEFAULT '',
        summary     TEXT NOT NULL DEFAULT '',
        tags        TEXT[] NOT NULL DEFAULT [],
        content     TEXT NOT NULL DEFAULT '',
        kicker      TEXT NOT NULL DEFAULT '',  -- eyebrow label, e.g. WE TRIED IT (added in migration v23)
        age_range   TEXT NOT NULL DEFAULT '',  -- eyebrow age band, e.g. Ages 3-7 (added in migration v23)
        created_at  TIMESTAMPTZ DEFAULT now(),
        updated_at  TIMESTAMPTZ DEFAULT now()
    );

    """
    # NOTE: community_posts + post_replies used to live in CONTENT_DDL. The
    # public board is retired (beta-v1 sprint 2) and both tables were DROPPED in
    # migration v21. Do NOT re-add the DDL: CREATE-IF-NOT-EXISTS runs before
    # migrations on every boot, so it would resurrect an empty table that v21
    # (already applied) will never drop again.

    # Versioned legal documents (privacy policy, terms) + per-user acceptance.
    # legal_documents is APPEND-ONLY for published rows -- publishing promotes
    # the single mutable draft row (published_at IS NULL) inside a transaction
    # and never mutates a published row. The is_current row per slug is the
    # required version (no env var). One draft per slug is enforced in
    # upsert_legal_draft, not by a constraint (DuckDB lacks partial unique
    # indexes). legal_acceptances is user-keyed audit state -- cascade on
    # delete_family. legal_documents survives account deletion (not user data).
    LEGAL_DDL = """
    CREATE TABLE IF NOT EXISTS legal_documents (
        id                     TEXT PRIMARY KEY,
        slug                   TEXT NOT NULL,
        version                TEXT NOT NULL DEFAULT '',
        title                  TEXT NOT NULL DEFAULT '',
        body_md                TEXT NOT NULL DEFAULT '',
        effective_date         DATE,
        requires_reacceptance  BOOLEAN DEFAULT false,
        published_at           TIMESTAMPTZ,
        published_by           TEXT,
        is_current             BOOLEAN DEFAULT false,
        created_at             TIMESTAMPTZ DEFAULT now(),
        updated_at             TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_legal_documents_slug
        ON legal_documents (slug, is_current);

    CREATE TABLE IF NOT EXISTS legal_acceptances (
        id           TEXT PRIMARY KEY,
        user_id      TEXT NOT NULL,
        document_id  TEXT NOT NULL,
        slug         TEXT NOT NULL,
        version      TEXT NOT NULL,
        accepted_at  TIMESTAMPTZ DEFAULT now(),
        ip_address   TEXT,
        user_agent   TEXT,
        platform     TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_legal_acceptances_user
        ON legal_acceptances (user_id, slug, accepted_at);
    """

    # NOTE: DM_DDL (dm_conversations / dm_messages / dm_reactions, plus the
    # UNIQUE participant-pair index) lived here. Parent-to-parent 1:1 DMs are
    # retired (beta-v1 sprint 2) -- CIRCLE_DDL's group threads replace them --
    # and all three tables were DROPPED in migration v21. Do NOT re-add the DDL:
    # CREATE-IF-NOT-EXISTS runs before migrations on every boot, so it would
    # resurrect empty tables that v21 (already applied) will never drop again.

    # Saved items (the Saved tab). DENORMALIZED snapshots on purpose -- a save
    # must survive a CMS edit or a deleted post, and for coach replies the
    # snapshot is the ONLY copy (coach chat has no durable server row). SOFT
    # delete via unsaved_at -- the unsave is itself a profiling signal -- and
    # deliberately NO unique constraint: re-saving bumps save_count on the
    # existing row (a unique index + soft delete would block re-save).
    SAVED_DDL = """
    CREATE TABLE IF NOT EXISTS saved_items (
        id           TEXT PRIMARY KEY,
        user_id      TEXT NOT NULL,
        item_type    TEXT NOT NULL,
        item_ref     TEXT NOT NULL,
        title        TEXT NOT NULL DEFAULT '',
        snippet      TEXT DEFAULT '',
        body         TEXT DEFAULT '',
        source_json  JSON,
        topic_tags   JSON,
        kid_name     TEXT,
        context_json JSON,
        save_count   INTEGER DEFAULT 1,
        saved_at     TIMESTAMPTZ DEFAULT now(),
        unsaved_at   TIMESTAMPTZ,
        created_at   TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_saved_items_user
        ON saved_items (user_id, unsaved_at, saved_at);

    CREATE INDEX IF NOT EXISTS idx_saved_items_lookup
        ON saved_items (user_id, item_type, item_ref);
    """

    # First-run agent warm-up (see app/onboarding_warmup.py). Brand-new tables,
    # so CREATE IF NOT EXISTS converges every deployment on next boot and no
    # migration row is needed (the migration framework is only for ALTERs on
    # already-shipped tables). Indexes live here for the same reason - the
    # columns ship with the CREATE TABLE, not with a later ALTER.
    # (No semicolons inside comments - the bootstrap splits this DDL on ';'.)
    WARMUP_DDL = """
    -- Durable job row for the onboarding warm-up. The phone never holds the
    -- job state - it polls/streams this row by run_id.
    CREATE TABLE IF NOT EXISTS onboarding_warmup_runs (
        id           TEXT PRIMARY KEY,          -- run_id (uuid)
        user_id      TEXT NOT NULL,
        status       TEXT NOT NULL DEFAULT 'queued',  -- queued|running|done|failed|canceled
        steps_json   JSON NOT NULL,             -- [{key,label,state,detail,error}] in display order
        context_json JSON,                      -- request context (kid count, postal code, ...)
        result_json  JSON,                      -- {coach_nudge_id, considerations_seeded, ...}
        error        TEXT,
        created_at   TIMESTAMPTZ DEFAULT now(),
        started_at   TIMESTAMPTZ,
        finished_at  TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_onboarding_warmup_user
        ON onboarding_warmup_runs (user_id, created_at);

    CREATE INDEX IF NOT EXISTS idx_onboarding_warmup_status
        ON onboarding_warmup_runs (status);

    -- Persisted coach nudges. The first one is written by the warm-up so the
    -- redesigned Home has a real COACH card on first open.
    CREATE TABLE IF NOT EXISTS coach_nudges (
        id          TEXT PRIMARY KEY,           -- uuid
        user_id     TEXT NOT NULL,
        source      TEXT NOT NULL DEFAULT 'warmup',  -- warmup|daily|manual
        kid_name    TEXT,                       -- who the nudge is about, NULL = family-wide
        body        TEXT NOT NULL,              -- the card copy the parent reads
        cta_label   TEXT,                       -- e.g. "Try this with Ben"
        origin_id   TEXT,                       -- warm-up run that produced it (audit)
        created_at  TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_coach_nudges_user
        ON coach_nudges (user_id, created_at);

    CREATE INDEX IF NOT EXISTS idx_coach_nudges_source
        ON coach_nudges (user_id, source);
    """

    # Household members / Circle (beta-v1 Phase 1). "Your actual people":
    # co-parents, spouse, nanny, grandparent, neighbour. Brand-new table, so
    # CREATE IF NOT EXISTS converges every deployment and the indexes ship in
    # the base DDL (their columns are here, not added by a later ALTER).
    #
    # Deliberately NOT the existing `caregivers` table: caregivers is
    # PLAN-scoped state that reset_plan() wipes, and this table is the
    # authorization source for Circle scoping - a "Start over" on the activity
    # board must not silently change who you are allowed to message. The two
    # are LINKED instead: caregiver_id below points at the mirrored
    # caregivers row so a nanny is entered once and shows up in logistics.
    #
    # Children are NOT stored here. kind='child' rows are reserved (the
    # discriminator exists so the client can render one roster), but the
    # source of truth for a kid stays FamilyProfile.children - moving it
    # would drag the kid-agent, crisis-lock and seed contract along.
    # (No semicolons inside comments - the bootstrap splits this DDL on ';'.)
    HOUSEHOLD_DDL = """
    CREATE TABLE IF NOT EXISTS household_members (
        id              TEXT PRIMARY KEY,       -- stable uuid, the ONLY key (never display_name)
        user_id         TEXT NOT NULL,          -- owning parent account
        kind            TEXT NOT NULL DEFAULT 'adult',  -- adult|child (child reserved, see above)
        display_name    TEXT NOT NULL,
        role            TEXT NOT NULL DEFAULT 'other',  -- me|spouse|co_parent|child|nanny|grandparent|neighbour|other
        relation        TEXT,                   -- free text, e.g. "Step Mom"
        mvp_username    TEXT,                   -- issued locally, unique within the household
        email           TEXT,
        avatar_key      TEXT,                   -- blob key, server-set only (ownership verified)
        member_user_id  TEXT,                   -- the MVP account this member IS, once claimed
        attributes_json JSON,                   -- role-scoped bag (likes/dislikes/challenges/excels_at/goals/co_parent_goals)
        notes           TEXT,
        caregiver_id    TEXT,                   -- mirrored caregivers.id for logistics, NULL when unlinked
        created_at      TIMESTAMPTZ DEFAULT now(),
        updated_at      TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_household_members_user
        ON household_members (user_id, created_at);

    -- Drives the Circle scoping lookup, which resolves both directions.
    CREATE INDEX IF NOT EXISTS idx_household_members_account
        ON household_members (member_user_id);
    """

    # Circle conversations (beta-v1 Phase 1) - the group threads that REPLACE
    # the anonymous community board.
    #
    # Why a new model rather than widening the old dm_conversations: that table
    # was structurally 1:1 (UNIQUE index on the canonically ordered participant
    # pair), so a third participant had nowhere to go. It is gone as of v21.
    #
    # circle_participants.user_id is NULLABLE on purpose: you can start a
    # thread with your nanny before she has an MVP account. The row is keyed by
    # the household_members id (stable), and user_id is filled in when she
    # claims an invite. Until then she simply cannot read it - authorization
    # only ever matches on user_id.
    #
    # Messages carry a denormalized author_name/initials snapshot so a thread
    # still renders correctly after a member is renamed or removed.
    # (No semicolons inside comments - the bootstrap splits this DDL on ';'.)
    CIRCLE_DDL = """
    CREATE TABLE IF NOT EXISTS circle_conversations (
        id            TEXT PRIMARY KEY,       -- stable uuid
        owner_user_id TEXT NOT NULL,          -- the parent who started it (only editor/deleter)
        title         TEXT NOT NULL,
        body          TEXT,                   -- the opening post
        created_at    TIMESTAMPTZ DEFAULT now(),
        updated_at    TIMESTAMPTZ DEFAULT now(),
        last_reply_at TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_circle_conversations_owner
        ON circle_conversations (owner_user_id, created_at);

    CREATE TABLE IF NOT EXISTS circle_participants (
        conversation_id TEXT NOT NULL,
        user_id         TEXT,                 -- NULL until the invited member claims an account
        member_id       TEXT NOT NULL,        -- household_members.id, or self:<user_id> for the owner
        role            TEXT NOT NULL DEFAULT 'member',  -- owner|member
        joined_at       TIMESTAMPTZ DEFAULT now(),
        last_read_at    TIMESTAMPTZ
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_circle_participants_member
        ON circle_participants (conversation_id, member_id);

    CREATE INDEX IF NOT EXISTS idx_circle_participants_user
        ON circle_participants (user_id);

    CREATE TABLE IF NOT EXISTS circle_messages (
        id              TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        user_id         TEXT NOT NULL,
        author_name     TEXT,                 -- snapshot at send time
        initials        TEXT,
        body            TEXT NOT NULL,
        created_at      TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_circle_messages_conversation
        ON circle_messages (conversation_id, created_at);

    -- Invite links. Claiming one is what makes a Circle link MUTUAL, so this
    -- table is an authorization primitive, not a convenience.
    CREATE TABLE IF NOT EXISTS invite_tokens (
        token      TEXT PRIMARY KEY,          -- url-safe secret
        user_id    TEXT NOT NULL,             -- inviter
        member_id  TEXT,                      -- the roster row being claimed, NULL for an open invite
        created_at TIMESTAMPTZ DEFAULT now(),
        expires_at TIMESTAMPTZ,
        claimed_by TEXT,                      -- the account that claimed it
        claimed_at TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_invite_tokens_user
        ON invite_tokens (user_id, created_at);

    -- Circle requests (beta-v1 sprint 2). "Type an email, and if that person
    -- is already an MVP user, pull them from the system instead of inviting
    -- them." A match does NOT create the mutual link - it creates a PENDING
    -- request here, and only the recipient's accept binds
    -- household_members.member_user_id on both sides. Same authorization
    -- primitive as invite_tokens, with the consent step made explicit.
    --
    -- from_member_id is the REQUESTER's own roster row (nullable): the row is
    -- created up front so the contacts list can show a pending contact, but a
    -- request may outlive it (the requester can delete the member).
    -- No semicolons anywhere in these comments - the bootstrap splits the DDL
    -- constant on the semicolon, so one inside a comment truncates a statement.
    CREATE TABLE IF NOT EXISTS circle_requests (
        id             TEXT PRIMARY KEY,       -- stable uuid
        from_user_id   TEXT NOT NULL,          -- who asked
        to_user_id     TEXT NOT NULL,          -- who must consent
        from_member_id TEXT,                   -- requester's household_members.id, NULL if it went away
        status         TEXT NOT NULL DEFAULT 'pending',  -- pending|accepted|declined
        created_at     TIMESTAMPTZ DEFAULT now(),
        responded_at   TIMESTAMPTZ
    );

    -- The inbox query: "my pending inbound requests".
    CREATE INDEX IF NOT EXISTS idx_circle_requests_to
        ON circle_requests (to_user_id, status);

    CREATE INDEX IF NOT EXISTS idx_circle_requests_from
        ON circle_requests (from_user_id, status);
    """

    # Family Companion (kid agent + handoff). Real tables, not blobs:
    # configs are versioned with content-hash; messages are append-only;
    # credentials and moderation events get their own rows.
    KID_DDL = """
    CREATE TABLE IF NOT EXISTS kid_agent_configs (
        id              TEXT PRIMARY KEY,           -- uuid
        user_id         TEXT NOT NULL,
        kid_name        TEXT NOT NULL,
        version         INTEGER NOT NULL,
        invariants_json JSON NOT NULL,              -- structured: tools, blocklist, goals, voice_template
        free_text_brief TEXT NOT NULL DEFAULT '',
        system_prompt   TEXT NOT NULL,
        content_hash    TEXT NOT NULL,
        model           TEXT NOT NULL,
        enabled         BOOLEAN NOT NULL DEFAULT FALSE,
        created_at      TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_kid_agent_configs_user_kid
        ON kid_agent_configs (user_id, kid_name, version);

    -- One row per (user, kid, version). DB-level guard against the check+insert
    -- TOCTOU race in save_kid_agent_config (B-9): two concurrent writers that
    -- read the same max(version) can't both land the same next version.
    CREATE UNIQUE INDEX IF NOT EXISTS uq_kid_agent_configs_version
        ON kid_agent_configs (user_id, kid_name, version);

    CREATE TABLE IF NOT EXISTS kid_messages (
        id                TEXT PRIMARY KEY,         -- uuid
        agent_id          TEXT NOT NULL,            -- references kid_agent_configs.id
        thread_id         TEXT NOT NULL DEFAULT 'default',
        role              TEXT NOT NULL,            -- 'user' | 'assistant' | 'system'
        content           TEXT NOT NULL,
        moderation_score  DOUBLE,
        age_score         DOUBLE,
        voice_score       DOUBLE,
        parent_flagged    BOOLEAN NOT NULL DEFAULT FALSE,
        created_at        TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_kid_messages_agent_thread
        ON kid_messages (agent_id, thread_id, created_at);

    CREATE TABLE IF NOT EXISTS kid_credentials (
        user_id          TEXT NOT NULL,
        kid_name         TEXT NOT NULL,
        pin_hash         TEXT NOT NULL,             -- bcrypt hash (salt embedded)
        last_rotated_at  TIMESTAMPTZ DEFAULT now(),
        PRIMARY KEY (user_id, kid_name)
    );

    CREATE TABLE IF NOT EXISTS moderation_events (
        id                  TEXT PRIMARY KEY,       -- uuid
        user_id             TEXT NOT NULL,
        kid_name            TEXT NOT NULL,
        agent_id            TEXT,
        message_id          TEXT,
        severity            TEXT NOT NULL,          -- 'low' | 'medium' | 'high' | 'crisis'
        category            TEXT NOT NULL,          -- e.g., 'self_harm' | 'age_inappropriate' | 'jailbreak' | 'voice_drift'
        action              TEXT NOT NULL,          -- 'allowed' | 'blocked_input' | 'blocked_output' | 'crisis_routed'
        details             JSON,
        parent_notified_at  TIMESTAMPTZ,
        created_at          TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_moderation_events_user_kid
        ON moderation_events (user_id, kid_name, created_at);

    -- Crisis locks: when an input or output trips a crisis pattern, we lock
    -- the agent until a parent explicitly revives it. Replaces the in-process
    -- _killed_agents set, which evaporated on every Railway restart. agent_id
    -- references kid_agent_configs.id, one row per lock cycle.
    CREATE TABLE IF NOT EXISTS kid_agent_crisis_locks (
        agent_id     TEXT PRIMARY KEY,
        user_id      TEXT NOT NULL,
        kid_name     TEXT NOT NULL,
        locked_at    TIMESTAMPTZ DEFAULT now(),
        category     TEXT NOT NULL,
        severity     TEXT NOT NULL,
        reason       TEXT NOT NULL,
        revived_at   TIMESTAMPTZ,
        revived_by   TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_crisis_locks_user_kid
        ON kid_agent_crisis_locks (user_id, kid_name);

    -- PRIMARY KEY column stores sha256(raw_token) hex, NOT the raw token itself.
    -- Clients hold the raw token. Server only sees the hash at rest.
    -- Older plaintext rows are tolerated by the schema, but the runtime lookup
    -- requires expires_at to be set, so legacy rows fail closed and force re-issue.
    CREATE TABLE IF NOT EXISTS auth_tokens (
        token         TEXT PRIMARY KEY,
        user_id       TEXT NOT NULL,
        created_at    TIMESTAMPTZ DEFAULT now(),
        expires_at    TIMESTAMPTZ,
        last_used_at  TIMESTAMPTZ,
        revoked_at    TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_auth_tokens_user ON auth_tokens (user_id);

    -- Auth v1 (Phase 2). One row per parent account. user_id stays the same
    -- soft FK used everywhere else (legacy name for grandfathered users, uuid
    -- hex for new signups). analytics_id is a distinct opaque id sent to
    -- product analytics so PII never keys events. Mirrored in migration v12.
    CREATE TABLE IF NOT EXISTS user_accounts (
        user_id       TEXT PRIMARY KEY,
        analytics_id  TEXT UNIQUE,
        display_name  TEXT,
        primary_email TEXT,
        created_at    TIMESTAMPTZ DEFAULT now()
    );

    -- Provider identities (Sign in with Apple / Google) linked to an account.
    -- provider_sub is the stable subject from the IdP. Migration v13.
    CREATE TABLE IF NOT EXISTS auth_identities (
        id             TEXT PRIMARY KEY,
        user_id        TEXT NOT NULL,
        provider       TEXT NOT NULL,
        provider_sub   TEXT NOT NULL,
        email          TEXT,
        email_verified BOOLEAN DEFAULT false,
        created_at     TIMESTAMPTZ DEFAULT now(),
        last_login_at  TIMESTAMPTZ,
        UNIQUE (provider, provider_sub)
    );

    CREATE INDEX IF NOT EXISTS idx_auth_identities_user ON auth_identities (user_id);

    -- Rotating refresh tokens. token_hash is sha256 of the raw token (raw lives
    -- only on the device). A row with rotated_at/revoked_at set that is
    -- presented again triggers reuse detection: the whole family_id is revoked.
    -- Migration v14.
    CREATE TABLE IF NOT EXISTS refresh_tokens (
        id           TEXT PRIMARY KEY,
        family_id    TEXT NOT NULL,
        user_id      TEXT NOT NULL,
        token_hash   TEXT UNIQUE NOT NULL,
        platform     TEXT,
        device_name  TEXT,
        created_at   TIMESTAMPTZ DEFAULT now(),
        last_used_at TIMESTAMPTZ,
        expires_at   TIMESTAMPTZ,
        rotated_at   TIMESTAMPTZ,
        replaced_by  TEXT,
        revoked_at   TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens (user_id);
    CREATE INDEX IF NOT EXISTS idx_refresh_tokens_family ON refresh_tokens (family_id);

    -- APNs device tokens for crisis-lock push notifications (migration v10).
    CREATE TABLE IF NOT EXISTS push_device_tokens (
        token         TEXT PRIMARY KEY,           -- the APNs device token
        user_id       TEXT NOT NULL,
        platform      TEXT,                        -- ios
        created_at    TIMESTAMPTZ DEFAULT now(),
        last_seen_at  TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_push_device_tokens_user ON push_device_tokens (user_id);

    -- Phase 3b: scoped, read-only, expiring share links (nanny/therapist views).
    -- Only the sha256 hash is stored like auth_tokens, the raw token lives in the
    -- URL. `scope` prunes which plan data the public view exposes.
    CREATE TABLE IF NOT EXISTS share_tokens (
        token       TEXT PRIMARY KEY,            -- sha256 of the raw link token
        user_id     TEXT NOT NULL,
        scope       TEXT NOT NULL,               -- full | logistics | therapy
        label       TEXT,                         -- e.g. "Nanny", free-text
        created_at  TIMESTAMPTZ DEFAULT now(),
        expires_at  TIMESTAMPTZ,
        revoked_at  TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_share_tokens_user ON share_tokens (user_id);

    CREATE TABLE IF NOT EXISTS consent_records (
        id                 TEXT PRIMARY KEY,        -- uuid
        user_id            TEXT NOT NULL,
        parent_name        TEXT,
        parent_email       TEXT,
        kid_age_band       TEXT,
        agreement_version  TEXT NOT NULL,
        accepted_at        TIMESTAMPTZ DEFAULT now(),
        ip_address         TEXT,
        user_agent         TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_consent_user_version
        ON consent_records (user_id, agreement_version, accepted_at);

    CREATE TABLE IF NOT EXISTS daily_summaries (
        id            TEXT PRIMARY KEY,        -- uuid
        user_id       TEXT NOT NULL,
        kid_name      TEXT NOT NULL,
        summary_date  DATE NOT NULL,
        agent_id      TEXT,
        message_count INTEGER NOT NULL,
        headline      TEXT NOT NULL,           -- "Today Nova talked to Julio for 12 minutes about X."
        curiosity     TEXT,                    -- one quoted moment
        frustration   TEXT,                    -- one quoted moment
        prompt_for_parent TEXT,                -- "Ask Julio about the multiplication problem..."
        full_json     JSON,                    -- raw LLM output for audit
        created_at    TIMESTAMPTZ DEFAULT now()
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_summaries_unique
        ON daily_summaries (user_id, kid_name, summary_date);

    -- Append-only audit log for sensitive parent actions: family delete,
    -- export, crisis revive. Survives every other table delete.
    CREATE TABLE IF NOT EXISTS audit_events (
        id          TEXT PRIMARY KEY,
        user_id     TEXT,
        actor       TEXT,
        action      TEXT NOT NULL,
        details     JSON,
        created_at  TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_audit_events_user
        ON audit_events (user_id, created_at);

    -- LEGACY (voice v1): per-user, per-day TTS character counter. The v1 TTS
    -- endpoints and cap logic were removed with the ConvAI (v2) migration but
    -- the table DDL stays so existing deployments keep bootstrapping cleanly.
    -- (Avoid semicolons inside comments here - the bootstrap splits this DDL
    -- string on the semicolon character.)
    CREATE TABLE IF NOT EXISTS tts_usage_daily (
        user_id  VARCHAR NOT NULL,
        date     DATE    NOT NULL,
        chars    INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id, date)
    );

    CREATE INDEX IF NOT EXISTS idx_tts_usage_daily_date
        ON tts_usage_daily (date);
    """

    # Activity planning + Chief-of-Staff. Brand-new tables, added the same way
    # as KID_DDL (CREATE IF NOT EXISTS in this string + bootstrap below) — no
    # migration rows are needed because these tables don't pre-exist on any
    # deployment, so CREATE IF NOT EXISTS converges every DB on next boot. The
    # migration framework is only for ALTERs on already-shipped tables (v4/v5).
    # (No semicolons inside comments - the bootstrap splits this DDL on ';'.)
    ACTIVITY_DDL = """
    -- Durable background-job state for a deep-research discovery run.
    CREATE TABLE IF NOT EXISTS research_runs (
        id              TEXT PRIMARY KEY,           -- run_id (uuid)
        user_id         TEXT NOT NULL,
        status          TEXT NOT NULL DEFAULT 'queued',  -- queued|running|done|failed|canceled
        location_json   JSON NOT NULL,              -- {postal_code, country, radius_km}
        kids_json       JSON NOT NULL,              -- snapshot of kid profiles used (audit/repro)
        params_json     JSON,                       -- season, categories, max_queries, etc.
        progress_json   JSON,                       -- {phase, queries_total, queries_done, candidates_found}
        candidate_count INTEGER NOT NULL DEFAULT 0,
        error           TEXT,
        created_at      TIMESTAMPTZ DEFAULT now(),
        started_at      TIMESTAMPTZ,
        finished_at     TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_research_runs_user ON research_runs (user_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_research_runs_status ON research_runs (status);

    -- Discovered candidates - the durable output of the research graph.
    CREATE TABLE IF NOT EXISTS activity_candidates (
        id            TEXT PRIMARY KEY,             -- uuid
        run_id        TEXT NOT NULL,                -- references research_runs.id
        user_id       TEXT NOT NULL,
        kid_name      TEXT,                         -- best-fit kid, NULL = family-wide
        name          TEXT NOT NULL,
        provider      TEXT,
        category      TEXT,                         -- camp|class|program|event|weekend
        age_min       DOUBLE,
        age_max       DOUBLE,
        start_date    DATE,
        end_date      DATE,
        schedule_text TEXT,
        price_text    TEXT,
        price_amount  DOUBLE,
        location_text TEXT,
        city          TEXT,                         -- town/city, for filtering (migration v8)
        region        TEXT,                         -- state/region abbr, e.g. CA
        distance_mi   DOUBLE,                        -- miles from the parent ZIP, for Nearest sort (migration v9)
        signup_url    TEXT,
        source_url    TEXT,                         -- provenance page we extracted from
        contact_json  JSON,                         -- {name, phone, email, person}
        fit_score     DOUBLE,
        raw_json      JSON,                         -- full extracted blob (audit)
        created_at    TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_activity_candidates_run ON activity_candidates (run_id);
    CREATE INDEX IF NOT EXISTS idx_activity_candidates_user ON activity_candidates (user_id, created_at);

    -- Parent's selections, with the artifact's granular confirmed/pending status.
    CREATE TABLE IF NOT EXISTS tracked_activities (
        id                TEXT PRIMARY KEY,
        user_id           TEXT NOT NULL,
        kid_name          TEXT,
        candidate_id      TEXT,                     -- nullable: may be added manually / from ingest
        name              TEXT NOT NULL,
        provider          TEXT,
        activity_type     TEXT,                     -- camp|extracurricular|outing|school_event|trip (see app/cos/verticals.py) NULL degrades to camp. Index lives in migration v16, not here
        week_start        DATE,                     -- derived anchor for week_block items (= start_date). Write via set_activity_dates, never directly
        start_date        DATE,                     -- v17 date model. week_block: the week anchor. recurring_weekly: active-from
        end_date          DATE,                     -- week_block: last day (backfilled rows are FABRICATED start+4d). recurring_weekly: active-until
        rrule             TEXT,                     -- RFC-5545, e.g. FREQ=WEEKLY BYDAY=TU. SINGLE SOURCE OF TRUTH for recurrence. weekly-only enforced at the tool layer
        recur_time        TEXT,                     -- 'HH:MM' local start for rrule occurrences
        recur_duration_min INTEGER,                 -- occurrence length in minutes
        status            TEXT NOT NULL DEFAULT 'exploring',
            -- reference|exploring|interested|signed_up|confirmed|pending_eligibility|waitlisted|declined|done
            -- exploring (R1) is the considering-not-decided default for pinned candidates + ingested items
        pending_reason    TEXT,
        price_amount      DOUBLE,
        price_status      TEXT NOT NULL DEFAULT 'tbd',  -- confirmed|tbd
        signup_url        TEXT,
        contact_json      JSON,
        carpool_with      TEXT,
        details_json      JSON,                     -- dates/price/location snapshot at track time
        notes             TEXT,
        decision_rationale TEXT,                    -- the artifact's "decision log"
        created_at        TIMESTAMPTZ DEFAULT now(),
        updated_at        TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_tracked_activities_user_status ON tracked_activities (user_id, status);
    CREATE INDEX IF NOT EXISTS idx_tracked_activities_user_week ON tracked_activities (user_id, week_start);

    -- Week-keyed calendar. The side-by-side weekly grid and the per-child daily
    -- views are both queries over this one table.
    CREATE TABLE IF NOT EXISTS calendar_entries (
        id            TEXT PRIMARY KEY,
        user_id       TEXT NOT NULL,
        kid_name      TEXT,
        activity_id   TEXT,                         -- nullable link to tracked_activities.id
        title         TEXT NOT NULL,
        week_start    DATE,
        start_ts      TIMESTAMPTZ,
        end_ts        TIMESTAMPTZ,
        all_day       BOOLEAN NOT NULL DEFAULT FALSE,
        location_text TEXT,
        kind          TEXT NOT NULL DEFAULT 'camp', -- camp|class|appointment|therapy|blackout|holiday|external
        status        TEXT NOT NULL DEFAULT 'confirmed',  -- confirmed|pending|tbd
        source        TEXT NOT NULL DEFAULT 'manual',     -- manual|research|email|photo|cos_agent|gcal
        -- Two-way Google Calendar sync (R4 part 2). provider_event_id is the
        -- Google event id (set after we push, or on a pulled external event).
        -- synced_at is the last reconcile (NULL means never pushed). A row is
        -- dirty (needs push) when updated_at is later than synced_at. The
        -- (user_id, provider_event_id) index lives in migration v7 because the
        -- columns are added there on existing DBs.
        provider_event_id TEXT,
        synced_at     TIMESTAMPTZ,
        created_at    TIMESTAMPTZ DEFAULT now(),
        updated_at    TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_calendar_entries_user ON calendar_entries (user_id, start_ts);
    CREATE INDEX IF NOT EXISTS idx_calendar_entries_user_week ON calendar_entries (user_id, week_start);

    -- Standing/recurring appointments (e.g. weekly therapy). Cancellations and
    -- make-ups are recorded as calendar_entries overrides referencing this row.
    -- Rows with activity_id are DERIVED from that activity's rrule (v17): they
    -- are regenerated by set_activity_dates on change, never hand-edited —
    -- "practice moved to Thursdays" edits the ACTIVITY and derivation reconciles.
    CREATE TABLE IF NOT EXISTS recurring_appointments (
        id            TEXT PRIMARY KEY,
        user_id       TEXT NOT NULL,
        kid_name      TEXT,                         -- or 'both'
        title         TEXT NOT NULL,
        provider_name TEXT,
        weekday       INTEGER,                      -- 0=Mon .. 6=Sun
        start_time    TEXT,                         -- 'HH:MM'
        end_time      TEXT,
        transporter   TEXT,
        notes         TEXT,
        active_from   DATE,
        active_to     DATE,
        activity_id   TEXT,                         -- back-reference: derived from tracked_activities.rrule (v17)
        created_at    TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_recurring_appointments_user ON recurring_appointments (user_id);

    -- People who transport/attend (parent, nanny, therapist, carpool parents).
    CREATE TABLE IF NOT EXISTS caregivers (
        id                      TEXT PRIMARY KEY,
        user_id                 TEXT NOT NULL,
        name                    TEXT NOT NULL,
        role                    TEXT NOT NULL DEFAULT 'other',  -- parent|nanny|therapist|family_friend|other
        contact_json            JSON,
        default_availability_json JSON,
        notes                   TEXT,
        created_at              TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_caregivers_user ON caregivers (user_id);

    -- Per-week coverage. A status='gap' row is the artifact's red COVERAGE GAP flag.
    CREATE TABLE IF NOT EXISTS logistics_assignments (
        id                TEXT PRIMARY KEY,
        user_id           TEXT NOT NULL,
        week_start        DATE,
        kid_name          TEXT,
        calendar_entry_id TEXT,                     -- nullable link to calendar_entries.id
        task              TEXT NOT NULL,            -- dropoff|pickup|transport|attend
        caregiver_id      TEXT,                     -- nullable until assigned
        status            TEXT NOT NULL DEFAULT 'tbd',  -- assigned|gap|tbd
        notes             TEXT,
        created_at        TIMESTAMPTZ DEFAULT now(),
        updated_at        TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_logistics_user_week ON logistics_assignments (user_id, week_start);

    -- To-dos / follow-ups (payments due, forms, welcome-letter actions).
    CREATE TABLE IF NOT EXISTS todo_items (
        id                 TEXT PRIMARY KEY,
        user_id            TEXT NOT NULL,
        kid_name           TEXT,
        activity_id        TEXT,                    -- nullable link to tracked_activities.id
        kind               TEXT NOT NULL DEFAULT 'task',  -- payment|form|action|task
        title              TEXT NOT NULL,
        detail             TEXT,
        due_date           DATE,
        status             TEXT NOT NULL DEFAULT 'open',  -- open|done|snoozed|dismissed
        source             TEXT NOT NULL DEFAULT 'manual',  -- manual|email|photo|research|cos_agent
        source_artifact_id TEXT,                    -- nullable link to ingest_artifacts.id
        created_at         TIMESTAMPTZ DEFAULT now(),
        updated_at         TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_todo_items_user ON todo_items (user_id, status, due_date);

    -- Ingested artifacts - multimodal (text paste, forwarded iMessage, flyer
    -- photo, screenshot, signed-form pdf, gmail). raw_text for text sources,
    -- blob_ref for stored images.
    CREATE TABLE IF NOT EXISTS ingest_artifacts (
        id             TEXT PRIMARY KEY,
        user_id        TEXT NOT NULL,
        source         TEXT NOT NULL,               -- paste|imessage|photo|screenshot|pdf|gmail|forward
        media_type     TEXT NOT NULL DEFAULT 'text',  -- text|image|pdf
        blob_ref       TEXT,                        -- path/key for stored image, NULL for text
        subject        TEXT,
        sender         TEXT,
        received_at    TIMESTAMPTZ,
        raw_text       TEXT,
        extracted_json JSON,                        -- structured ExtractedActivity dump
        extract_status TEXT NOT NULL DEFAULT 'pending',  -- pending|extracted|failed
        links_json     JSON,                        -- [{label, url}]
        external_id    TEXT,                        -- provider message id for R3 Gmail dedup (NULL for paste/photo)
        created_at     TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_ingest_artifacts_user ON ingest_artifacts (user_id, created_at);
    -- NOTE: the external_id dedup index is created in migration v6 (not here) —
    -- existing tables get the column via the migration, which runs AFTER this DDL.

    -- Chief-of-staff chat transcript (append-only, mirrors kid_messages).
    CREATE TABLE IF NOT EXISTS cos_messages (
        id          TEXT PRIMARY KEY,
        user_id     TEXT NOT NULL,
        thread_id   TEXT NOT NULL DEFAULT 'default',
        role        TEXT NOT NULL,                  -- user|assistant|system
        content     TEXT NOT NULL,
        created_at  TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_cos_messages_user_thread ON cos_messages (user_id, thread_id, created_at);

    -- Google OAuth tokens (Phase 3). Refresh token encrypted at rest.
    -- R5: provider-agnostic connected accounts (generalizes the old
    -- google_oauth_tokens). One row per (user_id, provider, kind) so a user can
    -- connect Gmail for email and Google Calendar for calendar independently, and
    -- other providers (microsoft, apple) drop in later. Refresh token is
    -- Fernet-encrypted at rest (see app/integrations/crypto.py).
    CREATE TABLE IF NOT EXISTS integration_accounts (
        id                      TEXT PRIMARY KEY,
        user_id                 TEXT NOT NULL,
        provider                TEXT NOT NULL,             -- google (v1) | microsoft | apple
        kind                    TEXT NOT NULL,             -- email | calendar
        account_email           TEXT,
        scopes                  TEXT,                      -- space-separated granted scopes
        encrypted_refresh_token TEXT NOT NULL,
        status                  TEXT NOT NULL DEFAULT 'connected',  -- connected | revoked | error
        connected_at            TIMESTAMPTZ DEFAULT now(),
        last_sync_at            TIMESTAMPTZ,
        revoked_at              TIMESTAMPTZ
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_integration_accounts_uniq
        ON integration_accounts (user_id, provider, kind);

    CREATE INDEX IF NOT EXISTS idx_integration_accounts_user
        ON integration_accounts (user_id);

    -- R3: durable job state for the daily Gmail sync agent (mirrors research_runs).
    CREATE TABLE IF NOT EXISTS email_sync_runs (
        id                TEXT PRIMARY KEY,
        user_id           TEXT NOT NULL,
        status            TEXT NOT NULL DEFAULT 'queued',  -- queued|running|done|failed
        trigger           TEXT NOT NULL DEFAULT 'manual',  -- manual|scheduled
        messages_seen     INTEGER NOT NULL DEFAULT 0,
        activities_touched INTEGER NOT NULL DEFAULT 0,
        progress_json     JSON,
        error             TEXT,
        created_at        TIMESTAMPTZ DEFAULT now(),
        started_at        TIMESTAMPTZ,
        finished_at       TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_email_sync_runs_status ON email_sync_runs (status, created_at);

    -- R4 part 2: durable job state for the two-way Google Calendar sync daemon
    -- (mirrors email_sync_runs). pushed and pulled count entries reconciled in
    -- each direction.
    CREATE TABLE IF NOT EXISTS calendar_sync_runs (
        id                TEXT PRIMARY KEY,
        user_id           TEXT NOT NULL,
        status            TEXT NOT NULL DEFAULT 'queued',  -- queued|running|done|failed
        trigger           TEXT NOT NULL DEFAULT 'manual',  -- manual|scheduled
        pushed            INTEGER NOT NULL DEFAULT 0,
        pulled            INTEGER NOT NULL DEFAULT 0,
        progress_json     JSON,
        error             TEXT,
        created_at        TIMESTAMPTZ DEFAULT now(),
        started_at        TIMESTAMPTZ,
        finished_at       TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS idx_calendar_sync_runs_status ON calendar_sync_runs (status, created_at);

    -- R3: generic operator/agent config (key/value JSON). Holds the email-sync
    -- and calendar-sync schedules plus each scheduler's once-a-day guard.
    CREATE TABLE IF NOT EXISTS agent_config (
        key        TEXT PRIMARY KEY,
        value      JSON NOT NULL,
        updated_at TIMESTAMPTZ DEFAULT now()
    );

    -- Registration-window watchlist (vertical expansion Phase 4, GTM Pillar 1).
    -- A window = "registration for X opens at T" that the parent must not miss.
    -- Buckets like "opening soon" are DERIVED from opens_at at read time and
    -- never stored. status is watching, dismissed or closed.
    CREATE TABLE IF NOT EXISTS registration_windows (
        id               TEXT PRIMARY KEY,
        user_id          TEXT NOT NULL,
        activity_id      TEXT,                     -- nullable link to tracked_activities.id
        provider         TEXT,
        signup_url       TEXT,
        opens_at         TIMESTAMPTZ,              -- UTC. Local rules use tz
        tz               TEXT,                     -- IANA, from the family ZIP
        opens_time_known BOOLEAN NOT NULL DEFAULT FALSE,
        closes_at        TIMESTAMPTZ,
        source           TEXT NOT NULL DEFAULT 'manual',      -- manual, email or agent_research
        confidence       TEXT NOT NULL DEFAULT 'confirmed',   -- confirmed or estimated
        status           TEXT NOT NULL DEFAULT 'watching',
        metro            TEXT,
        created_at       TIMESTAMPTZ DEFAULT now(),
        updated_at       TIMESTAMPTZ DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS idx_registration_windows_user ON registration_windows (user_id, status);
    CREATE INDEX IF NOT EXISTS idx_registration_windows_status ON registration_windows (status, opens_at);

    -- Append-only delivery log. The (window_id, kind, opens_at_snapshot)
    -- NOT-EXISTS due-selection is simultaneously restart idempotency, re-arm
    -- on date change (new opens_at = new snapshot) and the audit trail.
    CREATE TABLE IF NOT EXISTS window_notifications (
        id                TEXT PRIMARY KEY,
        window_id         TEXT NOT NULL,
        kind              TEXT NOT NULL,            -- t_minus_7 or day_of
        opens_at_snapshot TIMESTAMPTZ,
        sent_at           TIMESTAMPTZ DEFAULT now(),
        transport         TEXT,                     -- push or todo_only
        outcome           TEXT                      -- sent, no_push_token, failed or disabled
    );

    CREATE INDEX IF NOT EXISTS idx_window_notifications_window ON window_notifications (window_id, kind);
    """

    # Every table that must survive a volume rebuild, mapped to its parquet
    # snapshot filename. Used for both export (A2/A3) and bootstrap-merge (A2).
    # auth_tokens is safe to export — only sha256 hashes are stored at rest.
    BOOTSTRAP_TABLES = [
        ("agent_family_fences", "agent_family_fences.parquet"),
        ("agent_runs", "agent_runs.parquet"),
        ("agent_operation_receipts", "agent_operation_receipts.parquet"),
        ("user_data", "mvp.parquet"),
        ("categories", "categories.parquet"),
        ("articles", "articles.parquet"),
        ("kid_agent_configs", "kid_agent_configs.parquet"),
        ("kid_messages", "kid_messages.parquet"),
        ("kid_credentials", "kid_credentials.parquet"),
        ("moderation_events", "moderation_events.parquet"),
        ("kid_agent_crisis_locks", "kid_agent_crisis_locks.parquet"),
        ("consent_records", "consent_records.parquet"),
        ("daily_summaries", "daily_summaries.parquet"),
        ("audit_events", "audit_events.parquet"),
        ("auth_tokens", "auth_tokens.parquet"),
        # Auth v1 (Phase 2). refresh_tokens/user_accounts hold only hashes +
        # opaque ids; auth_identities holds provider subs + emails (same
        # sensitivity as consent_records, which is already exported).
        ("user_accounts", "user_accounts.parquet"),
        ("auth_identities", "auth_identities.parquet"),
        ("refresh_tokens", "refresh_tokens.parquet"),
        ("push_device_tokens", "push_device_tokens.parquet"),
        ("share_tokens", "share_tokens.parquet"),
        ("tts_usage_daily", "tts_usage_daily.parquet"),
        # Activity planning + Chief-of-Staff (user state — exclude from image
        # build context in .dockerignore so local data never overwrites prod).
        ("research_runs", "research_runs.parquet"),
        ("activity_candidates", "activity_candidates.parquet"),
        ("tracked_activities", "tracked_activities.parquet"),
        ("calendar_entries", "calendar_entries.parquet"),
        ("recurring_appointments", "recurring_appointments.parquet"),
        ("caregivers", "caregivers.parquet"),
        ("logistics_assignments", "logistics_assignments.parquet"),
        ("todo_items", "todo_items.parquet"),
        ("ingest_artifacts", "ingest_artifacts.parquet"),
        ("cos_messages", "cos_messages.parquet"),
        ("integration_accounts", "integration_accounts.parquet"),
        ("email_sync_runs", "email_sync_runs.parquet"),
        ("calendar_sync_runs", "calendar_sync_runs.parquet"),
        ("agent_config", "agent_config.parquet"),
        # Registration-window watchlist (Phase 4). A volume rebuild that loses
        # these silently deletes the product's core promise — export/bootstrap
        # them like every other user-state table.
        ("registration_windows", "registration_windows.parquet"),
        ("window_notifications", "window_notifications.parquet"),
        # Legal docs (CMS-published state, NOT git-restorable) + acceptances
        # (user audit state). Both excluded from the image in .dockerignore.
        ("legal_documents", "legal_documents.parquet"),
        ("legal_acceptances", "legal_acceptances.parquet"),
        # Saved items (user state).
        ("saved_items", "saved_items.parquet"),
        # First-run agent warm-up: the durable job rows + the coach nudges they
        # produce. Both are user state — a volume rebuild that seeded them from
        # a dev machine would show one family's nudge to another.
        ("onboarding_warmup_runs", "onboarding_warmup_runs.parquet"),
        ("coach_nudges", "coach_nudges.parquet"),
        # Household members / Circle. User state AND the authorization source
        # for every Circle conversation — a volume rebuild that lost it would
        # silently close every parent's Circle.
        ("household_members", "household_members.parquet"),
        # Circle conversations (beta-v1 Phase 1) — the group threads that
        # replaced the public board. User state, and invite_tokens is an
        # authorization primitive: losing it strands half-claimed links.
        ("circle_conversations", "circle_conversations.parquet"),
        ("circle_participants", "circle_participants.parquet"),
        ("circle_messages", "circle_messages.parquet"),
        ("invite_tokens", "invite_tokens.parquet"),
        # Circle requests (beta-v1 sprint 2) — the email-match consent step.
        # A pending request IS a user's intent; losing it strands the ask.
        ("circle_requests", "circle_requests.parquet"),
    ]

    def __init__(self, db_path: Path | str | None = None) -> None:
        if db_path is None:
            # Env override lets tests / ephemeral runs point at a throwaway DB
            # without editing server wiring (avoids the single-writer lock on the
            # real data/mvp.duckdb held by a running dev server).
            env_path = os.getenv("MVP_DUCKDB_PATH")
            if env_path:
                db_path = Path(env_path)
            else:
                db_path = Path(__file__).resolve().parent.parent / "data" / "mvp.duckdb"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.parquet_dir = self.db_path.parent
        self.parquet_path = self.db_path.with_suffix(".parquet")

        self._con = _ThreadSafeConn(duckdb.connect(str(self.db_path)))
        self._con.execute(self.DDL)
        for stmt in self.CONTENT_DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self._con.execute(stmt + ";")
        for stmt in self.KID_DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self._con.execute(stmt + ";")
        for stmt in self.ACTIVITY_DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self._con.execute(stmt + ";")
        for stmt in self.LEGAL_DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self._con.execute(stmt + ";")
        for stmt in self.SAVED_DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self._con.execute(stmt + ";")
        for stmt in self.WARMUP_DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self._con.execute(stmt + ";")
        for stmt in self.HOUSEHOLD_DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self._con.execute(stmt + ";")
        for stmt in self.CIRCLE_DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self._con.execute(stmt + ";")

        # Versioned schema migrations (A1) — replaces the old bare-except ALTERs.
        from app.migrations import run_migrations
        run_migrations(self._con)

        # Bootstrap every table from its parquet snapshot using INSERT OR IGNORE
        # (A2). This is a per-table MERGE, not the old all-or-nothing count gate:
        # rows already present (by primary key) are skipped, missing rows are
        # added. Fixes both the no-backup-path gap for kid tables and the
        # stranded-user bug where one existing row skipped the whole import.
        # Path is a bound parameter (H-10); table names are a fixed allowlist.
        for table, pq_name in self.BOOTSTRAP_TABLES:
            pq = self.parquet_dir / pq_name
            if not pq.exists():
                continue
            try:
                # SELECT * blows up when a migration adds a column that the
                # snapshot parquet doesn't have yet (e.g. categories.parent_id
                # after migration v4). Compute the intersection of parquet
                # columns × table columns and INSERT with an explicit column
                # list — the missing columns get their default (NULL for
                # nullable cols, which is what we want for additive migrations).
                parquet_cols = [
                    r[0] for r in self._con.execute(
                        "SELECT column_name FROM (DESCRIBE SELECT * FROM read_parquet(?))",
                        [str(pq)],
                    ).fetchall()
                ]
                table_cols = [
                    r[0] for r in self._con.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = ? ORDER BY ordinal_position",
                        [table],
                    ).fetchall()
                ]
                shared = [c for c in table_cols if c in parquet_cols]
                if not shared:
                    logger.warning(
                        f"[duckdb] bootstrap of {table} from {pq_name} skipped: "
                        f"no shared columns (parquet={parquet_cols}, table={table_cols})"
                    )
                    continue
                cols_sql = ", ".join(f'"{c}"' for c in shared)
                self._con.execute(
                    f"INSERT OR IGNORE INTO {table} ({cols_sql}) "
                    f"SELECT {cols_sql} FROM read_parquet(?)",
                    [str(pq)],
                )
                dropped = set(parquet_cols) - set(shared)
                added = set(table_cols) - set(parquet_cols)
                drift_note = ""
                if dropped or added:
                    drift_note = (
                        f" (drift: parquet-only={sorted(dropped)}, "
                        f"table-only={sorted(added)})"
                    )
                logger.info(
                    f"[duckdb] bootstrap-merged {table} from {pq_name}{drift_note}"
                )
            except Exception as exc:
                # Any remaining failure — disk-full, corrupt parquet — shouldn't
                # take the whole boot down. The live table keeps whatever it
                # already has (which on a fresh deploy is "empty"; on a warm
                # restart is "the last committed state").
                logger.warning(f"[duckdb] bootstrap of {table} from {pq_name} skipped: {exc}")

        # A partial export can refresh a parent snapshot while leaving its
        # old child snapshot. Clean only the known required joins, after every
        # table has loaded, so those orphan records cannot resurrect.
        self._remove_orphaned_family_children()

        # A crash after the deletion commit but before snapshot export leaves
        # old parquet rows. The durable tombstone wins over those snapshots.
        for recovered_user, permanently_deleted, snapshot_pending in self._con.execute(
            "SELECT user_id, deleted, snapshot_purge_pending FROM agent_family_fences "
            "WHERE deleted = TRUE OR snapshot_purge_pending = TRUE"
        ).fetchall():
            swept_tables = FAMILY_CASCADE_TABLES if permanently_deleted else [
                table for table in FAMILY_CASCADE_TABLES if table not in FAMILY_RESET_SKIP_TABLES
            ]
            has_rows = any(self._con.execute(
                f"SELECT 1 FROM {table} WHERE user_id = ? LIMIT 1", [recovered_user]
            ).fetchone() for table in swept_tables)
            if snapshot_pending or has_rows:
                cascade = self.delete_family if permanently_deleted else self.reset_family
                cascade(user_id=recovered_user, actor="snapshot-recovery")

        # Seed legal documents from repo markdown AFTER the bootstrap merge, so
        # a slug that already has a published row (restored from parquet, or
        # CMS-published) is never re-seeded — otherwise a redeploy would
        # resurrect v1 alongside a CMS-published v2.
        try:
            self._seed_legal_documents()
        except Exception as exc:
            logger.warning(f"[duckdb] legal-docs seed skipped: {exc}")

        logger.info(f"[duckdb] opened {self.db_path}")

    def _seed_legal_documents(self) -> None:
        """Insert each mvp-backend/legal/*.md as published v1 for slugs that
        have NO published row yet (slug-presence check, never row-count)."""
        import uuid
        legal_dir = Path(__file__).resolve().parent.parent / "legal"
        if not legal_dir.is_dir():
            return
        for md_path in sorted(legal_dir.glob("*.md")):
            slug = md_path.stem
            existing = self._con.execute(
                "SELECT count(*) FROM legal_documents WHERE slug = ? AND published_at IS NOT NULL",
                [slug],
            ).fetchone()
            if existing and existing[0] > 0:
                continue
            meta, body = _parse_legal_frontmatter(md_path.read_text(encoding="utf-8"))
            self._con.execute(
                """
                INSERT INTO legal_documents (
                    id, slug, version, title, body_md, effective_date,
                    requires_reacceptance, published_at, published_by, is_current
                ) VALUES (?, ?, ?, ?, ?, ?, false, now(), 'seed', true)
                """,
                [
                    f"legal-{uuid.uuid4().hex[:12]}", slug,
                    meta.get("version", "1.0"), meta.get("title", slug),
                    body, meta.get("effective_date"),
                ],
            )
            logger.info(f"[duckdb] seeded legal doc '{slug}' v{meta.get('version', '1.0')}")

    # ── StorageBackend interface ──────────────────────────────────────

    def assert_family_writable(self, user_id: str, generation: int | None = None) -> int:
        """Called while holding the transaction lock, before any harness write."""
        row = self._con.execute(
            "SELECT generation, deleted, checkpoint_purge_pending, snapshot_purge_pending FROM agent_family_fences WHERE user_id = ?", [user_id]
        ).fetchone()
        current = row[0] if row else 0
        if (row and (row[1] or row[2] or row[3])) or (generation is not None and generation != current):
            raise PermissionError("Family was deleted, reset, or is awaiting durable cleanup")
        return current

    _FAMILY_CHILD_JOINS = (
        ("kid_messages", "agent_id", "kid_agent_configs"),
        ("window_notifications", "window_id", "registration_windows"),
        ("circle_messages", "conversation_id", "circle_conversations"),
        ("circle_participants", "conversation_id", "circle_conversations"),
    )

    def _remove_orphaned_family_children(self) -> None:
        with self._con.transaction():
            for child, foreign_key, parent in self._FAMILY_CHILD_JOINS:
                self._con.execute(
                    f"DELETE FROM {child} WHERE {foreign_key} NOT IN (SELECT id FROM {parent})"
                )

    def pending_family_cleanups(self) -> List[Dict[str, Any]]:
        return [dict(user_id=row[0], generation=row[1]) for row in self._con.execute(
            "SELECT user_id, generation FROM agent_family_fences "
            "WHERE checkpoint_purge_pending = TRUE OR snapshot_purge_pending = TRUE"
        ).fetchall()]

    def refresh_family_snapshots(self, user_id: str) -> None:
        """Keep reset/deletion fenced until all snapshots are readable and clean.

        Ordinary shutdown export is best-effort. A deletion obligation is not:
        failure must survive restart and prevent stale parquet resurrection.
        """
        with self._con._lock:
            fence = self._con.execute(
                "SELECT generation, deleted, snapshot_purge_pending FROM agent_family_fences WHERE user_id=?",
                [user_id],
            ).fetchone()
            if not fence or not fence[2]:
                return
            self.export_all_parquet(strict=True)
            absent_tables = set(FAMILY_CASCADE_TABLES)
            if not fence[1]:
                absent_tables -= FAMILY_RESET_SKIP_TABLES
            for table, filename in self.BOOTSTRAP_TABLES:
                path = str(self.parquet_dir / filename)
                # Re-open every exported file, including the joined/circle
                # tables. For user-keyed swept tables also verify absence.
                self._con.execute("SELECT count(*) FROM read_parquet(?)", [path]).fetchone()
                if table in absent_tables and self._con.execute(
                    "SELECT count(*) FROM read_parquet(?) WHERE user_id=?", [path, user_id]
                ).fetchone()[0]:
                    raise RuntimeError("Snapshot still contains removed family rows")
            files = dict(self.BOOTSTRAP_TABLES)
            for child, foreign_key, parent in self._FAMILY_CHILD_JOINS:
                if self._con.execute(
                    f"SELECT count(*) FROM read_parquet(?) WHERE {foreign_key} "
                    "NOT IN (SELECT id FROM read_parquet(?))",
                    [str(self.parquet_dir / files[child]), str(self.parquet_dir / files[parent])],
                ).fetchone()[0]:
                    raise RuntimeError("Snapshot contains orphaned family child rows")
            with self._con.transaction():
                self._con.execute(
                    "UPDATE agent_family_fences SET snapshot_purge_pending=FALSE "
                    "WHERE user_id=? AND generation=?", [user_id, fence[0]],
                )
                # Publish the cleared obligation only after clean data files.
                # Failure rolls back the flag; new family writes stay blocked.
                self._export_table_atomic("agent_family_fences", self.parquet_dir / "agent_family_fences.parquet")

    def pending_checkpoint_purges(self) -> List[Dict[str, Any]]:
        return [dict(user_id=row[0], generation=row[1]) for row in self._con.execute(
            "SELECT user_id, generation FROM agent_family_fences "
            "WHERE checkpoint_purge_pending = TRUE"
        ).fetchall()]

    def mark_checkpoint_purged(self, user_id: str, generation: int | None = None) -> bool:
        query = "UPDATE agent_family_fences SET checkpoint_purge_pending = FALSE WHERE user_id = ?"
        params = [user_id]
        if generation is not None:
            query += " AND generation = ?"
            params.append(generation)
        return bool(self._con.execute(query + " RETURNING user_id", params).fetchone())

    def save_user_data(self, user_id: str, name: str, data: Dict[str, Any]) -> None:
        try:
            payload = json.dumps(data, ensure_ascii=False)
            with self._con.transaction():
                from app.services.operations import current_run
                run = current_run()
                if run and run.user_id != user_id:
                    raise PermissionError("Write tenant does not match authenticated run")
                self.assert_family_writable(user_id, run.generation if run else None)
                self._con.execute(
                    """
                    INSERT INTO user_data (user_id, name, data, updated_at)
                    VALUES (?, ?, ?, now())
                    ON CONFLICT (user_id, name)
                    DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at
                    """,
                    [user_id, name, payload],
                )
            logger.debug(f"[duckdb] saved {name} for user {user_id}")
        except Exception as exc:
            logger.error(f"[duckdb] failed to save {name} for user {user_id}: {exc}")
            raise

    def load_user_data(self, user_id: str, name: str) -> Optional[Dict[str, Any]]:
        try:
            row = self._con.execute(
                "SELECT data FROM user_data WHERE user_id = ? AND name = ?",
                [user_id, name],
            ).fetchone()
            if row is None:
                return None
            return json.loads(row[0])
        except Exception as exc:
            logger.error(f"[duckdb] failed to load {name} for user {user_id}: {exc}")
            return None

    def list_users(self) -> Iterable[str]:
        try:
            rows = self._con.execute(
                "SELECT DISTINCT user_id FROM user_data ORDER BY user_id"
            ).fetchall()
            return [r[0] for r in rows]
        except Exception as exc:
            logger.error(f"[duckdb] failed to list users: {exc}")
            return []

    # ── Content query methods ─────────────────────────────────────────

    def get_categories(self) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            "SELECT id, name, emoji, description, parent_id FROM categories ORDER BY id"
        ).fetchall()
        return [
            {"id": r[0], "name": r[1], "emoji": r[2], "description": r[3], "parent_id": r[4]}
            for r in rows
        ]

    def get_articles(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        # Compose WHERE dynamically with bound params — never f-string user
        # input. `? = ANY(tags)` is DuckDB's array-membership test (case-
        # sensitive exact match on each element).
        clauses: List[str] = []
        params: List[Any] = []
        if category:
            clauses.append("category = ?")
            params.append(category)
        if tag:
            clauses.append("? = ANY(tags)")
            params.append(tag)
        where = f"WHERE {' AND '.join(clauses)} " if clauses else ""
        params.append(limit)
        rows = self._con.execute(
            "SELECT id, category, title, subtitle, emoji, author, read_time, kicker, age_range, summary, tags "
            f"FROM articles {where}ORDER BY id LIMIT ?",
            params,
        ).fetchall()
        return [
            {"id": r[0], "category": r[1], "title": r[2], "subtitle": r[3],
             "emoji": r[4], "author": r[5], "read_time": r[6],
             "kicker": r[7], "age_range": r[8], "summary": r[9],
             "tags": list(r[10]) if r[10] else []}
            for r in rows
        ]

    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            "SELECT id, category, title, subtitle, emoji, author, read_time, kicker, age_range, summary, tags, content "
            "FROM articles WHERE id = ?",
            [article_id],
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0], "category": row[1], "title": row[2], "subtitle": row[3],
            "emoji": row[4], "author": row[5], "read_time": row[6],
            "kicker": row[7], "age_range": row[8], "summary": row[9],
            "tags": list(row[10]) if row[10] else [], "content": row[11],
        }

    def search_articles(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            "SELECT id, category, title, subtitle, emoji, author, read_time, kicker, age_range, summary, tags "
            "FROM articles "
            "WHERE title ILIKE ? OR subtitle ILIKE ? OR summary ILIKE ? OR array_to_string(tags, ' ') ILIKE ? "
            "ORDER BY id LIMIT ?",
            [f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit],
        ).fetchall()
        return [
            {"id": r[0], "category": r[1], "title": r[2], "subtitle": r[3],
             "emoji": r[4], "author": r[5], "read_time": r[6],
             "kicker": r[7], "age_range": r[8], "summary": r[9],
             "tags": list(r[10]) if r[10] else []}
            for r in rows
        ]

    def score_articles_by_words(self, words: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """Score articles by counting how many topic words match title/subtitle/tags."""
        # Build a SUM(CASE ...) expression for each word
        cases = " + ".join(
            f"(CASE WHEN title ILIKE '%' || ${i+1} || '%' OR subtitle ILIKE '%' || ${i+1} || '%' "
            f"OR array_to_string(tags, ' ') ILIKE '%' || ${i+1} || '%' THEN 1 ELSE 0 END)"
            for i in range(len(words))
        )
        # The score filter lives in an OUTER WHERE, not a bare HAVING: DuckDB
        # reads `HAVING` with no GROUP BY as an aggregate over the whole table
        # and rejects the plain columns ("column title must appear in the GROUP
        # BY clause"), so the bare-HAVING form 500s on every call.
        sql = (
            f"SELECT id, category, title, subtitle, emoji, author, read_time, kicker, age_range, summary, tags "
            f"FROM (SELECT id, category, title, subtitle, emoji, author, read_time, kicker, age_range, summary, tags, "
            f"({cases}) AS score FROM articles) "
            f"WHERE score > 0 ORDER BY score DESC LIMIT ?"
        )
        rows = self._con.execute(sql, words + [limit]).fetchall()
        return [
            {"id": r[0], "category": r[1], "title": r[2], "subtitle": r[3],
             "emoji": r[4], "author": r[5], "read_time": r[6],
             "kicker": r[7], "age_range": r[8], "summary": r[9],
             "tags": list(r[10]) if r[10] else []}
            for r in rows
        ]

    # ── Content CRUD methods ─────────────────────────────────────────

    def create_article(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._con.execute(
            "INSERT INTO articles (id, category, title, subtitle, emoji, author, read_time, "
            "kicker, age_range, summary, tags, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now(), now())",
            [data["id"], data["category"], data["title"], data.get("subtitle", ""),
             data.get("emoji", ""), data.get("author", "MVP Editorial"),
             data.get("read_time", ""),
             data.get("kicker", ""), data.get("age_range", ""),
             data.get("summary", ""),
             data.get("tags", []), data.get("content", "")],
        )
        return self.get_article(data["id"])

    def update_article(self, article_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.get_article(article_id)
        if existing is None:
            return None
        fields = []
        values = []
        for key in ("category", "title", "subtitle", "emoji", "author", "read_time",
                    "kicker", "age_range", "summary", "tags", "content"):
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        if not fields:
            return existing
        fields.append("updated_at = now()")
        values.append(article_id)
        self._con.execute(
            f"UPDATE articles SET {', '.join(fields)} WHERE id = ?", values
        )
        return self.get_article(article_id)

    def delete_article(self, article_id: str) -> bool:
        existing = self.get_article(article_id)
        if existing is None:
            return False
        self._con.execute("DELETE FROM articles WHERE id = ?", [article_id])
        return True

    def create_category(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._con.execute(
            "INSERT INTO categories (id, name, emoji, description, parent_id) VALUES (?, ?, ?, ?, ?)",
            [data["id"], data["name"], data.get("emoji", ""),
             data.get("description", ""), data.get("parent_id")],
        )
        return self._get_category(data["id"])

    def update_category(self, category_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        row = self._con.execute("SELECT id FROM categories WHERE id = ?", [category_id]).fetchone()
        if row is None:
            return None
        fields = []
        values = []
        # parent_id is included so callers can clear it by passing None — the
        # CMS dropdown's "— None (top-level) —" option round-trips that way.
        for key in ("name", "emoji", "description", "parent_id"):
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        if not fields:
            return self._get_category(category_id)
        values.append(category_id)
        self._con.execute(
            f"UPDATE categories SET {', '.join(fields)} WHERE id = ?", values
        )
        return self._get_category(category_id)

    def delete_category(self, category_id: str) -> bool:
        row = self._con.execute("SELECT id FROM categories WHERE id = ?", [category_id]).fetchone()
        if row is None:
            return False
        self._con.execute("DELETE FROM categories WHERE id = ?", [category_id])
        return True

    def _get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            "SELECT id, name, emoji, description, parent_id FROM categories WHERE id = ?",
            [category_id],
        ).fetchone()
        if row is None:
            return None
        return {"id": row[0], "name": row[1], "emoji": row[2], "description": row[3],
                "parent_id": row[4]}

    def get_content_stats(self) -> Dict[str, Any]:
        articles_count = self._con.execute("SELECT count(*) FROM articles").fetchone()[0]
        categories_count = self._con.execute("SELECT count(*) FROM categories").fetchone()[0]
        articles_by_cat = self._con.execute(
            "SELECT category, count(*) FROM articles GROUP BY category ORDER BY category"
        ).fetchall()
        return {
            "articles": articles_count,
            "categories": categories_count,
            "articles_by_category": {r[0]: r[1] for r in articles_by_cat},
        }

    # ── Family Companion (kid agent) ─────────────────────────────────

    def save_kid_agent_config(
        self,
        user_id: str,
        kid_name: str,
        invariants: Dict[str, Any],
        free_text_brief: str,
        system_prompt: str,
        content_hash: str,
        model: str,
        enabled: bool,
        expected_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Append a new versioned config row. The "current" config for a (user, kid)
        is the row with the highest version. expected_version supports optimistic
        concurrency: pass the version the caller thinks is current, and the
        function will refuse to write if that's stale.

        Raises ValueError on version conflict.
        """
        import uuid

        latest = self._con.execute(
            "SELECT max(version) FROM kid_agent_configs WHERE user_id = ? AND kid_name = ?",
            [user_id, kid_name],
        ).fetchone()
        current_version = (latest[0] if latest and latest[0] is not None else 0)

        if expected_version is not None and expected_version != current_version:
            raise ValueError(
                f"version conflict: caller had v{expected_version}, current is v{current_version}"
            )

        new_version = current_version + 1
        config_id = str(uuid.uuid4())
        invariants_json = json.dumps(invariants, ensure_ascii=False)

        try:
            self._con.execute(
                """
                INSERT INTO kid_agent_configs (
                    id, user_id, kid_name, version, invariants_json,
                    free_text_brief, system_prompt, content_hash, model, enabled, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now())
                """,
                [
                    config_id, user_id, kid_name, new_version, invariants_json,
                    free_text_brief, system_prompt, content_hash, model, enabled,
                ],
            )
        except duckdb.ConstraintException as exc:
            # uq_kid_agent_configs_version: a concurrent writer already landed
            # this version. Surface as a version conflict (mapped to 409) — the
            # DB-level guard for the check+insert TOCTOU race (B-9).
            raise ValueError(
                f"version conflict: v{new_version} for {user_id}/{kid_name} was "
                f"written concurrently; retry with the latest version"
            ) from exc
        logger.info(f"[duckdb] saved kid_agent_config v{new_version} for {user_id}/{kid_name}")
        return self.get_kid_agent_config(user_id, kid_name)

    def get_kid_agent_config(self, user_id: str, kid_name: str) -> Optional[Dict[str, Any]]:
        """Return the highest-version config row for (user_id, kid_name), or None."""
        row = self._con.execute(
            """
            SELECT id, user_id, kid_name, version, invariants_json, free_text_brief,
                   system_prompt, content_hash, model, enabled, created_at
            FROM kid_agent_configs
            WHERE user_id = ? AND kid_name = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            [user_id, kid_name],
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "user_id": row[1],
            "kid_name": row[2],
            "version": row[3],
            "invariants": json.loads(row[4]),
            "free_text_brief": row[5],
            "system_prompt": row[6],
            "content_hash": row[7],
            "model": row[8],
            "enabled": row[9],
            "created_at": row[10].isoformat() if row[10] else None,
        }

    def list_kid_agents(self, user_id: str) -> List[Dict[str, Any]]:
        """Return the latest config for each kid belonging to user_id."""
        rows = self._con.execute(
            """
            SELECT kid_name, max(version) AS v
            FROM kid_agent_configs
            WHERE user_id = ?
            GROUP BY kid_name
            ORDER BY kid_name
            """,
            [user_id],
        ).fetchall()
        results = []
        for kid_name, _ in rows:
            cfg = self.get_kid_agent_config(user_id, kid_name)
            if cfg:
                # Surface crisis-lock state so the Home can show a distinct
                # "needs review" companion instead of it looking un-set-up.
                lock = self.is_kid_agent_crisis_locked(cfg["id"])
                cfg["crisis_locked"] = lock is not None
                cfg["crisis_category"] = (lock or {}).get("category")
                results.append(cfg)
        return results

    def append_kid_message(
        self,
        agent_id: str,
        thread_id: str,
        role: str,
        content: str,
        moderation_score: Optional[float] = None,
        age_score: Optional[float] = None,
        voice_score: Optional[float] = None,
        parent_flagged: bool = False,
        message_id: Optional[str] = None,
    ) -> str:
        """Append a kid-chat message; returns the new message id.

        `message_id` may be pre-supplied by the caller — used by the kid-chat
        voice path which needs to reference the assistant `reply_id` in
        streamed voice_fragment events before the row is finalised.
        """
        import uuid
        if message_id is None:
            message_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO kid_messages (
                id, agent_id, thread_id, role, content,
                moderation_score, age_score, voice_score, parent_flagged, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, now())
            """,
            [
                message_id, agent_id, thread_id, role, content,
                moderation_score, age_score, voice_score, parent_flagged,
            ],
        )
        return message_id

    def get_kid_messages(
        self,
        agent_id: str,
        thread_id: str = "default",
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Return messages for a kid agent thread, oldest first."""
        rows = self._con.execute(
            """
            SELECT id, role, content, moderation_score, age_score, voice_score,
                   parent_flagged, created_at
            FROM kid_messages
            WHERE agent_id = ? AND thread_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            [agent_id, thread_id, limit],
        ).fetchall()
        return [
            {
                "id": r[0],
                "role": r[1],
                "content": r[2],
                "moderation_score": r[3],
                "age_score": r[4],
                "voice_score": r[5],
                "parent_flagged": r[6],
                "created_at": r[7].isoformat() if r[7] else None,
            }
            for r in rows
        ]

    def get_last_kid_message(
        self, agent_id: str, thread_id: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """Most recent message in a kid thread, or None. Used by the ConvAI
        token endpoint's greeting-persistence guard (don't stack greetings on
        reconnect)."""
        row = self._con.execute(
            """
            SELECT role, content FROM kid_messages
            WHERE agent_id = ? AND thread_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [agent_id, thread_id],
        ).fetchone()
        if row is None:
            return None
        return {"role": row[0], "content": row[1]}

    def set_kid_pin(self, user_id: str, kid_name: str, pin_hash: str) -> None:
        """Upsert a kid PIN. Caller must provide a bcrypt hash."""
        self._con.execute(
            """
            INSERT INTO kid_credentials (user_id, kid_name, pin_hash, last_rotated_at)
            VALUES (?, ?, ?, now())
            ON CONFLICT (user_id, kid_name)
            DO UPDATE SET pin_hash = excluded.pin_hash, last_rotated_at = excluded.last_rotated_at
            """,
            [user_id, kid_name, pin_hash],
        )

    def get_kid_pin_hash(self, user_id: str, kid_name: str) -> Optional[str]:
        row = self._con.execute(
            "SELECT pin_hash FROM kid_credentials WHERE user_id = ? AND kid_name = ?",
            [user_id, kid_name],
        ).fetchone()
        return row[0] if row else None

    def log_moderation_event(
        self,
        user_id: str,
        kid_name: str,
        severity: str,
        category: str,
        action: str,
        agent_id: Optional[str] = None,
        message_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        parent_notified_at: Optional[str] = None,
    ) -> str:
        """Record a moderation event. Returns the event id."""
        import uuid
        event_id = str(uuid.uuid4())
        details_json = json.dumps(details, ensure_ascii=False) if details else None
        self._con.execute(
            """
            INSERT INTO moderation_events (
                id, user_id, kid_name, agent_id, message_id,
                severity, category, action, details, parent_notified_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now())
            """,
            [
                event_id, user_id, kid_name, agent_id, message_id,
                severity, category, action, details_json, parent_notified_at,
            ],
        )
        logger.warning(
            f"[moderation] {severity}/{category}/{action} user={user_id} kid={kid_name}"
        )
        return event_id

    def get_moderation_events(
        self,
        user_id: str,
        kid_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        if kid_name:
            rows = self._con.execute(
                """
                SELECT id, kid_name, agent_id, message_id, severity, category,
                       action, details, parent_notified_at, created_at
                FROM moderation_events
                WHERE user_id = ? AND kid_name = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [user_id, kid_name, limit],
            ).fetchall()
        else:
            rows = self._con.execute(
                """
                SELECT id, kid_name, agent_id, message_id, severity, category,
                       action, details, parent_notified_at, created_at
                FROM moderation_events
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                [user_id, limit],
            ).fetchall()
        return [
            {
                "id": r[0],
                "kid_name": r[1],
                "agent_id": r[2],
                "message_id": r[3],
                "severity": r[4],
                "category": r[5],
                "action": r[6],
                "details": json.loads(r[7]) if r[7] else None,
                "parent_notified_at": r[8].isoformat() if r[8] else None,
                "created_at": r[9].isoformat() if r[9] else None,
            }
            for r in rows
        ]

    # ── Auth tokens ──────────────────────────────────────────────────

    AUTH_TOKEN_TTL_DAYS = int(os.getenv("AUTH_TOKEN_TTL_DAYS", "30"))

    @staticmethod
    def _hash_token(raw: str) -> str:
        import hashlib
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def issue_auth_token(self, user_id: str) -> str:
        """
        Generate a fresh raw token, persist its sha256 hash, return the raw
        token to the caller. Server never sees the raw token at rest again.
        """
        import uuid
        from datetime import datetime, timedelta, timezone
        raw = uuid.uuid4().hex
        token_hash = self._hash_token(raw)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.AUTH_TOKEN_TTL_DAYS)
        self._con.execute(
            "INSERT INTO auth_tokens (token, user_id, created_at, expires_at) "
            "VALUES (?, ?, now(), ?)",
            [token_hash, user_id, expires_at],
        )
        return raw

    def lookup_auth_token(self, token: str) -> Optional[str]:
        """
        Return user_id for an active, unexpired, non-revoked token.
        Refuses tokens with NULL expires_at (legacy plaintext rows).
        """
        token_hash = self._hash_token(token)
        row = self._con.execute(
            "SELECT user_id FROM auth_tokens "
            "WHERE token = ? "
            "  AND revoked_at IS NULL "
            "  AND expires_at IS NOT NULL "
            "  AND expires_at > now()",
            [token_hash],
        ).fetchone()
        if row is None:
            return None
        # Update last_used_at fire-and-forget; failure here doesn't deny.
        try:
            self._con.execute(
                "UPDATE auth_tokens SET last_used_at = now() WHERE token = ?",
                [token_hash],
            )
        except Exception:
            pass
        return row[0]

    def revoke_auth_token(self, token: str) -> None:
        token_hash = self._hash_token(token)
        self._con.execute(
            "UPDATE auth_tokens SET revoked_at = now() WHERE token = ?",
            [token_hash],
        )

    # ── Auth v1: accounts, identities, refresh tokens (Phase 2) ──────

    def get_or_create_account(
        self, user_id: str, *, display_name: Optional[str] = None,
        primary_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return the account row for user_id, creating it (with a fresh
        analytics_id) if absent. Idempotent."""
        import uuid
        row = self._con.execute(
            "SELECT user_id, analytics_id, display_name, primary_email "
            "FROM user_accounts WHERE user_id = ?", [user_id],
        ).fetchone()
        if row is None:
            analytics_id = uuid.uuid4().hex
            self._con.execute(
                "INSERT INTO user_accounts (user_id, analytics_id, display_name, "
                "primary_email, created_at) VALUES (?, ?, ?, ?, now())",
                [user_id, analytics_id, display_name, primary_email],
            )
            return {"user_id": user_id, "analytics_id": analytics_id,
                    "display_name": display_name, "primary_email": primary_email}
        # Backfill display_name/email opportunistically if newly known.
        if (display_name and not row[2]) or (primary_email and not row[3]):
            self._con.execute(
                "UPDATE user_accounts SET display_name = coalesce(?, display_name), "
                "primary_email = coalesce(?, primary_email) WHERE user_id = ?",
                [display_name, primary_email, user_id],
            )
        return {"user_id": row[0], "analytics_id": row[1],
                "display_name": display_name or row[2],
                "primary_email": primary_email or row[3]}

    def analytics_id_for(self, user_id: str) -> Optional[str]:
        """The opaque analytics id for a user, or None if no account row."""
        row = self._con.execute(
            "SELECT analytics_id FROM user_accounts WHERE user_id = ?", [user_id],
        ).fetchone()
        return row[0] if row else None

    def user_has_profile(self, user_id: str) -> bool:
        """True if the user has completed onboarding (a user_data profile row
        exists). Drives the client's post-sign-in routing: a returning user
        (any device) skips onboarding; a fresh account goes through it."""
        row = self._con.execute(
            "SELECT 1 FROM user_data WHERE user_id = ? LIMIT 1", [user_id],
        ).fetchone()
        return row is not None

    def get_identity(self, provider: str, provider_sub: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            "SELECT id, user_id, provider, provider_sub, email, email_verified "
            "FROM auth_identities WHERE provider = ? AND provider_sub = ?",
            [provider, provider_sub],
        ).fetchone()
        if row is None:
            return None
        return {"id": row[0], "user_id": row[1], "provider": row[2],
                "provider_sub": row[3], "email": row[4], "email_verified": row[5]}

    def link_identity(
        self, *, user_id: str, provider: str, provider_sub: str,
        email: Optional[str] = None, email_verified: bool = False,
    ) -> Dict[str, Any]:
        """Bind a provider identity to an account. If the (provider, sub) pair
        already exists, updates last_login_at and returns it (no duplicate)."""
        import uuid
        existing = self.get_identity(provider, provider_sub)
        if existing is not None:
            self._con.execute(
                "UPDATE auth_identities SET last_login_at = now() "
                "WHERE provider = ? AND provider_sub = ?",
                [provider, provider_sub],
            )
            return existing
        identity_id = uuid.uuid4().hex
        self._con.execute(
            "INSERT INTO auth_identities (id, user_id, provider, provider_sub, "
            "email, email_verified, created_at, last_login_at) "
            "VALUES (?, ?, ?, ?, ?, ?, now(), now())",
            [identity_id, user_id, provider, provider_sub, email, email_verified],
        )
        return {"id": identity_id, "user_id": user_id, "provider": provider,
                "provider_sub": provider_sub, "email": email,
                "email_verified": email_verified}

    def find_identity_user_by_verified_email(self, email: Optional[str]) -> Optional[str]:
        """Return the user_id of the SINGLE account with a VERIFIED identity at
        `email`, or None on zero or many matches.

        Exists so a parent who signs up with Apple, then later signs in with
        Google using the SAME email, lands on the SAME account instead of
        minting a second one — the "sent me to onboarding" bug (2026-08-09):
        Google was creating a fresh user_id with zero profile data even though
        an Apple-identity account with the same address and a real profile
        already existed.

        Verified-only, both directions:
          - the STORED identity we match against must have `email_verified`,
            so a spoofed/unconfirmed address on file can't be used to hijack
            an existing family, and
          - the CALLER only invokes this when the INCOMING provider payload
            also says the email is verified (checked by the caller, not here) —
            an unverified incoming email must never be trusted enough to link
            into someone else's account.

        Exactly one match required, same idiom as `find_account_by_email`
        (auth_identities) and `find_unclaimed_account_by_email`
        (consent_records): an ambiguous email is treated as no match rather
        than guessing, because auto-linking the wrong family is much worse
        than making the parent create a second account and merge later.
        """
        if not email:
            return None
        needle = email.strip().lower()
        if not needle:
            return None
        rows = self._con.execute(
            "SELECT DISTINCT user_id FROM auth_identities "
            "WHERE lower(trim(email)) = ? AND email_verified",
            [needle],
        ).fetchall()
        return rows[0][0] if len(rows) == 1 else None

    def user_has_any_identity(self, user_id: str) -> bool:
        row = self._con.execute(
            "SELECT 1 FROM auth_identities WHERE user_id = ? LIMIT 1", [user_id],
        ).fetchone()
        return row is not None

    def user_has_identity_for_provider(self, user_id: str, provider: str) -> bool:
        """True if the account already has an identity for THIS provider. Used by
        the claim guard so a valid-legacy-proof holder can bind a SECOND provider
        (Apple + Google) to their account, while still blocking a re-bind of a
        provider that's already linked (anti-hijack)."""
        row = self._con.execute(
            "SELECT 1 FROM auth_identities WHERE user_id = ? AND provider = ? LIMIT 1",
            [user_id, provider],
        ).fetchone()
        return row is not None

    def find_unclaimed_account_by_email(self, email: Optional[str]) -> Optional[str]:
        """Return the user_id of the SINGLE unclaimed legacy account whose consent
        email matches `email` (case-insensitive) — for the reinstall 'restore your
        family' flow. None if zero or more than one match (ambiguous → require
        manual/admin resolution, never auto-merge kid data on a fuzzy match)."""
        if not email:
            return None
        rows = self._con.execute(
            "SELECT DISTINCT c.user_id FROM consent_records c "
            "WHERE lower(c.parent_email) = lower(?) "
            "  AND NOT EXISTS (SELECT 1 FROM auth_identities i WHERE i.user_id = c.user_id)",
            [email],
        ).fetchall()
        return rows[0][0] if len(rows) == 1 else None

    def create_refresh_token(
        self, *, user_id: str, family_id: Optional[str] = None,
        platform: Optional[str] = None, device_name: Optional[str] = None,
        ttl_days: int = 60,
    ) -> str:
        """Mint a refresh token (returns the RAW token; only its hash is stored).
        A new family_id starts a rotation lineage; pass an existing one to
        continue a lineage across a rotation."""
        import secrets, uuid
        from datetime import datetime, timedelta, timezone
        raw = secrets.token_urlsafe(48)
        family_id = family_id or uuid.uuid4().hex
        expires_at = datetime.now(timezone.utc) + timedelta(days=ttl_days)
        self._con.execute(
            "INSERT INTO refresh_tokens (id, family_id, user_id, token_hash, "
            "platform, device_name, created_at, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?, now(), ?)",
            [uuid.uuid4().hex, family_id, user_id, self._hash_token(raw),
             platform, device_name, expires_at],
        )
        return raw

    def rotate_refresh_token(self, raw: str) -> Optional[Dict[str, Any]]:
        """Validate + rotate a refresh token. Returns
        {"user_id", "refresh_token", "family_id"} on success, None on an
        invalid/expired token. REUSE DETECTION: presenting a token whose row is
        already rotated or revoked nukes the entire family_id and returns None."""
        token_hash = self._hash_token(raw)
        row = self._con.execute(
            "SELECT id, family_id, user_id, expires_at, rotated_at, revoked_at, platform, device_name "
            "FROM refresh_tokens WHERE token_hash = ?", [token_hash],
        ).fetchone()
        if row is None:
            return None
        rt_id, family_id, user_id, expires_at, rotated_at, revoked_at, platform, device_name = row
        if rotated_at is not None or revoked_at is not None:
            # Reuse of an already-consumed/revoked token → compromise. Nuke the
            # whole lineage so a stolen token can't ride alongside the real one.
            self._con.execute(
                "UPDATE refresh_tokens SET revoked_at = now() "
                "WHERE family_id = ? AND revoked_at IS NULL", [family_id],
            )
            logger.warning("[auth] refresh-token reuse detected; revoked family %s", family_id)
            return None
        from datetime import datetime, timezone
        if expires_at is not None and expires_at <= datetime.now(timezone.utc):
            return None
        # Mint the successor in the same family, mark this one rotated.
        new_raw = self.create_refresh_token(
            user_id=user_id, family_id=family_id, platform=platform, device_name=device_name,
        )
        new_id = self._con.execute(
            "SELECT id FROM refresh_tokens WHERE token_hash = ?",
            [self._hash_token(new_raw)],
        ).fetchone()[0]
        self._con.execute(
            "UPDATE refresh_tokens SET rotated_at = now(), replaced_by = ?, last_used_at = now() "
            "WHERE id = ?", [new_id, rt_id],
        )
        return {"user_id": user_id, "refresh_token": new_raw, "family_id": family_id}

    def revoke_refresh_token(self, raw: str) -> None:
        """Revoke a single refresh token's whole family (logout on one device)."""
        row = self._con.execute(
            "SELECT family_id FROM refresh_tokens WHERE token_hash = ?",
            [self._hash_token(raw)],
        ).fetchone()
        if row is not None:
            self._con.execute(
                "UPDATE refresh_tokens SET revoked_at = now() "
                "WHERE family_id = ? AND revoked_at IS NULL", [row[0]],
            )

    def revoke_all_refresh_tokens(self, user_id: str) -> None:
        """Revoke every outstanding refresh token for a user (global logout)."""
        self._con.execute(
            "UPDATE refresh_tokens SET revoked_at = now() "
            "WHERE user_id = ? AND revoked_at IS NULL", [user_id],
        )

    # ── Migration ops (admin: monitor + manual relink safety net) ────

    def migration_status(self) -> Dict[str, Any]:
        """Snapshot of the legacy→sign-in migration for the operator. Lists every
        known account with whether it has claimed a provider identity yet, plus
        which identities exist. No PII beyond user_id/email (operator-only)."""
        accounts = self._con.execute(
            "SELECT ua.user_id, ua.primary_email, ua.created_at, "
            "  (SELECT count(*) FROM auth_identities ai WHERE ai.user_id = ua.user_id) AS identity_count "
            "FROM user_accounts ua ORDER BY ua.created_at"
        ).fetchall()
        identities = self._con.execute(
            "SELECT provider, provider_sub, user_id, email, last_login_at "
            "FROM auth_identities ORDER BY created_at"
        ).fetchall()
        acct_rows = [
            {"user_id": r[0], "primary_email": r[1], "created_at": str(r[2]) if r[2] else None,
             "claimed": r[3] > 0}
            for r in accounts
        ]
        return {
            "total_accounts": len(acct_rows),
            "claimed": sum(1 for a in acct_rows if a["claimed"]),
            "unclaimed": [a for a in acct_rows if not a["claimed"]],
            "accounts": acct_rows,
            "identities": [
                {"provider": r[0], "provider_sub": r[1], "user_id": r[2],
                 "email": r[3], "last_login_at": str(r[4]) if r[4] else None}
                for r in identities
            ],
        }

    def admin_relink_identity(
        self, *, provider: str, provider_sub: str, target_user_id: str,
        actor: str,
    ) -> Dict[str, Any]:
        """Operator safety net: bind (provider, provider_sub) to target_user_id,
        moving it off any wrong account and deleting that account IF it is empty
        (no data beyond the account/identity/refresh rows). Used when an
        automatic legacy claim failed (expired token / fresh install) and a
        founder's real Apple/Google identity landed on a fresh empty account.

        Returns {"relinked": bool, "moved_from": <old_user_id|None>,
                 "deleted_empty_account": <user_id|None>}.
        """
        result: Dict[str, Any] = {"relinked": False, "moved_from": None,
                                  "deleted_empty_account": None}
        with self._con.transaction():
            # Ensure the target account exists.
            self.get_or_create_account(target_user_id)
            existing = self._con.execute(
                "SELECT user_id FROM auth_identities WHERE provider = ? AND provider_sub = ?",
                [provider, provider_sub],
            ).fetchone()
            old_user_id = existing[0] if existing else None

            if old_user_id == target_user_id:
                return result  # already correct; no-op

            if existing is not None:
                self._con.execute(
                    "UPDATE auth_identities SET user_id = ?, last_login_at = now() "
                    "WHERE provider = ? AND provider_sub = ?",
                    [target_user_id, provider, provider_sub],
                )
                result["moved_from"] = old_user_id
                # Delete the vacated account only if it holds NO family data.
                if old_user_id and self._account_is_empty(old_user_id):
                    self._con.execute("DELETE FROM refresh_tokens WHERE user_id = ?", [old_user_id])
                    self._con.execute("DELETE FROM auth_identities WHERE user_id = ?", [old_user_id])
                    self._con.execute("DELETE FROM user_accounts WHERE user_id = ?", [old_user_id])
                    result["deleted_empty_account"] = old_user_id
            else:
                import uuid
                self._con.execute(
                    "INSERT INTO auth_identities (id, user_id, provider, provider_sub, "
                    "created_at, last_login_at) VALUES (?, ?, ?, ?, now(), now())",
                    [uuid.uuid4().hex, target_user_id, provider, provider_sub],
                )
            self.write_audit_event(
                user_id=target_user_id, actor=actor, action="auth.admin_relink",
                details={"provider": provider, "moved_from": old_user_id,
                         "deleted_empty_account": result["deleted_empty_account"]},
            )
            result["relinked"] = True
        return result

    def _account_is_empty(self, user_id: str) -> bool:
        """True if user_id has no family data (profile, kids, activities, chats).
        Only the account/identity/refresh/analytics scaffolding may exist."""
        for table in ("user_data", "kid_agent_configs", "tracked_activities",
                      "cos_messages", "consent_records", "research_runs"):
            row = self._con.execute(
                f"SELECT 1 FROM {table} WHERE user_id = ? LIMIT 1", [user_id],
            ).fetchone()
            if row is not None:
                return False
        return True

    # ── Push device tokens (crisis-lock notifications) ───────────────

    def save_push_token(self, *, user_id: str, token: str, platform: str = "ios") -> None:
        """Register (or refresh) an APNs device token for a parent. Idempotent —
        re-registering the same token just bumps last_seen_at."""
        self._con.execute(
            """
            INSERT INTO push_device_tokens (token, user_id, platform, last_seen_at)
            VALUES (?, ?, ?, now())
            ON CONFLICT (token) DO UPDATE SET user_id = excluded.user_id,
                platform = excluded.platform, last_seen_at = now()
            """,
            [token, user_id, platform],
        )

    def list_push_tokens(self, user_id: str) -> List[str]:
        rows = self._con.execute(
            "SELECT token FROM push_device_tokens WHERE user_id = ?", [user_id]
        ).fetchall()
        return [r[0] for r in rows]

    def delete_push_token(self, token: str) -> None:
        self._con.execute("DELETE FROM push_device_tokens WHERE token = ?", [token])

    # ── Share tokens (scoped read-only plan links) ───────────────────

    def issue_share_token(
        self, *, user_id: str, scope: str, label: Optional[str] = None, ttl_days: int = 30
    ) -> str:
        """Mint a scoped, expiring, read-only share link token. Returns the RAW
        token (stored hashed, like auth_tokens) — it's only ever returned here."""
        import secrets
        raw = secrets.token_urlsafe(24)
        self._con.execute(
            "INSERT INTO share_tokens (token, user_id, scope, label, expires_at) "
            "VALUES (?, ?, ?, ?, now() + INTERVAL (?) DAY)",
            [self._hash_token(raw), user_id, scope, label, ttl_days],
        )
        return raw

    def lookup_share_token(self, raw_token: str) -> Optional[Dict[str, Any]]:
        """Resolve a raw share token → {user_id, scope, label} if valid (not
        revoked, not expired). None otherwise."""
        row = self._con.execute(
            "SELECT user_id, scope, label FROM share_tokens WHERE token = ? "
            "AND revoked_at IS NULL AND expires_at IS NOT NULL AND expires_at > now()",
            [self._hash_token(raw_token)],
        ).fetchone()
        if not row:
            return None
        return {"user_id": row[0], "scope": row[1], "label": row[2]}

    def list_share_tokens(self, user_id: str) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            "SELECT scope, label, created_at, expires_at, revoked_at "
            "FROM share_tokens WHERE user_id = ? ORDER BY created_at DESC",
            [user_id],
        ).fetchall()
        return [
            {"scope": r[0], "label": r[1],
             "created_at": r[2].isoformat() if r[2] else None,
             "expires_at": r[3].isoformat() if r[3] else None,
             "revoked": r[4] is not None}
            for r in rows
        ]

    def revoke_share_token(self, *, user_id: str, raw_token: str) -> bool:
        cur = self._con.execute(
            "UPDATE share_tokens SET revoked_at = now() WHERE token = ? AND user_id = ?",
            [self._hash_token(raw_token), user_id],
        )
        return True

    def write_audit_event(
        self, *, user_id: Optional[str], actor: Optional[str],
        action: str, details: Optional[Dict[str, Any]] = None,
    ) -> str:
        import uuid
        event_id = uuid.uuid4().hex
        self._con.execute(
            "INSERT INTO audit_events (id, user_id, actor, action, details) "
            "VALUES (?, ?, ?, ?, ?)",
            [event_id, user_id, actor, action,
             json.dumps(details or {})],
        )
        return event_id

    def delete_family(self, *, user_id: str, actor: str) -> Dict[str, Any]:
        """
        Cascade-delete every row keyed to user_id across all tables that hold
        family data. Returns {"counts": {table: rows}, "agent_ids": [...]} —
        the caller uses agent_ids to abort in-flight streams (H-5). Always
        writes an audit_events row LAST so the delete itself is logged.

        Tables touched (every one that references user_id):
            user_data, kid_agent_configs, kid_messages (via agent_id),
            kid_credentials, moderation_events, kid_agent_crisis_locks,
            auth_tokens, daily_summaries, consent_records, and the
            activity-planning tables (research_runs, activity_candidates,
            tracked_activities, calendar_entries, recurring_appointments,
            caregivers, logistics_assignments, todo_items, ingest_artifacts,
            cos_messages, google_oauth_tokens).

        Tables left intact: content (categories/articles) and audit_events
        itself.

        The plain per-table sweep is driven by the module-level
        FAMILY_CASCADE_TABLES list, shared with `reset_family` so the two
        cascades cannot drift.
        """
        return self._cascade_family(
            user_id=user_id, actor=actor,
            tables=FAMILY_CASCADE_TABLES, action="family_deleted",
        )

    def reset_family(self, *, user_id: str, actor: str) -> Dict[str, Any]:
        """
        Tester reset: the `delete_family` cascade MINUS the sign-in identity
        (auth_identities, user_accounts, refresh_tokens, auth_tokens) and
        MINUS legal_acceptances (the testers already accepted the terms).
        The account keeps its Apple/Google identity, so after the wipe the
        tester signs back in on the SAME user_id, `hasProfile` comes back
        false, and the redesigned onboarding runs again on their real account.

        Same shape as delete_family: {"counts": {...}, "agent_ids": [...]},
        one transaction, audit_events row ("family.reset") written last.
        """
        tables = [t for t in FAMILY_CASCADE_TABLES if t not in FAMILY_RESET_SKIP_TABLES]
        return self._cascade_family(
            user_id=user_id, actor=actor,
            tables=tables, action="family.reset",
        )

    def user_exists(self, user_id: str) -> bool:
        """True if the user has an account row, a sign-in identity, or any
        user_data payload — used by the admin reset route's 404 check."""
        for table in ("user_accounts", "auth_identities", "user_data"):
            n = self._con.execute(
                f"SELECT count(*) FROM {table} WHERE user_id = ?", [user_id],
            ).fetchone()[0]
            if n:
                return True
        return False

    def _cascade_family(
        self, *, user_id: str, actor: str, tables: List[str], action: str,
    ) -> Dict[str, Any]:
        """Shared body of delete_family / reset_family: the pre-passes that
        join through other keys (kid_messages via agent_id, window_notifications
        via window_id, the Circle tables via owner/conversation), the plain
        per-table sweep over `tables`, the claimed_by / member_user_id
        null-outs, and the audit row written LAST."""
        deleted: Dict[str, int] = {}

        # Wrap the whole cascade in one transaction (A5) so a kill mid-delete
        # can't leave a half-deleted family (e.g. user_data gone but consent +
        # auth_tokens still present). The proxy holds the connection lock for
        # the duration, so no other thread joins this transaction.
        with self._con.transaction():
            if action == "family.reset" and self._con.execute(
                "SELECT 1 FROM agent_family_fences WHERE user_id=? AND deleted=TRUE", [user_id]
            ).fetchone():
                raise PermissionError("A deleted family cannot be reset")
            self._con.execute(
                "INSERT INTO agent_family_fences (user_id, generation, deleted, checkpoint_purge_pending, snapshot_purge_pending) "
                "VALUES (?, 1, ?, TRUE, TRUE) ON CONFLICT (user_id) DO UPDATE SET "
                "generation = agent_family_fences.generation + 1, deleted = excluded.deleted, "
                "checkpoint_purge_pending = TRUE, snapshot_purge_pending = TRUE, updated_at = now()",
                [user_id, action == "family_deleted"],
            )
            # kid_messages joins via agent_id, so collect agent_ids first and
            # snapshot the pre-delete row count before running DELETEs.
            agent_ids = [r[0] for r in self._con.execute(
                "SELECT id FROM kid_agent_configs WHERE user_id = ?",
                [user_id],
            ).fetchall()]
            if agent_ids:
                placeholders = ",".join(["?"] * len(agent_ids))
                deleted["kid_messages"] = self._con.execute(
                    f"SELECT count(*) FROM kid_messages WHERE agent_id IN ({placeholders})",
                    agent_ids,
                ).fetchone()[0]
                self._con.execute(
                    f"DELETE FROM kid_messages WHERE agent_id IN ({placeholders})",
                    agent_ids,
                )
            else:
                deleted["kid_messages"] = 0

            # window_notifications is keyed by window_id, not user_id — cascade
            # it via the user's windows BEFORE the windows themselves go.
            deleted["window_notifications"] = self._con.execute(
                "SELECT count(*) FROM window_notifications WHERE window_id IN "
                "(SELECT id FROM registration_windows WHERE user_id = ?)",
                [user_id],
            ).fetchone()[0]
            self._con.execute(
                "DELETE FROM window_notifications WHERE window_id IN "
                "(SELECT id FROM registration_windows WHERE user_id = ?)",
                [user_id],
            )

            # Circle conversations are keyed by owner_user_id / participant
            # rows, not a bare user_id, so they need a pre-pass like
            # kid_messages above. Threads I OWN die with me (participants lose
            # them — same rule as DMs); in threads I merely joined, only my
            # participant row and my messages go, so the other households keep
            # a readable thread.
            circle_conv_ids = [
                r[0] for r in self._con.execute(
                    "SELECT id FROM circle_conversations WHERE owner_user_id = ?",
                    [user_id],
                ).fetchall()
            ]
            circle_msgs = 0
            circle_parts = 0
            for conv_id in circle_conv_ids:
                circle_msgs += self._con.execute(
                    "SELECT count(*) FROM circle_messages WHERE conversation_id = ?",
                    [conv_id],
                ).fetchone()[0]
                circle_parts += self._con.execute(
                    "SELECT count(*) FROM circle_participants WHERE conversation_id = ?",
                    [conv_id],
                ).fetchone()[0]
                self._con.execute(
                    "DELETE FROM circle_messages WHERE conversation_id = ?", [conv_id]
                )
                self._con.execute(
                    "DELETE FROM circle_participants WHERE conversation_id = ?", [conv_id]
                )
                self._con.execute(
                    "DELETE FROM circle_conversations WHERE id = ?", [conv_id]
                )
            circle_parts += self._con.execute(
                "SELECT count(*) FROM circle_participants WHERE user_id = ?",
                [user_id],
            ).fetchone()[0]
            self._con.execute(
                "DELETE FROM circle_participants WHERE user_id = ?", [user_id]
            )
            circle_msgs += self._con.execute(
                "SELECT count(*) FROM circle_messages WHERE user_id = ?",
                [user_id],
            ).fetchone()[0]
            self._con.execute("DELETE FROM circle_messages WHERE user_id = ?", [user_id])
            deleted["circle_conversations"] = len(circle_conv_ids)
            deleted["circle_participants"] = circle_parts
            deleted["circle_messages"] = circle_msgs

            # Invites I issued go with me. Invites OTHERS issued that I claimed
            # survive as their record, but the pointer at my dead account must
            # not outlive it (a re-issued user_id would inherit the claim).
            deleted["invite_tokens"] = self._con.execute(
                "SELECT count(*) FROM invite_tokens WHERE user_id = ?", [user_id],
            ).fetchone()[0]
            self._con.execute("DELETE FROM invite_tokens WHERE user_id = ?", [user_id])
            self._con.execute(
                "UPDATE invite_tokens SET claimed_by = NULL WHERE claimed_by = ?",
                [user_id],
            )

            # Circle requests in EITHER direction die with the account
            # (CLAUDE.md: deletes cascade). A surviving row would point a
            # stranger's inbox at a dead user_id — and a re-issued id would
            # inherit an accept it never asked for.
            deleted["circle_requests"] = self._con.execute(
                "SELECT count(*) FROM circle_requests "
                "WHERE from_user_id = ? OR to_user_id = ?",
                [user_id, user_id],
            ).fetchone()[0]
            self._con.execute(
                "DELETE FROM circle_requests WHERE from_user_id = ? OR to_user_id = ?",
                [user_id, user_id],
            )

            for table in tables:
                pre = self._con.execute(
                    f"SELECT count(*) FROM {table} WHERE user_id = ?",
                    [user_id],
                ).fetchone()[0]
                self._con.execute(
                    f"DELETE FROM {table} WHERE user_id = ?", [user_id],
                )
                deleted[table] = pre

            # Reciprocal Circle links OTHER families hold on this account.
            # The row is THEIR data about THEIR person, so it survives — but
            # the pointer at a now-deleted account must go, or a re-issued
            # user_id would inherit a stranger's Circle (and its threads).
            deleted["household_member_links_cleared"] = self._con.execute(
                "SELECT count(*) FROM household_members WHERE member_user_id = ?",
                [user_id],
            ).fetchone()[0]
            self._con.execute(
                "UPDATE household_members SET member_user_id = NULL, updated_at = now() "
                "WHERE member_user_id = ?",
                [user_id],
            )

            self.write_audit_event(
                user_id=user_id, actor=actor,
                action=action, details={"counts": deleted},
            )
        return {"counts": deleted, "agent_ids": agent_ids}

    def delete_kid_data(self, *, user_id: str, kid_name: str) -> Dict[str, int]:
        """Cascade-delete the kid-agent data for ONE child (used when a parent
        removes a kid profile). Without this, deleting the profile child leaves
        an orphan kid_agent_config + messages/credentials behind — which keep the
        kid reachable via /kid-agent and can resurrect it. Mirrors the per-kid
        slice of `delete_family`. Does NOT touch the profiles blob (the caller's
        profiling_service already removed the child there)."""
        deleted: Dict[str, int] = {}
        with self._con.transaction():
            agent_ids = [r[0] for r in self._con.execute(
                "SELECT id FROM kid_agent_configs WHERE user_id = ? AND kid_name = ?",
                [user_id, kid_name],
            ).fetchall()]
            if agent_ids:
                placeholders = ",".join(["?"] * len(agent_ids))
                deleted["kid_messages"] = self._con.execute(
                    f"SELECT count(*) FROM kid_messages WHERE agent_id IN ({placeholders})",
                    agent_ids,
                ).fetchone()[0]
                self._con.execute(
                    f"DELETE FROM kid_messages WHERE agent_id IN ({placeholders})",
                    agent_ids,
                )
            else:
                deleted["kid_messages"] = 0

            for table in [
                "kid_agent_crisis_locks",
                "kid_agent_configs",
                "kid_credentials",
                "moderation_events",
                "daily_summaries",
            ]:
                pre = self._con.execute(
                    f"SELECT count(*) FROM {table} WHERE user_id = ? AND kid_name = ?",
                    [user_id, kid_name],
                ).fetchone()[0]
                self._con.execute(
                    f"DELETE FROM {table} WHERE user_id = ? AND kid_name = ?",
                    [user_id, kid_name],
                )
                deleted[table] = pre
        return deleted

    # ── Crisis locks ─────────────────────────────────────────────────

    def lock_kid_agent_for_crisis(
        self, *, agent_id: str, user_id: str, kid_name: str,
        category: str, severity: str, reason: str,
    ) -> None:
        """
        Persist a crisis lock for an agent. Idempotent: re-locking refreshes the
        timestamp. Survives restarts (replaces the in-process _killed_agents
        set, which didn't).
        """
        self._con.execute(
            """
            INSERT INTO kid_agent_crisis_locks
                (agent_id, user_id, kid_name, locked_at, category, severity, reason)
            VALUES (?, ?, ?, now(), ?, ?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET
                locked_at = now(),
                category = excluded.category,
                severity = excluded.severity,
                reason = excluded.reason,
                revived_at = NULL,
                revived_by = NULL
            """,
            [agent_id, user_id, kid_name, category, severity, reason],
        )
        # Mirror to kid_agent_configs.enabled so the existing "is enabled?"
        # check in /kid-chat remains the single read-side gate.
        self._con.execute(
            "UPDATE kid_agent_configs SET enabled = FALSE WHERE id = ?",
            [agent_id],
        )

    def is_kid_agent_crisis_locked(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Return the active crisis lock row (or None if not locked)."""
        row = self._con.execute(
            """
            SELECT user_id, kid_name, locked_at, category, severity, reason
            FROM kid_agent_crisis_locks
            WHERE agent_id = ? AND revived_at IS NULL
            """,
            [agent_id],
        ).fetchone()
        if row is None:
            return None
        return {
            "agent_id": agent_id,
            "user_id": row[0],
            "kid_name": row[1],
            "locked_at": row[2],
            "category": row[3],
            "severity": row[4],
            "reason": row[5],
        }

    def revive_kid_agent_from_crisis(self, *, agent_id: str, by: str) -> bool:
        """Mark a crisis lock as cleared. Returns True if a lock was active."""
        result = self._con.execute(
            """
            UPDATE kid_agent_crisis_locks
            SET revived_at = now(), revived_by = ?
            WHERE agent_id = ? AND revived_at IS NULL
            """,
            [by, agent_id],
        )
        # rowcount on duckdb returns -1; verify via separate read
        active = self._con.execute(
            "SELECT count(*) FROM kid_agent_crisis_locks "
            "WHERE agent_id = ? AND revived_at IS NULL",
            [agent_id],
        ).fetchone()[0]
        return active == 0

    def set_kid_agent_enabled(self, agent_id: str, enabled: bool) -> None:
        """Toggle the enabled flag on a single agent config (used by crisis revive)."""
        self._con.execute(
            "UPDATE kid_agent_configs SET enabled = ? WHERE id = ?",
            [enabled, agent_id],
        )

    def list_active_crisis_locks(self, user_id: str) -> List[Dict[str, Any]]:
        """All currently-locked agents for a parent user."""
        rows = self._con.execute(
            """
            SELECT agent_id, kid_name, locked_at, category, severity, reason
            FROM kid_agent_crisis_locks
            WHERE user_id = ? AND revived_at IS NULL
            ORDER BY locked_at DESC
            """,
            [user_id],
        ).fetchall()
        return [
            {
                "agent_id": r[0], "kid_name": r[1], "locked_at": r[2],
                "category": r[3], "severity": r[4], "reason": r[5],
            }
            for r in rows
        ]

    # ── Consent records ──────────────────────────────────────────────

    def record_consent(
        self,
        *,
        user_id: str,
        parent_name: Optional[str],
        parent_email: Optional[str],
        kid_age_band: Optional[str],
        agreement_version: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        import uuid
        record_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO consent_records (
                id, user_id, parent_name, parent_email, kid_age_band,
                agreement_version, accepted_at, ip_address, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, now(), ?, ?)
            """,
            [
                record_id, user_id, parent_name, parent_email, kid_age_band,
                agreement_version, ip_address, user_agent,
            ],
        )
        return {
            "id": record_id, "user_id": user_id, "agreement_version": agreement_version,
        }

    def latest_consent(self, user_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            """
            SELECT id, agreement_version, accepted_at, parent_name, parent_email,
                   kid_age_band
            FROM consent_records
            WHERE user_id = ?
            ORDER BY accepted_at DESC
            LIMIT 1
            """,
            [user_id],
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "agreement_version": row[1],
            "accepted_at": row[2].isoformat() if row[2] else None,
            "parent_name": row[3],
            "parent_email": row[4],
            "kid_age_band": row[5],
        }

    # ── Legal documents (versioned) + acceptances ────────────────────

    _LEGAL_COLS = (
        "id, slug, version, title, body_md, effective_date, "
        "requires_reacceptance, published_at, published_by, is_current"
    )

    @staticmethod
    def _legal_row_to_dict(row) -> Dict[str, Any]:
        return {
            "id": row[0],
            "slug": row[1],
            "version": row[2],
            "title": row[3],
            "body_md": row[4],
            "effective_date": row[5].isoformat() if row[5] else None,
            "requires_reacceptance": bool(row[6]),
            "published_at": row[7].isoformat() if row[7] else None,
            "published_by": row[8],
            "is_current": bool(row[9]),
        }

    def get_current_legal_docs(self) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT {self._LEGAL_COLS} FROM legal_documents "
            "WHERE is_current ORDER BY slug"
        ).fetchall()
        return [self._legal_row_to_dict(r) for r in rows]

    def get_legal_doc(self, slug: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {self._LEGAL_COLS} FROM legal_documents "
            "WHERE slug = ? AND is_current LIMIT 1",
            [slug],
        ).fetchone()
        return self._legal_row_to_dict(row) if row else None

    def list_legal_versions(self, slug: str) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT {self._LEGAL_COLS} FROM legal_documents "
            "WHERE slug = ? AND published_at IS NOT NULL "
            "ORDER BY published_at DESC",
            [slug],
        ).fetchall()
        return [self._legal_row_to_dict(r) for r in rows]

    def get_legal_draft(self, slug: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {self._LEGAL_COLS} FROM legal_documents "
            "WHERE slug = ? AND published_at IS NULL LIMIT 1",
            [slug],
        ).fetchone()
        return self._legal_row_to_dict(row) if row else None

    def upsert_legal_draft(self, slug: str, *, title: str, body_md: str) -> Dict[str, Any]:
        """Create or overwrite THE draft row for a slug (at most one — enforced
        here, since DuckDB has no partial unique index). Last write wins."""
        import uuid
        existing = self.get_legal_draft(slug)
        if existing:
            self._con.execute(
                "UPDATE legal_documents SET title = ?, body_md = ?, updated_at = now() "
                "WHERE id = ?",
                [title, body_md, existing["id"]],
            )
            return self.get_legal_draft(slug)  # type: ignore[return-value]
        doc_id = f"legal-{uuid.uuid4().hex[:12]}"
        self._con.execute(
            """
            INSERT INTO legal_documents (id, slug, title, body_md, is_current)
            VALUES (?, ?, ?, ?, false)
            """,
            [doc_id, slug, title, body_md],
        )
        return self.get_legal_draft(slug)  # type: ignore[return-value]

    def delete_legal_draft(self, slug: str) -> bool:
        existing = self.get_legal_draft(slug)
        if not existing:
            return False
        self._con.execute("DELETE FROM legal_documents WHERE id = ?", [existing["id"]])
        return True

    def publish_legal_draft(
        self, slug: str, *, version: str, effective_date: Optional[str],
        requires_reacceptance: bool,
    ) -> Dict[str, Any]:
        """Promote the draft to the current published version atomically.
        Raises ValueError('no_draft') / ValueError('duplicate_version')."""
        with self._con.transaction():
            draft = self.get_legal_draft(slug)
            if not draft:
                raise ValueError("no_draft")
            dup = self._con.execute(
                "SELECT count(*) FROM legal_documents "
                "WHERE slug = ? AND version = ? AND published_at IS NOT NULL",
                [slug, version],
            ).fetchone()
            if dup and dup[0] > 0:
                raise ValueError("duplicate_version")
            self._con.execute(
                "UPDATE legal_documents SET is_current = false "
                "WHERE slug = ? AND is_current",
                [slug],
            )
            self._con.execute(
                """
                UPDATE legal_documents
                SET version = ?, effective_date = ?, requires_reacceptance = ?,
                    published_at = now(), published_by = 'admin',
                    is_current = true, updated_at = now()
                WHERE id = ?
                """,
                [version, effective_date, requires_reacceptance, draft["id"]],
            )
        return self.get_legal_doc(slug)  # type: ignore[return-value]

    def record_legal_acceptance(
        self, *, user_id: str, docs: List[Dict[str, str]],
        ip_address: Optional[str] = None, user_agent: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """One acceptance row per doc, in one transaction. Each entry in `docs`
        is {document_id, slug, version} (already validated by the caller)."""
        import uuid
        saved = []
        with self._con.transaction():
            for doc in docs:
                record_id = str(uuid.uuid4())
                self._con.execute(
                    """
                    INSERT INTO legal_acceptances (
                        id, user_id, document_id, slug, version,
                        accepted_at, ip_address, user_agent, platform
                    ) VALUES (?, ?, ?, ?, ?, now(), ?, ?, ?)
                    """,
                    [
                        record_id, user_id, doc["document_id"], doc["slug"],
                        doc["version"], ip_address, user_agent, platform,
                    ],
                )
                saved.append({"id": record_id, "slug": doc["slug"], "version": doc["version"]})
        return saved

    def latest_legal_acceptance(self, user_id: str, slug: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            """
            SELECT version, accepted_at FROM legal_acceptances
            WHERE user_id = ? AND slug = ?
            ORDER BY accepted_at DESC
            LIMIT 1
            """,
            [user_id, slug],
        ).fetchone()
        if row is None:
            return None
        return {
            "version": row[0],
            "accepted_at": row[1].isoformat() if row[1] else None,
        }

    # ── Account display names ────────────────────────────────────────

    def list_account_names(self) -> Dict[str, Optional[str]]:
        """user_id → display_name for every account row (raw material for
        `server._display_name_for_user`, which resolves the profile fallback)."""
        rows = self._con.execute(
            "SELECT user_id, display_name FROM user_accounts"
        ).fetchall()
        return {r[0]: r[1] for r in rows}

    # ── Saved items ──────────────────────────────────────────────────

    @staticmethod
    def _saved_row(row) -> Dict[str, Any]:
        return {
            "id": row[0],
            "item_type": row[1],
            "item_ref": row[2],
            "title": row[3],
            "snippet": row[4] or "",
            "body": row[5] or "",
            "source": json.loads(row[6]) if row[6] else {},
            "topic_tags": json.loads(row[7]) if row[7] else [],
            "kid_name": row[8],
            "save_count": int(row[9] or 1),
            "saved_at": row[10].isoformat() if row[10] else None,
        }

    _SAVED_COLS = (
        "id, item_type, item_ref, title, snippet, body, source_json, "
        "topic_tags, kid_name, save_count, saved_at"
    )

    def save_item(self, *, user_id: str, item_type: str, item_ref: str,
                  title: str, snippet: str = "", body: str = "",
                  source: Optional[Dict[str, Any]] = None,
                  topic_tags: Optional[List[str]] = None,
                  kid_name: Optional[str] = None,
                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Idempotent save / re-save. Re-saving revives the soft-deleted row and
        bumps save_count (re-saving the same thing = unresolved — signal)."""
        import uuid
        updated = self._con.execute(
            """
            UPDATE saved_items
            SET unsaved_at = NULL, saved_at = now(), save_count = save_count + 1,
                title = ?, snippet = ?, body = ?
            WHERE user_id = ? AND item_type = ? AND item_ref = ?
            RETURNING id
            """,
            [title, snippet, body, user_id, item_type, item_ref],
        ).fetchone()
        if updated is None:
            self._con.execute(
                """
                INSERT INTO saved_items (
                    id, user_id, item_type, item_ref, title, snippet, body,
                    source_json, topic_tags, kid_name, context_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    f"sv-{uuid.uuid4().hex[:12]}", user_id, item_type, item_ref,
                    title, snippet, body,
                    json.dumps(source or {}), json.dumps(topic_tags or []),
                    kid_name, json.dumps(context or {}),
                ],
            )
        row = self._con.execute(
            f"SELECT {self._SAVED_COLS} FROM saved_items "
            "WHERE user_id = ? AND item_type = ? AND item_ref = ?",
            [user_id, item_type, item_ref],
        ).fetchone()
        return self._saved_row(row)

    def unsave_item(self, *, user_id: str, item_type: str, item_ref: str) -> bool:
        """SOFT delete — the unsave timestamp is itself a signal."""
        row = self._con.execute(
            """
            UPDATE saved_items SET unsaved_at = now()
            WHERE user_id = ? AND item_type = ? AND item_ref = ? AND unsaved_at IS NULL
            RETURNING id
            """,
            [user_id, item_type, item_ref],
        ).fetchone()
        return row is not None

    def list_saved(self, user_id: str, *, item_type: Optional[str] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        if item_type:
            rows = self._con.execute(
                f"SELECT {self._SAVED_COLS} FROM saved_items "
                "WHERE user_id = ? AND unsaved_at IS NULL AND item_type = ? "
                "ORDER BY saved_at DESC LIMIT ?",
                [user_id, item_type, limit],
            ).fetchall()
        else:
            rows = self._con.execute(
                f"SELECT {self._SAVED_COLS} FROM saved_items "
                "WHERE user_id = ? AND unsaved_at IS NULL "
                "ORDER BY saved_at DESC LIMIT ?",
                [user_id, limit],
            ).fetchall()
        return [self._saved_row(r) for r in rows]

    def saved_refs(self, user_id: str, item_type: str) -> List[str]:
        """Active refs only — the client fetches this ONCE per surface and
        renders bookmark states locally (a per-card is_saved call is N+1)."""
        rows = self._con.execute(
            "SELECT item_ref FROM saved_items "
            "WHERE user_id = ? AND item_type = ? AND unsaved_at IS NULL",
            [user_id, item_type],
        ).fetchall()
        return [r[0] for r in rows]

    def saved_signal(self, user_id: str, *, top_tags: int = 5,
                     recent_titles: int = 5) -> Dict[str, Any]:
        """Revealed-preference digest for the coach prompt: what this parent
        ACTUALLY saves vs what they said at onboarding. Read-time only — never
        written into the editable profile."""
        tag_rows = self._con.execute(
            "SELECT topic_tags FROM saved_items "
            "WHERE user_id = ? AND unsaved_at IS NULL",
            [user_id],
        ).fetchall()
        counts: Dict[str, int] = {}
        for (raw,) in tag_rows:
            for tag in (json.loads(raw) if raw else []):
                counts[tag] = counts.get(tag, 0) + 1
        top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_tags]
        titles = [
            r[0] for r in self._con.execute(
                "SELECT title FROM saved_items "
                "WHERE user_id = ? AND unsaved_at IS NULL "
                "ORDER BY saved_at DESC LIMIT ?",
                [user_id, recent_titles],
            ).fetchall()
        ]
        return {"top_tags": top, "recent_titles": titles}

    def saved_activity_projection(self, user_id: str) -> List[Dict[str, Any]]:
        """Read-only projection of shortlisted activities for the merged Saved
        list. NEVER materialized into saved_items — dual-writing guarantees
        drift; unsaving an activity is a STATUS change in the Plan tab."""
        rows = self._con.execute(
            "SELECT id, name, status, activity_type, updated_at "
            "FROM tracked_activities "
            "WHERE user_id = ? AND status IN ('exploring', 'interested') "
            "ORDER BY updated_at DESC",
            [user_id],
        ).fetchall()
        return [
            {
                "id": r[0], "item_type": "activity", "item_ref": r[0],
                "title": r[1], "snippet": (r[3] or "camp").replace("_", " "),
                "body": "", "source": {"status": r[2]}, "topic_tags": [],
                "kid_name": None, "save_count": 1,
                "saved_at": r[4].isoformat() if r[4] else None,
                "origin": "plan",
            }
            for r in rows
        ]

    # ── Daily summaries ──────────────────────────────────────────────

    def get_kid_messages_in_range(
        self,
        agent_id: str,
        start_iso: str,
        end_iso: str,
        thread_id: str = "default",
    ) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            """
            SELECT id, role, content, created_at
            FROM kid_messages
            WHERE agent_id = ? AND thread_id = ?
              AND created_at >= ? AND created_at < ?
            ORDER BY created_at ASC
            """,
            [agent_id, thread_id, start_iso, end_iso],
        ).fetchall()
        return [
            {"id": r[0], "role": r[1], "content": r[2],
             "created_at": r[3].isoformat() if r[3] else None}
            for r in rows
        ]

    def save_daily_summary(
        self,
        *,
        user_id: str,
        kid_name: str,
        summary_date: str,                 # 'YYYY-MM-DD'
        agent_id: Optional[str],
        message_count: int,
        headline: str,
        curiosity: Optional[str],
        frustration: Optional[str],
        prompt_for_parent: Optional[str],
        full_json: Dict[str, Any],
    ) -> Dict[str, Any]:
        import uuid
        record_id = str(uuid.uuid4())
        # Upsert by (user_id, kid_name, date)
        existing = self._con.execute(
            "SELECT id FROM daily_summaries WHERE user_id=? AND kid_name=? AND summary_date=?",
            [user_id, kid_name, summary_date],
        ).fetchone()
        full_json_str = json.dumps(full_json, ensure_ascii=False)
        if existing:
            self._con.execute(
                """
                UPDATE daily_summaries SET
                    agent_id=?, message_count=?, headline=?, curiosity=?, frustration=?,
                    prompt_for_parent=?, full_json=?, created_at=now()
                WHERE id=?
                """,
                [agent_id, message_count, headline, curiosity, frustration,
                 prompt_for_parent, full_json_str, existing[0]],
            )
            return self.get_daily_summary(user_id, kid_name, summary_date)
        else:
            self._con.execute(
                """
                INSERT INTO daily_summaries (
                    id, user_id, kid_name, summary_date, agent_id, message_count,
                    headline, curiosity, frustration, prompt_for_parent, full_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now())
                """,
                [record_id, user_id, kid_name, summary_date, agent_id, message_count,
                 headline, curiosity, frustration, prompt_for_parent, full_json_str],
            )
            return self.get_daily_summary(user_id, kid_name, summary_date)

    def get_daily_summary(
        self, user_id: str, kid_name: str, summary_date: str,
    ) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            """
            SELECT id, summary_date, agent_id, message_count, headline, curiosity,
                   frustration, prompt_for_parent, full_json, created_at
            FROM daily_summaries
            WHERE user_id = ? AND kid_name = ? AND summary_date = ?
            """,
            [user_id, kid_name, summary_date],
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "summary_date": row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1]),
            "agent_id": row[2],
            "message_count": row[3],
            "headline": row[4],
            "curiosity": row[5],
            "frustration": row[6],
            "prompt_for_parent": row[7],
            "full_json": json.loads(row[8]) if row[8] else None,
            "created_at": row[9].isoformat() if row[9] else None,
        }

    def list_daily_summaries(
        self, user_id: str, kid_name: Optional[str] = None, limit: int = 30,
    ) -> List[Dict[str, Any]]:
        if kid_name:
            rows = self._con.execute(
                """
                SELECT id, kid_name, summary_date, message_count, headline,
                       curiosity, frustration, prompt_for_parent, created_at
                FROM daily_summaries
                WHERE user_id = ? AND kid_name = ?
                ORDER BY summary_date DESC
                LIMIT ?
                """,
                [user_id, kid_name, limit],
            ).fetchall()
        else:
            rows = self._con.execute(
                """
                SELECT id, kid_name, summary_date, message_count, headline,
                       curiosity, frustration, prompt_for_parent, created_at
                FROM daily_summaries
                WHERE user_id = ?
                ORDER BY summary_date DESC, kid_name ASC
                LIMIT ?
                """,
                [user_id, limit],
            ).fetchall()
        return [
            {
                "id": r[0], "kid_name": r[1],
                "summary_date": r[2].isoformat() if hasattr(r[2], "isoformat") else str(r[2]),
                "message_count": r[3], "headline": r[4],
                "curiosity": r[5], "frustration": r[6], "prompt_for_parent": r[7],
                "created_at": r[8].isoformat() if r[8] else None,
            } for r in rows
        ]

    # ── Parquet export / import ───────────────────────────────────────

    def _export_table_atomic(self, table: str, target: Path) -> None:
        """
        Export one table to parquet atomically (A3): COPY to a .tmp file, then
        os.replace() into place. An interrupted COPY can only corrupt the .tmp,
        never the live snapshot — and replace() is atomic on the same
        filesystem, so a reader never sees a half-written file.
        """
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        try:
            self._con.execute(
                f"COPY {table} TO '{tmp}' (FORMAT PARQUET, OVERWRITE_OR_IGNORE)"
            )
            os.replace(tmp, target)
        except Exception:
            try:
                if tmp.exists():
                    tmp.unlink()
            except Exception:
                pass
            raise

    def export_parquet(self, path: Path | str | None = None) -> Path:
        """Export the full user_data table to a parquet file (atomic)."""
        target = Path(path) if path else self.parquet_path
        self._export_table_atomic("user_data", target)
        logger.info(f"[duckdb] exported parquet → {target}")
        return target

    def export_content_parquet(self) -> None:
        """Export content tables to separate parquet files (atomic)."""
        for table in ("categories", "articles"):
            self._export_table_atomic(table, self.parquet_dir / f"{table}.parquet")

    # ── Activity planning: research runs + candidates ────────────────────
    #
    # The research_runs row is the durable background-job record (the phone never
    # holds the job). The worker claims a queued run atomically, executes the
    # deep-research graph, and writes candidates. A startup sweeper re-queues any
    # run left 'running' by a crash/restart; re-runs are idempotent because
    # insert_activity_candidates deletes prior rows for the run_id first.

    def create_research_run(
        self,
        *,
        user_id: str,
        location: Dict[str, Any],
        kids: List[Dict[str, Any]],
        params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Insert a queued run and return its run_id."""
        import uuid
        run_id = str(uuid.uuid4())
        with self._con.transaction():
            self.assert_family_writable(user_id)
            self._con.execute(
                """
                INSERT INTO research_runs (
                    id, user_id, status, location_json, kids_json, params_json,
                    progress_json, candidate_count, created_at
                ) VALUES (?, ?, 'queued', ?, ?, ?, ?, 0, now())
                """,
                [
                    run_id, user_id,
                    json.dumps(location, ensure_ascii=False),
                    json.dumps(kids, ensure_ascii=False),
                    json.dumps(params or {}, ensure_ascii=False),
                    json.dumps({"phase": "queued"}, ensure_ascii=False),
                ],
            )
        return run_id

    def enqueue_research_run(
        self,
        *,
        user_id: str,
        location: Dict[str, Any],
        kids: List[Dict[str, Any]],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Atomically dedupe-or-create a research run. If the user already has an
        in-flight run (queued or running), return it; otherwise create one. The
        check and the insert run under a single transaction — the storage RLock
        is held for its whole duration — so two simultaneous submits can't both
        create a run. Closes the check-then-create TOCTOU on POST /research/runs.
        Returns {run_id, status, deduped}."""
        with self._con.transaction():
            self.assert_family_writable(user_id)
            active = self.get_active_research_run(user_id)
            if active is not None:
                # A run still `queued` hasn't been claimed by a worker yet — so
                # RETARGET it to the NEW request (params/location/kids). Otherwise
                # a re-picked count/radius/focus is silently dropped and the run
                # keeps the old defaults (the "select 50 → get 25" bug). A run
                # already `running` can't be retargeted mid-flight, so it dedupes
                # as-is. The `status='queued'` guard makes the update a no-op if a
                # worker claimed it between the read and the write.
                if active.get("status") == "queued":
                    self._con.execute(
                        "UPDATE research_runs SET location_json = ?, kids_json = ?, "
                        "params_json = ? WHERE id = ? AND status = 'queued'",
                        [
                            json.dumps(location, ensure_ascii=False),
                            json.dumps(kids, ensure_ascii=False),
                            json.dumps(params or {}, ensure_ascii=False),
                            active["id"],
                        ],
                    )
                return {"run_id": active["id"], "status": active["status"], "deduped": True}
            run_id = self.create_research_run(
                user_id=user_id, location=location, kids=kids, params=params
            )
            return {"run_id": run_id, "status": "queued", "deduped": False}

    def claim_next_queued_run(self) -> Optional[Dict[str, Any]]:
        """Atomically pick the oldest queued run, flip it to running, and return
        it. Single UPDATE...RETURNING so two workers can't claim the same row."""
        row = self._con.execute(
            """
            UPDATE research_runs
               SET status = 'running', started_at = now(),
                   progress_json = json_object('phase', 'starting')
             WHERE id = (
                 SELECT id FROM research_runs
                  WHERE status = 'queued'
                  ORDER BY created_at
                  LIMIT 1
             )
            RETURNING id
            """,
        ).fetchone()
        if row is None:
            return None
        return self.get_research_run(row[0])

    def update_research_run(
        self,
        run_id: str,
        *,
        status: Optional[str] = None,
        progress: Optional[Dict[str, Any]] = None,
        candidate_count: Optional[int] = None,
        error: Optional[str] = None,
        finished: bool = False,
    ) -> None:
        """Patch mutable fields on a run. `finished=True` stamps finished_at."""
        sets: List[str] = []
        params: List[Any] = []
        if status is not None:
            sets.append("status = ?"); params.append(status)
        if progress is not None:
            sets.append("progress_json = ?"); params.append(json.dumps(progress, ensure_ascii=False))
        if candidate_count is not None:
            sets.append("candidate_count = ?"); params.append(candidate_count)
        if error is not None:
            sets.append("error = ?"); params.append(error)
        if finished:
            sets.append("finished_at = now()")
        if not sets:
            return
        params.append(run_id)
        self._con.execute(
            f"UPDATE research_runs SET {', '.join(sets)} WHERE id = ?",
            params,
        )

    def finalize_run_if_running(
        self,
        run_id: str,
        *,
        status: str,
        candidate_count: Optional[int] = None,
        error: Optional[str] = None,
        progress: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Write a terminal status (done/failed) ONLY if the run is still
        'running'. Returns True if it transitioned, False if the run had already
        left 'running' (e.g. the parent cancelled it mid-run). The conditional
        UPDATE closes the cancel-clobber race: a finished worker can't resurrect
        a cancelled run back to done/failed."""
        sets: List[str] = ["status = ?", "finished_at = now()"]
        params: List[Any] = [status]
        if candidate_count is not None:
            sets.append("candidate_count = ?"); params.append(candidate_count)
        if error is not None:
            sets.append("error = ?"); params.append(error)
        if progress is not None:
            sets.append("progress_json = ?"); params.append(json.dumps(progress, ensure_ascii=False))
        params.append(run_id)
        row = self._con.execute(
            f"UPDATE research_runs SET {', '.join(sets)} "
            "WHERE id = ? AND status = 'running' RETURNING id",
            params,
        ).fetchone()
        return row is not None

    def requeue_stale_running_runs(self) -> int:
        """Startup sweeper: a restart kills the in-flight worker thread, so any
        run still 'running' is orphaned. Re-queue it (re-runs are idempotent).
        Returns how many were re-queued."""
        rows = self._con.execute(
            """
            UPDATE research_runs
               SET status = 'queued', started_at = NULL,
                   progress_json = json_object('phase', 'requeued_after_restart')
             WHERE status = 'running'
            RETURNING id
            """,
        ).fetchall()
        if rows:
            logger.warning("[research] re-queued %d stale running run(s) after restart", len(rows))
        return len(rows)

    def get_research_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            """
            SELECT id, user_id, status, location_json, kids_json, params_json,
                   progress_json, candidate_count, error,
                   created_at, started_at, finished_at
            FROM research_runs WHERE id = ?
            """,
            [run_id],
        ).fetchone()
        return self._research_run_row_to_dict(row) if row else None

    def list_research_runs(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            """
            SELECT id, user_id, status, location_json, kids_json, params_json,
                   progress_json, candidate_count, error,
                   created_at, started_at, finished_at
            FROM research_runs
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [user_id, limit],
        ).fetchall()
        return [self._research_run_row_to_dict(r) for r in rows]

    def research_run_health(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Aggregate research-run health over the last `window_minutes` for the
        observability gauges (failure rate, worst queue wait, in-flight count).
        Cheap: count/filter over the (status, created_at) indexes."""
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        row = self._con.execute(
            """
            SELECT
                count(*)                                              AS total,
                count(*) FILTER (WHERE status = 'failed')             AS failed,
                count(*) FILTER (WHERE status IN ('queued','running')) AS in_flight,
                coalesce(max(CASE WHEN started_at IS NOT NULL
                     THEN datediff('second', created_at, started_at) END), 0) AS max_queue_wait_s
            FROM research_runs
            WHERE created_at > ?
            """,
            [cutoff],
        ).fetchone()
        total, failed, in_flight, max_qw = (row or (0, 0, 0, 0))
        return {
            "window_minutes": window_minutes,
            "total": int(total or 0),
            "failed": int(failed or 0),
            "in_flight": int(in_flight or 0),
            "failure_rate": (float(failed) / float(total)) if total else 0.0,
            "max_queue_wait_s": int(max_qw or 0),
        }

    def get_active_research_run(self, user_id: str) -> Optional[Dict[str, Any]]:
        """The user's most recent still-in-flight run (queued or running), if any.
        Used to dedupe rapid re-submits (double-taps) so they reuse the run in
        flight instead of piling extra runs behind it in the worker queue."""
        row = self._con.execute(
            """
            SELECT id, user_id, status, location_json, kids_json, params_json,
                   progress_json, candidate_count, error,
                   created_at, started_at, finished_at
            FROM research_runs
            WHERE user_id = ? AND status IN ('queued', 'running')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [user_id],
        ).fetchone()
        return self._research_run_row_to_dict(row) if row else None

    @staticmethod
    def _research_run_row_to_dict(row: Any) -> Dict[str, Any]:
        return {
            "id": row[0],
            "user_id": row[1],
            "status": row[2],
            "location": json.loads(row[3]) if row[3] else {},
            "kids": json.loads(row[4]) if row[4] else [],
            "params": json.loads(row[5]) if row[5] else {},
            "progress": json.loads(row[6]) if row[6] else {},
            "candidate_count": row[7],
            "error": row[8],
            "created_at": row[9].isoformat() if row[9] else None,
            "started_at": row[10].isoformat() if row[10] else None,
            "finished_at": row[11].isoformat() if row[11] else None,
        }

    # ── First-run agent warm-up: durable job rows + coach nudges ─────
    #
    # Same durable-job shape as research_runs (the phone never holds the job):
    # enqueue -> atomic claim -> run -> conditional finalize, with a startup
    # sweeper for rows a restart left 'running'. Driven by
    # app/onboarding_warmup.py — see that module for the step semantics.

    _WARMUP_COLS = (
        "id", "user_id", "status", "steps_json", "context_json", "result_json",
        "error", "created_at", "started_at", "finished_at",
    )

    @staticmethod
    def _warmup_run_row_to_dict(row: Any) -> Dict[str, Any]:
        return {
            "id": row[0],
            "user_id": row[1],
            "status": row[2],
            "steps": json.loads(row[3]) if row[3] else [],
            "context": json.loads(row[4]) if row[4] else {},
            "result": json.loads(row[5]) if row[5] else {},
            "error": row[6],
            "created_at": row[7].isoformat() if row[7] else None,
            "started_at": row[8].isoformat() if row[8] else None,
            "finished_at": row[9].isoformat() if row[9] else None,
        }

    def create_warmup_run(
        self,
        *,
        user_id: str,
        steps: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Insert a queued warm-up run and return its run_id."""
        import uuid
        run_id = str(uuid.uuid4())
        with self._con.transaction():
            self.assert_family_writable(user_id)
            self._con.execute(
                """
                INSERT INTO onboarding_warmup_runs (
                    id, user_id, status, steps_json, context_json, created_at
                ) VALUES (?, ?, 'queued', ?, ?, now())
                """,
                [
                    run_id, user_id,
                    json.dumps(steps, ensure_ascii=False),
                    json.dumps(context or {}, ensure_ascii=False),
                ],
            )
        return run_id

    def get_active_warmup_run(self, user_id: str) -> Optional[Dict[str, Any]]:
        """The user's in-flight warm-up (queued or running), if any."""
        row = self._con.execute(
            f"SELECT {', '.join(self._WARMUP_COLS)} FROM onboarding_warmup_runs "
            "WHERE user_id = ? AND status IN ('queued', 'running') "
            "ORDER BY created_at DESC LIMIT 1",
            [user_id],
        ).fetchone()
        return self._warmup_run_row_to_dict(row) if row else None

    def enqueue_warmup_run(
        self,
        *,
        user_id: str,
        steps: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Atomically dedupe-or-create. A double-tap on the progress screen
        resumes the same run instead of stacking a second one behind it; the
        check + insert share one transaction so two simultaneous submits can't
        both create. Returns {run_id, status, deduped}."""
        with self._con.transaction():
            self.assert_family_writable(user_id)
            active = self.get_active_warmup_run(user_id)
            if active is not None:
                return {"run_id": active["id"], "status": active["status"], "deduped": True}
            run_id = self.create_warmup_run(user_id=user_id, steps=steps, context=context)
            return {"run_id": run_id, "status": "queued", "deduped": False}

    def claim_next_queued_warmup_run(self) -> Optional[Dict[str, Any]]:
        """Atomically pick the oldest queued run and flip it to running. Single
        UPDATE...RETURNING so two workers can't claim the same row."""
        row = self._con.execute(
            """
            UPDATE onboarding_warmup_runs
               SET status = 'running', started_at = now()
             WHERE id = (
                 SELECT id FROM onboarding_warmup_runs
                  WHERE status = 'queued'
                  ORDER BY created_at
                  LIMIT 1
             )
            RETURNING id
            """,
        ).fetchone()
        if row is None:
            return None
        return self.get_warmup_run(row[0])

    def update_warmup_run(
        self,
        run_id: str,
        *,
        status: Optional[str] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        finished: bool = False,
    ) -> None:
        """Patch mutable fields. `finished=True` stamps finished_at."""
        sets: List[str] = []
        params: List[Any] = []
        if status is not None:
            sets.append("status = ?"); params.append(status)
        if steps is not None:
            sets.append("steps_json = ?"); params.append(json.dumps(steps, ensure_ascii=False))
        if result is not None:
            sets.append("result_json = ?"); params.append(json.dumps(result, ensure_ascii=False))
        if error is not None:
            sets.append("error = ?"); params.append(error)
        if finished:
            sets.append("finished_at = now()")
        if not sets:
            return
        params.append(run_id)
        self._con.execute(
            f"UPDATE onboarding_warmup_runs SET {', '.join(sets)} WHERE id = ?",
            params,
        )

    def finalize_warmup_run_if_running(
        self,
        run_id: str,
        *,
        status: str,
        steps: Optional[List[Dict[str, Any]]] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Write a terminal status ONLY if the run is still 'running' — the same
        cancel-clobber guard as finalize_run_if_running. Returns True if it
        transitioned, False if the run had already left 'running'."""
        sets: List[str] = ["status = ?", "finished_at = now()"]
        params: List[Any] = [status]
        if steps is not None:
            sets.append("steps_json = ?"); params.append(json.dumps(steps, ensure_ascii=False))
        if result is not None:
            sets.append("result_json = ?"); params.append(json.dumps(result, ensure_ascii=False))
        if error is not None:
            sets.append("error = ?"); params.append(error)
        params.append(run_id)
        row = self._con.execute(
            f"UPDATE onboarding_warmup_runs SET {', '.join(sets)} "
            "WHERE id = ? AND status = 'running' RETURNING id",
            params,
        ).fetchone()
        return row is not None

    def requeue_stale_warmup_runs(self) -> int:
        """Startup sweeper: a restart kills the in-flight worker thread, so any
        run still 'running' is orphaned. Re-queue it (steps are idempotent).
        Returns how many were re-queued."""
        rows = self._con.execute(
            """
            UPDATE onboarding_warmup_runs
               SET status = 'queued', started_at = NULL
             WHERE status = 'running'
            RETURNING id
            """,
        ).fetchall()
        if rows:
            logger.warning(
                "[warmup] re-queued %d stale running run(s) after restart", len(rows)
            )
        return len(rows)

    def get_warmup_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {', '.join(self._WARMUP_COLS)} FROM onboarding_warmup_runs WHERE id = ?",
            [run_id],
        ).fetchone()
        return self._warmup_run_row_to_dict(row) if row else None

    def list_warmup_runs(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT {', '.join(self._WARMUP_COLS)} FROM onboarding_warmup_runs "
            "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            [user_id, limit],
        ).fetchall()
        return [self._warmup_run_row_to_dict(r) for r in rows]

    # coach_nudges ----------------------------------------------------------

    def upsert_coach_nudge(
        self,
        *,
        user_id: str,
        body: str,
        source: str = "warmup",
        kid_name: Optional[str] = None,
        cta_label: Optional[str] = None,
        origin_id: Optional[str] = None,
    ) -> str:
        """Write the nudge for (user_id, source), replacing any prior one from
        that source. Delete-then-insert in one transaction keeps a warm-up
        re-run idempotent — a restart can't leave a parent with two first
        nudges. Returns the nudge id."""
        import uuid
        nudge_id = str(uuid.uuid4())
        with self._con.transaction():
            self._con.execute(
                "DELETE FROM coach_nudges WHERE user_id = ? AND source = ?",
                [user_id, source],
            )
            self._con.execute(
                """
                INSERT INTO coach_nudges (
                    id, user_id, source, kid_name, body, cta_label, origin_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, now())
                """,
                [nudge_id, user_id, source, kid_name, body, cta_label, origin_id],
            )
        return nudge_id

    def latest_coach_nudge(self, user_id: str) -> Optional[Dict[str, Any]]:
        """The newest nudge for a parent, whatever produced it. Drives Home's
        COACH card; None means the card falls back to its empty state."""
        row = self._con.execute(
            "SELECT id, user_id, source, kid_name, body, cta_label, origin_id, created_at "
            "FROM coach_nudges WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            [user_id],
        ).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "user_id": row[1],
            "source": row[2],
            "kid_name": row[3],
            "body": row[4],
            "cta_label": row[5],
            "origin_id": row[6],
            "created_at": row[7].isoformat() if row[7] else None,
        }

    def insert_activity_candidates(
        self,
        *,
        run_id: str,
        user_id: str,
        candidates: List[Dict[str, Any]],
    ) -> int:
        """Replace this run's candidates with `candidates` in one transaction.
        Delete-then-insert keeps a re-run (after a restart) idempotent. Returns
        the number inserted."""
        import uuid
        cols = (
            "id", "run_id", "user_id", "kid_name", "name", "provider", "category",
            "age_min", "age_max", "start_date", "end_date", "schedule_text",
            "price_text", "price_amount", "location_text", "city", "region",
            "distance_mi", "signup_url", "source_url", "contact_json", "fit_score",
            "fit_reason", "raw_json",
        )
        placeholders = ", ".join(["?"] * len(cols))
        with self._con.transaction() as con:
            con.execute("DELETE FROM activity_candidates WHERE run_id = ?", [run_id])
            for c in candidates:
                con.execute(
                    f"INSERT INTO activity_candidates ({', '.join(cols)}) VALUES ({placeholders})",
                    [
                        str(uuid.uuid4()), run_id, user_id,
                        c.get("kid_name"), c.get("name") or "Untitled", c.get("provider"),
                        c.get("category"), c.get("age_min"), c.get("age_max"),
                        c.get("start_date"), c.get("end_date"), c.get("schedule_text"),
                        c.get("price_text"), c.get("price_amount"), c.get("location_text"),
                        c.get("city"), c.get("region"), c.get("distance_mi"),
                        c.get("signup_url"), c.get("source_url"),
                        json.dumps(c.get("contact") or {}, ensure_ascii=False) if c.get("contact") else None,
                        c.get("fit_score"),
                        c.get("fit_reason"),
                        json.dumps(c.get("raw") or c, ensure_ascii=False),
                    ],
                )
        return len(candidates)

    def get_candidate_category(self, candidate_id: str) -> Optional[str]:
        row = self._con.execute(
            "SELECT category FROM activity_candidates WHERE id = ?", [candidate_id]
        ).fetchone()
        return row[0] if row else None

    def list_candidates(
        self,
        *,
        run_id: Optional[str] = None,
        user_id: Optional[str] = None,
        kid_name: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        where: List[str] = []
        params: List[Any] = []
        if run_id is not None:
            where.append("run_id = ?"); params.append(run_id)
        if user_id is not None:
            where.append("user_id = ?"); params.append(user_id)
        if kid_name is not None:
            where.append("kid_name = ?"); params.append(kid_name)
        if category is not None:
            where.append("category = ?"); params.append(category)
        clause = ("WHERE " + " AND ".join(where)) if where else ""
        params.append(limit)
        rows = self._con.execute(
            f"""
            SELECT id, run_id, user_id, kid_name, name, provider, category,
                   age_min, age_max, start_date, end_date, schedule_text,
                   price_text, price_amount, location_text, city, region, distance_mi,
                   signup_url, source_url, contact_json, fit_score, fit_reason, raw_json, created_at
            FROM activity_candidates
            {clause}
            ORDER BY fit_score DESC NULLS LAST, created_at
            LIMIT ?
            """,
            params,
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append({
                "id": r[0], "run_id": r[1], "user_id": r[2], "kid_name": r[3],
                "name": r[4], "provider": r[5], "category": r[6],
                "age_min": r[7], "age_max": r[8],
                "start_date": r[9].isoformat() if r[9] else None,
                "end_date": r[10].isoformat() if r[10] else None,
                "schedule_text": r[11], "price_text": r[12], "price_amount": r[13],
                "location_text": r[14], "city": r[15], "region": r[16],
                "distance_mi": r[17],
                "signup_url": r[18], "source_url": r[19],
                "contact": json.loads(r[20]) if r[20] else None,
                "fit_score": r[21],
                "fit_reason": r[22],
                "raw": json.loads(r[23]) if r[23] else None,
                "created_at": r[24].isoformat() if r[24] else None,
            })
        return out

    # ── Chief-of-Staff CRUD ──────────────────────────────────────────
    #
    # Small shared helpers keep the per-table methods terse. JSON columns are
    # stored under a *_json name in the DDL but exposed to callers under a clean
    # key (contact_json -> contact, etc.); ts/date columns are serialised to
    # ISO strings on read.

    def _cos_update(
        self,
        table: str,
        row_id: str,
        fields: Dict[str, Any],
        *,
        json_cols: Iterable[str] = (),
        touch_updated: bool = True,
    ) -> None:
        """Build a dynamic UPDATE ... SET for a Chief-of-Staff row.

        Skips keys whose value is None (so callers pass **fields and only the
        present ones land). Keys in `json_cols` are json.dumps'd. When
        `touch_updated` is True an `updated_at = now()` is appended (tables that
        have no updated_at column pass touch_updated=False)."""
        json_set = set(json_cols)
        sets: List[str] = []
        params: List[Any] = []
        for key, value in fields.items():
            if value is None:
                continue
            sets.append(f"{key} = ?")
            if key in json_set:
                params.append(json.dumps(value, ensure_ascii=False))
            else:
                params.append(value)
        if not sets:
            return
        if touch_updated:
            sets.append("updated_at = now()")
        params.append(row_id)
        self._con.execute(
            f"UPDATE {table} SET {', '.join(sets)} WHERE id = ?", params
        )

    @staticmethod
    def _row_to_dict(
        cols: Iterable[str],
        row: Any,
        *,
        json_cols: Iterable[str] = (),
        ts_cols: Iterable[str] = (),
    ) -> Dict[str, Any]:
        """Zip a column list with a row tuple into a JSON-friendly dict.

        `json_cols` is a mapping-as-tuples of (db_col, clean_key) so a column
        like `contact_json` is parsed and re-keyed to `contact`. `ts_cols` are
        ISO-serialised."""
        json_map = dict(json_cols)
        ts_set = set(ts_cols)
        out: Dict[str, Any] = {}
        for col, val in zip(cols, row):
            if col in json_map:
                out[json_map[col]] = json.loads(val) if val else None
            elif col in ts_set:
                out[col] = val.isoformat() if val else None
            else:
                out[col] = val
        return out

    # tracked_activities ----------------------------------------------------

    _TRACKED_COLS = (
        "id", "user_id", "kid_name", "candidate_id", "name", "provider",
        "activity_type", "week_start", "start_date", "end_date",
        "rrule", "recur_time", "recur_duration_min", "status", "pending_reason",
        "price_amount", "price_status",
        "signup_url", "contact_json", "carpool_with", "details_json", "notes",
        "decision_rationale", "fit_score", "fit_reason", "created_at", "updated_at",
    )

    def track_activity(
        self,
        user_id: str,
        *,
        name: str,
        kid_name: Optional[str] = None,
        candidate_id: Optional[str] = None,
        provider: Optional[str] = None,
        activity_type: Optional[str] = None,
        week_start: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        rrule: Optional[str] = None,
        recur_time: Optional[str] = None,
        recur_duration_min: Optional[int] = None,
        status: str = "exploring",
        pending_reason: Optional[str] = None,
        price_amount: Optional[float] = None,
        price_status: str = "tbd",
        signup_url: Optional[str] = None,
        contact: Optional[Dict[str, Any]] = None,
        carpool_with: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        decision_rationale: Optional[str] = None,
        fit_score: Optional[float] = None,
        fit_reason: Optional[str] = None,
    ) -> str:
        import uuid

        from app.cos.verticals import (
            ACTIVITY_TYPES, derive_from_category, normalize_activity_type,
        )

        # Explicit valid type wins; otherwise a pinned candidate's category
        # decides (the LLM-facing default must not override what the candidate
        # already tells us); otherwise the camp default.
        atype = (activity_type or "").strip().lower()
        if atype not in ACTIVITY_TYPES:
            if candidate_id:
                atype = derive_from_category(self.get_candidate_category(candidate_id))
            else:
                atype = normalize_activity_type(activity_type)

        # Copy forward fit_score and fit_reason from the candidate when tracking
        # one (so "75% Match" / "Why it matched" survive into Planned). Explicit
        # args win (allows manual override), then candidate lookup, then None.
        if candidate_id and (fit_score is None or fit_reason is None):
            row = self._con.execute(
                "SELECT fit_score, fit_reason FROM activity_candidates WHERE id = ?",
                [candidate_id]
            ).fetchone()
            if row:
                if fit_score is None:
                    fit_score = row[0]
                if fit_reason is None:
                    fit_reason = row[1]

        # Copy forward the candidate's descriptive fields (ages, schedule,
        # price text, location, category) so a saved activity's detail view
        # doesn't go blank the moment it leaves the search results — those
        # fields have no dedicated tracked_activities columns, so they ride
        # in details_json (round 4: iOS detail view was dropping to just
        # kid/cost because the client saves lost this data on the way in).
        # start_date/end_date DO have columns; fill them only if the caller
        # didn't already set them explicitly.
        if candidate_id:
            crow = self._con.execute(
                """SELECT age_min, age_max, schedule_text, price_text, location_text,
                          city, category, start_date, end_date
                   FROM activity_candidates WHERE id = ?""",
                [candidate_id]
            ).fetchone()
            if crow:
                cand_details = {
                    "age_min": crow[0], "age_max": crow[1],
                    "schedule_text": crow[2], "price_text": crow[3],
                    "location_text": crow[4], "city": crow[5], "category": crow[6],
                }
                cand_details = {k: v for k, v in cand_details.items() if v is not None}
                if cand_details:
                    details = {**cand_details, **(details or {})}
                if start_date is None and crow[7] is not None:
                    start_date = str(crow[7])
                if end_date is None and crow[8] is not None:
                    end_date = str(crow[8])

        activity_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO tracked_activities (
                id, user_id, kid_name, candidate_id, name, provider,
                activity_type,
                status, pending_reason, price_amount, price_status, signup_url,
                contact_json, carpool_with, details_json, notes, decision_rationale,
                fit_score, fit_reason,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now(), now())
            """,
            [
                activity_id, user_id, kid_name, candidate_id, name, provider,
                atype,
                status, pending_reason, price_amount, price_status,
                signup_url,
                json.dumps(contact, ensure_ascii=False) if contact else None,
                carpool_with,
                json.dumps(details, ensure_ascii=False) if details else None,
                notes, decision_rationale,
                fit_score, fit_reason,
            ],
        )
        # ALL date writes flow through the one write path (v17). Legacy callers
        # that still send week_start mean "the week block starting that date".
        if rrule or start_date or week_start:
            self.set_activity_dates(
                activity_id,
                start_date=start_date or week_start,
                end_date=end_date,
                rrule=rrule,
                recur_time=recur_time,
                recur_duration_min=recur_duration_min,
            )
        return activity_id

    def set_activity_dates(
        self,
        activity_id: str,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        rrule: Optional[str] = None,
        recur_time: Optional[str] = None,
        recur_duration_min: Optional[int] = None,
    ) -> None:
        """THE date write path for tracked activities (v17) — no caller writes
        week_start/start_date/rrule columns directly.

        Shapes (by the vertical's date_model):
        - week_block (no rrule): ``start_date`` anchors the week —
          ``week_start`` is DERIVED (= start_date) and ``end_date`` defaults to
          start_date + 4 days.
        - single_date / date_range (no rrule, Phases 5–6): same start/end
          columns, but a missing ``end_date`` defaults to ``start_date`` — a
          school event or trip must never get a fabricated workweek.
        - recurring_weekly (rrule set): the RRULE string is the single source
          of truth; ``week_start`` is cleared, and the derived
          recurring_appointments row (activity_id back-reference) is
          REGENERATED — never hand-edited.
        """
        activity = self.get_tracked_activity(activity_id)
        if not activity:
            raise ValueError(f"tracked activity {activity_id} not found")

        from app.cos.verticals import get_profile
        profile_model = get_profile(activity.get("activity_type")).date_model

        from app import observability as obs
        obs.count("cos.dates.write",
                  date_model="recurring_weekly" if rrule
                  else profile_model if profile_model in ("single_date", "date_range")
                  else "week_block")

        if rrule:
            self._con.execute(
                """
                UPDATE tracked_activities
                SET rrule = ?, recur_time = ?, recur_duration_min = ?,
                    start_date = ?, end_date = ?, week_start = NULL,
                    updated_at = now()
                WHERE id = ?
                """,
                [rrule, recur_time, recur_duration_min,
                 start_date, end_date, activity_id],
            )
            self._regenerate_recurring_for_activity(
                activity, rrule=rrule, recur_time=recur_time,
                recur_duration_min=recur_duration_min,
                active_from=start_date, active_to=end_date,
            )
            return

        if start_date:
            derived_end = end_date
            if derived_end is None:
                if profile_model in ("single_date", "date_range"):
                    # One stated day IS the item (picture day, a trip whose
                    # return date isn't known yet) — never fabricate a week.
                    derived_end = str(start_date)[:10]
                else:
                    from datetime import date, timedelta
                    derived_end = (date.fromisoformat(str(start_date)[:10])
                                   + timedelta(days=4)).isoformat()
            self._con.execute(
                """
                UPDATE tracked_activities
                SET start_date = ?, end_date = ?, week_start = ?,
                    rrule = NULL, recur_time = NULL, recur_duration_min = NULL,
                    updated_at = now()
                WHERE id = ?
                """,
                [start_date, derived_end, start_date, activity_id],
            )
            # An activity that stops recurring loses its derived row too.
            self._delete_recurring_for_activity(activity_id)

    _RRULE_WEEKDAYS = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}

    def _regenerate_recurring_for_activity(
        self,
        activity: Dict[str, Any],
        *,
        rrule: str,
        recur_time: Optional[str],
        recur_duration_min: Optional[int],
        active_from: Optional[str],
        active_to: Optional[str],
    ) -> None:
        """Regenerate the DERIVED recurring_appointments row for an activity's
        rrule (delete + reinsert keyed on activity_id). Weekly-only in Phase 2:
        one BYDAY -> one row; parsing is lenient (a malformed rrule just skips
        derivation — the activity row still holds the truth)."""
        activity_id = activity["id"]
        self._delete_recurring_for_activity(activity_id)
        parts = {
            kv.split("=", 1)[0].strip().upper(): kv.split("=", 1)[1].strip().upper()
            for kv in (rrule or "").split(";") if "=" in kv
        }
        byday = (parts.get("BYDAY") or "").split(",")[0]
        weekday = self._RRULE_WEEKDAYS.get(byday)
        if weekday is None:
            return
        end_time = None
        if recur_time and recur_duration_min:
            try:
                from datetime import datetime, timedelta
                t = datetime.strptime(recur_time, "%H:%M")
                end_time = (t + timedelta(minutes=int(recur_duration_min))).strftime("%H:%M")
            except Exception:
                end_time = None
        self.add_recurring_appointment(
            activity["user_id"],
            title=activity.get("name") or "Recurring activity",
            kid_name=activity.get("kid_name"),
            provider_name=activity.get("provider"),
            weekday=weekday,
            start_time=recur_time,
            end_time=end_time,
            active_from=active_from,
            active_to=active_to,
            activity_id=activity_id,
        )

    def _delete_recurring_for_activity(self, activity_id: str) -> None:
        self._con.execute(
            "DELETE FROM recurring_appointments WHERE activity_id = ?",
            [activity_id],
        )

    def get_tracked_activity(self, activity_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {', '.join(self._TRACKED_COLS)} FROM tracked_activities WHERE id = ?",
            [activity_id],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(
            self._TRACKED_COLS, row,
            json_cols=(("contact_json", "contact"), ("details_json", "details")),
            ts_cols=("week_start", "start_date", "end_date", "created_at", "updated_at"),
        )

    def list_tracked_activities(
        self, user_id: str, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        where = "WHERE user_id = ?"
        params: List[Any] = [user_id]
        if status is not None:
            where += " AND status = ?"
            params.append(status)
        rows = self._con.execute(
            f"SELECT {', '.join(self._TRACKED_COLS)} FROM tracked_activities "
            f"{where} ORDER BY created_at",
            params,
        ).fetchall()
        return [
            self._row_to_dict(
                self._TRACKED_COLS, r,
                json_cols=(("contact_json", "contact"), ("details_json", "details")),
                ts_cols=("week_start", "start_date", "end_date", "created_at", "updated_at"),
            )
            for r in rows
        ]

    def update_tracked_activity(self, activity_id: str, **fields: Any) -> None:
        # Date fields (week_start/start_date/end_date/rrule/...) are DELIBERATELY
        # not writable here — set_activity_dates is the one date write path
        # (v17); callers route date changes there so week_start stays derived
        # and recurring rows stay regenerated.
        allowed = {
            "status", "pending_reason", "price_amount", "price_status",
            "signup_url", "notes", "decision_rationale",
            "carpool_with", "contact", "details", "activity_type",
        }
        patch: Dict[str, Any] = {}
        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "contact":
                patch["contact_json"] = value
            elif key == "details":
                patch["details_json"] = value
            else:
                patch[key] = value
        self._cos_update(
            "tracked_activities", activity_id, patch,
            json_cols=("contact_json", "details_json"),
        )

    def delete_tracked_activity(self, activity_id: str) -> None:
        """Remove a tracked activity permanently. CASCADES to every row that
        references it (to-dos, its calendar entries + their logistics) — orphans
        resurrect the "deleted" thing (see CLAUDE.md: deletes cascade)."""
        with self._con.transaction():
            self._con.execute("DELETE FROM todo_items WHERE activity_id = ?", [activity_id])
            self._con.execute(
                "DELETE FROM logistics_assignments WHERE calendar_entry_id IN "
                "(SELECT id FROM calendar_entries WHERE activity_id = ?)",
                [activity_id],
            )
            self._con.execute("DELETE FROM calendar_entries WHERE activity_id = ?", [activity_id])
            self._con.execute(
                "DELETE FROM recurring_appointments WHERE activity_id = ?", [activity_id]
            )
            self._con.execute(
                "DELETE FROM window_notifications WHERE window_id IN "
                "(SELECT id FROM registration_windows WHERE activity_id = ?)",
                [activity_id],
            )
            self._con.execute(
                "DELETE FROM registration_windows WHERE activity_id = ?", [activity_id]
            )
            self._con.execute("DELETE FROM tracked_activities WHERE id = ?", [activity_id])

    def reset_plan(self, *, user_id: str, actor: str) -> Dict[str, int]:
        """Wipe the user's PLAN slate — activities, to-dos, calendar, logistics,
        recurring appointments, caregivers, discovery results/runs, ingested
        artifacts — so they can start from scratch. KEEPS profile/kids, chats,
        integrations, and kid-agent data (this is a plan reset, not an account
        delete; cf. delete_family). One transaction; audit-logged; returns
        per-table deleted counts."""
        tables = [
            "todo_items",
            "logistics_assignments",
            "calendar_entries",
            "recurring_appointments",
            "caregivers",
            "tracked_activities",
            "activity_candidates",
            "research_runs",
            "ingest_artifacts",
            "registration_windows",  # notifications cascade below
        ]
        deleted: Dict[str, int] = {}
        with self._con.transaction():
            self._con.execute(
                "DELETE FROM window_notifications WHERE window_id IN "
                "(SELECT id FROM registration_windows WHERE user_id = ?)",
                [user_id],
            )
            for table in tables:
                deleted[table] = self._con.execute(
                    f"SELECT count(*) FROM {table} WHERE user_id = ?", [user_id]
                ).fetchone()[0]
                self._con.execute(f"DELETE FROM {table} WHERE user_id = ?", [user_id])
            # household_members SURVIVES a plan reset (it is the Circle, not
            # the plan) — but the caregivers rows it mirrors just went, so
            # clear the dangling links rather than leaving them pointing at
            # deleted ids.
            self._con.execute(
                "UPDATE household_members SET caregiver_id = NULL, updated_at = now() "
                "WHERE user_id = ? AND caregiver_id IS NOT NULL",
                [user_id],
            )
        self.write_audit_event(
            user_id=user_id, actor=actor, action="plan_reset",
            details={"counts": deleted},
        )
        return deleted

    # registration windows (Phase 4 watchlist) ------------------------------

    _WINDOW_COLS = (
        "id", "user_id", "activity_id", "provider", "signup_url",
        "opens_at", "tz", "opens_time_known", "closes_at",
        "source", "confidence", "status", "metro", "created_at", "updated_at",
    )
    _WINDOW_TS = ("opens_at", "closes_at", "created_at", "updated_at")

    def transaction(self):
        """Public transaction context (holds the connection lock across the
        block). The watchlist worker's durable-first delivery uses this:
        notification row + fallback to-do commit atomically BEFORE any push."""
        return self._con.transaction()

    def create_registration_window(
        self,
        user_id: str,
        *,
        activity_id: Optional[str] = None,
        provider: Optional[str] = None,
        signup_url: Optional[str] = None,
        opens_at: Optional[str] = None,
        tz: Optional[str] = None,
        opens_time_known: bool = False,
        closes_at: Optional[str] = None,
        source: str = "manual",
        confidence: str = "confirmed",
        metro: Optional[str] = None,
    ) -> str:
        import uuid
        window_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO registration_windows (
                id, user_id, activity_id, provider, signup_url, opens_at, tz,
                opens_time_known, closes_at, source, confidence, status, metro,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'watching', ?, now(), now())
            """,
            [window_id, user_id, activity_id, provider, signup_url, opens_at,
             tz, bool(opens_time_known), closes_at, source, confidence, metro],
        )
        return window_id

    def get_registration_window(self, window_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {', '.join(self._WINDOW_COLS)} FROM registration_windows WHERE id = ?",
            [window_id],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(self._WINDOW_COLS, row, ts_cols=self._WINDOW_TS)

    def list_registration_windows(
        self, user_id: str, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        where = "WHERE user_id = ?"
        params: List[Any] = [user_id]
        if status is not None:
            where += " AND status = ?"
            params.append(status)
        rows = self._con.execute(
            f"SELECT {', '.join(self._WINDOW_COLS)} FROM registration_windows "
            f"{where} ORDER BY opens_at NULLS LAST, created_at",
            params,
        ).fetchall()
        return [self._row_to_dict(self._WINDOW_COLS, r, ts_cols=self._WINDOW_TS)
                for r in rows]

    def list_watching_windows(self) -> List[Dict[str, Any]]:
        """Every watching window across ALL users — the worker's sweep input."""
        rows = self._con.execute(
            f"SELECT {', '.join(self._WINDOW_COLS)} FROM registration_windows "
            "WHERE status = 'watching' ORDER BY opens_at NULLS LAST",
        ).fetchall()
        return [self._row_to_dict(self._WINDOW_COLS, r, ts_cols=self._WINDOW_TS)
                for r in rows]

    def update_registration_window(self, window_id: str, **fields: Any) -> None:
        allowed = {
            "activity_id", "provider", "signup_url", "opens_at", "tz",
            "opens_time_known", "closes_at", "source", "confidence",
            "status", "metro",
        }
        patch = {k: v for k, v in fields.items() if k in allowed}
        if not patch:
            return
        sets = ", ".join(f"{k} = ?" for k in patch)
        self._con.execute(
            f"UPDATE registration_windows SET {sets}, updated_at = now() WHERE id = ?",
            [*patch.values(), window_id],
        )

    # Append-only delivery log ----------------------------------------------

    def window_notification_exists(
        self, window_id: str, kind: str, opens_at_snapshot: Optional[str]
    ) -> bool:
        """The due-selection guard: one delivery per (window, kind, snapshot).
        A CHANGED opens_at is a new snapshot → the window re-arms by design."""
        row = self._con.execute(
            "SELECT 1 FROM window_notifications WHERE window_id = ? AND kind = ? "
            "AND opens_at_snapshot IS NOT DISTINCT FROM ? LIMIT 1",
            [window_id, kind, opens_at_snapshot],
        ).fetchone()
        return row is not None

    def insert_window_notification(
        self,
        *,
        window_id: str,
        kind: str,
        opens_at_snapshot: Optional[str],
        transport: str,
        outcome: Optional[str] = None,
    ) -> str:
        import uuid
        notification_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO window_notifications (
                id, window_id, kind, opens_at_snapshot, sent_at, transport, outcome
            ) VALUES (?, ?, ?, ?, now(), ?, ?)
            """,
            [notification_id, window_id, kind, opens_at_snapshot, transport, outcome],
        )
        return notification_id

    def set_window_notification_outcome(self, notification_id: str, outcome: str) -> None:
        self._con.execute(
            "UPDATE window_notifications SET outcome = ? WHERE id = ?",
            [outcome, notification_id],
        )

    def list_window_notifications(self, window_id: str) -> List[Dict[str, Any]]:
        cols = ("id", "window_id", "kind", "opens_at_snapshot", "sent_at",
                "transport", "outcome")
        rows = self._con.execute(
            f"SELECT {', '.join(cols)} FROM window_notifications "
            "WHERE window_id = ? ORDER BY sent_at",
            [window_id],
        ).fetchall()
        return [self._row_to_dict(cols, r, ts_cols=("opens_at_snapshot", "sent_at"))
                for r in rows]

    def count_missed_windows(self) -> int:
        """The miss detector's input: watching windows already PAST opens_at
        with no day_of delivery row for the current snapshot. Anything > 0 is
        a broken promise — Grafana alerts on it."""
        row = self._con.execute(
            """
            SELECT count(*) FROM registration_windows w
            WHERE w.status = 'watching' AND w.opens_at IS NOT NULL
              AND w.opens_at < now()
              AND NOT EXISTS (
                  SELECT 1 FROM window_notifications n
                  WHERE n.window_id = w.id AND n.kind = 'day_of'
                    AND n.opens_at_snapshot IS NOT DISTINCT FROM w.opens_at
              )
            """,
        ).fetchone()
        return int(row[0]) if row else 0

    # calendar_entries ------------------------------------------------------

    _CALENDAR_COLS = (
        "id", "user_id", "kid_name", "activity_id", "title", "week_start",
        "start_ts", "end_ts", "all_day", "location_text", "kind", "status",
        "source", "provider_event_id", "synced_at", "created_at", "updated_at",
    )
    _CALENDAR_TS = ("week_start", "start_ts", "end_ts", "synced_at", "created_at", "updated_at")

    def add_calendar_entry(
        self,
        user_id: str,
        *,
        title: str,
        kid_name: Optional[str] = None,
        activity_id: Optional[str] = None,
        week_start: Optional[str] = None,
        start_ts: Optional[str] = None,
        end_ts: Optional[str] = None,
        all_day: bool = False,
        location_text: Optional[str] = None,
        kind: str = "camp",
        status: str = "confirmed",
        source: str = "manual",
        provider_event_id: Optional[str] = None,
    ) -> str:
        import uuid
        entry_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO calendar_entries (
                id, user_id, kid_name, activity_id, title, week_start,
                start_ts, end_ts, all_day, location_text, kind, status, source,
                provider_event_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now(), now())
            """,
            [
                entry_id, user_id, kid_name, activity_id, title, week_start,
                start_ts, end_ts, all_day, location_text, kind, status, source,
                provider_event_id,
            ],
        )
        return entry_id

    def get_calendar_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {', '.join(self._CALENDAR_COLS)} FROM calendar_entries WHERE id = ?",
            [entry_id],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(self._CALENDAR_COLS, row, ts_cols=self._CALENDAR_TS)

    def get_calendar_entry_by_provider_event(
        self, user_id: str, provider_event_id: str
    ) -> Optional[Dict[str, Any]]:
        """Look up an entry by its Google Calendar event id — used by the pull
        leg to dedupe (our own pushed echo) and to update an imported event."""
        row = self._con.execute(
            f"SELECT {', '.join(self._CALENDAR_COLS)} FROM calendar_entries "
            "WHERE user_id = ? AND provider_event_id = ?",
            [user_id, provider_event_id],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(self._CALENDAR_COLS, row, ts_cols=self._CALENDAR_TS)

    def list_calendar_entries(
        self,
        user_id: str,
        *,
        week_start: Optional[str] = None,
        kid_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        where = "WHERE user_id = ?"
        params: List[Any] = [user_id]
        if week_start is not None:
            where += " AND week_start = ?"
            params.append(week_start)
        if kid_name is not None:
            where += " AND kid_name = ?"
            params.append(kid_name)
        rows = self._con.execute(
            f"SELECT {', '.join(self._CALENDAR_COLS)} FROM calendar_entries "
            f"{where} ORDER BY start_ts NULLS LAST, week_start",
            params,
        ).fetchall()
        return [
            self._row_to_dict(self._CALENDAR_COLS, r, ts_cols=self._CALENDAR_TS)
            for r in rows
        ]

    def list_calendar_entries_to_push(self, user_id: str) -> List[Dict[str, Any]]:
        """Entries we own (source != 'gcal') with a concrete start that are new
        or have been locally edited since the last push (synced_at is NULL or
        older than updated_at). The calendar-sync push leg iterates these."""
        rows = self._con.execute(
            f"SELECT {', '.join(self._CALENDAR_COLS)} FROM calendar_entries "
            "WHERE user_id = ? AND source != 'gcal' AND start_ts IS NOT NULL "
            "AND (synced_at IS NULL OR updated_at > synced_at) "
            "ORDER BY start_ts",
            [user_id],
        ).fetchall()
        return [
            self._row_to_dict(self._CALENDAR_COLS, r, ts_cols=self._CALENDAR_TS)
            for r in rows
        ]

    def mark_calendar_pushed(self, entry_id: str, provider_event_id: str) -> None:
        """Stamp an entry as reconciled with the provider: record the event id +
        synced_at. Deliberately does NOT bump updated_at, so the dirty-check
        (updated_at > synced_at) only fires again on a real local edit."""
        self._con.execute(
            "UPDATE calendar_entries SET provider_event_id = ?, synced_at = now() WHERE id = ?",
            [provider_event_id, entry_id],
        )

    def update_calendar_entry(self, entry_id: str, **fields: Any) -> None:
        allowed = {
            "title", "kid_name", "week_start", "start_ts", "end_ts", "all_day",
            "location_text", "kind", "status",
        }
        patch = {k: v for k, v in fields.items() if k in allowed}
        self._cos_update("calendar_entries", entry_id, patch)

    def delete_calendar_entry(self, entry_id: str) -> None:
        self._con.execute("DELETE FROM calendar_entries WHERE id = ?", [entry_id])

    # recurring_appointments ------------------------------------------------

    _RECURRING_COLS = (
        "id", "user_id", "kid_name", "title", "provider_name", "weekday",
        "start_time", "end_time", "transporter", "notes", "active_from",
        "active_to", "activity_id", "created_at",
    )

    def add_recurring_appointment(
        self,
        user_id: str,
        *,
        title: str,
        kid_name: Optional[str] = None,
        provider_name: Optional[str] = None,
        weekday: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        transporter: Optional[str] = None,
        notes: Optional[str] = None,
        active_from: Optional[str] = None,
        active_to: Optional[str] = None,
        activity_id: Optional[str] = None,
    ) -> str:
        import uuid
        appt_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO recurring_appointments (
                id, user_id, kid_name, title, provider_name, weekday,
                start_time, end_time, transporter, notes, active_from, active_to,
                activity_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now())
            """,
            [
                appt_id, user_id, kid_name, title, provider_name, weekday,
                start_time, end_time, transporter, notes, active_from, active_to,
                activity_id,
            ],
        )
        return appt_id

    def list_recurring_appointments(self, user_id: str) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT {', '.join(self._RECURRING_COLS)} FROM recurring_appointments "
            "WHERE user_id = ? ORDER BY created_at",
            [user_id],
        ).fetchall()
        return [
            self._row_to_dict(
                self._RECURRING_COLS, r,
                ts_cols=("active_from", "active_to", "created_at"),
            )
            for r in rows
        ]

    def delete_recurring_appointment(self, appt_id: str) -> None:
        self._con.execute(
            "DELETE FROM recurring_appointments WHERE id = ?", [appt_id]
        )

    # caregivers ------------------------------------------------------------

    _CAREGIVER_COLS = (
        "id", "user_id", "name", "role", "contact_json",
        "default_availability_json", "notes", "created_at",
    )

    def add_caregiver(
        self,
        user_id: str,
        *,
        name: str,
        role: str = "other",
        contact: Optional[Dict[str, Any]] = None,
        default_availability: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> str:
        import uuid
        caregiver_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO caregivers (
                id, user_id, name, role, contact_json,
                default_availability_json, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, now())
            """,
            [
                caregiver_id, user_id, name, role,
                json.dumps(contact, ensure_ascii=False) if contact else None,
                json.dumps(default_availability, ensure_ascii=False) if default_availability else None,
                notes,
            ],
        )
        return caregiver_id

    def list_caregivers(self, user_id: str) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT {', '.join(self._CAREGIVER_COLS)} FROM caregivers "
            "WHERE user_id = ? ORDER BY created_at",
            [user_id],
        ).fetchall()
        return [
            self._row_to_dict(
                self._CAREGIVER_COLS, r,
                json_cols=(
                    ("contact_json", "contact"),
                    ("default_availability_json", "default_availability"),
                ),
                ts_cols=("created_at",),
            )
            for r in rows
        ]

    def update_caregiver(self, caregiver_id: str, **fields: Any) -> None:
        allowed = {"name", "role", "notes", "contact", "default_availability"}
        patch: Dict[str, Any] = {}
        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "contact":
                patch["contact_json"] = value
            elif key == "default_availability":
                patch["default_availability_json"] = value
            else:
                patch[key] = value
        self._cos_update(
            "caregivers", caregiver_id, patch,
            json_cols=("contact_json", "default_availability_json"),
            touch_updated=False,
        )

    # household_members (Circle) --------------------------------------------

    _MEMBER_COLS = (
        "id", "user_id", "kind", "display_name", "role", "relation",
        "mvp_username", "email", "avatar_key", "member_user_id",
        "attributes_json", "notes", "caregiver_id", "created_at", "updated_at",
    )

    # Columns a PATCH may set. `user_id`/`id`/`created_at` are never writable;
    # `attributes` is re-keyed to attributes_json by the caller.
    _MEMBER_PATCHABLE = (
        "kind", "display_name", "role", "relation", "mvp_username", "email",
        "avatar_key", "member_user_id", "attributes_json", "notes", "caregiver_id",
    )

    def _member_row(self, row: Any) -> Dict[str, Any]:
        return self._row_to_dict(
            self._MEMBER_COLS, row,
            json_cols=(("attributes_json", "attributes"),),
            ts_cols=("created_at", "updated_at"),
        )

    def add_household_member(
        self,
        user_id: str,
        *,
        display_name: str,
        role: str = "other",
        kind: str = "adult",
        relation: Optional[str] = None,
        mvp_username: Optional[str] = None,
        email: Optional[str] = None,
        avatar_key: Optional[str] = None,
        member_user_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        caregiver_id: Optional[str] = None,
    ) -> str:
        import uuid
        member_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO household_members (
                id, user_id, kind, display_name, role, relation, mvp_username,
                email, avatar_key, member_user_id, attributes_json, notes,
                caregiver_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now(), now())
            """,
            [
                member_id, user_id, kind, display_name, role, relation,
                mvp_username, email, avatar_key, member_user_id,
                json.dumps(attributes, ensure_ascii=False) if attributes else None,
                notes, caregiver_id,
            ],
        )
        return member_id

    def list_household_members(self, user_id: str) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT {', '.join(self._MEMBER_COLS)} FROM household_members "
            "WHERE user_id = ? ORDER BY created_at",
            [user_id],
        ).fetchall()
        return [self._member_row(r) for r in rows]

    def get_household_member(self, member_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {', '.join(self._MEMBER_COLS)} FROM household_members WHERE id = ?",
            [member_id],
        ).fetchone()
        return self._member_row(row) if row else None

    def update_household_member(self, member_id: str, fields: Dict[str, Any]) -> None:
        """Patch a member. Unlike ``_cos_update`` an explicit None CLEARS the
        column — the caller passes only the keys the client actually sent
        (``exclude_unset``), so "set relation to null" is expressible."""
        sets: List[str] = []
        params: List[Any] = []
        for key, value in fields.items():
            if key not in self._MEMBER_PATCHABLE:
                continue
            sets.append(f"{key} = ?")
            if key == "attributes_json" and value is not None:
                params.append(json.dumps(value, ensure_ascii=False))
            else:
                params.append(value)
        if not sets:
            return
        sets.append("updated_at = now()")
        params.append(member_id)
        self._con.execute(
            f"UPDATE household_members SET {', '.join(sets)} WHERE id = ?", params
        )

    def delete_household_member(self, member_id: str) -> Dict[str, int]:
        """Remove a member and everything that references it (CLAUDE.md:
        deletes cascade). The mirrored caregivers row goes too, and any
        logistics assignment that pointed at that caregiver falls back to an
        unassigned 'tbd' row rather than dangling at a deleted id."""
        counts: Dict[str, int] = {"household_members": 0, "caregivers": 0,
                                  "logistics_assignments_unassigned": 0}
        with self._con.transaction():
            row = self._con.execute(
                "SELECT user_id, caregiver_id FROM household_members WHERE id = ?",
                [member_id],
            ).fetchone()
            if row is None:
                return counts
            owner, caregiver_id = row[0], row[1]
            if caregiver_id:
                counts["logistics_assignments_unassigned"] = self._con.execute(
                    "SELECT count(*) FROM logistics_assignments "
                    "WHERE user_id = ? AND caregiver_id = ?",
                    [owner, caregiver_id],
                ).fetchone()[0]
                self._con.execute(
                    "UPDATE logistics_assignments SET caregiver_id = NULL, "
                    "status = 'tbd', updated_at = now() "
                    "WHERE user_id = ? AND caregiver_id = ?",
                    [owner, caregiver_id],
                )
                counts["caregivers"] = self._con.execute(
                    "SELECT count(*) FROM caregivers WHERE id = ? AND user_id = ?",
                    [caregiver_id, owner],
                ).fetchone()[0]
                self._con.execute(
                    "DELETE FROM caregivers WHERE id = ? AND user_id = ?",
                    [caregiver_id, owner],
                )
            self._con.execute("DELETE FROM household_members WHERE id = ?", [member_id])
            counts["household_members"] = 1
        return counts

    def circle_peer_ids(self, user_id: str) -> List[str]:
        """Account ids inside this user's Circle — the authorization set for
        every Circle conversation.

        MUTUAL by construction: I must hold a member row pointing at you AND
        you must hold one pointing at me. A one-sided link is just an address
        book entry, so nobody can unlock a channel by unilaterally typing
        a stranger's user_id into their own roster."""
        rows = self._con.execute(
            """
            SELECT DISTINCT mine.member_user_id
            FROM household_members mine
            WHERE mine.user_id = ?
              AND mine.member_user_id IS NOT NULL
              AND mine.member_user_id <> ?
              AND EXISTS (
                  SELECT 1 FROM household_members theirs
                  WHERE theirs.user_id = mine.member_user_id
                    AND theirs.member_user_id = ?
              )
            """,
            [user_id, user_id, user_id],
        ).fetchall()
        return [r[0] for r in rows]

    def find_household_member_by_account(
        self, user_id: str, member_user_id: str
    ) -> Optional[Dict[str, Any]]:
        """The roster row `user_id` holds that points at the account
        `member_user_id`. Used when claiming an invite, to decide whether the
        reciprocal side already exists or has to be created."""
        row = self._con.execute(
            f"SELECT {', '.join(self._MEMBER_COLS)} FROM household_members "
            "WHERE user_id = ? AND member_user_id = ? ORDER BY created_at LIMIT 1",
            [user_id, member_user_id],
        ).fetchone()
        return self._member_row(row) if row else None

    # circle_conversations / circle_participants / circle_messages ----------
    # The group threads that replaced the anonymous board. Authorization lives
    # in app/circle.py (one guard, every route through it); this layer is
    # deliberately dumb about who may read what.

    _CIRCLE_CONV_COLS = (
        "id", "owner_user_id", "title", "body",
        "created_at", "updated_at", "last_reply_at",
    )
    _CIRCLE_PARTICIPANT_COLS = (
        "conversation_id", "user_id", "member_id", "role", "joined_at", "last_read_at",
    )
    _CIRCLE_MESSAGE_COLS = (
        "id", "conversation_id", "user_id", "author_name", "initials", "body", "created_at",
    )

    def _circle_conv_row(self, row: Any) -> Dict[str, Any]:
        return self._row_to_dict(
            self._CIRCLE_CONV_COLS, row,
            ts_cols=("created_at", "updated_at", "last_reply_at"),
        )

    def create_circle_conversation(
        self, owner_user_id: str, *, title: str, body: Optional[str] = None
    ) -> str:
        import uuid
        conv_id = f"cc-{uuid.uuid4().hex[:12]}"
        self._con.execute(
            "INSERT INTO circle_conversations (id, owner_user_id, title, body, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, now(), now())",
            [conv_id, owner_user_id, title, body],
        )
        return conv_id

    def get_circle_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {', '.join(self._CIRCLE_CONV_COLS)} FROM circle_conversations "
            "WHERE id = ?",
            [conversation_id],
        ).fetchone()
        return self._circle_conv_row(row) if row else None

    def update_circle_conversation(self, conversation_id: str, fields: Dict[str, Any]) -> None:
        allowed = {"title", "body"}
        sets, params = [], []
        for key, value in fields.items():
            if key in allowed:
                sets.append(f"{key} = ?")
                params.append(value)
        if not sets:
            return
        sets.append("updated_at = now()")
        params.append(conversation_id)
        self._con.execute(
            f"UPDATE circle_conversations SET {', '.join(sets)} WHERE id = ?", params
        )

    def delete_circle_conversation(self, conversation_id: str) -> Dict[str, int]:
        """Deletes cascade (CLAUDE.md): the thread takes its messages and its
        participant rows with it — an orphan participant row would leave the
        thread listed in someone's Circle forever."""
        counts = {"circle_messages": 0, "circle_participants": 0,
                  "circle_conversations": 0}
        with self._con.transaction():
            counts["circle_messages"] = self._con.execute(
                "SELECT count(*) FROM circle_messages WHERE conversation_id = ?",
                [conversation_id],
            ).fetchone()[0]
            counts["circle_participants"] = self._con.execute(
                "SELECT count(*) FROM circle_participants WHERE conversation_id = ?",
                [conversation_id],
            ).fetchone()[0]
            self._con.execute(
                "DELETE FROM circle_messages WHERE conversation_id = ?", [conversation_id]
            )
            self._con.execute(
                "DELETE FROM circle_participants WHERE conversation_id = ?",
                [conversation_id],
            )
            counts["circle_conversations"] = self._con.execute(
                "SELECT count(*) FROM circle_conversations WHERE id = ?",
                [conversation_id],
            ).fetchone()[0]
            self._con.execute(
                "DELETE FROM circle_conversations WHERE id = ?", [conversation_id]
            )
        return counts

    def list_circle_conversations_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Threads this ACCOUNT participates in. Rows whose user_id is still
        NULL (invited, not yet claimed) match nobody — that is the point."""
        rows = self._con.execute(
            f"SELECT {', '.join('c.' + c for c in self._CIRCLE_CONV_COLS)} "
            "FROM circle_conversations c "
            "WHERE EXISTS (SELECT 1 FROM circle_participants p "
            "              WHERE p.conversation_id = c.id AND p.user_id = ?) "
            "ORDER BY COALESCE(c.last_reply_at, c.created_at) DESC",
            [user_id],
        ).fetchall()
        return [self._circle_conv_row(r) for r in rows]

    def add_circle_participant(
        self, conversation_id: str, *, member_id: str,
        user_id: Optional[str] = None, role: str = "member",
    ) -> None:
        """Idempotent per (conversation, member) — re-adding someone updates
        their account binding instead of creating a duplicate row."""
        existing = self._con.execute(
            "SELECT 1 FROM circle_participants WHERE conversation_id = ? AND member_id = ?",
            [conversation_id, member_id],
        ).fetchone()
        if existing:
            if user_id is not None:
                self._con.execute(
                    "UPDATE circle_participants SET user_id = ? "
                    "WHERE conversation_id = ? AND member_id = ?",
                    [user_id, conversation_id, member_id],
                )
            return
        self._con.execute(
            "INSERT INTO circle_participants (conversation_id, user_id, member_id, "
            "role, joined_at) VALUES (?, ?, ?, ?, now())",
            [conversation_id, user_id, member_id, role],
        )

    def list_circle_participants(self, conversation_id: str) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT {', '.join(self._CIRCLE_PARTICIPANT_COLS)} FROM circle_participants "
            "WHERE conversation_id = ? ORDER BY joined_at",
            [conversation_id],
        ).fetchall()
        return [
            self._row_to_dict(self._CIRCLE_PARTICIPANT_COLS, r,
                              ts_cols=("joined_at", "last_read_at"))
            for r in rows
        ]

    def get_circle_participant(
        self, conversation_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """The authorization lookup. Matches on user_id ONLY — an unclaimed
        (user_id IS NULL) roster row grants nothing."""
        row = self._con.execute(
            f"SELECT {', '.join(self._CIRCLE_PARTICIPANT_COLS)} FROM circle_participants "
            "WHERE conversation_id = ? AND user_id = ? LIMIT 1",
            [conversation_id, user_id],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(self._CIRCLE_PARTICIPANT_COLS, row,
                                 ts_cols=("joined_at", "last_read_at"))

    def bind_circle_participant_account(self, member_id: str, user_id: str) -> int:
        """Fill in the account for every pending participant row of a member.
        Called when an invite is claimed: the threads they were added to before
        they had an account become readable at that moment, and not before."""
        pending = self._con.execute(
            "SELECT count(*) FROM circle_participants "
            "WHERE member_id = ? AND user_id IS NULL",
            [member_id],
        ).fetchone()[0]
        self._con.execute(
            "UPDATE circle_participants SET user_id = ? "
            "WHERE member_id = ? AND user_id IS NULL",
            [user_id, member_id],
        )
        return pending

    def add_circle_message(
        self, conversation_id: str, *, user_id: str, body: str,
        author_name: Optional[str] = None, initials: Optional[str] = None,
    ) -> Dict[str, Any]:
        import uuid
        message_id = f"cm-{uuid.uuid4().hex[:12]}"
        with self._con.transaction():
            self._con.execute(
                "INSERT INTO circle_messages (id, conversation_id, user_id, "
                "author_name, initials, body, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, now())",
                [message_id, conversation_id, user_id, author_name, initials, body],
            )
            self._con.execute(
                "UPDATE circle_conversations SET last_reply_at = now(), updated_at = now() "
                "WHERE id = ?",
                [conversation_id],
            )
        row = self._con.execute(
            f"SELECT {', '.join(self._CIRCLE_MESSAGE_COLS)} FROM circle_messages WHERE id = ?",
            [message_id],
        ).fetchone()
        return self._row_to_dict(self._CIRCLE_MESSAGE_COLS, row, ts_cols=("created_at",))

    def list_circle_messages(self, conversation_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT {', '.join(self._CIRCLE_MESSAGE_COLS)} FROM circle_messages "
            "WHERE conversation_id = ? ORDER BY created_at LIMIT ?",
            [conversation_id, limit],
        ).fetchall()
        return [
            self._row_to_dict(self._CIRCLE_MESSAGE_COLS, r, ts_cols=("created_at",))
            for r in rows
        ]

    def circle_message_stats(self, conversation_id: str) -> Dict[str, Any]:
        """reply_count + who replied last, for the conversation list row."""
        row = self._con.execute(
            "SELECT count(*) FROM circle_messages WHERE conversation_id = ?",
            [conversation_id],
        ).fetchone()
        last = self._con.execute(
            "SELECT author_name, user_id FROM circle_messages WHERE conversation_id = ? "
            "ORDER BY created_at DESC LIMIT 1",
            [conversation_id],
        ).fetchone()
        return {
            "reply_count": row[0] if row else 0,
            "last_reply_from": (last[0] if last else None),
            "last_reply_user_id": (last[1] if last else None),
        }

    def circle_unread_count(self, conversation_id: str, user_id: str) -> int:
        row = self._con.execute(
            "SELECT count(*) FROM circle_messages m "
            "WHERE m.conversation_id = ? AND m.user_id <> ? "
            "AND m.created_at > COALESCE("
            "  (SELECT p.last_read_at FROM circle_participants p "
            "   WHERE p.conversation_id = m.conversation_id AND p.user_id = ?), "
            "  TIMESTAMPTZ '1970-01-01 00:00:00+00')",
            [conversation_id, user_id, user_id],
        ).fetchone()
        return row[0] if row else 0

    def mark_circle_conversation_read(self, conversation_id: str, user_id: str) -> None:
        self._con.execute(
            "UPDATE circle_participants SET last_read_at = now() "
            "WHERE conversation_id = ? AND user_id = ?",
            [conversation_id, user_id],
        )

    # invite_tokens ---------------------------------------------------------

    _INVITE_COLS = (
        "token", "user_id", "member_id", "created_at", "expires_at",
        "claimed_by", "claimed_at",
    )

    def create_invite_token(
        self, user_id: str, *, member_id: Optional[str], token: str, ttl_days: int = 14,
    ) -> Dict[str, Any]:
        self._con.execute(
            "INSERT INTO invite_tokens (token, user_id, member_id, created_at, expires_at) "
            f"VALUES (?, ?, ?, now(), now() + INTERVAL {int(ttl_days)} DAY)",
            [token, user_id, member_id],
        )
        return self.get_invite_token(token)

    def get_invite_token(self, token: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {', '.join(self._INVITE_COLS)} FROM invite_tokens WHERE token = ?",
            [token],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(
            self._INVITE_COLS, row,
            ts_cols=("created_at", "expires_at", "claimed_at"),
        )

    def claim_invite_token(self, token: str, claimed_by: str) -> None:
        self._con.execute(
            "UPDATE invite_tokens SET claimed_by = ?, claimed_at = now() WHERE token = ?",
            [claimed_by, token],
        )

    # circle_requests -------------------------------------------------------
    # The email-match path: a request is a PENDING intent, never a link. Only
    # `accept_circle_request` in app/circle.py binds the mutual roster rows,
    # through the same helper claim_invite uses. This layer is deliberately
    # dumb about who may accept what.

    _REQUEST_COLS = (
        "id", "from_user_id", "to_user_id", "from_member_id", "status",
        "created_at", "responded_at",
    )

    def _request_row(self, row: Any) -> Dict[str, Any]:
        return self._row_to_dict(
            self._REQUEST_COLS, row, ts_cols=("created_at", "responded_at"),
        )

    def find_account_by_email(self, email: Optional[str]) -> Optional[str]:
        """Return the user_id of the SINGLE account whose auth identity email
        matches `email` (case-insensitive). None on zero OR many matches.

        `auth_identities.email` is nullable and neither lowercased nor unique
        (Apple private relay means absence is normal, and one person can hold
        an Apple AND a Google identity), so "exactly one DISTINCT user_id"
        is the only safe predicate — same idiom as
        `find_unclaimed_account_by_email`. An ambiguous match is treated as no
        match: never auto-link a family on a fuzzy hit."""
        if not email:
            return None
        needle = email.strip().lower()
        if not needle:
            return None
        rows = self._con.execute(
            "SELECT DISTINCT user_id FROM auth_identities "
            "WHERE lower(trim(email)) = ? AND email IS NOT NULL",
            [needle],
        ).fetchall()
        return rows[0][0] if len(rows) == 1 else None

    def create_circle_request(
        self, *, from_user_id: str, to_user_id: str,
        from_member_id: Optional[str] = None,
    ) -> str:
        import uuid
        request_id = f"cr-{uuid.uuid4().hex[:12]}"
        self._con.execute(
            "INSERT INTO circle_requests (id, from_user_id, to_user_id, "
            "from_member_id, status, created_at) VALUES (?, ?, ?, ?, 'pending', now())",
            [request_id, from_user_id, to_user_id, from_member_id],
        )
        return request_id

    def get_circle_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {', '.join(self._REQUEST_COLS)} FROM circle_requests WHERE id = ?",
            [request_id],
        ).fetchone()
        return self._request_row(row) if row else None

    def find_pending_circle_request(
        self, *, from_user_id: str, to_user_id: str
    ) -> Optional[Dict[str, Any]]:
        """The duplicate-pending guard's lookup. DuckDB has no partial unique
        index, so "one pending per ordered pair" is enforced in code (here plus
        the caller); this is the read half."""
        row = self._con.execute(
            f"SELECT {', '.join(self._REQUEST_COLS)} FROM circle_requests "
            "WHERE from_user_id = ? AND to_user_id = ? AND status = 'pending' "
            "ORDER BY created_at LIMIT 1",
            [from_user_id, to_user_id],
        ).fetchone()
        return self._request_row(row) if row else None

    def list_circle_requests_for_user(
        self, to_user_id: str, *, status: str = "pending"
    ) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT {', '.join(self._REQUEST_COLS)} FROM circle_requests "
            "WHERE to_user_id = ? AND status = ? ORDER BY created_at DESC",
            [to_user_id, status],
        ).fetchall()
        return [self._request_row(r) for r in rows]

    def pending_outbound_member_ids(self, from_user_id: str) -> List[str]:
        """Roster rows of MINE that are waiting on the other person — either a
        pending circle_request, or an unclaimed invite token. One query per
        request instead of a per-row lookup, so `GET /household/members` stays
        one round trip.

        This exists because the client would otherwise have to GUESS at pending
        (the first iOS pass inferred it from `email != nil`, which marks every
        hand-typed nanny as "waiting on them" forever, and the fallback was
        parsing the `notes` prose)."""
        rows = self._con.execute(
            "SELECT DISTINCT from_member_id FROM circle_requests "
            "WHERE from_user_id = ? AND status = 'pending' "
            "  AND from_member_id IS NOT NULL "
            "UNION "
            "SELECT DISTINCT member_id FROM invite_tokens "
            "WHERE user_id = ? AND claimed_by IS NULL AND member_id IS NOT NULL "
            "  AND (expires_at IS NULL OR expires_at > now())",
            [from_user_id, from_user_id],
        ).fetchall()
        return [r[0] for r in rows if r[0]]

    def set_circle_request_status(self, request_id: str, status: str) -> None:
        self._con.execute(
            "UPDATE circle_requests SET status = ?, responded_at = now() WHERE id = ?",
            [status, request_id],
        )

    # logistics_assignments -------------------------------------------------

    _LOGISTICS_COLS = (
        "id", "user_id", "week_start", "kid_name", "calendar_entry_id", "task",
        "caregiver_id", "status", "notes", "created_at", "updated_at",
    )

    def add_logistics_assignment(
        self,
        user_id: str,
        *,
        task: str,
        week_start: Optional[str] = None,
        kid_name: Optional[str] = None,
        calendar_entry_id: Optional[str] = None,
        caregiver_id: Optional[str] = None,
        status: str = "tbd",
        notes: Optional[str] = None,
    ) -> str:
        import uuid
        assignment_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO logistics_assignments (
                id, user_id, week_start, kid_name, calendar_entry_id, task,
                caregiver_id, status, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, now(), now())
            """,
            [
                assignment_id, user_id, week_start, kid_name, calendar_entry_id,
                task, caregiver_id, status, notes,
            ],
        )
        return assignment_id

    def list_logistics_assignments(
        self, user_id: str, *, week_start: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        where = "WHERE user_id = ?"
        params: List[Any] = [user_id]
        if week_start is not None:
            where += " AND week_start = ?"
            params.append(week_start)
        rows = self._con.execute(
            f"SELECT {', '.join(self._LOGISTICS_COLS)} FROM logistics_assignments "
            f"{where} ORDER BY created_at",
            params,
        ).fetchall()
        return [
            self._row_to_dict(
                self._LOGISTICS_COLS, r,
                ts_cols=("week_start", "created_at", "updated_at"),
            )
            for r in rows
        ]

    def update_logistics_assignment(self, assignment_id: str, **fields: Any) -> None:
        allowed = {"task", "caregiver_id", "status", "notes", "week_start", "kid_name"}
        patch = {k: v for k, v in fields.items() if k in allowed}
        self._cos_update("logistics_assignments", assignment_id, patch)

    # todo_items ------------------------------------------------------------

    _TODO_COLS = (
        "id", "user_id", "kid_name", "activity_id", "kind", "title", "detail",
        "due_date", "status", "source", "source_artifact_id", "created_at",
        "updated_at",
    )

    def add_todo(
        self,
        user_id: str,
        *,
        title: str,
        kid_name: Optional[str] = None,
        activity_id: Optional[str] = None,
        kind: str = "task",
        detail: Optional[str] = None,
        due_date: Optional[str] = None,
        status: str = "open",
        source: str = "manual",
        source_artifact_id: Optional[str] = None,
    ) -> str:
        import uuid
        todo_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO todo_items (
                id, user_id, kid_name, activity_id, kind, title, detail,
                due_date, status, source, source_artifact_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now(), now())
            """,
            [
                todo_id, user_id, kid_name, activity_id, kind, title, detail,
                due_date, status, source, source_artifact_id,
            ],
        )
        return todo_id

    def list_todos(
        self, user_id: str, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        where = "WHERE user_id = ?"
        params: List[Any] = [user_id]
        if status is not None:
            where += " AND status = ?"
            params.append(status)
        rows = self._con.execute(
            f"SELECT {', '.join(self._TODO_COLS)} FROM todo_items "
            f"{where} ORDER BY due_date NULLS LAST, created_at",
            params,
        ).fetchall()
        return [
            self._row_to_dict(
                self._TODO_COLS, r,
                ts_cols=("due_date", "created_at", "updated_at"),
            )
            for r in rows
        ]

    def update_todo(self, todo_id: str, **fields: Any) -> None:
        allowed = {"title", "detail", "due_date", "status", "kind"}
        patch = {k: v for k, v in fields.items() if k in allowed}
        self._cos_update("todo_items", todo_id, patch)

    # cos_messages ----------------------------------------------------------

    _COS_MESSAGE_COLS = (
        "id", "user_id", "thread_id", "role", "content", "created_at",
    )

    def append_cos_message(
        self,
        user_id: str,
        *,
        thread_id: str = "default",
        role: str,
        content: str,
    ) -> str:
        import uuid
        message_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO cos_messages (id, user_id, thread_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?, now())
            """,
            [message_id, user_id, thread_id, role, content],
        )
        return message_id

    def get_cos_messages(
        self, user_id: str, thread_id: str = "default", limit: int = 200
    ) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT {', '.join(self._COS_MESSAGE_COLS)} FROM cos_messages "
            "WHERE user_id = ? AND thread_id = ? ORDER BY created_at ASC LIMIT ?",
            [user_id, thread_id, limit],
        ).fetchall()
        return [
            self._row_to_dict(self._COS_MESSAGE_COLS, r, ts_cols=("created_at",))
            for r in rows
        ]

    # ingest_artifacts ------------------------------------------------------

    _INGEST_COLS = (
        "id", "user_id", "source", "media_type", "blob_ref", "subject",
        "sender", "received_at", "raw_text", "extracted_json", "extract_status",
        "links_json", "external_id", "created_at",
    )

    def insert_ingest_artifact(
        self,
        user_id: str,
        *,
        source: str,
        media_type: str = "text",
        blob_ref: Optional[str] = None,
        subject: Optional[str] = None,
        sender: Optional[str] = None,
        received_at: Optional[str] = None,
        raw_text: Optional[str] = None,
        extract_status: str = "pending",
        external_id: Optional[str] = None,
    ) -> str:
        import uuid
        artifact_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO ingest_artifacts (
                id, user_id, source, media_type, blob_ref, subject, sender,
                received_at, raw_text, extract_status, external_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now())
            """,
            [
                artifact_id, user_id, source, media_type, blob_ref, subject,
                sender, received_at, raw_text, extract_status, external_id,
            ],
        )
        return artifact_id

    def get_ingest_artifact_by_external(
        self, user_id: str, external_id: str
    ) -> Optional[str]:
        """Return the artifact id for a (user, provider-message-id) if already
        ingested — the R3 idempotency check. None if not seen."""
        row = self._con.execute(
            "SELECT id FROM ingest_artifacts WHERE user_id = ? AND external_id = ? LIMIT 1",
            [user_id, external_id],
        ).fetchone()
        return row[0] if row else None

    def update_ingest_extraction(
        self,
        artifact_id: str,
        *,
        extracted_json: Optional[Dict[str, Any]] = None,
        links_json: Optional[List[Any]] = None,
        extract_status: str,
    ) -> None:
        """Stage-2 write-back: store the structured extraction + status. Failed
        extractions land status='failed' with extracted_json=None."""
        self._con.execute(
            """
            UPDATE ingest_artifacts
               SET extracted_json = ?, links_json = ?, extract_status = ?
             WHERE id = ?
            """,
            [
                json.dumps(extracted_json, ensure_ascii=False) if extracted_json else None,
                json.dumps(links_json, ensure_ascii=False) if links_json else None,
                extract_status, artifact_id,
            ],
        )

    def get_ingest_artifact(
        self, artifact_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {', '.join(self._INGEST_COLS)} FROM ingest_artifacts "
            "WHERE id = ? AND user_id = ?",
            [artifact_id, user_id],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(
            self._INGEST_COLS, row,
            json_cols=(("extracted_json", "extracted"), ("links_json", "links")),
            ts_cols=("received_at", "created_at"),
        )

    def list_ingest_artifacts(
        self, user_id: str, *, status: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        where = "WHERE user_id = ?"
        params: List[Any] = [user_id]
        if status is not None:
            where += " AND extract_status = ?"
            params.append(status)
        params.append(limit)
        rows = self._con.execute(
            f"SELECT {', '.join(self._INGEST_COLS)} FROM ingest_artifacts "
            f"{where} ORDER BY created_at DESC LIMIT ?",
            params,
        ).fetchall()
        return [
            self._row_to_dict(
                self._INGEST_COLS, r,
                json_cols=(("extracted_json", "extracted"), ("links_json", "links")),
                ts_cols=("received_at", "created_at"),
            )
            for r in rows
        ]

    # integration_accounts (R5) -------------------------------------------

    _INTEGRATION_COLS = (
        "id", "user_id", "provider", "kind", "account_email", "scopes",
        "encrypted_refresh_token", "status", "connected_at", "last_sync_at",
        "revoked_at",
    )

    def upsert_integration_account(
        self,
        user_id: str,
        *,
        provider: str,
        kind: str,
        encrypted_refresh_token: str,
        account_email: Optional[str] = None,
        scopes: Optional[str] = None,
        status: str = "connected",
    ) -> str:
        """Connect (or reconnect) a provider account for a (user, provider, kind).
        Replaces any existing row for that triple so a re-auth refreshes the token
        in place. Returns the row id."""
        import uuid

        account_id = str(uuid.uuid4())
        with self._con.transaction():
            self._con.execute(
                "DELETE FROM integration_accounts "
                "WHERE user_id = ? AND provider = ? AND kind = ?",
                [user_id, provider, kind],
            )
            self._con.execute(
                """
                INSERT INTO integration_accounts (
                    id, user_id, provider, kind, account_email, scopes,
                    encrypted_refresh_token, status, connected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, now())
                """,
                [
                    account_id, user_id, provider, kind, account_email, scopes,
                    encrypted_refresh_token, status,
                ],
            )
        return account_id

    def get_integration_account(
        self, user_id: str, provider: str, kind: str
    ) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {', '.join(self._INTEGRATION_COLS)} FROM integration_accounts "
            "WHERE user_id = ? AND provider = ? AND kind = ?",
            [user_id, provider, kind],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(
            self._INTEGRATION_COLS, row,
            ts_cols=("connected_at", "last_sync_at", "revoked_at"),
        )

    def list_integration_accounts(
        self, user_id: str, *, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        where = "WHERE user_id = ?"
        params: List[Any] = [user_id]
        if status is not None:
            where += " AND status = ?"
            params.append(status)
        rows = self._con.execute(
            f"SELECT {', '.join(self._INTEGRATION_COLS)} FROM integration_accounts "
            f"{where} ORDER BY connected_at DESC",
            params,
        ).fetchall()
        return [
            self._row_to_dict(
                self._INTEGRATION_COLS, r,
                ts_cols=("connected_at", "last_sync_at", "revoked_at"),
            )
            for r in rows
        ]

    def mark_integration_synced(self, account_id: str) -> None:
        self._con.execute(
            "UPDATE integration_accounts SET last_sync_at = now() WHERE id = ?",
            [account_id],
        )

    def revoke_integration_account(self, user_id: str, provider: str, kind: str) -> None:
        """Mark an account revoked + scrub its token (the parent disconnected)."""
        self._con.execute(
            "UPDATE integration_accounts "
            "SET status = 'revoked', revoked_at = now(), encrypted_refresh_token = '' "
            "WHERE user_id = ? AND provider = ? AND kind = ?",
            [user_id, provider, kind],
        )

    def list_connected_email_accounts(self) -> List[Dict[str, Any]]:
        """All connected email accounts across ALL users — the R3 daemon iterates
        these to know whose Gmail to sync."""
        return self._list_connected_accounts("email")

    def list_connected_calendar_accounts(self) -> List[Dict[str, Any]]:
        """All connected calendar accounts across ALL users — the R4 calendar-sync
        daemon iterates these to know whose Google Calendar to reconcile."""
        return self._list_connected_accounts("calendar")

    def _list_connected_accounts(self, kind: str) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT {', '.join(self._INTEGRATION_COLS)} FROM integration_accounts "
            "WHERE kind = ? AND status = 'connected' ORDER BY connected_at",
            [kind],
        ).fetchall()
        return [
            self._row_to_dict(
                self._INTEGRATION_COLS, r,
                ts_cols=("connected_at", "last_sync_at", "revoked_at"),
            )
            for r in rows
        ]

    # agent_config (R3) --------------------------------------------------

    def get_agent_config(self, key: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            "SELECT value FROM agent_config WHERE key = ?", [key]
        ).fetchone()
        return json.loads(row[0]) if row and row[0] else None

    def set_agent_config(self, key: str, value: Dict[str, Any]) -> None:
        """UPSERT a config blob (delete + insert — DuckDB ON CONFLICT on a PK is
        finicky, and this matches the integration upsert style)."""
        payload = json.dumps(value, ensure_ascii=False)
        with self._con.transaction():
            self._con.execute("DELETE FROM agent_config WHERE key = ?", [key])
            self._con.execute(
                "INSERT INTO agent_config (key, value, updated_at) VALUES (?, ?, now())",
                [key, payload],
            )

    # email_sync_runs (R3) -----------------------------------------------

    def create_email_sync_run(self, *, user_id: str, trigger: str = "manual") -> str:
        import uuid
        run_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO email_sync_runs (id, user_id, status, trigger, progress_json, created_at)
            VALUES (?, ?, 'queued', ?, ?, now())
            """,
            [run_id, user_id, trigger, json.dumps({"phase": "queued"})],
        )
        return run_id

    def claim_next_queued_email_sync_run(self) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            """
            UPDATE email_sync_runs
               SET status = 'running', started_at = now(),
                   progress_json = json_object('phase', 'starting')
             WHERE id = (
                 SELECT id FROM email_sync_runs WHERE status = 'queued'
                 ORDER BY created_at LIMIT 1
             )
            RETURNING id
            """,
        ).fetchone()
        return self.get_email_sync_run(row[0]) if row else None

    def update_email_sync_run(
        self,
        run_id: str,
        *,
        status: Optional[str] = None,
        progress: Optional[Dict[str, Any]] = None,
        messages_seen: Optional[int] = None,
        activities_touched: Optional[int] = None,
        error: Optional[str] = None,
        finished: bool = False,
    ) -> None:
        sets: List[str] = []
        params: List[Any] = []
        if status is not None:
            sets.append("status = ?"); params.append(status)
        if progress is not None:
            sets.append("progress_json = ?"); params.append(json.dumps(progress, ensure_ascii=False))
        if messages_seen is not None:
            sets.append("messages_seen = ?"); params.append(messages_seen)
        if activities_touched is not None:
            sets.append("activities_touched = ?"); params.append(activities_touched)
        if error is not None:
            sets.append("error = ?"); params.append(error)
        if finished:
            sets.append("finished_at = now()")
        if not sets:
            return
        params.append(run_id)
        self._con.execute(
            f"UPDATE email_sync_runs SET {', '.join(sets)} WHERE id = ?", params
        )

    def requeue_stale_email_sync_runs(self) -> int:
        rows = self._con.execute(
            "UPDATE email_sync_runs SET status = 'queued', started_at = NULL "
            "WHERE status = 'running' RETURNING id",
        ).fetchall()
        if rows:
            logger.warning("[email-sync] re-queued %d stale run(s) after restart", len(rows))
        return len(rows)

    _EMAIL_SYNC_COLS = (
        "id", "user_id", "status", "trigger", "messages_seen", "activities_touched",
        "progress_json", "error", "created_at", "started_at", "finished_at",
    )

    def get_email_sync_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {', '.join(self._EMAIL_SYNC_COLS)} FROM email_sync_runs WHERE id = ?",
            [run_id],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(
            self._EMAIL_SYNC_COLS, row,
            json_cols=(("progress_json", "progress"),),
            ts_cols=("created_at", "started_at", "finished_at"),
        )

    def list_email_sync_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT {', '.join(self._EMAIL_SYNC_COLS)} FROM email_sync_runs "
            "ORDER BY created_at DESC LIMIT ?",
            [limit],
        ).fetchall()
        return [
            self._row_to_dict(
                self._EMAIL_SYNC_COLS, r,
                json_cols=(("progress_json", "progress"),),
                ts_cols=("created_at", "started_at", "finished_at"),
            )
            for r in rows
        ]

    # calendar_sync_runs (R4 part 2) -------------------------------------
    # Mirrors email_sync_runs but counts entries reconciled per direction
    # (pushed / pulled) instead of messages_seen / activities_touched.

    _CALENDAR_SYNC_COLS = (
        "id", "user_id", "status", "trigger", "pushed", "pulled",
        "progress_json", "error", "created_at", "started_at", "finished_at",
    )

    def create_calendar_sync_run(self, *, user_id: str, trigger: str = "manual") -> str:
        import uuid
        run_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO calendar_sync_runs (id, user_id, status, trigger, progress_json, created_at)
            VALUES (?, ?, 'queued', ?, ?, now())
            """,
            [run_id, user_id, trigger, json.dumps({"phase": "queued"})],
        )
        return run_id

    def claim_next_queued_calendar_sync_run(self) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            """
            UPDATE calendar_sync_runs
               SET status = 'running', started_at = now(),
                   progress_json = json_object('phase', 'starting')
             WHERE id = (
                 SELECT id FROM calendar_sync_runs WHERE status = 'queued'
                 ORDER BY created_at LIMIT 1
             )
            RETURNING id
            """,
        ).fetchone()
        return self.get_calendar_sync_run(row[0]) if row else None

    def update_calendar_sync_run(
        self,
        run_id: str,
        *,
        status: Optional[str] = None,
        progress: Optional[Dict[str, Any]] = None,
        pushed: Optional[int] = None,
        pulled: Optional[int] = None,
        error: Optional[str] = None,
        finished: bool = False,
    ) -> None:
        sets: List[str] = []
        params: List[Any] = []
        if status is not None:
            sets.append("status = ?"); params.append(status)
        if progress is not None:
            sets.append("progress_json = ?"); params.append(json.dumps(progress, ensure_ascii=False))
        if pushed is not None:
            sets.append("pushed = ?"); params.append(pushed)
        if pulled is not None:
            sets.append("pulled = ?"); params.append(pulled)
        if error is not None:
            sets.append("error = ?"); params.append(error)
        if finished:
            sets.append("finished_at = now()")
        if not sets:
            return
        params.append(run_id)
        self._con.execute(
            f"UPDATE calendar_sync_runs SET {', '.join(sets)} WHERE id = ?", params
        )

    def requeue_stale_calendar_sync_runs(self) -> int:
        rows = self._con.execute(
            "UPDATE calendar_sync_runs SET status = 'queued', started_at = NULL "
            "WHERE status = 'running' RETURNING id",
        ).fetchall()
        if rows:
            logger.warning("[calendar-sync] re-queued %d stale run(s) after restart", len(rows))
        return len(rows)

    def get_calendar_sync_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            f"SELECT {', '.join(self._CALENDAR_SYNC_COLS)} FROM calendar_sync_runs WHERE id = ?",
            [run_id],
        ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(
            self._CALENDAR_SYNC_COLS, row,
            json_cols=(("progress_json", "progress"),),
            ts_cols=("created_at", "started_at", "finished_at"),
        )

    def list_calendar_sync_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            f"SELECT {', '.join(self._CALENDAR_SYNC_COLS)} FROM calendar_sync_runs "
            "ORDER BY created_at DESC LIMIT ?",
            [limit],
        ).fetchall()
        return [
            self._row_to_dict(
                self._CALENDAR_SYNC_COLS, r,
                json_cols=(("progress_json", "progress"),),
                ts_cols=("created_at", "started_at", "finished_at"),
            )
            for r in rows
        ]

    def export_all_parquet(self, *, strict: bool = False) -> None:
        """
        Export every table in BOOTSTRAP_TABLES atomically (A2). This is the
        full backup path — kid/consent/audit/auth tables included, so a volume
        rebuild can recover them. user_data uses its conventional mvp.parquet
        name. Failures on individual tables are logged but don't abort the rest.
        strict=True raises after attempting every table if any export failed.
        """
        failures = []
        for table, pq_name in self.BOOTSTRAP_TABLES:
            target = self.parquet_dir / pq_name
            try:
                self._export_table_atomic(table, target)
            except Exception as exc:
                logger.error(f"[duckdb] export of {table} → {pq_name} failed: {exc}")
                failures.append(table)
        if strict and failures:
            raise OSError("Snapshot export failed for: " + ", ".join(failures))

    def ping(self) -> bool:
        """Cheap liveness probe for the health check (A6): confirms the DB is
        open and answering. Raises/returns False if the connection is dead."""
        try:
            row = self._con.execute("SELECT 1").fetchone()
            return bool(row and row[0] == 1)
        except Exception:
            return False

    def close(self) -> None:
        """Export every table to parquet and close the connection."""
        try:
            self.export_all_parquet()
        except Exception as exc:
            logger.error(f"[duckdb] parquet export on close failed: {exc}")
        self._con.close()
        logger.info("[duckdb] connection closed")
