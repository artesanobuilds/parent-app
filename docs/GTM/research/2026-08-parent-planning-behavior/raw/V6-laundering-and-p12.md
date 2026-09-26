# V6 — Stat-Laundering Sweep + P12 Verification

Verifier V6. Run 2026-08-21. Scope: the entire `raw/` directory (P1–P12, P5b, M1–M4, S0, S1).

Two jobs: (1) hunt every number that reached a FINDINGS section on weak provenance, and re-test the
fleet's existing kills for FALSE KILLS; (2) verify `raw/P12-aggregation-email.md`, which drives a
live architectural decision.

**Method note.** All external verification was done against origin publishers and vendors' own
current documentation. Where a page was login-gated, Cloudflare-blocked or JS-only, that is stated
explicitly rather than papered over — an unreachable source is a finding, not a verdict.

**Headline.** The fleet's provenance discipline is genuinely good: P1, P2, P5b, P8, P9 and P10 are
close to airtight, and S1 independently caught a textbook devices-as-people laundering case (Litmus
"opens" are rendering clients, not mailboxes — 62.3% Apple opens vs 3.6% of mailboxes). But **three
of the fleet's kills are FALSE**, one widely-trusted kill turned out to be *more* fabricated than
anyone realised, and **five numbers sit in FINDINGS tables that their own authors labelled
uncitable**.

---

## JOB 1A — FALSE KILLS (overturned — these removed true facts)

A false kill is as damaging as a false claim. Three of the twelve spot-checked kills were wrong.

### FK-1. "8.4 billion voice assistants by 2024/2026" — **FALSE KILL, but requalify hard**
P8 killed this as having "no traceable primary origin." **The origin exists.** Juniper Research,
press release 2020-04-28, from *Voice Assistant Market: Player Strategies, Monetisation & Market
Size 2020–2024*: consumers will interact with voice assistants on over **8.4 billion devices by
2024**, against 4.2bn expected at end-2020.
- URL: https://www.juniperresearch.com/press/number-of-voice-assistant-devices-in-use/ (Business Wire copy: https://www.businesswire.com/news/home/20200427005609/en/)
- **P8's substantive analysis was right and its verdict was wrong.** P8's own kill-table entry already
  says "a Juniper Research 2020 FORECAST of DEVICES worldwide" — it correctly diagnosed the
  laundering and then mislabelled the row as originless. It has an origin with a stated basis.
- **The true statement:** a 2020 Juniper Research *forecast* of **8.4 billion voice-assistant
  DEVICES worldwide by 2024** — devices not people, forecast not measurement, global not US, and the
  target year is 2024, not 2026. Every aggregator version changes at least two of those four.
- Do not confuse it with Juniper's Feb-2019 "8 billion by 2023" release; the two are routinely blended.

### FK-2. ACA "more than 14,000 day and resident camps" — **FALSE KILL, but nine years stale**
P3 killed this alongside the "26 million" figure. It is real and was published by ACA:
> "More than 14,000 day and resident camps exist in the U.S. 8,400 are resident (overnight) and 5,600
> are day camps. **(2017 ACA Sites, Facilities, Programs Report)**"
- Archived: https://web.archive.org/web/20201119133200/https://www.acacamps.org/press-room/aca-facts-trends
- **Requalification:** 2017 data basis, and ACA has since **deleted the hosting page**. Citable only
  as "ACA, 2017 Sites/Facilities/Programs Report" with the date attached — never on a 2026 page
  without it. Note ACA's own current working universe is **>20,000 camp operations**, so 14,000
  understates ACA's present position as well as being old.

### FK-3. "Gen Z spends $377/month on subscriptions" — **FALSE KILL on the trace, KILL STANDS on quality**
P10 killed this by tracing it to Visa/Basis UK (£305, n=4,152, Nov–Dec 2024) and calling the US
version a currency-and-country relabel. **That trace is wrong.** The $377 figure has its own,
separate US origin:
- **Wethrift.com**, Oct 2021, n=1,030 US adults recruited via **Amazon MTurk**. Gen Z $377/mo;
  all-generation average $278/mo. Archived: https://web.archive.org/web/20230325101851/https://www.wethrift.com/articles/subscription-service-statistics/
- **The kill still stands, on different grounds.** Wethrift is a coupon-code affiliate site; MTurk is
  a non-probability convenience panel; the figure is five years old. It fails the brief's Tier C bar
  (industry/vendor reports *that disclose method* — this discloses a method that does not support the
  claim). **Correct the reasoning in the appendix, keep the number out.**
- P10's Visa/Basis finding is separately true and valuable — Visa did find Gen Z at **£305/mo in the
  UK**, and that number *is* laundered into US dollars elsewhere. Two different laundering events
  were collapsed into one; keep both, distinctly.
- Real US comparators with disclosed method: **West Monroe 2021** (n=2,500) $273/mo;
  **C+R Research 2022** (n=1,000) $219/mo actual vs $86/mo self-estimated, no generational dollar cut.

---

## JOB 1B — PARTIAL KILLS (an origin exists; the circulating number is corrupted)

These must not be cited as-is, but the appendix should state what is true, or a reader will assume
we simply could not find the source.

### PK-1. PwC "71% prefer voice over typing" — origin exists; three qualifiers stripped
P8 killed this citing a 403 on PwC's page. The report is real: PwC, *Consumer Intelligence Series:
Prepare for the voice revolution*, fielded **Feb 2018, n=1,000 US adults 18–64** with internet
access, online panel, plus two focus groups (Mar 2018). Archived PDF:
https://web.archive.org/web/2018id_/https://www.pwc.com/us/en/advisory-services/publications/consumer-intelligence-series/pwc-voice-assistants.pdf
- **The 71% is not in the report's body text.** It exists only as image-baked chart text on p.5, in a
  forced-choice "Would you rather?" graphic: *"Use your voice assistant to search for something —
  71%"* vs *"Physically type to search for something online — 29%."*
- **Three stripped qualifiers:** (a) it is a **hypothetical forced binary**, not observed behaviour;
  (b) it is scoped to **search only**; (c) the item says "*your* voice assistant," implying a base of
  voice-assistant **owners**, not all consumers — and the base is never published.
- **The same chart shows voice LOSING** on shopping (24–36%) and customer service (34%). Quoting the
  71% without those is cherry-picking within a single graphic.
- PwC has **retired both the page and the PDF** (404). An 8-year-old number, from a vendor-retired
  document, presented as current. **P8's verdict — do not use in any form — is correct.** Pew's actual
  measurement (22% cite naturalness-over-typing as a major reason) is the defensible replacement.

### PK-2. Custody X Change "fathers get 35% of custody time" — a MODEL, not a measurement
Origin exists: https://www.custodyxchange.com/topics/research/dads-custody-time-by-state.php (+ appendix).
M4 killed it for "no disclosed method." A method **is** disclosed, in the appendix — and it is worse
than no method, because it looks empirical and is not:
- Over four months in 2018 they emailed/called family-law attorneys, bar associations and courts about
  the *most common* visitation schedule in each state, then ran those schedules through **their own
  software** to compute percentages.
- Verbatim from the source: **"No customer data was used."** Assumes **a single child aged 6–11,
  amicable parents living within commuting distance, no violence, no substance abuse, no irregular
  schedules.** Where states lack standards they took "a more anecdotal approach."
- **The true statement:** a vendor's model of *typical state guideline schedules* under idealised
  assumptions — not an empirical distribution of real custody outcomes. **Kill stands, reasoning
  upgraded.** This matters: the SEO ecosystem repeats it as though it were a Census figure.

### PK-3. "30% pediatric no-show rate" — the ceiling sold as the average
P5/P5b killed this as having no national origin. Correct — **there is no US national pediatric
no-show rate.** But a large peer-reviewed literature exists and the honest range should be published
rather than a bare kill:
- Boston Children's (academic pediatric hospital) reports **20%** (NPJ Digit Med 2022). Across
  specialties the literature spans **1.5%–24%**, with **>30–50% only in urban safety-net, adolescent
  and high-social-risk subgroups**.
- **True statement: 10–25% typical, >30% in safety-net populations.** 30% is the subgroup ceiling
  being circulated as the mean. P5b's instinct — "treat 15–30% as a range, never a point estimate" —
  is right and should be the published line.

---

## JOB 1C — KILLS CONFIRMED (spot-checked, verdict upheld)

| Killed statistic | Verdict | What tracing found |
|---|---|---|
| **"15% completion drop per onboarding screen beyond five" (Appcues)** | **KILL CORRECT** | Appcues' full sitemap contains no such benchmark. The claim's entire internet footprint is ONE page: lowcode.agency/blog/mobile-onboarding-best-practices. Appcues actually publishes "60–70% completion is a solid target… below 50% you likely have too many steps" — directional, no per-step rate. A *hypothetical* worked example on their site containing both "5" and "15%" is the likely contamination source. |
| **"4–6% completion drop per form field beyond the eighth" (Baymard)** | **KILL CORRECT on the percentage** | No per-field percentage appears anywhere in Baymard. Their real 2024 findings (Edward Scott, 2024-06-26): average checkout is **5.1 steps / 11.3 form fields**; "most sites need only **8 form fields**"; 11.8 in 2021, 12.7 in 2019; 17% abandon on complexity. Baymard's method is site auditing + moderated usability testing, **not conversion A/B tests**, so it structurally cannot produce a slope. A parallel phantom — "4.1% per field per a 2024 HubSpot study" — circulates on brixongroup, formbeam, ivyforms with no source. |
| **"30%+ of parents secure summer childcare before the prior year ends, per BLS (2023)"** | **KILL CORRECT — fabricated attribution** | BLS publishes nothing on booking timing. ATUS measures minutes/day on childcare; OEWS/OOH cover childcare *workers*; CE covers *spending*. **No aggregator trail exists at all**, which is itself diagnostic of fabrication rather than laundering. Real cousins: CAP 2019 (32% started *looking* before March; n≈1,000 MTurk convenience) and Sawyer (7.2M bookings; families book camps 2–3 months ahead). Every element — agency, year, verb, threshold — is wrong. |
| **"$150B annual cost of missed medical appointments"** | **KILL CORRECT** | Dead-ends at *Health Management Technology*, 2017-04-26, bylined **Jamie Gier, CMO of SCI Solutions** — a scheduling-software vendor selling the fix. Asserted in the opening sentence with **no stated method**, supported only by an unsourced "$200 per open slot." No CMS/AHRQ/HHS/CBO equivalent exists. It has since back-propagated into peer-reviewed text by citation laundering (e.g. an Ann Fam Med 2024 abstract) — *the laundering has now contaminated the literature itself*. A competing published figure of **$50 billion** (J Patient Exp 2024) confirms neither rests on a real estimate. |
| **"92% of families will travel with their kids next year" (FTA/NYU)** | **KILL CORRECT — and this is the most dangerous item in the set** | Two independent defects. (a) **92% matches no year.** FTA's own series: 93% (2015, 2016), 88% (2017), 79% (2018), 70% (2019), 88% (2021), 81% (2023). (b) Even the real values are not population estimates — verbatim from the 2023 report: *"Respondents who were unlikely to travel with their children or grandchildren in the coming year were **filtered out at the end of the first question block**."* Same screen in 2018, 2019, 2021. Recruitment is non-probability from travel-affiliated lists (Travel+Leisure and Parents subscribers, MacaroniKid, Trafalgar/Shubert lists, a Club Med prize draw). FTA has pulled the PDFs from its live site. **This one survives a casual check** — real association, real university partner, real n=3,370 — which is exactly why it must be named in the appendix. |
| **"60% / 74% of parents feel guilty about screen time"** | **KILL CORRECT** | Neither traces anywhere. Diagnostic detail: **the major publishers do not measure guilt at all** — they measure concern, distraction and self-assessment. Closest real figure: Pew, Oct 2025, n=3,054 parents of children ≤12, ATP+SSRS, MOE ±2.2 — **42%** say they could do a better job managing their child's screen time; 65% say they spend too much time on their own phone. The two circulating numbers **bracket the real one on either side**, the signature of back-filling. |
| **Pew "37 million Millennial parents"** | **KILL CORRECT — and this is the surprise of the sweep** | A false kill here was the expected outcome; instead this is the most clearly fabricated item found. A full-text search of Pew's own REST API for "Millennial parents," "largest generation of parents" and "37 million Millennials" returns **nothing**. What Pew actually published: **17 million** Millennial women had become mothers as of 2016; **19 million** had given birth as of 2018 — **mothers only**, both times. **37M looks like someone doubled 19M to add fathers**, which is invalid arithmetic and not Pew's. Pew changed its generational-reporting policy in May 2023, so no newer figure will rescue it. **Attributing a fabricated number to Pew is the highest-reputational-risk error in the whole corpus.** |
| **ACA "26 million children and adults attend camp each summer"** | **KILL CORRECT** | ACA's published number was **14 million, never 26 million**: *"Each year more than 14 million children and adults attend camp in the U.S. (2013 ACA Camp Compensation and Benefits Report)."* The series ran 11M (2010 basis) → 14M (2013 basis) and stopped. ACA has deleted the page; its current site publishes only member reach (7.2M campers). The circulating 26M is roughly double the last real figure with no publisher behind it. |
| **"71% prefer voice over typing"** | See PK-1 — origin exists, kill upheld | |

---

## JOB 1D — NEWLY KILLED (numbers this sweep is removing for the first time)

### NK-1. ActivityHero "over 4 million families" / "400,000 email subscribers" — **KILL**
Sits in `M3-discovery.md` **Section 1, finding #9**, tagged "C (vendor, unverified)" — while M3's own
WEAK SIGNAL says "do not use it as a market-size input."
- The only sources are the company's own rate card (business.activityhero.com and
  /advertising-on-activityhero/, "up to 400k email subscribers"). The consumer press page carries
  media logos only — **no releases, no dates, no metrics**. `activityhero.com/advertise` 404s. No PR
  Newswire releases. **No third-party audit** (no IAB, BPA or Comscore).
- **No definition of the counting unit.** Nothing distinguishes cumulative registered accounts from
  active users, or households from individuals. This is the classic pair:
  **cumulative-registrations-sold-as-current-audience** plus **list-size-sold-as-subscribers**.
- **Verdict: KILL.** Quote only as "ActivityHero says," never as a market-size input. Move to WEAK SIGNAL.

### NK-2. Everything sourced to **usecarly.com** — **KILL the publisher, not just the number**
`P11-ai-parenting.md` **#41** ("ChatGPT scheduled tasks cannot be event-triggered; cannot run more
than hourly") cites usecarly as its sole source, in Section 1, and P11's own WEAK SIGNAL flags the
claim as "load-bearing" and unverified.
- usecarly.com is the marketing/SEO site for **Carly, a commercial AI assistant** — i.e. a direct
  competitor with an interest in the claim. ~200 posts, all listicles ("N Best AI Assistants for X
  (2026)"), programmatic "connect X to Y" pages, and competitor pricing explainers.
- **No survey, no n, no fielding window, no population, no questionnaire, no fielding partner, and no
  methodology page anywhere on the site.** The closest thing to a method is undocumented in-house
  testing of its own competitive set.
- Its "(2026)" title stamps are **not evidence the underlying numbers are current** — this is the
  date-stripping move in reverse: an old or invented number given a fresh year in the title.
- **Verdict: KILL, and treat usecarly as Tier D across the program.** If a claim traces there, the
  trail has gone cold, not ended. The ChatGPT scheduled-task limits are trivially checkable in-product
  and should be verified that way before any decision rests on them.

### NK-3. ACA-attributed "recommendations from friends and family is the #1 way parents find a camp" — **KILL (confirming M3)**
M3 flagged it; this sweep confirms. Circulates on Jumbula's blog, AdWave, TeenLife, RevenueBoomers and
a dozen camp-marketing SEO pages. **No n, no fielding window, no origin document.** ACA's own site
does not carry it. Given ACA's press room is demonstrably unmaintained (see below), attributing
anything to ACA without a named report and year is unsafe.

### NK-4. ACA's "Camp Trends / enrollment" page as a citable source — **KILL the page**
https://www.acacamps.org/press-room/camp-trends/enrollment currently reads: *"Each summer more than
26 million children and adults take advantage of the camp experience"* — **no year, no source, no n**.
The only dated item on the page is a **2016** Camper Enrollment Survey, and the page contains an
arithmetically broken statistic (female campers 56% + male 49% = 105%). **The page is unmaintained and
must not be cited.**
- **Cite this instead:** the **2024 National Economic Impact Study**, ACA with the **University of
  Michigan Economic Growth Institute** (2023 data) — the first national camp economic study since 1982.
  Method disclosed: "more than **20,000 records** and survey data from **1,137 camp operations**."
  Findings: **$70B economic impact, $23B labor income, 986,428 workers.**
  https://www.acacamps.org/resources/national-economic-impact-study-camp-industry ·
  https://news.umich.edu/us-camp-industry-adds-billions-to-national-economy/

---

## JOB 1E — CORRECT-AND-KEEP (origin real; the report's framing needs fixing)

These are **not** kills. Each has a real origin with a stated method. Each is currently stated in a
way that would not survive a hostile read.

### CK-1. Birthday party "$314 average" — the population qualifier is the whole story
`P5-appointments.md` #17. Every number checks out **exactly** against the origin. The framing does not.
- Origin: What to Expect (Everyday Health Group), **2024-07-30** — https://www.whattoexpect.com/family/celebrations/average-birthday-party-cost
- Verbatim method: *"The Everyday Health Group Pregnancy & Parenting **Talk to Moms Monthly Poll** was
  conducted… between **April 25 and 26, 2024**. We surveyed **404 women ages 18 to 44** who are
  currently pregnant or have at least one child **up to 5 years old**."*
- **Stripped qualifiers:** it is not "US parents" and not even "US mothers" — it is **404 mothers,
  18–44, pregnant or with a child under 5**; a **two-day** in-house poll of the publisher's own
  audience; **no probability sample, no MoE, no weighting disclosed**.
- **The killer detail: the "$344 for ages 6–10" cut is a subgroup of a survey whose recruitment screen
  required a child under 5.** That base is unreportably thin and self-contradictory.
- **P5 also uses the Millennial-vs-Gen-Z split ($329 vs $276) as the ONLY generational signal in the
  entire report.** Given the screen, that split describes *young mothers of toddlers*, not parent
  generations. **Do not build any Gen Z vs Millennial claim on it.**
- Also: P5 lists the publisher as "What to Expect" but the URL is **thebump.com**. Both are Everyday
  Health properties; fix the mismatch or a reader will call it a broken citation.
- **Aggregator watch:** partygeniusai.com republishes it as "The Party Genius **2026** Birthday Party
  Cost Report — 47 Birthday Party Statistics 2026" with "$314" as the 2026 headline. That is the
  date-stripping move, live.

### CK-2. Edsby / Cornerstone "App Overload" — **North America, not US**
`P4-extracurriculars.md` #31 and `P12` #11 both lean on it; S0/S1 inherit it.
- Origin PDF (free): https://cornerstonepr.net/wp-content/uploads/2025/03/AppOverloadReport_bg.pdf.pdf
- Verbatim method: *"stratified random sampling… **All respondents were located in North America**."*
  *"Surveys were administered over a **five-week period from December 2024 to January 2025**."*
  Participants: **109 teachers, 125 parents, 58 curriculum leaders.** Fielded by Cornerstone
  Communications (a PR firm) **in partnership with the vendor Edsby** — commissioned, not independent.
- **GEOGRAPHY CORRECTION: it is not a US study.** Of the 58 curriculum leaders, 49 were US. Edsby is a
  Canadian vendor. Anyone writing "a study of US parents" has performed the global-relabelled-as-US
  move. **State it as North America.** The brief's US-only rule means this cannot carry a US claim.
- **P4's arithmetic defence of the 85% is correct** (12% + 18% + 13% + 42% = 85% at 5-or-below), and
  worth keeping — but note **Edsby's own press release says 42%**, mis-transcribing its own report.
  **Cite the PDF, never the press release**, and never GovTech/eSchool News/PR Newswire, which are
  re-reports of the same release and fake corroboration.
- **Unit correction:** "10 to 15 apps" is what **curriculum leaders** said their *district* deploys —
  not a per-family count. The parent figure is per child: 14% use 1–3, 32% use 4–6, **44% use 7–9**,
  10% use 10+.

### CK-3. Bright Horizons Modern Family Index — **2026, not 2025, and both figures are subgroups**
The brief lists "Bright Horizons 85%/90% summer sleep-loss" as already known. The wave attribution is
wrong across the corpus, and P3 #25 tags it "method-deficient" when the current wave is fully disclosed.
- Origin: https://www.brighthorizons.com/newsroom/archive/2026-modern-family-index-working-parents-summer-break
- Verbatim method: *"conducted online within the United States by **The Harris Poll** between
  **April 14–16, 2026**, among **2,030 adults ages 18 and older** – among whom **616** are a
  parent/guardian of children under 18, and **479** are an **employed** parent/guardian."* ±2.7pp at
  95%, with an explicit warning that the interval widens for subsets.
- **True values: 90% of WORKING parents (n=479); 85% of ALL parents of under-18s (n=616).** Neither is
  out of 2,030. Both are subgroups with wider error than the headline MoE.
- **The 2025 wave is a different study** (school-readiness / tech detox). Its pages name Harris but
  **disclose no n and no fielding window** — if that wave is cited, say so. The 2017 MFI used a
  different partner entirely (Kelton Global, Oct 11–20 2017, ±2.2%). **MFI is now a multi-wave program
  with three separate 2026 releases: always name the wave.**

### CK-4. Google's "63% of Gemini users use voice" — global vendor telemetry, zero method
`P8-modality.md` #21–22. Value accurate; two qualifiers missing.
- Origin: Google's own post, **2026-08-11** — https://blog.google/innovation-and-ai/products/gemini-app/one-billion-monthly-users/
  Verbatim: *"63% percent of users now talk directly to Gemini, including more 'voice only' users."*
  And, confirmed: *"One in five Gemini Live interactions go beyond voice; people are using live camera
  feeds and screen sharing."*
- **No disclosed method whatsoever** — no definition of "monthly user" or "voice user", no measurement
  window, no geography. Gemini is a worldwide product at 1B monthly users, so this is **GLOBAL vendor
  telemetry**, not a US figure and not a survey. P8 flags this correctly; the flag must travel with
  the number into any synthesis.
- **Do not use the adjacent "busy parents are 43% more likely to use voice for everyday tasks"** from
  the same post. It has no base, no comparison group and no denominator. It is the single most
  tempting number in the corpus for this brief and it is unusable.

### CK-5. eMarketer voice-assistant series — a forecast, of people, US-only
`P8` #25. Confirmed and improved.
- Origin: EMARKETER, *Voice Assistant User Forecast 2025*, Jacob Bourne, **published 2025-09-03** —
  https://www.emarketer.com/content/voice-assistant-user-forecast-2025
- **eMarketer's own definition:** *"individuals of any age who use voice assistants at least once a
  month on any device"* — explicitly **de-duplicated across devices**, so it is **PEOPLE, not
  devices**, and **US-only**. Both endpoints are modelled: label **both** 139.8M and 168.2M as forecast.
- **"Of any age," not adults.** eMarketer publishes a separate adults-only series (123.5M US adults,
  Jan 2022). Anyone citing 139.8M as adults is wrong.
- Date it "EMARKETER forecast, September 2025" — the live series has since been revised to an
  April–May 2026 vintage.

### CK-6. US Travel "1.95B person-trips" — trips, not people; one endpoint is a forecast
`P6` #1. Confirmed exactly, with the split labelled at source.
- https://www.ustravel.org/research/travel-forecasts (Spring 2026 update, 2026-05-07; Tourism
  Economics + U.S. Travel Association).
- **2025's 1.95B sits under an ACTUAL header; 2026's 1.99B sits under FORECAST.** The 2026 figure must
  carry "forecast." **Unit: person-trips — one person taking six trips contributes six.** There is no
  person-count in the table. Never render as "1.95 billion Americans."
- Adjacent trap: the *total* domestic person-trip figures (2.40B / 2.44B) are frequently grabbed and
  mislabelled "leisure."

### CK-7. Harris Poll / Skylight — **SAFE, with one derived figure to quarantine**
`P4` #32. Fully verified and citable.
- https://myskylight.com/mental-load-report/ — *"conducted online in the U.S. by The Harris Poll on
  behalf of Skylight among **2,005 parents of children under the age of 18**… **May 15 to May 22,
  2024**."* Weighted, **±2.9pp at 95%**.
- Values confirmed: 30.4 hrs/week; 63% of brain space; ~402 tasks; **11.5 activities/week**;
  **17.5 communications/week**; 61% say it cut partner time.
- **Quarantine the $60,000/year figure** — it is a *derived calculation* (hours × $35.86/hr median
  wage), not a measurement. And **do not repeat Forbes' "$3.8 trillion in economic value,"** a
  national extrapolation the survey does not support. That is laundering of our own best source.

---

## JOB 1F — STRUCTURAL DEFECT: uncitable numbers sitting inside FINDINGS tables

Not stat kills — **placement** errors. Each is a number the collector itself labelled unusable, sitting
in a Section 1 table where a synthesist will lift the row and leave the caveat behind. The brief is
explicit: "Never mix these into Section 1."

| Where | The number | The defect |
|---|---|---|
| `M4` #23 | Custody X Change "fathers get 35% of custody time" | Tier column **literally reads "D → not citable"** — inside the FINDINGS table. The brief's HARD RULE is that Tier D is never citable. Move to WEAK SIGNAL. This is the most-recycled statistic in the co-parenting space; leaving it in a findings table is precisely how laundering propagates. |
| `P3` #26, #27 | YMCA "10 weeks of camp sold in ~90 seconds"; "registration opens Jan 5 / Jan 23" | Publisher is *Traverse City Ticker*; tier column reads **"press (non-tier)."** A single local-news interview with one YMCA program director in one Michigan market. Vivid and directionally useful — but n=1 market, and it must never be generalised to "camps sell out in seconds." |
| `P11` #41 | ChatGPT scheduled-task limits | Sole source **usecarly** (see NK-2). P11's own WEAK SIGNAL calls it "load-bearing" and demands in-product verification. Load-bearing + unverified + in Section 1. |
| `M3` #9 | ActivityHero "4M families" | See NK-1. A finding its own author forbids using is not a finding. |
| `P5` #17 | Birthday party $314 / the only generational split in the report | See CK-1. Missing fielding window alone disqualifies it under "no number without publisher, year, and method"; the under-5 screen disqualifies the age and generation cuts entirely. |

---

# ═══════════════════════════════════════════
# CONSOLIDATED KILL LIST — "Statistics We Refused To Use"
# Ready to lift into the final report as an appendix
# ═══════════════════════════════════════════

> **AMENDED after the second pass (2026-08-22).** Rows **K13, K15, K20, K22, K24 and K44 are superseded**
> by the SECOND PASS section at the end of this document. Read that section before lifting this appendix.

*Every number below circulates widely in this topic space. Each was traced to origin. None survived.
We publish this list because a research report's credibility rests as much on what it declined to
print as on what it did — and because several of these will appear in competitors' decks.*

**The four laundering moves.** Every item here is one of four: a **FORECAST** restated as a
MEASUREMENT; a **DEVICE** count restated as a PEOPLE count; a **GLOBAL** number relabelled **US**; or
a real number's **FIELDING DATE stripped** and reprinted on a "2026 statistics" page. A fifth,
rarer and worse, appears twice below: **fabricated attribution**, where a real institution's name is
bolted onto a number it never published.

### Tier 1 — FABRICATED: no origin publisher exists, or the named publisher never said it

| # | Statistic | Attributed to | What tracing found | Aggregators repeating it |
|---|---|---|---|---|
| K1 | **"37 million Millennial parents"** | Pew Research Center | **Pew never published this.** Full-text search of Pew's own API returns nothing. Pew published 17M Millennial *mothers* (2016) and 19M (2018) — mothers only. 37M appears to be 19M doubled to add fathers. **Fabricated attribution to the most-trusted publisher in the space.** | general parenting/marketing decks |
| K2 | **"30%+ of US parents secure summer childcare before the prior year ends"** | US Bureau of Labor Statistics (2023) | **BLS publishes nothing on booking timing.** No aggregator trail exists at all. Every element — agency, year, verb, threshold — is wrong. Probable corruption of CAP 2019's "32% started *looking* before March" (n≈1,000, MTurk). **Fabricated attribution.** | camp-vendor content marketing |
| K3 | **"15% completion drop per onboarding screen beyond five"** | Appcues | Not on any Appcues page. Entire footprint is one blog post. Appcues publishes only "60–70% is a solid target; below 50% you likely have too many steps." | lowcode.agency, openspaceservices, uxcam, semnexus |
| K4 | **"4–6% completion drop per form field beyond the eighth"** | Baymard Institute | No per-field percentage exists in Baymard. Their method (site audits + moderated testing, not A/B tests) structurally cannot produce a slope. Real: avg checkout 11.3 fields, "most sites need only 8." | numerous CRO blogs; a twin phantom "4.1% per field (HubSpot 2024)" on brixongroup, formbeam, ivyforms |
| K5 | **"$150 billion annual cost of missed US medical appointments"** | "industry" / peer-reviewed papers | Dead-ends at a 2017 trade-magazine op-ed by the **CMO of a scheduling-software vendor**, no method. Competing published figure: $50B. **Has since contaminated peer-reviewed literature by citation laundering.** | Aquina Health, Curogram, Simbo.AI, American Health Connection, MyPreOp |
| K6 | **"60% / 74% of parents feel guilty about screen time"** | various | No origin at any tier. Major publishers **do not measure guilt**. The two numbers bracket the real Pew figure on either side — the signature of back-filling. Real: Pew Oct 2025, n=3,054, **42%** say they could do better. | parenting blogs, vendor content marketing |
| K7 | **"Average child attends 8–12 birthday parties per year"** | various | No Tier A/B/C source exists. Lives only on party-vendor blogs and AI-generated listicles. | partygeniusai, jobera |
| K8 | **"57% of voice search users use voice commands daily"** | various | No publisher, no n, no date. Suspiciously adjacent to Edison's real 57% (share of voice-*command* users using them daily, Smart Audio Report 2022) with the base population silently swapped. | yaguara, keywordseverywhere, searchendurance |
| K9 | **"20.5% of people globally use voice search"** | — | No origin. No publisher named anywhere in the citation chain. | yaguara, embryo |
| K10 | **"24% / 26% / 38% use voice while cooking / doing chores / relaxing"** | — | No origin. **These are the context-of-use numbers this study most wanted, and they are entirely unsourced.** | serpwatch.io, bigsur.ai |
| K11 | **"Districts use 3–7 apps parents must download"** and **"parents get updates through 5–6 different apps"** | "studies" | No linked study; appears fabricated around Cornerstone's response buckets. | solvedconsulting and others |
| K12 | **"60% of parents miss important events"** | Cornerstone/Edsby | **Not in the Cornerstone PDF.** | secondary re-reports |
| K13 | **"70% of kids drop out of sports by 13"** | National Alliance for Youth Sports | **SUPERSEDED — see SP-4.** The number is dead, but a real origin study exists and says **35%, ages 11–18** (Ewing & Seefeldt, Michigan State, n≈26,000). The Washington Post (2016-06-01) hyperlinked the claim to nays.org's **bare homepage** — the laundering event is on the record. | Washington Post 2016, then ubiquitous |
| K14 | **"14,000+ AI startups launched 2024, 3,800 shut down 2025 = 40% failure rate"** | — | A Medium post with no methodology. | medium.com/@aiempiremedia |
| K15 | **"Only 19.2% of users complete onboarding; global average 8.4% after 30 days"** | — | **SUPERSEDED — see SP-8.** Both halves have origins and both are corrupted: 19.2% is Userpilot's **mean** (median 10.1%, n=547 **B2B SaaS** companies), and 8.4% is **Airship's 30-day RETENTION relabelled as onboarding completion**, over ~2.6bn **devices**, fielded Jan–Jun 2023. Only "top performers 40–50%" is genuinely originless. | setgreet.com, digia.tech, Business of Apps |
| K16 | **"Recommendations from friends and family is the #1 way parents find a camp"** | American Camp Association | No n, no fielding window, no origin document. ACA's own site does not carry it. | Jumbula blog, AdWave, TeenLife, RevenueBoomers |
| K17 | **ActivityHero "over 4 million families" / "400k subscribers"** | ActivityHero | Company rate card only. No press release, no date, no audit, and **no definition of the counting unit**. Cumulative-registrations-as-audience + list-size-as-subscribers. | vendor marketing |
| K18 | **Anything sourced to usecarly.com** | usecarly | SEO site for a competing commercial AI assistant. ~200 listicles, **no survey, no n, no method page anywhere.** "(2026)" title stamps are not evidence of currency. | self-propagating |
| K19 | **"Voice-AI startups raised $7B+ in Q1 2026"** | — | No dataset named — no PitchBook, Crunchbase or CB Insights cite. | metaintro.com |
| K20 | **"153.5 million US voice assistant users in 2025"** | eMarketer *(misattributed)* | **SUPERSEDED — see SP-3. The attribution is simply wrong.** The figure is **Astute Analytica's** (GlobeNewswire, 2025-12-08), and their framing is "engaged **daily**." eMarketer publishes no 2025 point; a 2025 midpoint of its forecast interpolates to ~152–155M, which is why it passes inspection. | voice-search listicles |
| K21 | **"Voice assistant market to reach $59.9B by 2033"** | Astute Analytica | Market-sizing press release, no methodology published. | GlobeNewswire, then everywhere |
| K22 | **"TeamSnap 24 million users"** | TeamSnap | **SUPERSEDED — FALSE KILL, see SP-2.** 24M was **TeamSnap's own homepage copy, Aug 2021–Feb 2022**. Not an aggregator artifact — just five years stale. Current figure is 30M, and TeamSnap's own Feb-2026 PR calls that a **"lifetime platform milestone"** against **2 million daily actives** — a 15x gap. | sports-tech blogs |
| K23 | **"Average consumer has 8.2 subscriptions / $118 per month"** vs **"4.5 subscriptions"** | — | Two mutually contradictory figures, no origin publisher. Self-contradiction is itself the tell. | subscription-management blogs |
| K24 | **"Children have ~50 days off school (excluding summer) in a 180-day year"** | — | **SUPERSEDED — see SP-6.** No origin, and the real figure is now measured: **30–38, median ~34.** CAP (2016) found the largest districts average **29**; independent counts of 2025-26 calendars give NYC 34, LAUSD 35, Chicago 33, Houston 32, Miami-Dade 32, Fairfax 38. **There is no path to 50 that does not smuggle summer back in.** | 2025 trade/opinion writing |
| K25 | **"add@cozi.com"** | Cozi | Appears nowhere on Cozi's site, FAQ, help sitemap, Wayback snapshots (2014/2017/2020/2023), or in **any of 1,917 Cozi reviews**. | forwarding-feature comparisons |

### Tier 2 — REAL ORIGIN, LAUNDERED BEYOND USE: cite only with every qualifier restored

| # | Statistic as circulated | The true statement | The move |
|---|---|---|---|
| K26 | **"8.4 billion voice assistants by 2026"** | Juniper Research, **2020 forecast**, of **8.4bn DEVICES worldwide by 2024**. | FORECAST→measurement, DEVICES→people, GLOBAL→US, **and the year moved**. All four moves in one number. |
| K27 | **"71% of consumers prefer voice over typing"** | PwC 2018 (n=1,000 US 18–64, online panel): in a **hypothetical forced binary**, **for search only**, on an implied base of **voice-assistant owners**, 71% chose voice. The same chart shows voice **losing** on shopping (24–36%) and service (34%). PwC has retired the page and PDF. | Qualifier-stripping + date-stripping. Contradicted by Pew's real measurement (22%). |
| K28 | **"92% of families will travel with their kids next year"** | **No year of the FTA survey reads 92%** (real series: 93/93/88/79/70/88/81%). And **non-travelers are filtered out at the end of the first question block**, so no year's value is a population estimate. Non-probability recruitment from travel-affiliated mailing lists. | Screened-sample artifact laundered into a population stat. **The most dangerous item here — it survives a casual check.** |
| K29 | **"Fathers get 35% of custody time"** | Custody X Change 2018 **model**, not measurement: they surveyed attorneys about *typical state guideline schedules*, then computed percentages **in their own software**. Verbatim: **"No customer data was used."** Assumes one child aged 6–11, amicable parents, no violence or substance abuse. | A vendor model of guidelines laundered into an empirical distribution, then re-laundered by SEO blogs as a Census figure. |
| K30 | **"30% pediatric no-show rate"** | **No US national rate exists.** Literature spans 1.5%–24%; Boston Children's reports 20%; **>30–50% only in urban safety-net / adolescent / high-social-risk subgroups.** Honest range: **10–25% typical.** | The subgroup ceiling published as the mean. |
| K31 | **"Gen Z spends $377/month on subscriptions"** | Real US origin — but it is **Wethrift.com (a coupon-affiliate site), Oct 2021, n=1,030 recruited on Amazon MTurk**. Fails Tier C. Separately, **Visa/Basis found £305/mo — in the UK** (n=4,152, Nov–Dec 2024), and that figure is independently laundered into US dollars. | Non-method source + a parallel GLOBAL→US relabel. Note Visa's Gen X (£91) is *lower* than Boomers (£108) — a contradiction the laundered US version silently "fixes." |
| K32 | **ACA "26 million attend camp each summer"** | ACA's published figure was **14 million (2013 basis)**, never 26 million. ACA has deleted the page. Its current site publishes only member reach (7.2M campers). | Roughly double the last real figure, with no publisher behind the inflation. |
| K33 | **ACA "more than 14,000 day and resident camps"** | **Real** — ACA, **2017 Sites, Facilities & Programs Report** (8,400 resident / 5,600 day). But nine years old and the hosting page is deleted; ACA's current working universe is **>20,000 camp operations**. | Date-stripping. Citable ONLY with "ACA, 2017." |
| K34 | **"Over 62% of US adults use a voice assistant" dated 2025/2026** | The 62% is real — **NPR/Edison, fielded Feb–Apr 2022**. | Pure date-stripping: sound number, fabricated year. |
| K35 | **"85% of parents rate their multi-app setup ≤5/10"** and the Edsby study generally | Arithmetically correct from the source PDF (12+18+13+42) — **but the study is NORTH AMERICAN (US + Canada), n=125 parents, commissioned by the vendor Edsby via a PR firm.** Edsby's own press release mis-states it as 42%. GovTech / eSchool News / PR Newswire are re-reports of the same release and **fake corroboration**. | GLOBAL→US, plus corroboration-faking. |
| K36 | **Birthday party "$314 average" on 2026 statistics pages** | Real: What to Expect / Everyday Health, **fielded April 25–26 2024**, **n=404 women 18–44, pregnant or with a child under 5.** The "$344 for ages 6–10" cut is a subgroup of a survey that screened for a child under 5. | Date-stripping (partygeniusai reprints it as a 2026 figure) + population-stripping. |
| K37 | **Bright Horizons "85% / 90% summer sleep-loss"** cited as 2025 or as all parents | Real: **Harris Poll for Bright Horizons, April 14–16 2026**, n=2,030 adults — but **90% is the n=479 EMPLOYED-parent subgroup** and **85% is the n=616 all-parents subgroup**. The 2025 wave is a different study with **no disclosed n or fielding window**. | Wave confusion + subgroup-as-topline. |
| K38 | **Google "63% of Gemini users use voice"** as a US or parent statistic | Google blog, 2026-08-11. **Global vendor telemetry, zero disclosed method**, no definition of "voice user," no window, no geography. | GLOBAL→US. **Also: never use the adjacent "busy parents are 43% more likely to use voice" — no base, no comparison group, no denominator.** |
| K39 | **eMarketer "139.8M → 168.2M US voice assistant users"** stated as measurement | A **forecast** at both endpoints (EMARKETER, Sept 2025). Definition: **individuals of any age using a voice assistant ≥ monthly on any device, de-duplicated across devices** — people, not devices; **not adults** (eMarketer's adults-only series is separate). | FORECAST→measurement; "any age"→adults. |
| K40 | **US Travel "1.99B trips in 2026"** | 2025's 1.95B is an **actual**; **2026's 1.99B is a forecast**. Unit is **person-trips, not people** — one person taking six trips contributes six. | FORECAST→measurement; TRIPS→people. |
| K41 | **Skylight/Harris "mental load worth $60,000/year"** and Forbes' **"$3.8 trillion"** | The underlying Harris survey is **sound and citable** (n=2,005 US parents, May 15–22 2024, ±2.9pp). But $60,000 is a **derived calculation** (hours × median wage), and Forbes' $3.8 trillion is a **national extrapolation the survey does not support**. | Derived-figure-as-measurement. A case of our own best source being laundered downstream. |
| K42 | **Klook "91% of global travelers rely on AI travel planners"** | Vendor survey, n=11,000, **global**, and implausibly high against every other source. | GLOBAL→US, outlier. |
| K43 | **Litmus email-client share as mailbox-provider share** | Litmus measures the **rendering client's user agent**: Apple = 62.3% of *opens* vs **3.6% of mailboxes** (Validity) vs 17% of US adults using iCloud Mail (Statista). **~90%+ of "Apple" opens are Apple's app reading someone else's mailbox.** | The purest DEVICES-as-PEOPLE case in the corpus. **Caught by S1 before it shipped — the model of what this appendix is for.** |
| K44 | **"CASA costs $15,000+"** | **SUPERSEDED — see SP-9.** A **real Google-published fee**, but never CASA's price: it is the **superseded pre-CASA restricted-scope regime** ($15k–$75k+, 2018–2020; lowered to $10k–$75k with a $4,500 floor in 2021–22). Removal window pins to **late Oct–early Nov 2022**, not June 2022–June 2023. Live lab prices $675–$8,000. | Date-stripping of a retired fee schedule from a superseded regime. |

### Tier 3 — MEASURED, BUT THE MEASUREMENT DOES NOT EXIST
*Numbers we looked for, could not find at any tier, and are therefore reporting as absent. Stating
these is what stops the next person fabricating them.*

- **Hours a US parent spends researching and booking summer care.** No survey measures it.
- **Trips per year for US households with children.** No publisher reports it.
- **Time spent deciding a weekend activity; weekend-outing spend per episode.** No data, US.
- **Share of US households sustaining a shared digital family calendar / the "we tried it and it
  didn't stick" pattern.** No data at any tier — probably the single most decision-relevant unknown.
- **Apps/portals/logins per family, probability-sampled.** Does not exist. Edsby n=125 (North
  American, vendor-partnered, screened for parents already using 3+ apps) is the only parent-level
  number in existence.
- **Permission slips / school forms per year; picture days; early-release and PD-day counts.** No source.
- **Parents' comfort granting a consumer app OAuth inbox access**, or comfort with a third party
  receiving their child's school communications. **No Tier A/B survey measures either construct**
  (independently confirmed by P10 and P12).
- **Any funnel comparison of email-forwarding onboarding vs OAuth inbox connection.** Does not exist
  in public. Put no number on it.
- **D1/D7/D30 retention benchmarks.** Every origin path is gated (AppsFlyer, Adjust, Statista, Sensor
  Tower). Not citable from this program.
- **Adoption of Apple Hide My Email / Firefox Relay.** Neither publishes any number.

---

# ═══════════════════════════════════════════
# JOB 2 — VERIFICATION OF raw/P12-aggregation-email.md
# ═══════════════════════════════════════════

**Overall verdict: P12 is a strong report and its central recommendation survives.** The pivot away
from "register our address with the school" toward "parent auto-forwards from their own mailbox" is
supported by everything I could independently confirm. But **the single most strategy-critical row in
the matrix — ParentSquare — rests on a source no reader can check**, and five other rows need
correction. P12 is commendably honest about its own limits (it discloses that its WebSearch budget
was exhausted and that it worked by curl and constructed URLs); that disclosure is exactly why these
corrections were findable.

## 2A — THE FEASIBILITY MATRIX

### ⚠️ ParentSquare — **VERDICT UNSOURCEABLE (highest-priority defect)**
The BLOCKED verdict on ParentSquare is one of the two verdicts that kill the register-with-the-school
strategy. It cannot be sourced to the vendor's own documentation, because **ParentSquare's help
center is not public**. It is a Zendesk instance behind a ParentSquare login:
- `parentsquare.zendesk.com/hc/en-us` and `help.parentsquare.com` return 403 to fetchers; in a real
  headless Chrome **both render the ParentSquare Sign In page**, not help content.
- ParentSquare says so itself: *"Go to the Help Center in ParentSquare **(login required)**…"*
  (https://www.parentsquare.com/resources/help-center/)
- `support.parentsquare.com` is the app, not docs. No public sitemap; robots.txt exposes no docs paths.

**Consequence.** None of the ParentSquare claims — SIS gating, the nightly-sync overwrite, the
"Please contact your school office to add an additional email address" quote, the Edit-Account
question, or the Digest-is-default claim — is verifiable by a reader without an account. P12 is
partly candid about this in its method notes ("ParentSquare's help center is now login-gated… its
row rests on district IT pages plus ParentSquare's own public FAQ"), and I agree the underlying
finding is probably right — three independent district pages say the same thing. **But the matrix
cites `parentsquare.com/resources/help-center/` as though it were the source of the quote, and it is
not.** Re-label the citation (district IT pages, named, with dates) or obtain the quote under an
authenticated session and date-stamp it. **Do not ship a strategy-killing verdict on an
unverifiable citation.**

### Corrections to individual rows

| Row | Verdict | Correction |
|---|---|---|
| **Infinite Campus** | **BLOCKED — CONFIRMED, all three sub-claims** | Verbatim confirmed: *"If you forget your Campus username or password, this email address will be used to help you through the recovery process"* (kb.infinitecampus.com/help/account-settings); *"**If your school has turned on certain options**, you may be able to modify your phone numbers and email addresses"* (/campus-parent-portal); and the approval queue at /portal-request-processor. **Add a sharper point than P12 makes:** even where a district enables editing, the parent edits **their own census contact record** (Home/Work/Other email). **There is no "additional notification email" field anywhere in Campus Parent.** The verdict is not just blocked — the feature does not exist. |
| **ClassDojo** | **BLOCKED — CONFIRMED, one sub-claim overstated, one blocker MISSING** | Email-is-login confirmed: *"you've already used that email address for another ClassDojo account… you'll need to use a different email address"* (/articles/202816865). No secondary-email field exists in any account doc. **CORRECTION:** "second parent account is teacher-initiated" overstates it — /articles/202027769 documents a **printed parent-code path**: *"Give the **same code to each parent**. Tell each parent to follow the directions on the sheet to create two different accounts using the same code."* A parent holding the class code can self-serve a second account on a second email. "School-originated" is defensible; "teacher-initiated per account" is not. **MISSING BLOCKER:** P12's finding #18 attributes app-kills-email to ClassDojo — correct — but the matrix ClassDojo row should state it as a *verdict driver*: *"By downloading the app, you'll receive push notifications instead of email notifications. At this time, it's **not possible to receive both**."* Any ClassDojo parent with the app gets **zero** email, which moots the whole row. |
| **Seesaw** | **BLOCKED — CONFIRMED, but SOFTEN** | Verbatim confirmed: *"Seesaw accounts can only use one email address at a time and cannot be merged"* (/articles/115005566243). **CORRECTION:** the same sentence documents the sanctioned workaround — *"please have each family member sign up with separate email addresses, and use the same QR code or email to **link up to 10 family accounts to a single child/class**."* So: blocked for a *secondary address on one account*; **open via a second family account (teacher-issued code required), up to 10 per child.** P12's "11th-slot" framing understates a real path. |
| **PowerSchool** | **WORKS — CONFIRMED VERBATIM, field name exact** | Section heading is literally **"Additional Notification Emails"**; the field is *"**Email Address(es)** — If you have authorized the delivery of email notifications to another person, enter the other person's email. **Separate multiple email addresses with commas.**"* Parent-controlled and self-serve, confirmed by the page's own framing. Cadence confirmed: the "How Often?" menu is Never / Weekly / Every Two Weeks / Monthly / *"**Daily** — Emails will be sent out every day, except Saturday and Sunday"* — **no instant option.** **Two fixes:** (1) **the cited URL is wrong** — `/pt/latest/email-notifications` 404s; the live path is **`https://ps.powerschool-docs.com/pssis-student-parent/latest/email-notifications`**. (2) Add the **"Send Now"** footnote — *"Send Now for [Student Name]? Select the checkbox to receive the selected information immediately"* — so "no real-time email" is not read as "no way to trigger an immediate send." Also soften "no school action" to **"no school action documented"**: the docs never mention a district toggle, but never affirmatively rule one out. |
| **Remind** | **WORKS — CONFIRMED, all three, verbatim** | *"Click on the **+ Add device** button to add an additional email or phone number"*; *"you'll need to **confirm your new device through a 4-digit confirmation code**"*; *"**When you download the app, push notifications are turned on, and your text and email Remind messages are automatically disabled**"* (help.remind.com/hc/en-us/articles/206430755). Mobile paths label it "Add phone or email" — cosmetic only. |
| **TeamSnap** | **WORKS — CONFIRMED, add two gates** | *"Click **+ Add Family Member**"*; *"**All contacts added under a member profile will have access to the same information the member has.**"* **Add:** the button is gated on the primary accepting their own invite first — *"If there is no option to add family members, this is because the main contact has not accepted their invitation yet"* — and account access requires a separate **"Invite to Join?"** toggle; without it you have added a contact record, not an account. |
| **SportsEngine** | **WORKS — CONFIRMED, both paths, verbatim** | Account-level: *"click Edit. Click **Add Email**"* (/articles/6311527), plus *"**You can not have two SportsEngine accounts with the same email address (primary or secondary)**"* — which a per-family address design satisfies, as P12 says. Per-athlete: *"Below the **Secondary** heading, enter the additional email address"* (/articles/6304756). |
| **Brightwheel** | **PROVIDER-GATED — the framing is INVERTED** | The quote is exact but proves the opposite of what the row says: *"**Providers are unable to edit** a student contact's email or phone number once the guardian account has been created… **only the student contact can change their username**… Please direct student contacts to **update the email themselves**."* The provider is locked out; the **guardian controls their own address**. **Correct framing:** email is the username, one per account, **guardian-editable** — and adding an *additional* address means adding a **new student contact**, which *is* a provider action. The gate is real but sits in a different place than the row states. |

**Net effect on the score.** P12's "5 clean WORKS / 6–7 BLOCKED" survives, with these adjustments:
PowerSchool, Remind, TeamSnap and SportsEngine are **confirmed WORKS** (the strongest part of the
report); ClassDojo and Infinite Campus are **confirmed BLOCKED and arguably more blocked than
stated**; Seesaw should soften from BLOCKED to **blocked-with-a-documented-workaround**; Brightwheel
needs rewording; and **ParentSquare's verdict is unsourceable pending an authenticated check.**

## 2B — THE CRUX: DOES THE EMAIL CARRY CONTENT, OR ONLY A LOGIN LINK?

This is the question the whole architecture turns on. Results are **more mixed than P12's matrix
implies**, and two cells must not be upgraded.

| Platform | Verdict | Evidence |
|---|---|---|
| **PowerSchool** | **CONFIRMED — real content** | The notification *is* the report. Checkboxes: "Summary of Current Grades and Attendance", "Detail Report Showing Assignment Scores for Each Class", "Detail Report of Attendance", "School Announcements", "Balance Alert." |
| **ClassDojo — announcements** | **CONFIRMED verbatim** | *"Email delivery will include **the full text of the announcement with images displayed in-line.** Subject line: up to 80 characters; Message body: **up to 10,000 characters**; Attachments: displayed in-line where possible."* (School/District Announcements FAQ) |
| **ClassDojo — private chat** | **UNDETERMINED — do not upgrade** | The parent-notifications article says *when* a notification fires but never describes the body. No ClassDojo doc states whether private-message email carries text. P12's "undetermined" is correct and must stay. **Overriding constraint: app installed ⇒ no email at all.** |
| **Seesaw — digest** | **CONFIRMED CONTENTLESS, verbatim** | *"Once Per Day… Family members will receive an email summary with the number of new posts or new messages received, **but will not see message content**."* Identical contentless wording for push and SMS. |
| **Seesaw — per-event** | **CANNOT VERIFY — do not infer content** | The "All" setting is documented only as *"Family members will receive an email for each new post or message."* Seesaw pointedly says "will not see message content" for the digest and **stays silent for "All."** Suggestive, not dispositive. Report as *per-event content undocumented*, never as content-bearing. |
| **Brightwheel** | **PARTIALLY CONFIRMED — a material carve-out P12 misses** | Daily Reports do carry content: *"will include **all logged activities** on a child's feed that are viewable for parents."* **But the same article excludes the messaging channel:** *"What information is included in a Daily Report? Any activities logged on a student's activity feed visible to parents. **Messages, paperwork, and other features are not visible.**"* And delivery is conditional on **check-out**. So Brightwheel email carries the daily-report stream but **not** provider messages or paperwork — a significant hole for a product whose value is catching what the parent would otherwise miss. |
| **ParentSquare** | **CANNOT VERIFY** | Login-gated help center. Neither the body-content claim nor the "Digest is default for new accounts" claim is publicly sourceable. |

**Implication for the architecture.** The content-in-body assumption holds cleanly for **PowerSchool**
and for **ClassDojo announcements**, holds partially for **Brightwheel**, is **explicitly false for
Seesaw's digest**, and is **unverified for ParentSquare and Seesaw per-event**. P12's own strongest
insight stands and is arguably strengthened: **the binding constraint is not link-vs-body, it is
app-install exclusivity** — ClassDojo and Remind both silently zero out email the moment the app is
installed. A parse-the-email architecture inherits a coverage hole that no amount of parsing skill
closes.

## 2C — THE CASA CLAIMS

**Verdict: the decisive claim survives interrogation intact and is if anything understated. Two
supporting claims need correction before publication.**

### ✅ The 100-user lifetime cap — **CONFIRMED, and NOT conflated**
This is the claim the recommendation rests on, and it holds. Google's own current wording, twice:
> "**The user cap limits the number of users that can grant permission to your app when requesting
> unapproved sensitive or restricted scopes. The user cap applies over the entire lifetime of the
> project, and it cannot be reset or changed.**" — https://support.google.com/cloud/answer/15549945
> "**Please note the user cap applies over the entire lifetime of the project, and it cannot be reset
> or changed.**" — https://support.google.com/cloud/answer/13463817

And the quota table: *"New user cap | Apps that present the unverified app screen to users | **100 new
users in total**, after the app presents the unverified app screen"* (support.google.com/cloud/answer/7454865).

**The two mechanisms, disambiguated** — these are widely conflated, and P12 did **not** conflate them:

| Mechanism | Google's wording | Resettable? |
|---|---|---|
| Publishing status = **Testing** | *"limited to up to **100 test users** listed in the OAuth consent screen. **A test user consumes a project's test user quota once added.**… **Authorizations by a test user will expire seven days from the time of consent.**"* | A list you edit — but quota is consumed on add, and **consent expires every 7 days**. Unusable for a real beta. |
| **In production**, unverified, sensitive/restricted scopes | The 100-new-user **grant** cap above. | **No — lifetime of the project, cannot be reset or changed.** |

**Two additions that make the finding stronger than P12 states:**
1. The failure mode is explicit and worse than "capped": *"Failure to get your app verified before
   making requests to sensitive or restricted scopes will result in your project's 100 new-user cap
   eventually getting exhausted and **Google sign-in being disabled for your users**."*
2. **The cap is a gate, not a permanent ceiling.** Once approved, *"the user cap does not apply if you
   are requesting only approved sensitive or restricted scopes."* A project that burns 100 grants
   while unverified has burned them permanently — but verification lifts the cap. State both halves.

**Verdict: LOUD CONFIRMATION.** A closed beta fits under it; a launch does not; and the burn is
irreversible per GCP project. P12 #25 is correct as written.

### ⚠️ "Free self-scan eliminated May 2024" — **RIGHT CONCLUSION, WRONG DATE BY ~2 YEARS, and the quoted sentence does not exist**
- **True today:** https://appdefensealliance.dev/casa/casa-tiering (now titled "Assurance Levels")
  lists exactly two levels, **both lab-only**: *"**2 | Lab Tested - Lab Verified**… Developers can
  contact one of the ADA authorized labs"* and *"**1 | Lab Tested - Lab Verified**."* **No self-scan
  path exists.** Google agrees: *"Applications are assigned to either the **AL1 or AL2** assurance
  level"* (support.google.com/cloud/answer/13465431).
- **The date is wrong.** Wayback shows the four-tier model *with* the developer self-scan still
  published long after May 2024 — the 2024-06-04, 2025-02-10, 2026-03-17 and **2026-05-20** snapshots
  all still read *"Tier 2… **Developer Tested - Lab Verified**… the application developer scans their
  application."* The **2026-07-01** snapshot is the first with zero "Developer Tested" rows. **The
  change landed between 2026-05-20 and 2026-07-01, not May 2024.**
- **The quoted sentence "The CASA self scanning process is deprecated" appears nowhere on
  appdefensealliance.dev today.** ADA deleted the tiers rather than announcing a deprecation.
- **Also flag, because it will make us look wrong:** Google's own FAQ is stale and still contradicts
  ADA — *"**If you are in scope for the free tier 2 assessment**…"* still sits on
  support.google.com/cloud/answer/13463817. P12 already caught this in WEAK SIGNAL; promote it, and
  **cite the ADA tiering page, not the Google FAQ**, or a reader checking us against that page will
  conclude we got it wrong.
- **Net: plan for paid. The conclusion is right. Fix the date and drop the fabricated quote.**

### ✅ Mandatory, annual, full re-test, tier assigned by Google — **CONFIRMED 3/3** (one quote needs updating)
- Annual: *"Apps that access restricted scopes are required to complete a security assessment **every
  12 months**. This 12-month period is calculated from the effective date of the app's previous
  '**Letter of Validation**' (LOV)."* (answer/13463816). P12's quoted phrasing ("must be reverified
  for compliance and complete a security assessment at least every 12 months") is not current wording
  — substance is right, update the quote.
- Full re-test: **verbatim confirmed** — *"**We require the annual security reassessment to be a
  complete test of your application whether you have made any changes or not.**"* (answer/13463817).
- Tier assigned by Google: **verbatim confirmed** — *"**The framework users (Google..etc) and not the
  application developer** calculate and determine which assurance level is required."*
- **Add this, because it changes the cost model:** *"The required assurance level is **dynamic and may
  increase**… **Once an application has been validated at the highest level (AL2), it will continue to
  be validated at that level in subsequent years.**"* **The level ratchets up and never comes back
  down.** An annual cost modelled at Tier 2 can become a permanent Tier 3 cost after one bad year.

### ⚠️ "$675 (Tier 2) to $4,500 (Tier 3)" — **PRICES CONFIRMED; "Google-named preferred partner" is FALSE**
- TAC Security's live page confirms every figure: **$675** (Tier 2 one-time, LoV in 1–3 weeks),
  **$855** (Tier 2 premium, unlimited revalidation), **$3,600** (Tier 2 unlimited), **$4,500**
  (Tier 3 one-time, 2–4 weeks).
- **CORRECTION:** TAC Security *is* an ADA-listed authorized lab (alongside Bishop Fox, NCC Group,
  DEKRA, Leviathan, Prescient Security, NowSecure, ValueMentor, NetSentries, Eydle). But **"Google
  Recommended" is TAC's own marketing copy on TAC's own page, not Google's language.** Google
  explicitly disclaims involvement: *"**Google does not charge the developer any fees for security
  assessment**… The cost is agreed between the developer and the assessor **without any involvement
  from Google**. We encourage our developers to reach out to multiple assessors."* **Google names no
  preferred partner.** Drop "Google-named."
- **Vocabulary trap:** TAC still prices in the **retired Tier 2 / Tier 3 vocabulary**. Map to AL1/AL2
  before treating a quote as a plan.

### ✅ "6 weeks to several months" — **CONFIRMED, all four figures**
Verification-types table (answer/13463817): Brand **2–3 business days**; Sensitive **10 business
days**; Restricted **6 weeks** — with Google's own asterisk: *"these estimates are **not guaranteed**
and will vary based on developer responsiveness."* And separately: *"verification **might require
several months** for the app to complete"* (answer/7454865). **Treat 6 weeks as the optimistic case:
it excludes your own remediation time, and the CASA assessment sits inside it.**

### ⚠️ "ALL Gmail body-reading scopes are restricted" — **CONCLUSION RIGHT, STATED RULE FALSE**
**`gmail.modify` IS restricted.** P12's operative point stands: it is not a workaround, and P12 is
right that this kills the widely-circulated "just use gmail.modify" advice (including the Orbis
engineering blog claim P12 already flags). But the *rule* P12 states is wrong in **both** directions:

| Scope | Actual classification |
|---|---|
| `gmail.readonly` | **Restricted** |
| `gmail.modify` | **Restricted** |
| `gmail.metadata` | **Restricted** — *and it reads NO body* ("labels and headers, **but not the email body**") |
| `gmail.addons.current.message.readonly` | **Sensitive** — *and it DOES expose message content* |
| `gmail.labels` | **Non-sensitive** |

"Reads bodies ⇒ restricted" is not Google's criterion — the published scope list is. **Keep the
conclusion, drop the rule.** Also load-bearing and worth promoting: *"**If you store restricted scope
data on servers (or transmit), then you must go through a security assessment.**"* The assessment
trigger is **server-side storage or transmission** of restricted-scope data — which is an
architecture lever, not just a compliance fact.

### ✅ The AI-training and human-read prohibitions — **CONFIRMED verbatim, but cite the right documents**
Both sentences exist; P12 cites them to one page when they live in two:
- *"**Google User Data may not be used to train or improve foundational or frontier models or be
  stored in conjunction with such models**"* — support.google.com/cloud/answer/13463817 (§ Limited Use).
  The binding policy text is at developers.google.com/workspace/workspace-api-user-data-developer-policy.
- *"**Don't allow humans to read the data, unless: You first obtained the user's affirmative agreement
  to view specific messages**…"* — developers.google.com/terms/api-services-user-data-policy. The
  Workspace-specific policy adds **"and documented"** to the consent requirement.
- **Google's own definition of the line, which P12 should carry because it is the escape hatch:**
  *"personalized models include any models run **exclusively on-device or a model specifically
  tailored to only that end user or organization**. Personalized models **do not co-mingle Google User
  Data with other end users or organizations**."* P12 calls this "genuinely ambiguous territory" —
  that is fair, but the per-user-no-comingling test is the concrete standard to design against.
- **One product requirement P12 omits:** if the app transfers data for AI model training, *"your
  demonstration video must show the flow of the user **explicitly consenting** to their data used for
  personalized AI model training."*

## 2D — GMAIL FORWARDING: DOES THE VERIFICATION LINK GO TO THE DESTINATION?

**CONFIRMED — but the "design unlock" is half an unlock, and P12 overstates it.**

Google's own wording (https://support.google.com/mail/answer/10957):
> "**After you add a forwarding email address, we send a verification link to the address.**"
> "A verification message is sent to the forwarding email address. **In the other email account, click
> the verification link in the message.** **Return to the 'Settings' page in Gmail. Refresh your
> browser… select 'Forward a copy of incoming mail to'… At the bottom of the page, click Save Changes.**"

So: **the destination does receive the link**, and a service owning that inbox **can** auto-complete
that half. **But there is a second step that cannot be automated:** the source user must return to
their own Gmail settings, select the forwarding option, and click **Save Changes**. **Verification
alone does not turn forwarding on.** P12 #31's "we can auto-click the verification link — collapsing
the hardest step" is right that it removes the copy-paste-a-code step; it is wrong that it collapses
the flow. The parent still walks a multi-step desktop-web sequence and must return to it *after*
we confirm.

**Two anti-abuse facts P12 does not carry, and should:**
- *"'You are forwarding your email to [address]' — If you set up automatic forwarding, **you get this
  notice for the first week** after you turned on forwarding."*
- *"**There's a forwarding notice & you didn't set up forwarding** — Change your password immediately.
  **Someone else might have access to your Gmail account.**"*

**Google treats unexplained forwarding as an account-compromise signal and shows a week-long banner.**
A flow that auto-confirms the destination side will, to an inattentive parent, look exactly like the
compromise pattern Google is warning them about. That is a product requirement — conspicuous
in-product explanation of the banner, timed to when it appears — not a footnote. It also reinforces
P12 #44's verbatim finding that silent failure is catastrophic: the same user who ignores the banner
is the user who goes 18 months without noticing forwarding broke.

## 2E — THE FERPA / SOPPA ANALYSIS

**⚠️ NOT LEGAL ADVICE. I verified only that the cited provisions exist and roughly say what is
claimed. Whether they bear the weight P12 puts on them — especially the §99.31(a)(12)/§99.33(c)
redisclosure theory and the ToS-enforceability arguments — is a question for licensed counsel, and
this section must not be relied on without one.**

| Cite | Verdict |
|---|---|
| **34 CFR §99.31(a)(12)** | **EXISTS, says what's claimed.** Verbatim: *"(12) The disclosure is to the parent of a student who is not an eligible student or to the student."* Under §99.31(a)'s chapeau permitting disclosure **without §99.30 consent**. |
| **34 CFR §99.33(c)** | **EXISTS, and (a)(12) IS among the enumerated paragraphs.** Verbatim list: *"§§ 99.31(a)(8), (9), (11), (12), (14), (15), and (16)"* plus the Clery carve-out. §99.33(d) carries the identical list for the notice duty. So P12's core FERPA point — that the school→parent chain terminates at the parent — is textually supported. |
| **"§99.33 has only (a)–(d)"** | **CONFIRMED. There is no §99.33(e).** P12's catch of this common mis-cite is correct. |
| **34 CFR §99.67(e)** | **EXISTS — five-year ban confirmed verbatim.** One nuance P12 should carry: the sanction is phrased as a prohibition on the **originating school** (*"the educational agency… **may not allow** the third party… access… for at least five years"*), **not as a direct penalty on the third party.** The commercial effect is the same; the mechanism is not. |
| **34 CFR §99.64(b)** | **EXISTS — SPPO may investigate a third party directly**, or on its own initiative with no complaint filed. Corroborated by §99.65(a) and §99.66(d). |
| **34 CFR §99.1(a), §99.3 "education records"** | **CONFIRMED both halves.** Applies to agencies receiving Dept-of-Education funds; "education records" requires records *"**Maintained by** an educational agency… **or by a party acting for** the agency."* P12 #52's conclusion follows textually. |
| **"'School official' is not defined in §99.3"** | **CONFIRMED** — I enumerated every §99.3 defined term; it is absent. **Slight overstatement to fix:** P12 says it is "operative only in §99.31(a)(1)." It is *defined* nowhere, but it also **appears** in §99.7(b)(3)(iii) (each agency must specify its own "criteria for determining who constitutes a school official"), §99.31(c), §99.32(d)(2) and §99.36(b)(2)–(3). |
| **Illinois SOPPA §26(2)** | **EXISTS — but P12 compresses it.** Verbatim, the exemption covers **four** categories, not one: *"other than the student's parent, **school personnel, appointed or elected school board members or local school council members, or the State Board**, without a written agreement."* **And: "This paragraph (2) does not apply to nonpublic schools."** P12's "IL blocker" conclusion is directionally supported for public schools; the framing needs both corrections. |
| **Illinois SOPPA §27(b)** | **EXISTS, verbatim** — *"Any agreement or contract entered into in violation of this Act is **void and unenforceable as against public policy**."* Note §27(h): the section does not apply to nonpublic schools. |
| **Illinois SOPPA §30(3) / operator definition** | **EXISTS BUT MIS-LOCATED.** The general-audience carve-out is in **§30 "Applicability"** — an Act-level scope exclusion — **not** inside the operator definition. The operator definition is **§5** and carries its own separate narrowing trigger ("used primarily for K-12 school purposes **and was designed and marketed for** K-12 school purposes"). P12 #54 attributes the carve-out to the operator definition; the substance is real but lives in two distinct places. |
| **Cal. B&P §22584(a)(7), §22584(j)** | **CONFIRMED both, verbatim**, exactly as P12 states. |
| **NY Ed. Law §2-d(1)(k)** | **CONFIRMED** — *"receives student data… **pursuant to a contract or other written agreement**."* **Confidence caveat:** nysenate.gov 403s scripted access and Justia/FindLaw also 403'd, so there is no second-source corroboration. Pull from Westlaw/Lexis before this is load-bearing. |

**Where P12's legal analysis is strongest:** the asymmetry it identifies — that OAuth-reading the
parent's inbox terminates the chain at the parent under §99.31(a)(12)+§99.33(c), while registering a
third-party address plausibly attaches §99.33(a)'s restriction — is **textually supported by
provisions that all exist and say roughly what is claimed.** P12 is also right to flag, in its own
WEAK SIGNAL, that *"whether a §99.30 consent authorizing onward use displaces §99.33(a)'s
redisclosure restriction"* has **no text, no SPPO guidance and no case** — that is the correct
posture, and it is the question to put to counsel first.

## 2F — THE ToS HOSTILITY CLAIMS

| Claim | Verdict |
|---|---|
| **Seesaw bans AI training on content** | **EXISTS, verbatim — but P12 cites the WRONG DOCUMENT.** The clause is **Seesaw End User Terms §2.2(c)** (https://seesaw.com/end-user-terms/, updated 2024-07-08): *"use any content available on or via the Service… for any **machine learning and/or artificial intelligence training or development purposes**, or for any technologies designed or intended for the identification of natural persons."* **The separate district-facing https://seesaw.com/terms-of-service/ (updated 2026-02-17) contains NO ML/AI clause, and ITS §2.2 is "Customer's Licenses to Us."** A cite reading "Seesaw ToS §2.2" points at the wrong document and will not check out. Also note §2.2(b) carries a conventional anti-bot clause. |
| **ClassDojo bans automation and competing products** | **EXISTS, all three, verbatim** (https://www.classdojo.com/terms/, updated 2026-01-07): the spiders/robots/crawlers/data-mining ban; *"The Service is available for your **personal, noncommercial use**"*; and *"Build or support… products or services **in competition with ClassDojo**, or access the ClassDojo Service to build a product using similar ideas, features, functions, interface, or graphics."* **P12's "most hostile overall" verdict is correct.** |
| **ParentSquare's terms run against the SCHOOL** | **PARTIALLY CONFIRMED — P12 overstates it.** True: *"These Terms of Use form a part of a legal agreement between ParentSquare, Inc. and **your school, district, or other organization (your 'District')**."* And the permissions line is verbatim. **But "You" throughout is the individual user, and the document binds them directly:** *"If you do not agree to these Terms of Use, **you are not authorized to use** the Subscription Services."* The accurate statement: **the agreement is with the District, and the parent is personally bound under it.** P12's operational point — that a violation notice lands on the parent's school, a worse failure mode than one landing on us — survives; the "'You' is the district" framing does not. **The no-anti-bot finding is CONFIRMED** (zero hits for robot/spider/crawl/scrape/automated/data-mining; only the email-harvesting bullet). |
| **Blackbaud's AUP runs against the school** | **SUBSTANTIALLY CONFIRMED, with a caveat.** The AUP **never expressly defines "You"** — but every operative use is unmistakably the institution (*"You will not, and will not allow or authorize **Your Users**…"*, *"**You** agree to post and maintain **Your own privacy policy**"*). The definitional sentence lives in the master subscription agreement, not the AUP, so **the AUP alone will not carry the point.** No anti-bot clause either. |
| **GameChanger names the pattern** | **EXISTS, verbatim** (gc.com/terms §3.2): *"may not **share it with a third party service so they can access your Account**."* **Add, because it strengthens P12's own case:** the same ToS separately bans *"access or use the Services by means of any automated program, expert system, electronic agent or bot"* and *"engage… in any **scraping**… of the data or information on the Services for commercial purposes."* |
| **BAND's "not means for continuous contact" clause** | **EXISTS, verbatim — but in the WRONG DOCUMENT.** It is in BAND's **Activity Policy** ("Activity Policy_20250929," https://www.band.us/policy/operating), under "Safe BAND" — **not the Terms of Use**, which were pulled and grepped and do not contain it. Re-cite. *(Confidence note: band.us serves a JS-only shell to plain fetchers; this was captured with a rendered browser. A second verifier using curl could not reach it at all.)* |
| **Jumbula's ToS is genuinely permissive (no anti-bot clause)** | **PROBABLY TRUE, LOW CONFIDENCE — do not ship as verified.** A rendered-browser pass found a ~2,000-word, six-section ToS (updated 2026-01-01) with **zero hits** for robot/spider/crawl/scrape/automated/data-mining/harvest/bot. **But a second pass could not reach the page at all** (Cloudflare 403 to non-browser clients; the JS-rendered page yields ~900 characters of extractable text), and the footer's "Service Agreements" link 404s. **A NEGATIVE claim — "this contract contains no such clause" — is the hardest kind to verify and the easiest to get wrong.** Jumbula is already P12's only UNKNOWN row; do not let a shaky negative make its ToS the argument for choosing it. |

---

## Summary of required edits to P12

**Must fix before this drives a decision:**
1. **ParentSquare's citation** — the help center is login-gated; re-source or date-stamp an
   authenticated capture. It is a strategy-killing verdict on an uncheckable source.
2. **CASA self-scan date** — May 2024 → **between 2026-05-20 and 2026-07-01**; delete the
   "self scanning process is deprecated" quote, which does not exist. Cite ADA, not Google's stale FAQ.
3. **PowerSchool URL** — `/pt/latest/` 404s; use `/pssis-student-parent/latest/email-notifications`.
4. **Drop "Google-named preferred partner"** for TAC Security — that is TAC's own copy; Google names none.
5. **Replace the "all body-reading scopes are restricted" rule** with the scope list. `gmail.metadata`
   is restricted and reads no body; `gmail.addons.current.message.readonly` reads content and is only
   sensitive. Conclusion about `gmail.modify` is unaffected.
6. **Seesaw ToS cite** → **End User Terms §2.2(c)**. **BAND cite** → **Activity Policy**, not ToS.
7. **Brightwheel row** — invert the framing; the provider is locked out, the guardian controls.
8. **Gmail forwarding** — the destination gets the link, but the **source user must still return and
   click Save Changes**. Not a collapsed step. Add the compromise-banner design requirement.

**Should add, because they strengthen the report:**
9. The unverified-app cap **disables Google sign-in** on exhaustion — and **verification lifts it**.
10. The CASA assurance level **ratchets up and never comes back down**.
11. The security-assessment trigger is **server-side storage or transmission** of restricted-scope data.
12. ClassDojo's app-kills-email exclusivity belongs **in the ClassDojo matrix row**, as a verdict driver.
13. Infinite Campus has **no additional-notification-email field at all** — stronger than "district-gated."
14. Seesaw's 10-family-account path is a **documented workaround**; soften BLOCKED accordingly.
15. Brightwheel Daily Reports **exclude messages and paperwork** — a real coverage hole.
16. Illinois SOPPA §26(2) exempts **four** categories and **does not apply to nonpublic schools**.
17. ParentSquare's terms **do bind the parent personally**, even though the agreement is with the District.

**Reduce confidence on:** Jumbula's "no anti-bot clause" (an unverified negative on a bot-blocked page).

---

## Coverage limits of this verification

- **ParentSquare's help center could not be reached** by any method without an account. Its matrix row
  and its content-in-body cell remain unverified.
- **BAND and Jumbula** required a rendered browser; one pass reached them and a second could not.
  Treat both as low-confidence, and the Jumbula negative especially so.
- **Seesaw per-event email body content and ClassDojo private-chat email body content** remain
  genuinely undetermined in vendor documentation. P12 was right to mark them so; I could not close them.
- **NY Ed. Law §2-d** has a single source (nysenate.gov); no corroborating fetch succeeded.
- The **existing kills not spot-checked** in this pass (roughly a dozen, mostly in P4, P6 and P9's
  weak-signal sections) were read but not independently re-traced. Given a 25% error rate in the
  sample I did re-trace, **a second pass over the remainder is warranted** before the appendix is
  treated as final.

---

# ═══════════════════════════════════════════
# SECOND PASS (2026-08-22) — the remaining kills, re-traced
# ═══════════════════════════════════════════

The first pass found a **25% error rate** in the kills it re-traced, so the ~12 kills it had *not*
independently re-traced were re-traced too, along with the sources collectors had explicitly flagged
for a verifier. That was the right call: **three more false kills surfaced**, one of them the
best-documented statistic in its whole domain.

**Running total across both passes: 22 kills re-traced, 6 FALSE KILLS overturned (27%).** A fleet
kill is now demonstrably *less* reliable than a coin flip on the question "does an origin exist" —
though it remains highly reliable on the question that actually matters, "is the circulating number
usable." Almost every false kill is a case where a **real study exists and the circulating number
misstates it**, which the collectors correctly refused to print. The verdicts were sound; the
*reasons* were often wrong, and a wrong reason published in an appendix is a falsifiable claim we
would have to retract.

## SP-1 to SP-3 — FALSE KILLS (round two)

### SP-1. Harris Poll / Good Sports "18% of parents took on debt for youth sports" — **FALSE KILL. The best-sourced number in its domain.**
P4 threw this out alongside LendingTree's 79%, reasoning that "a 4× discrepancy between two vendor
polls means neither is usable." **The discrepancy is denominator and vintage, not contradiction**, and
the Harris figure is exceptionally well documented:
- **The Harris Poll for Good Sports, "Cost of Sports Study," fielded Oct 16–18 2024**, n=741 parents
  of minors; **the 18% base is the 688 whose children ever played a sport**; weighted, **±4.2pp**.
- **Exact question wording is published** — *"I have taken on debt (e.g., used a credit card I
  couldn't pay off immediately, taken out a loan, used a line of credit) to afford to pay for my
  child(ren) to play sports."*
- http://www.goodsports.org/assets/Good-Sports_Key-Findings-Guide_FINAL.pdf
- **Verdict: fully usable — promote it into findings.** Caveat only that sponsor Good Sports itself
  strips the qualifier in its 2025 white paper, relabelling 18% as "of surveyed parents" with no
  methodology section. Cite the Key Findings Guide, not the white paper.

### SP-2. TeamSnap "24 million users" — **FALSE KILL on origin; stale by five years**
P4 called it "no origin… pure aggregator artifact." It was **TeamSnap's own homepage copy from Aug
2021 to Feb 2022**: *"More than 24 million people and 3 million teams, clubs, leagues and
associations rely on TeamSnap."*
- Their own timeline: 20M (2019) → 22M (2020) → 23M (Dec 2020) → **25M (Apr 2021 Waud Capital PR)** →
  **24M (homepage, Aug 2021–Feb 2022)** → 25M (Feb 2023) → **30M (current, teamsnap.com/about)**.
  The series is non-monotonic, which is itself a sign the vendor is not counting consistently.
- **The qualifier that matters more than the number:** TeamSnap's Feb-2026 PR calls 30M a
  **"lifetime platform milestone"** — cumulative people ever served — while separately reporting
  **2 million daily active users.** A **15× gap.** "Users" is the union of coaches, admins, players
  and parents. **Never cite any TeamSnap headline as an active-user count.**

### SP-3. Ewing & Seefeldt (Michigan State) youth-sports attrition research — **FALSE KILL of the underlying study**
P4 killed "70% drop out by 13" as tracing to "no defensible origin." The *number* is dead (see SP-4),
but a large, real, retrievable study was discarded with it:
- **Ewing & Seefeldt (1989), *Participation and Attrition Patterns in American Agency-Sponsored and
  Interscholastic Sports*, Institute for the Study of Youth Sports, Michigan State University**,
  published in Seefeldt et al. (1993) for the Carnegie Council on Adolescent Development.
  **Full text free: https://files.eric.ed.gov/fulltext/ED360267.pdf (ERIC ED360267).**
- **n = 26,000 youth aged 10–18**; the attrition analysis covers **~8,000 youth** (51% girls) across
  17 regional sites. Funded by the Athletic Footwear Council of the SGMA.
- Nice 30-year corroboration of the modern replacement: it found dropouts had played **3.2 years
  (male) / 2.5 (female)** before quitting — bracketing Aspen's 2.9.

## SP-4 to SP-9 — PARTIALS (origin real, number corrupted)

### SP-4. "70% of kids quit sports by 13" — the true value is **35%, ages 11–18**
- **The laundering event is documented on the record.** Washington Post, Julianna W. Miner,
  2016-06-01, headlined *"Why 70 percent of kids quit sports by age 13,"* opening: *"According to a
  poll from the National Alliance for Youth Sports…"* The hyperlink behind "National Alliance for
  Youth Sports" points to **`https://www.nays.org` — the bare homepage.** No study, no page, no date,
  no n. **NAYS has never published such a poll**; a Wayback sweep of the domain finds nothing.
- **What the real MSU study says, verbatim:** *"The attrition rate for youth between the ages of 11
  and 18 was reported to be **35%**… Gould (1987) synthesized several studies… and found that the
  average attrition rate was also 35%. There was considerable variance… varying from **22 to 59%**."*
- **Where "70" probably came from:** the same report notes ~42% of 10-year-olds vs 12.0% of
  18-year-olds on agency-sponsored teams — a **71% relative decline**. Four qualifiers stripped: it
  is the report's explicitly cherry-picked *"most dramatic display"* (baseball and swimming), it is
  ages **10→18** not "by 13," it is **agency-sponsored teams only** (excluding school sports), and it
  is a **cross-sectional participation gradient, not longitudinal dropout.**
- **Defensible replacement, with its own qualifiers intact:** Aspen Institute / Utah State **2019
  National Youth Sport Survey**, n=1,032 youth-sports parents — average age of last regular
  participation **10.5**, average length of participation **2.9 years**. ⚠️ Three qualifiers to keep:
  the base is **parents of kids already in sports** (not all children); the figures are **per sport**
  (a child quits soccer at 9.1 and still plays basketball to 11.2 — Project Play's own prose flattens
  a per-sport table); and it is **2019 and has not been refreshed** — the current Aspen/Utah State
  wave (n=1,848, fielded Nov 5–Dec 19 2024) **reports no quit-age figure at all.**

### SP-5. LendingTree "79% went into debt" vs Harris "18%" — **not a contradiction; the 79% is unusable**
- LendingTree: n=1,006 parents, Qualtrics, **fielded April 8–15 2021**; question wording **not
  published**. **Stripped qualifier: "competitive."** The base provably is not all parents — the same
  study reports only 70% have a child in a competitive activity, so 79% cannot sit on a 100% base.
  "Have *been* in debt" is lifetime; currently-in-debt is 58%.
- **LendingTree's own later wave re-measures it at 42%** (April 2023, QuestionPro, n=2,000); 2019 was
  62%. **79% is a one-off 2021 stimulus-era spike.** Note LendingTree's own `<title>` tag drops
  "Competitive" — **the publisher starts the laundering.**
- **Net: use Harris 18% (SP-1). Use LendingTree 79% only with "competitive," "ever," "April 2021" and
  the 42% re-measurement attached — which in practice means don't.**

### SP-6. "~50 school days off excluding summer" — true range **30–38, median ~34**
- Real research does exist: **Center for American Progress, *Workin' 9 to 5* (2016)** — *"the largest
  school districts shut their doors for an average of **29 days**"*, NYC 33, LA 34.
- Independently counted from official **2025-26** calendars (teacher workdays counted as days off,
  since students do not attend): **NYC 34, LAUSD 35, Chicago 33, Houston 32, Miami-Dade 32, Fairfax
  38.** Arithmetic check: 261 weekdays − ~48 summer weekdays − 180 instructional = **33**. The NYC and
  LA counts land within one day of CAP's, independently validating the method.
- P3's instinct that the circulating 50 was "probably wrong" and "too high" was correct; it is high by
  roughly 50%.

### SP-7. Edison "57% use voice commands daily" — base swapped, and **Edison itself may be the source of the corruption**
- True: **57% of *voice-command users*** use voice commands daily. **NPR/Edison Research, *The Smart
  Audio Report*, Spring 2022, fielded Feb 28–Apr 18 2022**, n=1,190 smart-speaker owners + 560
  voice-assistant users on other devices + 584 non-users, **US adults 18+**. Question: "How often do
  you use voice commands?", base "Ever use voice-operated personal assistants." The 2020 wave read 52%.
- **The tell:** Edison's own solution page says *"Fifty-seven percent of **Americans** use voice
  commands of some type daily"* — **internally impossible**, since Edison also reports only 62% of
  Americans use a voice assistant at all. **The base swap may originate with the publisher, not the
  aggregators.** Cite the report, never the marketing page.
- **Separately confirmed as genuinely originless:** the "24% cooking / 26% chores / 38% relaxing"
  triple. The full Smart Audio Report text was enumerated and **contains no context-of-use or
  in-home-location question at all** — so the plausible "corrupted Edison question" hypothesis is
  **false**. SerpWatch presents the triple with no inline citation; the only link in that paragraph is
  an unrelated affiliate link. This is **attribution-by-adjacency**: a credible bibliography lending
  authority to numbers none of those sources contain. These remain the numbers this brief most wanted.

### SP-8. Onboarding benchmarks — **the cleanest four-move laundering chain in the corpus**
- **"19.2% complete onboarding"** — real origin **Userpilot, Product Metrics Benchmark Report 2024**,
  n=**547 B2B SaaS companies**, metric = onboarding **checklist** completion. **Stripped: the median
  is 10.1%.** Quoting the mean nearly doubles the typical case, and it is B2B SaaS, not "users."
- **"8.4% global average completion after 30 days"** — real origin **Airship, *Mobile Lifecycle
  Benchmarks: Activation***, whose own definition is verbatim: *"Day 30 Activation Rate — This
  measures how many customers **return to the app** on the 30th day after download."* **That is
  30-day retention, relabelled as onboarding completion.** Then three further moves stack on top: the
  unit is **~2.6 billion DEVICES counted as people**; the **fielding window (January–June 2023) is
  stripped** and it is presented as current; and **Airship's own headline is 7–8%, not 8.4%.**
- **"Top performers 40–50%"** — **genuinely originless.** Airship's real best-category top decile is
  **24%** (finance). Appears back-formed from an unrelated Userpilot sentence.
- **This single bullet contains all four laundering moves at once** and is the best teaching example
  in the appendix.

### SP-9. "CASA costs $15,000+" — a **real Google-published fee**, for a **superseded regime**
Archived from Google's own OAuth API verification FAQ (`support.google.com/cloud/answer/9110914`):
- **2018-11-22 and 2020-06-04:** *"Assessments will be conducted by a Google-designated third-party
  assessor, **may cost between $15,000 and $75,000 (or more)** depending on the complexity of the
  application, and will be payable by the developer."*
- **2021-12-02 → 2022-10-27** (Google *lowered* it): *"typically **varies between $10,000 - $75,000
  (or more)**… **smaller applications may see costs at a lower threshold of $4,500.**"*
- **Removal pins tighter than P12 assumed:** last snapshot with fee language **2022-10-27**; first
  without it **2022-11-11** — which is also the first CASA mention. The window is **late Oct–early Nov
  2022**, not June 2022–June 2023.
- **P12's WEAK SIGNAL overstates the provenance the other way:** the HN origin is a **2018-10-09
  comment quoting Google's own FAQ**, not developer-reported pricing, and the Ask HN thread
  (2020-10-09) has **5 points and 0 comments**. "Developers reported this" is not supportable.
- **Fair restatement:** $15k–$75k+ was the fee for the **pre-CASA restricted-scope regime**. CASA is
  tiered and cheaper. Both P12 and this verifier reach the same practical conclusion; the history is
  now precise enough to publish.

### SP-10. Other corrections from the second pass
- **Astute Analytica "$59.9B by 2033"** — accurately quoted but **global**, a **forecast** (2025–2033,
  from a $7.08B 2024 base at 26.80% CAGR), and **no methodology exists**: `/research-methodology` and
  `/methodology` both 404, and the release discloses no sample, no sources, no model. Rigour is
  signalled by page count (395 pages, 100 figures) rather than method. **Same document as the 153.5M
  figure — killing the Astute citation kills both.**
- **Klook "91% of global travelers"** — real (Travel Pulse 2026, 2026-02-11, n=11,000, 20 markets).
  Four qualifiers stripped: the population is **Millennials + Gen Z who are Klook's own core users**
  (an experiences-booking platform's customers, not "global travelers"); *"widely used"* became
  *"rely on"*; "AI" became "AI travel planners"; and **Klook's own caveat — "its role remains largely
  functional" — was deleted.** Their sister release ranks **AI suggestions last (33%)** behind reviews
  (58%) and friends (49%). **Fielding dates and panel provider were disclosed in 2025 and dropped in
  2026.** The US is ~1 of 20 markets (~5%), so any US-labelled version is unsupported.
- **"4.5 subscriptions"** — real origin **Deloitte *Digital Media Trends***, and the value is **four,
  not 4.5**: *"90% of US households have a paid SVOD service (and an average of four services)"*
  (2026 edition, fielded Oct–Nov 2025, n=3,575). Three losses: category (**streaming video → all
  subscriptions**), base (**SVOD-subscribing households → all consumers**), and value drift 4 → 4.5.
  The companion "8.2 subscriptions / $118 per month" remains **fully originless** — almost certainly
  two unrelated orphans stitched together. Real comparators: C+R Research **$219/mo actual vs $86
  estimated** (2022, n=1,000); West Monroe **$273/mo** (2021, n=2,500); Bango **5.4 subscriptions**
  (2025, n=5,000). ⚠️ **The widely circulated "$219/$133" pair is C+R, not West Monroe** — that
  misattribution is itself in circulation.
- **Retrospec "96%"** — n=1,000 US parents **is** disclosed (P6 said it was not); everything else is
  absent — no fielding window, no panel vendor (checked for OnePoll, Talker, SWNS, Pollfish, Prolific,
  Qualtrics, Censuswide, Dynata: zero hits), no weighting, no MoE, no wording. **Stripped qualifier is
  Retrospec's own:** the measured item is *"improves their mood **the same day**"*; the headline says
  *"instantly."* Distributed via **Stacker Studio brand-content syndication**, not a wire. Kill stands.
- **"Districts use 3–7 apps"** — killed correctly, but note the real study says the **opposite
  direction**: the modal parent is at **7–9 apps per child**, and district leaders report **10–15**.
  The circulating number **understates** the only real measurement. Also: the Cornerstone report
  **contradicts itself on n** (executive summary "50 curriculum leaders" vs methodology body **58**),
  and teachers are only ever "over 100" with no exact n. Cite it with care.
- **"60% of parents miss important events"** — **definitively killed.** Full text extraction of the
  Cornerstone PDF: **"60%" does not appear anywhere**, and neither do "miss," "event," "deadline,"
  "overlook" or "forget" — zero hits across 22 pages. The complete percentage inventory contains no 60
  and no near-miss to have been rounded. It is not a distortion of that report; it is unrelated to it.
- **Vendor corrections confirmed 2/2.** Blue Sombrero **is** Stack Sports (acquired from DICK'S
  2019-08-22), not NBC Sports Next — **and it no longer exists as a product**: `bluesombrero.com`
  301-redirects to sportsconnect.com. Bloomz was **not** acquired by ParentSquare (that was **Remind,
  2023-11-29**). ⚠️ Search trap: "BloomZ Inc." (ticker BLMZ) is an unrelated Japanese voice-acting
  company. Bloomz's "26,000 schools" has no origin — its actual historical claim was **"over 30,000
  schools,"** unsourced and static across snapshots — and **Bloomz has since removed the aggregate
  figure entirely**, which is itself the tell.
- **"14,000 AI startups / 3,800 shutdowns / 40% failure"** — killed, and the **arithmetic is the
  tell**: 3,800/14,000 = 27.1% and 1,800/14,000 = 12.9%, summing to **exactly 40%** — but numerator
  and denominator are **different cohorts** (14,000 founded in 2024 globally vs shutdowns of any
  vintage, no geography). 40% is the design goal of the arithmetic, not its output. Contradicted by an
  order of magnitude: **Carta recorded 966 startup shutdowns in all of 2024 across every sector.** The
  post also labels its own central case study *"(made-up name, real pattern)."*

## SP-11 — SOURCES RETRIEVED that collectors flagged for a verifier

These were flagged as "real, valuable, could not fetch." All eight were retrieved. Several change
what the program can claim.

| Source | What it actually says |
|---|---|
| **Wisconsin shared custody** (M4 flagged) | **Confirmed single-state court-record data — never present as a US rate.** Cancian, Meyer, Brown & Cook, *Demography* 51(4) (2014), Wisconsin court records, divorces 1988–2008; and Meyer, Cancian & Cook, *Family Court Review* 55(4) (2017): for WI divorces filed 2010, **50% shared (35% equal, 15% unequal) vs 12% in 1989 (5% equal, 7% unequal)**. The famous "5% → 35%" maps exactly onto **equal-shared, Wisconsin, 1989→2010**. **The national companion exists and should be used instead:** Meyer, Carlson & Alam, *Demographic Research* 46(38) (2022), **8 waves of the CPS Child Support Supplement, n=18,757** — national shared physical custody after divorce **13% (pre-1985) → 34% (2010–14)**. That paper states Wisconsin runs **9.4 points ahead** of the nation. |
| **Census custodial-parents series** (M4 flagged) | Current edition found: **"Custodial Parents and Their Child Support: 2022," P60-285, published 2025-08-12**, from the **Child Support Supplement to the April 2023 CPS**. **22.2 million children under 21 have one parent living outside the household — 27.1% of all children under 21 in families; 13.9 million custodial parents (78.2% mothers).** Note the title changed (no longer "Custodial Mothers and Fathers"), and **CPS-CSS does not measure legal custody.** Confirms p60-281 is a different report. |
| **Child Trends, July 2026** (P12's "highest-value manual retrieval") | Retrieved. **n=1,025 parents of children 5–18, NORC AmeriSpeak probability panel, fielded December 2025**, weighted to CPS. **78.3% seek information about their child's education at least monthly; 2 in 3 use communications from their school — the most-used source by a wide margin; 43% name school communications as the source they trust MOST (more than double any other); 42.9% name social media as the source they trust LEAST.** This is a genuinely strong Tier B source and it was worth chasing. |
| **CDT student-privacy series** (P12's "second-highest-value") | Retrieved — **and the hoped-for number is not in it.** "Hand in Hand" (Oct 2025), n=1,018 parents of grades 6–12 (+1,030 students, 806 teachers), fielded Jun–Aug 2025. **Zero mentions of third parties, vendors, outside companies, selling, or sharing data with third parties.** The nearest usable figure is **69% of parents concerned about the privacy and security of student data their child's school collects and stores** — which must be described as **school-held data, not third-party sharing.** **P12 #51's negative finding ("no Tier A/B survey measures either construct") therefore SURVIVES and is strengthened.** |
| **ACA 2024 National Economic Impact Study** | Confirmed: ACA with **University of Michigan Economic Growth Institute**, released 2024-06-03 on 2023 data; **>20,000 records plus survey data from 1,137 camp operations**; **$70B economic impact, $23B labor income, 986,428 workers**; first such study since 1982. **But it supplies NO camper count** — and the only camper number in ACA's own release is the boilerplate *"annually serve 26 million campers."* **So the "26 million" this program is trying to replace is ACA's own unsourced boilerplate, and this study does not substantiate it.** Full report is member-gated. |
| **The defensible camp-participation replacement** | **Gallup / NSLA / ACA, published 2024-07-26: 30 million youth engaged in summer opportunities = 55% of K-12 youth**; 48% of K-12 parents wished their child could have participated but could not; **only 11 of 25 million low-income students accessed summer programs.** Narrower and better documented alternative: **AA3PM — ~12 million children (23%) took part in a structured summer experience in 2024.** |
| **America After 3PM 5th ed.** | Nailed down. **n=30,515 US parents/guardians of a school-age child**, ≥200 interviews in all 50 states + DC; subset of 14,663 got follow-ups; **fielded Jan 31–Apr 21 2025**; non-probability opt-in online panels plus supplementary phone; English and Spanish; weighted to ACS and NCES; **MoE <1%**. **⚠️ Edge Research is NOT named as the AA3PM fielding partner** — it appears only for a separate *provider* survey (Oct 27–Dec 22 2025). **P4 #15 and P3 #6 attribute AA3PM to Edge Research; that attribution is unsupported and should be dropped.** Headlines: parents of **29.6M children** would enroll in afterschool; only **6.95M (13%)** are enrolled — **22.6M unmet demand**. Summer companion: **24.6M want a structured summer experience, 51% (12,598,498 children) missing out.** |
| **Nah (2004) tolerable waiting time** (P9 flagged unverifiable) | **Verified, including the 38 seconds.** *Behaviour & Information Technology* 23(3):153–163; free predecessor at AMCIS 2003 paper 285. **Method: lab experiment, 70 undergraduate MIS students** (36 control / 34 treatment). First broken link: **mean 13s (median 9s) without feedback vs mean 37.6s (median 22.6s) with feedback**; second link 4s vs 17s; third 3.3s vs 6.7s — **tolerance collapses fast once users learn loads can fail.** Conclusion verbatim: *"the tolerable waiting time for information retrieval is approximately 2 seconds."* **The popular "~2s tolerable, ~38s with feedback" conflates two quantities** — 2s is the modal/settled tolerance, 38s is the *mean first-encounter* wait with a progress indicator, from n=34 students in 2003. P9 was right not to assert it; it can now be cited precisely. |

## SP-12 — NEWLY KILLED in the second pass

### Digital Promise "74% of US districts use more than 26 edtech tools" — **KILL as stated (n=40, self-selected)**
P12 listed this in WEAK SIGNAL as "tempting because it is quoted inside PowerSchool's SEC 10-K" and
untraced. It is now traced, and it should not be promoted:
- Origin is an **infographic, not a report**: *"The State of Data Interoperability in Public
  Education,"* Digital Promise, 2017-08-03. Figures are stated as claimed (74%; 17% use more than 100;
  only 33% have linked more than ½ of tools to their SIS).
- **Method, verbatim: "This infographic was informed by a survey of the Digital Promise League of
  Innovative Schools' Data Interoperability Working Group. The 40 respondents hold leadership roles in
  district technology across 40 U.S. public school districts."**
- **n = 40**, a self-selected working group of CTOs from a network explicitly branded *"Innovative,"*
  self-selected *again* into a data-interoperability working group — i.e. the sub-population most
  likely to have many tools and to care about integrating them. **Presenting this as "74% of US
  districts," as the 10-K framing implies, overstates it substantially.** Nine years old.
- **Verdict: do not promote. If used at all: "in a 2017 survey of 40 district technology leaders in
  Digital Promise's League of Innovative Schools…"** — at which point it is not worth the sentence.

## SP-13 — Method limits of the second pass

- **The WebSearch budget (200/200) was exhausted before the second pass began.** All of it is
  publisher-site and archive verification by direct fetch — which is the *stronger* test for "does an
  origin exist," but it means the **aggregator-enumeration column is less complete** than the origin
  findings for the TeamSnap, Klook, subscription and LendingTree items. The origin verdicts are solid;
  the "who repeats it" lists are partial.
- **archive.org went "Temporarily Offline"** partway through, after the TeamSnap and Google fee
  snapshots were captured but before some aggregator sweeps.
- **One item deserves a re-run with fresh search budget:** the "24% cooking / 26% chores / 38%
  relaxing" triple. It is killed on all evidence reachable, but it has the texture of a real
  early-2010s Google/Northstar mobile-voice question, and it is the single set of numbers this brief
  most wants. A false kill there would cost us the best context-of-use data in the study.
- Also unfinished: mapping how widely the **LendingTree 79%** circulates stripped of "competitive."
