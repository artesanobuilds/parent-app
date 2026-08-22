# Deep-Research Prompt — gaps the local agent fleet could not close

**How to use:** paste everything below the line into Claude Desktop (or any deep-research
tool with broader crawling). It is self-contained. Results come back in a format designed
to merge straight into `docs/GTM/research/2026-08-parent-planning-behavior/`.

**Why these specific asks:** a 20-agent local research program ran 2026-08-21 on US parent
planning behavior. The items below are the ones it could NOT close, for three distinct
reasons — and the distinction matters, because only the first is fixable by better crawling:

- **(A) ACCESS-BLOCKED** — the source exists and is authoritative, but bls.gov, cdc.gov,
  dol.gov, nces.ed.gov, ecs.org, americancamp.org and Trustpilot returned 403 / 404 /
  Cloudflare / CAPTCHA to an automated fetcher. **Highest value: just go get these.**
- **(B) PAYWALLED** — real data behind Statista / AppsFlyer / Adjust / Sensor Tower seats.
- **(C) MAY NOT EXIST** — the local fleet searched hard and found nothing at any tier.
  For these, the most valuable answer is a *confirmed negative*: "no such study exists."
  Do not fabricate a number to fill the hole. Saying "this has never been measured" is a
  finding we will act on by commissioning it.

---

# RESEARCH BRIEF

You are closing evidence gaps for a US market-research report on how parents plan their
children's lives. Today is 2026-08-21. **United States only** — if a source is global or
non-US, say so explicitly and do not present it as US.

## Cohorts (use these exact bands)

| Cohort | Birth years | Age in 2026 |
|---|---|---|
| Gen Z parents | 1997–2012 | ~18–29 |
| Millennial parents | 1981–1996 | ~30–45 |
| Gen X parents | 1965–1980 | ~46–61 |

## Source-tier rules — enforced, non-negotiable

- **Tier A** — government or peer-reviewed: Census (ACS/CPS), BLS (ATUS), NCES, NSCH, NHIS,
  MEPS, CDC/NCHS, peer-reviewed journals.
- **Tier B** — research orgs publishing methodology: Pew, Harris, Gallup, Edison Research,
  Aspen Project Play, RevenueCat, AP-NORC, Common Sense Media.
- **Tier C** — industry/vendor reports that disclose method. Flag vendor-interested sources.
- **Tier D** — SEO stat-aggregator blogs, "N statistics for 2026" listicles.
  **Tier D is NEVER citable.** Use it only as a lead to trace to an origin publisher, then
  fetch that origin directly. If no origin exists, report the number as UNVERIFIABLE and
  name the aggregators repeating it.

**No number without publisher, year, and method (n, fielding window, population).**
This topic space is heavily polluted by stat laundering. The local fleet already killed
~25 widely-circulated figures, including: "71% prefer voice over typing" (PwC 2018 with its
qualifier stripped; Pew's real figure is 22%), "15% onboarding drop per screen beyond five"
(attributed to Appcues; not on their site, no n, no date), "30%+ of parents secure summer
childcare before the prior year ends per BLS" (BLS publishes no such number), "Gen Z spends
$377/mo on subscriptions" (UK data, £305, relabeled as USD), and "8.4B voice assistants by
2026" (a Juniper *device* forecast, global). Expect more of the same. **Identifying a
laundered statistic is as valuable as finding a real one.**

## Output format

For every item, return:

| # | Gap ID | Claim / finding | Value | Publisher | Year | Method (n, fielding window, population) | Tier | URL |

Then, per gap, one short paragraph on what it means and any contradictions between sources.
End with a section listing every gap you could NOT close, marked either
**CONFIRMED NEGATIVE** (searched thoroughly, no such data exists at any tier) or
**STILL BLOCKED** (exists but you could not reach it) — this distinction is important to us.

---

# THE GAPS, IN PRIORITY ORDER

## PRIORITY 1 — access-blocked authoritative sources (type A)

**G1. BLS American Time Use Survey 2025 — household management detail.**
Fetch the actual ATUS 2025 tables from bls.gov (Tables 8A/8B/8C and the "household
management" activity code). We need minutes per day for parents of children under 18, by
SEX × EMPLOYMENT STATUS × AGE OF YOUNGEST CHILD. Also pull the 2015 and 2019 equivalents for
a trend line. Our current figures (mothers 12.0 vs fathers 6.0 min/day overall; 16.2 vs 5.4
when youngest is 6–17; parity when youngest is under 6) came from secondary routes and need
verification at source. NOTE: BLS suspended ATUS collection Oct 1 – Nov 12 2025 (government
shutdown) and reweighted Q4 — find and quote BLS's own statement on the effect.

**G2. Census family structure detail tables, 2024 and 2025.**
The cps-2024 and cps-2025 detail-table pages 404'd. Find whether Census published FG10 /
F1 / FM-1 / CH-1 detail tables for 2024 or 2025, or confirm 2023 is genuinely the newest.
We need families with own children under 18 by householder age (to size the Gen Z /
Millennial / Gen X parent split, currently 2.0M / 18.2M / 11.7M, derived from 2023 Table F1).
Also flag the universe problem: FM-1 says 33.56M families, FINC-03 36.82M, F1 36.44M —
document precisely what each universe counts.

**G3. NCES school-calendar structure.**
nces.ed.gov and ecs.org were unreachable. We need: average number of days US public schools
are closed per year BEYOND summer; distribution of teacher professional-development days,
early-release days, and conference days across the calendar; typical back-to-school start
dates by region. This is the single biggest hole in our seasonality analysis.

**G4. American Camp Association primary data.**
americancamp.org is Cloudflare-blocked. The widely-repeated "26M campers / 14,000 camps"
figures are untraceable to a fielding year. Find ACA's actual published research with a
year and method, or confirm it is not publicly documented.

**G5. CDC/NCHS pediatric utilization.**
cdc.gov 403'd; we sourced via the NIH/NCBI mirror. Verify at source: NAMCS physician office
visits per child per year by age; NHAMCS emergency department visits; NHIS dental visit
rates for children 5–17; and well-child visit adherence to the AAP/Bright Futures
periodicity schedule.

## PRIORITY 2 — the qualitative corpus we could not crawl (type A)

**G6. Reddit and Trustpilot.**
Both blocked our crawler entirely, so our 4,073-review corpus is App Store only. Harvest
verbatim parent language from r/Parenting, r/Mommit, r/daddit, r/workingmoms, r/coparenting,
r/breakingmom, r/SingleParents on these themes, with URLs and dates. **Quote exactly; never
paraphrase as if verbatim.** This is qualitative and non-representative — do not compute
percentages from it.
  - "we tried [family calendar app] and it didn't stick" — and specifically WHY
  - the homemade system: spreadsheets, paper planners, Apple Notes, the fridge, group texts
  - the capture moment: "I texted myself", "screenshot it", "the flyer in the backpack"
  - handing planning to a partner, and what happens
  - the January camp-registration scramble
  - "I wish there was an app that…"
  - parents using ChatGPT for family logistics — and parents refusing to
  - talking to Siri/Alexa/ChatGPT voice for family logistics, and why they don't
  Also: Trustpilot ratings and review themes for Cozi, Skylight, OurFamilyWizard,
  TalkingParents, ParentSquare.

## PRIORITY 3 — paywalled benchmarks (type B)

**G7. Mobile app retention and engagement benchmarks.**
Behind Statista / AppsFlyer / Adjust / Sensor Tower seats. We need US D1 / D7 / D30 retention
benchmarks for the Lifestyle, Parenting, and Productivity categories; average number of apps
a person actively uses per month; and median mobile session length. If only a summary or
press release is public, take that and label it as such.

**G8. School-communication platform reach.**
District counts and student reach for ParentSquare, ClassDojo, Remind, Seesaw, Brightwheel,
PowerSchool, Infinite Campus. Verify the ParentSquare–Remind acquisition (reported 2023) and
whether districts are consolidating onto single platforms — i.e. whether communication
fragmentation is shrinking on its own over time.

## PRIORITY 4 — probable confirmed negatives (type C)

For each of these the local fleet searched hard and found nothing. **A confirmed negative is
a useful result — say so plainly rather than filling the gap.**

**G9.** What share of US households sustain a shared digital family calendar over time, and
why family-organizer apps fail to stick. *(Flagged by our fleet as the single most
decision-relevant unknown in the whole study.)*

**G10.** Hours US parents spend researching and booking summer care. No US survey found.

**G11.** Hours spent on activity/camp ENROLLMENT episodes. No published measurement found.

**G12.** Weekend-outing frequency and decision time for US families. No publisher measures it.

**G13.** A probability-sampled count of how many apps/portals a family juggles per child.
Only a vendor study exists (n=125, non-probability, Cornerstone/Edsby "App Overload":
44% manage 7–9 apps per child). Find a real one or confirm none exists.

**G14.** Parent trust in AI advice about their children RANKED against a pediatrician, a
teacher, a friend, and a parenting influencer. No 2025–26 study makes this comparison. The
only hard datum is a 2024 University of Kansas study (n=116, blinded) finding parents rated
AI health advice MORE trustworthy than expert-written content — unreplicated. Confirm.

**G15.** Willingness to pay for AI household/family assistance specifically. No data at any tier.

**G16.** Any US study separating three distinct voice behaviors: (a) dictation/speech-to-text,
(b) voice-assistant commands, (c) conversational LLM voice. All Tier A/B sources merge them.
Also: US survey data on DICTATION usage rate specifically, and any published LLM-voice
session-length data (OpenAI, Google, Anthropic). The only datapoint we have is Google's
"63% of Gemini users use voice" — a vendor blog post with no n, no window, no definition.

**G17.** A US equivalent of Distel et al. (CHBR 2024, n=860, German) on social discomfort
using voice assistants in public. Does US research on this exist?

**G18.** Pew's flagship 2026 parenting study (n=3,757) publishes ZERO parent-age crosstabs.
Check whether Pew released a dataset or supplementary tables allowing a parent-generation
breakdown. Same question for Gallup's dual-full-time-couples work.

**G19.** Any method-disclosed research on dark-mode preference or expectation by age cohort.
We found none at any tier.

**G20.** Same-sex-couple parents and the division of planning labor — Pew could not analyze
them quantitatively (samples too small) in either 2025 or 2026. Is there any quantitative US
source? This is a useful natural experiment for planning labor without gender defaults.

## PRIORITY 5 — the feasibility question (mixed)

**G21. Can a third-party email address be registered as a parent contact?**
For ParentSquare, Brightwheel, ClassDojo, Seesaw, PowerSchool, Infinite Campus, TeamSnap,
SportsEngine, Sawyer and Jumbula, determine from actual product documentation or help pages:
(a) can a parent add a SECONDARY or arbitrary email address, or does it require district/admin
action? (b) do their notification emails contain the CONTENT in the body, or only a
"sign in to read this" LINK? (c) which are SMS/push-only with no email at all? (d) do any
Terms of Service prohibit registering a third-party service's address as a parent contact?
Cite the specific help page for each. **(b) is the crux** — a link-only platform makes
email aggregation useless.

**G22. Google CASA / restricted-scope verification, 2026.**
What does clearing the Gmail `readonly` restricted scope actually require in 2026 — cost,
elapsed time, annual re-assessment, and whether a solo or very small developer can realistically
clear it. Cite Google's own current documentation. Also the Apple/iCloud and Microsoft/Outlook
equivalents.

## PRIORITY 6 — anything we would have missed

**G23.** Any US survey fielded in 2026 on parental logistics load, family scheduling, school
communication overload, or the mental load, that the above does not name. Recency matters —
our most valuable single finding is five weeks old (AP-NORC/Ipsos, fielded Jul 21–26 2026:
~8 in 10 youth-sports parents rank scheduling/logistics/time as a challenge, ABOVE every cost
item at ~7 in 10). Look for anything comparably recent.

---

## Final instruction

Return the findings table, the per-gap interpretation, and the closing list splitting
**CONFIRMED NEGATIVE** from **STILL BLOCKED**. Where you find a laundered statistic, name it
and name the aggregators repeating it — we maintain a kill list. Where sources contradict
each other, present both and say which has the better method rather than averaging them.
