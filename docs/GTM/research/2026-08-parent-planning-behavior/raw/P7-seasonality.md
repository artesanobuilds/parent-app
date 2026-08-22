# P7 — SEASONALITY: a month × task-family demand map for US parent planning

Collector P7. Compiled 2026-08-21. United States only. Cohort note: none of the seasonality
evidence below is broken out by parent generation — search-index data carries no age attribute.
Any generational split of seasonality is **no data found** and is flagged as such.

---

## METHOD NOTE — how the primary dataset was produced (so it can be re-run)

The single largest evidence source here is **Google Trends**, pulled directly from Google's
`trends/api` endpoints on 2026-08-21 (not from a third-party write-up). Exact parameters:

- `geo=US`, `category=0`, `property=""` (web search), `hl=en-US`, `tz=360`
- Timeframe `today 5-y` → resolved by Google to **2021-08-22 through 2026-08-22**, `resolution=WEEK`
- Endpoint chain: `GET /trends/api/explore` → take the `TIMESERIES` widget's `request` + `token`
  → `GET /trends/api/widgetdata/multiline`
- Post-processing: each weekly point assigned to its calendar month; **5 years of weekly values
  averaged per calendar month**; the 12 monthly means then re-scaled so peak month = 100.
  Averaging 5 years removes single-year noise and holiday-week artifacts.

**What Google Trends is and is not.** It is a normalized *relative* index of search interest on a
sample of Google searches, not a volume count, and Google does not publish the sample size. It is
therefore a strong instrument for *shape over time* (which is exactly the question asked here) and a
weak one for *absolute size* or for cross-topic comparison of magnitude. Per the brief's tier rules
I am filing it as **Tier B** — a major organization with a published methodology page — and I flag
explicitly that it is an index, not survey data. Comparisons *between* keywords below are always
about curve shape, never about absolute demand.

40 keyword series were pulled. The full monthly matrix is in Section 1.

---

# Section 1: FINDINGS

## 1a. The primary Google Trends matrix

All values = 5-year mean of weekly US search index, re-scaled so each **row's** peak month = 100.
Read across a row for shape. Do **not** read down a column to compare keywords by size.

| Keyword (US, 2021-08→2026-08) | Peak | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| summer camp | May | 50 | 63 | 72 | 78 | **100** | 99 | 59 | 21 | 11 | 12 | 17 | 21 |
| summer camp near me | May | 32 | 48 | 57 | 72 | **100** | 84 | 37 | 10 | 5 | 6 | 12 | 14 |
| kids camps near me | May | 29 | 41 | 54 | 68 | **100** | 98 | 48 | 14 | 8 | 9 | 12 | 16 |
| camp registration | May | 90 | 98 | 95 | 87 | **100** | 98 | 70 | 30 | 22 | 23 | 32 | 38 |
| spring break camp | Mar | 32 | 67 | **100** | 18 | 1 | 1 | 1 | 1 | 1 | 1 | 3 | 8 |
| winter break camp | Dec | 13 | 25 | 1 | 0 | 1 | 2 | 1 | 2 | 7 | 26 | 69 | **100** |
| kids activities near me | Jul | 64 | 77 | 88 | 74 | 71 | 98 | **100** | 79 | 67 | 84 | 68 | 75 |
| things to do with kids | Jul | 56 | 68 | 87 | 63 | 67 | 97 | **100** | 67 | 50 | 48 | 50 | 61 |
| after school program | Aug | 64 | 65 | 64 | 64 | 59 | 52 | 73 | **100** | 66 | 56 | 52 | 45 |
| swim lessons | Jun | 44 | 53 | 65 | 75 | 95 | **100** | 80 | 50 | 33 | 27 | 25 | 28 |
| dance classes for kids | Aug | 93 | 92 | 84 | 79 | 84 | 93 | 94 | **100** | 85 | 72 | 69 | 73 |
| gymnastics for kids | Aug | 86 | 85 | 86 | 88 | 86 | 86 | 97 | **100** | 80 | 73 | 92 | 84 |
| youth soccer registration | Jul | 52 | 69 | 67 | 38 | 57 | 66 | **100** | 59 | 10 | 0 | 14 | 9 |
| fall soccer registration | Jul | 0 | 0 | 3 | 3 | 38 | 58 | **100** | 45 | 0 | 0 | 0 | 0 |
| youth football registration | Jul | 22 | 46 | 67 | 35 | 50 | 71 | **100** | 33 | 6 | 0 | 20 | 23 |
| little league registration | Jan | **100** | 83 | 60 | 35 | 27 | 33 | 50 | 50 | 2 | 12 | 27 | 31 |
| youth baseball registration | Feb | 44 | **100** | 92 | 49 | 28 | 33 | 24 | 11 | 0 | 16 | 0 | 0 |
| youth basketball registration | Nov | 53 | 45 | 92 | 17 | 57 | 30 | 52 | 49 | 17 | 53 | **100** | 26 |
| swim team registration | May | 0 | 52 | 26 | 0 | **100** | 0 | 28 | 21 | 43 | 0 | 0 | 0 |
| back to school | Aug | 18 | 15 | 13 | 15 | 17 | 23 | 78 | **100** | 26 | 11 | 11 | 15 |
| back to school supplies | Aug | 1 | 4 | 4 | 5 | 8 | 16 | 63 | **100** | 7 | 2 | 1 | 1 |
| school supply list | Jul | 2 | 2 | 2 | 2 | 4 | 13 | **100** | 82 | 7 | 3 | 2 | 2 |
| school registration | Jul | 50 | 52 | 50 | 48 | 52 | 54 | **100** | 72 | 28 | 26 | 30 | 27 |
| parent teacher conference | Oct | 21 | 39 | 35 | 16 | 12 | 7 | 7 | 14 | 48 | **100** | 62 | 12 |
| family vacation ideas | Jan | **100** | 91 | 84 | 77 | 79 | 90 | 78 | 63 | 63 | 65 | 63 | 75 |
| spring break trip | Feb | 93 | **100** | 93 | 29 | 16 | 13 | 17 | 21 | 26 | 38 | 42 | 54 |
| family road trip | Jun | 69 | 88 | 85 | 76 | 88 | **100** | 85 | 57 | 49 | 51 | 62 | 68 |
| summer vacation | May | 46 | 57 | 64 | 70 | **100** | 98 | 67 | 46 | 25 | 22 | 25 | 31 |
| summer plans | May | 40 | 56 | 59 | 71 | **100** | 85 | 61 | 35 | 27 | 26 | 30 | 27 |
| pediatrician appointment | Jul | 81 | 82 | 77 | 84 | 93 | 92 | **100** | 90 | 68 | 75 | 70 | 68 |
| well child visit | Jul | 85 | 92 | 91 | 87 | 83 | 91 | **100** | 89 | 84 | 82 | 81 | 56 |
| dentist appointment | Jul | 86 | 87 | 95 | 88 | 91 | 92 | **100** | 92 | 75 | 75 | 77 | 73 |
| school physical | Aug | 75 | 86 | 83 | 86 | 88 | 76 | 86 | **100** | 77 | 72 | 70 | 54 |
| sports physical | Aug | 56 | 67 | 63 | 65 | 71 | 72 | 95 | **100** | 62 | 60 | 56 | 42 |
| flu shot | Oct | 20 | 11 | 7 | 4 | 4 | 4 | 5 | 18 | 67 | **100** | 58 | 37 |
| birthday party ideas | Jan | **100** | 83 | 79 | 78 | 74 | 74 | 84 | 85 | 91 | 79 | 65 | 63 |
| kids birthday party places | Jan | **100** | 86 | 78 | 63 | 55 | 51 | 60 | 69 | 77 | 75 | 68 | 65 |
| halloween costumes for kids | Oct | 2 | 3 | 3 | 3 | 4 | 5 | 12 | 30 | 73 | **100** | 3 | 2 |
| thanksgiving activities for kids | Nov | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 17 | **100** | 1 |
| christmas gift ideas for kids | Nov | 2 | 2 | 0 | 0 | 1 | 0 | 0 | 2 | 9 | 33 | **100** | 95 |

Source for every row: Google Trends, Google LLC, pulled 2026-08-21, US, web search,
weekly 2021-08-22→2026-08-22, monthly means (n = ~261 weekly observations per keyword).
Tier B. https://trends.google.com/trends/explore?date=today%205-y&geo=US

## 1b. The forward-year experiment — when does *next summer* planning actually start?

Generic "summer camp" conflates next-summer *planning* with this-summer *chatter*. Year-tagged
queries isolate planning. Monthly means of the weekly index, raw (peak = 100 across the whole
5-year window):

| Series | Jul | Aug | Sep | Oct | Nov | Dec | Jan | Feb | Mar | Apr | May | Jun |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| "summer camp 2025" (2024-07 → 2025-06) | 2 | 2 | 4 | 5 | **10** | **23** | **68** | 78 | 84 | 81 | 94 | 79 |
| "summer camp 2026" (2025-07 → 2026-06) | 3 | 2 | 3 | 4 | **9** | **18** | **57** | 64 | 78 | 76 | 89 | 83 |

Two independent camp cycles produce the same curve, which is a real replication, not a one-year
artifact: next-summer search is at floor Jul–Oct, roughly **doubles in November**, doubles again in
December, then **jumps ~3x into January**, and stays elevated Jan–Jun.

**This is the most decision-relevant number in this report.** The truly dead window for camp is
**August, September, October — three months, not six.** Camp demand re-ignites in November.

## 1c. Flatness ranking — coefficient of variation across the 12 monthly means

Lower CV = more even year-round demand. Trough = the lowest month's index (higher = flatter floor).

| Rank | Keyword | CV | Trough month index |
|---|---|---|---|
| 1 | gymnastics for kids | 0.078 | 73 |
| 2 | dentist appointment | 0.099 | 73 |
| 3 | dance classes for kids | 0.112 | 69 |
| 4 | well child visit | 0.119 | 56 |
| 5 | birthday party ideas | 0.124 | 63 |
| 6 | pediatrician appointment | 0.124 | 68 |
| 7 | school physical | 0.139 | 54 |
| 8 | **kids activities near me** | **0.142** | **64** |
| 9 | family vacation ideas | 0.153 | 63 |
| 10 | kids birthday party places | 0.185 | 51 |
| 11 | after school program | 0.210 | 45 |
| 12 | family road trip | 0.214 | 49 |
| … | things to do with kids | 0.252 | 48 |
| … | camp registration | 0.486 | 22 |
| … | **summer camp** | **0.633** | **11** |
| … | summer camp near me | 0.786 | 5 |
| … | back to school | 0.974 | 11 |
| … | flu shot | 1.076 | 4 |
| … | spring break camp | 1.577 | 1 |
| … | back to school supplies | 1.687 | 1 |
| … | christmas gift ideas for kids | 1.753 | 0 |
| … | thanksgiving activities for kids | 2.753 | 0 |

"summer camp" is **4.5x more seasonally volatile** than "kids activities near me" and has a floor
one-sixth as high.

## 1d. THE DELIVERABLE — month × task-family intensity map (0–3)

0 = essentially no demand · 1 = background · 2 = active · 3 = peak.
Ratings are assigned from the curves in 1a/1b, thresholded per row: 3 = row-normalized index ≥ ~75
or a known hard deadline in that month; 2 = 45–75; 1 = 15–45; 0 = < 15.

| Task family | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | Yr total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Summer camps | 3 | 3 | 3 | 3 | 3 | 2 | 1 | 0 | 0 | 1 | 1 | 2 | 22 |
| School-break coverage (winter/spring/PD) | 1 | 2 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 2 | 3 | 13 |
| Fall activity registration | 0 | 0 | 1 | 1 | 2 | 3 | 3 | 3 | 1 | 0 | 0 | 0 | 14 |
| Spring activity registration | 3 | 3 | 3 | 2 | 1 | 1 | 0 | 0 | 0 | 1 | 2 | 1 | 17 |
| Youth sports in-season logistics | 2 | 2 | 3 | 3 | 3 | 2 | 2 | 2 | 3 | 3 | 3 | 2 | 30 |
| School admin / back-to-school | 1 | 2 | 2 | 1 | 2 | 1 | 3 | 3 | 2 | 3 | 2 | 1 | 23 |
| Family vacations | 3 | 3 | 2 | 2 | 2 | 3 | 2 | 1 | 1 | 2 | 2 | 2 | 25 |
| Weekend outings | 2 | 2 | 3 | 2 | 2 | 3 | 3 | 2 | 2 | 3 | 2 | 2 | 28 |
| Medical / dental appointments | 2 | 2 | 2 | 2 | 2 | 2 | 3 | 3 | 3 | 3 | 2 | 2 | 28 |
| Birthday parties | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 3 | 3 | 2 | 2 | 2 | 27 |
| Holiday planning | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 2 | 3 | 3 | 3 | 14 |
| **Column total (all-task load)** | **20** | **22** | **25** | **20** | **19** | **19** | **19** | **17** | **17** | **22** | **21** | **20** | 241 |

### Per-row source justification

| Row | Justification |
|---|---|
| **Summer camps** | 1b forward-year replication (Nov doubling, Dec doubling, Jan 3x jump, elevated through Jun) sets Jan–May = 3 and Dec = 2; 1a "summer camp"/"camp registration" confirms the Jan–Jun plateau and the Aug–Oct floor (index 11–21). Aug/Sep = 0 is the strongest zero in the whole table. |
| **School-break coverage** | 1a "spring break camp" (Feb 67 → **Mar 100** → Apr 18, zero May–Oct) and "winter break camp" (Oct 7 → **Nov 69 → Dec 100**, Jan 13). Two clean, narrow, non-overlapping spikes. Feb-mid/Mar and Nov/Dec are the only live windows. PD/in-service days: no accessible national dataset found (see WEAK SIGNAL); not rated separately. |
| **Fall activity registration** | 1a "fall soccer registration" (May 38 → Jun 58 → **Jul 100** → Aug 45, zero Sep–Apr), "youth football registration" (Jun 71 → **Jul 100**), "after school program" (Jul 73 → **Aug 100**). Fall signup happens in **summer**, before the season, which is why this row is 3 in Jun/Jul/Aug and 0 in Sep–Feb. |
| **Spring activity registration** | 1a "little league registration" (**Jan 100** → Feb 83 → Mar 60), "youth baseball registration" (Jan 44 → **Feb 100** → Mar 92), "youth basketball registration" (**Nov 100**, Mar 92), "swim lessons" (Apr 75 → May 95 → **Jun 100**). Winter-sport signup in Oct/Nov drives Nov = 2. |
| **Youth sports in-season** | No seasonality dataset published — Aspen Institute *State of Play 2025* (Tier B; synthesizes NSCH 2023 n≈55.4% participation, SFIA 2024 household survey, Aspen National Youth Sports Parent Survey) reports participation levels and cost but **explicitly contains no season-length, month-of-participation, or registration-timing data** (verified by direct fetch 2026-08-21). This row is therefore rated from the standard US three-season interscholastic/rec structure implied by the registration curves above (fall signup Jun–Aug → fall season Aug–Nov; winter signup Oct–Nov → season Nov–Feb; spring signup Jan–Feb → season Mar–May) plus summer travel ball Jun–Jul. Confidence: **medium-low**. It is the flattest row in the table and it is also the least directly sourced — treat with care. |
| **School admin / back-to-school** | 1a "school supply list" (**Jul 100** → Aug 82, ~0 rest of year), "back to school supplies" (Jul 63 → **Aug 100**), "school registration" (**Jul 100** → Aug 72, but with a 48–54 floor Jan–Jun = rolling enrollment/lottery/next-year registration), "parent teacher conference" (Sep 48 → **Oct 100** → Nov 62, secondary bump Feb 39/Mar 35). Two-hump shape: a July/August supply-and-enrollment peak and an October conference peak. |
| **Family vacations** | 1a "family vacation ideas" is a **January-peaking** planning curve (**Jan 100**, Feb 91, Jun 90) with a very high 63 floor — booking intent leads travel by months. "spring break trip" peaks **Feb 100** (Jan 93, Mar 93), i.e. ~4–6 weeks before the trip. "family road trip" peaks **Jun 100** (in-season). Aug/Sep = 1 is the only real trough. |
| **Weekend outings** | 1a "kids activities near me" — flattest meaningful row in the dataset (CV 0.142, **trough 64**), peaks Jul 100/Jun 98 but with a secondary **Oct 84** and **Mar 88**; never drops below 64. "things to do with kids" same shape (CV 0.252, trough 48). This is structurally weekly demand modulated by weather and school breaks, not an annual event. |
| **Medical / dental** | 1a "dentist appointment" (CV 0.099, trough 73 — the flattest health series), "pediatrician appointment" (CV 0.124, trough 68), "well child visit" (CV 0.119). Overlaid on that flat base are two real spikes: the **back-to-school physical** — "school physical" **Aug 100** and "sports physical" Jul 95 → **Aug 100** — and **flu season**, "flu shot" Sep 67 → **Oct 100** → Nov 58, near-zero Feb–Aug. Hence Jul–Oct = 3, everything else = 2 with no month below 2. |
| **Birthday parties** | 1a "birthday party ideas" (CV 0.124, trough 65 in Nov, **Jan 100**, secondary Sep 91/Aug 85) and "kids birthday party places" (**Jan 100**, Sep 77). Aug/Sep rated 3 because that is the venue-search secondary peak; Jan rated 3 on the New-Year planning peak. A near-flat row driven by the fact that birthdays are distributed across all 12 months. |
| **Holiday planning** | 1a "halloween costumes for kids" (Sep 73 → **Oct 100**, ~0 Nov–Aug), "thanksgiving activities for kids" (Oct 17 → **Nov 100**, ~0 all else), "christmas gift ideas for kids" (Oct 33 → **Nov 100** → Dec 95, ~0 Jan–Aug). The most extreme seasonality in the entire dataset (CV 1.75–2.75). Feb/Mar/Apr = 1 for Valentine's/Easter, unmeasured here. |

## 1e. Interpretation for the product decision

**The "camps are dead half the year" framing is wrong by three months, and the correction is
actionable.** The forward-year experiment (1b) — replicated across two independent camp cycles —
shows next-summer camp search rising in November, tripling in January, and holding through June.
The genuinely dead window is **August, September, October**. Eight months of the year the camp
vertical has real demand; three do not. That reframes the structural risk from "half the year" to
"one quarter," and it names the exact quarter that needs a different anchor.

**But camp is still the most volatile row in the table by a wide margin.** Its trough index (11) is
one-sixth the trough of "kids activities near me" (64) and it is 4.5x more volatile by CV. A product
whose *default-on* verticals are camp and outing (per the product description) has exactly one
all-season door open — outing — and it is currently the secondary one. The Aug–Oct hole is
covered almost perfectly by three task families that are all currently **behind feature flags that
default off**: school_event (Aug–Oct is its absolute peak: supply lists Jul/Aug 100, conferences
Oct 100), extracurricular (fall registration peaks Jun–Aug), and — for Sep–Dec — holiday planning,
which the product does not model at all. **The seasonal fix is a flag flip, not a new build.**

**The column totals are startlingly flat: 17 to 25 across all twelve months, a 1.47x spread.**
Aggregate parent planning load has no off-season. It rotates. March is the busiest month (25:
summer camp + spring break camp + spring sports registration + conferences all live simultaneously);
August and September are the quietest at 17 — and they are quiet only because camp goes to zero
exactly when back-to-school peaks. This is the central strategic read: **the product's problem is not
that parent demand is seasonal — it is that the product's coverage is narrower than the demand.**

**Registration for a season happens one to two seasons before the season.** Fall sports signup
peaks in **July** (index 100) and is at zero in September when the fall season is actually underway.
Spring baseball signup peaks in **January–February**. Winter basketball signup peaks in **November**.
Camp registration begins in **November** for a June start. Every single registration curve leads its
season by 2–6 months. A registration-window watchlist with push notifications — which the product
already ships — is therefore the single most seasonality-proof feature in the app, because *some*
registration window is open in every month of the year. The rotation is: Nov (winter sports, camp
opens, winter-break camp) → Jan–Feb (spring sports, camp mass wave) → Mar (spring-break camp) →
Jun–Aug (fall sports, after-school) → Oct–Nov (winter sports) and around again.

**Three task families are effectively aseasonal and the product does not serve any of them well.**
Medical/dental (CV 0.099–0.124, no month below 2), birthday parties (CV 0.124), and weekend outings
(CV 0.142) are the flat rows. The product has no general appointment-capture surface at all
(explicitly listed as Absent), no birthday-party concept, and treats outings as a discovery-agent
search rather than a recurring weekly loop. A generic "add an appointment / remind me" surface would
land on the flattest demand curve measured in this study — and it is the one thing the product
audit lists as missing.

**The travel curve is a lead-time curve, not a travel curve, and that matters for notification
design.** "family vacation ideas" peaks in **January** (100) — six months before the trips it
describes — and "spring break trip" peaks in **February**, roughly 4–6 weeks ahead. Parents search
when they *book*, not when they *go*. Any feature that surfaces travel help in June is arriving
five months late. The same logic applies to every registration row above.

**Explicit contradiction inside the data.** Generic "summer camp" peaks in **May** (100) while the
year-tagged "summer camp 2026" peaks in **May** too but is already at 57 in January and only 4 in
October — whereas generic "summer camp" reads 12 in October. The generic query's May peak is
substantially *in-season* traffic (parents of kids already enrolled, last-minute June/July fill,
camp staff, media) rather than planning traffic. **If you plan the product calendar off the generic
curve you will staff the camp vertical for May and miss the November–January decision window, which
is when placement is actually determined.** The forward-year series is the one to trust.

**Contradiction between search interest and stated industry timing.** Widely-repeated claims that
camp registration "opens in November–December" and that January–February carry the bulk of
registrations could not be traced to any Tier A/B/C origin (see WEAK SIGNAL). The Trends forward-year
data is *directionally consistent* with them — Nov is the inflection — but the search data puts the
*mass* of parent activity in January–May, not November–December. Registration opening and parent
searching are not the same event, and the gap between them (roughly 6–10 weeks) is itself the
product opportunity: that is precisely the interval a watchlist-plus-notification feature exists to
close.

---

# Section 2: WEAK SIGNAL (not citable — do not promote into findings)

- **Camp registration open dates (ACA and large operators).** *Could not source.* `acacamps.org` is
  behind Cloudflare and returned HTTP 403 to every fetch attempt on 2026-08-21 (four distinct paths:
  `/families/planning-camp`, `/families/planning-camp/`, `/resource-library/articles/when-register-camp`,
  `/news-publications/press-room`). Search results surfaced only Tier D content — camp-vendor blogs
  (film.camp, campsearch.com, jumbula.com, ultracampmanagement.com), a regional parenting magazine
  (Metrokids), and a WordPress blog — carrying assertions such as "overnight camps take deposits
  starting in September," "day camps open November–February," "sports camps open January–February,"
  "the vast majority of non-profit and YMCA camps open portals between January 1 and February 1," and
  "49% of revenue in January–February / 5,900% January ROI." **None of these disclose method, sample,
  or origin.** Per the brief's hard rule they are unusable. The 5,900% ROI figure in particular has
  the signature of stat laundering — a single vendor case study circulating without attribution.
  Recommended next step for a verifier: fetch ACA via a real browser session, and pull actual
  published registration-open dates from 8–10 named large operators (YMCA of the USA affiliates,
  Steve & Kate's, Camp Invention, JCC associations, municipal parks departments) as primary evidence.
- **Youth sports season and registration windows by sport.** No Tier A/B source found that publishes
  US season calendars nationally. Aspen *State of Play 2025* was fetched and verified to contain none.
  NFHS state-association calendars would be primary but are 51 separate documents. The "Youth sports
  in-season" row of the deliverable is my own construction from registration-lead curves — **it is the
  weakest-sourced row in the table** and is flagged as such in its justification cell.
- **School calendar rhythm — start dates by region, conference weeks, testing windows, count and
  distribution of no-school days.** *Could not source.* NCES Digest table 234.10 turned out to be
  compulsory-attendance ages, not instructional days; the d23/d24 equivalents 404'd or were
  Cloudflare-blocked; ECS 50-state instructional-time comparison returned a CAPTCHA notice; the Pew
  short read on back-to-school dates 404'd. The commonly-cited "180 instructional days" figure is
  therefore **unverified here**. What I *can* say from Trends is that the national back-to-school
  search peak is a two-month ramp (Jul 78 → Aug 100 for "back to school"), consistent with the known
  South-early / Northeast-late split, but Trends geo-splitting by state was not performed. The
  distribution of PD/in-service no-school days across the year — arguably the single most
  product-relevant school-calendar fact, since those are the days that create coverage gaps — has
  **no data found** at national level.
- **CDC flu-shot timing recommendation.** The Oct-100 / Sep-67 / Nov-58 search curve is solid Tier B
  Trends data, but I could not fetch the underlying CDC recommendation text to cite alongside it —
  `cdc.gov` returned HTTP 403 (Akamai edge) on three separate paths on 2026-08-21. The clinical
  recommendation is treated here as unsourced context, not a finding.
- **AAP well-child periodicity schedule.** The PDF at `downloads.aap.org` fetched successfully but
  returned as undecodable binary; visit ages were not extracted. Not used as a finding.
- **Travel booking lead times / peak booking months for family travel.** *Could not source.*
  `ustravel.org` returned 403. The January-peak booking-intent shape is established from Trends only.
  No airline/OTA (ARC, Expedia Group, Deloitte travel survey) lead-time figure was verified.
- **Consumer app engagement seasonality for family/parenting apps.** *No data found.* Nothing
  published at Tier A/B/C was located. Note the web-search budget for this session was exhausted
  (200/200) before this item could be pursued; a follow-up collector should treat it as unexplored
  rather than as absent.
- **Any generational (Gen Z / Millennial / Gen X parent) split of seasonality.** *No data found, and
  none is expected to exist* — search-index data carries no respondent age, and no survey was found
  that fields the same planning question across months and generations.

## Confidence

- **High** — the shape of every Trends curve in 1a, the forward-year camp result in 1b, and the
  flatness ranking in 1c. These are direct pulls from a primary endpoint, replicable with the
  parameters documented above, and the camp result replicates across two independent years.
- **Medium** — the 0–3 ratings in the deliverable table. The curves are solid; the thresholding of a
  continuous index into four buckets is my judgment call.
- **Low** — the "Youth sports in-season" row, and any claim about school-calendar structure or
  travel booking windows, none of which I could source to an accessible Tier A/B/C publisher.

## Limits of this study

Everything quantitative here is search-behavior data. Search interest is a proxy for planning
intent; it is not participation, spend, or app engagement. It over-weights tasks people research
online (camp discovery, party venues, vacation ideas) and under-weights tasks people execute without
searching (renewing an existing activity, a recurring pediatric appointment, the fourth season with
the same soccer club). The flat rows in this table may therefore be *understated* relative to the
spiky ones, since a repeat registration generates no search at all — which, if anything, strengthens
rather than weakens the central conclusion below.
