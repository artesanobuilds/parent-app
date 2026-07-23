"""
Thread-repair coverage: the self-heal that un-poisons LangGraph threads whose
history holds a dangling tool call (the 2026-07-20 parent-voice outage — an
ElevenLabs abort cancelled a turn between the tool_calls checkpoint and the
tool result, and every later turn 400'd at OpenAI forever).

Pure planning matrix + an integration pass against the real parent agent's
compiled graph (repair only reads/writes checkpointer state — no LLM calls).
"""

import asyncio
import os

os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used")
os.environ.setdefault("TAVILY_API_KEY", "test-key-not-used")

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, ToolMessage

from app.thread_repair import is_dangling_tool_error, plan_repairs, repair_thread


def _tc(call_id: str, name: str = "tavily_search") -> dict:
    return {"name": name, "args": {"query": "x"}, "id": call_id, "type": "tool_call"}


# ── plan_repairs matrix ──────────────────────────────────────────────

def test_healthy_thread_untouched():
    msgs = [
        HumanMessage(id="h1", content="hi"),
        AIMessage(id="a1", content="", tool_calls=[_tc("c1")]),
        ToolMessage(id="t1", content="result", tool_call_id="c1"),
        AIMessage(id="a2", content="all done"),
    ]
    assert plan_repairs(msgs) == []


def test_dangling_pure_tool_call_message_removed():
    # The outage shape: assistant message with ONLY a tool call, never answered,
    # then the user's later retries.
    msgs = [
        HumanMessage(id="h1", content="question"),
        AIMessage(id="a1", content="", tool_calls=[_tc("call_Zw2")]),
        HumanMessage(id="h2", content="retry 1"),
        HumanMessage(id="h3", content="retry 2"),
    ]
    updates = plan_repairs(msgs)
    assert len(updates) == 1
    assert isinstance(updates[0], RemoveMessage)
    assert updates[0].id == "a1"


def test_dangling_with_prose_keeps_prose_drops_calls():
    msgs = [
        HumanMessage(id="h1", content="question"),
        AIMessage(id="a1", content="Let me look that up.", tool_calls=[_tc("c1")]),
        HumanMessage(id="h2", content="retry"),
    ]
    updates = plan_repairs(msgs)
    assert len(updates) == 1
    fixed = updates[0]
    assert isinstance(fixed, AIMessage)
    assert fixed.id == "a1"
    assert fixed.content == "Let me look that up."
    assert fixed.tool_calls == []


def test_mixed_answered_unanswered_keeps_only_answered():
    msgs = [
        HumanMessage(id="h1", content="question"),
        AIMessage(id="a1", content="", tool_calls=[_tc("c1"), _tc("c2")]),
        ToolMessage(id="t1", content="result", tool_call_id="c1"),
    ]
    updates = plan_repairs(msgs)
    assert len(updates) == 1
    fixed = updates[0]
    assert isinstance(fixed, AIMessage)
    assert [tc["id"] for tc in fixed.tool_calls] == ["c1"]


def test_orphan_tool_message_removed():
    msgs = [
        HumanMessage(id="h1", content="hi"),
        ToolMessage(id="t1", content="result", tool_call_id="c-gone"),
        AIMessage(id="a1", content="hello"),
    ]
    updates = plan_repairs(msgs)
    assert len(updates) == 1
    assert isinstance(updates[0], RemoveMessage)
    assert updates[0].id == "t1"


def test_error_matcher():
    real = Exception(
        "Error code: 400 - {'error': {'message': \"An assistant message with "
        "'tool_calls' must be followed by tool messages responding to each "
        "'tool_call_id'. The following tool_call_ids did not have response "
        "messages: call_Zw2Vw9DKHASPCsbXgHmWIf7T\"}}"
    )
    assert is_dangling_tool_error(real)
    assert not is_dangling_tool_error(Exception("rate limit exceeded"))
    assert not is_dangling_tool_error(Exception("400 bad request"))


# ── integration: repair against the real compiled agent graph ────────

def test_repair_thread_heals_poisoned_checkpoint():
    from app.agent import get_agent

    agent = get_agent("thread-repair-test-user")
    config = {"configurable": {"thread_id": "thread-repair-test-user:poisoned"}}

    async def scenario():
        # Seed the exact poisoned shape from the outage.
        await agent.aupdate_state(
            config,
            {"messages": [
                HumanMessage(id="h1", content="my daughter can't sleep"),
                AIMessage(id="a1", content="", tool_calls=[_tc("call_dangling")]),
                HumanMessage(id="h2", content="retry"),
            ]},
        )
        repaired = await repair_thread(agent, config)
        state = await agent.aget_state(config)
        return repaired, state.values["messages"]

    repaired, messages = asyncio.run(scenario())
    assert repaired == 1
    # The poisoned assistant message is gone; the history is now valid.
    assert [m.id for m in messages] == ["h1", "h2"]
    assert plan_repairs(messages) == []


def test_repair_thread_noop_on_healthy_and_empty_threads():
    from app.agent import get_agent

    agent = get_agent("thread-repair-test-user")

    async def scenario():
        empty = await repair_thread(
            agent, {"configurable": {"thread_id": "thread-repair-test-user:empty"}}
        )
        healthy_config = {"configurable": {"thread_id": "thread-repair-test-user:healthy"}}
        await agent.aupdate_state(
            healthy_config,
            {"messages": [
                HumanMessage(id="h1", content="hi"),
                AIMessage(id="a1", content="hello!"),
            ]},
        )
        healthy = await repair_thread(agent, healthy_config)
        return empty, healthy

    empty, healthy = asyncio.run(scenario())
    assert empty == 0
    assert healthy == 0


# ── parent voice endpoint: repair-and-retry wiring ───────────────────

class _FakeState:
    values: dict = {}


class _FlakyAgent:
    """400s with the dangling-tool-call error on the first stream, then works."""

    def __init__(self, fail_times: int = 1):
        self.stream_calls = 0
        self.repair_updates = 0
        self.fail_times = fail_times

    async def aget_state(self, config):
        return _FakeState()

    async def aupdate_state(self, config, update, as_node=None):
        self.repair_updates += 1

    async def astream_events(self, _input, config=None, version=None):
        self.stream_calls += 1
        if self.stream_calls <= self.fail_times:
            raise Exception(
                "Error code: 400 - An assistant message with 'tool_calls' must be "
                "followed by tool messages responding to each 'tool_call_id'. The "
                "following tool_call_ids did not have response messages: call_x"
            )
        import types
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": types.SimpleNamespace(content="All better now.")},
        }


def _collect_stream(monkeypatch, agent):
    from app import parent_convai_endpoint

    monkeypatch.setattr(parent_convai_endpoint, "get_agent", lambda user_id: agent)

    async def run():
        chunks = []
        async for chunk in parent_convai_endpoint._stream_response("u1", "default", "hi"):
            chunks.append(chunk)
        return "".join(chunks)

    return asyncio.run(run())


def test_parent_voice_retries_once_after_dangling_tool_400(monkeypatch):
    agent = _FlakyAgent(fail_times=1)
    out = _collect_stream(monkeypatch, agent)
    assert "All better now." in out
    assert "snag" not in out
    assert agent.stream_calls == 2


def test_parent_voice_falls_back_when_retry_also_fails(monkeypatch):
    agent = _FlakyAgent(fail_times=99)
    out = _collect_stream(monkeypatch, agent)
    assert "I hit a snag on my end" in out
    assert agent.stream_calls == 2  # exactly one retry, never a loop
