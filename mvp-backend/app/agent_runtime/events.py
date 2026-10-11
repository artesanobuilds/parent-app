"""Private normalized events, deliberately unrelated to an HTTP envelope."""
from dataclasses import dataclass
from typing import Mapping, Any

@dataclass(frozen=True)
class RunEvent:
    kind: str
    content: str = ""
    tool: str = ""

def normalize(event: Mapping[str, Any]) -> RunEvent | None:
    kind = event.get("event")
    if kind == "on_chat_model_stream":
        content = event["data"]["chunk"].content
        if isinstance(content, str) and content:
            return RunEvent("token", content=content)
    if kind in ("on_tool_start", "on_tool_end"):
        return RunEvent("tool_start" if kind == "on_tool_start" else "tool_end", tool=event.get("name", ""))
    return None
