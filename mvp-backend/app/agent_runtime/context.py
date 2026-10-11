"""Trusted admission data, never populated from model arguments."""
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class RunContext:
    user_id: str
    surface: str
    thread_key: str
    conversation_id: str | None = None
    run_id: str = field(default_factory=lambda: uuid4().hex)


# Task-local trusted context propagates into LangChain's tool worker contexts.
# No tool schema exposes these fields to a model.
from contextlib import contextmanager
from contextvars import ContextVar

_current_run: ContextVar[RunContext | None] = ContextVar("agent_run", default=None)


def current_run() -> RunContext | None:
    return _current_run.get()


@contextmanager
def bind_run(context: RunContext):
    token = _current_run.set(context)
    try:
        yield
    finally:
        _current_run.reset(token)
