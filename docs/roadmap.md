# Roadmap

Living list of next-up work. Order is a rough priority, not a commitment. Items move to `docs/history/NNN.md` when shipped.

## Activity Planning / Chief of Staff (new, 2026-06-19)

Branch `feat/activity-planning-chief-of-staff`. A deep-research background agent (deepagents) discovers camps/activities by location + kid profile; an isolated chief-of-staff agent + planning service builds the calendar, to-dos, logistics/coverage, and cost. Surfaced on a new iOS **Plan** tab and a new **parent web dashboard** (`mvp-backend/parent-dashboard/`). Full design: `~/.claude/plans/we-are-going-to-frolicking-candy.md`; system diagram: `docs/system-architecture.md`.

### Shipped (backend + both surfaces)
- Adopting `deepagents` forced a langchain/langgraph stack bump — guarded by `mvp-backend/tests/agents/` (offline) + `tests/nl-harness/` (live). 11 new DuckDB tables; `/research/*` (run/poll/candidates) + `/cos/*` (chat SSE, calendar/todo/caregiver/logistics CRUD, `/cos/plan/summary`) + `GET /profile`.
- Discovery shows a **live progress feed** (Thinking / Searching for … / Found …, with `N of 25 found` target) via a `BaseCallbackHandler` writing `progress_json`; **fit-kids** chips (age-matched, multi-kid); ZIP override + profile prefill; iOS Settings → Profile editor.

### Yet to do
- **Latency optimization (priority).** A full run is ~140s for ~25 candidates because the agent records **one candidate per LLM turn** (~26 sequential round-trips). Add a **batch record tool** (`record_activity_candidates(list)`) so many land in one call, and/or lower the default `max_candidates`, and/or a cheaper model for the record/extract turns. The per-run profiler line (`[research] discovered N in Xs | LLM …x/…s | …`) confirms where the time goes.
- **Phase 3 — multimodal ingestion**: `/ingest/text` + `/ingest/image` (vision over flyer/form photos) → `ExtractedActivity` → pending activities/todos/calendar; then **Gmail OAuth** (`gmail.readonly` — start Google verification + CASA early). Tables (`ingest_artifacts`, `google_oauth_tokens`) already exist.
- **Phase 3b — export/share**: regenerate the workbook-style xlsx/pdf (openpyxl), scoped nanny/therapist share links, two-way Google Calendar sync.
- **Surfacing the COS coordination on the clients** (the CRUD exists; calendar/logistics editing UI is thin) and porting the export.
- **Web dashboard isn't wired into deploy** — no `/dashboard/*` static route in `server.py`, no build step in the Docker/entrypoint. Decide: serve from the backend (like CMS) or deploy separately.
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

- **`userID` is the parent's first name.** Onboarding stores the typed name as the identity used for tokens + profile, so two parents named "Miguel" collide on the same token and family data. This is the same auth-model gap the backend reviews flagged; it's a **v1 blocker**. Wire a real per-account identifier (UUID at first launch, then Apple Sign-In) end to end — iOS `userID`, `/auth/issue-token`, and every `authorize_user_match`.
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

- **Geo enrichment.** Server-side, derive `city` / `state` / `time_zone` from `postal_code` + `country` so the coaching agent can reference local context without us asking the user twice. No UI change needed.
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

- **Build environment.** This machine is missing the iOS 26.4 platform install — `xcodebuild` can't run a real build from CLI. Either install the platform or document that builds happen exclusively in Xcode.
- **Returning-user path.** `OnboardingView` welcome screen has a "Welcome back" branch that bypasses every demographic step. Decide whether returning users should be re-prompted for fields that didn't exist when they first onboarded (e.g., zip), or whether we surface a "Complete your profile" nudge in Settings instead.
- **Profile editing.** Today the only way to update profile data is to re-onboard or chat with the coaching agent. Add a Settings → Profile screen that lets users edit the structured fields directly.

## Content / Agent

- **`/onboarding-chat` finish signal.** The onboarding agent loops indefinitely — it never explicitly says "done." Decide on a completion heuristic (N tool calls, profile coverage threshold, user says "that's enough") and surface a "graduate to coaching" CTA in the iOS app.
- **Coaching agent guardrail.** The "weave into advice, never dump as raw data" instruction works most of the time, but worth a regression script: ask questions that tempt it to echo zip/age, confirm it doesn't.

## Family Companion (kid agent + handoff)

Plan: `~/.claude/plans/we-need-to-work-lively-wave.md`. Auto-generated kid agent per child + "Dear Robo" letter review + voice-first kid mode + daily summary to the parent. v0 ships as a closed beta.

### v0 — closed beta only

- Mixed ages allowed under explicit informed-consent agreement signed in-app by the parent.
- **Not COPPA-compliant.** Cannot list publicly on the App Store; cannot run marketing aimed at children.
- Pre-launch gates: real auth (JWT + locked CORS + rate limits), real tables for kid data (not JSON blobs), chunk-buffered moderation with crisis routing, eval suite v1 (~120 cases) wired to CI, kill-switch per `agent_id`, Slack telemetry.
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

## Held for mobile coordination (from 2026-05-11 Vix review)

- **Lock `/content/community/new` + `/content/community/{post_id}/replies` server-side.** Vix found these accept an arbitrary `user_id`/`author_name` with no auth (impersonation + spam). The iOS `ContentService` now attaches a Bearer token to both calls (shipped), but the **server-side `Depends(current_user)` + `authorize_user_match` is deliberately NOT deployed yet** — turning it on now would 401 every TestFlight 1.3 user (same trap as `/profile/seed`). Add the server lock in the same release as the next TestFlight build that includes the auth-sending `ContentService`.
- **Set `ADMIN_TOKEN` on Railway.** `/data/export`, `/data/download`, and all `/cms/*` mutations are now gated behind an `X-Admin-Token` header (fail-closed: they return 503 until `ADMIN_TOKEN` is set). After deploy, set `ADMIN_TOKEN` via `railway variables set` and put the same value in `MVP_ADMIN_TOKEN` locally for `sync-data.sh`. Until then, prod data sync is intentionally disabled.

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
1. Crisis parent-notification: `parent_notified_at` is always `None` — no APNs/SMS/email, only Slack-to-oncall. Interim email before beta?
2. Kid auth identity: kid runs under the parent's token; is the PIN a real boundary or UI-only? (Decides H-2 severity.)
3. COPPA: consent is self-reported (any kid can fabricate parent + age band). Needs legal review.
4. Parquet export scope: only `user_data` is exported; `kid_messages`/`consent_records`/`moderation_events`/`daily_summaries` never are. Intentional?
5. `revoke_auth_token` has no caller — no logout endpoint; tokens die only by 30d expiry or `delete_family`. Add logout + lost-device revoke?
6. Orphaned crisis locks: reviving requires the old `agent_id`, but `upsert_kid_agent_config` mints a new one — old lock rows orphan. Define the lifecycle.

## Family Companion v0 — pre-beta blockers (from 2026-05-07 critic review)

Findings doc: `docs/code-review-findings.md`. Items already shipped this session are removed; these are what's left before any family touches the build.

### Identity & access
- **App Attest / Apple Sign-In on `/auth/issue-token`.** Today the endpoint is rate-limited per-IP but still accepts an arbitrary `user_id` from the body. Until App Attest or an out-of-band invite-code flow is in place, the closed beta is one leaked `user_id` away from full read access on a victim family. Pair the iOS side with a `DCAppAttestService` keypair attestation; verify on the server.
- **Audit/redact `user_id` in Slack alerts and DEBUG logs.** Demote `logging.basicConfig(level=DEBUG)` in production; redact `user_id` to a stable hash prefix in `telemetry._post_slack`.
- **Re-name `JWT` → `opaque session token` in code/docs.** The roadmap claims JWT but the implementation ships uuid4 hex tokens. Either ship a real JWT (HS256 with rotating secret) or stop calling it that.

### Crisis safety
- **Real APNs parent push for crisis events.** The lock-and-freeze path is wired (parent must call `/kid-agent/{agent_id}/revive` to clear), but the `parent_notified_at` field is still set to `None` because there is no APNs delivery yet. Pair with iOS to register a device token at consent time, send via APNs from the crisis branch with retry+jitter, stamp `parent_notified_at` on success. Email fallback (Resend/Postmark) when APNs fails twice.
- **Crisis-routing telemetry SLO.** Define and instrument `crisis_event_to_parent_notified_p99 ≤ 60s`. Until `/metrics` exists this lives as a derived metric over `moderation_events.created_at` vs `parent_notified_at`.
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
- **`/metrics` endpoint via `prometheus-client`.** Gate to admin or VPN. Latency histograms on `moderate_input`, `moderate_with_openai`, the `/kid-chat` stream. Counters on every fail-closed path. One starter alert: moderation-API-error-rate > 1% over 5m.
- **Structured logs** with Request-ID propagation. Today `logger.info("[kid_chat] start ...")` is plain text and the Slack alert can't be tied to a single server log line.
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
