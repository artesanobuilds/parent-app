# flows/generated/test_registration_watch.py
#
# @generated_from: specs/tier-1/registration-watch.flow.yml
# @generated_at: 2026-07-11T00:00:00Z
# @modules: cos, chat, watchlist
# @promoted_by: (none -- awaiting review)
#
import sys
from pathlib import Path

import pytest

# Make `lib` importable even when pytest is invoked from a different cwd.
HARNESS_ROOT = Path(__file__).resolve().parents[2]
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from lib.sse import post_sse  # noqa: E402

pytestmark = [pytest.mark.tier1, pytest.mark.sse, pytest.mark.requires_openai]


def _non_empty_reply(stream) -> str:
    parts = []
    for e in stream.events:
        j = e.json
        if isinstance(j, dict) and j.get("type") == "token":
            parts.append(j.get("content", ""))
    return "".join(parts)


def test_stated_date_becomes_a_watched_window(flow_ctx, existing_parent):
    if flow_ctx.readonly:
        pytest.skip("write flow (creates a registration window); skipped on prod")
    if not flow_ctx.env.run_openai_flows:
        pytest.skip("RUN_OPENAI_FLOWS=false; /cos/chat would spend tokens")

    parent = existing_parent
    auth = {"Authorization": f"Bearer {parent.token}"}

    s = post_sse(
        flow_ctx.base_url,
        "/cos/chat",
        json_body={
            "user_id": parent.user_id,
            "thread_id": "registration-watch-flow",
            "message": "Rec soccer signup opens August 12 — don't let me miss it.",
        },
        headers=auth,
    )
    assert s.status_code == 200
    assert _non_empty_reply(s).strip(), "assistant reply was empty"

    resp = flow_ctx.get("/cos/windows", as_=parent)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "windows" in body
    watching = [w for w in body["windows"] if w.get("status") == "watching"]
    assert watching, f"no watching window created: {body['windows']}"
    window = watching[0]
    assert "-08-" in (window.get("opens_at") or ""), (
        f"opens_at not in August: {window.get('opens_at')}"
    )
    # Parent-stated dates are the 100% promise — never 'estimated'.
    assert window.get("confidence") == "confirmed", window

    # Dismiss quiets it. (FlowContext has no PATCH verb — plain httpx.)
    import httpx

    patched = httpx.patch(
        f"{flow_ctx.base_url}/cos/windows/{window['id']}",
        json={"user_id": parent.user_id, "action": "dismiss"},
        headers=auth,
        timeout=15.0,
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["window"]["status"] == "dismissed"
