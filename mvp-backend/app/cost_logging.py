"""
Structured cost logging.

Emits ONE parseable line per billable event so prod logs (Railway) can be
grepped and aggregated to estimate spend — per user, per feature, and per
*workflow* (one "find-activities run", one "coach session", one voice call).

Line format (stable, key=value — easy to parse with awk/jq-ish tooling):

    [COST][LLM]    feature=research workflow=<id> session=<id> user=<id> model=gpt-5.2 \
                   input_tokens=1234 output_tokens=567 total_tokens=1801 usd=0.004200
    [COST][SEARCH] feature=research workflow=<id> ... provider=tavily depth=advanced credits=2 usd=0.016000
    [COST][VOICE]  feature=parent_voice workflow=<id> ... provider=elevenlabs event=session_started

Aggregate a single workflow's total + breakdown:
    grep '\\[COST\\]' app.log \\
      | sed -E 's/.*\\[COST\\]\\[([A-Z]+)\\] (.*)/\\1 \\2/' \\
      | awk '{...group by workflow=..., sum usd by component...}'

Always logs RAW usage (tokens / credits / minutes) — the durable, vendor-price-
independent signal. Also logs `usd`, an ESTIMATE from the pricing table below
(override via env; prices change — verify against current vendor rates).

The same key=value convention carries LATENCY via `log_perf()`:

    [PERF][VOICE]  feature=parent_voice workflow=<id> session=<id> user=<id> \
                   repair_ms=12 model_ttft_ms=850 ttfb_ms=940 total_ms=6200 chunks=42 tool_turn=0

Because a turn's [PERF] line reuses the SAME workflow id as its [COST] lines,
"what did this slow turn cost / what did this expensive turn feel like" is one grep.
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict, Optional

from langchain_core.callbacks import BaseCallbackHandler

# Dedicated logger so cost lines are easy to route/grep ("[COST]"). Inherits the
# app's handler/format; the line itself is self-describing.
cost_logger = logging.getLogger("cost")

# Latency lines get their OWN logger so a perf grep doesn't drag in spend lines
# (and so either stream can be routed/leveled independently in prod).
perf_logger = logging.getLogger("perf")


# ── Pricing (USD) — PLACEHOLDER DEFAULTS. Override via env per real vendor rates.
def _f(env: str, default: str) -> float:
    try:
        return float(os.getenv(env, default))
    except (TypeError, ValueError):
        return float(default)


# OpenAI: per 1,000,000 tokens. Default in/out; per-model overrides via env
# COST_OPENAI_IN_<MODEL> / COST_OPENAI_OUT_<MODEL> (model upper, non-alnum -> _).
# Defaults track gpt-5.5 standard list price ($5 in / $30 out per 1M tokens,
# verified June 2026). Caveat: prompt-cached input is billed at $0.50/1M (90% off)
# but usage_metadata here counts cached + uncached together, so these defaults
# OVER-estimate when prompt caching is active — i.e. they're a conservative ceiling.
OPENAI_IN_PER_MTOK_DEFAULT = _f("COST_OPENAI_IN_PER_MTOK", "5.0")
OPENAI_OUT_PER_MTOK_DEFAULT = _f("COST_OPENAI_OUT_PER_MTOK", "30.0")
# Tavily PAYGO: ~$0.008/credit; basic=1 credit, advanced=2 credits.
TAVILY_USD_PER_CREDIT = _f("COST_TAVILY_PER_CREDIT", "0.008")
# ElevenLabs ConvAI bills per minute (plan-dependent). Estimate only.
ELEVENLABS_USD_PER_MIN = _f("COST_ELEVENLABS_PER_MIN", "0.10")


def _model_key(model: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in (model or "")).upper()


def openai_usd(model: str, in_tok: int, out_tok: int) -> float:
    mk = _model_key(model)
    p_in = _f(f"COST_OPENAI_IN_{mk}", str(OPENAI_IN_PER_MTOK_DEFAULT))
    p_out = _f(f"COST_OPENAI_OUT_{mk}", str(OPENAI_OUT_PER_MTOK_DEFAULT))
    return round((in_tok / 1_000_000) * p_in + (out_tok / 1_000_000) * p_out, 6)


def tavily_usd(credits: int) -> float:
    return round(credits * TAVILY_USD_PER_CREDIT, 6)


def elevenlabs_usd(minutes: float) -> float:
    return round(minutes * ELEVENLABS_USD_PER_MIN, 6)


def new_workflow_id() -> str:
    return uuid.uuid4().hex[:16]


def cost_config(
    feature: str,
    *,
    workflow: Optional[str] = None,
    session: Optional[str] = None,
    user: Optional[str] = None,
    search_depth: str = "basic",
) -> Dict[str, Any]:
    """LangChain config that cost-logs a one-off `.invoke()` (moderation,
    synthesis, summary, …). Pass `workflow=` to aggregate with a parent action
    (e.g. a kid-chat turn); omit it for a standalone fresh id."""
    return {"callbacks": [CostLoggingCallbackHandler(
        feature=feature, workflow=workflow or new_workflow_id(),
        session=session, user=user, search_depth=search_depth,
    )]}


# ── Emit ─────────────────────────────────────────────────────────────
def _kv(fields: Dict[str, Any]) -> str:
    parts = []
    for k, v in fields.items():
        if v is None:
            continue
        s = str(v)
        parts.append(f"{k}={s.replace(' ', '_')}")
    return " ".join(parts)


def log_cost(
    component: str,
    *,
    feature: str,
    workflow: str,
    user: Optional[str] = None,
    session: Optional[str] = None,
    usd: Optional[float] = None,
    **fields: Any,
) -> None:
    """Emit one `[COST][COMPONENT] ...` line. `workflow` is the correlation id to
    group a single user action's spend across all components."""
    base: Dict[str, Any] = {"feature": feature, "workflow": workflow}
    if session is not None:
        base["session"] = session
    if user is not None:
        base["user"] = user
    base.update(fields)
    if usd is not None:
        base["usd"] = f"{usd:.6f}"
    try:
        cost_logger.info("[COST][%s] %s", component.upper(), _kv(base))
    except Exception:  # cost logging must never break a request
        pass


def log_perf(
    component: str,
    *,
    feature: str,
    workflow: str,
    user: Optional[str] = None,
    session: Optional[str] = None,
    **fields: Any,
) -> None:
    """Emit one `[PERF][COMPONENT] ...` line — the latency twin of log_cost(),
    same `_kv` formatting and the same `workflow` correlation id, so a turn's
    timings join its spend lines on one grep.

    Fields whose value is None are DROPPED by `_kv` — that's load-bearing, not
    sloppiness: a turn blocked before the model runs legitimately has no
    `model_ttft_ms`, and an absent key parses better than a fake 0."""
    base: Dict[str, Any] = {"feature": feature, "workflow": workflow}
    if session is not None:
        base["session"] = session
    if user is not None:
        base["user"] = user
    base.update(fields)
    try:
        perf_logger.info("[PERF][%s] %s", component.upper(), _kv(base))
    except Exception:  # perf logging must never break a request
        pass


# ── LangChain callback: captures LLM tokens + Tavily searches ────────
class CostLoggingCallbackHandler(BaseCallbackHandler):
    """Attach to any agent/LLM run via config={"callbacks": [handler]}. Logs a
    `[COST][LLM]` line per model call (token usage) and a `[COST][SEARCH]` line
    per Tavily call, all tagged with the same workflow id for aggregation."""

    def __init__(
        self,
        *,
        feature: str,
        workflow: str,
        session: Optional[str] = None,
        user: Optional[str] = None,
        search_depth: str = "basic",
    ) -> None:
        self.feature = feature
        self.workflow = workflow
        self.session = session
        self.user = user
        self.search_depth = search_depth
        self._tool_name: Dict[Any, str] = {}

    def on_llm_end(self, response, *, run_id=None, **kwargs):
        in_tok, out_tok, model = self._extract_usage(response)
        if in_tok or out_tok:
            log_cost(
                "LLM", feature=self.feature, workflow=self.workflow,
                session=self.session, user=self.user, model=model,
                input_tokens=in_tok, output_tokens=out_tok,
                total_tokens=in_tok + out_tok, usd=openai_usd(model, in_tok, out_tok),
            )

    def on_tool_start(self, serialized, input_str, *, run_id=None, **kwargs):
        self._tool_name[run_id] = (serialized or {}).get("name", "") or ""

    def on_tool_end(self, output, *, run_id=None, **kwargs):
        name = self._tool_name.pop(run_id, "")
        low = name.lower()
        if "search" in low or "tavily" in low:
            credits = 2 if self.search_depth == "advanced" else 1
            log_cost(
                "SEARCH", feature=self.feature, workflow=self.workflow,
                session=self.session, user=self.user, provider="tavily",
                depth=self.search_depth, credits=credits, usd=tavily_usd(credits),
            )

    @staticmethod
    def _extract_usage(response) -> tuple:
        """Pull (input_tokens, output_tokens, model) from an LLMResult. Tries the
        chat usage_metadata path first, then the llm_output token_usage path."""
        in_tok = out_tok = 0
        model = "openai"
        try:
            for gens in getattr(response, "generations", []) or []:
                for gen in gens:
                    msg = getattr(gen, "message", None)
                    if msg is None:
                        continue
                    um = getattr(msg, "usage_metadata", None)
                    if um:
                        in_tok += int(um.get("input_tokens", 0) or 0)
                        out_tok += int(um.get("output_tokens", 0) or 0)
                    rm = getattr(msg, "response_metadata", None) or {}
                    model = rm.get("model_name") or rm.get("model") or model
        except Exception:
            pass
        try:
            llmout = getattr(response, "llm_output", None) or {}
            model = llmout.get("model_name") or llmout.get("model") or model
            if not (in_tok or out_tok):
                tu = llmout.get("token_usage") or llmout.get("usage") or {}
                in_tok = int(tu.get("prompt_tokens", 0) or 0)
                out_tok = int(tu.get("completion_tokens", 0) or 0)
        except Exception:
            pass
        return in_tok, out_tok, model
