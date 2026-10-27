# MVP — investor narrative

Pre-seed. Written for a partner who gives the deck two minutes and twenty-four seconds.
Revised after the Fadell / Jobs / Horowitz passes, recorded in `critics.md`.

This file is the argument and the script. The exact rendered copy lives in `build_deck.py`, which
is what actually generates the pptx. A few cards were tightened during layout to keep slides off
the footer line; where the two differ, the build script is what the deck says.

---

## The dinner-table version

> Agentic AI arrived for people who can drive it. Engineers got Claude Code and turned into
> teams. Parents got a chatbot with no memory of their family. MVP is the agent for the last
> unmanaged operations job in America — raising kids.

If a reader can repeat those two sentences to their partner over dinner, the deck worked.

---

## The kernel

**Diagnosis.** Coordinating a family is an operations job. A two-kid household tracks more entities
under more constraints than most small businesses: registration windows, age cutoffs, overlapping
pickups, two calendars, a school that communicates by PDF. Every comparable job in the economy got
real software. This one got a shared calendar and a group text, and the load lands on one parent's
memory. The reason nobody solved it is not that the market is small — parents already pay, and pay
twice. It is that the job requires an agent that can be trusted with a deadline, and until roughly
eighteen months ago no such thing existed. Milo tried, and said so on the way out.

**Guiding policy.** Build the agent for one acutely painful, seasonally forced slice of the job —
the activities and coverage a parent has to secure before a window closes — and make it work for one
parent alone. Earn the right to the rest of the job by being the thing that never lets a deadline
pass. Treat reliability and child safety as the product, not as compliance.

**Coherent actions.** Ship the five doors into one agent so a single relationship covers camps,
classes, school life, outings and trips. Watch registration windows nationally, and run an alarm
that watches the watcher. Ingest the flyer, the email, the photo of the form, so the parent stops
transcribing. Keep the second parent included by calendar invite and forwarding address, never by an
install. Hold the kid-facing companion out of the market until COPPA is done.

---

## What we refuse

Four refusals, and at least one costs us money.

1. **We will not build for the courtroom.** The incumbents monetize conflict by making a record
   admissible in court. We prevent the fight instead. This forfeits the highest-intent, highest-ARPU
   segment in the category — parents in active litigation.
2. **We will never require the other parent.** Nothing is gated on a second install, a second
   account, or a second payment. Every competitor's growth loop depends on exactly that.
3. **We will not market to children.** The kid companion is real and it works. It stays out of
   go-to-market until COPPA compliance is finished, which means we are sitting on our most demo-able
   asset.
4. **We will not take money in the transaction.** No bookings, no payments on the parent's behalf,
   not in v1. The marketplace is the second act; taking a cut before we've earned trust would poison
   the advice.

---

## Slide-by-slide

16 slides, plus a second version of slide 15 to choose between. Eyebrow in JetBrains Mono, title in Fraunces 54, body and cards in Inter.
Speaker notes follow Heather's one-line-intent convention.

---

### 01 — Title

**Wordmark** MVP · Most Valuable Parent
**Title** Nobody should have to be the only one who remembers.
**Sub** MVP finds the camps, watches the registration windows, and turns the school's PDF into both
homes' calendars. It works even when only one parent uses it.
**Footer** Pre-seed · 2026 · Heather Hannan-Kramer · Miguel Alvarado

> *Note: One sentence they can repeat to their partner. Say it and move on.*

---

### 02 — The thesis

**Eyebrow** THE THESIS
**Title** Agentic software escaped the enterprise.
**Body** Two years ago, AI that could actually *do* things — hold the whole context, make a plan,
take the next step, be trusted with the result — arrived for engineers. Claude Code turned one
engineer into a team. That capability is general now. It has not reached the household.

| Card | Copy |
| --- | --- |
| What engineers got | An agent that holds the context, works while they sleep, and hands back finished work. |
| What parents got | A chatbot that has never heard of their kids. |
| What we built | The first one, pointed at the second job. |

> *Note: This is the whole company in one line. Say it and stop talking.*

---

### 03 — The problem

**Eyebrow** THE PROBLEM
**Title** The last unmanaged operations job in America.
**Body** Sales got Salesforce. Engineering got Claude Code. The family got a group text.

| Card | Copy |
| --- | --- |
| **85%** | of parents lose sleep over summer care and scheduling. 90% among working parents. *Bright Horizons Modern Family Index, Harris Poll, April 2026* |
| **80+** | school and activity emails a month. *Yahoo/Censuswide, June 2024* |
| **62%** | have already missed something buried in one. |

> *Note: Three numbers, no argument. Every parent in the room is doing the math on their own inbox.*

---

### 04 — Why now

**Eyebrow** WHY NOW
**Title** Milo was right in 2024. They are wrong in 2026.
**Pull quote** "the technology is simply too early to be reliable in any useful way"
— Milo, shutting down, 12 January 2026

| Card | Copy |
| --- | --- |
| Agents crossed the reliability line | Tool-calling plus real eval infrastructure is the difference between a demo and a deadline. That gap closed in the last eighteen months. |
| Voice went conversational | Sub-150ms. A parent in the carpool line can talk to it now. |
| The category cleared | Milo closed January 2026. Yohana left the US in September 2025. |

**Bottom line** Yes, this category has killed companies. They died on a technology that arrived
about a year after they needed it. Meanwhile TalkingParents killed its free plan in March 2026 and
AppClose went paid in January — demand is inelastic enough to raise prices into. Nobody still
standing has the agent.

> *Note: A competitor's own words are the timing argument. The bottom line answers the skeptic
> before they raise it.*

---

### 05 — The moment

**Eyebrow** THE JOB
**Title** It's 11pm and she just remembered the deadline.
**Body** That is the moment we are building for. She doesn't need advice, a course, or a chatbot.
She needs someone to have already handled it.

| Card | Copy |
| --- | --- |
| She takes a photo of the flyer | The agent pulls out every date, fee and deadline in it. |
| It checks the whole family | Ages, conflicts, the other kid's Tuesdays, what she said about last summer. |
| It watches what she can't | The registration window that opens in nine days at 9am. |

**Footer line** Same agent, same memory, five doors in: camps · classes & sports · school life ·
outings · trips.

> *Note: Fadell's note — lead with the moment, reveal the system second.*

---

### 06 — The wedge

**Eyebrow** THE WEDGE
**Title** The window opens at 9am on a Tuesday in February.
**Body** Miss it and the camp is full, the summer has a hole in it, and the other parent finds out
before you do. No national product watches these dates for parents.

| Card | Copy |
| --- | --- |
| We watch the window | Seven days out, and again before it opens. Never after. |
| We confirm, we don't guess | A date the agent researched stays labeled an estimate until the parent taps to confirm it. |
| An alarm watches the watcher | A miss detector pages us when a window closes unnotified. We don't expand past the pilot metros until it runs clean through a real season. |

> *Note: This is the retention engine. Not the coaching.*

---

### 07 — Built, not slideware

**Eyebrow** THE EVIDENCE
**Title** It shows you the sentence it got the date from.
**Body** When the agent pulls a deadline out of a school PDF, it puts the source sentence right next
to it. A parent can see it didn't make anything up. That detail is the whole product philosophy, and
it's the kind of thing that only exists when someone builds for five months instead of demoing for
five weeks.

| Card | Copy |
| --- | --- |
| Live on TestFlight | Onboarding, companions, coaching grounded in a real family profile. |
| Backend in production | 24 schema migrations, 4 live alert rules, per-call cost telemetry. |
| Five-layer moderation | Crisis detection on a taxonomy aligned to 988/SAMHSA vocabulary. |
| Tested like infrastructure | 567 automated tests. 120 kid-safety evals. 29 black-box flow specs against the real API. |
| Voice, sub-150ms | Our backend stays the brain. The vendor only moves audio. |
| Content taxonomy | 110 categories, 45 articles, 25 community posts mapped. |

> *Note: Heather's credibility slide, hardened. The headline is the detail, not the count.*

---

### 08 — Why this gets big

**Eyebrow** THE SCALE CASE
**Title** Camps is the wedge. The job is the company.
**Body** A seasonal tool is a nice business. What makes this big is that solving one deadline earns
the right to the rest of the household's operations — and the graph we build getting there is not
available for purchase.

| Card | Copy |
| --- | --- |
| Act one · the wedge | Activities and coverage. One acute, recurring, seasonally forced pain. |
| Act two · the household | The same agent already reads the email, the calendar and the paperwork. Medical, school and the rest of the operations job are adjacent, not new. |
| Act three · the transaction | We source registrations that today flow through nobody who knows the family. $3–4B a year in US camp fees alone. |
| Why not OpenAI | They won't take on child-safety liability, they don't have your family's graph, and trust in this category is won by a product parents hand their kid — not by a better model. |

> *Note: Horowitz's slide. If they think this is a lifestyle business, it's because we didn't say this.*

---

### 09 — What compounds

**Eyebrow** THE MOAT
**Title** What compounds.
**Body** The honest question at pre-seed isn't "what's your moat today." It's "what are you
accumulating."

| Card | Copy |
| --- | --- |
| The family graph | Ages, interests, custody rhythm, what you tried last year and what you said about it. Every conversation deepens it. A general assistant starts from zero every session, forever. |
| Safety as architecture | Five layers and a crisis lock that freezes the conversation and pushes the parent's phone, verified on a physical device. Months of work, and the part a fast follower skips. |
| Evals that keep it honest | Every change to a prompt or a tool re-runs a live-model golden set before it ships. It's why the agent still works in month eight. |
| Solo-first coordination | A co-parenting app only learns how a family actually runs once *both* parents sign up, so its data stops at the households where the ex agreed. We learn the same thing from one side: the custody rhythm, whose week it is, which handoffs keep slipping — inferred from what one parent tells us and confirmed by the invites the other parent accepts. Our graph grows at one account per family. Theirs needs two, and the second one is the one that usually says no. |

> *Note: If they underwrite one slide, it's this one.*

---

### 10 — Safety

**Eyebrow** SAFETY
**Title** If a child is in crisis, a parent's phone rings.
**Body** That's a written design principle, enforced in code. Safety here isn't a filter bolted to a
chatbot. It's the architecture, and it's why a parent hands us their kid at all.

| Card | Copy |
| --- | --- |
| Five layers | Deterministic patterns, moderation API, age-appropriateness, a streaming token-level monitor, a final output check. The model sits on top of the backstop, never underneath. |
| A real taxonomy | Severity aligned to 988/SAMHSA ideation vocabulary, reviewed against pediatric safety practice. |
| The parent is paged | A crisis freezes the conversation, shows the child real resources, and pushes the parent's phone. The agent can't restart until a human intervenes. Verified on device, July 2026. |
| Privacy as a position | Logistics data is durable and exportable. The coaching conversation is designed to leave nothing behind. |

> *Note: Heather leads this one. It's the trust slide.*

---

### 11 — The market and the model

**Eyebrow** THE MARKET
**Title** Parents already pay. Twice, and for less.
**Body** We're not sizing a circle. We're pointing at cash registers already ringing next door.

| Card | Copy |
| --- | --- |
| **$34M** | Good Inside's 2025 revenue — 100,000+ subscribers at ~$276/yr, for parenting *advice*. No coordination, no deadlines. *Fortune, February 2026* |
| **$110–$300** | OurFamilyWizard's annual price, charged **per parent**. Two-household families already pay twice, for software built to be read by a judge. |
| **$3–4B** | US summer camp registrations a year. |

**The build** 100,000 families at $129/yr is $12.9M ARR. Good Inside reached that subscriber count
selling advice alone. We price at about 3% of what the activities themselves cost, one payer, hard
paywall after a trial — and the second parent participates by calendar invite, never an install.

> *Note: Bottoms-up from three verified anchors. If they push on TAM, push back with these.*

---

### 12 — Why we win

**Eyebrow** WHY WE WIN
**Title** Every other app needs your ex to sign up.
**Body** TalkingParents publishes a help article called "What if my co-parent won't sign up?" The
industry's answer is a contempt motion. Ours is a calendar invite.

**Supporting row** They document the fight; we prevent it. ChatGPT is better than us at nearly
everything and has never heard of your custody schedule.

> *Note: Let the title sit on a white field. Don't fill the slide.*

---

### 13 — Where we are

**Eyebrow** WHERE WE ARE
**Title** Five months. In stealth. On purpose.
**Body** We haven't launched. We spent the time on what kills consumer AI companies: reliability,
safety, and the evals that keep both true after the demo.

| Card | Copy |
| --- | --- |
| What's built | Five verticals live in production. A 20-tool agent. 98 TestFlight builds. 21 parent-facing releases in the last 24 days. |
| What isn't | No public launch. No revenue. No paywall in the app yet. We're not dressing a beta up as traction. |
| How we'll know | The gates are written down in advance, with the numbers that would make us stop: median willingness-to-pay ≥ $100, cost per email ≤ $5, 90-day retention ≥ 30% before we scale spend. |

> *Note: Say out loud — "we wrote down what would make us quit." Pre-written kill criteria read as maturity.*

---

### 14 — Team

**Eyebrow** THE TEAM
**Title** Both of our beachhead customers are sitting at the table.
**Body** Founder-market fit here is structural. Two founders, two different household structures,
overlapping kid ages. The product's two personas are the two people building it.

| Card | Copy |
| --- | --- |
| **Heather Hannan-Kramer** · CEO | Parent, educator, consultant. Originated the concept before the pandemic. Owns product vision, audience research and go-to-market. The coordinating mother the product is designed for, with two girls at home. |
| **Miguel Alvarado** · CTO | Single father of two. Thirty years shipping software, thirteen in AI, twice a CTO. Built the entire stack — backend, iOS, agents, moderation, deployment. |
| **Greg Harris** · Design | Grandparent, and a design leader on consumer products. Owns visual identity and the user journey from prototype to market. |

> *Note: VCs weight team ~40% more than they used to. AI made building easy; who builds matters more.*

---

### 15 — Miguel Alvarado, CTO

**Eyebrow** THE TECHNICAL CO-FOUNDER
**Title** Thirty years of range, in the year range became the qualification.
**Body** For most of my career, breadth was a liability — the industry wanted specialists. AI
inverted that. When one engineer can hold the backend, the app, the model layer and the deploy in a
single head, the person who has actually worked at every one of those layers is the one who ships. I
went from writing C++ for mobile carriers to TypeScript and agent orchestration, and I ran the teams
in between.

| Card | Copy |
| --- | --- |
| 30 years shipping | Microsoft in the Web 1.0 era. Brightcove through IPO, 450M players and ~1.3B daily video views. Intel Media's OnCue through the Verizon acquisition. VP Engineering at Vevo. |
| 13 years in AI | CTO at Lumiata, deep learning across 100+ medical conditions. CTO at Mindstrong, digital biomarkers, reliability from 92% to 99.99%, acquired by SonderMind. VP Engineering at SonderMind today. |
| AI-first, and board-facing | Multi-agent systems, real-time voice and regulated guardrails, built hands-on through Artesano. Board-facing at Lumiata and MetaStories. Ten years advising Loupe, with a three-part patent. |

**Full-width band, below the cards** — The proof is not the résumé. It is this product: one
engineer, five months. A native Swift app, a Python agent backend, a React dashboard.
~77,000 lines. 567 tests. 120 kid-safety evals. 98 builds.

> *Note: The last card is the point. Don't read the résumé — read the last card.*

---

### 15 alt — Miguel Alvarado, short version

Two candidates for slide 15. Heather picks one and deletes the other. Use this one if the deck is
running long, or if the audience already knows the technical story.

**Eyebrow** THE TECHNICAL CO-FOUNDER
**Title** Thirty years shipping. Thirteen in AI. Twice a CTO.
**Body** Miguel Alvarado. I built every layer of MVP myself, in five months.

| Card | Copy |
| --- | --- |
| Shipped at scale | Microsoft. Brightcove through IPO. Intel Media into Verizon. VP Engineering at Vevo. |
| AI in production | CTO at Lumiata and at Mindstrong, acquired by SonderMind. VP Engineering at SonderMind today. |
| Building MVP | Native Swift app, agent backend, five-layer safety system. One engineer. |

> *Note: Alternative to the previous slide. Pick one, delete the other.*

---

### 16 — The ask

**Eyebrow** THE ASK
**Title** Fund the proof, not the promise.
**Body** The product risk is behind us. What we're buying is the answer to one question: will
parents pay for this, at this price, without us in the room. `[NEEDS: raise amount + runway]`

| Card | Copy |
| --- | --- |
| Prove they'll pay | Run the gates in the pilot metros. Median WTP ≥ $100 and 90-day retention ≥ 30%. |
| Survive one season | The miss detector runs clean through a real winter-into-spring registration cycle. That's the difference between a product and a promise. |
| Close the two known gaps | COPPA compliance, which unlocks the kid companion we're sitting on, and the move off a single-writer database before scale demands it. |

**Closing line** Every hard coordination job in the economy got software. The family is the last one
holding out, and the technology that finally solves it arrived eighteen months ago. We built the
thing. We'd like to go find out what it's worth.

> *Note: End on the closing line. No thank-you slide.*

---

## Open items

- `[NEEDS: raise amount and runway]` — slide 16.
- **Miguel's full-time employment.** He is VP Engineering at SonderMind. Every investor asks. It is
  not a slide, but he needs the sentence ready before this deck goes out. See `critics.md`.
- Pricing states $129 inside a tested $99–$149 range. If the range is genuinely still open, say the
  range and lose some force.
- Heather's other 13 slides, if we're merging rather than running parallel.
