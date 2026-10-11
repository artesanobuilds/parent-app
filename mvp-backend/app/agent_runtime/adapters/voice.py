"""Parent voice presentation, independent of graph execution."""
import json
import re
import uuid
from typing import List, Tuple

# Matches the content links the parent agent emits. `id` stops at the closing
# paren; whitespace guards against accidental over-capture.
_LINK_RE = re.compile(r"\[([^\]]*)\]\(mvp://(library|community)/([^)\s]+)\)")
_HOLD_CAP = 120  # backstop: never buffer a "pending link" longer than this
_LINK_TARGETS = ("mvp://library/", "mvp://community/")
_MAX_LABEL = 80  # a content title; anything longer isn't a link label


def _is_plausible_link(tail: str) -> bool:
    """Could `tail` (which starts at a '[') still become an mvp:// link once more
    tokens arrive?

    This is the whole point of the hold. The old rule — hold everything after the
    last '[' until a link closes or 300 chars pile up — stalled speech for up to
    300 characters on ANY bracketed aside in prose, which the parent hears as the
    coach going silent mid-sentence. Now we hold only while the tail is still on a
    path to a real link, and flush the instant it can't be one:

      "[Some tit"              → inside the label      → plausible
      "[Some title]"           → label just closed     → plausible
      "[Some title](mvp://li"  → target prefix-matches → plausible
      "[sic] and then"         → prose aside           → flush now
      "[docs](https://…"       → not an mvp:// target  → flush now
    """
    close = tail.find("]")
    if close == -1:
        # Still inside the label. A "label" this long is prose, not a title.
        return len(tail) - 1 <= _MAX_LABEL
    if close - 1 > _MAX_LABEL:
        return False
    rest = tail[close + 1:]
    if not rest:
        return True                       # "[label]" — the "](" may be next chunk
    if not rest.startswith("("):
        return False                      # "[label] more prose" — never a link
    partial = rest[1:]
    # Prefix-compatible in either direction: "mvp://li" is a partial of the target,
    # "mvp://library/abc" is the target plus an id we're still waiting to close.
    return any(t.startswith(partial) or partial.startswith(t) for t in _LINK_TARGETS)


class _LinkStripper:
    """Incrementally strip mvp:// content links from streamed text, emitting the
    human label as speech and surfacing (kind, id) pairs to fire client tools.
    Holds a trailing partial so a link split across token chunks still matches."""

    def __init__(self) -> None:
        self._buf = ""

    def feed(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        self._buf += text
        out: List[str] = []
        tools: List[Tuple[str, str]] = []
        while True:
            m = _LINK_RE.search(self._buf)
            if not m:
                break
            out.append(self._buf[: m.start()])   # text before the link
            out.append(m.group(1))               # speak the label, drop the URL
            tools.append((m.group(2), m.group(3)))
            self._buf = self._buf[m.end():]
        # Hold from the last '[' ONLY while that tail is still a plausible link in
        # progress — a real link must never leak its URL into speech, but ordinary
        # bracketed prose must not stall it either. _HOLD_CAP stays as a backstop
        # for the pathological case (e.g. "[t](mvp://library/" that never closes).
        idx = self._buf.rfind("[")
        tail = self._buf[idx:] if idx != -1 else ""
        if idx == -1 or len(tail) > _HOLD_CAP or not _is_plausible_link(tail):
            safe, self._buf = self._buf, ""
        else:
            safe, self._buf = self._buf[:idx], tail
        return "".join(out) + safe, tools

    def flush(self) -> str:
        s, self._buf = self._buf, ""
        return s


def _show_content_tool_delta(content_id: str, chat_id: str) -> str:
    """OpenAI tool-call delta for a display-only client tool. finish_reason stays
    null (non-terminal) so the agent keeps talking — contrast the kid endpoint's
    end_call which terminates the turn.

    `show_article` is the ONLY tool name: the community board is retired, iOS
    has no handler for a post card, and firing a tool the client doesn't
    implement is how the ElevenLabs turn stalls."""
    name = "show_article"
    delta = {
        "tool_calls": [{
            "index": 0,
            "id": f"call_{uuid.uuid4().hex[:8]}",
            "type": "function",
            "function": {"name": name, "arguments": json.dumps({"id": content_id})},
        }]
    }
    obj = {
        "id": f"chatcmpl-{chat_id}",
        "object": "chat.completion.chunk",
        "choices": [{"delta": delta, "index": 0, "finish_reason": None}],
    }
    return f"data: {json.dumps(obj)}\n\n"


