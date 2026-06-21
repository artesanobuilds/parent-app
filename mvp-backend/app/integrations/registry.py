"""Provider registry (R5).

Callers ask for a provider by name + the connected account's credentials and get
the right adapter — they never import a vendor module. v1 supports `google`.
"""
from __future__ import annotations

from typing import Any

from app.integrations.base import CalendarProvider, EmailProvider, OAuthCredentials

SUPPORTED_PROVIDERS = ("google",)


def get_email_provider(
    provider: str, credentials: OAuthCredentials, *, service: Any = None
) -> EmailProvider:
    if provider == "google":
        from app.integrations.google import GoogleEmailProvider

        return GoogleEmailProvider(credentials, service=service)
    raise ValueError(
        f"unsupported email provider {provider!r} (supported: {SUPPORTED_PROVIDERS})"
    )


def get_calendar_provider(
    provider: str, credentials: OAuthCredentials, *, service: Any = None
) -> CalendarProvider:
    if provider == "google":
        from app.integrations.google import GoogleCalendarProvider

        return GoogleCalendarProvider(credentials, service=service)
    raise ValueError(
        f"unsupported calendar provider {provider!r} (supported: {SUPPORTED_PROVIDERS})"
    )
