#!/usr/bin/env python3
"""Synthetic latency benchmark for the two ElevenLabs Custom-LLM endpoints.

ElevenLabs does STT, turn-taking and TTS; the ONLY part of a voice turn we own
is the chat-completions stream it POSTs to us. So "voice felt slow" is almost
always a question about these two endpoints, and the number that matters is not
total duration — it's **time to first content delta**, because ElevenLabs can't
start speaking until real text arrives. This script calls both endpoints exactly
the way ElevenLabs does (same auth header, same `elevenlabs_extra_body` keys,
same SSE stream consumption) and records that number over N repetitions so a
change made in week 2 is comparable to week 1.

    kid    → POST /v1/chat/completions          (app/convai_endpoint.py)
    parent → POST /v1/parent/chat/completions   (app/parent_convai_endpoint.py)

Usage:
    source .venv/bin/activate
    python tools/voice_bench.py                       # localhost:8904, both endpoints, 3 reps
    python tools/voice_bench.py --endpoint parent --reps 5
    python tools/voice_bench.py --prod                # requires the prod secret in the env
    python tools/voice_bench.py --user-id bench-alt --kid-name Robin

REAL COST, REAL WRITES. Every non-stub turn runs the LangGraph agent against
OpenAI (money) and, on the kid endpoint, appends rows to that kid's transcript.
That is why the user id defaults to an obviously synthetic one and why any id
without "bench" in it is refused unless you pass --allow-nonsynthetic-user.
Never point this at a beta parent's id.

A kid agent that the parent hasn't reviewed/enabled yet short-circuits to a
canned "I'm not ready to chat yet" string in ~0ms — a beautiful benchmark
number that measures nothing. Those turns are detected, reported as STUB, and
excluded from the percentiles. To benchmark the real kid path, enable the
synthetic kid's agent first.

Output (tools/voice_bench_results/):
    voice_bench_summary.csv   one appended row per endpoint per run — the trend line
    run-<utc-timestamp>.csv   every individual turn from that run (detail/forensics)
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import httpx
except ImportError:  # pragma: no cover - operator error, not a code path
    sys.exit("httpx is not installed — run this inside the backend venv: source .venv/bin/activate")


REPO_BACKEND = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_BACKEND / "tools" / "voice_bench_results"
SUMMARY_CSV = RESULTS_DIR / "voice_bench_summary.csv"

LOCAL_URL = "http://127.0.0.1:8904"
PROD_URL = "https://mvp-backend-production-8678.up.railway.app"

# Obviously-synthetic defaults. The guard in main() keys off "bench".
DEFAULT_USER_ID = "bench-synthetic-voice-user"
DEFAULT_KID_NAME = "BenchBuddy"

# Realistic turns, one set per speaker — the kid endpoint is a child talking to
# their companion, the parent endpoint is a parent talking to the coach. Kept
# deliberately benign: a moderation-flagged kid turn short-circuits the agent
# and would silently poison the sample.
PARENT_PROMPTS = [
    "My six year old melts down every single morning about getting dressed. What do I do?",
    "How much screen time is actually okay for a nine year old on a school night?",
    "My kids fight constantly in the car and I lose it by the time we get there.",
    "She says nobody wants to play with her at recess and I don't know what to say back.",
    "Bedtime takes ninety minutes now. Where do I even start?",
]
KID_PROMPTS = [
    "What's the biggest animal that ever lived?",
    "I had a bad day at school today.",
    "Can you tell me a joke about dinosaurs?",
    "Why do people get nervous before a test?",
    "What should I build with my LEGOs?",
]

# Canned short-circuit replies from either endpoint. A turn whose entire output
# is one of these never reached the LLM, so its latency is meaningless — we
# count it, shout about it, and keep it out of the percentiles.
STUB_MARKERS = (
    "I'm not ready to chat yet",              # kid agent not parent-enabled
    "Your grown-up needs to check in",        # crisis lock
    "Hmm, let's try a different question",    # moderation blocked the input
    "I'm really glad you told me",            # crisis route
    "Something went wrong. Let's try again.",  # kid endpoint exception handler
    "I hit a snag on my end",                 # parent endpoint exception handler
)


# ── Endpoint definitions ─────────────────────────────────────────────
#
# extra_body mirrors what each endpoint actually reads out of
# `elevenlabs_extra_body`. The kid endpoint needs kid_name on top of user_id
# (it resolves a per-kid agent + moderation context); the parent endpoint does
# not. Getting these wrong yields a 400 or, worse, the connection-test stub
# stream — both of which this script surfaces rather than averaging in.

@dataclass(frozen=True)
class Endpoint:
    key: str
    path: str
    prompts: List[str]
    extra_body: Callable[[str, str, str], Dict[str, Any]]


ENDPOINTS: Dict[str, Endpoint] = {
    "kid": Endpoint(
        key="kid",
        path="/v1/chat/completions",
        prompts=KID_PROMPTS,
        extra_body=lambda user_id, kid_name, thread_id: {
            "user_id": user_id,
            "kid_name": kid_name,
            "thread_id": thread_id,
        },
    ),
    "parent": Endpoint(
        key="parent",
        path="/v1/parent/chat/completions",
        prompts=PARENT_PROMPTS,
        extra_body=lambda user_id, kid_name, thread_id: {
            "user_id": user_id,
            "thread_id": thread_id,
        },
    ),
}


@dataclass
class TurnResult:
    endpoint: str
    prompt_idx: int
    prompt: str
    rep: int
    status: str                      # ok | stub | error
    http_status: Optional[int] = None
    ttfb_ms: Optional[float] = None   # first byte of the SSE body
    ttfc_ms: Optional[float] = None   # first delta carrying non-empty content
    total_ms: Optional[float] = None  # request start → stream exhausted
    content_chars: int = 0
    deltas: int = 0
    tool_calls: int = 0
    error: str = ""

    @property
    def counts(self) -> bool:
        """Only clean, LLM-backed turns belong in the percentiles."""
        return self.status == "ok"


# ── Secret loading ───────────────────────────────────────────────────

def load_secret() -> str:
    """ELEVENLABS_CONVAI_SECRET from the environment, else mvp-backend/.env.

    The env wins so `--prod` runs can be given the prod secret inline without
    editing the local .env (they are different secrets).
    """
    secret = os.getenv("ELEVENLABS_CONVAI_SECRET", "").strip()
    if secret:
        return secret

    env_path = REPO_BACKEND / ".env"
    if env_path.exists():
        try:
            from dotenv import dotenv_values  # backend dep; avoids mutating os.environ
            secret = (dotenv_values(env_path).get("ELEVENLABS_CONVAI_SECRET") or "").strip()
        except ImportError:
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("ELEVENLABS_CONVAI_SECRET="):
                    secret = line.split("=", 1)[1].split("#", 1)[0].strip().strip("'\"")
                    break
    return secret


def git_short_sha() -> str:
    """Short SHA for the trend row, cheaply. Never fatal — a bench that can't
    run outside a checkout is a bench nobody runs."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_BACKEND, capture_output=True, text=True, timeout=2,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:  # noqa: BLE001
        pass
    return "unknown"


# ── One turn ─────────────────────────────────────────────────────────

def run_turn(
    client: httpx.Client,
    base_url: str,
    ep: Endpoint,
    secret: str,
    prompt: str,
    prompt_idx: int,
    rep: int,
    user_id: str,
    kid_name: str,
    thread_id: str,
) -> TurnResult:
    """POST one OpenAI-shaped turn and consume the SSE stream token by token.

    Timing origin is the moment we hand the request to httpx, matching what
    ElevenLabs experiences. We iterate the body (never .read()/.text) so
    first-byte and first-content are real wall-clock observations and not
    artifacts of buffering the whole response.
    """
    res = TurnResult(endpoint=ep.key, prompt_idx=prompt_idx, prompt=prompt, rep=rep, status="error")

    body = {
        # ElevenLabs sends its own model string; ours is ignored server-side
        # (the agent picks the model) but we send one so the shape stays honest.
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "elevenlabs_extra_body": ep.extra_body(user_id, kid_name, thread_id),
    }
    headers = {
        # Both endpoints accept either header; ElevenLabs' console sends the
        # bearer form, so that's what we exercise.
        "Authorization": f"Bearer {secret}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    url = base_url.rstrip("/") + ep.path
    t0 = time.perf_counter()
    try:
        with client.stream("POST", url, json=body, headers=headers) as resp:
            res.http_status = resp.status_code
            if resp.status_code >= 300:
                resp.read()
                res.error = _explain_http_error(resp)
                return res

            buf = ""
            text_out: List[str] = []
            for chunk in resp.iter_text():
                if res.ttfb_ms is None:
                    res.ttfb_ms = (time.perf_counter() - t0) * 1000
                buf += chunk
                # SSE frames are separated by a blank line; hold the trailing
                # partial frame until its terminator arrives.
                while "\n\n" in buf:
                    frame, buf = buf.split("\n\n", 1)
                    for line in frame.splitlines():
                        line = line.strip()
                        if not line.startswith("data:"):
                            continue  # ": keepalive" comments and stray lines
                        payload = line[5:].strip()
                        if payload == "[DONE]":
                            continue
                        try:
                            obj = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                        delta = (obj.get("choices") or [{}])[0].get("delta") or {}
                        if delta.get("tool_calls"):
                            res.tool_calls += 1
                        content = delta.get("content")
                        if not content:
                            continue  # keepalive / tool-only / empty delta
                        res.deltas += 1
                        res.content_chars += len(content)
                        text_out.append(content)
                        if res.ttfc_ms is None:
                            res.ttfc_ms = (time.perf_counter() - t0) * 1000

            res.total_ms = (time.perf_counter() - t0) * 1000
            full = "".join(text_out)
            res.status = "stub" if _is_stub(full) else "ok"
            return res

    except httpx.ConnectError:
        res.error = (
            f"nothing listening at {base_url} — start the backend first:\n"
            "    source .venv/bin/activate && uvicorn app.server:app --reload --port 8904"
        )
        return res
    except httpx.ReadTimeout:
        res.error = f"read timeout after {client.timeout.read}s (agent hung or model is cold)"
        return res
    except httpx.HTTPError as exc:
        res.error = f"{type(exc).__name__}: {exc}"
        return res


def _is_stub(text: str) -> bool:
    head = text.strip()[:120]
    return any(marker in head for marker in STUB_MARKERS)


def _explain_http_error(resp: httpx.Response) -> str:
    """Turn a non-2xx into something the operator can act on. A traceback here
    would just be noise — every failure mode is a config mistake."""
    detail = resp.text.strip()[:200]
    if resp.status_code == 401:
        return (
            "401 invalid secret — ELEVENLABS_CONVAI_SECRET does not match the server's. "
            "Local: check mvp-backend/.env. Prod: the prod value differs; pass it inline "
            "(ELEVENLABS_CONVAI_SECRET=... python tools/voice_bench.py --prod)."
        )
    if resp.status_code == 400:
        return f"400 bad request — elevenlabs_extra_body is missing a key the endpoint needs: {detail}"
    if resp.status_code == 429:
        return "429 rate limited — back off, or lower --reps."
    if resp.status_code in (502, 503, 504):
        return f"{resp.status_code} upstream/gateway error — server may be restarting: {detail}"
    return f"HTTP {resp.status_code}: {detail}"


# ── Stats + reporting ────────────────────────────────────────────────

def pct(values: List[float], p: float) -> Optional[float]:
    """Nearest-rank percentile. At the sample sizes this script produces (often
    <20 turns) interpolation invents precision that isn't there, so we report an
    observed value instead."""
    if not values:
        return None
    s = sorted(values)
    idx = max(0, min(len(s) - 1, math.ceil(p / 100.0 * len(s)) - 1))
    return s[idx]


@dataclass
class Summary:
    endpoint: str
    turns: List[TurnResult] = field(default_factory=list)

    def _series(self, attr: str) -> List[float]:
        return [getattr(t, attr) for t in self.turns if t.counts and getattr(t, attr) is not None]

    @property
    def ok(self) -> int:
        return sum(1 for t in self.turns if t.status == "ok")

    @property
    def stubs(self) -> int:
        return sum(1 for t in self.turns if t.status == "stub")

    @property
    def failed(self) -> int:
        return sum(1 for t in self.turns if t.status == "error")

    def stat(self, attr: str, p: float) -> Optional[float]:
        return pct(self._series(attr), p)

    def mean(self, attr: str) -> Optional[float]:
        s = self._series(attr)
        return statistics.fmean(s) if s else None


def _fmt(ms: Optional[float]) -> str:
    return f"{ms:,.0f}" if ms is not None else "—"


def print_report(summaries: List[Summary], base_url: str, sha: str) -> None:
    print()
    print(f"  voice bench · {base_url} · git {sha}")
    print("  ttfb = first SSE byte | ttfc = first spoken-text delta (the one that matters) | total = stream end")
    print()
    header = f"  {'endpoint':<8} {'ok':>3} {'stub':>4} {'err':>3} | " \
             f"{'ttfb p50':>9} {'ttfb p95':>9} | {'ttfc p50':>9} {'ttfc p95':>9} | " \
             f"{'total p50':>10} {'total p95':>10}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for s in summaries:
        print(
            f"  {s.endpoint:<8} {s.ok:>3} {s.stubs:>4} {s.failed:>3} | "
            f"{_fmt(s.stat('ttfb_ms', 50)):>9} {_fmt(s.stat('ttfb_ms', 95)):>9} | "
            f"{_fmt(s.stat('ttfc_ms', 50)):>9} {_fmt(s.stat('ttfc_ms', 95)):>9} | "
            f"{_fmt(s.stat('total_ms', 50)):>10} {_fmt(s.stat('total_ms', 95)):>10}"
        )
    print("  (milliseconds)")

    for s in summaries:
        if s.stubs:
            print(
                f"\n  ⚠ {s.endpoint}: {s.stubs} turn(s) returned a canned short-circuit reply and were "
                f"EXCLUDED from the numbers above."
            )
            if s.endpoint == "kid":
                print("    Most likely the synthetic kid's agent isn't parent-enabled yet, so no LLM ran.")
        for t in s.turns:
            if t.status == "error":
                print(f"\n  ✗ {s.endpoint} rep {t.rep} p{t.prompt_idx}: {t.error}")
                break  # one representative failure per endpoint; they repeat


# ── CSV output ───────────────────────────────────────────────────────

SUMMARY_FIELDS = [
    "ts_utc", "git_sha", "target", "base_url", "endpoint",
    "user_id", "prompts", "reps", "turns_ok", "turns_stub", "turns_failed",
    "ttfb_p50_ms", "ttfb_p95_ms", "ttfc_p50_ms", "ttfc_p95_ms", "ttfc_mean_ms",
    "total_p50_ms", "total_p95_ms", "content_chars_p50", "deltas_p50", "note",
]

TURN_FIELDS = [
    "ts_utc", "git_sha", "base_url", "endpoint", "prompt_idx", "rep", "status",
    "http_status", "ttfb_ms", "ttfc_ms", "total_ms", "content_chars", "deltas",
    "tool_calls", "prompt", "error",
]


def _round(v: Optional[float]) -> str:
    return "" if v is None else f"{v:.1f}"


def write_csvs(
    summaries: List[Summary], *, ts: str, sha: str, base_url: str, target: str,
    user_id: str, reps: int, note: str, results_dir: Path,
) -> tuple[Path, Path]:
    results_dir.mkdir(parents=True, exist_ok=True)
    summary_path = results_dir / SUMMARY_CSV.name
    run_path = results_dir / f"run-{ts.replace(':', '').replace('-', '')}.csv"

    # Append-only trend file. A header mismatch means the schema moved under an
    # old file — refuse rather than silently writing misaligned columns.
    existing_header: Optional[List[str]] = None
    if summary_path.exists() and summary_path.stat().st_size > 0:
        with summary_path.open(newline="") as fh:
            existing_header = next(csv.reader(fh), None)
    if existing_header is not None and existing_header != SUMMARY_FIELDS:
        sys.exit(
            f"{summary_path} has an older column set. Move it aside "
            f"(e.g. mv {summary_path.name} {summary_path.stem}-v1.csv) and re-run."
        )

    with summary_path.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=SUMMARY_FIELDS)
        if existing_header is None:
            w.writeheader()
        for s in summaries:
            w.writerow({
                "ts_utc": ts, "git_sha": sha, "target": target, "base_url": base_url,
                "endpoint": s.endpoint, "user_id": user_id,
                "prompts": len({t.prompt_idx for t in s.turns}), "reps": reps,
                "turns_ok": s.ok, "turns_stub": s.stubs, "turns_failed": s.failed,
                "ttfb_p50_ms": _round(s.stat("ttfb_ms", 50)),
                "ttfb_p95_ms": _round(s.stat("ttfb_ms", 95)),
                "ttfc_p50_ms": _round(s.stat("ttfc_ms", 50)),
                "ttfc_p95_ms": _round(s.stat("ttfc_ms", 95)),
                "ttfc_mean_ms": _round(s.mean("ttfc_ms")),
                "total_p50_ms": _round(s.stat("total_ms", 50)),
                "total_p95_ms": _round(s.stat("total_ms", 95)),
                "content_chars_p50": _round(pct([float(t.content_chars) for t in s.turns if t.counts], 50)),
                "deltas_p50": _round(pct([float(t.deltas) for t in s.turns if t.counts], 50)),
                "note": note,
            })

    with run_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=TURN_FIELDS)
        w.writeheader()
        for s in summaries:
            for t in s.turns:
                w.writerow({
                    "ts_utc": ts, "git_sha": sha, "base_url": base_url, "endpoint": t.endpoint,
                    "prompt_idx": t.prompt_idx, "rep": t.rep, "status": t.status,
                    "http_status": t.http_status if t.http_status is not None else "",
                    "ttfb_ms": _round(t.ttfb_ms), "ttfc_ms": _round(t.ttfc_ms),
                    "total_ms": _round(t.total_ms), "content_chars": t.content_chars,
                    "deltas": t.deltas, "tool_calls": t.tool_calls,
                    "prompt": t.prompt, "error": t.error.replace("\n", " ")[:200],
                })

    return summary_path, run_path


# ── CLI ──────────────────────────────────────────────────────────────

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Latency benchmark for the ElevenLabs Custom-LLM endpoints (kid + parent).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Each non-stub turn costs real OpenAI tokens. Keep --reps modest.",
    )
    target = p.add_mutually_exclusive_group()
    target.add_argument("--prod", action="store_true", help=f"target {PROD_URL}")
    target.add_argument("--base-url", default=None, help=f"explicit base URL (default {LOCAL_URL})")
    p.add_argument("--endpoint", choices=["kid", "parent", "both"], default="both")
    p.add_argument("--user-id", default=DEFAULT_USER_ID,
                   help=f"THROWAWAY user id (default {DEFAULT_USER_ID}) — never a beta parent's")
    p.add_argument("--kid-name", default=DEFAULT_KID_NAME, help=f"kid endpoint only (default {DEFAULT_KID_NAME})")
    p.add_argument("--thread-id", default=None,
                   help="conversation thread (default: fresh per run, so memory growth doesn't skew the trend)")
    p.add_argument("--reps", type=int, default=3, help="repetitions per prompt (default 3)")
    p.add_argument("--prompts", type=int, default=len(PARENT_PROMPTS),
                   help=f"how many of the built-in prompts to use (max {len(PARENT_PROMPTS)})")
    p.add_argument("--timeout", type=float, default=120.0, help="per-turn read timeout, seconds (default 120)")
    p.add_argument("--no-warmup", action="store_true",
                   help="keep the first (cold agent-construction) turn in the sample")
    p.add_argument("--note", default="", help="free-text label stored on the CSV row (e.g. 'after prompt trim')")
    p.add_argument("--results-dir", default=str(RESULTS_DIR), help=argparse.SUPPRESS)
    p.add_argument("--no-csv", action="store_true", help="print only; don't touch the results dir")
    p.add_argument("--allow-nonsynthetic-user", action="store_true",
                   help="override the guard that requires 'bench' in --user-id")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    base_url = PROD_URL if args.prod else (args.base_url or LOCAL_URL)
    target = "prod" if base_url == PROD_URL else ("local" if base_url == LOCAL_URL else "custom")

    # The one guard that matters: this script writes transcript rows and burns
    # tokens under whatever id it's given. CLAUDE.md's prod rule is "never touch
    # real users' data" — enforce it here rather than trusting the operator's
    # shell history.
    if "bench" not in args.user_id.lower() and not args.allow_nonsynthetic_user:
        return _fail(
            f"--user-id '{args.user_id}' doesn't look synthetic (no 'bench' in it).\n"
            "This benchmark writes messages and spends tokens under that id. If you really\n"
            "mean it, re-run with --allow-nonsynthetic-user."
        )

    secret = load_secret()
    if not secret:
        return _fail(
            "ELEVENLABS_CONVAI_SECRET is not set.\n"
            "  local: add it to mvp-backend/.env (see env.example)\n"
            "  prod : ELEVENLABS_CONVAI_SECRET=<prod value> python tools/voice_bench.py --prod"
        )

    keys = ["kid", "parent"] if args.endpoint == "both" else [args.endpoint]
    n_prompts = max(1, min(args.prompts, len(PARENT_PROMPTS)))
    reps = max(1, args.reps)
    thread_id = args.thread_id or f"bench-{uuid.uuid4().hex[:8]}"
    sha = git_short_sha()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"[bench] {base_url} · endpoints={','.join(keys)} · {n_prompts} prompts × {reps} reps "
          f"· user={args.user_id} · thread={thread_id}")

    summaries: List[Summary] = []
    # connect timeout stays short (a dead server should fail fast); read timeout
    # is long because a real agent turn legitimately takes tens of seconds.
    timeout = httpx.Timeout(connect=10.0, read=args.timeout, write=30.0, pool=10.0)
    with httpx.Client(timeout=timeout) as client:
        for key in keys:
            ep = ENDPOINTS[key]
            summary = Summary(endpoint=key)

            if not args.no_warmup:
                # First turn of a process pays agent construction, prompt
                # synthesis and connection setup. Real voice sessions pay it
                # once; averaging it into every run makes the trend line noise.
                warm = run_turn(client, base_url, ep, secret, ep.prompts[0], 0, 0,
                                args.user_id, args.kid_name, thread_id)
                print(f"  {key}: warmup {_fmt(warm.ttfc_ms)}ms to first content ({warm.status})")
                if warm.status == "error":
                    print(f"  {key}: {warm.error}")
                    summary.turns.append(warm)
                    summaries.append(summary)
                    continue

            for rep in range(1, reps + 1):
                for idx in range(n_prompts):
                    t = run_turn(client, base_url, ep, secret, ep.prompts[idx], idx, rep,
                                 args.user_id, args.kid_name, thread_id)
                    summary.turns.append(t)
                    mark = {"ok": "·", "stub": "s", "error": "x"}[t.status]
                    print(f"  {key} rep{rep} p{idx} {mark} ttfc={_fmt(t.ttfc_ms)}ms "
                          f"total={_fmt(t.total_ms)}ms chars={t.content_chars}")
            summaries.append(summary)

    print_report(summaries, base_url, sha)

    if not args.no_csv:
        summary_path, run_path = write_csvs(
            summaries, ts=ts, sha=sha, base_url=base_url, target=target,
            user_id=args.user_id, reps=reps, note=args.note,
            results_dir=Path(args.results_dir),
        )
        print(f"\n  trend  → {summary_path}")
        print(f"  detail → {run_path}")

    # Non-zero only when nothing usable came back — a bench that exits 1 on a
    # single flaky turn can't be wired into anything.
    return 0 if any(s.ok for s in summaries) else 1


def _fail(msg: str) -> int:
    print(f"\n[bench] {msg}\n", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
