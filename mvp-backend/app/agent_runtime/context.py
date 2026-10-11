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
