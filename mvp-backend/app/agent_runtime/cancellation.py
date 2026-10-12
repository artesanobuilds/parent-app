"""Cooperative coach cancellation at model/tool boundaries.

Never cancel the graph task: it may own a synchronous tool running in a worker
thread. Only model I/O is cancellable. Started tools settle under the existing
conversation ownership; pending tools return a checkpointable interruption.
"""
import asyncio
from contextlib import contextmanager
from contextvars import ContextVar

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage

from app.agent_runtime.context import current_run

_disconnect = ContextVar("agent_disconnect", default=None)


@contextmanager
def bind_disconnect(event):
    token = _disconnect.set(event)
    try:
        yield
    finally:
        _disconnect.reset(token)


def _voice_disconnect():
    run = current_run()
    return _disconnect.get() if run and run.surface == "parent_voice" else None


class VoiceCancellationMiddleware(AgentMiddleware):
    async def awrap_model_call(self, request, handler):
        from app.agent_runtime.service import RunInterrupted

        disconnected = _voice_disconnect()
        if disconnected is None:
            return await handler(request)
        if disconnected.is_set():
            raise RunInterrupted("Voice turn disconnected before model dispatch")
        model = asyncio.create_task(handler(request))
        closed = asyncio.create_task(disconnected.wait())
        try:
            await asyncio.wait((model, closed), return_when=asyncio.FIRST_COMPLETED)
            # Prefer interruption even if completion and disconnect race. An
            # abandoned model result must not dispatch another batch of tools.
            if disconnected.is_set():
                raise RunInterrupted("Voice turn disconnected during model generation")
            return model.result()
        finally:
            for task in (model, closed):
                if not task.done():
                    task.cancel()
            await asyncio.gather(model, closed, return_exceptions=True)

    async def awrap_tool_call(self, request, handler):
        disconnected = _voice_disconnect()
        if disconnected is not None and disconnected.is_set():
            # Raising here could cancel sibling tools that have already started.
            # A normal ToolMessage lets that batch settle and checkpoints the
            # skipped call; the next model boundary then interrupts the graph.
            return ToolMessage(
                content="Voice turn interrupted before tool dispatch.",
                tool_call_id=request.tool_call["id"],
                status="error",
            )
        return await handler(request)
