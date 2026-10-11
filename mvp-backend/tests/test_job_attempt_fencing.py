"""Real DuckDB faults and cooperative cancellation; no vendor or production I/O."""
import asyncio
import threading
import time
from types import SimpleNamespace

import pytest

from app.duckdb_storage import DuckDBStorage
from app.jobs.context import JobContext, JobStopped
from app.jobs.runner import JobReaper
from app.jobs.middleware import JobDispatchMiddleware
from app.onboarding_warmup import OnboardingWarmupWorker, initial_steps, STEP_KEYS
from app.research.worker import ResearchWorker


@pytest.fixture
def store(tmp_path):
    storage = DuckDBStorage(db_path=tmp_path / 'jobs.duckdb')
    yield storage
    storage._con.close()


def claim(store, budget=600):
    store.create_research_run(user_id='family', location={}, kids=[])
    run = store.claim_next_queued_run(budget)
    return run, JobContext.from_run(store, 'research', run)


def expire(store, kind, run_id):
    store._con.execute(f"UPDATE {store._job_table(kind)} SET deadline_at=now()-INTERVAL '1 second' WHERE id=?", [run_id])


def test_cancel_during_discovery_never_publishes_candidates(store):
    run, ctx = claim(store)
    def discover(**kwargs):
        store.cancel_research_run(run['id'])
        return [{'name': 'late'}]
    ResearchWorker(store, discover).process_run(run)
    assert store.get_research_run(run['id'])['status'] == 'canceled'
    assert store.list_candidates(run_id=run['id']) == []
    with pytest.raises(JobStopped):
        store.update_job_progress(ctx, progress={'phase': 'late'})


def test_expired_attempt_cannot_finalize_new_attempt(store):
    run, old = claim(store)
    store.requeue_stale_running_runs()
    new_run = store.claim_next_queued_run()
    assert new_run['_attempt_token'] != run['_attempt_token']
    assert new_run['_deadline_at'] == run['_deadline_at']
    assert not store.publish_research_attempt(old, 'family', [{'name': 'stale'}], {})
    assert not store.finalize_job_attempt(old, status='failed')
    assert store.get_research_run(run['id'])['status'] == 'running'
    new = JobContext.from_run(store, 'research', new_run)
    assert store.publish_research_attempt(new, 'family', [{'name': 'current'}], {})
    assert store.list_candidates(run_id=run['id'])[0]['name'] == 'current'


def test_publication_failure_rolls_back_candidates_and_terminal_state(store, monkeypatch):
    run, ctx = claim(store)
    original = store.finalize_run_if_running
    def fault(*args, **kwargs):
        original(*args, **kwargs)
        raise OSError('crash before commit')
    monkeypatch.setattr(store, 'finalize_run_if_running', fault)
    with pytest.raises(OSError):
        store.publish_research_attempt(ctx, 'family', [{'name': 'uncommitted'}], {})
    assert store.list_candidates(run_id=run['id']) == []
    assert store.get_research_run(run['id'])['status'] == 'running'


def test_periodic_reaper_works_while_worker_slot_is_stuck(store):
    entered, release = threading.Event(), threading.Event()
    def stuck(**kwargs):
        entered.set()
        release.wait(5)
        return [{'name': 'late'}]
    run_id = store.create_research_run(user_id='family', location={}, kids=[])
    worker = ResearchWorker(store, stuck, concurrency=1, poll_interval=.01)
    worker._reaper.interval = .01
    worker.start()
    try:
        assert entered.wait(2)
        expire(store, 'research', run_id)
        end = time.monotonic() + 2
        while store.get_research_run(run_id)['status'] == 'running' and time.monotonic() < end:
            time.sleep(.01)
        assert store.get_research_run(run_id)['status'] == 'failed'
        assert not release.is_set(), 'reaper must be independent of busy workers'
    finally:
        release.set()
        worker.stop()
    assert store.list_candidates(run_id=run_id) == []


def test_restart_retry_does_not_reset_exhausted_run_budget(store):
    run, _ = claim(store)
    store.requeue_stale_running_runs()
    expire(store, 'research', run['id'])
    assert store.claim_next_queued_run(600) is None
    assert store.get_research_run(run['id'])['status'] == 'failed'


def test_late_warmup_step_cannot_write_or_mutate_next_step_context(store):
    release, returned = threading.Event(), threading.Event()
    errors = []
    def late(storage, user_id, ctx):
        release.wait(3)
        ctx['result']['late'] = True
        try:
            storage.upsert_coach_nudge(user_id=user_id, body='too late')
        except JobStopped as exc:
            errors.append(exc)
        finally:
            returned.set()
        return {}
    funcs = {key: lambda *_: {} for key in STEP_KEYS}
    funcs[STEP_KEYS[0]] = late
    run_id = store.create_warmup_run(user_id='family', steps=initial_steps())
    run = store.claim_next_queued_warmup_run()
    worker = OnboardingWarmupWorker(store, funcs, step_timeout=.05)
    try:
        worker.process_run(run)
        final = store.get_warmup_run(run_id)
        assert final['status'] == 'done'
        assert final['steps'][0]['state'] == 'failed'
        assert final['steps'][-1]['state'] == 'done'
        release.set()
        assert returned.wait(2)
        assert errors
        assert store.latest_coach_nudge('family') is None
        assert 'late' not in store.get_warmup_run(run_id)['result']
    finally:
        release.set()
        worker.stop()


def test_warmup_deadline_reaper_keeps_degraded_done_contract(store):
    run_id = store.create_warmup_run(user_id='family', steps=initial_steps())
    store.claim_next_queued_warmup_run()
    expire(store, 'warmup', run_id)
    assert store.reap_expired_job_attempts('warmup') == 1
    run = store.get_warmup_run(run_id)
    assert run['status'] == 'done'
    assert run['result']['failed_steps'] == STEP_KEYS
    assert all(step['state'] == 'failed' for step in run['steps'])


def test_async_provider_is_canceled_and_joined_when_job_canceled(store):
    run, ctx = claim(store)
    closed = []
    async def scenario():
        async def provider():
            try:
                await asyncio.sleep(5)
            finally:
                closed.append(True)
        async def cancel():
            await asyncio.sleep(.02)
            store.cancel_research_run(run['id'])
        cancel_task = asyncio.create_task(cancel())
        with pytest.raises(JobStopped):
            await ctx.wait(provider())
        await cancel_task
    asyncio.run(scenario())
    assert closed == [True]


def test_model_retry_rechecks_deadline_and_disables_sdk_retries(store):
    run, ctx = claim(store)
    calls = []
    class Model:
        def model_copy(self, update):
            return update
    class Request:
        model = Model()
        def override(self, **kwargs):
            return SimpleNamespace(**kwargs)
    async def handler(request):
        calls.append(request.model)
        expire(store, 'research', run['id'])
        raise TimeoutError('provider stalled')
    with pytest.raises(JobStopped):
        asyncio.run(JobDispatchMiddleware(ctx).awrap_model_call(Request(), handler))
    assert len(calls) == 1
    assert calls[0]['max_retries'] == 0
    assert 0 < calls[0]['request_timeout'] <= 120


def test_public_row_serializers_do_not_leak_claim_metadata(store):
    run, _ = claim(store)
    assert '_attempt_token' not in store.get_research_run(run['id'])
    assert 'deadline_at' not in store.list_research_runs('family')[0]


def test_bounded_openai_model_changes_actual_sdk_retry_policy():
    from langchain_openai import ChatOpenAI
    from app.jobs.middleware import bounded_model
    original = ChatOpenAI(model='test-model', api_key='sk-test', max_retries=7, timeout=120)
    bounded = bounded_model(original, .25)
    assert bounded.root_client.max_retries == 0
    assert bounded.root_async_client.max_retries == 0
    assert bounded.root_client.timeout == .25
    assert bounded.root_async_client.timeout == .25
    assert original.root_client.max_retries == 7


def test_real_research_graph_runs_through_async_job_middleware(store, monkeypatch):
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage
    # test_research_api replaces the shared module's discover function during
    # collection. Load this production file in isolation for a real graph test.
    import importlib.util
    import sys
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(
        'app.research._job_test_graph', Path(__file__).parents[1] / 'app/research/graph.py')
    graph = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, graph)
    spec.loader.exec_module(graph)
    class FakeModel(FakeMessagesListChatModel):
        def bind_tools(self, tools, **kwargs):
            return self
    fake = FakeModel(responses=[AIMessage(content='No results')])
    monkeypatch.setattr(graph, 'build_research_model', lambda: fake)
    run, ctx = claim(store)
    assert graph.discover_activities(location={}, kids=[], job_context=ctx) == []


def test_dispatch_guard_rejects_internal_model_and_tool_calls_after_cancel(store):
    from app.jobs.middleware import JobDispatchGuard
    run, ctx = claim(store)
    guard = JobDispatchGuard(ctx)
    store.cancel_research_run(run['id'])
    for dispatch in (guard.on_chat_model_start, guard.on_llm_start, guard.on_tool_start):
        with pytest.raises(JobStopped):
            dispatch({}, [])
    assert guard.raise_error  # LangChain must propagate, not log-and-ignore.


def test_saturated_warmup_pool_does_not_accumulate_queued_futures(store):
    release = threading.Event()
    calls = []
    def stuck(*args):
        calls.append(True)
        release.wait(3)
        return {}
    worker = OnboardingWarmupWorker(store, {key: stuck for key in STEP_KEYS},
                                     concurrency=1, step_timeout=.02)
    try:
        for _ in range(2):
            run_id = store.create_warmup_run(user_id='family', steps=initial_steps())
            worker.process_run(store.claim_next_queued_warmup_run())
            assert store.get_warmup_run(run_id)['status'] == 'done'
        assert len(calls) == 2  # occupied threads hold both slots until returning
    finally:
        release.set()
        worker.stop()


def test_attempt_fence_migration_preserves_populated_jobs_and_reruns(store):
    from app.migrations import run_migrations
    research_id = store.create_research_run(user_id='family', location={}, kids=[])
    warmup_id = store.create_warmup_run(user_id='family', steps=initial_steps())
    for table in ('research_runs', 'onboarding_warmup_runs'):
        indexes = store._con.execute(
            'SELECT index_name, sql FROM duckdb_indexes() WHERE table_name=?', [table]
        ).fetchall()
        for name, _ in indexes:
            store._con.execute(f'DROP INDEX "{name}"')
        for column in ('attempt_token', 'deadline_at', 'heartbeat_at'):
            store._con.execute(f'ALTER TABLE {table} DROP COLUMN {column}')
        for _, sql in indexes:
            store._con.execute(sql)
    store._con.execute('DELETE FROM schema_migrations WHERE version=26')
    run_migrations(store._con)
    assert store.claim_next_queued_run()['id'] == research_id
    assert store.claim_next_queued_warmup_run()['id'] == warmup_id
    store._con.execute('DELETE FROM schema_migrations WHERE version=26')
    run_migrations(store._con)
    assert store.get_research_run(research_id)['status'] == 'running'
    assert store.get_warmup_run(warmup_id)['status'] == 'running'


def test_warmup_storage_call_that_crosses_deadline_rolls_back(store, monkeypatch):
    entered, release, returned = threading.Event(), threading.Event(), threading.Event()
    original = store.upsert_coach_nudge
    errors = []
    def slow_commit(**kwargs):
        original(**kwargs)  # joins the step transaction, does not commit yet
        entered.set()
        release.wait(3)
    monkeypatch.setattr(store, 'upsert_coach_nudge', slow_commit)
    def late(storage, user_id, ctx):
        try:
            storage.upsert_coach_nudge(user_id=user_id, body='must rollback')
        except JobStopped as exc:
            errors.append(exc)
        finally:
            returned.set()
        return {}
    funcs = {key: lambda *_: {} for key in STEP_KEYS}
    funcs[STEP_KEYS[0]] = late
    run_id = store.create_warmup_run(user_id='family', steps=initial_steps())
    run = store.claim_next_queued_warmup_run()
    worker = OnboardingWarmupWorker(store, funcs, step_timeout=.04)
    thread = threading.Thread(target=worker.process_run, args=(run,))
    thread.start()
    try:
        assert entered.wait(2)
        time.sleep(.08)
        release.set()
        assert returned.wait(2)
        thread.join(2)
        assert errors
        assert store.latest_coach_nudge('family') is None
        assert store.get_warmup_run(run_id)['status'] == 'done'
    finally:
        release.set()
        thread.join(2)
        worker.stop()


def test_family_deletion_invalidates_research_and_warmup_attempts(store):
    from app.jobs.context import StepStorage
    run, research = claim(store)
    store.create_warmup_run(user_id='family', steps=initial_steps())
    warmup = JobContext.from_run(store, 'warmup', store.claim_next_queued_warmup_run())
    step = StepStorage(store, warmup, time.monotonic()+60, threading.Event())
    store.delete_family(user_id='family', actor='test')
    assert not store.publish_research_attempt(research, 'family', [{'name': 'orphan'}], {})
    with pytest.raises(JobStopped):
        step.upsert_coach_nudge(user_id='family', body='orphan')
    assert store.list_candidates(user_id='family') == []
    assert store.latest_coach_nudge('family') is None
