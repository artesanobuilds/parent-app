# M1 — Family Calendar / Organizer Apps: Voice-of-Customer Mining

**Miner:** M1 · **Date:** 2026-08-21 · **Geography:** US App Store (US storefront enforced) + US Google Play
**Brief:** `../BRIEF.md`

## Method (state it, it matters)

The repo had zero verbatim customer language. To produce it I did **not** rely on
search-engine summaries (they paraphrase and are therefore useless as VOC). Instead:

- Pulled the **public Apple RSS customer-review feed** for the US storefront
  (`https://itunes.apple.com/us/rss/customerreviews/id={appId}/sortBy={mostRecent|mostHelpful}/page=N/json`),
  10 pages × 2 sort orders per app, deduped. **n = 4,073 real US App Store reviews.**
  Every quote below is copy-pasted verbatim from that feed, with star rating and review date.
- Pulled scale metrics from the **iTunes Lookup API** (`/lookup?id=&country=us`) and from
  the **US Google Play listing HTML** (`&gl=US&hl=en`).
- Pulled positioning lines from each vendor's own App Store description and marketing site.

**Corpus by app** (reviews sampled / rating mix in sample):

| App | App Store ID | n sampled | 1★ | 2★ | 3★ | 4★ | 5★ |
|---|---|---|---|---|---|---|---|
| Cozi Family Organizer | 407108860 | 917 | 94 | 49 | 92 | 146 | 536 |
| Skylight App | 1438779037 | 638 | 46 | 29 | 68 | 98 | 397 |
| TimeTree | 952578473 | 909 | 56 | 30 | 46 | 131 | 646 |
| FamilyWall | 496889629 | 448 | 37 | 17 | 56 | 108 | 230 |
| Hearth Companion | 6498717775 | 117 | 17 | 12 | 14 | 20 | 54 |
| Jam Family Calendar | 6449090626 | 88 | 5 | 1 | 6 | 5 | 71 |
| Google Calendar | 909319292 | 956 | 271 | 141 | 188 | 211 | 145 |

Note: the sample is skewed toward recent + most-helpful reviews, so the rating mix in the
sample is **not** the app's lifetime distribution (which is in the "Scale" rows below).
It is, however, exactly the right skew for complaint mining.

### Sources I could NOT reach (declared, not worked around)

- **Reddit** — blocked to this crawler ("domains not accessible to our user agent"). No Reddit
  quotes appear in this report. Anything you see attributed to Reddit elsewhere in this program
  did not come from me.
- **Trustpilot** — HTTP 403 on every locale. The widely-cited "Cozi Trustpilot 2.1 stars"
  figure appears only in vendor-competitor content-marketing blogs (`usecalendara.com`,
  `gethomsy.com`, `getsense.ai`, `ourcal.com` — all of which sell competing family calendars).
  **Treat it as Tier D / unverified.** I could not confirm it at source.
- **Google Play review text** — Play serves reviews via an XHR the static fetch does not
  return. Play ratings/download counts below are real; Play review *text* is absent.
- **Picniic, Maple, OurHome** — `picniic.com`, `getmaple.co`, `ourhomeapp.com` all fail to
  resolve/connect (HTTP 000), and none has a live US App Store listing under its own name
  (iTunes search returns only unrelated apps). **All three appear to be dead products.**
  I ran out of WebSearch budget before I could source a shutdown announcement, so this is
  stated as an observation about DNS + store presence, not as a sourced shutdown date.
  Nothing in the 2024–2026 review corpus mentions any of the three.

---

## PART 1 — Per-product profiles

### 1. Cozi Family Organizer (Cozi / Time Inc. lineage)

- **Positioning (their words):** "Cozi Family Organizer is the surprisingly simple way to
  manage everyday family life." (App Store description)
- **Pricing 2026:** Free with ads. **Cozi Gold $39/yr** (already known). Gold buys: month view
  on mobile, no ads, calendar search, 3 reminders per event, change notifications, birthday
  tracker, shopping mode. A higher "Max"/AI tier exists and is referenced by reviewers.
  Free tier is now **capped at a 30-day forward calendar window** — this is the single most
  resented product decision in the entire corpus.
- **Scale:** US App Store **4.81★, 396,679 ratings**. US Google Play **~119K reviews, 5M+
  downloads**. By ratings volume this is the category incumbent by an order of magnitude.

**Top praise themes**

1. *Shared visibility ends the "who's taking who" argument* — the load-bearing job.
   - "it aids in communication. It solves that whole 'I didn't know you had drinks tonight!' The term 'it's in cozy' has replaced 'it's on the calendar.'" (4★, 2020-07-21)
   - "With four kids, our schedule was pure chaos until we found Cozi… the consolidated calendar view means we never miss a pra…" (5★, 2026-07-17)
   - "We both know what the week holds and don't have to wait to schedule something until we 'talk to my husband/wife'." (4★, 2019-10-10)
2. *Cognitive prosthesis / longevity* — MENTAL_LOAD
   - "When i lose or forget my phone/cozi ap, I've literally lost my brain." (4★, 2023-04-24)
   - "I have used Cozi for nearly 25 years and I cannot imagine being a wife and mother without this important tool!!" (5★, 2026-07-18)
   - "I am mom to a very neurodivergent family. We tried planners, google calendars, everything —and nothing seemed to work… This app has literally changed my life!" (5★, 2025-09-26)
3. *Shared grocery list as the real daily habit* (frequently the actual reason for install)
   - "I actually initially downloaded it for the syncing grocery list between my husband and I." (3★, 2023-01-22)

**Top complaint themes**

1. **PRICE / paywall retrofit — the loudest theme by far.** Free users who had planned years
   ahead were retroactively cut to a 30-day window; Gold doubled $19.99 → $39.
   - "Why should I have to pay to see a calendar? I will not pay I will find something better." (1★, 2026-03-31)
   - "I have been using the free version for this entire time when suddenly this week was restricted access to anything more than 30 days out!!! … this was a very unethical and sneaky way to force members to upgrade!!!" (1★, 2024-05-24)
   - "Paying to see the entire month is insane… Makes no sense to pay for simple things other apps give for free absolutely ridiculous" (1★, 2026-03-12)
   - "After the price doubled, in one year, I decided to go back to the free version. You can't do anything without a pop up… May be time to move on" (3★, 2026-01-12)
   - "doubling the annual subscription from $19.99 to $39 in 2024? That's not just bold—it's baffling." (2★, 2025-10-03)
2. **ADS + upsell interruption** (PRICE-adjacent)
   - "I don't love the upsell to paid every time the app is opened." (4★, 2026-02-11)
   - "It also has a lot of ads and a clunky UX, but that would be okay if it worked to maintain shared lists. Unfortunately it doesn't." (1★, 2026-04-25)
   - "the home page is littered with ads, and when I'm simply going to check an event," (1★, 2024-05-24)
3. **Reliability / write-loss on the shared object** — this is the theme that actually kills
   the multi-user habit, because it silently punishes the partner who *did* adopt.
   - "I will add something and it will vanish when my husband refreshes his list, or I will delete items that will reappear when he opens his. **The solution has been for him to be the only one updating the list, which defeats the purpose of the app in the first place.**" (1★, 2026-04-20) ← ADOPTION FAILURE, caused by sync
   - "This app constantly freezes. I can't add anything to the calendar, I can't add family members. So dumb. I canceled my subscription and deleted the app." (1★, 2026-02-20)
   - "I go to write in my 3rd date of events and the app keeps freezing. Why would I pay for something I can't even put dates into?" (1★, 2026-04-07)
4. **ENTRY FRICTION + SYNC: additions do not appear where the family already lives**
   - "the iOS app is clunky and inconvenient to add events to. Integration with iPhone's Calendar is only as a subscribed calendar, meaning additions aren't reflected immediately, and you can't create new events without opening the Cozi app. **Ultimately these extra steps. Have been a barrier to wider use in our family.**" (2★, 2026-01-15) ← the single best quote in the corpus on ENTRY FRICTION → ADOPTION FAILURE
   - "This calendar does it work well with other calendars. It doesn't exchange with other calendars well it's all read only." (1★, 2021-07-27)
5. **Redesign regression** — a 2024 calendar redesign and a Dec-2025 AI addition both drew fury.
   - "The month view is impossible - too busy, too confusing, and the font won't let you see beyond a few characters." (1★, 2024-05-23)
   - "the Dec 2025 update now has an AI scheduler feature that takes up the top quarter of the screen. **I don't want it trolling through my emails offering nonsense appointments. I will NEVER pay for this feature.**" (1★, 2025-12-12) ← direct read on our Gmail-ingestion feature
   - "Classic example of developer trying to incorporate AI into an existing App and ruining it by trying to give people something they never wanted." (1★, 2025-11-28)
   - "do not upgrade to the max version. The AI function is extremely basic. It just suggest recipes no way to customize. **It's easier using ChatGPT.**" (1★, 2025-12-29)
6. **VOICE: removal of the Alexa skill is an active churn driver**
   - "Cozi was great when it had an Alexa app skill. Now we use it just on our phones." (3★, 2026-03-30)
   - "We no longer use the shopping list since Alexa is not connected anymore. It is not as convenient without Alexa." (5★, 2024-03-23)
   - "really disappointed they won't provide integration with Google Home or Siri nor automation APIs… **sadly may not renew my Cozi subscription since it lacks API integrations**" (3★, 2026-05-21)
   - "I wouldn't mind an AI so I can quickly speak an event, but even without fancy features, I'll still keep using it." (5★, 2026-03-30) ← voice = nice-to-have, not a switching reason

---

### 2. Skylight (Skylight App + Skylight Calendar hardware, Glimpse LLC)

- **Positioning (their words):** "Skylight is the operating system for your family, bringing
  everyone's calendars, lists, routines, and memories into one place." (App Store description)
- **Pricing 2026:** Hardware $150–$600 depending on size (Calendar / Cal Max / Frame / Buddy).
  **Skylight Plus $79/yr** (already known) and is *required* for the features people buy the
  device for: photo screensaver, meal planning, chore rewards, magic/email import.
- **Scale:** US App Store **4.80★, 50,446 ratings**. Hardware carries its own retail review
  counts (e.g. 4.7★ / 2,167 reviews on one 15" SKU per retail listings).

**Top praise themes**

1. **Capture-without-typing (photo / email forwarding) is the #1 delight driver.** This is the
   most product-relevant finding in the entire mining exercise.
   - "I love how it integrates with all the kids apps and I can **snap a picture of the school calendar and everything loads!**" (5★, 2026-07-21)
   - "The ability to upload a photo and have it then create an event or list is amazing!" (5★, 2026-04-12)
   - "The magic import lets me easily put in calendars so I don't have to look in 4 different places everyday." (5★, 2026-08-06)
2. **Ambient shared surface removes mom-as-router.**
   - "I had been looking for a tool like this to take me out of the driver seat as **the keeper of the calendar/mom/Siri.**" (5★, 2023-08-31)
   - "This has helped to consolidate all of my calendars, whiteboards, to-do lists into one, unified spot. This has helped save me so much time and mental load; I'm grateful." (5★, 2026-08-11)
   - "Unlike community calendars managed on iPads or personal devices, this hardware version fosters organic family gatherings in the morning, allowing everyone to refer to it without pulling out their phones." (4★, 2024-08-04)
3. **ADHD / executive-function segment self-identifies loudly.**
   - "My family and I LOVE our skylight calendar for keeping our ADHD brains organized." (5★, 2026-05-28)

**Top complaint themes**

1. **PRICE — "$300 device plus $80 to use it" is the recurring formulation.**
   - "A $300 digital calendar plus $80 to use it? Not sure how I missed this but I can't type in my recipes or meal plan without paying this app $80 after buying the device for $300." (2★, 2026-01-15)
   - "Woke up one day a couple of weeks ago to a QR code that basically said, 'if you want to show pictures, you need an upgraded plan.' Really frustrating and greedy" (1★, 2026-08-06)
   - "all the fun extras they talk about like grocery list and meal planning and recipes, chore lists, reward systems.. you have to additionally pay monthly to use it." (4★, 2026-05-01)
   - "For the price of this frame, the free side of the app is almost useless and is constantly trying to get you to purchase the subscription service." (2★, 2021-12-08)
2. **The app (as opposed to the device) is the weak link — COMPLEXITY + ENTRY FRICTION.**
   - "App UI is next to unusable: days and times always need meticulous adjustment. UX is clunky and slow: why isn't the calendar view the default when I open the app? … **The day I convince my wife to just use the native iOS apps is the day I go Office Space on this thing**" (1★, 2026-08-17) ← COMPLEXITY + ADOPTION FAILURE in one review
   - "using the app… is TERRIBLE. At least for Apple products. **It's confusing, with too many steps**, and often, when you get where you need, (like finding an 'upload calendar' button) it's just a set of directions for what to do yourself on your ph…" (2★, 2024-05-06)
   - "The organization of the app is not intuitive. If I could give the app a grade, then it would be a 'D.'" (2★, 2026-07-12)
   - "There was quite a learning c…" / "There was a learning curve switching over from other calendar apps" (3★ 2026-08-17; 4★ 2026-07-07)
3. **Regression of the capture feature = the loudest churn signal**, because it removed the
   exact thing praise theme #1 is built on.
   - "one of the biggest selling points was being able to simply forward emails directly to it. **As someone with ADHD that feature was invaluable.** … my brain works by checking things off as soon as I send them somewhere.. Once I forwarded an email to Skylight, it was out of my head. Then without realizing it, email forwarding. I kept…" (3★, 2026-07-30)
   - "I subscribed in order to be able to upload into the magic import and send in or forward emails with dates to make my life easier. But it just is not working all of a sudden. With one school calendar I sent in to be magically imported, **it got dates wrong all over the place. I had to delete**…" (1★, 2024-09-11) ← AI extraction accuracy is a trust cliff, not a gradient
4. **SYNC / onboarding a second adult.**
   - "Connecting another person to your calendar is very hard requiring multi-step process and requiring knowing the device email which is not found anywhere. **It took me 45 minutes to guess it.**" (2★, 2026-01-16)
   - "I had to delete account and app, reinstall and then get approval from my spouse to get the calendar. **Not a good start for a new app for me.**" (4★, 2025-08-17)
   - "my husband's Galaxy has some glitches with the app and it's hard for him to sign in and stay signed in." (4★, 2026-02-26)
   - "it doesn't transfer the color coordinated events in their colors, so you have to manually go in and change every single one, which took a large amount of time." (1★, 2025-01-24)

---

### 3. TimeTree (TimeTree, Inc. — Japanese, large US install base)

- **Positioning (their words):** "Connect over time. Grow bonds together." / "App loved by
  75 million users worldwide" (App Store description; global, not US).
- **Pricing 2026:** Free with ads. **Premium $4.49/mo or $44.99/yr**, first month free
  (source: timetreeapp.com/intl/en/premium, fetched 2026-08-21). Premium = no ads, file
  attachments, event pinning, vertical 3-day view, support. **Per-person, no family plan.**
- **Scale:** US App Store **4.85★, 89,860 ratings**. US Google Play **~235K reviews,
  10M+ downloads** (`works.jubilee.timetree`).

**Top praise themes**

1. **Speed of entry — the only app in the corpus praised for *how fast* you add an event.**
   - "It's FREE, it's quick to add and update your schedule/calendar… It also has the simplest interface when adding events" (4★, 2018-04-14)
   - "mostly the simplicity of using it. It is so quick and easy to add something on the cale…" (5★, 2026-02-24)
   - "I do not like google calendar. It looks too complicated. TimeTree looks nice and is the best calendar sharing app I've ever used." (4★, 2021-01-26)
2. **Instant change notification to the other adult.**
   - "My favorite feature is that we get alerts as soon as something is added to the calendar." (4★, 2017-11-16)
   - "he gets a notification and knows the plan. He knows when I'm free and when I'm not. We're so in sync now and we don't forget anything." (5★, 2026-06-14)
3. **Photo/flyer capture (added ~2024) rated as the standout.**
   - "The new feature that allows you to create events from your camera or from pictures you have taken already of flyers or posters etc. **is genius. It literally makes inputting events into your calendar effortless and super quick.**" (5★, 2024-07-08)
4. **Co-parenting / custody use case.**
   - "it has been a lifesaver for managing our shared custody of the kids." (5★, 2026-05-11)

**Top complaint themes**

1. **ADS — the dominant 2026 complaint; ad load escalated sharply.**
   - "Too many ads, many large and invasive. Ads take up 1/3 the screen. Gambling and casino ads. :(" (3★, 2026-06-24)
   - "Greed has completely overtaken TimeTree. It used to be a good shared calendar with non invasive ads. Now they have pop ups take up the entire screen that you have to X out. **Find a different calendar. I know I am now.**" (1★, 2026-06-13)
   - "I like this app, but OMG WHAT ARE THESE ADS?!" (3★, 2026-02-02)
2. **PRICE: per-seat pricing on a product whose entire value is multi-seat.**
   - "With this app being a shared calendar app it makes no sense that there isn't a family plan to remove ads/premium experience and **it's $45 a year per person. That's wild work.**" (2★, 2026-05-14)
   - "I would have no problem paying for the membership if it would include both my husband and myself. I think it's crazy that we would each have to subscribe and pay separately" (4★, 2024-08-15)
3. **SYNC: silent partial sharing — the worst possible failure mode for a shared calendar.**
   - "the events I am entering into the calendar aren't shown on his calendar. Or at least, not all of them. **We can't for the life of us figure out the rhyme or reason as to why some events are shared, while others aren't. But it renders the app entirely useless.**" (1★, 2026-01-29)
   - "when I add something to the calendar or my ex-wife does, we eventually realize the other person can't see it and it's causing a lot of problems." (2★, 2026-01-06)
   - "You will have to put everything in manually and then it will show twice on your own calendar. Takes all the convince out of a shared calendar." (1★, 2026-03-03)
4. **Lock-in / no export — an explicit stated reason to warn others off.**
   - "if you ever want to export your calendar for use with other calendar applications, you're out of luck. **They don't seem too concerned, as this tactic discourages users from leaving the app.**" (1★, 2025-11-15)
   - "Why can't I export this calendar to something like Google Calendar?? I'm forced to use this one now." (1★, 2026-07-06)
5. **ENTRY FRICTION, explicitly counted in taps.**
   - "Too many steps to submit an event. I pay for premium hoping to avoid having too many pop ups or extra clicks when entering daily events… To enter an events I have to click the add even button, then it asks if I want to use a picture, calendar event, or a 3rd option. This is another click. After I submit the even for a given day I'm given yet another notification and to confirm what I just did." (2★, 2024-05-06)
   - "Too many steps to do what you need to do, not fun and user friendly." (1★, 2026-03-21)
6. **AI backlash — blunt.**
   - "No one wants AI. Been using for 4 years. Deleting this right now. **No one wants AI.**" (1★, 2026-07-31)
   - "Their terms of service has been updated and includes AI now, absolutely useless. It really sucks, I loved this app" (1★, 2026-01-22)

---

### 4. FamilyWall (Family & Co)

- **Positioning (their words):** "Happy Family Organization — Helping families with their daily
  organization and communication… it's your all-in-one solution for a seamlessly coordinated
  family life." (familywall.com)
- **Pricing 2026:** Free tier is generous (calendar, lists, messaging, photos). Premium gates
  budget, meal planner, extra storage; a reviewer states **"$45 a year"** (1★, 2026-01-24).
- **Scale:** US App Store **4.85★, 22,354 ratings**. US Google Play **~102K reviews,
  5M+ downloads**.

**Top praise themes**

1. **Free tier does the core job — the counter-example to Cozi's paywall.**
   - "Free version so useful! So grateful it's free! It's a game changer for our busy family with both parents having more than one job, coordinating babysitters etc." (5★, 2026-01-21)
   - "I thought of buying the sky calendar but could not afford it. EVERYONE uses phones and apps in our family." (5★, 2025-10-16)
2. **ADHD / executive function — the strongest self-identification in the corpus.**
   - "AMAZING FOR ADHD MOMS — Okay moms… I have to put you on. 👀 I've been using FamilyWall – Family Organizer for about a month and WOW. My life finally feels organized again." (5★, 2025-12-07)
   - "This app has been life saving. An ADHD tool that finally helped me." (5★, 2026-05-23)
3. **Relationship outcome, stated bluntly.**
   - "App of the Decade — **This app probably saved my marriage.** Puts Outlook to shame." (5★, 2026-02-06)
   - "My husband has a TBI and this app has been a life saver!" (5★, 2026-02-18)
   - "It's helps me and my very disorganized husband stay in sync." (4★, 2024-12-11)

**Top complaint themes**

1. **Feature bloat vs. broken basics — the clearest COMPLEXITY quote in the whole corpus.**
   - "feature rich, but base functionality fails — **App can do everything, but I wish it only did one thing.** You name it, it's an option. Unfortunately, no matter what I try, if I put an entry on one device, it doesn't show up on the others about 20% of the time. **For me, I would give up every other feature to have a calendar app be in sy**…" (3★, 2026-07-05)
   - "Too freaking confusing trying to set up. No instructions no clarity..even to set up a simple task list." (1★, 2026-05-23)
   - "I love spending 40 minutes of my day trying to figure out why I'm getting the 'we're sorry, you can't connect to server'" (1★, 2026-07-27)
2. **SYNC failure between the two adults.**
   - "Out of no where, I can't see my husband's schedule and everything doubled and tripled on my calendar." (1★, 2025-07-11)
   - "there has been an ongoing syncing issue, not showing updates on each persons calendar" (1★, 2024-02-23)
   - "our shared family lists do not always sync. So my husband will have items on his list that I don't see and vice versa even though we both contribute" (5★, 2022-12-28)
   - "if you want to give heads up . Because your shared calendars on other apps as google calenda… You will have to do double work and rewrite all your schedules" (3★, 2023-04-11)
3. **ENTRY FRICTION on a single control — a scroll-wheel time picker nearly kills adoption.**
   - "**setting the time is a scrolling bar, which is seriously almost a dealbreaker for me. It takes so much**…" (4★, 2025-11-24) ← one widget, cited as a dealbreaker
4. **PRICE with stagnation.**
   - "I cancelled my paying membership. At $45 a year, that is $150 I have paid to support the app over the last few years and nothing that is a basic functionality/suggestion has been implemented. But they have time to launch a crowdsourcing fundraiser for a digital calendar - that no one asked for." (1★, 2026-01-24)
5. **"Why not just use the built-in Apple apps?" — the real substitute.**
   - "IPhone does all of this already? Redundant. Basically it's the Reminders/Lists app that's already in your phone. They just added a banner image. … You already have Find My. You already have iCal to import" (2★, 2022-01-29)
6. **Location tracking is unwanted friction for a calendar buyer.**
   - "PLEASE STOP ASKING FOR MY LOCATION. Every. Single. Time. I open the app… I just don't think there's any reason a calendar app should have my location." (3★, 2022-11-11)

---

### 5. Jam Family Calendar (Jam Life, Inc.)

- **Positioning (their words):** "Jam combines calendars, to do and shopping lists in one spot
  so everyone in the family can get on the same page and **do their fair share**. Jam is here to
  streamline, simplify, and support modern family life as we know it." (App Store description)
  — note "fair share": Jam is the only product in the set that positions against the *distribution*
  of the mental load rather than merely against disorganization.
- **Pricing 2026:** Free download, subscription. A 1★ reviewer states **"$100 a year to sync a
  calendar."** No public pricing page reachable (jamfamily.com is a JS shell that returns no
  server-rendered content).
- **Scale:** US App Store **4.64★, only 201 ratings.** This is a *tiny* product. Treat its
  praise as early-adopter signal, not market validation.

**Top praise themes** (skew heavily toward capture and toward partner-equity)

1. **Email forwarding as the entry surface — repeatedly the single named reason for love.**
   - "I love the fact that I can just forward emails with event details to Jam, and it puts them in my calendar for me! **I hate having to sit there typing all my events into my calendar**, so this feature is amazing." (5★, 2024-03-20)
   - "the ability to delegate tasks to specific family members, and being able to simply forward emails to…" (5★, 2024-05-03)
2. **It moves work off the default parent.**
   - "Hubs and I finally on the same page — **Gone are the 'no YOU'RE taking him to karate today'** and the 'I told you to pack swimsuits to the birthday!!'" (5★, 2024-07-17)
   - "My husband has the full family calendar at his fingertips. We don't argue as much about schedule misunderstandings or my impatience about him not remembering when som…" (5★, 2024-03-08)
   - "I really love that it includes driving time and you can assign a driver." (3★, 2024-07-08)
3. **Explicitly chosen over Skylight, on cost and usability.**
   - "I had looked into purchasing a skylight calendar, and read tons of reviews… I'm so thankful I stumbled upon the Jam Family calendar and went this route instead!" (5★, 2025-01-29)
   - "it felt so much more user friendly than skylight. I recommend to all my mom friends!" (5★, 2026-07-28)
4. **Caregiving edge cases: au pairs, temporary caregivers, multi-generational.**
   - "especially helpful when we have changing pickup and drop offs and temporary caregivers" (5★, 2025-12-12)
   - "My husband and I have a neurodivergent child who has a multitude of appointments, classes and therapies every week as well as hours of administrative work between insurance and IEP's. At the same time, my mom lives with us as well who has her own medical needs" (5★, 2024-07-23)

**Top complaint themes** (only 12 reviews below 4★ in the entire corpus — thin)

1. **PRICE relative to a commoditized job.**
   - "Expensive for commoditized functionality — **$100 a year to sync a calendar. Impossible to delete your data. Nonstop spam.**" (1★, 2025-05-15)
   - "Would love to see some additions, considering the price" (4★, 2025-08-26)
2. **Missing table stakes → immediate reversion to the incumbent.**
   - "the app is a bit clunky and buggy. **I can't believe there aren't recurring task options.** 🫠 **Back to Timepage for now.**" (3★, 2024-08-24)
   - "I don't think it is quite there yet and **I will be sticking to family wall for now.**" (3★, 2024-07-08)

---

### 6. Hearth Display (Hearth Display Inc — hardware + Hearth Companion App)

- **Positioning (their words):** "Kids grow fast. Hearth grows with them." / "Replace your
  whiteboard, wall calendar, chore charts, and scattered reminders with one shared, easy-to-use
  system." / "Transform daily organization into a seamless, shared responsibility."
  (hearthdisplay.com; App Store description)
- **Pricing 2026:** Wall display hardware (several hundred dollars) + subscription for
  "Hearth Helper" (an **SMS AI assistant**), synced calendars, routines. Site was running a
  "Save $105" back-to-school promo on 2026-08-21.
- **Scale:** US App Store **3.93★, 218 ratings** — *by far the lowest-rated app in this set.*
  US Google Play **~50 reviews, 10K+ downloads**. Vendor site claims 4.7/5 from 786 reviews
  for the hardware (self-hosted reviews, treat accordingly).

**Top praise themes**

1. **Kid routines + rewards is the actual product, not the calendar.**
   - "The routines feature has been a game changer for my 5 year old ADHD child." (vendor site testimonial, Andie P. — vendor-hosted, not App Store)
   - "It's transformed how my kids do chores, and helps me to be able to only 'nag' them about one thing…'did you look at the Hearth?'" (5★, 2026-08-17)
   - "The kids love earning stars that they can trade in for rewards and they feel a true sense of accomplishment" (5★, 2025-08-14)
2. **Photo capture → calendar, again.**
   - "Love the ability to just snap a photo of a schedule and have it added to my calendar automatically!" (5★, 2025-08-10)
   - "Hearth helper automatically adds items to the cal…" (5★, 2025-08-20)

**Top complaint themes** — Hearth is where COMPLEXITY and ENTRY FRICTION are most severe.

1. **ENTRY FRICTION, stated as the reason to not buy.**
   - "Don't buy it — Save your money. **It takes too long to add anything.** It glitches all of the time. Things go missing from it. I paid for the year subscription in advance which was stupid because I'd have sold this on fb marketplace by now." (1★, 2025-03-18)
   - "**Takes so long to input data because you have to scroll through entire months to get to the date you need. You can't just type in the numeric date.**" (1★, 2025-05-24)
2. **COMPLEXITY / data-model burden pushed onto the parent.**
   - "the way calendars are managed is so cumbersome! **You basically have to set up a unique calendar for each of your children, and if they are both attending the same activity, you have to input the same appointment multiple times for each kid!**" (3★, 2024-11-29)
   - "The app isn't very intuitive for managing 5 family members. As the parent I should be able to manage the whole family from my app **without having to log in / out of my kids accounts** to manage their calendars." (3★, 2025-03-16)
   - "You have to really use the app to figure out how it works and make it functional for yourself." (3★, 2024-12-11)
   - "the OS is clunky and feels like a 1990s Windows PC." (2★, 2025-01-01)
3. **Cost vs. delivered value; the spouse verdict.**
   - "what my husband calls **'the most expensive picture frame of all time,'** (I've finally gotten to a place of agreement here)… The interfaces do not speak to each other. The online pictures are beautiful. The ads are beautiful, the blog posts are beautiful." (1★, 2025-08-14)
   - "You could purchase a small tv to mount to the wall and upload a google calendar for way less. And you don't have a subscription fee which in my household grants me access to the weather and lists." (2★, 2025-03-27)
   - "it's a bit of a bummer to spend so much on the product and have the app ecosystem as clunky as it is." (3★, 2024-12-11)
4. **SYNC is import-only, not two-way.**
   - "It does not sync with Apple Calendar, rather **it imports a subscribed calendar. And vice versa.** This poses challenges because events ca…" (2★, 2025-02-24)
   - "When our family switched to hearth I didn't realize we would lose having locations listed on events. As a family with multiple sports where practices and games happen at different gyms and fields, this is super annoying." (2★, 2025-06-25)
5. **VOICE, asked for explicitly and by name.**
   - "It does not make sounds of any kind. No alarms. No reminders. It can't set times and **you can't talk to it like other 'ai helpers.'** Very disappointing." (5★[sic], 2025-10-28)
   - "Features like widgets, **smart voice event creation**, Alex skill enablement and google home compatibility are some features I would love to see incorporated in such a paid application." (3★, 2026-02-04)
6. **Onboarding death loop → immediate competitor switch.**
   - "Terrible UI. Stuck in a death loop of unrecognized email and password. Calendar and app are not usable. **Very poor onboarding experience for an expensive piece of hardware. Switching to skylight.**" (1★, 2025-01-07)

---

### 7. Google Calendar (as used by families)

- **Positioning:** "Google Calendar: Get Organized" — a general-purpose calendar, not a family
  organizer. It has no family/person model, which is precisely what reviewers in the *other*
  apps say they left it for.
- **Pricing:** Free. **Scale:** US App Store **4.54★, 131,441 ratings**; Google Play
  **4.74M reviews, 10B+ downloads** (bundled/preinstalled, so downloads are not comparable).
- **Sampled rating mix is by far the worst in the set** (271 of 956 sampled reviews are 1★),
  but that reflects general-purpose-app grievance rather than a family-specific verdict, so I
  am not ranking Google Calendar's complaint themes alongside the others.
- The family-relevant signal is what other apps' reviewers say **about** it:
  - "I do not like google calendar. **It looks too complicated.**" (TimeTree 4★, 2021-01-26)
  - "We had been living and dying on my iCal shared by the family, which seemed great for just events on the calendar, I like how Jam's layout is more of an 'all-in-one'" (Jam 4★, 2024-09-03)
  - "IPhone does all of this already? Redundant." (FamilyWall 2★, 2022-01-29) ← the substitute cuts both ways

---

## PART 2 — Cross-product synthesis

### Ranked complaint themes across all products

**1. PRICE — the paywall retrofit, not the price level.**
Nobody in this corpus objects to paying for a family calendar in principle. They object to
(a) a free capability being taken away from an existing habit, (b) a price doubling with no
new value, (c) per-seat pricing on an inherently multi-seat product, and (d) hardware plus
subscription. The Cozi 30-day-window retrofit and the TimeTree ad escalation are the two most
violent reactions in 4,073 reviews. Tags: PRICE.

**2. SYNC — silent, partial, or one-way propagation between the two adults.**
This is the most *destructive* theme even though it ranks second by volume, because it converts
directly into adoption failure: when the shared object is unreliable, families rationally
collapse back to one writer, at which point the app is a private calendar with extra steps.
Tags: SYNC → ADOPTION FAILURE.

**3. COMPLEXITY — setup burden, non-obvious data model, "app can do everything."**
Consistently framed as *the app made me do the modeling*: one calendar per child, per-kid
duplicate entry, log in/out of kid accounts, guess a device email, 45 minutes to add a spouse.
Reviewers do not ask for more features; several explicitly offer to trade every feature for a
reliable core. Tags: COMPLEXITY.

**4. ENTRY FRICTION — taps to log one event.**
Counted explicitly and repeatedly by users. Scroll-wheel time pickers, month-scrolling date
pickers, confirmation dialogs, add-event modals with a type-picker step. Called a "dealbreaker"
and a "barrier to wider use in our family." Tags: ENTRY FRICTION.

**5. ADOPTION FAILURE — the other adult never really lands.**
Rarely stated as "he refuses"; almost always stated as a *consequence* of #2/#3/#4 — the
Android partner can't stay signed in, the invite flow fails, additions don't show in his native
calendar, one person becomes the sole writer. Tags: ADOPTION FAILURE.

**6. Redesign / AI regression on an established habit.**
Cozi's 2024 calendar redesign and Dec-2025 AI scheduler, TimeTree's ad-heavy 2026 redesign, and
Skylight's email-import regression all produced 1★ reviews from users of 5–15 years. Users
punish change to a load-bearing habit far harder than they punish missing features.

**7. Support absence at the moment of failure.**
"no one to call and only AI responses"; unanswered support email chains; refund friction.

**8. Lock-in / no export.** TimeTree specifically; cited as a reason to warn others off.

**9. ADS.** Concentrated in TimeTree (2026 escalation, including gambling creative) and Cozi's
free tier. Notably: many users volunteer that they would *pay* to remove ads.

### Best 8 verbatim quotes (my selection)

1. "the iOS app is clunky and inconvenient to add events to… **Ultimately these extra steps. Have been a barrier to wider use in our family.**" — Cozi, 2★, 2026-01-15
2. "I will add something and it will vanish when my husband refreshes his list… **The solution has been for him to be the only one updating the list, which defeats the purpose of the app in the first place.**" — Cozi, 1★, 2026-04-20
3. "**App can do everything, but I wish it only did one thing.** … if I put an entry on one device, it doesn't show up on the others about 20% of the time. **I would give up every other feature to have a calendar app be in sy**…" — FamilyWall, 3★, 2026-07-05
4. "the events I am entering into the calendar aren't shown on his calendar. Or at least, not all of them. **We can't for the life of us figure out the rhyme or reason as to why some events are shared** … **But it renders the app entirely useless.**" — TimeTree, 1★, 2026-01-29
5. "I love the fact that I can just forward emails with event details to Jam, and it puts them in my calendar for me! **I hate having to sit there typing all my events into my calendar.**" — Jam, 5★, 2024-03-20
6. "Save your money. **It takes too long to add anything.** … I paid for the year subscription in advance which was stupid because I'd have sold this on fb marketplace by now." — Hearth, 1★, 2025-03-18
7. "I had been looking for a tool like this to take me out of the driver seat as **the keeper of the calendar/mom/Siri.**" — Skylight, 5★, 2023-08-31
8. "**I don't want it trolling through my emails offering nonsense appointments. I will NEVER pay for this feature.**" — Cozi (on its Dec-2025 AI scheduler), 1★, 2025-12-12

Runner-up, on the price retrofit: "I have been using the free version for this entire time when
suddenly this week was restricted access to anything more than 30 days out!!! … this was a very
unethical and sneaky way to force members to upgrade!!!" — Cozi, 1★, 2024-05-24

### Why families churn — the evidence

Ranked by frequency in the sub-4★ corpus:

1. **The shared object stopped being trustworthy.** Events/list items vanish, appear on one
   phone only, duplicate, or move. Because a family calendar's whole value is that *the other
   person can rely on it*, one silent failure is disproportionately fatal: the family reverts to
   texting, and one parent resumes being the router. Multiple reviewers describe exactly this
   degradation path before deleting.
2. **A price or paywall change hit an established habit.** Not new-user price sensitivity —
   5-to-15-year users. "I have used Cozi for over 5 years… when renewing this year I saw the
   price increased $10 and I just don't see why."
3. **A redesign or an AI addition degraded the thing they used daily.** Including outright
   AI rejection ("No one wants AI").
4. **The second adult never actually onboarded**, usually for a mechanical reason (Android
   sign-in, invite link, unfindable device email, no way to send/receive an invite from the
   partner's own app), after which the app is single-player and gets deleted.
5. **A missing table-stakes primitive** (recurring tasks, event locations, export, two-way sync)
   sends them straight back to the incumbent or to Apple/Google.

**The single most common reason a shared organizer gets abandoned:** it stops being a
*shared* source of truth — either because sync silently fails or because the second adult never
successfully onboarded — and the family collapses back to one writer plus text messages. Price
increases and redesigns are the second cluster; they are what makes a *still-working* app get
cancelled.

### Signal specifically on VOICE (our open question)

Voice appears in **51 of 4,073 reviews (~1.3%)**, and the character of those mentions matters
more than the count:

- The overwhelming majority want **smart-speaker integration for lists** (Alexa "add milk"),
  not dictation inside the app. Cozi's *removal* of its Alexa skill produced repeated churn
  language, including "sadly may not renew my Cozi subscription since it lacks API integrations."
- Only a handful ask for **speech-to-event**: "I wouldn't mind an AI so I can quickly speak an
  event, but even without fancy features, I'll still keep using it" (Cozi 5★, 2026-03-30);
  "smart voice event creation" (Hearth 3★, 2026-02-04); "Being able to speak to the board addi…"
  (Skylight 5★, 2025-05-17); "you can't talk to it like other 'ai helpers'" (Hearth, 2025-10-28).
- **No reviewer in 4,073 describes voice as a reason they chose, kept, or left a product.**
- What they *do* describe as transformative is **capture without typing by other means**:
  forwarding an email, snapping a photo of a paper schedule, "magic import." Those appear far
  more often than voice, in strongly positive language, and their breakage produces churn.

**Read:** for this population, the demand is for *low-effort capture*, and the proven modalities
are photo/flyer, email forward, and smart-speaker-for-lists — not conversational voice. Voice is
a nice-to-have; camera/inbox capture is a switching reason. Confidence: moderate-high for the
relative ranking, moderate for the absolute claim (App Store reviews systematically under-report
feature preferences that no shipped product has trained users to expect).

### Signal on COMPLEXITY TOLERANCE (our open question)

Direct, and unfavorable to elaborate products:

- Reviewers volunteer trades **against** breadth: "I would give up every other feature to have a
  calendar app be in sync"; "App can do everything, but I wish it only did one thing."
- Setup work is where they quit: "Too freaking confusing trying to set up"; "This app froze a
  minimum of 5 times in just initially trying to get it set up… Eventually gave up trying";
  "Very poor onboarding experience… Switching to skylight."
- Per-child modeling is repeatedly rejected as *the user doing the app's job*: setting up a
  calendar per kid, entering the same event once per kid, logging in and out of kid accounts.
- The highest-rated products in the set (TimeTree 4.85★, FamilyWall 4.85★, Cozi 4.81★) are the
  *narrow* ones; the elaborate hardware+AI product (Hearth) is the lowest at **3.93★**.

### Signal on the ADHD / executive-function segment (unprompted, cross-product)

Present in every product's praise, self-identified, often as the *reason* the product works:
"AMAZING FOR ADHD MOMS", "my family and I LOVE our skylight calendar for keeping our ADHD brains
organized", "As someone with ADHD that feature was invaluable", "I googled 'best planning app for
people with ADHD'". ~38 unprompted mentions across the corpus. This is a discoverable,
self-describing acquisition segment that none of these vendors targets by name in positioning.

---

## Confidence and caveats

- **High confidence:** all quotes are verbatim from the US App Store RSS feed with the stated
  rating and date; scale numbers are from Apple's and Google's own endpoints on 2026-08-21.
- **Medium confidence:** theme *rankings*. They come from regex-clustered frequency over a
  recency+helpfulness-skewed sample, not from a coded content analysis with an intercoder check.
- **Low confidence / declared gaps:** no Reddit, no Trustpilot, no Google Play review text, no
  Wirecutter/NYT/Verge comparative reviews (WebSearch budget exhausted at 200/200 before I could
  reach them). No sourced shutdown dates for Picniic, Maple, or OurHome — only the observation
  that all three domains fail to resolve and none has a live US App Store listing.
- Reviews are a **complaint-biased and delight-biased** instrument; they capture what people feel
  strongly enough to write about, and systematically miss quiet non-adoption. The absence of
  "my husband refuses to use it" as a stated theme should **not** be read as evidence that
  partner non-adoption is rare — reviewers describe its mechanical causes instead.
