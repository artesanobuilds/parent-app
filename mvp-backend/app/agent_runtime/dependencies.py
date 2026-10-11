"""Lifespan binding without importing the FastAPI application from the runtime."""
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class RuntimeDependencies:
    storage: Any
    profiles: Any
    chat_memory: Any
    onboarding_memory: Any
    coach_threads: Any

_dependencies: RuntimeDependencies | None = None

def bind(dependencies: RuntimeDependencies) -> None:
    global _dependencies
    _dependencies = dependencies

def get() -> RuntimeDependencies:
    if _dependencies is None:
        raise RuntimeError("Agent runtime dependencies have not been bound by lifespan")
    return _dependencies
