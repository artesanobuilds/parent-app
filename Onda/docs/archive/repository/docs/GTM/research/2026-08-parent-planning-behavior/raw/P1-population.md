# P1 — The US Parent Population, Sized and Segmented

Collector P1. Compiled 2026-08-21. Geography: **United States only.**
Cohort bands per BRIEF.md: Gen Z parents = born 1997–2012 (age ~18–29 in 2026); Millennial = 1981–1996 (~30–45); Gen X = 1965–1980 (~46–61).

**Sourcing note.** bls.gov, cdc.gov and dol.gov all return HTTP 403 to automated fetchers from this
environment. Where a BLS number appears below it was recovered from indexed text of the BLS release
itself (bls.gov/news.release/famee.nr0.htm), not from a secondary blog; the CDC natality figures were
recovered from the NIH/NCBI Bookshelf mirror of the identical NCHS report (NVSR 75-02), which is the
same peer-reviewed government document. Census figures were pulled as **raw Census .xls/.xlsx data
tables** from www2.census.gov and parsed directly — those are first-party, not summaries.

**Derivations are labelled.** Census publishes parent counts by *age of householder* in 5-year bands,
not by generation. Rows marked **A-derived** are my arithmetic on a Tier A table, with the mapping
assumption stated. They are not fabricated, but they are not published numbers either.

---

## Section 1: FINDINGS

| # | Claim (one sentence, with the number) | Value | Cohort/segment | Publisher | Year | Method (n, fielding window, population) | Tier | URL |
|---|---|---|---|---|---|---|---|---|
| 1 | There are **33.56 million US families with own children under 18**. | 33,562,000 families | All parents | US Census Bureau, Table FM-1 | 2025 | CPS ASEC, March 2025 supplement, ~60,000 addresses; universe = families, "own children" = never-married bio/step/adopted children under 18 | A | https://www2.census.gov/programs-surveys/demo/tables/families/time-series/families/fm1.xls |
| 2 | **72.73 million children under 18** live in the US. | 72,734,000 children | All kids | US Census Bureau, Table CH-1 | 2025 | CPS ASEC March 2025; excludes children in group quarters and householders/spouses under 18 | A | https://www2.census.gov/programs-surveys/demo/tables/families/time-series/children/ch1.xls |
| 3 | Roughly **62.1 million adults are parents living with a child under 18** (2×married-couple + 2×cohabiting-parent-couple + solo mothers + solo fathers). | 62,101,000 parents | All parents | **A-derived** from US Census Table FG10 | 2023 | CPS ASEC March 2023 family-group counts: 24,040K married couples w/ kids + 1,871K unmarried parent couples (both ×2) + 8,242K mother-only + 2,037K father-only groups | A-derived | https://www2.census.gov/programs-surveys/demo/tables/families/2023/cps-2023/tabfg10-all.xls |
| 4 | Family households with own children under 18, by **age of householder**: under 25 = 919K; 25–29 = 2,712K; 30–34 = 5,529K; 35–39 = 6,885K; 40–44 = 6,863K; 45–49 = 5,194K; 50–54 = 3,045K; 55–64 = 1,733K; 65+ = 410K (total 33,289K, mean age 40.9). | see cells | All parents, by age | US Census Bureau, Table F1 | 2023 | CPS ASEC March 2023; universe = family households with own children under 18 | A | https://www2.census.gov/programs-surveys/demo/tables/families/2023/cps-2023/tabf1-all.xls |
| 5 | Mapping Table F1's age bands to birth cohorts: **Gen Z ≈ 2.0M parent households (6.0%), Millennial ≈ 18.2M (54.5%), Gen X ≈ 11.7M (35.1%)**, remainder Boomer+ ≈ 1.4M (4.4%). | 2.0M / 18.2M / 11.7M | All three cohorts | **A-derived** from Census Table F1 | 2023 | Linear split of the 25–29 band (40% Gen Z), the 40–44 band (60% Millennial), and the 55–64 band (40% Gen X) by birth year; assumes uniform ages within band | A-derived | (same as #4) |
| 6 | In people terms that is roughly **3.7M Gen Z parents, 33.9M Millennial parents, 21.8M Gen X parents**. | 3.7M / 33.9M / 21.8M | All three cohorts | **A-derived** (finding #3 × finding #5 shares) | 2023 | Applies household-level cohort shares to the 62.1M parent count; assumes coupling rate does not vary by cohort (it does — see interpretation) | A-derived | — |
| 7 | Average number of own children under 18 per family that has any is **1.94**. | 1.94 | All parents | US Census Bureau, Table FM-3 | 2023 | CPS ASEC March 2023; married-couple families 1.99, solo-father 1.65, solo-mother 1.88 | A | https://www2.census.gov/programs-surveys/demo/tables/families/time-series/families/fm3.xls |
| 8 | Among family households with a member under 18: **43.2% have one child, 36.3% have two, 20.5% have three or more** (15,751K / 13,213K / 7,478K of 36,443K). | 43.2 / 36.3 / 20.5 % | All parents | US Census Bureau, Table F1 | 2023 | CPS ASEC March 2023, "number of family members under 18" panel | A | (same as #4) |
| 9 | Average own children per family household rises then falls with parent age: **1.39 (age 20–24), 1.83 (25–29), 2.01 (30–34), 2.19 (35–39), 2.09 (40–44), 1.84 (45–49), 1.62 (50–54)**. | see cells | By parent age | US Census Bureau, Table AVG3 | 2023 | CPS ASEC March 2023; SEs 0.02–0.04 | A | https://www2.census.gov/programs-surveys/demo/tables/families/2023/cps-2023/tabavg3.xls |
| 10 | **Share of parent households that contain a child under 6**, by householder age: under 25 = 90.5%; 25–29 = 84.1%; 30–34 = 70.8%; 35–39 = 54.9%; 40–44 = 28.4%; 45–49 = 12.8%; 50–54 = 7.1%. | see cells | By parent age | **A-derived** from Census Table F1 | 2023 | Row "with own children under 6" ÷ row "with own children under 18", within each age-of-householder column | A-derived | (same as #4) |
| 11 | **Share of parent households that contain a child 12–17**, by householder age: under 25 = 6.2%; 25–29 = 7.5%; 30–34 = 22.8%; 35–39 = 37.6%; 40–44 = 58.9%; 45–49 = 73.5%; 50–54 = 80.7%. | see cells | By parent age | **A-derived** from Census Table F1 | 2023 | Same method as #10 | A-derived | (same as #4) |
| 12 | **Share of parent households that contain a child 6–11**, by householder age: under 25 = 14.1%; 25–29 = 40.4%; 30–34 = 51.5%; 35–39 = 60.7%; 40–44 = 58.3%; 45–49 = 42.8%; 50–54 = 26.9%. | see cells | By parent age | **A-derived** from Census Table F1 | 2023 | Same method as #10 | A-derived | (same as #4) |
| 13 | **Share of parent households with a child under 3** (peak logistics-free zone): under 25 = 73.3%; 25–29 = 56.4%; 30–34 = 42.6%; 35–39 = 28.5%; 40–44 = 10.8%; 45–49 = 4.0%. | see cells | By parent age | **A-derived** from Census Table F1 | 2023 | Same method as #10 | A-derived | (same as #4) |
| 14 | Children under 18 split **22.33M under 6 / 24.16M ages 6–11 / 25.81M ages 12–17** (30.9% / 33.4% / 35.7%). | 22,326K / 24,156K / 25,814K | All kids | US Census Bureau, Table C2 | 2023 | CPS ASEC March 2023 | A | https://www2.census.gov/programs-surveys/demo/tables/families/2023/cps-2023/tabc2-all.xls |
| 15 | Of families with own children under 18, **69.5% are married-couple (23,323K) and 30.5% are one-parent (10,239K)** — 22.8% mother-only (7,666K), 7.7% father-only (2,574K). | 69.5 / 22.8 / 7.7 % | All parents | US Census Bureau, Table FM-1 | 2025 | CPS ASEC March 2025 | A | (same as #1) |
| 16 | **1.87 million cohabiting (unmarried) parent couples** with at least one joint never-married child under 18 — 2.1% of all family groups. | 1,871,000 couples | All parents | US Census Bureau, Table FG10 | 2023 | CPS ASEC March 2023; family-group universe of 89,179K | A | (same as #3) |
| 17 | Of all children under 18: **70.4% live with two parents (51,202K), 25.6% with one parent (18,647K — 21.0% mother-only, 4.6% father-only), 4.0% with neither (2,885K)**. | see cells | All kids | US Census Bureau, Table CH-1 | 2025 | CPS ASEC March 2025 | A | (same as #2) |
| 18 | Single-mother living arrangements **rise with child age**: 18.2% of children under 6 live with mother only vs 22.2% of children 15–17. | 18.2% → 22.2% | By kid age | **A-derived** from Census Table C2 | 2023 | 4,055K/22,326K vs 2,933K/13,202K | A-derived | (same as #14) |
| 19 | In **66.3% of married-couple families with children, both parents were employed**; at least one parent was employed in **91.6%** of all families with children. | 66.3% / 91.6% | Couples w/ kids | US Bureau of Labor Statistics, *Employment Characteristics of Families* | 2025 annual averages (rel. 2026) | CPS annual averages; universe = families with own children under 18 | A | https://www.bls.gov/news.release/famee.nr0.htm |
| 20 | Labor-force participation was **73.9% for mothers and 93.7% for fathers** of children under 18. | 73.9% / 93.7% | All parents | US Bureau of Labor Statistics (TED) | 2025 annual averages | CPS annual averages | A | https://www.bls.gov/opub/ted/2026/labor-force-participation-rate-was-73-9-percent-for-mothers-and-93-7-percent-for-fathers-in-2025.htm |
| 21 | Maternal LFPR by age of youngest child: **68.0% when youngest is under 6, 78.2% when youngest is 6–17**. | 68.0% / 78.2% | Mothers, by kid age | US Bureau of Labor Statistics, *Employment Characteristics of Families* | 2025 annual averages | CPS annual averages | A | https://www.bls.gov/news.release/famee.nr0.htm |
| 22 | Dual-earner intensity also rises with kid age in the Census cross-tab: of married couples with own children under 6, **65.3% have both spouses in the labor force**; with children 6–17, **69.4%**. | 65.3% / 69.4% | Couples, by kid age | US Census Bureau, Table FG1 | 2023 | CPS ASEC March 2023: 6,823K of 10,449K; 12,874K of 18,543K | A | https://www2.census.gov/programs-surveys/demo/tables/families/2023/cps-2023/tabfg1-all.xls |
| 23 | **52.7% of US families with a child under 18 had family income of $100,000 or more** in 2024 (19,390K of 36,820K). | 52.7% | All parents | US Census Bureau, Table FINC-03 | 2024 income (CPS ASEC 2025) | CPS ASEC March 2025, universe = primary families, related children under 18; income = total money income for calendar 2024 | A | https://www2.census.gov/programs-surveys/cps/tables/finc-03/2025/finc03_1_1.xlsx |
| 24 | **34.8% of families with a child under 18 are at $150K+ and 22.3% at $200K+**; median family income for this group is **$105,400** (SE $1,036), mean $146,700. | 34.8% / 22.3% / $105,400 | All parents | US Census Bureau, Table FINC-03 | 2024 income (CPS ASEC 2025) | Same as #23 | A | (same as #23) |
| 25 | Income per family member is **$35,960 in families with children vs $58,360 in families without** — a 38% per-head gap. | $35,960 vs $58,360 | Parents vs non-parents | US Census Bureau, Table FINC-03 | 2024 income (CPS ASEC 2025) | Same as #23 | A | (same as #23) |
| 26 | US public K–12 enrollment by locale: **suburban 38.9% (19.18M), city 29.7% (14.66M), rural 20.3% (9.99M), town 10.8% (5.31M)**. | see cells | Families w/ school-age kids | NCES, Digest of Education Statistics Table 214.40 | Fall 2022 (pub. 2023) | Common Core of Data universe count of all public schools; locale = NCES/Census locale codes. Proxy: public-school children, ~90% of K–12 | A | https://nces.ed.gov/programs/digest/d23/tables/xls/tabn214.40.xlsx |
| 27 | There were **3,628,934 US births in 2024**, distributed by maternal age: <15 = 1,727; 15–19 = 137,273; 20–24 = 611,800; 25–29 = 990,817; 30–34 = 1,112,409; 35–39 = 622,517; 40–44 = 141,515; 45–49 = 9,688; 50–54 = 1,188. | see cells | Birth cohort | CDC/NCHS, *Births: Final Data for 2024*, NVSR 75-02, Table 3 | 2024 (pub. 2025/26) | 100% of US birth certificates (National Vital Statistics System natality file) | A | https://www.cdc.gov/nchs/data/nvsr/nvsr75/nvsr75-02.pdf (mirror: https://www.ncbi.nlm.nih.gov/books/NBK623381/) |
| 28 | **48.0% of 2024 births were to mothers under 30** (1,741,617 of 3,628,934); ~**37% were to Gen Z mothers** (women under 28 in 2024). | 48.0% / ~37% | Gen Z / young parents | **A-derived** from NCHS NVSR 75-02 Table 3 | 2024 | Sum of <15/15–19/20–24/25–29 rows; Gen Z figure assumes uniform distribution within the 25–29 band to isolate ages 25–27 | A-derived | (same as #27) |
| 29 | **Mean age of mother at first birth hit a record high 27.6 years** in 2024 (27.5 in 2023); there were 1,427,020 first births. | 27.6 years | First-time parents | CDC/NCHS, NVSR 75-02 | 2024 | NVSS natality file, 100% of birth certificates | A | (same as #27) |
| 30 | Birth rates fell to **record lows for women 20–24 (55.8/1,000, −3% y/y) and 25–29 (89.5/1,000, −2%)**, while the 30–34 rate (93.7) has exceeded the 25–29 rate every year since 2016. | see cells | Gen Z / Millennial | CDC/NCHS, NVSR 75-02, Table 2 | 2024 | NVSS natality file | A | (same as #27) |
| 31 | The share of US **family households that include own children under 18 fell from 54% (1975) to 39% (2025)**; married-couple households with own children fell from 54% to ~37%. | 39% | All households | US Census Bureau press release CB25-TPS.xx (AFLA 2025) | 2025 | CPS ASEC March 2025 | A | https://www.census.gov/newsroom/press-releases/2025/families-and-living-arrangements.html |
| 32 | Only **11.0% of children live in a household where neither parent present is in the labor force or no parent is present** — i.e. ~89% of kids have at least one working parent in the home. | 11.0% | All kids | **A-derived** from Census Table C3 | 2023 | (3,450K mother-NILF-no-father + 362K father-NILF-no-mother + 1,387K neither-in-LF + 3,073K no-parent/same-sex) ÷ 72,296K | A-derived | https://www2.census.gov/programs-surveys/demo/tables/families/2023/cps-2023/tabc3-all.xls |

---

### Interpretation

**1. The addressable base is Millennial, overwhelmingly, and that will not change during this product's
planning horizon.** Millennials hold roughly 18.2M of the 33.3M parent households (54.5%) and Gen X
another 11.7M (35.1%). Gen Z is ~2.0M households — about **6%** of the base (findings #4–5). Even with
the fastest plausible aging-in, Gen Z cannot approach Millennial scale before the early 2030s, and the
2024 natality data says it will arrive smaller than any recent cohort: birth rates at ages 20–24 and
25–29 both hit record lows in 2024, and mean age at first birth hit a record high 27.6 (#29–30). Gen Z
parents are a *research* population, not a *targeting* population, for a 2026–2028 roadmap. Designing
the app's defaults around them would be optimizing a 6% tail.

**2. Kid age — not parent age — is the real segmentation variable, and the two are tightly coupled.**
Findings #10–13 are the most decision-relevant numbers in this report. 84% of parent households headed
by a 25–29-year-old contain a child under 6, and 56% contain a child under 3; only 7.5% contain a
teenager. Invert it at 45–49: 73.5% have a 12–17-year-old, 12.8% have a preschooler. The product's
five verticals map onto this cleanly and brutally. **Camp, extracurricular, school_event and trip are
essentially irrelevant to a household whose only child is under 3** — there is nothing to register for,
no school calendar, no camp season. That describes roughly half of all Gen Z-headed parent households.
The one vertical that survives at every kid age is `outing` — which is, notably, one of the two
verticals currently on by default. The default-on choice looks right; the cohort framing behind it does
not, because the same logic says the *typing/complexity* argument for Gen Z ("they're young, they'll
absorb more") is applied to the population with the least to plan.

**3. The paying segment is large and is mostly Millennial.** 52.7% of families with a child under 18
cleared $100K in 2024 income and 22.3% cleared $200K (#23–24) — that is ~19.4M families above $100K,
which at a $99–149 price point is not a niche. But note #25: income *per family member* in families
with children is $35,960 against $58,360 in families without. Parents are richer households and poorer
individuals. The willingness-to-pay case has to rest on time saved, not on discretionary income, and it
has to survive against the fact that these same families are already spending $1,016/child on youth
sports (already known).

**4. Two-earner is the norm and it intensifies exactly when planning load intensifies.** 66.3% of
married-couple families with children have both parents employed (#19), and both the BLS and Census
cross-tabs show participation *rising* with the age of the youngest child — maternal LFPR 68.0% under 6
vs 78.2% at 6–17 (#21), both-in-labor-force 65.3% vs 69.4% (#22). The naive read is "younger kids =
more time at home = less need for a planning tool." The counter-read, which I think is correct, is that
the tool's demand peaks where three things coincide: school-age children (registration seasons, school
calendars, activities), two working parents, and 2+ kids. That intersection is the 35–44 householder
band — 13.7M households, Millennial, mean 2.1–2.2 children, ~60% with a 6–11-year-old. That is the
product's real center of gravity, and it is not the youngest cohort.

**5. Two-thirds of the base has one or two kids, and the onboarding cost scales with N.** 43.2% of
parent households have exactly one child under 18 and 36.3% have two (#8). The audited onboarding is
8+N screens and 14 input fields for one kid, 19 for two — so ~80% of the addressable market faces the
14–19-field version, not the worst case. That is the good news. The bad news is that the modal family
is *small*: at 1.94 children average (#7), the multi-kid coordination features that justify a "family
operating system" framing apply in full to only the 20.5% with three or more.

**6. Nearly a third of parent families are single-parent, and the product has no answer for the
second household.** 30.5% of families with own children under 18 are one-parent (#15) and 25.6% of
children live with one parent (#17); single-mother arrangement share *rises* with child age, to 22.2%
at 15–17 (#18). Add 1.87M cohabiting parent couples (#16). The Circle tab is private conversations and
invites; there are no shared or assignable task lists with a partner and no document vault. For roughly
10.2M single-parent families — the segment that OurFamilyWizard prices at $110–299/parent/yr, i.e. the
one segment with a demonstrated $100+ willingness to pay — the missing feature is the *co-parent
handoff*, and it is absent. This is the single clearest population-to-product gap in this report.

**7. Contradiction to flag: the "number of families with children" depends entirely on definition, and
the spread is ~3.3M.** Census FM-1 reports 33,562K families with **own** children under 18 (2025);
Census FINC-03 reports 36,820K primary families with **related** children under 18 (ASEC 2025); Census
F1 reports 36,443K family households with any **member** under 18 (2023); Census FG10 reports family
*groups* (which count subfamilies separately) and so produces 8,242K mother-only groups against FM-1's
7,291K mother-only families for the same year. Anyone quoting "35 million American families with kids"
is quoting one of four different universes. **For TAM work, use 33.6M families / 62M parents /
72.7M children, and state the definition.** I have used FM-1 and CH-1 (2025) for headline counts and
F1/FG10 (2023) only where a 2025 cross-tab does not exist.

**8. Second contradiction: Census's own 2025 detail tables were not published.** The Census Bureau
released *America's Families and Living Arrangements: 2025* as a press release and updated time-series
tables in December 2025, but the detailed FG/C/F/AVG table set for 2024 and 2025 is not on census.gov
(both `/data/tables/2024/demo/families/cps-2024.html` and the 2025 equivalent return 404; the newest
published detail set is 2023). Every cross-tab in this report — parent age × kid age, dual-earner ×
kid age, cohabiting couples — is therefore **2023 data**, three years stale, while the headline counts
are 2025. The direction of drift is small (families with own children: 33,290K in 2023 → 33,562K in
2025, +0.8%) so the shares are safe, but the levels should be treated as ±1%.

**9. Geography is suburban, and the discovery agent's ZIP+radius model fits that.** 38.9% of public
K–12 students are in suburbs, 29.7% in cities, 20.3% rural, 10.8% in towns (#26). Two-fifths of the
market is suburban, where a radius search over camps and activities returns dense results; but one in
five children is rural, where a ZIP+radius discovery agent returns thin or empty result sets. There is
no published Census cross-tab of *families with children* by urban/suburban/rural — this is the
weakest-sourced item in the report and the school-enrollment locale distribution is a proxy, not the
thing itself.

---

## Section 2: WEAK SIGNAL

Everything below could **not** be sourced to Tier A/B/C at the required standard. Do not promote any of
it into a deck without further verification.

- **Number of Gen Z parents in 2026, published.** No US statistical agency publishes parent counts by
  generation. Pew has published "37 million Millennials are parents of children under 18" in secondary
  circulation, but I could not trace that to a Pew report with an n, a fielding window, and a
  definition — the number surfaced only via search summary and aggregator restatement. Treat it as
  unverified; note it is also ~10% above my Tier A-derived 33.9M (#6), and the gap is exactly the kind
  of definitional slippage described in interpretation §7. **Do not cite the 37M figure.**
- **Urban / suburban / rural split of families with children specifically.** Not published by Census as
  a cross-tab. Finding #26 substitutes public-school enrollment locale. A true household-level split
  would require an ACS microdata or API pull; api.census.gov now requires a key, which this environment
  does not have.
- **Two-household-after-separation counts (children with a formal shared-custody arrangement).** Census
  publishes custodial-parent and child-support statistics (the P60 "Custodial Mothers and Fathers"
  series), but no current-year count of children splitting time across two households was retrievable
  in this session. The 18.6M children living with one parent (#17) is an upper bound on the population,
  not a measure of shared custody. This is a real gap and it sits directly on top of the biggest
  product gap identified in interpretation §6 — worth a dedicated follow-up pull.
- **Kid-age distribution *within* Gen Z parents specifically, as published data.** Findings #10–13 are
  computed at the age-of-householder level, and the youngest published band is "under 25". The 25–29
  band straddles the Gen Z/Millennial boundary; I split it 40/60. A true cohort cut needs CPS or ACS
  microdata.
- **Mothers' LFPR with youngest child under 3.** BLS publishes it (famee Table 6), but bls.gov returned
  403 to every fetch method available here and the number did not surface in indexed text. The under-6
  figure (68.0%, #21) is the finest cut I can defend.
- **Growth trajectory of the Gen Z parent cohort as a projection.** Findings #27–30 give the inputs
  (births by maternal age, record-low 20s birth rates, record-high age at first birth) but no
  agency publishes a projected count of Gen Z parents. Any forward number in a deck would be my
  extrapolation and must be labelled as such.
- **Distribution of family income by parent cohort.** FINC-03 does not cross income with age of
  reference person in the published cut used here. The $100K+ share (#23) is for all families with
  children; it is near-certainly lower for Gen Z-headed families and higher for Gen X, but I have no
  number.
