"""Research dispatch limits for the pinned LangChain middleware interface."""
import asyncio

from langchain.agents.middleware import AgentMiddleware
from langchain_core.callbacks import BaseCallbackHandler
from openai import APIConnectionError, APIStatusError


class JobDispatchGuard(BaseCallbackHandler):
    """Include internal summarizers and any inherited nested model/tool calls."""
    raise_error = True
    run_inline = True

    def __init__(self, context):
        self.context = context

    def on_chat_model_start(self, *args, **kwargs):
        self.context.check()

    def on_llm_start(self, *args, **kwargs):
        self.context.check()

    def on_tool_start(self, *args, **kwargs):
        self.context.check()


def bounded_model(model, timeout):
    """Copy OpenAI transport options as well as Pydantic fields.

    model_copy alone retains already-constructed SDK clients and their retry
    policy. with_options shares the HTTP pool but changes request policy.
    """
    updates = {'request_timeout': timeout, 'max_retries': 0}
    if getattr(model, 'root_client', None) is not None:
        client = model.root_client.with_options(timeout=timeout, max_retries=0)
        updates.update(root_client=client, client=client.chat.completions)
    if getattr(model, 'root_async_client', None) is not None:
        client = model.root_async_client.with_options(timeout=timeout, max_retries=0)
        updates.update(root_async_client=client, async_client=client.chat.completions)
    return model.model_copy(update=updates)


class JobDispatchMiddleware(AgentMiddleware):
    def __init__(self, context, retries=2, call_timeout=120):
        self.context = context
        self.retries = retries
        self.call_timeout = call_timeout

    async def awrap_model_call(self, request, handler):
        for attempt in range(self.retries + 1):
            timeout = self.context.remaining(self.call_timeout)
            # Disable hidden SDK retries: every retry must re-check the attempt
            # and consume the original run deadline, including backoff.
            bounded = request.override(model=bounded_model(request.model, timeout))
            try:
                return await self.context.wait(asyncio.wait_for(handler(bounded), timeout))
            except (APIConnectionError, APIStatusError, TimeoutError) as exc:
                retryable = not isinstance(exc, APIStatusError) or exc.status_code in (408, 409, 429) or exc.status_code >= 500
                if not retryable or attempt == self.retries:
                    raise
                await self.context.wait(asyncio.sleep(min(2 ** attempt, self.context.remaining())))

    async def awrap_tool_call(self, request, handler):
        # Tavily provides native async I/O. Local deepagents tools may run in a
        # thread; cancellation is cooperative there, and they receive no domain
        # storage capability. Candidate publication remains separately fenced.
        timeout = self.context.remaining(self.call_timeout)
        return await self.context.wait(asyncio.wait_for(handler(request), timeout))
