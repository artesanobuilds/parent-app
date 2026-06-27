# Sentry Setup (Error Tracking)

How to turn on **error tracking** for the backend. The code already exists
(`app/observability/init_sentry`, wired in `app/server.py`) and is **gated on the
`SENTRY_DSN` env var** — with it unset, nothing runs. This doc is the external
config to make it live.

Once on, Sentry auto-captures every unhandled FastAPI route exception **and** the
research / email / calendar worker failures (they call `logger.exception`, which
Sentry's logging integration turns into an issue with the full traceback). It's
errors-only by default (`traces_sample_rate=0`) so it stays on the free tier.

**Cost:** free **Developer** tier (~5K errors/mo, 1 user) is plenty for the closed
beta. No credit card needed. (See `docs/roadmap.md` → Pre-Launch Hardening.)

---

## 1. Create the project

1. Sign up / log in at <https://sentry.io>.
2. **Create Project** → Platform: **Python → FastAPI** → name it `mvp-backend`.
3. On the setup screen, copy the **DSN** (looks like
   `https://<hash>@o<org>.ingest.sentry.io/<project>`). That's the only secret you need —
   our code does the SDK init, so you can ignore Sentry's copy-paste snippet.

## 2. Set the Railway env vars

Railway → the `mvp-backend` service → **Variables**:

| Variable | Value | Required |
| --- | --- | --- |
| `SENTRY_DSN` | the DSN from step 1 | **yes** (this is the on-switch) |
| `SENTRY_ENVIRONMENT` | `production` | optional (default `production`) |
| `SENTRY_RELEASE` | e.g. a git SHA | optional (nice for "first seen in" tracking) |
| `SENTRY_TRACES_SAMPLE_RATE` | `0` | optional — raise (e.g. `0.1`) only if you want perf tracing |

Saving a variable triggers a redeploy. On boot you'll see
`[observability] Sentry initialized (env=production)` in the Railway logs.

## 3. (Recommended) Route alerts to Slack

In Sentry: **Settings → Integrations → Slack** → install, pick the channel. Then
**Alerts → Create Alert → Issues** → "a new issue is created" (and/or "an issue
is seen more than N times in 1h") → action: **Send a Slack notification**. Now a
crash pages the team in real time.

## 4. Verify

With `SENTRY_DSN` set in prod (or locally), force a failure and confirm it lands:

```bash
# easiest: use the fault harness to make a research run fail
tests/nl-harness/tools/run-fault-flows.sh -k outage
# or hit the running app in a way that raises, then check:
#   Sentry → Issues  → you should see the exception with its traceback,
#   tagged with the environment, and (for worker failures) the "[research] run … failed" message.
```

If nothing appears: confirm `SENTRY_DSN` is set on the service, the deploy picked
it up (look for the `[observability] Sentry initialized` log line), and the error
actually fired.

---

**Local note:** to test locally, `export SENTRY_DSN=…` before starting uvicorn.
Leave it unset and the app is unaffected (the suite runs with it unset).
