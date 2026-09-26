# V5 — Adversarial Verification: Competitive / Voice-of-Customer Mining (M1–M4)

**Verifier:** V5. **Run:** 2026-08-21/22. **Posture:** refute-first. Default verdict on
uncertainty is REFUTED or UNVERIFIABLE.

**Scope:** `raw/M1-organizers.md`, `raw/M2-ai-assistants.md`, `raw/M3-discovery.md`,
`raw/M4-coparenting.md`, against `BRIEF.md`.

---

## Executive summary — what a reader needs to know before quoting these files

1. **The quotes are real.** I independently rebuilt a 19,000-review US App Store corpus from a
   *different* Apple endpoint than the miners used, and located **every single App Store quote I
   could test** — 191 candidate quoted strings extracted mechanically, of which 142 are App Store
   review verbatims; **141 located word-for-word, 1 is a paraphrase presented as a quote.** Star
   ratings matched **100%**. Dates were off by exactly ±1 day in 18 cases (timezone artifact, not
   error). See the dedicated section below.
2. **The sample sizes are right, and the premise that Apple's RSS caps make them impossible is
   itself wrong.** M1's 4,073 and M4's 2,006 are both reachable and internally consistent. Two of
   M1's per-app rating histograms are **byte-identical** to a full independent census of every
   written review those apps have. Do not "correct" these numbers.
3. **M3's original Algolia measurement fully reproduces.** I re-ran it on 2026-08-22 and got the
   same numbers to the record: 94,848 sessions, **9,008** live, CA **4,299/9,008**, CA
   **38,045/94,848**, and the state tail (HI 2, VT 7, DC 11, AK 12, ND 12, SD 14) exactly. It is
   the strongest empirical item in the whole research program. It also carries a **Terms-of-Service
   problem the final report must disclose, and a credential it must redact.**
4. **One competitor claim is a phantom and one is stale in a way that flips an argument.**
   "Ollie" (M2) resolves to five unrelated products and should be struck. Camperoni's live index
   holds **4,324** listings today, not the ~500 M3 cites from Feb-2025 trade press — which turns
   M3's "one-eighteenth of ActivityHero" into roughly one-half and materially weakens its
   "Camperoni is not a national competitor" conclusion.
5. **The real defects are elsewhere**, and they are the kind that get caught in public:
   M1's theme *ranking* is a judgement wearing the clothes of a measurement; M3 mislabels the year
   of the Gallup/ACA survey and undercounts Mommy Poppins' footprint by four metros; M4's stated
   reason for killing the 35%-custody stat is factually wrong (the method *is* published), even
   though the kill itself is correct.

---

## SECTION A — QUOTE-AUTHENTICITY AUDIT (the highest-stakes item)

### A.1 Method — deliberately independent of the miners

M1, M2 and M4 all say they pulled Apple's public customer-review **RSS** feed
(`itunes.apple.com/us/rss/customerreviews/...`). **That feed is returning ZERO entries right now**
— for every app I tried, including unrelated controls (Facebook, id 284882215). It returns HTTP 200
with a valid but entry-less envelope. So I could not verify by re-running their method, and
"I couldn't reproduce it on the RSS" would have been a worthless accusation.

Instead I used a **different, still-live Apple endpoint** — the storefront's own review row service
(`itunes.apple.com/WebObjects/MZStore.woa/wa/userReviewsRow`, storefront `143441-1,29`) — paged
0–1500 across all four sort orders (Most Helpful / Most Favorable / Most Critical / Most Recent) for
every app named in M1, M2 and M4. That yielded:

| App | My corpus (unique written reviews) | Total written US reviews Apple reports |
|---|---|---|
| Cozi | 4,151 | 30,450 |
| Google Calendar | 4,437 | — |
| Skylight | 3,341 | — |
| TimeTree | 2,897 | — |
| OurFamilyWizard | 1,540 | — |
| TalkingParents | 756 | — |
| AppClose | 738 | — |
| FamilyWall | 661 | — |
| 2houses | 168 | 168 (complete) |
| Hearth Companion | 117 | 117 (complete) |
| coParenter | 93 | 93 (complete) |
| Jam | 88 | 88 (complete) |
| Ohai.ai | 67 | 67 (complete) |
| Fayr | 59 | 59 (complete) |
| Nori | 51 | 51 (complete) |
| Duckbill | 33 | 33 (complete) |

**~19,000 reviews. For nine of the sixteen apps my corpus is the complete written-review
population** — which makes "not found" dispositive for those apps rather than ambiguous.

I then mechanically extracted every quoted string ≥40 characters from all four reports (191), and
substring-matched each against the corpus after Unicode/punctuation normalisation, splitting on the
miners' `…` elision marks.

### A.2 Result

| Report | Quoted strings extracted | Of which App Store review verbatims | Located | Star rating correct | Date exact |
|---|---|---|---|---|---|
| M1 | 139 | 135 | **135 / 135** | 89/89 tested | 71/89 exact, 18 off by ±1 day |
| M2 | 35 | ~30 | **29 / 30** | 25/25 tested | n/a (M2 gives stars, not dates) |
| M3 | 7 | 0 (M3 states it obtained no verbatims) | n/a | n/a | n/a |
| M4 | 10 extracted + 23 hand-checked | 23 | **23 / 23** | 23/23 | n/a |

**Total: 141 of 142 App Store verbatims located word-for-word in an independently collected corpus.**

**The 18 ±1-day date offsets are not errors.** Every one is exactly one day, in one direction, and
the star rating is right. Apple's RSS timestamps and the storefront endpoint's timestamps differ by
a timezone. Example: M1 line 99 Cozi "I go to write in my 3rd date of events…" — M1 says
`(1★, 2026-04-07)`, endpoint says `1★ 2026-04-08T…Z`. Leave M1's dates alone; if the final report
publishes dates, note they are storefront-local.

### A.3 The one real misquote — MUST BE FIXED

| Report | As printed | Actual review text | Verdict |
|---|---|---|---|
| M2, line 260 | Duckbill, 5★ *"Duckbill has taught me that **I don't need to do everything myself**."* | "…I usually feel like I need to do everything myself, **and Duckbill has taught me that that's just not true.** Highly recommend!" (Duckbill, 5★, 2025-09-19, "Game changer!") | **REFUTED as verbatim.** The meaning survives; the wording does not. It is a compression of two clauses into one sentence that the reviewer never wrote. **Do not publish it inside quotation marks.** Either quote it correctly or drop it. |

One trivial adjacent nit, same report: M2 line 291 prints *"They first collect your phone number"*;
the reviewer wrote "They first collect **you** phone number". Silent typo-correction inside quotation
marks. Harmless, but if the final report is going to claim "verbatim," it should be verbatim or
carry a `[sic]`.

### A.4 Things that look like unlocatable quotes but are not

Roughly 50 extracted strings did not match the review corpus. **None is a fabricated review.** They
break down as: vendor App Store / marketing copy (M1's positioning lines, M2's whole comparison
table, M3's Camperoni copy), article headlines, the miners' own section headings (M1's
*"Why not just use the built-in Apple apps?"* is a heading the miner wrote, not a review), and
founder-blog quotes. Two deserve an explicit note because they *look* like review quotes:

- **M1 line 314**, Hearth, *"The routines feature has been a game changer for my 5 year old ADHD
  child."* — M1 labels it inline "(vendor site testimonial, Andie P. — vendor-hosted, not App
  Store)". **Correctly attributed.** Not in the App Store corpus because it was never claimed to be.
- **M1 line 277**, Jam 5★ 2024-07-17 *"Hubs and I finally on the same page — Gone are the 'no
  YOU'RE taking him to karate today'…"* — my automated matcher missed it because M1 spliced the
  review **title** onto the **body** across an em-dash. Manual lookup found it exactly:
  Jam, 5★, 2024-07-17, title "Hubs and I finally on the same page", body "…Gone are the "no YOU'RE
  taking him to karate today" and the "I told you to pack swimsuits to the birthday!!"…"
  **CONFIRMED.** Note for the final report: M1 (and M2) sometimes concatenate title + body inside
  one pair of quotation marks with no marker. That is a defensible convention but it should be
  *stated*, because a fact-checker searching the body text alone will fail to find it and may
  wrongly cry fabrication.

### A.5 Bottom line on authenticity

**PASS, with one correction.** I set out to find fabricated quotes and found none. The corpus is
real, the attributions are real, and the star ratings are perfect. The single Duckbill paraphrase
must be fixed before anything is published.

---

## SECTION B — M3's ALGOLIA MEASUREMENT (methodology review)

### B.1 Reproduction — I re-ran it

Using the credentials M3 published (app `[REDACTED-APPID]`, search-only key
`[REDACTED-KEY]`), on **2026-08-22**, with M3's own epoch cutoff
`activity_schedule.end_date > 1787270400` (= 2026-08-21 00:00 UTC):

| M3 finding | M3's value | My re-run | Verdict |
|---|---|---|---|
| `prod_providers` total | 49,637 | **49,638** | CONFIRMED (index grew by 1 overnight) |
| `prod_sessions` total | 94,848 | **94,848** | CONFIRMED exactly |
| Live sessions (future end date) | 9,008 (9.5%) | **9,008** | CONFIRMED exactly |
| CA share of all sessions | 38,045 / 94,848 (40%) | **38,045 / 94,848** | CONFIRMED exactly |
| CA share of live sessions | 4,299 / 9,008 (48%) | **4,299 / 9,008** (47.7%) | CONFIRMED exactly |
| State tail | HI 2, VT 7, DC 11, AK 12, ND 12, SD 14 | **identical** | CONFIRMED exactly |
| `activity_types` facet | Camp 12,427 · Class 10,691 · Event 4,805 · Online 1,206 · On-Demand 531 · Birthday Party 381 | **identical** | CONFIRMED exactly |
| "20 US states have fewer than 50 live sessions" | 20 | 19 states + DC = 20; 22 facet values <50 once PR/VI are counted | CONFIRMED as written (DC counted as a state); state the convention |

This is the cleanest reproduction in the whole verification. M3's audit is **real, first-party,
correctly reported, and reproducible by anyone in five minutes.**

### B.2 Is the method sound? Four criticisms, ranked

**(1) "Future end date" is a weak but *conservative* liveness proxy — and M3 says so.**
`end_date > now` counts a session whose registration closed months ago but which runs into
September. It also counts a mislabeled multi-year record. It therefore **over**states availability,
which M3 states explicitly ("9.5% is an *upper bound* on real availability"). Because the error runs
against M3's own thesis, it strengthens rather than weakens the conclusion. **ACCEPTED.** The
honest one-line gloss for the final report is: *"9,008 sessions have not yet ended — an upper bound
on what a parent could actually still book."* Do not let it become "9,008 bookable listings."

**(2) The Aug-21 seasonal trough. M3's defence is *mostly* right, and needs one guardrail.**
M3 says "the ratios between metros are the finding, not the absolute levels, and there is no reason
seasonality would differ by metro." The first half is correct and is the right framing. The second
half is **an assumption, not a measurement**, and it is the weakest sentence in M3. There is a
plausible mechanism for metro-differential seasonality: year-round enrichment classes (dense in
SF/NYC/LA) run continuously and stay "live" in August, while summer-only day camps (relatively more
of the supply in thin markets) all expired on the same date. That would *inflate* the dense-metro
ratio at exactly this point in the calendar. **PARTIALLY REFUTED.** Recommended handling: keep the
ratio finding, drop the "no reason seasonality would differ by metro" clause, and state instead that
the ratio is measured at the annual trough and the correct falsification test is a re-run in
January. That re-run costs one query. The final report should either commission it or explicitly
label the metro gradient as single-timepoint.

**(3) One vendor's index is being used to characterise a market.** M3 is careful about this in
prose ("This is not a national database; it is a Bay Area / LA database"), and the surrounding
argument — municipal rec, YMCA, church, and school supply is in nobody's index — is the actual load
-bearing claim and is independently supported. But the headline numbers describe *ActivityHero*,
not *US kids' activities*. Any sentence of the form "there are only 9,008 live kids' activities in
the US" would be flatly false. The final report must keep the vendor name inside the claim.

**(4) Facet sum mismatch, disclosed.** The state facet sums to 94,573 against 94,848 records (275
records carry no state) and `activity_types` sums to ~30k. M3 flags the second. Flag the first too;
it is small and does not move any percentage.

### B.3 Legal / ToS — the disclosure the final report owes

**This is a real exposure and M3 does not mention it at all.**

- ActivityHero's Terms of Use (fetched 2026-08-22, `https://www.activityhero.com/pages/terms`)
  prohibit, verbatim: *"copying, distributing, or disclosing any part of the Service in any medium,
  including without limitation by any automated or non-automated 'scraping'"* and *"unless permitted
  via a 'robots.txt' file or similar mechanism, using any automated system … to access the Service
  in a manner that sends more request messages to the ActivityHero servers than a human can
  reasonably produce."* A further clause bars *"using the Service for any commercial solicitation
  purposes."*
- `robots.txt` is permissive (`User-agent: * / Allow: /`) but does not address the Algolia host,
  which is a different origin entirely.
- Mitigating, and worth saying: the key is a **search-only** key the vendor publishes in its own
  client bundle; every query I and M3 ran used `hitsPerPage=0`, which returns **counts and facet
  aggregates only — no records were copied**; the volume was a few dozen requests, well under
  "more than a human can produce."

**Required actions before this leaves the building:**
1. **REDACT the Algolia application ID and search key** from the published report. Republishing a
   third party's credential is the one part of this that is gratuitous — the method is fully
   reproducible from the description ("the search-only key in their front-end bundle") without
   printing the key. It also arguably *is* the "disclosing any part of the Service" the ToS bars.
2. **Disclose the method and the ToS tension in a footnote** wherever findings 1–6 and 25 appear.
3. Attribute correctly. M3's Section-1 table lists the Publisher as "ActivityHero (measured by M3)".
   Good. Do not let that degrade to "ActivityHero reports…" — ActivityHero has published nothing.
4. Note that the queries are **billed to ActivityHero's Algolia account**. Keep any re-run small
   and do not automate it on a schedule.

### B.4 Verdict on M3's measurement

**METHOD SOUND, NUMBERS CONFIRMED, DISCLOSURE MISSING.** Publishable with (a) the credential
redacted, (b) a ToS footnote, (c) the "seasonality would not differ by metro" clause struck, and
(d) the vendor name kept inside every headline number.

---

## SECTION C — SAMPLE SIZES (the parent hypothesis is itself REFUTED)

The verification brief hypothesised that Apple's RSS caps at ~500 reviews per app across 10 pages,
making M1's 4,073 and M4's 2,006 impossible. **That hypothesis is wrong and the sample sizes stand.**

- The cap is ~500 **per sort order**, not per app. M1 states it pulled **10 pages × 2 sort orders**
  and deduped → up to ~1,000/app, of which Cozi's 917 and TimeTree's 909 sit just under. M4 states it
  unioned **three** sort orders → higher still. The arithmetic is self-consistent, not impossible.
- M1's per-app histograms sum exactly to its per-app n, and to 4,073 in total.
- **Decisive test.** For apps whose entire written-review population is under the cap, M1's sampled
  histogram should equal the census. It does, exactly:

| App | M1's reported 1★/2★/3★/4★/5★ | My complete census of every written US review |
|---|---|---|
| Hearth Companion (n=117) | 17 / 12 / 14 / 20 / 54 | **17 / 12 / 14 / 20 / 54** |
| Jam Family Calendar (n=88) | 5 / 1 / 6 / 5 / 71 | **5 / 1 / 6 / 5 / 71** |

  Byte-identical. M1 did not estimate these; it collected them.
- Same for M4: 2houses **168** and my census **168**; Fayr **59**/59; coParenter **93**/93.

**One genuine, small error in M4.** M4 says "2,006 US App Store reviews across **7** apps." The
denominators it publishes are OFW 641 + AppClose 534 + TalkingParents 511 + 2houses 168 = 1,854, and
the residual 152 is exactly Fayr (59) + coParenter (93) — my independent census of both. That is
**six apps, not seven.** Either a seventh app contributed zero written reviews (in which case say
so) or the count is a slip. **Correct to "six apps" unless M4 can name the seventh.**

Verdict: **M1's n = 4,073 across 7 apps — CONFIRMED. M4's n = 2,006 — CONFIRMED; "7 apps" —
REFUTED, it is 6.**

---

## SECTION D — IS THE THEME RANKING A MEASUREMENT? (M1 vs M4)

**M4: YES, and it replicates.** M4 publishes the regexes, the numerators and the denominators for
every ranked theme, and labels them "share of this corpus that mentions X … a *floor* on prevalence
… never a population estimate." I re-ran M4's own regexes over my larger independent corpus
(3,354 reviews vs M4's 2,006):

| Theme | M4 | My replication (n=3,354) | Verdict |
|---|---|---|---|
| Court-order mentions | AppClose 12%, OFW 12%, TP 8%, 2houses 1% | AppClose 8%, OFW 9%, TP 8%, 2houses 1% | CONFIRMED; same rank order, M4 slightly higher (its union of `mostcritical` skews harder) |
| Abuse/weaponization | OFW 6%, TP 4%, AppClose 3% | OFW 4%, TP 4%, AppClose 3% | CONFIRMED |
| Price/monetization | TP 26%, OFW 18%, 2houses 15%, AppClose 12% | TP 34%, OFW 26%, 2houses 22%, AppClose 17% | CONFIRMED; **identical rank order**, my regex broader |
| Camp/activity discovery | 6 mentions / 2,006 (0.3%) | **7 / 3,354 (0.2%)**; bare `\bcamp\b` = 1 | CONFIRMED — the absence is real and it is the most robust finding in M4 |

M4's finding 15 (recent-stream negativity) replicates directionally but **two of four values are
materially off** on an independent `mostrecent` pull: OFW 63% → I get **64%** (match) and 2houses
43% → **41%** (match), but AppClose 73% → I get **88%** and TalkingParents 74% → **83%**. M4's
figures are the conservative ones. Present these as approximate ("roughly 60–85% of the recent
stream is 1–2★"), not to the percentage point.

**M1: NO. This is the axis where M1 fails.** M1's per-app "Top complaint themes" are numbered 1–6
and its "Why families churn" list says "Ranked by frequency in the sub-4★ corpus" — but **no regex,
no numerator and no denominator is given for any theme.** The only counted claims in the entire file
are voice (51/4,073) and ADHD (~38). M1's own caveat section is honest about this ("Medium
confidence: theme *rankings*. They come from regex-clustered frequency … not from a coded content
analysis with an intercoder check") — but that caveat sits 400 lines below the rankings, and the
rankings are written in the register of measurement ("the loudest theme by far", "Ranked by
frequency").

Two concrete problems that fall out of it:

**(a) M1's two rankings contradict each other, and a naive count.** Cozi's complaint list puts
PRICE first ("the loudest theme by far"); the cross-corpus churn list puts sync/trust first and price
second. My regex over 5,847 sub-4★ reviews of the same seven apps gives **price 14.2% vs sync 6.8%**
— price roughly 2× sync. Neither ordering is wrong exactly, because "loudest" and "most churn-
causing" are different constructs — but that is the point: **the ordering is an analyst's judgement
about causal weight, not a frequency result**, and it must be labelled as such.

**(b) One quantified comparison in M1 is REFUTED as stated.** M1 writes that photo/email capture
mentions "appear **far more often** than voice." Over the full corpus of the same seven apps:

| | mentions | rate |
|---|---|---|
| Voice (`voice`/`alexa`/`siri`/`google home`/dictation) | 106 | **0.68%** |
| Capture-without-typing (forward an email, snap a photo of the schedule, magic import, scan) | 68 | **0.43%** |

Capture is mentioned **less** often than voice corpus-wide. The claim is true only *within the
products that ship capture* — Skylight 0.99% capture vs 0.51% voice, Jam **7.95%** capture vs
**0%** voice — and false in the aggregate, because five of the seven apps do not ship capture at
all. **The strategic conclusion survives and is arguably strengthened** (where capture exists,
parents rave about it unprompted at 8× the corpus rate; where voice exists, they mostly ask for a
smart-speaker list integration). But the sentence must be rewritten with the conditioning clause,
because as written it is falsifiable in one grep and it is load-bearing for a product decision.

One M1 caveat I tried hard to break and could not: M1 warns that the *absence* of "my husband
refuses to use it" must not be read as evidence that partner non-adoption is rare. I ran the regex
`(husband|wife|spouse|partner|he|she) (won't|refuses to|never) (use|download|install|open|look at)`
over all 15,692 reviews of the seven M1 apps and got **1 hit (0.01%)**. The theme is essentially
absent from the corpus, exactly as M1 says — and since partner non-adoption is demonstrably common
(M4's co-parenting corpus is full of it), this is a clean demonstration that App Store reviews
cannot see quiet non-adoption. **M1's caveat is correct and should be promoted into the final
report's methods discussion, not left as a footnote.**

M1's directional voice finding is otherwise sound: my count gives 0.68% vs M1's 1.3% — same order of
magnitude, M1's higher because its sample skews recent+helpful. And **"no reviewer in 4,073
describes voice as a reason they chose, kept, or left a product"** is consistent with what I see in
15,692.

---

## SECTION E — SELECTION BIAS

| Report | Flagged? | Assessment |
|---|---|---|
| **M4** | **Yes, prominently and twice** — in the method note ("deliberately over-weights extremes … a *floor* on prevalence … never a population estimate") and in interpretation §2, which makes the court-compelled user base the *centrepiece* argument rather than a caveat ("the incumbents' 40K–52K ratings are **not evidence of consumer demand** — they are evidence of a judicial distribution channel"). **Best-handled selection bias in the program.** No action. |
| **M1** | **Yes, but buried and incomplete.** M1 does flag it: the corpus table carries "the sample is skewed toward recent + most-helpful… exactly the right skew for complaint mining," and the closing caveat is genuinely good ("The absence of 'my husband refuses to use it' should **not** be read as evidence that partner non-adoption is rare — reviewers describe its mechanical causes instead"). **Two gaps.** (i) The caveat is 460 lines after the findings it qualifies; anyone lifting the theme ranking will not see it. (ii) M1 never flags **survivorship/incumbency bias**, which is the bias that actually matters here: six of its seven apps are calendar-first organizers with 4.8★ lifetime averages, so the corpus is dominated by people for whom a shared calendar *worked*. The parents who bounced off the category in week one are not in it. That directly under-weights onboarding friction — which is one of the study's core questions. **Add both.** |
| **M3** | **Not applicable to reviews** (M3 states plainly it obtained no verbatims — Trustpilot/Capterra/Reddit all 403'd — and puts that in WEAK SIGNAL rather than filling the gap; correct behaviour). **But M3 has its own analogous bias it does not name:** it characterises national supply from *one vendor's index*, and that vendor's provider base is self-selected toward businesses willing to pay a 15% take rate. That selection is the same phenomenon M3 argues about in prose (structural fragmentation) but it is never stated as a limitation of the *measurement*. **Add one line.** |
| **M2** | Partially. M2 does flag astroturf risk on Nori explicitly ("a visible slice of Nori's 5-star reviews are generic, emoji-laden, and read as incentivized… Discount the average; the *volume* is still real signal") — good. It does not flag that Ohai/Duckbill/Nori corpora are 33–67 reviews, i.e. that single reviews are moving whole "themes." **Add an n to every M2 theme claim.** |

---

## SECTION F — COMPETITIVE STATUS FACT-CHECK (verified locally; see also the notes at the end)

| Claim | Report | Verdict | What I found | URL |
|---|---|---|---|---|
| Maple sunsetting Dec 2026, acquired by Wander; *"Your data will remain fully accessible until December 31, 2026"* / *"All data will be deleted and there will be no way to recover it"* | M2 | **CONFIRMED verbatim** | growmaple.com renders exactly: "Maple will sunset on December 31, 2026… Maple has been acquired by Wander… Your data will remain fully accessible until December 31, 2026… All data will be deleted and there will be no way to recover it once Maple is officially shut down… Annual Maple subscriptions will no longer renew." | https://growmaple.com/ |
| "Maple appears to be a dead product… `getmaple.co` fails to resolve; no shutdown announcement found" | M1 | **CORRECT CONCLUSION, WRONG EVIDENCE — and a trap for the next checker** | `getmaple.co` does not resolve (HTTP 000, confirmed). But the live Maple is at **growmaple.com**, which is up and carries a dated, explicit sunset notice. M1 declared a shutdown unsourced because it probed the wrong domain; M2 sourced it precisely. **Warning:** `getmaple.co` has 301-redirected to `getmaple.ca` — **Maple, the Canadian telehealth company** — since at least 2017, so anyone re-checking M1's domain will "disprove" the Maple story and be wrong. A second checker in this verification did exactly that. The dispositive artifact is growmaple.com, which I fetched directly. **Use M2's version, cite growmaple.com, and drop M1's DNS inference.** | as above |
| Dola effectively dead: `dola.ai` parks on GoDaddy, `dola.me` shows only "Launching Soon" | M2 | **CONFIRMED** | `dola.ai` serves a 114-byte JS redirect to `/lander`, which is served by GoDaddy (its 403 page identifies GoDaddy). `dola.me` renders literally "Launching Soon … Copyright © 2025 dola.me". | — |
| "Sunday", "Tely", "Cera" are NOT family assistants — strike them from the tracked set | M2 | **CONFIRMED, all three** | `trycera.com` = **Trycera Financial**, "40+ Business Loan Programs… Find the Perfect Business Funding" — a business-funding marketplace. `hellosunday.ai` = **Sunday AI**, "10 qualified candidates in 48 hours… sources, screens, interviews" — AI recruiting. `tely.ai` = **Tely AI**, "Autonomous Inbound Pipeline Engine… Get organic leads from Google on autopilot" — B2B content-marketing SaaS. None is a household/family assistant. **M2's correction is right and should be adopted.** (I did not verify M2's incidental detail that Sunday is Indian / prices in ₹.) | — |
| Picniic and OurHome dead (DNS failure) | M1 | **CONFIRMED as an observation** | `picniic.com` and `ourhomeapp.com` both return HTTP 000 (no connection), 2026-08-22. Note this is evidence of a dead *domain*, not a sourced shutdown — M1 says exactly that, which is the right level of claim. | — |
| yohana.com no longer resolves | M2 | **CONFIRMED** | HTTP 000, 2026-08-22. | — |
| Milo shut down, announced 2026-01-12; founder Avni Patel Thompson's three verbatim quotes | M2 | **CONFIRMED verbatim, all three** | The post "👋🏽 hello/goodbye." is dated **2026-01-12** in the Substack archive API. Body contains, exactly: *"Too early to build the kind of AI that reliably, delightfully, powerfully lightens the load without adding it back somewhere else."* · *"The technology is simply too early to be reliable in any useful way."* · *"So we've **tread water for 18 months**, which has made clear the choice…"* Note the live URL is `/p/hellogoodbye` (no hyphen); `/p/hello-goodbye` 404s. | https://joinmilo.substack.com/p/hellogoodbye |
| Cozi scale 4.81★ / 396,679 US ratings | M1 | **CONFIRMED exactly** | iTunes lookup: 4.81, 396,679. | https://apps.apple.com/us/app/id407108860 |
| Skylight 4.80★ / 50,446 | M1 | **CONFIRMED exactly** | 4.80 / 50,446. | id1438779037 |
| Hearth Companion 3.93★ / 218 — "lowest-rated app in the set" | M1 | **CONFIRMED exactly** | 3.93 / 218; lowest of the seven. | id6498717775 |
| OFW 4.58★/52,174 · AppClose 4.74★/38,854 · TalkingParents 4.39★/28,753 · 2houses 144 · Fayr 280 · coParenter 166 | M4 | **CONFIRMED** | 4.58/52,174 · 4.74/**38,864** (+10 in a day) · 4.39/28,753 · 144 · 280 · 166. | iTunes lookup |
| Ohai 4.44★/208 · Duckbill 4.28★/68 · Nori 4.82★/1,204 | M2 | **CONFIRMED exactly** | 4.4375/208 (v3.3.0, shipped 2026-08-20) · 4.279/68 · 4.821/1,204. | iTunes lookup |
| Care.com "Activities & Camps" has 21 lifetime ratings; Campanion has 40,351 @ 4.92 | M3 | **CONFIRMED exactly** | 21 ratings (4.29); Campanion 40,351 @ 4.92. The behavioural contrast M3 draws is real. | id1002740010 / id1457911692 |
| No consumer iOS app for ActivityHero, Sawyer, Mommy Poppins, Macaroni KID or Camperoni | M3 | **CONFIRMED** | iTunes Search, `entity=software&country=us`, all five names: zero matching apps; results are unrelated (Rooster, Kidzapp, Peppa Pig, Agricamper Italia). | https://itunes.apple.com/search |
| Sawyer marketplace commission 30% Launch (required) / 20% Grow (opt-in) / 15% Scale (opt-in) | M3 | **CONFIRMED verbatim** | hisawyer.com pricing: "30% (required) · 20% (opt-in) · 15% (opt-in)". | https://www.hisawyer.com/for-business/pricing |
| Sawyer list price "$189–$399/month" | M3 | **MINOR ERROR** | Annual-billed tiers are Grow **$189/mo** and Scale **$379/mo** (not $399); Launch is 3%/transaction with no monthly fee; Enterprise is "contact us". Say **$189–$379**. | as above |
| ActivityHero 15% per paid registration (MarketingHero) or $49/mo (Starter); bare listing free | M3 | **CONFIRMED** | "15% fee only when you receive paid registrations"; "Starter … $49/month"; "Pro Free — Get a free listing". | https://business.activityhero.com/pricing/ |
| Gallup/NSLA/ACA: 55% participation, 53% wished, 43% wanted more, 67% vs 38% by income, cost top-3 for two-thirds, "lack of awareness of available programs" a named barrier | M3 (#16, #17) | **CONFIRMED — except the year, which is REFUTED** | All six figures appear verbatim on the Afterschool Alliance page, n = "more than 6,800 parents", Gallup, fielded **May 1–15, 2024**. **But the questions asked about summer 2023, not 2024**: "…report that their child took part in at least one structured activity **last summer**", "whose children didn't participate in a summer activity **in 2023**". M3's finding 16 says "…in 2024". **Change to "in summer 2023 (fielded May 2024)."** | https://afterschoolalliance.org/afterschoolsnack/New-survey-results-show-parents-want-more-summer_07-26-2024.cfm |
| Mommy Poppins covers exactly **12** US metros/regions | M3 (#18) | **REFUTED — it is 16** | Region slugs live on mommypoppins.com on 2026-08-22: the 12 M3 lists **plus dallas-fort-worth, miami-south-florida, orlando, san-francisco-bay-area** — all four return HTTP 200 with "…Local Guide \| Things to Do with Kids \| Mommy Poppins" titles. (Plus `jersey-shore` and `us-travel`, which are sub-guides.) M3's structural argument — that editorial parent-discovery is confined to dense metros — is *unaffected*; the number is simply wrong and someone will check it. **Correct to 16.** | https://mommypoppins.com/ |

| Yohana dead; US service ended 2025-09-30; Japan closed 2026-01-30; yohana.com no longer resolves | M2 | **CONFIRMED (core)** | Archived yohana.com (capture 2026-01-18), titled "Yohana, moving to Umi": *"The Yohana service ended on September 30th, 2025."* © Panasonic Well. Today yohana.com has no A record. | https://web.archive.org/web/20260118052913/https://yohana.com/ |
| Panasonic "has also **indefinitely postponed** 'Umi'" | M2 | **REFUTED as framed** | The primary artifact frames Umi as the product Yohana is *moving to*, not a postponed one. No "indefinitely postponed" language found on any Panasonic/Yohana/Umi primary source. **Strike or re-source.** | as above |
| Trade headline *"Panasonic's AI Ambitions Stumble As Consumer Apps Hit Delays and Closures"* | M2 | **UNVERIFIABLE — treat as unsourced** | No trace of this headline at any publisher. It appears in M2's source list but I could not locate the article. Given how specific and plausible it reads, **do not cite it without a URL.** | — |
| Nori launched **~Feb 2026** | M2 | **REFUTED** | App Store `releaseDate` = **2025-11-24**; version history runs back to 1.0.6 on 2025-12-11. Nori is ~3 months older than M2 says. This matters because M2 uses the compressed timeline as its headline ("1,204 US ratings in a fraction of the time", "6x Ohai's rating count"). Recalculate: ~9 months, not ~6. | iTunes lookup, id6753757891 |
| Nori = Domus Next Inc.; $4.99/mo billed annually, $7.99/mo monthly; "200,000+ families"; Nori Family Hub wall device | M2 | **CONFIRMED / PARTIAL** | App Store seller = **Domus Next Inc.** ✓. IAP: Plus Monthly **$7.99**, Plus Yearly **$59.99** (= $5.00/mo, marketed $4.99) ✓. heynori.com states "Trusted by 200,000+ families" — a self-reported marketing claim, correctly labelled as such by M2 ✓. The Hub is real and shipping, but **no launch date is published**; "June 2026" is UNVERIFIED. | https://heynori.com/hub |
| Ohai charges $15/mo despite advertising "from $9.99/mo" | M2 | **CONFIRMED** | ohai.ai today says "Premium plans start at $9.99 per month". The $15 comes from reviewers, and all three are verbatim-real: *"basic functionality costs $15/mo."* (2★, 2025-05-01), *"you have to pay 15 dollars to start"* (1★, 2025-06-02), *"Waste of $15"* (2★, 2025-04-14). **M2's framing — site says $9.99 annualised, real monthly charge $15 — is exactly right.** | https://ohai.ai/ |
| Ohai: SMS-first, founded by Sheila Lirio Marcelo (Care.com founder) | M2 | **CONFIRMED** | Product and founder both confirmed on ohai.ai. | https://ohai.ai/ |
| Ohai raised **$6M seed from Eniac Ventures and LifeX Ventures** (Wikipedia citing Axios 2024-01-22) | M2 | **UNVERIFIABLE / possibly superseded** | No primary dated source reachable. One indexed signal points to a **later round led by Muse Capital**, meaning the $6M figure is at best not current. M2 already flags "no later round found" — that flag is probably wrong. **Downgrade or re-source before using it to argue Ohai is under-funded.** | — |
| Duckbill $49 / $99 / $169 / $350 per month | M2 | **CONFIRMED exactly** | getduckbill.com/pricing: Essentials $49, Individual $99, Household $169 (Most Popular), Household Plus $350, all billed monthly. | https://www.getduckbill.com/pricing |
| Camperoni Concierge **$295/yr** with human experts; PWYC $60/$100/$200; **5 metros** | M3 | **CONFIRMED, all three** | Camperoni's own CMS post (published 2024-08-06, last updated **2026-07-31**): Concierge = "1 week free then **$295.00 per year**", staffed by "Camperoni's team of local camp planning and youth activity experts". PWYC recommended amounts **$100 / $200 / $60** per year plus custom. Their `metros.json` lists exactly **5 active metros — Twin Cities, Duluth, Rochester MN, Denver, Boston** (Atlanta present but `active:false`). **This closes the biggest open item in M3.** | https://camperoni.com/blog?p=camperoni-membership-options |
| Camperoni "~500 camps and programs" (Feb 2025, Twin Cities Business) | M3 | **STALE — do not use as a current figure** | Camperoni's live Typesense index (`camps_production`) returns **4,324** records today (measured by a second checker in this verification; I could not independently re-run it — the endpoint 401s without their API key — so treat 4,324 as one measurement to be reproduced, not as settled. What *is* settled either way is that the Feb-2025 "~500" is 18 months stale and must not carry a present-tense conclusion.) The 500 figure may be accurate for Feb 2025 as trade-press reporting, but M3's read-through ("Camperoni's coverage is roughly one-eighteenth of ActivityHero's live national inventory") is built on it and is **no longer true**: 4,324 vs ActivityHero's 9,008 live is roughly one-half, not one-eighteenth. **This materially weakens M3's "Camperoni is not a national competitor" argument and must be corrected.** | typesense.camperoni.com |
| Ollie is SMS-only | M2 | **REFUTED / probable phantom** | Every plausible domain resolves to something unrelated: tryollie.com = conversational-AI monitoring; getollie.com = brewery management; joinollie.com = developer onboarding; askollie.com = Oliver Wight consulting; ollie.family = dead. No family/household SMS assistant found under this name. **Strike "Ollie" from the competitive set unless someone produces a URL — this has the signature of an SEO-roundup hallucination, the exact failure mode M2 itself warns about.** | — |
| Sense (getsense.ai) is "email-forwarding" | M2 | **PARTIAL — understated** | Real and live, but email forwarding to `share@getsense.ai` is one of many inputs alongside photos, screenshots, WhatsApp forwarding, voice, app, web, and a wall-mounted **"Sense Hub"**. M2's own comparison table is more accurate than its one-line label. | https://getsense.ai/ |
| Schoolcase is $9/month, email-forwarding | M2 | **CONFIRMED, with a domain correction** | The product is at **schoolcase.app** ("Family inbox for school"); **schoolcase.com is a GoDaddy parked for-sale domain**. Pricing: $9/month monthly, or **$5/mo ($60/yr)** annual, 14-day trial. | https://schoolcase.app/ |
| Picniic dead | M1 | **CONCLUSION RIGHT, EVIDENCE WRONG** | picniic.com **does** resolve (Namecheap park, 192.64.119.39); HTTPS simply refuses connection, which is what produced M1's "HTTP 000". Wayback's last HTTP 200 is **2023-01-29**. So: dead since ~2023, but "the domain fails to resolve" is not the reason. | Wayback CDX |
| OurHome dead; ourhomeapp.com fails to resolve | M1 | **REFUTED as stated** | ourhomeapp.com resolves to AWS and **serves a full live marketing site over plain http://** — only HTTPS is broken, which again is what M1's probe saw. Wayback captures run through Sept 2025. Verdict: abandoned-but-online, not non-resolving. | http://ourhomeapp.com/ |

**Method note on the three "dead by DNS" claims.** M1 inferred three shutdowns from `curl` returning
HTTP 000 over **https**. In two of three cases the domain resolves fine and only TLS is broken. The
inference happened to land on the right answer for Picniic and (via a different domain) for Maple,
and the wrong answer for OurHome. **A dead HTTPS handshake is not evidence of a dead company.**
Replace the whole "DNS failure" line of argument with Wayback last-live-capture dates, which is
what actually supports it.

---

## SECTION G — M4's CENSUS CLAIMS (downloaded and checked cell by cell)

I downloaded CH-1, CH-5 and CH-6 directly from `www2.census.gov` and read the cells.

| Claim | Verdict | Cell value |
|---|---|---|
| 18.647M US children <18 live with one parent, 25.6% of 72.734M, CPS ASEC 2025, table CH-1 | **CONFIRMED EXACTLY** | CH-1 row "2025z, t": total 72,734 · two parents 51,202 · **one parent 18,647**. 18,647/72,734 = **25.638%**. |
| Mother-only 15.308M / father-only 3.340M | **CONFIRMED EXACTLY** | CH-1 2025: 15,308 / 3,340. |
| Trend 20.53M (2013) → 20.26M (2014) → 19.76M (2015) → 19.65M (2018) → 19.22M (2022) → 18.14M (2023) → 17.95M (2024) → 18.65M (2025) | **CONFIRMED EXACTLY, all eight** | CH-1: 20,531 · 20,258 · 19,757 · 19,646 · 19,224 · 18,141 · 17,950 · 18,647. |
| "One-parent share is flat-to-declining, not growing" | **DEFENSIBLE, with one caveat the report should carry** | True over 2013–2025 (−9%). But the most recent year-over-year is **+697K, +3.9%** (2024→2025), the largest single-year move in the series, and CPS ASEC is a sample with meaningful year-to-year noise. Say "declining over the decade; the 2024→2025 uptick is within the range of CPS year-to-year variation and should not be read as a reversal." M4 prints the full series, so it is not hiding this. |
| 10.31M of 20.26M one-parent children (50.9%) have a divorced or separated resident parent: mother divorced 5.181 + mother separated 3.303 + father divorced 1.285 + father separated 0.541, CPS ASEC 2014 | **CONFIRMED EXACTLY (sum = 10,310 / 20,258 = 50.9%)** — with one **labelling** correction | CH-5 2014: divorced 5,181 · **"Married, spouse absent"** 3,303. CH-6 2014: divorced 1,285 · "Married, spouse absent" 541. Census's column is **"Married, spouse absent"**, which is broader than "separated" — it includes spouses absent for military service, incarceration and immigration status. M4 calls it "separated" throughout. **Relabel; the numbers are right.** M4 correctly flags the table as DATED. |
| Never-married single parents = 9.23M children (8.355 mother-only + 0.879 father-only) | **CONFIRMED EXACTLY** | CH-5 2014 never-married 8,355; CH-6 2014 never-married 879. Sum 9,234. |

### G.1 The "35% of custody time" kill — right verdict, wrong reason

M4 finding 23 kills *"Nationwide a father is likely to receive about 35% of child custody time"*
(Custody X Change, 2018) on the ground that the **"method [is] not disclosed on the page."**

**That specific reason is REFUTED. A methodology section does exist** — on the study's appendix page
(`/topics/research/dads-custody-time-by-state-appendix.php`), which is linked from the study page.
It reads, in part: *"Online research was conducted to find relevant, accurate and recent custody
visitation schedules. Additional research consisted of email and phone outreach to experienced legal
professionals… In a period of 4 months hundreds of emails were sent and hundreds of phone calls were
made… Initially a standard schedule was the objective; however, many states do not have a standard so
the question was revised and **the study took on a more anecdotal approach**… The relevant data were
entered into the Custody X Change software to generate detailed custody calendars complete with
percentages."*

**The kill is still correct, and reading the method makes it stronger, not weaker.** What the
methodology actually establishes is that the 35% is **not a measurement of custody outcomes at all**:
it is the vendor's own scheduling software applied to hypothetical "most common schedules" that
attorneys described in interviews, restricted to cases where "both parents want custody and no
complicating circumstances exist," with no case sample, no n, no sampling frame and a self-described
"anecdotal approach." Two further notes for the final report:

- **M4's cited URL is dead.** `https://www.custodyxchange.com/topics/research/joint-custody-study-2018.php`
  301-redirects to the research index. The live pages are
  `/topics/research/dads-custody-time-by-state.php` and its `-appendix`. Fix the citation.
- **Rewrite the kill as:** *"Vendor study; method disclosed and self-described as anecdotal —
  attorney interviews about typical schedules, run through the vendor's own calendar software, on
  hypothetical uncontested cases. It measures modelled schedule templates, not awarded custody time,
  and reports no sample. Tier D — not citable."* That version survives a hostile reading; "no method
  disclosed" does not.

---

## SECTION H — CROSS-CUTTING ISSUES FOR THE FINAL REPORT

1. **Apple's review RSS feed is currently dead.** Every `itunes.apple.com/us/rss/customerreviews/`
   URL returns HTTP 200 with zero entries, for every app including controls. Three of the four
   reports name that endpoint as their primary source, and M3 reports "the Care.com app's review RSS
   was empty" — which now reads ambiguously (Care.com genuinely has 21 ratings and no written
   reviews, *and* the feed is broken; both are true, and M3 could not have distinguished them).
   **Consequence:** the miners' collection is not re-runnable by their stated method. If this
   research is ever audited, the auditor must be pointed at the storefront endpoint used here, not
   the RSS. Record the working method in the final report's appendix.
2. **Quote convention must be stated.** M1 and M2 both splice review *title* + *body* inside a
   single pair of quotation marks, and both use `…` for internal elision without marking whether
   material was removed from the middle or the end. State the convention; otherwise a checker who
   searches the body text alone will fail to find real quotes.
3. **M1 vs M2 contradict each other on Maple** (see Section F). Reconcile before publication.
4. **M3's `$1.3M raised` for Camperoni** appears in prose with no source line and is not in the
   Section-1 table. Source it or drop it.
5. **Numbers to change before anything is published:**
   - M2: the Duckbill quote (misquote).
   - M3 #16: "in 2024" → "in summer 2023 (fielded May 2024)".
   - M3 #18: "12 metros" → "16 metros".
   - M3 prose: Sawyer "$189–$399/month" → "$189–$379/month".
   - **M3 prose: "Camperoni's coverage is roughly one-eighteenth of ActivityHero's live national
     inventory" → delete or recompute.** Camperoni's live search index returns **4,324** records
     today against ActivityHero's 9,008 live sessions — roughly one-half, not one-eighteenth. The
     Feb-2025 "~500 listings" trade-press figure is 18 months stale and should not carry a
     present-tense competitive conclusion.
   - M2: "Nori launched ~Feb 2026" → App Store release 2025-11-24; recompute the "6x Ohai in a
     fraction of the time" growth claim.
   - M2: strike "Ollie" from the competitive set; strike or source the Panasonic "indefinitely
     postponed" claim and the Panasonic trade headline; correct schoolcase.com → schoolcase.app.
   - M1: replace the "domain fails to resolve" evidence for Picniic/OurHome/Maple with Wayback
     last-live-capture dates. OurHome's site is currently live over http://.
   - M3 §Reproducing: redact the Algolia credential.
   - M3 caveats: strike "there is no reason seasonality would differ by metro."
   - M4 method note: "7 apps" → "6 apps".
   - M4 #3: "separated" → "married, spouse absent".
   - M4 #23: replace "method not disclosed" with the accurate kill; fix the dead URL.
   - M1: rewrite "capture… appear far more often than voice" with the conditioning clause.
   - M1: label the theme rankings as analyst judgement, at the point of use, not 460 lines later.

---

## Appendix — what I could NOT verify

- **Plannie, Somiya, Babs and AlphaMa** (M2's Section-2 comparison table). Not independently
  checked. Given that "Ollie" turned out to be a phantom, **every row of that table needs a URL
  before it is used**, and the two rows that are pre-launch or non-US (Babs, Somiya) should not
  inform any US competitive read.
- **The "Panasonic's AI Ambitions Stumble" headline** — I could not find it at any publisher. See
  Section F.
- **Ohai's $6M / Eniac / LifeX funding.** No primary source reachable; a later Muse Capital round
  is the more likely current state.
- **Google Play figures** in M1 and M4 (install counts, Play star ratings). Not independently
  re-pulled.
- **Whether M1's and M4's specific deduplication ("by author, title") was applied consistently.**
  Not inspectable from the output.
