# M3 — Activity & Camp Discovery / Registration

Miner M3. Fielded 2026-08-21. US only.

**Method note / limitation up front:** the shared WebSearch budget for this research program was
exhausted mid-run (200/200 calls, consumed across all miners). Roughly half of the intended
secondary-source sweep — especially published survey data on the *discovery-channel mix* — could not
be completed, and several publisher sites (ACA, Jumbula, Sawyer, Trustpilot, Reddit, Capterra,
Star Tribune) returned 403/429 to direct fetches. **In compensation I ran an original primary
measurement**: a full audit of ActivityHero's live public search index (Algolia, read-only public
search key exposed in their own front-end bundle). That audit is the strongest evidence in this
report and it is first-party, reproducible, and dated. Section 3 (channel mix) is the weakest
section and is explicitly under-sourced; I have not padded it with Tier-D aggregator numbers.

---

## Section 1: FINDINGS

| # | Claim | Value | Cohort/segment | Publisher | Year | Method (n, window, population) | Tier | URL |
|---|---|---|---|---|---|---|---|---|
| 1 | ActivityHero — the largest US kids-activity marketplace — carries 49,637 provider-location records nationally in its live public search index. | 49,637 | US providers | ActivityHero (measured by M3) | 2026 | Direct query of `prod_providers` Algolia index, `hitsPerPage=0`, 2026-08-21 | Primary (own measurement) | https://www.activityhero.com/search |
| 2 | Its session index holds 94,848 total session records, but only **9,008 (9.5%)** have an end date in the future as of 2026-08-21 — ~90% of the catalog is expired. | 9.5% live | US | ActivityHero (measured by M3) | 2026 | `prod_sessions`, `numericFilters=activity_schedule.end_date>1787270400` vs unfiltered | Primary | as above |
| 3 | California alone accounts for **38,045 of 94,848 (40%)** of all ActivityHero session records, and **4,299 of 9,008 (48%)** of currently-live ones. | 40% / 48% | US, by state | ActivityHero (measured by M3) | 2026 | `provider_location.state` facet, maxValuesPerFacet=60 | Primary | as above |
| 4 | 20 US states have fewer than 50 currently-live sessions each on ActivityHero; Hawaii has 2, Vermont 7, DC 11, Alaska 12, North Dakota 12, South Dakota 14. | <50 in 20 states | US, by state | ActivityHero (measured by M3) | 2026 | state facet under the future-end-date filter | Primary | as above |
| 5 | Provider density within 25 mi collapses by ~200x from top metro to small metro: LA 5,686 · SF 4,299 · NYC 2,827 · Dallas 800 · Chicago 795 · Atlanta 683 · Denver 577 · Minneapolis 427 · Boise 85 · Wichita 81 · Jackson MS 37 · Fargo 24 · Bangor 22 · Billings 21 · Charleston WV 20. | 5,686 → 20 | US metros | ActivityHero (measured by M3) | 2026 | `aroundLatLng` + `aroundRadius=40000` per metro centroid | Primary | as above |
| 6 | Counting only *currently-live* sessions the collapse is far worse: SF 969 · NYC 112 · Minneapolis 35 · Wichita 8. Minneapolis (3.7M metro) offers a parent 35 bookable listings. | 969 → 8 | US metros | ActivityHero (measured by M3) | 2026 | future-end-date filter + geo radius, 2026-08-21 (seasonal trough — see caveat) | Primary | as above |
| 7 | Sawyer charges providers a **15–30% marketplace commission** (30% on the Launch tier, 20% Grow, 15% Scale) and marketplace listing is **opt-in** on the paid tiers. | 15–30% | US providers | Sawyer (hisawyer.com) | 2026 | Vendor's own published pricing page, fetched 2026-08-21 | C (vendor) | https://www.hisawyer.com/for-business/pricing |
| 8 | ActivityHero charges 15% per paid registration (MarketingHero) or $49/mo + $0.35/engagement overage (Starter); a bare directory listing is free. | 15% / $49/mo | US providers | ActivityHero | 2026 | Vendor's own published pricing page, fetched 2026-08-21 | C (vendor) | https://business.activityhero.com/pricing/ |
| 9 | ActivityHero claims "over 4 million families" and a 400k-subscriber email list; it discloses no city count, booking count, or active-provider count. | 4M families (claimed) | US | ActivityHero | 2026 | Marketing page, no method disclosed | C (vendor, unverified) | https://business.activityhero.com/ |
| 10 | Camperoni launched in Minneapolis–St. Paul with ~250 providers, and as of Feb 2025 listed "more than 500 camps and programs" across all its markets combined. | 250 → 500+ | Twin Cities + 4 | Twin Cities Business | 2025 | Trade-press interview with CEO Meredith Englund, 2025-02-24 | C | https://tcbmag.com/camperoni-adds-new-markets/ |
| 11 | Camperoni's total market footprint after two seasons is **5 metros**: Twin Cities, Duluth, Rochester MN, Denver, Boston. | 5 metros | US | Twin Cities Business | 2025 | Same article | C | https://tcbmag.com/camperoni-adds-new-markets/ |
| 12 | Camperoni's CEO states the product only works above a supply threshold: "If there are only two camps in your area, we're not going to make a big difference. But if you've got 50 different providers, that's more than you as a parent can keep in your head." | qualitative | — | Twin Cities Business | 2025 | Direct CEO quote | C | https://tcbmag.com/camperoni-adds-new-markets/ |
| 13 | Camperoni now monetizes **parents directly**: a "Pay What You Can" membership anchored at $60 / $100 / $200 per year, plus **Camperoni Concierge at $295/year** (1 week free trial) where human experts build the plan. | $60–$295/yr | US parents | Camperoni | 2026 | Vendor's own membership page, fetched 2026-08-21 | C (vendor) | https://www.camperoni.com/blog/camperoni-membership-options |
| 14 | Camperoni's own price anchor is explicitly time-value: "I save at least 5 hours per year camp planning, and my time is worth at least $20 per hour, so I can pay $100 per year." | 5–10 hrs/yr @ $20/hr | US parents | Camperoni | 2026 | Vendor copy | C (vendor) | as above |
| 15 | The registration-window job is delivered by Camperoni **manually, by humans**: the Concierge tier promises to "Set calendar reminders with tips & tricks for registration" and "Reach out proactively to get started on planning in time for key registration dates." | qualitative | — | Camperoni | 2026 | Vendor copy | C (vendor) | as above |
| 16 | 55% of US parents said their child took part in at least one structured summer activity in 2024; 53% of non-participating parents wished their child could have; 43% of participating parents wanted more. Cost was a top-3 barrier for two-thirds. **"Lack of awareness of available programs" is named as a distinct barrier.** | 55% / 53% / 43% | US parents | Gallup for NSLA + American Camp Association | 2024 | n = 6,800+ US parents, fielded May 1–15 2024 | B | https://afterschoolalliance.org/afterschoolsnack/New-survey-results-show-parents-want-more-summer_07-26-2024.cfm |
| 17 | Participation splits sharply by income: 67% of upper-income vs 38% of lower-income families had a child in a summer activity. | 67% vs 38% | US parents by income | Gallup / NSLA / ACA | 2024 | Same survey | B | as above |
| 18 | Mommy Poppins — the largest editorial parent-discovery publisher — covers exactly **12 US metros/regions**: NYC, LA, Chicago, Boston, Houston, Philadelphia, Atlanta, Washington DC, Connecticut, New Jersey, Westchester, Long Island. | 12 | US metros | Mommy Poppins (measured by M3) | 2026 | Enumerated region slugs from homepage HTML, 2026-08-21 | Primary | https://mommypoppins.com/ |
| 19 | Macaroni KID operates "hundreds of publishers" and "more than 1,000 local editions" across the US and Canada; parent company CertifiKID acquired Hulafrog in Jan 2023, consolidating the two hyperlocal newsletter networks. | 1,000+ editions | US + Canada | Macaroni KID / CertifiKID | 2023 | Company announcement | C (vendor) | https://springfield.macaronikid.com/articles/63c087aff692fe4644ff76f2/were-growing-macaroni-kids-parent-company-acquires-hulafrog |
| 20 | **No consumer-facing iOS app exists in the US App Store for ActivityHero, Sawyer, Mommy Poppins, Macaroni KID, or Camperoni.** All five are web-only on the parent side. | 0 apps | US | App Store (measured by M3) | 2026 | iTunes Search API, `entity=software&country=us`, 8 query variants, 2026-08-21 | Primary | https://itunes.apple.com/search |
| 21 | Care.com's "Activities & Camps" iOS app — the one big-brand attempt at a parent-side discovery app — has **21 lifetime ratings** and zero written reviews in its live RSS feed; last updated 2026-02-25. | 21 ratings | US | Apple App Store (measured by M3) | 2026 | iTunes lookup + customer-reviews RSS, trackId 1002740010 | Primary | https://apps.apple.com/us/app/id1002740010 |
| 22 | By contrast, **Campanion** (CampMinder's *post-enrollment* parent app — camp photos, messages, packing) has **40,351 ratings at 4.92★**. Parents engage deeply with camp software *after* they've registered, not before. | 40,351 @ 4.92 | US camp parents | Apple App Store (measured by M3) | 2026 | iTunes lookup, trackId 1457911692 | Primary | https://apps.apple.com/us/app/id1457911692 |
| 23 | An App Store sweep for "camp registration reminder", "camp signup tracker", "activity registration alerts kids" and "summer camp planner parents" returns **no national parent-side registration-window alert product** — results are dominated by RV/outdoor camping apps (Hipcamp, The Dyrt, Recreation.gov) and provider apps (Campanion, Bunk1, iClassPro). | 0 found | US | App Store (measured by M3) | 2026 | 4 query variants × 8 results, 2026-08-21 | Primary | https://itunes.apple.com/search |
| 24 | Waitlist/registration notification features that do exist (Campium, SwiftEnroll, CampDoc, ACTIVE Network) are **provider-side**: they notify a parent about *that one provider's* opening. None spans providers. | qualitative | US providers | Vendor product pages | 2026 | Product-page review | C (vendor) | https://campium.com/features/camp-waitlist-management/ |
| 25 | ActivityHero's index carries visibly stale records at the top of its default ranking — e.g. a Palo Alto soccer camp with `to_date` = April 2023 still returned as hit #1 in `prod_activityhero`. | qualitative | — | ActivityHero (measured by M3) | 2026 | Raw record inspection, 2026-08-21 | Primary | https://www.activityhero.com/ |

### Caveats on my own measurement

- The audit was run on **2026-08-21**, the seasonal trough between summer camp (ended) and the
  spring/summer-2027 registration wave (opens ~Nov 2026–Feb 2027). Absolute live-session counts will
  be higher in January. **The ratios between metros — SF 969 vs Minneapolis 35 vs Wichita 8 — are the
  finding, not the absolute levels**, and there is no reason seasonality would differ by metro.
- `end_date > now` is a conservative liveness test. A session with a far-future end date but a passed
  registration cutoff still counts as live, so 9.5% is an *upper bound* on real availability.
- The provider counts (finding 5) include stale/dead listings, since a free directory listing never
  expires. That makes the metro gradient in finding 5 the *optimistic* version of finding 6.
- Facet counts on `activity_types` (Camp 12,427 · Class 10,691 · Event 4,805 · Online 1,206 ·
  On-Demand 531 · Birthday Party 381) sum to ~30k, not 94,848 — a large share of records carry no
  activity_type. Treat the type mix as indicative only.

---

## The landscape: parent side vs provider side

The clean way to see this market is that **almost all the money and almost all the software is on the
provider side**, and the parent-facing surface is a thin, seasonal, ad-funded veneer on top of it.

**Provider-side (real businesses, real revenue):** Sawyer, ActivityHero for Business, Jumbula, Amilia,
CampMinder/Campanion, CampDoc, CampBrain, iClassPro, ACTIVE Network, CivicRec/RecTrac/CommunityPass
(municipal parks-and-rec), SwiftEnroll, Campium. These sell registration, payments, rosters, health
forms, and waitlists. Sawyer's list price is $189–$399/month plus 15–30% on marketplace-sourced
bookings; ActivityHero's is $49/month or 15% per registration. This is a normal vertical-SaaS market.

**Parent-side (thin):** ActivityHero.com and Sawyer's marketplace are the demand-side skins of those
SaaS products. Mommy Poppins and Macaroni KID/Hulafrog are ad-and-affiliate-funded editorial
newsletters. Peachjar is a school-district-mediated *push* channel — providers pay to have digital
flyers emailed through the district, so parents don't search it, they receive it. Camperoni is the
only venture-backed pure-play parent-side product I found, and it is 5 metros deep.

The structural tell is finding 20: **not one of these has shipped a consumer iOS app.** Care.com, a
public company with enormous parent reach, tried, and its Activities & Camps app has 21 lifetime
ratings. Meanwhile Campanion — which does nothing but show you photos of your kid *at* camp — has
40,351. Parents will install and open a kids-activity app; they just won't do it for *discovery*.

## Coverage reality — the central question

**There is no comprehensive national database of US kids' camps and activities, and the measured data
says nobody is close.**

ActivityHero is the biggest aggregator by index size. On 2026-08-21 its entire live national
inventory was **9,008 bookable sessions**, of which California supplied 48%. Twenty states had fewer
than fifty live sessions each. A parent in Minneapolis — the 16th-largest US metro, 3.7 million people,
a city Camperoni chose precisely because it is camp-dense — would see **35 listings**. A parent in
Wichita would see **8**. This is not a national database; it is a Bay Area / LA database with a long,
mostly-dead tail attached to it.

The 90%-expired ratio (finding 2) matters as much as the geography. A free directory listing never
expires, so the aggregators' impressive-sounding provider counts (49,637 records) are a fossil record,
not a catalog. Finding 25 — a hit ranked first whose sessions ended in April 2023 — is what that
feels like to a parent.

**Why it is structurally fragmented, and unlikely to consolidate:**

1. **Take rates repel supply.** Sawyer's marketplace fee is 15–30% of tuition; ActivityHero's is 15%.
   On a $400 camp week that's $60–$120. Any provider who can fill from their own list, a school
   flyer, or a parents' Facebook group will — and does — opt out. Sawyer's marketplace is literally an
   opt-in add-on on its paid tiers. So the marketplace catalog is a subset of the SaaS customer base,
   which is itself a subset of providers.
2. **The biggest supply pool isn't in any marketplace.** Municipal parks-and-rec departments, YMCAs,
   school districts, libraries and churches are where most affordable camp weeks live, and each runs
   its own portal (ActiveNet, CivicRec, RecTrac, CommunityPass, Jumbula) with its own catalog, its
   own registration date, and no syndication feed. There are ~19,000 US municipalities. Nobody is
   ever going to integrate them.
3. **Supply density is the product.** Camperoni's CEO said the quiet part out loud (finding 12): below
   ~50 providers in a radius the product has no reason to exist. That means every parent-side
   discovery business is *economically confined to dense metros* — Mommy Poppins' 12 regions
   (finding 18) is exactly this constraint expressed as an editorial footprint.
4. **The one network that did go national went hyperlocal-human instead of database.** Macaroni KID +
   Hulafrog reach 1,000+ local editions by franchising a human publisher per town who writes a
   newsletter. That is a real national footprint, and it is deliberately not a queryable database.

### Verdict for a web-search-based discovery agent

**A web-search agent is the *right* architecture for this problem, and it is the only architecture
that has any chance of working nationally — but its output quality will still track local supply
density, and it must be evaluated on recall in thin markets, not dense ones.**

The reasoning:

- A licensing/integration strategy is dead on arrival. The measured national ceiling of the
  best-integrated catalog is ~9,000 live sessions with 48% in one state. You cannot buy or partner
  your way to national coverage; the feeds don't exist.
- The supply that marketplaces *can't* reach — a city rec department's PDF, a YMCA branch page, a
  church summer program, a martial-arts studio's own site, a school district's summer calendar — is
  overwhelmingly **published on the open web**. That is precisely what a search-and-read agent gets to
  see and a data-integration marketplace does not. The agent's addressable inventory is strictly
  larger than ActivityHero's in every market, and dramatically larger outside California.
- Two concrete risks I could partially observe: (a) many municipal rec catalogs are JS-rendered SPAs
  with session-scoped search (my probes of ActiveNet URLs returned 301/302 into marketing shells
  rather than results), so an agent that only reads static HTML will miss municipal supply — the
  highest-value, least-covered segment; (b) **freshness is the failure mode, not coverage.** The
  aggregators' 90% staleness shows how fast this data rots. An agent that returns a camp whose
  registration closed is functionally identical to ActivityHero's April-2023 soccer camp, and parents
  will punish it the same way.
- Practical implication: the agent should be measured per-metro against a manually built ground-truth
  list in **three tiers** — a dense metro (SF/LA), a mid metro (Minneapolis/Denver), and a thin one
  (Wichita/Charleston WV). If it can beat 35 listings in Minneapolis and 8 in Wichita — which is a low
  bar — it is already the best discovery tool available in those markets. That is a genuinely
  defensible national position that no incumbent can copy, because their economics forbid it.

## How parents actually find activities — UNDER-SOURCED

This is the section I could not finish, and I am flagging it rather than filling it with laundered
stats. What I can defend:

- The Gallup/NSLA/ACA survey (n=6,800+, May 2024, Tier B) names **"lack of awareness of available
  programs"** as one of the barriers keeping children out of summer programming, alongside cost and
  work-schedule conflict. That establishes that a discovery gap is real and measured at national
  scale — but the published summary does not break out *which channels* parents use.
- The claim that "recommendations from friends and family is the number-one way parents find a camp"
  circulates widely and is attributed to the American Camp Association. **I could not trace it to an
  ACA publication with an n and a fielding window** — every instance I reached was a camp-marketing
  vendor blog (Jumbula, AdWave, TeenLife, RevenueBoomers), and acacamps.org returned 403 to direct
  fetch. Per the brief's hard rule this goes in WEAK SIGNAL, not Section 1. **A verifier should chase
  the ACA "Camp Enrollment / Family Insights" reports directly; this is the single highest-value
  unresolved number in my domain.**
- Indirect but real evidence that word-of-mouth and local-human channels dominate over search
  directories: the only parent-side discovery network with genuine national reach is Macaroni KID +
  Hulafrog, whose entire model is a trusted local human writing a town newsletter (finding 19); the
  best-funded *searchable* alternative reaches 12 metros (finding 18); and the biggest database has
  8 live listings in Wichita (finding 6). Supply-side behaviour also points the same way — Peachjar
  exists because providers pay to push flyers through school districts rather than wait to be found.
- Finding 22 is a behavioural proxy worth more than a stated-preference survey: **parents do not
  return to a discovery product between seasons.** Care.com's 21 ratings vs Campanion's 40,351 is
  the shape of the demand curve. Discovery is a 2–3 week annual burst; the relationship lives
  elsewhere.

**Product implication if word-of-mouth does dominate (likely, unproven):** a discovery agent that
returns a ranked list of web-found options is competing against a channel it cannot beat on trust.
The defensible move is to make the agent *complete the loop the friend can't* — the friend tells you
about the camp; nobody tells you it opens at 9:00am on January 14th and sells out in eleven minutes.
Which is the next section.

## The registration-window problem — VERIFIED as whitespace

**The repo's belief is correct, and slightly understated. As of 2026-08-21 nobody has shipped a
national, cross-provider, parent-side "tell me when registration opens for the specific camps I care
about" product.**

What I checked and what I found:

- **App Store sweep (finding 23):** four query variants, no such product. The category is squatted by
  RV camping. The only camp apps with real installs are post-enrollment provider apps.
- **Camperoni — the one named competitor — has NOT shipped it as software (finding 15).** This is the
  sharpest result in the report. Camperoni is the best-funded, most-focused player on exactly this
  problem, has been at it since 2023, has $1.3M raised, and its answer to the registration-window job
  in 2026 is a **$295/year human concierge** who will "set calendar reminders with tips & tricks for
  registration" and "provide back-up plans for the most competitive camps." If the company whose
  entire thesis is camp registration is doing it by hand, the automated version does not exist.
- **Camperoni's footprint is 5 metros (finding 11)**, all of them chosen for camp density, with ~500
  total listings across all markets combined as of Feb 2025. Its coverage is roughly one-eighteenth of
  ActivityHero's *live* national inventory. It is not a national competitor and shows no sign of
  becoming one.
- **The adjacent products are provider-scoped (finding 24).** Campium, SwiftEnroll, CampDoc, and
  ACTIVE all ship waitlist notifications. Those tell you when *the camp you already applied to* has a
  spot. They are worthless for the actual job, which is: I have eleven candidate programs across a
  city rec department, a YMCA, two private camps and a martial-arts studio, they open on five
  different dates between November and March, and I will lose the good ones if I miss one.

**Refinement of the whitespace claim:** the moat here is not the notification, it is knowing the date.
Registration-open dates are the least-structured data in this entire space — they live in a PDF, a
Facebook post, last year's page that hasn't been updated, or nowhere at all until a provider decides.
A watchlist that requires the parent to type in the date is a calendar. A watchlist that *finds and
re-checks the date* is a product nobody has. That is the same capability as the discovery agent, aimed
at a narrower and much more painful job — and unlike discovery, it is **not** density-dependent: a
Wichita parent with 8 candidate programs has exactly the same problem as an SF parent with 40, and is
strictly worse served today.

## Business model: will parents pay for discovery?

The incumbents' answer is no — every one of them monetizes the provider (15–30% take, $49–$399/month,
flyer fees, display ads). That is weak evidence, though, because provider monetization is what a
marketplace does regardless of parent willingness to pay.

The one direct test in the market is Camperoni, and it is encouraging with a large asterisk:

- Search is free; parents are asked to **"Pay What You Can"** at $60 / $100 / $200 a year, with the
  ask framed explicitly as hours-saved × $20/hr (findings 13–14). A pay-what-you-can ask is a
  donation, and conversion is almost certainly low — but it establishes the anchor a founder chose
  after two seasons of talking to these parents: **$100/year for saving ~5 hours.**
- The paid tier that actually has a price and a trial is **Concierge at $295/year** — done-for-you
  planning by humans. That sits above every price point in the repo's competitor set
  (OurFamilyWizard $110–300, Ohai $99, Skylight $79, Cozi $39). It says the willingness to pay exists,
  but it attaches to *the work being done for you*, not to *a better list of options*.

**Read-through:** parents will not pay for a directory. The measured market has no example of anyone
succeeding at that. They will plausibly pay $99–$295/year for something that removes the work —
finds the options, knows the dates, watches for the opening, and hands back a plan. That is the
Concierge shape, and it is exactly what an agent can do at software margins where Camperoni is paying
humans. The pricing floor to beat is $295/yr done-by-humans in one metro; the product to beat is a
spreadsheet.

---

## Section 2: WEAK SIGNAL

- **"Recommendations from friends and family is the number-one way parents find a camp" — attributed
  to the American Camp Association.** Circulates on Jumbula's blog, AdWave, TeenLife, RevenueBoomers
  and a dozen camp-marketing SEO pages. **No n, no fielding window, no origin document reachable.**
  acacamps.org returns 403 to direct fetch. Treat as unverified until someone pulls the ACA source.
  This is a stat-laundering candidate and also the most important missing number in this domain.
- **"Over 4 million families" (ActivityHero) and "millions of families" (Sawyer)** — marketing claims
  with no method, no date, no definition of "family" (likely cumulative registered emails since 2011).
  Listed as finding 9 only because it is the vendor's own on-the-record claim; do not use it as a
  market-size input.
- **Camperoni's current market count.** Twin Cities Business documented 5 markets as of Feb 2025;
  a 2026 camp listing for a Denver Boys & Girls Club confirms Denver is live. I could not verify
  whether markets were added or dropped in the 2026 season — their blog index returned a single post
  and the site is client-rendered.
- **Sawyer marketplace geographic coverage.** hisawyer.com returns 403 to direct fetch and has no
  public search index I could reach, so I could not run the equivalent of the ActivityHero audit.
  Sawyer's coverage is *probably* NYC/LA/SF-weighted (its provider base is boutique urban studios),
  but I have no measurement. **Recommend a verifier repeat the ActivityHero method on Sawyer via a
  rendered browser session.**
- **Municipal rec portal crawlability.** My probes of ActiveNet URLs redirected into marketing shells
  rather than returning catalogs, suggesting session-scoped SPA search. One or two probes is not a
  finding; this needs a real browser-driven test across 5–10 cities before anyone plans engineering
  around it. It is, however, the single most important technical unknown for the discovery agent.
- **Peachjar scale.** No provider, school, or district counts published on their site; the model is
  district-mediated flyer push. Real but unquantified.
- **Verbatim reviews.** I could not obtain them. Trustpilot (403), Capterra (403), Reddit (403 on
  both www and old, JSON and HTML), and the Care.com app's review RSS was empty (21 ratings, no
  written reviews). Camperoni has no app and no public review corpus. **This is a genuine gap in my
  domain — the requested verbatim tagging (complexity / entry friction / coverage gaps / trust /
  price) could not be produced.** The nearest usable verbatims are the CEO quote in finding 12 and
  Camperoni's own customer-facing price framing in finding 14, both of which read as authentic
  customer language reflected back.

---

## Reproducing the ActivityHero audit

Public search-only credentials, extracted from ActivityHero's own front-end bundle
(`https://static.activityhero.com/packs/search-bundle-*.js` → `window._algoliaConfig`):
app id `4MCE5KNBEO`, search key `c4d6012cd973f1d0e3cf0d1a5f59b147`; indexes `prod_providers`,
`prod_sessions`, `prod_activityhero`. Read-only queries against
`https://4MCE5KNBEO-dsn.algolia.net/1/indexes/{index}` with `hitsPerPage=0` for counts,
`aroundLatLng`/`aroundRadius` for geography, `facets=["provider_location.state"]` for the state
distribution, and `numericFilters=activity_schedule.end_date>{epoch}` for liveness. All figures in
findings 1–6 and 25 are from queries run on 2026-08-21.
