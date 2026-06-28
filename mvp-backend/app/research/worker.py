"""
Background research worker.

A single daemon thread (matching the fire-and-forget threading idiom in
telemetry.py) drains queued research_runs: claim -> run the discovery graph ->
write candidates -> mark done/failed. The research_runs row is the durable job;
the phone never holds it. A startup sweeper (storage.requeue_stale_running_runs)
re-queues anything a restart left 'running', and insert_activity_candidates is
delete-then-insert so a re-run is idempotent.

The discovery function is injected (default app.research.graph.discover_activities)
so the worker is unit-testable with a fake that does no LLM/network calls.
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

DiscoverFn = Callable[..., List[Dict[str, Any]]]


def _default_concurrency() -> int:
    """How many runs execute at once. Discovery is I/O-bound (the model + Tavily
    calls release the GIL on network waits), so a small thread pool gives real
    parallelism on the single instance and removes head-of-line blocking when
    several parents discover at the same time. Bounded to keep us under the
    OpenAI/Tavily rate ceilings; raise via env as the beta grows."""
    try:
        n = int(os.getenv("RESEARCH_WORKER_CONCURRENCY", "3"))
    except (TypeError, ValueError):
        n = 3
    return max(1, min(n, 16))


class ResearchWorker:
    def __init__(
        self,
        storage: Any,
        discover_fn: DiscoverFn,
        poll_interval: float = 5.0,
        concurrency: Optional[int] = None,
    ) -> None:
        self._storage = storage
        self._discover = discover_fn
        self._poll = poll_interval
        self._concurrency = concurrency if concurrency is not None else _default_concurrency()
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._threads: List[threading.Thread] = []

    # ── lifecycle ────────────────────────────────────────────────────
    def start(self) -> None:
        if any(t.is_alive() for t in self._threads):
            return
        self._stop.clear()
        self._threads = []
        for i in range(self._concurrency):
            t = threading.Thread(target=self._loop, name=f"research-worker-{i}", daemon=True)
            t.start()
            self._threads.append(t)
        logger.info("[research] worker started (%d threads)", self._concurrency)

    def notify(self) -> None:
        """Wake idle workers immediately (called by the enqueue endpoint). A
        single set() releases all threads waiting on the event; each then claims
        runs atomically until the queue drains, so wakes are never lost beyond
        the poll-interval fallback."""
        self._wake.set()

    def stop(self, timeout: float = 3.0) -> None:
        self._stop.set()
        self._wake.set()
        for t in self._threads:
            t.join(timeout)
        logger.info("[research] worker stopped")

    # ── loop ─────────────────────────────────────────────────────────
    def _loop(self) -> None:
        while not self._stop.is_set():
            did_work = self._drain()
            if not did_work:
                # Idle: sleep until notified or the poll interval elapses (the
                # poll fallback also re-checks for sweeper-requeued runs).
                self._wake.wait(self._poll)
                self._wake.clear()

    def _drain(self) -> bool:
        worked = False
        while not self._stop.is_set():
            try:
                run = self._storage.claim_next_queued_run()
            except Exception:
                logger.exception("[research] claim_next_queued_run failed")
                break
            if not run:
                break
            worked = True
            self.process_run(run)
        return worked

    # ── one run ──────────────────────────────────────────────────────
    def process_run(self, run: Dict[str, Any]) -> None:
        """Execute a single claimed run. Public + synchronous so tests can call
        it directly without spinning the thread."""
        run_id = run["id"]
        user_id = run["user_id"]
        try:
            self._storage.update_research_run(run_id, progress={"phase": "researching"})
            candidates = self._discover(
                location=run.get("location") or {},
                kids=run.get("kids") or [],
                params=run.get("params") or {},
                progress_cb=lambda p: self._storage.update_research_run(run_id, progress=p),
                run_id=run_id,
                user_id=user_id,
            )
            n = self._storage.insert_activity_candidates(
                run_id=run_id, user_id=user_id, candidates=candidates
            )
            # Carry the "of M reviewed" breadcrumb (set by discover when it trimmed
            # a deep pool to the surfaced top N) into the terminal frame so the
            # results screen can honestly say "top N of M reviewed".
            done_progress: Dict[str, Any] = {"phase": "done", "candidates_found": n}
            try:
                prev = (self._storage.get_research_run(run_id) or {}).get("progress") or {}
                if prev.get("candidates_considered"):
                    done_progress["candidates_considered"] = prev["candidates_considered"]
            except Exception:  # breadcrumb is cosmetic; never block finalize
                pass
            # Finalize only if the run is still 'running'. If the parent cancelled
            # it during the (long) discovery, don't resurrect it to done — drop the
            # work so a cancel actually sticks (terminal state stays terminal).
            if self._storage.finalize_run_if_running(
                run_id,
                status="done",
                candidate_count=n,
                progress=done_progress,
            ):
                logger.info("[research] run %s done with %d candidate(s)", run_id, n)
            else:
                self._storage.insert_activity_candidates(
                    run_id=run_id, user_id=user_id, candidates=[]
                )  # discard candidates collected for a now-cancelled run
                logger.info("[research] run %s left 'running' mid-flight (cancelled?) — discarded %d candidate(s)", run_id, n)
        except Exception as exc:  # noqa: BLE001 - any failure marks the run failed
            logger.exception("[research] run %s failed", run_id)
            # Conditional too: a cancel during discovery must not be clobbered to failed.
            self._storage.finalize_run_if_running(
                run_id,
                status="failed",
                error=str(exc)[:1000],
                progress={"phase": "failed"},
            )


# ── module singleton, wired up by the server lifespan ────────────────
research_worker: Optional[ResearchWorker] = None


def init_worker(storage: Any, discover_fn: Optional[DiscoverFn] = None) -> ResearchWorker:
    """Create (or replace) the module-level worker. Imports the real discovery
    graph lazily so importing this module doesn't pull in deepagents."""
    global research_worker
    if discover_fn is None:
        from app.research.graph import discover_activities

        discover_fn = discover_activities
    research_worker = ResearchWorker(storage, discover_fn)
    return research_worker
