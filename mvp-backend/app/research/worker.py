"""
Background research worker.

A bounded worker pool claims durable attempts, runs discovery, and atomically
publishes candidates with terminal success. Attempts carry fencing tokens and a
total deadline that survives restart recovery. A separate periodic reaper can
expire rows even while every worker is occupied. Native async provider calls
are cancellable; injected synchronous functions remain cooperative and retain
their worker slot until returning.
The discovery function is injected (default app.research.graph.discover_activities)
so the worker is unit-testable with a fake that does no LLM/network calls.
"""
from __future__ import annotations

import logging

from app.jobs.context import JobContext, JobStopped
from app.jobs.runner import JobReaper
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
        run_timeout: float = 600,
    ) -> None:
        self._storage = storage
        self._run_timeout = run_timeout
        self._reaper = JobReaper(storage, "research")
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
        self._reaper.start()
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
        self._reaper.stop()
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
                run = self._storage.claim_next_queued_run(self._run_timeout)
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
        context = JobContext.from_run(self._storage, "research", run, self._stop)
        try:
            self._storage.update_job_progress(context, progress={"phase": "researching"})
            candidates = self._discover(
                location=run.get("location") or {},
                kids=run.get("kids") or [],
                params=run.get("params") or {},
                progress_cb=lambda p: self._storage.update_job_progress(context, progress=p),
                run_id=run_id, user_id=user_id, job_context=context,
            )
            context.check()
            progress = {"phase": "done", "candidates_found": len(candidates)}
            prev = (self._storage.get_research_run(run_id) or {}).get("progress") or {}
            if prev.get("candidates_considered"):
                progress["candidates_considered"] = prev["candidates_considered"]
            if self._storage.publish_research_attempt(context, user_id, candidates, progress):
                logger.info("[research] run %s done with %d candidates", run_id, len(candidates))
        except JobStopped:
            logger.info("[research] run %s stopped cooperatively", run_id)
            self._storage.reap_expired_job_attempts("research")
        except Exception as exc:
            logger.exception("[research] run %s failed", run_id)
            self._storage.finalize_job_attempt(context, status="failed", error=str(exc)[:1000],
                                               progress={"phase": "failed"})


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
