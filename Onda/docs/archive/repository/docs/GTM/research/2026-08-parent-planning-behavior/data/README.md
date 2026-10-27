# `data/` — auditable chart datasets

Built 2026-08-21 by QUANTIFIER Q1 from `raw/` (P1–P12, P5b, M1–M5, S0, S1) as corrected by the
verification reports (V1–V6) and the two **VERIFIED CORRECTIONS** blocks at the end of `BRIEF.md`.

**The corrections blocks override the collector reports.** Where a collector and a verifier disagree,
these CSVs carry the verifier's value and the `verification` column says `CORRECTED`.

Every chart in the final report renders from a file in this directory. Nothing in a chart should come
from a collector report directly.

---

## Column conventions

Each file carries its own data columns first, then these five, in this order:

| Column | What it holds |
|---|---|
| `source` | Publisher + year. For original measurement, the measuring party and the date. |
| `tier` | A / B / C / D, per the brief's source tiers (below). `A-derived`, `Primary (own measurement)` and `Analyst judgement` are used where none of A–D fits, and are always spelled out. |
| `method` | n, fielding window, population. A number with no method does not belong in a chart. |
| `verification` | `CONFIRMED` / `PLAUSIBLE` / `CORRECTED` / `UNVERIFIED` / `UNVERIFIABLE`. |
| `notes` | Every qualifier that MUST travel with the number. If a cell is long, that is the point — the qualifier is not optional. |

### `verification` values

- **CONFIRMED** — a verifier reached the primary source and matched the figure digit-for-digit.
- **PLAUSIBLE** — arithmetic and provenance check out, but a declared assumption or an unre-fetched
  input sits inside it. Usable; say so.
- **CORRECTED** — the collector's published value was wrong and this file carries the corrected one.
  The `notes` cell always says what changed and why.
- **UNVERIFIED** — no verifier tested it. Publish only where the report visibly marks it as untested.
- **UNVERIFIABLE** — a verifier tried and could not reach a source (paywall, login gate, 403, deleted
  page). Not the same as refuted. Publish only where the report visibly marks it.

Anything a verifier marked **REFUTED** is either excluded from these files entirely or replaced by the
corrected value; there is no `REFUTED` verification value, by design.

---

## Source tiers

- **A** — government or peer-reviewed: Census (ACS/CPS), BLS (ATUS), NSCH, NHIS, MEPS, CDC, NCES,
  peer-reviewed journals.
- **B** — major research organisations that publish methodology: Pew, Harris Poll, Bright Horizons MFI,
  Aspen/Project Play, Edison, RevenueCat, Gallup, Nielsen, eMarketer.
- **C** — industry or vendor reports that disclose method. Vendor-interested sources are tagged as such.
- **D** — SEO stat-aggregator blogs, listicles, "N statistics for 2026" pages.

Two labels sit outside A–D and are used explicitly:

- **Primary (own measurement)** — this program measured it (the ActivityHero index audit, the App Store
  review corpora, the Google Trends pulls, the code audit). Strong for shape and scale; it carries no
  publisher's assertion behind it, so the method cell has to do all the work.
- **Analyst judgement** — a structured opinion (the job-quadrant step counts, the email option scoring,
  the complexity comparison). Charted only under a heading that says so.

---

## THE HARD RULE

**No Tier-D row appears in any chart CSV.** Tier D is never citable. Where a Tier-D number was
load-bearing in a collector report, it has been removed from the data and recorded in
`killed_statistics.csv` instead, with its true origin and the corrected value where one exists.

Three consequences worth knowing before you read a chart:

1. `seasonality_month_x_task.csv` has **no youth-sports row**. It was Tier D (analyst construction; the
   cited source verifiably contains no season-timing data), it was the largest single contributor to the
   column totals, and it was the flattest row in the table. It is in `killed_statistics.csv` as `KX2`.
2. `seasonality_month_x_task.csv` has **no aggregate row and no column totals**. The "aggregate parent
   planning load varies only 1.47× across the year" figure is an artifact of row normalisation plus
   ordinal truncation and must not be published (`KX1`).
3. `competitor_landscape.csv` has **no Ollie row**. Ollie is a phantom — five plausible domains, five
   unrelated products (`KX4`).

`killed_statistics.csv` is itself the exception that proves the rule: it is a chart *about* Tier-D
numbers. Its `tier` column records what each killed statistic actually is, and its `verdict` column
is the thing being plotted.

---

## Rules that travel with specific files

- **`seasonality_month_x_task.csv`** — never render a flatness ranking without the
  `shared_scale_volume` column beside it. Summer camp's worst month exceeds the dentist row's best
  month by ~4.5×. Google Trends is **Tier C** here (a raw feed with no disclosed n, analysed by us), not
  Tier B, and it carries no parent/age filter — the medical, birthday and vacation rows are not
  parent-specific.
- **`planning_labor_by_employment.csv`** — the **employed-parent** series is the headline
  (8.4 vs 4.8 min/day, 1.75×). The all-parents series (12.0 vs 6.0) is a separate, labelled series and
  is levered by non-employed mothers. `bls.gov` returns HTTP 403 to every direct method in this
  environment; the figures were verified through **Wayback Machine `id_` raw snapshots**, which is the
  standard BLS route for this project.
- **`obligations_per_year.csv`** — ED and urgent-care visits are excluded from every count labelled
  *scheduled*. Use ~23/yr for a two-kid family with an honest band of **20–26**, and never a decimal:
  NCES publishes the school-attendance mean as a rounded integer.
- **`activity_supply_by_metro.csv`** — the Algolia application ID and search key are **redacted**. The
  ToS footnote and the August-trough caveat are in every `notes` cell and must appear wherever these
  numbers do. Keep the vendor's name inside every headline number.
- **`app_complexity_benchmark.csv`** — the column is `analyst_call`, not `verdict`, and every row
  carries `evidence_strength` (direct / adjacent / none). The string "SEVERE OUTLIER" is banned: no
  screens-to-completion distribution exists, so "outlier" is unavailable as a word. The 1–2 minute
  Planner wait may be stated as "6–12× Nielsen's verified 10-second limit" verbatim.
- **`killed_statistics.csv`** — every row is `PENDING V7`, which is still finalising the consolidated
  list. Built from V6, with rows contributed by V1–V5 marked in `verified_by`.

---

# METHOD APPENDIX — the Q2 completion pass (2026-08-22)

Added by QUANTIFIER Q2 to close three gaps Q1 left open. Everything below is an **original analyst
measurement**: reproducible method, no published *n*, no publisher asserting the finding. Every cell
Q2 added carries `tier=C` and `verification=CONFIRMED-BY-MEASUREMENT` in its own `notes` block.

## A. `seasonality_month_x_task.csv` — the `shared_scale_volume` column is now complete

The report's rule is that **flatness must never be shown without volume**, which made this column
load-bearing and Q1 had populated only 4 of 10 rows.

**Endpoint chain** (identical to P7 and V3, so the new cells are comparable to the old ones):

```
# 1. bootstrap a cookie — without it the API returns HTTP 429
curl -s -c ck.txt -o /dev/null 'https://trends.google.com/trends/?geo=US' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'

# 2. explore -> take the TIMESERIES widget's `request` and `token`
REQ='{"comparisonItem":[{"keyword":"summer camp","geo":"US","time":"today 5-y"},{"keyword":"<term 2>","geo":"US","time":"today 5-y"}],"category":0,"property":""}'
curl -s -b ck.txt -G 'https://trends.google.com/trends/api/explore' \
  --data-urlencode "req=$REQ" --data 'hl=en-US&tz=360' \
  -H 'Referer: https://trends.google.com/' -H 'User-Agent: …'

# 3. widgetdata/multiline with that request+token -> 261 weekly points per term
# 4. strip the )]}' prefix, group by calendar month, take means
```

`geo=US`, `category=0`, `property=""`, `hl=en-US`, `tz=360`, `time='today 5-y'` — Google resolves the
window to `2021-08-22 2026-08-22`, `resolution=WEEK`, **261 points**. No parent, age or household filter
exists in Trends, so any row built on a non-kid-scoped string is not parent-specific.

**Getting everything onto one scale.** All terms for a family go into a *single* `comparisonItem`
array alongside **`summer camp` as a shared anchor**, which is what forces Google to normalise them to
one maximum. Take each term's monthly means, then multiply by `36.6 / (anchor's mean in that request)`
so the result lands on the scale the summer-camp row already carries.

**The ladder, and why it is necessary.** Trends returns *integer* indices. Against an anchor as large as
`summer camp`, every registration term floors to 0 and its shape collapses — `little league
registration` and `youth baseball registration` both returned all-zero rows. Those terms were
re-measured against an intermediate **ladder anchor**, `kids activities near me`, whose position on the
summer-camp scale is independently fixed at **3.47**, and the result multiplied back. Any future
low-volume term must go through the ladder, not the direct anchor.

**CVs come from solo pulls, never from comparison pulls.** Co-normalisation quantises a low-volume
series and inflates its CV: `dentist appointment` reads **0.099 solo** and **0.136** inside the anchor
comparison. All CVs in the file are single-term pulls.

**Validation before use.** Re-running Q1's own anchor set reproduced all four published volumes to the
printed precision — summer camp **36.60** vs 36.6, kids activities near me **3.47** vs 3.5, dentist
appointment **1.49** vs 1.5, birthday party ideas **9.30** vs 9.3 — and solo re-pulls reproduced P7's
per-term monthly index tables cell-for-cell.

**Convention.** `shared_scale_volume` is the single highest-volume *on-concept* representative query for
the family, matching the single-term convention of the four cells Q1 populated. Every other term measured
for the family is listed in that row's `notes` with its own volume. Volumes are **approximate and
directional**. Per V3 the **fine CV ranking is not robust to quantisation** — only the coarse
flat-vs-spiky separation is. Do not re-rank families on small volume or CV differences.

**Two results that need to travel with the chart.** *Fall activity registration* is internally split:
essentially all its volume sits in the flat browse term `after school program` (CV 0.208) while the
registration-intent terms that produce the row's spiky bucketing carry ~1/150th of it — the bucketed
pattern and the volume figure describe different terms. *School admin* at 30.7 is dominated by
`back to school`, which is overwhelmingly a **retail** term; the admin-scoped terms inside the family are
an order of magnitude smaller. Neither number should be presented as product demand.

## B. `activity_supply_by_metro.csv` — live-session counts for all 15 metros

Q1 carried live counts for 4 metros; the other 11 had provider counts only. M3's query was re-run for
every metro.

**Method, minus the credential.** Read-only `POST /1/indexes/{prod_providers|prod_sessions}/query`
against the vendor's Algolia DSN host, authenticated with the **search-only key ActivityHero itself
publishes in its front-end search bundle**. That credential is read at runtime and is **never written
into any file in this repository** — do not add it here, to a script, or to the report.
`hitsPerPage=0` on every request, so only counts and facet aggregates come back and **no records are
copied**. Geography is `aroundLatLng` at the city centroid with `aroundRadius=40000` (~25 mi).
Liveness is `numericFilters=activity_schedule.end_date>1787270400` — **the same fixed 2026-08-21
00:00 UTC cutoff M3 and V5 used**, deliberately held rather than re-anchored to the run date, so this
pull is directly comparable to theirs.

**Calibration.** The re-run reproduced **all 15** of M3's provider counts exactly, **all 4** of M3's
published live counts exactly (SF 969, NYC 112, Minneapolis 35, Wichita 8), and the national totals
(providers 49,638 — the same +1 drift V5 saw; sessions 94,848; live 9,008; CA live 4,299). The 11 new
live counts came from the same script in the same pass as those 16 matched cells.

**The August-trough caveat is carried forward, and the new data strengthens it.** Measured at the
annual trough between expired summer camp and the ~Nov 2026 – Feb 2027 registration wave. Year-round
enrichment classes stay live in August while summer-only supply — relatively *more* of thin-market
supply — expired on the same date, so the metro gradient is **inflated** at this timepoint. This is a
**single-timepoint measurement**; the falsification test is a January re-run. The new counts supply
direct evidence for the caveat: **LA has more providers than SF (5,686 vs 4,299) but only 329 live
sessions against SF's 969**, and NYC's 2,827 providers yield just 112. Provider rank and live-session
rank disagree across the top three metros, so the two measures must not be presented as one gradient.
In the thinnest metros the live counts (3–8) are small enough that ordinary index churn moves them by
tens of percent — read the bottom of the table as an order of magnitude and do not rank thin metros
against each other.

**The SF / California 4,299 collision is resolved: it is a genuine coincidence, not a copy error.**
Both cells were re-measured independently in the same pass. SF providers within 25 mi = 4,299 comes
from `prod_providers` with a geo filter and **no** liveness filter. California live sessions = 4,299
comes from `prod_sessions` with a state facet filter **plus** the liveness filter. Different indexes,
different filters, different units — organisations versus sessions. Both stand as published; never put
them in one sentence without saying which is which. SF's own live-session count is **969**.

**One new discrepancy, flagged and unresolved.** Q2's re-run of California's share of *all* sessions
returned **39,346** against the **38,045** M3 published and V5 confirmed, on the same day the national
total (94,848) and the CA *live* count (4,299) both reproduced exactly. A one-day index change cannot
do that without moving the national total; the likely cause is a difference in how the CA subset was
addressed. The cell is **left unchanged and marked DISPUTED**. Resolve it before publishing any
California share-of-all-sessions figure. Nothing else in the file depends on it.

**ToS, unchanged from V5.** ActivityHero's Terms of Use bar copying, distributing or disclosing any
part of the Service, including by automated or non-automated scraping. Mitigating: the key is
search-only and vendor-published, every query used `hitsPerPage=0` so no records were copied, and the
volume was ~50 requests. The application ID and search key are redacted everywhere. **Queries bill to
ActivityHero's Algolia account — do not automate a re-run.** Keep the vendor's name inside every
headline number: this describes ActivityHero's index, not US kids' activities.

## C. `job_quadrants.csv` — a new `plot` column, and the corrected ratio

The file now carries a **`plot`** column immediately after `quadrant`. Two rows are `plot=false`:

- **Birthday party attended** — no frequency source at any tier, so the row has no x-position. The
  circulating "8–12 parties per year" is on the kill list (K7). The step count survives; the frequency
  is what is missing. Show it, if at all, as a labelled annotation with no x-coordinate.
- **Permission slip / school form** — the ~12/yr figure (and the 18 steps/yr derived from it) is an
  unverified analyst estimate with no publisher behind it. The qualitative claim is well supported; the
  number is not.

**One focused sourcing attempt was made for each, and both failed.** The session's web-search budget
(200 calls) was already exhausted by the collection phase, so the attempt fell back to direct fetches
against search endpoints, which returned bot-challenge pages. No Tier A/B/C publisher was reached.
This does not refute the existence of a source — it means **two** independent targeted searches (P5's
and this one) have now failed. If a later pass gets a live search budget, the highest-value targets are
NCES NHES:PFI, the AAP, and any state education agency publishing a field-trip or parental-consent
administrative count.

**Corrected totals, recomputed from the file.** Shallow objects = the sum of
`annual_frequency_per_family` over Q2 Treadmill + Q3 Recurrence; deep objects = the same over Q1
Campaign, with summer camp entered at its 7.5 sub-bookings.

| | shallow | deep | ratio |
|---|---|---|---|
| As Q1 counted it (permission slips 12/yr, birthday-attended at the killed 8–12 midpoint of 10) | 286.25 | 15.94 | **17.96 : 1** |
| Corrected (both rows dropped) | 264.25 | 15.94 | **16.58 : 1** |

The first line reproduces Q1's published "~280" and "18:1" pairing exactly, which confirms both
conventions. **But the corrected shallow count is ~264, not the ~250 Q1 reported — low by about 14 —
and the corrected ratio is ~17:1.** The claim survives: a 7.7% move, nowhere near the boundary, and
the finding it supports (parents face roughly an order of magnitude more shallow obligations than deep
campaigns) is untouched.

Two things to state wherever the ratio appears. **The convention matters more than the correction**: if
summer camp is counted as 1 annual cycle instead of 7.5 sub-bookings, the ratio is 30:1 before and 28:1
after — so name the convention. And **shallow is dominated by a single row**: weekly sports logistics
alone is 200 of the 264, and it rests on an analyst-defined step count over a non-probability Qualtrics
panel.
