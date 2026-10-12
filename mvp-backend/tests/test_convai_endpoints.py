"""ElevenLabs ConvAI Custom-LLM endpoints — the two voice surfaces.

`/v1/chat/completions` (kid, app/convai_endpoint.py) and
`/v1/parent/chat/completions` (parent, app/parent_convai_endpoint.py) are the
ONLY code path a live voice turn takes. ElevenLabs does STT/turn-taking/TTS and
POSTs us OpenAI-shaped requests; whatever we stream back is what the kid or
parent HEARS. There is no client-side second chance — a malformed chunk, a URL
that reaches TTS, or a crisis lock that doesn't fire is audible immediately.

Everything here is hermetic: no OpenAI, no ElevenLabs, no network. We fake the
agent (a scripted `astream_events`) and the two moderation LLM calls, and keep
the REAL StreamingModerator, link stripper, storage and SSE framing — those are
the parts worth testing.

TestClient idiom: a TestClient context exit closes the shared storage singleton,
so the module fixture rebuilds `server.storage_backend` BEFORE and AFTER (same
as tests/test_auth_v2.py). Without that, later test modules die with
"Connection already closed".
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import anyio
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "convai.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.testclient import TestClient  # noqa: E402
from langchain_core.messages import AIMessage  # noqa: E402

import app.convai_endpoint as convai  # noqa: E402
import app.kid_agent as kid_agent_service  # noqa: E402
import app.moderation as moderation  # noqa: E402
import app.parent_convai_endpoint as parent_convai  # noqa: E402
import app.server as server  # noqa: E402
import app.telemetry as telemetry  # noqa: E402

SECRET = "convai-test-secret"

KID_PATH = "/v1/chat/completions"
PARENT_PATH = "/v1/parent/chat/completions"


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def client():
    from app.duckdb_storage import DuckDBStorage
    # A prior module's TestClient may have closed the shared storage singleton;
    # rebuild it before entering our own lifespan (and again on exit).
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)
    with TestClient(server.app) as c:
        yield c
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


@pytest.fixture
def secret(monkeypatch):
    """Arm the shared secret on BOTH endpoints. The parent module copies
    CONVAI_SECRET into its own namespace at import, so patching one is not
    enough — that asymmetry is exactly how a half-configured deploy would 401
    only one surface."""
    monkeypatch.setattr(convai, "CONVAI_SECRET", SECRET)
    monkeypatch.setattr(parent_convai, "CONVAI_SECRET", SECRET)
    return SECRET


@pytest.fixture
def hermetic(monkeypatch):
    """Cut every outbound call the moderation pipeline would make.

    `moderate_with_openai` fails CLOSED on error, so leaving it live would turn
    every test into a "blocked" assertion against a network timeout. The cheap
    crisis regex (`scan_for_crisis`) stays REAL — it is the safety gate the
    crisis tests are actually about.
    """
    from app.moderation import ModerationResult
    from app.moderation import _AgeAppropriateVerdict

    def _clean(text: str) -> ModerationResult:
        return ModerationResult(
            flagged=False, severity="low", category="ok",
            reason="stubbed clean", suggested_action="allow",
        )

    def _age_ok(text, age_band, **kwargs):
        return _AgeAppropriateVerdict(age_appropriate=True, confidence=1.0, concern="")

    monkeypatch.setattr(moderation, "moderate_with_openai", _clean)
    monkeypatch.setattr(moderation, "classify_age_appropriate", _age_ok)
    async def async_clean(text):
        return moderation.moderate_with_openai(text)

    async def async_age(text, age_band, **kwargs):
        return moderation.classify_age_appropriate(text, age_band, **kwargs)

    monkeypatch.setattr(moderation, "amoderate_with_openai", async_clean)
    monkeypatch.setattr(moderation, "aclassify_age_appropriate", async_age)

    # A dev .env may set the Slack webhook; a crisis test must not page anyone.
    monkeypatch.setattr(telemetry, "SLACK_WEBHOOK_URL", "", raising=False)


# ── Test doubles ─────────────────────────────────────────────────────────────

TOOL_START = object()  # sentinel: script an `on_tool_start` event


class _Chunk:
    """Stands in for a LangChain AIMessageChunk — the endpoints only read
    `.content`, and only care whether it's a str (spoken text) or a list
    (tool-call content blocks, which must be skipped)."""

    def __init__(self, content: Any) -> None:
        self.content = content


class _FakeAgent:
    """Scripted LangGraph agent.

    `script` is a list of str (streamed model content), TOOL_START sentinels, or
    raw content values (list/None) to exercise the non-str skip. `raise_on_attempt`
    makes `astream_events` blow up BEFORE its first yield, which is the
    "poisoned thread, nothing streamed yet" case the parent endpoint retries.
    """

    def __init__(
        self,
        script: List[Any],
        *,
        raise_on_attempt: Optional[int] = None,
        error: Optional[BaseException] = None,
        state_messages: Optional[List[Any]] = None,
    ) -> None:
        self._script = script
        self._raise_on_attempt = raise_on_attempt
        self._error = error or RuntimeError(
            "Invalid parameter: messages with role 'tool' ... an assistant message "
            "with 'tool_calls' must be followed by tool messages responding to each "
            "tool_call_id"
        )
        self._state_messages = state_messages or []
        self.attempts = 0
        self.state_reads = 0
        self.state_updates = 0

    async def astream_events(self, inputs, config=None, version=None):
        self.attempts += 1
        # v2 is the cheap event API; v1 builds a much heavier payload per token
        # on a hot voice path. A silent regression to v1 costs audible ms.
        assert version == "v2", f"endpoint must request astream_events v2, got {version!r}"
        if self._raise_on_attempt == self.attempts:
            raise self._error
        for item in self._script:
            if item is TOOL_START:
                yield {"event": "on_tool_start", "data": {}}
                continue
            yield {"event": "on_chat_model_stream", "data": {"chunk": _Chunk(item)}}

    async def aget_state(self, config):
        self.state_reads += 1
        return SimpleNamespace(values={"messages": list(self._state_messages)})

    async def aupdate_state(self, config, values, as_node=None):
        self.state_updates += 1


def _kid_config(agent_id: str, *, enabled: bool = True) -> Dict[str, Any]:
    return {"id": agent_id, "enabled": enabled, "invariants": {}, "version": 1}


def _install_kid_agent(monkeypatch, agent: Any, config: Dict[str, Any]) -> None:
    monkeypatch.setattr(
        kid_agent_service, "get_kid_agent", lambda user_id, kid_name, **kwargs: (agent, config)
    )


def _install_parent_agent(monkeypatch, agent: Any) -> None:
    monkeypatch.setattr(parent_convai, "get_agent", lambda user_id: agent)


# ── SSE helpers ──────────────────────────────────────────────────────────────


def _payloads(body: str) -> List[Any]:
    """Decode an OpenAI SSE body into [dict, ..., '[DONE]']."""
    out: List[Any] = []
    for block in body.split("\n\n"):
        line = block.strip()
        if not line.startswith("data:"):
            continue
        raw = line[len("data:"):].strip()
        out.append(raw if raw == "[DONE]" else json.loads(raw))
    return out


def _content_deltas(payloads: List[Any]) -> List[Dict[str, Any]]:
    return [
        p for p in payloads
        if isinstance(p, dict) and "content" in p["choices"][0]["delta"]
    ]


def _spoken(payloads: List[Any]) -> str:
    return "".join(p["choices"][0]["delta"]["content"] for p in _content_deltas(payloads))


def _tool_deltas(payloads: List[Any]) -> List[Dict[str, Any]]:
    return [
        p for p in payloads
        if isinstance(p, dict) and "tool_calls" in p["choices"][0]["delta"]
    ]


def _tool_names(payloads: List[Any]) -> List[str]:
    return [
        tc["function"]["name"]
        for p in _tool_deltas(payloads)
        for tc in p["choices"][0]["delta"]["tool_calls"]
    ]


def _kid_body(*, message: str = "hi", extra: Optional[Dict[str, Any]] = None,
              omit_extra: bool = False) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": message}],
        "stream": True,
    }
    if not omit_extra:
        body["elevenlabs_extra_body"] = extra if extra is not None else {}
    return body


# ═════════════════════════════════════════════════════════════════════════════
# Connection probe + auth + request validation
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("path", [KID_PATH, PARENT_PATH])
def test_bare_probe_streams_stub_without_spinning_up_an_agent(
    client, secret, monkeypatch, path
):
    """ElevenLabs' console "Test connection" sends a bare OpenAI request with no
    elevenlabs_extra_body. It must get a valid stub stream — building an agent
    (or running moderation) for a health check would make the console probe
    spend money and time out."""
    def _boom(*a, **kw):  # pragma: no cover — asserts it's never reached
        raise AssertionError("probe must not build an agent")

    monkeypatch.setattr(kid_agent_service, "get_kid_agent", _boom)
    monkeypatch.setattr(parent_convai, "get_agent", _boom)

    res = client.post(
        path,
        json=_kid_body(omit_extra=True),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    payloads = _payloads(res.text)
    assert _spoken(payloads) == "OK"
    assert payloads[-1] == "[DONE]"


@pytest.mark.parametrize("path", [KID_PATH, PARENT_PATH])
def test_legacy_secret_header_is_accepted(client, secret, monkeypatch, path):
    """Both console configuration paths must authenticate: the Custom-LLM "API
    key" field arrives as `Authorization: Bearer`, our original wiring used
    X-ElevenLabs-Secret. Dropping either silently kills one agent."""
    monkeypatch.setattr(kid_agent_service, "get_kid_agent", lambda *a, **k: None)
    res = client.post(
        path,
        json=_kid_body(omit_extra=True),
        headers={"X-ElevenLabs-Secret": secret},
    )
    assert res.status_code == 200, res.text
    assert _spoken(_payloads(res.text)) == "OK"


@pytest.mark.parametrize("path", [KID_PATH, PARENT_PATH])
@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer wrong-secret"},
        {"X-ElevenLabs-Secret": "wrong-secret"},
        {"Authorization": f"Basic {SECRET}"},  # right value, wrong scheme
    ],
)
def test_bad_or_missing_secret_is_401(client, secret, path, headers):
    res = client.post(path, json=_kid_body(omit_extra=True), headers=headers)
    assert res.status_code == 401, res.text


@pytest.mark.parametrize("path", [KID_PATH, PARENT_PATH])
def test_unset_server_secret_rejects_everything(client, monkeypatch, path):
    """An unconfigured deploy must be closed, not open. `CONVAI_SECRET == ""`
    would make `presented != CONVAI_SECRET` false for a caller sending nothing."""
    monkeypatch.setattr(convai, "CONVAI_SECRET", "")
    monkeypatch.setattr(parent_convai, "CONVAI_SECRET", "")
    res = client.post(path, json=_kid_body(omit_extra=True))
    assert res.status_code == 401
    res = client.post(path, json=_kid_body(omit_extra=True),
                      headers={"Authorization": "Bearer "})
    assert res.status_code == 401


@pytest.mark.parametrize(
    "extra",
    [
        {"user_id": "u-1"},              # kid_name missing
        {"kid_name": "Ada"},             # user_id missing
        {"thread_id": "t-1"},            # neither
    ],
)
def test_kid_extra_body_present_but_incomplete_is_400(client, secret, extra):
    """An extra_body that EXISTS but lacks the session keys is a genuine
    misconfiguration (agent set up with the wrong overrides) — it must 400 loudly
    rather than fall through to the probe stub and pretend to work."""
    res = client.post(
        KID_PATH, json=_kid_body(extra=extra),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 400, res.text
    assert "user_id" in res.json()["detail"] or "kid_name" in res.json()["detail"]


@pytest.mark.parametrize("path", [KID_PATH, PARENT_PATH])
def test_empty_extra_body_falls_through_to_the_probe_stub(client, secret, monkeypatch, path):
    """Pins CURRENT behavior, which diverges from the endpoints' stated intent.

    Both handlers branch on `if not raw_extra:` — and `{}` is falsy — so an
    extra_body that is PRESENT but empty gets the probe stub instead of the 400
    the comment above the branch promises ("a body that *has* an extra_body but
    is missing the session keys is a genuine misconfiguration, so that still
    400s"). In practice that turns a mis-wired agent (overrides configured but
    none resolving) into a cheerful "OK" nobody investigates. Flagged for the
    owning agent; asserted here so a fix is a deliberate change, not a surprise.
    """
    def _boom(*a, **kw):  # pragma: no cover
        raise AssertionError("empty extra_body must not build an agent")

    monkeypatch.setattr(kid_agent_service, "get_kid_agent", _boom)
    monkeypatch.setattr(parent_convai, "get_agent", _boom)

    res = client.post(
        path, json=_kid_body(extra={}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200
    assert _spoken(_payloads(res.text)) == "OK"


@pytest.mark.parametrize("extra", [{"thread_id": "t-1"}, {"kid_name": "Ada"}])
def test_parent_extra_body_present_but_incomplete_is_400(client, secret, extra):
    """The parent agent needs FEWER keys than the kid one (no kid_name — there is
    no kid in the loop), so a parent request carrying only kid_name is still a 400."""
    res = client.post(
        PARENT_PATH, json=_kid_body(extra=extra),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 400, res.text
    assert "user_id" in res.json()["detail"]


def test_parent_accepts_extra_body_without_kid_name(client, secret, monkeypatch, hermetic):
    """Contract guard for the asymmetry above: user_id alone is a COMPLETE parent
    request. If this ever 400s, parent voice is dead."""
    _install_parent_agent(monkeypatch, _FakeAgent(["Hi there."]))
    res = client.post(
        PARENT_PATH, json=_kid_body(extra={"user_id": "u-parent-ok"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    assert _spoken(_payloads(res.text)) == "Hi there."


@pytest.mark.parametrize("path,extra", [
    (KID_PATH, {"user_id": "u-1", "kid_name": "Ada"}),
    (PARENT_PATH, {"user_id": "u-1"}),
])
def test_no_user_message_is_400(client, secret, path, extra):
    res = client.post(
        path,
        json={"messages": [{"role": "system", "content": "you are a coach"}],
              "elevenlabs_extra_body": extra},
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 400, res.text


# ═════════════════════════════════════════════════════════════════════════════
# Kid endpoint — SSE shape, persistence, safety
# ═════════════════════════════════════════════════════════════════════════════


def test_kid_normal_turn_streams_openai_chunks_and_persists(
    client, secret, monkeypatch, hermetic
):
    agent_id = "agent-kid-normal"
    _install_kid_agent(monkeypatch, _FakeAgent(["Hello ", "there, ", "friend!"]),
                       _kid_config(agent_id))

    res = client.post(
        KID_PATH,
        json=_kid_body(message="tell me a joke",
                       extra={"user_id": "u-normal", "kid_name": "Ada",
                              "thread_id": "th-normal"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    assert res.headers["content-type"].startswith("text/event-stream")
    payloads = _payloads(res.text)

    # Frame shape — ElevenLabs parses these as OpenAI chunks; a wrong `object`
    # or a premature finish_reason ends the turn early on their side.
    assert payloads[-1] == "[DONE]"
    for p in payloads[:-1]:
        assert p["object"] == "chat.completion.chunk"
        assert p["id"].startswith("chatcmpl-")
        assert p["choices"][0]["index"] == 0
    for p in _content_deltas(payloads):
        assert p["choices"][0]["finish_reason"] is None

    assert _spoken(payloads) == "Hello there, friend!"
    assert _tool_deltas(payloads) == []

    # Durable transcript: the parent reads this later.
    msgs = server.storage_backend.get_kid_messages(agent_id, "th-normal")
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[0]["content"] == "tell me a joke"
    assert msgs[1]["content"] == "Hello there, friend!"


def test_kid_non_string_chunk_content_is_skipped(client, secret, monkeypatch, hermetic):
    """astream_events v2 delivers tool-call deltas as a LIST of content blocks.
    Concatenating that into the buffer (or feeding it to the moderator) blows up
    mid-turn — the kid hears the error message instead of the answer."""
    agent_id = "agent-kid-blocks"
    script = ["I can ", [{"type": "tool_use", "id": "x"}], None, "help."]
    _install_kid_agent(monkeypatch, _FakeAgent(script), _kid_config(agent_id))

    res = client.post(
        KID_PATH,
        json=_kid_body(extra={"user_id": "u-blocks", "kid_name": "Ada",
                              "thread_id": "th-blocks"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    assert _spoken(_payloads(res.text)) == "I can help."


def test_kid_disabled_agent_refuses_before_any_model_call(
    client, secret, monkeypatch, hermetic
):
    agent_id = "agent-kid-disabled"
    agent = _FakeAgent(["should never be spoken"])
    _install_kid_agent(monkeypatch, agent, _kid_config(agent_id, enabled=False))

    res = client.post(
        KID_PATH,
        json=_kid_body(extra={"user_id": "u-disabled", "kid_name": "Ada"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    assert "grown-up needs to set me up" in _spoken(_payloads(res.text))
    assert agent.attempts == 0


def test_kid_crisis_locked_agent_is_frozen_and_ends_the_call(
    client, secret, monkeypatch, hermetic
):
    """A locked companion must not talk, and must hang up — leaving the call open
    invites the kid to keep trying a companion that will never answer."""
    agent_id = "agent-kid-prelocked"
    storage = server.storage_backend
    storage.lock_kid_agent_for_crisis(
        agent_id=agent_id, user_id="u-prelocked", kid_name="Ada",
        category="self_harm", severity="crisis", reason="prior turn",
    )
    agent = _FakeAgent(["should never be spoken"])
    _install_kid_agent(monkeypatch, agent, _kid_config(agent_id))

    res = client.post(
        KID_PATH,
        json=_kid_body(extra={"user_id": "u-prelocked", "kid_name": "Ada"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    payloads = _payloads(res.text)
    assert "grown-up needs to check in with you" in _spoken(payloads)
    assert _tool_names(payloads) == ["end_call"]
    assert agent.attempts == 0


def test_kid_crisis_input_locks_agent_and_ends_call(client, secret, monkeypatch, hermetic):
    """SAFETY. A crisis disclosure on the way IN must: never reach the model,
    speak the hand-off message, hang up, lock the agent durably, kill it
    in-process, and leave a crisis_routed moderation event for the parent.
    Do not weaken any of these."""
    agent_id = "agent-kid-crisis-in"
    agent = _FakeAgent(["the model must never run"])
    _install_kid_agent(monkeypatch, agent, _kid_config(agent_id))
    storage = server.storage_backend

    res = client.post(
        KID_PATH,
        json=_kid_body(message="sometimes I want to kill myself",
                       extra={"user_id": "u-crisis-in", "kid_name": "Ada",
                              "thread_id": "th-crisis"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    payloads = _payloads(res.text)

    assert "I'm really glad you told me" in _spoken(payloads)
    end_call = _tool_deltas(payloads)
    assert _tool_names(payloads) == ["end_call"]
    # end_call is TERMINAL — finish_reason must be "tool_calls" or ElevenLabs
    # keeps the mic open on a companion that has just been locked.
    assert end_call[0]["choices"][0]["finish_reason"] == "tool_calls"
    assert payloads[-1] == "[DONE]"

    assert agent.attempts == 0, "crisis input must never reach the model"

    lock = storage.is_kid_agent_crisis_locked(agent_id)
    assert lock is not None and lock["severity"] == "crisis"
    assert moderation.is_agent_killed(agent_id) is True

    events = storage.get_moderation_events("u-crisis-in", "Ada")
    assert any(e["action"] == "crisis_routed" and e["severity"] == "crisis"
               for e in events)

    # The kid's own words are still persisted (flagged) — the parent needs them.
    msgs = storage.get_kid_messages(agent_id, "th-crisis")
    assert msgs[0]["role"] == "user" and msgs[0]["parent_flagged"] is True

    moderation.revive_agent(agent_id)  # don't leak the kill into other tests


def test_kid_blocked_input_redirects_without_locking(client, secret, monkeypatch, hermetic):
    """A non-crisis flag is a soft redirect: no lock, no end_call, but a
    blocked_input event so the parent dashboard shows it."""
    from app.moderation import ModerationResult

    agent_id = "agent-kid-blocked-in"
    agent = _FakeAgent(["never spoken"])
    _install_kid_agent(monkeypatch, agent, _kid_config(agent_id))
    monkeypatch.setattr(
        moderation, "moderate_with_openai",
        lambda text: ModerationResult(
            flagged=True, severity="medium", category="violence",
            reason="stubbed flag", suggested_action="block_input",
        ),
    )

    res = client.post(
        KID_PATH,
        json=_kid_body(message="something spicy",
                       extra={"user_id": "u-blocked-in", "kid_name": "Ada"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    payloads = _payloads(res.text)
    assert "I can't help with that part" in _spoken(payloads)
    assert _tool_deltas(payloads) == []
    assert server.storage_backend.is_kid_agent_crisis_locked(agent_id) is None
    assert agent.attempts == 0


def test_kid_blocked_output_swaps_in_replacement_and_ends_call(
    client, secret, monkeypatch, hermetic
):
    """Output moderation firing mid-stream: the kid stops hearing the flagged
    text, gets the redirect, the call ends, and the DURABLE transcript stores the
    replacement (never the unreviewed text)."""
    from app.moderation import ModerationResult

    agent_id = "agent-kid-blocked-out"
    _install_kid_agent(monkeypatch, _FakeAgent(["Nice ", "banana ", "day"]),
                       _kid_config(agent_id))
    # Recheck on every token so the flag lands deterministically on chunk 2
    # instead of after 240 characters of scripted filler.
    monkeypatch.setattr(moderation, "OUTPUT_RECHECK_EVERY_CHARS", 1)
    monkeypatch.setattr(
        moderation, "moderate_with_openai",
        lambda text: ModerationResult(
            flagged=True, severity="medium", category="test_flag",
            reason="banana", suggested_action="block_output",
        ) if "banana" in text else ModerationResult(
            flagged=False, severity="low", category="ok",
            reason="clean", suggested_action="allow",
        ),
    )

    res = client.post(
        KID_PATH,
        json=_kid_body(extra={"user_id": "u-blocked-out", "kid_name": "Ada",
                              "thread_id": "th-blocked-out"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    payloads = _payloads(res.text)
    spoken = _spoken(payloads)

    assert "banana" not in spoken, "flagged text must stop at the gate"
    assert "I can't help with that part" in spoken
    assert _tool_names(payloads) == ["end_call"]
    assert _tool_deltas(payloads)[0]["choices"][0]["finish_reason"] == "tool_calls"

    msgs = server.storage_backend.get_kid_messages(agent_id, "th-blocked-out")
    assistant = [m for m in msgs if m["role"] == "assistant"]
    assert len(assistant) == 1
    assert "I can't help with that part" in assistant[0]["content"]
    assert assistant[0]["parent_flagged"] is True
    assert server.storage_backend.is_kid_agent_crisis_locked(agent_id) is None


def test_kid_crisis_in_output_locks_agent(client, secret, monkeypatch, hermetic):
    """SAFETY. Crisis can also EMERGE from the model. The output gate must lock
    the agent and end the call exactly like the input path."""
    agent_id = "agent-kid-crisis-out"
    _install_kid_agent(
        monkeypatch,
        # The per-token crisis regex runs on the assembled output, so this lands
        # on the second chunk — mid-stream, which is the case that matters.
        _FakeAgent(["I sometimes ", "hurt myself ", "too"]),
        _kid_config(agent_id),
    )
    storage = server.storage_backend

    res = client.post(
        KID_PATH,
        json=_kid_body(extra={"user_id": "u-crisis-out", "kid_name": "Ada",
                              "thread_id": "th-crisis-out"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    payloads = _payloads(res.text)
    assert "I'm really glad you told me" in _spoken(payloads)
    assert _tool_names(payloads) == ["end_call"]

    lock = storage.is_kid_agent_crisis_locked(agent_id)
    assert lock is not None and lock["severity"] == "crisis"
    assert moderation.is_agent_killed(agent_id) is True
    assert any(e["action"] == "crisis_routed"
               for e in storage.get_moderation_events("u-crisis-out", "Ada"))

    moderation.revive_agent(agent_id)


def test_kid_stream_error_speaks_a_recovery_line(client, secret, monkeypatch, hermetic):
    agent_id = "agent-kid-error"
    _install_kid_agent(
        monkeypatch,
        _FakeAgent([], raise_on_attempt=1, error=RuntimeError("model exploded")),
        _kid_config(agent_id),
    )
    res = client.post(
        KID_PATH,
        json=_kid_body(extra={"user_id": "u-error", "kid_name": "Ada"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    payloads = _payloads(res.text)
    assert "Something went wrong" in _spoken(payloads)
    assert payloads[-1] == "[DONE]"


def test_kid_interrupted_turn_still_persists_the_partial_reply(
    client, secret, monkeypatch, hermetic
):
    """REGRESSION for the finally-based persistence guard.

    A barge-in aborts the HTTP request, which throws GeneratorExit into the
    stream generator mid-loop — so neither post-loop persistence branch runs. The
    kid HEARD half a reply and the parent will look for it in the transcript. We
    drive the generator directly and `aclose()` it after two deltas, which is
    exactly what an aborted request does, minus TestClient's teardown timing.
    """
    agent_id = "agent-kid-interrupted"
    _install_kid_agent(monkeypatch, _FakeAgent(["Once ", "upon ", "a ", "time."]),
                       _kid_config(agent_id))
    storage = server.storage_backend

    async def _drive() -> None:
        gen = convai._stream_response("u-interrupted", "Ada", "th-interrupted",
                                      "tell me a story")
        seen = 0
        async for _chunk in gen:
            seen += 1
            if seen == 2:
                break
        await gen.aclose()

    anyio.run(_drive)

    msgs = storage.get_kid_messages(agent_id, "th-interrupted")
    assistant = [m for m in msgs if m["role"] == "assistant"]
    assert len(assistant) == 1, "the interrupted turn vanished from the transcript"
    assert assistant[0]["content"] == "Once upon "


def test_kid_blocked_turn_interrupted_persists_nothing_extra(
    client, secret, monkeypatch, hermetic
):
    """The finally guard must stay silent on a BLOCKED turn — the replacement
    message was never spoken, and re-persisting the raw buffer would put
    unreviewed text in a parent-visible transcript."""
    from app.moderation import ModerationResult

    agent_id = "agent-kid-interrupted-blocked"
    _install_kid_agent(monkeypatch, _FakeAgent(["Nice ", "banana ", "day"]),
                       _kid_config(agent_id))
    monkeypatch.setattr(moderation, "OUTPUT_RECHECK_EVERY_CHARS", 1)
    monkeypatch.setattr(
        moderation, "moderate_with_openai",
        lambda text: ModerationResult(
            flagged=True, severity="medium", category="test_flag",
            reason="banana", suggested_action="block_output",
        ) if "banana" in text else ModerationResult(
            flagged=False, severity="low", category="ok",
            reason="clean", suggested_action="allow",
        ),
    )

    async def _drive() -> None:
        gen = convai._stream_response("u-int-blocked", "Ada", "th-int-blocked", "hi")
        seen = 0
        async for _chunk in gen:
            seen += 1
            if seen == 2:  # "Nice " then the replacement message
                break
        await gen.aclose()

    anyio.run(_drive)

    msgs = server.storage_backend.get_kid_messages(agent_id, "th-int-blocked")
    assert [m["role"] for m in msgs] == ["user"], \
        "a blocked, interrupted turn must not write an assistant message"


# ═════════════════════════════════════════════════════════════════════════════
# Parent endpoint — link stripping / client tools
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("kind,tool", [
    ("library", "show_article"),
    # The community board is retired: a stale mvp://community/ link must still
    # be stripped from speech, but it fires NO client tool (there is no card).
    ("community", None),
])
def test_parent_link_split_across_chunks_speaks_label_only(
    client, secret, monkeypatch, hermetic, kind, tool
):
    """The whole point of the parent endpoint. The model emits
    `[Label](mvp://library/id)` token by token — the URL must never reach TTS,
    the label must be spoken, and the card must fire as a client tool."""
    script = [
        "Here's a great read: ",
        "[Bedtime ",
        "Routines](mvp://",
        f"{kind}/abc-123",
        ")",
        " — try it tonight.",
    ]
    _install_parent_agent(monkeypatch, _FakeAgent(script))

    res = client.post(
        PARENT_PATH,
        json=_kid_body(extra={"user_id": "u-link", "thread_id": "th-link"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    payloads = _payloads(res.text)
    spoken = _spoken(payloads)

    assert "mvp://" not in spoken, f"URL leaked to TTS: {spoken!r}"
    assert "abc-123" not in spoken
    assert spoken == "Here's a great read: Bedtime Routines — try it tonight."

    tools = _tool_deltas(payloads)
    if tool is None:
        assert tools == [], "a retired mvp://community/ link must fire no tool"
    else:
        assert len(tools) == 1
        call = tools[0]["choices"][0]["delta"]["tool_calls"][0]
        assert call["function"]["name"] == tool
        assert json.loads(call["function"]["arguments"]) == {"id": "abc-123"}
        # Display-only: finish_reason MUST stay null or the coach stops
        # mid-sentence.
        assert tools[0]["choices"][0]["finish_reason"] is None
    assert payloads[-1] == "[DONE]"


def test_parent_bracketed_aside_flushes_promptly(client, secret, monkeypatch, hermetic):
    """REGRESSION for the 120-cap `_is_plausible_link` rewrite.

    The old rule held everything after the last '[' until a link closed or 300
    chars piled up, so any bracketed aside in prose made the coach go silent
    mid-sentence. One delta per model chunk proves nothing stalled; the old
    behavior would merge chunks 2 and 3 into one late delta."""
    script = ["I hear you. ", "[long pause] ", "That's really hard."]
    _install_parent_agent(monkeypatch, _FakeAgent(script))

    res = client.post(
        PARENT_PATH,
        json=_kid_body(extra={"user_id": "u-aside"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    payloads = _payloads(res.text)
    deltas = [p["choices"][0]["delta"]["content"] for p in _content_deltas(payloads)]

    assert deltas == script, f"aside stalled the stream: {deltas!r}"
    assert _tool_deltas(payloads) == []


def test_parent_non_mvp_link_is_spoken_verbatim(client, secret, monkeypatch, hermetic):
    """A markdown link to a non-mvp target isn't a card — it must flush as soon
    as the target can't prefix-match, not sit in the hold buffer."""
    script = ["See ", "[the docs](https", "://example.com/x)", " for more."]
    _install_parent_agent(monkeypatch, _FakeAgent(script))

    res = client.post(
        PARENT_PATH,
        json=_kid_body(extra={"user_id": "u-extlink"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    payloads = _payloads(res.text)
    assert _spoken(payloads) == "See [the docs](https://example.com/x) for more."
    assert _tool_deltas(payloads) == []


def test_parent_dangling_tool_error_is_repaired_and_retried_once(
    client, secret, monkeypatch, hermetic, caplog
):
    """A concurrent turn can poison the thread AFTER our pre-flight repair. The
    endpoint repairs and retries exactly once — but only because nothing had
    streamed yet; a retry after spoken output would repeat the sentence aloud."""
    poisoned = [AIMessage(id="m1", content="",
                          tool_calls=[{"name": "search", "args": {}, "id": "call_1"}])]
    agent = _FakeAgent(["All set, ", "here's the plan."],
                       raise_on_attempt=1, state_messages=poisoned)
    _install_parent_agent(monkeypatch, agent)

    with caplog.at_level(logging.WARNING):
        res = client.post(
            PARENT_PATH,
            json=_kid_body(extra={"user_id": "u-dangling", "thread_id": "th-dangling"}),
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert res.status_code == 200, res.text
    payloads = _payloads(res.text)
    assert _spoken(payloads) == "All set, here's the plan."
    assert "snag on my end" not in _spoken(payloads)

    assert agent.attempts == 2, "the poisoned first attempt must be retried once"
    assert agent.state_reads >= 2, "pre-flight repair + mid-run repair"
    assert agent.state_updates >= 1, "the dangling tool call was never stripped"
    assert any("dangling tool call mid-run" in r.getMessage() for r in caplog.records)


def test_parent_non_dangling_error_is_not_retried(client, secret, monkeypatch, hermetic):
    """Only the dangling-tool-call error is retryable. Retrying anything else
    doubles the model spend and the parent's wait for the same failure."""
    agent = _FakeAgent([], raise_on_attempt=1, error=RuntimeError("rate limited"))
    _install_parent_agent(monkeypatch, agent)

    res = client.post(
        PARENT_PATH,
        json=_kid_body(extra={"user_id": "u-hard-error"}),
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    assert "snag on my end" in _spoken(_payloads(res.text))
    assert agent.attempts == 1


# ═════════════════════════════════════════════════════════════════════════════
# [PERF][VOICE] instrumentation
# ═════════════════════════════════════════════════════════════════════════════


def _perf_lines(caplog) -> List[str]:
    return [
        r.getMessage() for r in caplog.records
        if r.name == "perf" and "[PERF][VOICE]" in r.getMessage()
    ]


def test_kid_turn_emits_exactly_one_perf_line(client, secret, monkeypatch, hermetic, caplog):
    _install_kid_agent(monkeypatch, _FakeAgent(["Sure ", "thing."]),
                       _kid_config("agent-kid-perf"))

    with caplog.at_level(logging.INFO, logger="perf"):
        res = client.post(
            KID_PATH,
            json=_kid_body(extra={"user_id": "u-perf-kid", "kid_name": "Ada",
                                  "thread_id": "th-perf"}),
            headers={"Authorization": f"Bearer {secret}"},
        )
    assert res.status_code == 200, res.text

    lines = _perf_lines(caplog)
    assert len(lines) == 1, f"expected one [PERF][VOICE] line, got {lines!r}"
    line = lines[0]
    assert "feature=kid_voice" in line
    assert "ttfb_ms=" in line
    assert "repair_ms=" in line
    assert "total_ms=" in line
    assert "chunks=2" in line


def test_parent_turn_emits_exactly_one_perf_line(client, secret, monkeypatch, hermetic, caplog):
    _install_parent_agent(monkeypatch, _FakeAgent(["Sure ", "thing."]))

    with caplog.at_level(logging.INFO, logger="perf"):
        res = client.post(
            PARENT_PATH,
            json=_kid_body(extra={"user_id": "u-perf-parent", "thread_id": "th-perf"}),
            headers={"Authorization": f"Bearer {secret}"},
        )
    assert res.status_code == 200, res.text

    lines = _perf_lines(caplog)
    assert len(lines) == 1, f"expected one [PERF][VOICE] line, got {lines!r}"
    line = lines[0]
    assert "feature=parent_voice" in line
    assert "ttfb_ms=" in line
    assert "repair_ms=" in line


def test_perf_line_survives_a_blocked_turn(client, secret, monkeypatch, hermetic, caplog):
    """A turn that got blocked before the model ran is precisely the one worth
    timing — and it still gets exactly one line (never two)."""
    _install_kid_agent(monkeypatch, _FakeAgent(["never"]),
                       _kid_config("agent-kid-perf-blocked", enabled=False))

    with caplog.at_level(logging.INFO, logger="perf"):
        client.post(
            KID_PATH,
            json=_kid_body(extra={"user_id": "u-perf-blocked", "kid_name": "Ada"}),
            headers={"Authorization": f"Bearer {secret}"},
        )

    lines = _perf_lines(caplog)
    assert len(lines) == 1
    # A turn blocked before the model ran has no model_ttft_ms — log_perf DROPS
    # None fields on purpose, because an absent key parses better than a fake 0.
    assert "model_ttft_ms=" not in lines[0]


def test_tool_turn_is_bucketed_separately(client, secret, monkeypatch, hermetic, caplog):
    """`tool_turn=1` keeps a tool-using turn's latency out of the plain-answer
    distribution — without it the p95 chart is meaningless."""
    _install_parent_agent(monkeypatch, _FakeAgent([TOOL_START, "Found it."]))

    with caplog.at_level(logging.INFO, logger="perf"):
        client.post(
            PARENT_PATH,
            json=_kid_body(extra={"user_id": "u-tool-turn"}),
            headers={"Authorization": f"Bearer {secret}"},
        )

    assert "tool_turn=1" in _perf_lines(caplog)[0]


def test_perf_line_survives_a_kid_stream_error(client, secret, monkeypatch, hermetic, caplog):
    """A turn that blew up is the one you most want timed — how long did the kid
    wait before hearing the recovery line?"""
    _install_kid_agent(
        monkeypatch,
        _FakeAgent([], raise_on_attempt=1, error=RuntimeError("model exploded")),
        _kid_config("agent-kid-perf-error"),
    )

    with caplog.at_level(logging.INFO, logger="perf"):
        client.post(
            KID_PATH,
            json=_kid_body(extra={"user_id": "u-perf-err-kid", "kid_name": "Ada",
                                  "thread_id": "th-perf-err"}),
            headers={"Authorization": f"Bearer {secret}"},
        )

    lines = _perf_lines(caplog)
    assert len(lines) == 1, f"expected one [PERF][VOICE] line, got {lines!r}"
    assert "feature=kid_voice" in lines[0]


def test_perf_line_survives_a_parent_stream_error(client, secret, monkeypatch, hermetic, caplog):
    _install_parent_agent(
        monkeypatch,
        _FakeAgent([], raise_on_attempt=1, error=RuntimeError("model exploded")),
    )

    with caplog.at_level(logging.INFO, logger="perf"):
        client.post(
            PARENT_PATH,
            json=_kid_body(extra={"user_id": "u-perf-err-parent"}),
            headers={"Authorization": f"Bearer {secret}"},
        )

    lines = _perf_lines(caplog)
    assert len(lines) == 1, f"expected one [PERF][VOICE] line, got {lines!r}"
    assert "feature=parent_voice" in lines[0]


def test_kid_interrupted_turn_still_reports_perf(client, secret, monkeypatch, hermetic, caplog):
    """REGRESSION: a barge-in is the MOST common way a voice turn ends, and it
    unwinds the generator without reaching any clean exit. If only the clean
    exits reported, the latency histogram would silently measure just the turns
    nobody minded waiting for. Same aclose() drive as the persistence test."""
    _install_kid_agent(monkeypatch, _FakeAgent(["Once ", "upon ", "a ", "time."]),
                       _kid_config("agent-kid-perf-interrupted"))

    async def _drive() -> None:
        gen = convai._stream_response("u-perf-int", "Ada", "th-perf-int", "a story")
        seen = 0
        async for _chunk in gen:
            seen += 1
            if seen == 2:
                break
        await gen.aclose()

    with caplog.at_level(logging.INFO, logger="perf"):
        anyio.run(_drive)

    lines = _perf_lines(caplog)
    assert len(lines) == 1, f"expected one [PERF][VOICE] line, got {lines!r}"
    # TTFB is real on an interrupted turn — the kid did hear the reply start.
    assert "ttfb_ms=" in lines[0]


def test_parent_interrupted_turn_still_reports_perf(client, secret, monkeypatch, hermetic, caplog):
    _install_parent_agent(monkeypatch, _FakeAgent(["Here ", "is ", "a ", "thought."]))

    async def _drive() -> None:
        gen = parent_convai._stream_response("u-perf-int-p", "th-perf-int-p", "hi")
        seen = 0
        async for _chunk in gen:
            seen += 1
            if seen == 2:
                break
        await gen.aclose()

    with caplog.at_level(logging.INFO, logger="perf"):
        anyio.run(_drive)

    lines = _perf_lines(caplog)
    assert len(lines) == 1, f"expected one [PERF][VOICE] line, got {lines!r}"
    assert "feature=parent_voice" in lines[0]


# ═════════════════════════════════════════════════════════════════════════════
# _LinkStripper unit tests (no HTTP, no agent)
# ═════════════════════════════════════════════════════════════════════════════

_S = parent_convai._LinkStripper


def _feed_all(stripper, text: str, *, chunk: int = 1):
    """Feed `text` in `chunk`-sized pieces; return (spoken, tools)."""
    spoken, tools = "", []
    for i in range(0, len(text), chunk):
        safe, found = stripper.feed(text[i:i + chunk])
        spoken += safe
        tools.extend(found)
    spoken += stripper.flush()
    return spoken, tools


def test_stripper_char_by_char_link():
    """The worst case in production: one character per token."""
    spoken, tools = _feed_all(_S(), "Try [Bedtime Basics](mvp://library/art-9) tonight.")
    assert spoken == "Try Bedtime Basics tonight."
    assert tools == [("library", "art-9")]


def test_stripper_bracketed_aside_without_paren_flushes():
    """`[sic] and then` can never become a link — it must flush the instant the
    ']' is followed by anything other than '('."""
    s = _S()
    safe, tools = s.feed("[sic] and then")
    assert safe == "[sic] and then"
    assert tools == []
    assert s.flush() == ""


def test_stripper_holds_only_while_a_link_is_still_possible():
    s = _S()
    assert s.feed("[Title")[0] == ""      # still inside the label
    assert s.feed("]")[0] == ""           # "](" may be the next chunk
    assert s.feed("(mvp://li")[0] == ""   # target prefix-matches
    safe, tools = s.feed("brary/x1)")
    assert safe == "Title"
    assert tools == [("library", "x1")]


def test_stripper_non_mvp_target_flushes_immediately():
    """`](` followed by a target that can't prefix-match a card URL."""
    s = _S()
    assert s.feed("[docs]")[0] == ""
    safe, tools = s.feed("(https://example.com/a)")
    assert safe == "[docs](https://example.com/a)"
    assert tools == []


def test_stripper_pathological_label_past_the_cap_is_released():
    """A 'label' longer than _MAX_LABEL is prose, not a content title. Holding it
    is what made the coach go silent — release it and speak it."""
    long_prose = "[" + "x" * (parent_convai._MAX_LABEL + 5)
    safe, tools = _S().feed(long_prose)
    assert safe == long_prose
    assert tools == []


def test_stripper_hold_cap_is_a_backstop_for_an_unclosed_link():
    """`[t](mvp://library/` that never closes would otherwise buffer forever.
    _HOLD_CAP releases it — speech beats silence."""
    s = _S()
    unclosed = "[t](mvp://library/" + "a" * parent_convai._HOLD_CAP
    safe, tools = s.feed(unclosed)
    assert safe == unclosed
    assert tools == []


def test_stripper_multiple_links_in_one_chunk():
    s = _S()
    safe, tools = s.feed(
        "See [A](mvp://library/a1) and [B](mvp://community/b2) now."
    )
    assert safe == "See A and B now."
    assert tools == [("library", "a1"), ("community", "b2")]


def test_stripper_links_back_to_back_across_chunks():
    spoken, tools = _feed_all(
        _S(),
        "[One](mvp://library/l1)[Two](mvp://community/c2)!",
        chunk=3,
    )
    assert spoken == "OneTwo!"
    assert tools == [("library", "l1"), ("community", "c2")]


def test_stripper_flush_releases_an_unterminated_hold():
    """Stream ended mid-link: the tail must still be spoken, not swallowed."""
    s = _S()
    assert s.feed("Read [Sleep")[0] == "Read "
    assert s.flush() == "[Sleep"


# ═════════════════════════════════════════════════════════════════════════════
# Silence nudges — ElevenLabs turn-timeout "..." handling (both endpoints)
# ═════════════════════════════════════════════════════════════════════════════
# On user silence, ElevenLabs prompts the LLM with a literal "..." user message.
# Left alone, the model re-answers its previous turn (observed on device). The
# endpoints intercept the sentinel and speak a canned check-in WITHOUT running
# the agent.

_PARENT_NUDGE_1 = {
    "Still there? No rush.",
    "Take your time — I'm right here.",
    "Still with me?",
}


def _history_with_trailing_nudges(n: int) -> List[Dict[str, str]]:
    msgs = [
        {"role": "user", "content": "how do I handle bedtime?"},
        {"role": "assistant", "content": "Here's a bedtime plan."},
    ]
    for _ in range(n):
        msgs.append({"role": "user", "content": "..."})
        if _ < n - 1:
            msgs.append({"role": "assistant", "content": "Still there?"})
    return msgs


def test_parent_silence_nudge_speaks_checkin_without_running_the_agent(
    client, secret, monkeypatch
):
    agent = _FakeAgent(["the model must never run"])
    _install_parent_agent(monkeypatch, agent)

    res = client.post(
        PARENT_PATH,
        json={"messages": _history_with_trailing_nudges(1),
              "elevenlabs_extra_body": {"user_id": "u-quiet"}},
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    payloads = _payloads(res.text)
    assert _spoken(payloads) in _PARENT_NUDGE_1
    assert payloads[-1] == "[DONE]"
    # The whole point: no agent invocation, no thread repair, no LLM spend.
    assert agent.attempts == 0
    assert agent.state_reads == 0


@pytest.mark.parametrize("n,expected", [
    (2, "No hurry at all. I'll be here when you're ready."),
    (3, "I'll stay on the line — if you're done for now, just say goodbye or tap End."),
    (5, "I'll stay on the line — if you're done for now, just say goodbye or tap End."),
])
def test_parent_silence_nudges_escalate(client, secret, monkeypatch, n, expected):
    _install_parent_agent(monkeypatch, _FakeAgent(["never"]))
    res = client.post(
        PARENT_PATH,
        json={"messages": _history_with_trailing_nudges(n),
              "elevenlabs_extra_body": {"user_id": "u-quiet"}},
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert _spoken(_payloads(res.text)) == expected


def test_parent_empty_user_message_after_speech_is_a_nudge_not_400(
    client, secret, monkeypatch
):
    """EL sometimes delivers the timeout as an empty user turn. That used to hit
    the 'no user message found' 400 — every timeout became a spoken error."""
    _install_parent_agent(monkeypatch, _FakeAgent(["never"]))
    msgs = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": ""},
    ]
    res = client.post(
        PARENT_PATH,
        json={"messages": msgs, "elevenlabs_extra_body": {"user_id": "u-quiet"}},
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    assert _spoken(_payloads(res.text)) in _PARENT_NUDGE_1


def test_kid_silence_nudge_skips_agent_moderation_and_transcript(
    client, secret, monkeypatch, hermetic
):
    agent_id = "agent-kid-quiet"
    agent = _FakeAgent(["the model must never run"])
    _install_kid_agent(monkeypatch, agent, _kid_config(agent_id))

    def _boom(*a, **k):
        raise AssertionError("moderation must not run on a silence nudge")
    monkeypatch.setattr(moderation, "amoderate_input", _boom)

    msgs = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "Hi Ada!"},
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "Are you still there, Ada?"},
        {"role": "user", "content": "…"},
    ]
    res = client.post(
        KID_PATH,
        json={"messages": msgs,
              "elevenlabs_extra_body": {"user_id": "u-kid-quiet", "kid_name": "Ada",
                                        "thread_id": "th-quiet"}},
        headers={"Authorization": f"Bearer {secret}"},
    )
    assert res.status_code == 200, res.text
    # Two trailing nudges → the deterministic level-2 line.
    assert _spoken(_payloads(res.text)) == "That's okay, take your time. I'm right here."
    assert agent.attempts == 0
    # Neither the "..." nor the canned line belongs in the durable transcript.
    assert server.storage_backend.get_kid_messages(agent_id, "th-quiet") == []


def test_kid_crisis_lock_still_wins_over_a_silence_nudge(
    client, secret, monkeypatch, hermetic
):
    """Ordering guard: a locked companion must stay frozen even on a "..." turn —
    the nudge branch sits BELOW the crisis-lock check on purpose."""
    agent_id = "agent-kid-locked-quiet"
    _install_kid_agent(monkeypatch, _FakeAgent(["never"]), _kid_config(agent_id))
    server.storage_backend.lock_kid_agent_for_crisis(
        agent_id=agent_id, user_id="u-kid-lockq", kid_name="Ada",
        category="self_harm", severity="crisis", reason="test lock",
    )
    res = client.post(
        KID_PATH,
        json={"messages": _history_with_trailing_nudges(1),
              "elevenlabs_extra_body": {"user_id": "u-kid-lockq", "kid_name": "Ada",
                                        "thread_id": "th-lockq"}},
        headers={"Authorization": f"Bearer {secret}"},
    )
    payloads = _payloads(res.text)
    assert "grown-up needs to check in" in _spoken(payloads)
    assert "end_call" in _tool_names(payloads)


# ═════════════════════════════════════════════════════════════════════════════
# Personalized voice greeting (parent token endpoint helper)
# ═════════════════════════════════════════════════════════════════════════════


def _greeting_for(monkeypatch, *, name, returning_chat, thread_messages):
    from types import SimpleNamespace as NS

    monkeypatch.setattr(
        server.profiling_service, "get_family_profile",
        lambda uid: {"parent": {"name": name}, "children": {"Alkina": {}, "Ceiba": {}}},
    )
    monkeypatch.setattr(
        server, "chat_memory",
        NS(user_ids=lambda: ["u-returning"] if returning_chat else []),
    )
    import app.agent as agent_mod

    class _A:
        async def aget_state(self, config):
            return NS(values={"messages": thread_messages})

    monkeypatch.setattr(agent_mod, "get_agent", lambda uid: _A())

    async def _run() -> str:
        return await server._parent_voice_greeting("u-returning")

    return anyio.run(_run)


def test_greeting_returning_parent_is_personal_and_continuous(monkeypatch):
    g = _greeting_for(monkeypatch, name="Miguel Alvarado",
                      returning_chat=True, thread_messages=[])
    assert ", Miguel" in g            # first name only, from the profile
    assert g.rstrip().endswith("?")   # always opens the floor
    # Every returning variant references continuity, never a cold "how can I help".
    assert any(w in g.lower() for w in ("again", "back", "since we last"))


def test_greeting_first_session_introduces_the_coach(monkeypatch):
    g = _greeting_for(monkeypatch, name=None,
                      returning_chat=False, thread_messages=[])
    assert "back" not in g.lower() and "again" not in g.lower()
    assert g.rstrip().endswith("?")


def test_greeting_live_voice_thread_counts_as_returning(monkeypatch):
    """chat_memory empty but the in-process voice thread has history — greeting
    must not re-introduce the coach mid-relationship."""
    g = _greeting_for(monkeypatch, name="Heather",
                      returning_chat=False, thread_messages=["prior turn"])
    assert any(w in g.lower() for w in ("again", "back", "since we last"))
    assert ", Heather" in g


def test_parent_token_route_is_bound_to_the_authed_endpoint(client, monkeypatch):
    """REGRESSION: a helper def inserted between @app.get and the endpoint left
    the route decorating the helper — auth vanished and every client got a 422
    asking for a `user_id` query param (the 2026-07-24 "can't connect" outage).

    The route must reject an unauthenticated call as auth (401/403), never 422
    — a 422 here means the decorator is bound to the wrong function again."""
    res = client.get("/voice/parent-convai-token")
    assert res.status_code in (401, 403), res.text

    # And with auth it must reach the REAL endpoint: unset EL config → its 503,
    # which only that function raises.
    monkeypatch.delenv("ELEVENLABS_PARENT_AGENT_ID", raising=False)
    monkeypatch.setattr(server, "current_user", lambda: "u-route-check", raising=False)
    from app.auth import current_user as real_dep
    server.app.dependency_overrides[real_dep] = lambda: "u-route-check"
    try:
        res = client.get("/voice/parent-convai-token")
        assert res.status_code == 503, res.text
        assert "not configured" in res.text
    finally:
        server.app.dependency_overrides.pop(real_dep, None)


@pytest.mark.parametrize("buffer_chars", [0, 8])
def test_cancel_during_output_check_persists_only_yielded_prefix(
    client, secret, monkeypatch, hermetic, buffer_chars,
):
    import asyncio
    agent_id = f"agent-kid-pending-check-{buffer_chars}"
    thread = f"pending-check-{buffer_chars}"
    monkeypatch.setattr(moderation, "OUTPUT_CHUNK_BUFFER_CHARS", buffer_chars)
    monkeypatch.setattr(moderation, "OUTPUT_RECHECK_EVERY_CHARS", 8)
    _install_kid_agent(monkeypatch, _FakeAgent(["Hello ", "pending candidate"]), _kid_config(agent_id))

    async def drive():
        entered = asyncio.Event()
        release = asyncio.Event()
        async def pending(self, text):
            entered.set()
            await release.wait()
            return moderation.ModerationResult(False, "low", "ok", "test", "allow")
        monkeypatch.setattr(moderation.StreamingModerator, "_agate_text", pending)
        generator = convai._stream_response("u-pending-check", "Ada", thread, "hi")
        async def consume():
            async for _ in generator:
                pass
        task = asyncio.create_task(consume())
        await asyncio.wait_for(entered.wait(), 2)
        task.cancel()
        await asyncio.sleep(0)  # Let the owner record disconnection before the gate finishes.
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        await generator.aclose()
    anyio.run(drive)
    assistant = [m['content'] for m in server.storage_backend.get_kid_messages(agent_id, thread)
                 if m['role'] == 'assistant']
    assert assistant == (["Hello "] if buffer_chars == 0 else [])
