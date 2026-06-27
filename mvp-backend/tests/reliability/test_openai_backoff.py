"""
Reliability: the research model retries rate-limit (429) responses and recovers,
so a burst from several concurrent runs degrades to "slightly slower" instead of
"failed run." This pins the `max_retries` wiring (`app/research/graph.py`
`RESEARCH_LLM_MAX_RETRIES`) against the real OpenAI SDK retry path.

Hermetic: an `httpx.MockTransport` impersonates the OpenAI HTTP endpoint — no
network, no key spend, deterministic. We assert the call succeeds AND that it
took the retried path (3 HTTP attempts: 429, 429, 200).
"""
from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from langchain_core.messages import HumanMessage  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402

from app.research.graph import (  # noqa: E402
    RESEARCH_LLM_MAX_RETRIES,
    build_research_model,
)


def _chat_completion_ok() -> dict:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 0,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "ok"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def test_chatopenai_retries_429_then_succeeds():
    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] <= 2:
            return httpx.Response(429, json={"error": {"message": "rate limit"}})
        return httpx.Response(200, json=_chat_completion_ok())

    client = httpx.Client(transport=httpx.MockTransport(handler))
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key="test-key",
        max_retries=4,
        http_client=client,
    )

    out = llm.invoke([HumanMessage("hi")])

    assert out.content == "ok"
    assert attempts["n"] == 3, f"expected 2 retries then success, saw {attempts['n']} attempts"


def test_research_model_actually_carries_retries(monkeypatch):
    # Pin the WIRING, not just the constant: the production research model must
    # be constructed with max_retries == RESEARCH_LLM_MAX_RETRIES, so dropping
    # the kwarg from build_research_model() fails here. A dummy key keeps the
    # test hermetic (ChatOpenAI builds its client eagerly) and order-independent.
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-used")
    assert RESEARCH_LLM_MAX_RETRIES >= 1
    model = build_research_model()
    assert model.max_retries == RESEARCH_LLM_MAX_RETRIES
