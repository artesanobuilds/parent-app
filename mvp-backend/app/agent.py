"""The parent agent — ONE harness for the whole parent experience.

Coach and Chief-of-Staff used to be two separate `create_agent` graphs with
their own models, checkpointers and caches (`app/agent.py` + `app/cos/agent.py`).
They are now a SINGLE agent: one identity (Coach), one toolset, one thread per
parent across the text surfaces. `app/cos/agent.get_cos_agent` is a shim that
returns this agent.

Three things that are easy to get wrong here:

1. **All tools are registered flat.** LangChain has no API to add or remove
   tools after `create_agent()` (langchain#33808) — middleware can only filter
   what is already registered. `LLMToolSelectorMiddleware` exists and is
   deliberately NOT used: our whole tool block is ~3k prompt-cacheable tokens,
   and the selector trades that cached prefix for an extra model call every
   turn, while a `max_tools` cap would starve exactly the turns that motivated
   the merge ("Ben's summer is a mess" needs profile + activity search +
   calendar together).

2. **The summarizer's tokens must never reach the parent.** Middleware model
   calls surface on `astream_events` as ordinary `on_chat_model_stream` events
   — verified against the installed langchain, not assumed. Left alone, the
   context summary would be printed into the chat and SPOKEN on voice. Every
   internal model is tagged `INTERNAL_STREAM_TAG` and every streaming surface
   drops events carrying it (`is_internal_event`).

3. **Thread repair runs on every entry.** A cancelled tool call leaves a
   dangling `tool_calls` checkpoint that makes OpenAI 400 the thread forever
   (`app/thread_repair.py`). `tests/agents/test_merged_agent_harness.py` fails
   if a surface streams this agent without repairing first.
"""
import json
from app.agent_runtime.cache import AgentCache
from app.agent_runtime.cancellation import VoiceCancellationMiddleware

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ContextEditingMiddleware,
    ClearToolUsesEdit,
    PIIMiddleware,
    SummarizationMiddleware,
    ToolCallLimitMiddleware,
)
from langchain.tools import tool
from dotenv import load_dotenv
from pydantic import BaseModel

from app.profiling import profiling_service
from app.services.profiles import ParentUpdate, ChildUpdate, update_parent, update_child
from app.services.operations import durable_tool
from app.content import content_catalog_for_prompt
from app.checkpointing import checkpointer
from app.cos.prompt import COS_ROLE_SECTIONS

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize LLM. stream_usage=True so token usage surfaces during streaming
# (needed by the cost-logging callback).
model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-5.2")
llm = ChatOpenAI(model=model_name, stream_usage=True)

# Initialize Tools
search = TavilySearch(max_results=2)
tools = [search]

# Memory. `checkpointer` is re-exported (imported above) rather than
# constructed here: it is now the ONE durable SQLite saver shared by this agent,
# the kid agent and the onboarding agent, so agent context survives a restart
# (app/checkpointing.py). The symbol name is unchanged — every call site still
# passes `checkpointer=checkpointer`.

# Load soul file once at module level
_soul_path = Path(__file__).resolve().parent.parent / "soul.md"
_soul_content = _soul_path.read_text(encoding="utf-8")
logger.info("Loaded soul.md (%d chars)", len(_soul_content))


# --------------------------------------------------------------------------- #
# Threads
# --------------------------------------------------------------------------- #
# Coach and Chief-of-Staff kept SEPARATE conversations (`cos:{user}:{thread}`
# vs `{user}:{thread}`). One agent means one conversation: every TEXT surface
# now lands on the same per-parent thread, so a plan built on the board is in
# the coach's head and vice versa. Voice stays on its own thread for now — a
# spoken turn and a typed turn have different pacing, and unifying them is an
# open product decision (memory `project_voice_v2_state`).
#
# These ids ARE durable now (app/checkpointing.py) — the checkpointer is a
# SQLite saver on the Railway volume, not an in-process MemorySaver. Renaming a
# thread key therefore orphans real conversation history rather than costing
# nothing, and `DELETE /family/{user_id}` has to sweep them (that sweep matches
# on the `{user_id}:` / `onboarding:` / `kid:` segment, so keep user_id first).
#
# Coach is no longer ONE text thread: sprint-2 gives the parent a list of named
# past conversations, so the merged text thread is now per-CONVERSATION
# (`{user}:parent:{conversation_id}`) with the legacy un-suffixed
# `{user}:parent` kept as the conversation every existing beta parent is
# already mid-way through. Voice deliberately stays on `{user}:default`:
# voice and text threads are separate (memory `project_voice_v2_state`) and
# voice conversations must NOT appear in the coach history list.

PARENT_TEXT_THREAD = "parent"
PARENT_VOICE_THREAD = "voice"

_TEXT_SURFACES = ("chat", "cos")


def thread_key(
    user_id: str,
    surface: str,
    thread_id: str | None = None,
    conversation_id: str | None = None,
) -> str:
    """The LangGraph thread id for one parent on one surface.

    ``surface`` is "chat" or "cos" (both collapse to the parent's ONE ACTIVE
    text conversation, ignoring the client's per-install ``thread_id``), or
    "voice", which keeps its own per-``thread_id`` namespace.

    ``conversation_id`` names WHICH text conversation. Omitted means the
    legacy/default one, so every pre-sprint-2 thread keeps resolving to the
    same key. It is a stable minted id (`app/coach_threads.new_conversation_id`)
    and never a display title — a rename must not move the thread (CLAUDE.md:
    key by stable IDs, not editable display names).
    """
    if surface in _TEXT_SURFACES:
        if conversation_id:
            return f"{user_id}:{PARENT_TEXT_THREAD}:{conversation_id}"
        return f"{user_id}:{PARENT_TEXT_THREAD}"
    return f"{user_id}:{thread_id or 'default'}"


# --------------------------------------------------------------------------- #
# Internal model calls (summarization) must not leak into a surface's stream
# --------------------------------------------------------------------------- #

INTERNAL_STREAM_TAG = "mvp:internal"


def is_internal_event(event: Mapping[str, Any]) -> bool:
    """True for an `astream_events` event produced by an INTERNAL model call
    (context summarization), which must never be shown or spoken.

    Verified behavior, not a precaution: with `SummarizationMiddleware` the
    summarizer's output arrives as ordinary `on_chat_model_stream` events on
    both v1 and v2, so a surface that doesn't filter would print the summary
    into the parent's chat.
    """
    tags = event.get("tags") or ()
    return INTERNAL_STREAM_TAG in tags


def _internal_llm() -> ChatOpenAI:
    """A separate, tagged model instance for middleware's own calls."""
    name = os.getenv("MVP_INTERNAL_MODEL_NAME", model_name)
    return ChatOpenAI(model=name).with_config(tags=[INTERNAL_STREAM_TAG])


# --------------------------------------------------------------------------- #
# Middleware — the harness
# --------------------------------------------------------------------------- #
# Adopted only where the async hook exists on the INSTALLED langchain (this is
# an async FastAPI backend; a middleware with only the sync hook raises
# NotImplementedError mid-turn — langchain#33474). All four below implement
# their `a*` hooks in langchain 1.3.10; `tests/agents/test_merged_agent_harness`
# re-checks that on every run so an upgrade can't silently regress it.

# One merged thread outgrows the window; summarize far below the model's limit
# so a long planning session never hard-fails.
SUMMARIZE_TRIGGER_TOKENS = int(os.getenv("MVP_SUMMARIZE_TRIGGER_TOKENS", "120000"))
SUMMARIZE_KEEP_MESSAGES = int(os.getenv("MVP_SUMMARIZE_KEEP_MESSAGES", "30"))

# COS tools return large plan snapshots (GetPlanSnapshot, SearchActivities,
# CompareActivities). Old ones are pure noise once acted on — clear them and
# keep the last few verbatim.
CONTEXT_EDIT_TRIGGER_TOKENS = int(os.getenv("MVP_CONTEXT_EDIT_TRIGGER_TOKENS", "60000"))
CONTEXT_EDIT_KEEP_RESULTS = int(os.getenv("MVP_CONTEXT_EDIT_KEEP_RESULTS", "5"))

# A runaway tool loop is a cost event, not just a slow turn. Generous enough
# that a real "sort out my summer" turn (snapshot + compare + several tracks)
# never trips it.
TOOL_CALLS_PER_RUN = int(os.getenv("MVP_TOOL_CALLS_PER_RUN", "40"))

def build_middleware() -> list:
    """The agent harness. See the module docstring for what was rejected."""
    return [
        VoiceCancellationMiddleware(),
        # Order matters: PII scrubs the incoming turn BEFORE anything else sees
        # it, so a card never reaches the model, the checkpoint, or the
        # summarizer's input.
        PIIMiddleware(
            "credit_card",
            strategy="mask",
            apply_to_input=True,
            apply_to_output=True,
            apply_to_tool_results=False,
        ),
        SummarizationMiddleware(
            model=_internal_llm(),
            trigger=("tokens", SUMMARIZE_TRIGGER_TOKENS),
            keep=("messages", SUMMARIZE_KEEP_MESSAGES),
        ),
        ContextEditingMiddleware(
            edits=[
                ClearToolUsesEdit(
                    trigger=CONTEXT_EDIT_TRIGGER_TOKENS,
                    keep=CONTEXT_EDIT_KEEP_RESULTS,
                    # Inputs stay: "which activity did I just track" is the
                    # cheap half and the model reasons over it.
                    clear_tool_inputs=False,
                    # The two tools whose OUTPUT is the answer, not a lookup.
                    exclude_tools=("DraftEmail", "Help"),
                )
            ],
        ),
        ToolCallLimitMiddleware(run_limit=TOOL_CALLS_PER_RUN, exit_behavior="end"),
    ]


def _prune_empty(value: Any) -> Any:
    """Recursively prune empty/None values from dicts/lists to keep prompt lean."""
    if isinstance(value, dict):
        pruned = {k: _prune_empty(v) for k, v in value.items()}
        return {k: v for k, v in pruned.items() if v not in (None, [], {}, "")}
    if isinstance(value, list):
        pruned_list = [_prune_empty(v) for v in value]
        return [v for v in pruned_list if v not in (None, [], {}, "")]
    return value


_COACH_SECTIONS = """\
# Operational context

You are ONE agent doing two jobs for this parent, and you switch between them
without announcing it:

1. **Coaching** — the hard parenting moments. This is the voice and the
   response shape above: short, warm, one useful thing.
2. **Running the logistics** — camps, classes, school life, trips, the
   calendar, the to-dos. Detailed below.

Most turns are one or the other, and the good ones are both: "Ben's summer is a
mess" is a coverage problem AND an overwhelmed parent. Read the family profile,
call the planning tools, and answer the whole thing in one turn — never tell the
parent to go somewhere else in the app for the other half.

When you are running logistics the brevity ceiling relaxes: a tradeoff table or
a week-by-week gap list is the useful answer. Everything else about your voice
still holds.

Web search: use for factual claims or recent info. Cite sources as markdown links.

Content library: when relevant, weave max 1 link per response naturally into your
sentence. Format: [Title](mvp://library/slug)

Never emit an mvp://community/ link. The public board was retired with the
beta-v1 sprint-2 Circle redesign: the tables are dropped, the routes 404 and no
client handles that scheme, so such a link is dead on arrival. Library is the
only mvp:// host that resolves. Locked by tests/test_coach_citation_contract.py.
"""

_PASSIVE_PROFILING_SECTION = """\
# Passive profiling

As you coach, silently extract profile details from what the parent shares.
Call LearnedAboutParent or LearnedAboutChild whenever the conversation reveals new info about:
- The parent: household, work, stress patterns, coping, energy, goals, support system, parenting style, etc.
- A child: temperament, triggers, interests, challenges, school, sleep, escalation patterns, etc.

Signup no longer asks for any of these, so you are the ONLY way they are ever
learned — record them the moment the parent mentions them, and let a natural
opening surface them (never interrogate):
parent_age_range, employment, pronouns, cultural_background, adults_in_household,
energy_pattern, dreaded_moment, support_system, and each child's pronouns.

Rules:
- NEVER ask questions just to fill the profile. Your primary job is coaching. Profile building is a silent side effect.
- Only record what the parent actually said or clearly implied. Don't infer beyond their words.
- Partial updates are fine — send only the fields you learned in that exchange.
- Don't mention the profile or that you're tracking anything. Just coach naturally."""


def _build_system_prompt(
    user_name: str,
    profile_context: str | None = None,
    household_context: str | None = None,
    for_you_context: str | None = None,
) -> str:
    """Assemble the merged prompt.

    Ordered STATIC → DYNAMIC on purpose: soul, role sections, catalog and the
    profiling rules are identical for every turn and cache as one prefix; the
    family profile, the Circle roster and the ranked article shortlist change
    as the parent uses the app and go last.
    """
    dynamic: List[str] = []
    if household_context:
        dynamic.append(household_context)
    if profile_context:
        dynamic.append(
            "Family profile (weave into advice, never dump as raw data):\n"
            + profile_context
        )
    if for_you_context:
        dynamic.append(for_you_context)

    parts = [
        _soul_content,
        "---",
        _COACH_SECTIONS,
        f'User: "{user_name}" — use their name when natural.',
        content_catalog_for_prompt(),
        COS_ROLE_SECTIONS,
        _PASSIVE_PROFILING_SECTION,
    ]
    if dynamic:
        parts.append("# This family\n\n" + "\n\n".join(dynamic))
    return "\n\n".join(parts)


def _make_parent_tool(user_id: str):
    @durable_tool(user_id)
    def LearnedAboutParent(parent_updates: ParentUpdate) -> str:
        """
        Silently save new details about the parent gleaned from the conversation.
        Call this whenever the parent reveals something about themselves: household,
        work, stress triggers, coping, energy patterns, goals, etc.
        Partial updates are fine — send only the fields you learned.
        """
        payload = parent_updates.model_dump(exclude_none=True)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[coaching_tool] LearnedAboutParent user_id={user_id} updates={payload}")
        updated = update_parent(user_id, payload)
        return "Parent profile updated."

    return LearnedAboutParent


def _make_child_tool(user_id: str):
    @durable_tool(user_id)
    def LearnedAboutChild(update: ChildUpdate) -> str:
        """
        Silently save new details about a child gleaned from the conversation.
        Call this whenever the parent reveals something about a child: temperament,
        triggers, interests, challenges, school context, etc.
        child_name is required; send only the fields you learned.
        """
        payload = update.model_dump(exclude_none=True)
        child_name = payload.pop("child_name")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[coaching_tool] LearnedAboutChild user_id={user_id} child_name={child_name} updates={payload}")
        updated = update_child(user_id, child_name, payload)
        return "Child profile updated."

    return LearnedAboutChild


def build_parent_tools(user_id: str) -> list:
    """Every tool the merged agent can reach, flat.

    Coach half: web search + the two passive-profiling tools (still the ONLY
    way the fields the funnel stopped asking for are ever learned — memory
    `patterns_onboarding_parity`). Chief-of-Staff half: the full planning
    toolset, unchanged and still owned by `app/cos/tools.py`.
    """
    from app.cos.tools import build_cos_tools

    return [
        search,
        _make_parent_tool(user_id),
        _make_child_tool(user_id),
        *build_cos_tools(user_id),
    ]


_agent_cache = AgentCache()

def _saved_signal_context(user_name: str) -> str:
    """Revealed preference: what this parent actually SAVES (vs the goals they
    typed at onboarding). Appended to the profile context so the existing
    cache-on-profile-string invalidation rebuilds the agent when saves change.
    Read-time only — never written into the editable profile."""
    try:
        from app.server import storage_backend
        signal = storage_backend.saved_signal(user_name)
    except Exception:
        return ""
    if not signal["top_tags"] and not signal["recent_titles"]:
        return ""
    lines = ["", "What they save (revealed interest - weigh alongside stated goals):"]
    if signal["top_tags"]:
        lines.append("Recurring topics: " + ", ".join(
            f"{tag} (x{count})" for tag, count in signal["top_tags"]
        ))
    if signal["recent_titles"]:
        lines.append("Recently saved: " + "; ".join(signal["recent_titles"]))
    return "\n".join(lines)


def _household_context(user_id: str) -> str:
    """The Circle roster as prompt text (empty when there is none)."""
    try:
        from app.household import household_context_for_prompt

        return household_context_for_prompt(user_id)
    except Exception:  # noqa: BLE001
        logger.warning("[agent] household context unavailable", exc_info=True)
        return ""


def _for_you_context(family: Dict[str, Any]) -> str:
    """The ranked library shortlist — the same ranking `GET /content/for-you`
    serves. The Library is no longer browsable, so the agent is the path."""
    try:
        from app import content as content_service

        return content_service.for_you_prompt_lines(
            content_service.for_you_word_bag(family or {})
        )
    except Exception:  # noqa: BLE001
        return ""


def _dynamic_context(user_name: str) -> Dict[str, Optional[str]]:
    """Everything in the prompt that changes as the parent uses the app.

    Returned as one bundle because the agent cache is keyed on it: any change
    to the profile, the Circle roster or the ranked shortlist rebuilds the
    agent with a fresh prompt.
    """
    raw_profile = profiling_service.get_family_profile(user_name)
    pruned_profile = _prune_empty(raw_profile)
    profile_context = (
        json.dumps(pruned_profile, ensure_ascii=False, indent=2)
        if pruned_profile
        else None
    )
    saved_context = _saved_signal_context(user_name)
    if saved_context:
        profile_context = (profile_context or "") + saved_context
    return {
        "profile": profile_context,
        "household": _household_context(user_name) or None,
        "for_you": _for_you_context(raw_profile) or None,
    }


def get_agent(user_name: str = "0", *, surface: str = "text"):
    """Return the cached merged parent agent personalized to this parent."""
    from app.voice_policy import is_voice_surface, PARENT_VOICE_POLICY
    voice = is_voice_surface(surface)
    context = _dynamic_context(user_name)
    # One tenant slot keeps existing cache invalidation APIs valid. Surface
    # switches rebuild the graph rather than reusing a text prompt for speech.
    context = {**context, "surface": surface}
    prompt = _build_system_prompt(
        user_name, profile_context=context["profile"],
        household_context=context["household"], for_you_context=context["for_you"],
    ) + (PARENT_VOICE_POLICY if voice else "")

    cached = _agent_cache.get(user_name)
    if cached and cached.get("context") == context and cached.get("prompt") == prompt:
        return cached["agent"]

    agent_executor = create_agent(
        model=llm,
        tools=build_parent_tools(user_name),
        checkpointer=checkpointer,
        middleware=build_middleware(),
        system_prompt=prompt,
    )
    _agent_cache[user_name] = {
        "agent": agent_executor,
        "context": context,
        "prompt": prompt,
        # Back-compat: callers/tests that inspected the old cache shape.
        "profile": context["profile"],
    }
    return agent_executor


def build_system_prompt_for(user_name: str = "0", *, surface: str = "text") -> str:
    """Public: assemble the merged agent's per-user system prompt. Used by the
    ConvAI token endpoint to override the dashboard agent's prompt per
    connection, mirroring get_agent's assembly."""
    from app.voice_policy import is_voice_surface, PARENT_VOICE_POLICY
    voice = is_voice_surface(surface)
    context = _dynamic_context(user_name)
    return _build_system_prompt(
        user_name,
        profile_context=context["profile"],
        household_context=context["household"],
        for_you_context=context["for_you"],
    ) + (PARENT_VOICE_POLICY if voice else "")
