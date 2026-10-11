"""Fault injection around the domain commit / checkpoint boundary (offline)."""
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END


def tool_graph(tools):
    builder = StateGraph(MessagesState)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "tools")
    builder.add_edge("tools", END)
    return builder.compile()

from app.duckdb_storage import DuckDBStorage
from app.services.operations import (
    OperationConflict, execute, reconcile_receipts, run_scope,
)


@pytest.fixture
def storage(tmp_path):
    db = DuckDBStorage(tmp_path / "durable.duckdb")
    yield db
    db._con.close()


def test_committed_todo_replay_survives_missing_checkpoint(storage):
    from app.cos.tools import _make_add_todo_tool
    tool = _make_add_todo_tool("alice")
    call = {"name": "AddTodo", "args": {"title": "Register"}, "id": "call-1", "type": "tool_call"}
    node = tool_graph([tool])
    with run_scope(storage, "alice", "run-1", "parent:alice:default"):
        first = node.invoke({"messages": [AIMessage(content="", tool_calls=[call])]})
    # Crash before ToolMessage was checkpointed; a later run replays the SAME id.
    with run_scope(storage, "alice", "run-2", "parent:alice:default"):
        second = node.invoke({"messages": [AIMessage(content="", tool_calls=[call])]})
    assert first["messages"][-1].content == second["messages"][-1].content
    assert len(storage.list_todos("alice")) == 1
    assert storage._con.execute("SELECT count(*) FROM agent_operation_receipts").fetchone()[0] == 1
    assert "runtime" not in tool.tool_call_schema.model_json_schema()["properties"]


def test_new_model_call_is_not_deduplicated(storage):
    with run_scope(storage, "alice", "r", "thread"):
        for operation in ["a", "b"]:
            execute("alice", operation, "AddTodo", {"title": "Same"},
                    lambda: storage.add_todo("alice", title="Same"))
    assert len(storage.list_todos("alice")) == 2


def test_receipt_rejects_argument_mismatch(storage):
    with run_scope(storage, "alice", "r", "thread"):
        execute("alice", "op", "AddTodo", {"title": "A"}, lambda: storage.add_todo("alice", title="A"))
        with pytest.raises(OperationConflict):
            execute("alice", "op", "AddTodo", {"title": "B"}, lambda: storage.add_todo("alice", title="B"))
    assert len(storage.list_todos("alice")) == 1


def test_mutation_and_receipt_rollback_together(storage, monkeypatch):
    original = storage._con.execute
    def fail_receipt(sql, params=None):
        if sql.startswith("INSERT INTO agent_operation_receipts"):
            raise OSError("disk full")
        return original(sql, params)
    with run_scope(storage, "alice", "r", "thread"):
        monkeypatch.setattr(storage._con, "execute", fail_receipt)
        with pytest.raises(OSError):
            execute("alice", "op", "AddTodo", {}, lambda: storage.add_todo("alice", title="A"))
    assert storage.list_todos("alice") == []


def test_profile_commit_failure_does_not_pollute_cache(storage, monkeypatch):
    from app.services.profiles import update_parent
    from app.profiling import profiling_service
    profiling_service.replace_family_snapshot("alice", {"parent": {"name": "Original"}})
    storage.save_user_data("alice", "profiles", {"parent": {"name": "Original"}})
    with run_scope(storage, "alice", "r", "thread"):
        monkeypatch.setattr(storage, "save_user_data", lambda *a: (_ for _ in ()).throw(OSError("disk full")))
        with pytest.raises(OSError):
            execute("alice", "op", "LearnedAboutParent", {}, lambda: update_parent("alice", {"name": "Lost"}))
    assert profiling_service.get_family_profile("alice")["parent"]["name"] == "Original"
    assert storage.load_user_data("alice", "profiles")["parent"]["name"] == "Original"


def test_profile_tool_commits_then_refreshes_for_voice_and_text(storage):
    from app.agent import _make_parent_tool, ParentUpdate
    from app.onboarding_agent import ParentUpdate as OnboardingParentUpdate
    from app.profiling import profiling_service
    assert ParentUpdate is OnboardingParentUpdate
    assert "secondary_language" in ParentUpdate.model_fields
    node = tool_graph([_make_parent_tool("alice")])
    call = {"name": "LearnedAboutParent", "args": {"parent_updates": {"secondary_language": "es"}},
            "id": "profile-op", "type": "tool_call"}
    with run_scope(storage, "alice", "voice", "voice:alice"):
        result = node.invoke({"messages": [AIMessage(content="", tool_calls=[call])]})
    assert result["messages"][-1].content == "Parent profile updated."
    assert storage.load_user_data("alice", "profiles")["parent"]["secondary_language"] == "es"
    assert profiling_service.get_family_profile("alice")["parent"]["secondary_language"] == "es"


def test_tenant_and_resource_ownership(storage):
    todo = storage.add_todo("bob", title="Private")
    with run_scope(storage, "alice", "r", "thread"):
        with pytest.raises(PermissionError):
            execute("bob", "op", "AddTodo", {}, lambda: None)
        with pytest.raises(PermissionError):
            execute("alice", "op", "CompleteTodo", {"todo_id": todo},
                    lambda: storage.update_todo(todo, status="done"))
    assert storage.list_todos("bob")[0]["status"] == "open"


def test_family_delete_fences_old_and_new_runs_and_purges_receipts(storage):
    with run_scope(storage, "alice", "r", "thread"):
        execute("alice", "op", "AddTodo", {}, lambda: storage.add_todo("alice", title="A"))
        storage.delete_family(user_id="alice", actor="alice")
        with pytest.raises(PermissionError):
            execute("alice", "late", "AddTodo", {}, lambda: storage.add_todo("alice", title="Zombie"))
        with pytest.raises(PermissionError):
            storage.save_user_data("alice", "chat_threads", {"zombie": []})
    with pytest.raises(PermissionError):
        with run_scope(storage, "alice", "new", "thread"):
            pass
    assert storage._con.execute("SELECT count(*) FROM agent_runs").fetchone()[0] == 0
    assert storage._con.execute("SELECT count(*) FROM agent_operation_receipts").fetchone()[0] == 0
    assert storage._con.execute("SELECT checkpoint_purge_pending FROM agent_family_fences").fetchone()[0]


def test_reset_fences_old_run_but_accepts_new_onboarding(storage):
    with run_scope(storage, "alice", "r", "thread"):
        storage.reset_family(user_id="alice", actor="admin")
        with pytest.raises(PermissionError):
            execute("alice", "late", "AddTodo", {}, lambda: None)
    with run_scope(storage, "alice", "new", "thread"):
        execute("alice", "op", "AddTodo", {}, lambda: storage.add_todo("alice", title="New"))
    assert len(storage.list_todos("alice")) == 1


@pytest.mark.asyncio
async def test_reconcile_committed_receipt_before_generic_repair(storage):
    from app.services.operations import argument_digest
    messages = [AIMessage(id="ai", content="", tool_calls=[
        {"name": "AddTodo", "args": {"title": "A"}, "id": "op", "type": "tool_call"}
    ])]
    class Graph:
        updated = None
        async def aget_state(self, config):
            return SimpleNamespace(values={"messages": messages})
        async def aupdate_state(self, config, updates, **kwargs):
            self.updated = updates
    graph = Graph()
    with run_scope(storage, "alice", "r1", "thread"):
        execute("alice", "op", "AddTodo", {"title": "A"}, lambda: "Added A (id=one)")
    with run_scope(storage, "alice", "r2", "thread"):
        assert await reconcile_receipts(SimpleNamespace(user_id="alice"), graph, {}) == 1
    assert isinstance(graph.updated["messages"][-1], ToolMessage)
    assert graph.updated["messages"][-1].content == "Added A (id=one)"


def test_nested_failure_cannot_commit_partial_command(storage):
    with pytest.raises(RuntimeError, match="Nested transaction failed"):
        with storage.transaction():
            storage.add_todo("alice", title="partial")
            try:
                with storage.transaction():
                    raise ValueError("nested failure swallowed by legacy caller")
            except ValueError:
                pass
    assert storage.list_todos("alice") == []


def test_receipt_survives_database_reopen(tmp_path):
    path = tmp_path / "reopen.duckdb"
    first = DuckDBStorage(path)
    with run_scope(first, "alice", "r1", "thread"):
        identity = execute("alice", "op", "AddTodo", {"title": "A"},
                           lambda: first.add_todo("alice", title="A"))
    first._con.close()  # kill-like close without parquet export
    second = DuckDBStorage(path)
    try:
        with run_scope(second, "alice", "r2", "thread"):
            assert execute("alice", "op", "AddTodo", {"title": "A"},
                           lambda: pytest.fail("Committed mutation replayed")) == identity
        assert len(second.list_todos("alice")) == 1
    finally:
        second._con.close()


def test_deleted_family_is_not_resurrected_from_stale_snapshot(tmp_path):
    path = tmp_path / "reopen.duckdb"
    first = DuckDBStorage(path)
    first.save_user_data("alice", "profiles", {"parent": {"name": "A"}})
    first.add_todo("alice", title="Old task")
    first.export_all_parquet()
    first.delete_family(user_id="alice", actor="alice")
    first._con.close()  # simulate crash BEFORE exporting deletion
    second = DuckDBStorage(path)
    try:
        assert second.load_user_data("alice", "profiles") is None
        assert second.list_todos("alice") == []
        with pytest.raises(PermissionError):
            with run_scope(second, "alice", "new", "thread"):
                pass
    finally:
        second._con.close()


def test_lookup_commit_has_receipt_without_holding_lock_during_preparation(storage):
    from app.services.operations import prepared_tool, prepared_storage
    @prepared_tool("alice")
    def Lookup(activity_name: str) -> str:
        """Prepare outside the transaction, then save a local activity."""
        assert storage._con._transaction_depth == 0
        identity = prepared_storage(storage).track_activity("alice", name=activity_name, status="exploring")
        return f"Saved {identity}"
    node = tool_graph([Lookup])
    call = {"name": "Lookup", "args": {"activity_name": "Camp"}, "id": "lookup-1", "type": "tool_call"}
    for run_id in ["r1", "r2"]:
        with run_scope(storage, "alice", run_id, "thread"):
            node.invoke({"messages": [AIMessage(content="", tool_calls=[call])]})
    assert len(storage.list_tracked_activities("alice")) == 1


def test_populated_v24_upgrade_and_reboot(tmp_path):
    from app.migrations import run_migrations, current_version, MIGRATIONS
    path = tmp_path / "upgrade.duckdb"
    db = DuckDBStorage(path)
    db.save_user_data("alice", "profiles", {"parent": {"name": "Existing parent"}})
    identity = db.add_todo("alice", title="Existing task")
    for table in ["agent_operation_receipts", "agent_runs", "agent_family_fences"]:
        db._con.execute(f"DROP TABLE {table}")
    db._con.execute("DELETE FROM schema_migrations WHERE version >= 25")
    assert current_version(db._con) == 24
    run_migrations(db._con)
    run_migrations(db._con)  # restart must not reapply the additive migration
    assert current_version(db._con) == max(version for version, _, _ in MIGRATIONS)
    db._con.close()
    restored = DuckDBStorage(path)
    try:
        assert restored.load_user_data("alice", "profiles")["parent"]["name"] == "Existing parent"
        assert restored.list_todos("alice")[0]["id"] == identity
        with run_scope(restored, "alice", "run", "thread"):
            execute("alice", "op", "AddTodo", {"title": "New task"},
                    lambda: restored.add_todo("alice", title="New task"))
        assert len(restored.list_todos("alice")) == 2
    finally:
        restored._con.close()


def test_deleted_family_cannot_enqueue_new_background_jobs(storage):
    storage.delete_family(user_id="alice", actor="alice")
    for create in [
        lambda: storage.create_research_run(user_id="alice", location={}, kids=[]),
        lambda: storage.enqueue_research_run(user_id="alice", location={}, kids=[]),
        lambda: storage.create_warmup_run(user_id="alice", steps=[]),
        lambda: storage.enqueue_warmup_run(user_id="alice", steps=[]),
    ]:
        with pytest.raises(PermissionError):
            create()
    assert storage._con.execute("SELECT count(*) FROM research_runs").fetchone()[0] == 0
    assert storage._con.execute("SELECT count(*) FROM onboarding_warmup_runs").fetchone()[0] == 0


def test_concurrent_receipt_replay_commits_one_effect(storage):
    from concurrent.futures import ThreadPoolExecutor
    def perform(run_id):
        with run_scope(storage, "alice", run_id, "thread"):
            return execute("alice", "same-call", "AddTodo", {"title": "A"},
                           lambda: storage.add_todo("alice", title="A"))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(perform, ["r1", "r2"]))
    assert results[0] == results[1]
    assert len(storage.list_todos("alice")) == 1


def test_profile_read_failure_cannot_replace_existing_family(storage, monkeypatch):
    from app.services.profiles import update_parent
    storage.save_user_data("alice", "profiles", {"parent": {"name": "Original"}})
    original = storage._con.execute
    def fail_profile_read(sql, params=None):
        if sql.startswith("SELECT data FROM user_data"):
            raise OSError("read failure")
        return original(sql, params)
    with run_scope(storage, "alice", "r", "thread"):
        with monkeypatch.context() as patch:
            patch.setattr(storage._con, "execute", fail_profile_read)
            with pytest.raises(OSError):
                execute("alice", "op", "LearnedAboutParent", {},
                        lambda: update_parent("alice", {"name": "Lost"}))
    assert storage.load_user_data("alice", "profiles")["parent"]["name"] == "Original"
