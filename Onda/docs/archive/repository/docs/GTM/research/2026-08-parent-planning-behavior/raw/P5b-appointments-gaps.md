# P5b — Gap-closer for P5 (appointments / school admin)

Collector P5b. Compiled 2026-08-21. US unless stated. Follows BRIEF.md contract and tier rules.
Scope: the four gaps P5 left open, plus a recomputation of the annual-obligations model. Nothing else.

**Method note that matters for reading this report:** the session-wide WebSearch budget was already
exhausted when this collector started (200/200 used by earlier collectors). All retrieval here was done
through direct fetching: the NCBI E-utilities API (`esearch`/`efetch`) as a substitute search engine over
PubMed/MEDLINE, plus direct HTTP fetches of NFHS, AAFP and NCES documents. That channel is excellent for
peer-reviewed literature (Gaps 1, 2, 4) and useless for grey/vendor literature (Gap 3). Gap 3's answer is
shaped by that limitation as well as by the underlying absence of data — both are stated below.

---

## Section 1: FINDINGS

| # | Claim | Value | Cohort/segment | Publisher | Year | Method (n, window, population) | Tier | URL |
|---|---|---|---|---|---|---|---|---|
| 1 | **13% of scheduled pediatric preventive-care visits were missed** (same-day cancellation or no-show) across a 32-practice US primary-care network over 15 years. | **13%** | Children <19, PA + NJ | JAMA Network Open (Mayne, Fiks et al., Children's Hospital of Philadelphia) | 2026 | Cross-sectional time-series of EHR data; **504,428 patients; 4,137,542 scheduled preventive visits**; 32 CHOP-network primary-care practices, PA and NJ, 2009-01-01 to 2023-12-31 | A | https://pubmed.ncbi.nlm.nih.gov/42043814/ |
| 2 | Within that same network, **missed-visit rates were HIGHER for commercially insured children than publicly insured**, and higher in high-SES neighbourhoods, during cold months. | RR 1.02 (95% CI 1.02–1.02), commercial vs public | Children <19 by payer and neighbourhood SES | JAMA Network Open | 2026 | as above (n=4,137,542 scheduled visits) | A | https://pubmed.ncbi.nlm.nih.gov/42043814/ |
| 3 | **14.3% pediatric dental no-show rate** in a US academic dental setting; adolescents 12–17 were worst at **24%**. | 14.3% overall / 24% adolescents | Patients 0–19, Buffalo NY | International Journal of Dentistry (de Oliveira, McKernan et al.) | 2025 | Retrospective EHR secondary analysis, **7,379 visits**, ages 0–19, 2018–2023, single academic institution in a health-disparities region | A | https://pubmed.ncbi.nlm.nih.gov/40688818/ |
| 4 | **30.8% no-show** at an urban, low-income, resident-staffed US pediatric clinic; a text-message reminder cut it from 38.1% to 23.5% (−14.6 pp, p=0.04). | 30.8% baseline; −14.6 pp | Urban low-income (95.3% African American), Cleveland OH | International Journal of Pediatrics (Lin, Lazebnik et al., Rainbow Babies / Case Western) | 2016 | RCT, **n=170 patients**, Aug 2014–Feb 2015, tertiary ambulatory pediatric practice. **Dated (2014–15); single site; not generalizable to the US population.** | A | https://pubmed.ncbi.nlm.nih.gov/28127311/ |
| 5 | Mean missed-appointment rate in primary care is **15.2% (median 12.9%)**, and the three most commonly reported reasons are **work or family/childcare commitments, forgetting the appointment, and transport difficulties**. | 15.2% mean / 12.9% median | Primary-care patients, all ages | British Journal of General Practice (Parsons, Bryce, Atherton) | 2021 | Systematic review; 26 included studies, 19 reporting a rate, 12 reporting reasons. **UK-led, international evidence base — NOT a US figure.** Patients most likely to miss: minority ethnicity, low socio-demographic status, and age <21 | A (peer-reviewed) — **not US** | https://pubmed.ncbi.nlm.nih.gov/33606660/ |
| 6 | **Coverage with the CDC combined 7-vaccine series among US children aged 19–35 months rose from 70.8% (2010) to ~77% (2023)** — i.e. roughly **one child in four is not complete on the series** at 19–35 months. | 70.8% → ~77% | Children 19–35 months | JMIR Public Health and Surveillance (Majji, Pabon-Rodriguez, Indiana University), using NIS-Child | 2026 (2010–2023 data) | Cross-sectional analysis of **provider-verified** National Immunization Survey-Child; 2010 analytic sample 16,798; 2023 provider-verified response rate 47.7% (18,412/38,619) | A | https://pubmed.ncbi.nlm.nih.gov/41955615/ |
| 7 | US kindergarten vaccination coverage fell to **92.3%–92.7%** in 2023–24 (from 95% in 2019–20); exemptions rose to 3.3%. States operate **grace periods and provisional enrollment for students still completing requirements** — i.e. a hard, dated, school-enforced deadline exists. | 92.3% (DTaP) – 92.7% (MMR); 3.3% exempt | US kindergartners | CDC MMWR (Seither et al.) | 2024 (2023–24 school year) | Annual state-reported administrative census; **49 states + DC reporting** | A | https://pubmed.ncbi.nlm.nih.gov/39418212/ |
| 8 | **50 of 51 US jurisdictions (98%) require a preparticipation physical evaluation (PPE) before school-sports participation.** 53% require a specific form, 24% recommend one; 9 different provider types are permitted to administer it; policies are inconsistent nationwide. | 98% of states | US high-school athletes | *Pediatrics* (Caswell et al., George Mason / CHKD) | 2015 | Document review of PPE policies, documents and forms from **all 50 states + DC**, obtained from state interscholastic athletic associations, compared against PPE-4 consensus. **Dated (2015) — flagged.** | A | https://pubmed.ncbi.nlm.nih.gov/25535257/ |
| 9 | **Most state high-school athletic associations require an ANNUAL PPE** — even though the PPE5 guideline itself recommends a full evaluation only every 2–3 years with annual updates as needed. ~**7.9 million** US high-school students play sports and ~**60 million** US children and adolescents participate in sports overall. | annual; 7.9M HS / 60M total | US youth athletes | *American Family Physician* (peer-reviewed clinical review) | 2021 | Narrative clinical review, AFP 103(9):539–546. Participation figures are **secondary citations within the review**, not primary measurement — treat as indicative | A (journal) with secondary-citation caveat | https://www.aafp.org/pubs/afp/issues/2021/0501/p539.html |
| 10 | **8,266,244 high-school sports participations were recorded for the 2024-25 school year** (4,726,648 boys + 3,539,596 girls) — an all-time high, up from 8,062,302 in 2023-24 and 7,851,833 in 2022-23. | 8,266,244 | US high-school students | National Federation of State High School Associations (NFHS) | 2025 (2024-25 school year) | Annual census compiled from all state high-school associations. **Counts participations per sport, so multi-sport athletes are counted more than once — this is NOT a count of unique athletes.** | B (governing body, method disclosed in the report) | https://a-us.storyblok.com/f/1022696/x/85a6414d04/2024-25-nfhs-high-school-athletics-participation-survey.pdf |
| 11 | A review of State High School Association guidelines for all 50 states + DC found **variation in PPE frequency, forms used, and who may complete the physical**. | qualitative | US high-school athletes | Journal of Pediatric Health Care (Smith, Auburn University) | 2023 | Policy review, all 50 states + DC | A | https://pubmed.ncbi.nlm.nih.gov/36631350/ |
| 12 | **Mean duration of comprehensive fixed-appliance orthodontic treatment is 24.9 months (95% CI 24.6–25.1).** | 24.9 months | Orthodontic patients (mean age 18.4 yrs; 60% female) | *Korean Journal of Orthodontics* (Papageorgiou, Eliades, University of Zurich) | 2017 | Systematic review + random-effects meta-analysis of **34 clinical trials, 6,207 patients**, 9 databases searched to Oct 2016. International, not US-specific | A | https://pubmed.ncbi.nlm.nih.gov/29090128/ |
| 13 | Cochrane states **"Orthodontic treatment takes 20 months on average to correct malocclusion."** | 20 months | Orthodontic patients | Cochrane Database of Systematic Reviews (El-Angbawi et al.) | 2023 | Cochrane review of 23 RCTs, 1,027 participants, searched to Sept 2022; the 20-month figure is the review's background statement | A | https://pubmed.ncbi.nlm.nih.gov/37339352/ |
| 14 | **Orthodontic treatment requires a mean of 14.1–15.5 clinic visits over 18.2–20.4 months** — i.e. roughly **one appointment every 5.5–6.5 weeks, ~9 visits per year in active treatment.** | 14.1–15.5 visits | Adolescents (mean age 15.0–15.3 yrs) | *Angle Orthodontist* (Johansson & Lundström) | 2012 | Prospective RCT, 100 consecutive patients randomized, **90 analyzed** (44 self-ligating / 46 conventional). **Sweden, not US; dated (2012)** — the cadence is a clinical constant, but flag the geography | A — **not US** | https://pubmed.ncbi.nlm.nih.gov/22397386/ |
| 15 | **Over 30% of white US youths, 11% of Mexican-American and 8% of Black youths report having received orthodontic treatment**; 57–59% of every racial/ethnic group has at least some degree of orthodontic treatment need. Treatment is far more frequent in higher-income groups (~5% in the lowest income group; 10–15% in intermediate). | >30% / 11% / 8% | US youths by race/ethnicity and income | *International Journal of Adult Orthodontics and Orthognathic Surgery* (Proffit, Fields, Moray — UNC) | 1998 (NHANES III, 1988–91 data) | National Health and Nutrition Examination Survey III, nationally representative examination survey. **BADLY DATED — 35-year-old data.** This is nonetheless the most recent national prevalence estimate that exists (see #16) | A but severely dated | https://pubmed.ncbi.nlm.nih.gov/9743642/ |
| 16 | **"There has been no epidemiologic study of malocclusion prevalence and treatment need in the United States since NHANES III (1988–1991)."** Orthodontic procedures were the third-largest pediatric dental treatment category (14.5% of visits); lowest among publicly insured children (9.4%). | 14.5% of pediatric dental visits | US children ≤20 | *American Journal of Orthodontics and Dentofacial Orthopedics* (Laniado, Albert Einstein College of Medicine) | 2017 | Analysis of the 2009 and 2013 Medical Expenditure Panel Surveys (MEPS), nationally representative | A | https://pubmed.ncbi.nlm.nih.gov/29103445/ |
| 17 | **4.0% of MEPS respondents (491 of 12,422) reported orthodontic use in 2019**; use was concentrated in females, patients under 18, and families with income ≥$100,000 (52.7%). | 4.0% (all ages, one year) | US population, all ages | *Dentistry Journal* (Hung, Mohajeri — Roseman University) | 2023 (2019 MEPS data) | Cross-sectional analysis of the 2019 Medical Expenditure Panel Survey; **n=12,422**, nationally representative | A | https://pubmed.ncbi.nlm.nih.gov/38132429/ |
| 18 | Total US orthodontic expenditure rose from $11.5B (1996) to **$19.9B (2016)**; out-of-pocket is the largest payment component. | $19.9B | US, all ages | *BMC Oral Health* (Hung et al.) | 2021 (1996–2016 MEPS data) | MEPS, sampling-weighted per-capita and total expenditure estimates | A | https://pubmed.ncbi.nlm.nih.gov/34001095/ |

---

### GAP 1 — Pediatric no-show / missed appointments. **CLOSED, and the answer partly cuts against the product thesis.**

**What is citable now.** P5 was right to kill "30% pediatric no-show" and "$150B" — neither has an origin.
The replacement is stronger and lower: **13% of scheduled pediatric preventive-care visits are missed**,
from 4,137,542 scheduled visits across 504,428 children in a 32-practice network over 15 years (finding 1).
That is the largest US pediatric primary-care denominator I could find anywhere, and it is the number to
use. Dental is comparable at **14.3%** (7,379 visits, finding 3), rising to **24% among adolescents**. The
BJGP systematic review's primary-care mean of **15.2%** (finding 5) brackets both. The 30.8% figure
(finding 4) is real but is a single 170-patient urban safety-net resident clinic — it is the tail, not the
centre, and quoting it as "the pediatric no-show rate" would repeat exactly the error P5 killed.

**Missed well-child visits and immunization.** No source publishes "% of children who missed a well-child
visit" as such. The two closest Tier A anchors: 13% of *scheduled* preventive visits are missed (finding 1),
and P5's existing NSCH figure that 20.4% of children get zero preventive visits in a year. On immunization,
**roughly one child in four is not complete on the CDC 7-vaccine series at 19–35 months** (~77% coverage,
finding 6), and kindergarten coverage has slid to 92.3–92.7% with exemptions at 3.3% (finding 7). Note that
kindergarten non-coverage is now substantially *exemption*-driven (3.3% of the ~7.5% gap), which is a belief
problem, not a scheduling problem — do not present the vaccination gap as unmet demand for reminders.

**Is forgetting the driver? Be honest: partly, and it is not the largest single cause.**
The only systematic evidence on reasons (finding 5, BJGP, 26 studies) names three co-equal leading causes:
**work or family/childcare commitments, forgetting, and transport difficulties**. Forgetting is one of
three, not the dominant one, and that review is not US. A reminder product therefore addresses
*at most* the forgetting third of missed appointments, and only the share of that third not already covered
by the automated SMS/portal reminders every US pediatric practice now sends. The RCT in finding 4 shows the
headroom that remains where reminders are added to a clinic that only phoned: 14.6 percentage points. That
is a large effect — but it accrues to the *clinic*, which is who buys reminder software today.

**The one genuinely surprising, genuinely product-relevant result** is finding 2: within the CHOP network,
**commercially insured children and children from high-SES neighbourhoods missed MORE preventive visits than
publicly insured and low-SES children during cold months.** This inverts the usual access story precisely in
the segment a $99–149/year consumer subscription targets. For affluent families, missing an appointment is
not a transport or cost failure — it is a scheduling and priority failure. That is the only evidence in this
report that supports building for missed appointments as a *consumer* problem rather than a clinic problem.

**Verdict for the product:** appointment-reminder-as-feature is weakly supported. ~13% of preventive visits
are missed; at most a third of those are forgetting; clinics already own the reminder channel. The
defensible product claim is not "we stop you missing appointments" — it is "we hold the whole set of dated
obligations in one place," which is the volume argument, not the no-show argument.

### GAP 2 — Sports physicals / preparticipation exams. **CLOSED on requirement and volume; OPEN on timing and consequence.**

**The obligation is real, hard-deadline, and near-universal for athletes.** 50 of 51 jurisdictions (98%)
require a PPE before participation (finding 8), and **most state associations require it annually**
(finding 9) — notably *more often* than the clinical guideline itself recommends (PPE5 says a full
evaluation every 2–3 years suffices). That gap between what medicine recommends and what athletic
associations mandate is the reason this is a calendar obligation rather than a health decision: it recurs
annually because a bureaucracy says so, and a child without a current signed form does not play. It is also
form-mediated — 53% of states mandate a *specific form*, and 9 different provider types may sign it
(finding 8), which is exactly the kind of "which form, signed by whom, by when" problem parents lose track
of. Volume: 8,266,244 high-school sports participations in 2024-25 (finding 10, though this double-counts
multi-sport athletes so unique HS athletes are fewer), and ~60 million US children and adolescents in sports
overall (finding 9, secondary citation).

**What I could NOT source, and it matters:**
- **When in the year PPEs cluster.** No study measures seasonality of PPE volume. The August back-to-school
  cluster is universally assumed and nowhere measured. Any claim about a summer spike is unsourced.
- **How many parents miss the deadline and have a child held out of play.** Searched specifically. **No
  study, survey or association report at any tier reports this.** It is plausibly common and it is
  completely undocumented. This is the single highest-value primary-research question in this report: it is
  cheap to ask, high-emotion, and would give the wedge a number it does not currently have.

**Verdict:** the best-shaped obligation found by either collector — annual, near-universal among the
~50%+ of kids who play a sport, hard-deadline, form-mediated, and with a visible, emotionally loaded failure
mode (the kid doesn't play). But the failure rate is a hypothesis, not a finding. Do not ship a claim about
it without asking parents first.

### GAP 3 — School form / permission-slip volume. **NOT CLOSED. The number does not exist.**

I re-confirm P5's finding and can now state it more strongly: **there is no source at any tier that counts
forms, permission slips or signature-required documents per K-12 student per year, and no survey that
reports the share of parents who missed a form deadline.** Checked and came back empty: NCES NHES:PFI 2023
(NCES 2024-113) measures parent *participation* in school activities and *school-to-home communication
channels*, and contains no form or paperwork count; PubMed/MEDLINE has essentially no literature on family
administrative burden in schooling; ParentSquare's press page publishes only reach metrics (42,000+ schools,
22 million students) with no per-student document volume and no method. District back-to-school pages are
primary documents but are per-district, non-representative, and inconsistently structured — counting forms
across three districts would produce a number with no defensible population behind it, which is the same
stat-laundering failure the brief tells us to kill. I did not manufacture one.

The nearest defensible anchors remain adjacent and already known: NCES's finding that 90% of K-12 students'
families received school-wide newsletters/notices and 66% received communications specifically about their
own child (Tier A), and the Yahoo/Censuswide "80+ school emails per month, 62% missed something" figures
already in the brief. Note that both measure *communication volume*, not *action-required volume* — the
distinction that matters for a product is precisely the one nobody measures.

**Verdict:** treat form volume as an unmeasured category. If the product's pitch leans on it, that number
has to come from your own parent survey, and it is a cheap question to ask.

### GAP 4 — Orthodontia cadence. **CLOSED, and P5's instinct was right about the cadence but wrong about the aggregate size.**

Every component of the cadence is now sourced:
- **Duration: 24.9 months** (meta-analysis, 34 trials, 6,207 patients — finding 12); Cochrane's background
  figure is 20 months (finding 13). Call it **20–25 months**.
- **Visit frequency: 14.1–15.5 appointments across 18.2–20.4 months** (RCT, n=90 — finding 14) — i.e.
  **one visit every ~5.5–6.5 weeks, about 9 visits per year in active treatment.** P5's guessed "every
  4–8 weeks for 18–24 months" was accurate; it is now sourced (with the caveat that the visit-count study
  is Swedish).
- **Prevalence: this is where it gets bad.** The most recent *national* prevalence estimate of US children
  receiving orthodontic treatment is **NHANES III, 1988–91** (finding 15): >30% of white youths, 11% of
  Mexican-American, 8% of Black youths. AJODO stated flatly in 2017 that no epidemiologic study has been
  done since (finding 16). The only current national utilization figure is MEPS 2019: **4.0% of all
  respondents used orthodontics in that year** (finding 17), heavily concentrated in under-18s and in
  households earning ≥$100,000. Spend is $19.9B/year (finding 18).

**The strategic read is the opposite of P5's framing, and it is more useful.** As a *population average*,
orthodontia is small: a child spends roughly 2 of ~18 childhood years in treatment, and only a minority ever
get treated, so the annualized population-average load is around **0.3 visits per child per year** (see
arithmetic below). But *conditional on being in treatment, it is ~9 appointments a year for two consecutive
years* — on its own, roughly as many discrete scheduled obligations as everything else in a school-age
child's year combined. It is also strongly skewed toward high-income households, which is the segment that
buys a $99–149/year subscription. So orthodontia is not a mass-market volume driver; it is a **high-income
segment intensity driver**, and it is the clearest case in this research for age- and situation-conditioned
product behaviour rather than a uniform default.

---

## RECOMPUTED — discrete scheduled obligations per year, typical 2-kid US family

Same base case as P5: two children both aged 3–17. Two lines are added to P5's six; nothing P5 published
is revised downward.

| # | Category | Per child / yr | Source of the input | Input type |
|---|---|---|---|---|
| 1 | Office-based physician visits | **1.53** | NAMCS 2018 (153 visits/100 children 1–17) | **Sourced, Tier A** |
| 2 | Dental visits | **1.8** | 90% of 5–17s had ≥1 visit (NHIS 2023) + ADA/AAP 2/yr recall; P5's midpoint | Computed estimate |
| 3 | Emergency department visits | **0.45** | NHAMCS 2019 (48 ED visits/100 children 0–17) | **Sourced, Tier A** |
| 4 | Urgent care / retail clinic | **0.40** | NHIS 2022 prevalence 28.4% × assumed 1.4 visits/attender | Computed estimate |
| 5 | School activities a parent attended | **6.0** | NCES NHES:PFI 2023, n=19,562 K-12 students (published mean) | **Sourced, Tier A** |
| 6 | Mental-health / therapy sessions | **1.5** | NSCH 2023 prevalence 12.2% × assumed ~12 sessions | Computed estimate |
| 7 | **Sports physical (PPE)** | **0.50** | Rate is *sourced*: **1.0/yr for any child playing school sports** (98% of states require a PPE, finding 8; most require it annually, finding 9). The **0.50 population average assumes ~50% of school-age children play an organized sport in a given year — that participation share is MY ASSUMPTION and is not sourced in this report** | **Computed estimate** (conditional rate sourced, population share assumed) |
| 8 | **Orthodontic adjustment visits** | **0.28** | 9.1 visits/yr in treatment (14.8 visits ÷ 19.3 months, finding 14) × fraction of childhood spent in treatment. Fraction = 27.5% ever treated (finding 15, dated NHANES III) × 2.07 yrs treatment (finding 12) ÷ 18 childhood years = 3.16%. → 9.1 × 0.0316 = **0.288** | **Computed estimate** (all three inputs sourced; the multiplication is mine, and the prevalence input is 35 years old) |
| | **Per-child subtotal** | **12.46** | | |

**× 2 children = 24.9 ≈ 25 discrete scheduled obligations per year.**

**Sourced-only floor (lines 1, 3, 5 — published population rates, no assumptions):**
(1.53 + 0.45 + 6.00) × 2 = **15.96/year.** *Unchanged from P5.* Nothing found in this gap-closing pass is a
published *population rate*; findings 8–17 are all rates *conditional* on a state of the world (playing a
sport, being in braces). Honest conclusion: **the sourced floor cannot be raised. Only the best estimate moves.**

**Best estimate: 24.9/year** (up from P5's 23.4), ≈ **one obligation every 2.1 weeks.**

**Conditional case — the number that actually describes the target customer.** A 2-kid household where both
children play a school sport and one is in active orthodontic treatment:
- Kid A (sport + braces): 11.68 (P5 base) + 1.0 (PPE) + 9.1 (ortho) = **21.78**
- Kid B (sport only): 11.68 + 1.0 = **12.68**
- **Total = 34.5/year ≈ one scheduled obligation every 10.6 days.**

That is a 39% increase over the base case, driven almost entirely by one child's braces. Against 1–2 camp-
planning episodes per year, the ratio is **~17–25×** on episode count in the base case and **~17–35×** in
the conditional case — consistent with P5's conclusion that cadence, not ceremony, is the asymmetry that
matters.

**Still not included, still unsourced:** birthday parties attended and hosted, vision exams, haircuts,
picture day, spirit week, permission-slip and form deadlines, library returns, subscription renewals,
immunization catch-up visits. P5's unsourced band of 10–20 additional per 2-kid family per year stands
unchanged; I found nothing to move it in either direction. True total remains plausibly 35–45, with 25 as
the defensible estimate and 16 as the floor you can put in a deck.

---

## Section 2: WEAK SIGNAL (not citable — do not promote)

- **"30% pediatric no-show" and "$150B missed-appointment cost."** Confirmed dead, per P5. Superseded by
  finding 1 (13%). The 30.8% figure from finding 4 is real but is one 170-patient safety-net clinic and must
  never be presented as a national rate.
- **Seasonality of sports physicals.** No study, no association report, no vendor figure measures when PPEs
  are performed during the year. The August cluster is an assumption.
- **Parents missing a PPE deadline / children held out of play.** Searched specifically. **Zero sources at
  any tier.** Highest-value unmeasured question in this report.
- **Forms, permission slips, and signature-required documents per K-12 student per year.** Re-confirmed
  absent. NCES measures participation and communication channels, not action-required document counts.
  ParentSquare publishes reach, not document volume, and no method.
- **Share of US parents who missed a school form deadline.** No independent source. The only adjacent figure
  is the already-known Yahoo/Censuswide "62% missed something," which is about email, not forms.
- **Current US orthodontic treatment prevalence among children.** The last national epidemiologic estimate
  is NHANES III (1988–91). AJODO said so explicitly in 2017 and nothing has replaced it. The 27.5% figure
  used in line 8 above is my blend of Proffit's race-stratified 1988–91 numbers and should be treated as the
  weakest input in the whole model. AAO trade claims ("4 million patients in the US and Canada") were not
  retrievable and would be Tier C vendor-interested in any case.
- **Number of unique US high-school athletes.** NFHS publishes *participations*, not unique students; a
  three-sport athlete counts three times. The 8,266,244 figure is a ceiling, not a headcount.
- **US-specific reasons for missed pediatric appointments.** The only systematic reason evidence (finding 5)
  is UK-led and covers all ages. There is no US pediatric equivalent. The India/Navi Mumbai pediatric dental
  study P5 flagged remains non-US and must not be promoted.
- **Hours spent scheduling or coordinating appointments.** Still no ATUS or equivalent breakout. Unchanged
  gap from P5.

## Method notes / limitations

- Retrieval was done entirely through NCBI E-utilities (`esearch`/`efetch`) and direct HTTP, because the
  session WebSearch budget was exhausted before this collector began. This biases coverage *toward*
  peer-reviewed literature and *against* grey literature, vendor reports and news. Gap 3 in particular would
  benefit from a re-run with search budget, though I expect the answer to stay "no data."
- pubmed.ncbi.nlm.nih.gov article pages return a cookie wall to automated fetchers; abstracts were retrieved
  via the E-utilities API instead. URLs in the table point at the canonical PubMed records.
- Findings 5, 12 and 14 are peer-reviewed but **not US** (UK-led review; international meta-analysis;
  Swedish RCT). They are used for mechanism and clinical cadence, never as US population statistics.
- Finding 15 (orthodontic prevalence) is 35 years old and is the load-bearing weak input in the recomputed
  model. If the orthodontia line matters to a decision, that prevalence should be re-derived from current
  MEPS microdata rather than taken from here.
