"""Google adapters: Gmail (EmailProvider) + Google Calendar (CalendarProvider).

This is the v1 concrete implementation behind the R5 interfaces. The Google SDKs
are imported lazily inside `_build_service` so the module loads without them and
tests can inject a fake service via `service=`.

NOTE: the live Gmail/Calendar calls are written against the documented API shapes
but are UNTESTED end-to-end pending the OAuth flow + Google verification (R3).
The request structure + response parsing are unit-tested with an injected fake.
"""
from __future__ import annotations

import base64
import logging
import re
from typing import Any, List, Optional

from app.integrations.base import (
    CalendarEvent,
    CalendarProvider,
    EmailProvider,
    IngestMessage,
    OAuthCredentials,
)

logger = logging.getLogger(__name__)

_URL_RE = re.compile(r"https?://[^\s<>\"')]+")


class _GoogleMixin:
    """Shared Google service construction (overridable for tests)."""

    api_name: str = ""
    api_version: str = ""

    def __init__(self, credentials: OAuthCredentials, *, service: Any = None) -> None:
        super().__init__(credentials)  # type: ignore[misc]
        self._injected_service = service

    def _service(self) -> Any:
        if self._injected_service is not None:
            return self._injected_service
        return self._build_service()

    def _build_service(self) -> Any:
        # Lazy: only needed for live calls; keeps the module importable + tests
        # SDK-free. Requires google-api-python-client + google-auth.
        from google.oauth2.credentials import Credentials  # type: ignore
        from googleapiclient.discovery import build  # type: ignore

        creds = self.credentials  # type: ignore[attr-defined]
        oauth = Credentials(
            token=None,
            refresh_token=creds.refresh_token,
            client_id=creds.client_id,
            client_secret=creds.client_secret,
            token_uri=creds.token_uri,
            scopes=creds.scopes,
        )
        return build(self.api_name, self.api_version, credentials=oauth, cache_discovery=False)


# ── Gmail ────────────────────────────────────────────────────────────────────

class GoogleEmailProvider(_GoogleMixin, EmailProvider):
    provider_name = "google"
    api_name = "gmail"
    api_version = "v1"

    def list_messages(
        self,
        *,
        query: Optional[str] = None,
        since: Optional[str] = None,
        max_results: int = 25,
    ) -> List[IngestMessage]:
        q_parts: List[str] = []
        if query:
            q_parts.append(query)
        if since:
            q_parts.append(f"after:{since.replace('-', '/')}")  # Gmail wants YYYY/MM/DD
        q = " ".join(q_parts) or None

        svc = self._service()
        resp = (
            svc.users().messages()
            .list(userId="me", q=q, maxResults=max_results)
            .execute()
        )
        out: List[IngestMessage] = []
        for ref in resp.get("messages", []) or []:
            mid = ref.get("id")
            if not mid:
                continue
            meta = (
                svc.users().messages()
                .get(userId="me", id=mid, format="metadata",
                     metadataHeaders=["From", "Subject", "Date"])
                .execute()
            )
            out.append(self._parse(meta, full=False))
        return out

    def fetch_message(self, message_id: str) -> IngestMessage:
        meta = (
            self._service().users().messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        return self._parse(meta, full=True)

    @staticmethod
    def _parse(msg: dict, *, full: bool) -> IngestMessage:
        payload = msg.get("payload", {}) or {}
        headers = {
            (h.get("name") or "").lower(): h.get("value")
            for h in payload.get("headers", []) or []
        }
        body_text = _extract_gmail_body(payload) if full else ""
        snippet = msg.get("snippet")
        text_for_links = body_text or snippet or ""
        return IngestMessage(
            id=msg.get("id", ""),
            sender=headers.get("from"),
            subject=headers.get("subject"),
            received_at=headers.get("date"),
            body_text=body_text,
            snippet=snippet,
            links=_URL_RE.findall(text_for_links),
            raw=msg,
        )


def _extract_gmail_body(payload: dict) -> str:
    """Walk a Gmail payload tree and concatenate decoded text/plain parts."""
    chunks: List[str] = []

    def walk(part: dict) -> None:
        mime = part.get("mimeType", "")
        body = part.get("body", {}) or {}
        data = body.get("data")
        if mime == "text/plain" and data:
            chunks.append(_b64url(data))
        for sub in part.get("parts", []) or []:
            walk(sub)
        # Fall back to the top-level body when there are no parts.
        if not part.get("parts") and mime != "text/plain" and data and not chunks:
            chunks.append(_b64url(data))

    walk(payload)
    return "\n".join(c for c in chunks if c).strip()


def _b64url(data: str) -> str:
    try:
        return base64.urlsafe_b64decode(data.encode("ascii")).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return ""


# ── Google Calendar ──────────────────────────────────────────────────────────

class GoogleCalendarProvider(_GoogleMixin, CalendarProvider):
    provider_name = "google"
    api_name = "calendar"
    api_version = "v3"
    calendar_id = "primary"

    def push_event(self, event: CalendarEvent) -> str:
        body = _to_gcal_body(event)
        svc = self._service()
        if event.provider_event_id:
            res = (
                svc.events()
                .update(calendarId=self.calendar_id, eventId=event.provider_event_id, body=body)
                .execute()
            )
        else:
            res = svc.events().insert(calendarId=self.calendar_id, body=body).execute()
        return res.get("id", "")

    def pull_events(
        self, *, since: Optional[str] = None, until: Optional[str] = None
    ) -> List[CalendarEvent]:
        params: dict = {
            "calendarId": self.calendar_id,
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": 250,
        }
        if since:
            params["timeMin"] = since
        if until:
            params["timeMax"] = until
        resp = self._service().events().list(**params).execute()
        return [_from_gcal_item(it) for it in (resp.get("items", []) or [])]

    def delete_event(self, provider_event_id: str) -> None:
        self._service().events().delete(
            calendarId=self.calendar_id, eventId=provider_event_id
        ).execute()


def _to_gcal_body(e: CalendarEvent) -> dict:
    def stamp(value: Optional[str]) -> dict:
        if not value:
            return {}
        return {"date": value} if e.all_day else {"dateTime": value}

    body: dict = {"summary": e.title}
    if e.location:
        body["location"] = e.location
    if e.description:
        body["description"] = e.description
    start = stamp(e.start)
    end = stamp(e.end or e.start)
    if start:
        body["start"] = start
    if end:
        body["end"] = end
    return body


def _from_gcal_item(item: dict) -> CalendarEvent:
    start = item.get("start", {}) or {}
    end = item.get("end", {}) or {}
    all_day = "date" in start
    return CalendarEvent(
        title=item.get("summary", "(no title)"),
        start=start.get("dateTime") or start.get("date"),
        end=end.get("dateTime") or end.get("date"),
        all_day=all_day,
        location=item.get("location"),
        description=item.get("description"),
        provider_event_id=item.get("id"),
    )
