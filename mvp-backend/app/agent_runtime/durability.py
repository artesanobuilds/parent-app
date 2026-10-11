"""Durable transcript projections; adapters retain their existing wire contracts."""
import json

from app.services.operations import current_run, run_scope, reconcile_receipts, publication_lock


def scope_for(storage):
    return lambda context: run_scope(storage, context.user_id, context.run_id, context.thread_key)


def _assert_run(storage, context):
    run = current_run()
    if run is None or run.user_id != context.user_id or run.run_id != context.run_id:
        raise PermissionError("Transcript write requires its authenticated run")
    storage.assert_family_writable(context.user_id, run.generation)


def append_transcript(storage, context, blob_name, thread_id, role, content, *, memory=None):
    """Commit before exposing the new entry in the in-process history cache.

    Read the current JSON under the same writer lock so independent threads do
    not replace each other's projections. Voice uses parent_voice_threads, an
    internal projection with the same family deletion and snapshot retention as
    other user_data blobs; public history endpoints remain unchanged.
    """
    with publication_lock(storage):
        with storage.transaction():
            _assert_run(storage, context)
            row = storage._con.execute(
                "SELECT data FROM user_data WHERE user_id = ? AND name = ?",
                [context.user_id, blob_name],
            ).fetchone()
            snapshot = json.loads(row[0]) if row else {}
            snapshot.setdefault(thread_id, []).append({"role": role, "content": content})
            storage.save_user_data(context.user_id, blob_name, snapshot)
        if memory is not None:
            memory.load_user_snapshot(context.user_id, snapshot)
    # Retain the existing per-turn parquet refresh. Database commit is the
    # source of truth, including when a later snapshot export fails.
    storage.export_parquet()


def append_cos_transcript(storage, context, thread_id, role, content):
    with storage.transaction():
        _assert_run(storage, context)
        storage.append_cos_message(context.user_id, thread_id=thread_id, role=role, content=content)


async def repair_with_receipts(context, agent, config, repair):
    await reconcile_receipts(context, agent, config)
    await repair(agent, config)


def ensure_connected(disconnected):
    if disconnected is not None and disconnected.is_set():
        from app.agent_runtime.service import RunInterrupted
        raise RunInterrupted("Turn disconnected before durable completion")
