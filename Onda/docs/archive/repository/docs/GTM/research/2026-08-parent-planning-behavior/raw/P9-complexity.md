# P9 — COMPLEXITY TOLERANCE

Collector P9. Domain: how much product a time-poor parent will actually absorb.
Compiled 2026-08-21. Geography: US unless flagged otherwise.

**Headline for the synthesist:** the single most-cited number in this space — "onboarding
completion drops 15% for every screen beyond five (Appcues)" — **has no traceable origin and
Appcues' own page does not contain it.** It is killed in Section 2. There is *no* published,
method-disclosing screens→completion curve for mobile apps that I could reach. The defensible
benchmark for onboarding length is therefore the **form-field** literature (Baymard) plus the
**feature-fatigue** literature (Thompson/Hamilton/Rust, peer-reviewed), not an onboarding-vendor
blog. That substitution is the main methodological contribution of this collector.

---

## Section 1: FINDINGS

| # | Claim (one sentence, with the number) | Value | Cohort/segment | Publisher | Year | Method (n, fielding window, population) | Tier | URL |
|---|---|---|---|---|---|---|---|---|
| 1 | Before using a product, 62.3% of consumers chose the most feature-loaded model (21 features) over the mid (14 features, 28.5%) or simple (7 features, 9.2%) model. | 62.3 / 28.5 / 9.2 % | US undergraduates (not parents) | Thompson, Hamilton & Rust — *Journal of Marketing Research* 42(4):431–442; pre-print MSI Report 05-101 | 2005 | Study 1; n=130 undergrads (50.8% female, M age 20.55), lab, 2×3 repeated-measures ANCOVA on digital audio/video players. **Dated (2005) and student sample.** | A | https://thearf-org-unified-admin.s3.amazonaws.com/MSI/2020/06/MSI_Report_05-101.pdf |
| 2 | Given a free choice of features at zero cost, consumers self-selected a mean of 19.6 of 25 available features (median 20); about half chose more than 80% of all features. | 19.64 (video) / 19.58 (audio) of 25; median 20 | US undergraduates | Thompson, Hamilton & Rust (JMR / MSI 05-101) | 2005 | Study 2; n=141 undergrads (55.3% female, M age 21.07), between-subjects product-customization task, explicit "budget allows as many features as you like." Dated. | A | https://thearf-org-unified-admin.s3.amazonaws.com/MSI/2020/06/MSI_Report_05-101.pdf |
| 3 | Perceived capability of a feature-rich product was significantly LOWER after actually using it than before (F(1,186)=5.09, p=.025), and perceived usability fell significantly as features rose (F(1,185)=33.13, p=.000). | see F-stats | US undergraduates | Thompson, Hamilton & Rust (JMR / MSI 05-101) | 2005 | Study 3; n=190 (52.1% male, M age 20.54), 2 (before/after use) × 2 (7 vs 21 features) between-subjects, 4 real tasks on a working video-player interface + manual (4pp vs 8pp). Dated. | A | https://thearf-org-unified-admin.s3.amazonaws.com/MSI/2020/06/MSI_Report_05-101.pdf |
| 4 | Consumers gave significantly LESS weight to usability when predicting their satisfaction than when rating actual satisfaction after use (χ²(1)=4.48, p=.034) — the formal mechanism of feature fatigue. | χ²(1)=4.48, p=.034 | US undergraduates | Thompson, Hamilton & Rust (JMR / MSI 05-101) | 2005 | Study 3 multisample path analysis, ML estimation, Lagrange-multiplier test across before/after-use conditions. Dated. | A | https://thearf-org-unified-admin.s3.amazonaws.com/MSI/2020/06/MSI_Report_05-101.pdf |
| 5 | Employed US adults living with a child under 6 average **3.0 hours/day** of leisure and sports — 1.5 hours less than employed adults with no children under 18 (4.5 hours). | 3.0 h vs 4.5 h/day | US employed adults, child <6 (spans all three parent cohorts) | US BLS, American Time Use Survey 2024 (USDL-25-1060), table 8B | 2025 (2024 data) | ATUS annual averages; ~7,700 individuals interviewed in 2024; CPS-derived sample; continuous monthly fielding across calendar 2024. | A | https://www.bls.gov/news.release/archives/atus_06262025.pdf |
| 6 | US adults in households with a child under 13 spend **5.2 hours/day** on *secondary* childcare, of which **1.8 hours** occurs while doing leisure activities — i.e. a large share of parental "free time" is supervised and interruptible. | 5.2 h/day; 1.8 h overlapping leisure | US adults, child <13 | US BLS ATUS 2024, table 10 | 2025 (2024 data) | As above, n≈7,700, calendar 2024. | A | https://www.bls.gov/news.release/archives/atus_06262025.pdf |
| 7 | US adults living with a child under 6 spend **2.5 hours/day** on primary childcare (women 3.0 h vs men 2.0 h); secondary childcare runs 4.5 h on weekdays and 7.5 h on weekend days. | 2.5 h/day primary | US adults, child <6 | US BLS ATUS 2024, tables 9 & 10 | 2025 (2024 data) | As above, n≈7,700, calendar 2024. | A | https://www.bls.gov/news.release/archives/atus_06262025.pdf |
| 8 | **10 seconds is the limit for keeping a user's attention focused on the task**; 1.0 s is the limit for uninterrupted flow of thought and 0.1 s for the feeling of instantaneous response. | 0.1 s / 1.0 s / 10 s | All computer users (not US-specific) | Jakob Nielsen, *Usability Engineering* (excerpt published by Nielsen Norman Group), building on Miller (1968) and Card, Robertson & Mackinlay (1991) | 1993 (thresholds from 1968/1991) | Synthesis of prior HCI experiments; **dated, pre-mobile** — but the canonical and still-cited threshold. Beyond 10 s NN/g requires a percent-done indicator *plus* an estimate of completion time. | A | https://www.nngroup.com/articles/response-times-3-important-limits/ |
| 9 | 86% of users said they liked percent-done progress bars, and users shown a progress bar rated the same-length wait as faster, more reliable and more trustworthy than users shown nothing; inaccuracy in the bar was largely forgiven. | 86% preference | Students (n=48) | Brian Myers, "The importance of percent-done progress indicators for computer-human interfaces," ACM SIGCHI Bulletin | 1985 | Controlled experiment; 48 students ran computer searches with and without a filling-capsule progress bar. **Severely dated (1985), small n** — but the origin study for the entire progress-bar convention. | A | https://www.hcii.cmu.edu/news/nyt-highlights-myers-role-popularizing-progress-bars |
| 10 | Users given an animated progress indicator reported higher satisfaction and were **willing to wait on average 3× longer** than users with no indicator. | 3× | Web users (not US-specified) | Nah, F. (2004), *Behaviour & Information Technology* 23(3) — "A study on tolerable waiting time," as summarized by Nielsen Norman Group | 2004 (NN/g summary 2014) | Peer-reviewed; 673 citations. **Sample size and the raw tolerable-waiting-time seconds were behind the publisher paywall and could not be verified directly — the 3× multiplier is cited here second-hand from NN/g.** | A (paper) / B (the 3× as relayed) | https://www.nngroup.com/articles/progress-indicators/ ; DOI 10.1080/01449290410001669914 |
| 11 | Design thresholds: no indicator below 1 s; a looped animation (spinner) for 2–10 s; a **percent-done indicator above 10 s**. | 1 s / 2–10 s / 10 s+ | All users | Katie Sherwin, Nielsen Norman Group | 2014 | Practitioner guidance synthesizing Nah 2004 and Nielsen 1993; no new sample. | B | https://www.nngroup.com/articles/progress-indicators/ |
| 12 | The average e-commerce checkout in 2024 contained **11.3 form fields**, down from 11.8 (2021) and 12.7 (2019); Baymard's tested optimum is **~8 fields total**. | 11.3 avg / ~8 optimum | US + European e-commerce sites | Baymard Institute e-commerce UX benchmark | 2024 | Large-scale benchmark of live checkout flows plus moderated usability testing; **Baymard does not disclose the site count or participant n on the public page** — method partially disclosed. | C | https://baymard.com/blog/checkout-flow-average-form-fields |
| 13 | Among online shoppers who abandoned a cart for a reason other than browsing, **17% cited "the checkout process was too long / too complicated"** and **18% cited "the site wanted me to create an account."** | 17% / 18% | US online shoppers | Baymard Institute cart-abandonment study | 2024 (most recent public update) | Quantitative survey of online shoppers; **sample size and fielding window are not stated on the public page** — flag as method-incomplete. | C | https://baymard.com/lists/cart-abandonment-rate |
| 14 | **82% of trial starts happen on the same day the user installs the app** — the value judgment is made inside session one. | 82% | Subscription apps globally (not US-only) | RevenueCat, State of Subscription Apps 2025 | 2025 | 75,000+ subscription apps, >$10B tracked revenue, anonymized platform data across iOS + Android. **Global, vendor-interested (RevenueCat sells subscription infrastructure).** | B | https://www.revenuecat.com/state-of-subscription-apps-2025 |
| 15 | **55% of all trial cancellations occur on Day 0.** | 55% | Subscription apps globally | RevenueCat, State of Subscription Apps 2026 | 2026 | 115,000+ apps, $16B+ tracked revenue, YoY 2025→2026. Global; vendor-interested. | B | https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026 |
| 16 | 12-month subscription retention (median): **yearly 44.1%, monthly 17.0%, weekly 3.4%** — and **Social & Lifestyle shows the lowest retention of any category across all plan types.** | 44.1 / 17.0 / 3.4 % | Subscription apps globally | RevenueCat, State of Subscription Apps 2025 | 2025 | 75,000+ apps, >$10B revenue. Global; vendor-interested. | B | https://www.revenuecat.com/state-of-subscription-apps-2025 |
| 17 | 35% of annual subscriptions are cancelled within month 1 and 72% churn within year 1. | 35% / 72% | Subscription apps globally | RevenueCat, State of Subscription Apps 2026 | 2026 | 115,000+ apps, $16B+ revenue. Global; vendor-interested. | B | https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026 |
| 18 | Hard paywall converts at 10.7% by day 35 vs 2.1% for freemium (~5×). | 10.7% / 2.1% | Subscription apps globally | RevenueCat, State of Subscription Apps 2026 | 2026 | As #15. **ALREADY KNOWN per the brief — listed only to date-stamp the 2026 figures.** | B | https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026 |

### Interpretation

**1. There is no citable onboarding-screens→conversion curve. The closest defensible proxy is the
form-field literature, and by that yardstick our onboarding is longer than a retail checkout.**
Every "X screens → Y% completion" number in circulation traces back to onboarding-tool vendors with
no published method, and the most repeated one (Appcues, 15%/screen) does not appear on Appcues' own
site (Section 2). What *is* measurable is fields. Baymard's 2024 benchmark of live checkouts puts the
industry average at 11.3 fields with a tested optimum near 8, and 17% of cart abandoners name
checkout length/complexity as their reason. Our onboarding asks **14 fields for one kid and 19 for
two** — more than the average commercial checkout. The asymmetry that matters: a checkout is
completed by someone who has *already decided to buy*, after seeing the product. Our 14–19 fields are
demanded *before* the parent has seen a single thing the app does. Field-for-field parity with a
checkout is therefore not parity at all; it is materially worse positioning of the same friction.

**2. The account-creation finding is the sharpest single read on our second setup sequence.** 18% of
abandoners quit over being asked to create an account — a *shorter* obligation than what we impose.
Our "second setup sequence with ~5 more full editor stops, auto-presented from Home" is functionally
a second forced account creation, delivered at the exact moment the user finally reached the product.

**3. Feature fatigue predicts that our breadth will demo well and retain badly — and it explains why
user feedback will mislead us.** Thompson, Hamilton & Rust is the strongest evidence in this report
because it is peer-reviewed, experimental, and directly measures the before/after inversion. Pre-use,
62.3% of subjects chose the 21-feature model over the 7-feature one; given free rein they checked off
a median 20 of 25 features. Post-use, perceived capability *dropped* and usability fell significantly
with feature count, and the formal path analysis shows people systematically under-weight usability
when forecasting their own satisfaction (χ²=4.48, p=.034). Applied to us: parents in discovery calls
and surveys will ask for more verticals, more knobs, more fields — and the same parents will churn on
the product that grants those requests. **Any prioritization built on stated preference will
over-build.** The authors' own managerial conclusion is the recommendation this project should weigh:
prefer a larger set of narrow, dedicated products with few features each over one product carrying
every feature. Caveats: 2005, US undergraduates, consumer electronics — the mechanism generalizes
well (it has been replicated conceptually many times) but the effect sizes should not be transported
numerically to a parenting app.

**4. Our 1–2 minute async search is 6–12× the canonical attention limit, and progress indicators do
not close a gap that large.** Nielsen's 10-second threshold — the limit for keeping attention on the
task — is the most durable number in HCI, and NN/g's operational rule above 10 s is a *percent-done*
indicator plus an explicit completion estimate, not a spinner. The mitigation evidence is real but
bounded: Myers 1985 (n=48) found 86% preference and better perceived speed at identical actual wait;
Nah 2004, via NN/g, found ~3× longer willingness to wait with an animated indicator. Three times a
tolerance measured in the seconds-to-tens-of-seconds range does not reach 60–120 seconds. The honest
reading is that decoration buys us perhaps tens of seconds, not two minutes. **The structural fix is
to stop making the wait a wait**: return provisional results immediately, let the parent leave, and
notify on completion — the app already ships push notifications for the registration watchlist.

**5. The time-budget data explains why any of this bites harder for our user than for a general
consumer.** ATUS 2024 (Tier A, n≈7,700): employed adults with a child under 6 get 3.0 h/day of
leisure versus 4.5 h for the childless — and 1.8 h/day of adults' leisure in households with a child
under 13 is being conducted *while supervising a child*. The discretionary time exists but is
fragmented and interruptible. A ~34-tap onboarding plus five editor stops plus a two-minute blocking
wait is a design that assumes a contiguous, uninterrupted block. That block is precisely what this
population does not have. Note this is a household-composition cut, not a generational one; ATUS does
not publish a Gen Z / Millennial / Gen X parent breakdown of leisure time in the summary release, so
**no cohort contrast is available here**.

**6. The subscription data says the verdict lands on day zero.** RevenueCat 2025: 82% of trial starts
happen on install day. RevenueCat 2026: 55% of all trial cancellations happen on Day 0. Whatever
session one contains *is* the product as far as more than half the churning population is concerned.
Today session one is: 8+N onboarding screens, then a second setup sequence, then — if they reach the
Planner — a two-minute wait. Session one currently contains almost no product. Contradiction worth
flagging: RevenueCat's own hard-paywall finding pushes toward asking for commitment *early*, which
superficially argues for front-loading. It does not argue for front-loading *data entry*; a paywall
is one decision, a 14-field wizard is fourteen.

**7. Contradiction between sources on how much complexity is tolerable.** Baymard's direction of
travel is monotone — fewer fields is better, full stop. Feature-fatigue research is *not* monotone: it
finds a genuine capability benefit that is simply over-weighted pre-use, and its prescription is an
optimum, not a minimum. And RevenueCat's category data shows Social & Lifestyle retaining worst of
all categories regardless of design, suggesting a ceiling that no amount of simplification lifts. The
resolution I would offer the synthesist: simplify *acquisition-path* complexity (onboarding, fields,
waits) toward the minimum, but treat *post-activation* feature breadth as an optimum problem where
the current 5 verticals / 12 knobs is plausibly already past the peak. The feature flags that default
off on three verticals are, read this way, already the right instinct.

**8. What I could not source, and the fact that I could not is itself a finding.** Category-level D1/
D7/D30 retention benchmarks for "Lifestyle" and "Productivity" circulate everywhere but every path
led to a paywalled Statista slice or a vendor gate; no method-disclosing origin was reachable
(Section 2). Same for apps-actively-used-per-month and typical session length. And on the specific
question of parents abandoning shared family calendars — "we tried it and it didn't stick" — **no
data found at any tier.** There is no published measurement of what share of US households sustain a
shared digital family calendar. Given that this is arguably the central adoption question for a
family-organizer product, its absence is a genuine gap and a candidate for primary research.

---

## BENCHMARK VS. OUR APP

| Our measured number | Benchmark it is judged against | Verdict |
|---|---|---|
| **Onboarding: 8+N screens (10 for two kids)** | No citable screens→completion curve exists. Judged indirectly: 17% of cart abandoners quit on checkout length (Baymard 2024); 55% of trial cancellations occur Day 0 (RevenueCat 2026). | **SEVERE OUTLIER** — not because 10 screens is provably fatal, but because there is no product value anywhere inside those 10 screens and the churn decision is made in the same session. |
| **14 input fields for one kid / 19 for two** | Average e-commerce checkout = 11.3 fields; Baymard tested optimum ≈ 8 (2024). | **SEVERE OUTLIER** — 1.2–1.7× the average *checkout*, demanded pre-value rather than post-purchase-decision. |
| **~34 taps to complete onboarding** | No published tap-count benchmark exists at any tier. Judged against ATUS 2024: 3.0 h/day fragmented, supervised leisure for parents of under-6s. | **AT-RISK** (unbenchmarked) — flagged rather than scored; the tap count is only meaningful because it must fit an interrupted session. |
| **A SECOND setup sequence, ~5 editor stops, auto-presented from Home** | 18% of cart abandoners quit rather than create an account (Baymard) — a smaller ask than five editors. 82% of trial starts occur on install day (RevenueCat 2025). | **SEVERE OUTLIER** — this is the highest-leverage single cut in the report. A second forced sequence at the moment of arrival inverts the one thing the day-0 data demands. |
| **5 tabs** | Apple HIG and near-universal consumer-app convention is 3–5 tabs. No contrary evidence found. | **WITHIN NORM.** |
| **94 SwiftUI views / 44 tracked screens** | No published view-count benchmark exists. Judged against feature fatigue: pre-use preference for 21-feature over 7-feature models (62.3% vs 9.2%), post-use capability and usability both falling (Thompson/Hamilton/Rust 2005). | **AT-RISK** — surface count is not itself measurable as harmful, but it is the exact shape the feature-fatigue literature predicts users will request and then punish. |
| **58 text-entry fields app-wide** | Average whole checkout = 11.3 fields (Baymard 2024). | **SEVERE OUTLIER** — roughly five complete e-commerce checkouts' worth of typing distributed through the product. |
| **One profile screen with 18 open free-text fields** | Average whole checkout = 11.3 fields; optimum ≈ 8. Free-text is the highest-cost field type in Baymard's taxonomy. | **SEVERE OUTLIER** — a single screen exceeds an entire average checkout by 1.6×, in the most expensive input modality, with no completion incentive attached. |
| **Planner: 12 user-settable knobs** | Feature fatigue Study 2: given 25 free options, users self-select a median of 20 pre-use, then rate usability significantly lower (Thompson/Hamilton/Rust 2005). | **AT-RISK** — 12 knobs will test well and be used by few; expect strong stated demand and weak revealed use. Instrument actual knob-touch rates before adding a 13th. |
| **Planner: 16–20 taps to a saved plan** | Unbenchmarked. Adjacent: Baymard's field-count direction of travel; ATUS fragmented time. | **AT-RISK** (unbenchmarked). |
| **1–2 minute async wait for search results** | Nielsen's 10-second attention limit (canonical, from Miller 1968 / Card 1991). | **SEVERE OUTLIER** — 6–12× the threshold. |
| **…the same wait, WITH a percent-done indicator and an expectation-setting message** | NN/g's rule above 10 s is percent-done *plus* a completion estimate; Nah 2004 (via NN/g) ≈3× longer willingness to wait; Myers 1985 (n=48) 86% preference and faster perceived speed at identical wait. | **AT-RISK, improved but not resolved** — 3× a seconds-scale tolerance does not reach 120 s. Indicators are necessary and insufficient; the answer is provisional results + backgrounding + push notification, not a better spinner. |
| **5 verticals, 3 defaulted off behind flags** | Feature-fatigue prescription: prefer several narrow products with few features each over one loaded product. | **WITHIN NORM** — defaulting three off is the behavior the literature recommends. Keep them off until camp and outing show sustained use. |

---

## Section 2: WEAK SIGNAL

Not sourceable to Tier A/B/C. Do not promote any of these into findings.

1. **KILLED — "Completion rates drop by 15% for every additional onboarding screen beyond five
   (Appcues)."** This is the most-repeated onboarding statistic in existence and it is laundered. It
   appears verbatim on lowcode.agency, openspaceservices.com, uxcam, semnexus and others, always
   attributed to Appcues, always without a study, sample, or date. I fetched Appcues' own
   "User Onboarding Metrics & KPIs" page — the figure **does not appear on it**; the only benchmark
   Appcues states there is an unsourced "below 30% for a core onboarding checklist signals friction."
   **Treat as unverifiable. Do not cite. Flag if it appears in any other collector's output.**
2. **"Only 19.2% of users complete onboarding; global average completion after 30 days is 8.4%;
   top performers 40–50%."** Circulated by setgreet.com and digia.tech with no origin, no n, no
   fielding window. Unverifiable.
3. **"Simple apps 70–80% onboarding completion, complex apps 50–65%, regulated flows 40–60%."**
   Practitioner rules of thumb on vendor blogs; no underlying dataset located.
4. **Category retention benchmarks D1/D7/D30 — NOT SOURCED.** The widely-cited cross-industry
   "≈25–26% D1, 11–13% D7, 5–7% D30", "Lifestyle 20.9% D1 / 4.5% D30", "Productivity D30 4.1%
   (Statista) or 2.81% (AppsFlyer)" all appear only on aggregators. Every origin path was blocked:
   AppsFlyer's benchmark data sits behind an interactive gate, Adjust's blog is behind a Vercel bot
   challenge, Statista is paywalled, Sensor Tower's report URLs 404. **No D1/D7/D30 benchmark is
   citable from this collector.** If the program needs it, someone with a Statista or AppsFlyer seat
   should pull it directly. Business of Apps aggregates them but is Tier D.
5. **Share of apps opened once and never again.** No method-disclosing source reached.
6. **Number of apps a typical user actively uses per month.** No method-disclosing source reached
   (data.ai's *State of Mobile* was the historical origin; data.ai is now Sensor Tower and the
   report is gated).
7. **Typical mobile app session length.** Same — not reachable.
8. **Parents abandoning shared family calendars / family-organizer apps; the "we tried a shared
   calendar and it didn't stick" pattern; share of US households sustaining a shared digital family
   calendar.** **NO DATA FOUND AT ANY TIER.** This is a real void, not a search failure on my part —
   there is no published measurement. Strong candidate for primary research; it is probably the
   single most decision-relevant unknown in this collector's domain.
9. **Nah (2004) tolerable-waiting-time in seconds.** The paper is peer-reviewed and heavily cited
   (673), but the abstract and full text are paywalled (DOI 10.1080/01449290410001669914; the AMCIS
   2003 landing page carries no abstract). The commonly-quoted "~2 seconds tolerable, up to ~38
   seconds with feedback" could not be verified and is **not** asserted anywhere above. Only NN/g's
   relayed "≈3× longer with an animated indicator" is used, and it is flagged as second-hand.
10. **Baymard method detail.** Baymard's public pages state findings without sample size or fielding
    window. The 11.3-fields benchmark and the 17%/18% abandonment reasons are used above as Tier C
    with that limitation stated; if the program wants them at higher confidence, the underlying
    Baymard research requires a paid seat.
11. **"Reducing form fields to 12–14 improves conversion by 20–60%" and "completion rates drop 4–6%
    for every field beyond the eighth."** Attributed to Baymard by third parties; **neither
    statement appears on the Baymard pages I fetched.** Likely laundered or a third party's
    interpolation. Do not cite. (The directional claim — fewer fields is better — *is* Baymard's;
    the specific per-field decay rate is not.)
12. **No generational cut exists for any finding in this collector.** Nothing in the complexity,
    wait-tolerance, or feature-fatigue literature is broken out by Gen Z / Millennial / Gen X
    parents. ATUS publishes by presence/age of children, not by parent birth cohort, in the summary
    release. Treat every number here as cohort-agnostic.
