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

**Status note, 2026-08-22.** The 41-agent program has now finished, and several gaps in the first
version of this prompt were closed by the verification pass. They are removed below. What remains is
re-prioritised by how much a decision currently rests on it.

## PRIORITY 1 - one unsourceable verdict is holding up an architecture decision

**G1. Can a parent add a secondary or arbitrary notification email in ParentSquare?**
This is the single most valuable question in the list. ParentSquare's BLOCKED verdict is load-bearing:
it is one of two findings that killed a whole product strategy (registering our own address with
schools), and it rests on a citation no reader can check, because ParentSquare's help centre is
login-gated and renders a sign-in page in real Chrome. Determine from first-party sources, ideally by
seeing an actual account: (a) can a parent add or change a notification email themselves, or is the
field synced nightly from the student information system and overwritten? (b) does ParentSquare's
notification email carry the message CONTENT in the body, or only a "sign in to read" link? (c) what
is the default digest behaviour, and can a parent switch to instant per-message email? Their 6pm
digest default may mean a forwarding architecture captures envelopes rather than content across 22M
students. Same three questions, lower priority, for Brightwheel and Infinite Campus.

**G2. Google CASA and restricted-scope verification, 2026, confirmed at source.**
Confirm from Google's own current documentation: that the unverified-app cap is 100 users over the
GCP project's ENTIRE LIFETIME and is not resettable; that exhausting it disables Google sign-in; that
verification lifts it; that the security assessment is mandatory, annual, and a full re-test
regardless of whether anything changed; the current tier pricing and whether a self-start application
lands at the higher tier by default; and the current elapsed time from submission to grant. Also:
does an LLM pipeline processing Gmail message bodies satisfy Google's Limited Use policy at all? That
last one is unresolved and a product depends on it.

## PRIORITY 2 - blocked authoritative sources

**G3. NCES school-calendar structure.** nces.ed.gov and ecs.org were unreachable. Needed: the
distribution of teacher professional-development days, early-release days and conference days across
the calendar, and typical back-to-school start dates by region. A measured figure of 30 to 38
non-summer closure days (median ~34) was assembled from individual district calendars; confirm or
replace it with a published national figure.

**G4. American Camp Association primary data.** americancamp.org is Cloudflare-blocked. ACA's widely
repeated "26 million campers" was traced to ACA's own unsourced boilerplate and its 2024 economic
study supplies no camper count. Find ACA research with a stated year and method, or confirm none is
public. Gallup/NSLA's 30M (55% of K-12) is currently used instead.

**G5. Reddit and Trustpilot at scale.** A qualitative corpus of ~2,300 comments was built by
browser-driven comment search, but it skews heavily to r/adhdwomen and r/ADHD, has no full threads,
and contains nothing from BabyCenter or What to Expect. A broader harvest would firm up the
messaging work. Themes that produced the least material and would most repay effort: "we tried
[family calendar app] and it did not stick" and why; and "I wish there was an app that". Also:
Trustpilot ratings and complaint themes for Cozi, Skylight, OurFamilyWizard, TalkingParents and
ParentSquare.

## PRIORITY 3 - paywalled benchmarks

**G6. Mobile app retention and engagement benchmarks.** Behind Statista, AppsFlyer, Adjust and Sensor
Tower seats. Needed: US D1/D7/D30 retention for the Lifestyle, Parenting and Productivity categories;
average number of apps a person actively uses per month; median mobile session length.

## PRIORITY 4 - probable confirmed negatives

For each of these the fleet searched hard and found nothing at any tier. A CONFIRMED NEGATIVE is a
useful result. Do not fill the hole with a plausible number.

**G7.** What share of US households sustain a shared digital family calendar over time, and why
family-organizer apps fail to stick. Repeatedly flagged as the single most decision-relevant unknown
in the whole study.
**G8.** Willingness to pay for AI household or family assistance specifically. No data at any tier.
This makes every price hypothesis currently untested.
**G9.** Parent trust in AI advice about their children RANKED against a pediatrician, a teacher, a
friend and a parenting influencer. No 2025-26 study makes the comparison. The only hard datum is a
2024 University of Kansas study (n=116, blinded) finding parents rated AI health advice MORE
trustworthy than expert-written content, unreplicated.
**G10.** Any US study separating three distinct voice behaviours: dictation, assistant commands, and
conversational LLM voice. Every Tier A/B source merges them. Also: a US survey measuring DICTATION
usage rate specifically, and any published LLM-voice session-length data.
**G11.** A probability-sampled count of how many apps or portals a family juggles per child. Only a
vendor study exists (n=125, non-probability, North American not US).
**G12.** Hours US parents spend researching and booking summer care, and hours per activity
enrolment episode. No US survey found for either.
**G13.** Weekend-outing frequency and decision time for US families. No publisher measures it.
**G14.** School form and permission-slip volume per child per year. Searched twice, at higher
confidence the second time. NCES NHES measures participation and channels, never action-required
document counts.
**G15.** Frequency of birthday parties ATTENDED per child per year. The circulating 8 to 12 is on the
kill list.
**G16.** Any quantitative US source on same-sex-couple parents and the division of planning labour.
Pew could not analyse them in either 2025 or 2026 for sample-size reasons. This is a useful natural
experiment for planning labour without gender defaults.
**G17.** Any method-disclosed research on dark-mode preference or expectation by age cohort.
**G18.** Sports physicals: seasonal clustering, and how often parents miss the deadline and a child
is held out of play. The requirement side is well sourced (98% of states, most annually); the failure
rate is a hypothesis.
**G19.** Whether Pew released supplementary tables allowing a parent-age breakdown of its flagship
2026 parenting study (n=3,757), which publishes no parent-age crosstabs. Common Sense's Generation AI
report states generational differences exist but does not publish the crosstab; it may be obtainable
on request.

## PRIORITY 5 - re-runs that would firm up published findings

**G20. A third pass over the kill list.** Two independent verifiers re-traced 22 previously-killed
statistics and overturned 6 (27%). A third pass would likely still find one or two. The un-re-traced
remainder has no measured error rate in either direction. Highest-value single item: the
"24% cooking / 26% chores / 38% relaxing" voice context triple, killed on all reachable evidence but
exactly the data the study most wants, so a false kill there is costly. Note a separate, independently
sourced PwC 2018 context set (65% cooking, 40% driving on a smartphone vs 0% on a smart speaker) was
restored and stands regardless.

**G21. Re-run the ActivityHero live-supply audit in February.** The published measurement was taken
on 21 August, a seasonal trough. Year-round classes stay live through August while summer-only supply
expires, so the sparse-market coverage gradient is inflated at that timepoint. A February re-run
would establish whether the gradient is structural or seasonal. The August numbers: 94,848 session
records nationally, 9,008 live (9.5%), California 48% of live, and live counts of SF 969, LA 329,
NYC 112, Minneapolis 35, Wichita 8. Note LA has MORE providers than SF (5,686 vs 4,299) and a third
the live sessions, so provider rank and live rank already disagree.

**G22. Camperoni's current inventory and product.** Their live index was measured at ~4,324 records by
one checker and could not be independently reproduced. It matters because it moves them from roughly
one-eighteenth of ActivityHero's live inventory to roughly one-half. Also confirm whether their
registration-watch offering is still a $295/year human concierge across 5 metros, or has been
automated since.

**G23.** Any US survey fielded in 2026 on parental logistics load, family scheduling, school
communication overload or the mental load that this list does not name. Recency matters: the study's
newest load-bearing finding was five weeks old at the time of writing.

---

## Final instruction

Return the findings table, the per-gap interpretation, and the closing list splitting
**CONFIRMED NEGATIVE** from **STILL BLOCKED**. Where you find a laundered statistic, name it and name
the aggregators repeating it. Where sources contradict each other, present both and say which has the
better method rather than averaging them.
