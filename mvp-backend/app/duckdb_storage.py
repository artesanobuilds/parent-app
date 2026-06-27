"""
DuckDB + Parquet storage backend.

Stores user data as JSON blobs in a DuckDB database backed by parquet files.
Also stores content library tables (categories, articles, community_posts).
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
            self._con.execute("BEGIN TRANSACTION")
            try:
                yield self
                self._con.execute("COMMIT")
            except Exception:
                self._con.execute("ROLLBACK")
                raise

    def close(self) -> None:
        with self._lock:
            self._con.close()

from app.storage import StorageBackend

logger = logging.getLogger(__name__)


class DuckDBStorage(StorageBackend):
    """
    DuckDB-backed implementation of StorageBackend.

    Tables:
        user_data(user_id, name, data, updated_at)
        categories(id, name, emoji, description)
        articles(id, category, title, subtitle, emoji, author, read_time, summary, tags, content, created_at, updated_at)
        community_posts(id, category, initials, name, title, preview, user_id, created_at, updated_at)
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
        created_at  TIMESTAMPTZ DEFAULT now(),
        updated_at  TIMESTAMPTZ DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS community_posts (
        id          TEXT PRIMARY KEY,
        category    TEXT NOT NULL,
        initials    TEXT NOT NULL DEFAULT '',
        name        TEXT NOT NULL DEFAULT '',
        title       TEXT NOT NULL DEFAULT '',
        preview     TEXT NOT NULL DEFAULT '',
        user_id     TEXT,
        created_at  TIMESTAMPTZ DEFAULT now(),
        updated_at  TIMESTAMPTZ DEFAULT now()
    );

    CREATE TABLE IF NOT EXISTS post_replies (
        id          TEXT PRIMARY KEY,
        post_id     TEXT NOT NULL,
        user_id     TEXT NOT NULL,
        author_name TEXT NOT NULL DEFAULT '',
        initials    TEXT NOT NULL DEFAULT '',
        body        TEXT NOT NULL DEFAULT '',
        created_at  TIMESTAMPTZ DEFAULT now()
    );
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
        week_start        DATE,
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
    """

    # Every table that must survive a volume rebuild, mapped to its parquet
    # snapshot filename. Used for both export (A2/A3) and bootstrap-merge (A2).
    # auth_tokens is safe to export — only sha256 hashes are stored at rest.
    BOOTSTRAP_TABLES = [
        ("user_data", "mvp.parquet"),
        ("categories", "categories.parquet"),
        ("articles", "articles.parquet"),
        ("community_posts", "community_posts.parquet"),
        ("post_replies", "post_replies.parquet"),
        ("kid_agent_configs", "kid_agent_configs.parquet"),
        ("kid_messages", "kid_messages.parquet"),
        ("kid_credentials", "kid_credentials.parquet"),
        ("moderation_events", "moderation_events.parquet"),
        ("kid_agent_crisis_locks", "kid_agent_crisis_locks.parquet"),
        ("consent_records", "consent_records.parquet"),
        ("daily_summaries", "daily_summaries.parquet"),
        ("audit_events", "audit_events.parquet"),
        ("auth_tokens", "auth_tokens.parquet"),
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

        logger.info(f"[duckdb] opened {self.db_path}")

    # ── StorageBackend interface ──────────────────────────────────────

    def save_user_data(self, user_id: str, name: str, data: Dict[str, Any]) -> None:
        try:
            payload = json.dumps(data, ensure_ascii=False)
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
            "SELECT id, category, title, subtitle, emoji, author, read_time, summary, tags "
            f"FROM articles {where}ORDER BY id LIMIT ?",
            params,
        ).fetchall()
        return [
            {"id": r[0], "category": r[1], "title": r[2], "subtitle": r[3],
             "emoji": r[4], "author": r[5], "read_time": r[6], "summary": r[7],
             "tags": list(r[8]) if r[8] else []}
            for r in rows
        ]

    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            "SELECT id, category, title, subtitle, emoji, author, read_time, summary, tags, content "
            "FROM articles WHERE id = ?",
            [article_id],
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0], "category": row[1], "title": row[2], "subtitle": row[3],
            "emoji": row[4], "author": row[5], "read_time": row[6], "summary": row[7],
            "tags": list(row[8]) if row[8] else [], "content": row[9],
        }

    def get_community_posts(self, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        if category:
            rows = self._con.execute(
                "SELECT id, category, initials, name, title, preview "
                "FROM community_posts WHERE category = ? ORDER BY id LIMIT ?",
                [category, limit],
            ).fetchall()
            posts = [
                {"id": r[0], "category": r[1], "initials": r[2], "name": r[3],
                 "title": r[4], "preview": r[5]}
                for r in rows
            ]
        else:
            rows = self._con.execute(
                "SELECT id, category, initials, name, title, preview "
                "FROM community_posts ORDER BY id LIMIT ?",
                [limit],
            ).fetchall()
            posts = [
                {"id": r[0], "category": r[1], "initials": r[2], "name": r[3],
                 "title": r[4], "preview": r[5]}
                for r in rows
            ]
        # Add reply counts
        post_ids = [p["id"] for p in posts]
        if post_ids:
            counts = self.get_reply_counts(post_ids)
            for p in posts:
                p["reply_count"] = counts.get(p["id"], 0)
        return posts

    def search_articles(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            "SELECT id, category, title, subtitle, emoji, author, read_time, summary, tags "
            "FROM articles "
            "WHERE title ILIKE ? OR subtitle ILIKE ? OR summary ILIKE ? OR array_to_string(tags, ' ') ILIKE ? "
            "ORDER BY id LIMIT ?",
            [f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit],
        ).fetchall()
        return [
            {"id": r[0], "category": r[1], "title": r[2], "subtitle": r[3],
             "emoji": r[4], "author": r[5], "read_time": r[6], "summary": r[7],
             "tags": list(r[8]) if r[8] else []}
            for r in rows
        ]

    def search_community_posts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            "SELECT id, category, initials, name, title, preview "
            "FROM community_posts "
            "WHERE title ILIKE ? OR preview ILIKE ? "
            "ORDER BY id LIMIT ?",
            [f"%{query}%", f"%{query}%", limit],
        ).fetchall()
        return [
            {"id": r[0], "category": r[1], "initials": r[2], "name": r[3],
             "title": r[4], "preview": r[5]}
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
        sql = (
            f"SELECT id, category, title, subtitle, emoji, author, read_time, summary, tags, "
            f"({cases}) AS score "
            f"FROM articles HAVING score > 0 ORDER BY score DESC LIMIT ?"
        )
        rows = self._con.execute(sql, words + [limit]).fetchall()
        return [
            {"id": r[0], "category": r[1], "title": r[2], "subtitle": r[3],
             "emoji": r[4], "author": r[5], "read_time": r[6], "summary": r[7],
             "tags": list(r[8]) if r[8] else []}
            for r in rows
        ]

    def score_posts_by_words(self, words: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """Score community posts by counting how many topic words match title/preview."""
        cases = " + ".join(
            f"(CASE WHEN title ILIKE '%' || ${i+1} || '%' OR preview ILIKE '%' || ${i+1} || '%' "
            f"THEN 1 ELSE 0 END)"
            for i in range(len(words))
        )
        sql = (
            f"SELECT id, category, initials, name, title, preview, "
            f"({cases}) AS score "
            f"FROM community_posts HAVING score > 0 ORDER BY score DESC LIMIT ?"
        )
        rows = self._con.execute(sql, words + [limit]).fetchall()
        return [
            {"id": r[0], "category": r[1], "initials": r[2], "name": r[3],
             "title": r[4], "preview": r[5]}
            for r in rows
        ]

    # ── Content CRUD methods ─────────────────────────────────────────

    def create_article(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._con.execute(
            "INSERT INTO articles (id, category, title, subtitle, emoji, author, read_time, summary, tags, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now(), now())",
            [data["id"], data["category"], data["title"], data.get("subtitle", ""),
             data.get("emoji", ""), data.get("author", "MVP Editorial"),
             data.get("read_time", ""), data.get("summary", ""),
             data.get("tags", []), data.get("content", "")],
        )
        return self.get_article(data["id"])

    def update_article(self, article_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.get_article(article_id)
        if existing is None:
            return None
        fields = []
        values = []
        for key in ("category", "title", "subtitle", "emoji", "author", "read_time", "summary", "tags", "content"):
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

    def get_community_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        row = self._con.execute(
            "SELECT id, category, initials, name, title, preview, user_id "
            "FROM community_posts WHERE id = ?",
            [post_id],
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0], "category": row[1], "initials": row[2], "name": row[3],
            "title": row[4], "preview": row[5], "user_id": row[6],
        }

    def create_community_post(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._con.execute(
            "INSERT INTO community_posts (id, category, initials, name, title, preview, user_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, now(), now())",
            [data["id"], data["category"], data.get("initials", ""),
             data.get("name", ""), data.get("title", ""),
             data.get("preview", ""), data.get("user_id")],
        )
        return self.get_community_post(data["id"])

    def update_community_post(self, post_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        existing = self.get_community_post(post_id)
        if existing is None:
            return None
        fields = []
        values = []
        for key in ("category", "initials", "name", "title", "preview", "user_id"):
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        if not fields:
            return existing
        fields.append("updated_at = now()")
        values.append(post_id)
        self._con.execute(
            f"UPDATE community_posts SET {', '.join(fields)} WHERE id = ?", values
        )
        return self.get_community_post(post_id)

    def delete_community_post(self, post_id: str) -> bool:
        existing = self.get_community_post(post_id)
        if existing is None:
            return False
        self._con.execute("DELETE FROM community_posts WHERE id = ?", [post_id])
        return True

    def get_replies_for_post(self, post_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        rows = self._con.execute(
            "SELECT id, post_id, user_id, author_name, initials, body "
            "FROM post_replies WHERE post_id = ? ORDER BY created_at ASC LIMIT ?",
            [post_id, limit],
        ).fetchall()
        return [
            {"id": r[0], "post_id": r[1], "user_id": r[2], "author_name": r[3],
             "initials": r[4], "body": r[5]}
            for r in rows
        ]

    def create_reply(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._con.execute(
            "INSERT INTO post_replies (id, post_id, user_id, author_name, initials, body, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, now())",
            [data["id"], data["post_id"], data["user_id"], data.get("author_name", ""),
             data.get("initials", ""), data.get("body", "")],
        )
        return {"id": data["id"], "post_id": data["post_id"], "user_id": data["user_id"],
                "author_name": data.get("author_name", ""), "initials": data.get("initials", ""),
                "body": data.get("body", "")}

    def get_reply_counts(self, post_ids: List[str]) -> Dict[str, int]:
        if not post_ids:
            return {}
        placeholders = ", ".join(["?"] * len(post_ids))
        rows = self._con.execute(
            f"SELECT post_id, count(*) FROM post_replies WHERE post_id IN ({placeholders}) GROUP BY post_id",
            post_ids,
        ).fetchall()
        return {r[0]: r[1] for r in rows}

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
        posts_count = self._con.execute("SELECT count(*) FROM community_posts").fetchone()[0]
        categories_count = self._con.execute("SELECT count(*) FROM categories").fetchone()[0]
        articles_by_cat = self._con.execute(
            "SELECT category, count(*) FROM articles GROUP BY category ORDER BY category"
        ).fetchall()
        posts_by_cat = self._con.execute(
            "SELECT category, count(*) FROM community_posts GROUP BY category ORDER BY category"
        ).fetchall()
        return {
            "articles": articles_count,
            "community_posts": posts_count,
            "categories": categories_count,
            "articles_by_category": {r[0]: r[1] for r in articles_by_cat},
            "posts_by_category": {r[0]: r[1] for r in posts_by_cat},
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

        Tables left intact: content (categories/articles/community_posts/
        post_replies) and audit_events itself.
        """
        deleted: Dict[str, int] = {}

        # Wrap the whole cascade in one transaction (A5) so a kill mid-delete
        # can't leave a half-deleted family (e.g. user_data gone but consent +
        # auth_tokens still present). The proxy holds the connection lock for
        # the duration, so no other thread joins this transaction.
        with self._con.transaction():
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

            for table in [
                "kid_agent_crisis_locks",
                "kid_agent_configs",
                "kid_credentials",
                "moderation_events",
                "auth_tokens",
                "daily_summaries",
                "consent_records",
                "user_data",
                # Activity-planning / chief-of-staff tables — all keyed by
                # user_id. Account deletion must wipe these too (privacy), and
                # this lets a test-user purge fully clean up research runs etc.
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
            ]:
                pre = self._con.execute(
                    f"SELECT count(*) FROM {table} WHERE user_id = ?",
                    [user_id],
                ).fetchone()[0]
                self._con.execute(
                    f"DELETE FROM {table} WHERE user_id = ?", [user_id],
                )
                deleted[table] = pre

            self.write_audit_event(
                user_id=user_id, actor=actor,
                action="family_deleted", details={"counts": deleted},
            )
        return {"counts": deleted, "agent_ids": agent_ids}

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
        for table in ("categories", "articles", "community_posts", "post_replies"):
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
            active = self.get_active_research_run(user_id)
            if active is not None:
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
            "price_text", "price_amount", "location_text", "signup_url",
            "source_url", "contact_json", "fit_score", "raw_json",
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
                        c.get("signup_url"), c.get("source_url"),
                        json.dumps(c.get("contact") or {}, ensure_ascii=False) if c.get("contact") else None,
                        c.get("fit_score"),
                        json.dumps(c.get("raw") or c, ensure_ascii=False),
                    ],
                )
        return len(candidates)

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
                   price_text, price_amount, location_text, signup_url,
                   source_url, contact_json, fit_score, raw_json, created_at
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
                "location_text": r[14], "signup_url": r[15], "source_url": r[16],
                "contact": json.loads(r[17]) if r[17] else None,
                "fit_score": r[18],
                "raw": json.loads(r[19]) if r[19] else None,
                "created_at": r[20].isoformat() if r[20] else None,
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
        "week_start", "status", "pending_reason", "price_amount", "price_status",
        "signup_url", "contact_json", "carpool_with", "details_json", "notes",
        "decision_rationale", "created_at", "updated_at",
    )

    def track_activity(
        self,
        user_id: str,
        *,
        name: str,
        kid_name: Optional[str] = None,
        candidate_id: Optional[str] = None,
        provider: Optional[str] = None,
        week_start: Optional[str] = None,
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
    ) -> str:
        import uuid
        activity_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO tracked_activities (
                id, user_id, kid_name, candidate_id, name, provider, week_start,
                status, pending_reason, price_amount, price_status, signup_url,
                contact_json, carpool_with, details_json, notes, decision_rationale,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now(), now())
            """,
            [
                activity_id, user_id, kid_name, candidate_id, name, provider,
                week_start, status, pending_reason, price_amount, price_status,
                signup_url,
                json.dumps(contact, ensure_ascii=False) if contact else None,
                carpool_with,
                json.dumps(details, ensure_ascii=False) if details else None,
                notes, decision_rationale,
            ],
        )
        return activity_id

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
            ts_cols=("week_start", "created_at", "updated_at"),
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
                ts_cols=("week_start", "created_at", "updated_at"),
            )
            for r in rows
        ]

    def update_tracked_activity(self, activity_id: str, **fields: Any) -> None:
        allowed = {
            "status", "pending_reason", "price_amount", "price_status",
            "signup_url", "week_start", "notes", "decision_rationale",
            "carpool_with", "contact", "details",
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
        "active_to", "created_at",
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
    ) -> str:
        import uuid
        appt_id = str(uuid.uuid4())
        self._con.execute(
            """
            INSERT INTO recurring_appointments (
                id, user_id, kid_name, title, provider_name, weekday,
                start_time, end_time, transporter, notes, active_from, active_to,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, now())
            """,
            [
                appt_id, user_id, kid_name, title, provider_name, weekday,
                start_time, end_time, transporter, notes, active_from, active_to,
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

    def export_all_parquet(self) -> None:
        """
        Export every table in BOOTSTRAP_TABLES atomically (A2). This is the
        full backup path — kid/consent/audit/auth tables included, so a volume
        rebuild can recover them. user_data uses its conventional mvp.parquet
        name. Failures on individual tables are logged but don't abort the rest.
        """
        for table, pq_name in self.BOOTSTRAP_TABLES:
            target = self.parquet_dir / pq_name
            try:
                self._export_table_atomic(table, target)
            except Exception as exc:
                logger.error(f"[duckdb] export of {table} → {pq_name} failed: {exc}")

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
