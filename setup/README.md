# Setup

External configuration / one-time setup guides for the parent app. Code lives in
the repo; these docs cover the accounts, credentials, and console steps needed to
make integrations live.

| Guide | What it covers |
| --- | --- |
| [auth-setup.md](auth-setup.md) | **Auth v2** — Sign in with Apple (portal + Xcode capability) + Google login, `AUTH_JWT_SECRET`, and the account-migration operator playbook (migration-status, link-legacy safety net, orphan cleanup, T2 retire) |
| [security-hardening-setup.md](security-hardening-setup.md) | **Security hardening** — admin cookie gate + `ADMIN_TOKEN` rotation, security headers/HSTS, rate limits, secrets scanning (gitleaks), data-subject deletion, and the planned at-rest encryption + security CI |
| [analytics-posthog-setup.md](analytics-posthog-setup.md) | **PostHog** analytics + flags + experiments — project + `$0` cap + 4 env vars, and the kids-data privacy posture (opaque IDs, event allowlist, PII denylist, no autocapture, person deletion) |
| [google-oauth-setup.md](google-oauth-setup.md) | Google Cloud OAuth client + Railway env for Gmail ingestion + Google Calendar sync |
| [voice-v2-elevenlabs-setup.md](voice-v2-elevenlabs-setup.md) | ElevenLabs ConvAI v2 console setup (kid + parent voice agents) |
| [sentry-setup.md](sentry-setup.md) | Sentry error tracking — create the project, set `SENTRY_DSN`, route alerts to Slack |
| [grafana-observability-setup.md](grafana-observability-setup.md) | Grafana Cloud metrics via OpenTelemetry (OTLP), dashboards + Slack alerts, and the `mcp-grafana` read-only Claude Code MCP |
| [ios-simulator-testing.md](ios-simulator-testing.md) | Claude Code autonomous iOS Simulator testing — AXe + ios-simulator-skill + idb install, accessibility-tree loop, permission allowlist, gotchas (team-shareable) |
| [apns-setup.md](apns-setup.md) | Crisis-lock push notifications — APNs `.p8` auth key, Xcode Push capability, the four `APNS_*` Railway vars, and the "TestFlight = production" gotcha |
