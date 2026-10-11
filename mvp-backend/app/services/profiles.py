"""Shared tool schemas and durable profile commands; the public JSON is unchanged."""
import json
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from app.profiling import ProfilingService, profiling_service
from app.services.operations import current_run, storage_for

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


def update_parent(user_id: str, payload: dict) -> dict:
    return _update(user_id, payload)


def update_child(user_id: str, child_name: str, payload: dict) -> dict:
    return _update(user_id, payload, child_name=child_name)


def _update(user_id: str, payload: dict, child_name: str | None = None) -> dict:
    storage = storage_for(user_id)
    with storage.transaction():
        run = current_run()
        storage.assert_family_writable(user_id, run.generation if run else None)
        # Build from durable truth in isolation, so a failed write cannot leak
        # a successful-looking profile into the process cache.
        service = ProfilingService()
        family = _load_family(storage, user_id) or {}
        service.load_snapshot({user_id: family})
        if child_name is None:
            result = service.update_parent_profile(user_id, payload)
        else:
            result = service.update_child_profile(user_id, child_name, payload)
        snapshot = service.get_family_profile(user_id)
        storage.save_user_data(user_id, "profiles", snapshot)
        # Cache refresh is deferred to durable_tool after the outer commit.
        return result


def refresh_profile(user_id: str) -> None:
    storage = storage_for(user_id)
    with storage.transaction():
        storage.assert_family_writable(user_id)
        family = _load_family(storage, user_id)
        if family is not None:
            profiling_service.replace_family_snapshot(user_id, family)


def _load_family(storage, user_id: str) -> dict | None:
    # The legacy read helper converts storage failures to None. A command must
    # distinguish "no profile" from "could not read it" to avoid overwriting it.
    row = storage._con.execute(
        "SELECT data FROM user_data WHERE user_id = ? AND name = 'profiles'", [user_id]
    ).fetchone()
    return json.loads(row[0]) if row else None
