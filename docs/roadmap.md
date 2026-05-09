# Roadmap

Living list of next-up work. Order is a rough priority, not a commitment. Items move to `docs/history/NNN.md` when shipped.

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
