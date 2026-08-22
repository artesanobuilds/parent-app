# V2 — Adversarial verification of P3, P4, P5, P5b

Verifier V2. Run 2026-08-21. Posture: refute by default. Every URL below was fetched in this session
(PubMed via NCBI E-utilities; CDC via the Wayback snapshot because cdc.gov returns 403 to fetchers;
NCES/Aspen/AA3PM PDFs downloaded and text-extracted locally).

Constraint on this run: the session WebSearch budget was already exhausted (200/200) before V2 started.
All verification was done by direct fetch of URLs cited in the reports plus E-utilities. Claims whose only
route to verification was a fresh search are marked UNVERIFIABLE-BY-BUDGET, not refuted.

---

## SECTION A — THE OBLIGATIONS-PER-YEAR AUDIT (P5 23.4 / P5b 24.9 / floor 15.96 / conditional 34.5)

### A.0 Verdict up front

**The arithmetic is clean. The definition is not, and the floor is not a floor.**

- Every multiplication and sum in both models reproduces exactly (checked line by line, below).
- The largest input (6.0 school activities) is **real, Tier A, and — contrary to the hypothesis put to me —
  is NOT a count of "participation" categories. It is a count of occasions.** The category-error thesis is
  **REFUTED**. Roughly half the estimate does *not* collapse.
- But three defects are real and two of them are material:
  1. **ED visits (0.45) and urgent-care visits (0.40) are by definition UNSCHEDULED.** They cannot be
     calendared, watch-listed, or captured in advance. Including them in a count labelled "discrete
     **scheduled** obligations" is a category error worth **1.7 obligations/yr** for a 2-kid family — and
     0.9 of it sits *inside the sourced-only floor*.
  2. **The "sourced-only floor of 15.96 contains no estimates" claim is FALSE.** Line 3 uses **0.45**, which
     is a midpoint of a range the report itself prints as "0.41–0.48." The published NHAMCS 2019 rate is
     **48 per 100 = 0.48**. 0.45 is an unlabelled estimate sitting in the line the reports advertise as
     assumption-free.
  3. **The 6.0 is published by NCES as a rounded whole integer ("6"), not 6.0.** Carrying it to two decimals
     through to "23.4" and "24.9" is false precision: the underlying mean is somewhere in 5.5–6.49, which
     alone moves the 2-kid total by **±2.0**. Neither 23.4 nor 24.9 is justified to one decimal place.
  4. **×2 double-counts shared school events.** NHES asks about *this child's* school and counts occasions
     "any adult in the household" attended. Two siblings at the same school share a back-to-school night, a
     PTO meeting, a school play. The parent reports it under each child. Multiplying by 2 assumes zero
     sharing — the single biggest unstated assumption in the model, and it lives in the *floor*.

### A.1 Line-by-line

| # | Input | Claimed | Arithmetic reproduces? | Source verified? | V2 finding |
|---|---|---|---|---|---|
| 1 | Office-based physician visits | 1.53/child/yr | n/a (direct) | **YES.** NCHS Data Brief 408, *Characteristics of Office-based Physician Visits, 2018*, May 2021: "153 per 100 children aged 1–17 years"; infants <1 = "596 per 100 infants". Verbatim, via Wayback. | **CONFIRMED.** Caveats: (a) data is 2018 — 8 years old, flagged by P5, good; (b) denominator is **1–17**, but the base case is "both children aged 3–17" — 1–2yos are heavy utilisers, so 1.53 **overstates** a 3–17 child; (c) NAMCS covers office-based physicians only, so it likely **overlaps line 6** (a psychiatrist session is an office-based physician visit) and may overlap line 4 (physician-staffed urgent care). Double-count risk, not flagged in either report. |
| 2 | Dental | 1.8 | **Yes**: 0.90 × 2 = 1.80. | Prevalence source not re-fetched (childstats, Tier A, budget). | **PLAUSIBLE, upper bound.** The report calls 1.8 "the midpoint assuming most attenders make the recommended two." It is not a midpoint — it is 90% × **exactly 2**, i.e. it assumes *every* attender hits the full ADA recall. Real-world dental utilisation is right-censored (many attenders go once). Honest band: 0.9 (all attenders go once) to 1.8. Also applies a 5–17 prevalence to a 3–17 base. |
| 3 | ED visits | 0.45 | **NO — unsourced.** | **Source says 0.48.** NCHS DB 469 (Wayback): "The total ED visit rate for children aged 0–17 decreased from 48 visits per 100 children [2019] to 31 per 100 in 2020." | **REFUTED as sourced.** 0.45 is an undisclosed blend. Also: ED rates are *steeply* age-graded (<1 = 123/100; 1–5 = 63/100; 6–17 "not significant" change and clearly lowest) — so 0.45–0.48 badly overstates a 3–17 child. **And ED visits are not scheduled obligations at all.** Should be struck from the model. |
| 4 | Urgent care / retail clinic | 0.40 | **Yes**: 0.284 × 1.4 = 0.3976. Multiplier declared. | Prevalence not re-fetched (budget). | **Arithmetic OK, category wrong.** Walk-in by definition. Not a schedulable obligation. Strike. |
| 5 | School activities attended | 6.0 | n/a | **YES, and the definition is better than expected.** NCES 2024-113, Table A-2 + Appendix C: the first column is "the mean number of meetings or activities attended at the child's school (FSFREQ), which is computed from parents' responses to an item asking, **'During this school year, how many times has any adult in the household gone to meetings or participated in activities at this child's school?'**" Total = **6**. n = 19,562 K-12 students; weighted PFI unit response 87.8%, **overall unit response rate 53.3%**. | **CONFIRMED — and the "category error" hypothesis is REFUTED.** The 6 counts *times an adult physically went to the school*, i.e. dated, transported, calendar-consuming occasions. It is not a tally of participation types. **However**: (a) it is published rounded to an integer — no decimal exists; (b) it is per *child*, so ×2 double-counts siblings at one school; (c) the mean is strongly right-skewed (public 6, private school 10–11, religious private 11) and NCES publishes no median; (d) it applies only to **K-12 enrolled** children — a 3- or 4-year-old in the base case contributes 0. |
| 5b | "Breakdown of those activities: 83% / 74% / 72% / 52% / 36% / 28%" (P5 finding #10) | — | — | Percentages verified verbatim in Table A-2 (Total row: 83, 74, 72, 52, 36, 28). | **MISDESCRIBED.** These are **independent yes/no items**, not a decomposition of the 6, and NCES combines general-school and PTO meetings into the 83, and volunteering with committee service into the 36. One of them — "participated in school fundraising" (52%) — is explicitly **not** an attendance occasion and is not part of FSFREQ. Calling them a "breakdown of those activities" implies a partition that does not exist. (Mitigation: NCES's own Selected Findings bullet juxtaposes them the same way, so this is inherited, not invented.) |
| 6 | Therapy sessions | 1.5 | **Yes**: 0.122 × 12 = 1.464. | 12.2% prevalence not re-fetched (budget); the "~12 sessions" is declared as an assumption with no source at all. | **PLAUSIBLE with a stated assumption**, but the 12-sessions figure has **zero** source and the line **overlaps line 1** for physician-delivered care. P5's own note that it is "~0 for 88% of kids" is correct and makes the population average a poor description of any actual family. |
| 7 | Sports physical (PPE) | 0.50 | **Yes**: 1.0 × 0.50. | **Conditional rate CONFIRMED.** *Pediatrics* 2015;135(1):26-32 (PMID 25535257): "Fifty (98%) states required a PPE before participation… Most states (53%, n=27) required a specific PPE form… States permitted 9 different health care providers." AFP 2021 (aafp.org/pubs/afp/issues/2021/0501/p539.html): "**Most state high school athletic associations require an annual PPE**"; PPE5 recommends "a full evaluation every two to three years." | **CONFIRMED conditional; population share is an unsourced assumption AND probably too high.** The 50% is P5b's own assumption (declared). Two corrections it does not make: (a) state-association PPE mandates apply to **school-sanctioned interscholastic sport**, largely middle/high school — a 5-year-old in rec soccer triggers no PPE; (b) the base case is ages 3–17, so a majority of the age range is out of scope. 0.50 is a ceiling. |
| 8 | Orthodontic adjustments | 0.288 | Partially. 14.8 ÷ 19.3 mo × 12 = **9.20**/yr (report says 9.1 — rounding). 9.1 × 0.0316 = 0.2876 ✓. | Cadence CONFIRMED as *cited*, but two of three inputs are non-US (Swedish RCT n=90; international meta-analysis) and the prevalence is NHANES III 1988–91. | **The 27.5% "ever treated" cannot be derived from the numbers cited.** P5b calls it "my blend" of Proffit's race-stratified figures (>30% White, 11% Mexican-American, 8% Black). A population-weighted blend of those on any plausible US youth race distribution lands near **21%**, not 27.5%. Recompute: 9.1 × (0.21 × 2.07 / 18) = **0.22**, not 0.288. P5b does flag this as "the weakest input in the whole model" — correct, but the published number is still ~30% too high. |

### A.2 Sums — all reproduce

- P5 per-child: 1.53 + 1.8 + 0.45 + 0.40 + 6.0 + 1.5 = **11.68** ✓ ; ×2 = 23.36 ≈ **23.4** ✓
- P5b per-child: 11.68 + 0.50 + 0.288 = **12.468** ✓ ; ×2 = 24.94 ≈ **24.9** ✓
- Floor: (1.53 + 0.45 + 6.00) × 2 = **15.96** ✓ (arithmetically; see A.0 for why it is not a floor)
- Conditional: Kid A 11.68 + 1.0 + 9.1 = 21.78 ✓ ; Kid B 11.68 + 1.0 = 12.68 ✓ ; total **34.46 ≈ 34.5** ✓

**No arithmetic error found in either report.** The defects are definitional, precision, and one unsourced
input silently placed inside the "sourced-only" line.

### A.3 V2's recomputed number

Applying only the corrections I can defend: strike ED and urgent care (unscheduled); correct ortho to 0.22.

| Line | Per child |
|---|---|
| Office physician visits (Tier A) | 1.53 |
| Dental (estimate, upper bound) | 1.8 |
| School attendance occasions (Tier A, rounded integer) | 6 |
| Therapy (estimate, overlaps line 1) | 1.5 |
| PPE (estimate, ceiling) | 0.50 |
| Orthodontia (estimate, corrected) | 0.22 |
| **Per-child** | **11.55** |

**V2 best estimate: ~23 scheduled obligations/yr for a 2-kid family** (vs P5b's 24.9) — but the honest
reporting band, once the ±0.5 rounding on the NCES 6 and the sibling-sharing question are propagated, is
**roughly 20–26**. Do not quote a decimal.

**V2 sourced-only, scheduled-only floor: (1.53 + 6.00) × 2 = 15.06** — and if two siblings attend the same
school and the household's school trips are shared rather than doubled, the floor falls to **1.53×2 + 6 = 9.1**.
So the defensible floor is a range, **~9–15**, not the crisp 15.96 in both reports.

**Conditional case (34.5):** arithmetic correct, but it stacks three separately-assumed conditions (both kids
in school sport, one in braces) on top of a base that already includes two unscheduled categories. Strip
those and it is ~32.7. Directionally fine; do not put it in a deck as a "typical customer."

**The strategic conclusion survives.** Both reports' actual argument is the *ratio* (≈15–25× camp's 1–2
planning episodes per year) and the *cadence* (one obligation every ~2 weeks). At 20–26, that ratio is
10–26×. Nothing here overturns "cadence, not ceremony, is the asymmetry." What does not survive is the
precision, the word "scheduled" applied to ED/urgent care, and the claim that 15.96 is assumption-free.

---

## SECTION B — CLAIM TABLE

| Claim | Report | Verdict | What I found | Corrected value | URL |
|---|---|---|---|---|---|
| 1.53 office visits/child/yr, NAMCS 2018, ages 1–17 | P5, P5b | **CONFIRMED** | DB 408 (May 2021, 2018 data): "153 per 100 children aged 1–17 years"; infants 596/100. Rate, year and denominator all correct. | 1.53 (but denominator 1–17 ≠ base case 3–17; overlaps therapy line) | https://www.cdc.gov/nchs/products/databriefs/db408.htm |
| 6.0 school-related activities per K-12 student (NHES:PFI 2023, n=19,562) | P5, P5b | **CONFIRMED — and the category-error hypothesis is REFUTED** | FSFREQ: "how many times has any adult in the household gone to meetings or participated in activities at this child's school?" Mean = 6. Counts *occasions*, not participation categories. n=19,562 confirmed; overall unit response rate 53.3%. | 6 (integer, not 6.0); ×2 assumes zero sibling sharing | https://nces.ed.gov/pubs2024/2024113.pdf |
| "Breakdown of those activities: 83/74/72/52/36/28" | P5 (#10) | **REFUTED as a breakdown** | Percentages are exact, but they are independent binary items, not a partition of the 6. Fundraising (52%) is not an attendance occasion at all. | Report as separate participation rates, not components of the 6 | same |
| ED visits 0.45/child/yr "Sourced, Tier A" | P5, P5b | **REFUTED** | NCHS DB 469 publishes **48 per 100** for 2019. 0.45 appears nowhere; it is an undisclosed blend of the report's own 0.41–0.48 range, sitting inside the line advertised as assumption-free. Also unscheduled by definition. | 0.48 if kept; strike from a "scheduled obligations" count | https://www.cdc.gov/nchs/products/databriefs/db469.htm |
| "Sourced-only floor 15.96 carries no assumptions" | P5, P5b | **REFUTED** | Contains the unsourced 0.45; contains an unscheduled category; and embeds a zero-sibling-sharing assumption in the ×2 on the NCES 6. | ~9–15 (see A.3) | — |
| Dental 1.8 = "midpoint" | P5, P5b | **PLAUSIBLE, mislabelled** | The arithmetic is 0.90 × 2 — an all-attenders-hit-full-recall ceiling, not a midpoint. | Band 0.9–1.8 | — |
| Urgent care 0.40 (28.4% × 1.4) | P5, P5b | **PLAUSIBLE arithmetic / wrong category** | 0.284 × 1.4 = 0.3976 ✓; multiplier declared. Walk-in care is not schedulable. | Strike from scheduled count | — |
| Therapy 1.5 (12.2% × 12) | P5, P5b | **PLAUSIBLE** | 0.122 × 12 = 1.464 ✓. The "~12 sessions" has no source of any kind, and the line overlaps NAMCS office visits. | 1.5 ± large; flag overlap | — |
| Sports physical 0.50 | P5b | **PLAUSIBLE (ceiling)** | Conditional rate 1.0/yr is well sourced (98% of states require; most require annually). The 50% participation share is declared as an assumption; it also ignores that PPE mandates are interscholastic (mid/high school), not rec-league or elementary. | ≤0.50 | — |
| Orthodontia 0.28 | P5b | **REFUTED on the prevalence input** | 9.1 visits/yr and 2.07 yrs check out; the 27.5% "ever treated" is not derivable from the NHANES III race-stratified figures cited (>30/11/8%) — a population-weighted blend is ~21%. | **0.22** | https://pubmed.ncbi.nlm.nih.gov/9743642/ |
| 98% of states require a pre-participation exam (Pediatrics 2015) | P5b | **CONFIRMED** | Verbatim: "Fifty (98%) states required a PPE before participation. Most states (53%, n=27) required a specific PPE form… States permitted 9 different health care providers." Correctly flagged as dated (2015). | — | https://pubmed.ncbi.nlm.nih.gov/25535257/ |
| "Most state associations require it annually" (AFP 2021) | P5b | **CONFIRMED** | Verbatim: "Most state high school athletic associations require an annual PPE for participation in school-based athletics." PPE5 recommends full evaluation every 2–3 years. 7.9M HS / ~60M total also verbatim (secondary citations, correctly flagged). | — | https://www.aafp.org/pubs/afp/issues/2021/0501/p539.html |
| 13% of pediatric preventive visits missed (JAMA Netw Open 2026, 4.1M visits, CHOP) | P5b | **CONFIRMED (with a material omission)** | Verbatim: "Among 4 137 542 scheduled preventive care visits, 13% were missed"; 504,428 patients; 32 CHOP practices, PA/NJ, 2009–2023. **P5b never states the paper's actual subject: it is *Extreme Temperatures and Missed Pediatric Preventive Care Visits*.** The 13% is a valid descriptive statistic; the design is a temperature time-series. | 13% — cite the real title | https://pubmed.ncbi.nlm.nih.gov/42043814/ |
| Commercially insured / high-SES families missed MORE | P5b | **CONFIRMED as stated, OVERWEIGHTED as argued** | Verbatim: "higher rates of missed visits among patients with commercial vs public or other types of insurance (**RR, 1.02; 95% CI, 1.02-1.02**) as well as among younger patients and those from high SES neighborhoods" — **and only in cold months.** | A 2% relative difference, conditional on cold-weather stratification, in one 32-practice PA/NJ network. P5b builds "the only evidence that supports building for missed appointments as a *consumer* problem" on it. It cannot carry that. | same |
| 24% of parents who enrolled report the child was waitlisted first | P3 (#6) | **CONFIRMED** | AA3PM 2025 news release, verbatim: "Half of parents who were able to enroll their child agree it is difficult to afford and **24% report their child was on a waitlist prior to enrollment**." | — | https://afterschoolalliance.org/documents/AA3PM-2025/National-AA3PM-2025-NR.pdf |
| 77% of wanted enrollments never happen / 22.6M | P3 (#7) | **CONFIRMED** | Verbatim: "parents of 29.6 million children… want afterschool programs… but just 7 million are currently enrolled. Another 22.6 million children would attend… **three in four of the children (77%)**". Method: 30,515 parents, ≥200/state, EN+ES, mixed-mode, Jan 31–Apr 21 2025, MoE <±1%. | — | same |
| AA3PM method described as "online opt-in panel + phone supplement" | P3 (#6) | **UNVERIFIABLE** | The news release says only "a mixed-mode methodology." The panel type and phone supplement are not stated in any document I could retrieve. Minor embellishment. | Say "mixed-mode, method not further disclosed" | same |
| 62% of parents who paid for summer care went into debt (LendingTree n=638) | P3 (#14) | **PLAUSIBLE — definition UNVERIFIABLE** | Verbatim: "62% have taken on debt to pay for summer child care, camps and activities." Base is the **383** who "require child care arrangements or activities in the summer," not "paid" and not all 638. **LendingTree never defines "took on debt" and never breaks out the instrument** — credit-card float is not excluded and is the most likely majority. Method verbatim: QuestionPro online, 638 parents, Jun 2–3 2025, ages 18–79, **nonprobability** with quotas. Publisher is a debt-consolidation lender asking about debt. | Quote as "62% of the 383 who require summer care say they took on debt (instrument undefined; nonprobability n=383; vendor-interested)" | https://www.lendingtree.com/debt-consolidation/summer-activities-survey/ |
| ~8 in 10 sports parents say scheduling/logistics/time is a challenge, above ~7 in 10 for cost (AP-NORC/Ipsos, Jul 21–26 2026, n=510) | P4 (#1) | **CONFIRMED on existence, method and fairness of comparison; PLAUSIBLE on "ranks above"** | Verbatim: "The poll of 1,737 adults was conducted July 21-26, 2026, using a sample drawn from Ipsos' probability-based KnowledgePanel"; 510 sports parents; MoE ±2.7 / ±4.9. "About 8 in 10 say that scheduling and logistics — or the time commitment — present a challenge." "**Roughly 7 in 10 say the same** about team or club fees, the amount of travel involved and the equipment or uniform costs." "The same" = same major-or-minor basis, so the comparison **is** apples-to-apples. | **Caveat P4 does not state:** the published figures are rounded prose ("about 8 in 10" vs "roughly 7 in 10"). No point estimates and no significance test are published. At MoE ±4.9 on n=510, 76% vs 74% would also round that way. "Above every cost item" is directionally supported, not statistically established. Also: one AP attribution issue — P4 labels it "AP-NORC / Ipsos"; the poll is AP's with **Ipsos KnowledgePanel**, NORC is not named in the source. | https://www.foxsports.com/articles/summer/higherincome-families-more-likely-to-enroll-kids-in-organized-sports-an-apipsos-poll-finds |
| ~7 in 10 ≥$100K vs ~4 in 10 below play organized sports; spend split 2/3 ≤$2K, 2-in-10 $2–5K, 1-in-10 >$5K | P4 (#21) | **CONFIRMED** | All four figures verbatim in the source. | — | same |
| Cornerstone/Edsby "44% manage 7–9 apps per child" | P4 (#31) | **CONFIRMED as a claim, and CORRECTLY FLAGGED by P4** | P4's row already states n=125, "North American parents," "vendor-sponsored (Edsby)," "no MoE, non-probability," "Directional only — always cite with n and sponsor," Tier C. This matches P12's independent finding exactly. P4 additionally kills two laundered derivatives ("60% of parents miss important events" is **not** in the Cornerstone PDF). **No correction needed — this is the best-handled weak source in the four reports.** | — | https://cornerstonepr.net/wp-content/uploads/2025/03/AppOverloadReport_bg.pdf.pdf |
| $1,490.66 per participating child on sports ($1,015.64 + $475.02) | P4 (#5) | **CONFIRMED** | Aspen 2024 Parenting Survey PDF, verified in the source tables: "TOTAL 1015.64 2068.06 0-24600.00" and "TOTAL 475.02 1322.43 0-25500"; both are per the same target child, so the sum is valid. n=1848, Qualtrics, collected online **Nov 5 – Dec 19 2024**, "nationally representative." | **Caveat P4 omits:** the SDs are larger than the means ($2,068 and $1,322; ranges to $24,600/$25,500). These are severely right-skewed distributions and the mean describes almost no family. Aspen publishes no median. Also "nationally representative" is the authors' claim over a **Qualtrics non-probability panel** — P4's Tier B is generous. | https://www.aspeninstitute.org/wp-content/uploads/2025/06/National-Youth-Sports-Parent-Survey-FINAL.pdf |
| × 1.58 participating kids ≈ $2,355/family/yr | P4 | **PLAUSIBLE** | 1,490.66 × 1.58 = 2,355.24 ✓; 1.58 verified in source ("regularly participating in youth sports over the past year (M = 1.58)"). Assumes the second child costs the same as the surveyed target child — an undeclared assumption. | ~$2,355, assumption-dependent | same |
| 202.74 min/day, 2.01 sports, 61.6% volunteer / 4.21 hrs/wk, 40.84 yrs, 1.58 kids in sport | P4 (#2,6,10,25) | **CONFIRMED** | All values matched verbatim against the source tables. | — | same |
| $6,588 vs $734 per child on out-of-school-time, a 9× gap, up from 5× | P4 (#17) | **CONFIRMED** | AA3PM 2025 full report, verbatim: "families in the highest income bracket now spend approximately nine times as much on out-of-school time activities as families in the lowest income bracket, **$6,588 compared to $734**"; "spending by families in the lowest income bracket decreased, from $874 to $734, while spending by families in the highest income bracket grew… from $4,485 to $6,588." Footnote defines out-of-school-time activities and the percentile breaks (top band = $200,000+). | — | https://afterschoolalliance.org/documents/AA3PM-2025/AA3PM-Lost-Opportunity-Afterschool-in-Demand-But-Out-of-Reach-for-Many-Full-Report-2025.pdf |
| $124.10/week afterschool cost; 3.7 days, 5.3 hrs | P4 (#16) | **CONFIRMED** | "$124.10 / Average cost per week"; "3.7 days / Average days per week"; "5.3 hours / Average hours per week" — all verbatim in the full report. | — | same |

---

## SECTION C — WHAT I COULD NOT TEST

- P5 findings #3 (90% dental), #4 (79.6% preventive), #5 (28.4% urgent care), #7 (12.2% therapy), #12–#16
  (Brewer IMWUT 2017; intention-offloading; *Memory & Cognition* 2026) were not independently fetched —
  WebSearch budget was exhausted and these were not on the priority list. They feed estimates 2, 4 and 6,
  so the dental/urgent-care/therapy lines rest on prevalence figures V2 did not re-verify.
- P5b findings #3, #4, #6, #7, #11–#18 (dental no-show, Cleveland RCT, immunization, orthodontic
  duration/expenditure) were not re-fetched. #12/#14/#15 are the inputs to the ortho line; I verified the
  *arithmetic* against P5b's own stated inputs, and refuted the 27.5% blend on internal grounds, not by
  re-reading NHANES III.
- P3 findings #1–#5 (Gallup n=6,899), #10–#11 (BPC), #19–#23 were not re-fetched.
- P5's WEAK SIGNAL kills ("$150B", "30% pediatric no-show", birthday-party counts) could not be
  re-attempted without search budget. They read as sound and P5b independently re-confirms them.
