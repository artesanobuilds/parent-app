"""
Service / environment registry.

Parent-app is a single-service topology — there is one backend on one base URL,
varying by environment. This module centralizes the lookup so flow tests
never hardcode a URL.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class EnvConfig:
    name: str
    base_url: str
    readonly: bool
    admin_token: str | None
    consent_agreement_version: str
    user_id_prefix: str
    run_kid_agent_flows: bool
    run_openai_flows: bool


def load_env() -> EnvConfig:
    """
    Build an EnvConfig from process env. Caller is responsible for sourcing
    the right .env file (conftest does this once per session).
    """
    env_name = os.getenv("ENVIRONMENT", "local")
    base_url = os.getenv("BASE_URL")
    if not base_url:
        raise RuntimeError(
            "BASE_URL is not set. Source tests/nl-harness/.env.<env> or set "
            "BASE_URL=... before running pytest."
        )
    readonly = os.getenv("READONLY", "false").lower() in ("1", "true", "yes")
    return EnvConfig(
        name=env_name,
        base_url=base_url.rstrip("/"),
        readonly=readonly,
        admin_token=os.getenv("ADMIN_TOKEN"),
        consent_agreement_version=os.getenv(
            "CONSENT_AGREEMENT_VERSION", "2026-04-01-v1"
        ),
        user_id_prefix=os.getenv("USER_ID_PREFIX", "nl-harness"),
        run_kid_agent_flows=os.getenv("RUN_KID_AGENT_FLOWS", "true").lower()
        in ("1", "true", "yes"),
        run_openai_flows=os.getenv("RUN_OPENAI_FLOWS", "false").lower()
        in ("1", "true", "yes"),
    )
