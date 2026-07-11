"""
Observability: error tracking (Sentry) + metrics (OpenTelemetry → Grafana Cloud).

The "last mile" pre-launch layer (see `docs/roadmap.md` → Pre-Launch Hardening,
and the plan's "Last Mile — Observability" section). Everything here is **gated on
env vars** — with `SENTRY_DSN` / `OTEL_EXPORTER_OTLP_ENDPOINT` unset (local, tests,
CI) every function is a no-op and nothing is imported, so the app behaves exactly
as before. Setup guides: `setup/sentry-setup.md`, `setup/grafana-observability-setup.md`.

Wiring (in `app/server.py`):
    init_sentry()                       # after logging config, before the app
    init_otel(app)                      # after `app = FastAPI(...)`
    register_domain_metrics(storage)    # after storage exists
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_sentry_on = False
_otel_on = False


# ── Error tracking: Sentry ───────────────────────────────────────────────────

def init_sentry() -> bool:
    """Initialize Sentry if SENTRY_DSN is set. Captures unhandled FastAPI route
    exceptions (FastAPI/Starlette integrations) AND any logger.error/exception —
    so the research/email/calendar worker failure paths (which already call
    logger.exception) are captured with their traceback, no per-worker code.
    Errors-only by default (traces_sample_rate=0) to stay on the free tier."""
    global _sentry_on
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return False
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
    except Exception as exc:  # noqa: BLE001 — a misconfigured/missing dep must not crash boot
        logger.warning("[observability] SENTRY_DSN set but sentry-sdk unavailable: %s", exc)
        return False

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
            release=os.getenv("SENTRY_RELEASE") or None,
            # Errors only by default — tracing/perf is sampled in explicitly if wanted.
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0")),
            send_default_pii=False,
            integrations=[
                # INFO+ become breadcrumbs; ERROR+ become captured events (so
                # worker logger.exception → a Sentry issue with the traceback).
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("[observability] Sentry init failed: %s", exc)
        return False

    _sentry_on = True
    logger.info("[observability] Sentry initialized (env=%s)",
                os.getenv("SENTRY_ENVIRONMENT", "production"))
    return True


def capture_exception(exc: BaseException, **tags: Any) -> None:
    """Send an explicit exception to Sentry with string tags (e.g. feature=cos,
    tool=LookupAndSaveActivity, user=...). No-op when Sentry is off, so it's safe to
    call from anywhere (local/tests). Used by code paths that swallow an
    exception into a user-facing string but still want it tracked."""
    if not _sentry_on:
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in tags.items():
                if value is not None:
                    scope.set_tag(key, str(value))
            sentry_sdk.capture_exception(exc)
    except Exception:  # noqa: BLE001 — tracking must never break the caller
        pass


# ── Domain counters (vertical expansion Phase 3.9) ───────────────────────────
# One facade so call sites stay one-liners: count("cos.doors.request",
# fail_open=False). No-op when OTel is off (local/tests/CI), swallow-safe
# always — telemetry must never break the caller. Label discipline (BINDING,
# see the plan's telemetry section): ≤2 labels per metric, enum values only —
# bounded cardinality is what keeps Grafana Cloud usable/free.

_counters: dict = {}


def count(name: str, n: int = 1, **labels: Any) -> None:
    if not _otel_on:
        return
    try:
        from opentelemetry import metrics

        counter = _counters.get(name)
        if counter is None:
            counter = metrics.get_meter("mvp.domain").create_counter(name)
            _counters[name] = counter
        counter.add(n, {k: str(v) for k, v in labels.items() if v is not None})
    except Exception:  # noqa: BLE001 — telemetry must never break the caller
        pass


# ── Metrics: OpenTelemetry (OTLP push) → Grafana Cloud ───────────────────────

def init_otel(app: Any) -> bool:
    """Instrument FastAPI for metrics via OpenTelemetry if OTEL_EXPORTER_OTLP_ENDPOINT
    is set. OTLP/HTTP **push** (Railway is egress-only, so we push, never get
    scraped). Auto-emits request rate / duration / error count; custom domain
    gauges are added by register_domain_metrics(). The OTLP exporter reads
    OTEL_EXPORTER_OTLP_ENDPOINT/_HEADERS from the env."""
    global _otel_on
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return False
    try:
        from opentelemetry import metrics
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
    except Exception as exc:  # noqa: BLE001
        logger.warning("[observability] OTEL endpoint set but OpenTelemetry unavailable: %s", exc)
        return False

    try:
        resource = Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "mvp-backend")})
        interval = int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL_MS", "60000"))
        reader = PeriodicExportingMetricReader(OTLPMetricExporter(), export_interval_millis=interval)
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))
        FastAPIInstrumentor.instrument_app(app)  # HTTP server metrics (rate/duration/errors)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[observability] OpenTelemetry init failed: %s", exc)
        return False

    _otel_on = True
    logger.info("[observability] OpenTelemetry metrics → %s",
                os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))
    return True


def register_domain_metrics(storage: Any) -> bool:
    """Register observable gauges for the SRE-flagged degradation signals, computed
    from the durable run tables. OTel's exporter polls these callbacks each export
    interval — no separate watchdog thread needed. Grafana then alerts on them →
    Slack. Labels are intentionally NONE (keep cardinality at 1 series each)."""
    if not _otel_on:
        return False
    try:
        from opentelemetry import metrics
        from opentelemetry.metrics import Observation
    except Exception:  # noqa: BLE001
        return False

    meter = metrics.get_meter("mvp.domain")

    def _failure_rate(_options):
        try:
            h = storage.research_run_health(window_minutes=60)
            return [Observation(float(h.get("failure_rate", 0.0)))]
        except Exception:  # noqa: BLE001 — a metric must never break the export loop
            return []

    def _max_queue_wait(_options):
        try:
            h = storage.research_run_health(window_minutes=60)
            return [Observation(float(h.get("max_queue_wait_s", 0)))]
        except Exception:  # noqa: BLE001
            return []

    def _in_flight(_options):
        try:
            h = storage.research_run_health(window_minutes=60)
            return [Observation(int(h.get("in_flight", 0)))]
        except Exception:  # noqa: BLE001
            return []

    meter.create_observable_gauge(
        "research.run.failure_rate", callbacks=[_failure_rate], unit="1",
        description="Fraction of research runs that failed in the last 60 min",
    )
    meter.create_observable_gauge(
        "research.run.max_queue_wait_seconds", callbacks=[_max_queue_wait], unit="s",
        description="Worst queue wait (created→started) among research runs in the last 60 min",
    )
    meter.create_observable_gauge(
        "research.run.in_flight", callbacks=[_in_flight], unit="1",
        description="Research runs currently queued or running",
    )
    logger.info("[observability] domain metrics registered (research run health)")
    return True
