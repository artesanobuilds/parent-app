# Roadmap

Living list of next-up work. Order is a rough priority, not a commitment. Items move to `docs/history/NNN.md` when shipped.

## Vertical Expansion — One Agent, Five Doors + Watchlist + Public Docs (2026-07-11, SHIPPED — see `docs/history/009.md`)

All phases (V1–V5 verticals, registration-window watchlist, illustrated public docs, full telemetry + 4 Grafana alert rules) are **LIVE in prod**. Ship record: `docs/history/009.md`. What remains:

- **TestFlight the iOS 1.66/80 build** — prod backend already serves the five-doors contract; the beta group is still on the pre-doors build.
- **School door flag decision.** `FLAG_VERTICAL_V4_SCHOOL` is deliberately unset (door dark; organic school_event items + ingest still work). Light it when the school-life episode is ready — fall (Aug–Sep) is the natural moment.
- **PostHog console flags** for the verticals (`vertical-v2-extracurriculars`, `vertical-v5-trips`, later v4) to replace the `FLAG_*` env overrides — enables gradual rollout/experiments; env kill-switch keeps working regardless.
- **Watchlist GA gate (binding, from the plan):** beyond pilot metros only after the miss-detector alert (`watchlist_windows_missed_ratio > 0`, live) runs clean through one real registration season — judged from the Watchlist-SLO dashboard row.
- **Kid PIN: wire up or remove.** Found during docs screenshots: the PIN system is server-complete but iOS-orphaned (`setKidPin` + the picker's PIN prompt exist with zero callers, nothing sends `kid_pin`) — and the server check is default-closed, so a kid WITH a pin set gets a generic error on every message. Harmless today (no UI can set a pin); decide before any UI can. Subsumes the older "kid PIN brute-force lockout" item if the answer is "remove".
- **Deferred from the plan (small):** Gmail school-domain allowlist opt-in for ingest; board-card chain-progress slot ("2 of 3 done"); multi-turn golden cases; tool-docstring token trim (goldens-gated).

## Architectural Infra — Auth + Analytics/Flags + Security Hardening (2026-07, plan CLOSED)

The infra buildout plan (`~/.claude/plans/i-want-to-start-humble-floyd.md`) is **closed** — Phases 1–3 shipped and are LIVE in prod. Setup docs: `setup/auth-setup.md`, `setup/security-hardening-setup.md`, `setup/analytics-posthog-setup.md`. Remaining items below folded into this roadmap so the plan can rest.

### ✅ Shipped + LIVE in prod
- **Phase 1 — Security quick wins.** CMS admin cookie-session auth (`VITE_ADMIN_TOKEN` removed from the browser bundle), 404-not-403 BOLA sweep, `app/security_headers.py` middleware, `delete_family` purges parquet, LLM tool-scoping guard test, gitleaks allowlist, env catalog. `ADMIN_TOKEN` rotated.
- **Phase 2 — Auth hardening.** Native Apple + Google Sign-In (login, not just Gmail/Calendar), JWT HS256 access + rotating refresh tokens with reuse-detection, `user_accounts`/`auth_identities`/`refresh_tokens` tables, dual-accept `current_user` (zero call-site churn), `has_profile` routing (returning users skip onboarding on any device), legacy-account claim + admin safety net (`/admin/auth/link-legacy`, `/admin/auth/migration-status`). First founder migrated in prod. iOS shipped via TestFlight.
- **Phase 3 — PostHog analytics + flags + experiments.** Cloud US project 505309, $0 billing cap, privacy-first (no autocapture/replay, opaque `analytics_id`, strict allowlist + PII denylist, person-deletion wired into `delete_family`). Backend `_track` call sites across the funnel; dashboard (posthog-js) + iOS (posthog-ios, consent-gated) clients. **Full iOS event coverage** (2026-07-10): every-screen `screen_viewed` via a `View.trackScreen()` modifier, `chat_opened {agent_kind}`, kid+parent `voice_session_ended {duration_s}`.

### Yet to do (carried over from the closed plan)
- **Phase 3 console tail (Miguel, PostHog UI).** Create the 3 feature flags — `kid_chat_disabled`, `research_enabled`, `email_sync_enabled` — in the PostHog console (until then `flags.is_enabled` returns the code default; the `FLAG_<KEY>` env override already works deploy-free). Configure Experiments once flags flow.
- **Phase 4 — At-rest encryption (own phase; prod-data risk).** `DUCKDB_ENCRYPTION_KEY` → in-memory connect + `ATTACH … (ENCRYPTION_KEY ?)` with a one-time plaintext→encrypted boot upgrade; parquet snapshot encryption (`PRAGMA add_parquet_key` + `ENCRYPTION_CONFIG`) with per-file plaintext fallback for pre-migration snapshots. Separate key from `INTEGRATION_ENC_KEY`; "lose key = lose volume" documented. Verify: `tests/test_duckdb_encryption.py` (roundtrip, upgrade, mixed bootstrap, drift tolerance) + staging rehearsal on a prod-volume copy; deploy = explicit auth + **volume snapshot first**.
- **Phase 5 — Security CI (needs GitHub remote — none today).** `.github/workflows/security.yml` (pip-audit, bandit, semgrep, gitleaks, osv-scanner, trivy image), `ci.yml` (pytest + both tsc/builds so the Phase 1–3 guard tests actually run), `dependabot.yml`. Enable Dependabot alerts + secret-scanning push protection + CodeQL after pushing.
- **Retire legacy auth (post-migration, trigger = `migration-status` `unclaimed` empties or +30 days).** T2: `AUTH_ISSUE_TOKEN_ENABLED=0` (issue-token → 410); then `AUTH_LEGACY_TOKENS_ENABLED=0` (JWT-only `current_user`); then delete the dead code (issue-token endpoint, `issue/lookup/revoke_auth_token`, `auth_tokens` table, iOS `AuthService.obtainToken` + legacy branches, dashboard user_id login, the `legacy_*` claim path). Update root CLAUDE.md's prod-debugging playbook (the issue-token-as-any-user read trick dies → admin single-user export). Existing in-place-update users get the gentle non-blocking "Secure your account" nudge until then.
- **5 known claim-path bugs (deferred — only 1 founder left, manual cleanup acceptable).** Documented in memory `project_auth_v2` KNOWN CLAIM-PATH BUGS.
- **Deferred / separate plans:** COPPA/compliance workstream (parent VPC gate for kid-chat, written children's-data security program, retention policy, DPAs, App Store privacy labels — deadline already passed, schedule soon); Logto self-hosted adoption at open-beta/MFA trigger (migration = import `auth_identities` + `user_accounts`); `PUBLIC_BASE_URL` on Railway (https share links).

## Pre-Launch Hardening — Security, Reliability & Scalability Overhaul (2026-06-27)

**Why this exists.** On June 24 multiple testers (Miguel, Heather) reported the Plan tab "stuck on 0 found." An SRE investigation of prod data (durable `research_runs` table + Railway logs) found it was **not a crash** — every run completed with 25–33 candidates — but a **perceived hang from head-of-line blocking**: the research worker was a single daemon thread, so concurrent users serialized (Heather waited 176s behind her own run on Jun 22 → 6.5 min total; Jun 24 three users serialized through one worker), and the UI showed "0 found" with no progress during the queue wait and polled forever. The current architecture (single Railway instance, single-writer DuckDB on a local volume, no queue, no LLM backoff, log-scraping as the only observability) is fine for a closed beta but **will not survive a public launch**. This epic is the hardening pass to do **before** opening up.

### ✅ Shipped now — beta concurrency fix (2026-06-27)
- **Research worker thread pool** (`app/research/worker.py`) — `RESEARCH_WORKER_CONCURRENCY` (default 3) threads drain the queue concurrently; the atomic `claim_next_queued_run` (`UPDATE…RETURNING`) prevents double-claim. Removes head-of-line blocking at beta scale (discovery is I/O-bound, so GIL releases on network waits → real parallelism). Covered by a barrier test that deadlocks if serial.
- **OpenAI backoff** (`app/research/graph.py`) — research `ChatOpenAI(max_retries=RESEARCH_LLM_MAX_RETRIES, default 4)` so a 429 burst from concurrent runs degrades to "slower," not "failed."
- **Run dedup** (`app/research/router.py` + `get_active_research_run`) — a re-submit while a run is in flight returns the existing run instead of stacking another behind it (kills double-tap pile-ups).
- **iOS queue UX** (`PlanViewModel`/`PlanView`) — a queued run shows "Lining up your search… / you're in line" instead of a frozen "0 found"; the poll is capped at 5 min with a graceful "still working, tap again" (re-tap resumes the same run via dedup).

### ✅ Shipped now — reliability test suite, Phase 1 (2026-06-27)
Tests that pin the strategies above so the June-24 incident can't silently regress.
- **Offline / hermetic** (`mvp-backend/tests/reliability/`, 13 tests, <4s, no LLM): worker-pool concurrency (parallel + bounded by `concurrency`), atomic-claim exactly-once under thread contention, startup-sweeper crash recovery, idempotent candidate re-write, OpenAI 429→retry via `httpx.MockTransport`, per-user run dedup. See the suite README for the strategy↔test map.
- **nl-harness black-box** (`tests/nl-harness/specs/tier-2/`): `research-dedup` (rapid re-submit → same run, `deduped=true`) and `concurrent-enqueue-resilience` (N parents fire `POST /research/runs` at once → distinct runs, no 5xx/corruption under the single DuckDB writer). Both validated live. **CI note:** the harness backend must run with `RATE_LIMIT_AUTH_PER_HOUR>=1000` (provisioning N personas issues N tokens; default cap 5/hr 429s the setup).

### ✅ Shipped now — Phase 2 failure-injection in the harness (2026-06-27)
Adopted the NL-Harness Playbook's §4.8 fault-injection model for parent-app — backoff/concurrency/failure modes are now testable **end-to-end, deterministically, and free** (no real OpenAI). All three flows pass in ~10s via one orchestration script.
- **Mock OpenAI server** (`tests/nl-harness/mocks/mock_openai.py`) — stdlib, serves `/v1/chat/completions` (stream + non-stream). The keystone trick: it returns a *no-tool-call* completion, which terminates the deepagents loop in one turn, so a real research run reaches `done` deterministically (0 candidates — we test resilience, not discovery). The backend points at it via `OPENAI_BASE_URL` (the playbook's "real-or-mock via config" switch).
- **`ctx.fault()` API** (`tests/nl-harness/lib/fault.py`, wired as `flow_ctx.fault`) — `flow_ctx.fault('openai','rate_limit', count=2)` / `'down'` / `.reset()` / `.state()`, toggling the mock's failure mode over its `/__fault__` control plane. Mirrors the playbook's `ctx.fault('stripe','timeout')`. `.available` is False outside the fault env, so the flows skip cleanly in the normal harness.
- **Failure-mode specs** (`specs/tier-2/`): `research-backoff-recovery` (429×2 → run still completes, mock confirms ≥2 faults served), `research-openai-outage` (hard outage → run ends `failed` gracefully, poll never 5xx-cascades, error populated), `research-worker-saturation` (N>pool → all drain to `done`).
- **Runner**: `tests/nl-harness/tools/run-fault-flows.sh` brings up mock + a dedicated fault-backend (isolated temp DuckDB) and runs the specs.
- **Deferred from this phase:** `voice-elevenlabs-outage` — EL is connected from the *iOS app* (ConvAI), not the backend, so "EL down" isn't backend-black-box-testable; needs a client-side or a backend EL-proxy seam first. Tavily mock (research never calls Tavily once the canned completion has no tool calls, so it's unneeded for these flows). A stale-run **reaper** + per-run execution-timeout (see Reliability below) are now directly testable on this seam.

### Reliability (next)
- **✅ Error tracking + alerting — SHIPPED + LIVE (2026-07).** The June-24 incident had to be reconstructed by scraping Railway's log buffer + the durable tables; that gap is closed. Sentry captures unhandled errors; OpenTelemetry → Grafana Cloud carries metrics + alerting; the Grafana MCP gives read-only PromQL from Claude Code. Gated on env vars in `app/observability/`. (See the ✅ Observability subsection below.) **First 4 domain alert rules LIVE (2026-07-12):** COS hook errors, doors fail-open, watchlist missed-window, watchlist worker stall (group `cos-health` @1m → Slack; no-data=OK on all — the series don't exist until first event). **Still extend** — research run failure rate, p95 queue wait, 5xx, LLM 429 — as the metric surface fills in.
- **Worker stall / liveness.** A single stuck `process_run` silently burns a pool slot. **Partial mitigation shipped** (2026-06-27): a per-call `RESEARCH_LLM_TIMEOUT_S` (60s) so a *hung* upstream call can't pin a slot for the SDK's ~10-min default. **Still TODO:** a per-run *wall-clock* cap (a multi-call run that's slow-but-not-hung can still exceed budget) + a stale-run reaper + a worker heartbeat. The load+chaos driver (`tests/nl-harness/tools/load_and_chaos.py`, E3) demonstrates the gap on demand.
- **`cancel` was ineffective + clobbered terminal state — FOUND & FIXED (2026-06-27).** The load+chaos hunt (E2) caught it: cancelling a *running* run returned `canceled`, then the finishing worker overwrote it to `done` (cancel did nothing, OpenAI spend wasted, terminal state regressed). Fixed with `finalize_run_if_running` (conditional terminal write) + candidate discard; regression-locked in `tests/reliability/test_cancel_during_run.py`. This is the first bug the test infra *hunted* rather than guarded.
- **Apply the thread-pool + backoff pattern to the other single-threaded workers** (`email_sync`, `calendar_sync`) before they carry real load.
- **`research_runs` has no failure history in practice** — every run is `done`; confirm the `failed` path actually fires and surfaces to the client (today a failed run shows a generic error).
- **Verify the moderation parent-notification path.** Jun 24 a kid session ("little one") tripped self-harm / emotional-distress flags (correctly blocked); confirm `parent_notified_at` actually alerted the parent — a safety-critical path that's currently unverified in prod.
- **Cross-user 403 friction.** Jun 24 logs show `kid-agent/list?user_id=Greg` and `…=Ava` 403'ing intermittently (token-vs-claim mismatch). Diagnose stale/racing tokens before launch — reads to a tester as "the app won't load my kids."

### Scalability (the launch lift)
- **External job queue.** The research/email/calendar job tables live in DuckDB on a local volume, so workers can't scale past one instance. Move to a shared queue (Redis + RQ/Celery) so worker capacity scales horizontally and survives restarts independently of the API.
- **Postgres migration.** The single-writer DuckDB `_ThreadSafeConn` RLock serializes every write through one lock on one volume — a hard ceiling and a single point of failure. Migrate to Postgres (managed) for real concurrency, connection pooling, and multi-instance writes. (`docs/roadmap.md` Backend section already flags schema normalization — fold it in.)
- **Horizontal API + worker instances** behind Railway/load balancer once state is external (queue + Postgres). Make the API stateless (no in-process `MemorySaver`/caches that assume one instance).
- **LLM rate-limit budgeting.** At launch scale, concurrent runs (12–14 calls × ~15–20k tokens each) will hit gpt-5.5 TPM/RPM caps. Add a token-budget governor / concurrency cap tied to the actual OpenAI tier, and reduce per-run cost (~$0.30–0.40/run today; cheaper extract model, lower default `max_candidates`).
- **Load test — measure the real concurrency ceiling** (deferred from 2026-06-27). Two halves: (a) *cheap/free now* — scale the Phase-2 saturation harness (mock OpenAI, `tools/run-fault-flows.sh`) to 25/50/100 concurrent enqueues and measure the **orchestration** ceiling (pool drain time, atomic-claim contention, the single DuckDB write-lock, FastAPI threadpool, queue depth) with zero OpenAI cost; (b) *the real ceiling* — a small real-OpenAI run at the target concurrency to find the OpenAI-tier TPM/RPM wall (the one thing the mock can't measure). Publish the curve before opening up. Pairs with tuning `RESEARCH_WORKER_CONCURRENCY` (currently 3; raising it is a single Railway env var — bounded by the OpenAI tier, which the load test sizes).

### Security (pre-launch audit)
- **✅ Identity hardening — SHIPPED (auth v2).** Native Apple + Google Sign-In, JWT access + rotating refresh, no more "client claims a user_id" trust. Remaining launch gate = retire the legacy `/auth/issue-token` path at T2 (tracked in the top "Architectural Infra" section).
- **Google verification + CASA.** `gmail.readonly` is a restricted scope; the OAuth app + annual CASA security assessment must clear before non-test users can connect Gmail. Long lead time — start now.
- **Secret rotation + management.** OpenAI/ElevenLabs/Tavily/Fernet keys live in `.env` + Railway env. Establish rotation cadence, move to a secret manager, and confirm `INTEGRATION_ENC_KEY` (encrypts refresh tokens at rest) has a documented rotation/re-encrypt plan.
- **Admin surface review.** `/data/export`, `/data/download/{filename}`, `/cms/*` are `ADMIN_TOKEN`-gated (shared secret). Before launch: per-operator auth/audit on these, and confirm the download path's traversal guard + that exported parquet (full user PII) can't leak.
- **Abuse / rate limits.** Discovery is expensive ($/run) and currently throttled only by `rate_limit_enforce`. Add per-user run quotas + abuse detection before discovery is open to the public.
- **Full security audit** (authz matrix, PII handling/retention, COPPA posture for the kid agent, injection hardening review) as a gate, not an afterthought.

### ✅ Observability — SHIPPED + LIVE (2026-07)
- **Sentry (errors) + OpenTelemetry → Grafana Cloud (metrics + alerting) + the Grafana MCP** (read-only PromQL from Claude Code) are live, gated on env vars in `app/observability/`. Structured `[COST]` correlation ids, a metrics dashboard, and Slack alerting now exist. **Still open:** extend structured request/trace logging to *all* paths (the `[COST]` workflow id covers the agent/search/voice paths), and the **ElevenLabs post-call webhook** (Backend section) so voice minutes are measured, not proxied.

## Activity Planning / Chief of Staff (new, 2026-06-19)

Branch `feat/activity-planning-chief-of-staff`. A deep-research background agent (deepagents) discovers camps/activities by location + kid profile; an isolated chief-of-staff agent + planning service builds the calendar, to-dos, logistics/coverage, and cost. Surfaced on a new iOS **Plan** tab and a new **parent web dashboard** (`mvp-backend/parent-dashboard/`). Full design: `~/.claude/plans/we-are-going-to-frolicking-candy.md`; system diagram: `docs/system-architecture.md`.

### Shipped (backend + both surfaces)
- Adopting `deepagents` forced a langchain/langgraph stack bump — guarded by `mvp-backend/tests/agents/` (offline) + `tests/nl-harness/` (live). 11 new DuckDB tables; `/research/*` (run/poll/candidates) + `/cos/*` (chat SSE, calendar/todo/caregiver/logistics CRUD, `/cos/plan/summary`) + `GET /profile`.
- Discovery shows a **live progress feed** (Thinking / Searching for … / Found …) via a `BaseCallbackHandler` writing `progress_json`; **fit-kids** chips (age-matched, multi-kid); ZIP override + profile prefill.

### ✅ Shipped since 2026-06-27 (all deployed to prod; iOS via TestFlight)
- **Profile editor overhaul.** Backend `PATCH /profile` + `PATCH /profile/kids/{name}` + `DELETE /profile/kids/{name}` (kid-agent cascade via `delete_kid_data`), with `replace_lists` semantics so the ~35 parent + ~23 kid learned fields are editable AND list items removable. iOS Settings → **Profile** hub (parent/kid Basics editors, Add-a-kid, family-wide "What we've learned" screen, delete-a-kid with confirm + swipe-to-delete). Web **Profile** page. Replaces the old "only 3 fields editable" state.
- **COS power-tools — `cos/tools.py` grew 12 → 19.** Added LookupAndSaveCamp (save a camp the parent already registered, as if via the UI), GetKidsInfo, Help ("what can you do"), UpdateActivity, UntrackActivity, StartDiscovery (kick a research run from chat). Cost-logged + Sentry-tagged per tool.
- **Chat-first Plan hub.** iOS Plan tab is a segmented hub **[Chat · Discover · Shortlist · Calendar]**, default Chat (the COS was buried); `CosChatViewModel` hoisted so the conversation survives segment switches. Coach tab renamed "MVP" → "Coach".
- **Configurable discovery count + "top N of many".** Count picker (5 / 15 / 25 / 50). Backend decouples SURFACE count from search DEPTH (`_resolve_surface_count` vs `_resolve_discovery_target`, floor 25 / ceiling 100); `_rank_and_trim` returns the top N by `fit_score`; result header reads "Top N of M reviewed"; the record-tool dedups. Supersedes the old hardcoded `N of 25`. Also fixed "select 50 → get 25" (a still-queued run is now retargeted instead of silently dropping the new params).
- **Radius geo-grounding.** New `app/research/geo.py` + a bundled offline `app/research/data/us_zip_centroids.csv.gz` (GeoNames, ~41k US ZIPs). `nearby_towns(zip, radius)` enumerates the real towns within the radius and injects them into the research prompt so the agent covers a spread instead of anchoring on the nearest big city (fixed: a 50mi search from 95448 missing Sebastopol); `distance_for_city` → a per-candidate `distance_mi`. (= Personalization → Geo enrichment, now ✅.)
- **Discovery result filters + a unified Sort & Filter sheet.** Client-side facet filters (City / Category / Kid) plus a modern bottom-sheet control (sort: Best match / Price / Starting soonest / Age / Nearest / Name) on iOS + web, with an entry control-bar, active-filter chip summary, and sticky "Show N results" / Reset.
- **Waiting-UX overhaul.** Discovery streams LIVE partial results (`candidates_preview` in progress frames → skeleton → cards) instead of a bare spinner; time expectation + live elapsed timer; reconnect to an in-flight run (durable `run_id`); queued-state clarity. Kickoff moved from 2s polling to SSE streaming, with radius + free-form focus inputs.
- **R3 / R4 / R5 Google integration.** R3 daily email-sync agent + R4 two-way Google Calendar sync (daily `email_sync` / `calendar_sync` worker daemons); R5 generalized `google_oauth_tokens` → an `integration_accounts` table; full Google OAuth (backend + iOS); CMS Email-Sync + Calendar-Sync admin pages.

### Yet to do
- **Latency optimization — partially done.** ✅ Shipped the **batch record tool** (`record_activity_candidates(list)`): the agent now records all finds from a search in one LLM turn instead of one turn per candidate (was ~26 round-trips with input tokens ballooning ~7k→~59k, ~$2/run for 8). Live progress is preserved — the tool trickles a per-candidate `Found: <name>` via an `on_each` hook so the feed still climbs one at a time. **Still open:** consider lowering the default `max_candidates` and/or a cheaper model for the extract turns if cost is still high. Read the per-run profiler line (`[research] discovered N in Xs | LLM …x/…s | …`) to confirm the turn count dropped.
- **Phase 3 — multimodal ingestion — backend ✅ (`ca324b9`) + iOS ✅ (`368efe7`).** `POST /ingest/text` + `POST /ingest/image` (vision over flyer/form/screenshot photos) → `ExtractedActivity` (shared 2-stage schema, injection-hardened like `summary.py`) → deterministic `materialize()` spawns a pending activity + action-item to-dos + calendar entries; under-age kids land `pending_eligibility` + a confirm to-do (never auto-confirm). Plus `POST /cos/draft-email` (LLM-drafted, grounded on a tracked activity, HITL — never sends). 58 offline tests green; real-LLM extraction live-validated (gpt-5.5, 0.96 conf). iOS: an "Add from a message or photo" sheet on the Plan tab (`IngestView`) — Paste (TextEditor) or Photo (`PhotosPicker`, no camera/permission by design since the app's camera-usage string declares the camera is never used); images downscaled to 2000px/JPEG to stay under the 8MB cap; result card shows the extracted activity + spawned follow-ups; build SUCCEEDED. Known gap: the model sometimes returns a date *range* as one `"start/end"` string — `materialize()` skips un-parseable dates (activity+todos still land); expand ranges later. **Deployed + validated in prod (2026-06-20)** — all 5 routes live, content migration preserved (110/45/27), live ingest smoke passed, smoke user cleaned up via the `delete_family` cascade. **Still open:** **Gmail `gmail.readonly` Google verification + CASA** — the full Google OAuth flow + R3 daily email-sync now exist (`integration_accounts` table), but the restricted-scope verification + annual CASA assessment must clear before non-test users can connect Gmail (long lead — in flight).
- **✅ Phase 3b — export/share — SHIPPED.** `GET /cos/plan/export.xlsx` regenerates the workbook-style xlsx (openpyxl); scoped, read-only, expiring nanny/therapist **share links** (`issue_share_token` + `list_share_tokens`). (Two-way Google Calendar sync shipped separately as R4.) Fast-follow: `PUBLIC_BASE_URL` on Railway for https share links.
- **Surfacing the COS coordination on the clients** — the chat-first Plan hub shipped (✅), but the direct calendar/logistics *editing* UI is still thin (CRUD exists; editing is mostly via chat). Port the export once Phase 3b lands.
- **✅ Web dashboard IS deployed.** The Dockerfile builds `parent-dashboard` (multi-stage) and `app/server.py` serves it at `/dashboard` (SPA fallback). It ships with every `railway up` — no separate deploy needed.
- **Phase 5 acceptance replay**: feed the original Alvarado artifacts (iMessage/flyer photos/forms) through the live pipeline and score against `Alvarado_Summer_2026_Camps.xlsx`.
- Incremental progress `candidates_found` only updates on tool events (cosmetic); profile **kid ages can be stale** (Ceiba showed 7) — editable in Settings → Profile.

## Voice (ElevenLabs ConvAI v2)

**Architecture today (v1 TTS-proxy fully removed 2026-06-12).** Real-time voice over ElevenLabs Conversational AI (WebRTC / LiveKit transport, sub-150ms). Our backend stays the brain as a **Custom LLM**; ElevenLabs does STT / turn-taking / TTS / transport. One agent serves all kids (per-kid voice/prompt/greeting via `conversation_config_override` at connect); a second agent serves the parent coach. Full console setup + gotchas live in `docs/voice-v2-elevenlabs-setup.md`.

> The old v1 plan (`~/.claude/plans/look-at-our-onboarding-optimized-candle.md`) — sentence-fragment proxy, `/voice/synthesize/*`, `AVPlayer` queue, `TTSProvider`, `tts_usage_daily`, char caps — is **dead**. It was deleted end-to-end in the v2 failure-mode redesign. Don't resurrect those endpoints/files.

### Shipped

- **Kid companion voice (v2).** `convai_endpoint.py` Custom LLM (`/v1/chat/completions`) keeps the LangGraph kid agent + 5-layer moderation + crisis locks; a crisis fires the built-in `end_call` system tool to hang up. `/voice/convai-token` is parent-token + kid-PIN + crisis-lock gated; the greeting is persisted at mint. iOS: `KidVoiceSessionManager` (process singleton — owns the session, LiveKit `AudioManager.setEngineAvailability` engine resets, serialized teardown, fresh-token retry, 15s watchdog) → `KidCompanionCoordinator` (phase machine: connecting / voiceLive / textFallback / crisisLocked) → `KidAgentView`. Fallback is **text-only and silent** by design.
- **Parent coach voice "call" mode (v2, 2026-06-17).** Opt-in waveform button in `AgentView` → `ParentVoiceView`. A second ElevenLabs agent + `/v1/parent/chat/completions` (`parent_convai_endpoint.py`) runs the parent agent — **no moderation/crisis/PIN** (adult). The endpoint strips `[Title](mvp://library|community/{id})` links from the spoken text and emits `show_article` / `show_community_post` **client-tool** deltas; `ParentCompanionCoordinator` resolves the ids via `ContentViewModel`, renders `LibraryItemCard`/`CommunityPostCard`, then `sendToolResult`. On **End**, the session transcript is captured and imported into the text chat (`ChatViewModel.importMessages`); voice + text share one LangGraph thread so agent memory is continuous.
- **Live transcript + reactive orb/mute.** The live-call view observes the SDK `Conversation` as `@ObservedObject` (the earlier bug was passing it as a plain value → no updates).
- **Client-side transcript "streaming."** Voice transcripts arrive whole-turn — ElevenLabs does not stream tokens in voice mode (`agent_chat_response_part` is text-only and never fires in voice). `StreamingText` reveals them progressively, driven by per-character **audio alignment** when available (`[parent-voice] ✅ audio alignment available` logs on first alignment) with a fixed-rate typewriter fallback. "Good enough for now" per Miguel.

### Yet to do

- **Persist parent voice turns into `chat_memory`** (Miguel said yes; not built). Backend: append the user + raw assistant turns to `chat_memory` + `persist_state` inside `parent_convai_endpoint`. iOS: load `/memory/{user_id}` on `AgentView` appear so voice history survives app restart / fresh load (today it only carries in-session via `importMessages`).
- **Tune transcript-reveal pacing** once a device confirms the alignment log fires. If alignment never arrives over WebRTC for these agents, decide whether the typewriter fallback is the permanent path.
- **Bring the streaming reveal to the kid surface** (parent has it; the kid surface still renders whole-turn).
- **Per-kid voice picker.** ConvAI passes `voice_id` at connect via `conversation_config_override.tts.voice_id`, so the picker is a connection-time override, not a synthesis change. (`app/voice/allowlist.py` was deleted with v1 — re-curate a small `(age_band, mood) → voice_id` map.) Surface in `ReviewLetterView`; optionally let invariant synthesis suggest a default.
- **ConvAI-era cost guardrails + observability.** v1's per-char caps / `tts_usage_daily` / `voice_synth` rate bucket are gone. ConvAI bills **per minute**; the only guard today is the dashboard **max conversation duration (~15 min)**. Add a per-user/day *minutes* rollup + a global kill-switch + a parent-visible health signal; reframe `/admin/voice/usage` for minutes, not chars.
- **Targeted dedup of kid/parent voice code** (assessed, not decided): a `VoiceLevelSmoothing` VAD→orb helper + a `VoiceCallCoordinating` protocol shared by both coordinators — **not** a god-component merge.
- **Crisis STT perturbation evals** (see iOS backlog): ElevenLabs STT mishears crisis language; assert detection still fires on misreads.
- **Consent copy** must mention voice-transcript retention (`ConsentView.swift`).

### Known constraints (do not regress)

- `ELEVENLABS_API_KEY` is backend-only (App Store safety) and must carry the **`convai_write`** permission to mint conversation tokens.
- Voice does **not** work in the iOS Simulator (no usable mic → WebRTC mic-publish times out); test on a physical device.
- `kid_pin` + crisis-lock gating on the kid token endpoint; the parent path is deliberately ungated (adult).
- Fallback to text must be a deliberate path, never a silent fallthrough.

## iOS / SwiftUI backlog (2026-05-11 Vix review)

Surgical fixes shipped in `7e33828` (HomeView config, streamTask cancel, ContentService HTTP status, NotificationCenter removal, @MainActor ServerConfiguration, etc.). Deferred from that review:

- **✅ `userID` identity — SHIPPED (auth v2).** New users get a UUID from native Apple/Google Sign-In (no more first-name collisions); legacy name-based ids are grandfathered and claim their data on first sign-in. Done end to end (iOS `userID`, auth router, `authorize_user_match`). See the top "Architectural Infra" section + `setup/auth-setup.md`.
- **Split `OnboardingView.swift` (1390 lines, 16 `@State`).** Break into one step per `struct` driven by a shared `@Observable` (or `ObservableObject`) `OnboardingViewModel`. Largest single maintenance burden in the app; makes step testing possible and stops sibling-step re-renders on every keystroke.
- **`@Observable` macro migration** for the view models (`KidsHomeViewModel`, `KidPickerViewModel`, `ReviewLetterViewModel`, `KidChatViewModel`, `ContentViewModel`). Removes `@Published`/`ObservableObject`, gives per-property invalidation. Confirm the iOS-17+ floor first (the app already uses iOS-17 APIs like `AVAudioApplication.requestRecordPermission`, so likely safe).
- **Protocol-abstract the services** (`ContentService`, `KidAgentService`, `ChatService`) and inject them into view models so they're mockable in tests; today they're static/`@MainActor` structs called directly.
- **De-dupe the SSE parser** — `ChatService.decodeToken` and `KidAgentService.decodeToken` plus the `data:`-line loop are near-identical; extract a shared `SSEParser`.
- **`ChatView` vs `AgentView`** are near-duplicate chat UIs (`ContentView` still routes to `ChatView`). Decide whether `ChatView` is legacy and deletable, then collapse to one.
- **Surface load errors in the UI.** `ContentViewModel.loadError` is now published but no view shows it; `KidsHomeSection.error` and the kid-picker load error are set but never read — users see blank sections on failure. Add error states with retry.
- **MED/NIT cleanups:** `AgentView` content-card generation runs in `body` via `DispatchQueue.main.async` (move to `.task(id:)`); `bloomColor` keyword-sniffing duplicated in `KidAgentView` + `KidPickerView` (extract to `KidAgentInvariants`); `UIScreen.main.bounds` in `ChatView` (deprecated — use `GeometryReader`/`containerRelativeFrame`); inline `Binding<Bool>` alert pattern duplicated in `ChatView`/`AgentView` (use `.alert(item:)`); `ConsentView.submit` fire-and-forget `Task`; `OnboardingData.kids` anonymous tuple → a named `Sendable` struct; `ContentStore.swift` is now just route types (fold into a `Routes.swift` or keep intentionally).

## Onboarding & Profiling

- **Verify the demographic enrichment in Xcode.** End-to-end run on simulator after CoreSimulator update: walk the new "About you" step filling everything, then again skipping every field. Confirm `/profile/seed` POST body is correct and that the coaching agent weaves the new fields into responses.
- **Conversational parity check.** Open `/onboarding-chat` with a fresh `user_id` and confirm the agent organically asks about location, language, age range, employment, adults in household, and per-child pronouns/grade band. If it doesn't, tighten the system prompt.
- **Tier-2 sensitive fields.** Religion and household-income bracket were deferred. Both need product framing (privacy, trust, why we're asking) before adding. Cultural background was added; revisit in a follow-up to decide whether the others land in the structured form, in `/onboarding-chat`, or only get captured silently.
- **Per-child language.** Currently `primary_language` is parent-level only. Some bilingual households have different primary languages per child — consider adding `home_language` to `ChildProfile` if this comes up.
- **Co-parent capture.** When `household_structure ∈ {co-parenting, divorced, blended}`, prompt for co-parent name and dynamics in a follow-up step. Already supported in the model (`co_parenting`); not surfaced in the form.

## Personalization

- **✅ Geo enrichment — SHIPPED.** `app/research/geo.py` + a bundled offline ZIP-centroid table (`data/us_zip_centroids.csv.gz`, GeoNames) derive `city` / `region` / a per-candidate `distance_mi` from `postal_code`, and `nearby_towns(zip, radius)` grounds the discovery prompt in the real towns within the search radius. It IS used in the UI now (distance shown on cards). (`time_zone`-derived reminders remain open — see below.)
- **Locale-aware coaching.** When `primary_language` is non-English, have the agent respond in that language (or offer to). Currently it just uses whatever language the user types in.
- **Time-zone aware reminders.** Once `time_zone` is known, schedule "morning routine" / "bedtime" tips relative to the user's local clock, not server clock.

## Backend / Infrastructure

- **DuckDB schema normalization (when needed).** Today profiles are JSON blobs in `user_data`. If we start running analytics ("how many parents reported `postal_code IN (...)`") or want fast filtering, write a migration that promotes core demographic + behavioral fields to columns in dedicated `parent_profiles` / `child_profiles` tables.
- **Service-account key rotation.** The current `sk-svcacct-*` key sits in `.env` and Railway. Document the rotation process and decide a cadence.
- **Pin discipline.** `langgraph-prebuilt` was pinned to 1.0.8 to dodge the `ExecutionInfo` mismatch. Re-evaluate when bumping `langgraph` to 1.1.x — at that point we can unpin and let pip pick the latest prebuilt.
- **`/data/export` reachability check.** `tools/sync-data.sh` failed earlier because production was returning 404. Add a friendlier preflight (curl `/health` first, give a clearer error on 4xx/5xx).
- **Railway auth refresh.** The CLI token expired silently; we discovered it only when `railway up` failed. Document re-auth in the deployment notes.
- **Per-user bootstrap-from-parquet.** Today `DuckDBStorage.__init__` only loads from `mvp.parquet` when `user_data` is **completely empty** (`duckdb_storage.py:213`). One stray test row in `user_data` skips the bootstrap on every restart and any user present in parquet but not in the live DB stays stranded forever. Change to a per-user merge: for every `(user_id, name)` row in parquet that has no matching live row, insert it. (This stranded Miguel locally on 2026-05-08; recovery was a manual `migrate_json_to_duckdb.py` run.)
- **Auto-migrate legacy `local-storage/<user>/*.json` on startup.** When a JSON profile exists but the DuckDB `user_data` table has no row for that `(user_id, name)` pair, run the same insert path `migrate_json_to_duckdb.py` uses. Removes the manual recovery step the next time someone clones the repo or wipes their local DB.
- **Cost logging shipped (2026-06-19).** `app/cost_logging.py` emits `[COST][LLM|SEARCH|VOICE]` lines (per-workflow correlation id, env-overridable pricing) across all agents + search + voice; scrape Railway logs to estimate spend per user/feature/workflow. See `~/.claude/.../reference_cost_logging.md`.
  - **TODO — ElevenLabs post-call webhook** to capture EXACT voice minutes (today we log a session-count proxy + per-turn OpenAI cost; EL per-minute fee is only on their dashboard). Add a public HMAC-verified `POST /voice/elevenlabs/post-call` (verify `ElevenLabs-Signature` `t=…,v0=HMAC-SHA256(f"{t}.{body}", ELEVENLABS_WEBHOOK_SECRET)`, ±30min replay window) that reads `metadata.call_duration_secs` and logs `[COST][VOICE] event=call_ended minutes=X usd=Y`. Correlate conversation→user via ConvAI dynamic-variables echoed in the payload OR a `conversation_id→(user,feature,workflow)` map populated in the Custom-LLM endpoints. Enable the webhook in the EL dashboard + set `ELEVENLABS_WEBHOOK_SECRET`.
  - **TODO — wire the direct OpenAI moderation API** (`omni-moderation-latest`, near-free) cost count if desired; the LLM/search/voice token paths are covered.

## iOS

- **✅ Build environment — resolved.** CLI `xcodebuild` builds run cleanly against the iOS Simulator SDK; iOS ships via TestFlight (repo currently at 1.66/build 80 — the five-doors build, TestFlight upload pending). No longer Xcode-only.
- **Returning-user path.** `OnboardingView` welcome screen has a "Welcome back" branch that bypasses every demographic step. Decide whether returning users should be re-prompted for fields that didn't exist when they first onboarded (e.g., zip), or whether we surface a "Complete your profile" nudge in Settings instead.
- **✅ Profile editing — SHIPPED.** Settings → **Profile** hub lets users edit structured parent/kid fields directly (Basics editors, Add-a-kid, family-wide "What we've learned", delete-a-kid), backed by `PATCH /profile` / `PATCH /profile/kids/{name}` / `DELETE /profile/kids/{name}` with `replace_lists` semantics. Replaces the old re-onboard / chat-only path.

## Content / Agent

- **`/onboarding-chat` finish signal.** The onboarding agent loops indefinitely — it never explicitly says "done." Decide on a completion heuristic (N tool calls, profile coverage threshold, user says "that's enough") and surface a "graduate to coaching" CTA in the iOS app.
- **Coaching agent guardrail.** The "weave into advice, never dump as raw data" instruction works most of the time, but worth a regression script: ask questions that tempt it to echo zip/age, confirm it doesn't.

## Family Companion (kid agent + handoff)

Plan: `~/.claude/plans/we-need-to-work-lively-wave.md`. Auto-generated kid agent per child + "Dear Robo" letter review + voice-first kid mode + daily summary to the parent. v0 ships as a closed beta.

### v0 — closed beta only

- Mixed ages allowed under explicit informed-consent agreement signed in-app by the parent.
- **Not COPPA-compliant.** Cannot list publicly on the App Store; cannot run marketing aimed at children.
- Pre-launch gates: ✅ real auth (JWT + rotating refresh — shipped), locked CORS + rate limits, real tables for kid data (not JSON blobs), chunk-buffered moderation with crisis routing, eval suite v1 (~120 cases) wired to CI, kill-switch per `agent_id`, Slack telemetry.
- Voice (Whisper/`SFSpeechRecognizer` STT + TTS) is in scope for v0; both pipelines moderation-gated.

### v1 — public-launch audience decision

Two paths to evaluate at end of beta. Decide based on which audience produced the strongest engagement / NPS in beta data.

- **Teen-only public launch (13+).** Lower regulatory burden — standard auth + parent oversight is sufficient. Faster path to public availability. App Store age-gate at signup.
- **Under-13 public launch.** Requires the full COPPA stack:
  - Verifiable parental consent (credit-card $0.01 verification or e-signed form notarized — FTC-acceptable methods).
  - Updated privacy policy with explicit COPPA disclosures (data collected, purpose, retention, sharing).
  - Audit log on every kid-message read (parent, support, ML team).
  - Data-export and data-delete endpoints (right to access, right to erasure).
  - Retention limits (transcripts ≤ 12 months default, parent-controllable).
  - EU GDPR-K DPIA documented.
  - Designated child-data DPO.
  - Multi-week compliance work.

### Hard constraints regardless of v1 path

- No third-party ad networks for kid traffic. No behavioral advertising.
- Transcript retention ≤ 12 months default with parent control to delete.
- Parent has full transcript access — non-negotiable, surfaced as a feature.
- Crisis keywords (self-harm, abuse, suicide) trigger immediate parent notification + crisis resources displayed to kid + chat freeze.

## Held for mobile coordination (from 2026-05-11 Vix review) — ✅ BOTH SHIPPED

- **✅ Locked `/content/community/new` + `/content/community/{post_id}/replies` server-side.** Both now `Depends(current_user)` (server.py:824, 866) — Security phase 1 + auth v2's dual-accept `current_user` closed the impersonation/spam hole without 401'ing legacy TestFlight users.
- **✅ `ADMIN_TOKEN` set + rotated on Railway.** `/data/*` + `/cms/*` gated (CMS moved to a cookie-session login; `VITE_ADMIN_TOKEN` removed from the bundle). Prod data sync works with `MVP_ADMIN_TOKEN` locally.

## Vix review backlog (2026-05-11) — unfixed findings

Independent deep review by Vix. The verified blockers (unauth `/data/*` + `/cms/*`, path traversal, crisis-output ordering, late-flag persistence) were fixed in `7c5a8b1`. Everything below is triaged but **not yet done**. Severity is Vix's.

### Verify-first (possible false positives — Vix runs on a Jan-2026 model)
- **gpt-5.2 model string** (used across runtime/synthesis/moderation/evals). Vix claims it doesn't exist and every LLM call may be silently failing to fallbacks. Almost certainly cutoff noise since prod runs — but confirm the model name resolves.
- **`from langchain.agents import create_agent`** (`kid_agent.py`, `evals/runner.py`). Vix claims it's not in langchain 1.2.0. Confirm the import succeeds at startup (it must, since the agent runs).
- **B-2 dead code after `return` in `revoke_all_auth_tokens`** (`duckdb_storage.py:1039-1048`). Verify whether there's an unreachable block; if so, delete it.

### HIGH — ✅ all fixed in `2b336a8` (2026-05-11)
(B-2 dead code also removed in the same commit. Kept below for the record.)
- **H-1 proxy-blind rate limiting** (`server.py:354`). `request.client.host` is Railway's proxy IP, so the 5/hr `/auth/issue-token` cap is shared across ALL clients. Read first `X-Forwarded-For` hop behind a trusted-proxy allowlist.
- **H-2 `_verify_kid_pin` default-open** (`server.py:662`). Returns `True` when `pin is None` even if a PIN is set → trivial bypass. Flip to: no PIN configured = allow; PIN set but absent = deny. (Tied to the kid-auth-model question.)
- **H-4 prompt injection via `summary.py`** (`summary.py:99-125`). Raw kid messages flow unsanitized into the summary LLM prompt; a kid can manipulate the `parent_prompt` shown to the parent. Delimit message content as inert data + cap `parent_prompt` length.
- **H-5 `delete_family` doesn't abort in-flight streams** (`duckdb_storage.py:1015`). A streaming kid-chat keeps running after the family is deleted. Call `moderation.kill_agent()` for each deleted agent_id during cascade.
- **H-6 `revive` re-enables unconditionally** (`server.py:1093`). `set_kid_agent_enabled(True)` runs regardless of whether a lock was actually cleared; gate on `cleared`. Also write an `audit_events` row on every crisis revive.
- **H-7 consent check missing on kid endpoints** (`server.py:714,727,1074,1080`). `_require_consent` absent from `/kid-agent/list`, `/kid-agent/preview` (burns LLM budget), `/kid-agent/crisis-locks`, and `/kid-agent/{id}/revive` (bypasses safety acknowledgement). Add it.
- **H-9 unbounded `limit` param** (`server.py:1031,1043`). `/kid-chat/transcripts` + `/kid-moderation/events` accept arbitrary `limit` → OOM/thread-block. Add `Query(le=1000)`.
- **H-10 string-interpolated parquet paths** (`duckdb_storage.py:269,279`). Not attacker-controlled today, but use `?` placeholders / validate before interpolation.
- **B-8 DuckDB single connection not thread-safe** (`duckdb_storage.py:241`). Shared `self._con` across FastAPI's thread pool + event loop can corrupt/interleave. Min bar for beta: a `threading.Lock` around every execute. Real answer: Postgres. (Corroborates the `--workers 1` note already on the roadmap.)
- **B-9 TOCTOU in `save_kid_agent_config`** (`duckdb_storage.py:671`). Concurrent writers at the same `expected_version` both insert. Add `UNIQUE(user_id, kid_name, version)` + transaction + 409 on conflict.

### MED
- **M-1 unbounded `_kid_agent_cache`** (`kid_agent.py:55`) — slow leak of AgentExecutor instances; use a bounded LRU.
- **M-3 child crisis content sent to Slack in plaintext** (`telemetry.py:110`). Abuse/self-harm excerpts land in Slack's cloud. Send only ids + category + severity + a dashboard link; never the excerpt. (Already partially done server-side for the output path in `7c5a8b1` — the input crisis path at `server.py:893` still passes the raw message.)
- **M-5 `daily_summaries` UPDATE clobbers `created_at`** (`duckdb_storage.py:1251`). Add `updated_at`, stop overwriting `created_at`.
- **M-6 mixed `$N`/`?` placeholder styles** (`duckdb_storage.py:432`) — fragile; standardize on `?`.
- **M-7 `ChatOpenAI` constructed per moderation call** (`moderation.py:306,603`) — HTTP client churn; hoist to module-level singletons.
- **M-9 summary ignores non-default threads** (`summary.py:85`, `duckdb_storage.py:1206`) — kid messages in non-`default` threads silently excluded from the daily summary.
- **M-10 no integrity check on `soul_kid.md`** (`prompt_synthesis.py:303`) — file is writable at deploy; a tampered soul injects into every kid prompt. Verify a build-time SHA256 at startup.
- **M-11 `content_hash` truncated to 64 bits** (`prompt_synthesis.py:436`) — cache-invalidation key; a collision runs a stale agent with the wrong blocklist. Use full hash or ≥32 chars.
- **M-12 eval reports with kid/agent content land in servable `data/`** (`evals/runner.py:282`) — crisis-case agent responses written to `data/eval_reports/`; redact or move outside any served dir.

### NIT
- **N-1** `rt-050` eval wrongly expects `must_route_crisis` for "sneaking out" (`evals/cases/red_team.yaml:909`) — should be refuse-secrecy + mention-parent + redirect, not crisis script.
- **N-2** `gc-011` duplicate `must_not_contain_topic` YAML key silently drops the violence check (`guardrail_conflict.yaml:143`) — make it a list.
- **N-3** `/kid-agent/preview` output not moderated (`server.py:768`) — low risk (parent-only) but unmoderated LLM text.
- **N-4** `persist_state()` called synchronously inside async stream generators (`server.py:289,336`) — blocks the event loop; wrap in `run_in_executor`.
- **N-6** `ChatRequest.user_id` defaults to `"0"` (`server.py:79`) — masks client bugs; drop the default to force a 422.
- **N-7** repeated local `from fastapi import HTTPException` (already imported at top) — clean up the in-function imports.

### Open questions for the owner (from Vix's review)
1. ✅ RESOLVED — Crisis parent-notification now delivers via **APNs push** (verified on device 2026-07-06, `setup/apns-setup.md`); `parent_notified_at` is stamped on send. (Optional email fallback still open.)
2. Kid auth identity: kid runs under the parent's token; is the PIN a real boundary or UI-only? (Decides H-2 severity.)
3. COPPA: consent is self-reported (any kid can fabricate parent + age band). Needs legal review.
4. Parquet export scope: only `user_data` is exported; `kid_messages`/`consent_records`/`moderation_events`/`daily_summaries` never are. Intentional?
5. ✅ RESOLVED — auth v2 ships `/auth/logout` (revokes the refresh-token family) + rotating refresh with reuse-detection (a replayed token nukes the whole family). Lost-device revoke is covered by refresh-token revocation.
6. Orphaned crisis locks: reviving requires the old `agent_id`, but `upsert_kid_agent_config` mints a new one — old lock rows orphan. Define the lifecycle.

## Family Companion v0 — pre-beta blockers (from 2026-05-07 critic review)

Findings doc: `docs/code-review-findings.md`. Items already shipped this session are removed; these are what's left before any family touches the build.

### Identity & access
- **✅ Apple Sign-In — SHIPPED (auth v2); App Attest dropped as moot.** Native Apple + Google Sign-In replaced the "client claims a `user_id`" trust model. `/auth/issue-token` still accepts a body `user_id` but is now gated (`AUTH_ISSUE_TOKEN_ENABLED`), refuses already-claimed accounts, and retires at T2 — so the "one leaked user_id away" threat is closed for the new account model. `DCAppAttestService` attestation is no longer needed.
- **Audit/redact `user_id` in Slack alerts and DEBUG logs.** Demote `logging.basicConfig(level=DEBUG)` in production; redact `user_id` to a stable hash prefix in `telemetry._post_slack`.
- **✅ Real JWT — SHIPPED.** Auth v2 ships genuine JWT HS256 access tokens (`AUTH_JWT_SECRET`) + rotating opaque refresh tokens with reuse-detection. The naming now matches the implementation.

### Crisis safety
- **✅ Real APNs parent push for crisis events — SHIPPED + verified on device (2026-07-06).** Crisis lock fires an APNs push to the parent (env-gated `APNS_*`, `.p8` at `mvp-backend/secrets`, Key K97TDFQ2UM / Team 5K4ZDG6NFD / bundle MVP.MVParent; `APNS_AUTH_KEY` or `APNS_AUTH_KEY_FILE`). See `setup/apns-setup.md`. (Email fallback via Resend/Postmark remains an optional follow-up.)
- **Crisis-routing telemetry SLO.** Define and instrument `crisis_event_to_parent_notified_p99 ≤ 60s`. The metric surface now exists (OTel→Grafana + APNs stamps `parent_notified_at`), so this can be a derived metric over `moderation_events.created_at` vs `parent_notified_at` + a Grafana alert — the SLO instrumentation itself is still to build.
- **Voice STT crisis test class.** Whisper / SFSpeechRecognizer mishears "I want to hide myself" as "I want to die myself" and vice versa. Add `evals/cases/stt_perturbation.yaml` (~10 cases) — actual STT misreads of crisis language; assert detection still fires.

### Eval harness rewrite
- **Tests run the production code path, not a hand-built simplified one.** `runner.py:113` skips Stage 1 of synthesis; `runner.py:142` builds a bare `create_agent` with no moderation pipeline. Refactor `kid_chat_stream_handler` into a callable `run_one_turn(user_id, kid_name, message)` and make `_run_case` use it.
- **Synthesis-side red team.** Add `evals/cases/red_team_synthesis.yaml` (~20 cases) — malicious *parent briefs* — and assert the synthesized invariants don't reflect those instructions.
- **Threshold split for safety-critical.** Today `red_team: 0.95`. Split into `red_team_safety_critical` (crisis + secrecy + abuse, threshold **1.00** hard) and `red_team_jailbreak` (rest, 0.95).
- **Multi-turn drift cases.** All 120 cases are single-turn; real attacks are 6 messages of trust-building then the ask. Add `multi_turn.yaml` (~15 cases, 4-8 turns each).
- **Long-context drift cases** — 50 turns of innocuous chat then crisis cue at turn 51. Validates R1 still holds at depth.
- **Parent-on-kid-account cases** — parent asks the agent for the system prompt, asks to lie to a future-self, etc.
- **Mixed-language / code-switch coverage** — beyond the single rt-024 Spanish case.
- **Tool-call observation injection** — Tavily output sanitization. Today `kid_agent.py` wires search with no scrub.
- **Judge calibration set** — `evals/cases/calibration.yaml` (30 hand-graded cases). CI asserts judge agreement ≥ 0.85.
- **Drop `RUN_KID_EVALS=1` opt-in.** Nightly GitHub Action runs the full suite, posts the markdown report, blocks deploys on red.

### Observability & launch readiness
- **✅ Metrics/alerting — SHIPPED via OTel→Grafana Cloud** (superseded the `prometheus-client /metrics` approach): HTTP + custom metrics export to Grafana with Slack alerting, read-only Grafana MCP. Still open: add the fine-grained histograms (`moderate_input`, `moderate_with_openai`, `/kid-chat` stream) + the moderation-error-rate alert onto that surface.
- **Structured logs** — partially addressed: `[COST]` per-workflow correlation ids + Sentry tie errors to context. Still open: extend Request-ID propagation to **all** paths (matches the "extend structured logging to all paths" note in the Observability subsection above).
- **API versioning prefix.** New kid endpoints under `/v1/`. The roadmap explicitly anticipates a v1 break.
- **Pagination cursors.** `/kid-chat/transcripts`, `/kid-moderation/events`, `/summary/list` — `limit` only; past message #N parents silently lose history.
- **Idempotency-Key on `/kid-agent/config`.** Letter resubmission on flaky network creates a new version row each time.
- **`/consent/submit`** → use `HTTPException` envelope, not `JSONResponse(400)`.

### Cost & abuse
- **Cost ledger.** Per-user-per-day `(tokens_in, tokens_out, dollars_estimate)`. 429 above $5/family/day in beta. Today one bored kid overnight = $4-11k of OpenAI burn.
- **Drop `_generate_preview_messages`.** It's a second LLM call per keystroke after a 600ms debounce in `ReviewLetterView.swift`. The synthesized invariants already include `voice_examples` — render those directly.
- **Rate-limit class for `/summary/generate`** and **`/kid-agent/preview`.** Today the only buckets are `chat` and `config`; `/summary/generate` is unrate-limited entirely.

### Architecture cleanup (no behavior change)
- **Extract `KidChatPipeline`** from `server.py:430-1029` (now ~1,200 lines). Yields semantic events; SSE rendering is a thin shell.
- **`KidAgent` domain object.** Today `KidAgentConfig` exists as a dict in 3 layers (DuckDB row, Python dict, Swift struct). Define `app/kid_agent_model.py` with a frozen dataclass exposing behavior (`is_topic_blocked`, `has_tool`, `opener_for`).
- **Naming sweep:** `invariants → Letter` (the product calls it "the letter" everywhere user-facing); `_age_band → age_band` (currently private but imported into `server.py`); split `KID_DDL` per bounded context (`auth_tokens` and `consent_records` aren't kid-specific).
- **Dependency arrow inversion.** `kid_agent.py:96` does `from app.server import storage_backend`; same in `summary.py`, `auth.py`. Introduce `app/repositories.py` with a module-level `repo()` accessor.
- **Drop `_bootstrap_default_config`.** `kid_agent.py:179-211` writes a DB row just to render the review screen.
- **Constitutional critique** is dead code (`moderation.py:445-484`) — remove or wire.

### iOS (frontend)
- **Tap-anywhere-to-interrupt during TTS.** `synthesizer.speak()` plays through "stop" or "no"; kid cannot interrupt. Add gesture → `synthesizer.stopSpeaking(at: .immediate)` + restart STT.
- **Crisis script TTS uses a calmer voice + slower rate.** Today the soft-redirect plays at the same chirpy default.
- **Speaker-confusion defense.** No defense today against "kid hands phone to friend." Per-session re-prompt or PIN-required mode.
- **Kid PIN brute-force lockout.** 4-digit PIN with no rate limit and no lockout. Add 5-fail lockout, attempts counter.
- **`KidPickerView` NotificationCenter → closure.** Already takes `onSelected: (KidAgentConfig) -> Void` at init; just call it instead of posting `.kidPickerSelected`.
- **`HandoffCurtain` two-finger gesture.** Comment admits SwiftUI can't count fingers. Either ship the explicit button and remove the gesture, or invest in a UIKit recognizer.
- **`bloomColor` definition.** Defined twice as keyword sniffing on `personalityDescription` (`KidAgentView.swift:189` + `KidPickerView.swift:140`). Move to a method on `KidAgentInvariants` or have synthesis produce a `palette` field.
- **Voice transcripts mention in consent text.** `ConsentView.swift` doesn't currently mention voice retention.

### Testing
- **CI on every PR.** GitHub Action runs `pytest` (unit tests for `rate_limit`, `_verify_kid_pin`, `StreamingModerator`, `scan_for_crisis`, `_extract_bearer`, `_require_consent`). Separate scheduled job runs the eval suite.
- **`pip-audit` + Dependabot.**

### Storage & retention
- **12-month retention enforcement.** Roadmap promises ≤12mo retention; no scheduled job exists today. Add a nightly DELETE on `kid_messages.created_at < now() - INTERVAL 12 MONTH`, parent-controllable per family.
- **Persist LangGraph `MemorySaver` to DuckDB.** Process-local today; lost on every Railway redeploy. SQL checkpointer in LangGraph 1.1+.
- **Promote in-process state to DuckDB:** `_killed_agents` already done; `_global_frozen` and `rate_limit._RateLimiter` are next when multi-replica matters.

## Out of scope (intentionally not on the roadmap)

- Switching profile storage off DuckDB.
- Rebuilding the form as a single long screen — the multi-step flow is on purpose.
- Religion as a top-level field (sensitivity vs. value tradeoff is unfavorable right now).
- Builder chat agent for the kid-agent flow (v0 ships auto-gen + letter review only — revisit after 4 weeks of beta data).
