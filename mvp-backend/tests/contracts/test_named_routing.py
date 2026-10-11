"""COS behavior switch preserves legacy keys and captures admission once."""
import pytest
from .conftest import ScriptedAgent
from .test_agent_protocols import post


@pytest.mark.parametrize("shared", ["0", "1"])
@pytest.mark.parametrize("enabled", ["0", "1"])
def test_cos_routing_switch_and_history(harness, monkeypatch, shared, enabled):
    h = harness
    monkeypatch.setenv("MVP_SHARED_RUNTIME_COS", shared)
    monkeypatch.setenv("MVP_COS_ACTIVE_CONVERSATION", enabled)
    h.server.coach_threads.touch(h.user, "c-selected")
    assert post(h, "/cos/chat", thread_id="old-install").status_code == 200
    key = h.agent.configs[0]["configurable"]["thread_id"]
    assert key == h.user + (":parent:c-selected" if enabled == "1" else ":parent")
    # The checkpoint changes; the historical REST transcript projection does not.
    response = h.client.get("/cos/messages", params={"thread_id": "old-install"}, headers=h.headers)
    assert [m["role"] for m in response.json()["messages"]] == ["user", "assistant"]


@pytest.mark.parametrize("shared", ["0", "1"])
def test_cos_captures_selected_conversation_for_entire_turn(harness, monkeypatch, shared):
    h = harness
    monkeypatch.setenv("MVP_SHARED_RUNTIME_COS", shared)
    monkeypatch.setenv("MVP_COS_ACTIVE_CONVERSATION", "1")
    h.server.coach_threads.touch(h.user, "c-first")

    class SwitchingAgent(ScriptedAgent):
        async def astream_events(self, *args, **kwargs):
            h.server.coach_threads.touch(h.user, "c-next")
            async for event in super().astream_events(*args, **kwargs):
                yield event

    agent = SwitchingAgent()
    monkeypatch.setattr(h.cos, "get_cos_agent", lambda *args: agent)
    post(h, "/cos/chat")
    post(h, "/cos/chat")
    assert [c["configurable"]["thread_id"] for c in agent.configs] == [
        h.user + ":parent:c-first", h.user + ":parent:c-next",
    ]


@pytest.mark.parametrize("shared", ["0", "1"])
def test_cos_legacy_history_key_survives_correction(harness, monkeypatch, shared):
    monkeypatch.setenv("MVP_SHARED_RUNTIME_COS", shared)
    monkeypatch.setenv("MVP_COS_ACTIVE_CONVERSATION", "1")
    post(harness, "/cos/chat")
    assert harness.agent.configs[0]["configurable"]["thread_id"] == harness.user + ":parent"
