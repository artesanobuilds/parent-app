# Grafana Cloud Setup (Metrics + Dashboards + Alerts + Claude Code MCP)

How to turn on **metrics** for the backend. The code already exists
(`app/observability/init_otel` + `register_domain_metrics`, wired in
`app/server.py`) and is **gated on `OTEL_EXPORTER_OTLP_ENDPOINT`** — unset, it's a
no-op. We instrument with **OpenTelemetry** and **push over OTLP/HTTP** (Railway is
egress-only, so we push, never get scraped). OTel is vendor-neutral: this points at
Grafana Cloud, but switching backends later is just changing the endpoint + header.

What you get: HTTP request rate / p95 latency / error count automatically, plus
custom domain gauges — `research.run.failure_rate`, `research.run.max_queue_wait_seconds`,
`research.run.in_flight` — that read the durable run tables. Grafana then alerts on
these → Slack. And the **Grafana MCP** lets Claude Code query all of it read-only.

**Cost:** free tier (10k active series, 50GB logs/traces, 14-day retention, 3 users).
Hard-capped — it never auto-bills. No credit card. Chosen over New Relic for
PromQL, per-signal budgets, 3 seats, and the best Claude-Code MCP story.

---

## 1. Create the free Grafana Cloud stack

1. Sign up at <https://grafana.com/auth/sign-up/create-user> → create a stack
   (pick a region, e.g. `prod-us-east-0`). The free plan is the default.

## 2. Get the OTLP push endpoint + token

In the Grafana Cloud Portal → your stack → **OpenTelemetry** (or "OTLP") tile →
**Configure / Generate token**. It gives you, pre-built:
- an **endpoint** like `https://otlp-gateway-<region>.grafana.net/otlp`
- a **Basic auth header** = `Authorization=Basic <base64(instanceID:token)>`

Copy both. (The portal generates the base64 for you — don't hand-build it.)

## 3. Set the Railway env vars

Railway → `mvp-backend` → **Variables**:

| Variable | Value | Notes |
| --- | --- | --- |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `https://otlp-gateway-<region>.grafana.net/otlp` | the on-switch |
| `OTEL_EXPORTER_OTLP_HEADERS` | `Authorization=Basic%20<base64>` | **⚠ the space after `Basic` must be `%20`** (Python OTLP quirk) |
| `OTEL_SERVICE_NAME` | `mvp-backend` | stable name so restarts don't fragment the service |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` | optional; our exporter is HTTP already |

On boot you'll see `[observability] OpenTelemetry metrics → https://otlp-gateway-…`
and `[observability] domain metrics registered`.

> **Cardinality caution:** the free tier caps at 10k active series. Our metrics are
> deliberately label-free (1 series each). If you add custom metrics later, **do not**
> label them with `user_id` / `run_id` / paths-with-IDs — that explodes series count.

## 4. Wire the Grafana MCP into Claude Code (read-only)

So Claude Code can query metrics/dashboards/alerts but **never mutate** them:

1. Grafana → your stack → **Administration → Service accounts** → create one
   (Viewer role) → **Add token** → copy it.
2. Install the server + add it to Claude Code:
   ```bash
   # one-time: install the binary (Go) or use Docker — see github.com/grafana/mcp-grafana
   claude mcp add grafana -- mcp-grafana --disable-write
   ```
   with env on the MCP:
   ```
   GRAFANA_URL=https://<your-stack>.grafana.net
   GRAFANA_SERVICE_ACCOUNT_TOKEN=<token from step 1>
   ```
   `--disable-write` blocks all create/update/delete (dashboards, alerts) — the agent
   can run PromQL, read dashboards, list alerts/incidents, and that's it.
3. Verify: ask Claude "run a PromQL query for `research_run_failure_rate` via the
   grafana MCP" — it should return data; a write attempt should be refused.

## 5. Dashboard + Slack alerts

- **Explore** (Grafana → Explore, Prometheus data source): query
  `http_server_request_duration_seconds` (request latency) and
  `research_run_failure_rate` to confirm data is arriving.
- **Dashboard:** new dashboard → panels for request rate, p95 latency, error rate,
  `research_run_failure_rate`, `research_run_max_queue_wait_seconds`, `research_run_in_flight`.
- **Alerts → Contact points:** add **Slack** (reuse the team webhook). Then
  **Alert rules:** e.g. `research_run_failure_rate > 0.3 for 15m`, or
  `research_run_max_queue_wait_seconds > 300` → notify Slack. (Grafana alerting
  replaces the need for a bespoke in-app watchdog.)

## 6. Verify end-to-end

```bash
# generate failure/load signal through the mock backend (free):
tests/nl-harness/tools/load_and_chaos.py --conc 5
# then in Grafana Explore, research_run_failure_rate should move;
# lower an alert threshold briefly and confirm a Slack message fires.
```

---

**Switching backends later** (New Relic, SigNoz, self-hosted): change only
`OTEL_EXPORTER_OTLP_ENDPOINT` + `OTEL_EXPORTER_OTLP_HEADERS`. No code change — that's
the point of instrumenting with OpenTelemetry. (Dashboards/alerts get rebuilt per
backend; the data pipeline doesn't.)
