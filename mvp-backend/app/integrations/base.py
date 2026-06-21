"""Provider interfaces + shared shapes for email/calendar integrations (R5).

Everything downstream (the daily email agent in R3, the calendar sync in R4)
codes against `EmailProvider` / `CalendarProvider` and the dataclasses here — so
adding Microsoft 365 / iCloud later is a new adapter, no agent changes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── Shared shapes ────────────────────────────────────────────────────────────

@dataclass
class OAuthCredentials:
    """Decrypted credentials handed to a provider to act on a connected account.

    `refresh_token` is the long-lived token (decrypted from
    `integration_accounts`); the adapter exchanges it for short-lived access
    tokens. client_id/secret/token_uri are the app's OAuth-client config.
    """

    refresh_token: str
    scopes: List[str] = field(default_factory=list)
    account_email: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    token_uri: str = "https://oauth2.googleapis.com/token"


@dataclass
class IngestMessage:
    """A normalized inbound email/message (what an EmailProvider returns)."""

    id: str
    sender: Optional[str] = None
    subject: Optional[str] = None
    received_at: Optional[str] = None  # ISO-8601
    body_text: str = ""
    snippet: Optional[str] = None
    links: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CalendarEvent:
    """A normalized calendar event, used for both push and pull."""

    title: str
    start: Optional[str] = None  # ISO-8601 (date or datetime)
    end: Optional[str] = None
    all_day: bool = False
    location: Optional[str] = None
    description: Optional[str] = None
    provider_event_id: Optional[str] = None  # the provider's id (set on pull/after push)
    kid_name: Optional[str] = None


# ── Interfaces ───────────────────────────────────────────────────────────────

class EmailProvider(ABC):
    """Read-only inbound email access for ingestion (gmail.readonly et al.)."""

    provider_name: str = "base"

    def __init__(self, credentials: OAuthCredentials) -> None:
        self.credentials = credentials

    @abstractmethod
    def list_messages(
        self,
        *,
        query: Optional[str] = None,
        since: Optional[str] = None,
        max_results: int = 25,
    ) -> List[IngestMessage]:
        """List recent messages matching `query` (provider query syntax) and/or
        received since `since` (ISO date). Returns lightweight headers+snippet;
        call `fetch_message` for the full body."""

    @abstractmethod
    def fetch_message(self, message_id: str) -> IngestMessage:
        """Fetch one message in full (body + links)."""


class CalendarProvider(ABC):
    """Two-way calendar access: push our entries out, pull external events in."""

    provider_name: str = "base"

    def __init__(self, credentials: OAuthCredentials) -> None:
        self.credentials = credentials

    @abstractmethod
    def push_event(self, event: CalendarEvent) -> str:
        """Create (or update if `event.provider_event_id` is set) an event on the
        parent's calendar. Returns the provider event id."""

    @abstractmethod
    def pull_events(
        self, *, since: Optional[str] = None, until: Optional[str] = None
    ) -> List[CalendarEvent]:
        """List events on the parent's calendar in the [since, until] window."""

    @abstractmethod
    def delete_event(self, provider_event_id: str) -> None:
        """Remove an event we previously pushed."""
