# S4 — RED TEAM

Adversarial review of S0, S1, S2 and the data layer. Compiled 2026-08-22.
Reads: `BRIEF.md` (three corrections blocks), `raw/S0`, `raw/S1`, `raw/S2`, `raw/V1–V7`,
`raw/P4`, `raw/P5`, `raw/P6`, `raw/M3`, `raw/M5`, `data/README.md`, `data/job_quadrants.csv`,
`data/activity_supply_by_metro.csv`.

**Posture.** I am not scoring polish. I am looking for the argument that would make the founder
regret acting on this report. Where the program is right, I say so and move on — a red team that
objects to everything is worthless. Three things below I believe are load-bearing errors; the rest
are calibration.

**Headline:** the report's central quantitative claim (17–18:1 shallow-to-deep) survives arithmetic
but not interpretation, and the interpretation is what the recommendations rest on. Two of the three
top recommendations (capture, the forwarding address) are aimed at jobs the corpus's own evidence
says are already served free or unmeasured for adoption. The watchlist recommendation is the
strongest in the report and is still resting on an August snapshot and a killed source.

---

## 1. THE CENTRAL CLAIM — the ratio is arithmetically right and substantively hollow

### 1.1 One row is the finding

`data/README.md` §C states it plainly and the report never carries it forward: **weekly sports
logistics alone is 200 of the corrected 264.25 shallow objects.** Run the sensitivity the report
does not:

| Basis | Shallow | Deep | Ratio |
|---|---|---|---|
| As published (Q1's convention) | 286.25 | 15.94 | 18.0 : 1 |
| Corrected (2 unsourced rows dropped) | 264.25 | 15.94 | 16.6 : 1 |
| **Minus weekly sports logistics** | **64.25** | 15.94 | **4.0 : 1** |
| Minus sports logistics + weekend outings (P6: near-zero WTP, free incumbents) | 25.25 | 15.94 | **1.6 : 1** |
| Camp counted as 1 annual cycle instead of 7.5 sub-bookings | — | 9.44 | 28 : 1 (published) |

The headline moves by a factor of eleven depending on one analyst-defined row and one convention
choice. S2 §2.3 tests only the *smallest* sensitivity (dropping permission slips and birthday
parties, 280→250) and reports "the ratio survives." That is the sensitivity that could not have
changed the answer. The one that could was not run.

### 1.2 The 200 row is not a capture job at all

S0's own definition: *"N counts distinct actions the parent must take… **Attending is a step.**"*
So the 200 events are **attendances**, not planning objects. A parent does not capture 200 soccer
practices; they receive one season schedule (TeamSnap, an ICS feed, a paper roster) and enter it
**once per season** — which the report counts separately as ~5 registration episodes. The product
cannot reduce attendance, and a one-gesture capture surface fires roughly **once** against this row,
not 200 times.

Strip that row and the "volume lives in Q2" thesis reduces to P5's own bottom line: **~23
appointment-and-school episodes per year** (V2-corrected, band 20–26) against ~16 deep objects.
**That is 1.4:1, not an order of magnitude.** P5's number is the best-sourced version of the claim
and it does not support the sentence the report built on it.

The report even cites the corroboration that isn't one: P5's *"12–20× more discrete planning events
per year than camp"* compares against **camp only (1–2/yr)**, not against all Q1 objects (~16).
S0 §3.3 presents this as independent agreement with 18:1. It is agreement with a different
denominator.

### 1.3 Count is not value, and the report says so and proceeds anyway

S0 §3.4 concedes: *"Money is in Q1. Frequency is in Q2/Q3,"* and cites P6's verdict on the
highest-frequency shallow job verbatim: *"near-zero willingness to pay, no measurable articulated
pain."* Then §3.3's conclusion — *"Camp is the tail, not the distribution"* — and S2's B1
(*"the single highest-priority item in this report"*) re-centre the product on the end of the
distribution the same corpus says has no wallet.

**There is no willingness-to-pay evidence for capture anywhere in this corpus.** Every dollar
figure attaches to Q1: camp $893–954/child, sports $1,490.66/participating child, Camperoni $295/yr
for the registration race performed by humans. The only priced capture product found is Schoolcase
at $9/mo — a company V7 classes as small and with no precedent behind it. P6 goes further and names
the mechanism: *"A market that has never charged the parent has trained the parent not to pay."*

The uncomfortable pairing: S2 keeps the hard paywall at funnel step 11 (RevenueCat 5x) while moving
the product's centre of gravity to the jobs with no measured WTP. **What you charge for and what you
centre on become different things**, and no one in the program noticed.

### 1.4 The empty Q4 is a definitional artifact, not a finding

S0 §3.2: *"Q4 — deep AND frequent: EMPTY. No job in the entire research corpus lands here.
**That is the finding.**"*

It is the finding of the convention. Two counter-examples are in the report's own table, flattened
by fiat:

- **Orthodontia**: 12–26 visits per treated child over 18–24 months. Deep and frequent by any
  ordinary reading. S0 records it as *"N=1 per session; the series is booked once."*
- **Summer camp**: N=9, freq=1 in the quadrant table — but the *same* table enters it as **7.5
  sub-bookings** for the ratio computation. Sliced that way it is freq 7.5 with N≈3, which is not
  Q1; it sits on the Q2 border.

Any deep-and-frequent job can be moved out of Q4 by decomposing it into per-episode steps, and any
shallow-frequent job can be moved in by aggregating episodes into a campaign. The axes are
analyst-chosen (N≥4, freq≥8, with no justification given for either cut point) and the emptiness
follows from the slicing rule, not from parent behaviour. **Do not publish "Q4 is empty" as a
discovered fact about families.**

### 1.5 What survives

The defensible version, and it is worth stating because it is still useful:

> A two-kid family faces roughly **20–26 discrete, dated, low-step obligations a year** (V2, from
> P5), against roughly **16 multi-step campaigns**. The product can construct the second class and
> cannot construct the first. That is a real gap, of roughly the same order of magnitude as the
> class it already serves — not ten times larger.

That still justifies B1 (manual add). It does not justify "camp is the tail" or re-centring the
product.

---

## 2. THE SUBSTITUTION PROBLEM — the corpus contains the refutation and files it as support

This is my strongest attack and it is entirely internal to the program.

S0 §4.3 cites, as corroborating evidence that the capture job is unserved:

> *"In the only tool-inventory study available (Brewer/Morris et al., ACM IMWUT 2017, n=280…):
> digital calendar 65.7%, paper list 62.1%… **Digital assistants did not surface at all.**"*

M5 — the same program's 2026 verbatim corpus, ~2,300 comments — says the opposite about the exact
job S2 wants to build:

> *"'Hey Siri, remind me to…' — quoted verbatim in at least six unrelated comments."*
> *"I heavily rely on Siri. My phone, watch, homepod and car. **Reminders for EVERYTHING** and adding
> things to lists instantly as I think of them… Means that when my hands are busy I can still make
> reminders."*
> *"**If I'm driving I wake Siri up** to set a reminder."*
> *"Everyone in the family now knows to say 'Hey, Siri… in thirty minutes remind me to…'"*
> *"I immediately asked alexa 'remind me in 2 weeks call swim instructor.'"*

M5 then draws the conclusion the report needed rather than the one the data supports: *"digital
assistants appeared zero times as a planning tool: they are not planning tools in these parents'
mental model. **They are reminder-setters.**"*

**The product being recommended is a reminder-setter.** B1 is "one field, one gesture, on Home."
D3 is "voice-in, text-out, short dictated fragment." That is *precisely* what "Hey Siri, remind me
to reschedule my dental appointment" already is — free, pre-installed, hands-free, works from a car
seat and a watch, requires no app switch, and the corpus shows parents doing it habitually and
describing it warmly.

The report searched for "digital assistants as a **planning** tool," correctly found absence, and
then recommended building a **capture** tool — the one thing the same search shows is already
saturated. The 2017 citation is doing load-bearing work that the program's own 2026 evidence
falsifies, and it is cited as Tier A with a "(dated)" flag rather than as contradicted.

**The strongest case that capture is a feature, not a product:**

1. **The job has been available for fifteen years and nobody won it as a standalone.** Reminders,
   Notes, Google Keep, Todoist, TickTick, a text to yourself. M5 quotes a parent already stacking
   four channels: *"i have one on my watch, one on calendar, and two warnings on an Alexa."*
   The marginal capture surface is the fifth.
2. **Free and pre-installed beats one gesture.** P5's offloading-tax experiment (five extra clicks
   suppress offloading, dz 0.71–1.29) is the report's Tier A anchor for capture — and it is an
   argument *against* our capture surface, because opening our app is more clicks than raising a
   wrist. The experiment says the winner is whatever is nearest, and that is the OS.
3. **The platform is closing what gap exists.** P11 #32 has Apple shipping personal-context Siri
   with onscreen awareness and mass App Intents (BRIEF corrects the date to "beta later in 2026" —
   the date is wrong, the direction is not). P11's own verdict on our photo/flyer ingest: *"General
   AI does this better (fewer taps: no PhotosPicker, no app switch)."* S2 rates the same surface
   DOUBLE DOWN and does not reconcile.
4. **The corpus's only capture-love is for capture inside a product bought for something else.**
   V5's condition, which S2 carries but does not act on: capture beats voice in mentions *only
   within products that ship capture* (Jam 7.95%, Skylight 0.99%). Jam and Skylight are not capture
   products; they are a family organizer and a wall display. Capture is what makes them tolerable.

**What this does not kill.** Capture as the *entry gesture into durable structured household state
that something acts on without being asked* (P11's four genuine wins) is defensible. Siri Reminders
does not arm a registration watch, detect a coverage gap, or hold state across two adults. **The
right claim is "capture is the on-ramp"; the report's claim is "capture is the product."** Those
have very different roadmaps and only one of them is supported.

---

## 3. THE EMAIL RECOMMENDATION — the decision is probably right; the scorecard that produced it is not

I end up agreeing with "ship B′, do not launch A on the current GCP project." The 100-user
lifetime cap is structural and decisive. But the memo overstates its confidence, and three of its
load-bearing inputs are broken.

### 3.1 The highest-weighted criterion is scored on a falsified assumption

C3 (onboarding friction) carries **weight 3 — the highest in the memo** — and B′ scores **4**,
one point *below* Option A's tap-once. The justification is §6.2's "genuine design unlock": the
confirmation link lands in our inbox, so we auto-click it and *"collapse the hardest step."*

**V6 falsified this and the score was never revised.** BRIEF, authoritative: *"Gmail forwarding is
NOT a collapsed step — the destination does receive the verification link, but the source user must
still return to Gmail and click Save Changes, and Google shows a **week-long banner warning that
unexplained forwarding may mean someone else has account access.**"*

So the real B′ setup is: go to a desktop computer → Gmail settings → Forwarding → add address →
switch context → return → Save Changes → then live with a week of Google telling you your account
may be compromised. On the memo's own weights, dropping C3 from 4 to 2 costs B′ six points
(69.5 → 63.5). It still beats A (35.0), so the *ranking* holds. But the memo's headline —
"wins on the highest-weighted criterion" — no longer holds, and that sentence is §11.2's first
justification.

The banner is worse than a friction cost. B′'s entire strategic thesis (§8.5) is that A reads as
surveillance and B′ reads as delegation — *"we never read your inbox is a marketing asset."*
Google interposes a week-long security warning at exactly the trust moment. Nobody in the program
tested how a parent reacts to that.

### 3.2 No precedent, and the bimodal evidence has a second reading

V7 is unambiguous: **`add@cozi.com` never existed**, traced to a competitor's SEO site.
Email-forwarding intake has **no large-incumbent precedent**; the precedents are Sense, Schoolcase
and Jam — all small.

P12 #42's bimodal count is presented as an instruction about *placement*: Jam 8 of 88 (9.1%) name
the address unprompted; Cozi/Todoist/Evernote **0 of 3,917**. The memo reads this as "make it the
front door or don't bother." The equally consistent reading, which nobody argued:

> **Mainstream users do not forward email to robots.** Three products with tens of millions of users
> shipped the feature and produced literally zero organic mentions across 3,917 reviews. The 9.1%
> comes from 88 reviewers of a product self-selected for that feature — the purest survivorship
> sample in the corpus.

Absent a precedent at scale, "0 of 3,917" is at least as much a demand signal as a placement signal.
The memo picked the reading that supports the build.

### 3.3 ParentSquare — the uncertainty cuts the other way

V6: the ParentSquare BLOCKED verdict is **UNSOURCEABLE** (login-gated help centre).

Suppose it is wrong and ParentSquare permits secondary addresses. **Option B still dies** — it is
rejected on three independent grounds (ToS blast radius landing on the parent's district, the
FERPA §99.33(a) exposure, 13–18 setup actions), any one of which is disqualifying. So the memo's
anxiety ("how much of the chapter survives?") is misdirected.

The real exposure is the opposite one, and the memo has it in §7 without connecting it: **ParentSquare
defaults new accounts to a 6pm digest**, and a digest is content-poor. For the largest school install
base (22M students), B′ forwards an envelope that says "you have 4 new messages." B′'s coverage
claim — *"~100% of what reaches that mailbox"* — is ~100% of **envelopes**, not of **content**, and
C4 (weight 2) is scored 4/5 on the content reading. Combine with P12 #18 (ClassDojo, Remind and
Seesaw silently disable email once the parent installs the app — *which is how essentially every
parent uses them*) and B′'s school coverage in practice may be a fraction of the score.

The memo notes app-install-kills-email degrades A, B and B′ equally and files it as "not an
architecture problem." True — and also the reason the whole email chapter may be solving a channel
that is being drained.

### 3.4 The unmeasured thing is the thing being shipped

S1 §12 admits: no funnel comparison of forwarding vs OAuth exists; **no vendor publishes an
inbound-address activation rate**; no survey has asked a US parent about comfort with third-party
school-comms access. The memo then commits 2–3 engineer-weeks plus non-optional liveness work.

§11.5's test 1 (five parents, an address, watch who completes on a phone) costs **$0 and two days**
and is listed as Phase 0. **Do the test before Phase 1, not alongside it**, and treat a poor
completion rate as an architecture signal rather than — as §11.5 pre-commits — *"the fix is design,
not a change of architecture."* That sentence pre-registers the conclusion and should be struck.

### 3.5 What I still endorse

- Do not add users to the Gmail OAuth allowlist. Do not launch on that GCP project. The 100-user
  lifetime cap is documented, non-resettable, and exhausting it disables Google sign-in (V6).
- Reject Option B. The district blast radius is disqualifying on its own.
- The §1.2 audit finding — the built Gmail sync **cannot discover anything new**, it is a 14-day
  enrichment sweep over senders the parent already entered — is the single most useful fact in the
  memo and is correctly weighted.

---

## 4. THE WATCHLIST — the best idea in the report, on the weakest measurement in the report

I want this one to be true. The logic (value scales with scarcity, not density; a Wichita parent has
the same problem as an SF parent) is the sharpest reasoning in the program. Four problems.

### 4.1 Absence of a product is being read as presence of a market

M3: *"nobody has shipped a national, cross-provider, parent-side 'tell me when registration opens'
product."* S2 calls this **verified whitespace**.

Verified absence, not verified whitespace. The same corpus supplies the deflationary reading:
*"parents do not return to a discovery product between seasons"*; *"parents will not pay for a
directory"*; Care.com's Activities & Camps app has **21 lifetime ratings**. A category where every
consumer app has failed to get traction is at least as likely to be a bad market as an empty one.

Camperoni is the proof-of-demand exhibit: $295/yr, humans, **5 metros**, still not automated after
years. That is evidence of a small, metro-bound, human-scale services business — the shape of a
market that does not support software economics, not the shape of a moat waiting to be taken.

### 4.2 The Camperoni correction went the wrong way and was spun

V5 corrected Camperoni from ~1/18th to **~1/2 of ActivityHero's live inventory**. S2 §2.2's
response: *"The correction weakens 'Camperoni is not a national competitor' as a throwaway line and
**strengthens the underlying point**."*

A correction that moves a competitor from negligible to half the best national catalog's live
inventory inside its five metros should *reduce* confidence. Instead it was converted into support.
That is the clearest instance of momentum bias I found in the corpus. The honest restatement:
**inside the metros that matter, the named competitor is dense, human-operated, and produces better
registration-date data than a scraper will.**

### 4.3 The density evidence is a single August snapshot of a seasonal marketplace

V5 struck M3's claim that seasonality would not differ by metro: year-round classes in dense metros
stay live in August while summer-only supply expires, **inflating the gradient at an August trough.**
`data/activity_supply_by_metro.csv` shows the instability directly:

| Metro | Providers within 25mi | Live sessions |
|---|---|---|
| Los Angeles | 5,686 | 329 |
| San Francisco | 4,299 | **969** |
| New York | 2,827 | 112 |

Provider rank and live-session rank disagree across the top three. So "20 states have <50 live
sessions," "Minneapolis 35," "Wichita 8" cannot be presented as structural facts about supply
density — they are one day in the deadest month. **The thin-market premise under the watchlist's
signature asymmetry has no verified empirical footing.** The logical argument survives; the
measurement does not, and S2 presents it as measurement.

Required: re-run M3's counts in **February**, the camp mass wave. It is a re-run of an already-built
script.

### 4.4 Two internal contradictions

- **Habit.** S0 §3.4 rejects the Q1 board as a habit-former because *"Sixteen touches a year cannot
  build a habit or accumulate state."* The watchlist arms **5–7 windows per family per year**
  (S2 §2.2, admitted). By the report's own test it is three times worse.
- **Input.** The moat is *"knowing the date"* — and `registration_opens_at` must be populated by
  discovery or ingest. The report demotes discovery from the front door, and M3 warns that municipal
  rec catalogs are JS-rendered SPAs its probes could not read (301/302 into marketing shells). So the
  moat depends on the one capability M3 says is technically broken at the highest-value segment.
- **The competitive claim is dead.** S2 §6 already flags it: P11 #41 (ChatGPT cannot event-trigger or
  webhook) is sourced **solely to usecarly.com**, killed by V6 as Tier D and a competitor's SEO site.
  A 20-minute in-product check settles it and has not been run.

---

## 5. THE COHORT STORY — drop the generational frame entirely

### 5.1 The Gen Z correction is not an isolated error, it is a vintage class

V1 recomputed Gen Z from 6.0% to **~10.9%** because the original was a **2023 householder-age
snapshot** read against 2026 age bands. Everything else in the cohort chapter has the same vintage:

- P1's whole cohort table: Census Table F1, **2023**.
- The child-age distributions carrying the entire "child age, not parent generation" argument
  (84.1% of 25–29-headed households have a child under 6; 73.5% of 45–49-headed have a 12–17) —
  same 2023 householder-age snapshot, same defect that produced the Gen Z error, **not recomputed.**
- **1.94 own children per family** (Census FM-3 2023) is the multiplier under *every* per-family
  frequency in `job_quadrants.csv`, and it assumes zero sibling sharing — which V2 says drops the
  sourced floor from ~15 to **~9** if two siblings share a school.
- Supporting evidence is systematically old: Gallup 2019 (dated), Brewer/Morris 2017 (dated),
  PwC 2018 (dated, PDF retired), Ruan et al. 2016, Kowalczuk & Musial (German, intention not
  behaviour), CPS 2025 (11-month, BLS says "not strictly comparable").

### 5.2 The frame earns nothing

S2 §4 is titled *"BY CHILD AGE, NOT BY PARENT GENERATION"* and every actionable conclusion in it is
keyed to child age. The generational labels then contribute exactly one thing: a household-count
denominator that was **wrong by 80%** on first pass. Drop them. Keep cohort sizes as a one-line
footnote if a deck needs a market size.

### 5.3 What this does to "make the product hip to younger parents"

The founder's stated goal has **no support in this corpus, and the one relevant datum runs against
it.** V7's restored PwC finding: **18–24s use voice daily LESS than 25–49s (59% vs 65%)**, with the
stated reason that using voice in public *"just looks weird."* P11: 18–29s are *more* self-confident
with AI but the daily-use peak is 30–49. Nothing anywhere measures younger parents' response to
design, tone or aesthetics — that was not in scope and no collector went near it.

So: "hip" is an untested product hypothesis, not a research finding, and it aims at the cohort whose
kids are 0–5 and therefore have **no Q1 load at all**. If the founder wants it, it needs its own
cheap test (five 25–29 parents, two visual directions), and it should not borrow authority from this
report.

---

## 6. THE PRODUCT MEASUREMENTS ARE STALE — and one stale number is still deciding the email architecture

S2 §0 handles this honestly for itself: the Heisman sprint is committed (`b850a3e`), the legacy
wizard is **deleted** (OnboardingView 2,001 → 1,044 LOC), the funnel is 13 Heisman steps, and *"P9's
onboarding findings must be re-scored against the new funnel."* Good. But S2 is the only document
that got the memo.

**The live defect:** S1 §2 sets its criterion weights — the weights that decide the email
architecture — with this sentence:

> *"per `P9-complexity.md`, an onboarding funnel already rated a **SEVERE OUTLIER on five separate
> measures**. That last fact promotes onboarding friction to the highest weight."*

Two problems, both authoritative in BRIEF: **"SEVERE OUTLIER" is banned** (V4: no
screens-to-completion distribution exists, so "outlier" is unavailable), and the funnel it describes
**no longer exists**. §9.2 repeats the banned phrase. So the highest weight in a decision-ready
scorecard is justified by a banned characterization of a deleted artifact. Fix the memo or re-run the
scoring; do not ship it as-is.

Similarly stale everywhere except S2: "8+N screens," "14 fields," "~34 taps," "a SECOND setup
sequence with ~5 more full editor stops," "58 text-entry fields," "16–20 taps to a saved plan."
S0 §1.7 and §4.3 use these as present-tense facts. P9's whole chapter does.

**Does it undermine credibility?** Yes, if published as-is — a reader who opens the repo finds the
central complexity exhibit describes a funnel deleted the day before. **The framing that survives:**

> Publish every product measurement as a **dated as-measured snapshot** ("the funnel as of
> 2026-08-20, pre-Heisman"), state that the sprint replaced it, and **re-measure the post-Heisman
> funnel before any complexity claim enters a deck.** The complexity *method* (compare against
> Baymard/Nielsen; label as comparison, never score) is fine. The *readings* are expired.

And do not let the report take credit for predicting a fix that shipped before synthesis. S2 §5.4
comes close (*"built before the research landed and it anticipated the finding"*) — that is a
compliment to the founder, not a validation of the research.

---

## 7. SELF-SERVING RESEARCH DESIGN — where the fleet found what it went looking for

The brief was written by the synthesizing party, after seeing the product. Six specific places where
the framing produced the answer.

1. **The finding was in the brief.** BRIEF's product section lists under *Absent*: *"any general
   'add an appointment / remind me' capture surface."* S2's top recommendation is B1: a general add
   surface. The brief told twelve collectors what was missing before they collected. Every report
   that "independently converged" on capture had read that line.

2. **WTP was declared out of scope.** BRIEF's *"WHAT WE ALREADY KNOW — do not restate"* excludes
   market size, all competitor pricing, and RevenueCat conversion. Those are the inputs that would
   test whether the newly-centred jobs can be *sold*. The program measured demand for eleven weeks
   and never once measured willingness to pay for the thing it recommends building.

3. **The measure was defined by the party with the thesis.** S0 authored the step-count convention
   ("attending is a step; remembering is not — that is the product's job"), which produces the
   200-row, which produces the 18:1 headline, which is the report's central claim. No collector
   supplied that convention. §1.1–1.2 above show the answer moves 11x with it.

4. **The quadrant cut points are unjustified.** N≥4 and freq≥8/yr appear with no derivation. §1.4
   shows the "empty Q4" is a consequence of them plus the episode-slicing rule.

5. **S1's winning option was invented and scored by the same analyst mid-draft.** The memo says so:
   drafted on a two-option framing, restructured to four when P12 landed, and B′ — the recommendation
   — is the option the analyst added. He then set the weights (§2), assigned the scores (§10), and
   reported that his option won by 2 points on a subjective 5-point scale. No adversarial scorer ran.
   The memo's honesty about the 2-point gap is real and to its credit; the structural problem is not
   fixed by noting it.

6. **The negative findings were pre-cleared.** BRIEF told collectors that for Gen Z parents "no data
   found" is *"the expected answer in several areas."* That is a reasonable methodological note and
   also an instruction that reduces the cost of not finding things in the one cohort the founder
   wants to reach.

**Counter-evidence, stated so this section is fair.** The program worked hard against this bias in
places: V1–V7 produced ~30 corrections and a disclosed ~22–25% kill-list error rate; V6 killed a
fabricated Pew figure that appears in the repo's own `gtm-research.md`; V7 killed the Cozi email
precedent that would have supported the recommendation. S2 §6 lists 14 thin-evidence items unprompted
and names one of its own top-recommendation's supporting sources as killed. **That is genuinely
unusual discipline.** The bias I am naming is in *framing and emphasis*, not in fabrication.

---

## 8. THE THREE FINDINGS MOST LIKELY TO BE WRONG IN 12 MONTHS

**(1) "Volume lives in shallow capture, and capture is the wedge" (S0 §3.3, S2 B1/D2/D3).**
Why it breaks: 200 of 264 shallow objects are attendances of a recurring schedule captured once, not
capture events (§1.2). Strip that and the ratio is ~1.4:1 against P5's own defensible figure. Add
the substitution finding (§2) — parents already do this job in Siri Reminders, warmly, hands-free —
and Apple's personal-context Siri arriving in the window. Twelve months from now the likeliest
retrospective reads: *we shipped a capture surface into a job the OS already owns, and the capture
volume in our own telemetry was one-tenth of the projection because nobody captures their soccer
schedule 200 times.*
*Falsifier already specified:* S2 §3.5's four-week test — but run it with the sports row excluded
from the projection and measure **week-4** survival, not week-1 creation.

**(2) "The registration watchlist is verified whitespace and is worth more in thin markets"
(S2 D1, §2.2 — its self-described "strongest strategic fact").**
Why it breaks: absence of a shipped product is being read as an empty market rather than a bad one
(§4.1); the one named competitor got *bigger* on correction and is human-operated (§4.2); the
thin-market premise rests on a single August snapshot whose own metro gradient is internally
inconsistent (§4.3); the competitive claim rests on a killed Tier D source (§4.4); and the addressable
count is 5–7 windows/family/yr, which the report elsewhere argues is too few to build a habit.
Twelve months on: *the alerts fire correctly, ~5 times a year, and the parents who care already had
the date in their calendar from the provider's own mailing list.*
*Falsifier:* D1's own (<30% of armed windows convert), plus re-run M3's counts in February.

**(3) "B′ ships in two weeks and wins on onboarding friction" (S1 §10, §11.2).**
Why it breaks: the "design unlock" that justified the score was falsified by V6 and the score was
never revised (§3.1); Gmail forwarding is desktop-web-only, requires a return trip to Save Changes,
and triggers a week-long Google security banner at the exact moment the pitch is "we're the
trustworthy option"; **no vendor anywhere publishes an inbound-address activation rate**; and the
0-of-3,917 mainstream review count has a demand reading nobody argued (§3.2). Twelve months on:
*the pipe works perfectly and 15% of families ever complete a forwarding rule.*
*Falsifier:* S1's own §11.5 test 1 — but run it **before** the build, and delete the sentence that
pre-commits to "the fix is design, not architecture."

---

## 9. RECOMMENDATIONS THAT WERE NEVER ACTUALLY TESTED

These would have come out the same regardless of what the research found. They are not necessarily
*wrong* — several are clearly right — but they carry no evidential weight and should not be presented
as research conclusions.

| Recommendation | Why it was decided before the research |
|---|---|
| **C1 — cut the kid voice companion** | The argument is regulatory (FTC 6(b), amended COPPA, $10M Disney) plus the app's own `ConsentView.swift` saying *"not yet COPPA-compliant."* True with or without any demand data. And "zero demand evidence" for a closed-beta feature with near-zero users is unfalsifiable — the corpus could not have found demand evidence for it. Right call, no research content. |
| **C2 — cut the `trip` vertical** | The flag is already off; S2 §3.3 rates the effort *trivial*. A zero-cost cut of a dark feature needs no evidence. V3's correction made the case *stronger*, which is convenient, but nobody would have kept it either way. |
| **C5 — delete `SavedView` + the orphaned third `ChatView`; fix `build_board`'s `if aid:`** | Bugs and dead code. S2 calls C5 *"housekeeping, not strategy"* and is right. The `if aid:` fix is a one-line bug fix presented as the prerequisite to a strategic re-architecture. |
| **D3 — extend dictation** | Justified on cost (*"the cheapest large win"*, 140 LOC already built, attaching an existing accessory). At zero marginal cost, this is recommended at any evidence level. The P8 WPM evidence is decoration on a build-because-it's-free decision. |
| **D4 — turn on `extracurricular` and `school_event`** | Flipping two feature flags that gate demand-bearing verticals during the one window when the two on-by-default doors have nothing to do. No research outcome would have produced "leave them off." (P9's contrary WITHIN-NORM rating was overruled on a narrow argument about *which two*, not on evidence.) |
| **S4 — stop auto-presenting `SetupTailView`** | A forced second setup sequence at the moment of arrival was going to be cut before, during, and after the funnel was replaced. |
| **Reject Option B** | Decided by structural facts — the ToS blast radius landing on a school district, FERPA §99.33(a), 13–18 setup actions. No behavioural research entered the decision. |
| **"Simplify onboarding"** | The recommendation predates the research, survived the funnel being deleted, and would survive its replacement. V4 says the quiet part: *"the cut is probably right; the claim that data proves it is wrong."* |

The pattern: **almost every CUT and every trivially-cheap DOUBLE-DOWN was pre-decided.** The
recommendations the research actually drove are B1 (capture), B2 (the forwarding address), D1 (the
watchlist promotion) and S1 (invert the atom) — and those are precisely the four I have attacked
hardest above.

---

## 10. VERDICT — act / test / drop

### ACT (safe now; evidence or logic is independent of the contested claims)

1. **Cut the kid voice companion**, or dark-flag it this week. Regulatory exposure is structural and
   the app says in its own consent copy that it is not COPPA-compliant.
2. **Cut the `trip` vertical.** Delete `SavedView` and the orphaned third `ChatView`. Fix
   `lifecycle.py`'s `if aid:` so a parentless obligation is visible.
3. **Extend dictation to the capture surfaces and the 18 profile fields.** Zero marginal cost,
   bounded downside, already-correct architecture (voice-in / editable-text-out).
4. **Stop auto-presenting `SetupTailView`.** Make it a tap.
5. **Turn on `school_event`.** Its frequency evidence (NHES:PFI 2023, n=19,562, Tier A, 6.0
   parent-attended activities per child) is the best-sourced number in the entire corpus, and it owns
   the only vertical with a per-kind task-chain builder and the only `date_model` that renders a
   one-off correctly.
6. **Do not add a single user to the Gmail OAuth allowlist; do not launch on that GCP project.**
   The 100-user cap is lifetime, non-resettable, and exhausting it disables Google sign-in.
7. **Reject Option B.** District blast radius is disqualifying on its own.
8. **Reframe the existing expiring share link as the second-parent mechanism** (M4 is counted, its
   regexes are published, V5 replicated it). This is cheap and displaces 792 LOC of Circle
   conversation product that competes with iMessage.

### TEST FIRST (cheap, and the answer should be allowed to change the plan)

9. **B1 / the capture thesis — S0's four-week test, with three amendments.** Run it in
   September–October; project the denominator **excluding weekly sports logistics**; and report
   **week-4 captures per active user**, not week-1. Pre-register the threshold. If shallow captures
   do not exceed tracked activities by ~4x (not 10x — the honest ratio), the thesis is wrong.
10. **B2 / the forwarding address — run S1's five-parent test BEFORE the two-week build.** Two
    questions, not one: what share complete a Gmail forwarding rule on a phone, **and** what happens
    when Google shows them the week-long "someone else may have access to your account" banner.
    Strike §11.5's pre-commitment that a poor result means "design, not architecture."
11. **D1 / the watchlist — three cheap checks before promoting it to first-class.** (a) The
    20-minute in-product test of whether ChatGPT/Gemini scheduled tasks can watch a page and push —
    the current source is killed. (b) Re-run M3's ActivityHero metro counts in **February**, not
    August. (c) The ParentSquare first-party content test ($0, one day) — it bears on B′'s coverage
    more than on Option B.
12. **D4 / `extracurricular` ON** — cheap, but instrument `door_opened` against camp's rate during
    the Aug–Oct window exactly as S2 §3.1(d) specifies, and honour the falsifier.
13. **B3 (AAP schedule) and B4 (sports physical)** — both are strong-logic / zero-data. Ten families
    each before either goes on a roadmap. B4 in particular has **no citable US frequency at any tier**.
14. **S1 / "invert the atom" — do not run the migration until #9 returns.** It is a schema change plus
    a board renderer justified entirely by the contested ratio. The one-line `if aid:` fix (item 2)
    buys the same visibility at 1% of the risk and is the correct first step regardless.
15. **"Hip to younger parents"** — if the founder wants it, it needs its own five-parent test. This
    report gives it no support and one datum against it.

### DROP (do not publish, or publish only in corrected form)

16. **The 18:1 / "~280 shallow objects" headline.** Publish the corrected 264 with weekly sports
    logistics **broken out as its own line**, or publish P5's **~23 obligations/yr (band 20–26)**,
    which is the defensible number and is *not* an order of magnitude above the ~16 deep objects.
    Any chart must name the camp-counting convention (7.5 sub-bookings vs 1 cycle moves the ratio
    from 17:1 to 28:1).
17. **"Q4 — deep and frequent — is EMPTY. That is the finding."** It is an artifact of the
    analyst's episode-slicing convention (§1.4). Keep the quadrant plot as a descriptive device;
    drop the emptiness as a discovered fact.
18. **The three-generation frame.** Every actionable conclusion is keyed to child age; the
    generational labels contributed one denominator that was wrong by 80%. Footnote the cohort sizes;
    delete the chapter structure.
19. **Any claim resting on "digital assistants did not surface at all"** (Brewer/Morris 2017,
    n=280). Contradicted by the program's own 2026 corpus (§2). Where the capture argument needs a
    substitution claim, it must engage Siri Reminders directly and lose or win on the merits.
20. **P9's complexity readings as present-tense description**, and **S1's "SEVERE OUTLIER on five
    measures" weighting rationale** — banned phrase, deleted artifact, and it is currently setting
    the highest weight in the email scorecard. Re-run S1 §10 with a corrected C3 for B′ and a
    corrected §2, and state that the ranking survives (it does) rather than that B′ "wins on the
    highest-weighted criterion" (it no longer clearly does).
21. **"Camperoni is denser than we thought, which strengthens the point."** Restate neutrally: the
    named competitor holds ~half of ActivityHero's live inventory inside five metros with human
    operators. That is a competitive fact, not a supporting one.
22. **The M3 metro supply picture as a structural gradient.** One August day; provider rank and
    live-session rank disagree across LA/SF/NYC. Present as a dated snapshot until re-run.

---

## 11. WHAT I COULD NOT BREAK

Stated so the verdict is calibrated rather than uniformly hostile.

- **The Gmail OAuth 100-user lifetime cap** and the 7-day test-user expiry. Documented twice by
  Google, independently confirmed by P12 and V6. This is the most decision-relevant hard fact in the
  program and it is correct.
- **The §1.2 audit of the built email sync** — it cannot discover anything new; it is a 14-day
  enrichment sweep over senders the parent already entered. Verified in code by two parties.
- **M3's ActivityHero audit** — 94,848 sessions / 9,008 live, reproduced cell-for-cell by V5. The
  measurement is sound; only its *interpretation* as a structural gradient is not (§4.3).
- **M4's counted co-parenting analysis** — regexes and denominators published, all replicated. The
  conclusion that the refusal is *money, not installation*, and that personal artifacts survive the
  ex's non-participation while joint actions collapse, is the best-evidenced strategic claim in the
  corpus. C3/Circle-simplify follows from it cleanly.
- **The kid-companion regulatory exposure.** FTC 6(b), amended COPPA, live enforcement, and
  `TavilySearch` wired into a child's conversation. Nothing I found softens it.
- **The verification program itself.** Two passes, ~30 corrections, a disclosed ~22–25% residual
  error rate, and a stated decision to stop. Publishing that rate openly is the right call and makes
  the appendix more credible, not less.
