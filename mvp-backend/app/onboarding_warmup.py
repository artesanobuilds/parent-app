"""
First-run agent warm-up.

The redesigned onboarding funnel ends on a "Creating account" progress ring with
four beats. Each beat is REAL work, so the new dashboard is non-empty the first
time the parent opens it:

  1. family  — "Getting to know your family"      (the profile seed work)
  2. coach   — "Bringing your coach up to speed"  (prime the coach + write the
                                                   FIRST persisted coach nudge)
  3. plan    — "Sketching your first plan"        (seed the COS board with
                                                   age/ZIP-derived considerations)
  4. account — "Securing your family's space"     (account provisioning + the
                                                   legal-acceptance status flush)

Shape (modelled on app/research/worker.py, the established durable-background-job
pattern here): the `onboarding_warmup_runs` row IS the job — the phone never
holds it. Workers claim a queued run atomically, run the steps, and finalize
CONDITIONALLY (`finalize_warmup_run_if_running`) so a cancel can't be clobbered
back to done. A startup sweeper re-queues anything a restart left `running`, and
every step is idempotent so that re-run is safe.

THE HARD RULE — the warm-up must never block the parent.
Every step runs under its own timeout on a small pool; a step that raises, times
out, or stalls is marked `failed` and the loop MOVES ON. The run always reaches
a terminal state, and the overall status always reaches 100. A parent stuck
behind a spinner because an LLM call timed out is strictly worse than an
unpersonalised Home. `/profile/seed` and its durable client-side retry are
untouched — the warm-up is layered on top, never a replacement.

The step functions are injected (`STEP_FUNCS` by default) so tests can pass
fakes that do zero LLM/network work.
"""
from __future__ import annotations

import asyncio
import copy
from dataclasses import replace
import time

from app.jobs.context import JobContext, JobStopped, StepStorage
from app.jobs.runner import JobReaper
import json
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth import current_user, authorize_user_match
from app.rate_limit import enforce as rate_limit_enforce

logger = logging.getLogger(__name__)

# ── the four beats ───────────────────────────────────────────────────
#
# `key` is the stable contract the clients bind to; `label` is Greg's copy.
# Order here IS display order.

STEP_FAMILY = "family"
STEP_COACH = "coach"
STEP_PLAN = "plan"
STEP_ACCOUNT = "account"

STEP_LABELS: List[tuple] = [
    (STEP_FAMILY, "Getting to know your family"),
    (STEP_COACH, "Bringing your coach up to speed"),
    (STEP_PLAN, "Sketching your first plan"),
    (STEP_ACCOUNT, "Securing your family's space"),
]

STEP_KEYS = [k for k, _ in STEP_LABELS]

# Per-step states. `skipped` exists so a step with nothing to do is honestly
# distinguishable from one that succeeded at real work.
PENDING, RUNNING, DONE, FAILED, SKIPPED = "pending", "running", "done", "failed", "skipped"
_TERMINAL_STEP_STATES = {DONE, FAILED, SKIPPED}
_TERMINAL_RUN_STATES = {"done", "failed", "canceled"}

StepFn = Callable[..., Dict[str, Any]]


def initial_steps() -> List[Dict[str, Any]]:
    """A fresh step list, every beat pending."""
    return [
        {"key": key, "label": label, "state": PENDING, "detail": {}, "error": None}
        for key, label in STEP_LABELS
    ]


def overall_percent(steps: List[Dict[str, Any]], status: str) -> int:
    """0-100 for the UI's percentage ring. A terminal RUN is always 100 — the
    ring must land even when a step failed, or the parent watches a stuck 75%
    forever. Mid-flight, a finished step is worth a full share and the one
    currently running is worth half, so the number always moves."""
    if status in _TERMINAL_RUN_STATES:
        return 100
    total = len(steps) or 1
    score = 0.0
    for step in steps:
        state = step.get("state")
        if state in _TERMINAL_STEP_STATES:
            score += 1.0
        elif state == RUNNING:
            score += 0.5
    # Half-UP, not Python's banker's rounding — 12.5% must read as 13, and the
    # ring must never appear to tick backwards between two equal-looking states.
    return int(100.0 * score / total + 0.5)


def status_payload(run: Dict[str, Any]) -> Dict[str, Any]:
    """The wire shape both the poll endpoint and the SSE stream emit."""
    steps = run.get("steps") or []
    return {
        "run_id": run["id"],
        "status": run["status"],
        "percent": overall_percent(steps, run["status"]),
        "steps": steps,
        "result": run.get("result") or {},
        "error": run.get("error"),
    }


# ── tunables ─────────────────────────────────────────────────────────

def _default_concurrency() -> int:
    """How many warm-ups run at once. The work is I/O-bound (one LLM call plus
    DuckDB writes), so a small thread pool removes head-of-line blocking when
    several parents finish onboarding at the same moment."""
    try:
        n = int(os.getenv("ONBOARDING_WARMUP_CONCURRENCY", "2"))
    except (TypeError, ValueError):
        n = 2
    return max(1, min(n, 16))


def _step_timeout() -> float:
    """Ceiling for ONE step. The whole run is bounded by 4x this, which is the
    worst case the progress ring has to sit through before it lands."""
    try:
        t = float(os.getenv("ONBOARDING_WARMUP_STEP_TIMEOUT_S", "25"))
    except (TypeError, ValueError):
        t = 25.0
    return max(1.0, t)


# ── step 1: the family profile ───────────────────────────────────────

def step_family(storage: Any, user_id: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Read back what /profile/seed durably wrote.

    Deliberately does NOT re-do the seed: `/profile/seed` plus its durable
    client-side retry remains the one write path for onboarding answers. This
    step's job is to confirm the profile is there and give the later steps their
    context. An empty profile is reported, never raised — the parent is not
    blocked because a seed retry is still in flight."""
    from app.profiling import profiling_service

    family = profiling_service.get_family_profile(user_id) or {}
    parent = family.get("parent") or {}
    children = family.get("children") or {}

    # The seed endpoint owns profile persistence. Warmup only reads it: a
    # delayed cache snapshot here could overwrite a newer profile or recreate a
    # deleted family, bypassing the step's storage fence.
    ctx["family"] = family
    return {
        "profile_present": bool(parent.get("name") or children),
        "kid_count": len(children),
        "kids": sorted(children.keys()),
    }


# ── step 2: the coach + its first nudge ──────────────────────────────

class _NudgeDraft(BaseModel):
    body: str
    kid_name: Optional[str] = None
    cta_label: Optional[str] = None


_NUDGE_SYSTEM = (
    "You are the parenting coach in a family app, writing the very first card a "
    "parent sees on their Home screen.\n"
    "Write ONE short nudge (max 45 words) grounded in what this family actually "
    "told us. Name a specific child. Observe something true about them, then give "
    "ONE concrete thing to try TODAY. Warm, plain, specific — no jargon, no "
    "preamble, no emoji, no clinical or medical advice.\n"
    "Example of the register we want: \"Ben's been practicing taking turns. "
    "Tonight, try trading who picks the bedtime book — small wins build the "
    "muscle.\"\n"
    "Also return kid_name (exactly as spelled in the profile) and cta_label of "
    "the form \"Try this with <kid>\"."
)


def _family_context_text(family: Dict[str, Any]) -> str:
    """Prune the profile to non-empty fields so the prompt stays lean."""
    def _prune(value: Any) -> Any:
        if isinstance(value, dict):
            out = {k: _prune(v) for k, v in value.items()}
            return {k: v for k, v in out.items() if v not in (None, [], {}, "")}
        if isinstance(value, list):
            out_l = [_prune(v) for v in value]
            return [v for v in out_l if v not in (None, [], {}, "")]
        return value

    parts = [json.dumps(_prune(family or {}), ensure_ascii=False, indent=2)]

    # Heisman sprint-01: the funnel now captures the parent's own asks. Surface
    # them as explicit labeled lines (not just keys buried in the JSON) so the
    # first nudge can actually speak to what the parent said they wanted.
    parent = (family or {}).get("parent") or {}
    focus_topic = str(parent.get("focus_topic") or "").strip()
    if focus_topic:
        parts.append(f"Parent wants help with: {focus_topic}")
    self_care = [str(t).strip() for t in (parent.get("self_care_tasks") or []) if str(t).strip()]
    if self_care:
        parts.append("Parent's own to-dos this week: " + "; ".join(self_care))

    return "\n\n".join(parts)


def step_coach(storage: Any, user_id: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Prime the coaching agent with family context, then generate + persist the
    parent's FIRST coach nudge so Home's COACH card has real content.

    Idempotent: `upsert_coach_nudge` replaces the prior 'warmup' nudge, so a
    re-run after a restart can't leave a parent with two first nudges.

    Deliberately does NOT invent a generic nudge when the model is unavailable.
    A fabricated "every child is different" platitude is worse than the card's
    empty state — the step fails, the run still lands, Home degrades."""
    family = ctx.get("family")
    if family is None:
        from app.profiling import profiling_service
        family = profiling_service.get_family_profile(user_id) or {}
    children = family.get("children") or {}
    if not children:
        return {"skipped": True, "reason": "no children on the profile yet"}

    # Priming: rebuilding the cached coach agent bakes the just-seeded family
    # profile into its system prompt, so the parent's first message already
    # lands on a coach that knows them. Best-effort — a priming failure must
    # not cost the nudge.
    primed = False
    try:
        from app.agent import get_agent
        get_agent(user_id)
        primed = True
    except Exception:  # noqa: BLE001
        logger.exception("[warmup] coach priming failed for %s", user_id)

    from app.agent import llm

    job = ctx.get("job_context")
    if job:
        job.check()
        from app.jobs.middleware import bounded_model
        llm = bounded_model(llm, job.remaining(ctx["step_budget"]))
    draft = llm.with_structured_output(_NudgeDraft).invoke([
        {"role": "system", "content": _NUDGE_SYSTEM},
        {"role": "user", "content": "Family profile:\n" + _family_context_text(family)},
    ])

    body = (getattr(draft, "body", "") or "").strip()
    if not body:
        raise RuntimeError("coach returned an empty nudge")

    kid_name = (getattr(draft, "kid_name", None) or "").strip() or None
    # Never surface a hallucinated child: fall back to a real one.
    if kid_name not in children:
        kid_name = sorted(children.keys())[0]
    cta_label = (getattr(draft, "cta_label", None) or "").strip() or f"Try this with {kid_name}"

    nudge_id = storage.upsert_coach_nudge(
        user_id=user_id,
        body=body,
        source="warmup",
        kid_name=kid_name,
        cta_label=cta_label,
        origin_id=ctx.get("run_id"),
    )
    ctx.setdefault("result", {})["coach_nudge_id"] = nudge_id
    return {"primed": primed, "nudge_id": nudge_id, "kid_name": kid_name}


# ── step 3: the first plan ───────────────────────────────────────────
#
# Age-banded starter considerations. Deterministic and offline on purpose: this
# beat must land in milliseconds, and the real discovery run (POST /research/runs)
# is what fills the board with local, priced, dated options. These are the
# prompts that make the empty board legible — the parent keeps or passes each.

_STARTERS_BY_BAND: Dict[str, List[tuple]] = {
    "early": [
        ("Library story time", "outing"),
        ("Parent-and-tot swim lessons", "extracurricular"),
        ("Toddler music or movement class", "extracurricular"),
    ],
    "primary": [
        ("Summer day camp", "camp"),
        ("Beginner swim lessons", "extracurricular"),
        ("Youth soccer or T-ball season", "extracurricular"),
    ],
    "middle": [
        ("Sleepaway or specialty camp week", "camp"),
        ("STEM, robotics or maker club", "extracurricular"),
        ("Sports league tryouts", "extracurricular"),
    ],
    "teen": [
        ("Summer volunteer or service hours", "school_event"),
        ("Skills workshop (coding, art, music)", "extracurricular"),
        ("Teen sports or club season", "extracurricular"),
    ],
}

_FAMILY_STARTERS: List[tuple] = [
    ("A weekend outing everyone can do", "outing"),
]


def _band_for_age(age: Any) -> Optional[str]:
    try:
        a = float(age)
    except (TypeError, ValueError):
        return None
    if a < 5:
        return "early"
    if a < 9:
        return "primary"
    if a < 13:
        return "middle"
    return "teen"


def step_plan(storage: Any, user_id: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Seed the Chief-of-Staff board with a starting set of considerations
    derived from the kids' ages + the family's postal code.

    Everything lands in `exploring`, which `cos.lifecycle.stage_for` maps to the
    "Considering" stage — nothing is auto-registered, nothing is auto-watched,
    so no email/calendar side effects fire.

    Idempotent by (kid_name, name): a re-run skips anything already on the
    board, so a restart mid-warm-up can't duplicate the parent's list."""
    family = ctx.get("family")
    if family is None:
        from app.profiling import profiling_service
        family = profiling_service.get_family_profile(user_id) or {}
    parent = family.get("parent") or {}
    children = family.get("children") or {}
    postal_code = (parent.get("postal_code") or "").strip() or None

    existing_rows = storage.list_tracked_activities(user_id) or []
    existing = {
        ((a.get("kid_name") or "").strip().lower(), (a.get("name") or "").strip().lower())
        for a in existing_rows
    }

    # Heisman sprint-01: /profile/seed now writes REAL rows before this beat
    # runs — the parent's own week tasks ("onboarding_self") and the step-04
    # extraction results ("onboarding_extract"). The starters below exist only
    # to make an EMPTY board legible; when the seed already gave the board real
    # content, piling generic suggestions next to it dilutes the parent's own
    # data. Skip — honestly, as a SKIPPED beat, not a fake success.
    seed_rows = sum(
        1 for a in existing_rows
        if ((a.get("details") or {}).get("source")) in ("onboarding_self", "onboarding_extract")
    )
    if seed_rows:
        ctx.setdefault("result", {})["considerations_seeded"] = 0
        return {
            "skipped": True,
            "reason": f"board already seeded from onboarding ({seed_rows} rows)",
        }

    wanted: List[tuple] = []  # (kid_name, name, activity_type)
    for kid_name, prof in sorted(children.items()):
        band = _band_for_age((prof or {}).get("age"))
        if band is None:
            continue
        for name, atype in _STARTERS_BY_BAND[band]:
            wanted.append((kid_name, name, atype))
    if not wanted:
        # No usable ages (or no kids yet) — still give the board something so
        # it isn't a blank slate on first open.
        wanted = [(None, name, atype) for name, atype in _FAMILY_STARTERS]

    note = "Suggested while setting up your account"
    if postal_code:
        note += f" — look for options near {postal_code}"

    created = 0
    for kid_name, name, atype in wanted:
        key = ((kid_name or "").strip().lower(), name.strip().lower())
        if key in existing:
            continue
        storage.track_activity(
            user_id,
            name=name,
            kid_name=kid_name,
            activity_type=atype,
            status="exploring",
            notes=note,
            details={"source": "onboarding_warmup", "postal_code": postal_code},
        )
        existing.add(key)
        created += 1

    ctx.setdefault("result", {})["considerations_seeded"] = created
    return {"considerations_seeded": created, "postal_code": postal_code}


# ── step 4: the family's space ───────────────────────────────────────

def step_account(storage: Any, user_id: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Provision the account row and flush legal-acceptance status.

    Provisioning is `get_or_create_account` (idempotent by design), backfilling
    the display name from the just-seeded profile so the analytics id and the
    account scaffolding exist before the parent's first real request.

    The legal side is a FLUSH, not an acceptance: it reports which documents
    still need the parent's tap. Recording an acceptance the parent never made
    would be a compliance forgery, so this step never writes one — the client's
    existing /legal/accept path stays the only way in."""
    family = ctx.get("family")
    if family is None:
        from app.profiling import profiling_service
        family = profiling_service.get_family_profile(user_id) or {}
    display_name = ((family.get("parent") or {}).get("name") or "").strip() or None

    account = storage.get_or_create_account(user_id, display_name=display_name)

    pending: List[str] = []
    try:
        for doc in storage.get_current_legal_docs() or []:
            latest = storage.latest_legal_acceptance(user_id, doc["slug"])
            accepted = bool(latest) and (
                latest["version"] == doc["version"] or not doc["requires_reacceptance"]
            )
            if not accepted:
                pending.append(doc["slug"])
    except Exception:  # noqa: BLE001 — legal status is informational here
        logger.exception("[warmup] legal status flush failed for %s", user_id)

    return {
        "account_provisioned": bool(account.get("analytics_id")),
        "pending_legal": pending,
    }


STEP_FUNCS: Dict[str, StepFn] = {
    STEP_FAMILY: step_family,
    STEP_COACH: step_coach,
    STEP_PLAN: step_plan,
    STEP_ACCOUNT: step_account,
}


# ── the worker ───────────────────────────────────────────────────────

class OnboardingWarmupWorker:
    def __init__(
        self,
        storage: Any,
        step_funcs: Optional[Dict[str, StepFn]] = None,
        poll_interval: float = 5.0,
        concurrency: Optional[int] = None,
        step_timeout: Optional[float] = None,
    ) -> None:
        self._storage = storage
        self._reaper = JobReaper(storage, "warmup")
        self._steps = dict(step_funcs) if step_funcs is not None else dict(STEP_FUNCS)
        self._poll = poll_interval
        self._concurrency = concurrency if concurrency is not None else _default_concurrency()
        self._step_timeout = step_timeout if step_timeout is not None else _step_timeout()
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._threads: List[threading.Thread] = []
        # Bound both executing and queued steps. Timed-out synchronous work
        # retains its slot until it actually returns; no accumulating backlog.
        self._slots = threading.BoundedSemaphore(max(2, self._concurrency * 2))
        self._pool = ThreadPoolExecutor(
            max_workers=max(2, self._concurrency * 2),
            thread_name_prefix="warmup-step",
        )

    # ── lifecycle ────────────────────────────────────────────────────
    def start(self) -> None:
        if any(t.is_alive() for t in self._threads):
            return
        self._stop.clear()
        self._reaper.start()
        self._threads = []
        for i in range(self._concurrency):
            t = threading.Thread(target=self._loop, name=f"warmup-worker-{i}", daemon=True)
            t.start()
            self._threads.append(t)
        logger.info("[warmup] worker started (%d threads)", self._concurrency)

    def notify(self) -> None:
        """Wake idle workers immediately (called by the enqueue endpoint)."""
        self._wake.set()

    def stop(self, timeout: float = 3.0) -> None:
        self._stop.set()
        self._reaper.stop()
        self._wake.set()
        for t in self._threads:
            t.join(timeout)
        self._pool.shutdown(wait=False)
        logger.info("[warmup] worker stopped")

    # ── loop ─────────────────────────────────────────────────────────
    def _loop(self) -> None:
        while not self._stop.is_set():
            if not self._drain():
                self._wake.wait(self._poll)
                self._wake.clear()

    def _drain(self) -> bool:
        worked = False
        while not self._stop.is_set():
            try:
                run = self._storage.claim_next_queued_warmup_run(max(1, self._step_timeout * len(STEP_KEYS) + 5))
            except Exception:
                logger.exception("[warmup] claim_next_queued_warmup_run failed")
                break
            if not run:
                break
            worked = True
            self.process_run(run)
        return worked

    # ── one run ──────────────────────────────────────────────────────
    def process_run(self, run: Dict[str, Any]) -> None:
        """Execute a single claimed run. Public + synchronous so tests can call
        it directly without spinning the thread.

        Every step is independently guarded: a raise or a timeout marks THAT
        step failed and the loop continues to the next one. The run finalizes
        either way, so the ring always lands."""
        run_id = run["id"]
        user_id = run["user_id"]
        steps = run.get("steps") or initial_steps()
        job = JobContext.from_run(self._storage, "warmup", run, self._stop)
        ctx: Dict[str, Any] = {"run_id": run_id, "result": dict(run.get("result") or {})}

        try:
            for step in steps:
                job.check()
                # Idempotent re-run after a restart: don't redo finished beats.
                if step.get("state") in _TERMINAL_STEP_STATES:
                    continue
                key = step["key"]
                fn = self._steps.get(key)
                if fn is None:
                    step["state"] = SKIPPED
                    step["detail"] = {"reason": "no implementation registered"}
                    self._persist(job, steps)
                    continue

                step["state"] = RUNNING
                step["error"] = None
                self._persist(job, steps)

                try:
                    detail = self._run_step(fn, user_id, ctx, job) or {}
                    step["state"] = SKIPPED if detail.get("skipped") else DONE
                    step["detail"] = detail
                except FuturesTimeout:
                    step["state"] = FAILED
                    step["error"] = f"timed out after {self._step_timeout:.0f}s"
                    logger.warning("[warmup] run %s step %s timed out", run_id, key)
                except Exception as exc:  # noqa: BLE001 — one bad step, not a bad run
                    step["state"] = FAILED
                    step["error"] = str(exc)[:500]
                    logger.exception("[warmup] run %s step %s failed", run_id, key)
                self._persist(job, steps)
        except Exception:  # noqa: BLE001 — belt and braces around the loop itself
            logger.exception("[warmup] run %s loop failed", run_id)

        self._storage.reap_expired_job_attempts("warmup")
        failed = [s["key"] for s in steps if s.get("state") == FAILED]
        result = dict(ctx.get("result") or {})
        result["failed_steps"] = failed
        # `done` even with failed steps: the ONBOARDING is complete either way —
        # a degraded Home is the failure mode we accept, a blocked parent is not.
        # Conditional finalize so a cancel mid-flight stays terminal.
        if self._storage.finalize_job_attempt(
            job, status="done", steps=steps, result=result,
            error=("; ".join(failed) or None),
        ):
            logger.info(
                "[warmup] run %s done (%d/%d beats succeeded)",
                run_id, len(steps) - len(failed), len(steps),
            )
        else:
            logger.info("[warmup] run %s left 'running' mid-flight (cancelled?)", run_id)

    def _run_step(self, fn: StepFn, user_id: str, ctx: Dict[str, Any], job: JobContext) -> Dict[str, Any]:
        """Bound waiting and fence late writes; running threads are not killed."""
        budget = job.remaining(self._step_timeout)
        if not self._slots.acquire(blocking=False):
            raise RuntimeError("warmup step capacity exhausted")
        canceled = threading.Event()
        step_ctx = copy.deepcopy(ctx)
        step_ctx.update(job_context=replace(job, deadline=min(job.deadline, time.monotonic() + budget)), step_budget=budget)
        storage = StepStorage(self._storage, job, time.monotonic() + budget, canceled)
        try:
            future = self._pool.submit(fn, storage, user_id, step_ctx)
        except BaseException:
            self._slots.release()
            raise
        future.add_done_callback(lambda _: self._slots.release())
        try:
            result = future.result(timeout=budget)
            job.check()
            step_ctx.pop("job_context", None)
            step_ctx.pop("step_budget", None)
            ctx.clear()
            ctx.update(step_ctx)
            return result
        finally:
            # Retire this step even on exceptions. Its storage handle cannot be
            # reused by work continuing after the caller stops waiting.
            canceled.set()
            future.cancel()

    def _persist(self, job: JobContext, steps: List[Dict[str, Any]]) -> None:
        self._storage.update_job_progress(job, steps=steps)


# ── module singleton, wired up by the server lifespan ────────────────

warmup_worker: Optional[OnboardingWarmupWorker] = None


def init_worker(
    storage: Any, step_funcs: Optional[Dict[str, StepFn]] = None
) -> OnboardingWarmupWorker:
    """Create (or replace) the module-level worker."""
    global warmup_worker
    warmup_worker = OnboardingWarmupWorker(storage, step_funcs)
    return warmup_worker


# ── API ──────────────────────────────────────────────────────────────

router = APIRouter(prefix="/onboarding/warmup", tags=["onboarding"])
coach_router = APIRouter(prefix="/coach", tags=["coach"])


class WarmupRequest(BaseModel):
    # Optional: the authenticated identity is the source of truth. When present
    # it must MATCH — never trust a body user_id on its own.
    user_id: Optional[str] = None


def _storage():
    from app.server import storage_backend
    return storage_backend


def _require_owned_run(storage, run_id: str, user_id: str) -> Dict[str, Any]:
    run = storage.get_warmup_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="warm-up run not found")
    authorize_user_match(authenticated=user_id, claimed=run["user_id"], resource=True)
    return run


@router.post("")
def create_warmup(req: WarmupRequest, user_id: str = Depends(current_user)):
    """Enqueue the first-run warm-up for the authenticated parent. A double-tap
    (or a resumed funnel) dedupes onto the in-flight run rather than stacking a
    second one. Returns immediately — the work happens on the worker."""
    if req.user_id:
        authorize_user_match(authenticated=user_id, claimed=req.user_id)
    rate_limit_enforce(user_id, "warmup")

    storage = _storage()
    result = storage.enqueue_warmup_run(
        user_id=user_id, steps=initial_steps(), context={}
    )
    if not result["deduped"]:
        if warmup_worker is not None:
            warmup_worker.notify()
        try:
            from app.analytics import capture
            capture("onboarding_warmup_started", user_id)
        except Exception:
            pass
    return {
        "run_id": result["run_id"],
        "status": result["status"],
        "deduped": result["deduped"],
    }


@router.get("/{run_id}")
def get_warmup(run_id: str, user_id: str = Depends(current_user)):
    """Poll: per-step state + the overall percent the ring renders."""
    return status_payload(_require_owned_run(_storage(), run_id, user_id))


# Stream interval / cap (mirrors app/research/router.py). The ceiling is short:
# a warm-up that hasn't landed in ~2.5 min is one the client should stop waiting
# on, and the client is free to proceed regardless.
_STREAM_INTERVAL_S = 0.5
_STREAM_MAX_TICKS = 300


@router.get("/{run_id}/stream")
async def stream_warmup(run_id: str, user_id: str = Depends(current_user)):
    """SSE: stream the warm-up's progress so the ring animates without polling.
    Emits a frame whenever the payload changes, then a terminal `final` frame +
    `[DONE]`. The poll endpoint stays for fallback."""
    storage = _storage()
    _require_owned_run(storage, run_id, user_id)  # ownership check before streaming

    async def _gen():
        last_payload = None
        for _ in range(_STREAM_MAX_TICKS):
            run = storage.get_warmup_run(run_id)
            if not run:
                yield f"data: {json.dumps({'type': 'error', 'content': 'run not found'})}\n\n"
                return
            payload = dict(status_payload(run))
            payload["type"] = "progress"
            if payload != last_payload:
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                last_payload = payload
            if run["status"] in _TERMINAL_RUN_STATES:
                final = dict(status_payload(run))
                final["type"] = "final"
                yield f"data: {json.dumps(final, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                return
            await asyncio.sleep(_STREAM_INTERVAL_S)
        # Hit the ceiling without terminating — the client falls back to polling
        # (and, per the hard rule, is free to move the parent on regardless).
        yield f"data: {json.dumps({'type': 'timeout'})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")


@coach_router.get("/nudge")
def get_coach_nudge(user_id: str = Depends(current_user)):
    """The parent's current coach nudge — what Home's COACH card renders. The
    warm-up writes the first one; `nudge` is null before that, and the card
    falls back to its empty state."""
    return {"nudge": _storage().latest_coach_nudge(user_id)}
