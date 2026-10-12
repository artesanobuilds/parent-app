"""HTTP fault injection: actual adapters, tool runtime, receipts and temporary DB."""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, ToolMessage, RemoveMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

from app.services.operations import current_run


@pytest.fixture
def rig(monkeypatch, tmp_path):
    import app.server as server
    import app.cos.router as cos
    import app.parent_convai_endpoint as voice
    from app.duckdb_storage import DuckDBStorage
    from app.memory import MemoryRepository
    state = SimpleNamespace(storage=DuckDBStorage(tmp_path / 'http.duckdb'),
                            server=server, cos=cos, voice=voice)
    monkeypatch.setattr(server, 'storage_backend', state.storage)
    monkeypatch.setattr(cos, '_storage', lambda: state.storage)
    monkeypatch.setattr(voice, '_storage', lambda: state.storage)
    monkeypatch.setattr(voice, 'CONVAI_SECRET', 'offline-secret')
    monkeypatch.setattr(server, 'chat_memory', MemoryRepository())
    monkeypatch.setattr(server, 'onboarding_memory', MemoryRepository())
    monkeypatch.setattr(server, 'coach_threads', SimpleNamespace(
        active_conversation_id=lambda _: None, touch=lambda *args: None))
    monkeypatch.setattr(server, 'rate_limit_enforce', lambda *a: None)
    monkeypatch.setattr(cos, 'rate_limit_enforce', lambda *a: None)
    original = dict(server.app.dependency_overrides)
    server.app.dependency_overrides[server.current_user] = lambda: 'alice'
    state.client = TestClient(server.app)  # no worker/lifespan needed for these HTTP adapters
    yield state
    server.app.dependency_overrides.clear()
    server.app.dependency_overrides.update(original)
    state.client.close()
    state.storage._con.close()


def request(rig, surface):
    if surface == 'parent_voice':
        return rig.client.post('/v1/parent/chat/completions',
            headers={'Authorization': 'Bearer offline-secret'},
            json={'messages': [{'role': 'user', 'content': 'hi'}],
                  'elevenlabs_extra_body': {'user_id': 'alice', 'thread_id': 'phone'}})
    path = {'chat': '/chat', 'cos': '/cos/chat', 'onboarding': '/onboarding-chat'}[surface]
    return rig.client.post(path, json={'user_id': 'alice', 'thread_id': 'phone', 'message': 'hi'})


def history(rig, surface):
    if surface == 'cos':
        return rig.storage.get_cos_messages('alice', 'phone')
    blob = {'chat': 'chat_threads', 'onboarding': 'onboarding_threads',
            'parent_voice': 'parent_voice_threads'}[surface]
    return (rig.storage.load_user_data('alice', blob) or {}).get('phone', [])


class ToolGraph:
    """The provider is scripted; the compiled tool node and its storage are real."""
    def __init__(self, rig, surface, *, crash=False, restored_state=None):
        from app.cos.tools import _make_add_todo_tool
        from app.agent import _make_parent_tool
        self.rig, self.surface, self.crash = rig, surface, crash
        self.calls = 0
        self.messages = restored_state or []
        self.reconciled = False
        self.call = {'name': 'AddTodo', 'args': {'title': 'Register'}, 'id': 'durable-tool', 'type': 'tool_call'}
        builder = StateGraph(MessagesState)
        builder.add_node('tools', ToolNode([_make_add_todo_tool('alice'), _make_parent_tool('alice')]))
        builder.add_edge(START, 'tools')
        builder.add_edge('tools', END)
        self.tools = builder.compile()

    async def aget_state(self, config):
        return SimpleNamespace(values={'messages': self.messages})

    async def aupdate_state(self, config, values, **kwargs):
        self.reconciled = True
        self.messages = [m for m in values['messages'] if not isinstance(m, RemoveMessage)]

    async def astream_events(self, inputs, config, version):
        self.calls += 1
        run = current_run()
        assert run.user_id == 'alice' and run.storage is self.rig.storage
        assert run.thread_key == config['configurable']['thread_id']
        assert history(self.rig, self.surface)[-1]['role'] == 'user'
        if not any(isinstance(m, ToolMessage) for m in self.messages):
            self.messages = [AIMessage(id='checkpoint-ai', content='', tool_calls=[self.call])]
            yield {'event': 'on_tool_start', 'name': self.call['name'], 'data': {}}
            result = await self.tools.ainvoke({'messages': self.messages})
            if self.crash:
                raise OSError('crash after domain commit, before checkpoint result')
            self.messages = result['messages']
            yield {'event': 'on_tool_end', 'name': self.call['name'], 'data': {}}
        yield {'event': 'on_chat_model_stream', 'data': {'chunk': SimpleNamespace(content='Saved.')}}


def install(monkeypatch, rig, graph, shared):
    for surface in ['chat', 'cos', 'parent_voice', 'onboarding']:
        monkeypatch.setenv(f'MVP_SHARED_RUNTIME_{surface.upper()}', '1' if shared else '0')
    monkeypatch.setattr(rig.server, 'get_agent', lambda _: graph)
    monkeypatch.setattr(rig.server, 'get_onboarding_agent', lambda _: graph)
    monkeypatch.setattr(rig.cos, 'get_cos_agent', lambda _: graph)
    monkeypatch.setattr(rig.voice, 'get_agent', lambda _: graph)


@pytest.mark.parametrize('surface', ['chat', 'cos', 'onboarding', 'parent_voice'])
@pytest.mark.parametrize('shared', [False, True])
def test_http_receipt_recovery_precedes_repair_and_preserves_known_effect(rig, monkeypatch, surface, shared):
    graph = ToolGraph(rig, surface, crash=True)
    install(monkeypatch, rig, graph, shared)
    failed = request(rig, surface)
    assert failed.status_code == 200
    assert '[DONE]' not in failed.text
    assert len(rig.storage.list_todos('alice')) == 1
    assert rig.storage._con.execute('SELECT outcome FROM agent_runs').fetchone()[0] == 'failed'
    graph.crash = False
    completed = request(rig, surface)
    assert completed.status_code == 200 and completed.text.endswith('data: [DONE]\n\n')
    assert graph.reconciled, 'receipt must restore the ToolMessage before repair discards the call'
    assert len(rig.storage.list_todos('alice')) == 1
    assert [row['role'] for row in history(rig, surface)] == ['user', 'user', 'assistant']
    assert rig.storage._con.execute("SELECT count(*) FROM agent_runs WHERE outcome = 'completed'").fetchone()[0] == 1


@pytest.mark.parametrize('surface', ['chat', 'cos', 'onboarding', 'parent_voice'])
@pytest.mark.parametrize('shared', [False, True])
def test_http_user_persistence_failure_prevents_tool_dispatch(rig, monkeypatch, surface, shared):
    graph = ToolGraph(rig, surface)
    install(monkeypatch, rig, graph, shared)
    def fail(*args, **kwargs):
        raise OSError('disk full')
    monkeypatch.setattr(rig.storage, 'save_user_data', fail)
    monkeypatch.setattr(rig.storage, 'append_cos_message', fail)
    response = request(rig, surface)
    assert '[DONE]' not in response.text
    assert graph.calls == 0
    assert rig.storage.list_todos('alice') == []
    assert rig.storage._con.execute('SELECT outcome FROM agent_runs').fetchone()[0] == 'failed'


@pytest.mark.parametrize('shared', [False, True])
def test_voice_scope_exit_failure_withholds_done(rig, monkeypatch, shared):
    graph = ToolGraph(rig, 'parent_voice')
    install(monkeypatch, rig, graph, shared)
    original = rig.storage._con.execute
    def fail_run_completion(sql, params=None):
        if sql.startswith('UPDATE agent_runs SET outcome'):
            raise OSError('ledger commit failed')
        return original(sql, params)
    monkeypatch.setattr(rig.storage._con, 'execute', fail_run_completion)
    response = request(rig, 'parent_voice')
    assert 'snag on my end' in response.text
    assert '[DONE]' not in response.text
    assert rig.storage._con.execute('SELECT outcome FROM agent_runs').fetchone()[0] != 'completed'


@pytest.mark.parametrize('shared', [False, True])
def test_voice_profile_and_receipt_survive_restart(rig, monkeypatch, shared):
    from app.duckdb_storage import DuckDBStorage
    graph = ToolGraph(rig, 'parent_voice', crash=True)
    graph.call = {'name': 'LearnedAboutParent', 'args': {'parent_updates': {'secondary_language': 'es'}},
                  'id': 'profile-call', 'type': 'tool_call'}
    install(monkeypatch, rig, graph, shared)
    response = request(rig, 'parent_voice')
    assert '[DONE]' not in response.text
    path = rig.storage.db_path
    rig.storage._con.close()
    rig.storage = DuckDBStorage(path)
    monkeypatch.setattr(rig.server, 'storage_backend', rig.storage)
    recovered = ToolGraph(rig, 'parent_voice', restored_state=graph.messages)
    install(monkeypatch, rig, recovered, shared)
    response = request(rig, 'parent_voice')
    assert response.text.endswith('data: [DONE]\n\n')
    assert recovered.reconciled
    assert rig.storage.load_user_data('alice', 'profiles')['parent']['secondary_language'] == 'es'
    assert rig.storage._con.execute('SELECT count(*) FROM agent_operation_receipts').fetchone()[0] == 1


@pytest.mark.parametrize('surface', ['chat', 'cos', 'onboarding', 'parent_voice'])
@pytest.mark.parametrize('shared', [False, True])
def test_disconnect_does_not_publish_assistant_history(rig, monkeypatch, surface, shared):
    import asyncio
    class SlowGraph:
        async def aget_state(self, config):
            return SimpleNamespace(values={'messages': []})
        async def astream_events(self, *args, **kwargs):
            yield {'event': 'on_chat_model_stream', 'data': {'chunk': SimpleNamespace(content='First')}}
            await released.wait()
            yield {'event': 'on_chat_model_stream', 'data': {'chunk': SimpleNamespace(content=' Last')}}
    install(monkeypatch, rig, SlowGraph(), shared)
    async def run():
        nonlocal released
        released = asyncio.Event()
        if surface == 'parent_voice':
            stream = rig.voice._stream_response('alice', 'phone', 'hi')
        elif surface == 'cos':
            stream = rig.cos._cos_chat_stream('alice', 'phone', 'hi')
        elif surface == 'onboarding':
            stream = rig.server.generate_onboarding_stream('hi', 'phone', 'alice')
        else:
            stream = rig.server.generate_stream('hi', 'phone', 'alice')
        assert 'First' in await anext(stream)
        closing = asyncio.create_task(stream.aclose())
        await asyncio.sleep(0.01)
        assert not closing.done(), 'ownership must wait for the outstanding provider/tool work'
        released.set()
        await closing
    released = None
    asyncio.run(run())
    assert [row['role'] for row in history(rig, surface)] == ['user']
    assert rig.storage._con.execute('SELECT outcome FROM agent_runs').fetchone()[0] == 'interrupted'


def test_shared_voice_family_fence_withholds_success_for_connected_consumer(rig, monkeypatch, caplog):
    """Family cancellation ends the service iterator without a Completed event."""
    import asyncio
    from app.agent_runtime.service import execution_service

    class SlowGraph:
        async def aget_state(self, config):
            return SimpleNamespace(values={'messages': []})

        async def astream_events(self, *args, **kwargs):
            yield {'event': 'on_chat_model_stream', 'data': {'chunk': SimpleNamespace(content='First')}}
            await released.wait()
            yield {'event': 'on_chat_model_stream', 'data': {'chunk': SimpleNamespace(content=' Last')}}

    install(monkeypatch, rig, SlowGraph(), shared=True)

    async def run():
        nonlocal released
        released = asyncio.Event()
        stream = rig.voice._stream_response('alice', 'phone', 'hi')
        first = await anext(stream)
        assert 'First' in first
        canceling = asyncio.create_task(execution_service.cancel_family('alice'))
        try:
            await asyncio.sleep(0.01)
            assert not canceling.done(), 'family cancellation joins outstanding graph work'
            released.set()
            await canceling
            return first + ''.join([event async for event in stream])
        finally:
            released.set()
            await canceling
            execution_service.release_family('alice')
            await stream.aclose()

    released = None
    response = asyncio.run(run())
    assert '[DONE]' not in response
    # Deliberate interruption is not an application failure or another spoken
    # reply. In particular, deleting a family must not trigger retry advice.
    assert 'snag on my end' not in response
    assert ' Last' not in response
    assert not any(record.levelname == 'ERROR' and record.name == 'app.parent_convai_endpoint'
                   for record in caplog.records)
    assert [row['role'] for row in history(rig, 'parent_voice')] == ['user']
    assert rig.storage._con.execute('SELECT outcome FROM agent_runs').fetchone()[0] == 'interrupted'
