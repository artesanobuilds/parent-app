"""Shared lifecycle around existing graphs, with no HTTP or storage dependency.

Disconnect stops delivery, not a Python worker thread. A shielded producer drains
its graph while retaining ownership; another turn cannot repair that checkpoint
until outstanding synchronous tools finish. This intentionally does not promise
hard cancellation or zero model spend after disconnect.
"""
import asyncio
import inspect
import logging
import time
from contextlib import aclosing, nullcontext, asynccontextmanager
from weakref import WeakKeyDictionary
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable

from app.agent_runtime.context import RunContext
from app.agent_runtime.events import RunEvent, normalize
from app.agent_runtime.sessions import conversation_gates
from app import telemetry

logger = logging.getLogger(__name__)


class FamilyAdmissionClosed(RuntimeError):
    pass


class RunInterrupted(RuntimeError):
    """The detached run drained without reporting a successful outcome."""


# All tasks use the current ASGI event loop; separate test loops are isolated.
_families = WeakKeyDictionary()


def _family_state():
    return _families.setdefault(asyncio.get_running_loop(), {"fenced": {}, "runs": {}})



@dataclass
class _Failure:
    error: Exception


async def _call(hook, *args):
    if hook is not None:
        value = hook(*args)
        if inspect.isawaitable(value):
            await value


async def owned_stream(context: RunContext, factory: Callable, *, wait_timeout=30):
    """Run an async iterator under ownership, joining on close or cancellation.

    The bounded output queue races the disconnect signal so a producer never
    waits for an absent consumer. The producer is never cancelled by that
    consumer, including repeated cancellation while joining.
    """
    state = _family_state()
    if context.user_id in state["fenced"]:
        raise FamilyAdmissionClosed("Family execution is temporarily unavailable")
    queue = asyncio.Queue(maxsize=32)
    disconnected = asyncio.Event()
    end = object()

    async def publish(item):
        if disconnected.is_set():
            return
        put = asyncio.create_task(queue.put(item))
        closed = asyncio.create_task(disconnected.wait())
        try:
            await asyncio.wait((put, closed), return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in (put, closed):
                if not task.done():
                    task.cancel()
            await asyncio.gather(put, closed, return_exceptions=True)

    async def produce():
        started = time.monotonic()
        outcome = "failed"
        try:
            async with conversation_gates.hold(context.thread_key, timeout=wait_timeout):
                # A canceled waiter must not start a turn after the prior owner exits.
                if disconnected.is_set():
                    outcome = "interrupted"
                    return
                async with aclosing(factory(disconnected)) as events:
                    async for event in events:
                        await publish(event)
            outcome = "interrupted" if disconnected.is_set() else "completed"
        except RunInterrupted:
            outcome = "interrupted"
        except Exception as exc:
            await publish(_Failure(exc))
        finally:
            telemetry.incr(f"harness.{context.surface}.{outcome}")
            logger.info("[harness] run=%s surface=%s outcome=%s duration_ms=%d",
                        context.run_id, context.surface, outcome,
                        round((time.monotonic() - started) * 1000))
            await publish(end)
            if disconnected.is_set():
                while not queue.empty():
                    queue.get_nowait()
                queue.put_nowait(end)

    producer = asyncio.create_task(produce(), name=f"agent-run:{context.run_id}")
    runs = state["runs"].setdefault(context.user_id, {})
    runs[producer] = disconnected
    def forget(task):
        runs.pop(task, None)
        if not runs:
            state["runs"].pop(context.user_id, None)
    producer.add_done_callback(forget)
    try:
        while True:
            event = await queue.get()
            if event is end:
                break
            if isinstance(event, _Failure):
                raise event.error
            yield event
    finally:
        disconnected.set()
        # Keep joining under repeated ASGI cancel scopes. Ownership stays with
        # the producer, so even a canceled waiter cannot transfer it prematurely.
        while not producer.done():
            try:
                await asyncio.shield(producer)
            except asyncio.CancelledError:
                continue
        producer.result()


class AgentExecutionService:
    async def cancel_family(self, user_id: str):
        """Close admission, disconnect and join all runs. Caller releases the fence.

        Call BEFORE deleting domain/checkpoint state; never hold a DB transaction
        while joining a graph whose outstanding tool may still need that database.
        """
        state = _family_state()
        state["fenced"][user_id] = state["fenced"].get(user_id, 0) + 1
        pending = list(state["runs"].get(user_id, {}).items())
        for _, disconnected in pending:
            disconnected.set()
        if pending:
            joined = asyncio.gather(*(task for task, _ in pending), return_exceptions=True)
            while not joined.done():
                try:
                    await asyncio.shield(joined)
                except asyncio.CancelledError:
                    continue

    def release_family(self, user_id: str):
        fenced = _family_state()["fenced"]
        count = fenced.get(user_id, 0)
        if count <= 1:
            fenced.pop(user_id, None)
        else:
            fenced[user_id] = count - 1

    @asynccontextmanager
    async def family_fence(self, user_id: str):
        await self.cancel_family(user_id)
        try:
            yield
        finally:
            self.release_family(user_id)

    async def stream(
        self, agent: Any, inputs: dict, config: dict, context: RunContext, *,
        version="v1", repair=None, is_internal=None, is_retryable=None,
        before=None, reconcile=None, finalize=None, scope=None, agent_factory=None,
    ) -> AsyncIterator[RunEvent]:
        """Hooks execute inside ownership and the same context as graph tools.

        `scope(context)` returns a synchronous context manager (e.g. run ledger).
        Reconciliation runs before repair on each attempt. Finalization can fail;
        consumers then see an exception, never a successful stream exhaustion.
        """
        async def execute(disconnected):
            with scope(context) if scope else nullcontext():
                await _call(before, context)
                if disconnected.is_set():
                    raise RunInterrupted("Run disconnected before dispatch")
                graph = agent_factory() if agent_factory else agent
                for attempt in (1, 2):
                    await _call(reconcile, context, graph, config)
                    await _call(repair, graph, config)
                    if disconnected.is_set():
                        raise RunInterrupted("Run disconnected before dispatch")
                    text = []
                    tool_started = False
                    try:
                        upstream = graph.astream_events(inputs, config=config, version=version)
                        async with aclosing(upstream):
                            async for raw in upstream:
                                # Track tool dispatch before visibility filtering. An
                                # internal event may still represent a business effect.
                                if raw.get("event") == "on_tool_start":
                                    tool_started = True
                                if is_internal and is_internal(raw):
                                    continue
                                event = normalize(raw)
                                if event is None:
                                    continue
                                if event.kind == "token":
                                    text.append(event.content)
                                yield event
                        if disconnected.is_set():
                            raise RunInterrupted("Run disconnected while executing")
                        await _call(finalize, context, "".join(text))
                        break
                    except Exception as exc:
                        # No text is insufficient: a tool may already have committed.
                        if (attempt == 1 and not text and not tool_started
                                and not disconnected.is_set()
                                and is_retryable and is_retryable(exc)):
                            logger.warning("[harness] dangling tool call mid-run — repairing and retrying run=%s surface=%s",
                                           context.run_id, context.surface)
                            telemetry.incr(f"harness.{context.surface}.repair_retry")
                            continue
                        raise
            # Scope exit may commit the run ledger; it too precedes completion.
            yield RunEvent("completed")
        async with aclosing(owned_stream(context, execute)) as events:
            async for event in events:
                yield event


execution_service = AgentExecutionService()
