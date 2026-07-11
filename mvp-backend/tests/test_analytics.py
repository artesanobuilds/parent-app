"""Analytics + flags (app/analytics). Verifies the env-gated no-op default, the
event allowlist + PII denylist, and the flag facade's env-override/fallback.
No PostHog network — with no POSTHOG_API_KEY the client is None (hermetic)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

import app.analytics as analytics  # noqa: E402
from app.analytics import events, flags  # noqa: E402


def test_disabled_by_default_is_noop():
    # No POSTHOG_API_KEY → client None → capture/identify are silent no-ops.
    assert analytics._client is None
    analytics.capture("login_succeeded", "user-x", {"provider": "apple"})  # must not raise
    analytics.identify("user-x", {"foo": "bar"})


def test_init_returns_false_without_key(monkeypatch):
    monkeypatch.delenv("POSTHOG_API_KEY", raising=False)
    assert analytics.init_analytics() is False


def test_unknown_event_dropped_or_raised(monkeypatch):
    # Prod: unknown events are dropped silently.
    monkeypatch.setattr(analytics, "_STRICT", False)
    analytics.capture("not_a_real_event", "user-x")  # no raise
    # Strict (tests): unknown events raise so mistakes are caught pre-ship.
    monkeypatch.setattr(analytics, "_STRICT", True)
    with pytest.raises(KeyError):
        analytics.capture("not_a_real_event", "user-x")


def test_allowlist_strips_unlisted_and_denylisted_props():
    # kid_chat_message_sent allows only {agent_id}; content/kid_name must vanish.
    out = events.sanitize("kid_chat_message_sent", {
        "agent_id": "a1", "content": "secret transcript", "kid_name": "Nova", "extra": 1,
    })
    assert out == {"agent_id": "a1"}


def test_denylist_never_survives_even_if_somehow_allowlisted():
    # Guard: no event may list a denylisted key. If one ever does, sanitize
    # would still strip it (denylist wins) AND this asserts the taxonomy is clean.
    for event, allowed in events.EVENTS.items():
        leaked = allowed & events.DENYLIST
        assert not leaked, f"event {event!r} allows denylisted keys {leaked}"


def test_flag_env_override_wins(monkeypatch):
    monkeypatch.setenv("FLAG_KID_CHAT_DISABLED", "1")
    assert flags.is_enabled("kid_chat_disabled", default=False) is True
    monkeypatch.setenv("FLAG_KID_CHAT_DISABLED", "0")
    assert flags.is_enabled("kid_chat_disabled", default=True) is False


def test_flag_falls_back_to_default_when_disabled(monkeypatch):
    monkeypatch.delenv("FLAG_SOME_FLAG", raising=False)
    # client is None → returns the provided default.
    assert flags.is_enabled("some_flag", default=True) is True
    assert flags.is_enabled("some_flag", default=False) is False
