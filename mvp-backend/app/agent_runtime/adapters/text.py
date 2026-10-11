"""The established token/tool/error SSE envelope, byte-compatible with routes."""
import json
from app.agent_runtime.events import RunEvent

DONE = "data: [DONE]\n\n"

def encode(event: RunEvent) -> str:
    payload = {"type": event.kind}
    if event.kind in ("tool_start", "tool_end"):
        payload["tool"] = event.tool
    else:
        payload["content"] = event.content
    return f"data: {json.dumps(payload)}\n\n"
