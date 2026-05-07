import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent
from langchain.tools import tool
from dotenv import load_dotenv
from pydantic import BaseModel

from app.profiling import profiling_service
from app.content import content_catalog_for_prompt

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize LLM
model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-5.2")
llm = ChatOpenAI(model=model_name)

# Initialize Tools
search = TavilySearch(max_results=2)
tools = [search]

# Initialize Memory
checkpointer = MemorySaver()

# Load soul file once at module level
_soul_path = Path(__file__).resolve().parent.parent / "soul.md"
_soul_content = _soul_path.read_text(encoding="utf-8")
logger.info("Loaded soul.md (%d chars)", len(_soul_content))


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
Family profile (weave into advice, never dump as raw data):
{profile_context}
"""

    return f"""{_soul_content}

---

# Operational context

User: "{user_name}" — use their name when natural.

Web search: use for factual claims or recent info. Cite sources as markdown links.

Content library: when relevant, weave max 1 link per response naturally into your sentence.
Format: [Title](mvp://library/slug) or [Title](mvp://community/slug)

{content_catalog_for_prompt()}
{profile_section}

# Passive profiling

As you coach, silently extract profile details from what the parent shares.
Call LearnedAboutParent or LearnedAboutChild whenever the conversation reveals new info about:
- The parent: household, work, stress patterns, coping, energy, goals, support system, parenting style, etc.
- A child: temperament, triggers, interests, challenges, school, sleep, escalation patterns, etc.

Rules:
- NEVER ask questions just to fill the profile. Your primary job is coaching. Profile building is a silent side effect.
- Only record what the parent actually said or clearly implied. Don't infer beyond their words.
- Partial updates are fine — send only the fields you learned in that exchange.
- Don't mention the profile or that you're tracking anything. Just coach naturally."""


class ParentUpdate(BaseModel):
    name: Optional[str] = None
    pronouns: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    primary_language: Optional[str] = None
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
        updated = profiling_service.update_parent_profile(user_id, payload)
        return f"Parent profile updated: {updated}"

    return LearnedAboutParent


def _make_child_tool(user_id: str):
    @tool
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
        updated = profiling_service.update_child_profile(user_id, child_name, payload)
        return f"Child profile updated: {updated}"

    return LearnedAboutChild


_agent_cache: Dict[str, Dict[str, Any]] = {}

def get_agent(user_name: str = "0"):
    """Return a cached agent executor personalized to the given user name."""
    raw_profile = profiling_service.get_family_profile(user_name)
    pruned_profile = _prune_empty(raw_profile)
    profile_context = json.dumps(pruned_profile, ensure_ascii=False, indent=2) if pruned_profile else None

    cached = _agent_cache.get(user_name)
    if cached and cached.get("profile") == profile_context:
        return cached["agent"]

    user_tools = [search, _make_parent_tool(user_name), _make_child_tool(user_name)]
    agent_executor = create_agent(
        model=llm,
        tools=user_tools,
        checkpointer=checkpointer,
        system_prompt=_build_system_prompt(user_name, profile_context),
    )
    _agent_cache[user_name] = {"agent": agent_executor, "profile": profile_context}
    return agent_executor
