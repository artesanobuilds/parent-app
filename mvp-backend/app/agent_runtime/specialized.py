"""Graph events underneath specialized safety adapters, never around them."""
from contextlib import aclosing

from app.agent_runtime.events import normalize
from app.agent_runtime.service import execution_service, owned_stream


async def graph_events(agent, inputs, config, context, *, shared, version, repair=None):
    """Caller owns the whole safety workflow, including prechecks and final flush.

    The child graph producer drains outstanding tools before close returns. The
    outer safety workflow may therefore stop consuming immediately on a block or
    disconnect without releasing its conversation gate while a tool still runs.
    Kid policies never retry a model turn automatically.
    """
    from app.agent import is_internal_event
    if shared:
        async with aclosing(execution_service.stream(
                agent, inputs, config, context, version=version, repair=repair,
                is_internal=is_internal_event, acquire_ownership=False)) as events:
            async for event in events:
                if event.kind != 'completed':
                    yield event
    else:
        async def legacy(_disconnected):
            if repair:
                await repair(agent, config)
            async with aclosing(agent.astream_events(inputs, config=config, version=version)) as events:
                async for raw in events:
                    if is_internal_event(raw):
                        continue
                    event = normalize(raw)
                    if event is not None:
                        yield event
        async with aclosing(owned_stream(context, legacy, acquire_ownership=False)) as events:
            async for event in events:
                yield event
