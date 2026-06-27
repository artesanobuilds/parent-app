"""
Daily two-way calendar-sync worker (R4 part 2).

Mirrors `app/email_sync/worker.py`: a single daemon thread that drains queued
`calendar_sync_runs` (claim → run_calendar_sync → mark done/failed), plus a
**schedule tick** that once per day at the operator-configured hour
(`agent_config["calendar_sync_schedule"]`) enqueues one run per connected Google
Calendar account. Manual runs (CMS "Run now" or the iOS "Sync now" button) are
just queued rows + `notify()`.

The sync function is injected (default `app.calendar_sync.sync.run_calendar_sync`)
so the worker is unit-testable with a fake that does no network calls.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

SyncFn = Callable[..., Dict[str, int]]

SCHEDULE_KEY = "calendar_sync_schedule"
GUARD_KEY = "calendar_sync_last_scheduled"
_DEFAULT_TZ = "America/Los_Angeles"


def _now_in(tz: str) -> datetime:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo(tz))
    except Exception:  # noqa: BLE001 — bad tz name / missing tzdata → UTC
        from datetime import timezone

        return datetime.now(timezone.utc)


class CalendarSyncWorker:
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
        self._thread = threading.Thread(target=self._loop, name="calendar-sync-worker", daemon=True)
        self._thread.start()
        logger.info("[calendar-sync] worker started")

    def notify(self) -> None:
        self._wake.set()

    def stop(self, timeout: float = 3.0) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread:
            self._thread.join(timeout)
        logger.info("[calendar-sync] worker stopped")

    # ── loop ─────────────────────────────────────────────────────────
    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.maybe_schedule()
            except Exception:
                logger.exception("[calendar-sync] schedule tick failed")
            did_work = self._drain()
            if not did_work:
                self._wake.wait(self._poll)
                self._wake.clear()

    def maybe_schedule(self, now: Optional[datetime] = None) -> int:
        """Enqueue one scheduled run per connected calendar account if it's the
        configured hour and we haven't already scheduled today. Returns how many
        enqueued. `now` is injectable for tests."""
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

        accounts = self._storage.list_connected_calendar_accounts()
        for acct in accounts:
            self._storage.create_calendar_sync_run(user_id=acct["user_id"], trigger="scheduled")
        self._storage.set_agent_config(GUARD_KEY, {"date": today})
        if accounts:
            logger.info("[calendar-sync] scheduled %d run(s) for %s", len(accounts), today)
            self.notify()
        return len(accounts)

    def _drain(self) -> bool:
        worked = False
        while not self._stop.is_set():
            try:
                run = self._storage.claim_next_queued_calendar_sync_run()
            except Exception:
                logger.exception("[calendar-sync] claim failed")
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
            self._storage.update_calendar_sync_run(run_id, progress={"phase": "syncing"})
            result = self._sync(
                self._storage, user_id,
                on_progress=lambda n: self._storage.update_calendar_sync_run(
                    run_id, progress={"phase": "syncing", "pushed": n}
                ),
            )
            self._storage.update_calendar_sync_run(
                run_id,
                status="done",
                pushed=result.get("pushed", 0),
                pulled=result.get("pulled", 0),
                progress={"phase": "done", **result},
                finished=True,
            )
            logger.info("[calendar-sync] run %s done %s", run_id, result)
        except Exception as exc:  # noqa: BLE001
            logger.exception("[calendar-sync] run %s failed", run_id)
            self._storage.update_calendar_sync_run(
                run_id, status="failed", error=str(exc)[:1000],
                progress={"phase": "failed"}, finished=True,
            )


# ── module singleton, wired by the server lifespan ───────────────────
calendar_sync_worker: Optional[CalendarSyncWorker] = None


def init_worker(storage: Any, sync_fn: Optional[SyncFn] = None) -> CalendarSyncWorker:
    global calendar_sync_worker
    if sync_fn is None:
        from app.calendar_sync.sync import run_calendar_sync

        sync_fn = run_calendar_sync
    calendar_sync_worker = CalendarSyncWorker(storage, sync_fn)
    return calendar_sync_worker
