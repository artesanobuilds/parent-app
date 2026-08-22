# S0 — THE WORKFLOW MODEL

Analyst S0. Compiled 2026-08-21. Reads: BRIEF.md + P1, P3, P4, P5, P6, P7, P8, P9, P10, P11, M1, M2.
Code audit: `mvp-backend/app/cos/*`, `app/watchlist/*`, `app/ingest/*`, `app/calendar_sync/*`,
`app/duckdb_storage.py`, `mvp/MVP/PlanView.swift`, `mvp/MVP/PlanViewModel.swift`,
`mvp-backend/parent-dashboard/src/components/Card.tsx`. Every claim about the engine cites a file.

**The founder's framing under test:** *"the camp tool is the same tool that plans a weekend and a
vacation. Generalize it: anything that has a start, multiple steps in between, and a finish.
Research, then registration, then payment. Almost like a workflow."*

**Verdict in one line:** the generalization is right for the reason the founder did not name, and
wrong on the axis he did. Generalizing across *subject matter* is genuinely load-bearing — P7 shows
each individual job is violently seasonal (camp CV 0.633) while the aggregate is nearly flat (a 1.47×
spread across twelve months), so only a multi-job product has no off-season. But the engine
generalizes across subject matter while staying rigid about **depth**: every vertical inherits the
same six stages. Depth is the axis that actually varies, and ~95% of a family's planning objects have
a step count of one or two, which the six-stage lifecycle cannot represent without manufacturing
ceremony. One primitive *can* serve both ends, but only if the atom is inverted: the obligation must
be the base case and the workflow an optional attachment, not the reverse. The codebase has already
proven this twice, in `app/cos/outings.py` and in a nullable foreign key.

---

## STEP 1 — WHAT THE ENGINE ACTUALLY IS TODAY

### 1.1 The registry is data-only, and that is exactly its limit

`app/cos/verticals.py` defines `VerticalProfile` (frozen dataclass) with these fields, and this is
the complete set of things a vertical can vary:

| Field | Type | What it controls |
|---|---|---|
| `key`, `label`, `chip_label` | str | Display strings |
| `date_model` | str, 1 of 5 | `week_block \| recurring_weekly \| single_date \| date_range \| none` |
| `provides_coverage` | bool | Whether this vertical's weeks count as childcare in `uncovered_weeks` |
| `todo_wording` | dataclass | Payment/confirm/extras to-do **copy only** |
| `research_focus` | str | Query suffix appended in `LookupAndSaveActivity` |
| `door` | dataclass | Title, subtitle, starter prompt |
| `email_sync`, `registration_watch`, `ingest_taxonomy` | bool ×3 | Capability switches |
| `flag` | str? | PostHog flag gating **door visibility only** |
| `harness_spec` | str | Path to a test spec |

The module docstring states the binding rule explicitly: *"The registry is DATA-ONLY by design (a
binding rule from the plan's critic review): labels, wording templates, capability booleans, door
copy. Behavioral conditionals ... stay in code"* (`app/cos/verticals.py:9-14`).

**The consequence, stated plainly: there is no knob for step count.** Every registered vertical
inherits the same six stages, the same status enum, the same `next_step` CTA vocabulary, and the
same board sections. `date_model` is the only structural knob, it has five hardcoded values, and it
is consumed by an if-chain in `lifecycle.format_when` (`app/cos/lifecycle.py`) — so a sixth date
shape is a code change, not config.

### 1.2 What a vertical actually costs to add (measured, not guessed)

Not config-only. Eight touchpoints across three surfaces plus two locking tests:

1. `app/cos/verticals.py` — add to `ACTIVITY_TYPES`, `KIND_FOR_TYPE`, `_CATEGORY_TO_TYPE`, and a
   `REGISTRY` entry. **(genuine config)**
2. `app/cos/prompt.py:83-145` — a hand-written playbook section per vertical (camps, classes,
   school life, trips, outings each have one). The module docstring says the prompt is *"ONE static
   prompt in sections — no dynamic per-vertical assembly (a binding rule ...)"* (`prompt.py:9-13`).
   So prose is deliberately NOT registry-driven. **(code/prose, plus a golden-set rerun)**
3. `app/cos/lifecycle.py` `format_when()` — only if the vertical needs a date shape outside the
   five. **(code)**
4. `app/ingest/taxonomy.py` — a per-kind task-chain builder if the vertical ingests documents. Its
   docstring records this as *"the plan's FIRST config→strategy promotion: V4 task chains are
   structurally different per kind, so each kind gets a builder function"* (`ingest/taxonomy.py:1-6`).
   **(code)**
5. `mvp/MVP/BoardCardView.swift:32-36` — chip label dictionary, **hardcoded despite `chip_label`
   existing in the registry.** **(iOS code)**
6. `mvp-backend/parent-dashboard/src/components/Card.tsx:15-19` — the same dictionary again.
   **(web code)**
7. `tests/nl-harness/specs/...` — a spec file whose existence is asserted by
   `tests/test_verticals_registry.py:135`.
8. `parent-dashboard/docs/{key}.md` — a public doc page whose existence is asserted by
   `tests/test_public_docs.py:62`.

Plus a PostHog flag if gated. Realistically a day of work, and — the important part — **none of
those eight touchpoints let you change how many steps the thing has.**

### 1.3 What the six stages assume

`app/cos/lifecycle.py` defines the status groups and the stage map:

```
CONSIDERING = {exploring, interested, reference}   → CTA "We'll do it"
PLANNED     = {planned}                            → CTA "Register"
WATCHED     = {signed_up, confirmed}               → CTA = top open to-do
DONE        = {done}                               → collapsed under "All set"
BLOCKED     = {pending_eligibility, waitlisted}    → CTA resolve reason
DECLINED    = {declined}                           → hidden
```

Six embedded assumptions, each of which is a camp fact, not a planning fact:

- **A) There is a decision to make.** `stage_for` defaults every unknown status to `considering`
  (`lifecycle.py`), and the board's first section reads *"Saved ideas — decide yes or no when you're
  ready."* A dental recall notice has no considering phase; the decision was made by the last
  cleaning.
- **B) There is a registration event.** Both middle stages exist to service it: `to_register` ("You
  said yes — next step is signing up") and `registered · needs action`. A permission slip is signed,
  not registered.
- **C) The provider is discovered, not known.** `SearchActivities` reads *discovered candidates*;
  `StartDiscovery` (`cos/tools.py:1048`) is ZIP-anchored and refuses to run without a postal code;
  `CompareActivities` (`tools.py:626`) tabulates a *shortlist* and returns *"The shortlist is empty
  — pin some candidates first"* when there is nothing to compare; `CheckEligibility` tests a
  provider-published age window. All four presume a searchable market of substitutable options. Your
  pediatrician is not a search result.
- **D) The unit of time is a week.** `planning.uncovered_weeks` (`cos/planning.py:303`) keys coverage
  on `(kid_name, week_start)`; `coverage_gaps` (`planning.py:261`) reads `week_start` rows;
  `tracked_activities.week_start` is a first-class column (`duckdb_storage.py:813`). A Thursday 3pm
  dentist has no week semantics.
- **E) Being finished is a terminal, collapsible state.** `all_set` renders collapsed with the blurb
  *"Registered and nothing left to do."* For a camp in July that is right. For an appointment on
  Thursday it is catastrophically wrong — the most urgent object in the family's life gets filed
  under "nothing left to do" because nothing is left to do *before* it.
- **F) Recording something implies future paperwork.** `on_enter_watched` seeds a payment to-do when
  price is known and, when Gmail is not connected, a *"Forward or paste {name}'s confirmation
  email"* to-do (`lifecycle.py`). **The engine manufactures a second step at the moment a one-step
  obligation is recorded.** That is workflow ceremony, generated in code, on every object.

### 1.4 The 22 tools, split by what they presume

`build_cos_tools` (`cos/tools.py:1258-1283`) returns 21 tools (the "22" in the brief counts the
merged agent's separate `Help`/coach entry). Split:

**Depth-agnostic — work for any planning object (13):** `TrackActivity`, `AddToCalendar`,
`AddRecurringAppointment`, `AddCaregiver`, `AssignLogistics`, `AddTodo`, `CompleteTodo`,
`UpdateTodo`, `GetPlanSnapshot`, `UpdateActivity`, `UntrackActivity`, `GetKidsInfo`, `Help`.

**Market-shaped — presume research + choice + a provider-set registration (8):**
`SearchActivities`, `StartDiscovery`, `LookupAndSaveActivity`, `CompareActivities`,
`CheckEligibility`, `WatchRegistration`, `DraftEmail`, `SuggestOutings`.

So **38% of the agent's tool surface exists to service steps 1–2 of the camp workflow (research and
compare)** — the two steps that do not exist at all in a dental recall, a permission slip, a picture
day, a well-child visit, or a Thursday soccer run.

### 1.5 The supporting subsystems are all camp-shaped

- `app/watchlist/` — `windows.py` implements one law: *"notify BEFORE the window opens, never
  after"* with `T_MINUS_7`, `DAY_OF`, and an 18:00-local evening-before rule. This is a **registration
  race** primitive. It is superb for camp — P3 documents a YMCA selling ten weeks in ~90 seconds with
  the last accepted application timestamped 7:01:30 — and irrelevant to any obligation whose deadline
  is the event itself. Only `camp` and `extracurricular` carry `registration_watch=True`
  (`verticals.py`).
- `app/ingest/` — `extract.py` runs one structured-output LLM call over pasted text or a flyer photo,
  then `materialize()` writes a **`pending` tracked_activity** plus calendar entries plus to-dos.
  Every ingested artifact is forced through the activity object even when it is one dated fact.
- `app/calendar_sync/` — genuinely vertical-agnostic. Pushes owned `calendar_entries`, pulls external
  events back as `kind='external'` so conflict/coverage see real commitments (`sync.py:1-11`). This
  is the one subsystem already built at the right altitude.

### 1.6 The engine already forked — twice, in code

**Fork one, explicit.** The lowest-step-count vertical could not ride the lifecycle. `app/cos/outings.py`
is 327 lines whose docstring says so directly:

> *"This is deliberately its OWN self-contained flow, NOT a branch of the camp machinery ... A 'quick
> outing' ask needs none of the lifecycle: no `tracked_activities`, no board card, no watchlist, no
> to-dos. It's a one-shot ... Nothing is persisted."* (`app/cos/outings.py:1-8`)

Its registry entry reflects the surrender: `date_model="none"`, `provides_coverage=False`,
`email_sync=False`, `registration_watch=False`, and a door subtitle reading *"nothing saved unless
you say so."* The team discovered empirically that N≈1 does not fit, and built a bypass.

**Fork two, latent.** `todo_items.activity_id` is **nullable** — *"nullable link to
tracked_activities.id"* (`duckdb_storage.py:929`), as is `calendar_entries.activity_id`
(`duckdb_storage.py:844`). The storage layer already permits a free-standing dated obligation with a
title, a kid, a kind, a due date and a status. **The lightweight primitive exists in the schema and
is unreachable from the UI.**

### 1.7 Where the UI forces ceremony onto low-N jobs

- **There is no manual add.** The only iOS path that creates a tracked activity is
  `PlanViewModel.saveCandidate` — *"Pin a discovery candidate to the 'exploring' shortlist"*
  (`mvp/MVP/PlanViewModel.swift:583-600`). To get "dentist Thursday 3pm" onto the board a parent must
  either run a web-discovery job for a provider they already use, snap a flyer that does not exist,
  or hold a conversation with an agent.
- **There is no to-do creation UI at all.** `AddTodo` exists as an agent tool (`tools.py:399`); no
  SwiftUI view calls a create-todo endpoint. To-dos are visible only as children of an activity card
  (`BoardCardView.swift:126-129, 277-304`). The brief's audit already flagged the absence of any
  general capture surface; the code confirms the cause — **to-dos are not first-class objects in the
  product, only in the database.**
- **Everything enters at "Considering."** Default status is `exploring` both in the tool signature
  (`tools.py:132`) and the column default (`duckdb_storage.py:819`). A thing you already committed to
  starts life in a section called "Saved ideas."
- **The default date rendering is a week.** `format_when` falls through to `"Week of {date}"` for
  anything that is not an rrule, a same-day pair, or a `date_range` vertical (`lifecycle.py`). A
  one-off dated obligation renders as a week block — and that is the *default* branch.
- **Twelve knobs and 16–20 taps** on the path to a saved plan (BRIEF, code-audited). Against P9's
  benchmark — Baymard's tested optimum of ~8 form fields, 11.3 the e-commerce average, 17% of cart
  abandoners citing "too long/complicated" (P9 #12–13, Tier C) — the discovery panel is a checkout
  flow, and it sits in front of *every* object because it is the only door.

---

## STEP 2 — THE WORKFLOW TAXONOMY

**Definition.** A planning object = TRIGGER → OWNER/KID → DEADLINE (hard-external / soft-self /
recurring) → N STEPS → TERMINAL STATE. **N counts distinct actions the parent must take between the
trigger and the terminal state.** Attending is a step. Deciding is a step. Remembering is not (that
is the product's job).

### 2.1 The jobs, with step lists

| Job | Trigger | Deadline type | Steps (the actual list) | **N** |
|---|---|---|---|---|
| **Summer camp** | Self-initiated, seasonal (Jan–Apr per P7) | Hard, provider-set, **race-shaped** | 1 map which weeks need coverage · 2 research options · 3 compare/decide per kid×week · 4 catch the registration window · 5 register (timed form) · 6 pay deposit · 7 pay balance · 8 health forms + immunization record · 9 assign drop-off/pickup · 10 attend | **8–10** |
| **School-break coverage** (non-summer) | School calendar pushes it | Hard, school-set date | 1 notice the closure · 2 choose mechanism (camp / PTO / grandparent) · 3 arrange it · 4 confirm logistics | **2–4** |
| **Fall/spring activity registration** | Season + peer signal | Hard, provider-set, fills fast | 1 decide the activity · 2 find the window · 3 register · 4 pay fee · 5 buy gear/uniform | **4–5** |
| **Family trip** | Self-initiated | Soft self-set, hardens on booking | 1 pick dates · 2 clear school/work · 3 book travel · 4 book lodging · 5 arrange pets/house · 6 pack · 7 consent letter + docs · 8 go | **6–8** |
| **Birthday party hosted** | Calendar (the child's DOB) | Soft self-set, socially hard | 1 date · 2 venue · 3 invites · 4 RSVP chase · 5 cake/food · 6 favors · 7 host | **6–7** |
| **Weekly sports logistics** | Recurring schedule | Hard, recurring, provider-set | 1 be at the right place at the right time with the right kit | **1** (per event) |
| **School event** (concert, picture day, conference) | Inbound school comms | Hard, school-set | 1 note the date · 2 show up (sometimes: sign up for a slot) | **1–2** |
| **Permission slip / school form** | Inbound (backpack or email) | Hard, school-set | 1 sign and return (sometimes + pay) | **1–2** |
| **Well-child visit** | Provider recall / AAP periodicity | Recurring, soft-hard | 1 book · 2 attend (+ forms) | **2** |
| **Dental recall** | Provider recall notice | Recurring 6-month, soft | 1 book · 2 attend | **2** |
| **Sports physical** | League requirement | **Hard, blocks participation** | 1 book · 2 attend · 3 submit form to league | **3** |
| **Therapy / orthodontia series** | Provider-set cadence | Recurring, hard per session | 1 attend (per session; the series is booked once) | **1** per session |
| **Immunization deadline** | School/state mandate | **Hard, statutory; exclusion from school** | 1 locate record · 2 get the shot · 3 submit to school | **2–3** |
| **Birthday party attended** | Inbound invite | Hard, host-set | 1 RSVP · 2 gift · 3 drive there | **2–3** |
| **Weekend outing** | Self-initiated, discretionary | **None** | 1 pick something · 2 go | **1–2** |

### 2.2 Frequency, hardness, consequence — sourced

Per family per year. Where the research gives per-child numbers I use **1.94 own children per
family** (P1 #7, Census FM-3 2023) and, for activity-specific rows, the report's own participating-kid
multiplier.

| Job | Freq/family/yr | Source | Provider-set deadline? | Consequence of failure |
|---|---|---|---|---|
| Summer camp | **1 annual cycle → 5–10 week-level booking decisions per child** | P3 (CAP/AA3PM; Care.com 2026 n=3,000) | **Yes, to the second** | No childcare; PTO burn; 62% of paying parents took on debt (P3, LendingTree 2025 n=638) |
| School-break coverage | **8–15 closure episodes** | P3 (60% of working parents burn ≤2 wks PTO on closures/PD/snow days) | Yes (school calendar) | Missed work; 60% of caregivers report someone missed work/cut hours (P3, BPC 2026 n=1,039) |
| Fall/spring registration | **4–6** | P4 (derived: NSCH 2022 1.92 activity types × 1.58 participating kids; Aspen 2024 2.01 sports). Multiplied by **1.86 organizational settings for the primary sport alone** — *"Each setting is a separate registration, roster, comms channel and calendar"* | Yes, but **sell-out is unproven for rec sports** — Minneapolis Park & Rec guarantees placement to all registrants (P4) | Missed season; late fees |
| Weekly sports logistics | **150–250 events** | P4 (Aspen 2024 n=1,848: 2.66 practice + 1.80 game days/wk × 1.58 kids ≈ 7/wk in-season) | Yes, recurring | Kid misses/late; 7.1 hrs/wk/child of logistics, 4.8 of it pure coordination |
| Family trip | **2–4** | P6 (~2.4 trip *types* per respondent, FTA/NYU 2025 n=1,596, Tier C — **sample screened out non-travelers**; trips-per-household is unpublished) | No | Money; disappointment. **Zero-urgency** |
| Weekend outing | **26–52 possible** | P6 ("high frequency, near-zero willingness to pay, no measurable articulated pain") | No | None |
| Well-child visit | **~3.0** (1.53/child ×1.94; **5.96/child for infants <1**) | P5 #2 (NCHS NAMCS 2018, Tier A); AAP: 31 visits birth–21, 7 in year one | Recurring, AAP-set | Lapsed preventive care; forms blocked downstream |
| Dental recall | **~3.5** (1.8/child ×1.94; 90% of 5–17 attend ≥1/yr) | P5 #3 (NHIS 2023 via childstats, Tier A) | Recall notice | Cavities; rebooking churn |
| School event (parent-attended) | **~11.6** (6.0/child ×1.94) | P5 #40 (**NHES:PFI 2023, n=19,562 — the single best number in P5**) | **Yes, school-set** | Kid's disappointment; social cost |
| Permission slip / form | **No citable frequency exists** | P5 §"not included"; adjacent: 80+ school emails/month, 62% missed something (BRIEF, already-known) | **Yes, school-set** | Kid excluded from the trip |
| Sports physical | **~1.6** (1/participating athlete × 1.58) | Derived from P4 participation; no direct source | **Yes, league-set** | **Cannot play** |
| Therapy / orthodontia | **~2.9** population-avg (1.5/child ×1.94) but **~12+/yr for the 12.2% in therapy**, and **12–26 visits per treated child** for ortho (every 4–8 wks × 18–24 months) | P5 #7 (NSCH 2023, n=55,162, Tier A); ortho cadence **unsourced** — P5 calls it *"the highest-value unmeasured category"* and *"one of the largest single hidden recurring appointment blocks in a family's calendar"* | Yes, recurring | Missed session, often billed |
| Immunization deadline | **~1** at school-entry ages | P5 (AAP periodicity); no per-family frequency published | **Yes, statutory** | **Excluded from school** |
| Birthday party attended | **No citable source at any tier** — P5 searched specifically | P5 §164 | Yes, host-set | Social |
| Birthday party hosted | **~1.94** (one per child) | P1 #7 for the multiplier; $314 avg spend (P5 #17, Tier C, n=404) | No | Social/emotional |
| ED / urgent care | **~1.65** (0.45 + 0.40 per child ×1.94) | P5 #3, #5 (NHAMCS 2019; NHIS 2022, Tier A) | Unplanned | — |

**P5's own bottom line, which is the load-bearing number of this whole analysis:** a two-kid family
faces **~23 appointment-and-school episodes per year as a sourced floor, ~30–40 including the
categories with no citable source** (P5 line 18) — every one of them N=1 to N=3.

---

## STEP 3 — THE CENTRAL ANALYSIS: STEP COUNT × FREQUENCY

### 3.1 The plot table (chart-ready)

`freq` = episodes per family per year. `N` = step count per episode. `steps/yr` = N × freq — the
total work the object class puts on the parent annually.

| # | Job | N | Freq/yr | Steps/yr | Quadrant |
|---|---|---|---|---|---|
| 1 | Weekly sports logistics | 1 | 200 | **200** | **Q2 Treadmill** |
| 2 | School event (parent-attended) | 1.5 | 11.6 | 17 | **Q2 Treadmill** |
| 3 | Weekend outing | 1.5 | 39 | 59 | **Q2 Treadmill** |
| 4 | Permission slip / school form | 1.5 | ~12 (est., unsourced) | 18 | **Q2 Treadmill** |
| 5 | Therapy / orthodontia session | 1 | 2.9 (12+ in the 12.2%) | 3 (35) | **Q2 Treadmill** |
| 6 | Dental recall | 2 | 3.5 | 7 | **Q3 Recurrence** |
| 7 | Well-child visit | 2 | 3.0 | 6 | **Q3 Recurrence** |
| 8 | ED / urgent care | 1.5 | 1.65 | 2.5 | **Q3 Recurrence** |
| 9 | Sports physical | 3 | 1.6 | 5 | **Q3 Recurrence** |
| 10 | Birthday party attended | 2.5 | unsourced | — | **Q3 Recurrence** |
| 11 | Immunization deadline | 2.5 | ~1 | 2.5 | **Q3 Recurrence** |
| 12 | School-break coverage | 3 | 11.5 | 35 | **Q2/Q1 border** |
| 13 | Fall/spring registration | 4.5 | 5 | 23 | **Q1 Campaign** |
| 14 | Birthday party hosted | 6.5 | 1.94 | 13 | **Q1 Campaign** |
| 15 | Family trip | 7 | 1.5 | 11 | **Q1 Campaign** |
| 16 | Summer camp | 9 | 1 cycle (7.5 sub-bookings) | 68 | **Q1 Campaign** |

### 3.2 The quadrants, named

Cut at **N ≥ 4** (deep) and **freq ≥ 8/yr** (frequent):

- **Q1 — CAMPAIGNS (deep, rare).** Summer camp, fall/spring registration, family trip, hosted
  birthday. High N, 1–5×/yr. **The six-stage lifecycle is correct here and nothing else would be.**
  These carry the money (P3: $893–954/child summer, >$3,000 for two, ~20% of summer take-home;
  P4: $1,490.66 per participating child on sports) and the acute pain (P3: 87% report work
  disruption, 49% dread summer).
- **Q2 — TREADMILL (shallow, frequent).** Weekly sports logistics, school events, permission slips,
  outings, therapy sessions. N=1–2, dozens to hundreds per year. **Volume lives here.** Individually
  near-zero willingness to pay (P6 on outings, verbatim: *"near-zero willingness to pay, no
  measurable articulated pain"*), but P4 is unambiguous that in aggregate this is the top-rated pain:
  **~8 in 10 youth-sports parents call scheduling/logistics/time a challenge — MORE than the ~7 in 10
  who say cost** (AP-NORC/Ipsos KnowledgePanel, July 2026, n=510 sports parents, Tier B).
- **Q3 — RECURRENCES (shallow, rare).** Dental recall, well-child, sports physical, immunization,
  birthdays attended. N=2–3, 1–4×/yr each, but **provider-set, deadline-hard, and consequential** —
  a missed sports physical means the kid cannot play; a missed immunization means exclusion from
  school. These need a *recall* primitive, not a workflow and not a to-do list.
- **Q4 — deep AND frequent: EMPTY.** No job in the entire research corpus lands here. **That is the
  finding.** Nothing a parent does is both eight steps and weekly. Depth and repetition are
  anti-correlated in this domain, which means a product cannot amortize workflow ceremony across
  frequency — the ceremony is paid fresh each time on objects that recur, and those objects have no
  steps to justify it.

### 3.3 The volume verdict: hypothesis CONFIRMED

For a representative two-kid family with kids in the 6–12 band (the modal case — P1 §4: the 35–44
householder band is 13.7M households, ~60% with a 6–11-year-old):

| | Object count/yr | Total steps/yr |
|---|---|---|
| **Q1 Campaigns** (N≥4) | **~16 objects** (1 camp cycle ≈ 7.5 bookings + 5 registrations + 1.5 trips + 2 parties) | **~115** |
| **Q2 + Q3 Shallow** (N≤3) | **~280 objects** | **~355** |
| **Ratio** | **17.5 : 1** | **3.1 : 1** |

**Shallow objects outnumber deep objects roughly 18 to 1 by count, and still win 3 to 1 when you
weight every object by its own step count.** The founder's intuition that camp generalizes is
correct about *mechanism* — research→register→pay is a genuine chain — and wrong about *share*. Camp
is the tail, not the distribution. A product whose only object constructor is the camp workflow can
represent about 5% of what a family actually plans.

Two collectors reached the same conclusion independently, without being asked this question:

> **P5:** *"a family plans camp roughly 1–2 times/year (summer, plus school-break care)"* — so
> appointments and school admin generate **"~12–20× more discrete planning events per year than
> camp."**

> **P4:** *"Camp (on by default) is a 1–2 episode/year job. Extracurriculars are a 150–250-event/year
> job."* And: *"discovery fires maybe 4–6 times a year per family while comms fires daily."*

My 18:1 count ratio and P5's independent 12–20× estimate agree to within the width of the estimates.
This is not a marginal call.

### 3.4 The counter-weight, stated honestly

Frequency and willingness to pay sit in different quadrants, and this is the real tension the
founder's framing is trying to resolve:

- **Money is in Q1.** Camp $893–954/child and 62% taking on debt; sports $1,490.66 per participating
  child. Parents already spend four figures here, and the failure mode is expensive and dated.
- **Frequency is in Q2/Q3.** And P6 is blunt that the high-frequency discretionary end has *near-zero
  WTP* with free, excellent, already-adopted substitutes.
- **P11 resolves it.** Its honest tally of what this product does that ChatGPT cannot: *"registration
  watchlist, lifecycle board, coverage-gap detection, multi-adult shared context — and all four are
  the same underlying thing: durable structured household state that something acts on without being
  asked."* All four are Q1 mechanisms. But P11 also names the failure mode: *"it is that the
  assistant never accumulates enough state to be missed"* — and Q1 objects arrive ~16 times a year.
  **Sixteen touches a year cannot build a habit or accumulate state.**

So: **Q1 justifies the price; Q2/Q3 justify the app being open.** You need both, which is precisely
why the unification question matters rather than being an architecture nicety. And P9 sets the clock:
**82% of trial starts happen the same day as install and 55% of trial cancellations occur on Day 0**
(RevenueCat, Tier B) — the product must deliver value in session one, in August, when the camp
workflow has nothing to do and the treadmill has seven events that week.

### 3.5 Where the founder's generalization is straightforwardly right: seasonality

This deserves its own heading because it is the strongest argument *for* the unification, and it is
not the argument the framing makes.

P7 pulled 40 US keyword series from Google's `trends/api` directly (5 years weekly, `geo=US`,
resolution WEEK, Tier B) and computed coefficients of variation. The individual jobs are violently
seasonal, and they are seasonal at **different times**:

| Series | CV | Trough | Peak month |
|---|---|---|---|
| spring break camp | 1.577 | 1 | Mar |
| flu shot | 1.076 | 4 | Oct |
| back to school | 0.974 | 11 | Aug |
| summer camp | 0.633 | 11 | May |
| camp registration | 0.486 | 22 | — |
| family road trip | 0.214 | — | Jun |
| kids activities near me | **0.142** | **64** | Jul |
| birthday party ideas | **0.124** | **63** | Jan |
| well child visit | **0.119** | **56** | Jul |
| dentist appointment | **0.099** | **73** | Jul |

Every registration curve **leads its season by 2–6 months**, and the leads rotate: Nov (winter sports,
camp opens) → Jan–Feb (spring sports, the camp mass wave) → Mar (spring-break camp) → Jun–Aug (fall
sports, afterschool) → Oct–Nov (winter sports). P7's summed all-task load by month is
Jan 20 / Feb 22 / **Mar 25** / Apr 20 / May 19 / Jun 19 / Jul 19 / **Aug 17 / Sep 17** / Oct 22 /
Nov 21 / Dec 20 — and its own conclusion is decisive:

> *"The column totals are startlingly flat: 17 to 25 across all twelve months, a **1.47× spread**.
> Aggregate parent planning load has no off-season. It rotates."*

**This vindicates generalization on its own terms.** A camp-only product is dead for three months a
year — P3/P7 put the true dead window at **August, September and October**, which is *right now*,
2026-08-21, and is exactly when a new install would land. A product spanning many jobs never has an
off-season. That is a real and important reason to build one engine rather than five apps.

But note precisely *which* generalization the flatness argument endorses. **The three task families
P7 identifies as effectively aseasonal — medical/dental (CV 0.099–0.124), birthday parties (0.124),
weekend outings (0.142) — are all Q2/Q3, and the product has no concept for two of the three.** P7
says so flatly: *"the product has… no birthday-party concept."* The jobs that flatten the curve are
precisely the low-N jobs the engine cannot represent. Generalizing across *subject matter* buys the
flat curve only if the new subjects can actually be stored, and today they cannot.

One caveat P7 states about its own instrument, which strengthens the point: Google Trends
*"over-weights tasks people research online (camp discovery, party venues, vacation ideas) and
under-weights tasks people execute without searching (renewing an existing activity, a recurring
pediatric appointment, the fourth season with the same soccer club). The flat rows may therefore be
understated."* The measurement bias runs in favor of the camp end — and the treadmill still wins.

---

## STEP 4 — CAN ONE PRIMITIVE SERVE N=1 AND N=8?

**Yes — but only by inverting which object is the atom. The six-stage lifecycle does NOT degrade
gracefully, and the fix is not a separate lightweight path; it is making the lightweight thing the
base case and the workflow an optional attachment.**

### 4.1 Does the 6-stage lifecycle degrade to a 1-step obligation? No — six specific failures

Take "Dentist, Maya, Thursday 3pm" and push it through the engine as it stands:

1. **It enters at the wrong end.** Default status `exploring` (`tools.py:132`, `duckdb_storage.py:819`)
   → `stage_for` → section "Considering / *Saved ideas — decide yes or no when you're ready*"
   (`lifecycle.py` STAGES). There is nothing to decide.
2. **Recording it truthfully hides it.** Set it to `confirmed` and `stage_for(status, 0)` returns
   `all_set` — *"Registered and nothing left to do"*, rendered collapsed. **The correct status
   produces the wrong visibility.** The board has no representation for "settled, but it hasn't
   happened yet."
3. **Recording it manufactures a step.** `on_enter_watched` fires and, with Gmail unconnected, seeds
   *"Forward or paste Dentist's confirmation email"* (`lifecycle.py`). N goes from 1 to 2 by machine
   action.
4. **The CTA vocabulary is wrong.** `next_step` can only emit "We'll do it" / "Register" / "Mark
   registered" / a to-do title / "Reconsider" (`lifecycle.py`). None of these is "Thursday, 3pm."
5. **The date renders wrong by default.** `format_when` falls through to `"Week of Mar 9"` unless the
   vertical's `date_model` is `single_date` or `date_range` — and there is no appointment vertical.
6. **It is uncreatable.** No iOS surface constructs a tracked activity except pinning a discovery
   candidate (`PlanViewModel.swift:583`), and no surface constructs a to-do at all.

Five of the six failures are *semantic*, not cosmetic — the stage names, the collapse rule, the CTA
enum, and the seeding hook all encode "there was a decision and a registration." You cannot config
your way out of them, which is exactly what §1.2 predicts: the registry has no step-count knob.

### 4.2 The minimum viable representation that covers both

The schema already almost has it. `todo_items` (`duckdb_storage.py:925-939`) carries
`{id, user_id, kid_name, activity_id (NULLABLE), kind, title, detail, due_date, status, source,
source_artifact_id}`. That is the whole atom:

```
OBLIGATION := {
  id, kid,                    -- who
  title,                      -- what
  when: {date | datetime | rrule},   -- the ONE date field, three shapes
  deadline_kind: hard_external | soft_self | recurring,
  trigger: inbound | recall | self | schedule,
  state: open | done | dropped,      -- THREE states, not six
  parent_id: NULLABLE           -- the inversion
}

WORKFLOW := an OBLIGATION that has children.
```

Three moves make this work:

- **Invert containment.** Today an activity (heavy, six states, `name NOT NULL`, `status NOT NULL
  DEFAULT 'exploring'`) owns to-dos (light). Flip it: the obligation is the atom, and a "camp" is an
  obligation with eight children and a provider attached. `todo_items.activity_id` becomes
  `parent_id` pointing at the same table. **N is then data, not schema.** N=1 is one row. N=8 is nine
  rows. There is no degradation because there is no two-model split to degrade between.
- **Collapse six states to three, and derive the rest.** `open | done | dropped` is what a
  one-stepper needs. The camp's six stages become a *rendering* of which child rows are open —
  which is what `stage_for` already half-does today via `open_todo_count` (`lifecycle.py`). Keep the
  six-stage board as a **view over deep objects only**, not as the storage model for all objects.
- **Sort by date, not by stage.** The board's organizing principle is lifecycle position; a family's
  organizing principle is time. Q2/Q3 objects have no lifecycle position and every one of them has a
  date. One time-ordered surface holds both; a stage-ordered surface can only hold Q1.

This is not speculative refactoring — it is ratifying two decisions the codebase already made under
duress: the nullable FK, and `cos/outings.py`'s explicit bypass.

### 4.3 Where the UI forces ceremony — the concrete list

| Ceremony | Where | Cost on a low-N job |
|---|---|---|
| Only entry is web discovery | `PlanViewModel.swift:583`; `StartDiscovery` `tools.py:1048` needs a ZIP | 12 knobs, a 1–2 min async wait, to record a known provider |
| No to-do creation UI | `AddTodo` is agent-only (`tools.py:399`) | Capture requires a conversation |
| Everything starts "Considering" | `tools.py:132`, `duckdb_storage.py:819` | Committed things look undecided |
| `all_set` collapses | `lifecycle.py` STAGES | Imminent obligations hide |
| Confirmation to-do auto-seeded | `lifecycle.on_enter_watched` | N=1 becomes N=2 |
| Week-block default date | `lifecycle.format_when` | A Thursday renders as a week |
| 5 doors → 5 chat starters | `PlanView.swift:1563` `openDoor` | Every capture is a conversation |

#### The ceremony is not a taste question — it is causally measured

P5 surfaces the one experiment that settles this. In two web-based experiments (n=52 each,
within-subject, peer-reviewed, **Tier A**), raising the physical effort of setting a reminder — by
**five extra clicks**, then fifteen — **significantly reduced how often people offloaded an intention
at all**, with the largest drops at high memory load (mean reductions of .50 and .46 reminders at
loads 4 and 6 vs .29 at load 2; **dz 0.71–1.29**).

P5 draws the conclusion for us: *"58 text-entry fields, 12 knobs on Planner, and 16–20 taps to a
saved plan are not neutral: they are an **offloading tax**… A capture surface for this task family
has to be **one gesture, not a form**."*

Three corroborating findings, all pointing the same way:

- **Parents are not using assistants for this today.** In the only tool-inventory study available
  (Brewer/Morris et al., ACM IMWUT 2017, n=280 US adults + a one-week diary, Tier A, dated): digital
  calendar 65.7%, **paper list 62.1%**, paper calendar 53.5%, post-it 50.0%, digital list 37.8%.
  **"Digital assistants did not surface at all."** Paper beats digital for lists — in the diary week,
  16 participants used a paper list against 5 using a digital one.
- **The current fallback actively harms memory.** Screenshotting information to "save" it impairs
  later recall — the digital capture effect, seven experiments, *Memory & Cognition* 2026. Parents
  photographing a flyer are building a write-only archive. That is the demand for the ingest door,
  and it is a real one.
- **Capture modality.** P8: dictation runs 3× faster than thumb-typing for transcription (161.20 vs
  53.46 WPM, 20.4% lower error rate; Ruan et al. 2016, n=32, Tier A) but collapses to **7.8 WPM for
  composition** versus 32.5 typing. Users also *prefer the keyboard for error correction*, and that
  preference measurably improves performance. So the winning gesture is a **short dictated fragment
  rendered into an editable object — voice-in, text-out — not a conversation**, and there is no
  dictation anywhere in the app.

#### The market has already priced this, verbatim

M1 mined **n=4,073 real US App Store reviews** (Apple's public customer-review RSS, US storefront,
10 pages × 2 sort orders per app, deduped) across the incumbent organizers. The corpus is unambiguous
about what kills adoption, and it is entry friction — not missing features:

> *"the iOS app is clunky and inconvenient to add events to… **Ultimately these extra steps. Have
> been a barrier to wider use in our family.**"* — Cozi, 2★, 2026-01-15

> *"**Too many steps to submit an event.** I pay for premium hoping to avoid having too many pop ups
> or extra clicks when entering daily events… To enter an event I have to click the add event button,
> then it asks if I want to use a picture, calendar event, or a 3rd option. This is another click.
> After I submit the event for a given day I'm given yet another notification and to confirm what I
> just did."* — 2★, 2024-05-06

That review is describing, almost line for line, what `on_enter_watched` does when it seeds a
confirmation to-do on an object the parent just recorded.

The praise runs the same axis in reverse — and one quote is direct validation of the ingest door:

> *"It's FREE, it's **quick to add** and update your schedule/calendar… It also has the **simplest
> interface when adding events**"* — TimeTree, 4★

> *"The new feature that allows you to create events from your camera or from pictures you have taken
> already of flyers or posters etc. **is genius. It literally makes inputting events into your
> calendar effortless and super quick.**"* — 5★, 2024-07-08

And on voice, the corpus is a caution: *"I wouldn't mind an AI so I can quickly speak an event, but
even without fancy features, I'll still keep using it"* (5★) — M1's read is that voice is a
nice-to-have, **not a switching reason**.

P9 prices the rest: the 10-second attention limit (Nielsen, Tier A) against a 1–2 minute discovery
run — **6–12× the threshold**, and P9 notes a progress bar buys "tens of seconds, not two minutes";
~8 fields optimal (Baymard) against 12 knobs and 58 text fields app-wide, which P9 calls *"roughly
five complete e-commerce checkouts' worth of typing."*

### 4.4 What this implies for the five doors

**The doors are the cheapest thing in the system to change, and the most wrongly cut.**

`openDoor` (`PlanView.swift:1563-1570`) does exactly three things: fire `door_opened`, switch to the
chat segment, and `cosVM.send(door.starterPrompt)`. **A door is a canned first chat message.** It is
copy, not architecture. Re-cutting them costs a registry edit and a prompt-section edit.

And the code already made the right call once and then contradicted it. `PlanView.swift:23-24`
comments that the vertical chip is *"attribute, never navigation."* Correct. But the doors — which
*are* navigation — are cut on that same attribute. Verticals should be an attribute in both places.

**Cut doors by trigger × depth instead.** Four doors, mapped to how the object actually enters the
parent's awareness:

| Door | Trigger | Depth | Serves | Objects/yr |
|---|---|---|---|---|
| **"Something's coming up"** | Self, remembered | N=1 | Appointments, one-offs, anything | ~100+ |
| **"Here, deal with this"** | Inbound (photo/email/paste) | N=1–3, auto-derived | Permission slips, school events, flyers, recalls | ~40 |
| **"Find something"** | Self, research needed | N=4–10 | Camp, classes — **the six-stage board** | ~16 |
| **"Cover these weeks"** | Calendar (school closures) | N=2–4 × many | Break coverage — the highest-pain job | ~12 |

Camp, class, trip, outing, school_event survive as `activity_type` chips — filters and copy — exactly
as the chip comment says they should. Note what this fixes: today **three of five doors are behind
flags that default off** (extracurricular, school_event, trip), so a parent in August sees two doors,
both of which want to run a web search. Under the trigger cut, the always-on doors are the ones with
volume behind them.

**Two verticals should not be doors under any cut.** `outing` already bypasses the engine
(`cos/outings.py`) — it is a chat answer, not a plan object, and P6 rates it *"high frequency,
near-zero willingness to pay, no measurable articulated pain."* `trip` runs 2–4×/yr against a free,
already-adopted substitute — **59% of travelers with children have already used ChatGPT or similar
for travel planning** (MMGY *Portrait of American Travelers* Fall 2025, n=4,503, Tier C) — and P6's
verdict is verbatim: *"Confirms the internal 'weakest vertical' rating."* Both are chips at most.

**The honest counter-argument, stated.** P9's benchmark scorecard rates *"5 verticals, 3 defaulted
off"* as **WITHIN NORM** — the one dimension of the app it does not flag — on the grounds that
defaulting three off is exactly what the feature-fatigue literature prescribes. That is fair, and it
means re-cutting the doors is not urgent *as a complexity reduction*. The argument for re-cutting is
not that five doors is too many; it is that all five are cut on an axis (subject matter) that does
not predict what the parent needs to do, while the axis that does (trigger and depth) is invisible.
Four doors is not meaningfully simpler than five. It is meaningfully *truer*.

**What the re-cut is really buying** is a place to put the demand P4 measures and the product
currently has no surface for: **17.5 communications per week about kids' activities and 11.5
activities tracked per week** (Harris Poll for Skylight, n=2,005, May 2024, Tier C, vendor-interested)
and **44% of parents managing 7–9 apps per child with only 21% having any unified view** (Edsby/
Cornerstone, n=125, Tier C, directional only — P4 notes no probability-sampled study of app sprawl
exists anywhere, and calls it *"a genuine, fundable gap"*). Both numbers are weak. But both point at
the same door — "deal with this" — and it is the one door with daily traffic.

---

## STEP 5 — SERVING THE POPULATION

Cohort weights (P1 #5, A-derived from Census Table F1 2023, CPS ASEC): **Millennial 18.2M households
(54.5%), Gen X 11.7M (35.1%), Gen Z 2.0M (6.0%)**. The decisive variable is not the parent's birth
year — it is **the age of the child**, and P1 #10–13 show how tightly the two are coupled.

### 5.1 Gen Z parents (6.0%, ~2.0M households) — kids 0–5

**84.1% of 25–29-headed parent households contain a child under 6; 56.4% a child under 3; only 7.5%
a teenager** (P1 #10–13, Census Table F1 2023).

The Q1 quadrant does not exist for them. P4: children **0–5 have effectively zero organized-activity
load — the federal instrument does not even ask below age 6.** P3: camp barely applies; day care is
only 6% of K-12 summer arrangements. P1's own judgment: *"Camp, extracurricular, school_event and trip
are essentially irrelevant to a household whose only child is under 3 — there is nothing to register
for, no school calendar, no camp season. That describes roughly half of all Gen Z-headed parent
households."* P10: *"a camp-and-extracurricular planner is a job that begins around age 4–5."*

But **Q3 is at its lifetime maximum**: infants under 1 make **5.96 office visits/year vs 1.53 for
ages 1–17** (P5 #2, NCHS NAMCS 2018, Tier A), and AAP Bright Futures prescribes **7 well visits in
year one, 31 birth-to-21** (P5 #1, Tier A).

**What the engine should do differently for 0–5:** turn discovery, the coverage-gap model and the
six-stage board *off entirely* — there is no school calendar to have gaps against. Ship one thing:
**a well-visit and immunization schedule generated from the child's date of birth.** The AAP
periodicity schedule is a published deterministic table, not a search problem — the product can
populate a year of correctly-dated obligations from one field the onboarding already collects, at
zero taps. That is the single highest-leverage feature in this entire analysis for this cohort, and
it is pure Q3 recall with no workflow at all.

Caveat, stated: **6.0% of households**, and P1 shows fertility migrating up the age curve (30–34 rate
93.7 has exceeded 25–29's 89.5 every year since 2016; mean age at first birth a record 27.6). Build
for Gen Z as *retention through aging-in*, not as an acquisition segment.

### 5.2 Millennial parents (54.5%, ~18.2M households) — kids 6–12, the core

This is the only cohort where **both quadrants are simultaneously live**, and it is where the current
product is correctly aimed.

- Q1: peak camp spend (**$954/child vs $893 all-parent average**, P3, LendingTree 2025); the
  elementary/middle band where day camp is the modal summer activity (**29% elementary**, Gallup/NSLA/
  ACA 2024, n=6,899, Tier B). Mean youth-sports parent age **40.84** — squarely Millennial (P4, Aspen
  2024).
- Q2: 6–12 is peak organized-activity load and rising; afterschool dosage highest at **5.9 hrs/wk
  elementary** vs 4.8 middle, 4.5 high school (P4, AA3PM 2025). **~200 logistics events/yr.**
- Q3: 6.0 parent-attended school activities per child (P5 #40, NHES:PFI 2023, n=19,562, Tier A) plus
  the full appointment load.
- Structural intensity: both-parents-employed **69.4% when kids are 6–17** vs 65.3% under 6 (P1 #22);
  maternal LFPR **78.2% vs 68.0%** (P1 #21, BLS 2025).

**What the engine should do for 6–12:** everything, but with the treadmill layer added *underneath*
the campaign layer rather than beside it. Note the risk P8/P11 jointly flag: this cohort uses AI most
(**daily chatbot use peaks at 30–49 at 34%**, Pew 2026, n=5,119) while being **least self-confident
with it** (only 23% extremely/very confident vs 31% of 18–29s). They will adopt an agent and will not
trust it unsupervised — which argues for the agent *drafting* obligations that the parent confirms in
one tap, and against the agent silently running an eight-step workflow.

### 5.3 Gen X parents (35.1%, ~11.7M households) — teens 13–17

**73.5% of 45–49-headed parent households contain a 12–17-year-old; only 12.8% a preschooler**
(P1 #11, #10).

The job mix inverts. P3: the modal summer activity flips to a **job/internship (32%)** in high school
and overnight camp usage falls — *"the registration-race job decays into a different job."* P4: 13–17
regular sports participation **fell 3% in 2024**, but the surviving cohort is the most intense
(travel/club, longest seasons, a primary sport alone spanning **1.86 organizational settings**).
P5: urgent-care use is **highest at 12–17 (30.3%)**. And single-parent share rises with child age —
**22.2% of children 15–17 live with mother only vs 18.2% of under-6s** (P1 #18).

So Gen X's demand is **Q2 + Q3, almost none of Q1**: transport, don't-miss deadlines, sports
physicals that gate participation, and multi-org coordination. The discovery engine — 38% of the tool
surface — has almost nothing to sell 11.7M households.

**What the engine should do for 13–17:** drop discovery to a background utility; lead with capture,
deadline recall, and the logistics assignment model (`AddCaregiver` / `AssignLogistics` already
exist and are depth-agnostic — `tools.py:327, 357`). Add the teen as a second actor: P10 notes 88% of
US teens own an iPhone (Piper Sandler 2025, Tier C, flagged as the weakest inference in that report)
and 64% of teens 13–17 already use AI chatbots (Pew, Tier A/B) — but P11 is emphatic that parents
*"trust AI companies far less than they trust the output,"* with **84% concerned about AI misusing
young people's data** (Common Sense, Tier B). So: the teen may *receive* logistics, never be
*handled* by the product.

### 5.4 The engine's behavior by child age, in one table

| Child age | Live quadrants | Discovery | 6-stage board | Coverage-gap model | The one thing to ship |
|---|---|---|---|---|---|
| **0–5** | Q3 only | **Off** | **Off** — nothing to hold | **Off** — no school calendar | AAP well-visit + immunization schedule generated from DOB, zero taps |
| **6–12** | Q1 + Q2 + Q3 | **On** — earns its place | **On** for Q1 objects | **On** — the highest-pain job | Camp/break coverage *plus* a one-gesture capture for the ~200 treadmill events |
| **13–17** | Q2 + Q3 | Background utility | Rarely populated | Partial (teens self-cover) | Deadline recall + transport assignment; sports physical as a first-class gating obligation |

One measurement note that cuts across all three rows: **the sports physical is the cleanest
unserved job in the corpus.** It is hard-deadlined, institution-set, gates participation outright,
and P7 measured its timing precisely — *"school physical"* peaks at **Aug 100** and *"sports
physical"* runs **Jul 95 → Aug 100** — while P5 records that **no citable US frequency data exists
for it at any tier.** A back-to-school clearance obligation with a known date, a known consequence,
zero research step and no competitor concept is exactly the shape the inverted primitive handles and
the six-stage board cannot.

---

## SUMMARY OF THE ARGUMENT

1. The engine is general across subject matter and rigid about depth. `VerticalProfile`
   (`app/cos/verticals.py`) parameterizes copy, three capability booleans, one coverage boolean and a
   five-valued `date_model`. **There is no step-count knob.** Adding a vertical touches eight places
   across three surfaces plus two locking tests — config-plus-prose-plus-two-client-constants, not
   config.
2. Six of the engine's core assumptions are camp facts, not planning facts: a decision exists, a
   registration exists, the provider is discovered, the unit of time is a week, done is collapsible,
   and recording implies paperwork. `on_enter_watched` **manufactures a second step on every
   one-step object.**
3. Mapping every researched job onto (N, frequency) gives four quadrants, one of which is **empty**:
   nothing a parent does is both deep and frequent. Depth and repetition are anti-correlated, so
   workflow ceremony can never be amortized.
4. **Shallow objects outnumber deep objects ~18:1 by count and ~3:1 by total steps.** The camp
   workflow, generalized perfectly, still addresses ~5% of what a family plans. Hypothesis confirmed
   — and confirmed independently by P5 (*"~12–20× more discrete planning events per year than camp"*)
   and P4 (*"Camp is a 1–2 episode/year job. Extracurriculars are a 150–250-event/year job"*).
5. But the money and the defensible mechanism are in the deep 5% (P3/P4 spend; P11's four genuine
   wins are all Q1 mechanisms) — so this is a both-or-nothing problem, not a pivot. **And
   generalization is independently vindicated by seasonality:** every single job is violently
   seasonal while P7's aggregate load varies only 1.47× across the year. A camp-only product is dead
   in Aug–Sep–Oct; a many-job product has no off-season. But the three task families that flatten the
   curve (medical/dental, birthdays, outings — CV 0.099–0.142) are all Q2/Q3, and the product has no
   concept for two of the three.
6. One primitive can serve both, by inversion: **the obligation is the atom, a workflow is an
   obligation with children, N is data.** The schema already permits it (`todo_items.activity_id` is
   nullable, `duckdb_storage.py:929`) and the team already proved the alternative fails
   (`cos/outings.py` bypasses the entire lifecycle for the lowest-N vertical, and says so in its
   docstring). The ceremony cost is causally measured, not aesthetic: **five extra clicks
   significantly reduced whether people offloaded an intention at all** (n=52×2, dz 0.71–1.29,
   Tier A, via P5) — and 4,073 mined App Store reviews say the same thing in parents' own words
   (*"Ultimately these extra steps. Have been a barrier to wider use in our family"*).
7. Doors are canned chat openers (`PlanView.swift:1563`), so re-cutting them is free. Cut by trigger
   and depth — *coming up / deal with this / find something / cover these weeks* — and demote camp,
   class, trip, outing, school to chips, which the code's own chip comment already argues for
   (`PlanView.swift:23`).
8. By cohort: Gen Z (6.0%, kids 0–5) needs Q3 only and should get a DOB-generated AAP schedule with
   the board switched off; Millennials (54.5%, kids 6–12) are the only cohort needing the full engine
   and need the treadmill layer added under it; Gen X (35.1%, teens) needs Q2/Q3 — capture, recall,
   transport — and has almost no use for the 38% of the tool surface devoted to discovery.

### What would falsify this

Stated so the argument is checkable rather than merely asserted:

- **If the Q2/Q3 volume is real but inert.** The whole case rests on volume translating into product
  value. P6 shows the highest-frequency discretionary job (outings) has *near-zero* willingness to
  pay, and P9's void — *"share of US households sustaining a shared digital family calendar: NO DATA
  FOUND AT ANY TIER… probably the single most decision-relevant unknown"* — means nobody knows
  whether families sustain a capture habit at all. If they don't, the 280 shallow objects are a
  number, not a market.
- **Two step counts in my table are unsourced.** Permission slips (~12/yr) and birthday parties
  attended are estimates; P5 searched for both specifically and found nothing at any tier. Removing
  both drops the shallow count from ~280 to ~250 — the ratio survives, but say so.
- **The cheapest test.** Ship one manual-add field and one to-do row (both already representable in
  storage today) with no board, no discovery, no lifecycle, and instrument creations per user per
  week against `activity_tracked`. If shallow captures do not exceed tracked activities by an order
  of magnitude within four weeks, this analysis is wrong and the board is the right center of the
  product.
