import logging
import json
import os
from typing import Any, Dict, Optional, List

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from pydantic import BaseModel

from app.checkpointing import checkpointer
from app.profiling import profiling_service

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize LLM. stream_usage=True so token usage surfaces during streaming
# (captured by the cost-logging callback on /onboarding-chat).
model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-5.2")
llm = ChatOpenAI(model=model_name, stream_usage=True)

# Initialize Tools
search = TavilySearch(max_results=2)

# Memory. Re-exported from app/checkpointing (imported above): the ONE durable
# SQLite saver shared with the parent + kid agents, so a half-finished
# onboarding chat survives a restart instead of restarting from nothing.
# Onboarding thread ids are `onboarding:{user}:{thread}`.


def _prune_empty(value: Any) -> Any:
    """Recursively prune empty/None values from dicts/lists to keep prompt lean."""
    if isinstance(value, dict):
        pruned = {k: _prune_empty(v) for k, v in value.items()}
        return {k: v for k, v in pruned.items() if v not in (None, [], {}, "")}
    if isinstance(value, list):
        pruned_list = [_prune_empty(v) for v in value]
        return [v for v in pruned_list if v not in (None, [], {}, "")]
    return value


def _build_system_prompt(user_name: str, profile_context: str | None = None) -> str:
    profile_section = ""
    if profile_context:
        profile_section = f"""

Profile context (use when relevant; keep enriching):
{profile_context}

- This is what you have learned about the parent and kids; continue filling these profiles further.
- Use the context to ask sharper, shorter follow-ups and tailor suggestions.
- Do not dump the JSON back to the user; weave it into concise responses.
"""

    return f"""
You are MVP (Most Value Parent), an onboarding parenting coach. Your sole goal is to interview {{user}} to build structured parent and child profiles for personalized guidance. Keep tone warm, concise, and practical; prefer bullets.

What the signup funnel ALREADY captured (do NOT re-ask — you have it below in the profile context):
- Parent: name, household structure, education style, postal_code, what's hardest right now (stressors).
- Each child: name, age, temperament/personality traits.

What the funnel NO LONGER asks — YOU are now the only way these are ever learned, so treat them as HIGH PRIORITY and work them in naturally as the conversation gives you an opening (never as a form, never as a rapid-fire list):
- primary_language + secondary_language (language(s) spoken at home)
- goals (what would actually help them — the funnel used to ask this as "What would help")
- parent_age_range (bracket only — never ask for exact age)
- employment (work situation)
- pronouns (the parent's)
- cultural_background
- adults_in_household (1–4)
- energy_pattern (when in the day they have most/least in the tank)
- dreaded_moment (the part of the day they brace for)
- support_system (who they can actually call on)
- each child's pronouns

Everything else to gather (prioritize clarity over completeness):
- Parent demographics: approximate location (postal_code + country), primary language at home.
- Parent context: household structure, work hours, default stress response, support boundaries, parenting style tendencies, current stressors, goals/pain points, coping/de-escalation (what works/backfires), mental/physical health notes (non-clinical), coparent dynamics/boundaries, preferred guidance style.
- Each child: name, age, grade_band (Pre-K, K, 1–12, or N/A), temperament/traits (e.g., sensitivity, intensity, adaptability), interests/motivators, strengths (incl. academic), current challenges, triggers, escalation pattern, calming strategies, emotion regulation + triggers, social profile, learning profile (visual/auditory/kinesthetic, EF notes), neurodiversity/special needs/health, sensory notes, recent changes, school context/teacher notes, sibling conflict patterns, repair helpers, sleep/routines, safety flags.

How to operate:
- Ask concise, empathic questions; reflect back specifics learned. Be very succinct and compress information into the fewest words possible. As if it was a conversation with wise coach.
- When you have new structured info, call FoundMoreAboutParent or FoundMoreAboutChild(child_name) with JSON fields (partial updates are fine). Provide only fields you can back with the user’s words or clear inferences.
- Default to actionable next questions; avoid long monologues. Offer small-fit suggestions only when enough context is known.
- Avoid medical advice; invite professionals for clinical concerns.
- Use web search when a factual, time-sensitive, or example reference would improve the interview or suggestions.
- Don't suggest tools, methods or solutions. You job is just to learn about the user and their family.
- CRITICAL:When you're gathering the information, channel Dr Becky Kennedy, Carl Jung, Dr Daniel Amen and Gabor Mate, how would a human combining all their wisdom and experience would ask the questions to learn about the user and their family.

Personalize to user name: \"{user_name}\".
{profile_section}
    """


class ParentUpdate(BaseModel):
    name: Optional[str] = None
    pronouns: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    primary_language: Optional[str] = None
    # The sprint-1 funnel stopped asking for language (the design's
    # "Let's get acquainted" has four fields and neither is this), so the chat
    # path is now the only way a bilingual household is ever learned. The form
    # path still seeds `secondary_language`, so the field has to exist on BOTH
    # writers or the chat agent would be prompted for something it silently drops.
    secondary_language: Optional[str] = None
    parent_age_range: Optional[str] = None
    adults_in_household: Optional[int] = None
    household_structure: Optional[str] = None
    employment: Optional[str] = None
    work_hours: Optional[str] = None
    energy_pattern: Optional[str] = None
    default_stress_response: Optional[str] = None
    dreaded_moment: Optional[str] = None
    support_system: Optional[str] = None
    support_boundaries: Optional[str] = None
    cultural_background: Optional[str] = None
    parenting_style: Optional[str] = None
    stressors: Optional[List[str]] = None
    goals: Optional[List[str]] = None
    coping_strategies: Optional[List[str]] = None
    deescalation_works: Optional[List[str]] = None
    deescalation_backfires: Optional[List[str]] = None
    mental_health_notes: Optional[str] = None
    co_parenting: Optional[str] = None
    guidance_style: Optional[str] = None


class ChildUpdate(BaseModel):
    child_name: str
    pronouns: Optional[str] = None
    age: Optional[float] = None
    grade_band: Optional[str] = None
    temperament: Optional[str] = None
    interests: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
    academic_strengths: Optional[List[str]] = None
    challenges: Optional[List[str]] = None
    emotion_regulation: Optional[str] = None
    social_profile: Optional[str] = None
    learning_profile: Optional[str] = None
    neurodiversity: Optional[str] = None
    sensory_notes: Optional[str] = None
    sleep_routine: Optional[str] = None
    health_notes: Optional[str] = None
    triggers: Optional[List[str]] = None
    escalation_pattern: Optional[str] = None
    calming_strategies: Optional[List[str]] = None
    recent_changes: Optional[List[str]] = None
    school_context: Optional[str] = None
    teacher_notes: Optional[str] = None
    sibling_conflicts: Optional[List[str]] = None
    repair_helpers: Optional[List[str]] = None
    motivators: Optional[List[str]] = None
    safety_flags: Optional[str] = None


def _make_parent_tool(user_id: str):
    @tool
    def FoundMoreAboutParent(parent_updates: ParentUpdate) -> str:
        """
        Update the parent profile with structured fields (partial updates allowed).
        Fields: name, pronouns, postal_code, country, primary_language, parent_age_range,
        adults_in_household, household_structure, employment, work_hours, energy_pattern,
        default_stress_response, dreaded_moment, support_system, support_boundaries,
        cultural_background, parenting_style, stressors, goals, coping_strategies,
        deescalation_works, deescalation_backfires, mental_health_notes, co_parenting,
        guidance_style.
        """

        if not isinstance(parent_updates, ParentUpdate):
            return "Expected a ParentUpdate payload"
        payload = parent_updates.model_dump(exclude_none=True)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[onboarding_tool] FoundMoreAboutParent user_id={user_id} updates={payload}")
        updated = profiling_service.update_parent_profile(user_id, payload)
        return f"Parent profile updated: {updated}"

    return FoundMoreAboutParent


def _make_child_tool(user_id: str):
    @tool
    def FoundMoreAboutChild(update: ChildUpdate) -> str:
        """
        Update a child profile with structured fields (partial updates allowed).
        Fields: child_name (required), pronouns, age, grade_band, temperament, interests,
        strengths, academic_strengths, challenges, emotion_regulation, social_profile,
        learning_profile, neurodiversity, sensory_notes, sleep_routine, health_notes,
        triggers, escalation_pattern, calming_strategies, recent_changes, school_context,
        teacher_notes, sibling_conflicts, repair_helpers, motivators, safety_flags.
        """

        if not isinstance(update, ChildUpdate):
            return "Expected a ChildUpdate payload"
        payload = update.model_dump(exclude_none=True)
        child_name = payload.pop("child_name")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"[onboarding_tool] FoundMoreAboutChild user_id={user_id} child_name={child_name} updates={payload}")
        updated = profiling_service.update_child_profile(user_id, child_name, payload)
        return f"Child profile updated: {updated}"

    return FoundMoreAboutChild


_onboarding_agent_cache: Dict[str, Any] = {}


def get_onboarding_agent(user_name: str = "0"):
    """Return a cached onboarding agent executor personalized to the given user name."""
    raw_profile = profiling_service.get_family_profile(user_name)
    pruned_profile = _prune_empty(raw_profile)
    profile_context = json.dumps(pruned_profile, ensure_ascii=False, indent=2) if pruned_profile else None

    cached = _onboarding_agent_cache.get(user_name)
    if cached and cached.get("profile") == profile_context:
        return cached["agent"]

    tools = [_make_parent_tool(user_name), _make_child_tool(user_name), search]
    agent_executor = create_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer,
        system_prompt=_build_system_prompt(user_name, profile_context),
    )
    _onboarding_agent_cache[user_name] = {"agent": agent_executor, "profile": profile_context}
    return agent_executor

