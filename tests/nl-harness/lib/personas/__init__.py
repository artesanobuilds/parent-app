"""
Persona presets.

A persona is a dataclass + a factory function. The dataclass holds the auth
material (token, admin token, or PIN); the factory creates the server-side
state the preset implies (e.g. `existing_parent` runs through onboarding and
returns a Parent with consent + profile already seeded).

The flow test never instantiates a persona directly; pytest fixtures in
conftest.py resolve them per-test.
"""
from .new_parent import Parent, new_parent
from .existing_parent import existing_parent
from .kid_agent_parent import KidAgentParent, kid_agent_parent
from .admin import Admin, admin

__all__ = [
    "Parent",
    "new_parent",
    "existing_parent",
    "KidAgentParent",
    "kid_agent_parent",
    "Admin",
    "admin",
]
