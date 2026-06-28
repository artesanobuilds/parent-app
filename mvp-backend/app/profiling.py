from dataclasses import dataclass, field, asdict
from threading import Lock
from typing import Any, Dict, List, Optional


def _apply_update(obj: Any, updates: Dict[str, Any], *, replace_lists: bool = False) -> None:
    """Shared partial-update logic for ParentProfile / ChildProfile.

    Scalars are set directly. List fields MERGE by default (extend + dedupe);
    with ``replace_lists=True`` a list field present in ``updates`` is SET to the
    given value (scalar coerced to a 1-item list, None/empty → [])."""
    for key, value in updates.items():
        if not hasattr(obj, key):
            continue
        current = getattr(obj, key)
        if isinstance(current, list):
            if replace_lists:
                if value is None:
                    setattr(obj, key, [])
                elif isinstance(value, list):
                    setattr(obj, key, [v for v in value if v not in (None, "")])
                else:
                    setattr(obj, key, [value])
            elif value:
                if isinstance(value, list):
                    current.extend(v for v in value if v not in current)
                elif value not in current:
                    current.append(value)
        else:
            setattr(obj, key, value)


@dataclass
class ParentProfile:
    """Lightweight parent profile collected during onboarding."""

    name: Optional[str] = None
    pronouns: Optional[str] = None
    postal_code: Optional[str] = None  # zip / international postal code
    country: Optional[str] = None  # ISO-3166 alpha-2 (e.g., US, MX, CA)
    primary_language: Optional[str] = None  # e.g., en, es, zh, "other"
    parent_age_range: Optional[str] = None  # "<25" | "25-34" | "35-44" | "45-54" | "55+" | "prefer_not_to_say"
    adults_in_household: Optional[int] = None  # 1-4
    household_structure: Optional[str] = None  # e.g., single, co-parenting, divorced, widowed
    employment: Optional[str] = None  # e.g., stay-at-home, part-time, full-time, shift
    work_hours: Optional[str] = None  # schedule/availability windows
    energy_pattern: Optional[str] = None  # best/worst times of day
    default_stress_response: Optional[str] = None  # raise voice / withdraw / stays regulated
    dreaded_moment: Optional[str] = None  # e.g., bedtime, mornings
    support_system: Optional[str] = None  # e.g., family nearby, childcare, community, none
    support_boundaries: Optional[str] = None  # how/when helpers engage
    cultural_background: Optional[str] = None
    parenting_style: Optional[str] = None  # e.g., authoritative/connection-first tendencies
    stressors: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    coping_strategies: List[str] = field(default_factory=list)
    deescalation_works: List[str] = field(default_factory=list)
    deescalation_backfires: List[str] = field(default_factory=list)
    mental_health_notes: Optional[str] = None  # non-clinical, self-reported
    co_parenting: Optional[str] = None  # notes about coordination/boundaries
    guidance_style: Optional[str] = None  # concise scripts vs. explanations

    def apply_update(self, updates: Dict[str, Any], *, replace_lists: bool = False) -> None:
        """Merge partial updates into the parent profile.

        List fields are normally MERGED (extend + dedupe) — that's how the
        coaching/onboarding agents accumulate facts over time. With
        ``replace_lists=True`` a list field present in ``updates`` is SET to the
        given value instead, so the profile editor can edit/remove items (not
        only append) and a removal actually sticks."""
        _apply_update(self, updates, replace_lists=replace_lists)


@dataclass
class ChildProfile:
    """Per-child profile for personalization."""

    name: Optional[str] = None
    pronouns: Optional[str] = None
    age: Optional[float] = None
    grade_band: Optional[str] = None  # e.g., preschool, elementary, middle, high
    temperament: Optional[str] = None  # e.g., sensitive, high-energy, adaptable
    interests: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    academic_strengths: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    emotion_regulation: Optional[str] = None
    social_profile: Optional[str] = None
    learning_profile: Optional[str] = None  # e.g., visual, auditory, kinesthetic, EF notes
    neurodiversity: Optional[str] = None  # diagnosed/suspected
    sensory_notes: Optional[str] = None
    sleep_routine: Optional[str] = None
    health_notes: Optional[str] = None
    triggers: List[str] = field(default_factory=list)
    escalation_pattern: Optional[str] = None  # e.g., whining -> yelling -> screaming
    calming_strategies: List[str] = field(default_factory=list)
    recent_changes: List[str] = field(default_factory=list)
    school_context: Optional[str] = None  # e.g., Montessori/public, any notes
    teacher_notes: Optional[str] = None
    sibling_conflicts: List[str] = field(default_factory=list)
    repair_helpers: List[str] = field(default_factory=list)
    motivators: List[str] = field(default_factory=list)
    safety_flags: Optional[str] = None  # non-clinical concerns

    def apply_update(self, updates: Dict[str, Any], *, replace_lists: bool = False) -> None:
        """Merge partial updates into the child profile. See
        ``ParentProfile.apply_update`` for the ``replace_lists`` semantics."""
        _apply_update(self, updates, replace_lists=replace_lists)


@dataclass
class FamilyProfile:
    """Aggregate profile per user_id with one parent and many children."""

    parent: ParentProfile = field(default_factory=ParentProfile)
    children: Dict[str, ChildProfile] = field(default_factory=dict)

    def snapshot(self) -> Dict[str, Any]:
        """Return a serializable snapshot of the family profile."""
        return {
            "parent": asdict(self.parent),
            "children": {name: asdict(profile) for name, profile in self.children.items()},
        }


class ProfilingService:
    """
    In-memory profile store. Designed so a persistent backend can replace the storage later.
    """

    def __init__(self) -> None:
        self._profiles: Dict[str, FamilyProfile] = {}
        self._lock = Lock()

    def _get_or_create_family(self, user_id: str) -> FamilyProfile:
        with self._lock:
            if user_id not in self._profiles:
                self._profiles[user_id] = FamilyProfile()
            return self._profiles[user_id]

    def update_parent_profile(self, user_id: str, parent_updates: Dict[str, Any]) -> Dict[str, Any]:
        family = self._get_or_create_family(user_id)
        family.parent.apply_update(parent_updates)
        return family.snapshot()["parent"]

    def update_child_profile(
        self, user_id: str, child_name: str, child_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        family = self._get_or_create_family(user_id)
        if child_name not in family.children:
            family.children[child_name] = ChildProfile(name=child_name)
        family.children[child_name].apply_update(child_updates)
        return {child_name: asdict(family.children[child_name])}

    def replace_parent_profile(self, user_id: str, parent_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Like update_parent_profile but list fields are SET, not merged — used by
        the profile editor so edits/removals persist (see apply_update)."""
        family = self._get_or_create_family(user_id)
        family.parent.apply_update(parent_updates, replace_lists=True)
        return family.snapshot()["parent"]

    def replace_child_profile(
        self, user_id: str, child_name: str, child_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Editor-facing kid update (creates the kid if new; list fields SET)."""
        family = self._get_or_create_family(user_id)
        if child_name not in family.children:
            family.children[child_name] = ChildProfile(name=child_name)
        family.children[child_name].apply_update(child_updates, replace_lists=True)
        return {child_name: asdict(family.children[child_name])}

    def remove_child_profile(self, user_id: str, child_name: str) -> bool:
        """Editor-facing kid removal. Returns True if a child was removed. Used to
        delete a kid the parent added by mistake or a duplicate the coach created
        before it learned the real name."""
        family = self._get_or_create_family(user_id)
        existed = child_name in family.children
        family.children.pop(child_name, None)
        return existed

    def get_family_profile(self, user_id: str) -> Dict[str, Any]:
        family = self._get_or_create_family(user_id)
        return family.snapshot()

    def export_snapshot(self) -> Dict[str, Any]:
        """Return a serializable snapshot of all users' profiles."""
        with self._lock:
            return {user: profile.snapshot() for user, profile in self._profiles.items()}

    def load_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """Replace in-memory profiles with a loaded snapshot."""
        with self._lock:
            self._profiles = {}
            for user_id, family_data in snapshot.items():
                parent_data = family_data.get("parent", {})
                children_data = family_data.get("children", {})
                family = FamilyProfile()
                family.parent.apply_update(parent_data)
                for child_name, child_payload in children_data.items():
                    child_profile = ChildProfile(name=child_name)
                    child_profile.apply_update(child_payload)
                    family.children[child_name] = child_profile
                self._profiles[user_id] = family


# Single shared instance for app-wide use
profiling_service = ProfilingService()

