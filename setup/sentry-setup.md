# Sentry Setup (Error Tracking)

How to turn on **error tracking** for the backend. The code already exists
(`app/observability/init_sentry`, wired in `app/server.py`) and is **gated on the
`SENTRY_DSN` env var** — with it unset, nothing runs. This doc is the external
config to make it live.

Once on, Sentry auto-captures every unhandled FastAPI route exception **and** the
research / email / calendar worker failures (they call `logger.exception`, which
Sentry's logging integration turns into an issue with the full traceback). It's
errors-only by default (`traces_sample_rate=0`) so it stays on the free tier.

> **Status: LIVE in prod (2026-06-27).** `SENTRY_DSN` is set on Railway; verified
> with a real production error via `/debug/sentry-test` (below). This doc is the
> as-built record + how to re-do it.

**Cost:** signup gives a 14-day Business trial that **auto-drops to the free
Developer plan** (no card, no expiry) — ~5K errors/mo, 30-day retention, **1 user**.
Plenty for the closed beta; the 1-user cap is the main limit.

---

## 1. Create the project

1. Sign up / log in at <https://sentry.io/signup/> (no credit card; you'll create
   an **org** during signup).
2. **Create Project** → Platform: **Python → FastAPI** → name it `mvp-backend`.
   (Ignore the install snippet it shows — our code already does the SDK init.)
3. Copy the **DSN** (`https://<key>@o<org>.ingest.us.sentry.io/<project>`). Find it
   later at **Settings → Projects → mvp-backend → Client Keys (DSN)**. The DSN is the
   only thing needed, and it's safe as config (submit-only — it can't read data).

## 2. Set the Railway env vars

Railway → the `mvp-backend` service → **Variables**:

| Variable | Value | Required |
| --- | --- | --- |
| `SENTRY_DSN` | the DSN from step 1 | **yes** (this is the on-switch) |
| `SENTRY_ENVIRONMENT` | `production` | optional (default `production`) |
| `SENTRY_RELEASE` | e.g. a git SHA | optional (nice for "first seen in" tracking) |
| `SENTRY_TRACES_SAMPLE_RATE` | `0` | optional — raise (e.g. `0.1`) only if you want perf tracing |

Saving a variable triggers a redeploy. On boot you'll see
`[observability] Sentry initialized (env=production)` in the Railway logs — that's
the confirmation it's active.

## 3. (Recommended) Route alerts to Slack

In Sentry: **Settings → Integrations → Slack** → install + authorize the workspace.
Then **Alerts → Create Alert → Issues** → trigger **"a new issue is created"**
(and/or "seen more than N times in 1h") → action: **Send a Slack notification** →
pick the channel.

> For a **private** Slack channel, invite the bot first: type `@Sentry` in that
> channel so it can post there.

## 4. Verify (the as-built way)

There's a permanent, admin-gated verification lever built into the backend:

```bash
# forces a REAL production exception through the live app → Sentry captures it
curl -i https://mvp-backend-production-8678.up.railway.app/debug/sentry-test \
  -H "X-Admin-Token: <ADMIN_TOKEN>"
# → HTTP 500, and a "RuntimeError: Deliberate Sentry verification error …" issue
#   appears in Sentry → Issues under environment=production, with full request context.
```

`GET /debug/sentry-test` is gated by `ADMIN_TOKEN` (returns 401 without it), so it
can't be abused. It's the standard "is Sentry alive?" check.

Alternatively, the fault harness forces a *worker* failure locally:
`tests/nl-harness/tools/run-fault-flows.sh -k outage` (needs `SENTRY_DSN` exported
on that backend).

If nothing appears: confirm `SENTRY_DSN` is set on the service, the deploy picked it
up (the `[observability] Sentry initialized` log line), and the error actually fired.

---

**Local note:** to test locally, `export SENTRY_DSN=…` before starting uvicorn.
Leave it unset and the app is unaffected (the test suite runs with it unset).
