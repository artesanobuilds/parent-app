#!/usr/bin/env python3
"""
Mock OpenAI Chat Completions server with a fault-injection control plane.

This is the parent-app analog of the NL-Harness Playbook's §4.8 mock-service
layer (stripe-mock / WireMock behind Toxiproxy). The backend is pointed at it via
`OPENAI_BASE_URL=http://<host>:<port>/v1`, so every model call the research worker
makes hits this server instead of real OpenAI — deterministic and free. Tests
drive its failure modes through the control endpoint via `ctx.fault('openai',…)`.

Why a single canned response is enough to drive a *real* research run to
completion: the deepagents loop terminates the moment the model returns an
assistant message with NO tool calls. So `ok` mode returns exactly that — the run
reaches `done` (with 0 candidates, which is fine; we're testing resilience, not
discovery quality), and fault modes let us assert what happens when OpenAI 429s,
errors, or goes down mid-run.

Endpoints:
  POST /v1/chat/completions   the OpenAI surface (honours `stream: true`)
  POST /__fault__             set mode: {mode, count?, latency_ms?}
  GET  /__fault__             current state + call_count (for assertions)
  POST /__reset__             clear back to healthy (mode=ok)
  GET  /health                liveness

Fault modes: ok | rate_limit (429) | error (500) | down (503) | slow (latency).
`count` = how many calls to fault before self-healing (omit = until reset).

Run standalone:  python mock_openai.py --port 9099
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_CANNED_TEXT = "Research complete. No additional candidates to record."


class _State:
    """Thread-safe fault state shared across the server's worker threads."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.mode = "ok"
        self.fail_remaining = -1   # -1 = infinite while a fault mode is active
        self.latency_ms = 0
        self.call_count = 0        # /v1/chat/completions calls seen
        self.fault_count = 0       # of those, how many were faulted

    def set_fault(self, mode: str, count=None, latency_ms: int = 0) -> None:
        with self._lock:
            self.mode = mode or "ok"
            self.fail_remaining = -1 if count is None else int(count)
            self.latency_ms = int(latency_ms or 0)

    def reset(self) -> None:
        with self._lock:
            self.mode = "ok"
            self.fail_remaining = -1
            self.latency_ms = 0

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "mode": self.mode,
                "fail_remaining": self.fail_remaining,
                "latency_ms": self.latency_ms,
                "call_count": self.call_count,
                "fault_count": self.fault_count,
            }

    def decide(self) -> tuple[str, int]:
        """Decide how to handle one chat-completions call. Returns (action, latency_ms)
        where action is 'ok' | 'rate_limit' | 'error' | 'down'."""
        with self._lock:
            self.call_count += 1
            latency = self.latency_ms
            if self.mode == "ok" or self.fail_remaining == 0:
                return "ok", latency
            # a fault mode is active and not yet healed
            if self.fail_remaining > 0:
                self.fail_remaining -= 1
            self.fault_count += 1
            return self.mode, latency


STATE = _State()


def _canned_completion(model: str) -> dict:
    return {
        "id": "chatcmpl-mock",
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": _CANNED_TEXT},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 6, "total_tokens": 16},
    }


def _sse_chunks(model: str):
    base = {"id": "chatcmpl-mock", "object": "chat.completion.chunk", "created": 0, "model": model}
    # role+content delta, then a stop chunk, then a usage-only chunk (stream_usage=True).
    yield {**base, "choices": [{"index": 0, "delta": {"role": "assistant", "content": _CANNED_TEXT}, "finish_reason": None}]}
    yield {**base, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
    yield {**base, "choices": [], "usage": {"prompt_tokens": 10, "completion_tokens": 6, "total_tokens": 16}}


class Handler(BaseHTTPRequestHandler):
    # silence the default request logging (keeps fault-test output readable)
    def log_message(self, *args) -> None:  # noqa: D401
        pass

    def _json(self, code: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            return {}

    def do_GET(self) -> None:
        if self.path == "/health":
            return self._json(200, {"status": "ok"})
        if self.path == "/__fault__":
            return self._json(200, STATE.snapshot())
        return self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path == "/__fault__":
            body = self._read_body()
            STATE.set_fault(body.get("mode", "ok"), body.get("count"), body.get("latency_ms", 0))
            return self._json(200, STATE.snapshot())
        if self.path == "/__reset__":
            STATE.reset()
            return self._json(200, STATE.snapshot())
        if self.path.endswith("/chat/completions"):
            return self._chat_completion()
        return self._json(404, {"error": "not found"})

    def _chat_completion(self) -> None:
        body = self._read_body()
        model = body.get("model", "gpt-mock")
        action, latency_ms = STATE.decide()

        if latency_ms:
            time.sleep(latency_ms / 1000.0)

        if action == "rate_limit":
            return self._json(429, {"error": {"message": "Rate limit reached", "type": "rate_limit_error"}})
        if action == "error":
            return self._json(500, {"error": {"message": "Internal server error", "type": "server_error"}})
        if action == "down":
            return self._json(503, {"error": {"message": "Service unavailable", "type": "server_error"}})

        # healthy: return a no-tool-call completion that ends the agent loop.
        if body.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for chunk in _sse_chunks(model):
                self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
            self.wfile.write(b"data: [DONE]\n\n")
            return
        return self._json(200, _canned_completion(model))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9099)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"[mock-openai] listening on http://{args.host}:{args.port} (/v1/chat/completions)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
