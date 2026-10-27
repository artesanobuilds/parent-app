# GTM Market Research: AI Parenting Platform ("MVP") — Wedge, Pricing, and 90-Day Validation Plan

> **⚠️ Superseded in part (2026-07-07).** This report was subsequently stress-tested by a 5-persona adversarial review (`mvp-idea-roast.md`) and a verification research pass. The current, canonical strategy is **`gtm-strategy.md`** — it revises this report's $199 price anchor, the coach-as-retention thesis, the two-parent adoption assumption, and the launch timing. Known corrections to this report: Milo's shutdown was **January 2026** (not 2024); the co-parenting "wedge" survives but is now **solo-first** by design.

## Executive Summary

Miguel has built a broad, polished AI parenting platform in the exact inverse of the playbooks he admires — product-first, in silence, with zero demand signal. The correction is not more features; it is a beachhead. Based on the evidence, the recommended wedge is the **"family chief-of-staff" / mental-load killer built for the co-parenting (two-household) family** — a hybrid of W3 (activity/camp logistics) as the acquisition wedge and W2 (co-parenting) as the sharp ICP, with W1 (the AI coach that knows your family) as the retention engine. The kids' voice companion (W4) should be **hidden from GTM entirely** for now on regulatory grounds.

**The opportunity in numbers.** The global parenting-apps market is estimated at roughly $1.7–2.8 billion in 2025 depending on the analyst (estimates conflict; see Section 1), growing ~12% CAGR. Proof of budget is strong and specific: Good Inside (Dr. Becky) passed $34M revenue in 2025 (+50% YoY) with 100,000+ paid subscribers at $23.25–$28/mo, having raised just $10.5M (Inspired Capital, 2023) and otherwise bootstrapped; OurFamilyWizard serves ~1M+ families at $149.99–$299.88/yr per parent and is PE-backed by Spectrum Equity (2020); Skylight has 9.3M users and 99% YoY revenue growth; Cozi has 20M+ registered users. The co-parenting sub-segment is projected to be the fastest-growing slice of the parenting-app market (Roots Analysis, 2025).

**The three biggest risks.** (1) **The "ChatGPT is free" problem** — parents already use ChatGPT for parenting advice and trust it (KU 2024 study), and Milo, an OpenAI-endorsed "Family AI" copilot, shut down in 2024 precisely because, per its post-mortem, "the gap between 'a family-specific AI wrapper at $40/month' and 'ChatGPT with a good system prompt at $20/month' became difficult to justify… Building on a platform whose owner also competes in your application layer is a strategy with a countdown clock." (2) **Regulatory exposure** from the kids' voice feature under the amended COPPA rule (compliance deadline April 22, 2026) and the FTC's September 11, 2025 Section 6(b) inquiry, which issued orders to seven companies (Alphabet/Google, Character.AI, Meta/Instagram, OpenAI, Snap, and xAI) on chatbots "acting as companions." (3) **Zero audience + solo founder with ~10 hrs/week** — distribution, not product, is the binding constraint; RevenueCat's 2026 data shows apps launched in 2025 or later account for just 3% of subscription revenue, and only 17.3% of newly launched apps reach $1K MRR within two years.

**The one thing to do first.** Build and ship a single lead magnet — the "Family Snapshot" quiz funnel — gated by email, and run it against the 200-email bar before writing another line of feature code.

---



## Section 1 — Market Landscape & Sizing



### Headline market size (sources conflict — flagged)

Analyst estimates for the global parenting-apps market vary widely, which is itself a finding worth noting: this is a loosely-defined category and no single number should be trusted.


| Source (year)                         | 2025 market size              | CAGR       | Notes             |
| ------------------------------------- | ----------------------------- | ---------- | ----------------- |
| Business Research Insights (Nov 2025) | $1.06B (2025) → $1.27B (2026) | 20.37%     | Lowest base       |
| Roots Analysis (2025)                 | $1.94B (2025)                 | 12.0%      | To $6.02B by 2035 |
| Research & Markets / TBRC (2025)      | $1.71–1.72B (2025)            | 11.4–12.8% |                   |
| Dataintelo (Q4 2025)                  | $2.8B (2025)                  | 7.6%       | Highest base      |


**Best estimate:** ~$1.7–2.0B globally in 2025 for "parenting apps" as a category, growing low-double-digits. North America is ~36–45% of the market (Dataintelo: $1.02B, 36.5%). The wide spread reflects definitional disagreement (some include hardware/monitoring, some pregnancy trackers).

### TAM/SAM/SOM using Donnelly's formula (customers × annual spend)

These are **my constructed estimates** using US household counts and observed pricing; treat as order-of-magnitude, not precise.

- **US households with children under 18:** ~40 million (US Census, widely cited).
- **(a) Parenting apps overall (US):** If ~40M families and even 15% pay ~$60/yr → ~$360M/yr US serviceable spend. TAM if all 40M × $60 = $2.4B.
- **(b) AI parenting-coach / advice apps:** Good Inside alone proves ~100K subscribers × ~$276 = ~$28M+ from one brand. If the coaching niche captures 2M US families × $150 avg → ~$300M TAM.
- **(c) Co-parenting (divorce/custody):** ~22M children live in single-parent households (Dataintelo, citing ~50% divorce rate). Estimate ~10–12M separated-parent households. At OFW-style pricing ($150–$300/yr per parent) and even 10% penetration → 1–1.2M paying parents × $200 = ~$200–240M SAM. This is a proven, court-reinforced budget.
- **(d) Family organization / calendar / chief-of-staff:** Cozi (20M+ users), Skylight (9.3M users, hardware+sub). Large but low-ARPU on software alone ($39/yr Cozi Gold; $79/yr Skylight Plus).
- **(e) Kids' AI companions / kids' educational AI:** Nascent and volatile — Moxie ($799 hardware) shut down 2024; Curio (plush toys, no subscription). High-risk category.
- **(f) Camp & activity discovery/booking:** ActivityHero claims 4M+ families; Sawyer marketplace for providers. Take-rate/marketplace model, seasonal (Jan–Apr peak).



### The rising tide (the "C" in CODE)

The consumer trend this product should ride is the collision of three well-documented forces:

1. **The mental-load discourse has gone mainstream and is quantified.** A University of Bath study (published Oct 23, 2025; Dr. Ana Catalano Weeks and Leah Ruppanner, in the *Journal of Marriage and Family*; 2,133 partnered heterosexual US parents) found mothers carry 67% more items on their mental to-do list — an average of 13.72 tasks versus 8.2 among fathers; a separate 3,000-parent analysis found mothers handle 71% of household mental-load tasks. Fair Play/USC data (cited Motherly, Aug 2025) put mothers at 72.57% of cognitive labor. Skylight's Mental Load Report: the mental load consumes over 30 hours weekly.
2. **AI adoption among parents is already here.** A 2024 University of Kansas study (116 parents) found parents rated ChatGPT health advice as more trustworthy than expert-written content. ~30% of parents of school-age kids used ChatGPT by 2023 (Futurism, Nov 2025). Parents call it a "third co-parent" (GMA/ABC, Aug 2025).
3. **Millennial/Gen-Z normalization of the "parenting coach."** Good Inside ($34M rev), Big Little Feelings (3.5M IG followers, 400K course-takers) prove parents will pay experts for guidance that used to be free.

**So what this means for Miguel:**

- The market is real and growing, but "parenting apps overall" is too diffuse to attack — money concentrates in **specific, acute, budgeted pains** (co-parenting logistics, sleep, behavior coaching).
- The mental-load narrative is his single best content and positioning vein — culturally hot, data-backed, emotionally resonant.
- He should **size his own beachhead precisely** (separated-parent households × willingness-to-pay from his own funnel) rather than lean on the conflicting top-line reports.

---



## Section 2 — Competitive Deep Dive (Proof of Budget)



### Co-parenting


| App                                         | What it does                                                                        | Pricing (2026)                                                                                | Model / scale                                                                           | Gap it leaves                                                                                 |
| ------------------------------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| **OurFamilyWizard**                         | Court-admissible messaging, shared calendar, expense tracking, Info Bank, ToneMeter | $149.99 (Essential) / $216 (Premium) / $299.88 (Max) per parent/yr; no monthly, 30-day refund | PE-backed (Spectrum Equity, 2020, terms undisclosed); ~1M+ families; acquired Cozi 2022 | Legacy UX ("dated," "difficult"); no real AI coaching; conflict-documentation focus, not help |
| **TalkingParents**                          | Recorded communication, calendar                                                    | ~$7/parent/mo entry, up to ~$700/yr for two on Ultimate                                       | Court-record niche                                                                      | Documentation, not guidance                                                                   |
| **AppClose**                                | Messaging, calendar, expenses                                                       | Dropped free model Jan 2026 → $7.99–8.99/mo/parent                                            | Tens of thousands of users                                                              | Now monetizing; still logistics-only                                                          |
| **2houses / Custody X Change / coParenter** | Scheduling, custody plans; coParenter adds live human mediators                     | Custody X Change ~$144/yr (Bronze); coParenter $12.99/mo                                      | Various                                                                                 | Point tools; no persistent family intelligence                                                |


**What users love/hate (from reviews cited):** Love = "everything documented in one place," court-admissibility, ToneMeter, *"It has truly kept my children out of our divorce drama."* Hate = OFW's dated mobile UX; per-parent double-billing; PDF export fees; requirement that both parents join.

### Family organization / calendar


| App                                   | Pricing                          | Scale                                                                                | AI posture                                                                               | Gap                                                                                             |
| ------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **Cozi**                              | Free (ads) / Cozi Gold $39/yr    | 20M+ registered users                                                                | Minimal; email-only extraction                                                           | Nerfed free tier (30-day calendar limit, May 2024) → Trustpilot ~2.1★; one-way Google sync only |
| **Skylight (Calendar + Sidekick AI)** | Hardware $279–$629 + Plus $79/yr | 9.3M users; 99% YoY rev growth; $50M debt facility (SG Credit + Wingspire, Apr 2025) | "Sidekick": photo/PDF/email → calendar events, meal plans                                | Hardware-anchored; home-bound; not a coach; not co-parent-aware                                 |
| **Milo ("Family AI")**                | Was ~$40/mo                      | **SHUT DOWN 2024**                                                                   | GPT-4 SMS copilot; OpenAI-endorsed (Aug 2023), raised $1.3–2.5M, never disclosed revenue | Cautionary tale — see below                                                                     |
| **Maple / Jam / Hearth Display**      | Various (Hearth ~$699 + sub)     | Smaller                                                                              | Emerging                                                                                 | Space is heating up                                                                             |




### Parenting advice / coaching


| App                             | Pricing                                        | Scale / funding                                                                                                                                              | Notes                                                                                                  |
| ------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| **Good Inside (Dr. Becky)**     | $23.25–$28/mo (~$276–336/yr); HSA/FSA eligible | 100,000+ paid subscribers (passed 100K Q3 2025); $34M revenue 2025 (+50% YoY); $10.5M raised (Inspired Capital, 2023), otherwise bootstrapped; ~64 employees | AI "co-pilot" trained on Dr. Becky's method; deliberately NOT branded "AI coach"; clinical credibility |
| **Huckleberry**                 | Free / Plus ~$59/yr / Premium (higher)         | 5M+ families; $16M raised (Series A $12.5M; Tamarisc/Morningside/Spero); ~200K downloads / ~$600K rev per month (Sensor Tower estimate)                      | "Berry" AI chat + human sleep experts; SweetSpot predictive algorithm; 4.9★                            |
| **ParentLab (Era)**             | App-based                                      | VC-tracked                                                                                                                                                   | Launched "Era" AI parenting app May 2025 — attachment theory, daily 5-min check-ins                    |
| **BabySparks / Kinedu / Moshi** | Freemium/sub                                   | Kinedu large in LATAM                                                                                                                                        | Developmental activities, sleep/calm                                                                   |




### Kids AI

- **Moxie (Embodied):** $799 robot, ages 5–10, SEL curriculum. **Shut down late 2024**, bricking devices; viral TikToks of crying children. The defining cautionary tale for cloud-dependent kid-AI.
- **Curio:** AI plush toys, ages 3+, no subscription; separately markets a "safe AI learning companion."
- **PinwheelGPT / kid-safe chatbot landscape:** small, heavily scrutinized.



### Camp/activity discovery

- **ActivityHero:** 4M+ families; marketplace + provider registration software; parents praise one-stop search/filter by age/interest and saved child info.
- **Sawyer (hisawyer):** provider-side class/camp management + marketplace.
- **Incumbent "tool":** local Facebook groups + spreadsheets remain the real competitor for discovery.



### What ChatGPT/Claude/Gemini are doing to this category

This is the central competitive threat. Parents already ask ChatGPT parenting questions and trust it (KU 2024 study); ChatGPT has 400M+ weekly users. **Milo's post-mortem is the lesson:** it was structurally caught between general AI getting cheaper/better (eroding the case for a $40/mo wrapper) and a human-in-the-loop model that made unit economics impossible — and it was building atop OpenAI, which competes in its own layer.

**Who has answered it convincingly:** Good Inside (proprietary method + clinical brand + community) and Huckleberry (proprietary SweetSpot algorithm + real human experts + data moat). Both win by owning what ChatGPT can't replicate: a **branded method, proprietary data, human trust, and workflow integration.**

**So what this means for Miguel:**

- "An AI that gives parenting advice" is a losing wedge — that's ChatGPT with extra steps, and Milo proves it dies.
- The defensible moats are **(a) a persistent family profile ChatGPT lacks, (b) agentic workflow that does real work (camp research, calendar sync, Gmail ingestion), and (c) two-household coordination ChatGPT structurally cannot do.**
- Competitors' revenue is proof of budget: Good Inside $34M, Huckleberry 5M families, OFW ~1M families.

---



## Section 3 — The Wedge Decision (most important; opinionated)

Scoring each wedge (1–5):


| Criterion                        | W1 AI coach | W2 Co-parenting | W3 Chief-of-staff/camps | W4 Kids' AI |
| -------------------------------- | ----------- | --------------- | ----------------------- | ----------- |
| ICP sharpness                    | 2           | 5               | 4                       | 3           |
| Pain acuteness/frequency         | 3           | 5               | 4                       | 3           |
| Existing spend (proof of budget) | 4           | 5               | 3                       | 2           |
| Competitive whitespace           | 2           | 4               | 4                       | 2           |
| Virality / before-after content  | 3           | 4               | 5                       | 2           |
| Expansion path to platform       | 3           | 5               | 4                       | 2           |
| Regulatory risk (higher=safer)   | 4           | 4               | 5                       | 1           |
| **Total**                        | **21**      | **32**          | **29**                  | **15**      |




### Ranking and pick

**Winner: W2 — the co-parenting / two-household family — attacked through a W3 acquisition wedge (camp & activity logistics).** Runner-up: **W3 standalone (mental-load/chief-of-staff for all busy dual-income families).**

**The opinionated recommendation is a hybrid sequence:**

- **Acquisition wedge (top of funnel):** the seasonal, acute, spreadsheet-shaped pain of **planning summer camps/activities across two households** — best before/after content ("6 spreadsheets and 40 tabs across two houses → one shared screen"), Jan–Apr spike, authentic founder experience.
- **Sharp ICP:** the **divorced/separated co-parent** (Miguel's own story) — proven budget (OFW court-mandated willingness to pay), dated AI-less incumbents, coordination structurally impossible for ChatGPT.
- **Retention engine:** the **AI coach that knows your family** (W1) — the reason they stay after camp season.

**Why not W1 alone:** Good Inside owns the "AI parenting coach" brand position, and generic advice is ChatGPT-replaceable (Milo died here). Weakest ICP sharpness and whitespace.

**Why not W3 alone as identity:** low ARPU (Cozi $39, Skylight $79) and Milo proved a general "family AI copilot" is caught in the ChatGPT squeeze. Great wedge, weak *identity*. Anchoring it to the co-parent gives pricing power and defensibility.

**Why W4 must be hidden:** see Section 8 — amended COPPA (voiceprints now "personal information," AI-training consent), FTC's Sept 2025 chatbot inquiry, Moxie's disaster. Marketing a kids' voice AI now invites regulatory and trust catastrophe for a solo founder.

**So what this means for Miguel:**

- Lead with camp/activity coordination for separated families; retain with the coach; hide the kids' voice agent.
- His divorce story is not a footnote — it is the wedge's core credibility and content engine.
- Sequence beats breadth: one acute pain, one sharp ICP, one wedge feature.

---



## Section 4 — ICP & Segmentation



### Persona A — "Two-Home Logistics Dad" (Miguel's mirror)

- **Demographics:** 35–48, divorced/separated, 50/50 or every-other-weekend custody, 1–3 kids ages 3–12, HHI $90K+, urban/suburban.
- **Psychographics:** Wants to be a great dad, hates conflict with ex, feels behind on logistics, distrusts "mom-coded" apps.
- **Where they are:** r/Divorce, r/Coparenting, r/Daddit, r/singledads; divorce-attorney/mediator referrals; single-dad Facebook groups.
- **Already pays for:** OurFamilyWizard/TalkingParents (often court-ordered), maybe ChatGPT Plus.
- **Trigger moments:** Custody-handoff confusion; "who signed up for which camp"; a missed activity that caused conflict; camp-registration season.
- **Objections:** "My ex won't use another app"; "Isn't this just my court app?"; family-data privacy.



### Persona B — "Maxed-Out Coordinating Mom"

- **Demographics:** 32–45, married or separated, dual-income, 2+ kids, primary logistics owner.
- **Psychographics:** Carries the mental load (Bath 2025: 67% more tasks), resents being "the family's frontal lobe" (Motherly), optimizer, reads parenting IG.
- **Where they are:** r/workingmoms, r/Mommit, Big Little Feelings / Dr. Becky comment sections, local mom Facebook groups, TikTok #mentalload.
- **Already pays for:** Cozi/Skylight, Good Inside or Huckleberry, activity fees.
- **Trigger:** Spring camp-planning panic; the annual "spreadsheet with 40 tabs."
- **Objections:** "I already have a system (my spreadsheet)"; "another subscription."



### Persona C — "New-to-Separation Parent"

- Recently separated, in the acute chaos phase, highest willingness to adopt a new system, often referred by attorney/therapist.



### Verbatim language to reuse (real, cited — do not fabricate)

- Citable real quotes: OFW users — *"This app took a chaotic family situation and gave it the peace we needed"*; *"It has truly kept my children out of our divorce drama."* Mental-load framing — *"become the frontal lobe for your entire family"* (Motherly). ChatGPT-as-coparent — a mom calling it a *"third co-parent"* (GMA).
- **Gap flagged:** I did NOT harvest a large corpus of verbatim Reddit quotes. **How Miguel should get it:** spend 2–3 hours reading r/Coparenting and r/workingmoms, copy 20–30 exact phrases into a swipe file, and reuse them verbatim in ad hooks and landing-page subheads. Cheapest, highest-ROI research task this week.

**So what this means for Miguel:**

- Persona A is his authentic beachhead and his own story — start there.
- Build a verbatim-language swipe file from Reddit before writing any ad copy.
- Attorneys/mediators/therapists are a referral channel hiding in plain sight (B2B2C).

---



## Section 5 — Pricing & Willingness to Pay



### Benchmark table (sourced/dated above)


| App                 | Monthly       | Annual                         | Model                    |
| ------------------- | ------------- | ------------------------------ | ------------------------ |
| Good Inside         | $23.25–28/mo  | ~$276–336/yr                   | Sub, HSA/FSA eligible    |
| Huckleberry Plus    | ~$5/mo        | ~$59/yr                        | Freemium; Premium higher |
| OurFamilyWizard     | —             | $149.99–299.88/parent/yr       | Annual only, per-parent  |
| TalkingParents      | ~$7/parent/mo | up to ~$700/yr (two, Ultimate) | Per-parent               |
| Cozi Gold           | —             | $39/yr                         | Whole-family             |
| Skylight Plus       | —             | $79/yr (+ hardware)            | Sub + hardware           |
| Big Little Feelings | —             | $99 course (one-time)          | Course                   |




### What the data say about willingness to pay

- **(a) Advice/coaching:** Highest ARPU proven — Good Inside sustains ~$276/yr because parents anchor it against therapy copays (Dr. Becky: *"I pay way more than that in copays"*). Parents pay for a *method + brand + trust*, not raw chat.
- **(b) Logistics/organization:** Lower ARPU ($39–79/yr) unless bundled with hardware or a high-stakes use case. Milo's ~$40/mo failed.
- **(c) Kid-facing:** Volatile and dangerous (Moxie).
- **Price anchors:** OFW's court-mandated $150–300/yr per parent — separated parents have already accepted a *three-figure annual* co-parenting spend. Good Inside's $276 is the coaching anchor.



### Pricing hypothesis to TEST (not assume)

Given the co-parenting anchor ($150–300/parent) and coaching anchor ($276), and that this product does BOTH:

- **Hypothesis: $199/yr per family (one account, both parents), or $19.99/mo**, positioned against "two OFW subscriptions + a parenting-coach subscription."
- **A whole-family price (not per-parent) is a sharp wedge against OFW's resented per-parent double-billing** (competitor "Parenting Path" already markets one-price-per-family at $169.99–329.99/yr).
- **WTP question wording for the quiz:** *"To have every camp, activity, and custody handoff for both your kids organized in one place — with a coach that actually knows your family — what feels fair per year?"* buckets: **$0 / <$50 / $50–99 / $100–199 / $200–299 / $300+.** Green light if median ≥ $100.

**So what this means for Miguel:**

- Anchor price to the co-parenting/therapy comparison, not to Cozi — that's where pricing power lives.
- Test a whole-family flat price as the wedge against OFW's per-parent model.
- Do NOT default to freemium: RevenueCat 2026 shows hard paywalls convert 10.7% vs 2.1% (5x) with near-identical year-one retention (28% vs 27%).

---



## Section 6 — Channel & Content Strategy



### Channel ranking (with evidence)

1. **Founder-led content on the divorce-dad angle (TikTok/IG/Reddit)** — authenticity is the moat. Big Little Feelings (3.5M followers, 400K course-takers), Dr. Becky (3M+ IG → $34M business), and Ms. Rachel prove the founder/creator-led parenting playbook works. UGC/authentic outperforms polished (2025 Meta data).
2. **Reddit communities** (r/Coparenting, r/Daddit, r/workingmoms) — where the ICP is and where verbatim pain lives.
3. **Attorney/mediator/therapist referral (B2B2C)** — OFW's institutional channel; replicable.
4. **SEO/AEO** — "best summer camps near me," "co-parenting summer schedule," "how to plan camps with my ex."
5. **Paid Meta (validation only, not scale yet).** Benchmarks: Baby & Parenting Products among the lowest CPCs (~~$0.09, 2025); targeting "parents of young children" costs 15–25% higher CPM but 2–4x conversion. All-industry 2026 CPA ~$38, CPC ~$0.78, CPM ~$14.19 (up 20% YoY). Education CPA lowest (~~$7.85).



### Founder-led content examples that demonstrably drove growth

- **Dr. Becky / Good Inside:** IG advice → book → podcast → $34M app.
- **Big Little Feelings:** viral IG (started 2020) → $99 course, 400K takers, #1 podcast debut.
- **Ms. Rachel:** free YouTube → cultural phenomenon (free-content-first).
- **Huckleberry:** data-parent founders → 5M families.
- Lesson: **give away genuinely useful stuff daily; the audience compounds into product demand.**



### Before/after formats specific to this product

- "Camp planning across two houses: 6 spreadsheets and 40 tabs → one shared screen."
- "Bedtime battle → the one change the coach suggested (because it knows my 4-year-old)."
- "Photo of a flyer → tracked activity + calendar + follow-up task in 5 seconds."
- "My ex and I hadn't agreed on a summer schedule in 3 years. Here's the screen that fixed it."



### AEO

- Ask ChatGPT/Claude/Gemini today "best co-parenting app" → OFW/TalkingParents/AppClose; "best parenting app" → Huckleberry/Good Inside/Cozi. To get recommended, Miguel needs: named presence in "best of" listicles (parentlog, wealthysinglemommy, justalk all rank co-parenting apps), review-site inclusion, and a crisp category claim ("the first co-parenting app with an AI chief-of-staff").

**So what this means for Miguel:**

- His unfair advantage is the authentic engineer-divorced-dad story — that IS the content strategy.
- Reddit + founder content first (free, high-trust); Meta only as a paid truth-serum for validation.
- Get into the co-parenting-app listicles early for AEO.

---



## Section 7 — The Validation Funnel Blueprint



### Frame B pre-sale experiment

**Quiz funnel (adapt the 8-step onboarding into a landing-page quiz):**

1. How many kids, and ages?
2. One home or two? (custody structure)
3. Biggest friction right now? (camps/activities logistics / behavior / schedule coordination / communication with co-parent)
4. **[Email capture here — question 3–4 placement lifts completion ~40%]**
5. How do you currently manage it? (spreadsheet / group text / co-parenting app / my head)
6. What does a bad week look like? (free text — harvest language)
7. **WTP question** (wording in Section 5).
8. Generate my Family Snapshot.

**Lead magnet — "Family Snapshot":** quiz → AI generates a genuinely useful personalized read (each kid's stage, 2–3 named friction points, 3 things to try this week, a sample "one-screen" camp/activity view). Free to generate; **account required for the full version** — mirrors Donnelly's ~50% free→paid lead magnet and Frame B's WTP capture.

**Landing-page copy skeleton:**

- **Headline options:** (A) "One screen for every camp, activity, and custody handoff — for both your kids." (B) "The family chief-of-staff for parents raising kids across two homes." (C) "Stop running your family from 6 spreadsheets and 40 browser tabs."
- **Subheads:** mental-load stat (Bath 2025), "built by a divorced dad and engineer for his own two kids."
- **Social proof strategy WITHOUT fabrication:** Miguel has NO testimonials yet. Do NOT invent any. Use: (1) the founder's authentic story and screenshots of the real product; (2) "in private beta with [N] families" only if literally true; (3) borrowed authority (cited mental-load research); (4) real quotes only, once beta families consent. **The single biggest integrity risk is fake reviews — avoid entirely.**

**Meta ads test plan (~$20/day, 2 weeks):**

- **Pixel fires only on final email capture** (Frame B) so Meta's AI optimizes for the true event.
- **Audiences:** (1) broad "parents of young children"; (2) interest: divorce/co-parenting/single parents; (3) lookalike once ~50 leads exist.
- **8 ad concepts (hooks):**

1. "6 spreadsheets → 1 screen" (before/after — most viral format per Frame B).
2. "Co-parenting summer camps with your ex doesn't have to be a fight."
3. "I'm a divorced dad and an engineer. I built this for my own two kids."
4. "Snap a photo of the camp flyer. It's on both parents' calendars in 5 seconds."
5. "Your family's mental load, in one place."
6. "The custody handoff, minus the chaos."
7. "What if your parenting coach actually knew your kid?"
8. "Take the 2-minute Family Snapshot."

**Success/kill thresholds (with benchmarks):**

- **Quiz completion** ≥ 40–65% (Interact: 40.1% avg lead conversion across 80M+ leads; ~65% completion typical). Kill if <30%.
- **Cost per email** ≤ $3–5 (parenting CPCs low ~$0.09–0.78; quiz funnels cut CPL). Green if ≤$3.
- **200-email bar (Donnelly):** if he can't get 200 emails, the offer is wrong.
- **WTP distribution:** green light if median ≥ $100/yr; yellow $50–99 (reposition); kill if median <$50.
- **Conversion context:** waitlists convert 50–70% vs 2–5% cold (Donnelly); RevenueCat hard-paywall D35 conversion 10.7%.



### Donnelly waitlist motion (parallel)

- **200-email bar** as go/no-go.
- **Cadence:** daily educational content for 30 days.
- **30-day topic-calendar sketch:** Week 1 — the mental-load problem (Bath/USC stats, his own story). Week 2 — co-parenting logistics tactics (summer-schedule templates, handoff checklists). Week 3 — "what the coach knows" (age-stage tips for 4- and 10-year-olds). Week 4 — camp-planning-season playbook (before/after screens, flyer-to-calendar demos). Each day = one short post + CTA to the Family Snapshot.

**So what this means for Miguel:**

- Ship the Family Snapshot quiz first; it is simultaneously the lead magnet, the WTP test, and a product demo.
- 200 emails and a $100 median WTP are the two numbers that green-light everything.
- Never fabricate social proof; borrow authority from cited research and his own story until real testimonials exist.

---



## Section 8 — Trust, Safety & Regulatory Moat/Risk



### The regulatory picture (2025–2026)

- **Amended COPPA rule:** finalized Jan 16, 2025; effective June 23, 2025; **compliance deadline April 22, 2026.** Adds **biometric identifiers including voiceprints** to "personal information"; requires **separate verifiable parental consent** for AI training and third-party sharing; **bans indefinite retention**; requires a written data-retention policy. Penalties up to ~$53,088 per violation.
- **FTC chatbot-companion inquiry:** Sept 11, 2025 — Commission voted 3-0 to issue Section 6(b) orders to seven companies (Alphabet/Google, Character.AI, Meta/Instagram, OpenAI, Snap, xAI) on chatbots "acting as companions" and effects on children/teens.
- **Enforcement is real:** Disney $10M (Sept 2025), Apitor robotic toy $500K, HoYoverse $20M (Jan 2025).
- **Kid-AI reputational risk:** Moxie shutdown; Character.AI banned under-18 open chat (Nov 2025) after teen-suicide lawsuits; ongoing Congressional scrutiny.



### What this means for positioning

- **Position as a PARENT-FACING tool.** The parent is user, customer, and consenting adult. This sidesteps most COPPA exposure.
- **Kids' voice companion (W4) = do NOT market.** Keep it out of GTM (ideally off the beta's public surface) until (a) April 2026 compliance is built and (b) legal review is done. It is a regulatory and PR landmine for a solo founder.
- **Must build regardless:** age gates, verifiable parental consent flows, written data-retention policy, no-AI-training-without-consent, data deletion, security program (COPPA now models on the Safeguards Rule).



### Trust as a differentiator

- **Parents' stated fears (cited):** 72% of teens use AI chatbots and 1 in 3 report discomfort (Common Sense, 2025); ~40% of potential parenting-app users hesitant to share child data (Business Research Insights); Stanford (Oct 2025) found major chatbots collect/train on chat data by default.
- **How trusted brands earned it:** Good Inside = clinical-psychologist founder + "Good Inside method" + coaches trained in the method. Huckleberry = pediatric sleep experts + data + 4.9★.
- **Minimum credibility kit for Miguel:** (1) a named clinical/child-development advisor (even part-time/equity); (2) a public **evidence/methodology page**; (3) a plain-language **safety & data page** (what's collected, retention, no kid data for training, deletion); (4) SonderMind pedigree used carefully (mental-health-adjacent credibility) without implying clinical endorsement.

**So what this means for Miguel:**

- Brand the product as a parent's tool, full stop; the kid-voice feature stays dark.
- Hit April 22, 2026 COPPA compliance as a hard deadline; build consent/retention/deletion now.
- Recruit one named advisor and publish an evidence + safety page — cheap, high-trust, and a genuine moat vs. ChatGPT.

---



## Section 9 — Business Model & Opportunity Synthesis



### 24-month scenario model (winning wedge)

Assumptions benchmarked to RevenueCat 2026: hard-paywall D35 conversion ~10.7%; monthly churn ~13–14% median (annual far better); only 17.3% of 2025+ apps reach $1K MRR within 2 years; apps launched 2025+ = 3% of subscription revenue. ARPU anchored to a $199/yr family plan.


| Scenario         | Emails/waitlist (24mo) | Paid conversion | Paying families | ARPU | Gross ARR |
| ---------------- | ---------------------- | --------------- | --------------- | ---- | --------- |
| **Conservative** | 3,000                  | 8%              | 240             | $150 | ~$36K     |
| **Base**         | 12,000                 | 12%             | 1,440           | $199 | ~$286K    |
| **Optimistic**   | 40,000                 | 15%             | 6,000           | $220 | ~$1.3M    |


These are **modeled estimates**, not forecasts; the funnel test will replace top-of-funnel assumptions with real data.

### Venture-scale, indie, or feature?

**Honest assessment: most likely a strong indie/lifestyle business (base ~$300K ARR) with a credible but unproven path to venture-scale.** Evidence for the ceiling: Milo (better-funded, OpenAI-endorsed) died; RevenueCat shows brutal odds for 2025+ apps; incumbents own the brand/data moats. Evidence that could **upgrade** the assessment: (1) the funnel shows CAC ≪ LTV with a defensible co-parenting wedge; (2) two-sided expansion (camp-marketplace take-rate); (3) B2B2C contracts (EAPs, family courts, pediatricians) that de-risk churn — the institutional-demand insulation OFW enjoys. Good Inside ($34M, mostly bootstrapped) shows a category-leading *brand* can reach scale without heavy VC — but that required Dr. Becky's 3M+ audience, which Miguel does not have.

### Adjacent revenue

- **Camp-booking affiliate/marketplace take** (ActivityHero/Sawyer model) — natural extension of the discovery agent.
- **B2B2C:** employers/EAPs (mental-load benefit), family courts/mediators (co-parenting), pediatricians.
- **Hardware partnership** (Skylight-style display) — later, capital-intensive.

**So what this means for Miguel:**

- Plan for a strong indie business; treat venture-scale as an option unlocked only by funnel proof + a marketplace or B2B2C wedge.
- The camp-marketplace take-rate is the most natural second revenue line and reinforces the wedge.
- Don't raise until the funnel proves CAC/LTV — his AI-augmented build speed means he can reach revenue cheaply.

---



## Section 10 — The 90-Day GTM Play (Synthesis)



### The single recommendation

**Wedge:** the AI family chief-of-staff for parents raising kids across two homes — acquired through summer-camp/activity coordination, retained by the coach that knows your family.

**Positioning statement:** *For separated and co-parenting parents who are drowning in the logistics of raising kids across two households, [Product] is the AI chief-of-staff that plans camps and activities, syncs both homes' calendars, and coaches you on your actual kids — unlike OurFamilyWizard and TalkingParents, which only document conflict, and unlike ChatGPT, which forgets your family the moment you close the tab.*

**Name/rename considerations:** "MVP" is a working codename and must change. The name should signal calm coordination + family intelligence, work for a parent-facing brand, and avoid kid-AI connotations. Avoid "coach" as the lead noun (Good Inside owns coaching; "co-pilot"/"chief-of-staff" test better for logistics). Do a same-day trademark + App Store name check before committing.

### Sequenced 90-day plan (~10 hrs/week for marketing; can ship product fast)

**Weeks 1–2 — Instrument the truth.**

- Build/ship the **Family Snapshot quiz + email capture + WTP question**; wire Meta pixel to fire only on email capture.
- Spend 3 hrs harvesting verbatim Reddit/FB language into a swipe file.
- Write landing page (headline A/B) with borrowed-authority social proof (cited stats + founder story); no fabricated reviews.
- Publish the **evidence page + safety/data page**; line up one named advisor conversation.

**Weeks 3–6 — Run the two engines in parallel.**

- **Paid truth-serum:** $20/day Meta for 2 weeks, 5–8 hooks (Section 7); optimize to cost-per-email.
- **Founder content:** daily educational posts (30-day calendar) on the divorce-dad + mental-load angle across TikTok/IG/Reddit.
- Target the **200-email bar** and a **$100 median WTP.**
- Recruit an **early-access cohort** from the warmest leads.

**Weeks 7–12 — Convert and decide.**

- Offer the early-access cohort a **lifetime discount** ("founding families" locked at ~$99/yr for life vs $199 standard) in exchange for **daily feedback** (Donnelly's cohort model).
- Turn on a **hard-paywall trial** (RevenueCat: 5x conversion vs freemium); test a 7-day trial.
- Collect first *real* testimonials (with consent) and add them to the page.
- Begin outreach to 3–5 family-law mediators/therapists for B2B2C referral pilots.



### Explicit decision gates (numbers)

- **Day 30:** If **< 200 emails** → the offer/messaging is wrong. Pivot the hook (test W3-only "mental load" framing to the broader dual-income mom before abandoning the co-parent angle).
- **WTP:** If **median < $50/yr** → do not build more paid features; reposition as freemium-plus-marketplace or reconsider the wedge. If **$50–99** → reprice/re-message. If **≥ $100** → proceed to paid cohort.
- **Cost per email:** If **> $8** after creative iteration → paid is not viable yet; lean entirely on founder content + Reddit + referrals.
- **Cohort retention:** If early-access **90-day retention < 30%** (below RevenueCat norms) → fix onboarding/aha-moment before scaling spend.
- **Green light to invest heavily:** 200+ emails, ≤$3 cost-per-email, ≥$100 median WTP, and ≥1 before/after content piece that outperforms → scale Meta and consider a raise.

**So what this means for Miguel:**

- For the next 90 days, his job is distribution and truth-finding, not features — the platform is already over-built for a beta.
- Two numbers govern everything: 200 emails and $100 median WTP by day 30.
- Lead with his real story, hide the kid-AI, price against the co-parenting/therapy anchor, and let the funnel — not his intuition — pick the final wedge.

---



## Caveats

- **Market-size figures conflict** across analysts ($1.06B–$2.8B for 2025); best estimate ~$1.7–2.0B, spread flagged. TAM/SAM/SOM figures are constructed order-of-magnitude estimates, not audited.
- **OurFamilyWizard revenue is not officially disclosed**; third-party aggregator estimates ($6.2M–$10.5M) conflict and are low-reliability. Its Spectrum Equity deal value (2020) is undisclosed.
- **Good Inside valuation is undisclosed** (revenue and subscriber figures are well-sourced via Fortune/Forbes, Feb–Apr 2026).
- **No verbatim Reddit corpus was harvested**; the founder must build the language swipe file himself (method provided).
- **Miguel currently has zero testimonials** — all social-proof recommendations are structured to avoid fabrication.
- Ad-cost and conversion benchmarks are cross-industry proxies; parenting/co-parenting-specific CAC must be measured in his own funnel.
- Where sources conflict, primary figures (RevenueCat, FTC, company press releases, Fortune/Forbes on Good Inside, University of Bath) were prioritized over secondary aggregators and blogs.

