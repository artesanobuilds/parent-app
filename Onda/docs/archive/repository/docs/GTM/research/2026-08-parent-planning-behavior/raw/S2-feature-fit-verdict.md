# S2 — THE FEATURE-FIT VERDICT

Synthesist S2. Compiled 2026-08-21. Reads: `BRIEF.md` (both corrections blocks, authoritative),
`raw/S0-workflow-model.md`, `raw/S1-email-decision-memo.md`, P1–P12, M1–M5, V1–V6.
**Product surface independently re-verified against the code on 2026-08-21**, after the Heisman
sprint landed. Every product claim below carries a file path I read. Every demand claim carries a
report and a tier.

Language rule, per V4: **both "SEVERE OUTLIER" and "AT-RISK" are banned** — no screens-to-completion
distribution exists at any tier, so "outlier" is unavailable and every severity grade in P9's benchmark
table is an analyst judgement. Complexity judgements below are labelled `Analyst call` with an explicit
`Evidence: direct / adjacent / none`. Where evidence is thin I say so
rather than rounding up to a cleaner story.

---

## 0. THREE CORRECTIONS TO MY OWN BRIEF, FOUND IN THE CODE

I was told to score the current state and to establish what is legacy and what is new. Three things
in the brief are now stale, and one of them changes a headline verdict.

**0.1 The Heisman sprint is COMMITTED and SHIPPED, not uncommitted.** `git log` shows `b850a3e`
"Heisman sprint-01: unauth-first onboarding, anon extraction, day-zero Home, CMS tester reset"
(2026-08-21 22:19, 26 Swift files, +5,053/−3,127), followed by `781c985` (returning-parent merge fix),
`221db92` (iOS 1.91/105) and `d6436ff` (release notes). The working tree holds exactly one uncommitted
Swift change — a 7-line `.containerBackground` cosmetic fix in
`/Users/miguelalvarado/Coding/parent-app/mvp/MVP/CircleView.swift`. Nothing about the sprint is
pending.

**0.2 The legacy onboarding wizard no longer exists.** It was not put behind a flag; it was deleted.
`/Users/miguelalvarado/Coding/parent-app/mvp/MVP/OnboardingView.swift` (1,044 LOC, net −1,000 in the
sprint) is now a thin host whose `flow` array is 100% Heisman screens:
`.splash → .coldOpen → .children → .topic → .sampleProblem → .extractionCheck → .parentTasks →
.gettingReady → .coachDemo → .accountWall → .plan → .warmup → .allSet` (13 steps,
`OnboardingView.swift:206`). `/Users/miguelalvarado/Coding/parent-app/mvp/MVP/SwayApp.swift:118`
routes on one `@AppStorage("onboarding_completed")` boolean. There is no variant switch and no A/B.
**"Legacy wizard vs. Heisman funnel" is not a live choice — it is a completed migration**, and P9's
onboarding findings must be re-scored against the new funnel, not the old one.

**0.3 "Discovery is 38% of the tool surface" is true of the AGENT'S TOOLS and false of the
codebase.** S0's 38% counts 8 of 21 LangChain tools in
`/Users/miguelalvarado/Coding/parent-app/mvp-backend/app/cos/tools.py`. By lines of code,
`app/research/` is **1,185 LOC of 28,237 backend LOC = 4.2%**; adding its storage layer and the
`StartDiscovery` tool gives ~5.8%. Both framings matter and they say different things: discovery
dominates *what the agent can reach for* and is a small fraction of *what has been built*. That
asymmetry is good news for the recommendations below — re-centring the product away from discovery is
a prompt-and-tool-surface change far more than a rewrite.

---

## 1. THE FEATURE-FIT MATRIX

Verdict vocabulary: **DOUBLE DOWN** · **SIMPLIFY** · **KEEP-BUT-DEPRIORITIZE** · **CUT** ·
**BUILD-NEW**.

### 1.1 The five tabs

| Surface | What it does | File path | Demand evidence FOR | Demand evidence AGAINST | Cohort / child age served | Competitive position | VERDICT |
|---|---|---|---|---|---|---|---|
| **Tab bar (5 tabs: HOME/COACH/PLANNER/CIRCLE/SETTINGS)** | Custom bottom bar, no flags, no gating; `enum Tab {home, agent, planning, circle, settings}` | `mvp/MVP/MainTabView.swift:64,152-166` (337 LOC) | P9: 5 tabs is **WITHIN NORM** — Apple HIG and consumer convention are 3–5, "no contrary evidence found" (Tier: analyst call, evidence adjacent) | `Analyst call: 94 SwiftUI views / 44 tracked screens is the exact shape feature-fatigue predicts users will request and then punish. Evidence: none — no view-count benchmark exists at any tier.` The adjacent literature is strong though (Thompson/Hamilton/Rust, *JMR* 2005): pre-use, **62.3% chose the 21-feature model vs 9.2% the 7-feature** (Study 1, n=130); after use, perceived capability fell significantly (F(1,186)=5.09, p=.025) and usability fell as features rose (F(1,185)=33.13, p=.000) (Study 3, n=190). P9's consequence: *"**Any prioritization built on stated preference will over-build**"* | All | Neutral — structure, not differentiation | **KEEP.** The tab count is the one structural thing P9 clears. The problem is what is *behind* two of them. |
| **HOME** | Per-person "today" cards (max 3 activities/person), coach nudge, kids companion section, editorial card; auto-presents SetupTail | `mvp/MVP/HomeView.swift` (602), `HomeTodayCards.swift` (248, NEW), `HomeDashboardService.swift` (414) | S0/P7: a **time-ordered** surface is the one that can hold Q2/Q3 objects; "the board's organizing principle is lifecycle position; a family's organizing principle is time." P9: 82% of trial starts happen install-day (RevenueCat, Tier B) → day-zero value is decisive | Home renders a *flattening of the board* (`PersonToday` over `PlanBoard`), so it inherits the board's population problem: if the board only holds discovered activities, Home is empty for the ~280 shallow objects/yr | 6–12 and 13–17 primarily | Strong — a chat assistant has no persistent daily view (P11) | **DOUBLE DOWN.** Home is the correct centre of gravity and the day-zero Home was the right build. It needs objects to show. |
| **COACH** | Parenting-advice chat, `ChatViewModel(mode:.coaching)`, content cards, save-reply, history, **the app's only voice entry** | `mvp/MVP/AgentView.swift` (525); voice at `:173` | P11: 81% of US parents have used AI for a parenting task, 43% weekly (Lurie 2026, **Tier C — no panel, no MoE, no sampling method disclosed**); behaviour advice 43%, health info 53% | P11 #22: parents most distrust AI for **discipline advice (50% hesitant)**, health/medical (38%), emotional guidance (37%) — Coach's exact subject matter. This is also the surface a free general assistant replicates best | All | **Weak.** ChatGPT/Gemini do parenting advice for free, at higher quality, with no install | **KEEP-BUT-DEPRIORITIZE.** Retention furniture and the paywall's stated value, not the wedge. Do not invest further; do not cut (it is the only always-something-to-do surface in August). |
| **PLANNER** | Two segments: `Plan` (6-stage board, chips, list/timeline, sort/filter, export/share) and `Ask the coach` | `mvp/MVP/PlanView.swift` (2,573 LOC — the largest view in the app), `PlanViewModel.swift` (661), `PlanService.swift` (1,018) | P3/P4: this is where the money is — $893–954/child summer camp, $1,490.66/participating child on sports | P9: **12 knobs**, 16–20 taps to a saved plan. `Analyst call: high burden. Evidence: adjacent` (Baymard tested optimum ≈8 fields; 17% of cart abandoners cite length) | 6–12 | Genuinely ours per P11 (persistent mutable board) | **SIMPLIFY.** See §1.3. |
| **CIRCLE** | Group conversations + roster + invites; unread badge; requests accept/decline | `mvp/MVP/CircleView.swift` (565), `CircleService.swift` (200), `CircleInviteView.swift` (198), `MemberProfileSheet.swift` (792); backend `mvp-backend/app/circle.py` (792) | M1/M5: systems die at the seam between two people. M5's most-repeated exact phrase: *"no one else got onboard with it"* / *"I was the only one using it"* | M4 (counted, regexes + denominators published, replicated by V5): reviews turning on the other parent's participation are only **OFW 4% (28/641), AppClose 3% (14/534), 2houses 2%, TalkingParents 2%** — and the dominant concrete refusal is **"the ex won't PAY,"** not "won't install." Circle as built requires the second adult to have an MVP account: `claim_invite` and `accept_request` both `Depends(current_user)` (`app/circle.py`) | All, notionally | Weak — iMessage and a shared Google Calendar are free and already installed (M5) | **SIMPLIFY hard — see §2.5.** Right problem, wrong mechanism. |
| **SETTINGS** | Profile, Connections, Library, legal, add-kid, plan, logout, delete | `mvp/MVP/FamilySettingsView.swift` (588) | — | — | All | Neutral | **KEEP.** |

### 1.2 Discovery, the board, and the verticals

| Surface | What it does | File path | Demand evidence FOR | Demand evidence AGAINST | Cohort / child age | Competitive position | VERDICT |
|---|---|---|---|---|---|---|---|
| **Discovery / research agent** | `deepagents` harness + `TavilySearch(search_depth="advanced")` + `record_activity_candidates`; ZIP-anchored, bundled GeoNames ZIP centroids to stop town hallucination; off-request-path worker (concurrency 3), SSE progress, 1–2 min | `mvp-backend/app/research/graph.py` (579), `router.py` (222), `geo.py` (210), `worker.py` (173) = **1,185 LOC**; entry `app/cos/tools.py:1047 StartDiscovery`; iOS `PlanView.swift` findActivitiesCard | **M3 (Primary, measured by the miner, reproduced EXACTLY by V5):** ActivityHero's entire live national inventory is **9,008 bookable sessions** of 94,848 records (90% expired); **California = 48% of live**; 20 states have <50 live sessions; Minneapolis (16th metro, 3.7M people) shows **35 listings**, Wichita **8**. M3's verdict: *"A web-search agent is the right architecture… the only architecture that has any chance of working nationally."* Municipal parks-and-rec, YMCAs, churches, districts publish on the open web and are in no marketplace | **P3 (Tier B, AA3PM n=30,515, MoE <±1):** the measured pain is ACCESS, not CHOICE. 24% of enrolled children were **waitlisted first**; **77% of wanted enrollments never happen** (22.6M unmet vs 7M enrolled); P3 verbatim: *"nothing in the Tier A/B corpus shows parents struggling to decide which camp… **a discovery/fit-scoring agent is solving the cheap half of the problem.**"* Selection settles cheaply on child's interest 30% / cost 25% / **schedule fit 13%** (LendingTree 2025, Tier C). P11: the ChatGPT edge is *"12–18 months wide at most"* | 6–12 only. S0: 0–5 has zero organized-activity load (the federal instrument does not ask below 6); 13–17's modal summer activity is a **job/internship (32%)** | Mixed — see §2.1. Beats every incumbent on coverage; loses to free chatbots on the choice question it actually answers. **And M3 measured the demand side directly:** there is **no consumer iOS app** for ActivityHero, Sawyer, Mommy Poppins, Macaroni KID or Camperoni (V5-confirmed via iTunes Search); Care.com's Activities & Camps app has **21 lifetime ratings and zero written reviews**, while Campanion (post-enrollment, not discovery) has **40,351 ratings at 4.92★**. M3: *"Parents will install and open a kids-activity app; **they just won't do it for discovery**"* and *"**parents do not return to a discovery product between seasons.** Discovery is a 2–3 week annual burst; the relationship lives elsewhere."* Also: *"**parents will not pay for a directory.** The measured market has no example of anyone succeeding at that"* | **SIMPLIFY + RE-AIM.** Keep the engine (it is defensible and cheap in LOC); demote it from the Planner's front door; re-point the output at *access* — see §2.1. |
| **6-stage lifecycle board** | `considering / to_register / registered·needs action / all_set / blocked / declined`; free-text status column, any→any transitions, hooks on crossing | `mvp-backend/app/cos/lifecycle.py:52-65` (608 LOC); iOS `PlanView.swift:1600 stageGroup`, `:618` chip row | P11: *"A chat assistant has no persistent, mutable board… Getting this out of ChatGPT means re-pasting state every session."* Correct for Q1 objects — camp, class registration, hosted birthday, trip (S0 §3.2) | **S0's five code-level failures, which I re-verified.** An orphan obligation is *invisible*: `build_board` (`lifecycle.py:302-315`) does `aid = t.get("activity_id"); if aid:` — **a to-do with a NULL `activity_id` is dropped from the board entirely** and surfaces only via `GET /cos/todos`. Recording a settled one-off truthfully files it under *"Registered and nothing left to do"* (collapsed). `on_enter_watched` seeds a *"forward the confirmation email"* to-do when Gmail is unconnected — **N=1 becomes N=2 by machine action.** Default status is `exploring` → section *"Saved ideas."* Meanwhile ~23 obligations/yr (V2-corrected, honest band 20–26) for a 2-kid family are N=1–3 | 6–12 for Q1; useless at 0–5; rarely populated at 13–17 | Genuinely ours **conditional on the state being maintained for the parent** (P11) | **SIMPLIFY.** Keep the six stages as a *view over deep objects*; stop using them as the storage model for all objects (S0 §4.2). |
| **`camp` vertical** (ON, no flag) | `week_block`, coverage=Y, email_sync=Y, registration_watch=Y | `mvp-backend/app/cos/verticals.py`; `default_doors()` at `:361` | P3: the money and the acute pain. 87% report work disruption; 49% dread summer; day camp is the modal summer arrangement (33%) | 1–2 episodes/year (P4 verbatim: *"Camp is a 1–2 episode/year job"*). P7: **dead in August, September, October** — i.e. right now | 6–12 | Strong | **DOUBLE DOWN** (as a *seasonal campaign*, not as the year-round centre). |
| **`extracurricular` vertical** (flag `vertical-v2-extracurriculars`, **default OFF**) | `recurring_weekly`, coverage=Y, watch=Y | `verticals.py`; gate at `app/cos/router.py:415-446`, `default=False` | **Reach: 72.7% of US children 6–17** did ≥1 organized activity in the past 12 months (P4 #12, NSCH via HRSA/Census, n=26,488 of 33,618, CI 71.7–73.7, **Tier A**) — the largest reach number for any vertical. P4 verbatim: *"Extracurriculars are a 150–250-event/year job."* **94.83 min/day of pure logistics** on a sports day (driving 27.56 + other-parent comms 20.06 + coach comms 16.92 + equipment 30.29) vs 65.21 spectating (P4 #3, Aspen/Utah State n=1,848, Tier B). $1,490.66 per participating child. P4's own verdict: *"**The 'extracurricular' vertical being feature-flagged OFF is the largest misallocation this research surfaces… The vertical flags are inverted relative to demand.**"* | **Two hedges I must carry.** (1) The AP-NORC "logistics above cost" stat is **directional only** — BRIEF: *"Ipsos KnowledgePanel, not NORC, and its 'logistics above cost' gap is directional only — at ±4.9 on n=510, 76 vs 74 round identically."* State it as *"logistics is named at least as often as cost,"* never as "logistics beats cost." (2) **Rec-sports sell-out is unproven** — P4 §2: *"Sell-out evidence is negative where it exists — Minneapolis explicitly guarantees a team placement to everyone who registers. Treat 'activities sell out' as unproven for rec sports."* So the *registration-race* urgency does **not** transfer from camp to this vertical | 6–12 and 13–17 — the widest age span of any vertical | No incumbent owns the cross-kid view; P4 #34 (primary vendor docs): TeamSnap bills *"per team, not account"*, SportsEngine has *"no way for divorced parents"* to share a child. P4: *"That is not a product gap the incumbents are about to close — it is their billing model"* | **DOUBLE DOWN — and turn the flag ON.** Highest reach, highest volume, widest age span, dark by default while the two on-by-default doors both want to run a web search. |
| **`outing` vertical** (ON, no flag) | `date_model="none"`, no coverage, no email_sync, no watch; already bypasses the lifecycle entirely | `verticals.py`; `mvp-backend/app/cos/outings.py` (327 LOC), docstring: *"deliberately its OWN self-contained flow, NOT a branch of the camp machinery… Nothing is persisted"* | P7: outings are one of three near-aseasonal families (CV 0.142) that flatten the annual load curve. P6: it is the one place a local, kid-age-aware, calendar-aware agent beats ChatGPT | P6 verbatim: *"high frequency, near-zero willingness to pay, no measurable articulated pain."* Incumbents (Macaroni KID 1,000+ editions, Mommy Poppins **16 metros** per V5, Facebook groups) are free and ad-funded and have been for 15 years | **All — and uniquely so.** P1 §2: *"**The one vertical that survives at every kid age is `outing`** — which is, notably, one of the two verticals currently on by default. The default-on choice looks right"* | Free substitutes have won | **KEEP-BUT-DEPRIORITIZE.** Demote from a door to a chip / a chat answer, which the code already treats it as (`outings.py` persists nothing). It is a *retention* surface, not a paid job — P6: *"Better as a retention/habit surface inside a product bought for something else than as a paid job."* Do not invest. |
| **`school_event` vertical** (flag `vertical-v4-school`, **default OFF**; roadmap.md:44 says deliberately unset) | `single_date`, ingest_taxonomy=Y — the only vertical with a task-chain builder | `verticals.py`; `mvp-backend/app/ingest/taxonomy.py` (79 LOC: permission_slip / fee / picture_day / spirit_day / fundraiser / general) | **P5 #40 (NHES:PFI 2023, n=19,562, Tier A — S0 calls it "the single best number in P5"): 6.0 parent-attended school activities per child, ~11.6 per 2-kid family/yr.** Already-known: 80+ school emails/month, 62% missed something. This is the highest-frequency *hard-deadlined, institution-set* object class | Permission-slip frequency has **no citable source at any tier** (P5 searched specifically); S0's ~12/yr is an estimate. P12/V6: the school-platform aggregation matrix has 6–7 BLOCKED cells and the **ParentSquare verdict is UNSOURCEABLE** (login-gated help centre) | 6–12 and 13–17 | No incumbent concept; ParentSquare/Infinite Campus are *sources*, not organizers | **DOUBLE DOWN — turn the flag ON.** It already has the only per-kind task-chain builder in the codebase. Its date model (`single_date`) is the only one that renders a one-off correctly. |
| **`trip` vertical** (flag `vertical-v5-trips`, **default OFF**) | `date_range`, coverage=Y | `verticals.py` | Nothing survives verification | **P6, and the rejection got STRONGER on verification.** V3 corrected P6's own cross-battery comparison: within-battery, *"planning the trip"* ranks **27%, 6th of 17** obstacles — and 6% among parents unlikely to travel. 2–4 trips/yr against a free substitute the target user already uses: **59% of travelers with children have already used ChatGPT or similar for trip planning** (MMGY Fall 2025, n=4,503, Tier C). Layla ($1B planned trip value) exited to Expedia July 2026; travel-planning platforms shut at ~2x the rate of other travel segments | None | **Worst geometry in the portfolio** — parents are the *heaviest* AI trip-planning users, not the underserved ones | **CUT.** Delete the door, the flag, the prompt section and the playbook. Keep `trip` as an `activity_type` chip only. |
| **Registration watchlist** | Watches `registration_windows`; `t_minus_7` + `day_of` (opens−1h, or 18:00 local the evening before when time unknown); never notifies after open; 5-min poll with catch-up; durable-first (DB row + fallback to-do inside one txn, then push, retried each sweep to opens+2h) | `mvp-backend/app/watchlist/` (411 LOC: `service.py` 145, `windows.py` 105, `worker.py` 244); auto-created by `lifecycle._maybe_watch_registration` for verticals with `registration_watch=True` | **P3 is unambiguous that this is the expensive half.** *"The expensive half is knowing the exact date and minute a specific provider opens, having the form pre-filled, and not missing it. The product already has the right primitive for this — the registration-window watchlist with push notifications — and it is buried behind a 12-knob discovery tab."* P3 documents a YMCA selling ten weeks in ~90 seconds, last accepted application timestamped 7:01:30. **Camperoni charges $295/yr for a HUMAN to do this** (V5: CONFIRMED verbatim from their own CMS post, "1 week free then $295.00 per year," staffed by "local camp planning and youth activity experts") | Only `camp` and `extracurricular` carry `registration_watch=True`, so its addressable object count today is ~5–7 registrations/family/yr. It reaches a parent only if APNs is configured (the fallback to-do always lands). The window data has to come from somewhere — today from `details.registration_opens_at`, which discovery or ingest must populate | 6–12 primarily; 13–17 for club/travel sports | **The strongest position in the product.** M3 heads its section *"The registration-window problem — VERIFIED as whitespace"* and states: *"**The repo's belief is correct, and slightly understated. As of 2026-08-21 nobody has shipped a national, cross-provider, parent-side 'tell me when registration opens for the specific camps I care about' product.**"* Adjacent products (Campium, SwiftEnroll, CampDoc, ACTIVE) are **provider-scoped** waitlists. And: *"**Camperoni — the one named competitor — has NOT shipped it as software… If the company whose entire thesis is camp registration is doing it by hand, the automated version does not exist.**"* $295/yr, humans, **5 metros** (V5-confirmed: Twin Cities, Duluth, Rochester MN, Denver, Boston; Atlanta `active:false`) | **DOUBLE DOWN — hardest.** See §2.2 for why it survives the density objection that discovery does not. |
| **Coverage-gap detection / `uncovered_weeks`** | Pure stdlib; keys coverage on `(kid_name, week_start)`; vertical-aware via `provides_coverage` | `mvp-backend/app/cos/planning.py:261,303` (594 LOC) | P3: school-break coverage is **8–15 closure episodes/yr**; 60% of working parents burn ≤2 weeks PTO on closures/PD/snow days; 60% of caregivers report someone missed work or cut hours. S0 rates it the highest-pain job | The unit of time is a week, which is right for camp and wrong for everything else (S0 §1.3-D). No school-calendar ingestion exists — the parent must tell it which weeks are closed | 6–12; partial at 13–17 (teens self-cover); **inapplicable at 0–5** (no school calendar to have gaps against) | Genuinely ours (P11) | **DOUBLE DOWN**, conditional on §3's build-new item: it needs a school calendar to be automatic rather than declared. |

### 1.3 Capture and ingestion

| Surface | What it does | File path | Demand evidence FOR | Demand evidence AGAINST | Cohort | Competitive position | VERDICT |
|---|---|---|---|---|---|---|---|
| **Photo / flyer ingest** | `POST /ingest/text` + `/ingest/image` (jpeg/png/webp/heic/heif, 8MB); one structured-output LLM call → `materialize()` writes artifact + `tracked_activity` (status `exploring`, or `pending_eligibility` + confirm to-do if the kid is under-age — *never* auto-WATCHED) + calendar entries + to-dos; multi-item (`materialize_all`, cap-and-park); prompt-injection hardened with `<<<INGEST>>>` delimiters | `mvp-backend/app/ingest/extract.py` (471), `router.py` (185), `taxonomy.py` (79); iOS `mvp/MVP/IngestView.swift` (350), PhotosPicker (deliberately no photo-library permission prompt) | **M1, direct customer language, 5★:** *"The new feature that allows you to create events from your camera or from pictures you have taken already of flyers or posters etc. is genius. It literally makes inputting events into your calendar effortless and super quick."* P5 (Tier A): screenshotting information to "save" it **impairs later recall** (digital capture effect, 7 experiments, *Memory & Cognition* 2026) — parents photographing a flyer are building a write-only archive. That is measured demand for exactly this door | Nothing in the corpus against it. The weakness is placement, not concept: it is reachable **only from the Planner** (`PlanView.flyerCard` / `ingestEntry`) | All ages; strongest 6–12 and 13–17 | **M2 measured the competitive set and this is the consensus intake:** of eleven live products, **eight accept email forwarding as a primary intake**, four are SMS-native, and **at least six accept a photo of a paper flyer** — while *"in-app chat + forms is the ONLY model in this table that appears in no successful competitor as a primary channel."* M1 on Skylight: *"**Capture-without-typing (photo / email forwarding) is the #1 delight driver. This is the most product-relevant finding in the entire mining exercise.**"* M5, the parents' own verb: *"**I take a picture of it**"* — *"Never 'I scan it,' never 'I type it in.' **Picture.**"* | **DOUBLE DOWN.** The single best-evidenced surface in the product relative to its build cost. Promote it out of the Planner. |
| **Gmail sync** | `gmail.readonly`; matches senders against tracked activities' contact email/domain over `newer_than:14d`, restricted to WATCHED activities, then feeds the *same* extractor as `/ingest/text` | `mvp-backend/app/email_sync/sync.py` (188), `worker.py` (163), `router.py` (71); `app/oauth/google_flow.py:32-46`; iOS `mvp/MVP/GmailService.swift` (194), `IntegrationsSettingsView.swift` (297) | Already-known: 80+ school emails/month, 62% missed something | **S1's decisive audit, which I re-verified.** The built integration **cannot discover anything new** — if no registered activity carries a contact email it returns zero with *"no registered camps with a contact email to search."* It is a 14-day enrichment sweep over senders the parent already entered. And it is **doubly gated**: `_DEFAULT_SCHEDULE = {"enabled": False, …}` (`email_sync/router.py:16`), all routes behind `require_admin_token` (no parent-facing trigger exists), plus the OAuth restricted scope. P12/V6 (CONFIRMED, and understated): the unverified-app cap is **100 users over the GCP project's entire lifetime, non-resettable**, and exhausting it *disables Google sign-in*; "Testing" is not a holding pattern because test-user authorizations expire every **7 days**, taking the refresh token | Would serve ~half of US parents (Gmail share) | Blocked by a gate an external body controls | **KEEP-BUT-DEPRIORITIZE, per S1.** Do not put it on the critical path; do not add users to the beta allowlist. |
| **Inbound forwarding address (B′)** | Does not exist. `grep -rni "mailgun\|postmark\|sendgrid\|ses\|inbound_email"` over `mvp-backend/app` returns nothing | — (the *brain* exists: `ingest_artifacts.source` already enumerates `paste\|imessage\|photo\|screenshot\|pdf\|gmail\|**forward**` at `duckdb_storage.py:949`) | S1 scores it **69.5/77.5 vs Gmail OAuth's 35.0** — wins on the highest-weighted criterion (onboarding friction), no reviewer, no ToS violation in P12's entire matrix, ~$5/mo at 1M inbound, and it is **the only option with a mechanism for the second parent** (no install, no account, no payment) | S1 §6.4 names the real risk: **silent failure** (the 18-month Skylight case), and the desktop-web requirement for setting a Gmail forwarding rule on a phone. V6: Gmail forwarding is **not** a collapsed step — the source user must return and click Save Changes, and Google shows a week-long warning banner | All | Uncontested | **BUILD-NEW.** 1–2 engineer-weeks. See §3. |
| **Google Calendar sync** | Genuinely two-way. Push: owned `calendar_entries` (source≠gcal) → Google, stamping `provider_event_id`. Pull: external events return as `source='gcal'`, `kind='external'` so conflict/coverage see real commitments. Window −1d/+90d. Scope `calendar.events` — **sensitive, not restricted, no CASA** | `mvp-backend/app/calendar_sync/sync.py` (185), `worker.py` (164), `router.py` (71) | S0: *"genuinely vertical-agnostic… the one subsystem already built at the right altitude."* P9 flags the decision-relevant void: **"share of US households sustaining a shared digital family calendar: NO DATA FOUND AT ANY TIER"** — so nobody knows the denominator, but the calendar is the substrate every M5 respondent already lives in (*"Good ol' Google Calendar"*) | Also gated off by default (`calendar_sync/router.py:19` `enabled: False`, admin-token routes) — though iOS `GmailService.syncCalendar` does expose a manual `POST /cos/calendar/sync`. No Apple or Outlook calendar support | All | Table stakes that incumbents fail at — M1's counted corpus: sync complaints in **6.8% of 5,847 sub-4-star reviews** | **DOUBLE DOWN.** Right altitude, wrong default. Turn the scheduled sync on and add Apple/Outlook. |
| **Dictation (NEW)** | `SFSpeechRecognizer(en-US)` + `AVAudioEngine` + `SFSpeechAudioBufferRecognitionRequest`, on-device where supported; publishes partial transcripts; permission on first mic tap | `mvp/MVP/DictationController.swift` (140 LOC, NEW). Consumers: **onboarding only** — `OnboardingHeismanChrome.swift:280` (`HeismanMicAccessory`/`HeismanTextCard`), `OnboardingHeismanScreens.swift:168`, `OnboardingHeismanTail.swift:15` | **P8 (Ruan et al. 2016, n=32, Tier A):** speech is **161.20 vs 53.46 WPM** for transcription with a 20.4% lower error rate. P8's conclusion: *"voice wins when the user is emptying a formed thought ('swim lessons Tuesday at four')."* P5 (Tier A, n=52×2, within-subject, dz 0.71–1.29): **five extra clicks significantly reduced whether people offloaded an intention at all** — capture must be one gesture | P8: speech **collapses to 7.8 WPM vs 32.5 typing for composition**, and users prefer the keyboard for error correction. So the architecture must be voice-in / **text-out-and-editable** — which `DictationController` already is (it publishes an editable transcript) | All | Nobody in the organizer category ships this well; M1's counted corpus treats voice as a nice-to-have | **DOUBLE DOWN — extend it.** The hard part is built and correct. It touches 3 files and 0 of the app's ~58 other text-entry fields. |
| **Manual add / to-do creation** | **Does not exist anywhere in the app.** Verified: the only client POST that creates an activity is `PlanService.trackActivity`, whose sole call site is `PlanViewModel.saveCandidate:593` (pin a *discovery candidate*). `PlanService.todos()` is a **GET only**; there is no create-todo route in the client. Home's "Add event" link merely switches tabs | `mvp/MVP/PlanViewModel.swift:593`, `PlanService.swift:660` | S0's central argument; P5's offloading-tax experiment (Tier A); M1's counted verbatims — *"Ultimately these extra steps. Have been a barrier to wider use in our family"* (Cozi 2★), *"Too many steps to submit an event"* (2★) | The honest counter: P6 shows the highest-frequency discretionary job has near-zero WTP, and P9's calendar-adoption void means nobody knows whether families sustain a capture habit at all | All | Every incumbent has this; we uniquely do not | **BUILD-NEW — the single highest-priority item in this report.** See §3. |

### 1.4 Conversation, voice, and Circle

| Surface | What it does | File path | Demand evidence FOR | Demand evidence AGAINST | Cohort | Competitive position | VERDICT |
|---|---|---|---|---|---|---|---|
| **Two separate chat surfaces** | COACH tab (`ChatViewModel(mode:.coaching)`, voice, content cards, history, `agent_kind:"coaching"`) vs. `Ask the coach` inside Planner (`/cos/chat`, 21 tools, no voice, no content cards, `agent_kind:"planning"`). A *third* generic `ChatView.swift` (426 LOC) still exists | `mvp/MVP/AgentView.swift` (525), `CosChatView.swift` (335), `CosChatViewModel.swift` (94), `ChatView.swift` (426) | Separation is defensible internally: different tool sets, different threads, different prompts | Nothing in the corpus supports two chat entry points with the same label. Both are called "coach." M5: *"the more complex the system, the faster I stop using it."* P9 flags the 94-view surface count as the shape feature fatigue predicts (`Evidence: none` — no view-count benchmark exists) | All | Neutral | **SIMPLIFY.** One conversational surface, one name. Route by context, not by tab. Delete the orphaned third. |
| **Parent voice calls** | ElevenLabs ConvAI over LiveKit, full-duplex; whole-turn transcripts; `show_article` client-tool → on-screen cards. **One entry point: the mic in the Coach tab** | `mvp/MVP/ParentVoiceView.swift` (256), `ParentCompanionCoordinator.swift` (165), `KidVoiceSessionManager.swift` (539, shared); backend `mvp-backend/app/parent_convai_endpoint.py` (386) | P8: our core cohort is the most voice-equipped in America — smart-speaker ownership peaks at 30–49 (41%), daily chatbot use peaks there (34%, Pew 2026 n=5,119) | **M5 found ZERO instances of conversational voice planning in ~2,300 Reddit comments; the only voice grammar present is "Hey Siri, remind me to…" — capture, not conversation.** P8: smart-speaker owners issue **12.4 requests/week** (Edison/NPR 2022) — under two a day, mostly music/lights/timers; *"There is no evidence anywhere in the literature that a US consumer population has ever adopted voice for a multi-step, high-stakes, comparison-heavy task."* Alexa's >$25B loss is the market's verdict. Kowalczuk & Musial (n=860, **German, intention not behaviour** — V5 corrected the attribution from the non-existent "Distel et al.") find continuance intention significantly lower in public, shame the mediator — and a parent's planning moments are semi-public by construction | All, notionally | Siri/Alexa/Gemini own the two-second command; nobody owns the two-minute call because nobody wants it | **KEEP-BUT-DEPRIORITIZE.** Do not cut (it is built, it costs nothing to leave, and P8 §6 flags LLM voice as a possibly-moving ceiling — on vendor-grade evidence). Do not extend. **Do not let it consume the roadmap slot dictation should have.** |
| **Kid voice companion** | Full LLM agent (`ChatOpenAI` + `TavilySearch` — **web search wired to a child**) behind a 5-layer moderation pipeline, crisis lock, crisis push to the parent, PIN/end_call; four-phase iOS coordinator with no dead ends; parent→kid device handoff | `mvp-backend/app/kid_agent.py` (222), `convai_endpoint.py` (536); iOS `KidAgentView.swift` (668), `KidVoiceSessionManager.swift` (539), `KidCompanionCoordinator.swift` (229), `KidSettingsSheet.swift` (767), `ReviewLetterView.swift` (487), `KidAgentService.swift` (423), `ConsentView.swift` (176) — **~3,300 iOS LOC + ~760 backend LOC** | **None. I searched the corpus and found zero demand evidence at any tier.** The closest adjacent number cuts the other way: P11 #5 (Pew 2026) puts companionship at **4%** of adult chatbot use | **P11's verdict verbatim: "Not a win — a liability."** FTC **Section 6(b) inquiry opened 2025-09-11** into consumer AI companion chatbots and minors, ordering seven companies to explain safety testing and COPPA compliance; amended COPPA Rule effective 2025-06-23; enforcement is real and expensive (**Disney $10M**, Apitor $500K, Sept 2025). 84% of parents concerned about AI misusing young people's data; 82% about AI impersonating kids (Common Sense/LRP+Echelon 2026, Tier B); **a majority of parents of 0–8s explicitly do not want AI acting as their child's friend** (SSRS panel n=1,004, MoE ±3.4, Tier B). The app's own `ConsentView.swift` says it out loud: *"This is closed beta — **not yet COPPA-compliant**."* | Nominally 13+ per the consent picker's top band, but the band list starts below that | Irrelevant — the question is regulatory, not competitive | **CUT.** The largest single block of non-core code in the app, carrying the highest regulatory exposure, with zero demand evidence in a corpus that looked for it. See §2.4. |
| **Circle** | See §1.1 | `mvp/MVP/CircleView.swift`, `mvp-backend/app/circle.py` | M5 (qualitative, non-representative, **skews heavily to r/adhdwomen and r/ADHD**): the most-repeated exact phrase in the corpus is *"no one else got onboard with it."* M1: systems die at the seam between two people | M4 (counted): the dominant refusal is **won't PAY**, and M4's own read is that *"the MVP strategy's proposed mitigation — invite the second parent via a calendar invite plus a forwarding email, never an app install — directly and correctly dodges failure mode (a), which is the biggest one."* **Circle as built does the opposite**: it is an in-app conversation surface requiring the second adult to hold an MVP account. M4 also warns there is no evidence a *passive-recipient* second parent produces a coordinated outcome | All | iMessage + shared Google Calendar, free and installed | **SIMPLIFY to a zero-install, zero-cost participation layer.** See §2.5. |

### 1.5 Onboarding, profile, and export

| Surface | What it does | File path | Demand evidence FOR | Demand evidence AGAINST | Cohort | Competitive position | VERDICT |
|---|---|---|---|---|---|---|---|
| **Heisman unauth-first funnel (NEW, LIVE)** | 13 steps; **account wall at step 10 of 13** — nine screens of real product before any sign-in, including a live server-side extraction; answers persist to `OnboardingDraft` in UserDefaults as typed; returning-parent data now merges rather than being discarded | `mvp/MVP/OnboardingView.swift` (1,044), `OnboardingHeismanChrome.swift` (409), `OnboardingHeismanExtract.swift` (516), `OnboardingHeismanScreens.swift` (273), `OnboardingHeismanTail.swift` (489), `AnonOnboardingService.swift` (166 — 60-min anon token, never persisted, 401→re-mint-once) | **P9 (RevenueCat, Tier B):** 82% of trial starts happen the same day as install; **55.4% of 3-day-trial cancellations occur on Day 0** (V4-corrected scoping). P9 named the old funnel's core defect as *"there is no product value anywhere inside those 10 screens"* — the extraction check at step 4 is exactly the fix, and it happens before the account wall | The funnel is still 13 steps with a **fixed sequence and no conditional branching**, and the paywall sits at step 11. `Analyst call: still long. Evidence: adjacent` — no screens-to-completion distribution exists at any tier, so this cannot be scored, only flagged | All | Ahead of the category | **DOUBLE DOWN.** This was built before the research landed and it anticipated the finding. See §5. |
| **SetupTailView (the second setup sequence)** | Still auto-presents as a sheet from Home via `considerAutoSetupTail()`. Now a single scroll rather than a stepped walk. Asks household type, language at home, then per kid: age, grade, school style, plus four expandable free-text rows (interests / dislikes / challenges / strengths) | `mvp/MVP/SetupTailView.swift` (717); trigger `mvp/MVP/HomeView.swift:174-183`, sheet at `:163` | It collects real personalization inputs the coach uses | **P9 called this "the highest-leverage single cut in the report"** — a second forced sequence at the moment of arrival inverts what the Day-0 data demands (18% of cart abandoners quit rather than create an account, a *smaller* ask than five editors). The Heisman sprint rewrote it (±942 lines) but **did not remove the auto-present** | All | — | **SIMPLIFY.** Stop auto-presenting. Make it a Home card the parent taps when they want a better coach. Keep the content. |
| **The 18-free-text-field profile screen** | `LearnedProfileView` — "gathered from your conversations." I counted **exactly 18 `axis: .vertical` free-text fields** in `ProfileEditorViews.swift:870-925`: 6 parent (parenting style, dreaded moment, support system, support boundaries, co-parenting, mental-health notes) + 12 per kid (temperament, emotion regulation, social profile, learning profile, neurodiversity, sensory notes, sleep routine, health notes, escalation pattern, school context, teacher notes…) | `mvp/MVP/ProfileEditorViews.swift` (1,004 LOC) | It is an *editor over agent-inferred state*, not a form the parent must fill — a materially better design than P9 assumed. **This is the right architecture and the corpus says so**: P11 names passive accumulation as the competitor's structural advantage — *"ChatGPT memory accumulates the same facts PASSIVELY, from conversation, at zero onboarding cost… We charge a large setup toll for something the competitor gets for free by listening"* — and calls the toll *"**our worst competitive liability and it is entirely self-inflicted**"* | P9: an average whole e-commerce checkout is 11.3 fields; Baymard's tested optimum ≈8; free text is the most expensive field type in Baymard's taxonomy. **`Analyst call: one screen exceeds an entire average checkout by ~1.6x in the most expensive modality. Evidence: adjacent`** (checkout fields are largely autofillable, ours are generative — V4 notes this makes the comparison *understate* our burden, and that it must be published as a comparison, never as a score) | All | — | **SIMPLIFY.** Keep it as a read-mostly "what the coach believes" review surface; put dictation on every one of the 18. |
| **XLSX export** | Multi-sheet workbook (activities, calendar, logistics/coverage, to-dos + derived cost/conflict/gap summary), pending/confirmed cell colouring, red gap flags | `mvp-backend/app/cos/export.py` (163); route `app/cos/router.py:819` | None found at any tier | None found — it is simply unevidenced either way. No PDF, no ICS, no CSV | — | Neutral | **KEEP-BUT-DEPRIORITIZE.** 163 LOC, zero maintenance, no reason to remove. But **ICS export would be evidenced and XLSX is not** — M5's respondents live in Google Calendar. |
| **Expiring share links** | `POST /cos/plan/share` mints a scoped expiring token (`full \| logistics \| therapy`); public no-login HTML at `GET /share/{token}` | `app/cos/router.py:861`; `app/server.py:659-690`; `share_tokens` table (`duckdb_storage.py:2282-2330`, migration v11) | **This is the mechanism M4 says works** — zero-install, zero-cost, no account for the second adult. AppClose's 1M+ Android installs accumulated *while it was free*. It is already built and already the right shape | It is buried in a Planner menu and framed as an export, not as *the way you bring in the other parent* | All | The thing incumbents charge per-parent for | **DOUBLE DOWN — reframe.** This 30-line-ish primitive is a better answer to the second-parent problem than 792 LOC of Circle. |
| **PaywallView** | In-funnel only, step 11 of 13, post-auth. Not reachable from Settings or any tab | `mvp/MVP/PaywallView.swift` (337); sole call site `OnboardingView.planScreen:539` | RevenueCat (already-known): hard paywall converts ~5x freemium. V4: model annual retention from **44.1% yearly vs 17.0% monthly** — a 2.6x plan-type effect that dwarfs the ~1.4x AI effect | Placing it before the parent has seen the board is a bet the funnel's step-4 extraction has already delivered value | All | — | **KEEP.** |
| **`SavedView`** | **Orphaned — zero call sites.** `SavedService` still writes (Coach's save-reply bookmark), so bookmarks accumulate with no way to read them | `mvp/MVP/SavedView.swift` (188) | — | It is a live write path to a dead read path — a data-loss-shaped bug, not a feature decision | — | — | **CUT or re-link.** Pick one this week. |

---

## 2. SCORING AGAINST THE STRONGEST COUNTER-EVIDENCE

### 2.1 Discovery: ACCESS vs CHOICE — both are true, and the resolution is to keep the engine and change its output

The tension is real and I will not split it.

**P3 is right that we are solving the cheap half.** Its evidence is the best-methoded in the corpus
(AA3PM 5th ed., n=30,515, ≥200 interviews per state, MoE <±1, Tier B): 24% waitlisted before
enrollment, 77% of wanted enrollments never happen, and selection resolves on child's interest (30%)
and cost (25%) with schedule fit at 13%. P3's own sentence is the indictment: *"a discovery/
fit-scoring agent is solving the cheap half of the problem."* One caveat P3 volunteers and I must
carry: **the 24% is an afterschool measure used as a camp proxy** — it is a borrowed number.

**M3 is right that the engine is the only architecture that could work.** Its ActivityHero audit is
the strongest single item in the program (V5 reproduced it exactly: 94,848 sessions, 9,008 live, all
per-state and per-metro cells identical). A licensing strategy is dead: the best-integrated national
catalog is ~9,000 live sessions with 48% in California, 20 states under 50, Minneapolis at 35 and
Wichita at 8. The supply that matters — municipal parks-and-rec, YMCAs, churches, districts — is on
the open web and in no feed.

**They are not in conflict, because they answer different questions.** M3 answers *"if you need to
find local supply, is web search the right way?"* — yes, decisively. P3 answers *"is finding local
supply the parent's expensive problem?"* — no. So the honest synthesis is:

> **The discovery engine is a correct solution to a real but cheap problem, and it is also the only
> instrument that can produce the input the expensive problem needs.** A registration window is not
> published in any feed either. The engine's most valuable output is not a fit-scored candidate list;
> it is `details.registration_opens_at` — the field that arms the watchlist.

Concretely: keep `app/research/` (1,185 LOC, 4.2% of backend), stop making it the Planner's front
door, and change what it optimizes for. A discovery run that returns eight fit-scored candidates and
no open-dates has produced the cheap half. A run that returns three known-good providers **with their
registration dates and a watch armed on each** has produced the expensive half.

Two risks M3 states about the engine that I am not going to soften: many municipal rec catalogs are
JS-rendered SPAs (its probes of ActiveNet URLs returned 301/302 into marketing shells), so an agent
reading static HTML misses the highest-value segment; and **freshness, not coverage, is the failure
mode** — a returned camp whose registration closed is functionally identical to ActivityHero's
April-2023 soccer camp, and parents will punish it the same way.

There is one more thing the corpus says about the 1–2 minute wait that no amount of re-aiming fixes.
P9: Nielsen's 10-second attention limit, so the run is **6–12x the threshold** — and P9 is explicit
that a progress indicator buys "tens of seconds, not two minutes." `Analyst call: the async wait is
the discovery surface's binding constraint. Evidence: direct (Nielsen is canonical) applied to an
adjacent context (no parenting-app wait-tolerance study exists).` The answer is provisional results,
backgrounding and a push notification — which the backend already supports (`ResearchWorker`, SSE
progress, off-request-path).

### 2.2 The watchlist survives the objection that kills discovery

This is the most important asymmetry in the report and it deserves to be stated precisely.

Discovery is **density-dependent**. Camperoni's CEO said the quiet part out loud (M3 #12): below
~50 providers in a radius the product has no reason to exist. That is why every parent-side discovery
business is economically confined to dense metros — Mommy Poppins' **16 regions** (V5-corrected from
12) is that constraint expressed as an editorial footprint. Our engine relaxes the constraint but does
not remove it: M3 is explicit that output quality *"will still track local supply density."*

**The watchlist is not density-dependent.** A parent in Wichita with eight discoverable listings still
has exactly one YMCA whose registration opens at 7:00 a.m. on a Tuesday in February, and missing it
still costs them the summer. The value of knowing the minute does not scale with the number of
alternatives — it scales with the *scarcity* of the one you want, which is inversely related to
density. **The watchlist is worth more in thin markets, where discovery is worth least.** That is a
genuinely unusual property and it is the strongest strategic fact I found.

The whitespace is verified and I will state the corrected version. V5 confirmed all three Camperoni
claims from their own CMS post (published 2024-08-06, last updated 2026-07-31): Concierge is *"1 week
free then $295.00 per year,"* staffed by *"Camperoni's team of local camp planning and youth activity
experts,"* across exactly **5 active metros** (Twin Cities, Duluth, Rochester MN, Denver, Boston;
Atlanta present but `active:false`). **V5 also corrected M3's inventory read: Camperoni's live index
holds ~4,324 records against ActivityHero's 9,008 live — roughly one-half, not one-eighteenth.** So
Camperoni is *denser than we thought* inside five metros and still absent from the other ~380. The
correction weakens "Camperoni is not a national competitor" as a throwaway line and strengthens the
underlying point: **the registration-race job is valuable enough that someone sells it for $295/yr
performed by humans, and nobody has automated it.**

M3 makes the same point in its own words, and it locates the moat precisely:

> *"the moat here is not the notification, it is **knowing the date**. Registration-open dates are the
> least-structured data in this entire space — they live in a PDF, a Facebook post, last year's page
> that hasn't been updated, or nowhere at all until a provider decides. **A watchlist that requires
> the parent to type in the date is a calendar. A watchlist that finds and re-checks the date is a
> product nobody has.** That is the same capability as the discovery agent, aimed at a narrower and
> much more painful job — and unlike discovery, it is not density-dependent: **a Wichita parent with
> 8 candidate programs has exactly the same problem as an SF parent with 40, and is strictly worse
> served today.**"*

That sentence is the whole argument for §2.1's re-aim: the discovery engine's most valuable output is
the date, not the candidate list.

**There is one more reason to favour the watchlist that no other report in the corpus makes, and it
comes from P2's read of Daminger** (*American Sociological Review* 2019, 70 interviews / 35 couples,
Tier A, qualitative). Cognitive labour decomposes into anticipating · identifying options · deciding ·
monitoring, and — per the BRIEF's authoritative correction — **only *decision-making* is exempted as
roughly equal; "identifying options is also equal" is NOT established.** P2 draws the product line
directly: *"the noticing ('registration opens Feb 3') and the tracking ('did we ever confirm the
carpool?') are hers. **The choosing ('which camp') is genuinely joint.** Our Planner does discovery and
decision support — **the shared middle**. Our watchlist, conflict detection, coverage-gap detection and
to-dos do anticipation and monitoring — **the part that is hers alone.** That is where the acute pain
is, and it is the part the product should lead with."*

**Honest limits, and one of them is serious.** The watchlist's addressable object count today is
small: only `camp` and `extracurricular` carry `registration_watch=True`, giving ~5–7 armed windows
per family per year. Its input (`details.registration_opens_at`) has to come from discovery or
ingest. Delivery depends on APNs being configured, though the code is careful — one transaction
writes the notification row *and* a fallback to-do before the push is attempted
(`watchlist/worker.py`), so a push failure degrades rather than loses.

And **P4 contradicts P3 on how far the race framing travels.** P3 builds the race thesis on a
press-tier, single-market, non-survey anecdote (the Traverse City YMCA, named source, attributed
interview, but explicitly *"not a survey — anecdote with attribution"*). P4 says the opposite for its
own domain: *"**Sell-out evidence is negative where it exists** — Minneapolis explicitly guarantees a
team placement to everyone who registers. Treat 'activities sell out' as unproven for rec sports."*
Resolution: the race is real for **premium municipal/YMCA summer day camp** and unproven for
**rec-league extracurriculars**. Do not let the watchlist inherit P3's urgency when it is extended to
`extracurricular`; extend it there for the *deadline*, not the *race*.

**Finally, the honesty item.** P11 rates the watchlist *"the single clearest defensible capability in
the list"* — and the evidence it cites for why ChatGPT cannot do it (P11 #41: scheduled tasks cannot
be event-triggered, no webhooks, cannot run more than hourly) is sourced **solely to usecarly.com**,
which V6 killed as **Tier D and as a direct competitor's SEO site** — no method page, no n, no
fielding window, ~200 listicles. **So the single clearest defensible capability rests on a killed
source.** Nothing about the whitespace finding (M3, primary, App Store sweep, Camperoni-does-it-by-hand)
depends on it — that stands on its own. But the specific claim *"a general assistant cannot watch a
page and push you"* must be **verified in-product before it goes in a deck**, and it is a 20-minute
test.

### 2.3 The board does not degrade to N=1, and I verified the mechanism myself

S0 documented five code-level failures. I re-read the code and can confirm the sharpest one, which is
worse than "renders awkwardly":

```
# mvp-backend/app/cos/lifecycle.py:302-315, build_board
aid = t.get("activity_id")
if aid:
    ...
```

**A to-do with a NULL `activity_id` is dropped from the board entirely.** The storage layer permits
the free-standing obligation — `add_todo(..., activity_id: Optional[str] = None)`
(`duckdb_storage.py:5371`), and the `AddTodo` tool accepts it (`tools.py:397`) — and the board simply
does not render it. It surfaces only through `GET /cos/todos`. So the lightweight primitive exists in
the schema, is reachable from the agent, and is **invisible in the product**. That is not a design
disagreement; it is a dangling half-implementation.

Set that against V2's corrected load: **~23 obligations/yr, honest band 20–26**, for a 2-kid family
(sourced-only floor ~15.06, dropping to ~9 if two siblings share a school; ED and urgent care excluded
because they are unscheduled). Every one of those is N=1 to N=3. S0's ratio — shallow objects
outnumbering deep ~18:1 by count and ~3:1 by total steps — rests partly on two unsourced step counts
(permission slips ~12/yr and birthday parties attended, both of which P5 searched for and found
nothing at any tier); removing both drops the shallow count from ~280 to ~250 and the ratio survives.

I am not going to overclaim the consequence. **The counter-argument is real and P9 states it:** three
verticals defaulted off is rated **WITHIN NORM** — exactly what the feature-fatigue literature
prescribes — so this is not a complexity emergency. And P6 shows the highest-frequency shallow job has
near-zero WTP, while P9's void (*"share of US households sustaining a shared digital family calendar:
NO DATA FOUND AT ANY TIER"*) means **nobody knows whether families sustain a capture habit at all.**
If they do not, the 250–280 shallow objects are a number, not a market. That is precisely why the call
below is paired with a falsifier rather than asserted.

### 2.4 The kid voice companion: no demand evidence exists anywhere in the corpus

I looked for it specifically. There is none — not at Tier A, B, C, or in the weak-signal sections.
The nearest adjacent measurement points the wrong way: companionship is **4% of adult chatbot use**
(Pew 2026, n=5,119, Tier A/B).

Against that: an FTC Section 6(b) inquiry opened 2025-09-11 into exactly this feature class, ordering
seven companies to explain safety testing, minor-use limits and COPPA compliance; the amended COPPA
Rule in force since 2025-06-23; enforcement at $10M (Disney) and $500K (Apitor) in September 2025;
84% of parents concerned about AI misusing young people's data and 82% about AI impersonating kids
(Common Sense/LRP+Echelon 2026, Tier B); and a majority of parents of 0–8s explicitly not wanting AI
to be their child's friend (SSRS panel n=1,004, MoE ±3.4, Tier B). P11's verdict is one line:
**"Not a win — a liability."**

The code raises the exposure further than the brief implies. `mvp-backend/app/kid_agent.py` builds the
kid agent with `TavilySearch` in its tool list — **live web search wired to a child's conversation** —
and `ConsentView.swift` states the position in the product's own words: *"This is closed beta — not
yet COPPA-compliant."* The surface is roughly **3,300 iOS LOC + ~760 backend LOC**, the single largest
non-core block in the app, plus a 5-layer moderation pipeline, a crisis-lock state machine, crisis
push notifications, and a consent-versioning system — all of which must be maintained forever.

The engineering is good. That is not the question. **CUT.**

### 2.5 Circle: the right seam, the wrong mechanism

M1 and M5 establish the seam. M5's most-repeated exact phrase across a dozen unrelated threads is
*"no one else got onboard with it"* / *"I was the only one using it,"* and its three stated reasons for
abandonment are: it became *"another thing to maintain"*; one-sided adoption; and *"most apps want you
to build out a whole system before you get any value out of them."* M5 must be carried with its
caveats — qualitative, non-representative, browser-driven individual comments, **skewing heavily to
r/adhdwomen and r/ADHD**, with only 4 usable quotes on "what they wish existed."

M4 is the counted evidence and it names the mechanism precisely. It publishes its regexes and
denominators and V5 replicated all of them. Reviews turning on the other parent's participation are a
*floor* of 2–4% (OFW 28/641, AppClose 14/534), and the concrete refusal is **money, not installation**
— M4's read: *"The ex won't pay. This is the single most common concrete refusal in the corpus."* M4
then endorses the mitigation explicitly: *"invite the second parent via a calendar invite plus a
forwarding email, never an app install — directly and correctly dodges failure mode (a), which is the
biggest one."* AppClose's 1M+ Android installs accumulated while it was free.

**Circle as built does the opposite of what M4 endorses.** `claim_invite` and `accept_request` both
sit behind `Depends(current_user)` in `mvp-backend/app/circle.py` — the second adult must hold an MVP
account to read or reply. Unclaimed members can be added to a thread (`user_id IS NULL`) and the
invite preview is public, so the bones of a zero-account path exist; the participation path does not.

Meanwhile the product **already ships** the mechanism M4 describes, in the wrong place and under the
wrong name: scoped expiring share links (`POST /cos/plan/share`, public no-login HTML at
`GET /share/{token}`), and two-way Google Calendar sync. A calendar invite plus a read-only link
requires zero installs, zero accounts and zero payments from the second adult.

**M4's design rule is the sharpest sentence in the corpus on this question, and it decides the
verdict:**

> *"**jobs where the output is a personal artifact (a record, a log, a schedule I can see) survive the
> ex's non-participation; jobs where the output is a joint action (a payment, an agreement, a shared
> plan) collapse.**"*

A board, a watchlist alert and a coverage-gap report are personal artifacts. A shared conversation
thread is a joint action. Build the artifacts; stop building the joint action.

Two counters I will not paper over. **M4 finds no evidence that a passive-recipient second parent
produces a coordinated outcome** — its own verdict on the zero-install invite is *"unfalsified for
**reach** and unsupported for **completion**."* Receiving a link is not doing the pickup, and M4 notes
the invite dodges the "won't pay" refusal but not the "participates badly" one, *"and (b) is fatal for
a planning product in a way it is not for a messaging product."* M5 supplies the concrete failure:
*"we tried a method where I'd send a calendar invite to him, but then he'd have to actually see it in
his email and 'accept' the invite, and that didn't work for us **because he never saw them**."*
Second: M1's complaint-*ranking* is analyst judgement, not measurement (no regex, no denominator, its
two rankings contradict each other) — the counted numbers over 5,847 sub-4-star reviews are **price
14.2%, sync 6.8%**, a more modest claim than "the seam is the top complaint."

**Verdict: SIMPLIFY.** Keep the household roster and the invite. Cut the in-app group-conversation
product (a messaging app competing with iMessage). Re-point the invite at the share link and the
calendar.

### 2.6 Trips: cut, and the verification made it easier

P6 rejected it. V3 then found P6's headline comparison was invalid — *"73% affordability vs 43%
planning"* compared two different survey batteries — and the corrected within-battery figure is
**worse for the vertical**: *"planning the trip"* ranks **27%, 6th of 17** obstacles, and 6% among
parents unlikely to travel. Add: 2–4 trips/yr; **59% of travelers with children already use ChatGPT or
similar for trip planning** (MMGY Fall 2025, n=4,503, Tier C) — parents are the *heaviest* AI
trip-planning users, not the underserved ones; Google ships free persistent editable itinerary Canvas;
Layla exited to Expedia in July 2026; travel-planning platforms shut down at ~2x the rate of other
travel segments. P6's own words: *"That is the worst possible wedge geometry."*

**CUT.** The flag is already off, so the cost of the decision is deleting a registry entry, a prompt
section and a playbook — not a rewrite.

### 2.7 Voice calls vs dictation: the app has the wrong half, and now has both

P8's finding is the cleanest inversion in the corpus, and it is *no longer entirely true* — which is
the good news.

The evidence: dictation is 3.0x faster with a 20.4% lower error rate for transcription and collapses
to 7.8 vs 32.5 WPM for composition (Ruan et al. 2016, n=32, Tier A). Conversational voice has no US
adoption benchmark at task depth: 12.4 requests/week for smart-speaker owners (Edison/NPR 2022),
mostly music/lights/timers; Alexa's >$25B loss. **M5 found ZERO instances of conversational voice
planning in ~2,300 comments, and the only voice grammar present is "Hey Siri, remind me to…"** — which
is capture, not conversation. V5 sharpened this and I must carry the condition: corpus-wide, voice
mentions run 0.68% vs capture 0.43%, so *"capture is mentioned far more than voice"* is **false as
stated**; it is true only **within products that ship capture** (Jam 7.95% vs 0%; Skylight 0.99% vs
0.51%). The conclusion survives; the sentence needs the condition.

The app now ships both halves. `DictationController.swift` (140 LOC, `SFSpeechRecognizer` +
`AVAudioEngine`, on-device where supported, publishing an editable partial transcript) is **exactly**
the voice-in/text-out architecture P8 prescribes — including the detail that Ruan's subjects preferred
the keyboard for correction. It is wired into three files, all onboarding. It touches none of the ~58
other text-entry fields, none of the 18 profile fields, and neither chat composer.

**The gap between "built" and "deployed to the surfaces that need it" is the cheapest large win in this
report.**

### 2.8 The category's death pattern, which no single feature verdict captures

M2 mined what has already died — Yohana (US 2025-09-30, Japan 2026-01-30, domain now NXDOMAIN), Milo
(announced 2026-01-12), Maple (sunsets 2026-12-31; team acquihired by a luxury-travel company), Dola,
Facebook M. Four compounding killers, and every one of them lands on a surface scored above:

1. **The mental-load paradox.** *"Every one of these products asks the most overloaded person in the
   household to do setup work in order to be relieved of work. The debt is paid up front, in full, by
   the person with the least slack; the payoff is probabilistic and arrives later."* One reviewer in
   eleven words: *"I found it more complicated to get my tasks into than it was to just handle it
   myself."* → this is the case for B1, S4, and D3.
2. **Reliability is binary, not gradual.** *"Family logistics have no tolerance for an 85% extraction
   rate, because the 15% is a missed dentist appointment or a blown registration deadline. Once a
   parent catches one wrong entry, they revert to manual and keep doing manual forever."* M1 calls it
   *"a trust cliff, not a gradient."* → this is the binding constraint on D2 and B2, and it is why
   `extract.py`'s blast-radius law (never auto-WATCHED) is correct even though it costs a tap.
3. **Single-player adoption in a multi-player job.** *"The only mechanisms that demonstrably move the
   second adult are the ones that require **no adoption at all**: an SMS the spouse already receives,
   a group chat he's already in, or a screen on the kitchen wall he already walks past."* → §2.5.
4. **Unit economics — pick your poison.** Human-in-loop earns the warmest reviews at a 10–40x price
   premium but forces metering, and metering is the #1 complaint; full automation sells at $39–99/yr,
   *"but at that ARPU you cannot fund the model quality that failure mode #2 demands. Yohana — the
   richest parent in the category — died anyway, twice, on two continents. **Nobody has found the
   middle.**"*

Milo's founder, after six years of research and three of building: *"Too early to build the kind of AI
that reliably, delightfully, powerfully lightens the load **without adding it back somewhere else**."*
The structural problem she names and could not solve: ***"someone has to run point."***

**One inversion worth testing.** The only enthusiastic voice signal anywhere in the corpus is voice as
**output**, not input: Nori's outbound phone-call reminders — *"It actually alerts you with a phone
call and other means which is great for me bc I'm super bad about turning off all notifications"* (5★)
— corroborated by M5's ambient-output cluster (*"My Alexa reads me my events from the calendar the
night before. And then announces everything 1 hour ahead"*; *"It broadcasts on all devices across the
house"*). M2: *"That inverts the usual assumption and is worth testing."* The product has a
full-duplex conversational voice stack and no spoken-briefing output. Counterweight: M4 finds
missed-notification complaints in **14–15%** of AppClose/OFW/Fayr reviews and calls them *"the angriest
reviews in the corpus"* — an outbound channel you cannot deliver reliably is worse than none.

---

## 3. THE PRIORITIZED LIST

### 3.1 DOUBLE DOWN (5)

**D1 — The registration watchlist, promoted to a first-class product surface.**
(a) *Strongest evidence:* P3, verbatim — *"The expensive half is knowing the exact date and minute a
specific provider opens… The product already has the right primitive for this — the
registration-window watchlist with push notifications — and it is buried behind a 12-knob discovery
tab."* Corroborated by V5's CONFIRMED Camperoni Concierge at $295/yr performed by humans in 5 metros.
(b) *Counter:* today it can only arm ~5–7 windows per family per year, and it depends on an
`registration_opens_at` field that something else must populate; the AA3PM 24%-waitlist number is an
afterschool measure borrowed as a camp proxy.
(c) *Effort:* small-to-medium. The engine is built (411 LOC, durable-first, catch-up semantics). The
work is a user-facing "watch this signup" surface, extending `registration_watch=True` to
`school_event` (slot sign-ups, conference bookings), and making a watch armable from a pasted URL
without a discovery run.
(d) **FALSIFIER:** instrument `window_notification_sent → registration_completed`. If fewer than ~30%
of armed windows convert to a registration the parent attributes to the alert, the watchlist is a
notification nobody acts on, and its "verified whitespace" is whitespace because the job does not
need automating.

**D2 — Photo/flyer + inbound ingest, promoted out of the Planner.**
(a) *Strongest evidence:* M1's counted review corpus, direct customer language, 5★: *"create events
from your camera or from pictures… is genius. It literally makes inputting events into your calendar
effortless and super quick."* Plus P5's Tier A digital-capture effect — screenshotting to "save"
measurably impairs recall, so the photos parents already take are a write-only archive.
(b) *Counter:* the extractor is one LLM call and its failure mode is silent and confident; an
`ingest_artifact` that materializes the wrong date is worse than no capture. The blast-radius law
(`extract.py`: never auto-WATCHED, under-age → `pending_eligibility` + confirm to-do) is the right
mitigation and it adds a confirmation step to every capture.
(c) *Effort:* small. The pipeline is 739 LOC and deployed. This is placement plus a share-sheet
extension.
(d) **FALSIFIER:** if ingest-created objects are edited or deleted by the parent more often than they
are confirmed, extraction quality — not placement — is the binding constraint, and promoting it
amplifies a bad experience.

**D3 — Dictation extended from onboarding to every capture surface.**
(a) *Strongest evidence:* Ruan et al. (n=32, Tier A), 161.20 vs 53.46 WPM with 20.4% lower error for
transcription; and P5's offloading-tax experiment (n=52×2, within-subject, peer-reviewed, Tier A,
dz 0.71–1.29) where **five extra clicks significantly reduced whether people offloaded an intention at
all**, worst at high memory load.
(b) *Counter:* composition collapses to 7.8 WPM, and Kowalczuk & Musial (n=860, **German, intention
not behaviour**) find public-use shame suppresses continuance — a parent in a pickup line may not
speak. Mitigated by the fact that dictation is optional per field and the output is editable text.
(c) *Effort:* very small. `DictationController` is 140 LOC and already has a reusable
`HeismanMicAccessory`/`HeismanTextCard` wrapper (`OnboardingHeismanChrome.swift:280`). Extending it is
attaching an existing accessory to more fields.
(d) **FALSIFIER:** if mic-tap rate on the new surfaces stays under ~10% of field engagements after
four weeks, dictation is an onboarding-specific affordance, not a capture primitive, and the WPM
advantage does not survive contact with real usage contexts.

**D4 — The `extracurricular` and `school_event` verticals turned ON.**
(a) *Strongest evidence:* P4 verbatim — *"Camp is a 1–2 episode/year job. Extracurriculars are a
150–250-event/year job"* — plus AP-NORC/Ipsos KnowledgePanel July 2026 n=510 (Tier B): ~8 in 10 sports
parents name scheduling/logistics/time a challenge, **above** the ~7 in 10 naming cost. For
`school_event`: P5 #40, NHES:PFI 2023, n=19,562, Tier A — 6.0 parent-attended school activities per
child. And P7 puts the aggregate load's dead window at **August–September–October**, which is now:
camp has nothing to do and the treadmill has seven events this week.
(b) *Counter:* P9 rates "5 verticals, 3 defaulted off" **WITHIN NORM** and explicitly prescribes
keeping them off *"until camp and outing show sustained use."* That is a fair, literature-grounded
objection. My disagreement is narrow: P9 is scoring *count*, and the argument here is about *which
two*. Turning two on while cutting `trip` and demoting `outing` leaves the count unchanged at four.
(c) *Effort:* trivial for the flags (`FLAG_VERTICAL_V2_EXTRACURRICULARS`, `FLAG_VERTICAL_V4_SCHOOL` —
note nothing in-repo turns these on in prod; door state depends on Railway env or the PostHog console;
`docs/roadmap.md:44` records that `FLAG_VERTICAL_V4_SCHOOL` is *deliberately* unset). Medium for the
surfaces behind them to be worth opening. **P7 puts it best and it is the reason this is item four
rather than item ten:** *"**The Aug–Oct hole is covered almost perfectly by three task families that
are all currently behind feature flags that default off**… **The seasonal fix is a flag flip, not a
new build.**"* Its August ratings make the point numerically: summer camp **0**, school-break coverage
**0** — against school admin **3**, fall registration **3**, medical/dental **3**, birthday parties
**3**.
(d) **FALSIFIER:** if `door_opened` for the two new doors runs below camp's rate in the first four
weeks *of the August–October window when camp has nothing to offer*, the volume argument is wrong and
P9's keep-them-off prescription is right.

**D5 — Two-way calendar sync as the substrate, with Apple and Outlook added.**
(a) *Strongest evidence:* S0 — *"the one subsystem already built at the right altitude"* — and M5's
respondents' revealed preference (*"Good ol' Google Calendar"*). It is also the mechanism that makes
D-C2 (the second parent) work without an install.
(b) *Counter:* P9's void is decisive and I will not paper over it — **"share of US households
sustaining a shared digital family calendar: NO DATA FOUND AT ANY TIER… probably the single most
decision-relevant unknown."** Betting the substrate on shared-calendar behaviour is betting on an
unmeasured denominator. Also: M1's counted corpus puts sync complaints at 6.8% of 5,847 sub-4-star
reviews — sync is where organizer apps go to die.
(c) *Effort:* small to turn the scheduled sync on (`calendar_sync/router.py:19` defaults
`enabled: False`); medium-to-large for Apple/Outlook.
(d) **FALSIFIER:** if fewer than ~40% of activated families connect any calendar within two weeks, the
calendar is not the substrate and the product must own its own timeline instead.

### 3.2 SIMPLIFY (4)

**S1 — Invert the atom: the obligation becomes the base case, the workflow an optional attachment.**
S0's design, which I endorse on verified code. Three moves: make `todo_items.activity_id` a
self-referential `parent_id`; collapse six stored states to `open | done | dropped` and *derive* the
six stages as a rendering over deep objects; sort the primary surface by date, not stage. The
immediate, one-line prerequisite is fixing `build_board`'s `if aid:` so a parentless obligation is
visible at all (`lifecycle.py:302-315`). *Effort:* medium; a migration plus a board renderer.
**FALSIFIER:** see S0's own test, restated in §3.5.

**S2 — Re-cut the doors by trigger and depth, not subject matter.** A door is a canned chat opener
(`PlanView.openDoor`) — copy, not architecture. S0's cut: *"Something's coming up"* (N=1, ~100+/yr) ·
*"Here, deal with this"* (inbound, ~40/yr) · *"Find something"* (N=4–10, ~16/yr — the six-stage board)
· *"Cover these weeks"* (~12/yr, highest pain). The code's own comment already argues for it:
`PlanView.swift:23` says the vertical chip is *"attribute, never navigation"* — and then the doors,
which *are* navigation, are cut on that same attribute. *Effort:* small (registry + prompt section).

**S3 — One chat surface, one name.** Two surfaces both labelled "coach" (`AgentView` in a tab,
`CosChatView` inside the Planner), plus an orphaned third (`ChatView.swift`, 426 LOC). Route by
context. *Effort:* small-to-medium.

**S4 — Stop auto-presenting SetupTailView; make the 18-field profile a review surface.** P9 named the
auto-presented second setup sequence *"the highest-leverage single cut in the report,"* and the
Heisman sprint rewrote the view (±942 lines) without removing the trigger
(`HomeView.swift:174-183`). Keep the content; change the trigger to a tap. Put dictation on all 18
fields. *Effort:* trivial for the trigger.

### 3.3 CUT (5)

**C1 — The kid voice companion.** (a) P11: *"Not a win — a liability"*; FTC 6(b), amended COPPA,
$10M/$500K enforcement, 84%/82% parental concern, majority of 0–8 parents rejecting AI-as-friend;
**zero demand evidence at any tier in a corpus that searched for it.** (b) *Counter:* it is built,
carefully, with real moderation and crisis handling, and it is the most differentiated thing in the
app — a genuine product some beta families may love. Cutting it is a retention risk with those
families and a morale cost. (c) *Effort:* medium to remove ~4,000 LOC and the ElevenLabs/LiveKit kid
path; small to dark-flag it immediately. (d) **FALSIFIER:** if weekly-active kid-companion sessions
per consented family exceed weekly-active parent planning sessions, the feature is the product and
this call is wrong — in which case the correct response is not to keep it quietly but to fund COPPA
compliance properly.

**C2 — The `trip` vertical.** (a) V3's corrected within-battery figure: planning ranks **27%, 6th of
17**. (b) *Counter:* trips are the only vertical with a natural high-ticket attach. (c) *Effort:*
trivial — the flag is already off. (d) **FALSIFIER:** if organically-created `trip`-type activities
appear on boards at a rate comparable to `camp` despite the door being dark, latent demand exists that
the door was suppressing.

**C3 — In-app Circle group conversations.** (a) M4 (counted): the refusal is money, not installation,
and M4 explicitly endorses calendar-invite-plus-forwarding over an app install; `app/circle.py`
requires `current_user` to claim or accept. (b) *Counter:* M5's most-repeated phrase is about
one-sided adoption, and a shared thread is a plausible answer to it; there is no direct evidence that
*our* conversation surface fails. (c) *Effort:* medium — 792 LOC backend, ~2,500 LOC iOS across
CircleView/Thread/NewConversation/Contacts/MemberProfile. (d) **FALSIFIER:** if second adults who
claim an invite send messages at a sustained rate past week two, the thread is doing work no link
could do.

**C4 — Conversational parent voice as a roadmap item** (keep the code, stop investing). (a) M5: zero
conversational voice planning in ~2,300 comments; P8: no US precedent for voice at task depth; Alexa
>$25B. (b) *Counter:* P8 §6 flags Google's claim that 63% of Gemini users now use voice as evidence
the ceiling may be moving — and correctly labels it vendor-grade (company blog, no n, no window, no
definition). The countervailing figure in the same disclosure is more informative: ~1 in 5 Gemini Live
interactions already need a camera or screen share. (c) *Effort:* zero to stop. (d) **FALSIFIER:** if
parent voice sessions per weekly-active user exceed dictation invocations once dictation is deployed
app-wide, the conversational bet is the better one.

**C5 — `SavedView` (orphaned) and the third generic `ChatView`.** Dead read path with a live write
path, and 426 LOC of superseded chat. Housekeeping, not strategy.

### 3.4 BUILD-NEW (4)

**B1 — Manual add: one field, one gesture, on Home.**
(a) *Strongest evidence:* P5's Tier A offloading experiment — **five extra clicks significantly
reduced whether people offloaded an intention at all** (n=52×2, within-subject, dz 0.71–1.29) — plus
M1's counted verbatims (*"Ultimately these extra steps. Have been a barrier to wider use in our
family"*). Today **no form anywhere in the app creates a plain obligation**: the only client POST that
creates an activity is `PlanService.trackActivity`, called only from `PlanViewModel.saveCandidate:593`
(pin a discovery candidate), and `PlanService.todos()` is a GET.
(b) *Counter:* P9's calendar-adoption void means the capture habit itself is unmeasured, and P6 shows
the highest-frequency shallow job has near-zero WTP. It is entirely possible that parents will not
sustain manual capture in *any* app.
(c) *Effort:* small. The storage already permits it; the board renderer and one iOS field are the work.
(d) **FALSIFIER:** S0's test, below.

**B2 — The inbound forwarding address (Option B′).** S1 scores it 69.5/77.5 against Gmail OAuth's
35.0. It ships in ~2 weeks, needs no reviewer, violates no ToS in P12's matrix, costs ~$5/mo at 1M
inbound, and is **the only ingestion option with a mechanism for the second parent**. Two further
pieces of evidence I did not have when I wrote D2. **M2's competitive census:** of eleven live
products, **eight accept email forwarding as a primary intake** and *"in-app chat + forms is the ONLY
model in this table that appears in no successful competitor as a primary channel."* **P12 #42's own
review analysis (n=4,193, non-probability):** adoption is bimodal on *placement* — when the address is
the front door, **Jam gets 8 of 88 reviewers (9.1%) naming it unprompted as their favourite thing, all
5★**; when it is a settings-screen utility, **0 of 3,917** mainstream reviewers ever mention it
(Cozi 0/1,917, Todoist 0/1,000, Evernote 0/1,000). The lesson is not "build it" — it is "**make it the
front door or do not bother**." Non-optional
companion work per S1 §6.4: liveness ("last message N hours ago"), a quiet-stream nag, and a non-email
fallback — silent failure is the documented killer (the 18-month Skylight case). Carry V6's
correction: Gmail forwarding is **not** a collapsed step; the source user must return and click Save
Changes, and Google shows a week-long warning banner. **FALSIFIER:** S1's own cheapest test — give five
beta parents an address and watch; **the single number to get is what share complete a forwarding rule
on a phone.**

**B3 — A DOB-generated AAP well-visit + immunization schedule.** See §4. The AAP periodicity schedule
is a published deterministic table, not a search problem — a year of correctly-dated obligations from
one field onboarding already collects, at zero taps. **FALSIFIER:** if generated well-visit
obligations are dismissed or ignored at a higher rate than parent-created ones, the schedule is noise
rather than recall.

**B4 — The sports physical as a first-class gating obligation.** S0 calls it *"the cleanest unserved
job in the corpus"*: hard-deadlined, institution-set, gates participation outright, with P7 measuring
its timing precisely (*"school physical"* peaks Aug 100; *"sports physical"* Jul 95 → Aug 100) — and
**no citable US frequency data at any tier** (P5). Zero research step, no competitor concept, and it
peaks in the exact window (August) where camp has nothing to offer. *Effort:* small. **FALSIFIER:** if
fewer than ~15% of families with a 6–17-year-old engage the obligation when offered in August, the job
is real but already solved by the league's own reminders.

**B5 — A spoken daily briefing (voice as OUTPUT), as a cheap test, not a commitment.**
(a) *Strongest evidence:* the only enthusiastic voice signal in the entire corpus is outbound — Nori's
phone-call reminders (5★, verbatim in §2.8) and M5's Alexa "reads me my events… announces everything
1 hour ahead" cluster. M2: *"That inverts the usual assumption and is worth testing."*
(b) *Counter:* M4 finds missed-notification complaints in 14–15% of co-parenting-app reviews and calls
them the angriest in the corpus — an unreliable outbound channel is worse than none. And this is a
single vendor's review signal, not a measurement.
(c) *Effort:* small if it rides the existing push channel as a daily summary; medium if it is actually
spoken.
(d) **FALSIFIER:** if opt-in to a daily briefing runs below ~20% or opt-out exceeds ~40% within four
weeks, the ambient-output signal does not generalize beyond smart-speaker households.

### 3.5 The one test that adjudicates all of it

S0 supplies it and I adopt it unchanged, because it is cheap and genuinely decisive:

> Ship **one manual-add field and one to-do row** (both already representable in storage today) with
> no board, no discovery, no lifecycle, and instrument **creations per user per week against
> `activity_tracked`**. If shallow captures do not exceed tracked activities by an order of magnitude
> within four weeks, this analysis is wrong and the board is the right centre of the product.

Two things I would add to make it sharper. First, run it **in September or October** — P7's dead
window — so the comparison is not contaminated by camp season. Second, instrument *survival*, not just
creation: M5's abandonment language (*"dying in week two"*, *"another thing to maintain"*) predicts
that week-1 capture volume will look great and week-4 volume will not. **The number that matters is
week-4 captures per active user, not week-1.**

---

## 4. BY CHILD AGE, NOT BY PARENT GENERATION

The corrected cohort sizes (V1, authoritative): Gen Z parents **~3.6M households / ~10.9%** —
recomputed on this study's 2026 age bands from Census Table F1, nearly double the 2.0M/6.0%
householder-age snapshot the collectors used; Millennials **54.5%**; Gen X **35.1%**. The correction
makes Gen Z a bigger cohort than assumed and **does not change the child-age argument at all**, which
is the point of this section: the decisive variable is the child's age, not the parent's birth year.

Also carry V1's correction on the buyer: the household-management gap is **1.75x for employed
parents** (ATUS Table 8B, 8.4 vs 4.8 min/day), not the 2.0x/3.0x headline, which is levered by
non-employed mothers. Daminger exempts **decision-making only** as roughly equal — "identifying
options is also equal" is not established, so the Planner cannot be argued to sit in a gender-neutral
middle. And per the BRIEF, women lead **6 of 12** Gallup tasks in dual-full-time households, not 8 —
though **"family activity planning is one of the shared tasks" is confirmed and may stand** (Gallup,
n=3,062, dual-FT-with-kids subgroup n=566, MoE ±5, fielded 2019, dated). Note the discomfort that
creates: the one job Gallup says couples share is the one the Planner is built around, while the jobs
Daminger says are hers alone — anticipation and monitoring — are the watchlist and the recall.

One more shape worth stating because it cuts against the intuitive read. **Pew's "difficulty" curve
runs opposite to the planning-load curve**: parents call balancing work and family difficult at 56%
(youngest 0–5) → 54% → **47% (13–17)**, while household management rises the other way. P2's
explanation is the useful one: *"Under-6 parenting is physical and shared; school-age parenting is
administrative and mother-owned."* The product sells into the administrative half.

### 4.1 Ages 0–5 — Q3 only. Turn most of the product off.

84.1% of 25–29-headed parent households contain a child under 6; 56.4% a child under 3; only 7.5% a
teenager (P1 #10–13, Census Table F1 2023). P4: children **0–5 have effectively zero organized-
activity load — the federal instrument does not even ask below age 6.** P3: day care is 6% of K-12
summer arrangements. There is no Q1 quadrant and **no Q1 load at all in January**, the month the camp
funnel is built around.

But Q3 is at its lifetime maximum: infants under 1 make **5.96 office visits/year vs 1.53 for ages
1–17** (P5 #2, NCHS NAMCS 2018, Tier A), and AAP Bright Futures prescribes **7 well visits in year one
and 31 birth-to-21** (Tier A).

**Concretely, at 0–5:**
- **Off:** discovery, the six-stage board, coverage-gap detection (there is no school calendar to have
  gaps against), the registration watchlist, `camp`, `extracurricular`, `school_event`, `trip`.
- **On:** the DOB-generated AAP well-visit and immunization schedule (**B3**); capture; the calendar;
  the Coach (this is the cohort with the most genuine parenting-advice demand).
- **The one thing to ship:** B3. A year of correctly-dated obligations generated from one field
  onboarding already collects, at zero taps. It is pure Q3 recall with no workflow.
- **Strategic framing:** P1 shows fertility migrating up the age curve (the 30–34 rate of 93.7 has
  exceeded 25–29's 89.5 every year since 2016; mean age at first birth a record 27.6). Build for 0–5 as
  **retention through aging-in**, not as an acquisition segment.

### 4.2 Ages 6–12 — the only band where the whole engine earns its place.

Millennials, 54.5% of parent households, mean youth-sports parent age 40.84 (Aspen 2024). Q1: peak
camp spend ($954/child vs $893 all-parent average, LendingTree 2025, Tier C), day camp modal at 29%
elementary (Gallup/NSLA/ACA — fielded May 2024 but **asking about summer 2023**, per V5; label the
reference year). Q2: peak afterschool dosage at **5.9 hrs/wk elementary** vs 4.8 middle and 4.5 high
(AA3PM 2025), ~200 logistics events/yr. Q3: 6.0 parent-attended school activities per child
(NHES:PFI 2023, n=19,562, Tier A). Structural intensity: both parents employed **69.4%** when kids are
6–17 vs 65.3% under 6; maternal LFPR 78.2% vs 68.0% (BLS 2025).

**Concretely, at 6–12:**
- **Everything on — but with the treadmill layer *underneath* the campaign layer, not beside it.**
  Home shows the week; the board is a drill-down for the ~16 deep objects a year.
- Camp and break-coverage keep the six-stage board. Everything else enters as a dated obligation.
- The risk P8/P11 jointly flag: this cohort uses AI most (daily chatbot use peaks at 30–49, 34%, Pew
  2026 n=5,119) while being **least self-confident with it** (23% extremely/very confident vs 31% of
  18–29s). They will adopt an agent and will not trust it unsupervised. **Design implication: the
  agent drafts obligations the parent confirms in one tap; it does not silently run an eight-step
  workflow.**

### 4.3 Ages 13–17 — Q2 + Q3, almost no Q1. Discovery has nothing to sell them.

73.5% of 45–49-headed parent households contain a 12–17-year-old; only 12.8% a preschooler (P1 #11,
#10). Gen X is 35.1% of parent households — **11.7M households for whom the discovery engine (38% of
the agent's tool surface) is close to useless.** P3: the modal summer activity flips to a
**job/internship (32%)**; overnight camp usage falls. P4: 13–17 regular sports participation fell 3%
in 2024, but the survivors are the most intense — a primary sport alone spans **1.86 organizational
settings**, each a separate registration, roster, comms channel and calendar. P5: urgent-care use is
**highest at 12–17 (30.3%)**. P1 #18: single-parent share rises with child age — 22.2% of children
15–17 live with mother only vs 18.2% of under-6s, which raises the weight of the second-parent
mechanism precisely where discovery matters least.

**Concretely, at 13–17:**
- Discovery drops to a **background utility** — reachable, never the front door.
- Lead with capture, deadline recall, and the logistics-assignment model. `AddCaregiver` and
  `AssignLogistics` already exist and are depth-agnostic (`cos/tools.py:327,357`) — they are among the
  13 tools S0 classifies as depth-agnostic and they have no UI.
- Ship the **sports physical as a first-class gating obligation** (B4).
- Multi-org coordination is the differentiated job: TeamSnap bills **per team, not per account**, and
  SportsEngine states in its own help docs that *"there is no way for divorced parents to have
  separate accounts… we suggest the parents get a shared free email account"* (P4 #34, primary vendor
  doc). That is the gap.
- **The teen may receive logistics; the teen must never be handled by the product.** 88% of US teens
  own an iPhone (Piper Sandler 2025, Tier C — P10 flags this as its own weakest inference) and 64% of
  teens use AI chatbots (Pew), but P11 is emphatic that parents *"trust AI companies far less than they
  trust the output,"* with 84% concerned about AI misusing young people's data. A read-only schedule
  push to a teen's calendar is fine. A conversational agent for the teen is C1 again.

### 4.4 One line per band

| Child age | Live quadrants | Discovery | 6-stage board | Coverage gaps | Watchlist | Ship this |
|---|---|---|---|---|---|---|
| **0–5** | Q3 only | **Off** | **Off** | **Off** | **Off** | DOB-generated AAP well-visit + immunization schedule (B3) |
| **6–12** | Q1+Q2+Q3 | **On** | **On, for Q1 only** | **On** — highest-pain job | **On** | One-gesture capture underneath the campaign layer |
| **13–17** | Q2+Q3 | Background utility | Rarely populated | Partial | **On** (club/travel) | Sports physical (B4) + transport assignment + multi-org recall |

---

## 5. WHAT THE FOUNDER GOT RIGHT

Three calls anticipated findings that did not exist yet. Each is genuinely vindicated and each needs a
specific modification.

**5.1 The generalized-workflow instinct — right, for a reason he did not name.**

The framing under test was *"the camp tool is the same tool that plans a weekend and a vacation…
anything that has a start, multiple steps in between, and a finish."*

*Vindicated by:* P7's seasonality data, which is the strongest argument for generalization and is not
the argument the framing makes. Each job is violently seasonal — spring-break camp CV 1.577, flu shot
1.076, back-to-school 0.974, summer camp 0.633 — and the peaks **rotate**: Nov (winter sports, camp
opens) → Jan–Feb (spring sports, the camp mass wave) → Mar (spring-break camp) → Jun–Aug (fall sports)
→ Oct–Nov (winter sports). Every registration curve leads its season by 2–6 months. A camp-only
product is dead in **August, September and October** — which is today. **A multi-job product has no
off-season, and that is a real and load-bearing reason to build one engine rather than five apps.**

*Modification required, and V3 forces it:* do **not** publish P7's "aggregate load varies only 1.47x
across the year" figure — it is an artifact of row normalization plus ordinal truncation, and any
chart must carry a volume axis (on a shared scale, summer camp reads 36.6, kids-activities 3.5,
dentist 1.5 — summer camp's *worst* month exceeds dentist's *best* by ~4.5x). Only the flat-vs-spiky
separation is robust; the fine CV ranking is not. Google Trends here is **Tier C/D** (raw feed, no
disclosed n) and is not parent-scoped.

*The substantive modification:* the generalization is right across **subject matter** and wrong across
**depth**. `VerticalProfile` (`app/cos/verticals.py`) parameterizes copy, three capability booleans,
one coverage boolean and a five-valued `date_model` — **there is no step-count knob**, so every
vertical inherits the same six stages. And the three task families that actually flatten the annual
curve (medical/dental CV 0.099–0.124, birthday parties 0.124, outings 0.142) are all Q2/Q3, and the
product has no concept for two of the three. The flat curve is bought only if the new subjects can be
*stored*, and today they cannot.

**5.2 The aggregation instinct — right, and the corpus keeps confirming it from unrelated directions.**

*Vindicated by:* P4 #31, the only parent-level app-sprawl count that exists — **44% of parents use 7–9
apps per child, 68% must launch each individually, only 21% have any unified platform**, and *no
parent gave a top satisfaction rating; 85% rated 5/10 or below*. Also P4 #32: parents field **17.5
communications per week** about kids' activities and track 11.5 activities per week. Also P4 #34, in
the vendors' own words: TeamSnap bills per team, not per account; SportsEngine has no mechanism for
two parents on one child. Also M3: there is no national database and nobody is close, so aggregation
of *supply* is only reachable by an agent — and P12: aggregation of *inbound comms* is reachable by
email, which is the one channel every school and provider already uses.

*Modification required — and it is sharper than "weak sourcing."* P4 #31 is **n=125,
vendor-sponsored (Edsby/Cornerstone), non-probability, no MoE, five-week field, and per V6 it is
North American, not US** (Edsby is a Canadian vendor; 49 of its 58 curriculum leaders were US) — so
"a study of US parents" is itself the global-relabelled-as-US move. P4 itself says "directional only,
always cite with n and sponsor," and notes that **no probability-sampled study of parent app sprawl
exists anywhere**, calling it *"a genuine, fundable gap."* P4 #32 is Harris for Skylight,
vendor-interested. P12 #11 adds a **hard federal negative**: NHES:PFI 2023 asks only whether the
school sent notes/emails/newsletters/calls (yes/no) — *"there is NO item counting apps, portals or
logins, and no item on missed information."*

And P12 names the trap directly: districts touch ~3,000 tools while individuals touch ~4. *"Both are
true — the district number is an inventory, the individual number is usage — and the honest reading is
that **institutional sprawl does not automatically become parent-experienced sprawl.** Anyone building
a pitch deck off 'parents juggle 3,000 apps' will be caught."* **The defensible version of the founder's
instinct, in P12's words:** *"a US family's kid-related information arrives through school, district,
multiple activity providers, and other parents, and **no single platform — including the consolidators —
has jurisdiction over more than one of those.**"* Note where that puts the centre of gravity: the
sports and activity layer (TeamSnap 30M, SportsEngine 16M athletes) is **outside any district's
jurisdiction** — P12: *"The wedge survives, but its centre of gravity is OUTSIDE the school, not
inside it."*

*The substantive modification:* aggregate at the **inbound** seam, not the **directory** seam. S1's
scoring is unambiguous — the forwarding address (69.5/77.5) dominates Gmail OAuth (35.0) and
registering our address with schools (25.5), and the memo's own sentence is the argument: *"Building
the flagship feature on a permission an external body can withhold, when an un-gated mechanism with
better trust characteristics ships in two weeks, is not a defensible allocation of a solo developer's
runway."*

**5.3 The dictation build — right, built before the evidence landed, and currently under-deployed.**

*Vindicated by:* P8's Tier A modality evidence (Ruan et al., n=32: 161.20 vs 53.46 WPM, 20.4% lower
error for transcription) combined with M5's independent finding of **zero conversational voice planning
in ~2,300 comments** and the only voice grammar being *"Hey Siri, remind me to…"*. The architecture
chosen is precisely the one the literature prescribes: on-device `SFSpeechRecognizer`, partial
transcripts, **editable text output** — which matches Ruan's finding that users prefer the keyboard for
error correction, a preference that measurably improves performance. Building 140 LOC of the right
thing rather than extending 900+ LOC of the wrong thing (ElevenLabs/LiveKit conversational calls) was
the correct call, and it was made before P8 existed.

*Modification required, and it is the cheapest recommendation in this report:* it is wired into
**three onboarding files** (`OnboardingHeismanChrome.swift:280`,
`OnboardingHeismanScreens.swift:168`, `OnboardingHeismanTail.swift:15`) and **zero** of the app's ~58
other text-entry fields, the 18 profile fields, or either chat composer. Onboarding is the one place a
parent is *already* committed and least needs the speed. Move it to where the offloading tax is paid —
capture.

**5.4 Two more, briefly.**

*The unauth-first funnel* (`b850a3e`, account wall at step 10 of 13, with a real server-side
extraction at step 4 via `AnonOnboardingService`) directly answers P9's harshest finding about the old
funnel — *"there is no product value anywhere inside those 10 screens"* — against RevenueCat's Tier B
day-zero data (82% of trial starts on install day; 55.4% of 3-day-trial cancellations on Day 0). It
was built before the research landed and it anticipated the finding. *Modification:* it is still 13
fixed steps with no branching, and it did not remove the auto-presenting `SetupTailView` that P9 called
the single highest-leverage cut. Against M2's measured competitive benchmark — **Sense and Schoolcase
onboard in 1 step; Nori ~3–4; Ohai ~6+ gates, and Ohai's onboarding already generates one-star reviews
and documented total abandonment** — 13 steps is still the heaviest funnel in the set. The right frame
is that the sprint fixed *what is inside* the funnel and has not yet fixed *how long it is*. Carry
V4's discipline on this whole line of argument: **nothing in the onboarding-length case is a
measurement** — *"the cut is probably right; the claim that data proves it is wrong."*

*The `outings.py` bypass* (327 LOC, docstring: *"deliberately its OWN self-contained flow, NOT a branch
of the camp machinery… Nothing is persisted"*) and the **nullable `todo_items.activity_id`**
(`duckdb_storage.py:929`) are the team discovering S0's central finding empirically, under duress, and
writing it down. The recommendation in §3.2/S1 is not a new architecture — it is ratifying two
decisions the codebase already made.

---

## 6. WHERE THE EVIDENCE IS THIN — STATED, NOT SMOOTHED

- **Whether families sustain any capture habit.** P9: *"share of US households sustaining a shared
  digital family calendar: NO DATA FOUND AT ANY TIER."* The entire shallow-capture thesis rests on an
  unmeasured denominator. This is why §3.5 exists.
- **Permission-slip and birthday-party-attended frequency.** No citable source at any tier; P5 searched
  specifically. S0's ~12/yr is an estimate. Removing both drops the shallow object count from ~280 to
  ~250.
- **Sports-physical frequency.** No citable US data at any tier — yet it is the cleanest unserved job
  in the corpus. B4 is a strong-logic, weak-data recommendation and should be labelled as such.
- **Orthodontia cadence.** Unsourced; P5 calls it *"the highest-value unmeasured category"* and *"one of
  the largest single hidden recurring appointment blocks in a family's calendar."*
- **The 24% waitlist figure** is an afterschool measure borrowed as a camp proxy (P3 says so).
- **M5** is qualitative, non-representative, browser-driven (Reddit blocked all API and mirror paths),
  individual comments rather than threads, **skewing heavily to r/adhdwomen and r/ADHD**, with no
  BabyCenter/What-to-Expect sources and only 4 usable quotes on "what they wish existed."
- **M1's complaint-theme ranking** is analyst judgement, not measurement — no regex, no numerator, no
  denominator, and its two rankings contradict each other. The counted numbers over 5,847 sub-4-star
  reviews are price 14.2% and sync 6.8%. (M4's rankings *do* publish regexes and denominators and all
  replicated — M4 may be cited as counted.)
- **P4 #31's app-sprawl numbers** are n=125, vendor-sponsored, non-probability, no MoE.
- **The Kowalczuk & Musial voice-shame study** is German, measures intention rather than behaviour, and
  has no US equivalent.
- **Camperoni's live-index figure of 4,324** is one measurement V5 could not independently re-run (the
  endpoint 401s without their key). What is settled is that the Feb-2025 "~500" is 18 months stale and
  cannot carry a present-tense conclusion.
- **ParentSquare's BLOCKED verdict is unsourceable** (login-gated help centre) and needs a first-party
  test before any recommendation leans on it. S1 §11.5 already specifies that test at ~$0 and one day.
- **P11 #41 — the evidence under the watchlist's competitive win — is killed.** Its sole source,
  usecarly.com, is the SEO site of a competing AI assistant with no method page anywhere; V6 rules it
  Tier D program-wide. The *whitespace* finding (M3, primary) does not depend on it; the specific
  "ChatGPT cannot watch a page and push you" claim does, and needs a 20-minute in-product check.
- **P9's ATUS 2024 time-budget figures are unverifiable in this environment** — bls.gov 403s every
  method — so I have not used them. (V1 notes Wayback `id_` snapshots are the working route.)
- **Two headline numbers were mis-scoped by their own collectors and are used here in corrected form:**
  the trial-cancellation figure is **55.4% of 3-day-trial cancellations**, not of all trials; and the
  RevenueCat AI-retention haircut is **monthly-plan-scoped**, so an annual product must be modelled from
  the 44.1% yearly baseline with an explicit, sensitivity-tested haircut.
- **Complexity judgements throughout** are analyst calls. No screens-to-completion distribution exists
  for consumer apps at any tier, so surface counts, tap counts and field counts are published here as
  *comparisons against adjacent benchmarks*, never as scores.

---

## 7. THE VERDICT IN ONE PARAGRAPH

The engine is well built, correctly generalized across subject matter, and pointed at the cheap half of
the problem for one of three child-age bands. The three highest-value things in the product are the
registration watchlist (verified whitespace, sold by a competitor at $295/yr performed by humans, and —
uniquely — *worth more where discovery is worth less*), the ingest pipeline (the only surface with
direct, counted customer language praising it), and the 140-line dictation controller built yesterday
into the only screens that did not need it. The three most expensive mistakes are a kid-facing AI
companion with zero demand evidence and maximal regulatory exposure, a second-parent strategy that
requires the second parent to do the one thing the counted evidence says they refuse, and a product
whose only object constructor can represent about 5% of what a family actually plans. None of the fixes
is a rewrite: turning two flags on, deleting one flag, fixing one `if aid:` in `lifecycle.py`, moving
an existing mic accessory onto existing text fields, and shipping one input field on Home.
