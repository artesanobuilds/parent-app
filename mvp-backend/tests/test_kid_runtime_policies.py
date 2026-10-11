"""Kid text safety order across shared and compatibility execution paths."""
import asyncio
import json
from types import SimpleNamespace

import pytest


class Graph:
    def __init__(self, chunks):
        self.chunks = chunks
        self.calls = 0
    async def aget_state(self, config):
        return SimpleNamespace(values={'messages': []})
    async def astream_events(self, *args, **kwargs):
        self.calls += 1
        for content, tags in self.chunks:
            yield {'event': 'on_chat_model_stream', 'tags': tags,
                   'data': {'chunk': SimpleNamespace(content=content)}}


@pytest.fixture(params=[False, True])
def setup(monkeypatch, tmp_path, request):
    import app.server as server
    from app import moderation
    from app.duckdb_storage import DuckDBStorage
    storage = DuckDBStorage(tmp_path / 'kid.duckdb')
    moderation.unfreeze_all()
    moderation.revive_agent("agent-kid-policy")
    monkeypatch.setenv('MVP_SHARED_RUNTIME_KID_TEXT', '1' if request.param else '0')
    monkeypatch.setattr(server, 'storage_backend', storage)
    monkeypatch.setattr(server.profiling_service, 'get_family_profile', lambda _: {
        'children': {'Ada': {'age': 8}}})
    monkeypatch.setattr(server, '_dispatch_crisis_push', lambda *args: None)
    monkeypatch.setattr(server.telemetry, 'alert_crisis', lambda **kwargs: None)
    monkeypatch.setattr(server.telemetry, 'alert_moderation_event', lambda **kwargs: None)
    monkeypatch.setattr(moderation, 'moderate_with_openai', lambda text: moderation.ModerationResult(
        flagged=False, severity='low', category='ok', reason='offline', suggested_action='allow'))
    monkeypatch.setattr(moderation, 'classify_age_appropriate', lambda *args, **kwargs:
                        SimpleNamespace(age_appropriate=True))
    monkeypatch.setattr(moderation, 'OUTPUT_CHUNK_BUFFER_CHARS', 0)
    yield server, storage, moderation, monkeypatch
    storage.close()
    moderation.unfreeze_all()
    moderation.revive_agent("agent-kid-policy")


def install(setup, chunks):
    server, storage, moderation, monkeypatch = setup
    graph = Graph(chunks)
    monkeypatch.setattr(server.kid_agent_service, 'get_kid_agent', lambda *args: (
        graph, {'enabled': True, 'id': 'agent-kid-policy', 'invariants': {}}))
    return graph


async def frames(server, message='tell me a story'):
    result = []
    async for frame in server.generate_kid_stream('kid-family', 'Ada', 'kid-thread', message):
        result.append('[DONE]' if frame == 'data: [DONE]\n\n' else json.loads(frame[6:]))
    return result


def test_internal_output_filtered_before_kid_moderation(setup):
    server, storage, *_ = setup
    install(setup, [('internal summary', ['mvp:internal']), ('Safe story.', [])])
    result = asyncio.run(frames(server))
    assert result == [{'type': 'token', 'content': 'Safe story.'}, '[DONE]']
    assert storage.get_kid_messages('agent-kid-policy', 'kid-thread')[-1]['content'] == 'Safe story.'


def test_input_crisis_locks_before_stream_and_never_dispatches_graph(setup):
    server, storage, *_ = setup
    graph = install(setup, [('must never run', [])])
    async def run():
        seen = []
        async for frame in server.generate_kid_stream('kid-family', 'Ada', 'kid-thread',
                                                      'I want to hurt myself'):
            assert storage.is_kid_agent_crisis_locked('agent-kid-policy') is not None
            seen.append(frame)
        return seen
    result = asyncio.run(run())
    assert graph.calls == 0
    assert any('"type": "crisis"' in frame for frame in result)


def test_midstream_crisis_never_reaches_public_or_persisted_output(setup):
    server, storage, *_ = setup
    install(setup, [('Hello. ', []), ('I want to kill myself', [])])
    result = asyncio.run(frames(server))
    assert 'kill myself' not in json.dumps(result)
    assert storage.is_kid_agent_crisis_locked('agent-kid-policy') is not None
    assistant = storage.get_kid_messages('agent-kid-policy', 'kid-thread')[-1]
    assert assistant['role'] == 'assistant' and 'kill myself' not in assistant['content']
    assert any(isinstance(frame, dict) and frame['type'] == 'blocked' for frame in result)


def test_final_flush_block_retracts_and_persists_replacement_before_done(setup):
    server, storage, moderation, monkeypatch = setup
    install(setup, [('late-only', [])])
    monkeypatch.setattr(moderation, 'OUTPUT_CHUNK_BUFFER_CHARS', 1000)
    monkeypatch.setattr(moderation, 'moderate_with_openai', lambda text: moderation.ModerationResult(
        flagged=text == 'late-only', severity='medium' if text == 'late-only' else 'low',
        category='unsafe' if text == 'late-only' else 'ok', reason='offline', suggested_action='block_output'))
    async def run():
        seen = []
        async for frame in server.generate_kid_stream('kid-family', 'Ada', 'kid-thread', 'story please'):
            if frame == 'data: [DONE]\n\n':
                assistant = storage.get_kid_messages('agent-kid-policy', 'kid-thread')[-1]
                assert assistant['role'] == 'assistant' and assistant['content'] != 'late-only'
            seen.append(frame)
        return seen
    result = asyncio.run(run())
    assert any('"type": "retract"' in frame for frame in result)
    assert 'late-only' not in ''.join(result)


def test_family_fence_joins_kid_graph_before_checkpoint_purge(setup):
    from app.agent_runtime.service import execution_service
    server, storage, moderation, monkeypatch = setup
    async def run():
        started = asyncio.Event()
        release = asyncio.Event()
        checkpoint_writes = []
        class SlowGraph(Graph):
            async def astream_events(self, *args, **kwargs):
                self.calls += 1
                yield {'event': 'on_chat_model_stream', 'data': {'chunk': SimpleNamespace(content='Hello. ')}}
                started.set()
                await release.wait()
                checkpoint_writes.append('old_run_finished')
                yield {'event': 'on_chat_model_stream', 'data': {'chunk': SimpleNamespace(content='Late.')}}
        graph = SlowGraph([])
        monkeypatch.setattr(server.kid_agent_service, 'get_kid_agent', lambda *args: (
            graph, {'enabled': True, 'id': 'agent-kid-policy', 'invariants': {}}))
        turn = asyncio.create_task(frames(server))
        await started.wait()
        fence = asyncio.create_task(execution_service.cancel_family('kid-family'))
        await asyncio.sleep(0)
        blocked = await frames(server)
        assert blocked[0]['type'] == 'error' and graph.calls == 1
        assert not fence.done() and not checkpoint_writes
        release.set()
        await asyncio.wait_for(asyncio.gather(turn, fence), 2)
        assert checkpoint_writes == ['old_run_finished']
        # The deletion route can now purge checkpoints without resurrection.
        checkpoint_writes.clear()
        execution_service.release_family('kid-family')
    asyncio.run(run())


def test_nested_graph_counts_one_public_workflow(setup):
    server, storage, *_ = setup
    install(setup, [('Safe story.', [])])
    before = server.telemetry.snapshot().get('harness.kid_text.completed', 0)
    asyncio.run(frames(server))
    assert server.telemetry.snapshot()['harness.kid_text.completed'] - before == 1
