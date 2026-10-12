"""Exercise voice cancellation through real LangGraph model and tool dispatch."""
import asyncio
import threading
from typing import Any

import pytest
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from app.agent_runtime.cancellation import VoiceCancellationMiddleware, bind_disconnect
from app.agent_runtime.context import RunContext, bind_run
from app.agent_runtime.service import AgentExecutionService, RunInterrupted


class AsyncModel(BaseChatModel):
    """A controllable async provider; use real graph scheduling around it."""
    handler: Any
    calls: int = 0

    @property
    def _llm_type(self):
        return 'voice-cancellation-test'

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, *args, **kwargs):
        raise AssertionError('The graph must use the async model path')

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        self.calls += 1
        message = await self.handler(self.calls)
        return ChatResult(generations=[ChatGeneration(message=message)])


def graph_for(handler, *, tools=(), middleware=(), checkpointer=None):
    model = AsyncModel(handler=handler)
    graph = create_agent(model=model, tools=list(tools),
                         middleware=[VoiceCancellationMiddleware(), *middleware],
                         checkpointer=checkpointer)
    return model, graph


async def consume(service, graph, *, surface='parent_voice', before=None):
    return [event async for event in service.stream(
        graph, {'messages': [('user', 'Hello')]}, {},
        RunContext('cancellation-test', surface, 'cancellation-test:voice'), before=before)]


def test_model_disconnect_cancels_and_joins_before_replacement_owner():
    async def run():
        started = asyncio.Event()
        cleanup_started = asyncio.Event()
        allow_cleanup = asyncio.Event()
        order = []

        async def blocked_model(_):
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cleanup_started.set()
                await allow_cleanup.wait()
                order.append('model_closed')

        async def next_model(_):
            return AIMessage(content='Next response')

        _, first_graph = graph_for(blocked_model)
        _, next_graph = graph_for(next_model)
        service = AgentExecutionService()
        first = asyncio.create_task(consume(service, first_graph))
        await asyncio.wait_for(started.wait(), 2)
        first.cancel()
        try:
            await asyncio.wait_for(cleanup_started.wait(), 1)
            second = asyncio.create_task(consume(
                service, next_graph, before=lambda _: order.append('next_owner')))
            await asyncio.sleep(0.02)
            assert order == []
            assert not first.done() and not second.done()
            # Repeated ASGI cancellation must not detach provider cleanup.
            first.cancel()
            await asyncio.sleep(0.02)
            assert not first.done() and not second.done()
        finally:
            allow_cleanup.set()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(first, 1)
        result = await asyncio.wait_for(second, 1)
        assert result[-1].kind == 'completed'
        assert order == ['model_closed', 'next_owner']
    asyncio.run(run())


def test_inflight_sync_tool_finishes_before_replacement_and_skips_followup_model():
    async def run():
        started = threading.Event()
        release = threading.Event()
        order = []

        @tool
        def save_note() -> str:
            """Persist a test note."""
            started.set()
            assert release.wait(3), 'Test failed to release the tool'
            order.append('tool_committed')
            return 'saved'

        async def first_model(call):
            assert call == 1, 'Disconnected turn must not start a follow-up model'
            return AIMessage(content='', tool_calls=[
                {'name': 'save_note', 'args': {}, 'id': 'save-1', 'type': 'tool_call'}])

        async def next_model(_):
            return AIMessage(content='Replacement response')

        model, first_graph = graph_for(first_model, tools=[save_note])
        _, next_graph = graph_for(next_model)
        service = AgentExecutionService()
        first = asyncio.create_task(consume(service, first_graph))
        try:
            assert await asyncio.to_thread(started.wait, 2)
            first.cancel()
            await asyncio.sleep(0.01)
            first.cancel()
            second = asyncio.create_task(consume(
                service, next_graph, before=lambda _: order.append('next_owner')))
            await asyncio.sleep(0.02)
            assert not first.done() and not second.done()
            assert order == []
        finally:
            release.set()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(first, 1)
        assert (await asyncio.wait_for(second, 1))[-1].kind == 'completed'
        assert order == ['tool_committed', 'next_owner']
        assert model.calls == 1
    asyncio.run(run())


def test_tool_pending_at_disconnect_is_not_dispatched_and_keeps_matching_result():
    async def run():
        disconnected = asyncio.Event()
        dispatched = []

        class DisconnectBeforeTools(AgentMiddleware):
            async def aafter_model(self, state, runtime):
                disconnected.set()

        @tool
        def save_note() -> str:
            """Persist a test note."""
            dispatched.append(True)
            return 'saved'

        async def response(_):
            return AIMessage(content='', tool_calls=[
                {'name': 'save_note', 'args': {}, 'id': 'pending-1', 'type': 'tool_call'}])

        model, graph = graph_for(response, tools=[save_note],
                                 middleware=[DisconnectBeforeTools()],
                                 checkpointer=InMemorySaver())
        config = {'configurable': {'thread_id': 'pending-tool'}}
        with bind_run(RunContext('test', 'parent_voice', 'test:voice')):
            with bind_disconnect(disconnected):
                with pytest.raises(RunInterrupted):
                    await graph.ainvoke({'messages': [('user', 'Save a note')]}, config)
        assert dispatched == []
        assert model.calls == 1
        state = await graph.aget_state(config)
        results = [message for message in state.values['messages']
                   if isinstance(message, ToolMessage)]
        assert len(results) == 1
        assert results[0].tool_call_id == 'pending-1'
        assert results[0].content == 'Voice turn interrupted before tool dispatch.'
    asyncio.run(run())


@pytest.mark.parametrize('surface', ['chat', 'kid_voice'])
def test_non_parent_surfaces_keep_model_and_tool_behavior_when_disconnected(surface):
    async def run():
        disconnected = asyncio.Event()
        disconnected.set()
        dispatched = []

        @tool
        def save_note() -> str:
            """Persist a test note."""
            dispatched.append(True)
            return 'saved'

        async def response(call):
            if call == 1:
                return AIMessage(content='', tool_calls=[
                    {'name': 'save_note', 'args': {}, 'id': 'normal-1', 'type': 'tool_call'}])
            return AIMessage(content='Saved')

        model, graph = graph_for(response, tools=[save_note])
        with bind_run(RunContext('test', surface, 'test:thread')):
            with bind_disconnect(disconnected):
                result = await graph.ainvoke({'messages': [('user', 'Save a note')]})
        assert dispatched == [True]
        assert model.calls == 2
        assert result['messages'][-1].content == 'Saved'
    asyncio.run(run())


def test_skipped_parallel_tool_does_not_cancel_started_sibling():
    async def run():
        disconnected = asyncio.Event()
        started = threading.Event()
        release = threading.Event()
        pending_skipped = asyncio.Event()
        committed = []

        class DelayPendingTool(AgentMiddleware):
            async def awrap_tool_call(self, request, handler):
                if request.tool_call['id'] == 'pending-sibling':
                    assert await asyncio.to_thread(started.wait, 2)
                    disconnected.set()
                    result = await handler(request)
                    pending_skipped.set()
                    return result
                return await handler(request)

        @tool
        def save_note(label: str) -> str:
            """Persist a labeled test note."""
            if label == 'started':
                started.set()
                assert release.wait(3), 'Test failed to release the started tool'
            committed.append(label)
            return 'saved ' + label

        async def response(_):
            return AIMessage(content='', tool_calls=[
                {'name': 'save_note', 'args': {'label': 'started'},
                 'id': 'started-sibling', 'type': 'tool_call'},
                {'name': 'save_note', 'args': {'label': 'pending'},
                 'id': 'pending-sibling', 'type': 'tool_call'},
            ])

        model = AsyncModel(handler=response)
        graph = create_agent(model=model, tools=[save_note],
                             middleware=[DelayPendingTool(), VoiceCancellationMiddleware()],
                             checkpointer=InMemorySaver())
        config = {'configurable': {'thread_id': 'parallel-tools'}}
        with bind_run(RunContext('test', 'parent_voice', 'test:voice')):
            with bind_disconnect(disconnected):
                task = asyncio.create_task(graph.ainvoke(
                    {'messages': [('user', 'Save notes')]}, config))
                try:
                    await asyncio.wait_for(pending_skipped.wait(), 2)
                    await asyncio.sleep(0.02)
                    assert not task.done()
                    assert committed == []
                finally:
                    release.set()
                with pytest.raises(RunInterrupted):
                    await asyncio.wait_for(task, 1)
        assert committed == ['started']
        assert model.calls == 1
        state = await graph.aget_state(config)
        results = {message.tool_call_id: message.content
                   for message in state.values['messages'] if isinstance(message, ToolMessage)}
        assert results == {
            'started-sibling': 'saved started',
            'pending-sibling': 'Voice turn interrupted before tool dispatch.',
        }
    asyncio.run(run())
