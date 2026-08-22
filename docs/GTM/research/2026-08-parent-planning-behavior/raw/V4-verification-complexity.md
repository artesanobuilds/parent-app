# V4 — ADVERSARIAL VERIFICATION: P9 (complexity), P10 (generations), P11 (AI + parenting)

Verifier V4. Date 2026-08-21. Posture: refute first. Default verdict on uncertainty is UNVERIFIABLE.

**Environment limits, disclosed:** the program's shared WebSearch budget (200/200) was already exhausted
when this verification began, so every check below was done by direct WebFetch/curl of a named publisher
URL — no search. `bls.gov` returns HTTP 403 to this environment on every path, via both WebFetch and
curl, PDF and HTML. **The three ATUS findings could therefore not be verified at all** (see below); that
is an access failure on my side, not evidence against them, and it must be closed before publication.

---

## PART 1 — THE "SEVERE OUTLIER" QUESTION (answer first, because it governs the report)

### Verdict: the SEVERE OUTLIER labels are ANALYST JUDGEMENTS, not measurements. Three of the four are unevidenced as scored. The label must not appear in the final report.

P9 is unusually honest with itself and then undoes that honesty with a formatting choice. Its own
headline states there is "*no* published, method-disclosing screens→completion curve for mobile apps
that I could reach," and its own verdict cell for the onboarding row reads "**not because 10 screens is
provably fatal**." A cell that says "SEVERE OUTLIER" in bold, in a table column headed *Verdict*, sitting
directly beneath a Tier-graded findings table, will be read as a measured result. It is not one. Taking
the four in turn:

**1. "Onboarding: 8+N screens → SEVERE OUTLIER" — NOT EVIDENCED. This is an inference dressed as a
finding.** *Outlier* is a statistical word: it means far from a distribution. P9 established — correctly,
and I re-verified the kill — that **no distribution exists**. With no benchmark curve at any tier, there
is no set from which 10 screens can be an outlier, severe or otherwise. The two numbers actually cited in
that cell (Baymard's 17% checkout-length abandonment; RevenueCat's Day-0 cancellation figure) measure
neither screens nor onboarding. The reasoning — "the churn decision lands in session one, and session one
contains no product value" — is a good argument. It is an argument. Recommendation, not measurement.

**2. "A SECOND setup sequence → SEVERE OUTLIER" — NOT EVIDENCED, and the weakest of the four.** The
support is an a-fortiori step: 18% of cart abandoners quit rather than create an account, five editor
stops is a bigger ask than account creation, therefore worse. Two unstated assumptions carry the whole
weight: that abandonment scales monotonically with size of ask (Baymard measures no such gradient), and
that a self-reported *reason for abandoning a purchase* transfers to *a post-install setup screen*. Both
may be true. Neither is measured. This is also the cell the report calls "the highest-leverage single cut
in the report" — the strongest product recommendation in the document rests on the thinnest evidentiary
chain in it. That is exactly backwards, and it must be relabelled rather than removed: the cut is
probably right; the claim that data proves it is wrong.

**3. "1–2 minute wait → SEVERE OUTLIER (6–12× the threshold)" — PARTIALLY EVIDENCED; the arithmetic
survives, the severity grade does not.** This is the strongest of the four. Nielsen's 10-second limit is
real, canonical, and I verified it verbatim at NN/g ("about the limit for keeping the user's attention
focused on the dialogue," attributed to Miller 1968 / Card et al. 1991). 60–120 s genuinely is 6–12× it,
and P9's mitigation analysis (3× a seconds-scale tolerance does not reach 120 s) is sound reasoning. But
Nielsen's 10 s is a threshold for *attention on the dialogue* — it is not a churn threshold, and NN/g's
own prescription for waits above 10 s is to *handle* them (percent-done + completion estimate + visible
cancel), i.e. the literature treats >10 s as a design case, not a fatal defect. "6–12× the canonical
attention limit" is publishable verbatim. "SEVERE OUTLIER" adds severity the source does not carry.

**4. The three field-count rows (14/19 fields, 58 app-wide, 18 free-text on one screen) — ARITHMETICALLY
CORRECT against a real benchmark, but the benchmark is a different population.** See the checkout
question below. The count comparison is sound; the grade is not.

### Is comparing a parenting-app ONBOARDING to an e-commerce CHECKOUT methodologically fair?

**For the comparison.** Both are pre-completion, effortful, abandonable form sequences whose natural unit
is the discrete input. Baymard's 11.3-field average is the only large-scale, longitudinal, live-site
field-count benchmark that exists in public — I verified it on the source page along with the trend
(11.8 in 2021, 12.7 in 2019) and the 8-field recommendation. And P9's own asymmetry argument makes the
comparison *conservative against our own product*: checkout users have already decided to buy, so
matching a checkout's field count at lower intent is worse than parity, not equal to it. A defensible
sanity check.

**Against the comparison.** Five objections, of which the third is fatal to using it as a grade.
(1) *Motivation is unmeasured on both sides.* A checkout user has paid a search cost and is minutes from
a good they want; an onboarding user chose to install and may be equally motivated. Neither state is in
the data, so "high intent vs no value established" is an assertion, not a measured moderator.
(2) *The reward structure differs in kind, not degree.* Checkout's payoff is immediate, known and
externally priced; onboarding's is deferred and unknown. That difference is the entire reason the fields
are expensive — and Baymard measures nothing about it, so the benchmark is silent on the mechanism the
report is actually arguing.
(3) *Field type differs, and it cuts against the report's own case in a way it did not notice.* A
checkout's 11.3 fields are dominated by known-answer, browser-autofillable data (name, address, card).
Our onboarding fields are generative — a child's interests, free-text notes — which cost far more per
field. So the 1.2–1.7× *count* ratio materially **understates** the effort ratio. The honest correction
makes the product look worse, not better, but it also means the count comparison is not measuring the
same quantity on both sides, which is precisely what disqualifies it as a score.
(4) *Domain and geography transfer.* Baymard's population is US+European e-commerce sites, desktop and
mobile web. Ours is a US native iOS app. Cross-domain, cross-geography, cross-platform.
(5) *Method disclosure.* Baymard's public pages state neither site count nor participant n — P9 tags this
correctly as Tier C, partial method. A Tier C source with undisclosed n cannot carry a "SEVERE" grade.

**Verdict: fair as an order-of-magnitude sanity check; unfair as a scored judgement.** Objections 1 and 3
do not cancel — 3 says the count understates our burden, 1 says the intent premise is unresolvable — so
the net is not "it balances out," it is "the comparison establishes direction and rough scale and nothing
finer." Publish it as a comparison; do not publish it as a grade.

### How the final report MAY and MAY NOT phrase these judgements

**Permitted, verbatim-safe:**
- "Our onboarding asks 14 fields for one kid and 19 for two — more than the 11.3-field average
  e-commerce checkout (Baymard, 2024) and roughly double Baymard's 8-field recommendation — and asks them
  before the parent has seen anything the app does. The inputs are also of a costlier type: a checkout's
  fields are mostly autofillable, ours are generative."
- "The 1–2 minute Planner wait is 6–12× Nielsen's 10-second limit for holding attention on a task
  (Nielsen 1993, from Miller 1968 / Card et al. 1991). NN/g's rule above 10 s is a percent-done indicator
  plus a completion estimate and a visible cancel — not a spinner."
- "No published screens-to-completion curve exists at any tier. The most-repeated figure in this space —
  15% completion loss per screen beyond five, attributed to Appcues — is verified absent from Appcues'
  own user-onboarding-metrics page; the only benchmark that page states is an unsourced 'below 30% for a
  core onboarding checklist signals friction.' Do not cite the 15% figure."
- "On the evidence available, we judge the second setup sequence the highest-leverage single cut. This is
  our call, argued from adjacent data, not a measured result."

**Forbidden:**
- The strings "SEVERE OUTLIER" and "AT-RISK" anywhere in the report, and any grade presented inside or
  adjacent to a Tier-graded findings table.
- Any phrasing implying that a screen count, tap count, view count, or the second setup sequence has been
  measured against a benchmark distribution. None has.
- Presenting Baymard's 18% account-creation figure as evidence *for* the second-setup-sequence verdict.
  It may be cited as an analogy, explicitly labelled as one.

**Required if the BENCHMARK VS. OUR APP table is carried forward:** move it under a heading that reads
*Analyst judgement, not measurement*, and rename the column `Verdict` → `Analyst call` with a second
column `Evidence strength: direct / adjacent / none`. Under that scheme: fields = adjacent; wait =
direct-on-threshold; screens, taps, views, second setup sequence, 12 knobs = none.

---

## PART 2 — CLAIM-BY-CLAIM

| Claim | Report | Verdict | What I found | Corrected value | URL |
|---|---|---|---|---|---|
| Appcues "15% drop per screen beyond five" is unsourceable | P9 §2.1 KILLED | **KILL UPHELD** | Fetched the correct page (`/blog/user-onboarding-metrics-and-kpis`). The 15% figure does not appear. Only benchmarks present: activation 25–50%; D30 retention 20–40% consumer / 40–70% B2B; "completion rates below 30% for a core onboarding checklist usually signal significant friction" — matching P9's description exactly. Also checked `/blog/saas-onboarding-screens`: no per-screen figure. | Kill stands; do not cite the 15% | https://www.appcues.com/blog/user-onboarding-metrics-and-kpis |
| Thompson/Hamilton/Rust 62.3 / 28.5 / 9.2%, n=130 | P9 #1 | **VERIFIED EXACT** | PDF pp. Study 1: "62.3%… 28.5%… 9.2%"; "One hundred and thirty undergraduate students… 50.8% females, Mage = 20.55"; models are 7 / 14 / 21 features, Latin-square counterbalanced | — | https://thearf-org-unified-admin.s3.amazonaws.com/MSI/2020/06/MSI_Report_05-101.pdf |
| Free choice → mean 19.64/19.58 of 25, median 20, ~half >80%, n=141 | P9 #2 | **VERIFIED EXACT** | "19.64 (sd = 4.83)… 19.58 (sd = 4.28)… median… was 20"; "One hundred forty-one… 55.3% females, Mage = 21.07" | — | same |
| Capability F(1,186)=5.09 p=.025; usability F(1,185)=33.13 p=.000; n=190 | P9 #3 | **VERIFIED EXACT** | Verbatim in Study 3; n=190, 52.1% males, Mage=20.54; usability result is the features main effect in a 2×2 ANCOVA with expertise covariate — P9's framing is correct | — | same |
| Usability under-weighted pre-use, χ²(1)=4.48 p=.034 | P9 #4 | **VERIFIED EXACT** | Verbatim | — | same |
| Nielsen 0.1 / 1.0 / 10 s, from Miller 1968 & Card 1991 | P9 #8 | **VERIFIED** | All three limits and both attributions verbatim; 10 s = "limit for keeping the user's attention focused on the dialogue" | Note: NN/g says *dialogue*, P9 says *task* — keep NN/g's wording | https://www.nngroup.com/articles/response-times-3-important-limits/ |
| Myers 1985: 86% liked progress bars, n=48 students | P9 #9 | **VERIFIED** (at the relay) | CMU HCII page: "asked 48 students…", "Eighty-six percent said they liked the bars." Primary 1985 paper not fetched | Cite as relayed via CMU, not as read | https://www.hcii.cmu.edu/news/nyt-highlights-myers-role-popularizing-progress-bars |
| Nah 2004: willing to wait ~3× longer with an animated indicator | P9 #10 | **VERIFIED as relayed** | NN/g states it verbatim: "willing to wait on average 3 times longer than those who did not see any progress indicators." Paper itself still paywalled; P9's second-hand flag is correct and should be retained | Keep the second-hand flag | https://www.nngroup.com/articles/progress-indicators/ |
| Design thresholds: spinner 2–10 s | P9 #11 | **CORRECTED** | NN/g says "a looped indicator for delays of **2–9 seconds** and a percent-done indicator for delays of 10 seconds or more" | 2–9 s, not 2–10 s | same |
| Checkout avg 11.3 fields (11.8 / 12.7 prior); optimum ≈8 | P9 #12 | **VERIFIED, with a wording correction** | "the average in 2024 was 11.3 form fields"; 11.8 (2021), 12.7 (2019); "most sites need only 8 form fields in total." Site count and participant n genuinely absent from the public page — P9's Tier C tag is right | Say "Baymard's recommendation is 8 fields," not "tested optimum" | https://baymard.com/blog/checkout-flow-average-form-fields |
| 17% too long/complicated, 18% account creation | P9 #13 | **VERIFIED** | Both exact; full list also shows extra costs 40%, slow delivery 20%, card security 19%, site errors 17%. n and fielding window confirmed absent | — | https://baymard.com/lists/cart-abandonment-rate |
| 82% of trial starts happen on install day | P9 #14 | **VERIFIED EXACT** | "82% of trial starts occur the same day a user installs an app, which is even higher than last year!" Dataset "75,000 Subscription Apps" | — | https://www.revenuecat.com/state-of-subscription-apps-2025/ |
| **55% of ALL trial cancellations occur on Day 0** | P9 #15 | **REFUTED AS STATED** | Source: "**55.4% of all 3-day trial cancellations** occur on Day 0," with "84% of 3-day trial cancellations happen between Day 0 and Day 1." P9 dropped the *3-day trial* scope, generalising a 3-day-trial statistic to all trials. Longer trials mechanically cannot concentrate cancellations on Day 0 the same way | "55.4% of **3-day-trial** cancellations occur on Day 0" | https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026 |
| 12-mo retention yearly 44.1 / monthly 17.0 / weekly 3.4 | P9 #16 (first half) | **VERIFIED EXACT** | Verbatim in the 2025 report | — | https://www.revenuecat.com/state-of-subscription-apps-2025/ |
| "Social & Lifestyle shows the lowest retention of any category across all plan types" | P9 #16 (second half) | **UNVERIFIABLE** | Not present on either public RevenueCat page I could reach (2025 report page, 2026 blog, 2026 report landing). Likely in the gated full PDF. P9's interpretation ¶7 leans on it ("a ceiling no simplification lifts") | Drop or re-source before use | — |
| Hard paywall 10.7% vs freemium 2.1% by day 35 | P9 #18 | **VERIFIED EXACT** | Verbatim | — | https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026 |
| ATUS 2024: 3.0 h vs 4.5 h leisure (employed, child <6 vs no child <18) | P9 #5 | **UNVERIFIABLE (access)** | `bls.gov` returns HTTP 403 to this environment on every path — the USDL-25-1060 PDF, the archived HTML release, and `atus.nr0.htm` — via WebFetch and via curl with browser headers. Archive.org is blocked to this tool. Not refuted; **not confirmed either.** | Re-verify at BLS before publication | https://www.bls.gov/news.release/archives/atus_06262025.pdf |
| ATUS 2024: 5.2 h/day secondary childcare, 1.8 h of it during leisure | P9 #6 | **UNVERIFIABLE (access)** | As above. Additional caution for the synthesist: ATUS secondary childcare is defined only for household children **under 13** and excludes time already counted as primary childcare — so "1.8 h/day of leisure occurs while supervising a child" is a legitimate restatement *only* if the 1.8 h is measured within leisure-and-sports time. Verify the table cell, not just the number | Re-verify | same |
| ATUS 2024: 2.5 h/day primary childcare (women 3.0 / men 2.0) | P9 #7 | **UNVERIFIABLE (access)** | As above | Re-verify | same |
| Pew AI by age: ever-use 66 / 61 / 42 | P10 #1, P11 #3 | **VERIFIED EXACT** | 18–29 66%, 30–49 61%, 50–64 42%, 65+ 23%; n=5,119, Feb 17–23 2026 | — | https://www.pewresearch.org/internet/2026/06/17/how-opinions-and-use-of-ai-differ-by-age/ |
| **Daily use PEAKS at 30–49 (34%) not 18–29 (31%)** | P10 #2, P11 #4 | **VERIFIED EXACT** | 31 / 34 / 19 / 7. The counterintuitive inversion is real and correctly reported | — | same |
| **18–29 most negative on AI: 48% societal / 37% personal** | P10 #8, #9 | **VERIFIED EXACT** | 48 / 39 / 38 / 35 and 37 / 30 / 28 / 28 | — | same |
| Info-seeking 54/53/37; emotional 20/13/4; medical 27/25/17; confidence 31/23/12; AI summaries 72/68/59 | P10 #3–#7 | **VERIFIED EXACT** | All match | — | same |
| Smart speaker 33/41/36; smartwatch 44/44/35 | P10 #26, #27 | **VERIFIED EXACT** | Match | — | same |
| Facebook inverts: 68 / 80 / 74 | P10 #14 | **VERIFIED EXACT** | 68 / 80 / 74 / 57; n=5,022, Feb 5–Jun 18 2025 | — | https://www.pewresearch.org/internet/fact-sheet/social-media/ |
| Instagram 80/62/40, TikTok 63/44/30, YouTube 95/92/85, Reddit 48/35/16, Snapchat 58/31/13, X 33/25/16, WhatsApp 37/40/30, Threads 15/10/6 | P10 #12–#18 | **VERIFIED EXACT — all nine platforms** | Every figure matches the fact sheet | — | same |
| Pew's flagship parenting study (n=3,757) publishes ZERO parent-age crosstabs | P10 #35 | **VERIFIED, with one addition and one caution** | n=3,757, Sept 20–Oct 2 2022 confirmed. Breakouts published: gender, race/ethnicity, income, child age — **plus religious affiliation and party ID**, which P10 omits. No parent-age breakout anywhere in the report. Caution: this means *not published*, not *not collected* — ATP demographics include age | Say "publishes no parent-age breakout," not "no parent-age data exists" | https://www.pewresearch.org/social-trends/2023/01/24/parenting-in-america-today/ |
| "Gen Z spends $377/mo on subscriptions" is relabelled UK data | P10 §2.1 KILLED | **KILL UPHELD, and stronger than stated** | Visa/Basis: UK consumers, n=4,152, Nov–Dec 2024. £305 Gen Z / £261 Millennials / £91 Gen X / £108 Boomers — exactly as P10 reported, including the Gen X < Boomer inversion the laundered US version silently repairs. **Additional disqualifier P10 missed: Visa's own Gen Z band is ages 13–28**, i.e. it includes minors, so it cannot map to a US parent cohort even after currency conversion | Kill stands; add the 13–28 band as a second reason | https://corporate.visa.com/en/sites/visa-perspectives/trends-insights/gen-z-boosts-subscription-economy-tripling-spend-from-older-generations.html |
| "No parent-age crosstab of AI use exists" (implied by P10's NONE cells) | P10 dimension table | **NARROWED — a live lead exists** | Common Sense Media's *Generation AI* report states directly: "Within subgroups of parents, we see major divides in AI usage, with **generational**, gender, and racial differences." The crosstab was run; the report text does not publish the numbers (Figure 12 is an image). A data request to Lake Research / Echelon would likely produce a Tier B parent-age AI-use crosstab | Change "no data exists" → "not published; obtainable on request from Lake Research/Echelon" | https://www.commonsensemedia.org/sites/default/files/research/report/commonsensemedia_generationai.pdf |
| Pew 2026: 49% of US adults use chatbots, ~24% daily, n=5,119 Feb 17–23 2026 | P11 #1, #2 | **VERIFIED** | "49%… up from a third in 2024"; "about one-quarter use these tools daily, with 12% accessing them several times per day" | — | https://www.pewresearch.org/internet/2026/06/17/americans-and-ai-2026-chatbots-smart-devices-and-views-on-impact/ |
| ChatGPT 44% of adults, "double 2023's 22%" | P11 #7 | **CORRECTED** | Pew: "more than double the 2023 figure of **18%**" | 18%, not 22% | same |
| Parents 79% vs non-parents 54%; 29% vs 15% daily; n=5,031, Apr 2025 | P11 #10 | **VERIFIED EXACT** | All four figures and the method verbatim | — | https://menlovc.com/perspective/2025-the-state-of-consumer-ai/ |
| To-do lists 18%, meal planning 16%, emails 19%, research 18% | P11 #11 | **VERIFIED EXACT** | Match (page also lists "writing support 18%") | — | same |
| Childcare management 34% = #1 parent AI use | P11 #12 | **VERIFIED** (34% confirmed; "#1" is Menlo's framing) | — | — | same |
| ~3% of consumer AI users pay; ChatGPT ~5% of weekly actives; $12B spend | P11 #26 | **VERIFIED** | "about 3% of the 1.8 billion global AI users"; ~5%; $12B; user base stated as 1.7–1.8B | — | same |
| **AI apps: 12-mo payer retention 21.1% vs 30.7%; trials 8.5% vs 5.6%; LTV $30.16 vs $21.37; refunds 4.2% vs 3.5%; churn ~30% faster** | P11 #27, #28 | **PARTIALLY REFUTED / UNVERIFIABLE — and misapplied. See the note below the table.** | At the cited blog URL: "21.1", "30.7", "8.5%", "5.6%", "4.2%", "3.5%" and the word "refund" **all absent**. What the blog does say: LTV "$30.16 median vs. $21.37 median" (verified), "AI **monthly plans** retain 36% worse over 12 months," "churn **36%** faster." What the report landing page says: "41% more revenue per payer, but they churn **30%** faster." RevenueCat's own two public surfaces disagree (36 vs 30), and 21.1/30.7 = 31% worse, matching neither | See note | https://www.revenuecat.com/blog/growth/subscription-app-trends-benchmarks-2026 ; https://www.revenuecat.com/state-of-subscription-apps/ |
| Chatterji/NBER: practical guidance 28.1%, writing 28.3%, info 21.3% | P11 #8 | **REFUTED as stated** | None of the three decimals appears in WP 34255. The paper reports Practical Guidance "constant at roughly **29%**," Writing declining 36%→24%, Seeking Information growing 14%→24%, top three ≈77–80% of all conversations. Also self-inconsistent as written: P11 calls practical guidance "the single largest" while listing writing higher (28.3 > 28.1) | "Practical Guidance is the most common conversation topic at ~29% of messages (Chatterji et al., NBER WP 34255, ~1.1M sampled conversations May 2024–Jun 2025, global)" | https://www.nber.org/system/files/working_papers/w34255/w34255.pdf |
| Non-work rose to 73% by June 2025 from 53% | P11 #9 | **VERIFIED** | "53% of messages were not related to work in June 2024, which climbed to 73% by June 2025." (Abstract phrases it as "more than 70%" as of July 2025 — use the body figure with its date) | — | same |
| Common Sense: 49% of parents use AI often/sometimes, 49% rarely/never | P11 #16 | **VERIFIED EXACT** | Verbatim, p.11. Method: Lake Research Partners + Echelon Insights, online, Nov 17–26 2025, 1,244 parents incl. oversamples, base n=843 | — | https://www.commonsensemedia.org/sites/default/files/research/report/commonsensemedia_generationai.pdf |
| Common Sense 64% / 68% / 68%D-70%R / 84-81-82% / 75% / >80% / 58% | P11 #17–#20 | **VERIFIED EXACT — every figure** | All located verbatim in the PDF | — | same |
| Lurie: 81% used AI for a parenting task; 43% weekly, 15% daily; 53/49/43/42/37; 58 min/wk; 50/38/37 distrust; 31% over instinct; n=1,004 Apr 2026 | P11 #13–#15, #22–#24, #38 | **VERIFIED as-published; Tier C caveats CONFIRMED** | Every figure matches. Disclosed: n=1,004 parents of ≤17s, April 2026, 34% male / 65% female / 1% other, mean age 38. **Not disclosed: panel provider, sampling frame, margin of error, weighting.** Publisher is a hospital marketing blog | Keep Tier C; keep the discount | https://www.luriechildrens.org/en/blog/ai-parenting-statistics/ |
| Pew teen/parent: 64% of teens use chatbots; ~half of parents think so | P11 #25 (first half) | **VERIFIED** | 64% of teens; 51% of parents; n=1,458 teens and their parents, Sept 25–Oct 9 2025, MoE ±3.3pp | Add n and MoE, which P11 omits | https://www.pewresearch.org/internet/2026/02/24/what-parents-say-about-their-teens-ai-use/ |
| **"Only 4 in 10 parents have discussed chatbots with their child"** | P11 #25 (second half) | **REFUTED** | Pew: **just over half** of parents report having talked with their teen about chatbots. P11 states the opposite direction | "Just over half of parents have talked with their teen about chatbots" | same |
| **Gemini "Personal Intelligence" free-tier rollout began Mar 17 2026** | P11 #29 | **UNVERIFIABLE — the date is not at the cited source or any Google source I could reach** | The cited blog post states: "Launching as a beta in the U.S." Jan 14 2026, "rolling out over the next week to eligible **Google AI Pro and AI Ultra subscribers**." No free-tier date, no March 2026 mention. Gemini's official release notes date the launch **2026.01.20**, same Pro/Ultra scope, and contain **no March 2026 Personal Intelligence entry** (I enumerated every 2026.02.* and 2026.03.* entry; the March entries are chat-history import on 03.26). What IS verifiable today: Google's product page now says Personal Intelligence "is currently rolling out as a beta to eligible users globally" with **no subscription tier stated** — only an 18+ requirement and EEA/CH/UK/Nigeria exclusions | "By August 2026 Personal Intelligence is in beta to eligible users globally with no stated subscription requirement (Google product page); it launched Jan 2026 restricted to AI Pro/Ultra. No published free-tier rollout date located." | https://blog.google/innovation-and-ai/products/gemini-app/personal-intelligence/ ; https://gemini.google/release-notes/ ; https://gemini.google/overview/personal-intelligence/ |
| Google's launch example is family/spring-break planning | P11 #30 | **VERIFIED EXACT** | "By analyzing our family's interests and past trips in Gmail and Photos, it skipped the tourist traps…" | — | blog.google URL above |
| Google Assistant retires September 2026 | P11 #33 | **VERIFIED — strongest of the three platform claims** | September 4 2026; Android phones/tablets, Wear OS, headphones, Android Auto projected; Google-built-in car systems exempt. Sourced to a Google email to users quoted by 9to5Google. Tier C (trade press on vendor announcement) — correctly tagged | Add "Sept 4" and the car-systems exemption | https://9to5google.com/2026/08/04/google-assistant-september-2026-shutdown/ |
| **Apple personal-context Siri ships September 2026, free, iPhone 15 Pro and newer** | P11 #32 | **REFUTED** | Apple Newsroom, June 8 2026, states availability as **"beta later in 2026"** for supported devices set to English, with developer testing immediately. **No September date. No "at no additional charge" statement.** Device list: iPhone 16+, iPhone 15 Pro/Pro Max, iPad mini (A17 Pro), M1+ iPads/Macs, Vision Pro, Watch S9+/Ultra 2+. Personal context and Spotlight/App-Toolbox integration are confirmed | "Apple announced Siri AI with personal context on June 8 2026; **beta later in 2026**, supported devices iPhone 15 Pro and newer. No dated public release." | https://www.apple.com/newsroom/2026/06/apple-introduces-siri-ai-a-profoundly-more-capable-and-personal-assistant/ |
| KU study: parents rated ChatGPT text more trustworthy than expert text, n=116 | P11 #37 | **VERIFIED** | n=116 parents 18–65, blinded cross-sectional rating, *Journal of Pediatric Psychology*, 2024 | — | https://news.ku.edu/news/article/study-finds-parents-relying-on-chatgpt-for-health-guidance-about-children |

---

### Note: why the RevenueCat AI-retention number cannot carry the financial modelling advice

P11 ¶6 tells the program to model a **$99–149/year** product at "AI-app retention (~21%)". Four problems,
in ascending severity:

1. **The number is not at the cited URL.** Neither 21.1% nor 30.7% appears on the cited blog or on the
   report landing page. Both live, if anywhere, in RevenueCat's gated full report. Cite what you can open.
2. **RevenueCat's public surfaces disagree with each other** — "churn 36% faster" (blog) vs "churn 30%
   faster" (report page) — and 21.1/30.7 is a 31% gap, matching neither. Somebody is rounding a different
   quantity; we do not know which.
3. **The published comparison is scoped to monthly plans.** The blog's exact sentence is "AI **monthly
   plans** retain 36% worse over 12 months than traditional apps." It is not an all-payer figure.
4. **Applying it to an annual product is a plan-type category error, and it is large.** RevenueCat's own
   2025 data — P9 #16, which I verified verbatim — puts 12-month retention at **44.1% for yearly plans vs
   17.0% for monthly**. A 2.6× plan-type effect dwarfs the ~1.3–1.5× AI-vs-non-AI effect. Taking a
   monthly-plan AI number and applying it to a $99–149/yr annual subscription plausibly understates
   retention by roughly a factor of two, which would invert the LTV conclusion.

**Corrected guidance the report may use:** "RevenueCat 2026 reports that AI-powered apps monetise better
up front (41% more revenue per payer; Year-1 LTV median $30.16 vs $21.37) but churn faster — the company
states 30% faster on its report page and 36% worse 12-month retention for AI *monthly* plans on its blog.
The AI penalty is real and directionally material; the precise magnitude is not publicly resolvable and
the published figure is monthly-plan-scoped. **Do not model an annual-plan product on a monthly-plan
retention number.** Model from the yearly-plan baseline (44.1% at 12 months, RevenueCat 2025) with an
explicit, sensitivity-tested AI haircut, and label the haircut as an assumption."

---

### Note: the P11 "32-point contradiction" (Lurie 81% vs Common Sense 49%)

**Discounting Lurie is correct, but P11's reason is only half the reason, and the framing is wrong.**

The Tier-C discount is justified and I confirmed the grounds first-hand: Lurie discloses n and month but
no panel provider, no sampling frame, no margin of error, no weighting scheme, and the publisher is a
children's hospital's marketing blog with an interest in the "parents rely on AI" narrative. That is
enough to keep it out of any load-bearing position.

But **the 32-point gap is substantially a construct mismatch, not a methodological contradiction**, and
P11 does not say so. The two instruments do not ask the same question:

- **Lurie:** *ever used AI for a parenting task* — a lifetime-incidence measure on a parenting-specific
  behaviour.
- **Common Sense:** *use AI often/sometimes* (vs rarely/never) — a **frequency** measure on general AI use.
- **Pew:** *ever used an AI chatbot* — lifetime incidence, all adults, not parents.

Lifetime incidence is always higher than "often/sometimes". Comparing 81% ever-use against 49%
often/sometimes and calling the difference a contradiction manufactures a conflict out of two compatible
numbers. Note also that Lurie's own frequency split — 43% weekly, 15% daily — is **not** wildly out of
line with Common Sense's 49% often/sometimes; the instruments broadly agree once you compare like with
like. What genuinely is implausible in Lurie is the attitudinal battery P11 already flags (90% "AI makes
parenting easier", 91% "boosts confidence"), whose uniformity is the real tell.

**Recommended rewrite:** "Estimates of parental AI use range from 49% (Common Sense, *often/sometimes*,
n=843, Nov 2025) to 81% (Lurie, *ever used for a parenting task*, n=1,004, Apr 2026). Most of that spread
is a difference in what was asked — lifetime incidence versus frequency — not a disagreement about
reality; the two sources' frequency figures broadly agree. Plan against Common Sense's 49% and Menlo's
nationally-weighted 29%-daily, and treat Lurie's attitudinal figures as unusable."

Corollary: **P11 ¶2's headline "the adoption numbers contradict each other by 32 points and the gap is
methodological" should not be carried into the synthesis as written.**

---

## PART 3 — RESIDUAL RISKS FOR THE SYNTHESIST

1. **ATUS is unverified.** Three Tier A findings (P9 #5–#7) and the whole time-budget argument in P9 ¶5
   rest on a source this verification could not open. Someone must open `bls.gov` and confirm the table
   cells before these appear in a deliverable.
2. **Two of P11's three platform-absorption dates do not survive contact with the primary source.** Only
   the Google Assistant shutdown (Sept 4 2026) is a firm published date. Apple's is "beta later in 2026";
   Gemini's free-tier date does not exist in any Google source I could reach. The sentence "the platform
   shipped the first two courses in the last six months and the third lands the month after this research
   is filed" is not supportable as written and must be softened to "Google has retired Assistant on a
   published date; Apple and Google have both shipped or announced personal-context assistants, with
   Apple's still in beta and undated."
3. **P10 is the cleanest of the three files.** Every Pew figure I checked — 20 of them, across two
   instruments — matched exactly, including both counterintuitive corrections (Millennial daily-use peak;
   Gen Z most negative) and the Facebook inversion. Both of its kills hold. Its one over-reach is the
   blanket "no parent-age crosstab exists," which should be narrowed to "not published."
4. **Nothing in P9's onboarding-length case is a measurement.** Part 1 stands as the governing verdict.
