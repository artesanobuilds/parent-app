import asyncio
import sqlite3

import pytest

from app.checkpointing import DurableCheckpointer


def test_compiled_schema_clones_reused_across_graph_rebuilds(tmp_path):
    root = DurableCheckpointer(tmp_path / 'checkpoints.sqlite')
    schema_a = [('example', 'ParentState')]
    schema_b = [('example', 'KidState')]
    parent = root.with_allowlist(schema_a)
    assert all(root.with_allowlist(schema_a) is parent for _ in range(100))
    combined = parent.with_allowlist(schema_b)
    assert root.with_allowlist(schema_b + schema_a) is combined
    assert len(root._schema_clones) == 3


def test_shutdown_closes_schema_clone_sync_connections(tmp_path):
    root = DurableCheckpointer(tmp_path / 'checkpoints.sqlite')
    child = root.with_allowlist([('example', 'State')])
    connection = child._sync().conn
    connection.execute('SELECT 1')
    root.close_sync()
    assert child._sync_saver is None
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute('SELECT 1')


def test_shutdown_closes_all_current_loop_clone_connections(tmp_path):
    async def run():
        root = DurableCheckpointer(tmp_path / 'checkpoints.sqlite')
        children = [root.with_allowlist([('example', name)]) for name in ('Parent', 'Kid')]
        for child in children:
            assert await child.aget_tuple({'configurable': {'thread_id': 'empty'}}) is None
        assert all(child._async_savers for child in children)
        await root.aclose()
        assert all(not child._async_savers for child in children)
        # A later lifespan may reuse the compiled graph but gets a fresh connection.
        assert await children[0].aget_tuple({'configurable': {'thread_id': 'empty'}}) is None
        await root.aclose()
    asyncio.run(run())
