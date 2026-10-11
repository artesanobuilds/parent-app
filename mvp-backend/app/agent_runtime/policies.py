"""Admission-time switches; never re-read these during an in-flight turn."""
import os


def shared_execution_enabled(surface: str) -> bool:
    return os.getenv(f"MVP_SHARED_RUNTIME_{surface.upper()}", "0").lower() in {
        "1", "true", "yes",
    }


def cos_active_conversation_enabled() -> bool:
    """Separate behavior correction from shared runtime rollout."""
    return os.getenv("MVP_COS_ACTIVE_CONVERSATION", "0").lower() in {"1", "true", "yes"}


from dataclasses import dataclass


@dataclass(frozen=True)
class AgentPolicy:
    agent_kind: str
    event_version: str
    allow_repair_retry: bool
    output_requires_moderation: bool = False


_POLICIES = {
    'chat': AgentPolicy('parent', 'v1', True),
    'cos': AgentPolicy('parent', 'v1', True),
    'parent_voice': AgentPolicy('parent', 'v2', True),
    'onboarding': AgentPolicy('onboarding', 'v1', False),
    'kid_text': AgentPolicy('kid', 'v1', False, True),
    'kid_voice': AgentPolicy('kid', 'v2', False, True),
}


def policy_for(surface: str) -> AgentPolicy:
    return _POLICIES[surface]
