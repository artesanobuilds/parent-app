"""
existing-parent persona: a parent who has finished onboarding — has a token,
consent recorded, and a seeded profile with at least one child. The starting
state for any flow that should *not* be testing onboarding itself.
"""
from __future__ import annotations

from .new_parent import Parent, new_parent


def existing_parent(flow_ctx) -> Parent:
    """
    Build on new_parent: also submit consent + seed a minimal profile so the
    parent looks 'finished onboarding' to downstream endpoints.
    """
    parent = new_parent(flow_ctx)

    # Consent
    resp = flow_ctx.post(
        "/consent/submit",
        json={
            "parent_name": parent.display_name,
            "parent_email": "test@example.com",
            "kid_age_band": "6-8",
            "agreement_version": flow_ctx.consent_agreement_version,
        },
        as_=parent,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"existing_parent: /consent/submit returned {resp.status_code}: {resp.text}"
        )

    # Minimal profile seed
    resp = flow_ctx.post(
        "/profile/seed",
        json={
            "user_id": parent.user_id,
            "parent_name": parent.display_name,
            "kids": [
                {"name": "TestKid", "age": "7", "temperament": "curious",
                 "pronouns": "they/them", "grade_band": "elementary"},
            ],
        },
        as_=parent,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"existing_parent: /profile/seed returned {resp.status_code}: {resp.text}"
        )

    return parent
