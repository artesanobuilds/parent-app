# P5 — High-frequency, low-ceremony obligations: appointments, healthcare, school admin, small events

Collector P5. Compiled 2026-08-21. US only unless stated. Follows BRIEF.md output contract and tier rules.

**Scope note:** this domain is the one the product has no capture surface for. The headline result is that
the *sourced, Tier-A-anchored* volume of discrete scheduled obligations for a 2-kid family is ~23/year —
roughly one every 2.4 weeks — versus 1–2 camp-planning episodes/year. The volume asymmetry is real, but it
is smaller than "dwarfs" implies on visit counts alone; the asymmetry that actually matters is **cadence and
capture context**, not raw count. See § Interpretation.

---

## NORMALIZED SCORECARD — task family: one-off appointments / healthcare / school admin / small events

| Dimension | Value | Confidence | Source anchor |
|---|---|---|---|
| **Episodes / year (per child)** | **~11.7 discrete scheduled obligations** (1.53 physician office visits + ~1.8 dental + 0.45 ED + ~0.40 urgent care/retail clinic + 6.0 parent-attended school activities + ~1.5 therapy/counseling sessions) | Medium — 2 of 6 inputs are computed estimates, flagged below | NAMCS 2018; NHIS 2023; NHAMCS 2019; NHIS 2022; NHES:PFI 2023; NSCH 2023 |
| **Episodes / year (2-kid family)** | **~23** sourced floor; ~30–40 with unsourced categories (birthdays, vision, ortho, sports physicals, haircuts, picture day) | Medium / Low respectively | see arithmetic below |
| **Episodes / year (family with an infant)** | **~6 office visits for that child alone** (596 office visits per 100 infants <1 yr) plus AAP-recommended 7 well visits in year one | High | NAMCS 2018; AAP Bright Futures periodicity |
| **% households affected** | ~Universal. 79.6% of children 0–17 had ≥1 preventive medical visit in past 12 mo; 90% of children 5–17 had a dental visit in past year; 83% of K–12 students had a parent attend a general school/PTO meeting | High | NSCH 2023–24; NHIS 2023 (childstats); NHES:PFI 2023 |
| **Hours** | **No data found.** No time-use source isolates appointment scheduling/coordination from ATUS "household management." Flagged as a real gap. | — | — |
| **Dollars** | Out of scope for this collector except birthdays ($314 avg party, Tier C). Missed-appointment cost to the US health system commonly cited at $150B — **untraceable, see WEAK SIGNAL** | Low | — |
| **Pain evidence** | Effort of capture causally suppresses offloading: raising the physical cost of setting a reminder cut reminder-setting by .29–.50 per trial (dz 0.71–1.29), and unaided accuracy fell sharply as load rose (Exp 1+2, n=52 each, peer-reviewed). Screenshot-as-capture actively *worsens* memory across 7 experiments (Memory & Cognition 2026). Pediatric no-show rates run ~15–30% vs a 5–10% benchmark. | Medium-High | Psychon Bull Rev / PMC11103908; Memory & Cognition 2026; no-show literature (range, not a single US estimate) |
| **Tool used today** | Digital calendar 65.7%, paper list 62.1%, paper calendar 53.5%, post-it note 50.0%, timers 48.5%, ask another person 40.7%, digital list 37.8% (n=280 US adults). **Paper beats digital for lists.** Digital assistants: *did not appear at all* in either the survey or the diary study. | Medium (2017, dated; US adults not parents specifically) | Brewer et al., IMWUT 2017 |
| **Variation by kid age** | Steep. Infant <1: 5.96 office visits/yr. Ages 1–17: 1.53/yr. Urgent-care use rises with age (0–5 lowest, 12–17 30.3%). Dental ≥1/yr is 90% at 5–17. School-activity load only begins at K. | High | NAMCS 2018; NHIS 2022; NHES:PFI 2023 |
| **Variation by cohort (Gen Z / Millennial / Gen X)** | **Almost no data found.** No US source breaks appointment or school-admin load by parent generation. The one adjacent generational signal: Gen Z moms spend $276 vs Millennial moms $329 on a child's birthday party (Tier C, n=404 women). Memory-aid use splits by *age of adult*, not parent cohort: adults 65+ used digital calendars MORE (77.1%) than under-65 (58.9%) — the reverse of the intuition. | Low | What to Expect 2024; Brewer et al. 2017 |

---

## COMPUTED ESTIMATE — discrete scheduled obligations per year, typical 2-kid US family

Assume two children both aged 3–17 (the modal case; an infant in the house multiplies line 1 by ~4).

| # | Category | Per child / yr | Source of the input | Input type |
|---|---|---|---|---|
| 1 | Office-based physician visits | **1.53** | NAMCS 2018: 153 visits per 100 children aged 1–17 | **Sourced, Tier A** |
| 2 | Dental visits | **1.8** | 90% of children 5–17 had ≥1 dental visit in past year (NHIS 2023); ADA/AAP recommend 2/yr. 1.8 = midpoint assuming most attenders make the recommended two. | **Computed estimate** — the *rate* is not published, only the ≥1 prevalence |
| 3 | Emergency department visits | **0.45** | NHAMCS: 48 ED visits per 100 children 0–17 in 2019 (31/100 in 2020, COVID-depressed); 2022 rates for ages 1–74 were 41–47/100 | **Sourced, Tier A** (2019 pre-COVID rate used) |
| 4 | Urgent care / retail clinic visits | **0.40** | NHIS 2022: 28.4% of children ≤17 visited an urgent care or drug-store/grocery clinic in past 12 mo. Converted to a rate assuming ~1.4 visits per attending child. | **Computed estimate** — the 28.4% is sourced; the 1.4 multiplier is my assumption |
| 5 | School activities a parent attended | **6.0** | NHES Parent & Family Involvement 2023 (n=19,562 K–12 students): parents reported participating in a mean of **6 school-related activities** in 2022–23 | **Sourced, Tier A — the single best number in this report** |
| 6 | Mental-health / therapy sessions | **1.5** | NSCH 2023 (n=55,162): 12.2% of children 3–17 received treatment or counseling from a mental-health professional in past 12 mo. Population-average sessions estimated at 12.2% × ~12 sessions. | **Computed estimate** — extremely concentrated; ~0 for 88% of kids, ~12+ for the 12% |
| | **Per-child subtotal** | **11.68** | | |

**× 2 children = 23.4 discrete scheduled obligations per year.**

Sourced-only floor (lines 1, 3, 5 — no estimates): (1.53 + 0.45 + 6.0) × 2 = **15.96/year**.
Full estimate including all six lines: **~23/year ≈ one obligation every 2.4 weeks.**

**Not included because no citable source exists** (see WEAK SIGNAL): birthday parties attended and hosted,
vision exams, orthodontia adjustment visits (typically every 4–8 weeks for 18–24 months — a genuinely large
hidden block), sports physicals, immunization catch-up appointments, haircuts, picture day, spirit week,
permission-slip and form deadlines, library returns, subscription renewals. A plausible but **unsourced**
band for these is 10–20 additional per 2-kid family per year, which would put the true total at 33–43.

**Comparison to camp planning:** a family plans camp roughly 1–2 times/year (summer, plus school-break care).
So appointments+school-admin generate **~12–20× more discrete planning events per year** than camp, at a much
lower ceremony per event. That ratio, not the absolute count, is the strategic finding.

**Infant correction:** replace line 1 with 5.96 for a child under 1 (NAMCS 2018) and add the AAP-recommended
7 well-baby visits in the first year → a family with a newborn plus one school-age child carries roughly
**28–30/year** even before the unsourced categories.

---

## Section 1: FINDINGS

| # | Claim | Value | Cohort/segment | Publisher | Year | Method (n, window, population) | Tier | URL |
|---|---|---|---|---|---|---|---|---|
| 1 | AAP Bright Futures recommends 31 age-based health-supervision visits from birth through age 21, front-loaded: 7 in the first year (newborn, 1, 2, 4, 6, 9, 12 mo), then 15/18/24/30 mo, then annual from age 3. | 31 visits birth–21; 7 in yr 1 | All US children | American Academy of Pediatrics / Bright Futures (HRSA-supported) | 2026 schedule (annually reviewed) | Clinical guideline, not a survey; consensus periodicity schedule reviewed annually by AAP + Bright Futures | A | https://www.aap.org/en/practice-management/care-delivery-approaches/periodicity-schedule/ |
| 2 | Children aged 1–17 make 153 office-based physician visits per 100 children per year; infants under 1 make 596 per 100. | 1.53 and 5.96 visits/child/yr | By child age | NCHS (CDC), Data Brief 408 | 2021 (2018 data) | National Ambulatory Medical Care Survey 2018; national probability sample of office-based physicians; 860.4M total visits estimated; rates use Census 7/1/2018 population. **Dated (2018) — flagged.** | A | https://www.cdc.gov/nchs/products/databriefs/db408.htm |
| 3 | 90% of children aged 5–17 had a dental visit in the past year; the rate falls to 80–81% for children below the poverty threshold. | 90% (≥1 visit) | Children 5–17; by income | Federal Interagency Forum on Child and Family Statistics (America's Children), from NHIS | 2025 report, 2023 data | NHIS 2023; parent-reported ("how long since last dental exam or cleaning"), includes all provider types | A | https://www.childstats.gov/americaschildren/care4.asp |
| 4 | 79.6% of children 0–17 had one or more preventive medical visits in the past 12 months; state range 71.9% (NV) to 92.0% (VT). | 79.6% | Children 0–17 | HRSA MCHB, National Survey of Children's Health (via America's Health Rankings) | 2023–2024 two-year estimate | NSCH, parent/caregiver-completed; 55,162 children in the 2023 cycle | A | https://www.americashealthrankings.org/explore/measures/wellchild_visit_0to17_overall |
| 5 | 28.4% of children ≤17 visited an urgent care center or drug-store/grocery clinic in the past 12 months, up from 21.6% the prior year; highest at ages 12–17 (30.3%). | 28.4% (2022) | Children ≤17, by age band | NCHS/CDC QuickStats (MMWR) | 2024 (2021–2022 data) | National Health Interview Survey 2021 and 2022; civilian noninstitutionalized population | A | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10824549/ |
| 6 | Children 0–17 made 48 emergency-department visits per 100 children in 2019 (31 per 100 in 2020); 2022 ED rates for ages 1–74 ranged 41–47 per 100, with infants <1 at 99 per 100. | 0.41–0.48 ED visits/child/yr | Children 0–17; infants separately | NCHS (CDC), Data Briefs 469 and 503 | 2023 / 2024 (2019–2022 data) | National Hospital Ambulatory Medical Care Survey; national probability sample of ED visits | A | https://www.cdc.gov/nchs/products/databriefs/db469.htm |
| 7 | 12.2% of children aged 3–17 received treatment or counseling from a mental-health professional in the past 12 months. | 12.2% | Children 3–17 | HRSA MCHB, National Survey of Children's Health | 2023 | NSCH 2023; parent/caregiver questionnaires for 55,162 children 0–17 (18,397 adolescents 12–17); 6,479 affirmative responses | A | https://www.nschdata.org/browse/survey/results?q=11524&r=1 |
| 8 | Among adolescents with a current diagnosis who needed mental-health treatment, 61.0% had difficulty getting it in 2023 — a 35% increase since 2018. | 61.0% | Adolescents 12–17 with diagnosis | HRSA MCHB (NSCH data brief) | 2023 | NSCH 2023; n=18,397 adolescents within 55,162 total | A | https://mchb.hrsa.gov/sites/default/files/mchb/data-research/nsch-data-brief-adolescent-mental-behavioral-health-2023.pdf |
| 9 | **Parents of K–12 students participated in a mean of 6 school-related activities in the 2022–23 school year.** | 6.0 activities/student/yr | K–12 parents | NCES / IES, NHES:PFI 2023 First Look (NCES 2024-113) | 2024 (2022–23 school year) | National Household Education Surveys Program, Parent & Family Involvement questionnaire completed for **19,562 K–12 students**; nationally representative address-based sample, 50 states + DC, web-first with mail follow-up | A | https://nces.ed.gov/pubs2024/2024113.pdf |
| 10 | Breakdown of those activities: attended a general school/PTO meeting 83%; attended a school or class event 74%; attended a regularly scheduled parent-teacher conference 72%; participated in school fundraising 52%; volunteered or served on a school committee 36%; met with a guidance counselor 28%. | see values | K–12 parents | NCES / IES, NHES:PFI 2023 | 2024 (2022–23 school year) | as above, n=19,562 | A | https://nces.ed.gov/pubs2024/2024113.pdf |
| 11 | School→home communication reached 90% of K–12 students via school-wide newsletters/memos/e-mails/notices; 66% received e-mails or notes specifically about their own child; 41% received phone calls about their child. | 90% / 66% / 41% | K–12 parents | NCES / IES, NHES:PFI 2023 | 2024 (2022–23 school year) | as above, n=19,562 | A | https://nces.ed.gov/pubs2024/2024113.pdf |
| 12 | **Increasing the physical effort of setting a reminder significantly reduced how often people offloaded intentions**, with the largest drops at high memory load (mean reductions of .50 and .46 reminders at loads 4 and 6 vs .29 at load 2; dz 0.71–1.29). Unaided accuracy fell from .96 at load 2 to significantly lower at load 6. | see values | Adults (not parent-specific) | Peer-reviewed (intention-offloading literature; PMC11103908) | 2024 | Two web-based experiments, n=52 (mean age 25) and n=52 (mean age 29); within-subject manipulation of reminder-setting effort (5 extra clicks; 15 clicks) crossed with memory load | A | https://pmc.ncbi.nlm.nih.gov/articles/PMC11103908/ |
| 13 | Memory aids US adults report typically using: digital calendar 65.7%, paper list 62.1%, paper calendar 53.5%, post-it note 50.0%, timers 48.5%, ask a person 40.7%, digital list 37.8%, specialized objects 24.2%. **Digital assistants did not surface at all.** | see values | US adults 19–82 | Brewer, Morris et al., ACM IMWUT (PACM IMWUT Vol 1 No 3) | 2017 | Online survey of **280 US adults** recruited via panel, plus a one-week diary study with 20 participants (246 of 280 questionnaires returned, 87.8%). **Dated (2017) — flagged; US, all adults not parents.** | A (peer-reviewed) | https://cs.stanford.edu/~merrie/papers/memory_imwut2017.pdf |
| 14 | Paper beats digital for list capture: more survey respondents used paper lists (62.1%) than digital lists (37.8%), and in the diary week 16 participants used a paper list vs only 5 who used a digital list. | 62.1% vs 37.8% | US adults | Brewer et al., IMWUT | 2017 | as above (survey n=280; diary n=20) | A | https://cs.stanford.edu/~merrie/papers/memory_imwut2017.pdf |
| 15 | Adults 65+ in this sample used digital calendars (77.1%) and digital lists (46.6%) MORE than under-65 adults (58.9% / 31.9%) — the opposite of the usual assumption. | 77.1% vs 58.9% | Older vs younger US adults | Brewer et al., IMWUT | 2017 | as above; older n=131, younger n=149. Sample is not population-representative on age. | A | https://cs.stanford.edu/~merrie/papers/memory_imwut2017.pdf |
| 16 | Taking a screenshot to "save" information **impairs** later memory for that information — the "digital capture effect" — with no experiment showing a clear offsetting benefit. | directional; 7 experiments | Adults (lab) | Fabrizio, Lurie & Westerman, *Memory & Cognition* (Binghamton University) | 2026 | Seven experiments; **participant n not disclosed in the available press summary** — method partially unverified, treat the direction as the finding, not an effect size | A (journal) with method caveat | https://www.miragenews.com/screenshots-boost-forgetfulness-study-finds-1728248/ |
| 17 | Average spend on a child's birthday party is $314; $344 for ages 6–10; 20% of parents spend over $500 and 14% under $100. Millennial moms $329 vs Gen Z moms $276. | $314 avg | US mothers; Millennial vs Gen Z split | What to Expect (vendor-interested parenting site) | 2024 | Survey of **404 women**; fielding window not disclosed; self-selected site audience | C (vendor-interested; flag) | https://www.thebump.com/news/childs-birthday-party-cost |

### Interpretation

**1. The school channel, not the medical channel, is the volume leader — and it is the one the product already
half-touches.** The single strongest number in this report is NCES's mean of **6 school-related activities per
K–12 student per school year** (n=19,562, Tier A). For a 2-kid family that is 12 parent-attended school
obligations a year, against ~4 physician visits and ~3.6 dental visits. School admin is roughly half of all
discrete obligations in the model. The product's `school_event` vertical is **behind a feature flag that
defaults off** — that is the clearest misallocation this collector found.

**2. Healthcare volume is real but was overestimated in the brief's framing.** NAMCS puts children 1–17 at
1.53 office visits/year — not the 4–6 that clinical guidelines imply, because the AAP schedule is a
recommendation and actual utilization sits well below it (79.6% of children get even *one* preventive visit).
The exception is infancy: 5.96 office visits per infant per year is a 4× step change. **Healthcare appointment
load is a newborn/toddler-parent problem far more than a school-age problem**, which cuts against a
one-size-fits-all capture surface and argues for age-conditioned defaults.

**3. Explicit contradiction — guideline vs. utilization.** AAP/Bright Futures recommends 31 visits birth–21
(~1.5/yr averaged, but 7 in year one and 4 more by 30 months). NAMCS actual is 1.53/yr for ages 1–17 and NSCH
says 20.4% of children get *zero* preventive visits a year. A product that schedules to the guideline would
over-serve; a product that schedules to observed behavior under-serves the families with the most to gain.
Do not present the guideline number as demand.

**4. Contradiction — dental.** 90% of children 5–17 had ≥1 dental visit (NHIS 2023) while only 79.6% had a
preventive *medical* visit. Dental is the more reliably-attended appointment class and is on a fixed 6-month
recall cadence, which makes it the single most predictable recurring obligation in a family's year — and
therefore the cheapest thing for a product to own first.

**5. The capture moment: the strongest causal evidence in this report says friction, not intent, decides
whether a thing gets captured.** The intention-offloading experiments (n=52 ×2) show that adding as little as
five extra clicks to setting a reminder measurably reduced how often people set one — and that when they
didn't offload, accuracy collapsed as load rose. That is the mechanism behind "I'll remember it." Read against
the product audit, **58 text-entry fields, 12 knobs on Planner, and 16–20 taps to a saved plan** are not
neutral: they are an offloading tax, and this literature predicts parents will simply not capture. A capture
surface for this task family has to be one gesture, not a form.

**6. Corollary — what parents reach for today is paper and other people, not apps.** 62.1% use paper lists
against 37.8% digital lists; 50% use post-it notes; 40.7% "ask a person." Digital assistants did not appear
*once* in either the survey or the week-long diary. Two implications: (a) the incumbent to displace at the
capture moment is a sticky note and a partner's memory, not Cozi; (b) the app's voice bet — full-duplex
ElevenLabs calls in exactly two places, and **no dictation anywhere** — is aimed at the wrong end of the
funnel. The evidence supports a zero-friction *dictation/one-tap capture* affordance far more than it supports
conversational calls.

**7. Screenshotting is not a solution parents can be left with.** The 2026 *Memory & Cognition* result is that
capturing by screenshot degrades memory for the captured content across seven experiments, with no clear
offsetting benefit unless the capture is later reviewed. Parents photographing a flyer or screenshotting a
class text are creating a write-only archive. A product that ingests photos/flyers (the app already has
PhotosPicker) and *turns them into dated obligations* is directly addressing a documented failure mode — but
the app has **no in-app camera**, which means the capture still routes through the failing behavior.

**8. Failure is measurable and expensive on the clinic side, unmeasured on the family side.** Pediatric
no-show rates are consistently reported above adult rates and above the 5–10% primary-care benchmark, but the
literature is a scatter of single-clinic studies (see WEAK SIGNAL) — there is no US national pediatric no-show
rate. And there is **no time-use source that isolates appointment coordination**. Both are genuine gaps worth
a primary-research question rather than a citation.

**9. Cohort read: essentially no data.** Nothing in the Tier A/B literature breaks appointment or school-admin
load by parent generation. The one available generational signal is birthday spending (Tier C, n=404), and the
one adult-age signal — 65+ adults using digital calendars *more* than under-65 — actively warns against
assuming younger parents are the digital-capture cohort. For the Gen Z parent cohort specifically, the answer
here is the expected one: no data found.

---

## Section 2: WEAK SIGNAL (not citable — do not promote into findings)

- **"Pediatric no-show rate averages 30%."** Circulates widely (vendor blogs, dialoghealth). Traced to no
  national study. The credible underlying literature is single-site: an urban US pediatric primary-care clinic
  study (Pediatr Emerg Care / PubMed 25676833, 2015) and various QI projects reporting 15–20%; the "3% to 48%"
  range and the 5–10% international benchmark are frequently repeated without a common source. **There is no
  published US national pediatric no-show rate.** Treat 15–30% as a range, never a point estimate.
- **"$150 billion annual cost of missed medical appointments in the US."** Repeated on vendor sites; every
  trail I followed ended at another blog. Classic stat laundering — unverifiable, do not use.
- **Pediatric dental no-show, 52%, with 50% citing parental forgetfulness and "52.0% relied on their memory
  to remember their appointments."** Source is a real peer-reviewed study but it is **India (Navi Mumbai),
  n=294 parents, Jan–Jul 2015** — not US, dated, single clinic. Directionally supportive of the
  memory-reliance thesis; must never be presented as a US number.
- **How many birthday parties a child attends per year.** Searched specifically; **no Tier A/B/C source
  exists.** Everything found ("average child attends 8–12 parties/year") lives only on party-vendor blogs and
  AI-generated stat listicles (partygeniusai, jobera) with no origin. Killed. This is a real, unmeasured
  category — the RSVP/gift/dropoff burden is plausibly large and is entirely undocumented.
- **Party guest counts** ("average 15–20 kids", "most parties ~9 guests") — the two figures contradict each
  other and neither traces to a disclosed method. Unusable.
- **Permission slips / forms per year, picture day, spirit week, early-release and teacher-PD day counts.**
  No source found at any tier. NCES measures *parent participation* but not *form volume*. Genuine gap.
- **ParentSquare / Brightwheel / Peachjar adoption and message volume.** ParentSquare's 2025 year-wrap page
  returned 404; no vendor figure with disclosed method was obtainable. Their claims ("millions of secure
  documents") are marketing copy without method. Not citable. NB: the Yahoo/Censuswide "80+ school emails per
  month, 62% missed something" figures are already known per BRIEF and are not re-derived here.
- **Sports physicals, immunization-deadline appointments, vision exams, orthodontia visit cadence, haircuts,
  library due dates, subscription renewals.** No citable US data found for frequency. Orthodontia in
  particular (routine adjustments every 4–8 weeks across 18–24 months for a treated child) is likely one of
  the largest single hidden recurring appointment blocks in a family's calendar and is completely undocumented
  in the sources available here. Flagged as the highest-value unmeasured category.
- **Hours spent scheduling/coordinating appointments.** No ATUS or equivalent breakout exists. The BLS
  household-management category is too coarse. Gap.
- **Double-booking rates among parents.** No survey found. The only adjacent evidence is qualitative (parents
  double-booking soccer games with school events, in vendor/practitioner writing). Gap.
- **HEDIS W30 / WCV national rates.** NCQA gates the State of Health Care Quality Report behind a form; I
  could not retrieve MY2024 national rates. Would be a strong Tier A/B addition if obtained.
- **MEPS per-child visit counts.** MEPS Statistical Brief #419 (well-child visit trends, 2002–2009) exists but
  is badly dated and I could not extract a current mean-visits-per-child figure. NAMCS was used instead.
- **Recruitment caveat on the IMWUT memory-aid study:** the diary sample was drawn partly from Microsoft
  employees and a Seattle older-adult research pool. The n=280 survey is panel-recruited US adults and is the
  more generalizable half; treat the diary color as illustrative only.

## Method notes / limitations

- CDC.gov blocks automated fetching (HTTP 403); NAMCS/NHAMCS figures were read from the restoredcdc.org
  mirror of the NCHS Data Brief text and cross-checked against search-result summaries. Numbers and URLs point
  at the canonical NCHS briefs.
- The web-search budget for this session was exhausted before I could close the pediatric no-show, sports
  physical, and school-forms gaps. Those remain open and are listed above.
- Two of the six inputs to the annual-obligations model (dental rate, urgent-care rate) and one (therapy
  sessions) are my computed estimates from published prevalence, not published rates. The sourced-only floor
  of 15.96 obligations/year for a 2-kid family carries no such assumptions.
