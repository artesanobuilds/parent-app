# P2 — WHO PLANS: the distribution of household planning labor (US)

Collector P2. Compiled 2026-08-21. US only. All ATUS tables fetched directly from bls.gov
(the June 25, 2026 release of 2025 annual averages, USDL-26-1022) and from the archived
2020 and 2016 releases for the trend line.

---

## Section 1: FINDINGS

### Table A — the findings

| # | Claim (one sentence, with the number) | Value | Cohort/segment | Publisher | Year | Method (n, fielding window, population) | Tier | URL |
|---|---|---|---|---|---|---|---|---|
| 1 | US adults living with a child under 18 spend 9.0 min/day on "household management" (the ATUS code for organizing/planning, financial management, mail and email); mothers spend 12.0 min vs fathers 6.0 min — a 2.0x gap. | 0.20 h vs 0.10 h/day | Parents, both sexes, US | BLS, ATUS Table 8A | 2025 (rel. 2026-06-25) | ~6,100 individuals interviewed in 2025; one 24-hour time diary per person, continuous fielding, civilian pop. 18+; ATUS ops suspended Oct 1–Nov 12 2025 (shutdown), Q4 reweighted | A | https://www.bls.gov/news.release/atus.t08A.htm |
| 2 | The household-management gap is 3.0x among parents whose youngest child is 6–17 — the school-age years, exactly where kid logistics live: 16.2 min/day for mothers, 5.4 min for fathers. | 0.27 h vs 0.09 h/day | Parents, youngest child 6–17 | BLS, ATUS Table 8A | 2025 | as above | A | https://www.bls.gov/news.release/atus.t08A.htm |
| 3 | Among parents of a child under 6, household management is the ONE category with no female skew: fathers 6.6 min/day vs mothers 5.4 min/day. | 0.11 h vs 0.09 h/day | Parents, youngest child <6 | BLS, ATUS Table 8A | 2025 | as above; small cell — treat as "no measurable gap," not a male skew | A | https://www.bls.gov/news.release/atus.t08A.htm |
| 4 | Among EMPLOYED parents the household-management gap nearly closes (7.2 min women vs 5.4 min men, 1.33x); among NOT-employed parents it is 3.1x (20.4 vs 6.6 min). | 0.12 vs 0.09 h; 0.34 vs 0.11 h | Parents by employment status | BLS, ATUS Tables 8B, 8C | 2025 | as above | A | https://www.bls.gov/news.release/atus.t08B.htm |
| 5 | Parents' primary childcare: mothers 1.52 h/day vs fathers 0.84 h/day — 1.81x. | 91.2 vs 50.4 min/day | Parents of a child <18 | BLS, ATUS Table 8A | 2025 | as above | A | https://www.bls.gov/news.release/atus.t08A.htm |
| 6 | The parental childcare gender ratio has narrowed steadily: 2.14x (2015) → 1.94x (2019) → 1.81x (2025), driven by fathers rising (0.72 → 0.77 → 0.84 h/day) while mothers stayed flat (1.54 → 1.49 → 1.52). | ratio 2.14 → 1.81 | Parents of a child <18 | BLS, ATUS Table 8A (2015, 2019, 2025 releases) | 2015/2019/2025 | as above; 2015 and 2019 flagged as dated but used deliberately as trend anchors | A | https://www.bls.gov/news.release/archives/atus_06242016.htm ; https://www.bls.gov/news.release/archives/atus_06252020.htm |
| 7 | Household MANAGEMENT moved the other way: the mother/father ratio among parents widened from 1.40x (2015) to 1.67x (2019) to 2.00x (2025). Physical chores converged; the planning work did not. | 0.14/0.10 → 0.15/0.09 → 0.20/0.10 h/day | Parents of a child <18 | BLS, ATUS Table 8A (3 releases) | 2015/2019/2025 | as above; these are small cells (5–12 min/day), so treat the direction as suggestive, not precise | A | same as #6 |
| 8 | Secondary childcare (a child in your care while you do something else) totals 5.08 h/day for adults in households with a child under 13 — mothers 5.74 h, fathers 4.27 h. | 5.74 vs 4.27 h/day | Adults in HH with child <13 | BLS, ATUS Table 10 | 2025 | as above | A | https://www.bls.gov/news.release/atus.t10.htm |
| 9 | In US different-sex couples where BOTH parents work full time, 52% say the mom does more day-to-day parenting tasks, 10% say the dad does, 39% say equal. | 52 / 10 / 39 | Dual-full-time different-sex couples with kids <18 | Pew Research Center | 2026 | n=2,242 US working parents (division-of-labor items base n=2,422), fielded March 2–15 2026, American Trends Panel, weighted to CPS benchmarks | B | https://www.pewresearch.org/social-trends/2026/06/16/how-working-parents-divide-family-responsibilities/ |
| 10 | Household chores in the same households: 43% say mom does more, 17% say dad does more, 40% equal. | 43 / 17 / 40 | Dual-full-time different-sex couples | Pew Research Center | 2026 | as #9 | B | same as #9 |
| 11 | Mothers and fathers do not agree about their own household: 63% of moms say they do more day-to-day parenting vs 41% of dads who say their partner does; on chores it is 63% of moms vs 25% of dads. | 63 vs 41; 63 vs 25 | Dual-full-time different-sex couples | Pew Research Center | 2026 | as #9 | B | same as #9 |
| 12 | 25% of fathers in dual-full-time couples say THEY do more of the household chores; only 8% of mothers say their partner does. | 25% vs 8% | Fathers vs mothers, dual-FT | Pew Research Center | 2026 | as #9 | B | same as #9 |
| 13 | Even in families where the MOTHER works more hours than the father, 39% say the mom still does more parenting tasks vs 19% who say the dad does; chores 38% vs 22%. | 39/19 and 38/22 | Different-sex couples, mom works more | Pew Research Center | 2026 | as #9 | B | same as #9 |
| 14 | 48% of dual-full-time couples say the MOM is more likely to take unexpected time off for a sick child or a childcare breakdown; 22% say the dad; 29% say equally. Moms and dads disagree: 68% of moms say they would, only 29% of dads say their partner would. | 48 / 22 / 29 | Dual-full-time different-sex couples | Pew Research Center | 2026 | as #9 | B | same as #9 |
| 15 | The deciding factor for who covers a childcare emergency is schedule flexibility (70% call it a major factor), not skill (16% say "who does a better job caring for their children"). | 70% vs 16% | US working parents | Pew Research Center | 2026 | as #9 | B | same as #9 |
| 16 | Satisfaction collapses when the load is lopsided: only 22% of moms who say they do more parenting tasks are satisfied with the split (vs 65% of moms who split equally); on chores it is 11% vs 54%. | 22% / 11% | Mothers, dual-FT couples | Pew Research Center | 2026 | as #9 | B | same as #9 |
| 17 | Fathers are markedly more satisfied with the same arrangement: 55% of dads vs 36% of moms are satisfied with the parenting split; 49% vs 26% on chores. | 55/36 and 49/26 | Dual-FT couples | Pew Research Center | 2026 | as #9 | B | same as #9 |
| 18 | 88% of US married/partnered mothers say they alone ("mostly me") are responsible for "organizing schedules for the family"; 2% say mostly their partner; 10% say both equally. | 88 / 2 / 10 | Married/partnered US mothers, mostly upper-middle class | Ciciolla & Luthar, *Sex Roles* 81:467–486 | 2019 | n=393 US married/partnered mothers with a dependent child at home; online "Moms as People" survey fielded 2005–2010, convenience recruitment (word of mouth, flyers, media, lectures); ~50% held a graduate degree; DATED and non-representative | A (peer-reviewed) but non-probability sample | https://pmc.ncbi.nlm.nih.gov/articles/PMC8223758/ |
| 19 | On the other items in that scale: 70% of mothers say they are the "captain of the ship," 74% assign the tasks, 76% maintain routine/order, 78% know the children's teachers, 64% are the one vigilant of the children's emotions. | 64–78% "mostly me" | as #18 | Ciciolla & Luthar, *Sex Roles* | 2019 | as #18 | A / non-probability | same as #18 |
| 20 | The same mothers report household FINANCES as shared, not owned: only 10–18% say "mostly me" on the five financial-decision items (53–80% "both equally"). Ownership is concentrated in scheduling and routines, not in money. | 10–18% "mostly me" | as #18 | Ciciolla & Luthar, *Sex Roles* | 2019 | as #18 | A / non-probability | same as #18 |
| 21 | Cognitive labor decomposes into four components — anticipating needs, identifying options, deciding among them, monitoring results — and only two of the four are gendered: women do more ANTICIPATION and MONITORING, while participation in DECIDING is "roughly equal." | 4-part model; 2 of 4 gendered | Different-sex couples, US | Daminger, *American Sociological Review* 84(4):609–633 | 2019 | 70 in-depth interviews with members of 35 couples; qualitative, non-probability; author's later work draws on 170+ interviews incl. same-gender couples | A (peer-reviewed) | https://journals.sagepub.com/doi/10.1177/0003122419859007 |
| 22 | Gallup's 12-task division-of-labor battery finds women lead on 8 of 12 tasks in dual-full-time households — but "family activity planning" is explicitly one of the tasks couples SHARE, alongside savings/investment decisions. | shared, not mother-owned | Dual-full-time different-sex couples with kids <18 | Gallup | 2019 (pub. 2020-03-05) | combined telephone polls June 19–30, July 15–31, Aug 15–30 2019; n=3,062 heterosexual married/cohabiting adults; dual-FT-with-kids subgroup n=566, MOE ±5 pts; DATED | B | https://news.gallup.com/poll/286739/working-moms-little-reprieve-household-demands.aspx |
| 23 | In the same Gallup data, mothers in dual-full-time households lead on daily childcare 42% vs 6% for fathers, with 50% saying it is equal — the highest "equal" share of any task measured. | 42 / 6 / 50 | Dual-FT couples | Gallup | 2019 | as #22 | B | same as #22 |
| 24 | 52% of US different-sex couples with children under 18 are now dual-full-time — up from 46% in 2015 and 31% in 1975; the dad-works/mom-at-home household fell from 42% (1975) to 23% (2025). | 52% (2025) | Different-sex couples w/ kids <18 | Pew analysis of US Census CPS | 2025 data, pub. 2026 | Pew Research Center analysis of Current Population Survey | A/B | https://www.pewresearch.org/social-trends/2026/06/16/how-family-work-arrangements-have-changed-over-time/ |
| 25 | 73% of US parents with children under 18 work full time — 89% of dads and 59% of moms. | 73% / 89% / 59% | US parents | Pew analysis of US Census data | 2025 | Pew analysis of Census Bureau data | A/B | https://www.pewresearch.org/social-trends/2026/06/16/for-working-parents-the-boundary-between-work-and-family-is-often-blurred/ |
| 26 | 18.65 million US children under 18 live with one parent (25.6% of all 72.73 million) — 15.31M with mother only, 3.34M with father only. Single fathers are 17.9% of single-parent situations. | 18,647,000 children | US children <18 | US Census Bureau, CPS ASEC, Table CH-1 | 2025 | Current Population Survey Annual Social and Economic Supplement, March 2025 | A | https://www2.census.gov/programs-surveys/demo/tables/families/time-series/children/ch1.xls |
| 27 | There are 10.28 million US one-parent families with children under 18 (8.24M mother-only, 2.04M father-only) out of 36.36M families with children — 28% of all families with kids. | 10,280,000 families | US families w/ kids <18 | US Census Bureau, CPS ASEC, Table FM-2 | 2023 (latest published) | CPS ASEC; flagged as 2 years behind the CH-1 series | A | https://www2.census.gov/programs-surveys/demo/tables/families/time-series/families/fm2.xls |
| 28 | Working parents who are NOT married or living with a partner are the segment most likely to say balancing work and family is difficult: 60% vs 51% of partnered parents. | 60% vs 51% | Unpartnered vs partnered working parents | Pew Research Center | 2026 | as #9; appendix detailed tables | B | https://www.pewresearch.org/wp-content/uploads/sites/20/2026/06/ST_2026.6.16_working-parents_report.pdf |
| 29 | Difficulty peaks when the youngest child is 0–5 (56% say balancing is difficult) and falls to 47% when the youngest is 13–17 — but ATUS shows the PLANNING gap runs the opposite way, peaking at ages 6–17. | 56% → 54% → 47% | By age of youngest child | Pew Research Center | 2026 | as #28 | B | same as #28 |
| 30 | In 2023, 33% of US parents reported high stress in the past month vs 20% of other adults; 41% of parents say most days they are so stressed they cannot function (vs 20% of other adults) and 48% say their stress is completely overwhelming (vs 26%). | 33% vs 20% | US parents | US Surgeon General, "Parents Under Pressure" Advisory | 2024 | HHS advisory; the stress comparison traces to American Psychological Association surveys (APA 2023/2024), not to a government instrument — cite the APA origin, not the advisory, for the number itself | A (advisory) / underlying source B | https://www.hhs.gov/sites/default/files/parents-under-pressure.pdf |
| 31 | 77% of SINGLE parents reported loneliness vs 65% of parents overall and 55% of non-parents. | 77% vs 65% vs 55% | US single parents | Cigna, cited in Surgeon General's Advisory | 2021 survey, cited 2024 | Cigna "Loneliness Epidemic Persists" — vendor-published; the advisory does not restate n or fielding window | C (vendor) | https://newsroom.thecignagroup.com/loneliness-epidemic-persists-post-pandemic-look |
| 32 | Fathers' primary childcare rose 154% from 2.6 h/week (1985) to 6.6 h/week (2022); mothers' rose 40% from 8.4 to 11.8 h/week. Fathers are converging fast in absolute terms and still doing just over half as much. | +154% vs +40% | US parents | Surgeon General's Advisory, citing ATUS-based time-diary series | 2024 (data through 2022) | time-diary series (Allard/Bianchi/Stewart/Wight lineage) | A | https://www.hhs.gov/sites/default/files/parents-under-pressure.pdf |
| 33 | Feeling disproportionately responsible for household management explains only 1–4% of incremental variance in mothers' wellbeing after controlling for emotional and physical intimacy, and the parenting-role-overload model was NOT statistically significant. | ΔR² = .01–.04 | Married/partnered US mothers | Ciciolla & Luthar, *Sex Roles* | 2019 | as #18; hierarchical regression, Model 4 | A | same as #18 |
| 34 | The gender gap in caring for household members among 25–34-year-olds has narrowed materially: 2.98x (2015, W 1.58 h vs M 0.53 h) → 2.77x (2019) → 2.36x (2025, W 1.11 vs M 0.47). Among 35–44-year-olds it is essentially frozen: 2.05x → 2.04x → 2.01x. | 2.98x → 2.36x vs 2.05x → 2.01x | Age 25–34 (late-millennial/Gen-Z-adjacent) vs 35–44 (millennial/Gen X) | BLS, ATUS Table 3 (three releases) | 2015/2019/2025 | ATUS; NOTE these age bands are all adults, not parents only, so parenthood rates differ across bands and years — directional evidence, not a parent-only estimate | A | https://www.bls.gov/news.release/atus.t03.htm |
| 35 | Household-activities gap by age band in 2025 runs 1.88x at 20–24, 1.53x at 25–34, 1.48x at 35–44 and 1.65x at 45–54 — the gap is NOT monotonically smaller among younger adults. | 1.88 / 1.53 / 1.48 / 1.65 | All US adults by age | BLS, ATUS Table 3 | 2025 | as #34 | A | https://www.bls.gov/news.release/atus.t03.htm |
| 36 | Married adults show a 1.63x gender gap in caring for household members (W 0.91 h vs M 0.56 h); adults in "other marital statuses" show 2.27x (0.34 vs 0.15) — the relative gap is wider outside marriage even though absolute hours are lower. | 1.63x vs 2.27x | By marital status | BLS, ATUS Table 3 | 2025 | as #34; "other marital statuses" pools never-married, divorced, separated, widowed | A | https://www.bls.gov/news.release/atus.t03.htm |
| 37 | Same-sex parents describe allocating childcare and household work by WORK SCHEDULE and personal preference rather than by role — one couple runs a standing biweekly planning meeting to reallocate. | qualitative | Same-sex-couple parents, US | Pew Research Center | 2025 | 30 in-depth interviews (15 men, 15 women) raising children <18 with a same-sex spouse/partner, Nov 4–25 2024, conducted with PSB Insights; Pew states findings are NOT statistically representative | B (qualitative, non-representative) | https://www.pewresearch.org/social-trends/2025/06/12/same-sex-parents-raising-kids/ |
| 38 | Pew could not analyze same-sex couples quantitatively in either its 2026 working-parents survey or its 2025 LGBTQ survey because the samples were too small — there is no probability-sample US estimate of the planning split in same-sex-parent households. | no data | Same-sex-couple parents | Pew Research Center | 2025/2026 | stated explicitly in both reports | — (finding of absence) | https://www.pewresearch.org/social-trends/2026/06/16/how-working-parents-divide-family-responsibilities/ |

### Table B — ATUS 2025 detail, parents of a child under 18 (hours/day)

Table 8A/8B/8C, 2025 annual averages. Columns: Total / Men / Women.

| Activity | All parents | Employed parents | Not-employed parents |
|---|---|---|---|
| Household activities | 2.07 / 1.51 / 2.56 | 1.71 / 1.45 / 2.00 | 3.09 / 1.81 / 3.58 |
| — Housework | 0.60 / 0.29 / 0.88 | 0.47 / 0.27 / 0.70 | 0.97 / 0.36 / 1.20 |
| — Food prep & cleanup | 0.91 / 0.59 / 1.19 | 0.74 / 0.56 / 0.94 | 1.39 / 0.74 / 1.65 |
| — **Household management** | **0.15 / 0.10 / 0.20** | **0.11 / 0.09 / 0.12** | **0.28 / 0.11 / 0.34** |
| Purchasing goods & services | 0.67 / 0.50 / 0.82 | 0.58 / 0.52 / 0.64 | 0.93 / 0.39 / 1.14 |
| Caring for household children | 1.20 / 0.84 / 1.52 | 0.99 / 0.78 / 1.22 | 1.81 / 1.15 / 2.06 |
| Working & work-related | 4.15 / 4.97 / 3.42 | 5.55 / 5.82 / 5.25 | 0.13 / 0.33 / 0.06 |
| Leisure & sports | 3.90 / 4.29 / 3.56 | 3.53 / 3.80 / 3.21 | 4.97 / 6.95 / 4.22 |

By age of youngest child, all parents (Total / Men / Women):

| Activity | Youngest <6 | Youngest 6–17 |
|---|---|---|
| Household activities | 1.93 / 1.46 / 2.33 | 2.16 / 1.54 / 2.71 |
| **Household management** | **0.10 / 0.11 / 0.09** | **0.18 / 0.09 / 0.27** |
| Purchasing goods & services | 0.59 / 0.55 / 0.62 | 0.72 / 0.46 / 0.95 |
| Caring for household children | 2.08 / 1.53 / 2.56 | 0.61 / 0.38 / 0.81 |

### Table C — the trend line (ATUS Table 8A, parents of a child under 18, hours/day)

| Activity | 2015 T/M/W | 2019 T/M/W | 2025 T/M/W | W:M ratio 2015 → 2025 |
|---|---|---|---|---|
| Household activities | 1.91 / 1.29 / 2.41 | 1.85 / 1.28 / 2.33 | 2.07 / 1.51 / 2.56 | 1.87 → 1.70 |
| Household management | 0.12 / 0.10 / 0.14 | 0.12 / 0.09 / 0.15 | 0.15 / 0.10 / 0.20 | 1.40 → **2.00** |
| Purchasing goods & services | 0.73 / 0.58 / 0.85 | 0.72 / 0.60 / 0.83 | 0.67 / 0.50 / 0.82 | 1.47 → 1.64 |
| Caring for household children | 1.17 / 0.72 / 1.54 | 1.16 / 0.77 / 1.49 | 1.20 / 0.84 / 1.52 | 2.14 → **1.81** |

### Table D — the cohort question (ATUS Table 3, all adults by age band, hours/day)

Caring for and helping household members, women vs men:

| Age band | 2015 | 2019 | 2025 | Ratio 2015 → 2025 |
|---|---|---|---|---|
| 20–24 | 0.81 / 0.08 | 0.30 / 0.05 | 0.42 / suppressed | n/a (cells too small) |
| 25–34 | 1.58 / 0.53 (2.98x) | 1.47 / 0.53 (2.77x) | 1.11 / 0.47 (2.36x) | **2.98 → 2.36** |
| 35–44 | 1.56 / 0.76 (2.05x) | 1.53 / 0.75 (2.04x) | 1.63 / 0.81 (2.01x) | 2.05 → 2.01 |
| 45–54 | 0.43 / 0.32 (1.34x) | 0.47 / 0.38 (1.24x) | 0.57 / 0.45 (1.27x) | 1.34 → 1.27 |

Caveat that matters: these bands cover all adults, not parents only. Fewer 25–34-year-olds
are parents in 2025 than in 2015 (US fertility has shifted later), which depresses the
absolute hours in that band and could mechanically shrink the ratio. Read this as directional.

---

### Interpretation

**1. The buyer is a mother, and the product's specific job is her job more than the household
average suggests.** Every probability-sample source points the same way. In dual-full-time
different-sex couples — now the majority household type at 52% — 52% say the mother does more
day-to-day parenting and only 10% say the father does (Pew 2026, n=2,242). The ATUS 2025
diaries put mothers at 1.81x fathers on childcare and 2.0x on household management. And when
the mother works MORE hours than the father, she still does more parenting 39% to 19%. Work
hours do not explain the split, which means a product that saves planning time is aimed at
women regardless of the household's employment configuration.

**2. But the gap is not uniform across the four things "planning" actually means, and the part
our product does most is the least gendered part.** Daminger's four-component model is the
single most decision-relevant piece of theory here: cognitive labor is anticipate → identify →
decide → monitor, and her interviews find women do disproportionately more of the ANTICIPATING
and MONITORING while DECIDING is "roughly equal" between partners. Gallup's 12-task battery
independently lands in the same place: women lead on 8 of 12 tasks in dual-full-time
households, but "family activity planning" is named as one of the shared ones. Ciciolla &
Luthar's item-level data agrees a third time — 88% of mothers own "organizing schedules for the
family" but only 10–18% own the five financial-DECISION items. So: the noticing ("registration
opens Feb 3," "she has outgrown the cleats") and the tracking ("did we ever confirm the
carpool?") are hers. The choosing ("which camp") is genuinely joint. Our Planner does discovery
and decision support — the shared middle. Our watchlist, conflict detection, coverage-gap
detection and to-dos do anticipation and monitoring — the part that is hers alone. That is
where the acute pain is, and it is the part the product should lead with.

**3. The household-management trend contradicts the childcare trend, and the contradiction is
the opportunity.** Physical and hands-on labor is converging: fathers' childcare rose 0.72 →
0.84 h/day from 2015 to 2025 while mothers' stayed flat, narrowing the ratio from 2.14x to
1.81x; over the longer 1985–2022 series fathers' primary childcare rose 154%. Household
management went the other way — the ratio widened from 1.40x to 2.00x, with mothers' minutes
rising 8.4 → 12.0 per day while fathers stayed at 6. Men picked up the visible work and did not
pick up the invisible work. This is exactly Daminger's argument showing up in a federal time
diary. Caveat honestly: these are 5–12 minute cells and ATUS's "household management" code
bundles financial management and mail/email with organizing, so I would present the direction
and not the decimal.

**4. The load peaks at school age, not at infancy — and the product should follow.** For parents
of a child under 6, ATUS shows household management at parity (6.6 min for fathers, 5.4 for
mothers). For parents whose youngest is 6–17 it is 5.4 vs 16.2 minutes, a 3.0x gap, while
hands-on childcare collapses from 2.08 to 0.61 h/day. Under-6 parenting is physical and shared;
school-age parenting is administrative and mother-owned. That is precisely the camp /
extracurricular / school-event / trip surface area. It also means the Pew "difficulty" curve
(56% for youngest 0–5 falling to 47% at 13–17) measures a different thing than we sell against
— overall work-family strain falls with kid age while planning load rises with it.

**5. Fathers are a real but small primary-buyer segment, and their self-perception is the
obstacle.** In dual-full-time couples, 10% say the dad does more parenting tasks and 17% say he
does more chores; 13% of dads claim the parenting lead and 25% claim the chore lead, against
only 7–8% of mothers who concede it. Call it roughly one household in ten where the father is
genuinely the logistics parent, plus a much larger group of fathers who believe things are even
when their partner does not (47% of dads vs 30% of moms say parenting is split equally; 50% vs
29% on chores). Fathers also report far more satisfaction with the identical arrangement — 55%
vs 36% on parenting, 49% vs 26% on chores. Product implication: a father is unlikely to buy a
tool framed as relief from an unfair load, because he does not perceive one. He is reachable
through the 2.04M single-father families and the 3.34M children living with father only, where
there is no partner to misperceive. He is also reachable through the emergency-coverage frame:
70% of parents say whoever has more work flexibility takes the sick day, and only 16% say it
goes to whoever is better with the kids — that is a scheduling problem, not a gender problem,
and it is gender-neutral marketing copy.

**6. Single parents are the highest-intensity segment and the clearest "no partner to split
with" story — 10.28M families, 18.65M children.** Unpartnered working parents are the segment
most likely to call work-family balance difficult (60% vs 51%). The Surgeon General's advisory
cites 77% of single parents reporting loneliness vs 65% of parents overall. What I could NOT
find is a probability-sample measure of planning HOURS for single vs partnered parents — ATUS's
marital-status table (Table 3) is not restricted to parents, and its "other marital statuses"
cell mixes never-married 20-somethings with divorced 50-somethings, so the 2.27x gap there is
not usable as a single-parent statistic. I also found no citable US estimate of 50/50 joint
physical custody prevalence; the Census custodial-parent series and the Wisconsin court-record
studies are the right places to look, and neither was retrievable in this pass. Both go in WEAK
SIGNAL.

**7. On generation, the honest answer is: the gap is narrowing, slowly, and nobody has measured
Gen Z parents specifically.** The best Tier A evidence is ATUS Table 3: the female/male ratio on
caring for household members among 25–34-year-olds fell from 2.98x (2015) to 2.77x (2019) to
2.36x (2025), while the 35–44 band barely moved (2.05x → 2.01x). Younger cohorts are more equal
than the same age band was a decade ago, and more equal than older cohorts are today. But the
household-activities gap does NOT decline monotonically with youth (1.88x at 20–24, 1.53x at
25–34, 1.48x at 35–44, 1.65x at 45–54), and the age bands include non-parents, so I would not
claim more than "directionally narrowing, magnitude uncertain." Pew has published no
division-of-labor breakout by parent age or generation; its 2026 working-parents report weights
on age but reports no age crosstab for the who-does-more items. There is no US survey that
reports the planning split for Gen Z parents (18–29) as a distinct group. That is a genuine gap
and, per the brief, the expected answer.

**8. The consequence literature is weaker than the popular narrative claims, and we should not
overclaim it.** Ciciolla & Luthar is the paper everyone cites for "the mental load hurts
mothers," and it does find significant negative correlations with life satisfaction, partner
satisfaction and emptiness. But after controlling for emotional and physical intimacy, the
household-management block adds only 2% of variance in life satisfaction, 4% in partner
satisfaction and 2% in emptiness — and the parenting-role-overload model was not statistically
significant at all, which is the one outcome the "mental load causes burnout" story most needs.
The sample is 393 mostly graduate-degreed mothers recruited by word of mouth and fielded
2005–2010; it is a strong descriptive source for WHO owns which task and a weak causal source
for WHAT it does to them. Marketing copy should lean on the ownership distribution (88%) and on
Pew's satisfaction cliff (22% of moms who do more are satisfied with the split; 11% on chores),
both of which are defensible, rather than on burnout causation.

**9. Same-sex-couple parents are the natural experiment we cannot yet run.** Pew explicitly
could not analyze same-sex couples quantitatively in either its 2026 working-parents survey or
its 2025 LGBTQ survey — both samples were too small. Its 30 qualitative interviews report that
these couples allocate by work schedule and personal preference, with one couple describing a
standing biweekly planning meeting. Daminger's own book-length project draws on 170+ interviews
including same-gender couples and reports that women in DIFFERENT-gender couples do more
cognitive labor, implying the effect is about gender pairing rather than about individuals —
but I did not obtain a quantitative same-sex estimate. Treat "planning is allocated by
flexibility and preference when gender defaults are absent" as a well-supported qualitative
finding and nothing more.

---

## Section 2: WEAK SIGNAL

Not sourceable to Tier A/B/C in this pass. Do not use in any deliverable without further work.

1. **50/50 joint physical custody prevalence in the US.** No citable national estimate obtained.
   The right sources are the Census Bureau's "Custodial Mothers and Fathers and Their Child
   Support" series and the Wisconsin Court Record Data shared-placement studies (Institute for
   Research on Poverty). Neither was retrievable this pass. Any circulating "X% of custody is
   50/50" figure should be assumed unverified.

2. **Planning hours for single vs partnered parents.** ATUS does not publish a marital-status ×
   parenthood cross for household management. The 2.27x gap I computed from ATUS Table 3's
   "other marital statuses" row is NOT a single-parent statistic and must not be presented as
   one.

3. **Fathers' use of family-organization apps.** No credible US source found. Any vendor claim
   about "X% of Cozi/OurFamilyWizard users are dads" would need the vendor's own disclosed
   method and would be Tier C at best.

4. **Gen Z parents (18–29) as a distinct division-of-labor segment.** No data found from Pew,
   Gallup, BLS or the journals searched. ATUS suppresses the 20–24 male childcare cell entirely.
   This is a real hole, not a search failure.

5. **The 77% single-parent loneliness figure** traces to Cigna (2021), a vendor, and the Surgeon
   General's advisory reproduces it without n or fielding window. Tier C at best; verify against
   the Cigna report before use.

6. **The "33% of parents vs 20% of other adults" stress comparison** is widely attributed to the
   Surgeon General but originates in American Psychological Association survey work (APA 2023 /
   2024). Cite the APA release, not HHS, and obtain the APA method before publishing the number.

7. **A quantitative estimate of cognitive-labor HOURS.** Daminger's work is qualitative
   throughout; there is no minutes-per-day measure of anticipation and monitoring in the
   literature reviewed. ATUS "household management" (9 min/day for parents) is the closest
   available proxy and is almost certainly a severe undercount, because anticipation and
   monitoring happen inside other activities and time diaries only capture primary activity.
   Do not present 9 min/day as "the mental load."

8. **Methodological caveat on all 2025 ATUS figures.** BLS suspended all ATUS operations from
   October 1 through November 12, 2025 during the federal shutdown; there are no diaries for
   Sept 30 – Nov 11. Q4 was reweighted so Nov 12 – Dec 30 represents the full quarter. BLS
   states it is not possible to quantify the effect. Any 2024 → 2025 change should carry this
   caveat.
