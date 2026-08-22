# Heisman Sprint 01 — Onboarding

> Ingested 2026-08-21 from Greg's design-spec PDF (`sprint-01-onboarding-spec.pdf`, 9 pp).
> Figma: [mvp-heisman → section "Heisman" `43:8343`](https://www.figma.com/design/nAXZQhmvwEpzq3rkBisok7/mvp-heisman?node-id=43-8343&m=dev).
> Engineering decisions and scope overrides recorded in the **Appendix** at the bottom —
> where the appendix and the designer text conflict, the appendix wins.

**Design spec companion** — Design · Product Owner · Engineering. Status: decisions
resolved, pending design corrections and sizing review. Sprint 01 — Onboarding.

## How to use this document

A spec will accompany every design sprint. It is linked to the Figma section as a Dev
Resource so it travels with the frames — the design and the spec arrive together.

It is written for two readers: the Engineering representative picking up the work, and
the coding agent they are driving. That second reader is the reason for the *Out of
scope* and *States* sections. An agent reading a screen has no concept of sprint
boundaries or unrendered states unless they are written down. **Anything left blank gets
invented.**

**Sequence**: Design drafts → review with Product Owner (is this the right thing) →
review with Engineering (is this the right size) → Design revises → frames marked ready
for dev → build.

If a feature cannot be described with testable acceptance criteria, it is sized wrong.

**Scope note.** This sprint forks the existing onboarding flow — it is not a rebuild. It
reuses the same underlying data (children, selected topic, selected tasks) under a
faster, shorter presentation. Twelve frames are new or revised this sprint. Five more
appear in the flow table below purely for continuity — they are already built and
shipping, and this sprint does not modify them. They're included so the handoff point
between new and existing is visible in one place, not so they get rebuilt.

## 1. Scope

### The flow

| Frame | Figma node | Step | Status | Purpose |
| --- | --- | --- | --- | --- |
| Onboarding - 0 | `29:2778` | — | New/revised | App loading splash |
| Onboarding - 1 | `37:5704` | — | New/revised | Cold open. Capture user name and location |
| Onboarding - 2 | `37:5705` | 01 | New/revised | Capture first child: name and age |
| Onboarding - 3 | `38:5726` | 02 | New/revised | Parent picks one thing the coach should take on. Parent can enter their own text |
| Onboarding - 4a | `38:5724` | 03 | New/revised | Sample problem, based on the choice made in step 02 — freeform text or voice input |
| Onboarding - 4b | `38:5723` | 03 | New/revised | Sample problem — variant, not present in the section *(PDF said missing; frame exists in Figma)* |
| Onboarding - 4c | — | 03 | New/revised | Sample problem — choose an image or photograph a flyer *(listed in PDF; no separate frame in Figma — see drift note)* |
| Onboarding - 5 | `38:5722` | 04 | New/revised | Extracted data presented back as a sample plan. Parent can update or edit the cards |
| Onboarding - 6b | `38:5720` | 05 | New/revised | Parent selects real tasks for the coach to take on *(Figma frame is named "Onboarding - 6": "What about you — what's your to-do this week?")* |
| Onboarding - creating account | `29:4270` | Interstitial | **Existing** | A beat presenting a snapshot of the features in the plan |
| Onboarding - 7 | `42:8320` | — | New/revised | Coach demonstration |
| Onboarding - 8 | `42:8321` | — | New/revised | Account creation |
| choose a plan | `29:3563` (monthly) / `29:3635` (annual) | — | **Existing** | Parent selects a plan to secure the account |
| one last thing | `29:4183` | — | **Existing** | Fill in required data for the agent — parent and children handled separately |
| Onboarding - 9 | `42:8322` | — | New/revised | Day zero summary — home screen built from onboarding inputs |
| edit kid details - 001 | `29:4324` | — | **Existing** | Add unique data for a child |
| edit kid details - 002 | `29:4481` | — | **Existing** | Shows a child profile with the updated data |

### Progress indicator

Five steps. Steps 01–05 map as above. The agent will not infer these boundaries.

## 2. Out of scope *(designer's original fences — see Appendix for engineering overrides)*

- **Voice transcription.** The microphone appears on 1:549 and on the step 04 frames.
  Visual only this sprint. Do not integrate ElevenLabs, do not request microphone
  permission, do not add audio session handling. *(OVERRIDDEN — see Appendix A2.)*
- **Camera and photo library.** Frame 4c shows image capture. Extraction from an image
  is not built this sprint. *(OVERRIDDEN — see Appendix A2.)*
- **The coach pipeline.** Screens 5, 7, and 9 show sample coach output. *(Partially
  overridden — screen 5 shows REAL extraction output; screen 7 stays locked copy. See
  Appendix A2.)*
- **Kid companion.** Not in V1. If a string or asset referencing it survives in these
  frames, it is a leftover. Flag it, do not build it.
- **Olive tokens.** Nine layers in 1:1011 remain bound to
  `primitives/brand/olive-500/700`. Deliberately parked. Do not rename or rebind; that
  happens in the token reconciliation PR.
- **Navigation stack.** Do not restructure app-level navigation to accommodate this flow.

## 3. Screen specs

### Onboarding - 0 · Splash

App loading. No interaction, no data, no step count.

### Onboarding - 1 · Cold open

Entry screen. Capture user name and location.

### Onboarding - 2 · Children

**Purpose.** Capture the children the coach plans around. 2a takes the first child's
name and age. 2b takes additional children, and several can be added without leaving the
step.

**Behavior.** Adding a child appends a row rather than advancing — the parent controls
when the step ends. Rows are removable. Continue is disabled until at least one child
has both a name and an age.

**Data.** Writes an ordered list of children, each with a name and an age. This is the
only onboarding data guaranteed to reach the day zero summary. See D4.

*States table and edge cases need an MCP pull of both frames before handoff.*

### Onboarding - 3 · Step 03 · Topic selection

**Purpose.** The parent names one thing they want handled. Single-select.

| Element | Default | Selected | Disabled | Notes |
| --- | --- | --- | --- | --- |
| Topic card ×6 | `bg/elevated`, `border/strong` 1px, r12 | `accent/tint` fill, `accent/default` border | n/a | Single-select |
| Free-text field | `bg/elevated`, `border/hairline` 1px, r24, placeholder "Something else..." | — | n/a | No character limit |
| Mic button | icon 24px | n/a | n/a | Visual only *(OVERRIDDEN — real dictation, Appendix A2)* |
| Continue | `accent/default` fill, `ink/onPhoto-light` label | pressed uses `accent/press` | disabled until the step has an answer | Not skippable |
| Progress | `accent/default` at 30% opacity, "03 of 05" mono | n/a | n/a | |
| Back | 16×13 glyph on `bg/canvas` | n/a | n/a | Returns to 1:516 |

**Behavior**

- Tapping a card selects it; tapping another moves the selection.
- The free-text field and card selection are alternative routes to the same answer, not
  additive. Using one clears the other.
- Continue is disabled until a card is selected or the text field is non-empty.
- Continue advances to step 04 carrying the topic.
- Back returns to 1:516 with the previous answer intact.

**Data.** One value — an enum for the six cards or a free string. No character limit.
Read again on 1:940 to shape the coach demonstration.

### Onboarding - 4a, 4c · Step 04 · Sample problem

**Purpose.** The parent hands the coach a real-world scrap, the kind of thing that
arrives by email or group text, and watches it become structure. Four input methods
across the variant set: freeform text, voice, choosing an existing image, photographing
a flyer.

**Behavior.** All routes produce the same downstream result this sprint — static
extracted output on 1:732. Pickers and the microphone may open; nothing is parsed.
Continue is disabled until an input exists. *(OVERRIDDEN — all routes run REAL
extraction; see Appendix A2.)*

**Data.** Demonstration only. Step 04 input does **not** persist to the day zero
summary. *(OVERRIDDEN — extraction results persist and seed real plan items; Appendix
A2.)*

*Frame 4b is missing from the section. Resolve before handoff.* *(Frame 4b `38:5723`
exists in Figma as pulled 2026-08-21; no 4c frame found — see drift note.)*

### Onboarding - 5 · Sample plan

**Purpose.** Show the extracted data back as a structured plan. The payoff for step 04,
and the first time the coach performs its core value.

**Behavior.** Read-only. No editing this sprint. Advances to step 05.

**Copy.** Static. Coach output follows the voice rules in DESIGN.md — reference them, do
not restate or paraphrase. *(Static fallback only — the primary path renders real
extraction output; Appendix A2.)*

### Onboarding - 6b · Step 05 · Task selection

**Purpose.** The parent hands over real tasks. Multi-select.
*(Figma frame `38:5720`: "What about you — what's your to-do this week?" — the parent's
OWN weekly to-dos: gift to buy, grocery/dinner run, errand, house work, medical
appointment, date night, exercise or gym, social commitment + free text + mic.)*

**Behavior.** Multiple tasks can be selected. This is the only skippable step. Skipping
commits no task data and advances to 1:940. Continue is enabled with zero selections,
since skip and proceed lead to the same place.

**Data.** Writes zero or more tasks. Feeds the day zero summary.

*Skip affordance and selected state are not yet designed — see section 2.*

### Onboarding - 7 · Coach demonstration

**Purpose.** The coach performs before the account wall.

**Copy.** The approved screen 7 dialogue is locked in DESIGN.md. Reference it. Do not
paraphrase, do not generate alternates.

### Onboarding - 8 · Account creation

**Purpose.** Account wall, placed after the demonstration.

*Needs a full states pass — sign-in providers, error states, validation. Highest
behavioral weight in the sprint after 1:867.*

### Onboarding - 9 · Day zero summary

**Purpose.** The home screen, built from what onboarding collected. First real surface
after account creation.

**Behavior.** Renders from children (steps 01–02) and tasks (step 05). If step 05 was
skipped, the summary shows only the children entered during onboarding.

## 4. Acceptance criteria

Runnable by Design or the Product Owner against a TestFlight build with no Engineering
representative present. If a criterion cannot be checked by tapping, it is not a
criterion.

1. Multiple children can be added on step 02 without leaving the screen; each appears as
   a removable row.
2. Continue on steps 01–04 is disabled until the step has an answer.
3. Step 03 allows exactly one topic; tapping a second card moves the selection.
4. Typing in the step 03 free-text field clears any card selection and accepts input of
   any length.
5. Step 05 allows multiple task selections.
6. Step 05 is skippable. No other step offers a skip.
7. Skipping step 05 produces a day zero summary containing only the children from steps
   01–02.
8. Completing step 05 produces a day zero summary containing those tasks.
9. The progress indicator reads 01 through 05 and never exceeds 05. Screens 0, 1, 5, 7,
   8, 9 show no step count.
10. All step 04 variants advance to the same sample plan on 1:732.
11. No microphone or camera permission prompt appears anywhere in the flow. *(OVERRIDDEN
    — mic/speech/camera prompts are expected on first use of dictation/capture;
    Appendix A2.)*
12. Every surface renders from a semantic token — no hardcoded colors, no drop shadows
    on text.

## 5. Resolved decisions

Recorded so the reasoning survives the sprint.

| ID | Decision | Consequence |
| --- | --- | --- |
| D1 | Step 03 single-select; step 05 multi-select | Two card behaviors in one flow. One component with a selection mode, or two components. |
| D2 | Step 05 is the only skippable step | "Not right now" comes off 1:549 and goes onto 1:867. |
| D3 | Five steps total; 4a/4b/4c are variants of one step | Progress indicator stays stable across the variant set. |
| D4 | Skipping step 05 leaves the summary showing children only | Step 04 input is demonstration data and does not persist. *(OVERRIDDEN for the extraction half — Appendix A2.)* |
| D5 | No character limit on free text | No truncation logic, no counter. |
| D6 | Off-ramp greys map to existing tokens | Design task, no new tokens. |

## 6. Questions for Engineering at sizing review

- D1 gives two card behaviors. One component with a selection mode, or two? Which is
  cheaper.
- Does the day zero summary need a data model beyond the children list and the task
  list, given step 04 does not persist?
- Steps 04 and 05 open OS-level pickers that do nothing this sprint. Is stubbing them
  cheaper than hiding them?
- Twelve frames: one ticket or several? If several, where do the seams fall.
- Anything here that touches files outside the onboarding module.

## 7. Handoff checklist

Design completes before marking the section ready for dev.

- [ ] Every frame has a purpose line and a states table
- [ ] Every interactive element has its states enumerated, including states not drawn
- [ ] Out of scope names specific things, not categories
- [ ] Acceptance criteria are tappable
- [ ] Resolved decisions table is current
- [ ] Annotations pinned in Dev Mode at the point of ambiguity
- [ ] MCP pull on one frame returns tokens only, no raw hex, no stray effects
- [ ] This document linked to the section as a Dev Resource
- [ ] Section marked ready for dev; frames frozen until sprint closes

---

## Appendix — Engineering decisions & drift log (Miguel + Claude, 2026-08-21)

### A1. Resolved forks

- **Pre-account data lives client-side only** (extended `OnboardingDraft`); the seed
  fires after account creation at step 8. No anonymous server *accounts*, no TTL reaper
  — abandoned funnels die on the device.
- **Email auth deferred.** The account wall's "Use email instead" link is omitted this
  sprint; Apple/Google only. Needs its own states pass + email-auth design later.
- **Onboarding-9 is a full Home redesign** — it replaces `HomeView`, not a one-time
  first-run screen.
- **CMS gains a "reset a tester" action**: wipes all family data but keeps the auth
  identity, so Miguel/Heather/Greg can re-run onboarding on their real accounts
  (reset → sign out in app → relaunch → funnel → sign in at step 8 → continue).

### A2. Scope overrides (Miguel, product owner)

Mic/dictation and image extraction ARE in scope and must work **unauthenticated**:

- **Dictation** = on-device `SFSpeechRecognizer` (still no ElevenLabs). Mic + speech
  permission prompts are expected on first use (acceptance #11 overridden).
- **Image + text extraction** = stateless anonymous backend:
  `POST /onboarding/anon-session` (IP rate-limited) mints a short-lived scoped token;
  `POST /onboarding/extract` takes freeform text or an image and returns structured
  `{who, what, when, where}` activities. Nothing is persisted server-side.
- **Screen 5 renders the real extraction result** (static sample copy is the
  fallback when extraction was skipped or failed).
- **Extraction results persist** in the draft and ride the post-account seed into real
  `tracked_activities` (D4 half-overridden; the *task-skip* half of D4 stands).
- Screen 7 coach demonstration remains locked copy, templated with real names/data.

### A3. Spec ↔ Figma drift (flag to Greg)

- PDF lists frames **4c** and **6b**; the Figma section has **4a `38:5724` / 4b
  `38:5723`** (no 4c) and **6 `38:5720`**. The PDF's own note says 4b was missing —
  frames have moved since the PDF was written. Image-capture UI (4c) has no dedicated
  frame; engineering will place the image/camera affordances per 4a/4b patterns.
- Node references `1:516`, `1:549`, `1:732`, `1:867`, `1:940`, `1:1011` in the PDF
  predate the current section (nodes are now `29:*`–`43:*`); mapped by frame name.
- The locked screen-7 dialogue and coach voice rules are said to live in DESIGN.md —
  verify `spec/look-and-feel/DESIGN.md` actually contains them; if not, request from
  Greg.
- Step-05 skip affordance + selected state: not yet designed (designer's own flag).
- Onboarding-8 needs a full states pass (designer's own flag).

---

## Appendix B — Build record (engineering, 2026-08-21)

Frames pulled per screen via the Figma MCP (`get_design_context` + screenshot)
before implementation; the hex → token mapping used consistently across the
implementation is documented at the top of `mvp/MVP/OnboardingHeismanChrome.swift`.
Two hex drifts flagged to Greg: the file's `border/strong` resolves to
`#4A4741` (app `borderStrong` is `#8A8275` — implemented with the app token
per the sprint instruction), and screen 7's `ink/muted` resolves to `#4A4741`
(nearest app ink `inkSecondary` `#2D2D2D` used).

### Glyph exports (node id → imageset)

All exported as SVG via MCP `download_assets`, backdrop rects/overlay paths
stripped, single-SVG imagesets with `preserves-vector-representation`;
template rendering intent on every single-color glyph (multi-color marks and
the Google G omit it).

| Node | Asset | Notes |
| --- | --- | --- |
| `29:2779` | `OnboardingHeismanMark` | splash tumbler mark — TRUE VECTOR (black `#151412` + gold `#E8A33C`), multi-color, no template |
| `29:2299` | `OnboardingHeismanMarkSM` | 51×97 small mark on the cold open, multi-color, no template |
| `29:2408` | `OnbTopicIcon-dinner` | template |
| `29:2414` | `OnbTopicIcon-practice` | template |
| `29:2421` | `OnbTopicIcon-appointment` | template |
| `29:2427` | `OnbTopicIcon-playdate` | template |
| `29:2434` | `OnbTopicIcon-school` | template |
| `29:2440` | `OnbTopicIcon-birthday` | template |
| `29:2447` | `OnbIcon-mic` | template |
| `29:2448` | `OnbIcon-waveform` | template |
| `29:2474` | `OnbIcon-paste` | segmented-control clipboard, template |
| `29:2478` | `OnbIcon-photo` | segmented-control image icon, template |
| `29:2519` | `OnbIcon-camera` | template |
| `29:2751` | `AuthLogo-google` | multi-color Google G, no template |
| `29:2760` | `AuthLogo-apple` | template (native SignInWithAppleButton is what ships; asset kept for a custom variant) |

SF-symbol carve-outs (generic system glyphs the frames draw no purpose
shapes for): header back arrow (`arrow.left`), screen-7/8 back chevron
(`chevron.left`), extraction-row chevron (`chevron.right`), check marks
(`checkmark`), child-row remove (`xmark.circle.fill` — no remove affordance
drawn in the frame at all; rows must be removable per acceptance #1).

### Step indicator, as stamped on the frames

01 = cold open · 02 = children · 03 = topic AND sample problem (D3) ·
04 = extraction check · 05 = parent tasks. Rail fills measured 77/77/154/264/365
on the 365pt track; mono ink `#6E6A62` on 01–02, `#C8C3B8` from 03; track at
50% opacity on 01–02 only.

## Appendix C — Verification record (2026-08-21)

- **"one last thing" replaced by Greg mid-sprint**: old node `29:4183` deleted; the new
  frame is **`69:1313`** at page level (outside the Heisman section). New design: coach-
  voiced household card (Household Type + Language dropdowns) + per-kid "Tell me about
  {kid}" cards (age / grade / school-style dropdowns + four expandable free-text rows:
  into · would rather avoid · what's hard right now · where they shine) + "Set up later".
  Rebuilt onto `SetupTailView`; per-kid `school_style` added to ChildProfile (backend +
  iOS DTO).
- **Simulator E2E (fresh-erased iPhone 17 Pro, local backend)**: full funnel walked —
  cold open → children (row append/remove, gate) → topic (select + move, XOR field) →
  sample problem (typed scrap) → **live anonymous extraction** (anon-session minted,
  `[COST][LLM]` logged, one activity) → extraction check rendered the REAL who/what/
  when/where → parent tasks (2 selected) → getting-ready theatre → coach demo templated
  with the real data + "Remind me Friday about a gift to buy" → account wall
  (auto-advanced under UITEST_SKIP_SIGNIN) → paywall → warmup → "You're all set".
  Day-zero Home verified with the seeded user: per-person today cards incl. the
  parent's own card (kid_name NULL rows), live coach nudge card, black kid tile,
  editorial with real articles.
- Fixed during the pass: getting-ready headline vertical truncation
  (`.fixedSize(horizontal: false, vertical: true)`).
- Backend suite 581 passed post-integration; `lint-design-tokens` clean; combined
  xcodebuild SUCCEEDED; iOS bumped **104 / 1.90**.
