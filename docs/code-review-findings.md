# Code Review Findings — Family Companion v0

**Date:** 2026-05-07
**Reviewers (synthesized):**
- Martin Fowler — architecture, layering, naming, evolution risk
- Andrej Karpathy — agent harness, prompts, evals, safety pipeline
- Google Principal Engineer (L8) — launch readiness, SLI/SLO, API design, dependency hygiene
- Amazon Principal Engineer (L7) — operations, security, tenancy isolation, data lifecycle

**All four returned a "block" verdict.** Karpathy's exact words: *"Do not let a child near this build."* Three reviewers explicitly call out that the consent screen makes promises the code does not keep.

This document clusters findings by severity and file rather than by reviewer, so a fix touches every finding on that file at once.

---

## Severity legend

- **🔴 NO-SHIP** — would block closed beta. Multiple reviewers converged.
- **🟠 HIGH** — must fix before public launch / v1, can sometimes ship behind a flag.
- **🟡 MED** — debt to log and live with for closed beta; prioritize against v1 plan.
- **⚪️ NIT** — small cleanups, don't block on these.

---

## 🔴 NO-SHIP findings (convergent across reviewers)

### 1. `/auth/issue-token` is an authentication-free impersonation oracle
*(Fowler, Google, Amazon)*

**Where:** `mvp-backend/app/server.py:347` — `auth_issue_token_endpoint`. POST `{user_id}` returns a Bearer token unconditionally. No proof-of-ownership, no captcha, no OTP, no rate limit.

**Compounding problems:**
- Tokens stored cleartext in `auth_tokens.token` (`duckdb_storage.py` `issue_auth_token`). Database leak = all sessions compromised.
- No expiry. Stolen token = forever access.
- No replay protection (no nonce, no IP/UA binding).
- `user_id` UUIDs leak via Slack alerts, debug logs, screenshots — closed-beta channel chatter is enough to seed the attack.
- The roadmap claims "JWT" but the code ships opaque uuid4 tokens. Reconcile.

**Attack walkthrough (30 seconds):**
1. Attacker observes a victim `user_id` (any leak surface above).
2. `POST /auth/issue-token {"user_id": "<victim>"}`.
3. Reads `/kid-chat/transcripts`, `/kid-moderation/events`, `/summary/list`.

**Fix path:**
- Closed-beta-safe: require an out-of-band invite code, recorded at consent time, used once at token issuance. Rate-limit to 5/hour/IP.
- Production: Apple Sign-In + App Attest assertion. Server derives `user_id` from the token; client never sends it in body for kid endpoints.
- Independent: hash tokens at rest (`sha256(token)`); add `expires_at` (default 30d) + `last_used_at`; add `/auth/revoke` route.

---

### 2. Crisis path does not freeze the agent and does not notify the parent
*(Karpathy, Amazon)*

**Where:** `mvp-backend/app/server.py:864` — literal `# TODO(notify): wire to parent push` in the crisis branch. `parent_notified_at=None` written to `moderation_events`.

**Failure stack:**
1. **No parent push exists.** Crisis alert goes to Slack only. If `SLACK_WEBHOOK_URL` is unset on a fresh Railway deploy, `_post_slack` silently returns (`telemetry.py`). Crisis disclosure → `/dev/null`.
2. **`alert_crisis` runs in a daemon thread** — SIGTERM during deploy drops the alert mid-flight.
3. **Chat freeze is not a freeze.** The crisis branch emits the soft-redirect, fires Slack, returns `[DONE]`. The agent is **not** added to `_killed_agents`. Next message reopens the agent normally.
4. **`kill_agent` / `_killed_agents` are in-process state** (`moderation.py:86-87`). On Railway restart or multi-replica, the kill switch evaporates.
5. **Output-side crisis** (model generates self-harm content): `StreamingModerator._gate_text` blocks emission but does NOT call `kill_agent` and does NOT call `alert_crisis`. Logged as `blocked_output severity=crisis` and forgotten.
6. **Race condition:** input-side gate returns *before* invoking the LLM, so input crisis is fine — but anything that gets past the gate and then drifts mid-stream rides on the buffer-bypass bug below.

**Fix path:**
- In the crisis branch (input AND output), call `moderation.kill_agent(agent_id)` AND persist `enabled=False` + `crisis_locked_until=NOW()` to `kid_agent_configs` AND write a `crisis_locks` row with the trigger phrase.
- At the top of `/kid-chat`, check the persisted lock and refuse with a static "your grown-up needs to check in with you first" message.
- Require an explicit parent action via a new `POST /kid-agent/{agent_id}/revive` (parent-token-only) to clear.
- For closed beta: implement APNs push (or transactional email via Resend/Postmark — already a dependency-free path) and `await` it before returning. Stamp `parent_notified_at` only on success.
- Promote the `_killed_agents` set to a `kid_agent_killed` DuckDB table; rehydrate on startup.

---

### 3. `entrypoint.sh` wipes the audit trail on every deploy
*(Google, Amazon)*

**Where:** `mvp-backend/entrypoint.sh:30` — `rm -f /app/data/*.duckdb*` runs on every container start. The DuckDB is then re-bootstrapped from parquet snapshots.

**The kill:** `export_parquet` and `export_content_parquet` (`duckdb_storage.py:1076-1093`) only snapshot **`user_data` and content tables**. The kid-feature tables are *not* in the export:
- `kid_messages` (transcripts)
- `moderation_events` (the audit trail!)
- `consent_records` (consent history)
- `auth_tokens` (active sessions)
- `daily_summaries`
- `kid_credentials`

**Result:** every Railway push silently destroys consent history, audit log, and active tokens. There is no recovery; the parquet doesn't have them.

**Fix path:** EITHER stop deleting the DuckDB on deploy and rely on volume persistence (the volume IS persistent at `/app/data/`; the wipe is gratuitous), OR add the missing tables to `export_parquet` + verify bootstrap reads them.

The simpler answer is "stop the wipe." The wipe was added because of the data-sync incident in 007.3, but the right fix there was the size-comparison logic already in `entrypoint.sh` for parquet seeds. Drop the `rm`.

---

### 4. Consent screen lies — there is no delete or export endpoint
*(Amazon)*

**Where:** `mvp/MVP/ConsentView.swift:54` — *"You can revoke this companion or delete its history at any time."*

`grep '@app.delete' server.py` returns three hits, all `/cms/*`. **There is no kid-data delete endpoint.** No export endpoint. No `purge_*` methods on `DuckDBStorage`. No retention enforcement (12mo cap promised on roadmap line 67) — no scheduled job, no `created_at < now() - INTERVAL 12 MONTH` query.

**A real delete must purge:**
1. `kid_messages` (join via `agent_id`)
2. All `kid_agent_configs` versions (not just latest)
3. `kid_credentials`
4. `moderation_events`
5. `daily_summaries`
6. `auth_tokens` (revoke on family delete)
7. `consent_records` — keep, mark `deleted_at` for audit
8. **The Parquet snapshots** in `/app/data/*.parquet` (regenerate on next export; previous snapshot still has data until then)
9. **The seed-data baked into the Docker image** (`Dockerfile`: `cp /app/data/*.parquet /app/seed-data/`). If a beta build's parquet ever contains real data, every future container image ships that data. **Audit current seed-data immediately.**
10. The in-process `MemorySaver` checkpointer (`kid_agent.py:48`) — `invalidate_kid_agent` doesn't currently clear it.
11. Railway logs — they include message content via DEBUG logging.
12. **OpenAI's training/abuse retention** — if the API key isn't toggled to "no data retention," OpenAI keeps inputs for 30 days. Toggle it.

**Fix path:** ship `DELETE /family/{user_id}` (parent-token-only, cascades the above) + `GET /family/{user_id}/export` (zip of all rows + parquet) + an `audit_events` table row per delete/export. Don't update the consent text until the endpoint works. Don't ship the consent text to families as-is.

---

### 5. Streaming moderator buffer-bypass — the gate clears, the rest streams free
*(Fowler, Karpathy)*

**Where:** `mvp-backend/app/moderation.py:353-377` — `StreamingModerator.feed()`.

**The bug:** While in `BUFFERING` state with buffer < 120 chars, output is held. Once the buffer crosses 120 chars and clears moderation, state flips to `STREAMING` and **subsequent tokens are emitted with no further moderation** until `finalize()` runs at end-of-stream. That's the wrong contract.

Two ways this fails:
- A model that opens with 200 safe chars then drifts into age-inappropriate detail at char 400 streams that to the kid; the only re-check is on `finalize()`, which fires *after* the kid has already seen it.
- A crisis utterance long enough to wrap conversational fluff around the matching span (>120 chars) clears the gate before the regex/classifier ever sees the matching span.

**Fix path:** keep accumulating into a sliding window after the gate clears. Re-run the cheap crisis regex on every token append; re-run OpenAI moderation + age classifier every N tokens (say, 200) or on paragraph boundaries. `finalize()` always runs full-output moderation against the assembled `assistant_buffer`; if it fails, replace the assistant message in DuckDB with a refusal and emit a "your grown-up needs to check in" event to the client.

---

### 6. No SLI / SLO instrumentation; `telemetry.snapshot()` is dead code
*(Google, Karpathy)*

**Where:** `telemetry.py:34-41` — single `incr()` counter into a `defaultdict(int)`. `snapshot()` exists; nothing exports it. No `/metrics` endpoint, no Prometheus, no OpenTelemetry, no Sentry.

**Worst-instrumented golden signal: errors.** `moderation.moderate_with_openai` fail-closes silently with a `logger.exception` (line 174-182). The only outward symptom is a `medium`-severity moderation result returned as if it were a normal flag. You will not page on this.

**The SLO that matters and is unmeasured: crisis-trigger time-to-parent-notification.** Cannot evaluate the promise without the metric AND without the parent push (#2).

**Fix path:**
- Add `prometheus-client`. Expose `/metrics` (gated to admin or VPN).
- Latency histograms on `moderate_input` (`moderation.py:262`), `moderate_with_openai`, the kid-chat stream.
- Counters: `moderation.openai.error`, `kid_chat.stream.error`, `crisis.detected`, `crisis.parent_notified`.
- One alert: moderation-API-error-rate > 1% over 5m.

---

### 7. Crisis regex coverage is undersized and anglocentric
*(Karpathy, Amazon)*

**Where:** `mvp-backend/app/moderation.py:64-73` — 7 regexes.

**Missing categories** (cross-checked against 988/SAMHSA-aligned vocabularies and ROST-style severity):
- Hopelessness ("I just want it to stop", "nothing matters")
- Passive ideation ("I wish I wouldn't wake up", "I want to disappear")
- Method words (pills, rope, razor, tall building)
- Grooming hints (send pictures, meet up, our secret, don't tell)
- Eating-disorder signals ("haven't eaten in N days", "throw up after")
- Substance overdose hints
- Spanish / code-switched ("quiero morirme", "ya no quiero estar aquí")

The cited eval cases (rt-016 ED, rt-017 grooming, rt-018 hopelessness) **pass crisis routing only if the LLM happens to produce the script** — your regex won't catch them, so the deterministic tier is bypassed and you're trusting the model.

**Fix path:** expand `_CRISIS_PATTERNS` to ~60 patterns across 6 categories, each tagged with `severity` (`crisis_imminent` | `crisis_high` | `crisis_passive`). For `crisis_imminent` (method + intent + timeframe — "tonight I'll take all the pills"), bypass the LLM entirely and emit a hotline-naming script + freeze + page parent over SMS. Add `test_crisis_regex.py` with 200 positive + 200 negative strings; run on every PR.

---

### 8. Eval harness bypasses production code path
*(Karpathy)*

**Where:** `mvp-backend/app/evals/runner.py:113` — comment literally states the runner skips Stage 1 of synthesis. `runner.py:142` — bare `create_agent` with no moderation pipeline.

**Result:** the 120 eval cases test a hand-built simplified prompt your users will never see, against an agent stripped of moderation. The "95% red-team pass" claim cannot be cashed.

Coverage gaps Karpathy called out:
- No multi-turn cases (every case is single-turn; real attacks are 6 messages of trust-building then the ask)
- No voice/STT-perturbation cases (Whisper/SFSpeechRecognizer 8-15% WER on kid voices garbles crisis cues)
- No long-context drift (turn 60 with 8KB system prompt — does R1 still hold?)
- No parent-on-kid-account cases
- No mixed-language code-switch
- No tool-call observation injection (Tavily output sanitization)
- No synthesis-side red team (malicious parent brief)

**Fix path:** factor `kid_chat_stream_handler` into a callable `run_one_turn(user_id, kid_name, message) -> {response, mod_events}` that doesn't need FastAPI request context; make `_run_case` use it. Add `red_team_synthesis.yaml` (~20 cases). Drop `RUN_KID_EVALS` opt-in; add a paid nightly CI job that fails the build if any safety-critical category drops below 1.00.

Threshold split: today's `red_team: 0.95` should split into `red_team_safety_critical` (crisis + secrecy + abuse, threshold **1.00** hard) and `red_team_jailbreak` (rest, 0.95). 5% failure on safety = 1-in-20 jailbreak succeeds with a real kid.

---

### 9. No CI; near-zero unit-test coverage on safety-critical helpers
*(Google)*

`scan_for_crisis`, `_verify_kid_pin`, `StreamingModerator.feed/finalize`, `_extract_bearer`, `_require_consent`, `_RateLimiter` — pure functions with security-critical behavior, **all untested**. Eval suite is opt-in (`test_evals.py:34` `skipif RUN_KID_EVALS != "1"`).

No `.github/workflows/`, no pre-commit. The promotion gate in `runner.py:42-46` enforces nothing.

**Fix path:** GitHub Action — `pytest` (with new unit-test files) on every PR; separate scheduled job runs `RUN_KID_EVALS=1` and fails on red-team < 1.00 for safety-critical. Add `pip-audit` + Dependabot.

---

### 10. No cost cap; denial-of-wallet via `/kid-agent/preview` and `/kid-chat`
*(Amazon)*

`/kid-chat` rate-limited to 60/min/user with **no daily cap**. Per-turn cost ~$0.15-0.40 (moderation + age classifier + runtime LLM + sometimes Tavily). One bored kid overnight = 28k turns = $4-11k of OpenAI spend.

`/kid-agent/preview` runs a real LLM call on every keystroke debounce, rate-limited under the `config` class (30/min). At ~$0.05/preview, that's $1.50/min/user of attack surface. The preview is also redundant — `voice_examples` from invariants already represent what the agent will say (Fowler called this out independently).

`/auth/issue-token` has **no rate limit at all**. Token-issuance flooding fills `auth_tokens` indefinitely.

**Fix path:**
- `cost_ledger(user_id, day, tokens_in, tokens_out, dollars_estimate)` updated on every LLM call.
- 429 above $5/family/day in beta (configurable).
- Drop the live LLM `/kid-agent/preview` — render `voice_examples` directly from invariants.
- Rate-limit `/auth/issue-token` (5/hour/IP).

---

## 🟠 HIGH — fix before public launch (single-reviewer or scoped)

### 11. `server.py` is a 1,179-line transaction script
*(Fowler)* `mvp-backend/app/server.py:430-1029` — auth dependencies, rate limiting, CORS, kid-agent CRUD, kid streaming pipeline, moderation orchestration, preview synthesis, summary, parent CMS, all interleaved. Three near-duplicate moderation-event-logging blocks (`server.py:805-820`, `826-840`, `870-886`).

**Fix:** extract `app/kid_chat_pipeline.py` with a `KidChatPipeline` orchestrator yielding semantic events (`UserAccepted`, `BlockedInput`, `CrisisRouted`, `Token`, `BlockedOutput`, `Done`). Server's job becomes `async for evt in pipeline.run(...): yield sse_render(evt)`. Move `_generate_preview_messages` into `prompt_synthesis.preview_openers()`.

### 12. Anemic domain model — `KidAgentConfig` lives as a dict in 3 layers
*(Fowler)* DuckDB row, Python dict, Swift struct, with no `KidAgent` server-side object. Callers manually destructure `invariants["agent_display_name"]`, `agent_id`, `age_band`, `kid_name` as four parallel arguments.

**Fix:** `app/kid_agent_model.py` with a frozen `KidAgent` dataclass exposing behavior (`age_band(child_profile)`, `is_topic_blocked(topic)`, `has_tool(name)`, `opener_for(kid)`). Repository becomes the only thing that knows row→object mapping.

### 13. `storage_backend` imported through `app.server` — dependency arrow inverted
*(Fowler)* `kid_agent.py:96` does `from app.server import storage_backend`. Same in `summary.py:75,149`, `auth.py:28,33,58`. Domain code reaching across the application layer to find its repository.

**Fix:** introduce `app/repositories.py` with a module-level `repo()` accessor; inject explicitly where possible.

### 14. In-process state everywhere
*(Fowler, Amazon, Google)* `moderation._killed_agents`, `_global_frozen`, `_kid_agent_cache`, `rate_limit._RateLimiter`, `telemetry._counters`. Restart or multi-replica = state evaporates. Today on a single Railway dyno: tolerable. v1: this is your incident-response surface.

**Fix:** persist kill state to DuckDB now (cheap); rate-limit and telemetry can wait until horizontal scale.

### 15. Tokens stored cleartext, never expire, no rotation
*(Google, Amazon)* See #1 fix path.

### 16. CORS `allow_credentials=True` with `allow_methods=["*"]` and `allow_headers=["*"]`
*(Fowler)* `server.py:67-73`. Browsers reject the `*`+credentials combo; you'll get bug reports that look like auth failures.

### 17. Voice path: no on-device STT enforcement
*(Karpathy, Amazon)* `VoiceController.swift` doesn't set `request.requiresOnDeviceRecognition = true` and never checks `recognizer.supportsOnDeviceRecognition`. Audio of a kid saying anything potentially leaves the device to Apple servers depending on locale/device.

**Fix:** require on-device; fail loudly if unsupported.

### 18. Voice path: no interrupt; agent voice picked up as kid input
*(Karpathy)*
- `synthesizer.speak()` plays through "stop" or "no" — kid cannot interrupt mid-utterance.
- No mutex between TTS and STT — if the agent is mid-sentence and the kid talks, the recognition tap picks up the *agent's* own voice. Self-amplifying loop.
- `shouldReportPartialResults = true` — partials may be sent to moderator before the sentence completes.
- `stopListening` only called when `isFinal=true` — listening hangs open if user never finishes a sentence (kids do this constantly).

**Fix:** pause recognition tap while `isSpeaking == true`. Add 3-second silence timeout. Add tap-anywhere-to-interrupt that calls `synthesizer.stopSpeaking(at: .immediate)` AND restarts STT.

### 19. Multi-turn drift; long-context decay; `MemorySaver` is process-local
*(Karpathy)* At turn 60 the system prompt's behavioral weight has decayed; no forced compression. `MemorySaver` (`kid_agent.py:48`) holds messages in process RAM under `memory_key = f"kid:{user_id}:{kid_name}:{thread_id}"`; deploy = lost continuity AND lost kill state.

**Fix:** forced compression every N turns rebuilding from `build_system_prompt(...)` (pure!) + summary of last 20 turns. Persist checkpoints to DuckDB (LangGraph has SQL checkpointers).

### 20. Naming: `invariants` should be `Letter`
*(Fowler)* The product calls it "the letter" everywhere user-facing (consent copy, `ReviewLetterView`, `soul_kid.md:71`); the code calls it `invariants`. Rename `invariants → Letter` (with `LetterRules` for sealed parts). Swift type becomes `KidAgentLetter`.

### 21. `KidPickerView` uses NotificationCenter instead of the closure it already takes
*(Fowler)* `KidPickerView.swift:188-199` posts to `.kidPickerSelected`; `HandoffCurtain.swift:44-50` subscribes. The closure `onSelected: (KidAgentConfig) -> Void` is already captured at init (`KidPickerView.swift:8`). Just call it.

### 22. Two-finger-swipe handoff gesture is a single-touch swipe in disguise
*(Fowler)* `HandoffCurtain.swift:58-71` — comment admits SwiftUI can't count fingers. Either ship the explicit button (`HandoffEntryButton`) and remove the gesture, or invest in a UIKit recognizer.

### 23. Soft-policy prompt: non-negotiable block at the END, vibes at the top
*(Karpathy)* Recency bias varies per model; the safety policy belongs at the TOP. Concrete rewrite given in Karpathy's review (R1-R7 hard rules); see his agent transcript.

### 24. `_age_band` private symbol exported into `server.py`
*(Fowler)* `prompt_synthesis.py:401` — leading-underscore, but imported at `server.py:27`. Promote to `age_band(age)` and re-export.

### 25. `KID_DDL` lumps unrelated tables under "kid"
*(Fowler)* `duckdb_storage.py:88` — `auth_tokens` and `consent_records` aren't kid-specific. Split per bounded context.

### 26. `_bootstrap_default_config` writes a row just to render the review screen
*(Fowler)* `kid_agent.py:179-211`, called at `server.py:684-686`. Write a database row to render a screen. Drop it; let `ReviewLetterView` call `/kid-agent/preview` on first read.

### 27. `_generate_preview_messages` makes its own `ChatOpenAI` call
*(Fowler)* `server.py:691-722` — second LLM call per keystroke after a 600ms debounce in `ReviewLetterView.swift:391-396`. Render `voice_examples` from invariants directly.

### 28. Kid PIN default-open
*(Fowler)* `_verify_kid_pin` returns `True` if no PIN. Under COPPA the gate must be default-closed. Flip the default now so the v1 migration is "remove the closed-beta override," not "rebuild the whole gate."

### 29. Constitutional critique is dead code
*(Karpathy)* `moderation.py:445-484` defines `constitutional_critique`; nothing in `server.py` calls it. Remove or wire.

### 30. Unicode tag character / prompt-injection stripping
*(Karpathy)* Tag characters U+E0000-U+E007F are invisible but tokenize as instructions. Strip in `server.py:830` before `moderate_input`.

### 31. Tool-call observation injection — Tavily output unsanitized
*(Karpathy)* `kid_agent.py:74` wires Tavily with no output sanitization. A kid posts a URL containing prompt-injection text; web_search retrieves it.

### 32. DuckDB single-writer at scale
*(Google)* `duckdb_storage.py:201` — single embedded connection, single writer. `--workers > 1` = silent data loss. Document `--workers 1` everywhere; pin Railway to a single replica until you move to Postgres.

### 33. `__del__` calls `export_parquet` on shutdown
*(Amazon)* `__del__` is unreliable on interpreter shutdown. Wire to FastAPI lifespan shutdown event explicitly.

### 34. DEBUG-level logging includes message content
*(Amazon)* `server.py` lifespan sets `logging.basicConfig(level=logging.DEBUG)`; `generate_kid_stream` has `logger.debug(... msg={message[:120]})`. Demote to INFO with redaction in production. Redact `user_id` to a stable hash prefix in Slack payloads.

### 35. `openai` not pinned in `requirements.txt`
*(Google)* `moderation.py:38` does `from openai import OpenAI`; floats with whatever `langchain-openai==1.1.6` pulls. Pin it. Add a comment in `requirements.txt` next to `langgraph-prebuilt==1.0.8` explaining the `ExecutionInfo` rationale.

### 36. No API versioning prefix
*(Google)* No `/v1/` on the new endpoints. The roadmap explicitly anticipates a v1 break. Version now or pay later.

### 37. No pagination cursors
*(Google)* `/kid-chat/transcripts`, `/kid-moderation/events`, `/summary/list` — `limit` only. Past message #N the parent silently loses history.

### 38. `/consent/submit` returns `JSONResponse(400)` instead of `HTTPException`
*(Google)* `server.py:354`. Inconsistent error envelope shape will bite the iOS client.

### 39. No idempotency key on `/kid-agent/config`
*(Google)* Letter resubmission on flaky network creates a new version row each time. Optimistic concurrency via `expected_version` is a partial answer; an `Idempotency-Key` header is the standard fix.

### 40. No request-ID propagation
*(Google)* Cannot grep one event across logs from a Slack alert. Add a `Request-ID` header (UUID), include in structured logs and Slack payload.

### 41. No structured logs
*(Google)* `logger.info("[kid_chat] start user=%s ...")` plain-text. SRE-Book-equivalent: structured for query.

### 42. Crisis script TTS plays at chirpy default rate
*(Karpathy)* When the soft-redirect plays, no special handling — same voice, same rate. A 5-year-old in distress hearing the same chirpy voice is jarring. Slow `utterance.rate = 0.42` and use a calmer voice for crisis-tagged messages.

### 43. Kid-account brute force surface
*(Amazon)* 4-digit kid PIN with no rate limit and no lockout on `/kid-chat` — brute-forceable in seconds. Add: PIN attempts counter, 5-fail lockout, mandatory PIN for kid mode in beta.

### 44. Voice transcripts not mentioned in consent text
*(Amazon)* The current `ConsentView.swift` text doesn't mention voice. Document.

### 45. Speaker confusion (kid hands phone to friend)
*(Amazon)* No defense; the agent has no awareness. Single-session re-prompt or per-session reaffirmation could help.

### 46. `bloomColor` defined twice as keyword sniffing
*(Fowler)* `KidAgentView.swift:189-199` and `KidPickerView.swift:140-151` both string-match `personalityDescription` for `"playful"` / `"warm"`. Move to a method on `KidAgentInvariants` (`bloomColor: Color`) or have synthesis produce a `palette` field.

### 47. `STT_PERTURBATION` eval class missing
*(Karpathy)* No coverage of common Whisper/SFSpeechRecognizer misreads of crisis language.

---

## 🟡 MED — debt to log

- `langchain-agents-pip==0.1.0` is a 0.x package on a kid-safety path. Audit.
- No SBOM, no `pip-audit`, no Dependabot config.
- `daily_summaries` regenerates the LLM call even if no new messages exist; short-circuit on `message_count == existing.message_count`.
- Eval judge has no calibration set checked in (`judge.py:8`). Add `evals/cases/calibration.yaml` (30 cases, hand-written verdicts); CI asserts judge agreement ≥ 0.85.
- No mixed-language / code-switch eval coverage beyond the single rt-024.
- `agent.py` and `kid_agent.py` share no abstraction — wait until the third agent appears, then extract `agents/base.py`.
- The plan says "JWT" but the code ships opaque uuid4 tokens. Reconcile naming/docs.

---

## ⚪️ NIT

- Rename `StreamingModerator` → `OutputGuard` or `ResponseGate` (Fowler).
- Add inline comment in `requirements.txt` about the `langgraph-prebuilt==1.0.8` rationale.
- `KidsHomeSection` and `HomeView` tile nesting was not explicitly flagged; revisit during the iOS naming pass.

---

## Implementation plan (this session)

Given the scope (47 distinct findings, many blockers), I am implementing a tight subset — the convergent NO-SHIP fixes that I can land surgically and verify locally:

| # | Fix | Effort |
|---|---|---|
| ✅ | Update `entrypoint.sh` to stop wiping the DuckDB on deploy (#3) | XS |
| ✅ | Pin `openai` in `requirements.txt` + add comment for `langgraph-prebuilt` (#35) | XS |
| ✅ | Persist crisis lock to DuckDB and gate `/kid-chat` on it (#2 partial) | M |
| ✅ | Wire `kill_agent` from input AND output crisis paths (#2 partial) | S |
| ✅ | Hash auth tokens at rest + add `expires_at` (#1 partial) | M |
| ✅ | Rate-limit `/auth/issue-token` (#1 partial) | XS |
| ✅ | Add `DELETE /family/{user_id}` cascade endpoint (#4 partial) | M |
| ✅ | Force on-device STT + pause STT during TTS (#17, #18) | S |
| ✅ | Sliding-window streaming moderator (#5) | M |
| ✅ | Expand crisis regex categories (#7) | M |

Deferred to roadmap (require infra, separate workstreams, or are architectural):
- APNs push for parent crisis notification (#2 — needs APNs cert)
- App Attest / Apple Sign-In (#1 — separate auth project)
- `KidChatPipeline` extraction (#11 — refactor, no behavior change)
- `KidAgent` domain model (#12 — refactor)
- CI + unit-test bundle (#9 — separate workstream)
- Eval harness rewrite to test prod path (#8 — owns its own week)
- `/metrics` endpoint via prometheus-client (#6 — small but needs deploy plumbing)
- Cost ledger (#10 — needs DuckDB schema + middleware)
- Multi-turn / voice / synthesis red-team eval cases (#8 continued)
- Naming sweep (`invariants → Letter`, `_age_band → age_band`, `KID_DDL` split) (#20, #24, #25)
- Storage repository inversion (#13)

These are added to `docs/roadmap.md` as a "Family Companion v0 — pre-beta blockers" section so they don't get lost.
