# Grafana Cloud Setup (Metrics + Dashboards + Alerts + Claude Code MCP)

How to turn on **metrics** for the backend. The code already exists
(`app/observability/init_otel` + `register_domain_metrics`, wired in
`app/server.py`) and is **gated on `OTEL_EXPORTER_OTLP_ENDPOINT`** — unset, it's a
no-op. We instrument with **OpenTelemetry** and **push over OTLP/HTTP** (Railway is
egress-only, so we push, never get scraped). OTel is vendor-neutral: this points at
Grafana Cloud, but switching backends later is just changing the endpoint + header.

What you get: HTTP request rate / p95 latency / error count automatically, plus
custom domain gauges — `research_run_failure_rate`, `research_run_max_queue_wait_seconds`,
`research_run_in_flight` — that read the durable run tables. Grafana then alerts on
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
2. Add the server to Claude Code (install `mcp-grafana` first — see
   github.com/grafana/mcp-grafana):
   ```bash
   claude mcp add grafana -- mcp-grafana --disable-write
   ```
   with env on the MCP:
   ```
   GRAFANA_URL=https://<org>.grafana.net
   GRAFANA_SERVICE_ACCOUNT_TOKEN=<viewer token from step 1>
   ```
   `--disable-write` blocks all create/update/delete — the agent can only run PromQL,
   read dashboards, and list alerts/incidents.
3. Verify: ask Claude to "query `research_run_failure_rate` via the grafana MCP" — it
   returns data; a write attempt is refused.

## 5. Dashboard + Slack alerts

- **Dashboard:** new dashboard → panels for request rate, p95 latency, error rate,
  `research_run_failure_rate`, `research_run_max_queue_wait_seconds`, `research_run_in_flight`.
- **Alerts → Contact points:** add **Slack** (reuse the team webhook). Then
  **Alert rules:** e.g. `research_run_failure_rate > 0.3 for 15m`, or
  `research_run_max_queue_wait_seconds > 300` → notify Slack. (Grafana alerting
  replaces the need for a bespoke in-app watchdog.)

## 6. Verify in Explore (this is where the data actually shows)

Grafana → **Explore** → pick the Prometheus data source (`grafanacloud-<org>-prom`).
Type a metric name to autocomplete, switch the panel to **Time series**:

```promql
# total HTTP requests since the current deploy
sum(http_server_request_duration_seconds_count)

# requests/sec over the last 5 min (the graph that moves)
sum(rate(http_server_request_duration_seconds_count[5m]))

# by route + status
sum by (http_route, http_response_status_code) (http_server_request_duration_seconds_count)

# our domain health gauges
research_run_failure_rate
research_run_in_flight
```

(The exact HTTP metric name can vary by instrumentation version — type `http_` and
pick the `..._count` series the autocomplete shows.) To generate failure signal on
demand: `tests/nl-harness/tools/load_and_chaos.py --conc 5` (mock-backed, free).

---

**Switching backends later** (New Relic, SigNoz, self-hosted): change only
`OTEL_EXPORTER_OTLP_ENDPOINT` + `OTEL_EXPORTER_OTLP_HEADERS`. No code change — that's
the point of OpenTelemetry. (Dashboards/alerts get rebuilt per backend; the data
pipeline doesn't.)

**Want the trace-based APM / Application Observability view too?** That needs a
TracerProvider + OTLP span exporter added to `app/observability` (small change). The
FastAPI instrumentation already *creates* spans; they just need an exporter. Until
then, the wizard's trace check stays empty — expected.
