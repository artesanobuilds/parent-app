"""Force legacy snapshot writers into the durable commit/publication gap."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from app.agent_runtime.context import RunContext
from app.agent_runtime.durability import append_transcript
from app.duckdb_storage import DuckDBStorage
from app.memory import MemoryRepository
from app.profiling import ProfilingService
from app.services.operations import run_scope


@pytest.fixture
def state(tmp_path, monkeypatch):
    from app import server
    from app.services import profiles
    storage = DuckDBStorage(tmp_path / "state.duckdb")
    memory = MemoryRepository()
    profile = ProfilingService()
    monkeypatch.setattr(server, "storage_backend", storage)
    monkeypatch.setattr(server, "chat_memory", memory)
    monkeypatch.setattr(server, "onboarding_memory", MemoryRepository())
    monkeypatch.setattr(server, "profiling_service", profile)
    monkeypatch.setattr(profiles, "profiling_service", profile)
    monkeypatch.setattr(storage, "export_parquet", lambda: None)
    yield server, storage, memory, profile
    storage._con.close()


def race_snapshot(server, profile, monkeypatch, mutation, publication_owner, publication_name):
    """Pause after commit, then start the real legacy writer on another thread."""
    committed = Event()
    release_publication = Event()
    snapshot_started = Event()
    writer_started = Event()
    original_publish = getattr(publication_owner, publication_name)
    original_snapshot = profile.export_snapshot

    def pause_publication(*args, **kwargs):
        committed.set()
        assert release_publication.wait(5), "test did not release publication"
        return original_publish(*args, **kwargs)

    def record_snapshot():
        snapshot_started.set()
        return original_snapshot()

    def legacy_write():
        writer_started.set()
        server.persist_state("race-user")

    monkeypatch.setattr(publication_owner, publication_name, pause_publication)
    monkeypatch.setattr(profile, "export_snapshot", record_snapshot)
    with ThreadPoolExecutor(max_workers=2) as pool:
        producer = pool.submit(mutation)
        try:
            assert committed.wait(5), "mutation never reached publication"
            writer = pool.submit(legacy_write)
            assert writer_started.wait(5)
            # The writer cannot even snapshot a stale profile while publication
            # owns the DB lock. This catches moving only the write under lock.
            assert not snapshot_started.wait(0.2), "legacy writer read an unpublished cache"
            assert not writer.done()
        finally:
            release_publication.set()
        producer.result(timeout=5)
        writer.result(timeout=5)


def test_transcript_commit_and_publication_exclude_legacy_snapshot(state, monkeypatch):
    server, storage, memory, profile = state
    context = RunContext("race-user", "chat", "race-user:parent")

    def append():
        with run_scope(storage, context.user_id, context.run_id, context.thread_key):
            append_transcript(storage, context, "chat_threads", "parent", "user", "durable message", memory=memory)

    race_snapshot(server, profile, monkeypatch, append, memory, "load_user_snapshot")
    expected = {"parent": [{"role": "user", "content": "durable message"}]}
    assert storage.load_user_data("race-user", "chat_threads") == expected
    assert memory.snapshot_user("race-user") == expected


def test_profile_receipt_commit_and_refresh_exclude_legacy_snapshot(state, monkeypatch):
    from app.agent import _make_parent_tool, ParentUpdate
    from app.services import profiles
    server, storage, memory, profile = state
    profile.replace_family_snapshot("race-user", {"parent": {"name": "Original"}})
    storage.save_user_data("race-user", "profiles", profile.get_family_profile("race-user"))
    tool = _make_parent_tool("race-user")

    def update():
        with run_scope(storage, "race-user", "run", "parent:race-user"):
            result = tool.invoke({"parent_updates": ParentUpdate(name="Committed")})
            assert result == "Parent profile updated."

    race_snapshot(server, profile, monkeypatch, update, profiles, "refresh_profile")
    assert storage.load_user_data("race-user", "profiles")["parent"]["name"] == "Committed"
    assert profile.get_family_profile("race-user")["parent"]["name"] == "Committed"
    assert storage._con.execute("SELECT count(*) FROM agent_operation_receipts").fetchone()[0] == 1


def test_transcript_rollback_does_not_publish_cache(state, monkeypatch):
    from contextlib import contextmanager
    server, storage, memory, profile = state
    context = RunContext("race-user", "chat", "race-user:parent")
    transaction = storage.transaction

    @contextmanager
    def fail_before_commit():
        with transaction():
            yield
            raise OSError("commit failed")

    with run_scope(storage, context.user_id, context.run_id, context.thread_key):
        monkeypatch.setattr(storage, "transaction", fail_before_commit)
        with pytest.raises(OSError, match="commit failed"):
            append_transcript(storage, context, "chat_threads", "parent", "user", "lost", memory=memory)
    assert memory.snapshot_user("race-user") == {}
    assert storage.load_user_data("race-user", "chat_threads") is None


@pytest.mark.parametrize("surface", ["transcript", "profile"])
def test_cache_publication_rejects_uncommitted_outer_transaction(state, surface):
    from app.agent import _make_parent_tool, ParentUpdate
    server, storage, memory, profile = state
    context = RunContext("race-user", "chat", "race-user:parent")
    with run_scope(storage, context.user_id, context.run_id, context.thread_key):
        with storage.transaction():
            with pytest.raises(RuntimeError, match="outermost transaction"):
                if surface == "transcript":
                    append_transcript(storage, context, "chat_threads", "parent", "user", "lost", memory=memory)
                else:
                    _make_parent_tool("race-user").invoke({"parent_updates": ParentUpdate(name="lost")})
    assert storage.load_user_data("race-user", "chat_threads") is None
    assert storage.load_user_data("race-user", "profiles") is None
    assert memory.snapshot_user("race-user") == {}
    assert "race-user" not in profile.export_snapshot()
