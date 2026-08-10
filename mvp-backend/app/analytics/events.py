"""Product-analytics event taxonomy — a STRICT allowlist.

Two hard rules for a kids/family app:
  1. Only events named here are sent; only their listed property keys survive.
  2. A denylist of PII-ish keys must NEVER appear in any event (belt-and-braces
     against a future call site passing chat content / a kid's name).

Event names seed from cost_logging.py's `feature` vocabulary (research, cos,
kid_chat, parent_chat, parent_voice, onboarding) plus the auth surface. Values
are opaque/coarse only — counts, statuses, providers, enums. Never free text.
"""
from __future__ import annotations

# event name → allowed property keys
EVENTS: dict[str, set[str]] = {
    # Auth
    "signup_completed": {"provider", "platform"},
    "login_succeeded": {"provider", "platform", "is_new_account", "linked_legacy"},
    "legacy_account_claimed": {"provider"},
    # Onboarding / activation
    "onboarding_completed": {"kid_count", "path"},
    "companion_created": set(),                      # kid companion set up (activation milestone)
    # Conversational agents (COUNTS + LIFECYCLE — never content)
    "chat_opened": {"agent_kind"},                   # opened coach / a companion (engagement)
    "parent_chat_message_sent": {"thread_kind"},
    # Coach conversation history (sprint 2): does the parent actually go BACK to
    # past conversations, and do they start new ones? Counts only — no titles,
    # no ids, nothing about what was discussed.
    "coach_thread_opened": set(),
    "coach_thread_closed": set(),
    "kid_chat_message_sent": {"agent_id"},
    "voice_session_ended": {"surface", "duration_s"},  # pairs with voice_session_started → duration
    # Research / activity planning
    "research_run_started": set(),
    "research_run_completed": {"status", "duration_s", "candidate_count"},
    # activity_type/date_model = the per-vertical funnel segmentation
    # (vertical expansion Phase 3.9). Enums only, never names.
    "activity_tracked": {"status", "activity_type", "date_model"},
    # Fired from lifecycle.transition — the Considering→All-set funnel.
    "activity_stage_advanced": {"to_stage", "activity_type"},
    "plan_exported": {"format"},
    # Voice
    "voice_session_started": {"surface"},
    # Integrations
    "integration_connected": {"provider", "kind"},
    # Content + navigation engagement (client)
    "content_opened": {"type"},                      # library article
    "screen_viewed": {"screen"},                     # every screen (tabs + pushed/presented)
    # Legal acceptance (client) — surface = onboarding | banner. Never content.
    "legal_accepted": {"surface"},
    "legal_reaccept_shown": set(),
    # Circle conversations — the private group threads that replaced 1:1 DMs and
    # the public board (beta-v1 sprint 2). Emitted SERVER-side from app/circle.py.
    # source = directory | post | reply. Never content, never participant ids.
    "circle_conversation_started": {"source"},
    "circle_message_sent": set(),
    # Saved tab (client) — item_type + surface enums only, never titles/content.
    "item_saved": {"item_type", "surface"},
    "item_unsaved": {"item_type", "surface"},
    # Ingest flywheel (Phase 5): every confirm/correct on an extracted item is
    # a labeled example — the corrected/confirmed ratio IS the corpus metric.
    "ingest_uploaded": {"kind"},                     # text | image
    "ingest_item_confirmed": {"event_kind"},
    "ingest_item_corrected": {"event_kind"},
    # Registration-window watchlist (Phase 4) — the retention pillar. Enums
    # only: source manual|email|agent_research, confidence confirmed|estimated,
    # kind t_minus_7|day_of.
    "registration_window_watched": {"source", "confidence"},
    "registration_window_notified": {"kind"},
    "registration_window_confirmed": set(),   # the estimated→confirmed one-tap
    "registration_window_dismissed": set(),
    # Vertical doors ("Plan something" disclosure). door = the vertical key.
    # Tap distribution across doors informs which vertical ships next
    # (plan one-agent-five-doors, Phase 3).
    "door_opened": {"door"},                         # a door tapped in the sheet/menu
    "door_converted": {"door"},                      # its starter prompt actually sent
    # Safety
    "crisis_lock_triggered": {"category"},
    "companion_reactivated": set(),
    # Lifecycle
    "family_deleted": set(),
}

# Property keys that must never be captured, whatever the event. If a call site
# ever tries to pass one, it's dropped (and the guard test fails loudly so it's
# caught before shipping).
DENYLIST: frozenset[str] = frozenset({
    "message", "content", "text", "transcript", "body", "name", "kid_name",
    "child_name", "parent_name", "email", "pin", "token", "custody", "address",
})


def sanitize(event: str, properties: dict | None) -> dict:
    """Return the property subset allowed for `event` (denylisted keys removed).
    Unknown props are dropped silently in prod; unknown EVENTS are the caller's
    concern (see capture())."""
    allowed = EVENTS.get(event, set())
    props = properties or {}
    return {
        k: v for k, v in props.items()
        if k in allowed and k not in DENYLIST
    }
