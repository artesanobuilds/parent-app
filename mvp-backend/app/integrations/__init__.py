"""Provider-agnostic email + calendar integrations (R5).

The agents and sync jobs code against the `EmailProvider` / `CalendarProvider`
interfaces in `base.py` and resolve concrete adapters via `registry.py` — they
never import a vendor SDK directly. v1 ships Google (Gmail + Google Calendar);
Microsoft 365 / iCloud become drop-in adapters later.
"""
