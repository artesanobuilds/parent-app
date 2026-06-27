#!/usr/bin/env python3
"""
Load + adversarial chaos hunt against the research pipeline, driven through the
Phase-2 mock OpenAI (free + deterministic — no real OpenAI spend).

Self-orchestrating: starts the mock + a dedicated fault backend (isolated temp
DuckDB), runs a battery of experiments, tears everything down, prints findings.

  python tests/nl-harness/tools/load_and_chaos.py [--conc 5]

Experiments
  E1  load:            N concurrent enqueues — claim integrity, drain time, errors
  E2  cancel-mid-run:  cancel a running run — does the cancel stick, or get clobbered?
  E3  no-exec-timeout: a slow upstream holds a pool slot — is there any cap?
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

HARNESS = Path(__file__).resolve().parents[1]
REPO = HARNESS.parent.parent
BACKEND = REPO / "mvp-backend"
PY = str(BACKEND / ".venv" / "bin" / "python")
MOCK_PORT = 9097
BACKEND_PORT = 8907
MOCK = f"http://127.0.0.1:{MOCK_PORT}"
API = f"http://127.0.0.1:{BACKEND_PORT}"

findings: list[str] = []


def record(sev: str, msg: str) -> None:
    findings.append(f"[{sev}] {msg}")
    print(f"    >> [{sev}] {msg}")


# ── orchestration ───────────────────────────────────────────────────────────

def wait_health(url: str, name: str, timeout=30) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            if httpx.get(url, timeout=2).status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    print(f"ERROR: {name} not healthy at {url}")
    return False


def start_stack(conc: int):
    db_dir = tempfile.mkdtemp()
    mock = subprocess.Popen(
        [PY, str(HARNESS / "mocks" / "mock_openai.py"), "--port", str(MOCK_PORT)],
        stdout=open("/tmp/chaos-mock.log", "w"), stderr=subprocess.STDOUT,
    )
    if not wait_health(f"{MOCK}/health", "mock"):
        raise SystemExit(1)
    env = {
        **os.environ,
        "MVP_DUCKDB_PATH": f"{db_dir}/chaos.duckdb",
        "OPENAI_BASE_URL": f"{MOCK}/v1",
        "OPENAI_API_KEY": "test-key-mock",
        "TAVILY_API_KEY": "test-key-mock",
        "RATE_LIMIT_AUTH_PER_HOUR": "1000000",
        "RESEARCH_WORKER_CONCURRENCY": str(conc),
    }
    backend = subprocess.Popen(
        [PY, "-m", "uvicorn", "app.server:app", "--host", "127.0.0.1", "--port", str(BACKEND_PORT)],
        cwd=str(BACKEND), env=env,
        stdout=open("/tmp/chaos-backend.log", "w"), stderr=subprocess.STDOUT,
    )
    if not wait_health(f"{API}/health", "backend", timeout=40):
        raise SystemExit(1)
    return mock, backend


# ── api helpers (one shared, big-pool, thread-safe client) ──────────────────

CLIENT = httpx.Client(timeout=30, limits=httpx.Limits(max_connections=300, max_keepalive_connections=300))


def fault(mode: str, count=None, latency_ms=0) -> None:
    body = {"mode": mode}
    if count is not None:
        body["count"] = count
    if latency_ms:
        body["latency_ms"] = latency_ms
    CLIENT.post(f"{MOCK}/__fault__", json=body)


def reset_fault() -> None:
    CLIENT.post(f"{MOCK}/__reset__")


def mock_state() -> dict:
    return CLIENT.get(f"{MOCK}/__fault__").json()


def new_user(i: int):
    uid = f"chaos-{i}-{int(time.time()*1000)%100000}"
    r = CLIENT.post(f"{API}/auth/issue-token", json={"user_id": uid})
    r.raise_for_status()
    return uid, r.json()["token"]


def hdr(token):
    return {"Authorization": f"Bearer {token}"}


def enqueue(uid, token):
    return CLIENT.post(f"{API}/research/runs", json={"user_id": uid}, headers=hdr(token))


def get_run(uid, token, run_id):
    return CLIENT.get(f"{API}/research/runs/{run_id}", headers=hdr(token))


def cancel(uid, token, run_id):
    return CLIENT.post(f"{API}/research/runs/{run_id}/cancel", headers=hdr(token))


# ── experiments ─────────────────────────────────────────────────────────────

def e1_load(conc: int, n: int) -> None:
    print(f"\n=== E1: load — {n} concurrent enqueues (pool={conc}) ===")
    reset_fault()
    users = [new_user(i) for i in range(n)]

    def fire(u):
        uid, token = u
        t0 = time.perf_counter()
        r = enqueue(uid, token)
        dt = (time.perf_counter() - t0) * 1000
        return uid, token, r.status_code, (r.json().get("run_id") if r.status_code == 200 else None), dt

    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n) as ex:
        res = list(ex.map(fire, users))
    enqueue_done = time.perf_counter()

    codes = [r[2] for r in res]
    lat = sorted(r[4] for r in res)
    run_ids = [r[3] for r in res if r[3]]
    ok = sum(1 for c in codes if c == 200)
    p50 = lat[len(lat)//2]; p95 = lat[int(len(lat)*0.95)]; mx = lat[-1]
    print(f"    enqueue: {ok}/{n} ok | latency p50={p50:.0f}ms p95={p95:.0f}ms max={mx:.0f}ms | window={1000*(enqueue_done-t_start):.0f}ms")

    if ok != n:
        record("BUG", f"E1: {n-ok}/{n} enqueues did NOT return 200 under load ({[c for c in codes if c!=200][:5]})")
    if len(set(run_ids)) != ok:
        record("BUG", f"E1: distinct run_ids {len(set(run_ids))} != successful enqueues {ok} (claim collision / dup)")

    # drain
    pending = [(u, t, rid) for (u, t, _c, rid, _d) in res if rid]
    drain_start = time.perf_counter()
    stuck = []
    while time.perf_counter() - drain_start < 90:
        statuses = {}
        for uid, token, rid in pending:
            s = get_run(uid, token, rid)
            statuses[rid] = s.json().get("status") if s.status_code == 200 else f"http{s.status_code}"
        terminal = sum(1 for v in statuses.values() if v in ("done", "failed", "canceled"))
        if terminal == len(pending):
            break
        time.sleep(0.5)
    drain = time.perf_counter() - drain_start
    final = {}
    for uid, token, rid in pending:
        final[rid] = get_run(uid, token, rid).json().get("status")
    done = sum(1 for v in final.values() if v == "done")
    failed = sum(1 for v in final.values() if v == "failed")
    other = [v for v in final.values() if v not in ("done",)]
    print(f"    drain: {done}/{len(pending)} done in {drain:.1f}s | failed={failed} | non-done={len(other)}")
    if done != len(pending):
        record("BUG", f"E1: only {done}/{len(pending)} runs reached done under load — non-done={set(other)} (stranded/lost)")
    else:
        print(f"    OK: all {done} runs drained cleanly, claim integrity held at n={n}")
    # cleanup families
    for uid, token, _ in pending:
        CLIENT.delete(f"{API}/family/{uid}", headers=hdr(token))


def e2_cancel_mid_run(conc: int) -> None:
    print(f"\n=== E2: cancel a RUNNING run — does the cancel stick? ===")
    reset_fault()
    fault("slow", latency_ms=6000)  # each model call takes 6s → run stays 'running'
    uid, token = new_user(9001)
    rid = enqueue(uid, token).json()["run_id"]

    # wait until it's actually running (claimed by a worker)
    running = False
    for _ in range(40):
        st = get_run(uid, token, rid).json().get("status")
        if st == "running":
            running = True
            break
        time.sleep(0.2)
    if not running:
        record("INFO", "E2: run never observed 'running' (slow mode may not have engaged) — inconclusive")

    c = cancel(uid, token, rid)
    after_cancel = get_run(uid, token, rid).json().get("status")
    print(f"    cancel returned {c.status_code} {c.json()}; status right after = {after_cancel}")

    # let the in-flight model call finish + the worker complete process_run
    time.sleep(9)
    final = get_run(uid, token, rid).json().get("status")
    print(f"    final status after the run's work finished = {final}")

    if after_cancel == "canceled" and final != "canceled":
        record("BUG", f"E2: cancel CLOBBERED — run regressed from 'canceled' to '{final}'. "
                      f"Cancel is ineffective (work completed) AND a terminal state was overwritten.")
    elif final == "canceled":
        print("    OK: cancel stuck; final stayed 'canceled'")
    reset_fault()
    CLIENT.delete(f"{API}/family/{uid}", headers=hdr(token))


def e3_no_exec_timeout(conc: int) -> None:
    print(f"\n=== E3: slow upstream — is there ANY per-run execution cap? ===")
    reset_fault()
    fault("slow", latency_ms=20000)  # a 20s "hang" on the first model call
    uid, token = new_user(9002)
    rid = enqueue(uid, token).json()["run_id"]
    # observe how long the run stays non-terminal — a backend exec-timeout would
    # cap it; absence means a wedged upstream holds the slot for the full duration.
    t0 = time.time()
    running_for = 0.0
    for _ in range(60):
        st = get_run(uid, token, rid).json().get("status")
        if st in ("done", "failed", "canceled"):
            break
        running_for = time.time() - t0
        time.sleep(1)
    print(f"    run held non-terminal for ~{running_for:.0f}s against a 20s upstream stall")
    if running_for >= 15:
        record("GAP", "E3: no per-run execution timeout — a slow/wedged upstream occupies a worker "
                      "slot for the full upstream duration (here ~20s) with no backend cap. A truly "
                      "hung upstream (no client timeout hit) would hold the slot indefinitely, "
                      "starving the pool. (Roadmap: per-run execution timeout + reaper.)")
    reset_fault()
    time.sleep(1)
    CLIENT.delete(f"{API}/family/{uid}", headers=hdr(token))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conc", type=int, default=5)
    args = ap.parse_args()

    mock, backend = start_stack(args.conc)
    try:
        e1_load(args.conc, 30)
        e1_load(args.conc, 60)
        e2_cancel_mid_run(args.conc)
        e3_no_exec_timeout(args.conc)
    finally:
        for p in (backend, mock):
            try:
                p.send_signal(signal.SIGTERM)
            except Exception:
                pass
        time.sleep(1)

    # scan backend log for unexpected errors surfaced during the hunt
    try:
        log = Path("/tmp/chaos-backend.log").read_text()
        bad = [ln for ln in log.splitlines() if ("Traceback" in ln or "claim failed" in ln or "ERROR" in ln)]
        if bad:
            record("BUG", f"E*: backend log shows {len(bad)} error line(s) during the hunt: {bad[:3]}")
    except Exception:
        pass

    print("\n" + "=" * 64)
    print("FINDINGS")
    print("=" * 64)
    if not findings:
        print("  (none — system held up clean across load + chaos)")
    for f in findings:
        print("  " + f)


if __name__ == "__main__":
    main()
