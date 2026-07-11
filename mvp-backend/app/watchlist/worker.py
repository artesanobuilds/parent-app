"""Watchlist worker: a catch-up sweep with due-TIME semantics.

Deliberately NOT email_sync's hour-equality gate (`now.hour == target_hour`
skips work silently across deploys/downtime): every sweep asks "what is due
NOW that hasn't been delivered for this opens_at snapshot?" — so any downtime
is repaired within one poll of boot, and a changed opens_at re-arms the
window automatically (new snapshot → the NOT-EXISTS guard passes again).

Durable-first delivery per due notification:
  1. one storage.transaction(): append the window_notifications row + seed the
     fallback `action` to-do (the parent gets the board fallback even if APNs
     is down or they have no push tokens);
  2. BLOCKING push.send_push(...) — returns the outcome;
  3. record the outcome on the row. Failed sends retry each sweep until
     opens_effective + grace, then escalate via logger.error (→ Sentry).

The sweep also closes watched windows once they've opened and were notified;
windows past opens with NO day_of row stay `watching` on purpose — that is
exactly what the miss-detector gauge counts and Grafana alerts on.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from app import observability as obs
from app.watchlist import windows as W

logger = logging.getLogger(__name__)

# Heartbeat for the watchlist_seconds_since_last_tick gauge.
last_tick_at: Optional[float] = None

SendFn = Callable[..., str]


def _default_send(**kwargs: Any) -> str:
    from app import push
    return push.send_push(**kwargs)


def _capture(event: str, user_id: str, props: Dict[str, Any]) -> None:
    try:
        from app.analytics import capture
        capture(event, user_id, props)
    except Exception:  # noqa: BLE001
        pass


def _window_name(storage: Any, window: Dict[str, Any]) -> str:
    if window.get("activity_id"):
        try:
            activity = storage.get_tracked_activity(window["activity_id"])
            if activity and activity.get("name"):
                return activity["name"]
        except Exception:  # noqa: BLE001
            pass
    return window.get("provider") or "this activity"


def _short_local_date(window: Dict[str, Any]) -> str:
    opens = W.parse_ts(window.get("opens_at"))
    if not opens:
        return "soon"
    local = opens.astimezone(W._zone(window.get("tz")))
    return local.strftime("%b %-d") if hasattr(local, "strftime") else "soon"


class WatchlistWorker:
    def __init__(
        self,
        storage: Any,
        send_fn: Optional[SendFn] = None,
        poll_interval: float = 300.0,
        now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._storage = storage
        self._send = send_fn or _default_send
        self._poll = poll_interval
        self._now = now_fn
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ── lifecycle (email_sync worker idiom) ──────────────────────────
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="watchlist-worker", daemon=True)
        self._thread.start()
        logger.info("[watchlist] worker started (poll=%ss)", self._poll)

    def notify(self) -> None:
        self._wake.set()

    def stop(self, timeout: float = 3.0) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread:
            self._thread.join(timeout)
        logger.info("[watchlist] worker stopped")

    def _loop(self) -> None:
        global last_tick_at
        while not self._stop.is_set():
            try:
                self.sweep()
            except Exception:
                logger.exception("[watchlist] sweep failed")
            last_tick_at = time.time()
            self._wake.wait(self._poll)
            self._wake.clear()

    # ── one sweep ────────────────────────────────────────────────────
    def sweep(self, now: Optional[datetime] = None) -> Dict[str, int]:
        """Deliver everything due, retry recorded failures inside the grace
        window, escalate expired failures, close notified+opened windows.
        Returns counters (tests + logs). `now` injectable for tests."""
        now = now or self._now()
        stats = {"delivered": 0, "retried": 0, "escalated": 0, "closed": 0}
        for window in self._storage.list_watching_windows():
            try:
                self._process_window(window, now, stats)
            except Exception:
                # One bad window must not starve the rest of the sweep.
                logger.exception("[watchlist] window %s failed", window.get("id"))
        return stats

    def _process_window(self, window: Dict[str, Any], now: datetime, stats: Dict[str, int]) -> None:
        window_id = window["id"]
        snapshot = window.get("opens_at")

        # Retry pass FIRST, over pre-existing failures only — a delivery made
        # later in this same sweep must wait for the NEXT sweep to retry
        # (immediate same-sweep re-sends would double-buzz a flaky APNs).
        deadline = W.retry_deadline(window)
        for row in self._storage.list_window_notifications(window_id):
            if row.get("outcome") != "failed":
                continue
            if deadline and now < deadline:
                outcome = self._send_for(window, row["kind"])
                self._storage.set_window_notification_outcome(row["id"], outcome)
                obs.count("watchlist.notifications.sent", kind=row["kind"], outcome=outcome)
                stats["retried"] += 1
            else:
                # ERROR level on purpose: Sentry's LoggingIntegration turns
                # this into an issue with full context.
                logger.error(
                    "[watchlist] notification %s for window %s failed past grace "
                    "(user=%s kind=%s)", row["id"], window_id,
                    window.get("user_id"), row["kind"],
                )
                self._storage.set_window_notification_outcome(row["id"], "failed_final")
                stats["escalated"] += 1

        kind = W.due_kind(window, now)
        if kind and not self._storage.window_notification_exists(window_id, kind, snapshot):
            self._deliver(window, kind, now)
            stats["delivered"] += 1

        # Close pass: opened + day_of delivered for the current snapshot →
        # closed. Opened with NO day_of row stays `watching` — that's the miss
        # detector's signal, never paper over it here.
        opens = W.opens_effective(window)
        if opens and now > opens and self._storage.window_notification_exists(
            window_id, W.DAY_OF, snapshot
        ):
            self._storage.update_registration_window(window_id, status="closed")
            stats["closed"] += 1

    # ── durable-first delivery ───────────────────────────────────────
    def _deliver(self, window: Dict[str, Any], kind: str, now: datetime) -> None:
        window_id = window["id"]
        user_id = window["user_id"]
        name = _window_name(self._storage, window)

        # (1) Durable first: log row + fallback to-do in ONE transaction. The
        # to-do is the promise's floor — it exists even if every push fails.
        with self._storage.transaction():
            notification_id = self._storage.insert_window_notification(
                window_id=window_id, kind=kind,
                opens_at_snapshot=window.get("opens_at"), transport="push",
            )
            self._storage.add_todo(
                user_id,
                title=self._todo_title(window, kind, name),
                activity_id=window.get("activity_id"),
                kind="action",
                detail="From your registration watchlist — dismiss it if you're already set.",
                source="watchlist",
            )

        # (2) Blocking send; (3) record the outcome.
        outcome = self._send_for(window, kind)
        self._storage.set_window_notification_outcome(notification_id, outcome)

        obs.count("watchlist.notifications.sent", kind=kind, outcome=outcome)
        due_at = W.day_of_due_at(window) if kind == W.DAY_OF else W.t_minus_due_at(window)
        if due_at:
            obs.observe("watchlist.notification.delay_seconds",
                        max(0.0, (now - due_at).total_seconds()), kind=kind)
        _capture("registration_window_notified", user_id, {"kind": kind})

    def _todo_title(self, window: Dict[str, Any], kind: str, name: str) -> str:
        date = _short_local_date(window)
        if kind == W.DAY_OF:
            return f"Register for {name} — registration opens {date}"
        if window.get("confidence") == "estimated":
            # The trust design: estimated dates ASK, they don't assert.
            return f"Confirm {name}'s registration date (we think it's {date})"
        return f"{name} registration opens {date} — get your info ready"

    def _send_for(self, window: Dict[str, Any], kind: str) -> str:
        name = _window_name(self._storage, window)
        date = _short_local_date(window)
        if kind == W.DAY_OF:
            title = "Registration opens today"
            body = f"{name} — don't miss it. Tap to open your plan."
        elif window.get("confidence") == "estimated":
            title = "Registration coming up — is the date right?"
            body = f"We think {name} opens {date}. Tap to confirm the date."
        else:
            title = "Registration opens in a week"
            body = f"{name} opens {date}. Get your details ready."
        return self._send(
            storage=self._storage, user_id=window["user_id"],
            title=title, body=body,
            data={"type": "registration_window", "window_id": window["id"],
                  "kind": kind},
        )


# ── module singleton, wired by the server lifespan ───────────────────
watchlist_worker: Optional[WatchlistWorker] = None


def init_worker(storage: Any, send_fn: Optional[SendFn] = None) -> WatchlistWorker:
    global watchlist_worker
    watchlist_worker = WatchlistWorker(storage, send_fn=send_fn)
    return watchlist_worker
