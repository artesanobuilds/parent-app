"""Tenant-scoped local command receipts, never client-message deduplication.

A checkpointed tool-call id is the operation identity. Receipt lookup spans runs
of the same thread so recovery can restore the lost ToolMessage. A new model
call with a new id is a new operation, even when its arguments are identical.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import wraps
import hashlib
import inspect
import json
from typing import Any, Callable, get_type_hints
from uuid import uuid4

from langchain.tools import ToolRuntime, tool


@dataclass(frozen=True)
class DurableRun:
    storage: Any
    user_id: str
    run_id: str
    thread_key: str
    generation: int


_run: ContextVar[DurableRun | None] = ContextVar("durable_run", default=None)
_active_command: ContextVar[bool] = ContextVar("durable_command", default=False)


class OperationConflict(ValueError):
    """A known operation was presented with different command arguments."""


def current_run() -> DurableRun | None:
    return _run.get()


def storage_for(user_id: str):
    run = current_run()
    if run:
        if run.user_id != user_id:
            raise PermissionError("Tool tenant does not match authenticated run")
        return run.storage
    # Compatibility for callers not yet moved onto the execution service.
    from app.server import storage_backend
    return storage_backend


@contextmanager
def run_scope(storage, user_id: str, run_id: str, thread_key: str):
    with storage.transaction():
        generation = storage.assert_family_writable(user_id)
        existing = storage._con.execute(
            "SELECT thread_key, generation FROM agent_runs WHERE user_id = ? AND run_id = ?",
            [user_id, run_id],
        ).fetchone()
        if existing and existing != (thread_key, generation):
            raise OperationConflict("Run identity belongs to a different conversation or generation")
        storage._con.execute(
            "INSERT INTO agent_runs (user_id, run_id, thread_key, generation) VALUES (?, ?, ?, ?) "
            "ON CONFLICT DO NOTHING", [user_id, run_id, thread_key, generation],
        )
    token = _run.set(DurableRun(storage, user_id, run_id, thread_key, generation))
    outcome = "failed"
    try:
        yield current_run()
        outcome = "completed"
    except BaseException as exc:
        if type(exc).__name__ in {"CancelledError", "GeneratorExit"}:
            outcome = "cancelled"
        raise
    finally:
        _run.reset(token)
        # UPDATE only: a deleted ledger must never be recreated by finalization.
        storage._con.execute(
            "UPDATE agent_runs SET outcome = ?, finished_at = now() WHERE user_id = ? AND run_id = ?",
            [outcome, user_id, run_id],
        )


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      default=lambda v: v.model_dump(exclude_unset=True) if hasattr(v, "model_dump") else str(v))


def argument_digest(arguments: dict) -> str:
    return hashlib.sha256(_json(arguments).encode()).hexdigest()


def execute(user_id: str, operation_id: str, command: str, arguments: dict, mutation: Callable):
    run = current_run()
    if run is None:
        raise RuntimeError("Durable command requires a trusted run scope")
    if user_id != run.user_id:
        raise PermissionError("Command tenant does not match authenticated run")
    digest = argument_digest(arguments)
    with run.storage.transaction():
        run.storage.assert_family_writable(user_id, run.generation)
        row = run.storage._con.execute(
            "SELECT command, argument_digest, result_json FROM agent_operation_receipts "
            "WHERE user_id = ? AND thread_key = ? AND operation_id = ?",
            [user_id, run.thread_key, operation_id],
        ).fetchone()
        if row:
            if row[0] != command or row[1] != digest:
                raise OperationConflict("Operation identity reused with different arguments")
            return json.loads(row[2])
        _validate_references(run.storage, user_id, arguments)
        token = _active_command.set(True)
        try:
            result = mutation()
        finally:
            _active_command.reset(token)
        run.storage._con.execute(
            "INSERT INTO agent_operation_receipts "
            "(user_id, run_id, thread_key, operation_id, command, argument_digest, result_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [user_id, run.run_id, run.thread_key, operation_id, command, digest, _json(result)],
        )
        return result


def _validate_references(storage, user_id: str, arguments: dict):
    # All local resource references are checked inside the mutation transaction.
    # Table names come exclusively from this constant allowlist.
    for field, table in {
        "todo_id": "todo_items", "activity_id": "tracked_activities",
        "candidate_id": "activity_candidates", "caregiver_id": "caregivers",
        "calendar_entry_id": "calendar_entries",
    }.items():
        identity = arguments.get(field)
        if identity:
            row = storage._con.execute(f"SELECT user_id FROM {table} WHERE id = ?", [identity]).fetchone()
            if not row or row[0] != user_id:
                raise PermissionError(f"{field} does not belong to this account")


def _tool_arguments(runtime, bound: dict) -> dict:
    # Prefer the exact checkpointed JSON over Pydantic-coerced values (3 vs
    # 3.0, omitted defaults). Recovery hashes that same persisted call.
    if runtime is not None:
        for message in reversed((runtime.state or {}).get("messages", [])):
            for call in getattr(message, "tool_calls", []) or []:
                if call.get("id") == runtime.tool_call_id:
                    return call.get("args") or {}
    return bound


def durable_tool(user_id: str):
    """Keep the public tool schema; ToolRuntime is injected by ToolNode only.

    Local commands execute synchronously under DuckDB's reentrant writer lock.
    Do not decorate tools which perform network calls: prepare those externally,
    then pass their local commit to execute().
    """
    def decorate(fn):
        signature = inspect.signature(fn)
        hints = get_type_hints(fn)

        @wraps(fn)
        def invoke(*args, runtime=None, **kwargs):
            bound = signature.bind(*args, **kwargs)
            # Normalize supplied arguments only. Defaults must match the persisted
            # checkpoint call's argument digest during recovery.
            arguments = _tool_arguments(runtime, dict(bound.arguments))
            call_id = getattr(runtime, "tool_call_id", None) or uuid4().hex

            def perform():
                result = fn(*args, **kwargs)
                if isinstance(result, str) and (result.startswith("Could not ") or " hit an error: " in result):
                    raise RuntimeError(result)
                return result

            def dispatch():
                value = execute(user_id, call_id, fn.__name__, arguments, perform)
                if fn.__name__ in {"LearnedAboutParent", "LearnedAboutChild", "FoundMoreAboutParent", "FoundMoreAboutChild"}:
                    from app.services.profiles import refresh_profile
                    refresh_profile(user_id)
                return value

            if current_run() is not None:
                return dispatch()
            storage = storage_for(user_id)
            with run_scope(storage, user_id, uuid4().hex, "standalone:" + uuid4().hex):
                return dispatch()

        invoke.__signature__ = signature.replace(parameters=[
            *[p.replace(annotation=hints.get(p.name, p.annotation)) for p in signature.parameters.values()],
            inspect.Parameter("runtime", inspect.Parameter.KEYWORD_ONLY, default=None, annotation=ToolRuntime),
        ], return_annotation=hints.get("return", signature.return_annotation))
        invoke.__annotations__ = {**hints, "runtime": ToolRuntime}
        return tool(invoke)
    return decorate


async def reconcile_receipts(context, agent, config):
    """Restore known committed results before generic dangling-call repair.

    Replace the ordered message list, rather than appending a result after later
    human/AI messages. Keep all original message ids and checkpoint keys.
    """
    from langchain_core.messages import AIMessage, ToolMessage, RemoveMessage
    from langgraph.graph.message import REMOVE_ALL_MESSAGES

    run = current_run()
    if not run or run.user_id != context.user_id:
        raise PermissionError("Reconciliation requires its authenticated run scope")
    state = await agent.aget_state(config)
    messages = (state.values or {}).get("messages", []) if state else []
    answered = {m.tool_call_id for m in messages if isinstance(m, ToolMessage)}
    restored = []
    count = 0
    for message in messages:
        restored.append(message)
        if not isinstance(message, AIMessage):
            continue
        for call in message.tool_calls or []:
            if call.get("id") in answered:
                continue
            row = run.storage._con.execute(
                "SELECT command, argument_digest, result_json FROM agent_operation_receipts "
                "WHERE user_id = ? AND thread_key = ? AND operation_id = ?",
                [run.user_id, run.thread_key, call.get("id")],
            ).fetchone()
            if not row:
                continue
            if row[0] != call.get("name") or row[1] != argument_digest(call.get("args") or {}):
                raise OperationConflict("Checkpoint tool arguments do not match committed receipt")
            result = json.loads(row[2])
            restored.append(ToolMessage(content=result if isinstance(result, str) else _json(result),
                                        tool_call_id=call["id"], name=call["name"]))
            count += 1
    if count:
        await agent.aupdate_state(config, {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *restored]}, as_node="tools")
    return count


@dataclass(frozen=True)
class PreparedCall:
    user_id: str
    call_id: str
    command: str
    arguments: dict


_prepared: ContextVar[PreparedCall | None] = ContextVar("prepared_tool_call", default=None)


def prepared_storage(storage):
    """Network lookup runs outside the writer lock; only its save is receipted."""
    call = _prepared.get()
    if call is None:
        return storage

    class Storage:
        def __getattr__(self, name):
            return getattr(storage, name)

        def track_activity(self, user_id, **fields):
            if user_id != call.user_id:
                raise PermissionError("Prepared command tenant mismatch")
            def save():
                _validate_references(storage, user_id, fields)
                identity = storage.track_activity(user_id, **fields)
                # Local lifecycle writes belong in the same transaction.
                from app.cos import lifecycle
                lifecycle.on_created(storage, user_id, identity, fields.get("status"))
                return {"entity_id": identity, "outcome": "Activity saved"}
            result = execute(user_id, call.call_id, call.command, call.arguments, save)
            return result["entity_id"]
    return Storage()


def prepared_tool(user_id: str):
    """Variant for lookup-and-save: receipt only the local prepared mutation."""
    def decorate(fn):
        signature = inspect.signature(fn)
        hints = get_type_hints(fn)
        @wraps(fn)
        def invoke(*args, runtime=None, **kwargs):
            arguments = _tool_arguments(runtime, dict(signature.bind(*args, **kwargs).arguments))
            call = PreparedCall(user_id, getattr(runtime, "tool_call_id", None) or uuid4().hex,
                                fn.__name__, arguments)
            def perform():
                storage = storage_for(user_id)
                with storage.transaction():
                    storage.assert_family_writable(user_id, current_run().generation)
                token = _prepared.set(call)
                try:
                    return fn(*args, **kwargs)
                finally:
                    _prepared.reset(token)
            if current_run() is not None:
                return perform()
            with run_scope(storage_for(user_id), user_id, uuid4().hex, "standalone:" + uuid4().hex):
                return perform()
        invoke.__signature__ = signature.replace(parameters=[
            *[p.replace(annotation=hints.get(p.name, p.annotation)) for p in signature.parameters.values()],
            inspect.Parameter("runtime", inspect.Parameter.KEYWORD_ONLY, default=None, annotation=ToolRuntime),
        ], return_annotation=hints.get("return", signature.return_annotation))
        invoke.__annotations__ = {**hints, "runtime": ToolRuntime}
        return tool(invoke)
    return decorate
