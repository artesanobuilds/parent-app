"""
Thin httpx wrapper used by FlowContext.

We expose only the verbs the harness uses, with a single auth dispatch knob
(`as_=...`) — that's how flow tests stay readable and how generated tests
stay uniform across personas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx


# Sentinel persona values. The real Parent/Admin/Kid dataclasses live in
# lib/personas/ — they expose .token (parents) or .admin_token / .pin so this
# wrapper can stay persona-agnostic.
ANONYMOUS = "anonymous"


@dataclass
class HttpClient:
    base_url: str
    timeout: float = 30.0
    readonly: bool = False
    _client: Optional[httpx.Client] = None

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            # Don't follow redirects by default; the harness asserts exact
            # status codes and following hides redirects.
            follow_redirects=False,
        )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    # ── HTTP verbs ───────────────────────────────────────────────────

    def get(self, path: str, *, as_: Any = ANONYMOUS, params: dict | None = None) -> httpx.Response:
        return self._client.get(path, headers=self._headers(as_), params=params)

    def post(self, path: str, *, json: dict | None = None, as_: Any = ANONYMOUS) -> httpx.Response:
        self._enforce_readonly("POST", path)
        return self._client.post(path, json=json, headers=self._headers(as_))

    def put(self, path: str, *, json: dict | None = None, as_: Any = ANONYMOUS) -> httpx.Response:
        self._enforce_readonly("PUT", path)
        return self._client.put(path, json=json, headers=self._headers(as_))

    def patch(self, path: str, *, json: dict | None = None, as_: Any = ANONYMOUS) -> httpx.Response:
        self._enforce_readonly("PATCH", path)
        return self._client.patch(path, json=json, headers=self._headers(as_))

    def delete(self, path: str, *, as_: Any = ANONYMOUS) -> httpx.Response:
        self._enforce_readonly("DELETE", path)
        return self._client.delete(path, headers=self._headers(as_))

    # ── Internals ────────────────────────────────────────────────────

    def _headers(self, as_: Any) -> dict[str, str]:
        if as_ is ANONYMOUS or as_ == ANONYMOUS:
            return {}
        # Parent persona: has a bearer token
        token = getattr(as_, "token", None)
        if token:
            return {"Authorization": f"Bearer {token}"}
        # Admin persona: has an admin_token
        admin_token = getattr(as_, "admin_token", None)
        if admin_token:
            return {"X-Admin-Token": admin_token}
        # Otherwise: anonymous
        return {}

    def _enforce_readonly(self, verb: str, path: str) -> None:
        if not self.readonly:
            return
        raise RuntimeError(
            f"READONLY env refused {verb} {path}. Production runs are read-only; "
            "wrap write-side flows with @pytest.mark.skipif(env.readonly, ...)."
        )
