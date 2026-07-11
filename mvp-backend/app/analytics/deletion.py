"""Delete a person + their events from PostHog — wired into delete_family so the
consent screen's "delete my data" promise also purges product analytics.

No-op unless BOTH POSTHOG_PERSONAL_API_KEY and POSTHOG_PROJECT_ID are set (the
deletion API needs the personal key, not the project key). Best-effort: a
failure here must never block the family delete (the DB rows are already gone).
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def delete_person(analytics_id: str) -> None:
    """Best-effort delete of a PostHog person + their events by distinct_id."""
    personal_key = os.getenv("POSTHOG_PERSONAL_API_KEY")
    project_id = os.getenv("POSTHOG_PROJECT_ID")
    if not (personal_key and project_id and analytics_id):
        return
    host = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")
    try:
        import httpx
        headers = {"Authorization": f"Bearer {personal_key}"}
        # Find the person id for this distinct_id, then delete with events.
        r = httpx.get(
            f"{host}/api/projects/{project_id}/persons/",
            params={"distinct_id": analytics_id}, headers=headers, timeout=10,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        for person in results:
            pid = person.get("id")
            if pid is None:
                continue
            httpx.delete(
                f"{host}/api/projects/{project_id}/persons/{pid}/",
                params={"delete_events": "true"}, headers=headers, timeout=10,
            )
        logger.info("[analytics] deleted %d PostHog person(s) for a family delete", len(results))
    except Exception:
        logger.warning("[analytics] PostHog person deletion failed (non-fatal)", exc_info=True)
