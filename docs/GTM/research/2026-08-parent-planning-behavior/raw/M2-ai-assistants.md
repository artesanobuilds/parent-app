# M2 — AI Family / Household Assistants: The Direct Competitive Set

Miner M2. Compiled 2026-08-21. US-focused unless noted.

**Method note.** WebSearch budget was exhausted mid-run; the back half of this report was
built by direct WebFetch against primary sources (product sites, pricing pages, Apple's
public customer-review RSS feeds, founder Substack, Wikipedia, trade press). Apple review
data was pulled programmatically from `itunes.apple.com/us/rss/customerreviews/` on
2026-08-21 — that is a primary, verbatim source and is the strongest evidence in this file.
Trustpilot and Crunchbase both 403'd; where a number comes only from a secondary aggregator
I say so and mark it low confidence. Several "best AI family organizer 2026" roundups are
written BY competitors (getsense.ai, heynori.com, alphamothers.com, usecarly.com) — they are
tagged vendor-interested and used only for lead generation, never as evidence.

---

## Section 1 — The live set as of August 2026

### Tier 1: real, funded, actively shipping

**Ohai.ai** — the closest analogue to us, and the most instructive.
- Founded 2024 by Sheila Lirio Marcelo (founder of Care.com, which IAC bought for $500M in 2019).
- **$6M seed** from Eniac Ventures and LifeX Ventures (Wikipedia, citing Axios 2024-01-22). No
  later round found. This is a small raise for the ambition — worth noting.
- Assistant is named "O." Positioning: "text-based AI household assistant."
- **Pricing:** free tier (daily summaries only); Premium advertised on the site as "starting at
  $9.99 per month" — but multiple 2026 App Store reviewers report the real charge as **$15/month**
  ("basic functionality costs $15/mo.", "you have to pay 15 dollars to start"). The $9.99 is
  almost certainly the annual-billed monthly equivalent. **No free trial** — reviewers complain
  about this repeatedly.
- **Scale:** "Thousands of families trust Ohai" (own marketing, unquantified). App Store: **4.44
  stars over 208 US ratings**, version 3.2.3, last shipped 2026-08-20 — small install base, very
  active development.
- Media: Forbes, Bloomberg, WSJ logos on the site.

**Nori (Domus Next Inc.)** — the fastest-growing entrant, launched ~Feb 2026.
- **Pricing:** Free Forever ($0) with **10 total AI uses**; Nori AI Plus **$4.99/mo billed
  annually, $7.99/mo monthly**. Cheapest credible product in the category.
- **Scale:** claims "200,000+ families" and featured in a Google Play Story two months after
  launch (Apr 2026, GlobeNewswire press release — company-issued, treat as marketing).
  App Store: **4.82 stars over 1,204 US ratings** — 6x Ohai's rating count in a fraction of
  the time. Caveat: a visible slice of Nori's 5-star reviews are generic, emoji-laden, and
  read as incentivized or astroturfed ("I'm really happy to support your amazing work 💛📱").
  Discount the average; the *volume* is still real signal.
- Hardware: "Nori Family Hub" wall device launched June 2026, explicitly to solve "inability to
  wake the app when the phone screen is off."
- Note: an unrelated work-productivity company also used the name Nori. Don't conflate them.

**Duckbill** — the human-in-the-loop benchmark.
- Founded 2022, San Francisco. StartupHub estimates ~122 employees and ~$10.8M annual revenue
  (low confidence — algorithmic estimate, wide range $9.7M–$28.3M).
- **Pricing (fetched from getduckbill.com/pricing, 2026-08-21):**
  Essentials **$49/mo** (~3–5 tasks), Individual **$99/mo** (~4–6 tasks), Household **$169/mo**
  (~8–12 tasks, 2 accounts, "Most Popular"), Household Plus **$350/mo** (~16–20 tasks), Team custom.
- **Model:** AI named "Bill" intakes the request and asks clarifying questions, then routes to
  US-based background-checked human "copilots." Turnaround "usually within 24 hours."
- App Store: **4.28 stars over 68 US ratings** — tiny install base, but this is a service where
  the app is a thin front door, not the product.
- Duckbill migrated from unlimited tasks → a credit/bandwidth system, and the reviews show the scar.

**Ollie (ollie.ai)** — the purest anti-app play, and the most interesting strategic contrast.
- **No app, no login, no download.** Entirely SMS. "Just talk to Ollie like a friend."
  You can add Ollie to a group chat with your spouse, nanny, or kids.
- **Pricing:** Free ($0, 50 Ollie-messages/mo + 6/day), Everyday **$25/mo** (150/mo + 10/day),
  Always-On **$100/mo** (1,000/mo + 15/day). Top-ups $0.25–$0.30/message.
- Note the price ladder: an SMS-only product with no app charges **2–7x** what the app-based
  competitors charge. Channel choice is a pricing-power decision, not just a UX decision.

**Sense (getsense.ai)** — single-job wedge: email → calendar.
- Positioning: "reads your school emails and quietly handles the mental load."
- **Intake channels:** forward to `share@getsense.ai`, WhatsApp message, photo of a flyer,
  screenshot, PDF, pasted text, shared URL, iOS Share Sheet, voice (incl. Alexa/Siri).
  Deliberately many *inbound* channels, near-zero *setup*.
- **Pricing (per its own roundup):** Free / **$6.99/mo or $59.99/yr**.
- Its explicit onboarding thesis, quoted verbatim from its own marketing: *"The right test is not
  'is the chatbot smart?' It is 'can I forward one email and forget it.'"* and *"Forward one email
  tonight. Check the calendar in the morning. If the events are there, you have your answer."*

**Plannie (plannie.io)** — app + kitchen-tablet mode.
- **$99/year** for the whole household; free tier; currently discounting hard ("free for everyone
  until Aug 30", "50% off lifetime deal") — a company buying its way into the Maple refugee flow.
- Claims **~5-minute setup**: create household, add family members with colors, connect calendars.
- Assistant accepts forwarded emails, photos, pasted links.

**Schoolcase (schoolcase.app)** — **$9/month**, email-forwarding-to-a-private-inbox only.
Narrowest wedge in the set: school email → tasks and dates. No app-first ambition.

**Somiya (somiya.app)** — **€9.99/mo or €59.99/yr**, up to 8 people. **Euro-priced; not a US
product.** Interaction: capture by text/voice/photo → auto-sort → nudge the right person. Its
tagline is a direct shot at our category: *"For families who are done with dashboards."*

**Babs (hellobabs.ai)** — **pre-launch, waitlist only** as of 2026-08-21. Email-inbox-parsing
positioning ("email decoder, calendar wrangler, and reminder-in-chief"). No pricing disclosed.

**AlphaMa (alphamothers.com)** — free "for now," voice + email forwarding + app, positions itself
as an autonomous agent vs. the others as "organizing platforms." Very early; also publishes the
comparison roundup that ranks itself #1, so treat all its claims as marketing.

### Adjacent hardware (relevant because it competes for the same budget and the same wall)
- **Skylight Calendar 2** — ~$380 device + **$79/yr** Plus. Already known in repo.
- **Hearth Display** — wall display, "Replace your whiteboard, wall calendar, chore charts, and
  scattered reminders with one shared system." Live and running back-to-school promos in Aug 2026.
  Syncs Google, Outlook AND Apple Calendar — a gap in our product.
- **Nori Family Hub** — June 2026 (above).

### Dead or gone
- **Milo** (Avni Patel Thompson) — shut down, announced 2026-01-12.
- **Yohana** (Panasonic) — US wound down 2025-09-30; **Japan service closed 2026-01-30**;
  **yohana.com no longer resolves in DNS** (verified 2026-08-21). The brand is fully gone, not
  just the US arm. Panasonic's stated reason: a "comprehensive assessment of the business
  environment." Panasonic has also **indefinitely postponed "Umi,"** its next family-focused AI
  app, with no revised timeline.
- **Maple (growmaple.com)** — **sunsetting December 31, 2026.** Acquired late July 2026 by
  **Wander**, a luxury vacation-rental company; founders Michael Perry and Mike Taylor (both ex-Shopify
  execs) joined Wander to work on WanderOS. Annual subscriptions stopped renewing. Verbatim from
  the shutdown notice: *"Your data will remain fully accessible until December 31, 2026"* and
  after that *"All data will be deleted and there will be no way to recover it."* Maple is already
  delisted from the US App Store. This is an **acquihire away from the category**, not a
  product failure per se — but note where the talent went: travel, not family.
- **Dola** — the SMS/messaging AI calendar assistant. **dola.ai now redirects to a GoDaddy
  "for sale" parking page**; dola.me shows only "Launching Soon." Effectively dead or in limbo.
  Third-party directories still list it as live at $8/mo — those directories are stale.
- **"Sunday", "Tely", "Cera"** — **CORRECTION TO THE REPO'S COMPETITOR LIST.** I could not find
  any live US family/household AI assistant under these names. `trycera.com` is a business-loan
  marketplace; `hellosunday.ai` is an Indian AI recruiting platform (prices in ₹); `tely.ai` and
  Capterra's "Tely" are healthcare/marketing SaaS. `cera.ai`, `sundayapp.ai`, `heytely.com` do
  not resolve. Recommend striking these three from our tracked set unless someone can produce a URL.

---

## Section 2 — Comparison table

| Product | Price | Interaction model | Human-in-loop? | Onboarding depth | Status |
|---|---|---|---|---|---|
| **Ohai.ai** | Free tier; **$15/mo** monthly (site says "from $9.99/mo" annual). No free trial | **SMS-first** + iOS/Android app + email forwarding + photo/PDF scan + voice | **Partial** — "combines AI automation with human support"; Premium users can book a human walkthrough | Medium-high: phone number → SMS code → connect email → connect Google Calendar → answer onboarding questions → paywall before any real feature. **Google Calendar only** (no iCal/Outlook) | Live, shipping weekly (v3.2.3, 2026-08-20) |
| **Nori** | Free (10 AI uses total); **$4.99/mo annual**, $7.99/mo monthly | App + web + **wall hardware**; input by voice, chat, photo, email forward. **Outbound phone-call reminders.** WhatsApp/iMessage/Messenger "coming soon" | No | Low: install → create family → invite members. Free core needs no payment | Live, fastest-growing (1,204 US ratings since ~Feb 2026) |
| **Duckbill** | **$49 / $99 / $169 / $350 per month** by task volume | **App, text, OR email — user's choice.** AI ("Bill") intakes and clarifies; humans execute | **Yes — core of the product.** US-based, background-checked "copilots," team-pooled not dedicated | Low to start (address + billing), but **high per-task friction**: "dozens of follow up questions on every request" | Live |
| **Ollie** | Free (50 msgs/mo); **$25/mo**; **$100/mo** | **SMS only. No app, no login, no download.** Works inside existing family group chats | No | **Lowest in the set**: text a number. Then optionally delegate calendar/email access and add household members to the group chat | Live |
| **Sense** | Free; **$6.99/mo or $59.99/yr** | **Email forwarding first** (`share@getsense.ai`) + WhatsApp + photo/PDF + Share Sheet + voice/Alexa/Siri | No | **Deliberately one step**: "Forward one email tonight. Check the calendar in the morning." | Live |
| **Plannie** | Free; **$99/yr household** | App + web + kitchen-tablet display; assistant takes forwarded email, photos, links | No | ~5 min: create household, add members with colors, connect calendars | Live (aggressive Maple-refugee discounting) |
| **Schoolcase** | **$9/mo** | **Email forwarding to a private inbox.** That's it | No | One step: forward to your inbox address | Live |
| **Somiya** | **€9.99/mo or €59.99/yr** (up to 8 people) | App; capture by text/voice/photo → auto-sort → nudge one person | No | 3 stated steps: "Add anything / Somiya sorts it / The right person is nudged" | Live — **EU, not US** |
| **Babs** | Undisclosed | Inbox parsing (channels not yet specified) | Unknown | "Get started in minutes"; explicitly promises you need NOT connect every school and sports app | **Waitlist / pre-launch** |
| **AlphaMa** | Free (for now) | Voice, email forwarding, app | No | Unstated | Live, very early |
| **Hearth Display** | Hardware + subscription (undisclosed on site) | **Wall display**, touch; AI meal-plan assistant; syncs Google + Outlook + **Apple** | No | Hardware unboxing + calendar connect | Live |
| **Skylight Calendar 2** | **~$380 device + $79/yr** | Wall display, hardware-bound auto-intake | No | Hardware + calendar connect | Live (already known) |
| **Cozi** | Free w/ ads; **$39/yr Gold** | App, **manual entry, no AI** | No | Lowest of the legacy set — "easiest onboarding for the whole extended family" | Live (already known) |
| **Milo** | n/a | **SMS-first** family assistant | No | n/a | **Dead — announced 2026-01-12** |
| **Yohana** | ~$149/mo (US, historical) | App + human specialists | **Yes — fully human execution** | High (intake call + weekly planning) | **Dead — US 2025-09-30; Japan 2026-01-30; domain now unresolvable** |
| **Maple** | Free + Maple+ | App + email extraction + calendar sync (Google/Apple/Outlook) + TeamSnap | No | Medium | **Dying — sunsets 2026-12-31; team acquihired by Wander (travel) July 2026** |
| **Dola** | ~$8/mo (stale listing) | **SMS / messaging-first** AI calendar | No | Minimal — text it | **Apparently dead — dola.ai domain parked for sale** |
| **Panasonic "Umi"** | n/a | Family AI app | n/a | n/a | **Indefinitely postponed, no timeline** |

---

## Section 3 — Interaction model: the single clearest finding

Sort the category by channel and a pattern falls out immediately.

**Nobody who is winning attention right now is app-first.** Of the eleven live products above,
**eight accept email forwarding as a primary intake**, **four are SMS-native**, and **at least
six accept a photo of a paper flyer**. The two products with the loudest current traction —
Nori (1,204 ratings in ~6 months) and Sense — both lead their marketing with "you don't have to
type." Sense's entire positioning is a single-step onboarding claim. Ollie's is that there is
**no app at all**.

The stated reasoning, verbatim, where it exists:
- Sense: *"The right test is not 'is the chatbot smart?' It is 'can I forward one email and forget it.'"*
- Ollie: no download, no login, add it to the group chat you already have — meeting the family
  where the family already talks.
- Nori shipped **hardware** in June 2026 for an explicitly stated reason: *"inability to wake the
  app when the phone screen is off."* That is a company admitting the phone app is the weak link.
- Somiya: *"For families who are done with dashboards."*

Three distinct channel bets are visible:
1. **Zero-app messaging** (Ollie, Milo†, Dola†, Ohai's SMS half) — bet: the mental-load carrier
   won't open another app, but she will read a text.
2. **Inbox as the intake pipe** (Sense, Schoolcase, Babs, Maple†, Ohai) — bet: the load arrives
   as email, so intercept it where it lands and never ask the parent to re-enter anything.
3. **The wall** (Nori Hub, Hearth, Skylight) — bet: coordination is a household act, not a
   personal one; put it where everyone walks past.

**Where our product sits:** in-app chat + forms is the ONLY model in this table that appears
in no successful competitor as a *primary* channel. Everyone who has app chat has it as one
of four or five intake paths, behind email forwarding. We have Gmail ingestion and photo
ingestion already built — those are the channels the market has converged on — but they sit
*behind* an 8+N screen wizard, which is the opposite of the sequencing everyone else uses.

**Voice is a supporting actor everywhere, never the wedge.** Nori, Sense, Ohai and AlphaMa
all support voice input; none of them lead with it. Nori's most-praised voice-adjacent feature
in reviews is not conversation at all — it's **outbound phone calls as a reminder channel**:
*"It actually alerts you with a phone call and other means which is great for me bc I'm super
bad about turning off all notifications."* That is voice as *output*, not input. Nobody in this
category is selling a full-duplex conversational agent as the main event.

---

## Section 4 — Human-in-the-loop

Only three products in the set put real humans behind the AI, and the pricing separation is stark:

| Model | Price band |
|---|---|
| Fully automated app (Nori, Sense, Plannie, Schoolcase, Cozi) | **$39–$99 per YEAR** |
| Automated + SMS delivery (Ohai, Ollie) | **$15–$100 per month** |
| Humans execute the work (Duckbill, Yohana†) | **$49–$350 per month** |

Human-in-the-loop buys roughly a **10–40x price premium** — and it buys the best reviews in the
entire category. Duckbill's App Store reviews are dramatically warmer than Ohai's or Nori's, and
the praise is explicitly about the *humans*, not the AI: *"The human copilots are so thoughtful
and hardworking."* / *"There are humans that take this off your plate like a good friend!"*

But it also buys the sharpest failure mode. Both Duckbill's negative reviews and Yohana's death
point the same way: humans make the unit economics fragile, which forces metering, and metering
is what users hate. Duckbill went from unlimited tasks to credits, and the reviews record it in
real time: *"Ugh. What happened with this app?! It used to be amazing. I signed up when it was
unlimited tasks. That was incredible. Then they changed the plans"* and *"This whole credit system
is confusing and it's not worth my money! Having them book a dinner reservation costs 12 credits????"*

Ohai's "human support" claim is thin — a bookable walkthrough call for Premium users, plus
support staffing. It is a *service* layer, not an *execution* layer, and Ohai's reviews get none
of Duckbill's human-praise warmth.

---

## Section 5 — Verbatim reviews, tagged

All quotes below are from Apple's public US customer-review feed, pulled 2026-08-21, unless noted.

### PRAISE

**[capture-without-typing] — the single most-praised capability in the entire category**
- Ohai, 5★ *"The docu scan feature has changed everything for sports and school. I just take a
  pic of my son's basketball and baseball schedules and O loads them right into my calendar.
  **No more inputting each one on my own.** Love it!"*
- Ohai, 5★ *"Daily dump has changed my life with organization, especially the documents scanning feature!"*
- Nori, 5★ *"I especially love that I can **upload photos of event flyers and it instantly turns
  them into clean calendar entries.** Everything is finally in one place."*
- Ohai, 4★ *"I love that I can just forward calendar invites and it adds them to a single calendar."*

**[voice / channel]**
- Nori, 5★ *"**It actually alerts you with a phone call** and other means which is great for me bc
  I'm super bad about turning off all notifications except one or two bc I get annoyed by people. 😂"*
- Ohai, 5★ *"My husband hates technology. He is a mechanic, and thinking about using a flip phone lol.
  **He likes that it texts you without logging in.** Like my husband is reminding me of stuff now."*
  ← This is the whole SMS thesis in one review: the *non-adopting spouse* participated because
  there was no app to open.

**[low-complexity]**
- Ohai, 5★ *"**Some of these kinds of apps can be more work than they're worth** but Ohai just works."*
- Nori, 5★ *"**You don't need to spend hours setting it up** or learning complicated features."*
- Duckbill, 5★ (autistic professor, parent of four) *"The interface is calm, direct, and never wastes
  my time. The status labels ('In Progress,' 'Done,' 'Ready to Review') keep everything crystal clear.
  Reminders are gentle and predictable, **not nagging**."*

**[human-in-loop]**
- Duckbill, 5★ *"The human copilots are so thoughtful and hardworking."*
- Duckbill, 5★ *"It's a blessing to have a place to delegate those mundane things... **There are
  humans that take this off your plate like a good friend!**"*
- Duckbill, 5★ *"Duckbill has taught me that **I don't need to do everything myself**."*
- Duckbill, 5★ *"Duckbill got me hundreds of dollars back in flight compensations and **all I had to
  do was forward a couple of emails!**"*

**[ADHD / executive function] — a recurring, unprompted self-identification**
- Nori, 5★ *"Helped with my ADHD and show my husband what we need to do it help alot"*
- Ohai, 4★ *"**My ADHD brain struggles to have to go a bunch of places for things.**"*
- Nori, 5★ *"I struggle to stay focused and sometimes I forget important things. Nori helps with that."*

### COMPLAINTS

**[trust] — the dominant negative theme; broken extraction destroys the entire premise**
- Ohai, 1★ *"It would set them wrong and remind me on the wrong days. I would ask to fix and it would
  say oh yes I will fix. But then it wouldn't and we would do that over and over. **It's like working
  with Dory. I am a better personal assistant than this AI.** Great idea but it's not delivering."*
- Ohai, 2★ *"In the less than 24 hours since I've been using the app, I've needed support twice...
  **So how can I trust that things are actually being added to my calendar?**"*
- Ohai, 2★ *"I had a handwritten calendar in very well penmanship... and it scanned it and **got all
  the events wrong.** And so it was weird because it wanted me to pay for their suggesting that this
  was their most powerful feature."*
- Ohai, 1★ *"Great concept, but the app simply doesn't work properly and one of the emails I sent
  went ignored. **Definitely not a time saver.**"*

**[entry friction] — the paywall-before-value pattern, repeatedly**
- Ohai, 1★ *"You have to sign up with your phone number, then attach your email, and then you have to
  pay 15 dollars to start.. stay away"*
- Ohai, 2★ *"can't even create events in the free tier. only gives you daily summaries, so basically
  useless. and **the setup process takes too long just to find this out.**"*
- Ohai, 2★ *"The free trial is so limited you have to opt into paying to see how it really works...
  **I found it more complicated to get my tasks into than it was to just handle it myself.** Email
  scanning was disappointing. **Felt like it was another big mess to clean up.**"*
- Ohai, 1★ *"They first collect your phone number, email etc so they can continue to market to you
  before letting you know if you want even a single one of the features advertised you have to pay."*

**[adoption failure — onboarding literally never completed]**
- Ohai, 1★ *"**I got stuck in onboarding where it asks to answer a few questions. No text box or
  multiple choice popped up for me to click on.** I reopened in a different web browser. Same thing.
  Then I downloaded the app. Same thing. **I haven't been able to use any functionality to actually
  review because I never got out of onboarding.**"*

**[adoption failure — the rest of the family]**
- Ohai (via Agent Finder, secondary): *"Requires buy-in from the whole family. **If your spouse won't
  check the app, you're back to being the single source of truth.**"*
- Nori, 5★ (buried caveat) *"even my **reluctant husband** has started using it regularly."*

**[complexity — the surprising direction: users want LESS surface, and a plain calendar]**
- Ohai, 2★ *"the developers failed on the most basic app structure — the dashboard interface...
  What really made the app **unusable as a household manager is the inability to view my monthly
  calendar. Ohai can't tell you anything about your schedule at a glance.**"*
- Nori, 2★ *"I really liked this app... **But i dont like that you cant see a normal calender.**
  I want to know like what im doing tomorrow or thursday and i cant"*
- Ohai, 4★ *"can you make the home page more of a dashboard? Calendar, lists, action items, etc?
  As much in one place. **I definitely don't need all the 'we can do this' stuff on the home page.**"*
  ← Three independent users across two products asking for the same thing: **a plain month view**,
  and less aspirational capability marketing on the home screen.

**[price]**
- Ohai, 3★ *"Compared to other AI assistants, the pricing model feels steep. **There is no free
  trial**, and basic advertised features like calendar sync and email management require a $15/month
  minimum."*
- Ohai, 3★ *"**I'd rather just manage things myself and not depend on ai** especially because the
  subscription is so high and there is no free trial to understand what it's capable of."*
- Duckbill, 2★ *"Not even remotely worth the cost. **They ask dozens of follow up questions on every
  request**, which might be fine if each follow up question did not have an over 1-business-day
  response time. So, in the end, it ends up taking well over a week to complete anything."*
- Nori, 2★ *"The description claims that you get so many free credits per day to use AI, but **you
  only get ten in total** it appears."*

**[trust — privacy and data]**
- Ohai, 3★ *"**giving full inbox access with no granular control over what's shared** makes me
  cautious about privacy. My Gmail inbox is a treasure chest of personal data and I can't just
  trust a shiny new app."*
- Ohai, 1★ *"**Never use your phone number. They will spam your phone with SMS text messages with
  no way to opt out.** I requested deletion of my account and I still get these messages daily."*
- Ohai, 1★ *"Can't delete account — This is not per Apple ToS"*
- Ohai, 1★ *"It's also complicated to cancel it"*

**[integration lock-in — a specific, fixable killer]**
- Ohai, 1★ *"**Only works with Google calendar.** I need this to work with iCal. I've had my entire
  life on iCal for 20 years now."*
- Ohai, 1★ *"If you don't have a google calendar it's useless."*
  ← Directly relevant: we are also Google-Calendar-only, with no Apple or Outlook support.
  Hearth and Maple both support all three. This shows up as **1-star reviews**, not feature requests.

*(Secondary, unverified: multiple aggregator blogs claim Ohai holds an 86% one-star share on
Trustpilot. Trustpilot 403'd every fetch attempt and I could not confirm this. It contradicts
Apple's 4.44/208. Do not cite it. Plausible explanation: Trustpilot skews to people arriving
with a billing/cancellation grievance, which matches the cancel-and-spam complaints above.)*

---

## Section 6 — Shutdown post-mortems and THE PATTERN

### The deaths, 2025–2026

| Company | Died | Model | Stated reason |
|---|---|---|---|
| **Yohana** (Panasonic) | US 2025-09-30; **Japan 2026-01-30**; domain now dead | Human specialists, ~$149/mo | *"comprehensive assessment of the business environment"* — corporate for: the unit economics never closed |
| **Milo** (Avni Patel Thompson) | Announced **2026-01-12** | SMS-first family AI | *"the technology is simply too early to be reliable in any useful way"* |
| **Maple** | Sunsets **2026-12-31** | App + calendar sync | Acquihired by **Wander** (travel) July 2026; founders left the category |
| **Dola** | ~2026 | SMS/messaging AI calendar | No announcement; **domain listed for sale** |
| **Panasonic "Umi"** | Indefinitely postponed | Family AI app | No timeline given |
| **Facebook "M"** | (historic precedent) | Human+AI messenger assistant | Human-in-loop could not scale |

### Milo's post-mortem — the most valuable document in this whole file

Founder Avni Patel Thompson, "hello/goodbye," joinmilo.substack.com, 2026-01-12. Six years of
research, three years of building. Her stated reasons, verbatim:

- *"Too early to build the kind of AI that reliably, delightfully, powerfully lightens the load
  **without adding it back somewhere else**."*
- *"The technology is simply too early to be reliable in any useful way."*
- The team *"tread water for 18 months"* trying different technical approaches without reaching
  production reliability at scale. Scaling would have required building proprietary models and
  infrastructure, or waiting for the technology to mature.

Her lessons on adoption. Parents **would** adopt something that addressed the invisible load
without creating new overhead, that offered *"intentional friction"* rather than pure convenience,
and that enabled *being together* rather than doing more tasks faster. Parents **would not** adopt:
- systems requiring constant manual data entry **by the already-overloaded coordinator**;
- technology that merely outsourced tasks without solving the coordination burden;
- solutions that treated family needs like **workplace productivity optimization**.

She also names the structural problem she never solved: *"someone has to run point."* The product
still required one person to be the operator of the system. That is the exact trap our 8+N wizard
plus 58 text-entry fields plus 18 free-text profile fields sets up.

### THE PATTERN — what actually kills these companies

Synthesizing across all six deaths and the complaint corpus, four failure modes recur, and they
compound:

**1. The mental-load paradox.** Every one of these products asks the most overloaded person in
the household to do setup work in order to be relieved of work. The debt is paid up front, in
full, by the person with the least slack; the payoff is probabilistic and arrives later. Milo
names this exactly ("without adding it back somewhere else"). One reviewer names it in eleven
words: *"I found it more complicated to get my tasks into than it was to just handle it myself."*
Every product that is currently gaining ground — Sense, Ollie, Nori — competes primarily on
*shrinking this debt to near zero* (forward one email; text a number; snap a flyer), not on
capability.

**2. Reliability is binary, not gradual.** Family logistics have no tolerance for an 85% extraction
rate, because the 15% is a missed dentist appointment or a blown registration deadline. Once a
parent catches one wrong entry, they revert to manual and keep doing manual *forever* — and, worse,
they now have to double-check the system as well, which is net-negative work. *"It's like working
with Dory. I am a better personal assistant than this AI."* This is the failure Milo shut down over.
It is the top complaint against Ohai in 2026. It has not been solved by anyone.

**3. Single-player adoption in a multi-player job.** Coordination value is superlinear in
participants and near-zero at n=1, but adoption is per-person and the second adult is the hardest
sell in consumer software. *"If your spouse won't check the app, you're back to being the single
source of truth."* The only mechanisms that demonstrably move the second adult are the ones that
require **no adoption at all**: an SMS the spouse already receives, a group chat he's already in,
or a screen on the kitchen wall he already walks past. This is why the category is drifting to
SMS and to hardware simultaneously — both are adoption-free channels. Ohai's own best review is
about a flip-phone-loving mechanic husband who participated *because there was no app*.

**4. Unit economics — pick your poison.** Humans-in-the-loop deliver the love (Duckbill's reviews
are the warmest in the category) but cost so much that you must meter, and metering is the #1
complaint against both Duckbill and Nori. Fully automated is cheap enough to sell at $39–$99/year,
but at that ARPU you cannot fund the model quality that failure mode #2 demands. Yohana — the
richest parent in the category, backed by Panasonic, with full human execution at ~$149/mo —
died anyway, twice, on two continents. Nobody has found the middle.

**A fifth, softer pattern: the founders leave for adjacent, better-monetizing categories.**
Maple's team went to a luxury travel company. Panasonic postponed its follow-up. Milo's founder
concluded the *timing* was wrong, not the problem. The talent is voting that family coordination
is a real problem with an unsolved business model — which is simultaneously the bear case and the
opening.

---

## Section 7 — Onboarding depth benchmark (direct comparison to our 8+N wizard)

Ranked by pre-value setup burden, lightest first:

| Rank | Product | Steps before first value |
|---|---|---|
| 1 | **Ollie** | **1.** Send a text message. No app, no account, no login. |
| 1 | **Sense** | **1.** Forward one email to `share@getsense.ai`. Marketing is literally built on this being one step. |
| 1 | **Schoolcase** | **1.** Forward an email to your private inbox address. |
| 4 | **Somiya** | **3** stated: add anything → it sorts → the right person is nudged. |
| 5 | **Nori** | ~**3–4**: install → create family → invite members → start. Free core, no paywall gate. |
| 6 | **Plannie** | ~**5 minutes**: create household, add members with colors, connect calendars. |
| 7 | **Duckbill** | Low signup (address + billing) but **high per-task friction** — "dozens of follow up questions on every request," >1 business day per round trip. |
| 8 | **Ohai** | ~**6+ gates**: phone number → SMS verification → connect email/Gmail → connect Google Calendar → answer onboarding questions → **hard paywall at $15/mo with no free trial**. Reviews contain a user who *never escaped onboarding at all*, across three browsers and the app. |
| 9 | **MVP (us)** | **8+N screens**, 14 fields for one kid / 19 for two, **~34 taps**, then a SECOND setup sequence auto-presents from Home with ~5 more editor stops. Planner adds 12 knobs and 16–20 taps to a saved plan. |

**We are the heaviest onboarding in the competitive set — heavier than Ohai, whose onboarding
is already generating one-star reviews and documented total-abandonment.** No competitor in this
table asks for anything close to 34 taps before first value. The products gaining share in 2026
have converged on one step.

The mitigating fact: only 2+N of our fields are strictly required. But that is invisible to the
user walking the wizard — perceived length is what causes abandonment, not required length.

---

## Section 8 — Retention and engagement evidence

Honest answer: **almost none is public.** What exists:

- **Milo disclosed no metrics at all** in its shutdown post — no users, no revenue, no retention.
  A founder shutting down after six years who publishes zero numbers is itself weak evidence that
  the numbers were not good.
- **Rating volume as a crude proxy for active install base** (US App Store, 2026-08-21):
  Nori 1,204 · Ohai 208 · Duckbill 68. Nori accumulated 6x Ohai's rating count in roughly
  one-eighth the time. Whatever else is true, the free-core, low-setup, cheap product is acquiring
  users an order of magnitude faster than the paywalled, high-setup one.
- **Duckbill's revenue estimate** (~$10.8M/yr, StartupHub algorithmic, 64% confidence, wide range)
  is the only revenue figure I could find in the category. If roughly right, at a $169/mo blended
  price that implies on the order of 5,000 households — for the best-reviewed product in the set.
  **This category has no consumer-scale winner yet.** Treat the derived household count as an
  order-of-magnitude estimate only.
- **Ohai's review corpus shows churn mechanics directly**: multiple "tried to cancel," "complicated
  to cancel," "can't delete account," "still get these messages daily" reviews. Cancellation
  friction in the reviews is a reliable tell for weak voluntary retention.
- **Nori shipped hardware four months after software launch.** Companies do not build a wall
  device four months in unless phone-app engagement is disappointing them. Their stated reason —
  the app can't wake when the screen is off — is an engagement problem described as a technical one.
- Agent Finder (secondary, low confidence) claims Ohai takes **"2 weeks to build habits."** No
  method behind it; treat as directional only.

**No product in this category has published a retention curve, a DAU/MAU, or a cohort chart.**
If we have our own retention data, we know more about this category than any public source does.

---

## Section 9 — Direct implications for our product

1. **Our interaction model is the outlier.** In-app chat + forms as the primary path is not the
   winning model anywhere in this set. Our Gmail ingestion and photo/flyer ingestion ARE the
   winning model — they are just buried behind the wizard. Sequencing, not capability, is the gap.
2. **The one-step-to-value test is the category's competitive frontier.** "Forward one email
   tonight, check the calendar in the morning" is a real, specific, brutal benchmark. We are at
   34 taps plus a second setup flow.
3. **SMS is the demonstrated second-adult unlock**, and it is the one thing none of our five tabs
   can do. The single best review in this entire corpus is about a husband who participated only
   because there was no app to open.
4. **Apple Calendar and Outlook support are producing one-star reviews for Ohai right now.**
   We share the same Google-only gap. This is cheap, and competitors (Hearth, Maple) already have it.
5. **Users are asking for a plain month calendar view**, across two different products, in negative
   reviews. We should check whether we have one at a glance.
6. **Voice as an input wedge has no evidence behind it in this category.** Voice as an *output*
   channel — Nori's phone-call reminders — has enthusiastic, specific praise. That inverts the
   usual assumption and is worth testing.
7. **Feature-flagged verticals are consistent with the market.** Every product that is winning is
   narrow (Sense = school email; Schoolcase = school email; Ollie = texts). Our two-of-five default
   is defensible; the instinct to turn on the other three is not.
8. **Metering is the most hated pricing mechanic in the category** (Duckbill credits, Nori's 10 AI
   uses). Flat pricing with a real free tier is what Nori is winning on.

---

## Sources

- Apple App Store customer-review RSS, US, pulled 2026-08-21: Ohai.ai id 6477802468 (4.44 / 208);
  Duckbill id 6455085338 (4.28 / 68); Nori – Family AI id 6753757891 (4.82 / 1,204)
- Avni Patel Thompson, "👋🏽 hello/goodbye.", https://joinmilo.substack.com/p/hellogoodbye (2026-01-12)
- Maple shutdown notice, https://www.growmaple.com/
- Wander acquires Maple team, https://shorttermrentalz.com/news/wander-acquires-maple/
- "Panasonic's AI Ambitions Stumble As Consumer Apps Hit Delays and Closures", channelnews.com.au
- Duckbill pricing, https://www.getduckbill.com/pricing
- Ollie pricing + product, https://www.ollie.ai/ and /pricing
- Nori pricing, https://heynori.com/pricing
- Sense, https://getsense.ai/ and its (vendor-interested) 2026 roundup
- Plannie, https://plannie.io/ ; Somiya, https://somiya.app/ ; Babs, https://www.hellobabs.ai/ ;
  Schoolcase, https://schoolcase.app/maple-alternatives ; Hearth, https://www.hearthdisplay.com/
- Wikipedia, Sheila Lirio Marcelo / Ohai.ai ($6M seed, Eniac Ventures, LifeX Ventures)
- Axios, "Say hi to Ohai.ai from Care.com founder" (2024-01-22) — referenced; page 403'd on fetch
- StartupHub.ai Duckbill profile (algorithmic estimates, low confidence)
- Bustle and PeacockParent Duckbill reviews
- Agent Finder parents guide (SEO directory, low confidence — its Nori pricing contradicts Nori's own page)
- DNS/HTTP status checks run 2026-08-21: yohana.com NXDOMAIN; dola.ai → GoDaddy for-sale parking
