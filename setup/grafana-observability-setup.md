# Grafana Cloud Setup (Metrics + Dashboards + Alerts + Claude Code MCP)

How to turn on **metrics** for the backend. The code already exists
(`app/observability/init_otel` + `register_domain_metrics`, wired in
`app/server.py`) and is **gated on `OTEL_EXPORTER_OTLP_ENDPOINT`** — unset, it's a
no-op. We instrument with **OpenTelemetry** and **push over OTLP/HTTP** (Railway is
egress-only, so we push, never get scraped). OTel is vendor-neutral: this points at
Grafana Cloud, but switching backends later is just changing the endpoint + header.

What you get: HTTP request rate / p95 latency / error count automatically, plus
custom domain gauges — `research_run_failure_rate_ratio`, `research_run_max_queue_wait_seconds`,
`research_run_in_flight_ratio` — that read the durable run tables. Grafana then alerts on
these → Slack. And the **Grafana MCP** lets Claude Code query all of it read-only.

> **Status: metrics LIVE in prod (2026-06-27).** The three `OTEL_*` vars are set on
> Railway (endpoint `https://otlp-gateway-prod-us-west-0.grafana.net/otlp`); boot log
> shows `OpenTelemetry metrics → …` + `domain metrics registered`. Remaining optional:
> the read-only MCP token (§4) and dashboards/alerts (§5).

**Cost:** free tier (10k active series, 50GB logs/traces, 14-day retention, 3 users).
Hard-capped — never auto-bills. No credit card. Chosen over New Relic for PromQL,
per-signal budgets, 3 seats, and the best Claude-Code MCP story.

---

## 1. Create the free Grafana Cloud stack

Sign up at <https://grafana.com/auth/sign-up/create-user> → create a stack (the free
plan is the default). Your stack URL is `https://<org>.grafana.net`.

## 2. Get the OTLP endpoint + ingest token (the as-built wizard path)

Use the **OpenTelemetry setup** guided flow (Home → Getting started, or search
"OpenTelemetry"):

1. **Choose your infrastructure → `Serverless / Other`.** (NOT Kubernetes/Linux —
   those install a collector agent; we push OTLP directly from the app.)
2. **Choose your method → the OpenTelemetry SDK / OTLP (direct)** option.
3. **Instrumentation → "Use an API Token" → Create a new token.** Name it e.g.
   `mvp-backend-otlp`; leave the default scopes (`metrics:write, logs:write,
   traces:write, profiles:write, stacks:read`). Click **Create token**.
4. The **"Append the generated configuration"** box now shows exactly what we need
   (Grafana pre-encodes the space as `%20` for you):
   ```
   OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp-gateway-<region>.grafana.net/otlp"
   OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic%20<base64(instanceID:token)>"
   ```
   **Copy to clipboard.** (This is the *write/ingest* token — separate from the
   read-only MCP token in §4.)

> **Ignore the wizard's last "Finish setup / Application Observability" step.** It
> checks for **traces** ("could not find any traces yet") — we send **metrics only**,
> so that check stays empty *by design*; it is **not** a failure. Likewise ignore the
> separate **"Prometheus onboarding"** wizard — it's a redundant ingestion path; OTLP
> push is ours. **Verify in Explore (§6), not the wizards.**

## 3. Set the Railway env vars

Railway → `mvp-backend` → **Variables**:

| Variable | Value | Notes |
| --- | --- | --- |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `https://otlp-gateway-<region>.grafana.net/otlp` | the on-switch |
| `OTEL_EXPORTER_OTLP_HEADERS` | `Authorization=Basic%20<base64>` | paste exactly as the wizard gave it; if you ever hand-build it, the space after `Basic` **must** be `%20` (Python OTLP quirk) |
| `OTEL_SERVICE_NAME` | `mvp-backend` | stable name so restarts don't fragment the service |

On boot: `[observability] OpenTelemetry metrics → https://otlp-gateway-…` and
`[observability] domain metrics registered`. First export lands within ~60s.

> **Cardinality caution:** free tier caps at 10k active series. Our metrics are
> deliberately label-free (1 series each). If you add custom metrics later, **do not**
> label them with `user_id` / `run_id` / paths-with-IDs — that explodes series count.

## 4. Wire the Grafana MCP into Claude Code (read-only)

So Claude Code can query metrics/dashboards/alerts but **never mutate** them. This
needs a **separate, read-only token** (NOT the ingest token from §2):

1. Grafana → **Administration → Service accounts** → **Add service account**
   (role: **Viewer**) → **Add token** → copy it.
2. Install the binary + add it to Claude Code (as-built — `go` was already present):
   ```bash
   go install github.com/grafana/mcp-grafana/cmd/mcp-grafana@latest   # → ~/go/bin/mcp-grafana
   claude mcp add grafana \
     --env GRAFANA_URL=https://<org>.grafana.net \
     --env GRAFANA_SERVICE_ACCOUNT_TOKEN=<viewer token from step 1> \
     -- ~/go/bin/mcp-grafana --disable-write
   ```
   (`GRAFANA_URL` is the bare stack URL — strip any `/a/...` app path. `--disable-write`
   blocks all create/update/delete; the agent can only run PromQL, read dashboards,
   list alerts/incidents.)
3. **Restart Claude Code** — MCP tools load at session start, so a freshly-added
   server isn't usable until you restart (verify it's registered with `claude mcp list`
   → `grafana … ✔ Connected`).
4. Verify: ask Claude to "query `research_run_failure_rate_ratio` via the grafana MCP" —
   it returns data; a write attempt is refused.

## 5. Dashboard + Slack alerts

- **Dashboard:** new dashboard → panels for request rate, p95 latency, error rate,
  `research_run_failure_rate_ratio`, `research_run_max_queue_wait_seconds`, `research_run_in_flight_ratio`.
- **Alerts → Contact points:** add **Slack** (reuse the team webhook). Then
  **Alert rules:** e.g. `research_run_failure_rate_ratio > 0.3 for 15m`, or
  `research_run_max_queue_wait_seconds > 300` → notify Slack. (Grafana alerting
  replaces the need for a bespoke in-app watchdog.)

## 6. Verify in Explore (this is where the data actually shows)

Grafana → **Explore** → pick the Prometheus data source (`grafanacloud-<org>-prom`).
Type a metric name to autocomplete, switch the panel to **Time series**:

```promql
# total HTTP requests in the last 30 min
sum(increase(http_server_duration_milliseconds_count[30m]))

# requests/sec over the last 5 min (the graph that moves)
sum(rate(http_server_duration_milliseconds_count[5m]))

# by method + status (this OTel version does NOT populate http_route)
sum by (http_method, http_status_code) (increase(http_server_duration_milliseconds_count[30m]))

# our domain health gauges (note the _ratio suffix — see below)
research_run_failure_rate_ratio
research_run_in_flight_ratio
research_run_max_queue_wait_seconds
```

**As-built metric-name notes (verified live 2026-06-27):**
- The HTTP request metric is **`http_server_duration_milliseconds_count`** (this OTel
  version uses the older `http.server.duration` convention, not `..._request_duration_seconds`).
  Labels present: `http_method`, `http_status_code` (no `http_route`).
- The OTLP→Prometheus translation **appends `_ratio`** to gauges declared with
  `unit="1"` → `research_run_failure_rate_ratio`, `research_run_in_flight_ratio`. The
  seconds gauge stays `research_run_max_queue_wait_seconds`. All carry
  `service_name="mvp-backend"`.
- If a name doesn't autocomplete, use the Grafana MCP from Claude Code:
  `list_prometheus_metric_names(regex="research.*")` to see exact names.

To generate failure signal on demand: `tests/nl-harness/tools/load_and_chaos.py --conc 5`
(mock-backed, free).

---

**Switching backends later** (New Relic, SigNoz, self-hosted): change only
`OTEL_EXPORTER_OTLP_ENDPOINT` + `OTEL_EXPORTER_OTLP_HEADERS`. No code change — that's
the point of OpenTelemetry. (Dashboards/alerts get rebuilt per backend; the data
pipeline doesn't.)

**Want the trace-based APM / Application Observability view too?** That needs a
TracerProvider + OTLP span exporter added to `app/observability` (small change). The
FastAPI instrumentation already *creates* spans; they just need an exporter. Until
then, the wizard's trace check stays empty — expected.

---

## 7. Vertical-expansion dashboard + alerts (Phase 3.9, 2026-07-11)

The vertical expansion (plan `one-agent-five-doors`) added domain counters via
`app.observability.count()`. The MCP token stays read-only by design, so the
dashboard ships as code: **import `setup/grafana/vertical-expansion-dashboard.json`**
(Dashboards → New → Import → paste). Panels: hook errors, doors fail-open,
taxonomy escapes, rrule rejections, transition funnel by stage/vertical,
date-model mix, lookup-path spend split.

**Counter names** (OTLP→Prometheus appends `_total` to counters, dots→underscores;
verify post-deploy with `list_prometheus_metric_names(regex="cos_.*")`):
`cos_lifecycle_transition_total{to_stage, activity_type}` ·
`cos_lifecycle_hook_error_total{hook}` · `cos_doors_request_total{fail_open}` ·
`cos_dates_write_total{date_model}` · `cos_dates_rrule_rejected_total{edge}` ·
`cos_lookup_path_total{path}` · `cos_type_degraded_total`.

**Alert rules to add** (Alerting → Alert rules; reuse the Slack contact point):

1. **COS lifecycle hook errors** — the swallow-safe hooks fail INVISIBLY (users
   see nothing; to-dos/email-watching silently don't happen):
   `sum(increase(cos_lifecycle_hook_error_total[1h])) > 0`, pending 0m,
   no-data → OK (metric only exists after the first error).
2. **Doors failing open** — flag evaluation is down; everyone silently sees
   default doors: `sum(increase(cos_doors_request_total{fail_open="true"}[15m])) > 0`
   **for 15m**, no-data → OK.

Both: no-data must be OK, not Alerting — these series don't exist until the
first occurrence (that's the point).

**Watchlist SLO alerts (Phase 4 — add these too; the dashboard's "Watchlist
SLO" row visualizes the same signals).** Metric names (VERIFIED live
2026-07-11): Grafana Cloud's OTLP translator appends `_ratio` to unit-"1"
gauges — `watchlist_windows_watching_ratio`, `watchlist_windows_missed_ratio`
— while the seconds-unit gauge keeps its name:
`watchlist_seconds_since_last_tick`; counters get `_total`:
`watchlist_notifications_sent_total{kind, outcome}`,
`watchlist_windows_created_total{source, confidence}`; histogram:
`watchlist_notification_delay_seconds_bucket`.

3. **Watchlist missed a window** — the product promise broken (a window opened
   with no day-of notification): `max(watchlist_windows_missed_ratio) > 0`,
   pending 0m. **No-data → OK** (gauge registers only when OTel is on and the
   backend is up — a separate liveness concern).
4. **Watchlist worker stalled** — sweep heartbeat dead; notifications stop
   silently: `max(watchlist_seconds_since_last_tick) > 900` (3× the 300s
   poll), pending 5m, no-data → OK.

The GA gate from the plan is judged from this row + rules: watchlist beyond
pilot metros only after the miss-detector alert runs clean through one real
registration season.

**Post-deploy smoke (binding, from the plan's telemetry verification):** fire one
real action per instrument — track an activity with an rrule, open the doors
endpoint, run a `pytest tests/test_date_model.py` locally is NOT enough (OTel is
off in tests); use the live backend — then confirm each series appears:
`increase(cos_dates_write_total[1h]) > 0` etc. PostHog side: `activity_tracked`
now carries `activity_type` + `date_model`; new event `activity_stage_advanced`
{to_stage, activity_type} fires from every lifecycle transition.
