# Setup

External configuration / one-time setup guides for the parent app. Code lives in
the repo; these docs cover the accounts, credentials, and console steps needed to
make integrations live.

| Guide | What it covers |
| --- | --- |
| [google-oauth-setup.md](google-oauth-setup.md) | Google Cloud OAuth client + Railway env for Gmail ingestion + Google Calendar sync |
| [voice-v2-elevenlabs-setup.md](voice-v2-elevenlabs-setup.md) | ElevenLabs ConvAI v2 console setup (kid + parent voice agents) |
| [sentry-setup.md](sentry-setup.md) | Sentry error tracking — create the project, set `SENTRY_DSN`, route alerts to Slack |
| [grafana-observability-setup.md](grafana-observability-setup.md) | Grafana Cloud metrics via OpenTelemetry (OTLP), dashboards + Slack alerts, and the `mcp-grafana` read-only Claude Code MCP |
| [ios-simulator-testing.md](ios-simulator-testing.md) | Claude Code autonomous iOS Simulator testing — AXe + ios-simulator-skill + idb install, accessibility-tree loop, permission allowlist, gotchas (team-shareable) |
| [apns-setup.md](apns-setup.md) | Crisis-lock push notifications — APNs `.p8` auth key, Xcode Push capability, the four `APNS_*` Railway vars, and the "TestFlight = production" gotcha |
