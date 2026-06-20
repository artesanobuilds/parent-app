"""
kid-agent-parent persona: an existing parent who has additionally introduced
a kid agent and set the kid's PIN. Used by the kid-agent-lifecycle flow.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from .existing_parent import existing_parent
from .new_parent import Parent


@dataclass
class KidAgentParent:
    parent: Parent
    kid_name: str
    kid_pin: str
    agent_id: str | None = None
    _flow_ctx: object = field(default=None, repr=False, compare=False)

    @property
    def user_id(self) -> str:
        return self.parent.user_id

    @property
    def token(self) -> str:
        return self.parent.token

    async def voice_fragment_id_for_last_reply(
        self, *, thread_id: str = "voice-harness", message: str = "Tell me a tiny story.",
    ) -> Tuple[str, str]:
        """
        Drive a /kid-chat round-trip in voice_mode and return
        (reply_id, fragment_id) for the first voice fragment emitted.

        The reply_id + fragment_id are the resource-id pair /voice/synthesize
        is keyed on. We read them straight off the SSE stream (the
        `voice_fragment` event payload contains both) so flow specs don't
        need to inline a DuckDB lookup or depend on an admin-only path.

        Raises RuntimeError if the stream emits zero voice_fragment events —
        that means the agent's voice_mode flag isn't set or the chunker
        didn't see a sentence boundary. Either is a backend regression worth
        surfacing loudly.
        """
        import json as _json
        # Local import: lib.sse is only on the path inside the harness, and
        # the persona module is also importable from non-test code that
        # doesn't need SSE machinery.
        from lib.sse import post_sse

        if self._flow_ctx is None:
            raise RuntimeError(
                "KidAgentParent.voice_fragment_id_for_last_reply: persona was "
                "constructed without a flow_ctx reference; can't reach the backend."
            )

        stream = post_sse(
            self._flow_ctx.base_url,
            "/kid-chat",
            json_body={
                "user_id": self.user_id,
                "kid_name": self.kid_name,
                "kid_pin": self.kid_pin,
                "thread_id": thread_id,
                "message": message,
            },
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=60,
        )
        if stream.status_code != 200:
            raise RuntimeError(
                f"voice_fragment_id_for_last_reply: /kid-chat returned "
                f"{stream.status_code}"
            )

        for event in stream.events:
            payload = event.json
            if not isinstance(payload, dict):
                continue
            if payload.get("type") != "voice_fragment":
                continue
            frag = payload.get("content") or {}
            reply_id = frag.get("reply_id")
            fragment_id = frag.get("id")
            if isinstance(reply_id, str) and isinstance(fragment_id, str):
                return reply_id, fragment_id

        raise RuntimeError(
            "voice_fragment_id_for_last_reply: /kid-chat completed without "
            "emitting any voice_fragment events. Is the agent's "
            "invariants.voice_mode = true?"
        )


def kid_agent_parent(flow_ctx, *, kid_name: str = "TestKid", kid_pin: str = "1234") -> KidAgentParent:
    parent = existing_parent(flow_ctx)

    # Create + introduce the kid agent. POST /kid-agent/config does the
    # upsert; the first call also lazily synthesises the agent. We pass a
    # minimal brief; the agent service has its own defaults.
    resp = flow_ctx.post(
        "/kid-agent/config",
        json={
            "user_id": parent.user_id,
            "kid_name": kid_name,
            "brief": "Be warm, curious, and developmentally appropriate.",
            "enable": True,
        },
        as_=parent,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"kid_agent_parent: /kid-agent/config returned {resp.status_code}: {resp.text}"
        )
    agent_id = resp.json().get("id")

    # Set the kid's PIN
    resp = flow_ctx.post(
        "/kid-auth/set-pin",
        json={
            "user_id": parent.user_id,
            "kid_name": kid_name,
            "pin": kid_pin,
        },
        as_=parent,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"kid_agent_parent: /kid-auth/set-pin returned {resp.status_code}: {resp.text}"
        )

    return KidAgentParent(
        parent=parent, kid_name=kid_name, kid_pin=kid_pin,
        agent_id=agent_id, _flow_ctx=flow_ctx,
    )
