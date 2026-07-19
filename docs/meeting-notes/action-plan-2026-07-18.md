# MVP Action Plan — July 18, 2026

*Synthesized from the July 15 sync (Gemini notes), Heather's follow-up notes, and the
original June 5 "meeting of the minds." Owners: Miguel (build), Heather (product +
knowledge), Greg (design).*

---

## Where we are, in one paragraph

The product the June meeting sketched is built and live: the planner (chief of staff)
handles camps, weekly classes, school life, outings, and trips through one agent; it
watches registration windows and reminds you before they open; it reads Gmail, syncs
Google Calendar both ways, and turns flyers and pasted messages into calendar entries
and to-dos; the coach and the kids' companions work by text and voice with the full
safety layer; and a public illustrated "How MVP works" site ships with the product.
What follows is the plan for the next layer — the two directions Heather's notes call
for, plus everything we agreed on July 15.

---

## Workstream A — The Planner reads everywhere you do

**Heather's ask:** the scheduler must be able to grab schedule/logistics info from ANY
place a family indicates — Brightwheel, G Suite, WhatsApp, ParentSquare, and so on —
and aggregate it in MVP.

**What already works today:** Gmail (a daily agent reads activity email), Google
Calendar (two-way sync), paste any text, snap a photo of anything (the vision pipeline
extracts every item on a flyer or newsletter, with the source sentence shown next to
each extracted deadline).

**The honest technical picture:** Brightwheel, ParentSquare, and WhatsApp have no
public APIs a parent-side app can plug into. But every one of them already passes
through two choke points we can own: **email** (Brightwheel and ParentSquare send
digest emails; almost everything school-related does) and **the phone's share sheet /
screenshots** (anything on a screen, including WhatsApp messages). So the strategy is
capture-at-the-choke-point first, direct integrations only where a real API exists and
demand proves it.

**Phase 1 — universal capture (build next):**
1. **The magic forwarding address.** Every family gets a private MVP email address.
   Forward anything to it — a Brightwheel digest, a ParentSquare announcement, a camp
   confirmation — and it lands in the planner like a pasted message. This is the same
   mechanism our GTM already promises for the second parent ("no app, no account —
   just forward it"), so one build serves both. Auto-forwarding rules (set once in
   Gmail/Outlook) make it hands-free.
2. **"Share to MVP" (iOS share sheet).** From WhatsApp, ParentSquare, Safari, Photos —
   share any message, screenshot, or page straight into the planner. This makes
   "ANY place" literally true without a single partnership.
3. Screenshots already work — we market this harder ("screenshot the group chat,
   we'll do the rest").

**Phase 2 — per-source smarts.** Tune the extractor on real samples from each source
(Brightwheel digests look different from PTA newsletters). We already run this
flywheel for school flyers: real samples become test fixtures, every miss becomes a
fix. **Heather: forward 5–10 real digests/messages from each source you use
(Brightwheel, ParentSquare, WhatsApp school groups) — that's the fuel.**

**Phase 3 — direct integrations,** only where an API actually exists and beta demand
points (e.g., school calendar subscriptions/ICS feeds are easy wins; Brightwheel API
access would require a partnership conversation).

---

## Workstream B — The coach as curator: "the mom next door"

**Heather's ask:** the coach needs a way to extract and integrate HER recommendations
for the topics we originally earmarked — she brain-dumps her battle-tested knowledge
per topic, and the coach becomes a curator of it, tailored to each family. This is the
original framing: human communication, the mom next door who knows all the
battle-tested stuff. The personalization MVP provides — her knowledge combined with AI
and the family profile — is the secret sauce.

**Answer to her direct question: yes — buckets plus brain-dumping is the right
mechanism.** Here's the concrete shape:

1. **The buckets.** We seed them from the content taxonomy already in the product
   (11 top-level topics — sleep, behavior, school, siblings, screens, etc.) plus the
   list from our original discussions. Heather owns the list: add, split, rename.
2. **The brain-dump (intake).** Per bucket, whichever is easiest per topic:
   - **Voice memo** — talk for 20–30 minutes like she's telling a friend everything
     she knows about, say, bedtime battles. We transcribe and structure it.
   - **Curator interview** — a dedicated agent session that interviews her per bucket
     ("what age does this apply to? what do people get wrong? what's the first thing
     you'd try?"). This is her "talking to the coach" idea, formalized.
   - Existing docs/notes she already has — paste or forward them.
3. **The playbook.** Each dump is distilled into reviewable entries: the
   recommendation, when it applies (age band, situation), why it works, and her
   phrasing kept intact — the voice IS the product. **Heather reviews and approves
   every entry**; curation stays human.
4. **The coach retrieves and personalizes.** When a family hits a bedtime question,
   the coach draws on Heather's playbook first, tailored by what it knows about that
   family (kid's age, temperament, what's been tried). Battle-tested beats generic —
   this is precisely what raw ChatGPT can't do.
5. **Two boundaries that keep us honest:** (a) founder/expert intake is a separate
   pipeline from user-coach conversations — the zero-retention posture on user coach
   chats (our GTM privacy commitment) is untouched; (b) safety-sensitive topics stay
   under the existing moderation and crisis rules regardless of playbook content.

**Bonus synergy:** every approved playbook entry can also become a content-library
article — the "knowledge-trading" idea from the original discussions, delivered
through both the library and the coach.

**Pilot (2 weeks):** Heather picks ONE bucket she knows cold → one voice-memo dump →
Miguel builds the intake-to-playbook pipeline against it → we A/B the coach's answers
on that topic with and without the playbook, on our own families first.

---

## Locked decisions from July 15 (for the record)

| Decision | Note |
|---|---|
| Beta is **free** — payments deferred | Stripe coupons later for paywall testing; Greg drafts subscription/payment screens as placeholders |
| "Circle" → **"Team"** | Terminology research still open on team-vs-family concepts |
| "Schedule" → **"Planner"** | Terminology research with younger-parent demographic (Miguel + Heather) |
| **Saved items** gets a main-nav tab | Temporary placement until design sprint settles it |
| **No photo sharing** in beta | Moderation/CDN/security burden not worth it now |
| External invites yes; internal team/circle logic deferred | |
| **Zip code captured early** in onboarding, typed not IP-guessed | Backend already stores it; the change is asking earlier + conversationally |
| Onboarding moves from dense forms toward **conversational** collection | Design sprint #1 territory |
| **Kids' companions deferred to a future paid release** | Stays built, stays out of beta scope and GTM |
| **3 design sprints** (Greg, ~2 weeks): onboarding · core nav/dashboard · profile/settings | |
| Cloud credits: AWS/Azure startup programs ($20k–100k) | Docker-portable architecture keeps us provider-flexible |
| Early investor conversations with key AI contacts; build in the open | Show adoption + engagement metrics |
| Neuroscience advisor to deepen the profiling moat | |

## Added July 18

- **Pursue ISO certification for security and privacy** — ISO/IEC 27001 (information
  security) and ISO/IEC 27701 (privacy). This turns our security posture from a
  claim into a credential: it strengthens the trust kit (a family app holding kids'
  data), differentiates against every consumer competitor (none are certified), and
  is close to a prerequisite for the B2B2C channels in the GTM (employers/EAPs,
  mediator/therapist networks vet vendors on exactly this). First step is a scoping
  pass — gap analysis against the current hardening work, cost, and a realistic
  timeline — not a commitment to certify before beta.
- **Scope the release ladder: friends & family → private beta → public beta.** Define
  each stage before the first invite goes out: who's in it and how many, what has to
  be true to enter it (feature scope, stability bar, support load we can absorb),
  what we're trying to learn from it, and the graduation criteria to the next rung.
  "Beta" stops being one word and becomes three gates with numbers.

## Action items

| Owner | Action | Status / next step |
|---|---|---|
| Miguel | Send meeting summary + this action plan | This document |
| Miguel | Beta features punch list (saved-items tab, rename Team/Planner, early-zip onboarding) | To scope this week |
| Miguel | **Workstream A phase 1**: magic forwarding address + share-sheet extension | Next build block |
| Miguel | **Workstream B pilot**: intake→playbook pipeline for one bucket | After Heather's first dump |
| Miguel | Apply for AWS + Azure startup credits | Applications this week |
| Miguel | Contact neuroscientist about advisory role | |
| Miguel | Scope the ISO 27001/27701 path — gap analysis, cost, timeline | New (July 18) |
| Heather | **Forward 5–10 real samples each** from Brightwheel, ParentSquare, WhatsApp groups | Fuel for Workstream A phase 2 |
| Heather | Pick pilot bucket + record first brain-dump voice memo | Kicks off Workstream B |
| Heather | Review/adjust the bucket list (seeded from the content taxonomy) | |
| Heather | Share matriarch investor deck sample | |
| Heather + Miguel | Planner/Scheduler terminology research | |
| Greg | Schedule + run the 3 design sprints; share Figma link + sprint list | In motion |
| Greg | Design: saved-content strategy, payment placeholder screens, onboarding zip step | Within sprints |
| Group | Team-vs-family concept research | |
| Group | Scope the release ladder: friends & family → private beta → public beta (entry bars, cohort sizes, learning goals, graduation criteria per stage) | New (July 18) |

---

*The through-line, from June 5 to now: the app is the mom next door — she knows
everybody's schedule (Workstream A) and she's seen everything before (Workstream B).
Everything above serves one of those two sentences.*
