# Fault injection (NL-Harness Playbook §4.8, Phase 2)

Lets flow tests make a real dependency **fail** as a first-class scenario, then
assert graceful degradation + recovery — deterministically and free (no real
OpenAI spend). This is the parent-app port of the playbook's `ctx.fault()` model
(which drove Toxiproxy + mock-service layer).

## Pieces
- **`mock_openai.py`** — a stdlib mock of OpenAI's `/v1/chat/completions` (stream +
  non-stream). In `ok` mode it returns a *no-tool-call* completion, which ends the
  deepagents research loop in one turn → a real run reaches `done` deterministically
  (0 candidates; we test resilience, not discovery). A `/__fault__` control plane
  toggles failure modes: `ok | rate_limit (429) | error (500) | down (503) | slow`,
  with an optional `count` (fault N calls then self-heal).
- **`../lib/fault.py`** — the `FaultController` exposed as `flow_ctx.fault`.
- **`../tools/run-fault-flows.sh`** — brings up the mock + a dedicated backend
  pointed at it (`OPENAI_BASE_URL`, isolated temp DuckDB) and runs the fault specs.

## Run
```bash
tests/nl-harness/tools/run-fault-flows.sh          # all fault flows
tests/nl-harness/tools/run-fault-flows.sh -v -k backoff
```

## Write a fault flow
```python
def test_x(flow_ctx, new_parent):
    if not flow_ctx.fault.available:
        pytest.skip("run via tools/run-fault-flows.sh")
    flow_ctx.register_cleanup("reset", lambda: flow_ctx.fault.reset())

    flow_ctx.fault("openai", "rate_limit", count=2)   # next 2 model calls 429
    # ... POST /research/runs, wait_for(status==done), assert it survived
    assert flow_ctx.fault.state()["fault_count"] >= 2   # the faults were served
```
`flow_ctx.fault.available` is False unless `OPENAI_MOCK_CONTROL_URL` is set, so these
flows skip cleanly in the normal harness and only run under the orchestration script.

## Covered today
- `research-backoff-recovery` — 429 burst → run still completes (backoff retried)
- `research-openai-outage` — hard outage → run ends `failed` gracefully, no 5xx cascade
- `research-worker-saturation` — N>pool concurrent runs → all drain to `done`

See `docs/roadmap.md` → *Pre-Launch Hardening* for what's deferred (voice-EL outage,
stale-run reaper, per-run execution timeout).
