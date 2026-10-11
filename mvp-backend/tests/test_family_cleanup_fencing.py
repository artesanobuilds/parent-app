"""Deletion/reset drains runs and verifies both durable cleanup obligations."""
import asyncio
import threading

import pytest
from langgraph.checkpoint.base import empty_checkpoint

from app import checkpointing
from app.agent_runtime.context import RunContext
from app.agent_runtime.service import FamilyAdmissionClosed, owned_stream
from app.duckdb_storage import DuckDBStorage
from app.services.operations import run_scope


@pytest.fixture
def store(tmp_path, monkeypatch):
    storage = DuckDBStorage(db_path=tmp_path / 'family.duckdb')
    saver = checkpointing.DurableCheckpointer(tmp_path / 'checkpoints.sqlite')
    monkeypatch.setattr(checkpointing, 'checkpointer', saver)
    yield storage
    saver.close_sync()
    storage._con.close()


def seed_checkpoint(thread):
    checkpointing.checkpointer.put(
        {'configurable': {'thread_id': thread, 'checkpoint_ns': ''}},
        empty_checkpoint(), {'source': 'input', 'step': -1, 'parents': {}}, {},
    )


def test_failed_or_unverified_checkpoint_purge_stays_pending_and_retries(store, monkeypatch):
    seed_checkpoint('victim:parent')
    seed_checkpoint('neighbor:parent')
    store.reset_family(user_id='victim', actor='test')
    original = checkpointing.checkpointer.delete_thread
    monkeypatch.setattr(checkpointing.checkpointer, 'delete_thread', lambda _: None)
    assert checkpointing.purge_family_checkpoints(store, 'victim') == 0
    assert store.pending_checkpoint_purges()
    with pytest.raises(PermissionError):
        with run_scope(store, 'victim', 'new-run', 'victim:parent'):
            pass
    monkeypatch.setattr(checkpointing.checkpointer, 'delete_thread', original)
    asyncio.run(checkpointing.retry_pending_checkpoint_purges(store))
    assert store.pending_family_cleanups() == []
    assert checkpointing.checkpointer.thread_ids() == ['neighbor:parent']
    with run_scope(store, 'victim', 'new-run', 'victim:parent'):
        pass


def test_orphan_checkpoint_writes_are_included_in_verified_purge(store):
    checkpointing.checkpointer.put_writes(
        {'configurable': {'thread_id': 'victim:voice', 'checkpoint_ns': '', 'checkpoint_id': 'missing'}},
        [('messages', 'unfinished')], 'task',
    )
    assert checkpointing.checkpointer.thread_ids() == ['victim:voice']
    store.delete_family(user_id='victim', actor='test')
    assert checkpointing.purge_family_checkpoints(store, 'victim') == 1
    assert checkpointing.checkpointer.thread_ids() == []
    assert store.pending_checkpoint_purges() == []


def test_older_purge_cannot_clear_a_newer_reset_obligation(store):
    store.reset_family(user_id='victim', actor='test')
    generation = store.pending_checkpoint_purges()[0]['generation']
    store.reset_family(user_id='victim', actor='test')
    assert not store.mark_checkpoint_purged('victim', generation)
    assert store.pending_checkpoint_purges()[0]['generation'] == generation + 1


def test_reset_crash_before_snapshot_export_cannot_restore_old_data(tmp_path, monkeypatch):
    path = tmp_path / 'reset.duckdb'
    saver = checkpointing.DurableCheckpointer(tmp_path / 'reset-checkpoints.sqlite')
    monkeypatch.setattr(checkpointing, 'checkpointer', saver)
    storage = DuckDBStorage(db_path=path)
    storage.get_or_create_account('victim', primary_email='victim@example.test')
    storage.save_user_data('victim', 'profiles', {'parent': {'name': 'Before reset'}})
    storage.add_todo('victim', title='Before reset')
    storage.export_all_parquet()
    seed_checkpoint('victim:parent')
    storage.reset_family(user_id='victim', actor='test')
    storage._con.close()  # simulate crash: deliberately skip close() export
    reopened = DuckDBStorage(db_path=path)
    try:
        assert reopened.load_user_data('victim', 'profiles') is None
        assert reopened.list_todos('victim') == []
        assert reopened.user_exists('victim')  # reset retains sign-in identity
        with pytest.raises(PermissionError):
            reopened.assert_family_writable('victim')
        asyncio.run(checkpointing.retry_pending_checkpoint_purges(reopened))
        assert reopened.pending_family_cleanups() == []
        reopened.save_user_data('victim', 'profiles', {'parent': {'name': 'After reset'}})
        reopened.close()
        reopened = DuckDBStorage(db_path=path)
        assert reopened.load_user_data('victim', 'profiles')['parent']['name'] == 'After reset'
    finally:
        reopened._con.close()
        saver.close_sync()


def test_snapshot_export_failure_remains_durable_and_retryable(store, monkeypatch):
    store.save_user_data('victim', 'profiles', {'parent': {'name': 'Old'}})
    store.export_all_parquet()
    store.reset_family(user_id='victim', actor='test')
    store.mark_checkpoint_purged('victim')
    original = store._export_table_atomic
    def fail(table, target):
        if table == 'user_data':
            raise OSError('injected full disk')
        return original(table, target)
    monkeypatch.setattr(store, '_export_table_atomic', fail)
    with pytest.raises(OSError):
        store.refresh_family_snapshots('victim')
    assert store.pending_family_cleanups()
    with pytest.raises(PermissionError):
        store.assert_family_writable('victim')
    monkeypatch.setattr(store, '_export_table_atomic', original)
    asyncio.run(checkpointing.retry_pending_checkpoint_purges(store))
    assert store.pending_family_cleanups() == []


def test_delete_drains_active_writer_and_queued_turn_before_cascade(store, monkeypatch):
    from app import server, blobs
    monkeypatch.setattr(server, 'storage_backend', store)
    monkeypatch.setattr(blobs, 'delete_all', lambda *_: 0)
    entered, release = threading.Event(), threading.Event()
    queued_started = []
    def slow_writer():
        entered.set()
        release.wait(3)
        store.save_user_data('victim', 'profiles', {'parent': {'name': 'Last write'}})
        seed_checkpoint('victim:parent')
    async def active(disconnected):
        await asyncio.to_thread(slow_writer)
        yield 'old output'
    async def queued(disconnected):
        queued_started.append(True)
        yield 'must not execute'
    async def consume(factory):
        async for _ in owned_stream(RunContext('victim', 'parent', 'victim:parent'), factory):
            pass
    async def scenario():
        first = asyncio.create_task(consume(active))
        assert await asyncio.to_thread(entered.wait, 2)
        waiting = asyncio.create_task(consume(queued))
        await asyncio.sleep(.01)
        deletion = asyncio.create_task(server.delete_family('victim', authenticated_user='victim'))
        await asyncio.sleep(.03)
        assert not deletion.done()
        assert not store.pending_family_cleanups()  # no cascade before joining
        with pytest.raises(FamilyAdmissionClosed):
            await consume(queued)
        release.set()
        result = await deletion
        await asyncio.gather(first, waiting)
        assert set(result) == {'ok', 'user_id', 'deleted'}
    try:
        asyncio.run(scenario())
    finally:
        release.set()
    assert queued_started == []
    assert store.load_user_data('victim', 'profiles') is None
    assert checkpointing.checkpointer.thread_ids() == []
    assert store.pending_family_cleanups() == []
    with pytest.raises(PermissionError):
        store.save_user_data('victim', 'profiles', {})


def test_canceled_delete_request_holds_admission_until_cleanup_finishes(store, monkeypatch):
    from app import server
    started, release = threading.Event(), threading.Event()
    def cleanup(*args):
        started.set()
        release.wait(3)
        return {'ok': True}
    monkeypatch.setattr(server, '_delete_family_data', cleanup)
    async def never(disconnected):
        yield 'must not start'
    async def scenario():
        task = asyncio.create_task(server.delete_family('victim', authenticated_user='victim'))
        assert await asyncio.to_thread(started.wait, 2)
        task.cancel()
        await asyncio.sleep(.02)
        assert not task.done()
        with pytest.raises(FamilyAdmissionClosed):
            async for _ in owned_stream(RunContext('victim', 'parent', 'victim:parent'), never):
                pass
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
    try:
        asyncio.run(scenario())
    finally:
        release.set()


def test_partial_snapshot_export_does_not_restore_orphan_kid_messages(tmp_path, monkeypatch):
    path = tmp_path / 'partial.duckdb'
    storage = DuckDBStorage(db_path=path)
    storage.get_or_create_account('victim')
    config = storage.save_kid_agent_config('victim', 'Child', {}, '', 'test', 'hash', 'test', True)
    storage.append_kid_message(config['id'], 'default', 'user', 'private child message')
    storage.export_all_parquet()
    storage.reset_family(user_id='victim', actor='test')
    original = storage._export_table_atomic
    def fail_child(table, target):
        if table == 'kid_messages':
            raise OSError('partial snapshot write')
        original(table, target)
    monkeypatch.setattr(storage, '_export_table_atomic', fail_child)
    with pytest.raises(OSError):
        storage.refresh_family_snapshots('victim')
    storage._con.close()  # no best-effort shutdown export
    reopened = DuckDBStorage(db_path=path)
    try:
        assert reopened._con.execute('SELECT count(*) FROM kid_agent_configs').fetchone()[0] == 0
        assert reopened._con.execute('SELECT count(*) FROM kid_messages').fetchone()[0] == 0
        assert reopened.user_exists('victim')
        reopened.mark_checkpoint_purged('victim')
        reopened.refresh_family_snapshots('victim')
        assert reopened.pending_family_cleanups() == []
        child_file = str(reopened.parquet_dir / 'kid_messages.parquet')
        assert reopened._con.execute('SELECT count(*) FROM read_parquet(?)', [child_file]).fetchone()[0] == 0
    finally:
        reopened._con.close()


def test_reset_cannot_reopen_permanently_deleted_family(store):
    store.delete_family(user_id='victim', actor='test')
    with pytest.raises(PermissionError):
        store.reset_family(user_id='victim', actor='racing-admin')
    assert store._con.execute("SELECT deleted FROM agent_family_fences WHERE user_id='victim'").fetchone()[0]


def test_bootstrap_orphan_cleanup_preserves_other_family_children(tmp_path):
    path = tmp_path / 'joins.duckdb'
    storage = DuckDBStorage(db_path=path)
    config = storage.save_kid_agent_config('neighbor', 'Kid', {}, '', 'test', 'hash', 'test', True)
    storage.append_kid_message(config['id'], 'default', 'user', 'keep', message_id='keep-kid')
    storage.append_kid_message('missing-config', 'default', 'user', 'orphan', message_id='orphan-kid')
    storage._con.execute("INSERT INTO registration_windows(id,user_id) VALUES ('window','neighbor')")
    storage._con.execute("INSERT INTO window_notifications(id,window_id,kind) VALUES ('keep-window','window','day_of'),('orphan-window','missing-window','day_of')")
    storage._con.execute("INSERT INTO circle_conversations(id,owner_user_id,title) VALUES ('circle','neighbor','Keep')")
    storage._con.execute("INSERT INTO circle_messages(id,conversation_id,user_id,body) VALUES ('keep-circle','circle','neighbor','keep'),('orphan-circle','missing-circle','neighbor','orphan')")
    storage._con.execute("INSERT INTO circle_participants(conversation_id,user_id,member_id) VALUES ('circle','neighbor','keep-member'),('missing-circle','neighbor','orphan-member')")
    storage.export_all_parquet()
    storage._con.close()
    reopened = DuckDBStorage(db_path=path)
    try:
        for table, column, expected in (
            ('kid_messages', 'id', 'keep-kid'),
            ('window_notifications', 'id', 'keep-window'),
            ('circle_messages', 'id', 'keep-circle'),
            ('circle_participants', 'member_id', 'keep-member'),
        ):
            assert reopened._con.execute(f'SELECT {column} FROM {table}').fetchall() == [(expected,)]
    finally:
        reopened._con.close()
