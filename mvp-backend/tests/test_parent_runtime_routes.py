"""Shared and rollback adapters exercise actual durable transcript storage."""
import asyncio
import json
from types import SimpleNamespace

import pytest


@pytest.fixture
def route_storage(tmp_path, monkeypatch):
    import app.server as server
    import app.cos.router as cos
    from app.duckdb_storage import DuckDBStorage
    from app.memory import MemoryRepository
    storage = DuckDBStorage(tmp_path / 'routes.duckdb')
    monkeypatch.setattr(server, 'storage_backend', storage)
    monkeypatch.setattr(cos, '_storage', lambda: storage)
    monkeypatch.setattr(server, 'chat_memory', MemoryRepository())
    monkeypatch.setattr(server, 'coach_threads', SimpleNamespace(
        active_conversation_id=lambda _: 'named', touch=lambda *args: None))
    yield storage
    storage._con.close()


@pytest.mark.parametrize('surface', ['chat', 'cos'])
@pytest.mark.parametrize('shared', [False, True])
def test_shared_text_finalizes_before_done_and_filters_internal(monkeypatch, surface, shared, route_storage):
    import app.server as server
    import app.cos.router as cos
    storage = route_storage
    seen_config = []
    class Graph:
        async def astream_events(self, inputs, config, version):
            seen_config.append(config)
            if surface == 'chat':
                assert storage.load_user_data('u', 'chat_threads')['named'] == [{'role': 'user', 'content': 'hi'}]
            else:
                assert storage.get_cos_messages('u', 'install')[0]['role'] == 'user'
            for content, tags in [('hidden', ['mvp:internal']), ('hello', [])]:
                yield {'event': 'on_chat_model_stream', 'tags': tags,
                       'data': {'chunk': SimpleNamespace(content=content)}}
        async def aget_state(self, config):
            return SimpleNamespace(values={'messages': []})
    graph = Graph()
    monkeypatch.setenv(f'MVP_SHARED_RUNTIME_{surface.upper()}', '1' if shared else '0')
    monkeypatch.setattr(server, 'get_agent', lambda _: graph)
    monkeypatch.setattr(cos, 'get_cos_agent', lambda _: graph)
    async def run():
        stream = (server.generate_stream('hi', 'install', 'u') if surface == 'chat'
                  else cos._cos_chat_stream('u', 'install', 'hi'))
        frames = []
        async for frame in stream:
            frames.append(frame)
            if frame == 'data: [DONE]\n\n':
                assert storage._con.execute('SELECT outcome FROM agent_runs').fetchone()[0] == 'completed'
                if surface == 'chat':
                    assert storage.load_user_data('u', 'chat_threads')['named'][-1] == {'role': 'assistant', 'content': 'hello'}
                else:
                    assert storage.get_cos_messages('u', 'install')[-1]['role'] == 'assistant'
        assert frames == ['data: {"type": "token", "content": "hello"}\n\n', 'data: [DONE]\n\n']
        expected_key = 'u:parent:named' if surface == 'chat' else 'u:parent'
        assert seen_config[0]['configurable']['thread_id'] == expected_key
    asyncio.run(run())


@pytest.mark.parametrize('surface', ['chat', 'cos'])
@pytest.mark.parametrize('shared', [False, True])
def test_shared_text_finalization_failure_uses_existing_error_envelope(monkeypatch, surface, shared, route_storage):
    import app.server as server
    import app.cos.router as cos
    storage = route_storage
    class Graph:
        async def astream_events(self, *args, **kwargs):
            yield {'event': 'on_chat_model_stream', 'data': {'chunk': SimpleNamespace(content='hello')}}
        async def aget_state(self, config):
            return SimpleNamespace(values={'messages': []})
    original_save = storage.save_user_data
    original_cos = storage.append_cos_message
    def fail_save(user_id, name, data):
        if name == 'chat_threads' and data['named'][-1]['role'] == 'assistant':
            raise OSError('disk full')
        return original_save(user_id, name, data)
    def fail_cos(*args, **kwargs):
        if kwargs['role'] == 'assistant':
            raise OSError('disk full')
        return original_cos(*args, **kwargs)
    monkeypatch.setattr(storage, 'save_user_data', fail_save)
    monkeypatch.setattr(storage, 'append_cos_message', fail_cos)
    monkeypatch.setenv(f'MVP_SHARED_RUNTIME_{surface.upper()}', '1' if shared else '0')
    monkeypatch.setattr(server, 'get_agent', lambda _: Graph())
    monkeypatch.setattr(cos, 'get_cos_agent', lambda _: Graph())
    async def run():
        stream = (server.generate_stream('hi', 'install', 'u') if surface == 'chat'
                  else cos._cos_chat_stream('u', 'install', 'hi'))
        frames = [frame async for frame in stream]
        assert 'data: [DONE]\n\n' not in frames
        error = json.loads(frames[-1][6:])
        assert error == {'type': 'error', 'content':
                         'Something went wrong. Please try again.' if surface == 'chat' else 'disk full'}
        assert storage._con.execute('SELECT outcome FROM agent_runs').fetchone()[0] == 'failed'
        if surface == 'chat':
            assert server.chat_memory.snapshot_user('u')['named'] == [{'role': 'user', 'content': 'hi'}]
            server.persist_state('u')
            assert storage.load_user_data('u', 'chat_threads')['named'] == [{'role': 'user', 'content': 'hi'}]
    asyncio.run(run())
