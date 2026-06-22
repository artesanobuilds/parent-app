"""
Daily email-sync worker (R3).

Mirrors `app/research/worker.py`: a single daemon thread that drains queued
`email_sync_runs` (claim → run_email_sync → mark done/failed). On top of the
queue-drain it adds a **schedule tick**: once per day at the operator-configured
hour (`agent_config["email_sync_schedule"]`) it enqueues one run per connected
Gmail account. Manual runs (CMS "Run now") are just queued rows + `notify()`.

The sync function is injected (default `app.email_sync.sync.run_email_sync`) so
the worker is unit-testable with a fake that does no network/LLM calls.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

SyncFn = Callable[..., Dict[str, int]]

SCHEDULE_KEY = "email_sync_schedule"
GUARD_KEY = "email_sync_last_scheduled"
_DEFAULT_TZ = "America/Los_Angeles"


def _now_in(tz: str) -> datetime:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo(tz))
    except Exception:  # noqa: BLE001 — bad tz name / missing tzdata → UTC
        from datetime import timezone

        return datetime.now(timezone.utc)


class EmailSyncWorker:
    def __init__(self, storage: Any, sync_fn: SyncFn, poll_interval: float = 120.0) -> None:
        self._storage = storage
        self._sync = sync_fn
        self._poll = poll_interval
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ── lifecycle ────────────────────────────────────────────────────
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="email-sync-worker", daemon=True)
        self._thread.start()
        logger.info("[email-sync] worker started")

    def notify(self) -> None:
        self._wake.set()

    def stop(self, timeout: float = 3.0) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread:
            self._thread.join(timeout)
        logger.info("[email-sync] worker stopped")

    # ── loop ─────────────────────────────────────────────────────────
    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.maybe_schedule()
            except Exception:
                logger.exception("[email-sync] schedule tick failed")
            did_work = self._drain()
            if not did_work:
                self._wake.wait(self._poll)
                self._wake.clear()

    def maybe_schedule(self, now: Optional[datetime] = None) -> int:
        """Enqueue one scheduled run per connected account if it's the configured
        hour and we haven't already scheduled today. Returns how many enqueued.
        `now` is injectable for tests."""
        cfg = self._storage.get_agent_config(SCHEDULE_KEY) or {}
        if not cfg.get("enabled"):
            return 0
        tz = cfg.get("tz") or _DEFAULT_TZ
        now = now or _now_in(tz)
        try:
            target_hour = int(cfg.get("hour", 6))
        except (TypeError, ValueError):
            return 0
        if now.hour != target_hour:
            return 0
        today = now.strftime("%Y-%m-%d")
        guard = self._storage.get_agent_config(GUARD_KEY) or {}
        if guard.get("date") == today:
            return 0  # already scheduled today

        accounts = self._storage.list_connected_email_accounts()
        for acct in accounts:
            self._storage.create_email_sync_run(user_id=acct["user_id"], trigger="scheduled")
        self._storage.set_agent_config(GUARD_KEY, {"date": today})
        if accounts:
            logger.info("[email-sync] scheduled %d run(s) for %s", len(accounts), today)
            self.notify()
        return len(accounts)

    def _drain(self) -> bool:
        worked = False
        while not self._stop.is_set():
            try:
                run = self._storage.claim_next_queued_email_sync_run()
            except Exception:
                logger.exception("[email-sync] claim failed")
                break
            if not run:
                break
            worked = True
            self.process_run(run)
        return worked

    # ── one run ──────────────────────────────────────────────────────
    def process_run(self, run: Dict[str, Any]) -> None:
        run_id = run["id"]
        user_id = run["user_id"]
        try:
            self._storage.update_email_sync_run(run_id, progress={"phase": "syncing"})
            result = self._sync(
                self._storage, user_id,
                on_progress=lambda n: self._storage.update_email_sync_run(
                    run_id, progress={"phase": "syncing", "messages_seen": n}
                ),
            )
            self._storage.update_email_sync_run(
                run_id,
                status="done",
                messages_seen=result.get("messages_seen", 0),
                activities_touched=result.get("activities_touched", 0),
                progress={"phase": "done", **result},
                finished=True,
            )
            logger.info("[email-sync] run %s done %s", run_id, result)
        except Exception as exc:  # noqa: BLE001
            logger.exception("[email-sync] run %s failed", run_id)
            self._storage.update_email_sync_run(
                run_id, status="failed", error=str(exc)[:1000],
                progress={"phase": "failed"}, finished=True,
            )


# ── module singleton, wired by the server lifespan ───────────────────
email_sync_worker: Optional[EmailSyncWorker] = None


def init_worker(storage: Any, sync_fn: Optional[SyncFn] = None) -> EmailSyncWorker:
    global email_sync_worker
    if sync_fn is None:
        from app.email_sync.sync import run_email_sync

        sync_fn = run_email_sync
    email_sync_worker = EmailSyncWorker(storage, sync_fn)
    return email_sync_worker
