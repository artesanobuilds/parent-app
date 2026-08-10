"""The DURABLE agent checkpointer: context must survive a restart.

Every agent used to hold a process-local `MemorySaver()`, so a Railway deploy
silently amnesia'd every in-flight conversation. That was invisible while Coach
was one unnamed thread; a visible LIST of past conversations makes it a bug the
parent can see, which is why the two shipped together.

What this pins:

1. **State survives a simulated restart** — rebuild the graph AND the saver on a
   fresh event loop, same thread id, and the history is still there. The
   restart has to be simulated on a NEW loop: `AsyncSqliteSaver` captures the
   running loop, and a stale loop is exactly how this breaks in production.
2. **All three agents share ONE saver** — a second saver on a second file would
   look fine in tests and lose kid/onboarding context in prod.
3. **Thread repair still heals through the proxy.** A dangling `tool_calls`
   checkpoint 400s a thread forever (`app/thread_repair.py` — the 2026-07
   two-day voice outage). Restarting used to clear it; now nothing does but
   repair, so repair working against THIS saver is load-bearing.
4. **The delete cascade reaches checkpoints.** They're durable now, so
   `DELETE /family/{id}` has to purge them or conversations outlive the family.
5. **The file is dockerignored + gitignored.** `railway up` uploads the working
   tree; a user-state file in the build context seeds prod with local data
   (memory `debugging_railway_parquet_deploy_hazard`).

Never `DuckDBStorage(":memory:")` anywhere here — its connection is process-wide
in this codebase and rows leak between tests. Per-test temp files only.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("OPENAI_API_KEY", "test-key-not-used")
os.environ.setdefault("TAVILY_API_KEY", "test-key-not-used")

from langchain.agents import create_agent  # noqa: E402
from langchain_core.language_models.fake_chat_models import (  # noqa: E402
    GenericFakeChatModel,
)
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage  # noqa: E402

from app.checkpointing import DurableCheckpointer, delete_user_threads  # noqa: E402
from app.thread_repair import repair_thread  # noqa: E402


@pytest.fixture()
def saver(tmp_path) -> DurableCheckpointer:
    """A checkpointer over a per-test temp file."""
    checkpointer = DurableCheckpointer(tmp_path / "agent_checkpoints.sqlite")
    yield checkpointer
    checkpointer.close_sync()


def _graph(checkpointer, replies=("ok",) * 10):
    """A minimal real compiled graph — no LLM calls, real checkpointing."""
    model = GenericFakeChatModel(messages=iter([AIMessage(content=r) for r in replies]))
    return create_agent(
        model=model, tools=[], checkpointer=checkpointer, system_prompt="sys"
    )


# ── 1. survives a restart ────────────────────────────────────────────


def test_agent_state_survives_a_simulated_restart(tmp_path):
    """The whole point: rebuild the graph and the saver on a FRESH event loop
    and the conversation is still there. With MemorySaver this returns [].
    """
    db = tmp_path / "ck.sqlite"

    async def first_boot():
        checkpointer = DurableCheckpointer(db)
        agent = _graph(checkpointer)
        config = {"configurable": {"thread_id": "u1:parent:c-abc"}}
        await agent.ainvoke(
            {"messages": [HumanMessage(content="Ben hates broccoli")]}, config=config
        )
        await checkpointer.aclose()

    async def second_boot():
        # Fresh saver + fresh graph, as after a deploy.
        checkpointer = DurableCheckpointer(db)
        agent = _graph(checkpointer)
        config = {"configurable": {"thread_id": "u1:parent:c-abc"}}
        state = await agent.aget_state(config)
        await checkpointer.aclose()
        return [m.content for m in (state.values or {}).get("messages", [])]

    asyncio.run(first_boot())
    # A NEW event loop is the part that matters — AsyncSqliteSaver binds to the
    # loop it was built on, so reusing one would not exercise a real restart.
    survived = asyncio.run(second_boot())

    assert "Ben hates broccoli" in survived, (
        "agent context did not survive the restart — the checkpointer is not durable"
    )


def test_threads_stay_isolated_per_conversation(saver):
    """A named conversation must not see another conversation's history —
    otherwise the history list would show every row with the same contents."""

    async def run():
        agent = _graph(saver)
        await agent.ainvoke(
            {"messages": [HumanMessage(content="one")]},
            config={"configurable": {"thread_id": "u1:parent:c-one"}},
        )
        await agent.ainvoke(
            {"messages": [HumanMessage(content="two")]},
            config={"configurable": {"thread_id": "u1:parent:c-two"}},
        )
        first = await agent.aget_state(
            {"configurable": {"thread_id": "u1:parent:c-one"}}
        )
        second = await agent.aget_state(
            {"configurable": {"thread_id": "u1:parent:c-two"}}
        )
        await saver.aclose()
        return (
            [m.content for m in first.values["messages"]],
            [m.content for m in second.values["messages"]],
        )

    first, second = asyncio.run(run())
    assert "one" in first and "two" not in first
    assert "two" in second and "one" not in second


# ── 2. one saver for all three agents ────────────────────────────────


def test_all_three_agents_share_one_durable_saver():
    """Parent, kid and onboarding agents must be the SAME saver instance.

    A per-module saver would pass every other test here and still lose kid and
    onboarding context on restart in production.
    """
    from app.agent import checkpointer as parent_saver
    from app.checkpointing import checkpointer as shared
    from app.kid_agent import _kid_checkpointer as kid_saver
    from app.onboarding_agent import checkpointer as onboarding_saver

    assert parent_saver is shared
    assert kid_saver is shared
    assert onboarding_saver is shared
    assert isinstance(shared, DurableCheckpointer)


def test_no_agent_module_still_constructs_a_memorysaver():
    """Source-level: a re-introduced `MemorySaver()` in any agent module is a
    silent regression to process-local context."""
    for rel in ("app/agent.py", "app/kid_agent.py", "app/onboarding_agent.py"):
        src = (BACKEND_ROOT / rel).read_text()
        assert "MemorySaver()" not in src, (
            f"{rel} constructs a MemorySaver again — agent context would stop "
            "surviving restarts (app/checkpointing.py is the durable saver)"
        )


# ── 3. thread repair still works against the durable saver ───────────


def test_thread_repair_heals_a_poisoned_durable_checkpoint(saver):
    """A dangling tool call poisons a thread FOREVER now that the checkpoint
    outlives the process — repair is the only thing that clears it."""

    async def run():
        agent = _graph(saver)
        config = {"configurable": {"thread_id": "u1:parent:c-poisoned"}}
        # Seed a healthy turn, then hand-write the outage shape: an assistant
        # message with a tool call that never received its ToolMessage.
        await agent.ainvoke(
            {"messages": [HumanMessage(content="hi")]}, config=config
        )
        await agent.aupdate_state(
            config,
            {
                "messages": [
                    AIMessage(
                        id="dangling-1",
                        content="",
                        tool_calls=[
                            {
                                "name": "tavily_search",
                                "args": {"query": "x"},
                                "id": "call-1",
                                "type": "tool_call",
                            }
                        ],
                    )
                ]
            },
            as_node="model",
        )
        before = await agent.aget_state(config)
        poisoned = any(
            getattr(m, "tool_calls", None) for m in before.values["messages"]
        )

        repairs = await repair_thread(agent, config)

        after = await agent.aget_state(config)
        still_dangling = [
            m
            for m in after.values["messages"]
            if getattr(m, "tool_calls", None)
            and not any(
                isinstance(x, ToolMessage) and x.tool_call_id == m.tool_calls[0]["id"]
                for x in after.values["messages"]
            )
        ]
        await saver.aclose()
        return poisoned, repairs, still_dangling

    poisoned, repairs, still_dangling = asyncio.run(run())
    assert poisoned, "test no longer sets up the poisoned state it guards"
    assert repairs >= 1, "repair did not fire against the durable saver"
    assert not still_dangling, "thread is still poisoned after repair"


def test_repair_survives_a_restart_and_stays_healed(tmp_path):
    """Repair must PERSIST. If the fix only lived in memory, the poisoned
    checkpoint would come back on the next deploy."""
    db = tmp_path / "ck.sqlite"
    config = {"configurable": {"thread_id": "u1:parent:c-heal"}}

    async def poison_then_repair():
        checkpointer = DurableCheckpointer(db)
        agent = _graph(checkpointer)
        await agent.ainvoke({"messages": [HumanMessage(content="hi")]}, config=config)
        await agent.aupdate_state(
            config,
            {
                "messages": [
                    AIMessage(
                        id="dangling-2",
                        content="",
                        tool_calls=[
                            {
                                "name": "tavily_search",
                                "args": {},
                                "id": "call-2",
                                "type": "tool_call",
                            }
                        ],
                    )
                ]
            },
            as_node="model",
        )
        await repair_thread(agent, config)
        await checkpointer.aclose()

    async def after_restart():
        checkpointer = DurableCheckpointer(db)
        agent = _graph(checkpointer)
        state = await agent.aget_state(config)
        await checkpointer.aclose()
        return [m for m in state.values["messages"] if getattr(m, "tool_calls", None)]

    asyncio.run(poison_then_repair())
    assert asyncio.run(after_restart()) == [], (
        "the repair did not persist — the poisoned checkpoint returned after restart"
    )


# ── 4. the delete cascade reaches checkpoints ────────────────────────


def test_delete_user_threads_purges_every_surface(tmp_path, monkeypatch):
    """`DELETE /family/{id}` promises "delete my data". Checkpoints hold every
    verbatim turn and used to evaporate on their own; now they must be swept —
    across the parent text/voice, onboarding and per-kid threads."""
    import app.checkpointing as checkpointing_module

    checkpointer = DurableCheckpointer(tmp_path / "ck.sqlite")
    monkeypatch.setattr(checkpointing_module, "checkpointer", checkpointer)

    async def seed():
        agent = _graph(checkpointer, replies=("ok",) * 20)
        for thread_id in (
            "victim:parent",
            "victim:parent:c-1",
            "victim:default",
            "onboarding:victim:default",
            "kid:victim:Ben:default",
            "bystander:parent",
        ):
            await agent.ainvoke(
                {"messages": [HumanMessage(content="x")]},
                config={"configurable": {"thread_id": thread_id}},
            )
        await checkpointer.aclose()

    asyncio.run(seed())
    assert len(checkpointer.thread_ids()) == 6

    deleted = delete_user_threads("victim")

    remaining = checkpointer.thread_ids()
    checkpointer.close_sync()
    assert deleted == 5, f"expected 5 threads purged, got {deleted}"
    assert remaining == ["bystander:parent"], (
        f"delete swept the wrong threads: {remaining}"
    )


def test_delete_family_route_sweeps_checkpoints():
    """Source-level: the route must call the sweep. A cascade that forgets it
    leaves a deleted family's conversations on disk."""
    src = (BACKEND_ROOT / "app" / "server.py").read_text()
    assert "delete_user_threads" in src, (
        "DELETE /family/{user_id} no longer purges agent checkpoints — a deleted "
        "family's verbatim conversations would survive on the volume"
    )


# ── 5. the file is user state: never committed, never in the image ───


def test_checkpoint_file_respects_the_storage_path_convention(tmp_path, monkeypatch):
    """The file belongs beside the DuckDB (the Railway volume), NOT at the
    backend root — a loose state file there is the known deploy hazard."""
    from app.checkpointing import CHECKPOINT_FILENAME, checkpoint_db_path

    monkeypatch.setenv("MVP_DUCKDB_PATH", str(tmp_path / "vol" / "mvp.duckdb"))
    monkeypatch.delenv("MVP_CHECKPOINT_DB_PATH", raising=False)
    path = checkpoint_db_path()
    assert path.parent == tmp_path / "vol"
    assert path.name == CHECKPOINT_FILENAME
    assert path.suffix != ".parquet"

    monkeypatch.setenv("MVP_CHECKPOINT_DB_PATH", str(tmp_path / "explicit.sqlite"))
    assert checkpoint_db_path() == tmp_path / "explicit.sqlite"


def test_checkpoint_file_is_excluded_from_the_docker_build_context():
    from app.checkpointing import CHECKPOINT_FILENAME

    ignored = {
        line.strip()
        for line in (BACKEND_ROOT / ".dockerignore").read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert f"data/{CHECKPOINT_FILENAME}" in ignored, (
        "the durable checkpoint file is NOT dockerignored — `railway up` would "
        "bake local conversations into the image (memory "
        "`debugging_railway_parquet_deploy_hazard`)"
    )


def test_checkpoint_file_is_gitignored():
    from app.checkpointing import CHECKPOINT_FILENAME

    gitignore = (BACKEND_ROOT.parent / ".gitignore").read_text()
    assert CHECKPOINT_FILENAME in gitignore, (
        "the durable checkpoint file is NOT gitignored — every parent's verbatim "
        "conversation would be committable"
    )
