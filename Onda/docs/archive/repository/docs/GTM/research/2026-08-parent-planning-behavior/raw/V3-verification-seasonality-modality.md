# V3 — ADVERSARIAL VERIFICATION: P6 (trips/weekends), P7 (seasonality), P8 (modality)

Verifier V3. Run 2026-08-21. Posture: refute by default; REFUTED or UNVERIFIABLE when uncertain.
Every numeric claim was put through three lenses — (1) does the primary source say exactly this,
fetched directly; (2) is the method sound for the inference drawn; (3) stale or misquoted.

Where the source was a publisher, I fetched the publisher. Where the claim was **original
measurement** (P7's Google Trends analysis), no publisher exists to check against, so I
independently re-ran the pull and audited the statistics. That work has its own section below.

---

## HEADLINE VERDICTS

1. **P7's Google Trends pull is real and reproduces to ±1 index point across 11 re-pulled series.
   The coefficient-of-variation comparison across query terms is methodologically SOUND** — CV is
   scale-invariant, so Trends' per-term normalisation cancels exactly, and I confirmed this
   empirically. **But the product inference built on the CV ranking is REFUTED**: flatness is not
   demand, and a shared-scale pull shows the "volatile" camp term carries ~25x the search volume of
   the "flat" rows P7 recommends over it. The chart is publishable with three mandatory changes.
2. **P8 does NOT overreach on the dictation 3x figure** — it self-limits correctly in two findings
   and an interpretation. But **P8 cites an author who does not exist** ("Distel et al."), its
   headline product claim ("we offer dictation nowhere") is **contradicted by the repo**, and its
   kill of the 71% statistic is right in conclusion and wrong in both stated reasons.
3. **P6's self-declared "single most decision-relevant number" is an apples-to-oranges error.**
   73% and 43% come from different questions with different answer batteries. The correct
   within-question figure is 27%, ranked 6th of 17 — which makes P6's conclusion *stronger*, but the
   sentence as printed will not survive scrutiny.

---

## SUMMARY TABLE

| Claim | Report | Verdict | What I found | Corrected value | URL |
|---|---|---|---|---|---|
| Google Trends pulled directly from `trends/api`, 2026-08-21, US, weekly 2021-08-22→2026-08-22, n≈261/term | P7 method | **VERIFIED** | I re-ran the identical endpoint chain. Google resolves `today 5-y` to exactly `2021-08-22 2026-08-22`, `resolution=WEEK`, **261 points**. Byte-identical to P7's method note. | as stated | trends.google.com/trends/api/explore |
| CVs: dentist 0.099, pediatrician 0.124, birthday 0.124, kids-activities 0.142, summer camp 0.633 | P7 §1c | **VERIFIED** | Independently re-pulled: 0.0992 / 0.124 / 0.124 / 0.142 / 0.634. Also recomputed all 22 CVs from P7's own printed rows — all match to 3 dp using population sd. All 22 trough values equal the row minimum. | as stated | (re-pull) |
| Is CV a legitimate statistic on normalized relative data, compared ACROSS query terms? | P7 method | **SOUND — verified empirically** | CV=σ/μ is scale-invariant, so the arbitrary per-term normaliser cancels. Confirmed: shared-scale vs own-scale CVs identical to 3 dp for high-volume terms (summer camp 0.633/0.634; birthday 0.124/0.125). | method stands | (see §T3) |
| Fine rank-ordering among the flat terms (ranks 1–9, CV 0.078–0.153) | P7 §1c | **PARTLY REFUTED** | Quantisation alone moved dentist's CV by 0.037 in my diagnostic — comparable to the whole spread of the top nine ranks. Coarse flat-vs-spiky separation is robust; the ordering within the flat cluster is not. | present as a cluster, not a rank | (see §T4) |
| "A generic add-an-appointment surface would land on the flattest demand curve measured in this study" | P7 §1e | **REFUTED** | Flatness ≠ demand. Shared-scale volume: summer camp 36.6, kids-activities 3.5, dentist 1.5. Summer camp's **worst** month (8.1) is ~4.5x dentist's **best** month (1.8). P7 states the rule ("do not read down a column") and then builds its investment recommendation as if magnitude did not exist. | strike, or re-derive with a volume axis | (see §T5) |
| Search volume as a proxy for parent PLANNING LOAD | P7 throughout | **REFUTED as used** | Trends has no age/parent/household filter, and P7 never flags it. "dentist appointment", "birthday party ideas", "flu shot", "family vacation ideas" are not parent-scoped; the table is titled "US **parent** planning". Kid-scoped rows are clean. | restrict parent claims to kid-scoped strings | (see §T6) |
| Column totals 17–25, "1.47x spread", "aggregate parent planning load has no off-season" | P7 §1d | **REFUTED** | Arithmetically correct (I re-summed: 241 grand total, 1.4706x) but it is an artifact — row-normalisation deletes magnitude, 0–3 buckets truncate peaks, 11 hand-chosen families are equal-weighted, and ordinal scores are summed. Removing the single unsourced row moves the spread to 1.57x. | do not publish the column totals | (see §T7) |
| 1b forward-year: next-summer camp search ~2x in Nov, ~2x again in Dec, ~3x into Jan, replicated across two cycles | P7 §1b | **VERIFIED — exactly** | My raw monthly means for "summer camp 2025": 2.0, 2.2, 3.6, 5.2, **10.0, 22.8, 68.0**, 78.2, 84.4, 81.0, 93.8, 78.8. For "summer camp 2026": 2.8, 2.0, 2.8, 4.2, **9.4, 18.2, 57.0**, 64.5, 78.4, 76.0, 89.2, 83.0. P7's printed rows are these, rounded. The dead window really is Aug–Oct. | as stated | (re-pull) |
| "swim team registration" row (table 1a) | P7 §1a | **REFUTED** | **250 of 261 weekly observations are zero.** Raw monthly means 0.0–11.1. The row is quantisation noise published as a curve. My re-pull matches P7's row almost exactly — because we are both faithfully reproducing the same noise. Nothing downstream depends on it. | strike or mark "below reporting threshold" | (see §T8) |
| Google Trends filed as **Tier B** | P7 + `data/seasonality_month_x_task.csv` | **REFUTED** | The BRIEF's Tier B is an enumerated list of research organisations publishing *survey* methodology. Trends is a raw feed with no disclosed sample size, and the analysis is the collector's own — no publisher asserts these findings. | "original analysis on a primary data feed; no disclosed n; not a survey" | (see §T9) |
| "Youth sports in-season" row is the analyst's own construction and is quarantined | P7 §1d | **VERIFIED, with a structural gap** | Quarantined in four places incl. `tier=D, NOT SOURCED` in the CSV. But it sits in table 1d with **no in-table marker** and is the largest single contributor to the column totals (30 of 241) and the flattest row. | add an in-table marker | (see §T10) |
| Birthday-parties trough = 65 (Nov) | P7 §1d justification + CSV | **REFUTED (cosmetic)** | Row minimum is **63** (Dec); Nov is 65. Table 1c prints 63. A printed number disagreeing with the table above it. | 63 | — |
| ACA / CDC sources returned HTTP 403 | P7 WEAK SIGNAL | **VERIFIED** | Independently reconfirmed today: `acacamps.org/families/planning-camp` → 403, `cdc.gov` → 403. The WEAK SIGNAL entries are honest, not excuses. | as stated | — |
| Raw weekly series preserved for audit | P7 | **REFUTED** | Neither file in `data/` contains any of the 42 weekly series. The CVs cannot be audited from the repo — only recomputed from rounded 12-cell rows, or re-pulled. | save the raw pull | — |
| Dictation 3.0x, 161.20 vs 53.46 WPM, 20.4% fewer errors, n=32, iPhone 6 Plus, quiet room, TRANSCRIPTION | P8 #16 | **VERIFIED** | Confirmed against the paper's own text incl. Table 2. 38 recruited, six discarded, 32 analysed. Same phone, Deep Speech 2, MacKenzie/Soukoreff phrase set, 10 practice + 50 test, counterbalanced, "quiet meeting room". | as stated | arxiv.org/abs/1608.07323v1 |
| Same paper: composition by speech 7.8 WPM vs 32.5 keyboard-and-mouse | P8 #17 | **VERIFIED** | Verbatim in Related Work: *"users reached only 7.8 WPM for composition tasks and 13.6 WPM for transcription tasks using speech, compared to 32.5 WPM for a keyboard-mouse method"* — Karat, Halverson, Horn & Karat, CHI 1999. Attribution correct. | as stated | same |
| Is the 3x generalised beyond transcription? Does P8's recommendation depend on the overreach? | P8 | **NO OVERREACH** | #16 is tagged "NOT a composition task"; #17 exists to kill the generalisation; §3 lands on the correct restriction. One residual stretch in §4 (see below). | qualifier belongs in §4 too | — |
| "71% prefer voice over typing" is unsourceable; PwC page 403s; no copy carries an n or fielding date | P8 laundered #1 | **KILL CORRECT, REASONING REFUTED** | An accessible mirror of the PwC primary discloses method verbatim: *"During February 2018, PwC surveyed a nationally representative sample of 1,000 Americans between the ages of 18-64…"*. **And the 71% does not appear in the PwC report at all** — "typing" appears zero times; the only "71" is an unrelated advertising item. So it is a pure **misattribution**, not a stripped qualifier. | kill it, but for misattribution | andresromero.org/wp-content/uploads/2019/03/pwc-voice-assistants.pdf |
| "8.4B voice assistants by 2026" = a Juniper DEVICE forecast | P8 laundered #2 | **VERIFIED, one correction** | Juniper Research, 28 April 2020: *"Number of Voice Assistant Devices in Use to Overtake World Population by 2024"*, "over 8.4 billion devices". Devices/global/forecast all confirmed. **Juniper's target year is 2024, not 2026** — the "2026" is aggregator year-drift, a fifth laundering move. | target year 2024 | juniperresearch.com/press/number-of-voice-assistant-devices-in-use/ |
| 62% of US adults use a voice assistant; 12.4 requests/week; NPR/Edison 2022, n=2,334, Feb 28–Apr 18 2022 | P8 #12, #13 | **VERIFIED** | All four elements exact on Edison's own page. 1,190 + 560 + 584 = 2,334. P8's identification of this as the cleanest date-stripping case is correct. Nit: Edison says 12.4 **"tasks"**, not "requests". | as stated | edisonresearch.com/smart-audio-report-2022-from-npr-and-edison-research/ |
| Pew's 22% "more natural than typing" contradicts the 71% | P8 §7(c) | **VERIFIED** | Pew's item reads *"speaking to the assistant feels more natural than typing"* — 22% major reason, vs 55% hands-free. The contradiction is real and the wording is exactly as P8 needs. | as stated | pewresearch.org/short-reads/2017/12/12/… |
| Smart-speaker ownership peaks 30–49 (41%); 18–29 second-lowest (33%); 50–64 36%; 65+ 24%; Pew 2026, n=5,119 | P8 #3 | **VERIFIED** | Every figure exact. n=5,119, fielded Feb 17–23 2026, published 17 June 2026, both URLs live. **No fabrication.** Also verified: 35% overall; 49% ever / 24% daily chatbot; daily 30-49 34% vs 18-29 31%; confidence 18-29 31% vs 30-49 23%. | as stated | pewresearch.org/internet/2026/06/17/how-opinions-and-use-of-ai-differ-by-age/ |
| "Distel et al., Computers in Human Behavior Reports 15:100450 (2024), n=860" | P8 #19, #20, §5 | **REFUTED — author does not exist** | The DOI is real; the paper is **Kowalczuk & Musial**, *"The impact of self-conscious emotions on the continuance intention of digital voice assistants in private and public contexts"*. No author named Distel; Crossref returns nothing. n=860, German, SEM+multigroup confirmed. Cited three times, load-bearing in §5. | Kowalczuk & Musial 2024 | doi.org/10.1016/j.chbr.2024.100450 |
| 39% of Americans 12+ own a smart speaker, ~112 million, largest gain since 2021 | P8 #1 | **UNVERIFIABLE** | Edison's public Infinite Dial 2026 release confirms n=2,050, 12+, Jan 2026, and the 93% gen-AI figure — but carries **no smart-speaker ownership number**. The 39%, the 112M, and the 35/34/35/39 series behind P8 §7(b) are unsourced to a public primary. | open the paid deck or downgrade | edisonresearch.com/the-infinite-dial-2026/ |
| "MVP offers dictation nowhere — no SFSpeechRecognizer" | P8 §4 | **REFUTED by the repo** | `mvp/MVP/DictationController.swift` exists, **140 LOC**, SFSpeechRecognizer-based, wired into four `OnboardingHeisman*` files. The BRIEF was corrected at 21:53; P8 compiled at 21:18 and uses the superseded text. P8's headline ("our product has the wrong half… close to an inversion") rests on this. | dictation exists, scoped to onboarding | (repo) |
| MMGY: 59% of travelers with children use AI for trip planning; n=4,503, July 2025 | P6 #10 | **VERIFIED, two wording corrections** | n, fielding, age bands, the 40% and the "+10 pts YoY" all verbatim. But MMGY says *"individuals with children"* (a household-composition cut), not "travelers with children" or "parents"; and it qualifies adoption as *"primarily using AI to discover activities of interest"* — narrower than trip planning. | "individuals with children", activity discovery | mmgyintel.com/breaking-from-travel-tradition-… |
| Affordability (73%) outranks planning difficulty (43%) | P6 #4, #5, §1 | **REFUTED — apples-to-oranges** | Different questions, different batteries: 73% from a **17-option obstacles** battery; 43% from an **8-option advisor-motivation** battery with an unstated base. Within the same obstacles battery, **"Planning the trip" is 27%, ranked 6th of 17**. Among parents unlikely to travel, "too difficult/time-consuming to plan" is **6%**. | 27%, 6th of 17 | familytravel.org/assets/pdf/FTA-Survey2025-Report/ |
| Does FTA's likely-traveller screen invalidate the comparison, or only the population estimate? | P6 | **Only the population estimate** | Both figures come from the same screened sample, so a ranking comparison *would* have survived the screen. It fails for the separate reason above. Additional skew P6 does not carry: parents are **94% female, 84% White, 6% under $60k**, recruited via a Good Housekeeping prize drawing. | levels are directional for affluent white mothers | same |
| 1.95B US domestic leisure person-trips 2025 / 1.99B 2026 | P6 #1 | **UNVERIFIABLE** | The Spring 2026 forecast is real (7 May 2026) but the public page reports **spending only** ($909B domestic leisure 2026, +0.9%). Person-trip volumes are member-only. The cited PDF URL does not carry the figure. | obtain the member table or drop | ustravel.org/research/travel-forecast |
| ATUS: 7.5 hrs weekend vs 4.5 weekday secondary childcare; 1.8 hrs during leisure | P6 #16 | **STALE** | Correct for **2024**, but BLS released **2025** results on 25 June 2026 — two months before P6 was compiled. Current: **7.7 weekend / 4.2 weekday** (gap is *wider*) and **1.9 hrs**. This is P6's only Tier A citation. ATUS collection was also suspended 1 Oct–12 Nov 2025 (shutdown). | 7.7 / 4.2 / 1.9 (ATUS 2025) | bls.gov/news.release/atus.nr0.htm |
| TNMT: ~3%/yr shutdown rate for inspiration/planning/booking, 2x peers | P6 #21 | **CAVEATED** | "Nearly 3%" is the **2024** rate for the online-travel segment specifically, against 1.3–2.2%/yr for all travel/mobility tech across three years. A single-year figure, not a standing rate. P6 prints "~3%/yr". | 2024 only; fix the unit | tnmt.com/startup-graveyard/ |
| Pew screen-time: n=3,054 parents of kids ≤12, May 13–26 2025, 42%, fewer than half rank it a top priority | P6 #17 | **VERIFIED** | Exact. Pew's own subhead: *"Most parents say managing their child's screen time is a priority. Fewer than half say it's one of their biggest ones."* P6 §7 is well supported. | as stated | pewresearch.org/internet/2025/10/08/how-parents-manage-screen-time-for-kids/ |
| FTA method + every other FTA number (92%, 83/68/49/30/11, $8,052, 19%/61%, 35/31/3/3, 81/77/74/63/57/27, 11%, advisor battery 60/58/47/45/43) | P6 #2–#9 | **VERIFIED** | n=1,596 (778 parents / 818 grandparents), fielded 18 Jul – 25 Aug 2025, Good Housekeeping recruitment, unlikely travellers screened out. All numbers exact. Bonus for P6's verdict: the 61% is *down* from 71% in 2023. | as stated | same |
| Expedia × Luth: 5+ hrs / 45 days; 71-day window (33+38); 70,000+ panel; 5,700+ survey | P6 #13 | **VERIFIED** | Survey n=5,713. | as stated | expedia.com/newsroom/eg-path-to-purchase-research/ |
| Amex: US n=2,011, Jan 8–13 2025, $50k+ and travels annually, 58% vs 31% | P6 #15 | **VERIFIED** | Population is Millennial/Gen Z **parents**, which P6 states correctly. | as stated | americanexpress.com/…/2025_AMEX_GLOBAL_TRAVEL_TREND_REPORT.pdf |
| Ruan et al.: keyboard preferred for error correction; Koester 7-of-8 abandonment | P8 #18, #28 | **VERIFIED** | Both verbatim in the paper. Koester ref = Koester 2003, RESNA. | as stated | arxiv.org/abs/1608.07323v1 |
| Pew 2017 (46% / 55% / 22% / 61-28-27-18); Menlo (n=5,031, Morning Consult, Apr 2025, Alexa 32% / Siri 25%); Edison n=2,050 / Jan 2026 / 93% | P8 #9–#11, #23, #8 | **VERIFIED** | All exact. | as stated | (see rows above) |

**Kills I did NOT check**, so neither confirmed nor cleared: P8's laundered rows for "voice search will
be 50% of all searches", "57% of voice search users use voice commands daily", "20.5% globally use
voice search", "46% of shoppers don't trust voice assistants", "nearly half of Americans will use
voice assistants by 2026", "$59.9B by 2033". Four checked kills came back three-and-a-half correct,
which is a prior, not a verification.

---

## THE GOOGLE TRENDS ANALYSIS — dedicated methodology verdict

**Headline: the DATA is real and reproduces almost exactly. The CV STATISTIC is legitimate.
The PRODUCT INFERENCE built on the CV ranking is REFUTED.**

### What I did
I re-ran the pull independently on 2026-08-21 from this machine, using P7's own documented
parameter chain (`GET /trends/api/explore` → TIMESERIES widget `request`+`token` →
`GET /trends/api/widgetdata/multiline`, `geo=US`, `category=0`, `property=""`, `hl=en-US`,
`tz=360`, `time=today 5-y`). Google resolved the window to **`2021-08-22 2026-08-22`,
`resolution=WEEK`, 261 weekly points** — byte-identical to P7's method note. I then recomputed
monthly means, re-scaled to peak=100, and computed CV.

### Finding T1 — the pull is genuine and reproduces. VERIFIED.
Eleven of the 42 series were re-pulled independently. Every one reproduces to **±1 index point
on 12 monthly cells**, and every CV to ≤0.006:

| Series | P7 CV | My CV | Row agreement |
|---|---|---|---|
| dentist appointment | 0.099 | 0.0992 | 11/12 exact, Mar 95 vs 94 |
| summer camp | 0.633 | 0.634 | 12/12 exact |
| kids activities near me | 0.142 | 0.142 | 11/12 exact, May 71 vs 72 |
| pediatrician appointment | 0.124 | 0.124 | 12/12 exact |
| birthday party ideas | 0.124 | 0.124 | 12/12 exact |
| family vacation ideas | 0.153 | 0.1537 | 11/12, Feb 91 vs 92 |
| after school program | 0.210 | 0.2096 | 11/12, Jan 64 vs 65 |
| flu shot | 1.076 | 1.0813 | 12/12 exact |
| school supply list | — | 1.792 | 11/12 |
| swim team registration | — | 1.305 | 12/12 exact |
| "summer camp 2025" / "2026" (1b) | see below | see below | 24/24 exact to rounding |

The 1b forward-year table reproduces **exactly**: my raw monthly means for "summer camp 2025"
(Jul→Jun) are 2.0, 2.2, 3.6, 5.2, 10.0, 22.8, 68.0, 78.2, 84.4, 81.0, 93.8, 78.8 — P7 printed
2, 2, 4, 5, 10, 23, 68, 78, 84, 81, 94, 79. For "summer camp 2026": 2.8, 2.0, 2.8, 4.2, 9.4,
18.2, 57.0, 64.5, 78.4, 76.0, 89.2, 83.0 — P7 printed 3, 2, 3, 4, 9, 18, 57, 64, 78, 76, 89, 83.
The Nov-doubling / Dec-doubling / Jan-tripling pattern and its two-cycle replication are **VERIFIED**.
The Nov step rests on values of 4–10 on a 0–100 integer index, so it is the fragile end of the
claim, but it survives: a 2x move is well outside ±0.5 quantization, and it replicates.

I also pulled "dentist appointment" three times in the same session: CV=0.0992 and an identical
12-cell row every time. Google's disclaimer that Trends is a *sample* that can differ between
pulls is true in principle but is **not** a practical threat to a 5-year weekly series — the
series is stable within a day. P7's "replicable with the parameters documented above" is fair.

### Finding T2 — the CVs are internally consistent. VERIFIED.
I recomputed CV directly from P7's own published 1a rows. All 22 CVs in table 1c reproduce to
three decimals using **population** standard deviation (ddof=0) over the 12 monthly means. All 22
"trough month index" values equal the row minimum. All 11 row totals and all 12 column totals in
table 1d are arithmetically correct (241 grand total, 1.47x spread). No arithmetic was fudged.

### Finding T3 — IS CV A LEGITIMATE STATISTIC ON NORMALIZED RELATIVE DATA? **YES.**
This is the question the task flagged as decisive, and the answer favours the report.

Google Trends divides an entire single-term series by one scalar (its own peak) and scales to
0–100. **CV = σ/μ is scale-invariant**: multiply every value by any constant k and CV is unchanged.
The arbitrary normalisation constant therefore *cancels exactly*. CV is in fact one of the very
few statistics that IS safe to compare across independently-normalised Trends series — unlike
standard deviation, range, or trough index, all of which are not. P7's second normalisation
(re-scaling monthly means so peak month = 100) is also multiplicative and likewise cancels.

I verified this empirically rather than taking it on theory. I re-pulled five of the terms in a
single *shared-scale* comparison request (all five normalised to one common maximum) and
recomputed CV on that scale:

| Term | CV, own-scale pull | CV, shared-scale pull | mean index on shared scale |
|---|---|---|---|
| summer camp | 0.633 | 0.634 | 36.6 |
| birthday party ideas | 0.124 | 0.125 | 9.3 |
| kids activities near me | 0.142 | 0.153 | 3.5 |
| dentist appointment | 0.099 | 0.136 | 1.5 |
| gymnastics for kids | 0.078 | 0.070 | 1.1 |

For the two high-volume terms the CVs are **identical to three decimals** — scale-invariance
holds exactly, as theory requires. The divergence appears only where the shared scale crushes a
term into integers 1–2, i.e. it is a *quantisation* artifact of my diagnostic pull, not a defect
in P7's method. P7's choice of individual per-term pulls is the correct one: it gives each term
the full 0–100 resolution. **Verdict: the CV comparison across query terms is methodologically
sound and is the right tool for the "shape over time" question.**

### Finding T4 — but the FINE ORDERING among the flat terms is not defensible. PARTLY REFUTED.
Ranks 1–9 in table 1c span CV 0.078 → 0.153. My shared-scale diagnostic showed that changing only
the quantisation of the same underlying series moved dentist's CV by 0.037 and gymnastics's by
0.008 — a wobble comparable to the entire spread of the top nine ranks. Low-volume terms also
carry proportionally more Poisson sampling noise, which biases CV *upward*, so a term can rank
"less flat" purely for being less searched. The report's coarse separation — flat cluster ~0.08–0.15
vs. spiky cluster ~0.5–2.8 — is robust and load-bearing. The claim that dentist (0.099) is flatter
than pediatrician (0.124) which is flatter than kids-activities (0.142) is **not** measurably true,
and the report should not present a rank-ordered table that invites reading it that way. The single
derived headline "summer camp is 4.5x more seasonally volatile than kids activities near me"
(0.633/0.142 = 4.46) sits across the robust gap and survives.

### Finding T5 — THE CENTRAL PRODUCT INFERENCE IS REFUTED.
This is the most serious finding in P7.

P7 states the rule correctly — *"Do not read down a column to compare keywords by size"* — and then
violates its spirit in Section 1e, where the entire recommendation is built on flatness:

> "A generic 'add an appointment / remind me' surface would land on the flattest demand curve
> measured in this study."

Flatness is not demand. My shared-scale pull measures relative volume directly, and it inverts the
recommendation:

- "summer camp" mean index **36.6** vs "dentist appointment" **1.5** — roughly **25x** the search volume.
- Summer camp's **worst** month on the shared scale (8.1, September) is still about **4.5x**
  dentist appointment's **best** month (1.8, March).
- "kids activities near me" (3.5) — the row P7 nominates as the all-season anchor — carries about
  **one tenth** the volume of the camp row it is being recommended over.

So the volatile row that P7 argues against is an order of magnitude larger at its trough than the
flat rows are at their peak. A CV ranking with the magnitude axis deleted cannot support a
"which vertical to invest in" conclusion, and P7 draws exactly that conclusion. **The flatness
finding is real; the investment inference drawn from it does not follow and must be struck or
re-derived with a volume axis.**

### Finding T6 — search volume as a proxy for PLANNING LOAD. REFUTED as used.
Two distinct problems, only the first of which P7 acknowledges (in its Limits section):

1. Search measures *information-seeking*, not work performed. A flat "dentist appointment" curve is
   close to an a-priori certainty rather than a discovery: dental visits are individually scheduled
   ~6 months apart and are uniformly distributed across the population because no shared calendar
   forces them. Flatness there is a definitional property of the task class, not evidence of demand.
2. **Trends carries no age, parent, or household filter, and P7 never flags this.** "dentist
   appointment", "birthday party ideas", "flu shot" and "family vacation ideas" are not
   parent-specific queries — a large and unmeasurable share is adults booking for themselves.
   Yet the report titles table 1d "month × task-family demand map for **US parent** planning" and
   the column-total paragraph reads it as "aggregate **parent** planning load". The parent-specific
   subset of these curves is unmeasured. Rows built on explicitly kid-scoped strings ("kids
   activities near me", "pediatrician appointment", "well child visit", "summer camp") are clean;
   the medical/dental, birthday and vacation rows are not.

### Finding T7 — the 1d column totals must NOT be published as a number. REFUTED.
> "The column totals are startlingly flat: 17 to 25 across all twelve months, a 1.47x spread.
> Aggregate parent planning load has no off-season."

This number is an artifact, not a measurement. It is produced by (a) row-normalising every series,
which deletes magnitude entirely, so a task family with 25x the volume contributes the same maximum
of 3 as one with 1x; (b) compressing a continuous index into four ordinal buckets, which truncates
peaks — summer camp is capped at 3 for five consecutive months despite an index range of 78–100;
(c) equal-weighting eleven hand-chosen task families; and (d) summing ordinal scores, which is not a
defined operation. The flatness of the column total is close to a mathematical consequence of the
construction. Deleting the single unsourced row (youth sports) changes the spread from 1.47x to
1.57x, i.e. the flattest and least-sourced row is what makes the total look flat. **Publish the
0–3 map as a qualitative calendar if you like; do not publish the column totals, and delete the
sentence "1.47x spread."**

### Finding T8 — "swim team registration" is noise published as a curve. REFUTED.
I re-pulled it: **250 of 261 weekly observations are zero**. The whole row rests on 11 non-zero
weeks in five years, with raw monthly means of 0.0–11.1 before re-scaling. My reproduction matches
P7's printed row [0, 52, 26, 0, 100, 0, 28, 21, 43, 0, 0, 0] almost exactly — because we are both
faithfully reproducing the same quantisation noise. It appears in table 1a with no volume caveat.
It does not appear in 1c and is not cited in any justification cell, so nothing downstream depends
on it, but it should be struck from 1a or marked "below reporting threshold." Several other rows
("fall soccer registration", "thanksgiving activities for kids", "youth baseball registration")
have long zero runs and warrant the same audit.

### Finding T9 — the Tier B label. REFUTED.
P7 files Google Trends as **Tier B** on the grounds that Google is "a major organization with a
published methodology page." The BRIEF's Tier B is an enumerated list of *research organizations
publishing survey methodology* (Pew, Harris, Bright Horizons, Aspen, Edison, RevenueCat, Gallup,
Nielsen, eMarketer). Google Trends is none of those things: it is a raw data feed, not a published
study, and the analysis is the collector's own — there is no publisher who has asserted any of these
findings. The BRIEF also requires "no number without publisher, year, and **method (n)**"; Google
does not disclose the sample size, which P7 correctly notes and then files as Tier B anyway. The
honest label is **"original analysis by the collector on a primary data feed; no disclosed sample
size; not a survey"** — arguably stronger than Tier B for shape questions and weaker for anything
else, but it is not Tier B. The `data/seasonality_month_x_task.csv` file propagates the `B` tag to
ten of eleven rows. Fix the label in both places.

### Finding T10 — the "youth sports in-season" quarantine. VERIFIED, with one structural gap.
The task asked me to confirm this row is quarantined and not presented as data. It is, in four
places: the justification cell calls it "my own construction… Confidence: medium-low… the least
directly sourced — treat with care"; the WEAK SIGNAL section repeats it; the Confidence section
lists it as Low; and `data/seasonality_month_x_task.csv` tags it `source="Analyst construction from
registration-lead curves"`, `tier=D`, `notes="NOT SOURCED"`. That is an honest quarantine and
better than most of this program.

The gap is structural, not textual: the row still sits inside deliverable table 1d with **no
in-table marker** — no asterisk, no shading, nothing distinguishing it from the ten Trends-derived
rows — and its values are summed into the column totals, where at 30 of 241 it is the **largest
single contributor** and the flattest row in the table. Add an in-table marker, and since the column
totals should go anyway (T7), the contamination goes with them.

### Findings T11 — minor internal inconsistencies
- **Birthday parties trough.** Table 1c and my recomputation both give the row minimum as **63**
  (December). The justification cell in 1d and the CSV note both say "trough 65 in Nov". Nov is 65,
  Dec is 63. Cosmetic, but it is a printed number that disagrees with the table above it.
- **"Flattest meaningful row."** 1d describes "kids activities near me" (0.142) as "the flattest
  meaningful row in the dataset." Seven rows are flatter. "Meaningful" is carrying the claim; it is
  not wrong, but it is not measured either.
- **Blocked-source claims are honest.** I independently confirmed `acacamps.org/families/planning-camp`
  → HTTP 403 and `cdc.gov` → HTTP 403 today. P7's WEAK SIGNAL entries are not excuses.
- **Raw series were not preserved.** Neither `data/` file contains the 42 weekly series. The CVs
  cannot be audited from the repo — only recomputed from the rounded 12-cell rows P7 printed (which
  is what I did) or re-pulled from Google (which is what I also did). Save the raw pull.

### CAN THE CHART BE PUBLISHED?
**Yes, with three mandatory changes.**

1. **Publish 1a, 1b and 1c** — the data is genuine, reproduces to ±1 point, and the CV statistic is
   correct and appropriate. Label it "original analysis of Google Trends, US, weekly 2021-08-22 →
   2026-08-22, n=261 weekly points per term; Google does not disclose sample size" — **not Tier B**.
2. **Add a volume axis, or drop every claim that ranks task families by flatness.** Without it,
   Finding T5 stands: the report recommends the low-volume rows over a row with ~25x the volume.
   A shared-scale comparison pull (one request, five terms) is a ten-minute fix and would let the
   chart carry both axes honestly.
3. **Do not publish the 1d column totals or the "1.47x spread" sentence** (T7); mark the youth-sports
   row in-table (T10); strike or footnote "swim team registration" (T8); and state plainly that
   Trends has no parent/age filter, so the medical, birthday and vacation rows are not
   parent-specific (T6).

The 1b forward-year camp result — "the dead window is August–October, three months, not six; camp
search re-ignites in November" — is the strongest thing in P7. It reproduces exactly, it replicates
across two independent camp cycles, it is built on kid-scoped query strings, and it does not depend
on any cross-term comparison. **That one is publishable as-is.**

---

## P8 — MODALITY

### THE DICTATION-OVERREACH VERDICT (asked for explicitly)

**The 3x figure is NOT overreached, and P8's recommendation does not depend on an overreach.**
Everything in the task's suspicion list was independently confirmed against the paper's own text
(extracted from arxiv.org/pdf/1608.07323v1): English 161.20 vs 53.46 WPM = 3.0x; total error 2.93%
vs 3.68% = 20.4% lower; 38 recruited, six discarded, **32 analysed**; "All participants used the
same iPhone 6 Plus"; Deep Speech 2; "we performed the study in a quiet meeting room"; a
**transcription** task over the MacKenzie/Soukoreff phrase set (120 of 500 phrases), 10 practice
then 50 test trials, counterbalanced.

And the paper's Related Work carries P8's own counter-cites verbatim: *"users reached only 7.8 WPM
for composition tasks and 13.6 WPM for transcription tasks using speech, compared to 32.5 WPM for a
keyboard-mouse method"* (Karat, Halverson, Horn & Karat, CHI 1999 — attribution correct) and
*"participants entered text at an average rate of 18 WPM when seated and 13 WPM when walking"*
(Vertanen & Kristensson, Parakeet 2009). Also confirmed verbatim: *"most users prefer keyboard to
speech for error correction and this significantly improves performance"* and *"seven out of eight
new users abandoned their speech recognition system after six months"* (Koester 2003, RESNA).

P8 does not launder its own headline. Finding #16 is tagged **"DATED (2016) and NOT a composition
task"** in the Method column; finding #17 exists purely to kill the generalisation; and
interpretation §3 lands on the correct restriction — *"voice wins when the user is emptying a formed
thought… and loses when the user is forming one"* — plus the correct architectural conclusion
(voice-in / text-out-and-editable, never voice-only), which follows from the error-correction
finding rather than from the 3x. That is a model of self-limiting citation and it should be said so.

**One residual stretch, and it is minor.** Interpretation §4 attaches the bare "3x measured speed
advantage" to a general product recommendation covering "the app's 58 text-entry fields" without
re-asserting the transcription restriction there. Most of those fields (a kid's name, an allergy, an
activity) are transcription of a formed thought, so the application is defensible — but the
paragraph should carry the qualifier the two findings above it establish, and the magnitude claimed
for a modern on-device recogniser in a noisy kitchen is not 3.0x on any measured basis. Restate as
"substantially faster for short, formed utterances" and the recommendation is unharmed.

### THE LAUNDERED-STATISTICS SECTION — is P8 right to kill?

Spot-checked four kills. **Three kills stand; two of them stand for a different reason than P8 gives,
and one carries a factual error.** A false kill is as damaging as a false claim, and P8 has one
half-false kill.

**"71% prefer voice over typing."** P8 says the PwC page 403s and *"no accessible copy carries an n
or fielding date."* **That specific ground is REFUTED.** A mirror of the primary PDF is accessible
and PwC discloses method verbatim: *"During February 2018, PwC surveyed a nationally representative
sample of 1,000 Americans between the ages of 18-64 who have access to the internet via an online
survey conducted by a leading global research firm."* PwC's own URL does return 403 — that half is
right.

But the correct verdict is **harsher** than P8's, not softer: **the 71% statistic does not appear in
the PwC report at all.** Full-text search of the 12-page primary finds "typing"/"type" zero times;
"prefer" three times, none about voice-vs-typing; and the only "71" in the document is an unrelated
advertising item. So this is not "a real number with the qualifier stripped" — it is a **pure
misattribution**: a real, methodologically disclosed 2018 PwC survey exists and it does not contain
this statistic. P8's *conclusion* (do not use in any form) is correct; its *reasoning* is wrong on
both limbs and must be rewritten, because "PwC hid its method" is itself a falsifiable claim that
someone will falsify. Caveat: one canonical mirror was checked; another PwC voice artifact cannot be
formally excluded.

**"8.4 billion voice assistants by 2026."** P8's characterisation is right — a **Juniper Research
press release dated 28 April 2020**, *"Number of Voice Assistant Devices in Use to Overtake World
Population by 2024"*, forecasting *"over 8.4 billion devices"*, up 113% from 4.2bn at end-2020.
Devices not people, global not US, forecast not measurement: all four of P8's points confirmed.
**One correction: Juniper's target year is 2024, not 2026.** The "by 2026" in circulation is
year-drift the aggregators added, which is arguably a fifth laundering move worth naming. Fix the
row to say so.

**"62% of US adults use a voice assistant / 12.4 requests per week."** P8 calls this genuine but
misdated by aggregators. **VERIFIED exactly, all four elements**: Edison's own page states 62% of
Americans 18+ use a voice assistant on any device, *"smart speaker owners request an average of 12.4
tasks on their device each week"*, 1,190 + 560 + 584 = **2,334** US adults 18+, and *"Surveys were
conducted 2/28/2022-4/18/2022"*. P8's identification of this as the cleanest case of date-stripping
is correct. Wording nit: Edison says **12.4 "tasks"**, not "requests".

**The Pew contradiction P8 uses to bury the 71%.** VERIFIED and the wording is exactly as P8 needs
it: Pew's item reads *"speaking to the assistant feels more natural than typing"*, endorsed as a
major reason by **22%**, against **55%** for hands-free. The 71%-vs-22% contradiction is real.

### P8 — items REFUTED or UNVERIFIABLE

**REFUTED — the author of findings #19/#20 does not exist.** DOI 10.1016/j.chbr.2024.100450 is real,
but the paper is **Pascal Kowalczuk & Jennifer Musial**, *"The impact of self-conscious emotions on
the continuance intention of digital voice assistants in private and public contexts"*, Computers in
Human Behavior Reports 15:100450 (2024). There is no author named **Distel**; a Crossref search for
Distel + voice assistant + continuance returns nothing. n=860, German institution, SEM + multigroup
all confirmed. P8 cites "Distel et al." three times, including in interpretation §5 where it is
load-bearing for the entire "voice is socially unusable for parents" argument. A named citation that
does not exist is the single most quotable error in the report. Also tighten the finding: the paper
is subtler than "continuance intention is lower in public" — **shame** inhibits continuance in
**public**, **guilt** in **private**, pride raises it everywhere, vicarious embarrassment null. P8's
finding #20 has this right; finding #19's one-line summary overstates it.

**UNVERIFIABLE — P8's finding #1, the 39% / ~112 million smart-speaker figure.** Edison's public
Infinite Dial 2026 release confirms n=2,050, age 12+, fielded January 2026, ~half SSRS Opinion Panel,
and the 93% gen-AI familiarity figure — but carries **no smart-speaker ownership number**; "smart
speaker" appears only in boilerplate about what the series tracks. The 39% may live in the paid deck
or the March webinar. P8 cites a specific PDF URL for it. Until someone opens that deck, the 39%,
the 112 million, the "largest one-year gain since 2021", and the 35/34/35/39 series P8 builds its
contradiction §7(b) on are all **unsourced to a public primary**. Downgrade or open the deck.

**REFUTED — P8's interpretation §4 is factually wrong about the product.** It states MVP *"offers
(a) dictation nowhere — no SFSpeechRecognizer, and the mic was actively REMOVED from the Coach
composer,"* and builds its headline ("our product has the wrong half… close to an inversion of what
the literature supports") on that. The repo contradicts it: `mvp/MVP/DictationController.swift`
exists, is **140 LOC**, is SFSpeechRecognizer-based, and is wired into four files
(`OnboardingHeismanTail/Extract/Chrome/Screens.swift`). The BRIEF was corrected at 21:53 on
2026-08-21 to say exactly this; P8 was compiled at 21:18 and is working from the superseded text.
The *direction* of P8's recommendation survives and is arguably strengthened — the pattern is now
proven in-house and the open question is extending it to capture surfaces, not inventing it — but
the "we offer it nowhere / this is an inversion" framing is false and must be rewritten before this
reaches a synthesis.

**Not checked by me** (so: neither confirmed nor cleared): the kills on "voice search will be 50% of
all searches", "57% of voice search users use voice commands daily", "20.5% globally use voice
search", "46% of shoppers don't trust voice assistants", "nearly half of Americans will use voice
assistants by 2026", and "$59.9B by 2033". The four I did check came back three-and-a-half correct,
which is a reasonable prior for the rest, but it is a prior and not a verification.

**Verified and passing** (listed only because the task said a false kill is as damaging as a false
claim, and these are the ones that would have hurt most if wrong): the entire Pew 2026 block —
n=5,119, fielded Feb 17–23 2026, published 17 June 2026, both URLs live, no fabrication. Smart
speaker 35% overall and **18-29: 33%, 30-49: 41%, 50-64: 36%, 65+: 24%** — peaks at 30-49, 18-29
second-lowest, exactly as printed. Chatbots 49% ever (from 33% in 2024) / 24% daily; daily use
30-49: 34% vs 18-29: 31%; confidence 18-29: 31% vs 30-49: 23%. Also verified: Pew 2017 (46% / 55% /
22% / 61-28-27-18), Menlo Ventures (n=5,031, Morning Consult, April 2025, Alexa 32% / Siri 25%), and
Edison's n=2,050 / Jan 2026 / 93%.

---

## P6 — TRIPS & WEEKEND OUTINGS

### THE HEADLINE REFUTATION: the 73%-vs-43% comparison is apples-to-oranges

P6 calls this *"the single most decision-relevant number in the report"* and marks it **High
confidence**. It is wrong, and the correct number cuts the same way but from a different place.

The two figures come from **two different questions with two different answer batteries**:

- **73% affordability** — *"Which of the following factors listed below are the most challenging to
  you when considering travel with your children?"* — a **17-option obstacles battery**.
- **43% "planning and booking on my own is time-consuming and/or confusing"** — *"What are the
  reasons you have used or would be open to using a travel agent for your family trips?"* — an
  **8-option advisor-motivation battery**, with an unstated base whose wording ("have used or would
  be open to using") suggests advisor-rejecters may be excluded, which would inflate the 43% further.

Comparing a rank within a 17-item obstacles list against a rank within an 8-item advisor-motivation
list is not a comparison. **The correct within-question figure is in the same obstacles battery that
produces the 73%: "Planning the trip" is cited by 27%, ranked 6th of 17** — tied with "dealing with
potential cancellations" and below timing of school breaks (51%), available vacation time (47%) and
"finding a destination everyone will enjoy" (40%). Among parents *unlikely* to travel, "it's too
difficult/time-consuming to plan" is cited by just **6%**.

So P6's claim that planning difficulty "ranks 5th of 8 at 43%" should read **6th of 17 at 27%** —
16 points lower and four ranks further down. **P6's conclusion survives and gets stronger:** parents
are telling researchers this is a money problem, not a labour problem, by a wider margin than P6
claimed. But the sentence as printed is a methodological error that a hostile reader will find, and
it is the one P6 flagged as its most load-bearing. Rewrite it with the 27% and the correct battery.

### The screening question, answered

The task asked whether FTA's screen to likely travellers invalidates the comparison or merely the
population estimate. **Merely the population estimate.** Both the 73% and the 43% come from the same
screened sample, so a ranking comparison *would* have survived the screen — the comparison fails for
the separate reason above. P6 is right to quarantine the 92% as a screened-sample artifact and to
call it a laundering case.

The screen is worse than P6 says, though, and in a direction P6 should carry: FTA's parent sample is
**94% female, 84% White, with only 6% under $60k household income**, recruited from Good
Housekeeping's consumer database with a prize drawing. Every FTA level in P6 — 73%, $8,052, 27% AI,
19% advisor — is directional for affluent white mothers, not for US parents. Since P6's whole verdict
on the trips vertical rests on FTA, that skew belongs in the verdict cell, not just the method column.

### MMGY 59% — VERIFIED, with a wording correction that matters

n=4,503 US adults, interviewed July 2025, generational bands Gen Z 18-28 / Millennial 29-44 / Gen X
45-60 / Boomer 61-79: all **VERIFIED**. "40% of active US leisure travelers have used ChatGPT or
another AI tool for travel planning, +10 points YoY": **VERIFIED verbatim**. "Travelers trust
recommendations from human experts more than twice as much as AI-generated suggestions":
**VERIFIED verbatim**.

Two corrections to how P6 states the 59%:

1. MMGY's wording is *"Millennials and **individuals with children** lead adoption (both at 59%)"*.
   P6 renders this as "travelers with children" in finding #10 and as "**59% of travelers with
   children**" in the interpretation. "Individuals with children" is a household-composition cut, not
   a with-kids-on-this-trip cut, and MMGY does not say "parents." Minor, but P6's §3 leans on the
   phrase to argue "parents are the *heaviest* AI trip-planning users."
2. **MMGY qualifies the adoption**: travellers are *"primarily using AI to discover activities of
   interest"* — narrower than trip planning end-to-end. P6 drops the qualifier and then argues the
   category is lost because free chatbots "produce a genuinely good first draft." Activity discovery
   is precisely the shallow end of the task; the deep end (execution, deadlines, reconciliation
   against camp and school dates) is what P6's own §9 says would change the verdict. Restoring the
   qualifier makes §3 weaker and §9 stronger, which is a real shift in the argument.

Note also that P6's §4 resolves the 27%-vs-59% spread as a population artifact ("27% is the floor,
59% the ceiling"). That reconciliation is sound and both endpoints are verified.

### Other P6 items refuted, stale, or unverifiable

**UNVERIFIABLE — finding #1, 1.95B / 1.99B domestic leisure person-trips.** The US Travel /
Tourism Economics Spring 2026 forecast is real (published 7 May 2026), but the public page reports
**spending only** ($909B domestic leisure in 2026, +0.9%). Person-trip *volumes* live in the
member-only forecast table. Neither figure could be confirmed from any public primary. The magnitudes
are plausible, and P6 already labels the derived "~5.7 person-trips per resident" as its own
arithmetic and quarantines it in WEAK SIGNAL — but the 1.95B itself is presented in the findings
table with a direct PDF URL that does not carry it. Either obtain the member table or drop #1.

**STALE — finding #16, the ATUS numbers, are one release out of date.** P6 cites ATUS **2024**
(released 2025-06-26) for 7.5 weekend vs 4.5 weekday secondary childcare and 1.8 hrs during leisure.
Those are correct for 2024. But **BLS released the 2025 results on 25 June 2026 — two months before
this report was compiled.** Current figures: **7.7 weekend / 4.2 weekday** (the weekend-weekday gap
is *wider*, not narrower) and **1.9 hrs** during leisure. This is P6's only **Tier A** citation and it
is the one that is out of date; that is an avoidable miss on the highest-tier source in the report.
Note also that ATUS collection was suspended 1 Oct – 12 Nov 2025 for the government shutdown, which
belongs in the method column. The direction of P6's inference is unchanged — if anything the wider
gap strengthens the weekend-load point.

**CAVEATED — finding #21, TNMT.** The "~3%" is the **2024** failure rate for the online-travel
segment specifically, against 1.3–2.2% per year for all travel/mobility tech across three years. It
is a single-year figure, not a standing rate. P6 prints it as "~3%/yr", which implies a rate. Fix the
unit.

**CAVEATED — finding #15, Amex.** US n=2,011, fielded 8–13 Jan 2025, screened to $50k+ income and
travels at least annually, 58% vs 31%: all **VERIFIED**. The population is Millennial/Gen Z
**parents**, which P6 states correctly.

### P6 items that verified cleanly

FTA method (n=1,596; 778 parents / 818 grandparents; fielded 18 Jul – 25 Aug 2025; Good Housekeeping
recruitment; unlikely travellers screened out) and every FTA number P6 prints: 92%; trip types
83/68/49/30/11; $8,052 and +20% YoY; 19% used an advisor and 61% would consider (worth adding: 61% is
*down* from 71% in 2023, which strengthens P6's verdict); lead times 35/31/3/3; tool incidence
81/77/74/63/57/27 and grandparents' 11%; and the advisor battery 60/58/47/45/43 — all eight exact.

Pew (n=3,054 parents of children ≤12, fielded 13–26 May 2025, 42%) is **VERIFIED**, and Pew's own
subhead states P6's point almost verbatim: *"Most parents say managing their child's screen time is a
priority. Fewer than half say it's one of their biggest ones."* P6's §7 is well supported.

Expedia × Luth (5+ hrs in 45 days; 71-day window = 33 inspiration + 38 research; 70,000+ passive
panel; survey n=5,713) **VERIFIED**. Skift/Layla July 2026 **VERIFIED**.

---

## REPRODUCTION APPENDIX — how to re-run the Trends check

```
# 1. bootstrap a cookie
curl -s -c ck.txt -o /dev/null 'https://trends.google.com/trends/?geo=US' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'

# 2. explore -> grab the TIMESERIES widget's request + token
REQ='{"comparisonItem":[{"keyword":"dentist appointment","geo":"US","time":"today 5-y"}],"category":0,"property":""}'
curl -s -b ck.txt -G 'https://trends.google.com/trends/api/explore' \
  --data-urlencode "req=$REQ" --data 'hl=en-US&tz=360' \
  -H 'Referer: https://trends.google.com/' -H 'User-Agent: Mozilla/5.0 …'

# 3. widgetdata/multiline with that request+token -> 261 weekly points
# 4. group by calendar month, mean, rescale peak=100, CV = pstdev/mean
```

Notes for whoever re-runs it: strip the `)]}'` prefix before parsing JSON; without the cookie the
endpoint returns **HTTP 429**; three consecutive pulls of the same term in one session returned an
identical 12-cell row and CV=0.0992, so the series is stable within a day despite Google's
sample-based disclaimer. For a volume axis, issue **one** comparison request with all terms in a
single `comparisonItem` array — that normalises them to a shared maximum and is what P7 is missing.
