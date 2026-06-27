"""
Fault-injection control for flow tests — the parent-app analog of the NL-Harness
Playbook's §4.8 `ctx.fault()` (which drove Toxiproxy). Here it toggles the mock
OpenAI server's failure mode over its control endpoint, so a flow can make a real
dependency "fail" as a first-class test scenario and assert graceful degradation
+ recovery.

Usage in a flow test (mirrors the playbook):
    flow_ctx.fault("openai", "rate_limit", count=2)   # next 2 model calls 429, then heal
    flow_ctx.fault("openai", "down")                  # outage until reset
    flow_ctx.fault.reset()                            # back to healthy
    state = flow_ctx.fault.state()                    # {mode, call_count, fault_count, ...}

`available` is False when OPENAI_MOCK_CONTROL_URL is unset — fault flows skip
cleanly outside the orchestrated fault-test environment (tools/run-fault-flows.sh).
"""
from __future__ import annotations

from typing import Optional

import httpx

_SUPPORTED = ("openai",)


class FaultController:
    def __init__(self, control_url: Optional[str]) -> None:
        # e.g. http://127.0.0.1:9099/__fault__
        self._url = control_url

    @property
    def available(self) -> bool:
        return bool(self._url)

    def _require(self) -> str:
        if not self._url:
            raise RuntimeError(
                "fault injection unavailable: OPENAI_MOCK_CONTROL_URL is unset "
                "(run via tools/run-fault-flows.sh)"
            )
        return self._url

    def inject(
        self, target: str, mode: str, *, count: Optional[int] = None, latency_ms: int = 0
    ) -> dict:
        url = self._require()
        if target not in _SUPPORTED:
            raise ValueError(f"unsupported fault target {target!r} (supported: {_SUPPORTED})")
        body: dict = {"mode": mode}
        if count is not None:
            body["count"] = count
        if latency_ms:
            body["latency_ms"] = latency_ms
        return httpx.post(url, json=body, timeout=5.0).json()

    # Callable form so tests read like the playbook: flow_ctx.fault("openai", "down")
    def __call__(self, target: str, mode: str, **opts) -> dict:
        return self.inject(target, mode, **opts)

    def reset(self, target: str = "openai") -> dict:
        url = self._require()
        reset_url = url.rsplit("/__fault__", 1)[0] + "/__reset__"
        return httpx.post(reset_url, timeout=5.0).json()

    def state(self) -> dict:
        url = self._require()
        return httpx.get(url, timeout=5.0).json()
