# Shared Research Brief — 2026-08 Parent Planning Behavior Study

Every collector, miner, verifier, and synthesist reads this file first. Today is 2026-08-21.

## The decision this research serves

A US consumer app ("MVP", a working codename) helps parents plan their kids' lives. We must decide
what to double down on, what to simplify, and what to cut. We need a defensible, cited ranking of
planning jobs by demand across THREE parent generations, an answer on voice vs. typing, and a read on
how much product complexity this population will absorb.

## The three cohorts (use these exact bands; state them in every finding)

| Cohort | Birth years | Age in 2026 |
|---|---|---|
| Gen Z parents | 1997–2012 | ~18–29 |
| Millennial parents | 1981–1996 | ~30–45 |
| Gen X parents | 1965–1980 | ~46–61 |

Geography: **United States only.** If a source is global, say so and do not present it as US.

## OUTPUT CONTRACT — follow exactly

Return markdown with two clearly separated sections:

### Section 1: FINDINGS
A table, one row per finding:

| # | Claim (one sentence, with the number) | Value | Cohort/segment | Publisher | Year | Method (n, fielding window, population) | Tier | URL |

Then, below the table, 3–8 short paragraphs of interpretation — what the numbers mean for the decision
above, including explicit contradictions between sources.

### Section 2: WEAK SIGNAL
Anything you could not source to Tier A/B/C. Never mix these into Section 1.

## SOURCE TIERS — enforced

- **A** — government or peer-reviewed: US Census (ACS/CPS), BLS (ATUS), NSCH, NHIS, MEPS, CDC, NCES, peer-reviewed journals.
- **B** — major research organizations publishing methodology: Pew Research Center, Harris Poll, Bright Horizons Modern Family Index, Aspen Institute Project Play, Edison Research, RevenueCat, Gallup, Nielsen, eMarketer.
- **C** — industry/vendor reports that disclose method. Tag vendor-interested sources as such.
- **D** — SEO stat-aggregator blogs, listicles, content-marketing "N statistics for 2026" pages.

**HARD RULE: Tier D is never citable.** If you find a number only on aggregator blogs, treat the blog as
a lead: trace it to the origin publisher and fetch that directly. If no origin exists, the number goes in
WEAK SIGNAL, flagged as unverifiable. This topic space is heavily polluted by stat laundering — several
numbers circulate with no traceable origin. Finding and killing those is as valuable as finding real data.

**No number without publisher, year, and method.** "71% of users say X" with no n and no fielding date is
WEAK SIGNAL, not a finding.

Prefer 2024–2026 data. Anything older than 2020 must be flagged as dated in the Method column.

## WHAT WE ALREADY KNOW — do not restate

The repo already contains deep desk research. Do NOT re-derive any of the following; if you encounter
them, note "already known" in one line and move on:

- Parenting-app market size (~$1.7–2.0B global 2025) and analyst disagreement.
- Competitor pricing: OurFamilyWizard $110–299.88/parent/yr, Cozi Gold $39/yr, Skylight Plus $79/yr,
  Ohai $99/yr, Nori ~$8/mo. Milo shut down January 2026; Yohana US ended 2025-09-30.
- Good Inside $34M revenue / 100K+ subscribers.
- Headline mental-load stats: Bath 2025 (mothers carry ~67% more to-do items, 13.72 vs 8.2);
  Bright Horizons 85%/90% summer sleep-loss; Yahoo/Censuswide 80+ school emails/month, 62% missed something.
- US summer camps ~$4.6B (IBISWorld 2025); youth sports $1,016/child (Aspen 2025, n=1,848);
  extracurriculars $731/child.
- RevenueCat hard-paywall vs freemium conversion (~5x).

**What is genuinely missing and therefore valuable:** distributions rather than headlines (who plans,
broken out by gender × employment × kid age × household type), a normalized cross-task comparison,
anything on interaction modality, anything on complexity tolerance, anything comparing the three
generations, and verbatim customer language.

## THE PRODUCT (ground your interpretation in this)

Shipped today, verified by code audit:

- **5 tabs**: Home, Coach, Planner, Circle, Settings. 94 SwiftUI views, 44 tracked screens, 28,307 LOC.
- **Onboarding**: a form wizard of 8+N screens (N = number of kids); 14 discrete input fields for one
  kid, 19 for two; ~34 taps if fully filled. Only 2+N fields are strictly required. **No conversational
  onboarding path exists.** After finishing, a SECOND setup sequence auto-presents from Home with ~5 more
  full editor stops.
- **Planner**: discovery agent searches the live web (ZIP + radius + category + max-results + optional
  free-text focus), runs 1–2 minutes async, returns fit-scored candidates. A 6-stage lifecycle board
  (considering / to_register / registered / all_set / blocked / declined), conflict + coverage-gap
  detection, to-dos, XLSX export, expiring read-only share links. **12 user-settable knobs on this tab;
  16–20 taps on a realistic path to a saved plan.**
- **5 verticals** ("one agent, five doors"): camp, extracurricular, outing, school_event, trip.
  **Only camp and outing are on by default** — extracurricular, school_event and trip are behind
  feature flags that default off.
- **Voice**: ElevenLabs full-duplex conversational calls in exactly 2 places — a button in the Coach tab,
  and a separate kid-facing companion mode. No conversational voice in Planner, Home, Circle, Settings.
- **Dictation — CORRECTED 2026-08-21, supersedes any earlier statement in this brief.** An earlier
  version of this brief told collectors "there is no dictation anywhere in the app." That is now FALSE.
  A `DictationController` (140 LOC, SFSpeechRecognizer-based) was built on 2026-08-21 as part of an
  uncommitted "Heisman" onboarding redesign. It is wired into FOUR onboarding files ONLY
  (`OnboardingHeismanScreens/Tail/Extract/Chrome.swift`). It is NOT in the Coach composer, NOT in the
  Planner, NOT in the profile editors, and NOT in any of the app's other ~58 text-entry fields.
  Correct framing for analysis: **the dictation pattern is now proven in-house and scoped to onboarding;
  the open question is whether to extend it to capture surfaces**, not whether to invent it.
  The same uncommitted sprint also adds an unauthenticated-first onboarding funnel with live anonymous
  extraction and a day-zero Home — which partially addresses the onboarding-weight findings below.
  Treat all onboarding measurements in this brief as describing the LEGACY funnel that is being replaced.
- **Two separate chat surfaces**: the Coach tab, and "Ask the coach" inside the Planner (a 22-tool agent).
- **Integrations**: two-way Google Calendar sync, Gmail ingestion of camp/school email, photo/flyer
  ingestion (PhotosPicker; no in-app camera), a registration-window watchlist with push notifications.
- **58 text-entry fields** across the app; one profile screen alone has 18 open free-text fields.
- **Absent**: any general "add an appointment / remind me" capture surface; shared or assignable task
  lists with a partner; a document vault; Apple/Outlook calendar support; dark mode.

## LIMITS

Do not fabricate. If the data does not exist, say "no data found" — that is a finding, and for Gen Z
parents especially it is the expected answer in several areas. Never extrapolate a number and present it
as sourced. Mark your own confidence.
