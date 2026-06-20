"""
new-parent persona: a freshly-issued bearer token with no consent and no
profile. The canonical starting state for the parent-onboarding flow.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass
class Parent:
    user_id: str
    token: str
    display_name: str = "Test Parent"


def new_parent(flow_ctx) -> Parent:
    """
    Issue a token for a fresh uuid. Register a cleanup that DELETEs
    /family/{user_id} so we don't leave orphan rows across runs.
    """
    user_id = f"{flow_ctx.env.user_id_prefix}-{uuid4()}"
    resp = flow_ctx.post("/auth/issue-token", json={"user_id": user_id})
    if resp.status_code != 200:
        raise RuntimeError(
            f"new_parent: /auth/issue-token returned {resp.status_code}: {resp.text}"
        )
    body = resp.json()
    parent = Parent(user_id=user_id, token=body["token"])

    def _cleanup() -> None:
        # /family/{user_id} requires auth — use the same token we just got
        try:
            flow_ctx.delete(f"/family/{user_id}", as_=parent)
        except Exception:
            # cleanup is best-effort; logged by FlowContext
            pass

    flow_ctx.register_cleanup(
        description=f"DELETE /family/{user_id}",
        fn=_cleanup,
    )
    return parent
