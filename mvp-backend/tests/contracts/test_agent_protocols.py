"""Characterize the wire contract independently of the graph implementation.

Known defects are strict expected failures with the target behavior asserted.
They must become ordinary passing tests in their owning implementation PR.
"""
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

TEXT_PATHS = ["/chat", "/cos/chat", "/onboarding-chat"]


def decode_sse(body):
    frames = []
    for frame in body.split("\n\n"):
        if not frame:
            continue
        assert frame.startswith("data: "), frame
        data = frame[6:]
        frames.append(data if data == "[DONE]" else json.loads(data))
    return frames


def post(h, path, **kwargs):
    return h.client.post(path, json={"user_id": h.user, "message": "hello", **kwargs}, headers=h.headers)


@pytest.mark.parametrize("path", TEXT_PATHS)
def test_text_success_protocol(harness, path):
    h = harness
    h.agent.script = ["Hello", "", {"event": "on_tool_start", "name": "GetPlanSnapshot", "data": {}},
                      {"event": "on_tool_end", "name": "GetPlanSnapshot", "data": {}}, " parent"]
    response = post(h, path)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    assert decode_sse(response.text) == [
        {"type": "token", "content": "Hello"},
        {"type": "tool_start", "tool": "GetPlanSnapshot"},
        {"type": "tool_end", "tool": "GetPlanSnapshot"},
        {"type": "token", "content": " parent"}, "[DONE]",
    ]


@pytest.mark.parametrize("path", TEXT_PATHS)
@pytest.mark.parametrize("partial", [False, True])
def test_text_failure_protocol(harness, path, partial):
    h = harness
    h.agent.script = (["Partial"] if partial else []) + [RuntimeError("fixture failure")]
    response = post(h, path)
    assert response.status_code == 200  # headers have already been sent
    expected = ([{"type": "token", "content": "Partial"}] if partial else [])
    expected.append({"type": "error", "content": "fixture failure" if path == "/cos/chat" else "Something went wrong. Please try again."})
    assert decode_sse(response.text) == expected
    assert len(h.agent.configs) == 1, "a generic/partial failure must not replay the turn"


@pytest.mark.parametrize("path", TEXT_PATHS)
def test_text_auth_validation_and_cross_tenant(harness, path):
    h = harness
    body = {"user_id": h.user, "message": "hello"}
    assert h.client.post(path, json=body).status_code == 401
    assert post(h, path, user_id="another-parent").status_code == 403
    assert h.client.post(path, json={"user_id": h.user}, headers=h.headers).status_code == 422
    assert h.agent.configs == []


@pytest.mark.parametrize("path", ["/chat", "/cos/chat"])
def test_internal_model_text_does_not_cross_public_boundary(harness, path):
    harness.agent.script = [
        {"event": "on_chat_model_stream", "tags": ["mvp:internal"],
         "data": {"chunk": SimpleNamespace(content="private summary")}}, "public answer",
    ]
    assert decode_sse(post(harness, path).text) == [{"type": "token", "content": "public answer"}, "[DONE]"]


def test_legacy_checkpoint_namespaces_remain_stable(harness):
    h = harness
    for path in TEXT_PATHS:
        post(h, path, thread_id="install-id")
    assert [c["configurable"]["thread_id"] for c in h.agent.configs] == [
        "contract-parent:parent", "contract-parent:parent", "onboarding:contract-parent:install-id",
    ]


def test_cos_follows_active_named_conversation(harness, monkeypatch):
    monkeypatch.setenv("MVP_COS_ACTIVE_CONVERSATION", "1")
    h = harness
    h.server.coach_threads.touch(h.user, "c-named")
    post(h, "/chat")
    post(h, "/cos/chat")
    assert [c["configurable"]["thread_id"] for c in h.agent.configs] == [
        "contract-parent:parent:c-named", "contract-parent:parent:c-named",
    ]


@pytest.mark.parametrize("surface", ["chat", "cos", "onboarding"])
def test_assistant_is_durable_at_success_marker(harness, surface):
    h = harness

    async def consume_to_marker():
        if surface == "cos":
            stream = h.cos._cos_chat_stream(h.user, "install-id", "hello")
        else:
            method = h.server.generate_stream if surface == "chat" else h.server.generate_onboarding_stream
            stream = method("hello", "install-id", h.user)
        try:
            async for frame in stream:
                if frame == "data: [DONE]\n\n":
                    if surface == "cos":
                        messages = h.storage.get_cos_messages(h.user, thread_id="install-id")
                    else:
                        key = "chat_threads" if surface == "chat" else "onboarding_threads"
                        messages = (h.storage.load_user_data(h.user, key) or {}).get("install-id", [])
                    assert any(m["role"] == "assistant" and m["content"] == "Hello parent" for m in messages)
                    return
            pytest.fail("no completion marker")
        finally:
            await stream.aclose()

    asyncio.run(consume_to_marker())


def test_cos_history_projection_keeps_legacy_shape(harness):
    h = harness
    post(h, "/cos/chat", thread_id="install-id")
    response = h.client.get("/cos/messages", params={"thread_id": "install-id"}, headers=h.headers)
    assert response.status_code == 200
    assert set(response.json()) == {"messages"}
    messages = response.json()["messages"]
    assert [(m["role"], m["content"]) for m in messages] == [("user", "hello"), ("assistant", "Hello parent")]
    assert all(set(m) == {"id", "user_id", "thread_id", "role", "content", "created_at"} for m in messages)


@pytest.mark.parametrize("status", ["done", "failed", "canceled"])
def test_research_terminal_stream_and_poll_contract(harness, status):
    h = harness
    run_id = h.storage.create_research_run(user_id=h.user, location={}, kids=[])
    h.storage.update_research_run(run_id, status=status, progress={"phase": status}, finished=True)
    response = h.client.get(f"/research/runs/{run_id}/stream", headers=h.headers)
    assert response.status_code == 200
    assert decode_sse(response.text) == [
        {"type": "progress", "status": status, "progress": {"phase": status}, "candidate_count": 0},
        {"type": "final", "status": status, "candidate_count": 0, "error": None}, "[DONE]",
    ]
    assert h.client.get(f"/research/runs/{run_id}", headers=h.headers).json() == {
        "run_id": run_id, "status": status, "progress": {"phase": status}, "candidate_count": 0, "error": None,
    }


@pytest.mark.parametrize("surface", ["research", "warmup"])
def test_job_stream_timeout_stays_client_compatible(harness, monkeypatch, surface):
    h = harness
    if surface == "research":
        from app.research import router as module
        run_id = h.storage.create_research_run(user_id=h.user, location={}, kids=[])
        path = f"/research/runs/{run_id}/stream"
    else:
        from app import onboarding_warmup as module
        run_id = h.storage.create_warmup_run(user_id=h.user, steps=module.initial_steps(), context={})
        path = f"/onboarding/warmup/{run_id}/stream"
    monkeypatch.setattr(module, "_STREAM_MAX_TICKS", 0)
    response = h.client.get(path, headers=h.headers)
    assert response.status_code == 200
    assert decode_sse(response.text) == [{"type": "timeout"}, "[DONE]"]


def test_warmup_degraded_completion_contract(harness):
    from app import onboarding_warmup as warmup
    h = harness
    steps = warmup.initial_steps()
    for step in steps:
        step["state"] = warmup.FAILED
        step["error"] = "fixture timeout"
    run_id = h.storage.create_warmup_run(user_id=h.user, steps=steps, context={})
    h.storage.claim_next_queued_warmup_run()
    h.storage.finalize_warmup_run_if_running(run_id, status="done", steps=steps, result={"failed_steps": list(warmup.STEP_KEYS)})
    poll = h.client.get(f"/onboarding/warmup/{run_id}", headers=h.headers)
    assert poll.status_code == 200
    assert poll.json()["percent"] == 100
    stream = h.client.get(f"/onboarding/warmup/{run_id}/stream", headers=h.headers)
    assert decode_sse(stream.text) == [{**poll.json(), "type": "progress"}, {**poll.json(), "type": "final"}, "[DONE]"]


def test_kid_disabled_gate_retains_error_and_done(harness, monkeypatch):
    h = harness
    monkeypatch.setattr(h.server.kid_agent_service, "get_kid_agent", lambda *args: (h.agent, {"enabled": False}))
    async def run():
        return "".join([x async for x in h.server.generate_kid_stream(h.user, "Ada", "install", "hello")])
    assert decode_sse(asyncio.run(run())) == [
        {"type": "error", "content": "agent not yet enabled by parent"}, "[DONE]",
    ]
    assert not h.agent.configs
