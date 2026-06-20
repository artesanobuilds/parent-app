"""
Minimal SSE reader.

The backend uses two SSE endpoints — `/chat` (parent coaching) and `/kid-chat`
(kid agent). Both emit `data: ...\\n\\n`-delimited events. For flow tests we
just need to:

- send the POST
- read until the stream closes or a terminal event arrives
- return the list of decoded events for assertions

Anything fancier (interactive streaming, partial-token assertions) belongs in
the test itself.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Iterator, Optional

import httpx


@dataclass
class SseEvent:
    event: str  # SSE 'event:' field (defaults to "message" when absent)
    data: str   # raw data line(s) joined
    json: dict | list | str | None = None  # parsed if data was JSON

    @classmethod
    def from_raw(cls, event_name: str, data_lines: list[str]) -> "SseEvent":
        data = "\n".join(data_lines)
        parsed: dict | list | str | None = None
        if data.strip().startswith(("{", "[")):
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError:
                parsed = data
        else:
            parsed = data
        return cls(event=event_name or "message", data=data, json=parsed)


@dataclass
class SseCollectedStream:
    status_code: int
    events: list[SseEvent] = field(default_factory=list)

    def events_of(self, event_name: str) -> list[SseEvent]:
        return [e for e in self.events if e.event == event_name]

    def text(self) -> str:
        """All `data:` payloads concatenated — useful for token-stream flows."""
        return "".join(
            e.data for e in self.events
            if isinstance(e.json, str) or e.json is None
        )


def post_sse(
    base_url: str,
    path: str,
    *,
    json_body: dict,
    headers: Optional[dict] = None,
    timeout: float = 60.0,
) -> SseCollectedStream:
    """
    POST + read the SSE stream to completion. Returns the full event list.

    Note: this is *not* an interactive reader. It blocks until the server
    closes the stream. For long-running streams that should be interrupted
    on a terminal event, build a generator-style wrapper.
    """
    full_url = base_url.rstrip("/") + path
    final_headers = {"Accept": "text/event-stream"}
    if headers:
        final_headers.update(headers)

    events: list[SseEvent] = []
    with httpx.Client(timeout=timeout) as client:
        with client.stream("POST", full_url, json=json_body, headers=final_headers) as resp:
            status = resp.status_code
            if status != 200:
                # Drain body so we get a useful error
                body = resp.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"SSE POST {path} returned {status}: {body[:500]}")
            for event in _iter_sse(resp.iter_lines()):
                events.append(event)
    return SseCollectedStream(status_code=status, events=events)


def _iter_sse(lines: Iterator[str]) -> Iterator[SseEvent]:
    event_name = ""
    data_lines: list[str] = []
    for raw in lines:
        line = raw.rstrip("\n").rstrip("\r")
        if line == "":
            # End of event
            if data_lines:
                yield SseEvent.from_raw(event_name, data_lines)
            event_name = ""
            data_lines = []
            continue
        if line.startswith(":"):
            # SSE comment / keep-alive
            continue
        if line.startswith("event:"):
            event_name = line[len("event:"):].strip()
            continue
        if line.startswith("data:"):
            data_lines.append(line[len("data:"):].lstrip(" "))
            continue
        # Unknown field — ignore per SSE spec
    # Tail flush
    if data_lines:
        yield SseEvent.from_raw(event_name, data_lines)
