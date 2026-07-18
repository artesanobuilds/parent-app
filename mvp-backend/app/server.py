import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Any, Optional

from fastapi import FastAPI, Request, Depends, Header, HTTPException, Query, Body
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from app.agent import get_agent
from app.onboarding_agent import get_onboarding_agent
from app.memory import MemoryRepository
from app.profiling import profiling_service, ParentProfile, ChildProfile
from app.duckdb_storage import DuckDBStorage
from app import content as content_service
from app import kid_agent as kid_agent_service
from app import moderation
from app import telemetry
from app import email_smtp
from app import summary as kid_summary
from app.auth import current_user, authorize_user_match, issue_token as auth_issue_token
from app.rate_limit import enforce as rate_limit_enforce
from app.cost_logging import CostLoggingCallbackHandler, new_workflow_id
from app.prompt_synthesis import _age_band as _kid_age_band, synthesize as kid_synthesize


# Closed-beta consent agreement version. Bump when terms change to force re-consent.
CONSENT_AGREEMENT_VERSION = os.getenv("CONSENT_AGREEMENT_VERSION", "closed-beta-v1-2026-05")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Quiet third-party debug logs unless explicitly enabled
verbose_external_logs = os.getenv("DEBUG_ALL_LOGS", "0").lower() in ("1", "true", "yes")
if not verbose_external_logs:
    for noisy in ("httpx", "httpcore", "openai", "urllib3", "langchain", "langgraph"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

# Error tracking (gated on SENTRY_DSN — no-op if unset). Init as early as possible
# so it wraps app creation + the workers. See app/observability + setup/sentry-setup.md.
from app.observability import init_sentry
init_sentry()
from app.push import init_push
init_push()
# Product analytics + feature flags (gated on POSTHOG_API_KEY — no-op if unset).
from app.analytics import init_analytics, capture as _analytics_capture
init_analytics()


def _track(event: str, user_id: str, props: dict | None = None) -> None:
    """Fire-and-forget product-analytics capture. Never lets an analytics error
    (or an unset PostHog) affect a user flow."""
    try:
        _analytics_capture(event, user_id, props or {})
    except Exception:
        pass

storage_backend = DuckDBStorage()
content_service.init(storage_backend)
chat_memory = MemoryRepository()
onboarding_memory = MemoryRepository()


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_persisted_state()
    # Activity-research background worker. Sweep any run a prior restart left
    # 'running' back to 'queued' (re-runs are idempotent), then start the daemon.
    try:
        storage_backend.requeue_stale_running_runs()
        from app.research.worker import init_worker
        init_worker(storage_backend).start()
    except Exception:
        logger.exception("[research] worker failed to start")
    # R3 daily Gmail-sync worker (same daemon idiom + a schedule tick).
    try:
        storage_backend.requeue_stale_email_sync_runs()
        from app.email_sync.worker import init_worker as init_email_sync_worker
        init_email_sync_worker(storage_backend).start()
    except Exception:
        logger.exception("[email-sync] worker failed to start")
    # R4 part 2: two-way Google Calendar sync worker (same daemon idiom).
    try:
        storage_backend.requeue_stale_calendar_sync_runs()
        from app.calendar_sync.worker import init_worker as init_calendar_sync_worker
        init_calendar_sync_worker(storage_backend).start()
    except Exception:
        logger.exception("[calendar-sync] worker failed to start")
    # Registration-window watchlist (Phase 4): catch-up sweep with due-time
    # semantics — any downtime is repaired within one poll of boot.
    try:
        from app.watchlist.worker import init_worker as init_watchlist_worker
        init_watchlist_worker(storage_backend).start()
    except Exception:
        logger.exception("[watchlist] worker failed to start")
    yield
    try:
        from app.research.worker import research_worker
        if research_worker is not None:
            research_worker.stop()
    except Exception:
        logger.exception("[research] worker failed to stop cleanly")
    try:
        from app.email_sync.worker import email_sync_worker
        if email_sync_worker is not None:
            email_sync_worker.stop()
    except Exception:
        logger.exception("[email-sync] worker failed to stop cleanly")
    try:
        from app.calendar_sync.worker import calendar_sync_worker
        if calendar_sync_worker is not None:
            calendar_sync_worker.stop()
    except Exception:
        logger.exception("[calendar-sync] worker failed to stop cleanly")
    try:
        from app.watchlist.worker import watchlist_worker
        if watchlist_worker is not None:
            watchlist_worker.stop()
    except Exception:
        logger.exception("[watchlist] worker failed to stop cleanly")
    persist_state()
    try:
        from app.analytics import shutdown as analytics_shutdown
        analytics_shutdown()   # flush queued events (no-op if disabled)
    except Exception:
        pass
    storage_backend.close()


app = FastAPI(title="MVP Backend", version="1.0.0", lifespan=lifespan)

# ConvAI: ElevenLabs Custom LLM endpoints (kid companion + parent coach)
from app.convai_endpoint import router as convai_router
app.include_router(convai_router)
from app.parent_convai_endpoint import router as parent_convai_router
app.include_router(parent_convai_router)
from app.research.router import router as research_router
app.include_router(research_router)
from app.cos.router import router as cos_router
app.include_router(cos_router)
from app.ingest.router import router as ingest_router
app.include_router(ingest_router)
from app.oauth.router import router as oauth_router
app.include_router(oauth_router)
from app.email_sync.router import router as email_sync_router
app.include_router(email_sync_router)
from app.calendar_sync.router import router as calendar_sync_router
app.include_router(calendar_sync_router)

# Metrics via OpenTelemetry → Grafana Cloud (gated on OTEL_EXPORTER_OTLP_ENDPOINT —
# no-op if unset). Instrument after the app + routers exist; register the domain
# gauges that read research-run health. See setup/grafana-observability-setup.md.
from app.observability import init_otel, register_domain_metrics, register_watchlist_metrics
if init_otel(app):
    register_domain_metrics(storage_backend)
    register_watchlist_metrics(storage_backend)

# Lock CORS to known origins. Env: ALLOWED_ORIGINS=https://a.com,https://b.com
# Default keeps localhost dev usable. iOS does not need CORS (not a browser).
_allowed_origins = [
    o.strip() for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8904,http://localhost:5173,http://127.0.0.1:8904",
    ).split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security response headers (nosniff/frame/referrer/permissions everywhere,
# HSTS behind ENABLE_HSTS, CSP on the served SPAs). See app/security_headers.py.
from app.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)


# When behind a trusted reverse proxy (Railway), request.client.host is the
# proxy IP, so per-IP rate limiting collapses to one shared bucket. Read the
# real client from X-Forwarded-For ONLY when TRUST_PROXY is enabled, else fall
# back to the socket peer. TRUST_PROXY must only be set when a proxy you control
# actually sets XFF, otherwise clients can spoof it.
_TRUST_PROXY = os.getenv("TRUST_PROXY", "0").lower() in ("1", "true", "yes")


def client_ip_for(http_request: Request) -> str:
    if _TRUST_PROXY:
        xff = http_request.headers.get("x-forwarded-for", "")
        first = xff.split(",")[0].strip()
        if first:
            return first
    return http_request.client.host if http_request.client else "unknown"


# Operator gate + CMS cookie-session endpoints live in app.admin_auth (shared
# with the email-sync/calendar-sync routers; accepts X-Admin-Token or cookie).
from app.admin_auth import require_admin_token, router as admin_auth_router
app.include_router(admin_auth_router)
# Phase 2 auth: native Apple/Google sign-in, refresh rotation, logout.
from app.auth_router import router as auth_router
app.include_router(auth_router)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_thread"
    user_id: str = "0"


class AuthIssueRequest(BaseModel):
    user_id: str  # closed-beta: clients claim a user_id; v1 upgrades to Apple Sign-In


class ConsentSubmitRequest(BaseModel):
    parent_name: Optional[str] = None
    parent_email: Optional[str] = None
    kid_age_band: Optional[str] = None
    agreement_version: str  # must match CONSENT_AGREEMENT_VERSION


LEGAL_SLUGS = ("privacy-policy", "terms")


class LegalAcceptRequest(BaseModel):
    # Client echoes the versions it displayed: {"privacy-policy": "1.0", ...}.
    # A mismatch with the current published version 409s so a stale client
    # re-fetches before recording acceptance of text the user never saw.
    versions: Dict[str, str]
    platform: Optional[str] = None


class LegalDraftRequest(BaseModel):
    title: str
    body_md: str


class LegalPublishRequest(BaseModel):
    version: str
    effective_date: Optional[str] = None
    requires_reacceptance: bool = False


class FeedbackRequest(BaseModel):
    message_id: str
    thread_id: str
    user_id: str
    feedback: str  # "thumbs_up", "thumbs_down", or "none"


class DebugReportRequest(BaseModel):
    """A test-user diagnostic bundle, posted from the iOS app's 'send debug
    data' affordance. All fields optional/best-effort — this endpoint must
    accept reports even when the user's auth/consent is broken (that's the
    bug class we most want to capture), so it is unauthenticated."""
    user_id: Optional[str] = None
    note: str = ""
    diagnostics: Dict[str, Any] = {}   # version, device, baseURL, consent, mic, ...
    logs: str = ""                     # recent client log buffer


class OnboardingSeedRequest(BaseModel):
    user_id: str
    parent_name: str
    kids: List[Dict[str, str]] = []      # [{"name", "age", "temperament", "pronouns", "grade_band"}]
    household: str = ""
    support_system: str = ""
    energy_pattern: str = ""
    dreaded_moment: str = ""
    challenges: List[str] = []
    goals: List[str] = []
    # Demographic additions
    postal_code: str = ""
    country: str = ""
    primary_language: str = ""
    parent_age_range: str = ""
    adults_in_household: Optional[int] = None
    cultural_background: str = ""
    employment: str = ""
    pronouns: str = ""


# ── CMS Pydantic models ──────────────────────────────────────────────

class ArticleCreateRequest(BaseModel):
    id: str
    category: str
    title: str
    subtitle: str = ""
    emoji: str = ""
    author: str = "MVP Editorial"
    read_time: str = ""
    summary: str = ""
    tags: List[str] = []
    content: str = ""


class ArticleUpdateRequest(BaseModel):
    category: str | None = None
    title: str | None = None
    subtitle: str | None = None
    emoji: str | None = None
    author: str | None = None
    read_time: str | None = None
    summary: str | None = None
    tags: List[str] | None = None
    content: str | None = None


class CommunityPostCreateRequest(BaseModel):
    id: str
    category: str
    initials: str = ""
    name: str = ""
    title: str = ""
    preview: str = ""
    user_id: str | None = None


class CommunityPostUpdateRequest(BaseModel):
    category: str | None = None
    initials: str | None = None
    name: str | None = None
    title: str | None = None
    preview: str | None = None
    user_id: str | None = None


class CategoryCreateRequest(BaseModel):
    id: str
    name: str
    emoji: str = ""
    description: str = ""
    parent_id: str | None = None


class CategoryUpdateRequest(BaseModel):
    name: str | None = None
    emoji: str | None = None
    description: str | None = None
    # parent_id is omitted-from-payload-vs-explicit-null sensitive: the route
    # strips keys with v is None before forwarding, so clearing the parent
    # requires a sentinel handled at the route layer (see /cms/categories PUT).
    parent_id: str | None = None


class UserPostCreateRequest(BaseModel):
    category: str
    title: str
    preview: str
    user_id: str
    author_name: str


class ReplyCreateRequest(BaseModel):
    user_id: str
    author_name: str
    body: str


def load_persisted_state():
    users = set(storage_backend.list_users())
    profile_snapshot: Dict[str, Any] = {}

    for user_id in users:
        chat_data = storage_backend.load_user_data(user_id, "chat_threads")
        if chat_data:
            chat_memory.load_user_snapshot(user_id, chat_data)

        onboarding_data = storage_backend.load_user_data(user_id, "onboarding_threads")
        if onboarding_data:
            onboarding_memory.load_user_snapshot(user_id, onboarding_data)

        profile_data = storage_backend.load_user_data(user_id, "profiles")
        if profile_data:
            profile_snapshot[user_id] = profile_data

    if profile_snapshot:
        profiling_service.load_snapshot(profile_snapshot)
        logger.debug(f"[storage] loaded profiles for users: {list(profile_snapshot.keys())}")

    logger.debug(f"[storage] loaded chat memory users: {chat_memory.user_ids()}")
    logger.debug(f"[storage] loaded onboarding memory users: {onboarding_memory.user_ids()}")


def persist_state(user_id: str | None = None):
    """Persist state. If user_id is given, only save that user. Otherwise save all."""
    if user_id:
        user_ids = {user_id}
    else:
        user_ids = set(chat_memory.user_ids()) | set(onboarding_memory.user_ids())
        # Include profile-only users
        user_ids |= set(profiling_service.export_snapshot().keys())

    for uid in user_ids:
        storage_backend.save_user_data(uid, "chat_threads", chat_memory.snapshot_user(uid))
        storage_backend.save_user_data(uid, "onboarding_threads", onboarding_memory.snapshot_user(uid))

    # Persist profiles for targeted users
    all_profiles = profiling_service.export_snapshot()
    for uid in user_ids:
        if uid in all_profiles:
            storage_backend.save_user_data(uid, "profiles", all_profiles[uid])

    storage_backend.export_parquet()
    logger.debug(f"[storage] persisted state for users: {list(user_ids)}")


async def generate_stream(message: str, thread_id: str, user_id: str) -> AsyncGenerator[str, None]:
    """
    Streams events from the LangGraph agent.
    Format: SSE (Server-Sent Events)
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"[chat] start user_id={user_id} thread_id={thread_id} message={message[:200]}")
    agent = get_agent(user_id)
    # Memory is scoped per user + thread to isolate conversations by user
    memory_key = f"{user_id}:{thread_id}"
    # Cost: one coach turn = one workflow; session groups the whole thread.
    cost_cb = CostLoggingCallbackHandler(
        feature="coach", workflow=new_workflow_id(), session=thread_id, user=user_id
    )
    config = {"configurable": {"thread_id": memory_key}, "callbacks": [cost_cb]}

    thread_messages = chat_memory.get_thread_messages(user_id, thread_id)
    thread_messages.append({"role": "user", "content": message})
    assistant_buffer = ""
    
    try:
        # Stream events from the graph
        # "values" mode streams the full state at each step
        # "updates" mode streams only the changes
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            version="v1"
        ):
            # We are interested in chat model stream events to stream tokens back to client
            kind = event["event"]
            
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    # Format as SSE data
                    assistant_buffer += content
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            
            elif kind == "on_tool_start":
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"[chat] tool_start name={event.get('name')} input={event.get('data', {}).get('input')}")
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': event['name']})}\n\n"
                 
            elif kind == "on_tool_end":
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"[chat] tool_end name={event.get('name')} output={event.get('data', {}).get('output')}")
                yield f"data: {json.dumps({'type': 'tool_end', 'tool': event['name']})}\n\n"

        yield "data: [DONE]\n\n"
        if assistant_buffer:
            thread_messages.append({"role": "assistant", "content": assistant_buffer})
        persist_state(user_id)

    except Exception as e:
        logger.error(f"Error in stream: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


async def generate_onboarding_stream(message: str, thread_id: str, user_id: str) -> AsyncGenerator[str, None]:
    """
    Streams events from the onboarding agent.
    Format: SSE (Server-Sent Events)
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"[onboarding] start user_id={user_id} thread_id={thread_id} message={message[:200]}")
    agent = get_onboarding_agent(user_id)
    memory_key = f"onboarding:{user_id}:{thread_id}"
    cost_cb = CostLoggingCallbackHandler(
        feature="onboarding", workflow=new_workflow_id(), session=thread_id, user=user_id
    )
    config = {"configurable": {"thread_id": memory_key}, "callbacks": [cost_cb]}

    thread_messages = onboarding_memory.get_thread_messages(user_id, thread_id)
    thread_messages.append({"role": "user", "content": message})
    assistant_buffer = ""

    try:
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            version="v1"
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    assistant_buffer += content
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            elif kind == "on_tool_start":
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"[onboarding] tool_start name={event.get('name')} input={event.get('data', {}).get('input')}")
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': event['name']})}\n\n"
            elif kind == "on_tool_end":
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"[onboarding] tool_end name={event.get('name')} output={event.get('data', {}).get('output')}")
                yield f"data: {json.dumps({'type': 'tool_end', 'tool': event['name']})}\n\n"

        yield "data: [DONE]\n\n"
        if assistant_buffer:
            thread_messages.append({"role": "assistant", "content": assistant_buffer})
        persist_state(user_id)

    except Exception as e:
        logger.error(f"Error in onboarding stream: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

# ── Auth (closed-beta opaque tokens) ─────────────────────────────────

@app.post("/auth/issue-token")
def auth_issue_token_endpoint(request: AuthIssueRequest, http_request: Request):
    """
    LEGACY closed-beta token issuance. Being retired by the Phase 2 auth
    migration (native Apple/Google sign-in via /auth/login):

    - Disabled entirely once AUTH_ISSUE_TOKEN_ENABLED=0 (returns 410 Gone) —
      the T2 rollout step after every family has claimed their account.
    - Refuses a user_id that has ALREADY claimed a real identity (403): once a
      family signs in, nobody can mint a legacy token for their name again.
      This closes the "guess a parent's name → mint their token" hole
      family-by-family as sign-in adoption progresses.

    Rate-limited per source IP.
    """
    if os.getenv("AUTH_ISSUE_TOKEN_ENABLED", "1").lower() not in ("1", "true", "yes"):
        raise HTTPException(status_code=410, detail="legacy token issuance retired; sign in instead")
    rate_limit_enforce(client_ip_for(http_request), "auth")
    if storage_backend.user_has_any_identity(request.user_id):
        raise HTTPException(
            status_code=403,
            detail="this account has sign-in enabled; use Sign in with Apple/Google",
        )
    token = auth_issue_token(request.user_id)
    return {"token": token, "user_id": request.user_id}


# ── Push notifications ───────────────────────────────────────────────

class PushRegisterRequest(BaseModel):
    user_id: str
    device_token: str
    platform: str = "ios"


@app.post("/push/register-device")
def push_register_device(req: PushRegisterRequest, user_id: str = Depends(current_user)):
    """Register the caller's APNs device token so crisis-lock pushes can reach
    them. Idempotent. A no-op registration is harmless when APNs is unconfigured."""
    authorize_user_match(authenticated=user_id, claimed=req.user_id)
    token = req.device_token.strip()
    if token:
        storage_backend.save_push_token(user_id=req.user_id, token=token, platform=req.platform)
    return {"ok": True}


def _dispatch_crisis_push(user_id: str, kid_name: str, agent_id: str) -> Optional[str]:
    """Fire the crisis-lock push to the parent (no-op when APNs is unconfigured)
    and return an ISO timestamp to record in `parent_notified_at` when we actually
    dispatched one. Fire-and-forget; never raises."""
    from app import push
    if not push.is_enabled():
        return None
    try:
        push.send_crisis_push(
            storage=storage_backend, user_id=user_id, kid_name=kid_name, agent_id=agent_id
        )
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    except Exception:  # noqa: BLE001 — notification must never break crisis handling
        return None


# ── Public scoped share view (Phase 3b) ──────────────────────────────

@app.get("/share/{token}")
def share_view(token: str):
    """Public, no-login, read-only view of a family's plan, scoped by the share
    token (nanny → logistics; therapist → therapy; full → everything). Renders a
    minimal HTML page so a link is directly usable by someone without the app."""
    from fastapi.responses import HTMLResponse
    from app.cos import planning as _planning

    info = storage_backend.lookup_share_token(token)
    if info is None:
        return HTMLResponse(_share_html("This link is invalid or has expired.", []), status_code=404)

    uid, scope = info["user_id"], info["scope"]
    calendar = storage_backend.list_calendar_entries(uid)
    logistics = storage_backend.list_logistics_assignments(uid)
    caregivers = storage_backend.list_caregivers(uid)
    recurring = storage_backend.list_recurring_appointments(uid)
    tracked = storage_backend.list_tracked_activities(uid)
    cg = {c.get("id"): c.get("name") for c in caregivers}

    sections: List[tuple] = []
    if scope in ("full", "logistics"):
        sections.append(("Schedule", ["Week", "Kid", "Activity", "When", "Where"], [
            [e.get("week_start"), e.get("kid_name"), e.get("title"),
             " – ".join(x for x in [e.get("start_ts"), e.get("end_ts")] if x) or "",
             e.get("location_text")]
            for e in sorted(calendar, key=lambda x: (x.get("week_start") or ""))
            if scope == "full" or e.get("kind") in ("camp", "class", "program", "appointment")
        ]))
        sections.append(("Coverage", ["Week", "Kid", "Task", "Who", "Status"], [
            [l.get("week_start"), l.get("kid_name"), l.get("task"),
             cg.get(l.get("caregiver_id")) or ("— GAP —" if l.get("status") == "gap" else ""),
             l.get("status")]
            for l in sorted(logistics, key=lambda x: (x.get("week_start") or ""))
        ]))
    if scope in ("full", "therapy"):
        sections.append(("Therapy & appointments", ["Kid", "Title", "Provider", "Weekday", "Time"], [
            [r.get("kid_name"), r.get("title"), r.get("provider_name"),
             ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][r["weekday"]] if isinstance(r.get("weekday"), int) and 0 <= r["weekday"] < 7 else r.get("weekday"),
             " – ".join(x for x in [r.get("start_time"), r.get("end_time")] if x)]
            for r in recurring
        ]))
        sections.append(("Therapy sessions", ["Week", "Kid", "Title", "When"], [
            [e.get("week_start"), e.get("kid_name"), e.get("title"),
             " – ".join(x for x in [e.get("start_ts"), e.get("end_ts")] if x)]
            for e in calendar if e.get("kind") in ("therapy", "appointment")
        ]))
    if scope == "full":
        sections.append(("Activities", ["Kid", "Activity", "Status", "Provider"], [
            [a.get("kid_name"), a.get("name"), a.get("status"), a.get("provider")] for a in tracked
        ]))

    title = {"logistics": "Family schedule & coverage", "therapy": "Therapy schedule"}.get(scope, "Family plan")
    return HTMLResponse(_share_html(title, sections))


def _share_html(title: str, sections: List[Any]) -> str:
    import html
    def esc(v: Any) -> str:
        return html.escape("" if v is None else str(v))
    body = [
        "<!doctype html><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        f"<title>{esc(title)}</title>",
        "<style>body{font-family:-apple-system,system-ui,sans-serif;background:#F3F0EB;color:#1A1A1A;",
        "margin:0;padding:24px;max-width:900px;margin:auto}h1{font-size:22px}h2{font-size:16px;color:#4F5D3A;",
        "margin-top:28px}table{border-collapse:collapse;width:100%;background:#fff;border-radius:10px;overflow:hidden}",
        "th{background:#4F5D3A;color:#fff;text-align:left;padding:8px 10px;font-size:13px}",
        "td{padding:8px 10px;border-top:1px solid #eee;font-size:14px}",
        ".gap{color:#A03A3A;font-weight:600}.muted{color:#6F6A60;font-size:13px}</style>",
        f"<h1>{esc(title)}</h1><p class='muted'>Read-only. Shared from the MVP parenting app.</p>",
    ]
    for name, headers, rows in sections:
        body.append(f"<h2>{esc(name)}</h2>")
        if not rows:
            body.append("<p class='muted'>Nothing here yet.</p>"); continue
        body.append("<table><tr>" + "".join(f"<th>{esc(h)}</th>" for h in headers) + "</tr>")
        for r in rows:
            cells = "".join(
                f"<td class='{'gap' if str(c)=='— GAP —' else ''}'>{esc(c)}</td>" for c in r
            )
            body.append(f"<tr>{cells}</tr>")
        body.append("</table>")
    return "".join(body)


# ── Consent ──────────────────────────────────────────────────────────

@app.post("/consent/submit")
def consent_submit(req: ConsentSubmitRequest, request: Request,
                   user_id: str = Depends(current_user)):
    if req.agreement_version != CONSENT_AGREEMENT_VERSION:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content={
                "error": "agreement_version_mismatch",
                "required_version": CONSENT_AGREEMENT_VERSION,
            },
        )
    saved = storage_backend.record_consent(
        user_id=user_id,
        parent_name=req.parent_name,
        parent_email=req.parent_email,
        kid_age_band=req.kid_age_band,
        agreement_version=req.agreement_version,
        ip_address=(request.client.host if request.client else None),
        user_agent=request.headers.get("user-agent"),
    )
    return saved


@app.get("/consent/status")
def consent_status(user_id: str = Depends(current_user)):
    latest = storage_backend.latest_consent(user_id)
    accepted = bool(latest and latest.get("agreement_version") == CONSENT_AGREEMENT_VERSION)
    return {
        "accepted": accepted,
        "latest_version": CONSENT_AGREEMENT_VERSION,
        "accepted_version": latest.get("agreement_version") if latest else None,
        "accepted_at": latest.get("accepted_at") if latest else None,
    }


def _require_consent(user_id: str) -> None:
    """Raise 403 if user has not accepted the current consent agreement."""
    latest = storage_backend.latest_consent(user_id)
    if not latest or latest.get("agreement_version") != CONSENT_AGREEMENT_VERSION:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403,
            detail={
                "error": "consent_required",
                "required_version": CONSENT_AGREEMENT_VERSION,
            },
        )


# ── Legal documents (versioned; CMS-published; NOT the kid-consent gate) ──
#
# Deliberately separate from consent_records/_require_consent: latest_consent
# is kind-blind, so legal rows there would silently satisfy the kid-companion
# gate. The required version is the is_current published row — no env var —
# so a CMS publish (no deploy) can require re-acceptance.

@app.get("/content/legal")
def list_legal_docs():
    """Public: the current published legal docs (metadata, no body)."""
    docs = storage_backend.get_current_legal_docs()
    return {
        "documents": [
            {k: d[k] for k in ("slug", "title", "version", "effective_date", "published_at")}
            for d in docs
        ]
    }


@app.get("/content/legal/{slug}")
def get_legal_doc(slug: str):
    """Public: the current published version of one legal doc, incl. body."""
    doc = storage_backend.get_legal_doc(slug)
    if not doc:
        raise HTTPException(status_code=404, detail="Unknown legal document")
    return doc


@app.get("/legal/status")
def legal_status(user_id: str = Depends(current_user)):
    """Per-doc acceptance state for the signed-in parent. `accepted` is true
    when the latest acceptance matches the current version OR the current
    version doesn't require re-acceptance (typo-fix publishes don't nag)."""
    docs = storage_backend.get_current_legal_docs()
    out, needs = [], []
    for doc in docs:
        latest = storage_backend.latest_legal_acceptance(user_id, doc["slug"])
        accepted = bool(latest) and (
            latest["version"] == doc["version"] or not doc["requires_reacceptance"]
        )
        if not accepted:
            needs.append(doc["slug"])
        out.append({
            "slug": doc["slug"],
            "title": doc["title"],
            "required_version": doc["version"],
            "requires_reacceptance": doc["requires_reacceptance"],
            "accepted_version": latest["version"] if latest else None,
            "accepted_at": latest["accepted_at"] if latest else None,
            "accepted": accepted,
        })
    return {"documents": out, "accepted_all": not needs, "needs": needs}


@app.post("/legal/accept")
def legal_accept(req: LegalAcceptRequest, request: Request,
                 user_id: str = Depends(current_user)):
    """Record acceptance of the CURRENT versions. The client echoes the
    versions it showed; a stale echo 409s so it re-fetches /legal/status."""
    current = {d["slug"]: d for d in storage_backend.get_current_legal_docs()}
    to_record = []
    for slug, version in req.versions.items():
        doc = current.get(slug)
        if not doc:
            raise HTTPException(status_code=400, detail=f"Unknown legal document: {slug}")
        if version != doc["version"]:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=409,
                content={
                    "error": "version_mismatch",
                    "required": {s: d["version"] for s, d in current.items()},
                },
            )
        to_record.append({"document_id": doc["id"], "slug": slug, "version": version})
    if not to_record:
        raise HTTPException(status_code=400, detail="No documents to accept")
    saved = storage_backend.record_legal_acceptance(
        user_id=user_id,
        docs=to_record,
        ip_address=(request.client.host if request.client else None),
        user_agent=request.headers.get("user-agent"),
        platform=req.platform,
    )
    return {"ok": True, "accepted": saved}


@app.get("/cms/legal")
def cms_legal_overview(_: None = Depends(require_admin_token)):
    overview = []
    for slug in LEGAL_SLUGS:
        current = storage_backend.get_legal_doc(slug)
        draft = storage_backend.get_legal_draft(slug)
        overview.append({
            "slug": slug,
            "current": current,
            "draft": draft,
            "version_count": len(storage_backend.list_legal_versions(slug)),
        })
    return {"documents": overview}


@app.get("/cms/legal/{slug}/versions")
def cms_legal_versions(slug: str, _: None = Depends(require_admin_token)):
    return {"versions": storage_backend.list_legal_versions(slug)}


@app.get("/cms/legal/{slug}/draft")
def cms_legal_get_draft(slug: str, _: None = Depends(require_admin_token)):
    draft = storage_backend.get_legal_draft(slug)
    if not draft:
        raise HTTPException(status_code=404, detail="No draft")
    return draft


@app.put("/cms/legal/{slug}/draft")
def cms_legal_put_draft(slug: str, req: LegalDraftRequest,
                        _: None = Depends(require_admin_token)):
    if slug not in LEGAL_SLUGS:
        raise HTTPException(status_code=400, detail="Unknown legal slug")
    return storage_backend.upsert_legal_draft(slug, title=req.title, body_md=req.body_md)


@app.delete("/cms/legal/{slug}/draft")
def cms_legal_delete_draft(slug: str, _: None = Depends(require_admin_token)):
    return {"deleted": storage_backend.delete_legal_draft(slug)}


@app.post("/cms/legal/{slug}/publish")
def cms_legal_publish(slug: str, req: LegalPublishRequest,
                      _: None = Depends(require_admin_token)):
    if slug not in LEGAL_SLUGS:
        raise HTTPException(status_code=400, detail="Unknown legal slug")
    try:
        return storage_backend.publish_legal_draft(
            slug, version=req.version, effective_date=req.effective_date,
            requires_reacceptance=req.requires_reacceptance,
        )
    except ValueError as exc:
        if str(exc) == "no_draft":
            raise HTTPException(status_code=409, detail="No draft to publish")
        if str(exc) == "duplicate_version":
            raise HTTPException(status_code=409,
                                detail=f"Version {req.version} already published for {slug}")
        raise


# ── Debug reports (test-user diagnostics → email) ───────────────────

def _format_debug_email(req: "DebugReportRequest", server_notes: List[str]) -> str:
    """Render the diagnostic bundle as a readable plaintext email body."""
    lines: List[str] = []
    lines.append(f"user_id: {req.user_id or '(none)'}")
    lines.append("")
    lines.append("NOTE FROM USER:")
    lines.append(req.note.strip() or "(none)")
    if server_notes:
        lines.append("")
        lines.append("SERVER ENRICHMENT:")
        lines.extend(f"  {n}" for n in server_notes)
    if req.diagnostics:
        lines.append("")
        lines.append("CLIENT DIAGNOSTICS:")
        for k, v in req.diagnostics.items():
            lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append("RECENT CLIENT LOGS:")
    lines.append(req.logs.strip() or "(none)")
    return "\n".join(lines)


@app.post("/debug/report")
async def debug_report(req: DebugReportRequest, http_request: Request):
    """
    Receive a test-user diagnostic bundle and email it to the developer.

    Deliberately unauthenticated (the failures worth capturing include auth /
    consent breakage), so it is rate-limited per source IP. Enriches the bundle
    with server-side consent state — that line alone makes the common
    'consent_required masquerading as a connection error' bug obvious.
    """
    rate_limit_enforce(client_ip_for(http_request), "debug")

    server_notes: List[str] = []
    if req.user_id:
        try:
            latest = storage_backend.latest_consent(req.user_id)
            if latest and latest.get("agreement_version") == CONSENT_AGREEMENT_VERSION:
                server_notes.append(f"consent: OK ({CONSENT_AGREEMENT_VERSION})")
            elif latest:
                server_notes.append(
                    f"consent: STALE (has {latest.get('agreement_version')}, "
                    f"need {CONSENT_AGREEMENT_VERSION})"
                )
            else:
                server_notes.append(f"consent: NONE at {CONSENT_AGREEMENT_VERSION}")
        except Exception as e:  # noqa: BLE001
            server_notes.append(f"consent: lookup failed ({e})")

    note_head = (req.note.strip().splitlines() or [""])[0][:80]
    subject = f"[MVP debug] {req.user_id or 'anon'} — {note_head or 'no note'}"
    body = _format_debug_email(req, server_notes)

    # Always log the full bundle so reports are retrievable via `railway logs`
    # even when no email/Slack delivery is configured. Filter with:
    #   railway logs --filter "[debug-report]"
    logger.info("[debug-report] %s\n%s", subject, body)

    from starlette.concurrency import run_in_threadpool
    sent = await run_in_threadpool(email_smtp.send_email, subject, body)
    return {"ok": True, "emailed": sent}


# ── Chat / onboarding (parent-facing, auth required) ────────────────

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=request.user_id)
    rate_limit_enforce(user_id, "chat")
    _track("parent_chat_message_sent", user_id, {"thread_kind": "coach"})
    return StreamingResponse(
        generate_stream(request.message, request.thread_id, request.user_id),
        media_type="text/event-stream"
    )


@app.post("/onboarding-chat")
async def onboarding_chat_endpoint(request: ChatRequest, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=request.user_id)
    rate_limit_enforce(user_id, "chat")
    return StreamingResponse(
        generate_onboarding_stream(request.message, request.thread_id, request.user_id),
        media_type="text/event-stream"
    )


@app.get("/memory/{user_id}")
def dump_memory(user_id: str, authenticated_user: str = Depends(current_user)):
    """
    Returns all conversation threads for a given user_id from in-memory storage.
    Includes both coaching (/chat) and onboarding (/onboarding-chat) memories.
    """
    authorize_user_match(authenticated=authenticated_user, claimed=user_id)
    return {
        "user_id": user_id,
        "chat_threads": chat_memory.snapshot_user(user_id),
        "onboarding_threads": onboarding_memory.snapshot_user(user_id),
        "profile": profiling_service.get_family_profile(user_id),
    }

@app.get("/content/categories")
def list_categories():
    """Return all content categories."""
    return content_service.get_categories()


@app.get("/content/articles")
def list_articles(category: str | None = None, tag: str | None = None, limit: int = 50):
    """Return library articles, optionally filtered by category and/or tag.

    `tag` matches against the article's `tags` array (case-sensitive exact
    slug match). When both are provided, the filters are AND'd. Unknown tag
    returns an empty list with 200.
    """
    return content_service.get_articles(category=category, tag=tag, limit=limit)


@app.get("/content/articles/{article_id}")
def get_article(article_id: str):
    """Return a single article with full content."""
    article = content_service.get_article(article_id)
    if article is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Article not found"})
    return article


@app.post("/content/community/new")
def create_user_community_post(req: UserPostCreateRequest, user_id: str = Depends(current_user)):
    """Create a community post from the mobile app. Authenticated: an
    unauthenticated write with a caller-chosen user_id/author_name is an
    impersonation + spam vector (found by tests/test_bola_sweep.py's class
    of audit; iOS has always sent the bearer token here)."""
    authorize_user_match(authenticated=user_id, claimed=req.user_id)
    import uuid
    words = req.author_name.strip().split()
    initials = "".join(w[0].upper() for w in words[:2]) if words else "?"
    post_id = f"cp-{uuid.uuid4().hex[:12]}"
    data = {
        "id": post_id,
        "category": req.category,
        "title": req.title,
        "preview": req.preview,
        "user_id": req.user_id,
        "name": req.author_name,
        "initials": initials,
    }
    return content_service.create_community_post(data)


@app.get("/content/community/{post_id}")
def get_community_post_detail(post_id: str):
    """Get a single community post with its replies."""
    post = content_service.get_community_post(post_id)
    if post is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Post not found"})
    replies = content_service.get_replies_for_post(post_id)
    post["replies"] = replies
    post["reply_count"] = len(replies)
    return post


@app.get("/content/community/{post_id}/replies")
def get_post_replies(post_id: str, limit: int = 100):
    """Get replies for a community post."""
    return content_service.get_replies_for_post(post_id, limit=limit)


@app.post("/content/community/{post_id}/replies")
def create_post_reply(post_id: str, req: ReplyCreateRequest, user_id: str = Depends(current_user)):
    """Create a reply on a community post. Authenticated — see
    create_user_community_post."""
    authorize_user_match(authenticated=user_id, claimed=req.user_id)
    post = content_service.get_community_post(post_id)
    if post is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Post not found"})
    import uuid
    words = req.author_name.strip().split()
    initials = "".join(w[0].upper() for w in words[:2]) if words else "?"
    data = {
        "id": str(uuid.uuid4()),
        "post_id": post_id,
        "user_id": req.user_id,
        "author_name": req.author_name,
        "initials": initials,
        "body": req.body,
    }
    return content_service.create_reply(data)


@app.get("/content/community")
def list_community_posts(category: str | None = None, limit: int = 50):
    """Return community posts, optionally filtered by category."""
    return content_service.get_community_posts(category=category, limit=limit)


@app.get("/content/search")
def search_content(q: str, limit: int = 10):
    """Search articles and community posts by keyword."""
    return content_service.search_content(q, limit=limit)


@app.get("/content/relevant")
def relevant_content(topic: str, limit: int = 5):
    """Return content relevant to a topic (for contextual recommendations)."""
    return content_service.get_relevant_content(topic, limit=limit)


@app.get("/profile")
def get_profile(user_id: str = Depends(current_user)):
    """Return the family profile (parent + kids) for the authenticated user, so
    surfaces like the Settings → Profile screen can prefill an edit form.
    Avatar keys are turned into FRESHLY presigned URLs at read time — the key
    is stored, never a URL (a stored URL bakes in an expiry and leaks a
    capability into the parquet snapshots)."""
    family = profiling_service.get_family_profile(user_id) or {"parent": {}, "children": {}}
    from app import blobs
    if blobs.is_configured():
        parent = family.get("parent") or {}
        if parent.get("avatar_key"):
            parent["avatar_url"] = blobs.presign_get(parent["avatar_key"])
        for kid in (family.get("children") or {}).values():
            if kid.get("avatar_key"):
                kid["avatar_url"] = blobs.presign_get(kid["avatar_key"])
    return family


# ── Blob storage (profile photos; Railway Storage Buckets) ───────────

class BlobUploadUrlRequest(BaseModel):
    kind: str                      # avatar (ingest reserved for later)
    content_type: str
    byte_size: int


class AvatarAttachRequest(BaseModel):
    key: str


@app.post("/blobs/upload-url")
def blob_upload_url(req: BlobUploadUrlRequest, user_id: str = Depends(current_user)):
    """Mint a presigned PUT. The key is SERVER-derived from the authenticated
    user — a client-supplied key would be a cross-family write primitive."""
    from app import blobs
    if not blobs.is_configured():
        raise HTTPException(status_code=503, detail="blob storage is not configured")
    if req.kind not in ("avatar",):
        raise HTTPException(status_code=400, detail="unsupported blob kind")
    if req.content_type not in blobs.ALLOWED_IMAGE_MIME:
        raise HTTPException(status_code=400, detail="unsupported image type")
    if not (0 < req.byte_size <= blobs.MAX_IMAGE_BYTES):
        raise HTTPException(status_code=400, detail="image too large (8 MB max)")
    key = blobs.new_key(user_id=user_id, kind=req.kind, content_type=req.content_type)
    url = blobs.presign_put(key, req.content_type)
    return {"key": key, "url": url, "expires_in_s": int(os.getenv("BLOB_PRESIGN_TTL_S", "900"))}


def _attach_avatar(user_id: str, key: str, *, kid_name: Optional[str]) -> Dict[str, Any]:
    from app import blobs
    if not blobs.is_configured():
        raise HTTPException(status_code=503, detail="blob storage is not configured")
    # Ownership boundary: the key's u/{user_id}/ prefix must be the caller's.
    if not blobs.key_belongs_to(key, user_id):
        raise HTTPException(status_code=403, detail="key does not belong to this account")
    if blobs.head(key) is None:
        raise HTTPException(status_code=404, detail="no uploaded object at that key")
    family = profiling_service.get_family_profile(user_id)
    if kid_name is not None:
        # Attach must not CREATE a kid (update_child_profile would) — a typo'd
        # name minting a ghost kid is the name-as-key trap.
        if kid_name not in (family.get("children") or {}):
            raise HTTPException(status_code=404, detail="unknown kid")
        old = (family["children"][kid_name] or {}).get("avatar_key")
        profiling_service.update_child_profile(user_id, kid_name, {"avatar_key": key})
    else:
        old = (family.get("parent") or {}).get("avatar_key")
        profiling_service.update_parent_profile(user_id, {"avatar_key": key})
    persist_state(user_id)
    # Replacing a photo deletes the old object — no orphan accumulation.
    if old and old != key:
        blobs.delete(old)
    return get_profile(user_id)


@app.post("/profile/avatar")
def attach_parent_avatar(req: AvatarAttachRequest, user_id: str = Depends(current_user)):
    return _attach_avatar(user_id, req.key, kid_name=None)


@app.post("/profile/kids/{kid_name}/avatar")
def attach_kid_avatar(kid_name: str, req: AvatarAttachRequest,
                      user_id: str = Depends(current_user)):
    return _attach_avatar(user_id, req.key, kid_name=kid_name)


@app.post("/profile/seed")
def seed_profile(request: OnboardingSeedRequest, user_id: str = Depends(current_user)):
    """
    Receive structured onboarding data from the mobile app and seed
    the parent + child profiles so the coaching agent has context.
    """
    authorize_user_match(authenticated=user_id, claimed=request.user_id)
    # Seed parent profile
    parent_updates: Dict[str, Any] = {"name": request.parent_name}
    if request.challenges:
        parent_updates["stressors"] = request.challenges
    if request.goals:
        parent_updates["goals"] = request.goals
    if request.household:
        parent_updates["household_structure"] = request.household
    if request.support_system:
        parent_updates["support_system"] = request.support_system
    if request.energy_pattern:
        parent_updates["energy_pattern"] = request.energy_pattern
    if request.dreaded_moment:
        parent_updates["dreaded_moment"] = request.dreaded_moment
    if request.postal_code:
        parent_updates["postal_code"] = request.postal_code
    if request.country:
        parent_updates["country"] = request.country
    if request.primary_language:
        parent_updates["primary_language"] = request.primary_language
    if request.parent_age_range:
        parent_updates["parent_age_range"] = request.parent_age_range
    if request.adults_in_household is not None:
        parent_updates["adults_in_household"] = request.adults_in_household
    if request.cultural_background:
        parent_updates["cultural_background"] = request.cultural_background
    if request.employment:
        parent_updates["employment"] = request.employment
    if request.pronouns:
        parent_updates["pronouns"] = request.pronouns

    profiling_service.update_parent_profile(request.user_id, parent_updates)

    # Seed child profiles
    for kid in request.kids:
        child_name = kid.get("name", "").strip()
        if not child_name:
            continue
        child_updates: Dict[str, Any] = {"name": child_name}
        age_str = kid.get("age", "").strip()
        if age_str:
            try:
                child_updates["age"] = float(age_str)
            except ValueError:
                pass
        temperament = kid.get("temperament", "").strip()
        if temperament:
            child_updates["temperament"] = temperament
        pronouns = kid.get("pronouns", "").strip()
        if pronouns:
            child_updates["pronouns"] = pronouns
        grade_band = kid.get("grade_band", "").strip()
        if grade_band:
            child_updates["grade_band"] = grade_band
        profiling_service.update_child_profile(request.user_id, child_name, child_updates)

    # Persist immediately so nothing is lost if server restarts
    persist_state(request.user_id)

    logger.info(f"[profile/seed] seeded profile for user_id={request.user_id}")
    try:
        from app.analytics import capture as _capture
        _capture("onboarding_completed", request.user_id, {"kid_count": len(request.kids)})
    except Exception:
        pass
    return profiling_service.get_family_profile(request.user_id)


# ── Profile editor write path (PATCH) ────────────────────────────────
# The full ~35 parent + ~23 kid fields are already stored + returned by GET
# /profile; these let the iOS/web profile editor WRITE them (the seed endpoint
# only whitelists a subset and merges lists). List fields use replace semantics
# so the editor can edit/remove items, not only append.

from dataclasses import fields as _dc_fields

# The PATCH whitelists are auto-derived from the dataclasses — avatar_key must
# be subtracted or it becomes client-writable and one family can PATCH in
# another family's key and presign their kid's photo. Only the dedicated
# avatar endpoints (which verify key ownership) may set it.
_PARENT_FIELDS = {f.name for f in _dc_fields(ParentProfile)} - {"avatar_key"}
_CHILD_FIELDS = {f.name for f in _dc_fields(ChildProfile)} - {"avatar_key"}
_INT_FIELDS = {"adults_in_household"}
_FLOAT_FIELDS = {"age"}


def _coerce_profile_value(key: str, value: Any) -> Any:
    """Light type coercion so JSON strings land as the right scalar type."""
    if value is None:
        return None
    try:
        if key in _INT_FIELDS:
            return int(value)
        if key in _FLOAT_FIELDS:
            return float(value)
    except (TypeError, ValueError):
        return value
    return value


def _validated_updates(payload: Dict[str, Any], allowed: set) -> Dict[str, Any]:
    """Keep only known profile keys (drop junk / control keys) + coerce types."""
    return {
        k: _coerce_profile_value(k, v)
        for k, v in payload.items()
        if k in allowed
    }


@app.patch("/profile")
def patch_profile(
    payload: Dict[str, Any] = Body(default={}),
    user_id: str = Depends(current_user),
):
    """Partial-update the authenticated user's PARENT profile. Body is any subset
    of ParentProfile fields (unknown keys ignored); list fields are replaced."""
    claimed = payload.pop("user_id", None)
    if claimed is not None:
        authorize_user_match(authenticated=user_id, claimed=claimed)
    updates = _validated_updates(payload, _PARENT_FIELDS)
    profiling_service.replace_parent_profile(user_id, updates)
    persist_state(user_id)
    return profiling_service.get_family_profile(user_id)


@app.patch("/profile/kids/{kid_name}")
def patch_kid(
    kid_name: str,
    payload: Dict[str, Any] = Body(default={}),
    user_id: str = Depends(current_user),
):
    """Partial-update (or CREATE if new — covers add-a-kid) a child profile. Body
    is any subset of ChildProfile fields; list fields are replaced."""
    claimed = payload.pop("user_id", None)
    if claimed is not None:
        authorize_user_match(authenticated=user_id, claimed=claimed)
    updates = _validated_updates(payload, _CHILD_FIELDS)
    profiling_service.replace_child_profile(user_id, kid_name, updates)
    persist_state(user_id)
    return profiling_service.get_family_profile(user_id)


@app.delete("/profile/kids/{kid_name}")
def delete_kid(
    kid_name: str,
    user_id: str = Depends(current_user),
):
    """Remove a child profile (a mistakenly-added kid, or a duplicate the coach
    created before it learned the real name). Scoped to the authenticated user.
    Also cascades the kid's agent data (config/messages/credentials/etc.) so the
    delete is complete — otherwise an orphan kid-agent lingers and can resurface
    the kid."""
    # The kid's photo goes with the kid — dropping only the JSON reference
    # would leave an orphan object holding the most sensitive data type.
    _family = profiling_service.get_family_profile(user_id)
    _avatar = ((_family.get("children") or {}).get(kid_name) or {}).get("avatar_key")
    if _avatar:
        from app import blobs
        blobs.delete(_avatar)
    profiling_service.remove_child_profile(user_id, kid_name)
    try:
        storage_backend.delete_kid_data(user_id=user_id, kid_name=kid_name)
    except Exception:  # noqa: BLE001 — profile removal already succeeded; cleanup is best-effort
        logger.exception("[profile/kids] kid-agent cleanup failed for %s/%s", user_id, kid_name)
    persist_state(user_id)
    return profiling_service.get_family_profile(user_id)


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest, user_id: str = Depends(current_user)):
    """
    Store thumbs-up/down feedback for an assistant message.
    Persisted inside the user's chat_threads data keyed by message_id.
    """
    authorize_user_match(authenticated=user_id, claimed=req.user_id)
    # Load existing feedback store (or create one)
    feedback_data = storage_backend.load_user_data(req.user_id, "feedback") or {}
    if req.feedback == "none":
        feedback_data.pop(req.message_id, None)
    else:
        feedback_data[req.message_id] = {
            "thread_id": req.thread_id,
            "feedback": req.feedback,
        }
    storage_backend.save_user_data(req.user_id, "feedback", feedback_data)
    logger.info(f"[feedback] user={req.user_id} message={req.message_id} feedback={req.feedback}")
    return {"ok": True}


# ── Family Companion (kid agent + handoff) ───────────────────────────

class KidAgentConfigRequest(BaseModel):
    user_id: str
    kid_name: str
    brief: str = ""                       # parent's free-text letter
    expected_version: Optional[int] = None  # optimistic concurrency
    enable: bool = False                  # set True from "Introduce them"


class KidChatRequest(BaseModel):
    user_id: str
    kid_name: str
    message: str
    thread_id: str = "default"
    kid_pin: Optional[str] = None  # selection convenience; not auth boundary


class KidPinRequest(BaseModel):
    user_id: str
    kid_name: str
    pin: str  # 4 digits, parent-set


def _verify_kid_pin(user_id: str, kid_name: str, pin: Optional[str]) -> bool:
    """
    Default-closed PIN check (H-2). The truth table:
      - no PIN configured for this kid  -> allow (selection convenience)
      - PIN configured, none supplied   -> DENY (was: silently allowed)
      - PIN configured, supplied        -> bcrypt verify

    The parent session is still the primary auth boundary; this prevents one
    child on a shared device from opening another child's companion once a
    parent has set a PIN.
    """
    pin_hash = storage_backend.get_kid_pin_hash(user_id, kid_name)
    if pin_hash is None:
        return True  # no PIN configured — allow
    if pin is None:
        return False  # PIN required but not supplied
    try:
        import bcrypt
        return bcrypt.checkpw(pin.encode("utf-8"), pin_hash.encode("utf-8"))
    except Exception as exc:
        logger.error(f"[kid_auth] bcrypt check failed: {exc}")
        return False


@app.post("/kid-agent/config")
def kid_agent_upsert(req: KidAgentConfigRequest, user_id: str = Depends(current_user)):
    """Re-synthesize and persist a new KidAgentConfig version."""
    authorize_user_match(authenticated=user_id, claimed=req.user_id)
    _require_consent(user_id)
    rate_limit_enforce(user_id, "config")
    try:
        config = kid_agent_service.upsert_kid_agent_config(
            user_id=req.user_id,
            kid_name=req.kid_name,
            brief=req.brief,
            expected_version=req.expected_version,
            enable=req.enable,
        )
        # Activation milestone: first version = a companion was just created.
        if (config or {}).get("version") == 1:
            _track("companion_created", user_id)
        return config
    except ValueError as exc:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=409, content={"error": str(exc)})


@app.get("/kid-agent/config")
def kid_agent_get(user_id: str, kid_name: str, authenticated_user: str = Depends(current_user)):
    """Fetch the latest config for a kid. Triggers auto-gen on first read."""
    authorize_user_match(authenticated=authenticated_user, claimed=user_id)
    _require_consent(user_id)
    config = storage_backend.get_kid_agent_config(user_id, kid_name)
    if config is None:
        # Lazy bootstrap so the parent's first review screen has something to show.
        _, config = kid_agent_service.get_kid_agent(user_id, kid_name)
    return config


@app.get("/kid-agent/list")
def kid_agent_list(user_id: str, authenticated_user: str = Depends(current_user)):
    """List all kid agents for this parent user."""
    authorize_user_match(authenticated=authenticated_user, claimed=user_id)
    _require_consent(user_id)
    return {"agents": storage_backend.list_kid_agents(user_id)}


class KidAgentPreviewRequest(BaseModel):
    user_id: str
    kid_name: str
    brief: str = ""


@app.post("/kid-agent/preview")
def kid_agent_preview(req: KidAgentPreviewRequest, user_id: str = Depends(current_user)):
    """
    Synthesize without saving. Returns the would-be invariants + summary +
    3-message preview so the iOS letter editor can render live regenerations
    without persisting drafts.
    """
    authorize_user_match(authenticated=user_id, claimed=req.user_id)
    _require_consent(user_id)
    rate_limit_enforce(user_id, "config")

    family = profiling_service.get_family_profile(req.user_id)
    children = family.get("children") or {}
    kid_profile = children.get(req.kid_name) or {"name": req.kid_name}
    parent_summary = family.get("parent")
    prior = storage_backend.get_kid_agent_config(req.user_id, req.kid_name)

    result = kid_synthesize(
        brief=req.brief,
        kid_profile=kid_profile,
        parent_profile_summary=parent_summary,
        prior_config=prior,
    )

    # 3-message preview: synthetic kid prompt run through a draft agent.
    # We do NOT instantiate a full LangGraph agent here (heavy + cached).
    # The preview is "what the agent would say to a generic opener" — fast,
    # cheap, and stable across edits. iOS shows this under the letter.
    preview_messages = _generate_preview_messages(
        kid_profile=kid_profile,
        invariants=result.invariants,
        system_prompt=result.system_prompt,
    )

    return {
        "invariants": result.invariants,
        "summary": result.summary,
        "content_hash": result.content_hash,
        "system_prompt_excerpt": result.system_prompt[:600] + "…",
        "preview_messages": preview_messages,
    }


def _generate_preview_messages(*, kid_profile, invariants, system_prompt) -> list:
    """
    Three short opener replies the agent would produce, used by the letter
    editor as live preview. Uses a single LLM call with a compact prompt to
    keep latency low. Falls back to template lines on error.
    """
    from langchain_openai import ChatOpenAI
    name = kid_profile.get("name") or "there"
    display_name = invariants.get("agent_display_name") or "Friend"
    try:
        llm = ChatOpenAI(model=os.getenv("KID_PREVIEW_MODEL", "gpt-5.2"), temperature=0.4)
        prompt = (
            f"You are roleplaying as the kid agent '{display_name}'. Below is the system "
            f"prompt that will run you in production. Generate THREE short example "
            f"opening lines (1-2 sentences each) the kid '{name}' might see when they "
            f"first open you. The lines should reflect the personality and respect every "
            f"non-negotiable rule. Output ONLY the three lines, one per line, no numbering.\n\n"
            f"=== SYSTEM PROMPT ===\n{system_prompt[:3500]}\n=== END ===\n"
        )
        from app.cost_logging import cost_config
        out = llm.invoke(prompt, config=cost_config("kid_preview")).content
        lines = [ln.strip() for ln in out.splitlines() if ln.strip()][:3]
        if len(lines) == 3:
            return lines
    except Exception as exc:
        logger.warning(f"[preview] generation failed: {exc}")
    return [
        f"Hi {name}! I'm {display_name}. What's on your mind today?",
        "Hmm, that's a good one. Want to think about it together?",
        "I heard your grown-up wants me to help with stuff like that.",
    ]


@app.post("/kid-auth/set-pin")
def kid_set_pin(req: KidPinRequest, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=req.user_id)
    if not (req.pin.isdigit() and 3 <= len(req.pin) <= 8):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400, content={"error": "PIN must be 3-8 digits"}
        )
    import bcrypt
    pin_hash = bcrypt.hashpw(req.pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    storage_backend.set_kid_pin(req.user_id, req.kid_name, pin_hash)
    return {"ok": True}


async def generate_kid_stream(
    user_id: str,
    kid_name: str,
    thread_id: str,
    message: str,
) -> AsyncGenerator[str, None]:
    """
    Streams the kid agent response with moderation gates.

    Pipeline per turn:
      1. Pre-input moderation -> on flag, log event, emit soft redirect (or crisis), return.
      2. Append user message to kid_messages.
      3. Stream tokens through StreamingModerator (chunk-buffered).
      4. On output flag, emit replacement_message + log event.
      5. On stream end, append assistant message; log moderation event if any.
    """
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"[kid_chat] start user={user_id} kid={kid_name} msg={message[:120]}")

    # Look up config (lazy-bootstraps a default if none exists).
    agent, config = kid_agent_service.get_kid_agent(user_id, kid_name)
    if not config.get("enabled"):
        yield f"data: {json.dumps({'type': 'error', 'content': 'agent not yet enabled by parent'})}\n\n"
        yield "data: [DONE]\n\n"
        return

    agent_id = config["id"]
    invariants = config["invariants"]

    # Crisis lock check — survives restarts, unlike the in-process kill set.
    # If a previous turn tripped a crisis pattern, the agent is frozen until a
    # parent calls /kid-agent/{agent_id}/revive.
    lock = storage_backend.is_kid_agent_crisis_locked(agent_id)
    if lock is not None:
        frozen_msg = (
            "Your grown-up needs to check in with you before we can chat again. "
            "I told them — they'll come find you."
        )
        yield f"data: {json.dumps({'type': 'token', 'content': frozen_msg})}\n\n"
        yield f"data: {json.dumps({'type': 'frozen', 'content': lock['category']})}\n\n"
        yield "data: [DONE]\n\n"
        return

    # Resolve the kid's age band for the age classifier.
    family = profiling_service.get_family_profile(user_id)
    kid_profile = (family.get("children") or {}).get(kid_name) or {}
    age_band = _kid_age_band(kid_profile.get("age"))

    # One workflow id for the whole kid turn — the agent LLM, the input/output
    # moderation LLM, and any tool/search all log cost under it (feature varies).
    kid_wf = new_workflow_id()

    # Pre-input gate
    pre = moderation.moderate_input(
        user_id=user_id, kid_name=kid_name, agent_id=agent_id,
        age_band=age_band, text=message,
        cost_workflow=kid_wf, cost_user=user_id,
    )
    if pre.flagged:
        msg_id = storage_backend.append_kid_message(
            agent_id=agent_id, thread_id=thread_id, role="user", content=message,
            moderation_score=1.0, parent_flagged=True,
        )
        if pre.suggested_action == "crisis_route":
            crisis_msg = (
                "I'm really glad you told me. This is something your "
                "grown-up needs to know — they want to help. I'm letting "
                "them know now."
            )
            # Persist the lock BEFORE logging/alerting so even if downstream
            # paths fail, the next turn from this kid is gated.
            storage_backend.lock_kid_agent_for_crisis(
                agent_id=agent_id, user_id=user_id, kid_name=kid_name,
                category=pre.category, severity="crisis", reason=pre.reason,
            )
            moderation.kill_agent(agent_id)  # in-process for the current request
            _track("crisis_lock_triggered", user_id, {"category": pre.category})
            storage_backend.log_moderation_event(
                user_id=user_id, kid_name=kid_name, severity="crisis",
                category=pre.category, action="crisis_routed",
                agent_id=agent_id, message_id=msg_id,
                details={"reason": pre.reason},
                parent_notified_at=_dispatch_crisis_push(user_id, kid_name, agent_id),
            )
            telemetry.alert_crisis(
                user_id=user_id, kid_name=kid_name, agent_id=agent_id,
                excerpt=message,
            )
            for chunk in crisis_msg.split(". "):
                yield f"data: {json.dumps({'type': 'token', 'content': chunk + '. '})}\n\n"
            yield f"data: {json.dumps({'type': 'crisis', 'content': pre.category})}\n\n"
            yield "data: [DONE]\n\n"
            return
        else:
            storage_backend.log_moderation_event(
                user_id=user_id, kid_name=kid_name, severity=pre.severity,
                category=pre.category, action="blocked_input",
                agent_id=agent_id, message_id=msg_id,
                details={"reason": pre.reason},
            )
            telemetry.alert_moderation_event(
                user_id=user_id, kid_name=kid_name, agent_id=agent_id,
                severity=pre.severity, category=pre.category,
                action="blocked_input", excerpt=message,
            )
            redirect = "Hmm, let's try a different question — your grown-up will see this chat."
            yield f"data: {json.dumps({'type': 'token', 'content': redirect})}\n\n"
            yield f"data: {json.dumps({'type': 'blocked', 'content': pre.category})}\n\n"
            yield "data: [DONE]\n\n"
            return

    # Cleared — store the user turn.
    user_msg_id = storage_backend.append_kid_message(
        agent_id=agent_id, thread_id=thread_id, role="user", content=message,
    )

    memory_key = f"kid:{user_id}:{kid_name}:{thread_id}"
    kid_cost_cb = CostLoggingCallbackHandler(
        feature="kid", workflow=kid_wf, session=thread_id, user=user_id
    )
    config_lg = {"configurable": {"thread_id": memory_key}, "callbacks": [kid_cost_cb]}

    sm = moderation.StreamingModerator(
        user_id=user_id, kid_name=kid_name, agent_id=agent_id, age_band=age_band,
        cost_workflow=kid_wf, cost_user=user_id,
    )
    assistant_buffer = ""
    block_handled = False  # ensures lock/log/alert runs exactly once

    # Voice is exclusively the ConvAI (v2) path's job now — /kid-chat streams
    # text only. reply_id is pre-generated so the assistant row has a stable id.
    import uuid as _uuid
    reply_id = str(_uuid.uuid4())

    def _apply_block_side_effects() -> None:
        """Lock (on crisis) + log + alert for a blocked output. Must run BEFORE
        the replacement message is yielded so the agent is frozen before the
        kid can send another turn (B-7). Idempotent via block_handled."""
        nonlocal block_handled
        if block_handled or not sm.block_reason:
            return
        block_handled = True
        if sm.block_reason.severity == "crisis":
            # Freeze first — persist the lock and kill the in-process agent
            # before anything goes back on the wire.
            storage_backend.lock_kid_agent_for_crisis(
                agent_id=agent_id, user_id=user_id, kid_name=kid_name,
                category=sm.block_reason.category, severity="crisis",
                reason=f"output: {sm.block_reason.reason}",
            )
            moderation.kill_agent(agent_id)
            _track("crisis_lock_triggered", user_id, {"category": sm.block_reason.category})
            storage_backend.log_moderation_event(
                user_id=user_id, kid_name=kid_name, severity="crisis",
                category=sm.block_reason.category, action="crisis_routed",
                agent_id=agent_id, message_id=user_msg_id,
                details={"side": "output"},
                parent_notified_at=_dispatch_crisis_push(user_id, kid_name, agent_id),
            )
            telemetry.alert_crisis(
                user_id=user_id, kid_name=kid_name, agent_id=agent_id,
                excerpt="[redacted-crisis-output]",
            )
        else:
            storage_backend.log_moderation_event(
                user_id=user_id, kid_name=kid_name, severity=sm.block_reason.severity,
                category=sm.block_reason.category, action="blocked_output",
                agent_id=agent_id, message_id=user_msg_id,
                details={"reason": sm.block_reason.reason},
            )
            telemetry.alert_moderation_event(
                user_id=user_id, kid_name=kid_name, agent_id=agent_id,
                severity=sm.block_reason.severity, category=sm.block_reason.category,
                action="blocked_output", excerpt="[redacted-blocked-output]",
            )

    try:
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config_lg,
            version="v1",
        ):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if not content:
                    continue
                assistant_buffer += content
                for safe in sm.feed(content):
                    yield f"data: {json.dumps({'type': 'token', 'content': safe})}\n\n"
                if sm.state.value == "blocked":
                    # Lock/kill BEFORE the replacement reaches the kid (B-7).
                    _apply_block_side_effects()
                    yield f"data: {json.dumps({'type': 'token', 'content': sm.replacement_message()})}\n\n"
                    yield f"data: {json.dumps({'type': 'blocked', 'content': (sm.block_reason.category if sm.block_reason else 'unknown')})}\n\n"
                    break
            elif kind == "on_tool_start":
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': event['name']})}\n\n"
            elif kind == "on_tool_end":
                yield f"data: {json.dumps({'type': 'tool_end', 'tool': event['name']})}\n\n"

        # End-of-stream flush. finalize() may flag late (under-threshold or
        # whole-output recheck) — handle that BEFORE [DONE].
        for chunk in sm.finalize():
            yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

        if sm.state.value == "blocked" and sm.block_reason:
            # Covers both the mid-stream break (already handled, idempotent) and
            # the late finalize() flag. Lock/log/alert, then emit a retract so
            # the client replaces anything already shown.
            already = block_handled
            _apply_block_side_effects()
            if not already:
                yield f"data: {json.dumps({'type': 'retract', 'content': sm.replacement_message()})}\n\n"
            # Persist the replacement, NEVER the raw (possibly harmful) buffer (H-3).
            storage_backend.append_kid_message(
                agent_id=agent_id, thread_id=thread_id, role="assistant",
                content=sm.replacement_message(), parent_flagged=True,
            )
        elif assistant_buffer:
            # Clean output — safe to persist what was actually streamed.
            storage_backend.append_kid_message(
                agent_id=agent_id, thread_id=thread_id, role="assistant",
                content=sm.assembled_output or assistant_buffer,
                message_id=reply_id,
            )

        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.exception("[kid_chat] stream error")
        yield f"data: {json.dumps({'type': 'error', 'content': 'Something went wrong. Please try again.'})}\n\n"


@app.post("/kid-chat")
async def kid_chat_endpoint(request: KidChatRequest, user_id: str = Depends(current_user)):
    authorize_user_match(authenticated=user_id, claimed=request.user_id)
    _require_consent(user_id)
    rate_limit_enforce(user_id, "chat")
    if not _verify_kid_pin(request.user_id, request.kid_name, request.kid_pin):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"error": "PIN check failed"})
    _track("kid_chat_message_sent", user_id)
    return StreamingResponse(
        generate_kid_stream(
            user_id=request.user_id,
            kid_name=request.kid_name,
            thread_id=request.thread_id,
            message=request.message,
        ),
        media_type="text/event-stream",
    )


@app.get("/kid-agent/status")
def kid_agent_status(
    kid_name: str,
    user_id: str = Depends(current_user),
):
    """
    Lightweight status probe for the kid surface. iOS calls this when a voice
    session ends unexpectedly to distinguish a crisis end_call (frozen surface)
    from a benign disconnect (text fallback).
    """
    config = storage_backend.get_kid_agent_config(user_id, kid_name)
    if config is None:
        raise HTTPException(status_code=404, detail="agent not found")
    locked = storage_backend.is_kid_agent_crisis_locked(config["id"]) is not None
    return {"enabled": bool(config.get("enabled")), "crisis_locked": locked}


@app.get("/voice/convai-token")
async def voice_convai_token(
    kid_name: str,
    user_id: str = Depends(current_user),
    x_kid_pin: Optional[str] = Header(default=None, alias="X-Kid-Pin"),
):
    """
    Issue a signed WebSocket URL for ElevenLabs Conversational AI.
    iOS connects directly to this URL for real-time voice.
    """
    import httpx
    _require_consent(user_id)

    config = storage_backend.get_kid_agent_config(user_id, kid_name)
    if config is None:
        raise HTTPException(status_code=404, detail="agent not found")
    agent_id = config["id"]
    _track("voice_session_started", user_id, {"surface": "kid"})

    if not _verify_kid_pin(user_id, kid_name, x_kid_pin):
        raise HTTPException(status_code=401, detail="PIN check failed")

    if storage_backend.is_kid_agent_crisis_locked(agent_id) is not None:
        raise HTTPException(status_code=403, detail="agent is crisis-locked")

    elevenlabs_agent_id = os.getenv("ELEVENLABS_AGENT_ID")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    if not elevenlabs_agent_id or not elevenlabs_api_key:
        raise HTTPException(status_code=503, detail="ConvAI not configured")

    invariants = config.get("invariants") or {}
    first_message = None
    persona_examples = invariants.get("personaExamples") or invariants.get("persona_examples") or []
    if persona_examples:
        first_message = persona_examples[0]

    # Voice: intentionally NOT overridden here. By omitting the `tts.voice_id`
    # override we let ElevenLabs use the voice configured on the agent in the
    # dashboard. (Re-add a `"tts": {"voice_id": ...}` block below to restore
    # per-kid voice selection from the allowlist.)
    override: Dict[str, Any] = {
        "agent": {
            "prompt": {"prompt": config.get("system_prompt", "")},
            "language": "en",
        },
        "conversation": {"client_events": [
            "audio", "agent_response", "agent_chat_response_part", "user_transcript",
            "interruption", "conversation_initiation_metadata",
        ]},
    }
    if first_message:
        override["agent"]["first_message"] = first_message

    extra_body = {
        "user_id": user_id,
        "kid_name": kid_name,
        "thread_id": "default",
        "kid_pin": x_kid_pin or "",
        "agent_id": agent_id,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.elevenlabs.io/v1/convai/conversation/token",
            params={"agent_id": elevenlabs_agent_id},
            headers={"xi-api-key": elevenlabs_api_key},
        )
        if resp.status_code != 200:
            logger.error("[convai-token] ElevenLabs token failed: %s %s", resp.status_code, resp.text)
            raise HTTPException(status_code=503, detail="failed to get conversation token")

        token = resp.json().get("token")

    # Persist the greeting: ElevenLabs speaks first_message client-side, so it
    # never flows through our Custom LLM and would otherwise be missing from
    # transcripts/history. Guard against stacking — a reconnect (e.g. the
    # mic-retry path mints a fresh token) must not append the greeting twice.
    if first_message:
        last = storage_backend.get_last_kid_message(agent_id, thread_id="default")
        already_last = last is not None and last.get("role") == "assistant" \
            and last.get("content") == first_message
        if not already_last:
            storage_backend.append_kid_message(
                agent_id=agent_id, thread_id="default",
                role="assistant", content=first_message,
            )

    # Cost: count voice sessions. ElevenLabs bills per CONVERSATION MINUTE — the
    # exact minutes live on the EL dashboard / post-call webhook, not here; this
    # marker counts sessions (× avg minutes = estimate). The per-turn OpenAI token
    # cost of the call is logged separately as feature=kid_voice.
    from app.cost_logging import log_cost as _log_cost, new_workflow_id as _wf
    _log_cost("VOICE", feature="kid_voice", workflow=_wf(), user=user_id,
              provider="elevenlabs", event="session_token_issued", kid=kid_name)
    return {
        "signed_url": token,
        "conversation_config_override": override,
        "custom_llm_extra_body": extra_body,
    }


@app.get("/voice/parent-convai-token")
async def voice_parent_convai_token(user_id: str = Depends(current_user)):
    """
    Issue a ConvAI conversation token for the PARENT coaching agent. Mirrors the
    kid token endpoint but: no PIN, no crisis lock, no first-message ritual. The
    per-user system prompt (soul + family profile + content catalog) is sent as
    an override so the dashboard agent personalizes per connection.
    """
    import httpx
    from app.agent import build_system_prompt_for
    # NOTE: no _require_consent here. The kid-agent informed-consent gate is
    # COPPA-scoped to the child companion; the parent coach involves no child
    # data and mirrors the parent text chat (/chat), which is also ungated.
    # Gating this accidentally locked parents with no consented kid out of voice.

    elevenlabs_agent_id = os.getenv("ELEVENLABS_PARENT_AGENT_ID")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    if not elevenlabs_agent_id or not elevenlabs_api_key:
        raise HTTPException(status_code=503, detail="parent ConvAI not configured")
    _track("voice_session_started", user_id, {"surface": "parent"})

    # Voice directive: the spoken output must be clean (no markdown/headers/lists),
    # but the agent MUST keep emitting [Title](mvp://...) links — the Custom-LLM
    # endpoint strips them from speech and turns them into on-screen cards.
    voice_directive = (
        "\n\nVOICE MODE: You are being spoken aloud to the parent. Reply in short, "
        "natural spoken sentences — no markdown, no headers, no bullet lists, no "
        "asterisks or bold. Keep weaving content recommendations as "
        "[Title](mvp://library/{id}) or [Title](mvp://community/{id}) exactly as "
        "instructed: the link text is spoken naturally and the app shows the card."
    )
    override: Dict[str, Any] = {
        "agent": {
            "prompt": {"prompt": build_system_prompt_for(user_id) + voice_directive},
            "language": "en",
        },
        "conversation": {"client_events": [
            "audio", "agent_response", "agent_chat_response_part", "user_transcript",
            "interruption", "conversation_initiation_metadata",
        ]},
    }
    extra_body = {"user_id": user_id, "thread_id": "default"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.elevenlabs.io/v1/convai/conversation/token",
            params={"agent_id": elevenlabs_agent_id},
            headers={"xi-api-key": elevenlabs_api_key},
        )
        if resp.status_code != 200:
            logger.error("[parent-convai-token] ElevenLabs token failed: %s %s", resp.status_code, resp.text)
            raise HTTPException(status_code=503, detail="failed to get conversation token")
        token = resp.json().get("token")

    from app.cost_logging import log_cost as _log_cost, new_workflow_id as _wf
    _log_cost("VOICE", feature="parent_voice", workflow=_wf(), user=user_id,
              provider="elevenlabs", event="session_token_issued")
    return {
        "signed_url": token,
        "conversation_config_override": override,
        "custom_llm_extra_body": extra_body,
    }


@app.get("/kid-chat/transcripts")
def kid_transcripts(user_id: str, kid_name: str, thread_id: str = "default",
                    limit: int = Query(default=200, ge=1, le=1000),
                    authenticated_user: str = Depends(current_user)):
    """Parent reads the kid's history. Always available — by design."""
    authorize_user_match(authenticated=authenticated_user, claimed=user_id)
    config = storage_backend.get_kid_agent_config(user_id, kid_name)
    if config is None:
        return {"messages": [], "agent": None}
    messages = storage_backend.get_kid_messages(config["id"], thread_id=thread_id, limit=limit)
    return {"agent_id": config["id"], "messages": messages}


@app.get("/kid-moderation/events")
def kid_moderation_events(user_id: str, kid_name: Optional[str] = None,
                           limit: int = Query(default=100, ge=1, le=1000),
                           authenticated_user: str = Depends(current_user)):
    """Parent (or oncall) reads moderation events for their family."""
    authorize_user_match(authenticated=authenticated_user, claimed=user_id)
    return {"events": storage_backend.get_moderation_events(user_id, kid_name=kid_name, limit=limit)}


@app.delete("/family/{user_id}")
def delete_family(user_id: str, authenticated_user: str = Depends(current_user)):
    """
    Honor the consent screen's "delete history at any time" promise. Cascades
    across every kid-data table; writes one audit_events row recording the
    delete (including row counts per table). The audit event is the only
    thing that survives.

    Parquet snapshots in /app/data/*.parquet are re-exported immediately after
    the cascade so they forget the family NOW, not "on next export" (they are
    the durability path on Railway and would otherwise retain deleted kid data
    until some later export ran). The in-memory LangGraph MemorySaver
    checkpointer is NOT touched (process-local; discarded next restart).
    """
    authorize_user_match(authenticated=authenticated_user, claimed=user_id)
    # Grab the analytics id BEFORE the cascade deletes the account row, so we can
    # purge the PostHog person too (part of the "delete my data" promise).
    _analytics_id = storage_backend.analytics_id_for(user_id)
    try:
        from app.analytics import capture as _capture
        _capture("family_deleted", user_id)
    except Exception:
        pass
    result = storage_backend.delete_family(user_id=user_id, actor=authenticated_user)
    counts = result.get("counts", {})
    # Evict the in-memory family profile BEFORE the parquet re-export below. The
    # storage cascade drops the DB rows, but `profiling_service` is a separate
    # process-local singleton that `GET /profile` and the agents read from — and
    # `export_all_parquet` can flush it back into `user_data`. Popping it here
    # makes the delete visible immediately and stops a re-export resurrecting it.
    profiling_service.remove_family(user_id)
    # Photos live outside the DB entirely — sweep the family's whole blob
    # prefix so "delete my data" covers them too (no-op when unconfigured).
    from app import blobs as _blobs
    _blobs_deleted = _blobs.delete_all(f"u/{user_id}/")
    if _blobs_deleted:
        counts["blobs"] = _blobs_deleted
    if _analytics_id:
        try:
            from app.analytics.deletion import delete_person
            delete_person(_analytics_id)   # no-op unless PostHog is configured
        except Exception:
            logger.warning("[delete-family] PostHog person deletion failed (non-fatal)")
    try:
        storage_backend.export_all_parquet()
    except Exception:
        # The DB rows are gone (the delete stands); a failed snapshot refresh
        # must be visible, not silent — the stale snapshot still holds PII.
        logger.exception("[delete-family] parquet re-export failed after delete of %s", user_id)
    # Abort any in-flight kid streams for the deleted agents (H-5): the kill
    # flag is checked by the moderation gate, so a streaming response can't
    # keep serving a family that no longer exists.
    for agent_id in result.get("agent_ids", []):
        moderation.kill_agent(agent_id)
    # Drop process-local kid agent caches so a fresh family_id doesn't reuse them.
    try:
        kid_agent_service.invalidate_user(user_id)
    except Exception:
        pass
    return {"ok": True, "user_id": user_id, "deleted": counts}


@app.get("/kid-agent/crisis-locks")
def kid_agent_crisis_locks(user_id: str, authenticated_user: str = Depends(current_user)):
    """Parent dashboard: which of my kids' agents are currently locked, and why."""
    authorize_user_match(authenticated=authenticated_user, claimed=user_id)
    _require_consent(user_id)
    return {"locks": storage_backend.list_active_crisis_locks(user_id)}


@app.post("/kid-agent/{agent_id}/revive")
def kid_agent_revive(agent_id: str, authenticated_user: str = Depends(current_user)):
    """
    Parent-only: clear a crisis lock so the kid can resume chatting.

    Verifies the requesting parent owns the agent, NOT just that they're some
    authenticated user — otherwise any token holder could revive any agent.
    """
    lock = storage_backend.is_kid_agent_crisis_locked(agent_id)
    if lock is None:
        raise HTTPException(status_code=404, detail="agent has no active crisis lock")
    if lock["user_id"] != authenticated_user:
        # 404, not 403: a non-owner must not learn the agent_id exists/is locked.
        raise HTTPException(status_code=404, detail="agent has no active crisis lock")
    _require_consent(authenticated_user)
    cleared = storage_backend.revive_kid_agent_from_crisis(
        agent_id=agent_id, by=authenticated_user,
    )
    moderation.revive_agent(agent_id)  # clear the in-process flag too
    # Only re-enable if we actually cleared an active lock (H-6); never flip
    # enabled=True as a side effect of a no-op revive.
    if cleared:
        storage_backend.set_kid_agent_enabled(agent_id, True)
        _track("companion_reactivated", authenticated_user)
    # Safety-relevant parent action — always audit it.
    storage_backend.write_audit_event(
        user_id=lock["user_id"], actor=authenticated_user,
        action="crisis_revive",
        details={"agent_id": agent_id, "kid_name": lock["kid_name"],
                 "category": lock.get("category"), "cleared": cleared},
    )
    return {"ok": cleared, "agent_id": agent_id, "kid_name": lock["kid_name"]}


# ── Daily summaries (Phase 4) ────────────────────────────────────────

class SummaryGenerateRequest(BaseModel):
    user_id: str
    kid_name: Optional[str] = None       # if absent, generate for every kid
    date: Optional[str] = None           # 'YYYY-MM-DD'; defaults to today


@app.post("/summary/generate")
def summary_generate(req: SummaryGenerateRequest, user_id: str = Depends(current_user)):
    """Generate (or regenerate) the daily summary for one kid or the whole family."""
    authorize_user_match(authenticated=user_id, claimed=req.user_id)
    if req.kid_name:
        result = kid_summary.generate_for_kid(
            user_id=req.user_id, kid_name=req.kid_name, date_iso=req.date,
        )
        return {"summaries": [result]}
    results = kid_summary.generate_for_user_on_date(req.user_id, date_iso=req.date)
    return {"summaries": results}


@app.get("/summary/list")
def summary_list(user_id: str, kid_name: Optional[str] = None, limit: int = 30,
                 authenticated_user: str = Depends(current_user)):
    authorize_user_match(authenticated=authenticated_user, claimed=user_id)
    return {"summaries": storage_backend.list_daily_summaries(
        user_id, kid_name=kid_name, limit=limit
    )}


# ── CMS CRUD Endpoints ────────────────────────────────────────────────

@app.post("/cms/articles")
def cms_create_article(req: ArticleCreateRequest, _: None = Depends(require_admin_token)):
    return content_service.create_article(req.model_dump())


@app.put("/cms/articles/{article_id}")
def cms_update_article(article_id: str, req: ArticleUpdateRequest, _: None = Depends(require_admin_token)):
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    result = content_service.update_article(article_id, data)
    if result is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Article not found"})
    return result


@app.delete("/cms/articles/{article_id}")
def cms_delete_article(article_id: str, _: None = Depends(require_admin_token)):
    if not content_service.delete_article(article_id):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Article not found"})
    return {"deleted": True}


@app.get("/cms/community-posts/{post_id}")
def cms_get_community_post(post_id: str, _: None = Depends(require_admin_token)):
    post = content_service.get_community_post(post_id)
    if post is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Post not found"})
    return post


@app.post("/cms/community-posts")
def cms_create_community_post(req: CommunityPostCreateRequest, _: None = Depends(require_admin_token)):
    return content_service.create_community_post(req.model_dump())


@app.put("/cms/community-posts/{post_id}")
def cms_update_community_post(post_id: str, req: CommunityPostUpdateRequest, _: None = Depends(require_admin_token)):
    data = {k: v for k, v in req.model_dump().items() if v is not None}
    result = content_service.update_community_post(post_id, data)
    if result is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Post not found"})
    return result


@app.delete("/cms/community-posts/{post_id}")
def cms_delete_community_post(post_id: str, _: None = Depends(require_admin_token)):
    if not content_service.delete_community_post(post_id):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Post not found"})
    return {"deleted": True}


@app.post("/cms/categories")
def cms_create_category(req: CategoryCreateRequest, _: None = Depends(require_admin_token)):
    return content_service.create_category(req.model_dump())


@app.put("/cms/categories/{category_id}")
def cms_update_category(category_id: str, req: CategoryUpdateRequest, _: None = Depends(require_admin_token)):
    # Drop unset fields (so the UPDATE only touches explicitly-sent columns),
    # but KEEP explicit None — null on parent_id is how the CMS clears a
    # category back to top-level ("— None (top-level) —"). model_fields_set
    # distinguishes "client omitted the field" from "client sent null".
    sent = req.model_fields_set
    data = {k: getattr(req, k) for k in sent}
    result = content_service.update_category(category_id, data)
    if result is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Category not found"})
    return result


@app.delete("/cms/categories/{category_id}")
def cms_delete_category(category_id: str, _: None = Depends(require_admin_token)):
    if not content_service.delete_category(category_id):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"error": "Category not found"})
    return {"deleted": True}


@app.get("/cms/stats")
def cms_stats(_: None = Depends(require_admin_token)):
    return content_service.get_content_stats()


@app.post("/cms/export-parquet")
def cms_export_parquet(_: None = Depends(require_admin_token)):
    content_service.export_content_parquet()
    return {"exported": True}


@app.get("/data/export")
def data_export(_: None = Depends(require_admin_token)):
    """Trigger parquet export and return checksums for sync detection. Admin-only."""
    import hashlib
    # Export EVERY table (A2) — including kid/consent/audit/auth — so the sync
    # script and any volume-rebuild can recover them, not just user_data + content.
    persist_state()
    storage_backend.export_all_parquet()
    data_dir = Path(__file__).resolve().parent.parent / "data"
    checksums = {}
    for pq in sorted(data_dir.glob("*.parquet")):
        checksums[pq.name] = hashlib.md5(pq.read_bytes()).hexdigest()
    return {"checksums": checksums}


@app.get("/data/download/{filename}")
def data_download(filename: str, _: None = Depends(require_admin_token)):
    """Download a parquet file from the data directory. Admin-only."""
    if not filename.endswith(".parquet"):
        return JSONResponse(status_code=400, content={"error": "Only .parquet files"})
    data_dir = (Path(__file__).resolve().parent.parent / "data").resolve()
    # Resolve and confirm the path stays inside data_dir (block ../ traversal).
    file_path = (data_dir / filename).resolve()
    if not str(file_path).startswith(str(data_dir) + os.sep):
        return JSONResponse(status_code=400, content={"error": "invalid path"})
    if not file_path.is_file():
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)


@app.get("/health")
def health_check():
    # DB-aware (A6): a 200 must mean the DuckDB file is open and answering, so a
    # corrupt/absent DB fails the Railway deploy gate instead of taking traffic.
    if not storage_backend.ping():
        raise HTTPException(status_code=503, detail="database not ready")
    return {"status": "ok"}


@app.get("/debug/sentry-test")
def sentry_test(_: None = Depends(require_admin_token)):
    """Admin-gated verification lever: deliberately raise an unhandled exception so
    Sentry's FastAPI integration captures a REAL production event (full request
    context), confirming error tracking works end-to-end. Returns 500. Safe — gated
    by ADMIN_TOKEN, touches no data. (Standard Sentry verification pattern.)"""
    raise RuntimeError("Deliberate Sentry verification error from /debug/sentry-test")


# ── Serve built CMS static files ─────────────────────────────────────

_cms_dist = Path(__file__).resolve().parent.parent / "cms" / "dist"
if _cms_dist.is_dir():
    # Catch-all for SPA routing: serve index.html for any /cms/* path not matched above
    @app.get("/cms/{full_path:path}")
    def cms_spa_fallback(full_path: str):
        # Try to serve the static file first
        file_path = _cms_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for SPA client-side routing
        return FileResponse(_cms_dist / "index.html")

    @app.get("/cms")
    def cms_root():
        return FileResponse(_cms_dist / "index.html")


# ── Serve built parent dashboard (Vite SPA, base=/dashboard/) ─────────
# In prod the dashboard is same-origin with the API, so its relative fetches
# (/research, /cos, /auth, /profile) hit this backend directly — no proxy.

_dashboard_dist = Path(__file__).resolve().parent.parent / "parent-dashboard" / "dist"
if _dashboard_dist.is_dir():
    @app.get("/dashboard/{full_path:path}")
    def dashboard_spa_fallback(full_path: str):
        file_path = _dashboard_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_dashboard_dist / "index.html")

    @app.get("/dashboard")
    def dashboard_root():
        return FileResponse(_dashboard_dist / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8904)

