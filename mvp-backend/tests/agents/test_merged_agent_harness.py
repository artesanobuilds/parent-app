"""
Offline guard for the MERGED parent agent (coach + Chief-of-Staff, one harness).

Four things this pins, each of which has a concrete failure mode behind it:

1. **One agent, all tools, flat.** The merge exists so a single turn can reach
   profile lookup AND activity search AND the calendar. If either half's tools
   stop being registered, that turn silently answers "I can't do that".
2. **Async middleware only.** Some built-in middleware ship a sync hook and
   raise `NotImplementedError` from the async one (langchain#33474). This
   backend is async FastAPI, so a sync-only middleware is a latent 500 that
   only fires in production.
3. **The summarizer must not reach the parent.** Middleware model calls stream
   as ordinary `on_chat_model_stream` events — verified here against a real
   graph, not assumed. Unfiltered, the context summary gets printed into the
   chat and SPOKEN on voice.
4. **Thread repair on every entry.** A cancelled tool call poisons a thread
   forever (`app/thread_repair.py`, the 2-day voice outage). The merge must not
   create a surface that streams the agent without the pre-flight self-heal.
"""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]


# ── 1. one agent, both halves' tools ─────────────────────────────────


def test_merged_agent_registers_both_halves_flat():
    from app.agent import build_parent_tools

    names = [t.name for t in build_parent_tools("merge-user")]

    # Coach half: web search + the two passive-profiling tools. Those tools are
    # the ONLY way the fields the signup funnel stopped asking for are learned
    # (memory `patterns_onboarding_parity`).
    assert "LearnedAboutParent" in names
    assert "LearnedAboutChild" in names
    assert any("search" in n.lower() for n in names), "web search tool went missing"

    # Chief-of-Staff half: the whole planning toolset, unfiltered.
    from app.cos.tools import build_cos_tools

    cos_names = {t.name for t in build_cos_tools("merge-user")}
    assert cos_names <= set(names), f"missing COS tools: {cos_names - set(names)}"

    assert len(names) == len(set(names)), f"duplicate tool names: {names}"
    # Flat registration is a deliberate decision (see app/agent.py); this is the
    # tripwire for the "revisit the selector past ~50 tools" threshold.
    assert 20 <= len(names) <= 50, f"unexpected tool count {len(names)}"


def test_cos_agent_shim_returns_the_merged_agent(monkeypatch):
    import app.agent as agent_mod
    from app.cos.agent import get_cos_agent

    monkeypatch.setattr(agent_mod.profiling_service, "get_family_profile", lambda u: {})
    monkeypatch.setattr(agent_mod, "content_catalog_for_prompt", lambda: "")
    agent_mod._agent_cache.clear()

    assert get_cos_agent("merge-user") is agent_mod.get_agent("merge-user")


# ── 2. every adopted middleware supports async ───────────────────────


def test_every_adopted_middleware_implements_its_async_hook():
    """A middleware that only defines the sync hook raises NotImplementedError
    the moment an async surface runs it. Check the INSTALLED classes, not the
    issue tracker."""
    from app.agent import build_middleware

    pairs = [
        ("before_model", "abefore_model"),
        ("after_model", "aafter_model"),
        ("before_agent", "abefore_agent"),
        ("after_agent", "aafter_agent"),
        ("wrap_model_call", "awrap_model_call"),
        ("wrap_tool_call", "awrap_tool_call"),
    ]
    for mw in build_middleware():
        cls = type(mw)
        implemented = False
        for sync_name, async_name in pairs:
            defines_sync = any(sync_name in k.__dict__ for k in cls.__mro__[:-1])
            if not defines_sync:
                continue
            assert any(async_name in k.__dict__ for k in cls.__mro__[:-1]), (
                f"{cls.__name__} overrides {sync_name} but not {async_name} — "
                "it would raise NotImplementedError on this async backend"
            )
            implemented = True
        assert implemented, f"{cls.__name__} overrides no known middleware hook"


# ── 3. harness-internal model output never reaches a surface ─────────


def test_is_internal_event_flags_tagged_model_events():
    from app.agent import INTERNAL_STREAM_TAG, is_internal_event

    assert is_internal_event({"event": "on_chat_model_stream",
                              "tags": ["seq:step:1", INTERNAL_STREAM_TAG]})
    assert not is_internal_event({"event": "on_chat_model_stream",
                                  "tags": ["seq:step:1"]})
    assert not is_internal_event({"event": "on_chat_model_stream"})


def test_summarizer_output_is_tagged_and_filtered_out_of_the_stream():
    """End-to-end on a real graph with fake models: force summarization and
    prove (a) the summary DOES stream as a model event, and (b) the filter
    every surface applies removes exactly it and nothing else."""
    from langchain.agents import create_agent
    from langchain.agents.middleware import SummarizationMiddleware
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage, HumanMessage
    from langgraph.checkpoint.memory import MemorySaver

    from app.agent import INTERNAL_STREAM_TAG, is_internal_event

    answer = GenericFakeChatModel(messages=iter([AIMessage(content="coach reply")] * 20))
    summarizer = GenericFakeChatModel(
        messages=iter([AIMessage(content="INTERNAL-SUMMARY")] * 20)
    ).with_config(tags=[INTERNAL_STREAM_TAG])

    agent = create_agent(
        model=answer,
        tools=[],
        checkpointer=MemorySaver(),
        system_prompt="sys",
        middleware=[
            SummarizationMiddleware(
                model=summarizer, trigger=("messages", 2), keep=("messages", 1)
            )
        ],
    )

    async def turn(text: str):
        seen, kept = [], []
        async for ev in agent.astream_events(
            {"messages": [HumanMessage(content=text)]},
            config={"configurable": {"thread_id": "merge-t1"}},
            version="v1",
        ):
            if ev["event"] != "on_chat_model_stream":
                continue
            chunk = ev["data"]["chunk"].content
            if not chunk:
                continue
            seen.append(chunk)
            if not is_internal_event(ev):
                kept.append(chunk)
        return "".join(seen), "".join(kept)

    async def run():
        await turn("first")
        return await turn("second")  # summarization triggers on this turn

    seen, kept = asyncio.run(run())
    assert "INTERNAL-SUMMARY" in seen, (
        "test is no longer exercising the leak it guards — the summarizer "
        "stopped streaming, so re-check whether the filter is still needed"
    )
    assert "INTERNAL-SUMMARY" not in kept, "summary leaked to the parent"
    assert "coach reply" in kept


def test_every_streaming_surface_filters_internal_events():
    """Source-level: a new surface that streams the parent agent must drop
    harness-internal events, or the parent reads/hears the summary."""
    for rel in ("app/server.py", "app/cos/router.py", "app/parent_convai_endpoint.py"):
        src = (BACKEND_ROOT / rel).read_text()
        assert "is_internal_event" in src, (
            f"{rel} streams the parent agent without filtering harness-internal "
            "model events"
        )


# ── 4. thread repair covers every entry into the merged agent ────────


# Every module that runs a TURN on the merged parent agent. `app/server.py`
# additionally drives the separate onboarding agent through the same helper.
_AGENT_SURFACES = (
    "app/server.py",
    "app/cos/router.py",
    "app/parent_convai_endpoint.py",
)


def _calls_in(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Attribute):
                names.add(fn.attr)
            elif isinstance(fn, ast.Name):
                names.add(fn.id)
    return names


@pytest.mark.parametrize("rel", _AGENT_SURFACES)
def test_surface_streams_only_with_thread_repair(rel):
    calls = _calls_in(BACKEND_ROOT / rel)
    assert "astream_events" in calls, (
        f"{rel} no longer streams an agent — drop it from _AGENT_SURFACES"
    )
    # Durable adapters reconcile known effects before invoking the same repair
    # through repair_with_receipts. The HTTP fault tests pin that ordering.
    assert "repair_thread" in calls or "repair_with_receipts" in calls, (
        f"{rel} streams the merged parent agent without app/thread_repair's "
        "pre-flight self-heal. A cancelled tool call would poison that thread "
        "forever (memory `debugging_voice_thread_poisoning`)."
    )
    assert "is_dangling_tool_error" in calls, (
        f"{rel} has no retry-once path for a thread poisoned MID-run"
    )


def test_text_surfaces_share_one_thread_and_voice_does_not():
    from app.agent import thread_key

    chat = thread_key("u1", "chat", "install-uuid-a")
    other_install = thread_key("u1", "chat", "install-uuid-b")
    cos = thread_key("u1", "cos", "default")
    voice = thread_key("u1", "voice", "default")

    assert chat == cos == other_install, "coach and COS text must share one thread"
    assert voice != chat, "voice keeps its own thread for now"
    # The old COS key was `cos:{user}:{thread}` and voice is `{user}:default`;
    # the merged text key must collide with neither.
    assert chat != f"cos:u1:default" and chat != "u1:default"
    assert thread_key("u2", "chat", "x") != chat, "threads stay per-parent"


# Actual /chat and /cos/chat checkpoint routing is exercised by the HTTP
# contract tests (legacy keys, selected conversations, both runtime modes).


# ── household + library wiring ───────────────────────────────────────


def test_household_members_reach_the_system_prompt(monkeypatch):
    """The Circle roster is prompt context, and a roster change must rebuild
    the cached agent (the cache is keyed on the dynamic block)."""
    import app.agent as agent_mod
    import app.household as household

    rows = [
        {
            "id": "m1", "display_name": "Sam", "role": "co_parent",
            "relation": "Ben's dad", "member_user_id": "u-sam",
            "attributes": {"co_parent_goals": ["share the summer load"],
                           "likes": ["hiking"]},
            "notes": None,
        },
        {
            "id": "m2", "display_name": "Rosa", "role": "nanny",
            "relation": None, "member_user_id": None,
            "attributes": {"excels_at": ["bedtime"]}, "notes": "Tue/Thu",
        },
    ]
    monkeypatch.setattr(
        household, "_storage",
        lambda: type("S", (), {"list_household_members": staticmethod(lambda u: rows)})(),
    )

    context = household.household_context_for_prompt("u1")
    assert "Sam" in context and "Co-Parent" in context
    assert "share the summer load" in context
    assert "Rosa" in context and "bedtime" in context

    prompt = agent_mod._build_system_prompt("Pat", household_context=context)
    assert "Sam" in prompt and "Rosa" in prompt


def test_household_context_is_empty_and_safe_without_a_roster(monkeypatch):
    import app.household as household

    monkeypatch.setattr(
        household, "_storage",
        lambda: type("S", (), {"list_household_members": staticmethod(lambda u: [])})(),
    )
    assert household.household_context_for_prompt("u1") == ""

    def boom():
        raise RuntimeError("storage down")

    monkeypatch.setattr(household, "_storage", boom)
    assert household.household_context_for_prompt("u1") == ""


def test_prompt_keeps_both_role_halves_and_the_profiling_rules(monkeypatch):
    import app.agent as agent_mod

    monkeypatch.setattr(agent_mod, "content_catalog_for_prompt", lambda: "CATALOG")
    prompt = agent_mod._build_system_prompt("Pat", profile_context='{"a": 1}')

    assert "Your name is **Coach**" in prompt          # soul
    assert "Chief-of-Staff job" in prompt              # planning half
    assert "GetPlanSnapshot" in prompt                 # planning operating rules
    assert "LearnedAboutParent" in prompt              # passive profiling survived
    assert "CATALOG" in prompt
    # Dynamic context goes LAST so the static half stays one cacheable prefix.
    assert prompt.index("CATALOG") < prompt.index('{"a": 1}')


def test_for_you_ranking_feeds_the_agent_not_a_browse_surface():
    """`GET /content/for-you`'s ranker is what the coach recommends from —
    same function, so the feed and the coach agree on order."""
    from app import content as content_service

    assert content_service.for_you_word_bag({}) == []
    family = {
        "parent": {"stressors": ["bedtime battles"]},
        "children": {"Ben": {"interests": ["dinosaurs"], "age": 7.0}},
    }
    words = content_service.for_you_word_bag(family)
    assert "bedtime" in words and "dinosaurs" in words
    # No signal -> no shortlist; the full catalog in the static prompt covers it.
    assert content_service.for_you_prompt_lines([]) == ""


# ── PII posture ──────────────────────────────────────────────────────


def test_card_numbers_are_masked_before_the_model_and_the_checkpoint():
    """Chat transcripts are discoverable (memory
    `project_gtm_validation_playbook`). A card pasted into the coach must never
    reach OpenAI or the checkpoint. Emails are deliberately NOT redacted — the
    draft-email and email-sync tools carry them legitimately."""
    from langchain.agents import create_agent
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage, HumanMessage
    from langgraph.checkpoint.memory import MemorySaver

    from app.agent import build_middleware

    model = GenericFakeChatModel(messages=iter([AIMessage(content="ok")] * 10))
    agent = create_agent(
        model=model, tools=[], checkpointer=MemorySaver(),
        system_prompt="sys", middleware=build_middleware(),
    )

    async def run():
        config = {"configurable": {"thread_id": "pii-t1"}}
        await agent.ainvoke(
            {"messages": [HumanMessage(
                content="pay with 4111 1111 1111 1111, reply to me@example.com"
            )]},
            config=config,
        )
        return await agent.aget_state(config)

    state = asyncio.run(run())
    text = "\n".join(str(m.content) for m in state.values["messages"])
    assert "4111 1111 1111 1111" not in text, "card survived into the checkpoint"
    assert "1111" in text, "masking should keep the last four, not drop the turn"
    assert "me@example.com" in text, (
        "emails must stay intact — DraftEmail and the email-sync tools need them"
    )
