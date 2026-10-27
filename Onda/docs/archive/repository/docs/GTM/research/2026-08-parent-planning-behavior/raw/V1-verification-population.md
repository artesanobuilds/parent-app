# V1 — Adversarial verification of P1 (population) and P2 (who plans)

Verifier V1. Run 2026-08-21. Posture: refute by default; "CONFIRMED" means I reached the primary
source and matched the figure digit-for-digit, not that it looked reasonable.

## How I got to the sources

- **Census**: downloaded the raw `.xls`/`.xlsx` from `www2.census.gov` and parsed every cell
  (FM-1, FM-2, FM-3, CH-1, F1, FG1, FG10, AVG3, C2, C3, FINC-03). First-party, no summaries.
- **NCES**: downloaded `tabn214.40.xlsx` from nces.ed.gov and parsed the Fall 2022 panel.
- **NCHS**: pulled `nvsr75-02.pdf` and read Table 3 directly.
- **BLS**: `bls.gov` returns **HTTP 403 to every method available here** (curl with browser UA,
  WebFetch). P1 documents this honestly; **P2's header claim that "All ATUS tables [were] fetched
  directly from bls.gov" cannot be true from this environment.** I got around it via the Wayback
  Machine (`id_` raw snapshots) and recovered the full ATUS 2025 release (t03, t08A, t08B, t08C,
  t10, nr0, tn) plus the archived **2015** and **2019** Table 8A. Every ATUS figure below was
  checked against those originals. P2's numbers are real; only its provenance sentence is wrong.
- **Pew / Gallup / PMC / SagePub / HHS**: WebFetch, plus the 57-page Pew PDF pulled and grepped
  locally, and the HHS advisory PDF via Wayback + pdftotext.
- WebSearch budget for this session was already exhausted, so nothing below rests on a search snippet.

---

## Section 1 — Claim-by-claim table

### P1 — population

| # | Claim | Verdict | What I found | Corrected value | Source I checked |
|---|---|---|---|---|---|
| 1 | 33.562M families w/ own children <18 (2025) | **CONFIRMED** | FM-1 row `2025t`: 33,562 | — | fm1.xls |
| 2 | 72.734M children <18 (2025) | **CONFIRMED** | CH-1 row `2025z,t`: 72,734 | — | ch1.xls |
| 3 | 62.101M parents (derived) | **CONFIRMED (arithmetic)** | FG10: 24,040 + 1,871 married/unmarried parent couples ×2, + 8,242 mother-only + 2,037 father-only = 62,101 exactly. Caveat: **excludes married same-sex parent couples** (757 such couples in FG10, kids not broken out) and grandparent-headed groups (1,122). Lower bound, not a count. | — | fg10.xls |
| 4 | F1 age-of-householder distribution, total 33,289, mean 40.9 | **CONFIRMED** | Every cell matched: 919 / 2,712 / 5,529 / 6,885 / 6,863 / 5,194 / 3,045 / 1,733 / 410; mean 40.9 | — | tabf1-all.xls |
| 5 | **Gen Z 2.0M (6.0%) / Millennial 18.2M (54.5%) / Gen X 11.7M (35.1%)** | **CONFIRMED as arithmetic — REFUTED as a 2026 statement** | I recomputed independently from F1 and got 2,003.8K (6.02%) / 18,159K (54.55%) / 11,677K (35.08%) / Boomer+ 1,450K (4.36%), summing to 33,290. The 40/60/40 band splits are the *correct* splits for **householder ages in March 2023** (Gen Z = age ≤26 then). **But the report then uses "6%" as the 2026 targeting fact.** In 2026 the whole 25–29 band is Gen Z, so the same table implies **~3.63M / ~10.9%** — the headline understates the 2026 Gen Z base by roughly half. Second-order caveat: within-band uniformity is false (householder rates rise steeply with age), so even the 2023 Gen Z share is a soft upper estimate. | Gen Z ≈ **2.0M / 6.0% as of 2023**; ≈ **3.6M / ~11% on a 2026 cohort frame** | tabf1-all.xls, recomputed |
| 6 | 3.7M / 33.9M / 21.8M Gen Z / Mill / Gen X parents | **PLAUSIBLE — do not quote as a count** | Arithmetic checks (62.101 × the #5 shares). But it stacks the #5 vintage error on top of an assumption (equal coupling by cohort) the report itself says is false — and false in the direction that inflates Gen Z. Two derivations deep from any published number. | — | derived |
| 7 | 1.94 own children per family (1.99 / 1.65 / 1.88) | **CONFIRMED** | FM-3 row 2023 exactly | — | fm3.xls |
| 8 | 43.2% one / 36.3% two / 20.5% three+ | **CONFIRMED as worded; MISUSED in Interpretation §5** | F1: 15,751 / 13,213 / 7,478 of 36,443 ✓. But that panel is "**number of family MEMBERS under 18**" (36,443 households), not own children (33,289) — a 3.15M / 9.5% different universe that includes under-18 siblings, grandchildren, etc. Interpretation §5 restates it as "43.2% of parent households have exactly one child under 18." | Keep the finding's wording; fix §5 | tabf1-all.xls |
| 9 | Avg own children by parent age 1.39→2.19→1.62 | **CONFIRMED** | AVG3 "AGE OF HOUSEHOLDER" panel matched every value; SEs 0.02–0.04 ✓ | — | tabavg3.xls |
| 10–13 | Kid-age composition by householder age (under 6 / 12–17 / 6–11 / under 3) | **CONFIRMED** | I recomputed all 27 ratios from F1 rows 26/36/34/30 over row 22. Every one matched to the stated decimal. | — | tabf1-all.xls |
| 14 | 22.33M / 24.16M / 25.81M children by age | **CONFIRMED** | C2 TOTAL row: 22,326 / 24,156 / 25,814 of 72,296 ✓ | — | tabc2-all.xls |
| 15 | 69.5% married / 22.8% mother-only / 7.7% father-only | **CONFIRMED** | FM-1 2025: 23,323 / 7,666 / 2,574 of 33,562 ✓ | — | fm1.xls |
| 16 | 1.871M cohabiting parent couples, 2.1% of family groups | **CONFIRMED** | FG10: 1,871; percent panel says 2.1 ✓ | — | fg10.xls |
| 17 | 70.4% two parents / 25.6% one / 4.0% neither | **CONFIRMED** | CH-1 2025: 51,202 / 18,647 / (2,323+562) of 72,734 ✓ | — | ch1.xls |
| 18 | 18.2% → 22.2% mother-only by child age | **CONFIRMED** | C2: 4,055/22,326 = 18.16%; 2,933/13,202 = 22.22% ✓ | — | tabc2-all.xls |
| 19 | 66.3% both employed; 91.6% at least one | **CONFIRMED** | famee release text verbatim. Independently triangulated: Census FG1 gives 16,025/24,040 = 66.7%. **Missing caveat — see below.** | — | famee.nr0.htm (Wayback 2026-08-19) |
| 20 | LFPR 73.9% mothers / 93.7% fathers | **CONFIRMED** | famee release text verbatim (the TED URL P1 cites was not reachable, but the substance is in the release). **Missing caveat.** | — | same |
| 21 | 68.0% under 6 / 78.2% 6–17 maternal LFPR | **CONFIRMED** | famee release text verbatim ✓ | — | same |
| 22 | 65.3% vs 69.4% both-in-LF by kid age | **CONFIRMED** | FG1: 6,823/10,449 = 65.30%; and the "own children 6–17" row = 12,874/18,543 = 69.43% ✓. Note "with own children 6–17" is not "youngest 6–17" — it includes couples who also have an under-6. | — | tabfg1-all.xls |
| 23 | **52.7% of families with a child <18 at $100K+ (19,390 of 36,820)** | **CONFIRMED** | I summed the 21 income bands from $100,000–104,999 through "$200,000 and over" in the "one or more related children" column: **19,390 exactly**. 19,390/36,820 = 52.66%. Universe is primary families with **related** children — correctly disclosed in the Method column. | — | finc03_1_1.xlsx |
| 24 | 34.8% $150K+, 22.3% $200K+, median $105,400 (SE 1,036), mean $146,700 | **CONFIRMED** | 12,818/36,820 = 34.81%; 8,202/36,820 = 22.28%; median/SE/mean rows matched | — | same |
| 25 | $35,960 vs $58,360 per family member, 38% gap | **CONFIRMED** | FINC-03 "Income per family member" row ✓; gap 38.4% | — | same |
| 26 | Suburban 38.9% / city 29.7% / rural 20.3% / town 10.8% | **CONFIRMED** | Fall **2022** panel: 19,179.3 (38.897%) / 14,656.1 (29.724%) / 9,994.1 (20.269%) / 5,306.3 (10.761%). Year label correct. Caveat stands: NCES locale is the **school's** locale, not the family's residence. | — | tabn214.40.xlsx |
| 27 | 3,628,934 births, distributed by maternal age | **CONFIRMED** | NVSR 75-02 Table 3 total row matched every one of the nine cells (1,727 / 137,273 / 611,800 / 990,817 / 1,112,409 / 622,517 / 141,515 / 9,688 / 1,188) | — | nvsr75-02.pdf |
| 28 | 48.0% of births to mothers <30; ~37% to Gen Z mothers | **CONFIRMED (arithmetic)** | 1,741,617/3,628,934 = 47.99%; the ~37% follows from a stated uniform split of the 25–29 band. Births rise with age inside that band, so ~37% is a mild overstatement. | — | derived from Table 3 |
| 29 | Mean age at first birth 27.6 (from 27.5); 1,427,020 first births | **CONFIRMED** | Both verbatim in NVSR 75-02 (Table 3 "1st child" row = 1,427,020) | — | nvsr75-02.pdf |
| 30 | Record lows 20–24 (55.8, −3%) and 25–29 (89.5, −2%); 30–34 (93.7) above 25–29 since 2016 | **CONFIRMED** | All three rates verbatim; "record low" language verbatim; the 2016 rate table shows 30–34 (99.2) > 25–29 (98.4), consistent with the "since 2016" claim | — | nvsr75-02.pdf |
| 31 | Families with own children <18: 54% (1975) → 39% (2025) | **CONFIRMED (twice)** | Census press release states it; and FM-1 gives 33,562/85,963 = 39.04% independently | — | census.gov CB25 release + fm1.xls |
| 32 | **"Only 11.0% of children live in a household with no parent in the labor force"** | **REFUTED** | The four C3 components the report itself names — 3,450 + 362 + 1,387 + 3,073 = **8,272** — over 72,296 is **11.44%**, not 11.0%. I verified the five labor-force rows are mutually exclusive (they sum to 72,294 ≈ the 72,296 total). The corollary "~89% of kids have at least one working parent" should be ~88.6%. | **11.4%** (and ~88.6%) | tabc3-all.xls |

### P2 — who plans

| # | Claim | Verdict | What I found | Corrected value | Source I checked |
|---|---|---|---|---|---|
| 1 | HH management 0.15 / 0.10 / 0.20 h (9.0 / 6.0 / 12.0 min), 2.0x | **CONFIRMED** | ATUS Table 8A 2025 exactly. But 2.0x is over-precise: BLS rounds to hundredths, so the true ratio sits anywhere in **1.86x–2.16x**. | present as "about 2x" | atus.t08A (Wayback 2026-08-19) |
| 2 | 3.0x for youngest 6–17: 16.2 vs 5.4 min | **CONFIRMED as a number — NOT ROBUST as the decision input** | 8A youngest 6–17 = 0.18/0.09/**0.27** ✓. **But Table 8B (employed parents), which the report also cites, gives youngest 6–17 = 0.11/0.08/0.14 — a 1.75x gap and 8.4 vs 4.8 min.** The 3.0x/16.2-min figure is driven by non-employed mothers (8C: 0.51 h). The product sells to dual-earner households; for them the school-age gap is ~1.75x, not 3.0x. | for employed parents: **8.4 vs 4.8 min, 1.75x** | atus.t08A / t08B / t08C |
| 3 | "**The ONE category with no female skew**" for parents of a child <6 (fathers 6.6 vs mothers 5.4 min) | **Number CONFIRMED — structural claim REFUTED** | 2025 8A: 0.10/0.11/0.09 ✓. But I pulled the same cell from the archived releases the report itself uses for its trend line: **2015 = 0.11/0.10/0.13 and 2019 = 0.12/0.09/0.15 — mothers ahead in both years.** The "parity" is a single-wave reversal in a small cell, not a feature of how under-6 households work. Interpretation §4 ("under-6 parenting is physical and shared") rests on it. | one-year artifact; do not state structurally | atus.t08A 2015 / 2019 / 2025 |
| 4 | Employed 7.2 vs 5.4 min (1.33x); not-employed 20.4 vs 6.6 (3.1x) | **CONFIRMED** | 8B = 0.11/0.09/0.12; 8C = 0.28/0.11/0.34 ✓. Rounding envelope on 1.33x is 1.21–1.47. **This finding contradicts the report's own headline and is not carried into Interpretation §1.** | — | atus.t08B / t08C |
| 5 | Childcare 1.52 vs 0.84 h, 1.81x | **CONFIRMED** | 8A 2025 exactly | — | atus.t08A |
| 6 | Childcare ratio 2.14 → 1.94 → 1.81 | **CONFIRMED** | 2015 = 1.17/0.72/1.54; 2019 = 1.16/0.77/1.49; 2025 = 1.20/0.84/1.52. All exact. | — | 3 releases |
| 7 | **HH-management ratio widened 1.40x (2015) → 1.67x (2019) → 2.00x (2025)** | **Numbers CONFIRMED — inference REFUTED** | The point estimates are real and exact (0.14/0.10 → 0.15/0.09 → 0.20/0.10). The inference does not survive: **(a)** it rests on a 3.6-min/day move in one female cell while the male series is flat at rounding resolution; **(b)** no standard errors, no significance test — BLS publishes SEs separately and P2 used none, and household management is a low-incidence activity in a **~6,100-person** annual sample (confirmed in the ATUS Technical Note), so the parent subgroup is small and the by-sex-by-kid-age cells smaller still; **(c)** 2025 is not methodologically comparable to 2015/2019 — the shutdown removed Sept 30–Nov 11 diaries and Q4 was reweighted, and BLS states flatly "it is not possible to quantify the effect"; **(d)** the ATUS code bundles financial management **and mail/e-mail** with organizing, so a decade of e-mail migration is an unexcluded rival explanation; **(e)** the same three waves show the by-kid-age structure inverting entirely (see #3), which is the signature of noise rather than a trend. | present as "no evidence of convergence in household management," never "the gap widened to 2.0x" | atus.t08A ×3, atus.nr0, atus.tn |
| 8 | Secondary childcare 5.08 / 4.27 / 5.74 h | **CONFIRMED** | Table 10, "Children under age 13, total" row exactly | — | atus.t10 |
| 9–17 | Pew 2026 division-of-labor battery (52/10/39; 43/17/40; 63 vs 41 and 63 vs 25; 25% vs 8%; 39/19 and 38/22; 48/22/29 and 68 vs 29; 70% vs 16%; 22% vs 65% and 11% vs 54%; 55/36 and 49/26) | **CONFIRMED — every one** | I pulled the 57-page report PDF and read the chart data series directly. Parenting: all 52/10/39, fathers 41/13/47, mothers 63/7/30. Chores: all 43/17/40, fathers 25/25/50, mothers 63/8/29. Satisfaction 65 vs 22 and 54 vs 11 verbatim. The two different "25%"s in #11 and #12 are genuinely different quantities — I checked, it is not an internal contradiction. | — | ST_2026.6.16 PDF |
| 9 | *method note*: "division-of-labor items base n=2,422" | **REFUTED** | There is no 2,422 base. Pew's methodology states 2,242 respondents out of 2,843 sampled, MOE ±2.6. "2,422" appears twice in Pew's own boilerplate and is a transposition typo — a base larger than the total sample is impossible. | drop it; n = **2,242** | ST_2026.6.16 PDF |
| 18–20 | Ciciolla & Luthar item-level "mostly me" percentages | **CONFIRMED** | 88% schedules, 70% captain, 74% assigning, 76% routine/order, 78% teachers, 64% emotions; financial items 10–18% (10/12/15/15/18). n=393, word-of-mouth/flyers/media/lectures, **2005–2010**, ~50% graduate degrees — all as P2 states. **On whether it can carry weight in 2026: as a descriptive ranking of which tasks a mother owns, yes — it is the only item-level instrument available and P2 labels its limits accurately. As a level estimate ("88% of mothers"), no** — a convenience sample of mostly graduate-degreed mothers whose diaries predate the smartphone cannot generate a population percentage, and the number should never appear as "88% of US mothers." | say "in this sample of 393 mostly graduate-degreed mothers, 88%…" | PMC8223758 |
| 21 | Daminger four-part model; "**only two of the four are gendered**"; deciding "roughly equal" | **"Roughly equal" CONFIRMED verbatim — "two of four" REFUTED** | The ASR abstract reads: *"cognitive labor entails anticipating needs, identifying options for filling them, making decisions, and monitoring progress… women in this study do more cognitive labor overall and more of the anticipation and monitoring work in particular. However, male and female participation in decision-making… is roughly equal."* 70 interviews / 35 couples ✓. **The paper exempts only decision-making.** It says women do more cognitive labor *overall*, which implies **identification is also female-skewed**. So it is 1 of 4 that is equal, not 2 of 4. This matters directly: Interpretation §2 argues the Planner's **discovery** (= identifying options) sits in "the shared middle." Daminger does not support that. | "three of four components are female-skewed; only deciding is roughly equal" | journals.sagepub.com (Wayback) |
| 22 | **"Women lead on 8 of 12 tasks"**; family activity planning is shared | **Half REFUTED, half CONFIRMED** | In dual-full-time households Gallup shows women leading on **6** — laundry 52/14, cleaning 49/10, groceries 49/14, meals 45/19, childcare 42/6, dishes 38/23 — men leading 2, and 4 shared. "**Family activity planning**" **is** item 12 of the battery and **is** named as shared alongside savings/investment decisions ✓. Method (n=3,062; dual-FT-with-kids n=566; ±5; June–Aug 2019; pub. 2020-03-05) all ✓. | **6 of 12** | news.gallup.com/poll/286739 |
| 23 | Gallup childcare 42 / 6 / 50 | **CONFIRMED** | exact | — | same |
| 24 | 52% dual-FT (2025), 31% (1975), dad-only 42% → 23% | **Mostly CONFIRMED; one clause UNVERIFIABLE** | The cited Pew page gives 52% / 31% / 42% / 23% with 1975 as the earliest year ✓. **"up from 46% in 2015" is not on the cited page** — that chart runs 1975→2025 with no 2015 point. It is a real Pew figure from a different (2015) report, but it is not sourced by the URL given. | cite the 2015 figure separately or drop it | pewresearch.org …changed-over-time |
| 25 | 73% of parents work FT; 89% dads / 59% moms | **CONFIRMED** | Pew analysis of Census data, 2025, verbatim | — | pewresearch.org …blurred |
| 26 | 18.647M children with one parent; 15.31M / 3.34M; 17.9% father | **CONFIRMED** | CH-1 2025 exactly; 3,340/18,647 = 17.9% ✓ | — | ch1.xls |
| 27 | "**10.28M one-parent families … out of 36.36M families with children**" | **REFUTED (universe)** | FM-2 does say 10,280 / 8,242 / 2,037 / 36,356 for 2023 — but **FM-2 is a FAMILY GROUPS table** ("All Parent/Child Situations… Family groups with children"), which counts subfamilies separately. Calling them "families" is exactly the error P1's own §7 warns about. The **family** figures for the same year are FM-1: 9,767 one-parent of 33,290 (29.3%); for 2025, 10,239 of 33,562 (30.5%). P2 and P1 therefore disagree by ~0.5M families and ~3M denominators, and neither reconciles it. | "10.28M one-parent **family groups** (2023)", or use FM-1 2025: **10.24M of 33.56M** | fm2.xls, fm1.xls |
| 28 | 60% unpartnered vs 51% partnered say balancing is difficult | **CONFIRMED** | Pew detailed table: Married/partnered 51, Not married 60 ✓ | — | ST_2026.6.16 PDF |
| 29 | 56% → 54% → 47% by age of youngest child | **CONFIRMED** | Pew detailed table: 0–5 = 56, 6–12 = 54, 13–17 = 47 ✓ | — | same |
| 30 | 33% vs 20% stress; 41%; 48% vs 26% | **CONFIRMED** | HHS advisory verbatim; and P2's instruction to cite the APA origin rather than HHS is correct — the advisory footnotes them to refs 15/16, not to a federal instrument | — | parents-under-pressure.pdf |
| 31 | 77% single-parent loneliness vs 65% / 55% | **CONFIRMED as quoted** | Advisory verbatim ("In a 2021 survey, approximately 65% of parents and guardians, and 77% of single parents in particular, experienced loneliness, compared to 55% of non-parents"). Vendor origin (Cigna), no n or fielding window in the advisory — P2's Tier C label is right. | — | same |
| 32 | Fathers 2.6 → 6.6 h/wk (+154%); mothers 8.4 → 11.8 (+40%) | **CONFIRMED** | Advisory verbatim. Note for the synthesist: this series is **not** commensurable with the ATUS 2025 figures used elsewhere in P2 (0.84 h/day = 5.9 h/wk for fathers, 1.52 = 10.6 for mothers). Do not put them in one chart. | — | same |
| 33 | ΔR² = .02 / .04 / .02; role-overload model not significant | **CONFIRMED** | Exactly as reported; P2's §8 restraint about the consequence literature is warranted and correct | — | PMC8223758 |
| 34 | 25–34 ratio 2.98 → 2.77 → 2.36; 35–44 frozen 2.05 → 2.01 | **Numbers CONFIRMED — "narrowed materially" REFUTED as a generational claim** | Table 3 values all exact (2025: W 1.11 / M 0.47; W 1.63 / M 0.81; and the 20–24 male cell is indeed suppressed). **But the mechanism is compositional, and P2's own numbers show it: among 25–34s, men's hours FELL 0.53 → 0.47 alongside women's 1.58 → 1.11.** The ratio narrowed because fewer 25–34-year-olds are parents at all, not because young couples share more. Both sexes did less caring. Reading it as evidence that younger cohorts are more equal inverts the finding. | "the 25–34 ratio fell, but so did both sexes' hours — this is delayed fertility, not convergence" | atus.t03 2015/2019/2025 |
| 35 | 1.88 / 1.53 / 1.48 / 1.65 household-activities gap by age | **CONFIRMED** | Table 3 2025: 1.79/0.95, 1.91/1.25, 2.36/1.59, 2.71/1.64 → 1.884, 1.528, 1.484, 1.652 ✓ | — | atus.t03 |
| 36 | Married 1.63x vs other marital statuses 2.27x | **CONFIRMED** | 0.91/0.56 and 0.34/0.15 ✓ | — | atus.t03 |
| 37 | Same-sex parents allocate by schedule/preference; biweekly planning meeting | **CONFIRMED** | 30 interviews, 15 men / 15 women, Nov 4–25 2024, PSB Insights, Pew states findings "are not statistically representative" ✓. The quote is verbatim: *"we schedule every two weeks a meeting to talk about, 'How did the last two weeks go?'"* | — | pewresearch.org 2025/06/12 |
| 38 | Pew could not analyze same-sex couples quantitatively | **CONFIRMED** | Stated in both reports; the 2026 PDF says "there aren't enough same-sex couples in the sample to analyze separately" | — | both |

---

## Section 2 — Cross-cutting problems neither report flags

**1. Both reports' 2025 BLS figures sit on a broken collection year, and only P2 says so.**
The federal shutdown hit *both* surveys. ATUS: no diaries Sept 30 – Nov 11, Q4 reweighted, BLS says
the effect cannot be quantified (P2 flags this; good). **CPS: October 2025 was not collected at all,
and the famee release states in a boxed notice that "2025 annual estimates are not strictly
comparable with annual averages for other years."** P1 findings #19, #20 and #21 carry no such
caveat. P1's CPS **ASEC** figures (March fielding) are unaffected — that distinction should be made
explicitly rather than left to the reader.

**2. There is a fifth "families with children" universe, and it is in P1's own cited release.**
The BLS famee text says "In 2025, 32.9 million families … included children under age 18." P1's
§7 catalogues four universes spanning ~3.3M and recommends 33.6M. Add 32.9M (CPS monthly,
11-month average) to that list, or the spread is understated.

**3. P2's employed/not-employed split quietly undercuts P2's own thesis.**
Household-management gap: all parents 2.0x; **employed parents 1.33x**; employed parents with a
school-age youngest **1.75x**; not-employed parents 3.1x. The report's framing ("the buyer is a
mother… 2.0x on household management") is drawn from the total, which is levered by non-employed
mothers. For dual-full-time households — the segment the product actually addresses, and the one
Pew shows is now the majority — the time-diary gap is roughly a third as large as the headline.
The gender argument for the product should rest on the Pew perception and satisfaction data
(which is strong, probability-sampled and fully confirmed), not on the ATUS management minutes.

**4. The two reports disagree with each other on single-parent counts and neither notices.**
P1 #15: 10.24M one-parent **families** (FM-1, 2025). P2 #27: 10.28M one-parent "families"
(actually FM-2 family **groups**, 2023). P1's own interpretation §6 then uses "10.2M"; P2's §6 uses
"10.28M". Pick FM-1 2025 and one label.

**5. Provenance.** P1 is candid that bls.gov 403s and says it used indexed text; every number it
recovered that way checked out. P2 asserts it fetched the ATUS tables "directly from bls.gov,"
which is not possible from this environment — though every figure it reports is nonetheless exact,
including obscure ones (5.08/4.27/5.74) and the 2015/2019 archives. The numbers are sound; the
sourcing sentence should be corrected rather than trusted as a description of method. **The
Wayback `id_` route works and should be the standard method for BLS in this project.**

---

## Section 3 — MUST NOT appear in the final report

Ordered by damage if published.

1. **"Gen Z parents are ~6% of the base" presented as a 2026 fact.** It is a 2023 householder-age
   snapshot. On the brief's own 2026 cohort bands the same Census table gives ~11%. Publishing 6%
   as current would understate the cohort by roughly half and it is the foundation of P1's entire
   "Gen Z is a research population, not a targeting population" recommendation. **Either relabel as
   2023 and state the 2026 figure alongside, or drop the cohort framing.**
2. **"The household-management gap widened from 1.40x to 2.00x while childcare converged."**
   The numbers are real; the inference is not defensible. Untested, un-SE'd, ~6,100-person survey,
   5–12-minute cells, a discontinuous 2025 collection year, an activity code that bundles e-mail,
   and a by-kid-age structure that inverts between waves. This is P2's most quotable line and its
   least survivable one.
3. **"Among parents of a child under 6, household management has no female skew."** Contradicted by
   the 2015 and 2019 waves of the identical table (0.13 vs 0.10; 0.15 vs 0.09). Do not build the
   "under-6 parenting is shared" segmentation on it.
4. **"Women lead on 8 of 12 Gallup tasks."** It is 6 of 12 in dual-full-time households. Correct
   the count; the "family activity planning is shared" half is solid and can stay.
5. **"Only two of Daminger's four components are gendered" / "discovery is the shared middle."**
   The paper exempts decision-making only, and states women do more cognitive labor overall.
   Identifying options — which is what the Planner's discovery agent does — is not established as
   equal. Rewrite to "only *deciding* is roughly equal."
6. **"88% of mothers own scheduling"** stated as a population figure. Convenience sample, n=393,
   fielded 2005–2010, ~50% graduate degrees. Usable only with the sample described in the sentence.
7. **"10.28M one-parent families out of 36.36M families with children."** Family *groups*, 2023.
   Replace with FM-1 2025: 10.24M of 33.56M (30.5%).
8. **"11.0% of children have no parent in the labor force."** Arithmetic error; it is 11.4%.
9. **"n=2,422 for the Pew division-of-labor items."** No such base; Pew typo for 2,242.
10. **"52% dual-full-time, up from 46% in 2015"** with the 2026 Pew URL attached. The 2015 point is
    not on that page.
11. **"3.7M Gen Z / 33.9M Millennial / 21.8M Gen X parents"** as a headcount. Two derivations deep,
    on an assumption the author says is false. Household counts only.
12. **"43.2% of parent households have exactly one child under 18"** (P1 Interpretation §5). Wrong
    universe — that is the distribution of household *members* under 18 across 36.4M households.

## Section 4 — corrections to apply, not delete

- P1 #32: 11.0% → **11.4%**; "~89% of kids" → **~88.6%**.
- P1 #19/#20/#21: add the CPS notice — *2025 annual averages are 11-month averages excluding
  October and are not strictly comparable with other years.*
- P1 #3: note it excludes married same-sex parent couples and grandparent-headed groups; it is a
  lower bound.
- P1 §7: add BLS's 32.9M as a fifth universe.
- P1 §2: "roughly half of Gen Z-headed households have a child under 3" is actually **~64%** on
  P1's own numbers — the point is stronger than stated.
- P2 #1: "2.0x" → "about 2x" (rounding envelope 1.86–2.16).
- P2 #2: add the employed-parent figures (8.4 vs 4.8 min, 1.75x) beside the 16.2 vs 5.4.
- P2 #21 method: Daminger's interviews predate 2020 and should carry the brief's "dated" flag,
  as Ciciolla and Gallup already do.
- P2 header: correct the "fetched directly from bls.gov" sentence.
- P2 #32: do not chart the 1985–2022 h/week series against the ATUS 2025 h/day series.

## What held up

Not the subject of this memo, but worth recording so the corrections above are read in proportion:
**of ~70 numeric claims across the two reports, I reached a primary source for all but a handful,
and the overwhelming majority matched digit-for-digit** — including every Census table cell, the
full ATUS 2025/2019/2015 trend grid, every Pew 2026 percentage, the NCHS birth distribution
(all nine cells), the NCES Fall 2022 locale panel, the Ciciolla item battery, and the Daminger
abstract. P1's A-derived rows reproduce exactly when recomputed independently. The failures above
are concentrated in *characterization* — vintage labels, universe labels, count-of-tasks, and
inferences drawn past what small ATUS cells can carry — not in fabrication.
