"""The DURABLE LangGraph checkpointer — agent context survives a restart.

Every agent here used to hold its own `MemorySaver()`: process-local, so a
Railway deploy or a crash silently amnesia'd every in-flight conversation. That
was invisible while Coach was one unnamed thread; the moment the parent can see
a LIST of past conversations, "open it and the coach has forgotten everything"
is a visible bug. So the three savers (`app/agent.py`, `app/kid_agent.py`,
`app/onboarding_agent.py`) are now all this one durable saver.

Four things that are easy to get wrong here:

1. **`AsyncSqliteSaver` is loop-bound and cannot be built at import time.**
   Its `__init__` calls `asyncio.get_running_loop()` — constructing it at module
   scope raises, and an instance built on one event loop cannot be driven from
   another (aiosqlite dispatches onto the loop it captured; a closed loop gives
   `RuntimeError: Event loop is closed`). `DurableCheckpointer` below is
   therefore a thin proxy that lazily builds ONE inner saver per running loop.
   That is also what makes TestClient teardown safe — a test that closes its
   loop just orphans that loop's saver instead of poisoning the singleton
   (the trap in memory `debugging_testclient_storage_singleton`).

2. **Both the sync and async halves are used.** Streaming surfaces go through
   `astream_events`/`aget_state`; `app/evals` and several tests drive graphs
   synchronously. `AsyncSqliteSaver`'s sync methods raise from the main thread,
   so the sync half is delegated to a separate `SqliteSaver` over its own
   `sqlite3` connection. Both point at the same file — SQLite in WAL mode
   (which both savers set in `setup()`) handles the concurrent readers.

3. **The file is USER STATE.** It holds every parent's and kid's verbatim
   conversation, so it lives beside the DuckDB on the Railway volume (never
   baked into the image) and is excluded from git + the Docker build context.
   `delete_user_threads` exists because `DELETE /family/{user_id}` promises
   "delete my data": with a process-local saver the checkpoints evaporated on
   their own, and now they don't.

4. **A poisoned checkpoint outlives the process too.** A dangling `tool_calls`
   checkpoint 400s a thread forever (`app/thread_repair.py`, the 2026-07
   two-day voice outage). It used to be cleared by the next restart; now
   nothing clears it but repair. `tests/test_durable_checkpointer.py` proves
   repair still heals a thread through this proxy.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, AsyncIterator, Collection, Dict, Iterator, Optional, Sequence

import aiosqlite
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Where the file lives
# --------------------------------------------------------------------------- #
# Same convention as `DuckDBStorage.__init__`: honour MVP_DUCKDB_PATH so the
# checkpoints land on the same Railway volume as the DB (and, in tests, in the
# same tmpdir), rather than wherever the CWD happens to be. Deliberately NOT a
# `.parquet` and NOT at the backend root — see memory
# `debugging_railway_parquet_deploy_hazard` for what happens to loose state
# files there.

CHECKPOINT_FILENAME = "agent_checkpoints.sqlite"


def checkpoint_db_path() -> Path:
    """The durable checkpoint file's path (parent dirs created)."""
    explicit = os.getenv("MVP_CHECKPOINT_DB_PATH")
    if explicit:
        path = Path(explicit)
    else:
        duckdb_env = os.getenv("MVP_DUCKDB_PATH")
        data_dir = (
            Path(duckdb_env).parent
            if duckdb_env
            else Path(__file__).resolve().parent.parent / "data"
        )
        path = data_dir / CHECKPOINT_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


# --------------------------------------------------------------------------- #
# The proxy
# --------------------------------------------------------------------------- #


class DurableCheckpointer(BaseCheckpointSaver[str]):
    """SQLite-backed checkpointer with per-event-loop inner savers.

    Presents the whole `BaseCheckpointSaver` surface so `create_agent(
    checkpointer=...)` and `thread_repair` see an ordinary saver. Every method
    forwards to the inner saver for the CURRENT loop (async) or to the shared
    sync saver (sync).
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        super().__init__()
        self.db_path = Path(db_path) if db_path is not None else checkpoint_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # id(loop) -> AsyncSqliteSaver. Keyed by id and never evicted on loop
        # close: a closed loop's entry is unreachable (nothing runs on it
        # again) and the aiosqlite worker thread is a daemon, so leaving it is
        # cheaper than trying to detect closure. In prod there is exactly one
        # loop for the process's life; in tests, one per TestClient.
        self._async_savers: Dict[int, AsyncSqliteSaver] = {}
        self._sync_saver: Optional[SqliteSaver] = None
        self._lock = threading.Lock()
        # Extra msgpack allowlist entries accumulated via `with_allowlist`
        # (langgraph derives one per compiled graph from its state schema).
        # Applied when an inner saver is built, since the inner savers own the
        # serde that actually does the decoding.
        self._extra_allowlist: tuple[tuple[str, ...], ...] = ()
        logger.info("[checkpointer] durable sqlite saver at %s", self.db_path)

    # ── inner savers ─────────────────────────────────────────────────────

    def _apply_allowlist(self, saver: BaseCheckpointSaver) -> Any:
        if not self._extra_allowlist:
            return saver
        return saver.with_allowlist(self._extra_allowlist)

    def _async(self) -> AsyncSqliteSaver:
        """The inner saver bound to the loop we're running on."""
        loop = asyncio.get_running_loop()
        key = id(loop)
        saver = self._async_savers.get(key)
        if saver is not None:
            return saver
        with self._lock:
            saver = self._async_savers.get(key)
            if saver is None:
                # aiosqlite.connect() returns an awaitable Connection that
                # starts its worker thread on first await; AsyncSqliteSaver's
                # own `setup()` awaits it (`_ensure_connected`), so we do NOT
                # await it here and can stay in a sync method.
                conn = aiosqlite.connect(str(self.db_path))
                # aiosqlite's worker thread is NON-daemon and is only joined by
                # an explicit `await conn.close()`. Without this line any
                # process that ever touched a checkpoint HANGS at exit waiting
                # on it — verified: pytest and one-off scripts both wedge after
                # printing their results. The thread object is constructed in
                # `aiosqlite.connect()` and not started until the first await,
                # so flipping the flag here is in time. `close()` below is the
                # graceful path; this is the guarantee that a missed close (a
                # crashed worker, a test that forgets teardown) can't wedge the
                # process.
                thread = getattr(conn, "_thread", None)
                if thread is not None:
                    thread.daemon = True
                saver = self._apply_allowlist(AsyncSqliteSaver(conn))
                self._async_savers[key] = saver
        return saver

    def _sync(self) -> SqliteSaver:
        """The shared sync saver. `check_same_thread=False` matches the
        package's own `from_conn_string` — SqliteSaver holds a lock."""
        if self._sync_saver is not None:
            return self._sync_saver
        with self._lock:
            if self._sync_saver is None:
                conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
                self._sync_saver = self._apply_allowlist(SqliteSaver(conn))
        return self._sync_saver

    # ── serde plumbing ───────────────────────────────────────────────────

    def with_allowlist(
        self, extra_allowlist: Collection[tuple[str, ...]]
    ) -> "DurableCheckpointer":
        """Return a clone whose inner savers decode the given extra types.

        A clone rather than a mutation because langgraph calls this once per
        compiled graph and each graph must keep its own allowlist. The clone
        opens its own connections to the same file (bounded: one per distinct
        graph schema, and WAL handles the concurrency).
        """
        extra = tuple(tuple(entry) for entry in extra_allowlist)
        if not extra or set(extra) <= set(self._extra_allowlist):
            return self
        clone = DurableCheckpointer(self.db_path)
        clone._extra_allowlist = tuple(dict.fromkeys(self._extra_allowlist + extra))
        return clone

    def get_next_version(self, current: str | None, channel: None) -> str:
        # MUST match the inner savers' scheme (zero-padded int + random tail),
        # because the versions this returns are what get written by them.
        # Delegated rather than copied so a package bump can't drift it.
        return SqliteSaver.get_next_version(self, current, channel)  # type: ignore[arg-type]

    # ── async surface (what every streaming surface uses) ─────────────────

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        return await self._async().aget_tuple(config)

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        async for item in self._async().alist(
            config, filter=filter, before=before, limit=limit
        ):
            yield item

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return await self._async().aput(config, checkpoint, metadata, new_versions)

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        return await self._async().aput_writes(config, writes, task_id, task_path)

    async def adelete_thread(self, thread_id: str) -> None:
        return await self._async().adelete_thread(thread_id)

    async def aget_delta_channel_history(
        self, *, config: RunnableConfig, channels: Sequence[str]
    ):
        return await self._async().aget_delta_channel_history(
            config=config, channels=channels
        )

    # ── sync surface (app/evals + several tests drive graphs synchronously) ─

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        return self._sync().get_tuple(config)

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        return self._sync().list(config, filter=filter, before=before, limit=limit)

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        return self._sync().put(config, checkpoint, metadata, new_versions)

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        return self._sync().put_writes(config, writes, task_id, task_path)

    def delete_thread(self, thread_id: str) -> None:
        self._sync().delete_thread(thread_id)

    def get_delta_channel_history(
        self, *, config: RunnableConfig, channels: Sequence[str]
    ):
        return self._sync().get_delta_channel_history(config=config, channels=channels)

    # ── housekeeping ─────────────────────────────────────────────────────

    async def aclose(self) -> None:
        """Close this loop's connection. Called from the FastAPI lifespan's
        shutdown half, and by tests between TestClient instances.

        Only the CURRENT loop's saver is closed — closing another loop's would
        dispatch onto a loop we aren't running (and, at shutdown, a loop that
        may already be gone). Never raises: a checkpointer that fails to close
        must not turn a clean shutdown into a crash loop.
        """
        try:
            loop_key = id(asyncio.get_running_loop())
        except RuntimeError:
            return
        with self._lock:
            saver = self._async_savers.pop(loop_key, None)
        if saver is None:
            return
        try:
            await saver.conn.close()
        except Exception:
            logger.warning("[checkpointer] async close failed", exc_info=True)

    def close_sync(self) -> None:
        """Close the sync connection. Separate from `aclose` because the two
        halves hold independent connections (see the module docstring)."""
        with self._lock:
            saver, self._sync_saver = self._sync_saver, None
        if saver is None:
            return
        try:
            saver.conn.close()
        except Exception:
            logger.warning("[checkpointer] sync close failed", exc_info=True)

    def thread_ids(self) -> list[str]:
        """Thread IDs from checkpoints AND unfinished writes.

        An interrupted write can survive without a corresponding checkpoint;
        family cleanup must include both tables.
        """
        saver = self._sync()
        with saver.cursor(transaction=False) as cur:
            cur.execute("SELECT thread_id FROM checkpoints UNION SELECT thread_id FROM writes")
            return [row[0] for row in cur.fetchall()]


# One saver for the whole process. Built at import so the module-level
# `checkpointer` symbol every agent already imports keeps working — safe
# because the constructor opens no connections (see the class docstring).
checkpointer: DurableCheckpointer = DurableCheckpointer()


def _checkpoint_owner(thread_id: str) -> str:
    """Read the owner segment of the existing, unescaped thread namespaces."""
    parts = thread_id.split(":")
    if parts[0] in {"onboarding", "kid"} and len(parts) > 1:
        return parts[1]
    return parts[0]


def delete_user_threads(user_id: str, *, strict: bool = False) -> int:
    """Delete verified family threads without treating a namespace as an owner.

    Legacy thread keys do not escape user IDs or parent voice thread IDs. A
    reserved or colon-containing user ID therefore has ambiguous ownership;
    fail closed before any deletion, retaining the lifecycle retry obligation.
    Such identities need independent ownership evidence before manual repair.
    Compatibility callers still receive a best-effort count; strict callers
    receive failures and must not mark the purge complete.
    """
    deleted = 0
    try:
        if not user_id or ":" in user_id or user_id in {"kid", "onboarding"}:
            raise ValueError("Ambiguous legacy checkpoint owner; independent ownership evidence required")
        for thread_id in checkpointer.thread_ids():
            if _checkpoint_owner(thread_id) == user_id:
                checkpointer.delete_thread(thread_id)
                deleted += 1
        if any(_checkpoint_owner(thread_id) == user_id
               for thread_id in checkpointer.thread_ids()):
            raise RuntimeError("Checkpoint verification found remaining family threads")
    except Exception:
        logger.exception("[checkpointer] failed to purge threads for %s", user_id)
        if strict:
            raise
        return deleted
    if deleted:
        logger.info("[checkpointer] purged %d thread(s) for %s", deleted, user_id)
    return deleted


def purge_family_checkpoints(storage, user_id: str) -> int:
    """Clear the durable pending flag only after verified SQLite deletion.

    The caller holds execution_service.family_fence. Failure leaves a durable
    retry obligation and blocks new scoped runs; the domain cascade still stands.
    """
    pending = next((row for row in storage.pending_checkpoint_purges()
                    if row['user_id'] == user_id), None)
    if pending is None:
        return 0
    try:
        # Freeze the durable identity inventory while verifying ownership and
        # deleting SQLite rows. No async wait or provider work occurs here.
        with storage.transaction():
            known_users = {row[0] for row in storage._con.execute(
                "SELECT user_id FROM user_data UNION SELECT user_id FROM user_accounts "
                "UNION SELECT user_id FROM agent_family_fences"
            ).fetchall()}
            candidates = [thread for thread in checkpointer.thread_ids()
                          if _checkpoint_owner(thread) == user_id]
            for other in known_users - {user_id}:
                prefixes = (f"{other}:", f"onboarding:{other}:", f"kid:{other}:")
                if (other.startswith(user_id + ":") or user_id.startswith(other + ":")
                        or any(thread == other or thread.startswith(prefixes)
                               for thread in candidates)):
                    raise ValueError("Overlapping legacy checkpoint owners; independent ownership evidence required")
            count = delete_user_threads(user_id, strict=True)
            storage.mark_checkpoint_purged(user_id, pending['generation'])
            return count
    except Exception:
        logger.exception('[checkpointer] family purge remains pending for %s', user_id)
        return 0


async def join_cleanup(fn, *args):
    """Keep the family fence until a synchronous cleanup actually finishes."""
    task = asyncio.create_task(asyncio.to_thread(fn, *args))
    canceled = False
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            canceled = True
    result = task.result()
    if canceled:
        raise asyncio.CancelledError
    return result


def _retry_family_cleanup(storage, user_id):
    purge_family_checkpoints(storage, user_id)
    try:
        storage.refresh_family_snapshots(user_id)
    except Exception:
        logger.exception('[checkpointer] snapshot cleanup remains pending for %s', user_id)


async def retry_pending_checkpoint_purges(storage) -> None:
    from app.agent_runtime.service import execution_service
    for pending in storage.pending_family_cleanups():
        async with execution_service.family_fence(pending['user_id']):
            await join_cleanup(_retry_family_cleanup, storage, pending['user_id'])


async def checkpoint_purge_retries(storage, interval: float = 30) -> None:
    while True:
        await asyncio.sleep(interval)
        try:
            await retry_pending_checkpoint_purges(storage)
        except Exception:
            logger.exception('[checkpointer] pending purge retry failed')
