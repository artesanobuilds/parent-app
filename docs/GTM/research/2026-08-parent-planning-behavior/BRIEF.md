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

---

## VERIFIED CORRECTIONS — 2026-08-21, Phase 3. These OVERRIDE any collector report.

Synthesis and chart-building agents MUST use these values, not the originals.

**Cohort sizing (V1).** The Gen Z / Millennial / Gen X parent-household split of 2.0M / 18.2M / 11.7M
is a **2023 householder-age snapshot**. Recomputed on this study's 2026 age bands from the same
Census Table F1, Gen Z parent households are **~3.6M (~10.9%)** — nearly double. Any statement that
Gen Z is ~6% of parent households is wrong. The cohort is larger than the collectors assumed, though
the child-age argument (their kids are infants/toddlers, so the camp/activity job has not started)
is unaffected and still stands.

**The planning gap, by employment (V1).** The headline "household management gap is 2.0x, and 3.0x
when the youngest child is 6-17" is ALL parents. For **employed** parents — the actual buyer — ATUS
Table 8B gives **8.4 vs 4.8 min/day = 1.75x**, and 1.33x overall for employed vs 3.1x for
not-employed. The 2.0x/3.0x headline is levered by non-employed mothers. Use the employed figures
when reasoning about the customer.

**Daminger (V1).** Only **decision-making** is exempted as roughly equal. "Identifying options is
also equal" is NOT established — Daminger finds women do more cognitive labor overall. Do not argue
that the Planner sits entirely in a gender-neutral middle.

**Gallup (V1).** Women lead **6 of 12** tasks in dual-full-time households, not 8 of 12. ("Family
activity planning is one of the shared tasks" is confirmed and may stand.)

**Trends volume (V3).** The seasonality CV method is sound, but flatness must never be presented as
demand size. On a shared scale: summer camp 36.6, kids-activities 3.5, dentist 1.5 — summer camp's
WORST month exceeds dentist's BEST by ~4.5x. Any chart must carry a volume axis. **Do not publish**
the "aggregate load varies only 1.47x across the year" figure — it is an artifact of row
normalization plus ordinal truncation. The fine CV ranking (dentist flatter than pediatrician) is
not robust to quantization; only the flat-vs-spiky separation is. The forward-year experiment
(Nov/Dec doubling, Jan tripling, Aug-Oct dead window) reproduced exactly and IS publishable.
Trends is Tier C/D (raw feed, no disclosed n), not Tier B, and is not parent-scoped.

**Obligations per year (V2).** Use **~23/yr, honest band 20-26** for a 2-kid family. The
sourced-only floor is **~15.06**, dropping to **~9** if two siblings share a school — not 15.96.
ED and urgent-care visits are unscheduled and must be excluded from any count labelled "scheduled."
NCES publishes the mean as a rounded integer 6, so decimals are false precision. Corrected inputs:
ED **0.48**, orthodontia **0.22**, dental band 0.9-1.8 (1.8 is a ceiling, not a midpoint).

**Complexity language (V4).** **"SEVERE OUTLIER" is banned from the report** — no screens-to-
completion distribution exists, so "outlier" is unavailable. Rename the column `Analyst call` and
add `Evidence strength: direct / adjacent / none`, under a heading stating it is analyst judgement,
not measurement. The 1-2 min Planner wait may be stated as "6-12x Nielsen's verified 10-second
limit" verbatim. Note that checkout fields are largely autofillable while ours are generative, so
the field-count comparison understates our burden — publish as comparison, never as a score.

**Retention modelling (V4).** RevenueCat's 21.1%-at-12-months AI figure is **monthly-plan** scoped.
For an annual product model from **44.1% yearly vs 17.0% monthly** (a 2.6x plan-type effect that
dwarfs the ~1.4x AI effect), applying an explicit, sensitivity-tested AI haircut.

**Platform absorption dates (V4).** Apple's personal-context Siri is **beta later in 2026** — there
is no September 2026 date and no pricing statement. Gemini's "free-tier rollout March 17 2026" is
unverifiable. Absorption is real; the specific dates are not. Also: "55% of trial cancellations on
Day 0" is **55.4% of 3-day-trial cancellations**.

**Attribution fixes.** The public-voice-shame study (n=860) is **Kowalczuk & Musial**, NOT "Distel
et al." — that author does not exist. The "71% prefer voice" figure does not appear in the PwC
report at all (misattribution, not a stripped qualifier). Juniper's device forecast target year is
**2024**, not 2026. The AP-NORC youth-sports survey is **Ipsos KnowledgePanel**, not NORC, and its
"logistics above cost" gap is directional only — at ±4.9 on n=510, 76 vs 74 round identically.

**Trips (V3).** P6's "73% affordability vs 43% planning" compared two different survey batteries.
The correct within-battery figure: **"planning the trip" ranks 27%, 6th of 17** obstacles, and 6%
among parents unlikely to travel. The rejection of the trips vertical gets stronger, not weaker.

**Weak-source qualifiers that must travel with the number.** The "88% of mothers own scheduling"
figure must carry "in a sample of 393 mostly graduate-degreed mothers, fielded 2005-2010." The
"affluent families miss more appointments" finding is **RR 1.02, cold months only, one PA/NJ
network**, from a paper titled *Extreme Temperatures and Missed Pediatric Preventive Care Visits* —
it cannot carry a strategic argument. "62% went into debt for summer care" has an undefined
instrument, a base of 383 who *require* care, and a debt-consolidation lender as publisher.

**Data-access note (V1).** bls.gov 403s every direct method in this environment, but **Wayback
Machine `id_` snapshots work** and are the standard BLS route for this project. Also: CPS October
2025 was not collected, so 2025 annual averages are 11-month and BLS states they are "not strictly
comparable with annual averages for other years."
