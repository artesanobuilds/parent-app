"""Snapshot only wire-relevant OpenAPI, including transitively used schemas."""
import json
from pathlib import Path

PATHS = {
    "/family/{user_id}", "/admin/users/{user_id}/reset", "/admin/users/{user_id}/delete",
    "/chat", "/cos/chat", "/cos/messages", "/onboarding-chat", "/kid-chat",
    "/v1/chat/completions", "/v1/parent/chat/completions", "/coach/threads",
    "/coach/threads/{conversation_id}", "/profile", "/profile/seed",
    "/research/runs", "/research/runs/{run_id}", "/research/runs/{run_id}/stream",
    "/research/runs/{run_id}/cancel", "/research/runs/{run_id}/candidates",
    "/onboarding/warmup", "/onboarding/warmup/{run_id}",
    "/onboarding/warmup/{run_id}/stream", "/coach/nudge",
}
SNAPSHOT = Path(__file__).parent / "fixtures" / "harness-openapi.json"


def wire_schema(document):
    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if k not in {"description", "summary", "title", "operationId", "tags"}}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value

    missing = PATHS - document["paths"].keys()
    assert not missing, f"Public routes removed: {missing}"
    result = {"paths": {p: clean(document["paths"][p]) for p in sorted(PATHS)}, "components": {"schemas": {}}}
    todo = [result["paths"]]
    while todo:
        item = todo.pop()
        if isinstance(item, list):
            todo.extend(item)
        elif isinstance(item, dict):
            ref = item.get("$ref", "")
            if ref.startswith("#/components/schemas/"):
                name = ref.rsplit("/", 1)[1]
                if name not in result["components"]["schemas"]:
                    schema = clean(document["components"]["schemas"][name])
                    result["components"]["schemas"][name] = schema
                    todo.append(schema)
            todo.extend(item.values())
    return result


def test_agent_openapi_is_backward_compatible(harness):
    assert wire_schema(harness.server.app.openapi()) == json.loads(SNAPSHOT.read_text())
