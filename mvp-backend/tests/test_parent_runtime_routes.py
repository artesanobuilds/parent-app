"""Exercise shared text adapters through the same generators the HTTP routes use."""
import asyncio
import json
from types import SimpleNamespace

import pytest

from app.agent_runtime.events import RunEvent


@pytest.mark.parametrize('surface', ['chat', 'cos'])
@pytest.mark.parametrize('shared', [False, True])
def test_shared_text_finalizes_before_done_and_filters_internal(monkeypatch, surface, shared):
    import app.server as server
    import app.cos.router as cos
    from app.memory import MemoryRepository

    persisted = []
    seen_config = []
    class Graph:
        async def astream_events(self, inputs, config, version):
            seen_config.append(config)
            for content, tags in [('hidden', ['mvp:internal']), ('hello', [])]:
                yield {'event': 'on_chat_model_stream', 'tags': tags,
                       'data': {'chunk': SimpleNamespace(content=content)}}
        async def aget_state(self, config):
            return SimpleNamespace(values={'messages': []})
    graph = Graph()
    monkeypatch.setenv(f'MVP_SHARED_RUNTIME_{surface.upper()}', '1' if shared else '0')
    monkeypatch.setattr(server, 'get_agent', lambda _: graph)
    monkeypatch.setattr(cos, 'get_cos_agent', lambda _: graph)
    monkeypatch.setattr(server, 'chat_memory', MemoryRepository())
    monkeypatch.setattr(server, 'coach_threads', SimpleNamespace(
        active_conversation_id=lambda _: 'named', touch=lambda *args: None))
    monkeypatch.setattr(server, 'persist_state', lambda _: persisted.append('saved'))
    monkeypatch.setattr(cos, '_storage', lambda: SimpleNamespace(
        append_cos_message=lambda *args, **kwargs: persisted.append(kwargs['role'])))

    async def run():
        stream = (server.generate_stream('hi', 'install', 'u') if surface == 'chat'
                  else cos._cos_chat_stream('u', 'install', 'hi'))
        frames = []
        async for frame in stream:
            frames.append(frame)
            if frame == 'data: [DONE]\n\n':
                assert persisted[-1] == ('saved' if surface == 'chat' else 'assistant')
        assert frames == ['data: {"type": "token", "content": "hello"}\n\n',
                          'data: [DONE]\n\n']
        expected_key = 'u:parent:named' if surface == 'chat' else 'u:parent'
        assert seen_config[0]['configurable']['thread_id'] == expected_key
    asyncio.run(run())


@pytest.mark.parametrize('surface', ['chat', 'cos'])
@pytest.mark.parametrize('shared', [False, True])
def test_shared_text_finalization_failure_uses_existing_error_envelope(monkeypatch, surface, shared):
    import app.server as server
    import app.cos.router as cos
    from app.memory import MemoryRepository

    class Graph:
        async def astream_events(self, *args, **kwargs):
            yield {'event': 'on_chat_model_stream', 'data': {'chunk': SimpleNamespace(content='hello')}}
        async def aget_state(self, config):
            return SimpleNamespace(values={'messages': []})
    def fail(*args, **kwargs):
        if surface == 'chat' or kwargs['role'] == 'assistant':
            raise OSError('disk full')
    monkeypatch.setenv(f'MVP_SHARED_RUNTIME_{surface.upper()}', '1' if shared else '0')
    monkeypatch.setattr(server, 'get_agent', lambda _: Graph())
    monkeypatch.setattr(cos, 'get_cos_agent', lambda _: Graph())
    monkeypatch.setattr(server, 'chat_memory', MemoryRepository())
    monkeypatch.setattr(server, 'coach_threads', SimpleNamespace(
        active_conversation_id=lambda _: None, touch=lambda *args: None))
    monkeypatch.setattr(server, 'persist_state', fail)
    monkeypatch.setattr(cos, '_storage', lambda: SimpleNamespace(append_cos_message=fail))
    async def run():
        stream = (server.generate_stream('hi', 'install', 'u') if surface == 'chat'
                  else cos._cos_chat_stream('u', 'install', 'hi'))
        frames = [frame async for frame in stream]
        assert 'data: [DONE]\n\n' not in frames
        error = json.loads(frames[-1][6:])
        assert error == {'type': 'error', 'content':
                         'Something went wrong. Please try again.' if surface == 'chat' else 'disk full'}
    asyncio.run(run())
