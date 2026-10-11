"""Faults and ownership at the actual execution boundary; no models or databases."""
import asyncio
from contextlib import aclosing, contextmanager
from types import SimpleNamespace

import pytest

from app.agent_runtime.context import RunContext
from app.agent_runtime.service import AgentExecutionService, FamilyAdmissionClosed


def token(text, *, internal=False):
    return {'event': 'on_chat_model_stream', 'tags': ['internal'] if internal else [],
            'data': {'chunk': SimpleNamespace(content=text)}}


class Graph:
    def __init__(self, script):
        self.script = script
        self.calls = 0
        self.closed = 0

    async def astream_events(self, inputs, config, version):
        self.calls += 1
        try:
            for item in self.script(self.calls):
                if isinstance(item, Exception):
                    raise item
                yield item
        finally:
            self.closed += 1


async def collect(service, graph, context, **kwargs):
    return [e async for e in service.stream(graph, {}, {}, context, **kwargs)]


def test_reconcile_repair_filter_finalize_and_scope_order():
    async def run():
        service = AgentExecutionService()
        order = []
        graph = Graph(lambda _: [token('private', internal=True), token('hello')])
        @contextmanager
        def scope(context):
            order.append('scope')
            yield
            order.append('scope_exit')
        async def reconcile(*args): order.append('reconcile')
        async def repair(*args): order.append('repair')
        async def finalize(context, text):
            assert text == 'hello'
            order.append('finalize')
        result = await collect(service, graph, RunContext('u', 'chat', 'u:parent'),
                               scope=scope, reconcile=reconcile, repair=repair,
                               is_internal=lambda e: 'internal' in e.get('tags', []),
                               finalize=finalize)
        assert [(e.kind, e.content) for e in result] == [('token', 'hello'), ('completed', '')]
        assert order == ['scope', 'reconcile', 'repair', 'finalize', 'scope_exit']
        assert graph.closed == 1
    asyncio.run(run())


@pytest.mark.parametrize('prior', [token('partial'), {'event': 'on_tool_start', 'name': 'save'}])
def test_ambiguous_write_or_partial_text_never_retries(prior):
    async def run():
        graph = Graph(lambda _: [prior, ValueError('dangling')])
        with pytest.raises(ValueError):
            await collect(AgentExecutionService(), graph, RunContext('u', 'chat', 'u:parent'),
                          is_retryable=lambda _: True)
        assert graph.calls == 1
    asyncio.run(run())


def test_pre_dispatch_failure_retries_once_and_repairs_again():
    async def run():
        graph = Graph(lambda attempt: [ValueError('dangling')] if attempt == 1 else [token('ok')])
        repaired = []
        result = await collect(AgentExecutionService(), graph, RunContext('u', 'chat', 'u:parent'),
                               repair=lambda *args: repaired.append(1), is_retryable=lambda _: True)
        assert graph.calls == len(repaired) == 2
        assert result[-1].kind == 'completed'
    asyncio.run(run())


def test_storage_failure_cannot_complete():
    async def run():
        def fail(*args): raise OSError('disk full')
        seen = []
        with pytest.raises(OSError, match='disk full'):
            async for event in AgentExecutionService().stream(
                    Graph(lambda _: [token('hello')]), {}, {}, RunContext('u', 'chat', 'u:parent'),
                    finalize=fail):
                seen.append(event.kind)
        assert seen == ['token']
    asyncio.run(run())


def test_same_thread_queues_through_finalization_but_other_family_runs():
    async def run():
        service = AgentExecutionService()
        finalizing = asyncio.Event()
        release = asyncio.Event()
        order = []
        async def finalize(*args):
            order.append('first_finalize')
            finalizing.set()
            await release.wait()
        first = asyncio.create_task(collect(service, Graph(lambda _: [token('one')]),
                                           RunContext('u', 'chat', 'u:parent'), finalize=finalize))
        await finalizing.wait()
        def before(*args): order.append('second_start')
        second = asyncio.create_task(collect(service, Graph(lambda _: [token('two')]),
                                            RunContext('u', 'cos', 'u:parent'), before=before))
        other = await asyncio.wait_for(collect(service, Graph(lambda _: [token('other')]),
                                              RunContext('v', 'chat', 'v:parent')), 1)
        assert other[-1].kind == 'completed'
        assert order == ['first_finalize']
        release.set()
        await asyncio.gather(first, second)
        assert order == ['first_finalize', 'second_start']
    asyncio.run(run())


def test_disconnect_joins_synchronous_tool_before_next_owner():
    async def run():
        import threading
        started = threading.Event()
        release = threading.Event()
        order = []
        class ThreadGraph:
            async def astream_events(self, *args, **kwargs):
                yield token('first')
                def tool():
                    started.set()
                    release.wait(3)
                    order.append('tool_committed')
                await asyncio.to_thread(tool)
                yield token('late')
        service = AgentExecutionService()
        stream = service.stream(ThreadGraph(), {}, {}, RunContext('u', 'parent_voice', 'u:voice'))
        assert (await anext(stream)).content == 'first'
        assert await asyncio.to_thread(started.wait, 1)
        close = asyncio.create_task(stream.aclose())
        second = asyncio.create_task(collect(service, Graph(lambda _: [token('next')]),
                                            RunContext('u', 'parent_voice', 'u:voice'),
                                            before=lambda _: order.append('next_owner')))
        await asyncio.sleep(0.02)
        assert not close.done() and not second.done()
        release.set()
        await asyncio.wait_for(asyncio.gather(close, second), 2)
        assert order == ['tool_committed', 'next_owner']
    asyncio.run(run())


def test_disconnect_does_not_deadlock_full_output_queue():
    async def run():
        graph = Graph(lambda _: [token(str(i)) for i in range(200)])
        stream = AgentExecutionService().stream(graph, {}, {}, RunContext('u', 'chat', 'u:parent'))
        await anext(stream)
        await asyncio.sleep(0.02)
        await asyncio.wait_for(stream.aclose(), 2)
        assert graph.closed == 1
    asyncio.run(run())


def test_family_deletion_fence_joins_active_and_blocks_queued_and_new_runs():
    async def run():
        service = AgentExecutionService()
        started = asyncio.Event()
        release = asyncio.Event()
        finalized = []
        class BlockingGraph:
            async def astream_events(self, *args, **kwargs):
                started.set()
                await release.wait()
                yield token('late')
        active = asyncio.create_task(collect(service, BlockingGraph(), RunContext('u', 'chat', 'u:parent'),
                                            finalize=lambda *args: finalized.append('bad')))
        await started.wait()
        queued_graph = Graph(lambda _: [token('queued')])
        queued = asyncio.create_task(collect(service, queued_graph, RunContext('u', 'cos', 'u:parent')))
        await asyncio.sleep(0)
        fence = asyncio.create_task(service.cancel_family('u'))
        await asyncio.sleep(0)
        with pytest.raises(FamilyAdmissionClosed):
            await collect(service, queued_graph, RunContext('u', 'chat', 'u:other'))
        assert not fence.done()
        release.set()
        await asyncio.wait_for(asyncio.gather(active, queued, fence), 2)
        assert not finalized and queued_graph.calls == 0
        service.release_family('u')
        assert (await collect(service, queued_graph, RunContext('u', 'chat', 'u:parent')))[-1].kind == 'completed'
    asyncio.run(run())


def test_scope_exit_failure_also_precedes_completion():
    async def run():
        @contextmanager
        def fail_on_exit(context):
            yield
            raise OSError('ledger unavailable')
        seen = []
        with pytest.raises(OSError, match='ledger unavailable'):
            async for event in AgentExecutionService().stream(
                    Graph(lambda _: [token('hello')]), {}, {}, RunContext('u', 'chat', 'u:parent'),
                    scope=fail_on_exit):
                seen.append(event.kind)
        assert seen == ['token']
    asyncio.run(run())


def test_repeated_task_cancellation_cannot_transfer_ownership_early():
    async def run():
        running = asyncio.Event()
        release = asyncio.Event()
        class SlowGraph:
            async def astream_events(self, *args, **kwargs):
                running.set()
                await release.wait()
                yield token('late')
        service = AgentExecutionService()
        task = asyncio.create_task(collect(service, SlowGraph(), RunContext('u', 'chat', 'u:parent')))
        await running.wait()
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        next_run = asyncio.create_task(collect(service, Graph(lambda _: [token('next')]),
                                              RunContext('u', 'chat', 'u:parent')))
        await asyncio.sleep(0.01)
        assert not next_run.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert (await next_run)[-1].kind == 'completed'
    asyncio.run(run())


def test_nested_graph_cannot_bypass_ownership_without_outer_workflow():
    async def run():
        graph = Graph(lambda _: [token('not allowed')])
        with pytest.raises(RuntimeError, match='requires ownership'):
            await collect(AgentExecutionService(), graph, RunContext('u', 'chat', 'u:parent'),
                          acquire_ownership=False)
        assert graph.calls == 0
    asyncio.run(run())
