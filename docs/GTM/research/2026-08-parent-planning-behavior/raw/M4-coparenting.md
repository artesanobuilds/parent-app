# M4 — Co-Parenting / Two-Household Apps

Miner: M4. Date: 2026-08-21. Geography: US (app stores queried with `country=us` / `gl=US`).

**Method note.** WebSearch budget for the session was exhausted before this miner started, so all
primary evidence here was collected by direct API/HTTP retrieval rather than search:
- Apple: `itunes.apple.com/search`, `/lookup`, and the public customer-reviews RSS
  (`/us/rss/customerreviews/page=N/id=X/sortby={mostrecent|mosthelpful|mostcritical}/json`),
  pulled 2026-08-21. Ratings/counts are US storefront, lifetime.
- Google Play: server-rendered `play.google.com/store/apps/details` JSON-LD `aggregateRating`,
  `hl=en_US&gl=US`, pulled 2026-08-21.
- Census: `www2.census.gov` historical table CH-1 / CH-5 / CH-6 (CPS ASEC), downloaded directly.
- Product feature claims: the App Store `description` field of each app (the vendor's own copy).

Review corpus: **2,006 US App Store reviews** across 7 apps, deduped by (author, title). Because the
corpus was assembled by unioning `mostrecent`, `mosthelpful` and `mostcritical` feeds, it is **not a
random sample** — it deliberately over-weights extremes. Percentages below are "share of this corpus
that mentions X," a *floor* on prevalence of a theme (reviewers who don't mention court orders may
still be court-ordered), never a population estimate. Where I report an unbiased distribution I say
so explicitly and use the `mostrecent`-only pull.

---

## Section 1: FINDINGS

| # | Claim | Value | Cohort/segment | Publisher | Year | Method | Tier | URL |
|---|---|---|---|---|---|---|---|---|
| 1 | US children under 18 living with one parent | 18.647M of 72.734M (25.6%) | All US children <18 | US Census Bureau (CPS ASEC), table CH-1 | 2025 | CPS ASEC 2025; excludes <18 householders/subfamily reference persons; numbers in thousands | A | https://www2.census.gov/programs-surveys/demo/tables/families/time-series/children/ch1.xls |
| 2 | Of those, mother-only vs father-only | 15.308M mother-only / 3.340M father-only | US children <18 | US Census CH-1 | 2025 | as above | A | same |
| 3 | Children <18 in one-parent households whose resident parent is divorced or separated (not never-married, not widowed) | 10.31M of 20.26M one-parent children (50.9%): mother divorced 5.181M + mother separated 3.303M + father divorced 1.285M + father separated 0.541M | US children <18 | US Census CH-5 / CH-6 | 2014 (**DATED** — Census stopped updating this breakout) | CPS ASEC 2014 | A | https://www2.census.gov/programs-surveys/demo/tables/families/time-series/children/ch5.xls |
| 4 | Never-married single parents (the other large slice, many with an involved nonresident parent) | 9.23M children (8.355M mother-only + 0.879M father-only) | US children <18 | US Census CH-5 / CH-6 | 2014 (**DATED**) | CPS ASEC 2014 | A | as above |
| 5 | One-parent share of US children is flat-to-declining, not growing | 20.53M (2013) → 20.26M (2014) → 19.76M (2015) → 19.65M (2018) → 19.22M (2022) → 18.14M (2023) → 17.95M (2024) → 18.65M (2025) | US children <18 | US Census CH-1 | 2013–2025 | CPS ASEC annual | A | as #1 |
| 6 | Share of US children under 18 living with a single parent and no other adults | ~23% | US children | Pew Research Center | 2019 (**DATED**) | 130-country analysis of household living arrangements; US figure from Census/CPS-equivalent | B | https://www.pewresearch.org/short-reads/2019/12/12/u-s-children-more-likely-than-children-in-other-countries-to-live-with-just-one-parent/ |
| 7 | OurFamilyWizard US App Store scale | 4.58★, 52,174 ratings | US iOS | Apple App Store | 2026-08-21 | lifetime US storefront ratings, `/lookup` API | C (platform-reported) | https://apps.apple.com/us/app/id497405393 |
| 8 | AppClose US App Store scale | 4.74★, 38,854 ratings | US iOS | Apple App Store | 2026-08-21 | as above | C | https://apps.apple.com/us/app/id1019290876 |
| 9 | TalkingParents US App Store scale | 4.39★, 28,753 ratings | US iOS | Apple App Store | 2026-08-21 | as above | C | https://apps.apple.com/us/app/id1092220726 |
| 10 | 2houses / Fayr / coParenter are an order of magnitude smaller | 144 / 280 / 166 ratings | US iOS | Apple App Store | 2026-08-21 | as above | C | — |
| 11 | Google Play: OFW 4.55★ / 15,171 ratings / 500K+ installs | see value | US Android | Google Play | 2026-08-21 | JSON-LD aggregateRating, gl=US | C | https://play.google.com/store/apps/details?id=com.ourfamilywizard |
| 12 | Google Play: AppClose 4.32★ / 29,898 ratings / **1M+ installs** — the largest install base in the category | see value | US Android | Google Play | 2026-08-21 | as above | C | https://play.google.com/store/apps/details?id=com.appclose.androidapp |
| 13 | Google Play: TalkingParents **2.27★** / 3,618 ratings / 100K+ installs — vs 4.39★ on iOS | see value | US Android | Google Play | 2026-08-21 | as above | C | https://play.google.com/store/apps/details?id=com.talkingparents.tpandroid |
| 14 | Google Play: 2houses 3.15★ / 594 ratings; coParenter 3.05★ / 206 ratings | see value | US Android | Google Play | 2026-08-21 | as above | C | — |
| 15 | The *recent* review stream is overwhelmingly negative despite high lifetime stars | 1–2★ share of last ~200–350 reviews: OFW 63% (n=350), AppClose 73% (n=200), TalkingParents 74% (n=200), 2houses 43% (n=118) | US iOS reviewers | Apple RSS `sortby=mostrecent` | 2026-08-21 | most-recent feed only, deduped; unbiased within "reviewers who wrote recently" | C | Apple RSS |
| 16 | Unprompted court-order mentions in the review corpus | AppClose 12% (63/534), OFW 12% (79/641), TalkingParents 8% (41/511), 2houses 1% (1/168) | US iOS reviewers | This miner, Apple review corpus | 2026-08-21 | regex over 2,006 deduped reviews; **floor, not prevalence** | C | this file |
| 17 | Reviews that explicitly turn on the *other parent's* participation (both-parties dependency, refusal, one-sidedness) | OFW 4% (28/641), AppClose 3% (14/534), 2houses 2%, TalkingParents 2% | US iOS reviewers | This miner | 2026-08-21 | regex + manual read; floor | C | this file |
| 18 | Abuse/weaponization language | OFW 6% (41/641), TalkingParents 4%, AppClose 3% | US iOS reviewers | This miner | 2026-08-21 | regex `weaponiz\|abus\|narciss\|harass\|stalk\|toxic\|used against me` | C | this file |
| 19 | Price/monetization complaints dominate the recent stream | TalkingParents 26% (131/511), OFW 18% (117/641), 2houses 15%, AppClose 12% | US iOS reviewers | This miner | 2026-08-21 | regex | C | this file |
| 20 | **Activity discovery / camp / class finding is essentially absent from the entire category** | 6 mentions across 2,006 reviews (0.3%), all of them requests or incidental calendar mentions — zero product references | US iOS reviewers | This miner | 2026-08-21 | regex `\bcamp\b\|find a (camp\|activity\|class)\|discover\|sign up for a (camp\|sport\|class)` | C | this file |
| 21 | Not one of the seven products offers activity/camp discovery, recommendation, or registration | 0 of 7 | Product feature audit | Apple App Store vendor descriptions | 2026-08-21 | full `description` field of each app read end-to-end | C (vendor copy) | iTunes lookup API |
| 22 | Self-described positioning of the two largest apps is *legal compliance*, not planning | "court-ordered in every U.S. County"; "trusted by courts and family law professionals across all 50 states" | AppClose; OurFamilyWizard | Vendor App Store copy | 2026 | vendor's own description text | C | as above |
| 23 | "Nationwide a father is likely to receive about 35% of child custody time" | 35% | US | Custody X Change (vendor) | 2018 | **method not disclosed on the page** — see WEAK SIGNAL | D → not citable | https://www.custodyxchange.com/topics/research/joint-custody-study-2018.php |

---

### Interpretation

**1. The second-parent assumption does not survive contact with this evidence — but it fails in a
more specific way than "the ex won't install it."** The failure mode in the reviews is almost never
"my ex refused to download an app." It is one of three things:

  (a) **The ex won't *pay*.** This is the single most common concrete refusal in the corpus. It shows
      up dozens of times across OFW and AppClose and it is what the January 2026 AppClose paywall
      turned into a mass event. Verbatim: *"After my ex said she couldn't afford this app. 3 days
      from purchase, I requested a refund…"* (OFW, 1★). *"My child's parent who demanded that we use
      this app stopped paying. She is still able to use the app."* (OFW, 1★). *"we upgraded our
      account… and our coparent never paid for the upgrade therefore we never got to use the upgraded
      feature once. We had it for a year and we were never able to use it."* (OFW, 1★). *"co parent
      can't navigate either, but won't pay to switch to Family Wizard."* (AppClose, 1★).
  (b) **The ex participates *badly* — logs in and doesn't read, denies expenses, ghosts.** *"The
      system does not take into account when the other parent refuses to log in to read messages,
      thus manipulates the entire program. This program has done more harm than good."* (OFW, 1★).
  (c) **The ex participates *maliciously*.** 6% of the OFW corpus contains abuse/weaponization
      language. *"An app that can and will be weaponized."* *"If a person is abusive, this app just
      magnifies the abuse."* (AppClose, 1★). *"It allows for harassment and manipulation in a closed
      door setting."* (OFW, 1★).

  The MVP strategy's proposed mitigation — invite the second parent via a calendar invite plus a
  forwarding email, never an app install — **directly and correctly dodges failure mode (a)**, which
  is the biggest one. Nothing in this corpus contradicts the claim that a zero-install, zero-cost
  invite has a materially higher acceptance rate than a paid app install; a very strong point in the
  strategy's favour is that AppClose's 1M+ Android installs were accumulated *while it was free* and
  its own reviewers say so repeatedly (*"I chose it because it was free and accessible for both
  parents — exactly what courts want"*). Free/no-install is demonstrably the adoption mechanism in
  this category.

  But it does **not** dodge (b) and (c), and (b) is fatal for a *planning* product in a way it is not
  for a *messaging* product. A messaging product still delivers when the ex is passive: the record is
  the product. A planning product that needs the other parent to actually take the camp week, drive to
  the practice, or split the fee delivers nothing if the invite is ignored. **The zero-friction claim
  is best read as unfalsified for *reach* and unsupported for *completion*.** No review in this corpus
  is evidence that a passive-recipient second parent produces a coordinated outcome.

**2. The court is the acquisition channel, and that is the deepest structural problem with this ICP.**
8–12% of reviewers mention a court order *unprompted*, and both category leaders lead their own store
copy with judicial endorsement ("court-ordered in every U.S. County"). The corpus contains almost no
one who chose a co-parenting app for its own merits; it contains many people saying the opposite:
*"I'm only using it because the court told me I had to, if I wasn't ordered to by the court, I
wouldn't be using it."* (AppClose, 3★). *"This app survives only because it is legally required."*
(OFW, 1★). *"If I weren't handcuffed to this app by court documents, I would find one that is more
functional."* (OFW, 2★). *"will be switching as soon as my order is changed can't happen fast
enough."* (TalkingParents, 1★). *"I'm just glad that our last child just turned 18 so I don't have to
waste the money on this."* (OFW, 1★).

  This has two implications for MVP. First, the incumbents' 40K–52K ratings and 1M+ installs are
  **not evidence of consumer demand** — they are evidence of a judicial distribution channel MVP does
  not have and cannot easily get. Second, and more usefully, it means the *voluntary* two-household
  segment is almost entirely unserved: every product in this category is built for the compelled user,
  and the compelled user is a hostile, price-sensitive, churn-on-emancipation customer. A product for
  amicable-but-logistically-strained two-household families is a genuine white space. The question is
  whether that segment is large enough and whether it is reachable without the court referral.

**3. The activity-planning gap is real, total, and confirmed from vendor copy.** I read the complete
App Store description of all seven products. Every single one is the same four primitives:
tamper-proof messaging, a custody/parenting-time calendar, expense splitting and reimbursement, and a
court-exportable record — plus, at the edges, GPS drop-off proof (Fayr), call recording (OFW,
AppClose, TalkingParents), AI tone-checking (OFW ToneMeter, AppClose Co-Parent Assist, TalkingParents
Sentiment Scanner), and an info bank of contacts. **Not one offers discovery, search, recommendation,
registration, deadline-watching, or fit-scoring for camps, classes, sports, or outings.** The word
"camp" appears in 2,006 reviews six times, always as a scheduling complaint or a feature request:
*"I have in the calendar all of the school breaks, so I can't put in her camps/activities during the
same time"* (Fayr, 3★). *"an associated calendar would be an awesome addition to this app so that
sporting events, school, extracurricular, and medical appointments can be shared"* (TalkingParents,
4★ — note this reviewer is asking a $10/mo product for a *calendar*). This is MVP's clearest
differentiation claim in the entire competitive set, and it is safe to make.

  The countervailing read: the near-total absence of camp/activity language in 2,006 reviews is also
  evidence that this population, *while in the court-ordered posture*, is not thinking about activity
  planning at all. They are thinking about documentation, notifications, and money. That is a
  demand-timing warning, not just a whitespace signal.

**4. Stigma: the evidence says the branding risk is real but is NOT expressed as self-shame — it is
expressed as resentment of the vendor and a desire to exit.** I searched explicitly for
embarrassment. The word "ashamed" appears 17 times in the corpus and in **16 of 17 cases it is
directed at the company** ("They should be ashamed of themselves", "AppClose should be ashamed of
turning accountability into a subscription"). Exactly one review expresses personal embarrassment,
and it is about the money, not the category: *"This app is actually terrible and the fact that I paid
for it is the most embarrassing part for me"* (OFW, 1★). "Divorce app" as a self-applied label
appears zero times. So: **no direct evidence of consumer shame at using a co-parenting app.** Two
caveats before treating that as reassuring: public app reviews are a terrible instrument for
measuring stigma (people who are embarrassed don't write reviews about being embarrassed), and this
population is court-compelled, which removes the choice that stigma would otherwise suppress.

  The **brand-jump risk runs the other direction and is well supported.** Every product in the
  category self-identifies in its first sentence with separation: "Are you a separated parent?"
  (2houses), "Parents who are divorced, separated, or were never legally married" (TalkingParents),
  "help your kids thrive after a separation or a divorce" (OFW). The category has *chosen* this
  positioning and no player has attempted the crossover. There is no evidence in this corpus that an
  intact-family parent would adopt any of them, and the entire acquisition mechanism (judge, family
  law attorney, GAL, parenting coordinator) is unavailable to an intact family. **A product that
  leads with two-household/co-parenting positioning is very likely locked out of intact families;
  a product that leads with planning can add two-household support without paying that tax.** For
  MVP, whose ICP is "the load-bearing parent in a two-household family," the actionable read is:
  build the *capability* for two households, do not build the *brand* around it.

**5. Solo-use value: the evidence is thin but leans negative — with one important exception.** The
clearest statement in the corpus is a 4★ AppClose review titled *"Great app, but it only can…"* —
*"…work so well when just one side actually uses it 😅"*. Others: *"Apps like these work only if
both parents are interested in co-parenting"* (OFW, 1★). *"it's a great app for coParenting as long
as both parties put forth the effort"* (AppClose, 3★). *"It only works if both parties participate"*
(OFW, 3★). The single most instructive review is a 5★ that is really a 1★ about the second-parent
problem: *"The app is great, but it doesn't help when the other parent refuses to get it. The court
orders require us to only communicate through this app, she won't get the app. There is no officer of
the court or anyone to report this to. My only recourse is to file another court case."* (OFW, 5★).

  The exception — and it matters for MVP — is that the **record-keeping and one-sided-documentation
  jobs demonstrably do deliver solo value.** *"So guess what my ex has refused to use family wizard
  and her lawyer doesn't like it either well I like it simply because she can't be rude and
  disrespectful to me anymore"* (OFW, 5★). And: *"it helps when the other parent refuses to co parent
  and doesn't want to pay"* (AppClose, 4★). The pattern: **jobs where the output is a personal artifact
  (a record, a log, a schedule I can see) survive the ex's non-participation; jobs where the output is
  a joint action (a payment, an agreement, a shared plan) collapse.** For MVP this is a design rule,
  not just a finding — the solo-first wedge should ship jobs of the first kind, and treat every
  second-parent-dependent feature as a bonus that must degrade gracefully to solo.

**6. Sizing — and an explicit contradiction.** The defensible Tier A number is **18.6M US children
under 18 living with one parent in 2025 (25.6% of all children), CPS ASEC table CH-1.** That is the
outer bound of the two-household population and it is an imperfect proxy in both directions: it
*excludes* children living with a biological parent plus a stepparent who also have an active
nonresident parent (counted as "two parents" by CPS, but genuinely two-household), and it *includes*
children with a deceased, incarcerated, or wholly absent second parent (not two-household in any
operational sense). Using the last Census breakout that separates those (CH-5/CH-6, **2014, dated**),
about half of one-parent children — 10.3M — lived with a divorced or separated parent, and 9.2M with
a never-married parent. A reasonable working range for "children in a genuinely two-household
arrangement with an active second parent" is therefore **roughly 10–19M children, i.e. on the order
of 7–13M households**, and I would not present a tighter number as sourced.

  The contradiction worth naming: **this population is not growing.** CH-1 shows one-parent children
  drifting *down* from 20.5M (2013) to 18.6M (2025), a ~9% decline over twelve years while the total
  child population was roughly flat. Every vendor and content-marketing page in this space implies a
  growing divorce-driven market; the Census series does not support that. Whatever the case for
  targeting the two-household parent, "the market is expanding" is not part of it.

**7. Two structural warnings for MVP that fall out of the operational data.** First, the
**notification-reliability finding**: 14–15% of AppClose, OFW and Fayr reviews are complaints about
missed or absent notifications, and they are the angriest reviews in the corpus because a missed
message has legal consequences. MVP's registration-window watchlist and push notifications sit on the
same nerve — a two-household parent who misses a camp registration deadline because a push didn't
fire will react the way these reviewers do. Second, the **Android divergence**: TalkingParents is
4.39★ on iOS and **2.27★ on Play**. In a category where one parent picks the platform and the other
is compelled onto it, the weaker platform's rating is the honest one, because it is populated by the
parent who did not choose the tool. That is an unusually clean natural experiment on what happens to
satisfaction when adoption is not voluntary — and a caution against reading a 4.7★ average in this
category as product-market fit.

---

## Section 2: WEAK SIGNAL

- **"Nationwide a father is likely to receive about 35% of child custody time"** — Custody X Change,
  2018. This is the single most-recycled statistic in the co-parenting space and it is a **vendor
  study with no disclosed method on the page**: no n, no sampling frame, no statement of whether it
  reflects statute, guideline worksheets, or observed orders. It is widely re-laundered by SEO blogs
  as though it were a Census figure. **Not citable. Treat every "X% of custody is shared" number
  traced to this page as unverified.**
- **Joint/shared physical custody prevalence trend.** The widely-cited finding that shared physical
  custody rose from ~5% to >35% of divorce cases derives from Wisconsin court-record research
  (Meyer, Cancian & Cook; Institute for Research on Poverty, UW–Madison). I could not fetch the
  primary paper in this session (the URLs I tried 404'd or resolved to unrelated articles) and I am
  not citing numbers I could not verify. **Flagged for a verifier: this is a real Tier A source and
  worth retrieving, but it is single-state court-record data and must never be presented as a US
  national rate.**
- **US Census "Custodial Mothers and Fathers and Their Child Support" report series.** This is the
  *right* Tier A source for a direct "children with a parent living elsewhere" count — it measures
  exactly the two-household construct rather than the one-parent-household proxy. I could not locate a
  working URL for the current edition without WebSearch (p60-281 turned out to be the income/poverty
  report). **Recommended follow-up for a collector with search budget.**
- **Court-order prevalence among co-parenting-app users.** No published figure exists that I could
  find. My 8–12% unprompted-mention rate is a floor and should not be quoted as "12% of users are
  court-ordered" — the true share is plainly far higher given the vendors' own positioning, but it is
  unmeasured.
- **Stigma.** I found no survey, panel, or study measuring whether separated parents feel stigma about
  using a co-parenting app, or whether intact-family parents would adopt a separation-branded product.
  The brand-jump argument in §4 is inference from category positioning and the absence of any
  crossover attempt, not from measured consumer attitude. **Confidence: medium-low. This is the
  cheapest and most valuable thing left to test directly.**
- **Whether users would use these tools absent a court order.** Directionally answered by verbatims
  (§2) but never measured. Every quote I have is from someone who *is* court-ordered; there is no
  counterfactual population in the data.
- **Onward.** I found no US App Store or Play listing under that name in this category; it may be
  defunct, renamed, non-US, or not an app. Not covered.
- **Custody X Change.** Web/desktop parenting-plan software with no US App Store listing surfaced by
  the search API. Its store presence could not be measured; its content marketing is the source of the
  35% figure above.

### Confidence

- Feature-gap finding (#20, #21): **high.** Read directly from every vendor's own description.
- Court-as-channel (#16, §2): **high** on direction, **low** on magnitude.
- Second-parent failure modes (§1): **high** on the taxonomy, **medium** on relative frequency
  (corpus is extreme-weighted by construction).
- Solo-use value (§5): **medium.** The artifact-vs-joint-action rule is well supported by the quotes
  but rests on a modest number of them.
- Stigma / brand-jump (§4): **medium-low** on brand-jump, **low** on consumer stigma — absence of
  evidence in a bad instrument.
- Sizing (#1–#5): **high** for the CH-1 number itself; **medium** for the 10–19M two-household range,
  which requires a dated (2014) table to construct.
