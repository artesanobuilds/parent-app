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

### Phase-3 corrections, round 2 (V5/V6) — also authoritative

**Quotes are authentic (V5).** A ~19,000-review US App Store corpus was rebuilt from a different live
Apple endpoint; 141 of 142 quoted verbatims located WORD-FOR-WORD, star ratings 100% correct, date
offsets all ±1 day (timezone). Nothing fabricated. TWO fixes: (1) the Duckbill 5-star quote in M2 is a
PARAPHRASE inside quotation marks — replace with the actual text or drop it; (2) M1/M2 sometimes splice
a review TITLE + BODY inside one pair of quotes — state that convention where quotes are used.

**Sample sizes are CORRECT — do not "fix" them (V5).** The Apple RSS cap is ~500 per SORT ORDER, not
per app; M1 used 2 sorts, M4 used 3. M1's 4,073 and M4's 2,006 stand, confirmed against a complete
census for several apps. One slip: M4 covers **6 apps, not 7**.

**M3's ActivityHero audit reproduced EXACTLY (V5)** — 94,848 sessions, 9,008 live, the per-state and
per-metro cells all identical on a re-run. It is the strongest single item in the program. Required
before publication: **redact the Algolia app-id and search key** (ActivityHero's ToS bars disclosing
any part of the service, incl. scraping) and add a ToS footnote; **strike** the claim that seasonality
would not differ by metro (year-round classes in dense metros stay live in August while summer-only
supply expires, inflating the gradient at an August trough); keep the vendor's name inside every
headline number.

**M1's complaint-theme RANKING is analyst judgement, not measurement (V5).** No regex, numerator or
denominator; its two rankings contradict each other. Real counts over 5,847 sub-4-star reviews:
price 14.2%, sync 6.8%. Label it as judgement AT THE POINT OF USE. (M4's rankings DO publish regexes
and denominators and all replicated — M4 may be cited as counted.)

**Voice-vs-capture must be conditioned (V5).** Corpus-wide, voice mentions 0.68% vs capture 0.43% —
so "capture is mentioned far more than voice" is FALSE as stated. It is true only WITHIN products that
ship capture (Jam 7.95% vs 0%; Skylight 0.99% vs 0.51%). The conclusion survives; the sentence must
carry the condition. M5 independently found ZERO instances of conversational voice planning in ~2,300
Reddit comments, and voice grammar there is only "Hey Siri, remind me to…" — capture, not conversation.

**Competitive-set corrections (V5).** **"Ollie" is a PHANTOM — strike it entirely** (five plausible
domains, five unrelated products). Nori launched **2025-11-24**, not ~Feb 2026 — recompute any growth
claim. Panasonic "indefinitely postponed" is unsupported. schoolcase.com → **schoolcase.app**.
Mommy Poppins covers **16 metros, not 12**. **Camperoni is ~1/2 of ActivityHero's live inventory, not
1/18th** (the ~500-listing figure was Feb 2025; their live index now holds ~4,324) — recompute or delete.
M1's "dead by DNS" method is unsound: OurHome serves a live site over http:// and Picniic's domain
resolves to a park. Maple's real artifact is **growmaple.com** (getmaple.co is unrelated Canadian
telehealth) — M2's sunset quotes and the Wander acquisition are verbatim-correct.
Custody X Change DOES publish a methodology (self-described "more anecdotal": attorney interviews run
through the vendor's own software on hypothetical uncontested cases) — the kill stands but must be
rewritten as "method disclosed but not survey-based," not "no method disclosed."
Gallup/NSLA/ACA was fielded May 2024 but asked about **summer 2023** — label the reference year.

**Bright Horizons (V6 sub-agent).** The 85%/90% summer sleep-loss figures are **2026, not 2025**
(Harris Poll, fielded Apr 14-16 2026, n=2,030 adults). CRITICAL: **90% rests on n=479** employed
parents and **85% on n=616** parents of under-18s — never present either as a finding on the full
2,030 sample. MFI is now a multi-wave program; always name the wave. `gtm-strategy.md` carries the
wrong year in its cleared-for-marketing list.

**More kills (V6).** Pew's **"37M Millennial parents" is FABRICATED** — Pew published 17M/19M
Millennial MOTHERS; 37M appears to be 19M doubled. Highest reputational risk in the corpus; it appears
in the repo's own gtm-research.md. The **"$150B missed-appointment cost"** is a 2017 op-ed by a
scheduling-vendor CMO, now contaminating peer-reviewed work by citation laundering. **ActivityHero's
"4M families"/"400k subscribers"** are rate-card marketing with no counting-unit definition — cite only
as "ActivityHero says." **Skylight's "$60,000"** is DERIVED (mental-load hours x a $35.86/hr wage),
never an earnings finding. **All of usecarly.com** is an SEO site for a competing AI assistant with no
method page — it is P11 #41's sole source.

**CASA corrections (V6).** The 100-user lifetime cap is CONFIRMED and understated: Google says twice it
"applies over the entire lifetime of the project, and it cannot be reset or changed," exhausting it
**disables Google sign-in**, and verification lifts it. But the free self-scan died in **2026, not May
2024**, and "all body-reading scopes are restricted" is too broad (`gmail.metadata` is restricted and
reads no body; `gmail.addons.current.message.readonly` reads content and is only sensitive). The
`gmail.modify` conclusion is unaffected. Drop "Google-named preferred partner."

**Feasibility matrix (V6).** **ParentSquare's BLOCKED verdict is UNSOURCEABLE** — its help center is
login-gated, so a strategy-critical verdict rests on a citation no reader can check. It needs a
first-party test before any recommendation leans on it. **Brightwheel is INVERTED** (the guardian can
edit; providers cannot). **Infinite Campus is worse than stated** — no additional-notification-email
field exists at all. PowerSchool confirmed verbatim but the cited URL 404s (use `/pssis-student-parent/`).
Seesaw softens (up to 10 family accounts per child) though its digest is confirmed contentless.
**Gmail forwarding is NOT a collapsed step** — the destination does receive the verification link, but
the source user must still return to Gmail and click Save Changes, and Google shows a week-long banner
warning that unexplained forwarding may mean someone else has account access.

**M5 corpus caveats.** Qualitative and non-representative. Reddit blocked all API/mirror paths, so it is
browser-driven comment search — individual comments, not threads. The sample **skews heavily to
r/adhdwomen and r/ADHD**. No BabyCenter/What-to-Expect/Substack quotes. The "what they wish existed"
theme yielded only 4 usable quotes.

### Phase-3 corrections, round 3 (V7 kill-list second pass) — authoritative

**Kill-list residual error rate: ~22%.** V6 overturned 3 of 12 re-traced (25%); V7 overturned or
reclassified 4 of 18 (22%). V7 states a third pass would likely still find one or two. **Decision: two
passes is where this stops.** The report's method section must disclose the residual rate openly and
the kill-list appendix must carry per-item confidence and verifier attribution. An appendix that admits
its own error rate is more credible than one that pretends to none.

**RESTORED — the voice context-of-use data EXISTS. P8 wrongly declared it absent.**
PwC *Prepare for the voice revolution*, 2018-04-30, n=1,000 US adults 18-64:
**65% cooking · 62% multitasking · 57% watching TV · 29% working · 0% driving (smart speaker) vs 40%
driving (smartphone) · 74% use voice in the home.** (PwC's PDF is retired; values via Voicebot.ai and
TechCrunch 2018 — cite as 2018 and flag as dated.) The separately-circulating 24/26/38% context figures
stay killed. Also newly usable and directly on point: adoption is driven by **households with children**,
yet **18-24s use voice daily LESS than 25-49s (59% vs 65%)**, with the stated reason that using voice
in public "just looks weird." This is a second, independent line of support for the public-use social
barrier alongside Kowalczuk & Musial (n=860, German).

**RESTORED/RECLASSIFIED.** "57% use voice commands daily" is a BASE SWAP, not a fabrication — true
value: **57% of voice-COMMAND users** (NPR/Edison Smart Audio Report 2022, fielded Feb-Apr 2022).
eMarketer's "153.5M US voice users 2025" is very likely a real paywalled forecast point (the 2024
vintage gives 145.1M in 2023 → 170.3M in 2028, so ~154.9M in 2025) — reclassify from "fabricated" to
"unverifiable at origin, paywalled, FORECAST presented as measurement." Still not citable.

**CORRECTED REPLACEMENT VALUES to use.**
- Non-summer school closures: **~20-30 days** (from Pew/ECS 2023's 179-180 mandated days). The
  circulating "50" is roughly 2x too high.
- Youth sports: **the average age at which a child quits sports is 12** (Aspen/Project Play) — usable
  in place of the killed statistic, and it sharpens the Gen X/teen argument.
- EdTech sprawl anchor: LearnPlatform/Instructure *EdTech Top 40* — **2,739 distinct tools per district
  per year (2024) → 2,982 (2025)**. This measures DISTRICT/student/teacher access, NOT parent installs;
  do not launder it into a parent-facing app count.
- Subscription blindness: West Monroe (n=2,500 US, June 2021) — $273/mo across 21 categories, **100% of
  respondents underestimated their own spend, 66% by more than $200.**
- Klook's "91% use AI" is global (n=11,000, 15 of 20 markets APAC), is Klook's OWN customer base, and
  "used for tasks" was corrupted to "rely on." Do not use for US parents.
- TeamSnap's "30M" is **"parents, players, coaches and administrators"** — mixed-role, unaudited, never
  households.

**NO COZI PRECEDENT FOR EMAIL FORWARDING.** `add@cozi.com` does not exist and never did — verified
against Cozi's full current FAQ plus a Wayback CDX sweep of every archived cozi.com "email" URL,
2007-2025. The claim traces to usecarly.com (an SEO site for a competing AI assistant). The
email-forwarding architecture has NO large-incumbent precedent; its only precedents are Sense and
Schoolcase, both small. State that honestly in the S1 memo's competitive section.

**NO ONBOARDING-COMPLETION BENCHMARK EXISTS AT ANY TIER (re-confirmed).** The onboarding-simplification
recommendation must rest on Nielsen's verified 10-second limit and the field-count comparison — never
on a completion slope. This closes the question V4 raised.

### Phase-3 corrections, round 4 (V6 second pass) — authoritative; supersedes round 3 where they conflict

**Kill-list error rate revised UP: 6 of 22 re-traced kills overturned (27%).** The report's method
section must state this plainly and the appendix must carry per-item confidence. Two independent
verifiers converged on ~22-27%, so treat any single kill as ~3-in-4 reliable, not certain.

**RESTORED — youth-sports debt. Use this, it is the best-sourced statistic in its domain.**
**18% of youth-sports parents took on debt** — Harris Poll for Good Sports, **n=741 parents**, fielded
Oct 16-18 2024, weighted, **±4.2pp, exact question wording published** (the 18% base is the 688 whose
children ever played). P4 killed it wrongly, reasoning that a 4x gap with LendingTree's 79% meant
neither was usable. It is a denominator-and-vintage difference, not a contradiction. **LendingTree's
79% is the unusable one** — its base excludes non-competitive families (only 70% have a child in a
competitive activity, so 79% cannot sit on a 100% base) and **LendingTree's own 2023 re-run measures
42%**. Their own page title drops the word "Competitive," so the publisher begins the laundering.

**RESTORED — the Ewing & Seefeldt Michigan State study (n=26,000 youth)** was discarded along with a
bad number derived from it. Free full text at ERIC ED360267. The study is usable; the derived stat is not.

**BEST-DOCUMENTED LAUNDERING EVENT IN THE APPENDIX — "70% quit sports by 13."** The Washington Post
(2016-06-01) hyperlinked "According to a poll from the National Alliance for Youth Sports" to **nays.org's
bare homepage**. NAYS has never published such a poll. **The real measured value is 35%, ages 11-18.**
Use this as the appendix's worked example of how a statistic is born.

**SUPERSEDES ROUND 3 — non-summer school closures are 30-38 days, median ~34**, measured from actual
district calendars (NYC 34, LAUSD 35, Chicago 33, Fairfax 38; CAP's 29 for large districts). Round 3's
"~20-30" derived from mandated-days arithmetic; the measured figure wins. The circulating "50" stays killed.

**ATTRIBUTION FIXES.** "153.5M US voice assistant users" is **Astute Analytica's**, not eMarketer's, and
their framing is "engaged DAILY" (same press release as their $59.9B forecast — one citation kills both).
**AA3PM is NOT fielded by Edge Research** — P3 and P4 both make that attribution; drop it.
**ACA's "26 million campers" is ACA's own unsourced boilerplate** — its 2024 economic study supplies no
camper count. **Use Gallup/NSLA's 30M (55% of K-12) instead.**
**Edison may be laundering its own statistic**: their marketing page says "57% of *Americans* use voice
commands daily," which is internally impossible against their own 62% ever-use figure.

**THE APPENDIX'S CLEANEST TEACHING EXAMPLE.** The "8.4% onboarding completion" benchmark is Airship's
**Day-30 app RETENTION** relabelled as onboarding completion, measured over ~2.6 BILLION **devices**,
fielded Jan-Jun 2023, against Airship's own 7-8% figure. All four laundering moves — measurement
substitution, devices-as-people, date-stripping, and metric relabelling — in a single number.

**NEWLY KILLED.** Digital Promise's "74% of US districts use 26+ tools" (quoted in PowerSchool's own
10-K) is **n=40 self-selected CTOs** from a network branded "Innovative."

**SCALE CLAIMS TO RESTATE.** TeamSnap's "24M users" was TeamSnap's own homepage copy from Aug 2021-Feb
2022 — stale, not laundered. More important: their current **30M is a "lifetime platform milestone"
against 2M daily actives — a 15x gap.** Never present platform lifetime totals as active users; this
applies equally to every competitor scale figure in the corpus.

**VERIFIED AND USABLE.** Nah (2004) confirmed including the 38-second tolerance figure (n=70 students,
2003) — the wait-tolerance argument may cite it directly rather than second-hand. Meyer/Carlson/Alam
(2022, CPS-CSS, n=18,757) gives the national shared-custody trend 13%→34%, with Wisconsin (single-state
court records) running 9.4 points ahead. Census P60-285: 22.2M children, 13.9M custodial parents.
Child Trends (n=1,025, NORC AmeriSpeak, Dec 2025): **43% of parents trust school communications most.**
CDT does NOT contain a third-party-access number, which STRENGTHENS P12's negative finding on that gap.

**ONE KILL WORTH RE-RUNNING** with fresh search budget: the "24% cooking / 26% chores / 38% relaxing"
context triple. Killed on all reachable evidence, but it is the context-of-use data this study most
wants, so a false kill there would be costly. (Note the PwC 2018 context data restored in round 3 is a
DIFFERENT and independently sourced set — it stands regardless.)
