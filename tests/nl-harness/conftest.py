"""
Shared pytest fixtures for the NL test harness.

Responsibilities:
- Source the right `.env.<env>` file once per session
- Pre-flight: ensure `BASE_URL/health` is reachable before any test runs
- Provide `flow_ctx`, `new_parent`, `existing_parent`, `kid_agent_parent`,
  `admin` fixtures
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterator

import pytest

# Ensure `lib/` is importable from tests no matter where pytest is invoked.
HARNESS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(HARNESS_ROOT))

from lib.client import HttpClient  # noqa: E402
from lib.flow_context import FlowContext  # noqa: E402
from lib.personas import (  # noqa: E402
    new_parent as _new_parent,
    existing_parent as _existing_parent,
    kid_agent_parent as _kid_agent_parent,
    admin as _admin,
)
from lib.services import EnvConfig, load_env  # noqa: E402


# ── Environment loading ────────────────────────────────────────────────


def _load_dotenv_for(env_name: str) -> None:
    """
    Load `.env.<env>` from the harness root. Pure stdlib — avoids the
    python-dotenv runtime dependency for the common case (and keeps the env
    file the source of truth). Values already in os.environ win.
    """
    dotenv_path = HARNESS_ROOT / f".env.{env_name}"
    if not dotenv_path.exists():
        return
    with open(dotenv_path) as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


@pytest.fixture(scope="session")
def env() -> EnvConfig:
    env_name = os.environ.get("ENVIRONMENT", "local")
    _load_dotenv_for(env_name)
    cfg = load_env()
    return cfg


@pytest.fixture(scope="session", autouse=True)
def _backend_health_check(env: EnvConfig) -> None:
    """
    Fail loudly if the backend isn't reachable before running any flow.
    The default 5-second timeout matches uvicorn cold start.
    """
    import httpx
    try:
        resp = httpx.get(f"{env.base_url}/health", timeout=5.0)
    except Exception as exc:
        pytest.exit(
            f"\n[nl-harness] backend health check failed against {env.base_url}/health: {exc}\n"
            f"Start the backend (cd mvp-backend && uvicorn app.server:app --reload --port 8904) "
            f"or set BASE_URL to a reachable instance.",
            returncode=2,
        )
    if resp.status_code != 200:
        pytest.exit(
            f"\n[nl-harness] {env.base_url}/health returned {resp.status_code}: {resp.text[:200]}",
            returncode=2,
        )


@pytest.fixture(scope="session")
def consent_agreement_version(env: EnvConfig) -> str:
    """
    Probe the backend's current CONSENT_AGREEMENT_VERSION once per session.
    The backend mismatch response is structured:
      {"error": "agreement_version_mismatch", "required_version": "<value>"}
    so we hit /consent/submit with a deliberately-wrong sentinel and read
    `required_version` from the error body. Falls back to the env default
    if the probe can't decode (e.g. the contract changed shape).

    Why probe instead of hardcoding: the version string bumps with every
    legal/consent revision; we don't want the whole suite to break on a
    version bump in production. The flow specs reason about the version
    as "whatever the backend currently requires", not a specific string.
    """
    import httpx
    fallback = env.consent_agreement_version

    # We need ANY bearer token to even hit /consent/submit (it's behind
    # current_user). Mint one for a throwaway user; rate-limited but fine
    # at session scope.
    try:
        tok_resp = httpx.post(
            f"{env.base_url}/auth/issue-token",
            json={"user_id": "nl-harness-version-probe"},
            timeout=5.0,
        )
        if tok_resp.status_code != 200:
            return fallback
        token = tok_resp.json()["token"]

        probe = httpx.post(
            f"{env.base_url}/consent/submit",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "parent_name": "probe",
                "parent_email": "probe@example.com",
                "kid_age_band": "3-5",
                "agreement_version": "__nl_harness_intentionally_wrong__",
            },
            timeout=5.0,
        )
        if probe.status_code == 400:
            body = probe.json()
            required = body.get("required_version")
            if isinstance(required, str) and required:
                return required
    except Exception:
        pass
    return fallback


# ── Per-test context ──────────────────────────────────────────────────


@pytest.fixture
def flow_ctx(env: EnvConfig, consent_agreement_version: str) -> Iterator[FlowContext]:
    client = HttpClient(base_url=env.base_url, readonly=env.readonly)
    ctx = FlowContext(
        env=env,
        client=client,
        _consent_agreement_version_override=consent_agreement_version,
    )
    try:
        yield ctx
    finally:
        ctx.cleanup()
        client.close()


# ── Persona fixtures ──────────────────────────────────────────────────


@pytest.fixture
def new_parent(flow_ctx: FlowContext):
    if flow_ctx.readonly:
        pytest.skip("new_parent requires write access; production runs are read-only")
    return _new_parent(flow_ctx)


@pytest.fixture
def existing_parent(flow_ctx: FlowContext):
    if flow_ctx.readonly:
        pytest.skip("existing_parent requires write access; production runs are read-only")
    return _existing_parent(flow_ctx)


@pytest.fixture
def kid_agent_parent(flow_ctx: FlowContext):
    if flow_ctx.readonly:
        pytest.skip("kid_agent_parent requires write access; production runs are read-only")
    if not flow_ctx.env.run_kid_agent_flows:
        pytest.skip("RUN_KID_AGENT_FLOWS=false in this environment")
    return _kid_agent_parent(flow_ctx)


@pytest.fixture(scope="session")
def _backend_admin_enabled(env: EnvConfig) -> bool:
    """
    Probe the backend once per session to see whether it has ADMIN_TOKEN set.
    The backend returns 503 ("admin endpoints disabled") when ADMIN_TOKEN is
    unset, regardless of what the client sends — different from the 401 you
    get when the token IS set but missing/wrong. Admin tests need to skip on
    503 (a config issue, not a regression) but still run on 401 (the actual
    gate behavior they want to verify).
    """
    import httpx
    try:
        resp = httpx.get(f"{env.base_url}/data/export", timeout=5.0)
    except Exception:
        return False
    return resp.status_code != 503


@pytest.fixture
def admin(flow_ctx: FlowContext, _backend_admin_enabled: bool):
    if not flow_ctx.env.admin_token:
        pytest.skip("ADMIN_TOKEN not set in the harness env; admin flows skipped")
    if not _backend_admin_enabled:
        pytest.skip(
            "Backend has ADMIN_TOKEN unset (returns 503 on admin paths). "
            "Set ADMIN_TOKEN on the backend's .env to the same value as the "
            "harness's ADMIN_TOKEN to exercise admin flows."
        )
    return _admin(flow_ctx)
