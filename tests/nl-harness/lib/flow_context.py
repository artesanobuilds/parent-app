"""
Per-test session object exposed to every flow test as `flow_ctx`.

Responsibilities:
- Wrap the HTTP client so flows can call `ctx.post(...)`, `ctx.get(...)` etc.
- Track entities the test created (community posts, kid agents, family rows)
  so `ctx.cleanup()` reverses them in LIFO order at teardown.
- Provide `wait_for(...)` for eventually-consistent assertions (e.g. crisis
  lock landing in DuckDB after a kid-chat SSE event).
- Expose env constants (consent_agreement_version, base_url) so generated
  tests stay environment-portable.

Explicitly NOT here:
- Persona resolution (lives in lib/personas/)
- SSE handling (lives in lib/sse.py)
- Schema validation patterns (left to the generated test — use pydantic or
  dict-key assertions inline, as the contract dictates)
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import httpx

from .client import ANONYMOUS, HttpClient
from .services import EnvConfig

logger = logging.getLogger(__name__)


@dataclass
class _CleanupAction:
    description: str
    fn: Callable[[], None]


@dataclass
class FlowContext:
    env: EnvConfig
    client: HttpClient
    # If set, used in place of env.consent_agreement_version. Populated by
    # conftest from a session-scoped probe against /consent/submit so the
    # harness auto-tracks backend version bumps. Falls through to env if None.
    _consent_agreement_version_override: Optional[str] = None
    _cleanups: list[_CleanupAction] = field(default_factory=list)
    _state: dict[str, Any] = field(default_factory=dict)

    # ── HTTP verb passthrough ────────────────────────────────────────

    def get(self, path: str, *, as_: Any = ANONYMOUS, params: dict | None = None) -> httpx.Response:
        return self.client.get(path, as_=as_, params=params)

    def post(self, path: str, *, json: dict | None = None, as_: Any = ANONYMOUS) -> httpx.Response:
        return self.client.post(path, json=json, as_=as_)

    def put(self, path: str, *, json: dict | None = None, as_: Any = ANONYMOUS) -> httpx.Response:
        return self.client.put(path, json=json, as_=as_)

    def delete(self, path: str, *, as_: Any = ANONYMOUS) -> httpx.Response:
        return self.client.delete(path, as_=as_)

    # ── Environment constants ────────────────────────────────────────

    @property
    def consent_agreement_version(self) -> str:
        return (
            self._consent_agreement_version_override
            if self._consent_agreement_version_override is not None
            else self.env.consent_agreement_version
        )

    @property
    def base_url(self) -> str:
        return self.env.base_url

    @property
    def readonly(self) -> bool:
        return self.env.readonly

    # ── Cleanup tracking ─────────────────────────────────────────────

    def register_cleanup(self, description: str, fn: Callable[[], None]) -> None:
        """
        Record a teardown action. Cleanups run in LIFO order from cleanup().
        Use this whenever a flow creates a server-side entity it should
        reverse — community posts, kid agent configs, family rows.
        """
        self._cleanups.append(_CleanupAction(description=description, fn=fn))

    def cleanup(self) -> None:
        # LIFO: last created, first cleaned. Mirrors a stack of resources.
        while self._cleanups:
            action = self._cleanups.pop()
            try:
                action.fn()
            except Exception as exc:
                logger.warning("[flow-ctx] cleanup failed: %s: %s", action.description, exc)

    # ── Shared state between steps in a flow ─────────────────────────

    def store(self, key: str, value: Any) -> None:
        self._state[key] = value

    def retrieve(self, key: str) -> Any:
        return self._state[key]

    # ── Eventual-consistency polling ─────────────────────────────────

    def wait_for(
        self,
        condition: Callable[[], bool],
        *,
        timeout_s: float = 15.0,
        interval_s: float = 0.5,
        fail_if: Optional[Callable[[], bool]] = None,
        description: str = "condition",
    ) -> bool:
        """
        Poll `condition()` until it returns True or `timeout_s` elapses.
        If `fail_if()` returns True at any point, short-circuit and raise —
        useful when polling for a 'success' state and a 'terminal error'
        state would otherwise force a full timeout wait.
        """
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if fail_if is not None and fail_if():
                raise AssertionError(
                    f"wait_for({description}): hit terminal failure state before condition was True"
                )
            if condition():
                return True
            time.sleep(interval_s)
        raise AssertionError(
            f"wait_for({description}): timed out after {timeout_s}s"
        )
