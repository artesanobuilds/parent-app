# MVP — GTM Strategy (canonical, v2)

**Last updated: 2026-07-07.** This is the single source of truth for MVP's go-to-market strategy. It synthesizes four inputs, in order:

1. `gtm-research.md` — the deep market-research report (July 2026)
2. `gtm-research-expansion.md` — the Activity OS addendum (5 verticals, seasonality fix)
3. `mvp-idea-roast.md` — the 5-persona adversarial review (verdict: RESHAPE)
4. A verification + deep-dive research pass (July 2026) that fact-checked the roast's load-bearing claims at primary sources and researched its three new strategic pillars

Where this document disagrees with the earlier docs, **this document wins** — the earlier docs are preserved as evidence and provenance. The Ground Zero doc's Section 12 carries the team-facing summary of this strategy.

---

## The strategy in one paragraph

Lead with one acute, seasonal logistics pain (whichever activity-registration episode is next on the calendar) for one sharp audience (the load-bearing parent in a two-household family) — **designed solo-first so it delivers full value even when only one parent participates**, with the other parent included at zero friction (plain calendar invites + a magic forwarding email address; never an app install, never an account, never a charge). Retain with the always-on ingestion loop (school emails, flyers, registrations) and the **registration-window watchlist** — not the coach. Price against the family-organizer market ($99–149/family/yr test range), not against court-mandated documentation apps. Treat data privacy as product: logistics data is durable and exportable; the AI coach runs zero-retention. Validate demand with the Family Snapshot funnel before building anything else, gated on hard numbers.

## What changed from v1 (the roast's four revisions)

The adversarial council (Contrarian 3/10, Expansionist 8/10, First-Principles 5/10, Deep Researcher 5/10, Buyer 5/10 — verdict **RESHAPE, high confidence**) confirmed the wedge direction (logistics for two-household families; coach demoted; kids' AI dark) but overturned four specifics:

| # | v1 said | v2 says | Why |
|---|---|---|---|
| 1 | "One price covers both parents" solves the two-household problem | **Solo-first product; parent #2 participates without adopting** (invites + email forwarding, no account) | Money was never the second parent's objection. Three personas independently found the two-sided adoption paradox; OFW only solved it with court orders. The Buyer's ex "would NOT install an app because he asked… but would absolutely forward a camp email to a magic address." |
| 2 | $199/yr, anchored against OFW's $150–300/parent | **Test $99–$149/family/yr** (WTP buckets centered lower; $199 kept as the top bucket) | Court-ordered buyers can't cancel OFW — MVP is additive to their $432, not a replacement. Surviving AI family assistants cluster $39–99 (Ohai $99/yr, Nori ~$96/yr, Skylight Plus $79/yr); Milo died at $40/mo. Buyer's fair zone: $99–149, "charge ME, make it genuinely free for her." |
| 3 | The coach is the retention engine | **Retention = the always-on ingestion loop + the registration-window watchlist; the coach is a supporting feature pending a privacy architecture** | Triple-refuted: if the coach could retain it could be the wedge (First-Principles); free general AI is churn-decision-quality (Contrarian); coach transcripts are discoverable in custody litigation, so the target buyer "will never type an honest word into it" and would pay MORE with the coach removed (Buyer). See the privacy pillar below. |
| 4 | Launch into camp season | **Launch into whichever episode is next** — as of July: fall activity registration (Aug–Sep) + back-to-school email chaos; camps return in January | The camp wedge is dead July–December; the 90-day validation window must not depend on an out-of-season pain. (Already anticipated by the Activity OS addendum; the roast made it binding.) |

## The three new pillars (researched and verified, July 2026)

### Pillar 1 — The registration-window watchlist (the "spot-getter")

**The finding (high confidence):** the sharpest camp pain is not choosing — it's *getting a spot*. Nationally documented "Hunger Games" registration races: camps selling out in 3–7 minutes, parents hardwiring ethernet and hovering at 8:45am, rec departments posting "Parents, set your alarms!" (Outside Online; WTTW/Block Club Chicago; Oak Park; Axios Atlanta; Burlington/Cobb County rec Facebook posts). A discovery agent that recommends full camps is a taunt.

**The whitespace:** no national parent-side product watches registration-open dates. The only entrant is Camperoni (Twin Cities-only; manual calendar-save reminders; paid concierge tier proves willingness to pay). Provider-side software (ActivityHero, Sawyer, Jumbula, ACTIVENet, 6crickets) alerts only that provider's own past customers. Nobody owns the cross-provider, parent-owned watchlist.

**The product implication:** "We watch registration-open dates across every provider near you, alert you before they open, and have your details ready" turns the discovery agent from list-maker into **spot-getter**. It re-arms the product every season (the retention answer the coach was failing to provide), it's uniquely enabled by what's already built (discovery agent + family profile + typed to-dos), and the data-harvesting cost is the moat. This is the single highest-leverage feature addition the entire research program surfaced.

### Pillar 2 — Zero-friction second-parent participation

**The finding (high confidence on the pain, medium on defensibility):** "my ex won't use the app" is so common that TalkingParents maintains a help article titled "What if my co-parent won't sign up?", Avvo/JustAnswer host recurring threads on non-compliant exes, and the industry's standard remedy is a contempt motion. Some incumbents market "solo mode" (AppClose, Custody X Change, BestInterest's "even if your coparent won't get on board") — but their solo modes mean *unilateral documentation for court*, not *frictionless inclusion*. Nobody lets parent #2 fully participate via plain Google Calendar invites + a magic forwarding address + an optional read-only iCal feed, with zero installs and zero cost.

**The product implication:** build exactly that, and make it the positioning: **"the logistics work even when only one of you does."** It converts the largest blocked segment (one motivated parent), avoids the surveillance framing (an invite is not an app her ex chose for her), and creates the natural viral path — every activated household has a built-in second household receiving useful invites from it. Caveat: the primitives (iCal feeds, magic emails) are commoditizing (Cozi, Jam, Ohai have pieces); the co-parent-specific packaging is the open ground, so move fast and own the message.

### Pillar 3 — Coach privacy as architecture (the split data model)

**The finding (high confidence):** in this category, discoverability is the incumbents' *product* (TalkingParents' court-certified "Unalterable Records"; OFW's published subpoena price list) — so users are trained to assume everything in a family app is court-visible. Meanwhile the family-law bar spent 2025–26 telling divorcing clients to stop typing into chatbots: no privilege exists (Altman's own July 2025 warning), pasting privileged material can *waive* attorney-client privilege, and the NYT v. OpenAI preservation order proved "we delete it" can be overridden by a litigation hold — while **zero-data-retention customers were carved out of that order**. Architecture determines exposure. Proton's Lumo (zero-access encryption, ephemeral Ghost Mode) is the existence proof that a private AI mode is buildable and marketable.

**The product implication:** split the data model in two and say so loudly. **Logistics data** (calendar, activities, handoffs) is durable, exportable, yours. **The coach runs zero-retention** — ZDR inference, no server-side transcript, at most user-held history — with honest copy: "we can't produce what we never stored," while never claiming litigation-proofness (courts can still reach the user's own device; nothing creates privilege). No family app occupies this position today. Until this architecture ships, the coach stays out of marketing for the co-parent segment.

## Positioning statement (v2)

*For the parent who carries the logistics of raising kids across two households, MVP is the AI chief-of-staff that finds the camps, watches the registration windows, turns flyers and school emails into both homes' calendars, and warns you before a coverage gap becomes a fight — and it works even when only one of you uses it. Unlike OurFamilyWizard and TalkingParents, which document conflict for court, MVP prevents it; unlike ChatGPT, it knows your family, your custody rhythm, and your deadlines.*

## Pricing (v2 hypothesis — the funnel decides)

- **Test range: $99–$149/family/yr** ($199 kept as the top WTP bucket to measure headroom). One subscription covers the family; the second parent is genuinely free forever.
- WTP question buckets: $0 / <$50 / $50–99 / **$100–149** / $150–199 / $200+. Green light: median ≥ $100. Yellow $50–99 (reprice/re-message). Kill <$50.
- Hard paywall with trial (RevenueCat 2026: ~5x conversion vs freemium, near-identical retention). Consider the Buyer's seasonal-risk reversal: full refund before Sept 1 in year one ("if it doesn't survive one real summer, you pay nothing").
- Anchor in copy against the activity budget ("~3% of what you already spend on the activities it coordinates") and the coverage-gap save ("one prevented scramble week pays for it"), NOT against OFW.

## The validation funnel (v2)

Unchanged in structure from the research (Family Snapshot quiz → email capture at Q3–4 → friction vote across the five verticals → WTP question → AI-generated personalized snapshot + activity-year map; $20/day Meta for 2 weeks, pixel fires only on email capture; two-voice founder content — Miguel = divorce-dad angle, Heather = maxed-out-mom angle). Changes:

1. **Lead episode as of July: fall registration + school-email season**, not camps.
2. **Quiz adds one question:** "Does your kids' other parent live with you?" → branches the snapshot and segments WTP by household structure (the single most valuable cut of the data).
3. **WTP buckets centered lower** (above).
4. **Ad hooks add the two new pillars:** "It watches registration-open dates so you don't have to set alarms" and "Works even if your ex never installs it — she just gets calendar invites."
5. **Before any ad spend: the 48-hour falsification test** (below).

## Decision gates (v2)

- **Gate 0 (48 hours, <$50):** message 25 separated/divorced parents (r/Coparenting, r/Daddit, co-parenting FB groups, personal network) with the solo-first pitch. Pass = ≥5/25 would pay ~$10/mo AND ≥15/25 say zero-friction ex participation (invites/forwarding) would actually happen in their situation. Fail on the second condition → lead with the maxed-out-mom persona instead of the co-parent angle before spending on ads.
- **200 emails by day 30** of the funnel, or the offer/messaging is wrong (pivot the hook; the friction-vote data says where).
- **Median WTP ≥ $100/yr** → paid cohort. $50–99 → reprice. <$50 → rethink.
- **Cost per email ≤ $3–5** after creative iteration, else shelve paid for organic + referrals.
- **Friction vote:** if a non-camp vertical wins by >2x, the headline changes (the product doesn't have to).
- **Sports/registration claims stay out of ads** until the discovery agent's hit-rate is validated in 2–3 metros.
- **Early-access cohort 90-day retention ≥ 30%** before scaling spend.

## 90-day sequence (v2, from July)

**Weeks 1–2 — falsify cheap, instrument the truth.** Run Gate 0 (the 25-parent test). Harvest the Reddit/FB verbatim swipe file (2–3 hrs). Ship the Family Snapshot funnel (fall-registration lead, household-structure question, revised WTP buckets). Publish the evidence page + the safety/data page (including the split-data-model promise). Approach one clinical/child-development advisor.

**Weeks 3–6 — run both engines.** Meta at $20/day (pixel on email capture only; hooks include the watchlist + works-without-your-ex angles). Daily founder content alternating Miguel/Heather. Drive to 200 emails + the WTP read. Recruit founding families from the warmest leads. Product work in parallel (small, funnel-informed): the zero-friction parent-#2 flow (invites + magic address + iCal feed) and a first registration-window watchlist for 1–2 pilot metros.

**Weeks 7–12 — convert and decide.** Founding-family lifetime deal (~$79–99/yr locked vs $129–149 standard) for daily feedback. Hard-paywall trial + Sept-1-style risk reversal. First real testimonials (with consent). Pilot outreach to 3–5 family-law mediators/therapists (the referral channel every persona endorsed). Then the gates decide.

## Verified numbers (safe for marketing copy)

All verified at primary sources, July 2026:

- **85%** of parents of under-18s lose sleep over summer care/scheduling; **90%** among working parents (Bright Horizons 2026 Modern Family Index, Harris Poll, April 2026)
- **80+** school/activity emails per month; **62%** of parents have missed something important buried in email; 71% feel like "bad parents" when they do (Yahoo/Censuswide, June 2024)
- Good Inside: **$34M revenue 2025, 100K+ subscribers** at ~$276/yr (Fortune, Feb 2026)
- OurFamilyWizard: $110–$299.88 **per parent** per year (official pricing page)
- TalkingParents killed its free plan **March 30, 2026**; AppClose went paid ($8.99/mo/parent) **January 1, 2026**
- Skylight: **9.3M+ users**, 99% YoY revenue growth, $50M financing (company PR, April 2025) — use "9.3M users," NOT "1.3M families"
- Ohai.ai **$99/yr**; Nori **$8/mo** (vendor sites)

**Corrections log (do not repeat the old versions):** Milo's farewell post is **January 12, 2026** (not 2024 or March 2025) — the founder quote "the technology is simply too early to be reliable in any useful way" is verbatim-safe. Yohana's **US service ended September 30, 2025** (Japan January 30, 2026). The gtm-research.md executive summary's "Milo shut down in 2024" is wrong; its market-sizing spreads remain flagged as analyst-conflicting.

## What stays true from v1

The wedge direction (activity logistics for two-household families; the coach is not the front door; the kids' voice companions stay entirely out of GTM pending COPPA compliance + legal review). The Activity OS relay (5 verticals, one seasonal episode in the headline, the activity-year map as the reveal). The two-voice founder content engine. The trust kit (named advisor, evidence page, safety/data page). The honest ceiling: base case is a strong indie business (~$300K ARR at 24 months); the upgrades are funnel-proven CAC≪LTV, the camp-booking marketplace take-rate, and B2B2C channels (mediators/therapists, EAPs) — plus, per the roast's Expansionist, the long-game assets are the two-household coordination graph and the local-activity data the watchlist accumulates.
