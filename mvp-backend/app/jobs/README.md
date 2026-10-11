# Background job attempts

Research and onboarding warmup retain their existing tables and public states.
Migration 26 adds `attempt_token`, `deadline_at`, and `heartbeat_at` columns. Only
claim results expose these internally; poll/list/SSE payloads are unchanged.
No new table or parquet export is introduced.

A claim atomically assigns a fresh token and a total deadline. Restart recovery
requeues unfinished rows and clears their token, retaining the original deadline.
Every progress write, publication, and worker finalization validates the current
token, running state, and deadline under the connection lock. Family deletion or
reset removes the job row in the existing cascade, immediately invalidating its
attempt. Old workers cannot recreate family data through their fenced handles.

Research keeps candidates in memory until publication. Candidate replacement and
terminal success commit in the same DuckDB transaction. A cancellation racing
publication therefore observes either a committed result or a canceled run with
no newly published candidates. The cancel route retains its existing response.
Research defaults to a ten-minute total budget. Retries and backoff consume that
budget, and each provider call is limited to the remaining budget and existing
per-call limit. An independent one-second reaper terminalizes expired jobs even
when the worker pool is busy.

The production research graph uses native async model/Tavily calls, cancellation
polling (at most 200 ms between checks), and model/tool dispatch guards. Its
DeepAgents general-purpose subagent explicitly receives the same middleware;
callbacks guard internal model work such as summarization. OpenAI copies update
actual SDK transport options, not only the ChatOpenAI Pydantic fields. SDK retries
are disabled for guarded calls; middleware owns bounded retries.

Warmup keeps its four independent steps and `done` result with `failed_steps`
when a step fails. Each step receives its own context copy and fenced storage
handle. A timed-out step cannot later write a nudge, activity, or account, or
mutate a following step's context. A semaphore bounds outstanding step futures
at twice worker concurrency. If all slots remain occupied, following steps fail
quickly and the parent can proceed. The family step reads the already-durable
profile seed; it no longer performs an unrelated global snapshot flush.

## Limits

Cancellation is cooperative. Native async provider requests are canceled and
joined, but a request already accepted by a vendor may still incur cost. Python
threads are not killed: an uncooperative injected research function retains its
worker slot, and an uncooperative warmup step retains its executor slot until it
returns. No unbounded queue of timed-out replacements is created. Process
isolation is required for a hard wall-clock kill of arbitrary code; this change
does not implement it. The reaper expires durable/public state independently of
occupied worker slots. It still needs a responsive database; a thread stuck
inside a storage transaction can hold the connection lock until it returns.

This is a single-process DuckDB design. Heartbeat timestamps are diagnostic;
expiry uses the fixed total deadline, not a renewable lease. Email/calendar sync
retain their existing deterministic workflows and scheduling. No REST schema,
framework version, or client change is required. Migration deployment still needs
an explicitly authorized backup and the repository deploy runbook.

## Verification

`tests/test_job_attempt_fencing.py` exercises cancellation and late publication,
superseded claims, rollback after candidate insertion, live-worker deadline
reaping, restart budget preservation, late warmup writes, saturation admission,
async cancellation/join, SDK retry configuration, a real fake-model DeepAgents
run, and populated migration replay. Existing research/warmup contract suites
continue to exercise public state and SSE shapes without vendor access.
