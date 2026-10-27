# S3 — THE INTERACTION-MODALITY PRESCRIPTION

Synthesist S3. Compiled 2026-08-22. Answers: **voice or typing, and where.**

Authorities used, in precedence order: the BRIEF's THREE CORRECTIONS blocks (override all collectors)
→ V7 (restores the voice context-of-use data P8 wrongly declared absent) → V3/V5 (correct P8 and M1)
→ M5 (qualitative capture/voice corpus) → M1 (counted review corpus) → S0/S2 (structural and product
verdicts I must not contradict). All product claims below were re-verified in the repo on 2026-08-22
and carry file paths.

---

## 0. THE PRESCRIPTION IN SIX LINES

1. **Dictation is the app's voice strategy.** Voice-in / text-out-and-editable, one gesture, everywhere
   a parent enters a fragment. The pattern is already built and correct.
2. **Conversational voice is a keep-but-don't-extend.** It is the only voice behaviour with zero
   supporting evidence in either the qualitative or the counted corpus.
3. **But dictation is not the LEAD.** The camera is. A photograph of a piece of paper is the
   best-evidenced capture input in this entire program, and — a new finding below — the app has an
   in-app camera today, in onboarding only.
4. **The single largest unclaimed opportunity is not a modality at all.** It is the *transposition*
   between capture and reference that every working parent system performs by hand, weekly, and
   resents (M5, cross-cutting observation #3).
5. **Every capture modality must land in the same editable object.** Ruan's subjects preferred the
   keyboard for repair; the extraction corpus says reliability is a cliff, not a gradient (M2 via S2
   §2.8). Voice, camera and email are three doors into one confirm-and-edit row.
6. **None of this is decidable from published research.** No US source separates dictation from
   assistant commands from LLM voice (P8, explicit negative finding). §5 is therefore not optional.

---

## 1. THE MODALITY MATRIX

Modality vocabulary: **dictation** (speech→editable text, one shot) · **typing** · **tap-confirm**
(the parent adjudicates a pre-filled object) · **camera** (photo of paper/screen) · **email-forward**
(inbound address) · **conversational voice** (full-duplex spoken session).

| # | Interaction | RIGHT modality | Evidence | What the product does TODAY |
|---|---|---|---|---|
| 1 | **Quick capture of an obligation** ("swim lessons Tuesday at four") | **Dictation, primary; typing, co-equal fallback.** One field, one gesture, no sequence | Ruan et al. 2016 (Tier A, n=32, quiet room, **transcription**): 161.20 vs 53.46 WPM = 3.0x, 20.4% fewer errors — and capture *is* transcription, because the parent already knows the words. P5 (Tier A, n=52x2, within-subject, dz 0.71–1.29): five extra clicks **significantly reduced whether people offloaded an intention at all**, worst at high memory load — so the gesture count, not the modality, is the binding constraint. M5's law of capture: *"if I don't do it in the moment, the thought is gone"* | **Nothing exists.** No form anywhere in the app creates a plain obligation: the only client POST that creates an activity is `PlanService.trackActivity`, sole call site `mvp/MVP/PlanViewModel.swift:593` (pin a discovery candidate); `PlanService.todos()` is GET-only. Verified by S2 §1.3 and re-checked here. Dictation exists but is wired only to onboarding (below) |
| 2 | **Capturing a piece of paper** (flyer, permission slip, schedule) | **Camera.** Shutter → extraction → tap-confirm | M5's verb, unambiguous: *"**I take a picture of it**" — never "I scan it," never "I type it in."* Two independent flyer-capture systems described (Google Photos shared album; "the flyer comes in my son's weekly folder and I just take a picture of it"). M1 5★, unprompted: *"create events from your camera or from pictures… **is genius**."* V5 (counted): where a product ships capture, praise runs at **7.95%** of reviews (Jam) vs **0%** voice in the same app. P5's adjacent Tier A finding — the digital capture effect (*Memory & Cognition* 2026, 7 experiments) — is that photographing to "save" **impairs later recall**, i.e. parents are already building a write-only archive that wants a reader | **Two half-surfaces, both misplaced.** `mvp/MVP/IngestView.swift:146` is **PhotosPicker only** — "Choose a photo," library, no shutter — and is reachable only from the Planner (`mvp/MVP/PlanView.swift:87`, `:761` `flyerCard`, `:1031`). **NEW, corrects the BRIEF's "no in-app camera":** a real camera exists — `HeismanCameraCapture` (`UIImagePickerController`, `sourceType = .camera`) at `mvp/MVP/OnboardingHeismanExtract.swift:482`, presented at `:83`, `NSCameraUsageDescription` in `mvp/MVP/Info.plist:11` — **in onboarding only.** Same shape as dictation: proven in-house, trapped in the funnel |
| 3 | **Capturing what arrives by email** (registration confirmations, school blasts) | **Email-forward** to an inbound address. Zero new UI, zero modality | S1 scores inbound forwarding **69.5/77.5 vs Gmail OAuth's 35.0**, winning on the highest-weighted criterion (onboarding friction), and it is the only option with a mechanism for the second parent (no install, no account, no payment). M2: of eleven live products **eight accept email forwarding as a primary intake**. Already-known: 80+ school emails/month, 62% missed something. **Honest caveat, per V7: there is NO large-incumbent precedent — `add@cozi.com` does not exist and never did**; the only precedents are Sense and Schoolcase, both small | **Does not exist.** `grep -rni "mailgun\|postmark\|sendgrid\|ses\|inbound_email"` over `mvp-backend/app` returns nothing. The *brain* exists: `ingest_artifacts.source` already enumerates `…\|gmail\|forward` at `mvp-backend/app/duckdb_storage.py:949`. Gmail OAuth ingestion exists but cannot discover anything new and is admin-gated (`mvp-backend/app/email_sync/router.py:16`) |
| 4 | **Reviewing / confirming an extracted item** | **Tap-confirm over an editable text object.** Never voice, never a form | Ruan et al. (Tier A): *"most users prefer keyboard to speech for error correction and this significantly improves performance"* — repair is a typing job even when capture was a speaking job. M2 via S2 §2.8: *"Family logistics have no tolerance for an 85% extraction rate… once a parent catches one wrong entry, they revert to manual and keep doing manual forever"* — M1 calls it a **trust cliff, not a gradient** | **This is the product's best-built thing.** `mvp-backend/app/ingest/extract.py` (471 LOC) → `materialize()` writes a `tracked_activity` at `exploring`/`pending_eligibility` with a confirm to-do, **never auto-WATCHED**; prompt-injection hardened. `DictationController` publishes an *editable partial transcript* — exactly the voice-in/text-out architecture. Keep both laws |
| 5 | **Searching / discovery** ("find me a soccer camp near 80206") | **Typing** the seed, **tap** the knobs, **screen** for the result. Not voice in any form | P8 §2: *"There is no evidence anywhere in the literature that a US consumer population has ever adopted voice for a multi-step, high-stakes, comparison-heavy task."* Alexa's Devices division lost **>$25B 2017–21** (Tier C, documented reporting) precisely on discovery and comparison. Even Google's flagship voice product needs a screen in **~1 in 5** Gemini Live interactions (Tier C, vendor, method undisclosed). Ruan again: composition-by-speech **7.8 WPM vs 32.5 keyboard** — forming a query is composition | Correct by accident: discovery is typed + tapped (`mvp/MVP/PlanViewModel.swift:583`; `StartDiscovery` needs a ZIP). The defect is elsewhere — 12 knobs and a 1–2 min async wait, which P9 prices at **6–12x Nielsen's verified 10-second limit** |
| 6 | **Comparing candidates** | **Screen + tap.** The one place a list beats every spoken interface | Same as #5. This is the structural argument, not a preference: comparison requires simultaneous presentation, which speech cannot deliver. Note the honest limit — this is reasoning from the Alexa-commerce failure and the Gemini-Live 20% figure, **not** from a measurement of parents comparing camps by voice. No such measurement exists | Correct today (fit-scored candidate list, lifecycle board) |
| 7 | **Editing a profile** (the 18 free-text "what the coach believes" fields) | **Dictation on every field**, typing to repair, and *stop asking for it up front* | Ruan (Tier A) on volume: these are the app's most expensive fields in Baymard's taxonomy and the most dictation-shaped — the parent is emptying a formed thought about their own child. P11 via S2: passive accumulation is the competitor's structural advantage; *"we charge a large setup toll for something the competitor gets for free by listening"* — **our worst competitive liability and entirely self-inflicted** | `mvp/MVP/ProfileEditorViews.swift` carries **31 of the app's text-entry instances** (the 18 `axis: .vertical` free-text rows plus short fields). **Zero have a mic.** S2's verdict — keep as a read-mostly review surface, put dictation on all of them — stands |
| 8 | **Long-form coaching conversation** | **Typing, with dictation into the composer.** Conversational voice stays available and unpromoted | Kowalczuk & Musial 2024 (Tier A, n=860, **German, continuance intention not behaviour**): continuance intention significantly lower in public in every scenario, **shame** the mediator. Independent second line, restored by V7 — PwC 2018 (n=1,000 US 18-64): 18-24s use voice daily **less** than 25-49s (59% vs 65%), stated reason that using voice in public *"just looks weird."* A parent's planning moments are semi-public by construction: pickup line, kid in the room, partner on the couch, waiting room. And the content is a child's name, a budget, a custody schedule | `mvp/MVP/AgentView.swift:173` `fullScreenCover` → `ParentVoiceView` (256 LOC, ElevenLabs ConvAI over LiveKit) is the **only** parent-facing conversational entry point. The Coach composer (`AgentView.swift`, 1 TextField) and the Planner's `CosChatView.swift` (1 TextField) **have no mic**. Fix that; leave the call button where it is |
| 9 | **Scanning what's coming up** | **Screen, date-ordered — and spoken *output* is the one under-tested upside** | M5's ambient-output cluster: *"My Alexa reads me my events from the calendar the night before. And then announces everything 1 hour ahead"*; *"It broadcasts on all devices across the house."* M2's inversion, corroborated by a Nori 5★ on outbound phone-call reminders. PwC/V7 context data: **74% use voice in the home**, 65% cooking, 62% multitasking, 57% watching TV — the exact geometry of a morning briefing. **Counterweight:** M4 finds missed-notification complaints in **14–15%** of AppClose/OFW/Fayr reviews, *"the angriest reviews in the corpus"* — an unreliable outbound channel is worse than none | Home is a screen; there is no spoken briefing anywhere. The full-duplex stack that exists is input-shaped, not output-shaped |

**The one-line reading of the matrix.** Voice belongs at the two ends — *emptying a formed thought in*
and *hearing a reminder out* — and nowhere in the middle. Everything between capture and reminder is
screen work: comparison, confirmation, repair.

### 1.1 Where the context-of-use data actually lands (V7's restoration, applied)

PwC 2018 (n=1,000 US 18-64, values via Voicebot/TechCrunch since PwC's PDF is retired; **cite as 2018
and flag as dated**) is the only real context data in the program, and it is more favourable to this
product than P8's "no data" implied — with one caveat that changes the design:

- **65% cooking · 62% multitasking · 57% watching TV · 29% working · 74% in the home.** These are
  hands-occupied, at-home, semi-private moments — the same three contexts M5's parents name verbatim
  (*"when my hands are busy"*, *"if I'm driving"*, *"unless my kids are being feral"*). Two
  independent corpora, one survey and one forum, converge on the same trigger.
- **40% driving on a SMARTPHONE vs 0% on a smart speaker.** The device split is the whole finding.
  Voice-in-the-car is a phone behaviour, and this is a phone app. P8 §8 proposed exactly the right
  test and it survives: if voice sessions cluster into a commute window, voice here is a car feature.
- **Adoption peaks at 30-49** (smart speaker 41%, daily chatbot 34%; Pew 2026, n=5,119, Tier B) —
  the core cohort is the most voice-equipped and most AI-habituated group in America, while being
  *less* confident with chatbots than 18-29s (23% vs 31%). High exposure, low self-trust. That argues
  for forgiving, low-stakes voice — a mic on a field the parent can edit — and against a modality that
  is the only way to accomplish anything.

The caveat: every one of those contexts is a **capture or listening** context. None of them is a
comparison context. The restored data raises the ceiling for dictation and for spoken output. It does
not raise the ceiling for conversational planning at all.

---

## 2. THE CAPTURE-VS-REFERENCE SPLIT

M5's cross-cutting observation #3, in full: *"Capture and reference are separate problems with
separate winning technologies. Capture: phone, voice, camera, text-to-self. Reference: paper,
whiteboard, wall-mounted screen. **Every parent in this corpus who has a working system has both, and
transposes between them by hand, weekly. The transposition step is manual labor that nobody has
automated and everyone resents.**"*

**Is this the real product opportunity? Yes — and it is the strongest structural claim in the
program that nothing in the roadmap currently addresses.** Four reasons it holds up:

1. **It is over-determined by independent evidence.** Brewer/Morris (ACM IMWUT 2017, Tier A, n=280 +
   one-week diary, dated): digital calendar 65.7%, **paper list 62.1%**, paper calendar 53.5%,
   post-it 50.0%, digital list 37.8% — and in the diary week 16 participants used a paper list against
   5 digital. Paper is not nostalgia; it wins on the reference job. M5 supplies the mechanism:
   *"Paper is a display, not a database"*; *"paper survives the partner"* (a whiteboard is passively
   broadcast, a shared app requires the second adult to open it); *"striking something out gets a
   small amount of dopamine going."*
2. **The parents state the split themselves, unprompted.** *"I love my paper planner but can't use it
   for stuff like that"* — said about on-the-spot capture. That is one person naming both halves and
   the seam between them in one sentence.
3. **It explains the category's death pattern better than any feature verdict.** M1/M4/M5 all converge
   on failure at the seam between two people; M2's four killers include *"the only mechanisms that
   demonstrably move the second adult are the ones that require no adoption at all."* A wall display
   is exactly such a mechanism, and Skylight — the one incumbent that ships one — is the one whose
   capture praise M1 counts.
4. **It is the one job with no competitor.** Skylight sells the display and is weak at capture; Jam
   and Ohai sell capture and have no display. Nobody sells the transposition.

**What it means concretely.** Not "build a hardware display." Three moves, in order of cost:

- **(a) Make the app's reference layer transposable, not just viewable.** One date-ordered surface
  (S0 §4.2's `OBLIGATION` atom, S2's S1) whose output is a *thing you can put on a wall*: a printable
  week, an ICS feed, a share link. The share primitive already exists and is already the right shape —
  `POST /cos/plan/share` → scoped expiring token → public no-login HTML at `GET /share/{token}`
  (`mvp-backend/app/cos/router.py:861`, `app/server.py:659-690`, `share_tokens` migration v11). S2
  calls reframing it *"a better answer to the second-parent problem than 792 LOC of Circle."* Add
  **ICS** — S2 notes ICS export would be evidenced and XLSX is not, and M5's respondents live in
  Google Calendar.
- **(b) Automate the transposition itself.** The weekly manual step is: everything captured this week
  → onto the wall/fridge/planner. That is a *scheduled render*, not a new feature — a Sunday-night
  "here is the week, printable / castable / textable" artifact. This is the specific labor M5 says
  nobody has automated.
- **(c) Close the loop with spoken output** (matrix row 9), which is the reference layer delivered to
  the room instead of to a person. Gated on notification reliability, per M4's 14-15%.

**Honest limit.** M5 is qualitative, non-representative, browser-scraped individual comments, and
**skews heavily to r/adhdwomen and r/ADHD**. The paper-beats-digital numbers come from a 2017 study of
280 US adults, not parents. The split is a strong hypothesis with two independent lines of support —
not a measured market. §5 says how to test it before building (b).

---

## 3. RANKED CAPTURE MECHANISMS, BY EVIDENCE STRENGTH

| Rank | Mechanism | Evidence strength | The strongest single item | The honest weakness |
|---|---|---|---|---|
| **1** | **Camera / photo of paper** | **Strongest in the program.** Two independent corpora (qualitative verb + counted reviews), a Tier A adjacent mechanism, and a competitive consensus | M5's verb is exclusive — *"I take a picture of it," never "I scan it," never "I type it in."* V5 counted: Jam 7.95% capture praise vs 0% voice. M1 5★ unprompted: *"is genius."* At least six of eleven live competitors accept a photo (M2) | Extraction reliability is a cliff (M2/M1). A camera that produces a wrong date once is worse than no camera. The `never auto-WATCHED` law in `extract.py` is the correct answer and it costs a tap |
| **2** | **Tap-confirm** | **Strong, and it is a multiplier not a standalone.** Tier A on repair-preference; Tier A on gesture cost | Ruan et al.: users prefer the keyboard for correction *and it significantly improves performance*. P5: five extra clicks suppress offloading (dz 0.71–1.29) — so confirmation must be **one tap**, not a form | It is not a capture mechanism on its own; it only exists downstream of 1, 3, or 4. Its risk is being over-built into the "another notification to confirm what I just did" pattern M1 quotes at 2★ |
| **3** | **Email-forward** | **Strong on reasoning, thin on precedent.** S1's scored decision, M2's competitive census | Eight of eleven products take email as primary intake; S1's 69.5 vs 35.0; the only mechanism that reaches the second parent with no install | **V7: no large-incumbent precedent exists — `add@cozi.com` never existed.** V6: setting a Gmail forward is *not* a collapsed step (return trip + Save Changes + a week-long Google warning banner), and it is a desktop-web flow on a phone-first product. Silent failure is the named risk (S1 §6.4) |
| **4** | **Dictation** | **Strong lab evidence, narrow scope, near-zero stated demand.** Tier A magnitude; the demand is inferred | Ruan et al.: 3.0x and 20.4% fewer errors for transcription. The pattern is already built and correct (`DictationController.swift`, editable partial transcripts) | The 3x is transcription in a quiet room on a 2016 phone with n=32; composition collapses to 7.8 vs 32.5. And **no parent in either corpus asks for in-app dictation** — M1's handful of speech-to-event requests total four quotes in 4,073 reviews |
| **5** | **Conversational voice** | **Weakest. No supporting evidence in either corpus.** Two Tier B/C negatives and one Tier A social barrier against | **M5: zero instances of conversational voice planning in ~2,300 comments.** Edison/NPR 2022 (n=2,334): 12.4 tasks/week, mostly music/lights/timers. >$25B Amazon Devices loss. Kowalczuk & Musial (n=860, German, intention) + PwC 2018's "just looks weird" | Its one live upside is vendor-grade (Google's 63%-of-Gemini-users-use-voice, no n, no window, no definition of a voice user) and P8 is right that the ceiling may be moving. That is a reason not to delete it, not a reason to fund it |

### 3.1 What to lead with, plainly

**Lead with the camera.** Ship a shutter as the primary capture affordance on Home — not a
library picker, not inside the Planner. The evidence for it is the strongest in the program; the
component already exists (`HeismanCameraCapture`, `OnboardingHeismanExtract.swift:482`) and is
currently reachable **only during onboarding**, which means the product teaches a parent the gesture
on day zero and then takes it away. That is the cheapest large win available.

**Ship dictation in the same gesture, not as a second product.** One capture bar on Home with two
affordances — shutter and mic — both landing in the same editable object, alongside plain typing.
Extending `DictationController` is a wiring job: it is one 140-LOC file, currently instantiated five
times across four onboarding files (`OnboardingHeismanChrome.swift:279`/`:356`,
`OnboardingHeismanScreens.swift:168`, `OnboardingHeismanTail.swift:15`,
`OnboardingHeismanExtract.swift:26`/`:27`). Re-counted today, the app holds **61 text-entry instances**
(53 `TextField`, 7 `TextEditor`, 1 `SecureField`); dictation reaches **3 of them** — all in onboarding.
The BRIEF's "~58 other text-entry fields" survives the Heisman rewrite almost exactly: **58 fields
have no mic**, including both chat composers and all 31 instances in `ProfileEditorViews.swift`.

**Email-forward third, as infrastructure**, per S1 — with the V7 honesty that it has no incumbent
precedent, and with a delivery receipt so it can never fail silently.

**Where conversational voice legitimately belongs — one place.** Keep the Coach-tab call button
(`AgentView.swift:173`) exactly as it is: unpromoted, one entry point, zero roadmap slots. Its
defensible use case is the hands-and-eyes-occupied *private* moment that PwC's 40%-driving-on-a-phone
figure describes and M5's parents name — and even there, the corpus behaviour is a one-shot command,
not a session. Do not put it in the Planner. Do not put it on Home. Do not let it consume the roadmap
slot dictation should have (S2's verdict, which I am ratifying, not extending). The kid companion —
the other conversational surface — S2 cuts on regulatory grounds; nothing in the modality evidence
argues to save it, and the closest adjacent number (companionship = 4% of adult chatbot use, Pew 2026)
argues the other way.

---

## 4. THE HONEST CASE AGAINST MY OWN RECOMMENDATION

**The strongest case that dictation is a nice-to-have, stated at full strength:**

1. **Nobody asks for it.** Voice appears in 51 of 4,073 M1 reviews (~1.3%), 106 of 15,692 in V5's
   fuller count (0.68%), and **no reviewer in 4,073 describes voice as a reason they chose, kept, or
   left a product** (V5 confirmed this against 15,692). Of those mentions, the overwhelming majority
   want *smart-speaker list integration* — Alexa "add milk" — not dictation inside the app. Requests
   for speech-to-event total four quotes. M1's own read: **"voice is a nice-to-have; camera/inbox
   capture is a switching reason."**
2. **Two reviewers said the quiet part.** "No one wants AI" appears in the corpus, and M5's
   privacy-refusal chain is a complete adoption-failure loop in one comment: *"I refused to link up my
   email, calendar… It was USELESS and FRUSTRATING."*
3. **The 3x is fragile.** n=32, university students 19-32, an iPhone 6 Plus, a **quiet meeting room**,
   a transcription task with the words supplied. A parent capturing at pickup is in a loud car with a
   kid talking. The same paper reports mobile speech in the field at **18 WPM seated / 13 walking**
   (Parakeet) — against a keyboard's 53. In the field the advantage may be near zero.
4. **The OS already owns it.** Every one of those 58 fields already has a mic on the iOS keyboard.
   Adding our own may be duplicating a system affordance the parent already has and mostly ignores.
5. **No US research separates the three voice behaviours** (P8, explicit negative). Every argument I
   have made that "dictation ≠ conversational voice" is a *reading* of two lab studies and a forum
   corpus, not a measured distinction in any US population.
6. **Historical base rate is bad.** Koester (via Ruan): seven of eight new users abandoned a speech
   system within six months. Pew 2017: only 22% cite naturalness-over-typing as a major reason for
   voice; 55% cite hands-free — i.e. voice is a *situational* tool, not a preferred one.

**Do I accept it? Partly — and the part I accept changes the ranking, not the recommendation.**

I accept **#1 and #6**: dictation is not a switching reason and should never be marketed as one, and
it must never be the only way to do anything. I have ranked it **4th**, below camera, tap-confirm and
email-forward, precisely because of this. Anyone reading this report should not fund a "voice
strategy."

I **reject** the inference that it is therefore not worth building, on three grounds:

- **The corpus cannot see it.** V5 demonstrated this mechanism directly and independently: the regex
  for partner non-adoption returns **1 hit in 15,692 reviews** for a phenomenon M4 shows is
  ubiquitous. App Store reviews cannot see quiet non-adoption, and they cannot see demand for a
  feature no shipped product has trained users to expect. M1 says so itself. Argument #1 is evidence
  about the corpus's sensitivity as much as about the demand.
- **The cost is a rounding error and it is already sunk.** This is not a bet. `DictationController` is
  140 lines, committed (b850a3e), on-device where supported, already publishing editable partial
  transcripts, already shipping in production onboarding. Extending it to a capture bar and the two
  chat composers is wiring, not invention. A feature whose evidence is "strong lab, thin field" and
  whose cost is one sprint-day is a straightforwardly good trade; the same feature at one engineer-
  month would not be.
- **Argument #4 cuts the other way once you look at the gesture.** The keyboard mic requires: tap
  field → keyboard raises → find mic → tap → speak. P5's Tier A result is that **five extra clicks
  measurably suppress whether the offload happens at all**. The value of an in-app mic is not the WPM;
  it is removing three gestures from a path where gesture count is the causally measured constraint.
  That reframing also means the win only materialises if the mic sits on a *one-gesture capture bar* —
  a mic added to the current 58 fields buys almost nothing.

**What would change my mind:** if instrumented dictation starts fewer than ~10% of captures after four
weeks of availability on a one-gesture surface, dictation is a nice-to-have and should be quietly left
where it is. That threshold is in §5, and I would apply it without argument.

**Where this prescription is thin, stated plainly.** (a) The dictation-vs-conversation distinction is
mine, not any source's. (b) Field-condition dictation performance for parents is unmeasured
everywhere. (c) The public-use social barrier rests on a German intention study plus a 2018 PwC
attitude item — no US behavioural measure exists. (d) The capture/reference split rests on one
qualitative corpus skewed to ADHD subreddits plus a dated 2017 tool inventory. (e) The camera
recommendation is the only one I would call well-evidenced without qualification.

---

## 5. INSTRUMENTATION

Published research cannot answer whether *these* parents will talk to *this* app. Everything below is
first-party, and every recommendation above has a numbered falsifier.

**Fielding conditions (both required).** Run the capture experiments in **September or October** —
P7's dead window — so nothing is contaminated by camp season. And report **week-4** numbers, never
week-1: M5's abandonment language (*"another thing to maintain"*, dying in week two) predicts week-1
capture volume will look great and week-4 will not.

### 5.1 Events to emit

| Event | Required properties |
|---|---|
| `capture_started` | `surface` (home_bar / planner / coach / profile / onboarding), `modality` (**camera / dictation / typing / paste / forward**), `local_hour`, `day_of_week` |
| `capture_committed` | as above + `latency_ms` (first gesture → saved), `edited_before_commit` (bool), `chars_changed`, `field_count` |
| `capture_abandoned` | as above + `stage` (permission / recording / review), `elapsed_ms` |
| `dictation_session` | `duration_ms`, `transcript_chars`, `partial_count`, `error` (permission_denied / no_speech / recognizer_unavailable) |
| `extraction_confirmed` | `source` (photo / forward / paste / gmail), `items_returned`, `items_kept`, `items_edited`, `fields_corrected[]` |
| `voice_call_started` / `voice_call_ended` | `entry_point`, `duration_ms`, `turns`, `abandoned_within_15s` (bool), `local_hour` |
| `obligation_created` / `obligation_completed` / `obligation_dropped` | `origin_modality`, `has_parent` (workflow vs standalone), `days_to_due` |
| `reference_view` | `surface` (home_week / share_link / ics_subscribe / print), `viewer` (owner / link_recipient) |
| `share_link_opened` | `scope`, `viewer_is_owner` |

Cuts to hold on all of them: **modality × surface × local_hour × week-since-install × child-age-band**
(0-5 / 6-12 / 13-17 — S2 §4 shows child age, not parent generation, is the real segmentation) ×
**cohort** (Gen Z / Millennial / Gen X, for the report's own three-cohort contract).

### 5.2 The decisive tests, with thresholds

| # | Question | Test | CONFIRMS if | REFUTES if |
|---|---|---|---|---|
| **T1** | Is capture the product at all? (S0/S2's adjudicating test — I adopt it unchanged) | Ship one manual-add field + one to-do row, no board, no discovery, no lifecycle. Measure creations/user/week vs `activity_tracked` | Shallow captures exceed tracked activities by **≥10x within 4 weeks** | They do not — in which case this whole analysis is wrong and the board is the centre of the product |
| **T2** | Does the capture habit survive? | `capture_committed` per active user, week 1 vs week 4 | Week-4 ≥ **50%** of week-1 volume | Week-4 < 25% of week-1 — the habit is a novelty and no modality fixes it |
| **T3** | **Camera-first is right** | Modality share of `capture_committed` once a shutter and a mic sit side by side on one Home bar | Camera is the **#1 non-typing modality by committed captures** | Camera < dictation, or camera < 10% of captures — my rank-1 call is wrong |
| **T4** | **Dictation earns its extension** | Dictation share of `capture_committed`, weeks 3-4 | Dictation ≥ **20%** of captures → extend to both chat composers and all 31 `ProfileEditorViews` instances | **< 10%** → dictation is a nice-to-have; leave it in onboarding, ship nothing further. §4's case against wins |
| **T5** | **Voice-in/text-out is the right architecture** (Ruan's repair finding, in the field) | `edited_before_commit` and `chars_changed` on dictated captures | Parents edit **>25%** of dictated captures → the editable-transcript law is load-bearing, keep it everywhere | <5% edits → either recognition is better than the literature predicts, or parents are committing wrong data. Cross-check against `obligation_dropped` before celebrating |
| **T6** | **Is conversational voice a car feature?** (P8 §8's test, which I endorse) | `voice_call_started` by `local_hour`, plus `abandoned_within_15s` | Sessions spread across the day with <20% 15-second abandonment → the ceiling really is moving; revisit | Sessions cluster into commute windows (7-9am / 4-6pm) or >40% abandon in 15s → voice here is a car feature, not a planning feature. **Confirms the keep-but-don't-extend call** |
| **T7** | The public-use social barrier, in behaviour | Dictation and voice-call rates by `local_hour` and day type, as a proxy for private vs semi-public context | Evening/at-home skew mirroring PwC's 74%-in-home → the barrier is real and voice is a home behaviour | Flat across the day → the shame finding (German, intention-only) does not transfer to US parents; loosen the placement constraints |
| **T8** | **Extraction reliability vs the trust cliff** | `items_kept / items_returned` and `fields_corrected[]`; then 30-day retention of parents who hit **≥1** wrong extraction vs those who hit none | Retention gap **<10pp** → it is a gradient after all | Gap **>25pp** → M1's trust cliff is real; raise the extraction bar before promoting the camera at all. **This test gates T3's rollout** |
| **T9** | **The capture/reference split is a real product opportunity** | Instrument `reference_view` and `share_link_opened`; ship (a) ICS + a printable/castable week before building (b) the automated weekly transposition | Weekly `reference_view` per active user **≥2**, or ≥30% of families open a share link more than once → §2 is a market, fund (b) | <1 reference view/week and share links opened once-and-never-again → the split is real in life but our surface is not where parents do reference. Do not build the transposition engine |
| **T10** | Spoken output (the M2/M5 inversion) | Opt-in morning/evening briefing to a small cell; measure opt-in, retention of the opt-in, and **notification delivery success** | Opt-in retained ≥4 weeks by ≥30% of the cell, with ≥99% delivery | Delivery <99% → **stop immediately.** M4: missed-notification complaints are 14-15% of reviews and *"the angriest in the corpus"* — an unreliable outbound channel is worse than none |

### 5.3 What NOT to measure

- **Do not** measure "voice usage" as one number. Merging dictation, the Coach call, and any future
  assistant command reproduces exactly the bucket error that makes all published research
  (Edison, Pew, eMarketer) useless for this decision. Three behaviours, three event families, always.
- **Do not** read week-1 modality share as preference. Novelty inflates the newest affordance; T4's
  threshold is deliberately scoped to weeks 3-4.
- **Do not** treat absence of voice complaints as satisfaction. V5's 1-hit-in-15,692 result on partner
  non-adoption is the standing proof that this corpus class cannot see quiet non-use.

---

## 6. CONSISTENCY CHECK AGAINST S0 AND S2

- **S0 §4.2** (the `OBLIGATION` atom; three states; sort by date): every modality above lands in that
  one atom. The matrix is the input layer for S0's schema, not a competing design.
- **S0 §4.3** (P5's offloading tax; *"one gesture, not a form"*): §3.1's single capture bar is the
  literal implementation. S0's line *"and there is no dictation anywhere in the app"* is now stale —
  V3 corrected it; there is dictation, in onboarding only.
- **S2 §1.3** (photo ingest DOUBLE DOWN, promote out of the Planner; dictation DOUBLE DOWN, extend;
  manual add BUILD-NEW as the single highest-priority item; inbound forwarding BUILD-NEW): §3.1
  ratifies all four and adds one fact S2 did not have — **the in-app camera already exists in
  onboarding**, which lowers the cost of S2's D-list item.
- **S2 §1.4 / §2.7** (parent voice calls KEEP-BUT-DEPRIORITIZE; kid companion CUT): §3.1 restates both
  without extension.
- **S2 §3.5** (the one adjudicating test): adopted unchanged as T1, with S2's two sharpenings (run in
  the Sept/Oct dead window; measure week-4, not week-1) carried into §5's fielding conditions.

**Corrections this report contributes back:**
1. **The BRIEF's "photo/flyer ingestion (PhotosPicker; no in-app camera)" is now wrong.** A camera
   exists: `HeismanCameraCapture` at `mvp/MVP/OnboardingHeismanExtract.swift:482`, presented at `:83`,
   `NSCameraUsageDescription` at `mvp/MVP/Info.plist:11` — onboarding only. `IngestView.swift:146`
   remains PhotosPicker-only.
2. **The text-entry count, re-measured after the Heisman rewrite:** 61 instances (53 `TextField`, 7
   `TextEditor`, 1 `SecureField`); `ProfileEditorViews.swift` holds 31. Dictation reaches 3, all in
   onboarding — so **58 fields have no mic**, a coincidence that preserves the BRIEF's figure.
3. **Dictation is instantiated five times across four files**, not four: `OnboardingHeismanExtract.swift`
   holds two controllers (`:26` and `:27`).
