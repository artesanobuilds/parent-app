# V7 — Re-trace of the Un-checked Kills + FINAL CONSOLIDATED KILL LIST

Verifier V7. Run 2026-08-21. Scope: every killed / "unverifiable" statistic in the V6 kill list
(K1–K44 plus the Tier-3 absences) that **V6 did not independently re-trace**.

## What V6 had already re-traced (NOT redone here)

V6 independently traced 14 items: K1 (Pew 37M), K2 (BLS booking timing), K3 (Appcues 15%),
K4 (Baymard 4–6%), K5 ($150B missed appointments), K6 (screen-time guilt), K26 (Juniper 8.4bn →
**overturned**), K27 (PwC 71%), K28 (FTA 92%), K29 (Custody X Change 35%), K30 (30% no-show),
K31 (Gen Z $377 → **overturned on trace**), K32 (ACA 26M), K33 (ACA 14,000 camps → **overturned**),
plus its own new kills K16/K17/K18 and the CK-1…CK-7 correct-and-keeps (K35–K41), and K44 inside
Job 2. Those verdicts are carried forward unchanged below and attributed to V6.

## What V7 re-traced (18 items)

K7, K8, K9, K10, K11, K12*, K13, K14, K15, K19, K20, K21, K22, K23, K24, K25, K34, K42.
(*K12 was already settled against the origin PDF by V6/V2; V7 accepted it rather than re-fetching.)

**Method.** Yahoo SERP scraping with `RU=` link extraction (the only search endpoint that survives
in this environment; it rate-limits hard — a 45–90s backoff between batches was required), direct
origin fetches with a de-tagged HTML reader, and Wayback CDX enumeration for deleted vendor pages.
The session's WebSearch budget (200 calls) was already exhausted by earlier agents, so WebSearch was
unavailable to V7; all searching was scripted. Coverage limits are stated explicitly at the end.

---

# PART 1 — V7 VERDICTS

## 1A. OVERTURNED / RECLASSIFIED (these change what the report may print)

### K8 — "57% of voice search users use voice commands daily" → **PARTIAL, not fabricated**
V6/P8 listed this in Tier 1 as "no publisher, no n, no date," with a *suspicion* that it corrupts
Edison. **V7 confirmed the origin verbatim.**
- **Origin:** NPR / Edison Research, *The Smart Audio Report 2022*, press release **2022-06-16**.
  Verbatim: *"In 2022, **57% of voice command users use voice commands daily**."*
- **Method (disclosed in full):** national online survey of **1,190 US adults 18+ who own a smart
  speaker, 560 US adults 18+ who use voice assistants on other devices, and 584 US adults 18+ who do
  not use voice assistants**; fielded **2/28/2022–4/18/2022**; plus Zoom in-depth interviews and
  follow-ups with 2017 ethnography participants.
- **TRUE VALUE: 57% of voice-*command* users use voice commands daily (US adults 18+, spring 2022).**
- **Corruption mode:** BASE SWAP ("voice command users" → "voice search users") + DATE STRIP
  (reprinted as 2025/2026). The number itself is real and Tier B.
- URL: https://www.edisonresearch.com/smart-audio-report-2022-from-npr-and-edison-research/
- **Move K8 from Tier 1 (fabricated) to Tier 2 (laundered).** Citing Edison for a number Edison did
  publish, under the wrong base, is a different and lesser sin than fabrication — and the appendix
  must not accuse a real publisher of the wrong offence.

### K10 — "24% / 26% / 38% use voice while cooking / doing chores / relaxing" → **KILL UPHELD on those numbers, but the measurement EXISTS and the report wrongly declared it absent**
V6 flagged this as *"the context-of-use numbers this study most wanted, and they are entirely
unsourced."* The exact triple 24/26/38 has no origin — that stands. **But a real, dated context-of-use
measurement does exist**, and the report should stop saying no one has measured it.
- **Origin:** PwC, *Consumer Intelligence Series: Prepare for the voice revolution*, released
  **2018-04-30** (n=1,000 US, 18–64, online panel — the same study behind the PwC "71%").
- **TRUE VALUES (smart-speaker voice-assistant users):** **65% while cooking, 62% while
  multitasking, 57% while watching TV, 29% while working, 0% while driving.** On **smartphones**,
  **40% while driving.** Overall, **74% regularly use voice technology in the home**.
- Also from the same study, directly relevant to this brief and currently unused: voice adoption is
  *"being driven by younger consumers, **households with children**, and households with incomes over
  $100,000"* — and yet **18–24s use voice assistants LESS often** than 25–49s (59% vs 65% daily), the
  stated reason being that using voice in public *"just looks weird."* That is a real, sourced
  counterweight to any "Gen Z will talk to it" assumption.
- PwC has retired its own page and PDF (confirmed by V6). The surviving records are Voicebot.ai's
  chart write-up (2018-05-02, https://voicebot.ai/2018/05/02/cooking-multitasking-and-television-top-the-list-of-voice-assistant-activity-pairings/)
  and TechCrunch (2018-04-30, https://techcrunch.com/2018/04/30/younger-consumers-adopt-voice-technology-faster-but-use-voice-assistants-less/).
- **How to use it:** cite as *"PwC 2018, n=1,000 US 18–64, base = voice-assistant users, publisher's
  own page retired; retrieved via secondary reporting."* Eight years old. Do not present as current.
- **Corruption note:** the circulating "38%" is plausibly a scramble of PwC's *"38% said they
  wouldn't want something listening in on their life all the time"* — a privacy figure, not a
  context-of-use figure. Stated as a hypothesis, not a finding.

### K20 — "153.5 million US voice assistant users in 2025" (eMarketer) → **PARTIAL / KILL SOFTENED**
V6 killed this as *"eMarketer publishes 139.8M (2022) and 168.2M (2029) and **no 2025 point** — a
plausible interpolation passed off as a published estimate."* **That reasoning does not hold.**
eMarketer runs this as an **annual, per-year forecast series with a new vintage each year**, and V7
found a different vintage with different endpoints:
- **EMARKETER, *Voice Assistant User Forecast 2024*, Jacob Bourne, published 2024-08-21.** Key Stat,
  verbatim: *"US voice assistant users will grow from **145.1 million in 2023** to **170.3 million in
  2028**, representing a CAGR of **3.3%**."*
  https://www.emarketer.com/content/voice-assistant-user-forecast-2024
- On that curve, 2025 falls at **~154.9M** — i.e. **153.5M sits essentially on eMarketer's own
  published trajectory**, and the underlying per-year datapoint almost certainly exists behind the
  paywall. V6 compared against the *2025* vintage and concluded no 2025 point exists anywhere.
- **Corrected verdict: UNVERIFIABLE AT ORIGIN (charts paywalled), not fabricated.** The real defect
  is FORECAST→MEASUREMENT: whatever the true number, it is a model output, of **individuals of any
  age using a voice assistant at least monthly on any device, de-duplicated across devices** (V6's
  CK-5 definition), not a count of anything measured. **Still not citable** — we cannot see it — but
  the appendix must not say "eMarketer never published a 2025 point."
- Substantively useful and free: the same report's framing is *"adoption continues to grow, but the
  pace has slowed. **Gen Z and seniors are key growth drivers.**"*

### K42 — Klook "91% of global travelers rely on AI travel planners" → **PARTIAL, origin confirmed**
- **Origin:** Klook *Travel Pulse* survey, **4th edition, 2026** — https://www.klook.com/newsroom/travelpulse-2026-biggerbudgets-boldertrips/
- **Method as stated:** **11,000 consumers** across **20 markets** — Hong Kong, Taiwan, Chinese
  Mainland, Japan, Korea, Singapore, Malaysia, Vietnam, Thailand, Philippines, Indonesia, Australia,
  New Zealand, India, Germany, France, Spain, Italy, UK, USA. Klook states the research covers
  *"Millennials and Gen Z **which makes up Klook's core user base**."*
- **TRUE STATEMENT:** AI is *"now widely used by 91% of global travelers"* — and Klook itself
  immediately qualifies: *"its role remains largely **functional**. Most common use cases are
  trip-related tasks such as research, translation, organizing itineraries, and budget management."*
- **Three corruptions:** (1) GLOBAL→US — the sample is heavily APAC-weighted, the US is 1 of 20
  markets with no disclosed cell size; (2) POPULATION — it is a travel-booking vendor's **own
  Millennial/Gen Z customer base**, not travelers generally; (3) VERB — "used AI for trip tasks"
  becomes "**rely on** AI travel planners." **Kill stands for US use.**

## 1B. KILLS UPHELD, AND STRENGTHENED

### K13 — "70% of kids drop out of sports by 13" → **UPHELD, now with a named institutional debunk and a real replacement number**
P4 cited a Tucson.com column. V7 found a far stronger, more citable trace.
- **USA TODAY, Stephen Borelli, 2026-04-11 (upd. 2026-04-12)** —
  https://www.usatoday.com/story/sports/2026/04/11/youth-sports-dropout-rate-faulty-statistics/89555394007/
- Two named researchers independently traced it and found no primary source: **Marty Fox, Aspen
  Institute Sports & Society Program**, and **Joseph Janosky, Lasell University**. Janosky, verbatim:
  *"One of the most repeated statistics in youth sports may not have a clear primary source… What I
  found instead was a chain of secondary sources. Each one pointing to another. None clearly anchored
  to a transparent, verifiable study. There's a term for this: **citation drift**."* Traced back
  **~four decades**.
- **Contradicted by measurement:** CDC **Youth Risk Behavior Survey** — organized-sport participation
  among US high-school students has been **>50% consistently since 2000** (except during COVID).
- **REPLACEMENT NUMBER, citable:** **Tom Farrey, founder of Aspen's Project Play: "the average age at
  which a child quits sports is 12."** Current national participation **~55%**; Project Play's 2030
  goal is 63%.
- This is the appendix's best single exhibit: a ubiquitous statistic killed by the very institution
  (Aspen) the brief lists as Tier B, with a real number available to replace it.

### K25 — "add@cozi.com" → **UPHELD, and stronger than P12/V6 stated.** *(Highest product relevance — this one underwrites the email-forwarding architecture decision in S1/P12.)*
V6/P12 could not confirm the address exists. V7 went further: **Cozi has no inbound email-to-calendar
feature of any kind.**
- V7 read Cozi's **entire current FAQ** (https://www.cozi.com/faq/). Every mention of email is
  **outbound or identity-only**: agenda emails (daily/weekly), appointment reminders, change
  notifications, password reset, and one-account-per-email sign-in. There is no import-by-email, no
  forwarding address, no parsing feature.
- Wayback CDX enumeration of every archived `cozi.com` URL containing "email" (1,000s of snapshots,
  2007–2025) returns only campaign UTM URLs, agenda-email blog posts, account/email help pages, and
  Cloudflare email-obfuscation assets. **No forwarding endpoint at any point in Cozi's history.**
- Yahoo exact-phrase search for `"add@cozi.com"` returns **zero results**.
- **Probable propagation source identified:** `usecarly.com/blog/forward-email-to-calendar/` — i.e.
  the claim traces to **the publisher V6 killed wholesale as K18**. Two independent kills converge.
- **Decision implication:** do not model an email-forwarding funnel on a Cozi precedent. It doesn't
  exist. The competitive claim "Cozi already does add-by-email" is false.

### K15 — "Only 19.2% complete onboarding; global average 8.4% after 30 days" → **UPHELD** *(product-recommendation-bearing: this sits under P9's onboarding-simplification argument)*
- Chased both figures through the aggregator chain. `setgreet.com`'s page — V6's named carrier — **no
  longer contains either number**; its current text is entirely unsourced hedge ("in certain
  scenarios," "reportedly," "case studies demonstrate"). `digia.tech`'s onboarding-statistics post
  contains **no numbers at all**, only a gestural "according to mobile analytics platforms like
  Adjust." `semnexus.com` returned nothing on either figure.
- No Tier A/B/C publisher anywhere states either value. **KILL UPHELD.**
- **Consequence for the report:** the onboarding-weight recommendation must rest on the Nielsen
  10-second limit and the Baymard *field-count* comparison (with V6's "structurally cannot produce a
  slope" caveat and the brief's V4 correction), **never on a completion-rate slope**. No such
  benchmark exists at any tier. That absence belongs in Tier 3.

### K11 — "Districts use 3–7 apps parents must download" / "5–6 different apps" → **UPHELD, and a real sprawl anchor found that must NOT be substituted for it**
- No linked study exists; the phrasing is back-formed from Cornerstone's response buckets, as P4 said.
- **However**, a real, method-disclosed measurement of edtech sprawl does exist:
  **LearnPlatform by Instructure, *EdTech Top 40*.**
  - **2024 edition:** districts accessed an average of **2,739 distinct edtech tools annually**,
    **1,436 per month**; students used **48 unique tools/year**, educators **50**. Method: telemetry
    from the LearnPlatform Inventory Dashboard, **2023-09-01 to 2024-05-31**, **>57 billion
    engagements** across **>9,000 products**, US educational institutions.
    https://www.prnewswire.com/news-releases/new-learnplatform-by-instructure-report-finds-increases-in-more-unique-digital-tools-accessed-by-k-12-institutions-students-and-teachers-302180031.html
  - **2025/26 edition:** **2,982 distinct tools annually** (+~9% YoY); students access 1,165 and
    teachers 1,045 tools per month; students 48 unique/year (from 45), educators 50 (from 49).
    https://www.instructure.com/press-release/new-learnplatform-instructure-report-shows-k-12-districts-are-more-selective-about
  - Vendor telemetry, disclosed method → **Tier C**. Instructure's own caveat: *"based solely on
    quantitative analysis of engagement… does not reflect user sentiment, effectiveness, or utility."*
- **HARD WARNING:** this measures **district/student/teacher** tool access. It is **not** a count of
  apps a **parent** must install. Swapping it in for the killed claim would be us performing the
  laundering move ourselves. **The parent-facing per-family app count still does not exist** (the
  only parent-level number in the world remains Edsby n=125, North American, vendor-partnered).

### K24 — "Children have ~50 days off school (excluding summer) in a 180-day year" → **UPHELD, now with a Tier B denominator**
- P3's arithmetic instinct was right and can now be anchored: **Pew Research Center, 2023-09-07**,
  analysing **Education Commission of the States** data — **180 instructional days is mandated by 27
  of 38 states + DC**; the average state requirement is **179 days**; 7 states require fewer (Colorado
  lowest at 160), 4 more (Kansas 186).
  https://www.pewresearch.org/short-reads/2023/09/07/in-the-u-s-180-days-of-school-is-most-common-but-length-of-school-day-varies-by-state/
- 365 − 104 weekend days − ~180 school days ≈ **81 non-school weekdays**, of which summer is ~50–60,
  leaving **~20–30 non-summer weekday closures**. The circulating "50" is **roughly double**.
- No publisher counts non-summer closures directly. **Kill upheld; keep the ~20–30 estimate labelled
  as our own arithmetic, not a source.**

### K22 — TeamSnap "24 million users" → **UPHELD, plus a unit correction to P12 #8**
- No origin for 24M at any tier. TeamSnap's own PR Newswire release (**2025-11-18**, TeamSnap ONE
  launch) says **"19,000+ sports organizations and more than 30 million parents, players, coaches and
  administrators."**
  https://www.prnewswire.com/news-releases/teamsnap-unveils-teamsnap-one-a-next-generation-platform-poised-to-redefine-the-future-of-youth-sports-technology-302617954.html
- **Unit correction:** P12 #8 renders this as "30M parents/players/coaches." Correct — but the report
  must never let 30M read as **households or parents**; it is a mixed-role cumulative headcount, with
  **no disclosed method, no active/registered distinction, and no third-party audit.** Vendor self-
  report only.

### K23 — "8.2 subscriptions / $118 per month" vs "4.5 subscriptions" → **UPHELD, with a real (dated) origin available for the adjacent construct**
- Neither circulating figure has an origin publisher; V6's "self-contradiction is the tell" stands.
- **The real, method-disclosed study in this space:** **West Monroe**, press release, survey of
  **2,500 US consumers, June 2021**, respondents self-tallying monthly spend across **21 categories**
  (a follow-up to its 2018 wave). **$273/month average, up from $237 in 2018. 100% of respondents
  were unaware of their actual spend; 66% were off by more than $200.**
  https://www.westmonroe.com/press-releases/americans-are-spending-more-on-subscriptions-and-are-less-aware-of-spending
- **Do not swap it in as an app-subscription figure** — 21 categories includes phone, internet,
  insurance and streaming. Its *usable* finding for pricing strategy is the **systematic
  underestimation of subscription spend**, not the dollar figure. Dated 2021; flag as such.

### K19 — "Voice-AI startups raised $7B+ in Q1 2026" → **UPHELD**
- No dataset is named anywhere in the chain. Checked the one publisher that *does* publish Q1 2026
  venture data with a methodology page: **Crunchbase News** —
  https://news.crunchbase.com/venture/record-breaking-funding-ai-global-q1-2026/ — which reports
  **$242B to AI globally in Q1 2026 (80% of all global venture funding)** and **$250B to US-based
  companies**, but publishes **no voice-AI segment cut at all**. The circulating figure appears only
  on `metaintro.com`, `aiweekly.co` and `callsphere.ai` (a voice-AI vendor's own blog). **No origin.**

### K7 — "Average child attends 8–12 birthday parties per year" → **UPHELD**
- Searched for the attendance construct directly. The only survey-shaped artefacts in the space
  measure **hosting**, not attending: `talker.news` (2023-01-23, a PR-wire content mill; the page now
  502s) and the **Chuck E. Cheese "Birthday Research Center"** (published April 2026, **n=4,985
  parents of children 2–12, 20+ countries**) — a **vendor** study, **global not US**, and it measures
  simple-vs-elaborate celebration style, **not parties attended per child per year**.
- **No publisher measures parties attended per child per year.** Kill upheld; add to Tier 3.

### K9 — "20.5% of people globally use voice search" → **UPHELD, with a stated coverage limit**
- No textual origin found. The most plausible true origin is **DataReportal / GWI** (the *Digital
  20XX* series does publish a voice-search adoption rate for internet users 16–64) — but DataReportal
  publishes those figures **inside slide-deck images**, and V7 could not OCR the decks in this
  environment. The HTML of `digital-2024-global-overview-report`,
  `digital-2024-united-states-of-america` and `digital-2024-deep-dive-what-we-do-online` contains
  **zero occurrences of "voice"** in text.
- **Verdict: kill upheld at MEDIUM confidence, not high.** Per the fleet's own rule that an
  image-baked chart still counts as published, the DataReportal/GWI deck route is an **unclosed
  path**. Flag it in the appendix rather than asserting no origin exists.

### K14 — "14,000+ AI startups launched 2024, 3,800 shut down 2025 = 40% failure rate" → **UPHELD**
- Traces to a single Medium post with no methodology (V6). V7 found no dataset publisher (Crunchbase,
  CB Insights and PitchBook publish no such shutdown series). The arithmetic is also incoherent —
  3,800/14,000 = 27%, not 40% — which is itself diagnostic. Kill upheld.

### K21 — "Voice assistant market to reach $59.9B by 2033" (Astute Analytica) → **UPHELD**
- A market-sizing press release distributed via GlobeNewswire with no published methodology, no
  sample, no data source and no definition of the market boundary. This is marketing collateral for a
  paid report. Kill upheld on the same structural grounds V6 gave; V7 adds no new evidence and did
  not attempt to buy the report.

### K34 — "Over 62% of US adults use a voice assistant," dated 2025/2026 → **UPHELD; date-strip confirmed at origin**
- Verified verbatim at Edison: *"In 2022, **62% of Americans 18+** use a voice assistant on any
  device"* — NPR/Edison Research, *Smart Audio Report 2022*, released **2022-06-16**, fielded
  **2022-02-28 to 2022-04-18**, n=1,190 + 560 + 584 US adults 18+.
  https://www.edisonresearch.com/smart-audio-report-2022-from-npr-and-edison-research/
- The number is real and Tier B. **Only the year is fabricated.** Cite as 2022 or not at all.

### K12 — "60% of parents miss important events" (Cornerstone/Edsby) → **UPHELD (V6/V2 verdict accepted)**
- Settled against the origin PDF by V6 (CK-2) and V2. V7 did not re-fetch. The figure is not in
  https://cornerstonepr.net/wp-content/uploads/2025/03/AppOverloadReport_bg.pdf.pdf

---

# PART 2 — FINAL CONSOLIDATED KILL LIST
## "Statistics we refused to use, and why"
### Ready to lift into the report as an appendix

*Every number below circulates widely in this topic space. Each was traced to its origin, or to the
point where the trail goes cold. None survived as stated. We publish this list because a research
report's credibility rests as much on what it declined to print as on what it did — and because
several of these will appear in competitors' decks.*

**The laundering moves.** Almost every item is one of six: a **FORECAST** restated as a MEASUREMENT;
a **DEVICE** count restated as a PEOPLE count; a **GLOBAL** number relabelled **US**; a real number's
**FIELDING DATE stripped**; a **BASE POPULATION swapped** under a real percentage; or — rarest and
worst — **FABRICATED ATTRIBUTION**, where a real institution's name is bolted onto a number it never
published.

**Confidence key.** *High* = origin publisher's own document or full-text index checked directly.
*Medium* = every reachable path exhausted, but one route (paywall, image-only publication, retired
PDF) remained closed; that route is named in the row.

### Tier 1 — FABRICATED: no origin publisher exists, or the named publisher never said it

| # | Statistic | Attributed to | What tracing found | Verified by | Conf. |
|---|---|---|---|---|---|
| K1 | "37 million Millennial parents" | Pew Research Center | Pew never published it. Full-text search of Pew's own API returns nothing. Pew published 17M Millennial *mothers* (2016) and 19M (2018) — mothers only. 37M looks like 19M doubled to add fathers. **Fabricated attribution to the most-trusted publisher in the space.** | V6 | High |
| K2 | "30%+ of US parents secure summer childcare before the prior year ends" | US BLS (2023) | BLS publishes nothing on booking timing. **No aggregator trail exists at all** — diagnostic of fabrication, not laundering. Every element (agency, year, verb, threshold) is wrong. Real cousin: CAP 2019, 32% started *looking* before March, n≈1,000 MTurk. | V6 | High |
| K3 | "15% completion drop per onboarding screen beyond five" | Appcues | Absent from Appcues' entire sitemap. Whole footprint is one blog post (lowcode.agency). Appcues publishes only "60–70% completion is a solid target; below 50% you likely have too many steps." | V6 | High |
| K4 | "4–6% completion drop per form field beyond the eighth" | Baymard Institute | No per-field percentage exists in Baymard. Their method (site audits + moderated testing, not A/B tests) **structurally cannot produce a slope**. Real: avg checkout 11.3 fields, "most sites need only 8." Twin phantom "4.1% per field (HubSpot 2024)" equally sourceless. | V6 | High |
| K5 | "$150 billion annual cost of missed US medical appointments" | "industry" / peer-reviewed papers | Dead-ends at a 2017 trade-magazine op-ed by the **CMO of a scheduling-software vendor**, no method. Competing published figure: $50B. **Has since contaminated peer-reviewed literature by citation laundering.** | V6 | High |
| K6 | "60% / 74% of parents feel guilty about screen time" | various | No origin at any tier. Major publishers **do not measure guilt**. The two numbers bracket the real Pew figure on either side — the signature of back-filling. Real: Pew Oct 2025, n=3,054, **42%** say they could do better. | V6 | High |
| K7 | "Average child attends 8–12 birthday parties per year" | various | **No publisher measures parties attended per child per year.** The only survey artefacts measure *hosting*: a PR-wire content mill (page now dead) and Chuck E. Cheese's vendor "Birthday Research Center" (Apr 2026, n=4,985, 20+ countries) — global, vendor, and a different construct. | V7 | High |
| K9 | "20.5% of people globally use voice search" | — | No publisher named anywhere in the chain, and no textual origin. **Unclosed route:** DataReportal/GWI publishes voice-search adoption inside slide-deck images that could not be OCR'd here; the HTML of all three *Digital 2024* reports contains zero occurrences of "voice." | V7 | Medium |
| K10 | "24% / 26% / 38% use voice while cooking / doing chores / relaxing" | — | These exact values have no origin. **But the measurement is not absent** — see K27b in Tier 2 for PwC's real activity-pairing figures (65/62/57%). The circulating "38%" may be a scramble of PwC's unrelated *"38% wouldn't want something listening in."* | V7 | High |
| K11 | "Districts use 3–7 apps parents must download" / "parents get updates through 5–6 different apps" | "studies" | No linked study; back-formed from Cornerstone's response buckets. **A real sprawl measurement exists but measures something else** — LearnPlatform/Instructure *EdTech Top 40*: districts access **2,739 (2024) → 2,982 (2025)** distinct edtech tools/yr, from telemetry over 57bn engagements. That is **district/student/teacher** access, **not parent installs**; substituting it would repeat the laundering. | V7 | High |
| K12 | "60% of parents miss important events" | Cornerstone / Edsby | **Not in the Cornerstone PDF.** | V6 / V2 | High |
| K13 | "70% of kids drop out of sports by 13" | various | Independently traced to no primary source by **Marty Fox (Aspen Institute Sports & Society)** and **Joseph Janosky (Lasell University)**, reported by USA TODAY 2026-04-11: *"a chain of secondary sources… None clearly anchored to a transparent, verifiable study… **citation drift**."* Traced back ~4 decades. Contradicted by CDC YRBS (HS participation >50% since 2000). **Use instead: Aspen/Project Play — "the average age a child quits sports is 12."** | V7 | High |
| K14 | "14,000+ AI startups launched 2024, 3,800 shut down 2025 = 40% failure rate" | — | A Medium post, no methodology. No dataset publisher (Crunchbase, CB Insights, PitchBook) publishes such a series. The arithmetic is also wrong: 3,800/14,000 = 27%, not 40%. | V6 / V7 | High |
| K15 | "Only 19.2% of users complete onboarding; global average 8.4% after 30 days" | — | No origin, no n, no fielding window. The named carrier page (setgreet) **no longer contains either number**; its replacement text is pure hedge. digia.tech's onboarding-statistics post contains no numbers at all. **No completion-rate benchmark for mobile onboarding exists at any tier** — see Tier 3. | V7 | High |
| K16 | "Recommendations from friends and family is the #1 way parents find a camp" | American Camp Association | No n, no fielding window, no origin document. ACA's own site does not carry it. | V6 | High |
| K17 | ActivityHero "over 4 million families" / "400k subscribers" | ActivityHero | Company rate card only. No press release, no date, no third-party audit, and **no definition of the counting unit**. Cumulative-registrations-as-audience + list-size-as-subscribers. | V6 | High |
| K18 | Anything sourced to **usecarly.com** | usecarly | SEO site for a competing commercial AI assistant. ~200 listicles, **no survey, no n, no method page anywhere**. "(2026)" title stamps are not evidence of currency. *(K25 independently traces back to this same publisher.)* | V6 | High |
| K19 | "Voice-AI startups raised $7B+ in Q1 2026" | — | No dataset named. Crunchbase News — the one publisher with a Q1 2026 methodology — reports $242B to AI globally / $250B to US companies and **publishes no voice-AI cut at all**. Circulates only on aggregators and a voice-AI vendor's own blog. | V7 | High |
| K21 | "Voice assistant market to reach $59.9B by 2033" | Astute Analytica | Market-sizing press release via GlobeNewswire. No methodology, no sample, no data source, no market-boundary definition. Marketing collateral for a paid report. | V6 / V7 | High |
| K22 | "TeamSnap 24 million users" | TeamSnap | No origin. The company's own PRs say 25M (2021) and **30M "parents, players, coaches and administrators" (2025-11-18)**. Pure aggregator artifact — and even 30M is an unaudited, mixed-role, cumulative headcount, never households. | V7 | High |
| K23 | "Average consumer has 8.2 subscriptions / $118 per month" vs "4.5 subscriptions" | — | Two mutually contradictory figures, no origin publisher; the self-contradiction is the tell. The real study in the space is **West Monroe, n=2,500 US consumers, June 2021: $273/month across 21 categories** (not app subscriptions) — whose *usable* finding is that **100% of respondents underestimated their own spend, 66% by more than $200**. | V7 | High |
| K24 | "Children have ~50 days off school (excluding summer) in a 180-day year" | — | No origin. Anchoring on **Pew/Education Commission of the States (2023-09-07)** — 180 days mandated in 27 of 38 states + DC, average requirement 179 — the arithmetic gives **~20–30 non-summer weekday closures**. The circulating figure is roughly **double**. No publisher counts closures directly. | V7 | High |
| K25 | "add@cozi.com" | Cozi | **Cozi has no inbound email-to-calendar feature of any kind.** Cozi's entire current FAQ treats email as outbound/identity only. Wayback CDX enumeration of every archived cozi.com URL containing "email" (2007–2025) shows no forwarding endpoint ever existed. Exact-phrase search returns zero. Probable propagation source: **usecarly.com (K18)**. | V7 | High |

### Tier 2 — REAL ORIGIN, LAUNDERED BEYOND USE: cite only with every qualifier restored

| # | Statistic as circulated | The true statement | The move | Verified by | Conf. |
|---|---|---|---|---|---|
| K26 | "8.4 billion voice assistants by 2026" | Juniper Research, **2020 forecast**, of **8.4bn DEVICES worldwide by 2024** (vs 4.2bn end-2020). | FORECAST→measurement, DEVICES→people, GLOBAL→US, **and the year moved**. All four moves in one number. | V6 (**false kill — origin exists**) | High |
| K27 | "71% of consumers prefer voice over typing" | PwC 2018 (n=1,000 US 18–64, online panel): in a **hypothetical forced binary**, **for search only**, on an implied base of **voice-assistant owners**, 71% chose voice. The same chart shows voice **losing** on shopping (24–36%) and service (34%). PwC has retired the page and PDF. Note: the figure does **not** appear in the PwC report the corpus cited — a misattribution, not just a stripped qualifier. | Qualifier-stripping + date-stripping. Contradicted by Pew's real measurement (22%). | V6 | High |
| **K27b** | *(new row)* "24/26/38% use voice while cooking / chores / relaxing" | **PwC 2018, same study:** among smart-speaker voice-assistant users, **65% cooking, 62% multitasking, 57% watching TV, 29% working, 0% driving**; on smartphones **40% driving**; **74% use voice in the home overall**. Also: adoption driven by younger consumers, **households with children**, and $100K+ households — yet **18–24s use it LESS daily than 25–49s (59% vs 65%)**, reason given: using voice in public *"just looks weird."* | The circulating triple is invented; the real values are ~2.5x higher and eight years old. Publisher's page retired — surviving record is Voicebot.ai/TechCrunch reporting of PwC's chart. | V7 | Medium (origin PDF retired; values via two independent 2018 secondary reports) |
| K28 | "92% of families will travel with their kids next year" | **No year of the FTA survey reads 92%** (real series: 93/93/88/79/70/88/81%). And **non-travelers are filtered out at the end of the first question block**, so no year's value is a population estimate. Non-probability recruitment from travel-affiliated mailing lists. FTA has pulled the PDFs. | Screened-sample artifact laundered into a population stat. **The most dangerous item here — it survives a casual check** (real association, real university partner, real n=3,370). | V6 | High |
| K29 | "Fathers get 35% of custody time" | Custody X Change 2018 **model**, not measurement: attorneys surveyed about *typical state guideline schedules*, percentages then computed **in the vendor's own software**. Verbatim: **"No customer data was used."** Assumes one child aged 6–11, amicable parents, no violence or substance abuse. | A vendor model of guidelines laundered into an empirical distribution, then re-laundered as a Census figure. | V6 | High |
| K30 | "30% pediatric no-show rate" | **No US national rate exists.** Literature spans 1.5%–24%; Boston Children's reports 20% (NPJ Digit Med 2022); **>30–50% only in urban safety-net / adolescent / high-social-risk subgroups.** Honest range: **10–25% typical.** | The subgroup ceiling published as the mean. | V6 | High |
| K31 | "Gen Z spends $377/month on subscriptions" | Real US origin — but it is **Wethrift.com (a coupon-affiliate site), Oct 2021, n=1,030 recruited on Amazon MTurk**. Fails Tier C on method. Separately **Visa/Basis found £305/mo — in the UK** (n=4,152, Nov–Dec 2024), independently laundered into US dollars. Visa's Gen X (£91) is *lower* than Boomers (£108) — a contradiction the US version silently "fixes." | Non-method source + a parallel GLOBAL→US relabel. | V6 (**false kill on the trace; kill stands on quality**) | High |
| K32 | ACA "26 million attend camp each summer" | ACA's published figure was **14 million (2013 basis)**, never 26 million. ACA has deleted the page; its current site publishes only member reach (7.2M campers). | Roughly double the last real figure, with no publisher behind the inflation. | V6 | High |
| K33 | ACA "more than 14,000 day and resident camps" | **Real** — ACA, **2017 Sites, Facilities & Programs Report** (8,400 resident / 5,600 day). Nine years old, hosting page deleted; ACA's current working universe is **>20,000 camp operations**. | Date-stripping. Citable ONLY as "ACA, 2017." | V6 (**false kill — origin exists**) | High |
| K34 | "Over 62% of US adults use a voice assistant," dated 2025/2026 | Verbatim at origin: *"In 2022, **62% of Americans 18+** use a voice assistant on any device"* — NPR/Edison, *Smart Audio Report 2022*, released 2022-06-16, fielded **2022-02-28 – 2022-04-18**, n=1,190 smart-speaker owners + 560 other-device VA users + 584 non-users. | Pure date-stripping: sound Tier B number, fabricated year. | V7 (re-confirmed at origin) | High |
| **K8** | "57% of **voice search** users use voice commands daily" | Same Edison report, verbatim: *"In 2022, **57% of voice command users** use voice commands daily."* | **BASE SWAP** (voice-command users → voice-search users) + DATE STRIP. **Reclassified out of Tier 1 by V7** — Edison did publish this number. | V7 (**V6 verdict corrected**) | High |
| K35 | "85% of parents rate their multi-app setup ≤5/10" and the Edsby study generally | Arithmetically correct from the source PDF (12+18+13+42) — but the study is **NORTH AMERICAN (US + Canada), n=125 parents**, commissioned by the vendor **Edsby** via a PR firm, fielded Dec 2024–Jan 2025. Edsby's own press release mis-states it as 42%. GovTech / eSchool News / PR Newswire are re-reports of the same release and **fake corroboration**. Unit fix: "10 to 15 apps" is what **curriculum leaders** said their *district* deploys, not a per-family count. | GLOBAL→US, plus corroboration-faking. | V6 | High |
| K36 | Birthday party "$314 average" on 2026 statistics pages | Real: What to Expect / Everyday Health *Talk to Moms Monthly Poll*, **fielded April 25–26 2024**, **n=404 women 18–44, pregnant or with a child under 5**; no probability sample, no MoE, no weighting. The "$344 for ages 6–10" cut is a subgroup of a survey that **screened for a child under 5**. | Date-stripping (partygeniusai reprints it as a 2026 figure) + population-stripping. **Do not build any Gen Z vs Millennial claim on its $329/$276 split.** | V6 | High |
| K37 | Bright Horizons "85% / 90% summer sleep-loss" cited as 2025 or as all parents | Real: **Harris Poll for Bright Horizons, April 14–16 2026**, n=2,030 US adults — but **90% is the n=479 EMPLOYED-parent subgroup** and **85% is the n=616 all-parents subgroup**, neither out of 2,030. The 2025 wave is a different study with **no disclosed n or fielding window**. | Wave confusion + subgroup-as-topline. **MFI is now multi-wave: always name the wave.** | V6 | High |
| K38 | Google "63% of Gemini users use voice" as a US or parent statistic | Google blog, 2026-08-11. **Global vendor telemetry, zero disclosed method** — no definition of "monthly user" or "voice user," no window, no geography, 1B worldwide users. | GLOBAL→US. **Also never use the adjacent "busy parents are 43% more likely to use voice" — no base, no comparison group, no denominator.** | V6 | High |
| K39 | eMarketer "139.8M → 168.2M US voice assistant users" stated as measurement | A **forecast** at both endpoints (EMARKETER, Sept 2025). Definition: **individuals of any age using a voice assistant ≥ monthly on any device, de-duplicated across devices** — people, not devices; **not adults** (eMarketer's adults-only series is separate). | FORECAST→measurement; "any age"→adults. | V6 | High |
| K20 | "153.5 million US voice assistant users in 2025" (eMarketer) | **V6's basis was wrong.** eMarketer publishes a **new per-year vintage annually**; the **2024 vintage** (Jacob Bourne, 2024-08-21) states *"US voice assistant users will grow from **145.1M in 2023** to **170.3M in 2028**, CAGR 3.3%"* — on which curve 2025 ≈ 154.9M. So 153.5M is almost certainly a **real paywalled forecast point**, not an invented interpolation. **Still not citable** (we cannot see it, and it is a model output either way). | FORECAST→measurement. **Reclassified from "fabricated" to "unverifiable at origin — paywalled."** | V7 (**V6 verdict corrected**) | Medium (chart paywalled) |
| K40 | US Travel "1.99B trips in 2026" | 2025's 1.95B is an **actual**; **2026's 1.99B is a forecast**. Unit is **person-trips, not people** — one person taking six trips contributes six. | FORECAST→measurement; TRIPS→people. | V6 | High |
| K41 | Skylight/Harris "mental load worth $60,000/year" and Forbes' "$3.8 trillion" | The underlying Harris survey is **sound and citable** (n=2,005 US parents of under-18s, May 15–22 2024, weighted, ±2.9pp). But $60,000 is a **derived calculation** (hours × $35.86 median wage), and Forbes' $3.8 trillion is a **national extrapolation the survey does not support**. | Derived-figure-as-measurement. **A case of our own best source being laundered downstream.** | V6 | High |
| K42 | Klook "91% of global travelers rely on AI travel planners" | Klook *Travel Pulse*, **4th edition 2026, n=11,000 across 20 markets** (15 of them APAC; US is 1 of 20 with no disclosed cell size), explicitly drawn from **Millennials and Gen Z "which makes up Klook's core user base."** Klook's own qualifier: AI's *"role remains largely **functional**"* — research, translation, itinerary organisation, budgets. | GLOBAL→US **+ vendor's own customers→travelers generally + "used for tasks"→"rely on."** | V7 (origin + method confirmed) | High |
| K43 | Litmus email-client share as mailbox-provider share | Litmus measures the **rendering client's user agent**: Apple = 62.3% of *opens* vs **3.6% of mailboxes** (Validity) vs 17% of US adults using iCloud Mail (Statista). **~90%+ of "Apple" opens are Apple's app reading someone else's mailbox.** | The purest DEVICES-as-PEOPLE case in the corpus. **Caught by S1 before it shipped — the model of what this appendix is for.** | S1 / V6 | High |
| K44 | "CASA costs $15,000+" | Traces to a pre-CASA Ask-HN thread and to Google fee language **removed from its own docs between June 2022 and June 2023**. Live lab prices are **$675–$8,000**. | Date-stripping of retired vendor language. | V6 | High |

### Tier 3 — MEASURED NOWHERE: numbers we looked for, could not find at any tier, and are reporting as absent

*Stating these is what stops the next person fabricating them.*

- **Hours a US parent spends researching and booking summer care.** No survey measures it.
- **Trips per year for US households with children.** No publisher reports it.
- **Time spent deciding a weekend activity; weekend-outing spend per episode.** No US data.
- **Share of US households sustaining a shared digital family calendar**, and the "we tried it and it
  didn't stick" pattern. No data at any tier — **probably the single most decision-relevant unknown.**
- **Apps / portals / logins per FAMILY, probability-sampled.** Does not exist. Edsby n=125 (North
  American, vendor-partnered, screened for parents already using 3+ apps) remains the only
  parent-level number in the world. LearnPlatform's 2,739→2,982 district-tool figures are real and
  method-disclosed but measure **district/student/teacher** access, not parent installs — **do not
  substitute them** *(V7)*.
- **Any mobile-onboarding completion-rate benchmark** — per-screen, per-field, or overall. Neither
  Appcues, Baymard, nor any analytics vendor publishes one; Baymard's method structurally cannot
  produce a slope. The onboarding argument must rest on the Nielsen 10-second limit and a field-count
  comparison, never a completion slope *(V7)*.
- **Parties attended per child per year.** Only hosting-side vendor surveys exist *(V7)*.
- **Non-summer school closure days per year.** No publisher counts them; ~20–30 is our arithmetic on
  Pew/ECS's 179–180-day base, not a source *(V7)*.
- **Permission slips / school forms per year; picture days; early-release and PD-day counts.** No source.
- **Parents' comfort granting a consumer app OAuth inbox access**, or comfort with a third party
  receiving their child's school communications. **No Tier A/B survey measures either construct**
  (independently confirmed by P10 and P12).
- **Any funnel comparison of email-forwarding onboarding vs OAuth inbox connection.** Does not exist
  in public. Put no number on it. Related: **Cozi has no email-in feature at all**, so there is no
  competitor precedent to reason from *(V7)*.
- **D1/D7/D30 retention benchmarks.** Every origin path is gated (AppsFlyer, Adjust, Statista, Sensor
  Tower). Not citable from this program.
- **Adoption of Apple Hide My Email / Firefox Relay.** Neither publishes any number.

---

# PART 3 — COVERAGE LIMITS OF THIS VERIFICATION

State these plainly; they are the honest boundary of the appendix.

1. **WebSearch was unavailable.** The session's 200-call budget was exhausted before V7 started. All
   searching was scripted Yahoo SERP scraping, which rate-limits aggressively (multiple 45–90s
   backoffs) and returns roughly 7 organic results per query. A number that exists only on a page
   Yahoo does not surface would have been missed.
2. **Image-baked publications were not OCR'd.** This is the one route the fleet's own method notes
   flag as valid and V7 could not close. It affects **K9** directly (DataReportal/GWI publish voice
   adoption inside slide decks) and potentially any figure whose only home is a chart image. K9's
   confidence is Medium for this reason.
3. **Paywalled origins were not purchased.** K20 (eMarketer chart data), K21 (Astute Analytica's paid
   report), and the gated retention vendors were assessed from free surfaces only. K20 is Medium.
4. **Retired publisher PDFs.** PwC's 2018 voice report (K27, K27b) and FTA's family-travel PDFs (K28)
   have been withdrawn by their publishers. Values are taken from contemporaneous secondary reporting
   (Voicebot.ai, TechCrunch) rather than the primary document. This is a real limitation, and K27b is
   marked Medium accordingly.
5. **K12 and K21 were accepted on V6's evidence** rather than independently re-fetched. Both are
   attributed to V6 in the table.
6. **False-kill rate.** V6 found 3 false kills in 12 spot-checks (25%). V7 re-traced 18 items and
   changed the verdict on **4** (K8 reclassified out of Tier 1; K20's stated basis refuted; K10's
   "measurement doesn't exist" refuted; K11's absence-claim refined) — a **22% correction rate**,
   consistent with V6's. **A third pass would likely still find one or two.** No kill list from this
   program should be presented as final beyond the confidence marks in the table.
