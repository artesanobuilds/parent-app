# Parent App ("MVP") — Complete Project Context

Compiled 2026-09-26 for the hand-off to the bb project **Parent Agent**. This is the
single document a new agent or engineer reads to know everything that was built, why, what
broke, what shipped, what the research concluded, and what is still open. It merges the
Claude Code auto-memory (75 notes, Mar–Aug 2026), the repo docs, the git history (146
commits, 2026-02-17 → 2026-08-22) and a code inventory. Treat every claim as context to
verify against the code; the newest memory note is dated 2026-08-22.

**Status on 2026-09-26:** closed beta, live in prod with a handful of real families, no
commits since 2026-08-22, and the project is pivoting. What the pivot is has not been
decided. That decision is the first job of the Parent Agent bb project.

**Naming:** the product is **MVP** ("Most Valuable Parent"). It was "Sway" until
2026-02-17; the iOS entry file is still `SwayApp.swift`. Never call it Sway.

**People:** Miguel Alvarado (founder, builds everything, "divorce-dad" founder voice),
Heather Hannan-Kramer (co-founder/CEO, product + parenting knowledge, "maxed-out-mom"
voice, beta tester), Greg (head of design, owns the Figma files, beta tester). A few
other beta parents (Julio, Pepe, Gina) exist in prod. Never delete real users' data.

---

## 1. Architecture and stack

### Repo layout
- `mvp-backend/` — FastAPI + LangGraph + DuckDB backend. Python 3.13 in Docker, local
  `.venv`. `app/server.py` (2,649 lines) is the app; local port **8904**.
- `mvp/` — SwiftUI iOS app. `mvp/MVP.xcodeproj`, target MVParent, bundle id
  `MVP.MVParent`, **1.93 build 107** as of the last commit. 93 flat Swift files, ~29.6K
  lines. FileSystemSynchronized groups, so new files need no pbxproj edit. No Info.plist
  edits by hand: `INFOPLIST_KEY_*` build settings plus `plutil` for purpose strings.
- `mvp-backend/parent-dashboard/` — Vite/React 19/Tailwind 4 parent web dashboard at
  `/dashboard` (dev :5174). Public product docs at `/dashboard/docs` outside auth.
- `mvp-backend/cms/` — Vite/React/TS admin CMS at `/cms` (dev :5173). Admin writes need
  the `X-Admin-Token` header. Pages: articles, categories, legal, email-sync,
  calendar-sync, testers.
- `spec/look-and-feel/` — Hearth design system spec (tokens, components, surfaces, logo,
  fonts, photography). `tools/lint-design-tokens.py` enforces spec ↔ code.
- `tests/nl-harness/` — natural-language flow tests over HTTP (31 YAML specs → generated
  pytest). `mvp-backend/tests/` — 78 hermetic test files, 529 tests (~585 passing at last
  run incl. parametrized).
- `docs/` — `roadmap.md`, `system-architecture.md`, `history/` (deploy runbook, backup
  ledger, sprint histories 001–009), `design/` (sprint specs, Figma playbook), `GTM/`
  (strategy, research, roast, Ground Zero), `meeting-notes/`, `release-notes/`.
- `pitch/` — pre-seed investor deck (pptx/pdf, 16 slides) + `narrative.md`, `critics.md`,
  `evidence.md`. `setup/` — external-service setup guides (Apple/Google auth, APNs,
  Sentry, Grafana, PostHog, ElevenLabs, Google OAuth, security hardening).
- Both web apps build inside the Dockerfile and ship with every backend deploy. iOS
  ships via TestFlight (internal group "POC").

### Backend modules (all under `mvp-backend/app/`)
- `agent.py` — the ONE merged parent agent (Coach + Chief-of-Staff, merged in sprint-2,
  Aug 2026). `langchain.agents.create_agent`, `ChatOpenAI(OPENAI_MODEL_NAME)`, 24 tools
  (Tavily + profile tools + `cos/tools.py` planning tools). Middleware: PII credit-card
  mask → Summarization (tagged internal so it never streams to the client) → Context
  editing → Tool-call limit. `cos/agent.py` is a shim returning the same agent.
- `thread_repair.py` — pre-flight on every entry: repairs LangGraph checkpoints with
  dangling `tool_calls` (an aborted call otherwise 400s the thread forever).
- `checkpointing.py` — durable SQLite checkpointer at `data/agent_checkpoints.sqlite`
  (gitignored; every family's verbatim conversation).
- `onboarding_agent.py` (chat onboarding), `onboarding_extract.py` (anonymous
  pre-account extraction, HMAC session), `onboarding_warmup.py` (first-run warm-up worker
  + SSE + `/coach/nudge`).
- `kid_agent.py`, `kid_agent_service.py`, `prompt_synthesis.py`, `moderation.py`
  (40 crisis regexes, OpenAI moderation, age classifier, streaming moderator,
  constitutional critique, crisis lock/revive), `convai_endpoint.py` (kid voice, ElevenLabs
  custom-LLM at `/v1/chat/completions`), `parent_convai_endpoint.py` (`/v1/parent/...`).
- `profiling.py` (ProfilingService, in-memory dict snapshotted to `user_data` JSON blobs),
  `memory.py`, `content.py`, `summary.py`, `coach_threads.py`.
- `duckdb_storage.py` (5,953 lines, 235 methods, ~45 tables), `storage.py` interface,
  `migrations.py` (versions 1–24, transactional).
- `cos/` — `planning.py` (cost/conflict/eligibility/coverage-gap engine), `lifecycle.py`
  (the 4-stage board, single source of truth), `tools.py` (1,283 lines), `export.py`
  (XLSX), `outings.py` (quick outings), `verticals.py` (five-door registry), `router.py`
  (`/cos/*`), `prompt.py`.
- `research/` — deepagents deep-research discovery (`RESEARCH_MODEL`), worker pool with
  atomic claim, geo grounding, SSE stream. `watchlist/` — registration windows +
  notifications. `ingest/` — text + vision flyer extraction. `email_sync/`,
  `calendar_sync/`, `integrations/` (Fernet-encrypted Google tokens), `oauth/` (PKCE).
- `auth.py`, `auth_router.py`, `auth_providers.py`, `auth_login_google.py`,
  `auth_pairing.py`, `admin_auth.py`, `rate_limit.py`, `security_headers.py`.
- `household.py`, `circle.py` (792 lines), `blobs/` (S3 presign), `push/` (APNs),
  `analytics/` (PostHog), `observability/` (Sentry + OTel), `telemetry.py` (Slack
  webhook on moderation flags), `cost_logging.py`, `email_smtp.py`, `evals/`.

### Routes (prefix → highlights)
- Root: `/health`, `/chat` (SSE coach), `/onboarding-chat`, `/kid-chat`, `/kid-agent/*`,
  `/profile` (+ `/seed`, `/kids/{name}`), `DELETE /family/{user_id}`, `/consent/*`,
  `/legal/*`, `/content/*` (articles, categories, for-you, search), `/saved`,
  `/share/{token}`, `/coach/threads`, `/voice/convai-token`, `/voice/parent-convai-token`,
  `/push/register-device`, `/blobs/upload-url`, `/cms/*` admin, `/data/export`,
  `/data/download/{file}`, `/debug/report`.
- `/auth/*` (login, refresh, logout, exchange-code, google/start, pairing-code, legacy
  issue-token), `/admin/auth/*`, `/admin/users/{id}/reset|delete`, `/admin/session`.
- `/onboarding/anon-session`, `/onboarding/extract`, `/onboarding/warmup*`, `/coach/nudge`.
- `/cos/*`: chat, verticals, activities, calendar (+sync), recurring, caregivers,
  logistics, todos, windows, plan/board, plan/compare, plan/summary, plan/export.xlsx,
  plan/share, plan/reset, draft-email.
- `/research/runs*` (create, list, candidates, stream, cancel). `/ingest/text|image|artifacts`.
- `/oauth/google/*`, `/cms/email-sync/*`, `/cms/calendar-sync/*`, `/household/*`,
  `/circle/*` (conversations, messages, invites, contacts, requests).

### Data
- Single DuckDB file `data/mvp.duckdb` (single writer, `_ThreadSafeConn` RLock) on a
  Railway volume at `/app/data`. Persists across deploys since 2026-06-20; schema evolves
  only through `migrations.py`. Shutdown exports every table to parquet in `data/`;
  bootstrap on a fresh DB re-imports parquets with column-intersection merge.
- Four content parquets ship in the image and seed prod (articles 45, categories 110 = 11
  parents + 99 children, community_posts, post_replies). Every user-state parquet is
  `.dockerignore`d and gitignored (guard tests exist). `data/mvp.parquet` is tracked and
  always drifts locally; never commit it casually.
- Profiles are schemaless JSON in `user_data`. Tables include tracked_activities,
  activity_candidates, calendar_entries, recurring_appointments, caregivers,
  logistics_assignments, todo_items, registration_windows, window_notifications,
  ingest_artifacts, cos_messages, research_runs, integration_accounts, household_members,
  circle_*, kid_agent_configs, kid_messages, kid_agent_crisis_locks, moderation_events,
  consent_records, legal_documents, legal_acceptances, saved_items, share_tokens,
  push_device_tokens, user_accounts, auth_identities, refresh_tokens, coach_nudges,
  onboarding_warmup_runs, audit_events.
- Migrations of note: v16/17 activity type + RRULE date model, v18 watchlist, v19 index
  hotfix (caused a 30-min prod outage on 2026-07-11), v20 household/circle, **v21 drops the
  community board and DMs**, v22 fit_score/fit_reason, v23 circle_requests + article
  eyebrow, v24 backfill candidate details into `details_json`.

### Models and vendors
- OpenAI only at runtime: `OPENAI_MODEL_NAME=gpt-5.5-2026-04-23` (coach, ingest, outings),
  `RESEARCH_MODEL=gpt-5.2` (set 2026-08-11; discovery 183s → 97s), kid agent default
  `gpt-5.2`, coach thread titles `claude-haiku-4-5` (only Anthropic reference). gpt-5.5
  rejects any non-default `temperature`. `sk-proj-*` keys spend per-project budget; dev
  and prod use different keys.
- Tavily search (`TAVILY_API_KEY` is a hard boot requirement).
- ElevenLabs Conversational AI v2 (two agents: kid-companion-v2, parent-coach-v2), LiveKit
  WebRTC on iOS. Voice and text threads are SEPARATE and do not share memory.
- PostHog Cloud US project 505309 (strict event allowlist, PII denylist, flags via
  `FLAG_<KEY>` env override → PostHog → default; consent-gated on iOS).
- Sentry project `mvp-backend` (errors only). OTel metrics → Grafana Cloud
  `beigemarsh3480.grafana.net`; 4 alert rules in group `cos-health` → Slack
  `slack-mvp-alerts`, all with `no_data_state=OK` (load-bearing). Dashboard uid
  `vertical-expansion`. Cost lines `[COST][LLM|SEARCH|VOICE]` in Railway logs.
- APNs token-based (hand-rolled ES256 JWT over httpx/h2; TestFlight uses PRODUCTION APNs).
- Google OAuth (Gmail readonly + Calendar) via PKCE; Google verification + CASA for the
  restricted scope was never completed (unverified apps cap at 100 users for the project's
  lifetime, non-resettable; exhausting it disables Google sign-in).
- Railway Storage Bucket `photos-blob` for profile photos (no server-side encryption).
- Pins: langgraph 1.2.6, langgraph-prebuilt 1.1.0 (minors must stay aligned or startup
  ImportError), langchain 1.3.10, langchain-core 1.4.8, deepagents 0.6.11, openai 2.14.0,
  fastapi 0.115.0, duckdb 1.5.0, elevenlabs 2.50.0, posthog 7.22.0, cryptography 49.0.0.
  iOS: elevenlabs-swift-sdk 3.2.2, livekit 2.14.1, MarkdownUI 2.4.1, posthog-ios 3.64.2.

### Auth (v2, live since 2026-07-08)
Sign in with Apple + Google. HS256 JWT access tokens (`AUTH_JWT_SECRET`) + rotating hashed
refresh tokens with reuse detection. `current_user` dual-accepts JWT or legacy opaque token
(`AUTH_LEGACY_TOKENS_ENABLED`). Legacy `POST /auth/issue-token {user_id}` still exists for
the closed beta but 403s for any account that has claimed a sign-in identity.
`resolve_account()` claims legacy accounts and, since 2026-08-09, links Apple + Google at the
same verified email into one account (the earlier "keep them separate" policy routed a
returning parent into onboarding). Known unfixed claim-path bugs: reinstall wipes
`user_name`, 30-day legacy TTL, second-provider claim blocked. Retire-legacy checklist:
`AUTH_ISSUE_TOKEN_ENABLED=0` then `AUTH_LEGACY_TOKENS_ENABLED=0`.

### Env vars (names only; values in `mvp-backend/.env`, Railway, `~/.zshenv`)
OPENAI_API_KEY, OPENAI_MODEL_NAME, TAVILY_API_KEY, RESEARCH_MODEL,
RESEARCH_WORKER_CONCURRENCY, KID_*_MODEL, MVP_DUCKDB_PATH, MVP_CHECKPOINT_DB_PATH,
AUTH_JWT_SECRET, AUTH_LEGACY_TOKENS_ENABLED, AUTH_ISSUE_TOKEN_ENABLED, ADMIN_TOKEN,
RATE_LIMIT_AUTH_PER_HOUR (code default 5, prod 60; harness needs 1000+),
RATE_LIMIT_CHAT_PER_MIN, ALLOWED_ORIGINS, ENABLE_HSTS, PUBLIC_BASE_URL,
GOOGLE_OAUTH_CLIENT_ID/SECRET/REDIRECT_URI, APP_OAUTH_CALLBACK_SCHEME=mvparent,
INTEGRATION_ENC_KEY (rotating it kills stored Google tokens), ELEVENLABS_API_KEY,
ELEVENLABS_AGENT_ID, ELEVENLABS_PARENT_AGENT_ID, ELEVENLABS_CONVAI_SECRET, APNS_*,
BLOB_*, POSTHOG_*, SENTRY_DSN, OTEL_EXPORTER_OTLP_ENDPOINT, SLACK_WEBHOOK_URL, SMTP_*
(dormant), FLAG_VERTICAL_V2_EXTRACURRICULARS, FLAG_VERTICAL_V5_TRIPS,
ONBOARDING_EXTRACT_ENABLED, CIRCLE_INVITE_BASE_URL. `mvp-backend/env.example` is the
annotated catalog.

---

## 2. Product as built

### iOS surfaces (5 tabs since beta-v1): Home · Coach · Plan · Circle · Settings
- **Onboarding (Heisman sprint-01, 2026-08-21, current):** 13-step unauth-first funnel:
  splash → cold open → children → topic → sample problem (text / on-device dictation /
  photo / camera) → live extraction check (real stateless extraction via
  `/onboarding/anon-session` + `/onboarding/extract`) → parent tasks → getting ready → coach
  demo → account wall (Apple/Google only, step 10) → paywall (smoke-and-mirrors behind a
  PostHog flag, both Buy buttons just advance, nothing charged; Stripe vs StoreKit
  undecided) → warm-up (4 beats, always reaches 100%) → all set → day-zero Home. Draft
  persists in UserDefaults; the profile seed retries until the server returns 200. There
  is ALSO a conversational path (`/onboarding-chat`) and the two must stay in sync
  (form + chat parity checklist in section 4).
- **Home:** day-zero dashboard: per-person today cards, coach nudge card, YOUR KIDS tiles
  with missing/locked states, COMING UP, FOR YOU editorial feed (`/content/for-you`).
- **Coach:** the merged agent over `/chat` SSE with silent profile extraction and
  `mvp://library/{slug}` article citations; voice via parent-coach-v2 (no consent gate).
  "Chief of Staff" is retired from all UI copy; `/cos/*` paths remain.
- **Plan (Planner):** segments Plan | Ask the coach. Discovery = deep-research run
  (zip, radius, category chips, top-N, free-form focus, SSE live results, "75% match"
  fit scores). Lifecycle board (`/cos/plan/board`): Considering → To register →
  Registered/needs action → All set, plus Blocked; register hook seeds typed to-dos and
  triggers Gmail sync; deletes cascade; `POST /cos/plan/reset`. Overlap/conflict
  detection, coverage gaps, cost roll-up. Flyer ingest (photo → structured activity),
  XLSX export (7 sheets), scoped expiring share links (`full|logistics|therapy`),
  draft-email (never sends), calendar List | Timeline.
- **Five doors ("one agent, five doors", deployed 2026-07-11):** V1 camps/breaks, V2
  extracurriculars (flag), V3 outings, V4 school life (dark), V5 trips (flag). Data-only
  registry in `cos/verticals.py`; RRULE date model; registration-window **watchlist**
  (notify-before-never-after, Grafana miss alert). Quick outings ("what to do this
  weekend", tuned to the youngest kid) via the `SuggestOutings` tool.
- **Circle (sprint-2, 2026-08-08):** household members with roles, private group
  conversations, invites with landing page, mutual-link requirement, circle requests.
  Replaced the public community board and 1:1 DMs (migration v21; 73 real DM messages
  were backed up first; the two beta parents who used DMs were never told their threads
  are gone).
- **Kid companion (Family Companion v0, 2026-05-09):** per-kid agent config, COPPA-scoped
  consent (`ConsentView` says "not yet COPPA-compliant"), 5-layer moderation, deterministic
  crisis lock (`enabled=FALSE` + lock row, parent APNs push, red "Review" pill on Home,
  deliberate Reactivate). Kid voice via kid-companion-v2. Kid PIN is server-complete and
  iOS-orphaned (a set PIN breaks kid chat). **Deferred out of beta and GTM by decision on
  2026-07-15**; the Aug research recommends cutting it entirely.
- **Settings:** 7-card family settings (MVP information, family structure, your family,
  your circle, caregivers, language at home, coach settings) + Library, Saved, Report a
  problem, Legal (CMS-versioned, `/legal/accept`), Connections (Gmail/Calendar), Secure
  your account, Log out, Delete account (`DELETE /family/{user_id}` cascades everything).
  Developer server override via 7-tap on the version.
- **Content:** 45 articles, 11-parent/99-child taxonomy (locked slugs, e.g.
  `raising-kids`, `school-activities`, `care-village`), library no longer browsable from a
  tab; the coach recommends from it. Saved items with snapshots. Community posts unused.
- **Web dashboard:** chat, discovery, plan, profile, invite landing, public docs (15
  pages incl. release notes). **CMS:** articles (TipTap), categories, legal versions with
  publish, email-sync and calendar-sync control panels, testers (reset keeps identity +
  legal; delete).

### Design system
Hearth (June 2026): cream canvas, ink, Fraunces display / Inter / JetBrains Mono bundled
fonts, typographic logo (Fraunces ExtraBold "M"; geometric marks read as faces, rejected),
Midjourney Kodak-Portra photography. Beta-v1 tokens (2026-08-07, Greg's Figma file
`Wb072IjTsBT7Ooqc41UFbK`): canvas `#E9E4DC`, card cream `#F5F3EF`, teal accent `#1B7498`,
saffron kid accent `#E89C2E`, voice navy `#2E3A5F`, radii control 10 / card 18 / sheet
24, cards use shadow not hairline, section headers Inter w800. Values live ONLY in
`mvp/MVP/Theme.swift` and `spec/look-and-feel/DESIGN.tokens.md`; the linter checks
contrast pairs, spec ↔ code drift, and inline hex. Heisman onboarding Figma file
`nAXZQhmvwEpzq3rkBisok7`, spec `docs/design/heisman-sprint01-onboarding.md`. Binding
process: `docs/design/figma-fidelity-playbook.md` (walk every frame into a measured spec
with `tools/figma-walk.py`, translate every property, vector-export every glyph as a
template SVG, verify per section to zero visible diff). Figma MCP caps on a View seat;
use REST with `FIGMA_TOKEN` (expired at last note).

---

## 3. Timeline

| When | What |
|---|---|
| Dec 2025 | "Sway": SwiftUI hello world, FastAPI + LangGraph ReAct coach with SSE, per-user memory, Jung/Becky Kennedy/Maté grounding (docs/history 001–007, pre-git). |
| 2026-02-17 → 02-22 | Rebrand to MVP; content library (45 articles) in DuckDB; Circle community tab. First commits. |
| Mar–Apr 2026 | Railway deploy (Dockerfile, volume, seeding); first TestFlight 1.1 (5) on 03-27; data-sync incident and JSON→DuckDB recovery. |
| 2026-05-07/09 | Production stack committed; 9-step demographic onboarding + `/profile/seed`; Family Companion v0 (kid agent, crisis lock, consent, `DELETE /family`) with a 4-persona critic review that said "block" on everything. |
| 2026-05-27 | Vix review fixes, operator-endpoint lockdown, migration framework. |
| 2026-06-19/20 | Mega-commit: voice v2 (ElevenLabs ConvAI), Chief-of-Staff activity planning, deep-research agent, Hearth design system, CMS, cost logging. DuckDB now persists on the volume. Multimodal flyer ingest. |
| 2026-06-21/22 | Google OAuth, daily Gmail-sync agent, CMS control panel. |
| 2026-06-24/27 | "0 found" discovery incident → worker pool, dedup, backoff, fault-injection harness, Sentry + OTel, Google Calendar sync. |
| 2026-06-28 | Greg's fresh install lost his family (localhost fallback) → durable seed + `ServerConfiguration` rule + root CLAUDE.md. |
| 2026-07-05/07 | Geo-grounded discovery, crisis-regex false positive fix, APNs crisis push verified on device, XLSX export, share links, lifecycle board. iOS 1.51–1.53. |
| 2026-07-07/10 | GTM strategy v2 after the 5-persona roast (verdict RESHAPE); Ground Zero doc; Auth v2 live (07-08); PostHog live (07-09); quick outings; investor deck. |
| 2026-07-11/12 | Vertical expansion phases 0–7 deployed (five doors, watchlist, telemetry); migration v16/v19 outage (~30 min); 4 Grafana alerts; illustrated public docs. iOS 1.66 (80). |
| 2026-07-15/19 | Beta-readiness (Heather's 16 items): logout/delete, Settings, versioned legal, Coach naming + citations, profile photos, DMs, Saved tab, release-notes page, privacy v1.1. iOS 1.67–1.73. Decisions: beta is free; kids' companions deferred; "Circle"/"Planner" naming; three Greg design sprints. |
| 2026-07-22/24 | Heather's voice outage → thread self-heal; voice v2.1 streaming text (1.74–1.75); route-decorator outage hotfix + guard test. |
| 2026-08-07/08 | Greg's beta-v1 redesign: token rewrite, sprint-2 Circle replaces board + DMs (v21), merged coach + planner agent, planner match/overlap (v22). iOS 1.76–1.80 (94) to TestFlight, then backend deploy. |
| 2026-08-09/11 | Consolidated Settings, splash fidelity, onboarding plan-first, cross-provider email linking fix, v23 + v24 deployed, backup ledger. iOS 1.85–1.89 (103; 1.89 never reached TestFlight). |
| 2026-08-21/22 | Heisman sprint-01: unauth-first onboarding with live extraction, day-zero Home, CMS testers, iOS 26.4 white-strips fix, paywall rebuilt to Figma. Backend deployed and prod-verified. iOS 1.90 (104) to TestFlight; 1.91–1.93 (107) committed, TestFlight push of the latest build was Miguel's step. |
| 2026-08-21/22 | Parent-planning-behavior research (~41 agents, 31 source reports) compiled into `report.md/html/pdf`. Never acted on in code. |
| 2026-08-22 → 09-26 | No commits. Pivot decision pending. |

Public release notes (`mvp-backend/parent-dashboard/docs/release-notes.md`) cover
2026-07-18 → 08-21, app updates 1.67–1.91. Backup ledger `docs/history/prod-backups.md`
records five pre-migration snapshots (2026-08-08 ×2, 08-10, 08-11, 08-22); snapshot files
live in `~/Desktop/mvp-prod-snapshot-<date>/` and `snapshots/`, never in git.

---

## 4. Hard-won lessons and conventions

The root `CLAUDE.md` holds the short list that caused real user-facing bugs. This is the
longer list. Every item cost a real incident or a lost afternoon.

**Networking, persistence, contracts**
- A `?? "http://127.0.0.1:8904"` fallback posts to the phone's own localhost on a fresh
  real-device install and silently loses the onboarding seed (two beta users). Resolve
  URLs only through `ServerConfiguration`; guard `tests/test_ios_baseurl_guard.py`.
- User-state writes are durable and verified (persist intent, retry to 2xx, surface
  failure). Views that render server data re-fetch when control returns (`onDismiss` →
  token → `.task(id:)`). Deletes cascade. Key by stable IDs, not names (kid rename via
  name-as-key is still an open gap; the coach's `LearnedAboutChild` can re-create a
  deleted kid).
- iOS Codable is strict: one type mismatch empties a whole list. DuckDB DOUBLE →
  `Double?`. Any shape change touches iOS + dashboard + backend in one go with a contract
  test (`test_onboarding_seed_contract.py`); parallel agents drifted (`all_todos` vs
  `todos`) with no error.
- Onboarding parity: a new profile field touches `profiling.py`, `onboarding_agent.py`
  (models + prompt + docstring), `agent.py`, `server.py` seed model/handler,
  `OnboardingView.swift`, `SwayApp.swift`. `gradeBandOptions` vs `ProfileOptions.gradeBand`
  still hold different values.

**DuckDB / data**
- No `;` inside DDL comments (the DDL string is split on `;`). Index on a
  migration-added column goes in the migration. `CREATE INDEX` cannot share a transaction
  with an `UPDATE` (only fails on a DB with rows → prod crash-loop 2026-07-11); give the
  index its own migration.
- Bootstrap tolerates parquet column drift (intersection insert). Re-export after
  migrations anyway.
- `railway up` uploads the working tree and bakes any `data/*.parquet` into the image;
  user-state parquets must stay in `.dockerignore` (`test_dockerignore_guard.py`).
  `export_parquet` writes relative to CWD, so running it from `mvp-backend/` once dropped
  44 user-state files at the backend root and they got staged.
- Never hand-filter harness rows out of content parquets: `WHERE NOT (user_id = …)` is
  NULL for seed rows and deleted all 27 posts. Restore from git HEAD (which itself carries
  5 harness rows since 2026-08-07).
- In-memory singletons (`profiling_service`, chat/onboarding memory, kid caches,
  checkpoints, blobs, PostHog person) must be evicted on `delete_family`, BEFORE the
  parquet export, or deleted families resurrect in prod (Greg's did). Verify deletes via
  the public GET.
- TestClient exit closes the storage singleton: every test module rebuilds
  `server.storage_backend` before and after.

**Backend / agents**
- Never insert a `def` between a route decorator and its endpoint (auth vanished, 422s,
  30-min voice outage 2026-07-24); `test_route_binding_guard.py`. Unauth returns 401.
- Aborted tool calls poison a LangGraph thread (OpenAI 400s forever); `thread_repair`
  pre-flights every surface. SummarizationMiddleware streamed its summary to clients until
  tagged internal.
- Crisis-locked ≠ vanished: the companion is `enabled=False` with a lock row. The regex
  `hits?` matched "she hit a guardrail"; now `hits?\s+me`. Only kid endpoints gate on
  consent; parent voice must not.
- Research "0 found" came from a single-threaded worker; now pool + atomic claim
  (`UPDATE … RETURNING`), enqueue dedup, cancel-clobber guard, LLM timeouts/backoff. LLM
  calls dominate cost, not Tavily; a batch-record tool cut a run from $2.10 to $0.64.
- gpt-5.5 rejects `temperature`. `--reload` ignores `.env` changes (`touch app/server.py`).
  Check `ps -o etime` before trusting a local smoke test; the server may be stale.
- langgraph and langgraph-prebuilt minors must align (ImportError `ExecutionInfo`).
- Auth: JWKS fetch needs an explicit certifi SSL context locally; PKCE verifier rides in
  signed state; oauthlib logs full tokens at DEBUG (pinned to WARNING); a pasted client
  secret once contained Cyrillic homoglyphs; ASWebAuthenticationSession needs no
  `CFBundleURLTypes`.
- Admin endpoints want `X-Admin-Token` as a header. `railway variables --json` has control
  characters (`json.loads(strict=False)`); Railway API times out ~1/3 of calls; CLI tokens
  expire silently (`railway login` by Miguel); `railway logs` caps ~500 lines.

**iOS**
- SourceKit cross-file "cannot find type" errors are false positives; `xcodebuild` is
  truth. "Unable to type-check in reasonable time" can be an ordinary type error in a big
  view body.
- AVPlayer is wrong for extension-less authed mp3; use `URLSession` + `AVAudioPlayer(data:)`.
  CoreAudio Virus TI / LoudnessManager console lines are host noise.
- TestFlight: PNG icons only (SVG rejected, ITMS-90013), `ITSAppUsesNonExemptEncryption=false`,
  camera + local-network purpose strings required by LiveKit, TestFlight = production APNs.
- Simulator: `simctl spawn defaults write` never reaches the app; only `simctl erase`
  clears scene restoration; `axe tap` coordinates are points (use `--label`); launch env
  needs `SIMCTL_CHILD_`; iPhone 17 Pro is 402×874 pt. Voice needs a physical device.
- LaunchScreen.storyboard handoff breaks whenever the first SwiftUI screen changes.
- Bump `CURRENT_PROJECT_VERSION` +1 and `MARKETING_VERSION` +0.01 after every iOS batch.

**Process**
- Subagents ship plausible no-ops and mislabel real failures as "fixture issues"; read
  the failures yourself; re-grep for dangling symbols after an agent dies mid-edit.
- Every user-facing push gets a dated release-notes entry and, for a new door, a public
  docs page (`test_public_docs.py`). Every new user flow gets a hermetic E2E test and an
  NL-harness flow. New agent concerns get their own module + thin tool wrapper.

---

## 5. Operations

- **Prod:** `https://mvp-backend-production-8678.up.railway.app` (`/health`, `/cms`,
  `/dashboard`). Railway project `mvp-backend`, single instance, volume at `/app/data`,
  `healthcheckTimeout 300`.
- **Deploy:** follow `docs/history/deploy-runbook.md` exactly. Summary: know whether the
  migration drops/alters or changes a shape; `BACKUP_REASON="…" ./tools/backup-prod.sh`
  (uses `/cms/stats` + per-file `/data/download`, never bulk `/data/export`) and commit
  the ledger; ship iOS to TestFlight FIRST when removing routes/columns; green gates
  (`pytest -q`, token linter, `tsc && build`, `xcodebuild`); confirm `git status | grep
  parquet` is empty; `cd mvp-backend && railway up --detach`; verify migrations in boot
  logs, `/cms/stats` (45/110), retired routes 404, one throwaway flow then
  `DELETE /family/{id}`, read-only harness against prod; release-notes entry; bump iOS.
  Rollback: forward-fix > redeploy reverted tree (does NOT undo migrations) > restore rows
  from the snapshot through the API. **Every prod deploy needs Miguel's explicit OK.**
- **Read one user:** `POST /auth/issue-token {user_id}` → `GET /profile` (403 for
  signed-in accounts; then mint an HS256 JWT with `AUTH_JWT_SECRET` directly). **Delete
  one prod user by email:** map email → user_id from `auth_identities` + `user_accounts`
  parquets only, mint a JWT, `DELETE /family/{user_id}`, verify, delete the temp parquets.
  Or CMS `/cms/testers`. Run PII-touching commands via the `!` prefix in Claude Code.
- **Local:** backend `uvicorn app.server:app --reload --port 8904` with `.env` from
  `env.example`; CMS `npm run dev` in `cms/`; dashboard `npm run dev` in
  `parent-dashboard/`; iOS DEBUG targets localhost via `ServerConfiguration`. Harness:
  isolated backend on :8913 with `RATE_LIMIT_AUTH_PER_HOUR=5000`, then
  `BASE_URL=http://127.0.0.1:8913 pytest -q` in `tests/nl-harness` (~5 min). Goldens:
  `RUN_COS_GOLDENS=1 pytest mvp-backend/tests/goldens/` (27/27 baseline). Kid evals:
  `RUN_KID_EVALS=1 pytest test_evals.py`. Local blob emulator `tools/dev_blob_server.py`
  (moto :9333). Docs screenshot pipeline: isolated backend :8907 + synthetic family.
- **iOS automation:** AXe + idb + ios-simulator-skill; DEBUG env hooks
  `UITEST_SKIP_SIGNIN`, `UITEST_USER_ID`, `TEST_SIGNIN`. Only when explicitly asked.
- **External:** Google Drive "MVP" folder (`gws-personal`, multipart only) holds Ground
  Zero and legal drafts; Ground Zero is generated by `docs/GTM/ground-zero.py`. Grafana MCP
  is read-only. Vix (`vix -p`) only when asked.
- **CI: none.** Nothing runs on push; there is no GitHub remote. Biggest infra gap.

---

## 6. Strategy, GTM and research

### Positioning as documented
- Investor narrative (`pitch/narrative.md`): coordinating a family is an operations job;
  MVP is the agent for "the last unmanaged operations job in America". Guiding policy:
  build the agent for one acutely painful, seasonally forced slice (activities + coverage
  before a registration window closes), working for one parent alone. Four refusals: no
  courtroom product; never require the other parent; no marketing to children before
  COPPA; no money in the transaction in v1.
- Through-line from the June/July meetings: "the app is the mom next door: she knows
  everybody's schedule (planner reads everywhere) and she's seen everything before (coach
  as curator of Heather's playbook)".
- Ground Zero (`docs/GTM/MVP-Ground-Zero.docx`, July 2026): brand/voice/audience; the
  critic review flagged scope creep, asked for one hero screenshot, questioned the name.

### GTM strategy v2 (`docs/GTM/gtm-strategy.md`, 2026-07-07, canonical)
Lead with the next seasonal activity-registration episode for the load-bearing parent in
a two-household family, **solo-first** (parent #2 joins via calendar invites + a magic
forwarding address, never an install/account/charge). Retain with the ingestion loop +
registration-window watchlist, not the coach. Price against family organizers,
$99–149/family/yr test range. Privacy as product: logistics durable and exportable, coach
zero-retention (transcripts are discoverable in custody court). Validate with a Family
Snapshot quiz funnel before building more. Gate 0: 48-hour, <$50 DM test with 25
separated/divorced parents. Day-30 gates: 200 emails, median WTP ≥ $100/yr. Honest
ceiling: ~$300K ARR at 24 months as an indie business. The 5-persona roast
(`mvp-idea-roast.md`) scored 3/8/5/5/5 and said RESHAPE: second-parent activation is the
structural flaw, $199 pricing is contradicted, coach-as-retention fails; the watchlist is
the killer feature the council missed. `gtm-research.md` (July) is partly superseded and
contains a fabricated "37M Millennial parents" Pew figure. Diagnosis in the playbook:
product built in silence with zero waitlist; gating question is business vs craft project.

### Parent-planning-behavior research (Aug 2026, `docs/GTM/research/2026-08-parent-planning-behavior/`)
Goal: decide what to double down on, simplify, and cut, with a cited ranking of planning
jobs across Gen Z / Millennial / Gen X parents, an answer on voice vs typing, and a read
on complexity tolerance. Method: ~41 agents (collectors, miners over ~19,000 App Store
reviews and ~2,300 Reddit comments, an ActivityHero index audit, verifiers, quantifiers,
synthesists, a red team), source tiers A–D with Tier D never citable, 12 chart CSVs each
carrying source/tier/method, ~44 killed statistics catalogued, disclosed residual error
(~27% of kills overturned on re-trace). No parent was interviewed; no survey fielded.
Outputs: `report.md` (~19K words), `report.html`, `report.pdf`, `sources.md`, `BRIEF.md`
(four "VERIFIED CORRECTIONS" blocks override the collectors), `DESKTOP-RESEARCH-PROMPT.md`
(23 open gaps for a broader crawl; G1 ParentSquare notification emails, G2 Google CASA).

Headline findings:
- A two-kid family faces ~23 scheduled low-step obligations/yr vs ~16 multi-step
  campaigns: parity, not the 18:1 the first synthesis produced.
- The app has **no manual-add surface at all**, and `build_board` drops any to-do with a
  NULL `activity_id` (`app/cos/lifecycle.py` `if aid:`).
- Modality by evidence: camera > tap-confirm > email-forward > dictation > conversational
  voice (zero instances in either corpus). Planner wait of 1–2 min is 6–12× Nielsen's
  10-second limit.
- Email: ship parent-side auto-forward to a per-family inbound address; reject registering
  our address with schools; keep Gmail OAuth off the critical path (100-user cap).
- First audience = child age 6–12 with employed parents, not a generation. Camp search
  doubles in Nov, doubles in Dec, triples in Jan; Aug–Oct is the dead window.
- Feature-fit verdicts (`raw/S2-feature-fit-verdict.md`): DOUBLE DOWN on Home, camp as a
  seasonal campaign, extracurricular and school_event doors (turn flags on), watchlist,
  coverage gaps, flyer ingest, Google Calendar sync, dictation on all fields, Heisman
  funnel, share links reframed as the second-parent mechanism. SIMPLIFY the Planner (12
  knobs, 16–20 taps), the board (a view, not a storage model), Circle (requires a second
  account; 792 LOC vs a share-link primitive), two chat surfaces → one, the 18-field
  profile. DEPRIORITIZE Coach, outings, Gmail sync, parent voice, XLSX. CUT the kid voice
  companion (~3,300 iOS + ~760 backend LOC, zero demand evidence, FTC 6(b) inquiry,
  COPPA), the trip door, orphaned `SavedView` and the third `ChatView`. BUILD manual add
  (highest priority) and the inbound forwarding address.
- Red team (published unsoftened as report §4): the central ratio is hollow; count ≠
  value (no willingness-to-pay evidence for capture anywhere, and the paywall sits at step
  11 while the centre of gravity moves to unpriced jobs); the watchlist is the best idea on
  the weakest measurement; most cuts were pre-decided. It could not break the Gmail cap,
  the email-sync-can't-discover audit, the ActivityHero measurement, the co-parenting
  counts, or the kid-companion regulatory exposure.
- Pre-registered tests before building: capture thesis (week-4 captures ≥ ~4× tracked
  activities), forwarding-rule completion with 5 parents, watchlist whitespace check,
  extracurricular door-open rate vs camp, instrumentation as
  `capture_started/committed/abandoned` with modality/surface/hour.

Nothing from this research has been acted on in code.

---

## 7. Open work and known gaps (as recorded before the pivot)

- TestFlight push of the latest iOS build (1.93/107); real-device fresh-install walk
  through OAuth to Home never done; Heisman per-section zero-diff verification and Greg's
  open flags.
- Paywall purchase rail (Stripe link-out vs StoreKit) undecided; Circle invite domain
  undecided (`share.mvparent.ai` placeholder); existing beta DM threads unreachable
  post-v21.
- No per-family LLM cost cap ("one bored kid overnight = $4–11k"); no per-run wall-clock
  reaper; no CI; no GitHub remote; Postgres + external queue, at-rest and blob encryption,
  load test, secret rotation, Logto, COPPA workstream all unstarted.
- Auth claim-path bugs; retire legacy auth; prod split-email audit.
- Kid PIN wire-or-remove; name-as-key kid rename; agent re-creating deleted kids; grade
  band parity; GCal push needs `start_ts`; Gmail verification + CASA; school-domain
  allowlist; PostHog flags `kid_chat_disabled`/`research_enabled`/`email_sync_enabled`.
- Voice: persist parent voice turns to chat memory; unify voice/text threads; per-minute
  cost guardrails; gpt-5.5 first-token latency owns p95.
- Taxonomy phase 2 (editorial sourcing; `pregnancy-babies` has 0 articles) and phase 3
  (hierarchical browse) not started.
- Beta readiness leftovers: legal counsel round-trip, Railway CDN toggle, encryption.
- The Aug research's ACT list and TEST-FIRST list (section 6) are the last recorded plan
  and were never started.

---

## 8. Working preferences (Miguel)
Lead with a prose recommendation; ask one crisp question only at a real fork. On plan
approval, execute end-to-end in the same turn. Prod deploys and destructive actions need
explicit confirmation every time. No sleep-polling loops. Bump iOS build numbers after
every iOS batch. Release notes with every user-facing push. Config snippets must be
literally paste-ready. Never invoke Vix or the iOS simulator loop unprompted. Figma UI is
pixel-perfect or it is not done. Real data only in demos, no fake credentials rows.
