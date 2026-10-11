"""Deterministic offline regressions using the production parent graph factory.

Scripted models test orchestration, tenant binding and durable tools. They do NOT
measure parenting quality, live tool selection, provider latency or model cost.
Internal-summary and voice-interruption scenarios are additionally pinned by
`test_merged_agent_harness.py` and `test_convai_endpoints.py`.
"""
import asyncio
from typing import Any

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import PrivateAttr
from langgraph.checkpoint.memory import MemorySaver

from app.agent_runtime.cache import AgentCache
from app.agent_runtime.context import RunContext, current_run
from app.agent_runtime.service import execution_service
from app.duckdb_storage import DuckDBStorage
from app.services.operations import run_scope


class ScriptedModel(BaseChatModel):
    replies: list[AIMessage]
    _index: int = PrivateAttr(default=0)
    _prompts: list = PrivateAttr(default_factory=list)

    @property
    def _llm_type(self):
        return 'offline-parent-scenario'

    def bind_tools(self, tools, **kwargs):
        return self

    def get_num_tokens_from_messages(self, messages, tools=None):
        return sum(len(str(message.content)) for message in messages) // 4

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self._prompts.append(messages)
        response = self.replies[self._index]
        self._index += 1
        return ChatResult(generations=[ChatGeneration(message=response)])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        message = self._generate(messages, stop, run_manager, **kwargs).generations[0].message
        yield ChatGenerationChunk(message=AIMessageChunk(
            content=message.content, tool_calls=message.tool_calls))


def call(name, args, call_id):
    return AIMessage(content='', tool_calls=[{'name': name, 'args': args, 'id': call_id}])


@pytest.fixture
def storage(tmp_path):
    storage = DuckDBStorage(tmp_path / 'scenarios.duckdb')
    yield storage
    storage.close()


def graph_for(monkeypatch, user_id, model):
    import app.agent as parent
    monkeypatch.setattr(parent, 'llm', model)
    monkeypatch.setattr(parent, 'checkpointer', MemorySaver())
    monkeypatch.setattr(parent, '_dynamic_context', lambda uid: {
        'profile': '{"family":"' + uid + '"}', 'household': None, 'for_you': None})
    monkeypatch.setattr(parent, 'content_catalog_for_prompt', lambda: '')
    monkeypatch.setattr(parent, '_agent_cache', AgentCache(4))
    return parent.get_agent(user_id)


async def run_graph(storage, graph, user_id, prompt):
    context = RunContext(user_id, 'chat', f'{user_id}:parent')
    finalized = []
    async def finalize(ctx, text):
        assert current_run() == ctx
        finalized.append(text)
    events = [event async for event in execution_service.stream(
        graph, {'messages': [HumanMessage(content=prompt)]},
        {'configurable': {'thread_id': context.thread_key}}, context,
        version='v2', scope=lambda ctx: run_scope(storage, ctx.user_id, ctx.run_id, ctx.thread_key),
        finalize=finalize)]
    assert events[-1].kind == 'completed'
    assert finalized == [''.join(event.content for event in events if event.kind == 'token')]
    return events


def test_mixed_coaching_and_planning_uses_one_production_graph(monkeypatch, storage):
    model = ScriptedModel(replies=[
        AIMessage(content='That sounds like a lot to juggle.'),
    ])
    # A mixed turn can speak and issue a planning call in the same model step.
    model.replies = [AIMessage(content='That sounds like a lot to juggle.', tool_calls=[{
        'name': 'AddTodo', 'args': {'title': 'Call the camp about registration'}, 'id': 'mixed-todo'}]),
        AIMessage(content='I saved a reminder to call the camp.')]
    graph = graph_for(monkeypatch, 'scenario-mixed', model)
    events = asyncio.run(run_graph(storage, graph, 'scenario-mixed',
                                   'I am overwhelmed. Help me remember to call the camp.'))
    assert [event.tool for event in events if event.kind == 'tool_start'] == ['AddTodo']
    assert storage.list_todos('scenario-mixed')[0]['title'] == 'Call the camp about registration'
    assert 'I saved a reminder' in ''.join(event.content for event in events)


def test_profile_correction_uses_shared_schema_and_durable_tool(monkeypatch, storage):
    model = ScriptedModel(replies=[
        call('LearnedAboutParent', {'parent_updates': {'secondary_language': 'Spanish'}}, 'language'),
        AIMessage(content='I have updated the language spoken at home.')])
    graph = graph_for(monkeypatch, 'scenario-profile', model)
    asyncio.run(run_graph(storage, graph, 'scenario-profile', 'We also speak Spanish at home.'))
    assert storage.load_user_data('scenario-profile', 'profiles')['parent']['secondary_language'] == 'Spanish'


def test_concurrent_production_graphs_keep_tenants_and_context_separate(monkeypatch, storage):
    models = []
    graphs = []
    for user in ('scenario-alice', 'scenario-bob'):
        model = ScriptedModel(replies=[call('AddTodo', {'title': user + ' task'}, 'same-call-id'),
                                      AIMessage(content=user + ' saved')])
        models.append(model)
        graphs.append(graph_for(monkeypatch, user, model))
    async def run():
        await asyncio.gather(*(run_graph(storage, graph, user, user + ' request')
                               for graph, user in zip(graphs, ('scenario-alice', 'scenario-bob'))))
        assert current_run() is None
    asyncio.run(run())
    assert storage.list_todos('scenario-alice')[0]['title'] == 'scenario-alice task'
    assert storage.list_todos('scenario-bob')[0]['title'] == 'scenario-bob task'
    for model, other in zip(models, ('scenario-bob', 'scenario-alice')):
        assert other not in str(model._prompts)


def test_failed_planning_tool_never_commits_a_partial_result(monkeypatch, storage):
    model = ScriptedModel(replies=[call('AddTodo', {'title': 'Must not save'}, 'failed-todo'),
                                  AIMessage(content='I could not save that reminder.')])
    graph = graph_for(monkeypatch, 'scenario-failure', model)
    def fail(*args, **kwargs):
        raise OSError('simulated storage failure')
    monkeypatch.setattr(storage, 'add_todo', fail)
    with pytest.raises(RuntimeError, match='simulated storage failure'):
        asyncio.run(run_graph(storage, graph, 'scenario-failure', 'Save a reminder.'))
    assert storage.list_todos('scenario-failure') == []
    assert storage._con.execute('SELECT count(*) FROM agent_operation_receipts').fetchone()[0] == 0
