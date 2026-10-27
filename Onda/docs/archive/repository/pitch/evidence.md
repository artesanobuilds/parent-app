# Evidence map

Every factual claim on a slide, with where it comes from. If an investor asks "where did that
number come from," the answer is on this page. Nothing on a slide is here without a source, and
nothing was rounded up.

Read this before the meeting. The claims most likely to be challenged are flagged **[CHALLENGE]**.

---

## Slide 03 — the problem

| Claim | Source |
| --- | --- |
| 85% of parents lose sleep over summer care and scheduling; 90% among working parents | Bright Horizons Modern Family Index, Harris Poll, April 2026 |
| 80+ school and activity emails a month | Yahoo / Censuswide, June 2024 |
| 62% have missed something buried in one | Yahoo / Censuswide, June 2024 (same study also found 71% say it makes them feel like a bad parent) |

## Slide 04 — why now

| Claim | Source |
| --- | --- |
| "the technology is simply too early to be reliable in any useful way" | Milo's public shutdown post, 12 January 2026. Quoted verbatim. |
| Yohana left the US September 2025 | Yohana service-end notice (US 30 Sep 2025; Japan 30 Jan 2026) |
| TalkingParents killed its free plan | Effective 30 March 2026 |
| AppClose went paid | $8.99/month per parent, effective 1 January 2026 |
| Sub-150ms voice | Measured on our own ElevenLabs ConvAI v2 pipeline, not a vendor claim |

## Slides 05, 07 — the job, the wedge and the evidence

All from the repository. These are verifiable by demo or by reading the code.

| Claim | Where it lives |
| --- | --- |
| Five verticals live in production | `mvp-backend/app/cos/verticals.py` — CAMP, EXTRACURRICULAR, SCHOOL_EVENT, OUTING, TRIP |
| 20-tool agent | `mvp-backend/app/cos/tools.py` |
| Source sentence shown beside each extracted deadline | ingestion path, `POST /ingest/image` → `ExtractedActivity` |
| Registration watchlist + miss detector | `watchlist_windows_missed_ratio` Grafana alert; docs page `registration-watchlist.md` |
| Five-layer moderation | `mvp-backend/app/moderation.py` |
| 988 / SAMHSA-aligned taxonomy | `moderation.py` crisis severity model |
| Crisis push verified on a physical device | July 2026, APNs; `setup/apns-setup.md` |
| 567 automated tests | pytest functions across 106 test files |
| 120 kid-safety eval cases | `app/evals/cases/` — 50 red-team, 40 age-appropriate, 30 guardrail-conflict |
| 29 flow specs against the real API | `tests/nl-harness/specs/` |
| 24 schema migrations | `mvp-backend/app/migrations.py`, latest v24 |
| 4 live alert rules | Grafana `cos-health` group, MCP-verified |
| 110 categories / 45 articles / 25 community posts | content taxonomy, carried over from Heather's original slide |
| Product screenshots available | `parent-dashboard/public/docs-assets/` (no visual slide in this deck) |

## Slide 08 — the scale case

| Claim | Source |
| --- | --- |
| $3-4B US camp registrations a year | Category estimate from the GTM research file. **[CHALLENGE]** This is the softest number in the deck. Present it as an order of magnitude, not a figure. |
| "Why not OpenAI" reasoning | Argument, not a fact. Own it as a judgment call. |

## Slide 11 — the market

| Claim | Source |
| --- | --- |
| Good Inside $34M 2025 revenue, 100,000+ subscribers at ~$276/yr | Fortune, February 2026 |
| OurFamilyWizard $110-$299.88 per parent per year | OurFamilyWizard public pricing page |
| $12.9M ARR at 100,000 families × $129 | Arithmetic on our own price point. It is an illustration of unit scale, not a forecast. **[CHALLENGE]** Do not let it be heard as a projection. |
| ~3% of what the activities cost | Anchor framing from the GTM strategy doc |

## Slide 12 — why we win

| Claim | Source |
| --- | --- |
| TalkingParents publishes "What if my co-parent won't sign up?" | Their public help centre |
| The industry remedy is a contempt motion | Characterisation of the category's standard advice. Defensible, but it is our framing. |

## Slide 13 — where we are

| Claim | Source |
| --- | --- |
| 98 TestFlight builds | Version/build progression, 1.1/5 through 1.89/103 |
| 21 parent-facing releases in 24 days | `parent-dashboard/docs/release-notes.md`, 18 July to 10 August 2026 |
| Gate numbers (WTP ≥ $100, CPE ≤ $5, retention ≥ 30%) | `docs/GTM/gtm-strategy.md` decision gates, written 7 July 2026 |
| No revenue, no launch, no paywall | True. Payments are deliberately deferred; there is no StoreKit integration. |

## Slides 14–15 — team

| Claim | Source |
| --- | --- |
| Heather originated the concept pre-pandemic; owns product and GTM | `docs/GTM/ground-zero.py` team section |
| Miguel's roles and dates | LinkedIn profile export, August 2026 |
| Brightcove 450M players, ~1.3B daily video views | LinkedIn, Brightcove tenure |
| Lumiata: 100+ medical conditions, IAAI Deployed Application Award | LinkedIn + Lumiata press |
| Mindstrong: 92% → 99.99% reliability | LinkedIn, Mindstrong tenure |
| Three-part patent | US20220083588A1, via the Loupe advisory |
| Board-facing at Lumiata and MetaStories | Stated as board-facing exec, **not** a board seat. Miguel's explicit framing decision. **[CHALLENGE]** Do not upgrade this in conversation. |
| ~77,000 lines / 567 tests / 98 builds, one engineer, five months | Measured from the repo, 11 August 2026: 28,398 lines of **native Swift** (SwiftUI, not React Native), 44,563 Python, 4,188 TS/React for the web dashboard only. Five months is the honest working span; the repo's first commit predates sustained work. |

---

## What is deliberately not claimed

An investor will look for these. We say them first.

- **No user count, retention figure, or engagement metric.** None is recorded anywhere, so none
  appears. The product has not launched.
- **No revenue and no paying customers.** Payments are not built.
- **No funding history or valuation.**
- **COPPA compliance is not finished.** The kid-facing companion is therefore excluded from
  go-to-market, which is why it does not appear on the product slide.
- **Known scale ceiling.** Single Railway instance, single-writer DuckDB. Named on slide 16 as
  something the raise closes.
- **No CI.** The test suite runs locally; the repo has no remote.

## The question not on any slide

Miguel is VP Engineering at SonderMind full time. Every investor will ask about commitment and
timing. That is a founder decision, not a deck decision, and he should have the sentence ready
before this goes out. See `critics.md`, Horowitz pass.
