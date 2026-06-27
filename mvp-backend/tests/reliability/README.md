# Reliability test suite (offline / hermetic)

White-box tests that exercise the reliability strategies behind the activity-research
pipeline — the ones that mitigate the June-24 "0 found" incident (see
`docs/roadmap.md` → *Pre-Launch Hardening*). They use a tempfile `DuckDBStorage` +
injected fakes, so they're deterministic, fast (<2s total), free (no OpenAI/Tavily),
and CI-safe.

| File | Strategy under test | What would break if it regressed |
|---|---|---|
| `test_worker_concurrency.py` | Multi-worker thread pool drains the queue in parallel, bounded by `concurrency` | Head-of-line blocking returns (the June-24 symptom) |
| `test_atomic_claim.py` | `claim_next_queued_run` is exactly-once under thread contention | Two workers process the same run → duplicate candidates / wasted spend |
| `test_sweeper_requeue.py` | Startup sweeper re-queues `running` runs after a crash, leaves terminal runs alone | A restart silently strands in-flight runs |
| `test_idempotent_candidates.py` | Re-running a run replaces (not appends) candidates | Sweeper re-runs would duplicate candidates |
| `test_openai_backoff.py` | `ChatOpenAI(max_retries=…)` retries 429s and recovers | A rate-limit burst from concurrent runs fails runs instead of slowing |
| `test_run_dedup.py` | `get_active_research_run` only matches in-flight runs (per user) | Double-taps pile up extra runs behind each other |

The end-to-end / black-box counterparts live in the nl-harness
(`tests/nl-harness/specs/tier-2/research-dedup.flow.yml`,
`concurrent-enqueue-resilience.flow.yml`). The fault-injection layer (mock OpenAI via
`OPENAI_BASE_URL`, `ctx.fault()`) is the Phase-2 fast-follow tracked in the roadmap.
