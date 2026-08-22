"""Account deletion must evict the in-memory chat/onboarding thread stores.

Found live in prod (2026-08-10): two accounts Greg deleted kept their coach
conversations in `user_data`. `delete_family` cascaded the DB rows correctly,
but `chat_memory` / `onboarding_memory` are process-local singletons that
`persist_state()` flushes back into `user_data` — so as long as the deleted
user's id stayed in those stores, every subsequent persist (any other user's
save, any /data/export) REWROTE the deleted conversations into the DB. The
delete held for milliseconds.

Same bug class as memory `debugging_inmemory_singleton_delete` (the profiling
cache had the identical hole earlier); this locks the two thread stores.

A throwaway DuckDB is selected via MVP_DUCKDB_PATH before importing app.server,
mirroring tests/test_profile_edit.py, and the storage singleton is rebuilt in
teardown (tests/test_testclient pattern — TestClient exit closes storage).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "del_evict.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from app.memory import MemoryRepository  # noqa: E402


# --------------------------------------------------------------------------- #
# Pure unit: the store can actually forget a user
# --------------------------------------------------------------------------- #


def test_memory_repository_remove_user_forgets_everything():
    repo = MemoryRepository()
    repo.append_message("victim", "t-1", "user", "hello")
    repo.append_message("victim", "t-1", "assistant", "hi Greg")
    repo.append_message("bystander", "t-9", "user", "unrelated")

    repo.remove_user("victim")

    assert "victim" not in repo.user_ids()
    assert repo.snapshot_user("victim") == {}
    # A second removal is a no-op, never a KeyError.
    repo.remove_user("victim")
    # The bystander is untouched.
    assert repo.snapshot_user("bystander") == {"t-9": [{"role": "user", "content": "unrelated"}]}


# --------------------------------------------------------------------------- #
# Behavior: after deletion + eviction, persist_state cannot resurrect the rows
# --------------------------------------------------------------------------- #


def test_persist_after_delete_does_not_resurrect_chat_threads():
    from app import server

    from app.duckdb_storage import DuckDBStorage

    victim = "evict-victim"
    try:
        # Seed a conversation through the in-memory store and persist it — the
        # exact write path that resurrected Greg's deleted chats.
        server.chat_memory.append_message(victim, "t-1", "user", "Yo")
        server.chat_memory.append_message(victim, "t-1", "assistant", "Hey Greg.")
        server.persist_state(victim)
        assert server.storage_backend.load_user_data(victim, "chat_threads"), (
            "seed failed — persist_state should have written the thread"
        )

        # The delete cascade + the route's eviction (the fix under test).
        server.storage_backend.delete_family(user_id=victim, actor="test")
        server.chat_memory.remove_user(victim)
        server.onboarding_memory.remove_user(victim)

        # A subsequent full persist (any other user's save, any export) must
        # NOT bring the conversation back.
        server.persist_state()
        assert not server.storage_backend.load_user_data(victim, "chat_threads"), (
            "deleted user's chat_threads resurrected — the in-memory store "
            "still held the id at persist time"
        )
    finally:
        server.chat_memory.remove_user(victim)
        server.onboarding_memory.remove_user(victim)
        server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


# --------------------------------------------------------------------------- #
# Source-level: the route must call the evictions (pattern from
# test_delete_family_route_sweeps_checkpoints)
# --------------------------------------------------------------------------- #


def test_delete_family_route_evicts_thread_stores():
    src = (BACKEND_ROOT / "app" / "server.py").read_text()
    assert "chat_memory.remove_user" in src and "onboarding_memory.remove_user" in src, (
        "DELETE /family/{user_id} no longer evicts the in-memory thread stores — "
        "the next persist_state() resurrects the deleted family's conversations"
    )
