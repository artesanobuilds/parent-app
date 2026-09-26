# How US parents plan their children's lives

A research report for the MVP product decision. Compiled 2026-08-22.

Six phases, 41 automated research agents, 31 source reports, 12 chart datasets. Full evidence lives in `raw/` and `data/`; this report cites those files rather than reproducing them. Every number carries publisher, year, method and tier inline. The four corrections blocks at the end of `BRIEF.md` govern every figure and override the collector reports. This feeds `docs/GTM/gtm-strategy.md`, which stays canonical. It does not replace it.

Start at Part I. It is the decision content and it stands alone. The glossary that sits before it is a lookup table rather than a chapter, so skip past it and come back only when a term sends you there.

---

## Why this document exists

This report does three jobs, in this order.

It informs what to build and refine next, by setting the evidence that users want each candidate move against the free substitutes already doing that job.

It generates initial product hypotheses. Every recommendation here is a hypothesis that still needs validating by experiment. None of it is a conclusion to implement on faith, and section 5 splits the two explicitly.

It informs go-to-market: which audience to reach first, when in the year to spend, and what language works with that audience and what repels it.

This is a decision input, not a plan. The canonical strategy document remains `docs/GTM/gtm-strategy.md`. Nothing here replaces it.

Nothing in this report has been tested with a real user. No parent was interviewed and no survey was fielded. The cheapest test it proposes takes twenty minutes: open ChatGPT and Gemini and check whether a general assistant can already watch a registration page and push you when it opens, which decides whether the registration watchlist is whitespace or a bad market.

---

## Contents

| Part | What it is | Words |
|---|---|---|
| **Method** | What was done and in what order, the prior desk research this study checked rather than repeated, why an adversarial pass exists, source tiers, the scope of the ~27% re-traced-kill error rate, and the honest limitation that this is not primary customer research. Read before any conclusion | 627 |
| **Terms used in this report** | A glossary of the product internals, research-program labels, external rules, survey instruments and metrics the report names. First use of each is marked with an asterisk | ~2,600 |
| **Part I - Decision** | Executive summary, what could resonate most, inputs to go-to-market, the case against this report, what to do next. **About an 18-minute read** | ~4,482 |
| **Part II - Evidence** | Who plans, what they plan, seasonality, voice, complexity, cohorts, competitive position, email architecture, product fit. All eleven charts live here | ~3,999 |
| **Part III - Reference** | Appendix A the verbatim corpus, Appendix B the five email defects, Appendix C what this research cannot answer, Appendix D the kill list | ~5,410 |

Part I stands alone. Parts II and III exist to be checked against, not read straight through.

---

## Method

**What was actually done.** About 41 independent research agents ran in six stages, each feeding the next. Collection agents went out for published statistics on population, task frequency, seasonality, interaction modality and complexity tolerance (labelled P1 to P12). Mining agents read what parents themselves wrote, in App Store reviews and Reddit threads (M1 to M5). Verification agents re-traced the collectors' numbers to their origin publishers and killed the ones that did not survive the trace (V1 to V7). A quantification pass turned what survived into the twelve chart datasets in `data/`. Synthesis agents built the workflow model, the email decision memo and the product-fit verdict (S0 to S3). A red team then attacked all of it (S4), and S4's verdict is this report's spine. Those letter-number labels are a filing system for reading the filenames in `raw/`, not vocabulary anyone needs to learn.

**What it started from.** This project already held a substantial body of desk research in `docs/GTM/`: a market-research report, a five-vertical expansion, a canonical strategy document and an adversarial critique of the idea. This study read and challenged that work rather than starting fresh. So it deliberately did not re-derive market sizing, competitor pricing or the headline mental-load statistics, all of which were already established there, and spent the budget on what was missing instead. It also found errors in that corpus. `gtm-research.md` carries a fabricated Pew figure, "37 million Millennial parents," which Pew never published. `gtm-strategy.md`'s cleared-for-marketing list carries the Bright Horizons summer statistics under the wrong year, with a subgroup base presented as a full-sample finding. The existing work was the starting point and it was the first thing checked.

**Why an adversarial pass exists.** Research agents left unchecked will confirm whatever they went looking for, and a fleet of them will do it fast and in unison. So a separate set of agents was tasked with refuting the findings rather than extending them, and a red team was tasked with attacking the recommendations rather than dressing them. That produced ~35 corrections, several of them against this report's own recommendations: V7 killed the Cozi email precedent that would have supported the email build, and V6 killed a fabricated Pew figure that appears in this repo's own `gtm-research.md`.

Tiers: **A** government or peer-reviewed; **B** research organisations publishing method; **C** industry or vendor disclosing method; **D** stat-aggregator blogs. **Tier D is never citable.** Two labels sit outside A-D and are always named: *Primary (own measurement)* and *Analyst judgement*.

**About 27% of the kills that were re-traced were overturned.** Read that scoping carefully: two verifiers re-traced **22** previously-killed statistics across two passes and overturned or reclassified **six** of those 22 (V6: 3 of 12; V7: 4 of 18). The figure describes the re-traced subset, **not the appendix as a whole** - it does not mean a quarter of Appendix D is wrong, and the un-re-traced remainder has no measured error rate in either direction. V7 states a third pass would likely still find one or two and declines to call the list final; the stop was budget-forced, not judged sufficient. Treat any individual re-traced kill as roughly three-in-four reliable, and carry the per-item confidence and verifier attribution printed against every row in Appendix D. Most research of this kind never measures its own residual error, so the rate is published here as a working tolerance on the numbers that survived, not as a disclaimer against them. It is also the one part of the verification programme the red team in section 4 could not find fault with.

**Honest limitation.** This is secondary research plus review and forum mining. No parent was interviewed and no survey was fielded. The Reddit corpus is browser-scraped individual comments skewed heavily to r/adhdwomen and r/ADHD. App Store reviews cannot see quiet non-adoption: V5's partner-refusal regex returns **1 hit in 15,692 reviews** for a phenomenon the counted co-parenting analysis shows is ubiquitous, and six of M1's seven apps average 4.8 stars, so the corpus over-represents people for whom a shared calendar worked. Strong prior, not a substitute for talking to parents.

---

## Terms used in this report

This report names parts of a codebase and a research apparatus that a reader outside the project has no reason to know. This section is a lookup table, not a chapter: nobody needs to read it straight through, and Part I is written to be followed without it. Everything below is defined once here. The first time each term appears in the body it carries an asterisk, like `if aid:`* and CASA*, meaning "defined in this section." Later uses are unmarked.

### The product

**MVP.** The working codename of the product under decision: a US consumer iOS app, in closed beta, that helps parents plan their children's lives. There is also a web dashboard and an admin CMS. Nothing about the name is final.

**The five tabs.** Home, Coach, Planner, Circle, Settings.

**The Coach tab.** A general parenting-chat surface. The parent types or speaks a question and gets an answer with citations and saved history. It is advice, not logistics.

**The Planner.** Where a parent goes to sort out who is doing what. It has two halves. "Plan" holds the lifecycle board, a calendar, and a search that goes out to the live web looking for programs. "Ask the coach" is a second, separate chat, wired to the planning agent rather than the advice one. This is where the product's scheduling work happens.

**Circle.** The tab for other adults: group conversations scoped to people the parent has linked with, such as a grandparent or a sitter, plus a household roster and invite links. Both ways of forming a link, claiming an invite and accepting a request, require the other adult to hold an account, which matters because the counted evidence in this report says the second adult is exactly who refuses to install anything.

**The lifecycle board, and its six stages.** What a parent sees when they open the Planner: everything they are tracking, sorted by where it stands. Considering. To register. Registered and needing action. All set. Waiting or blocked. Not doing. Six places for one thing to be, which is the right amount of scaffolding for something that takes many steps to finish.

**`build_board`.** A parent opens the Planner and sees cards, each one carrying a next step and a date. One function on the server assembles that entire view out of the family's tracked activities and to-dos, and hands the same result to the phone and to the web dashboard, so whatever it leaves out is missing from both (`mvp-backend/app/cos/lifecycle.py`).

**`activity_id`.** A reminder in this app normally hangs off something bigger: sign the form, for the camp. Nothing forces that, and a reminder is allowed to belong to nothing at all, which is exactly the shape of a permission slip or a dentist appointment. This is the column that would hold the link, and it is permitted to be empty.

**`if aid:`.** A parent cannot write down "dentist, Tuesday, 4pm" anywhere in this app. The only way to create anything is to search the web for an activity and save the result. The database already stores a reminder that belongs to no activity, and the planning agent can already create one, but no screen ever shows it: a single line inside `build_board` checks whether the reminder has a parent activity and drops the row when it does not. The fix is to show what is already there, not to build a new system.

**The five verticals, or "doors."** Five kinds of planning job the app knows how to walk a parent through: summer camp, an after-school activity, an outing, a school event and a trip. Each carries its own wording, its own idea of what a date means and its own capabilities, so teaching the app another kind of job is an entry in a list rather than new machinery (`camp`, `extracurricular`, `outing`, `school_event`, `trip`).

**A feature flag defaulting off.** Three of the five doors are shut unless somebody opens them, and a shut door is an invisible one: the parent is never shown a way in, so as far as they can tell the app does not do that job. Everything behind the door works, and an activity of that kind created some other way still appears normally. Opening one is a setting somebody changes, not something anyone has to build.

**The registration watchlist.** The parent gets told before registration for a program opens: once seven days out, once just before. A to-do is written alongside the notification, so a push that never lands does not take the obligation with it. It arms itself the moment an activity carries an opening date, and that date comes from the discovery search (`registration_opens_at`).

**`SavedView`.** A parent can bookmark things in several places in the app and then cannot find any of them again. The screen that would list what they saved exists and nothing opens it, so saving works and reading back does not (`SavedView.swift`).

**The orphaned third `ChatView`.** A parent can talk to the app in two places, the Coach tab and the Planner's "Ask the coach." There is a third chat screen that no parent can reach, left over from before the app had tabs and openable only from a design-time preview, still carrying its own settings and its own mode picker (`ChatView.swift`).

**`SetupTailView`.** Straight after signing up, the parent is handed a second "one last thing" form: household details, then for every child their age, grade, school style and four open boxes to write in. It puts itself in front of them from Home rather than waiting to be tapped, and that self-presenting is the behaviour this report recommends stopping.

**`OnboardingView.swift`.** The sign-up walk. A parent now goes through thirteen steps, and watches the coach pull real details out of what they gave it, before any account exists: the account wall arrives at step ten. This replaced the longer wizard that the complexity findings in section 10 measured, which is why section 10 reads in the past tense.

**`DictationController`.** A parent can press and hold and just say the thing, and it lands as text without leaving the phone. That works while they are signing up, and nowhere else: not in the Coach's message box, not in the Planner, not on any profile field. Behind it sit 140 lines of iOS code using Apple's on-device speech recognition, which is the right architecture for capture.

**`HeismanCameraCapture`.** While signing up, a parent can hold their phone over a flyer, photograph it inside the app, and the picture goes straight into extraction. That camera lives on that one screen and nowhere else. Everywhere else in the app they have to go and find the picture in their photo library first. About thirty lines of code.

**The Heisman sprint.** An internal codename, meaning nothing outside this project. The August 2026 design sprint, run from a designer's spec, that cut the sign-up walk down to the shorter one described above. What came out of it is what a parent now meets on the way in: the new sign-up screens, the second setup form, press-and-hold dictation and the in-app camera (`SetupTailView`, `DictationController`). It shipped after most of this research was collected, which is why several product measurements here describe a funnel that no longer exists.

**The expiring share link.** The other parent, or the grandparent, or the sitter, opens a link and sees the family's plan, limited to the part they are meant to see, and the link stops working after thirty days. They install nothing and create no account. It is currently filed under export, and this report argues it is the second-parent mechanism the product has been looking for.

**Gmail sync, and ingest.** Two ways information already gets in. Gmail sync looks through a connected Google account once a day for mail from providers the family has already registered with, so it confirms what the parent has told it rather than finding anything new. Ingest is the paste-or-photograph path: the parent hands over text or an image, a model reads it into a structured activity, and a fixed step writes it onto the board along with its calendar entries and to-dos.

### Terms from this research program

**Tier A / B / C / D.** The source-quality scale every number in this report carries. A is government statistics or peer-reviewed journals. B is a research organisation that publishes its method, such as Pew or Harris. C is an industry or vendor report that discloses its method, which usually means the vendor has an interest in the answer. D is a stat-aggregator blog or listicle. Tier D is never citable here, and a number found only at Tier D is treated as a lead to trace, not a fact.

**Primary (own measurement).** A label for numbers this study produced itself rather than found, such as the counts of a competitor's live inventory or of review text. It sits outside A to D because no outside publisher stands behind it.

**Analyst judgement.** A label for a call made by the analyst rather than measured, such as the weights in the email scorecard. Wherever it appears, it is a marker that the number cannot be checked against a source and should be argued with rather than cited.

**The kill list.** Appendix D. Every statistic the study encountered and then refused to use, with the reason, the verifier who traced it and a confidence mark. Publishing it is what stops a killed number quietly returning in a deck.

**Statistic laundering.** How a number that means one thing comes to be repeated as something else. Four moves account for nearly all of it: a forecast restated as a measurement, a device count restated as a people count, a global number relabelled US, and a real number's fielding date stripped so it can be reprinted on a "2026 statistics" page. A fifth and worse move, fabricated attribution, bolts a real institution's name onto a number it never published.

**Confirmed negative.** A finding that no data exists at any tier, reached by searching hard rather than by not looking. It is treated here as a real result, because it tells you the claim is unavailable to competitors too and that the only way to get the number is to measure it yourself.

**P / M / V / S labels.** The filenames in `raw/`. P is a collection agent, M a corpus-mining agent, V a verification agent, S a synthesis or red-team agent. They are a filing system, explained in the Method section.

**The quadrant model, Q1 to Q4.** The study's map of planning jobs on two axes: N, the number of steps one episode of the job takes, and how many times a year it happens. Q1 campaigns are deep and rare, such as booking a summer of camp. Q2 treadmill jobs are shallow and frequent, such as this week's practice. Q3 recurrences are shallow and rare but deadline-hard, such as a well-child visit. Q4, deep and frequent, is empty. The cut points, N of 4 or more for deep and 8 or more times a year for frequent, were chosen by the analyst and are attacked in section 4 on exactly that ground.

**N, the step count.** How many discrete actions one episode of a job takes, assigned by the analyst rather than observed. It is the axis that produces the shallow-to-deep ratio, and section 4's central attack is that the convention was written by the person who held the thesis.

### External rules, laws and data sources

**OAuth.** The standard by which a user grants one app access to their account at another service without handing over a password. Here it means the flow in which a parent grants this app read access to their Gmail.

**Restricted scopes.** Google's classification for the most sensitive Gmail permissions, including reading message bodies. Using one puts the app under Google's verification and security-audit regime rather than a self-service approval.

**CASA.** Cloud Application Security Assessment, the annual third-party security audit Google requires of any app using a restricted Gmail scope. The developer does not choose the tier; self-starting forces the most demanding one, which grants an outside auditor read-only access to production. It recurs every year for as long as the scope is used.

**Google's Limited Use policy.** The contractual restriction on what an app may do with data obtained through a restricted Google scope. It bars using it to train general models, to serve advertising, or to transfer it except in narrow cases, and compliance is a legal question, not an engineering one.

**Options A, B, B-prime and C.** The four architectures considered for getting school and provider email into the product. A is Gmail OAuth, already built. B is registering the product's own address directly with each school and provider. B-prime, written B' in the tables, is a parent-side auto-forward rule pointing at a per-family inbound address the product owns. C is A and B-prime together.

**COPPA.** The US Children's Online Privacy Protection Act, which regulates collecting personal information from children under 13 and requires verifiable parental consent. It is why a kid-facing conversational feature carries regulatory exposure independent of whether anyone wants it.

**FERPA.** The US Family Educational Rights and Privacy Act, which governs student education records held by schools receiving federal funds. It matters here because a third party receiving a school's messages about a named child may attach to the school's obligations under it.

**SOPPA.** Illinois' Student Online Personal Protection Act, a state-level student-data law that is stricter than FERPA and requires written agreements between schools and the online services that handle student data. It is named as an example of state law adding to the federal floor. It does not appear elsewhere in this report.

**ATUS.** The American Time Use Survey, run by the Bureau of Labor Statistics. Respondents reconstruct a single day in a diary interview, which is where the minutes-per-day figures for household management come from. Tier A.

**NHES:PFI.** The Parent and Family Involvement survey within the National Household Education Surveys programme, run by the National Center for Education Statistics. It is the source of the six parent-attended school occasions per child per year, the best-sourced frequency number in this report. Tier A.

**NAMCS.** The National Ambulatory Medical Care Survey, run by the National Center for Health Statistics. It samples visits to office-based physicians, which is where the per-child doctor-visit rates come from. Tier A.

**NSCH.** The National Survey of Children's Health, sponsored by the federal Maternal and Child Health Bureau. A parent-reported survey covering health, activities and family context, and the source of the organized-activity participation rate. Tier A.

**CPS ASEC.** The Annual Social and Economic Supplement to the Census Bureau's Current Population Survey, fielded each March. It is the source of the household counts, family composition and family income figures. Tier A.

**NHIS.** The National Health Interview Survey, the main federal household survey of health, and the source of the dental-visit rate. Tier A.

### Metrics

**n.** The number of respondents a survey figure rests on. A percentage without an n and a fielding date is not a finding here, and several figures in the corpus are correct on the full sample and wrong on the subgroup they are quoted against.

**Margin of error.** The sampling uncertainty around a survey percentage, written here as plus or minus a number of points. It is the reason two numbers a few points apart may not differ at all, which is why one youth-sports comparison in Appendix D is stated as "at least as often as" rather than "more than."

**D1 / D7 / D30 retention.** The share of users still active one, seven and thirty days after install. They are the standard early read on whether a product held onto anyone, and no published benchmark exists for this category, which is noted as a gap rather than filled with a guess.

**LTV and CAC.** Lifetime value, the total revenue expected from a customer, and customer acquisition cost, the marketing and sales spend to get one. Their ratio decides whether paid acquisition can work at a given price. Neither is computed in this report; the price anchors in section 3.5 are inputs to that arithmetic, not the arithmetic.

**Willingness to pay.** What a buyer will actually part with for a job, as distinct from how often the job occurs. The two come apart sharply here: the frequent jobs have no measured willingness to pay anywhere in the corpus, and no US study measures it for AI household help at any tier.

**Coefficient of variation.** In the seasonality work, a month-to-month variation measure: the standard deviation of the twelve monthly values divided by their mean. A low value means demand is flat across the year, a high value means it spikes. It says nothing about how large the demand is, which is why every flatness ranking in this report is published beside a volume figure.

---

# PART I - DECISION

**Part I is the decision content and stands alone: read it and stop.** Parts II and III are the evidence and reference layers, and they exist to be checked against rather than read straight through, so every claim below names the section, appendix or `raw/` file that carries its evidence.

## 1. Executive summary

**Demand.** A two-kid family faces roughly **23 scheduled, dated, low-step obligations a year** (band 20 to 26, sourced-only floor ~15, ~9 if two siblings share a school) against roughly **16 multi-step campaigns**. That is parity, not an order of magnitude. The product can build the second kind and gives a parent nowhere at all to put the first: there is no way to write anything down by hand anywhere in the app, and a reminder that belongs to no activity is dropped before the board is drawn (`build_board`*'s `if aid:`*, on a null `activity_id`*). What survives strategically is **cadence**, not volume, since sixteen touches a year cannot accumulate state. (Evidence: section 7.)

**Modality.** Ranked by evidence: camera, tap-confirm, email-forward, dictation, conversational voice last. Conversational voice has zero support in either corpus (zero instances of conversational voice planning in ~2,300 Reddit comments; no reviewer in 4,073 App Store reviews names voice as a reason they chose, kept or left a product). Dictation is the right architecture, built, and wired to onboarding only. The counter, which section 9 gives real space: general assistants already are reminder-setters and parents use them that way warmly, so capture is the on-ramp to durable state rather than the product. (Evidence: sections 9 and 12, Appendix A, `raw/S3-modality-prescription.md`.)

**Complexity.** The sign-up walk this research measured is not what a parent meets today, and the old one was deleted rather than parked behind a switch, so there is nothing to go back to (`OnboardingView.swift`* fell from 2,001 to 1,044 lines of code; commit `b850a3e`). Read section 10 in the past tense. Two findings survive: a parent waits 1 to 2 minutes on the Planner*, which is 6 to 12x Nielsen's verified 10-second limit, and the second setup form still puts itself in front of them, because the sprint rewrote it without removing what triggers it. (Evidence: section 10.)

**Email.** Ship B'* (a parent-side auto-forward rule into a per-family inbound address). Reject B (registering our address with schools). Keep Gmail OAuth* off the critical path: the unverified restricted-scope* cap is 100 users over the Google Cloud project's **lifetime**, non-resettable, and exhausting it disables Google sign-in. The scorecard publishes at **63.5/77.5 for B'**, not 69.5; the unlock that justified the higher score was falsified. (Evidence: section 13 and Appendix B, which sets out five defects any one of which can change the call.)

**ACT now.** Cut the kid voice companion. Stop doing trips (`trip`*). Stop letting parents bookmark into a screen nothing opens, and delete the chat screen no parent can reach (`SavedView`*, the orphaned third `ChatView`*). Show the reminders the board silently drops (`if aid:`). Let a parent speak instead of type wherever the app asks them for something, the 18 profile fields included. Stop the second setup form presenting itself (`SetupTailView`*). Open the school-event door (`school_event`*). Add nobody to the Gmail allowlist. Reject Option B. Reframe the existing expiring share link* as the second-parent mechanism.

**TEST FIRST.** The capture thesis, the forwarding address, the watchlist*, opening the after-school door (`extracurricular`*), the AAP schedule, the sports physical, the atom inversion (letting a short dated obligation stand on its own instead of making every reminder hang off a multi-step activity), and "make it hip to younger parents."

**DROP.** (Evidence: section 4, and `raw/S4-redteam.md` for each verdict.) The 18:1 shallow-to-deep headline, meaning the claim that short dated obligations outnumber multi-step campaigns eighteen to one. "Q4* is empty, that is the finding." The three-generation frame as product segmentation. Anything resting on "digital assistants did not surface at all." The legacy complexity readings as present tense. "The Camperoni correction strengthens the point." The metro supply gradient as structural, meaning the idea that big metros reliably carry more bookable activity supply than small ones.

---

## 2. What could resonate most

Ranked by **strength of evidence that users want the thing**, not by value or effort. An input to prioritization, not a roadmap.

| Move | Evidence users want it | Strength | Competes with | Falsified if |
|---|---|---|---|---|
| **Camera capture of paper** | The parents' verb is exclusive and unprompted: "I take a picture of it," never "I scan it," never "I type it in." Counted: Jam 7.95% capture mentions vs 0% voice in the same app. Unprompted 5-star: "create events from your camera or from pictures... is genius." Six of eleven live competitors accept a photo. The app teaches this gesture in onboarding (`HeismanCameraCapture`*) and then removes it | **Strongest in the program.** Two independent corpora plus a Tier A* adjacent mechanism (photographing to save measurably impairs recall, 7 experiments, Memory and Cognition 2026) | Apple Notes, the camera roll, Google Photos shared albums, all free | Ingest-created objects are edited or deleted more often than confirmed, which would mean extraction quality and not placement is the binding constraint |
| **Registration-window alerting** | Camperoni sells exactly this job at **$295/yr performed by humans** in 5 metros and has not automated it after years. Premium municipal and YMCA camp registration is a timed race. Unlike discovery, value scales with **scarcity** rather than density, so a Wichita parent with 8 candidate programs has the same problem as an SF parent with 40 and is worse served | **Strong on competitive evidence, weak on measurement.** The whitespace is verified absence, not verified demand | Provider mailing lists, which already carry the date to the parents who care | Fewer than ~30% of armed windows convert to a registration the parent attributes to the alert |
| **A low-N obligation object** (manual add, dated, one gesture) | 6.0 parent-attended school occasions per child per year (NCES NHES:PFI* 2023, n=19,562, **Tier A**, the best-sourced number in the corpus), ~23 scheduled obligations/yr for a two-kid family, and **no surface at all** for them. Causal support: five extra clicks significantly reduced whether people offloaded an intention at all (n=52x2, dz 0.71-1.29, Tier A) | **Strong on frequency, unmeasured on demand.** Nobody has measured whether families sustain a capture habit in any app | Apple Reminders, Notes, Siri, a text to yourself | Week-4 shallow captures do not exceed tracked activities by ~4x |
| **Email capture (inbound address)** | Eight of eleven live competitors accept email forwarding as a primary intake. Where the address is the front door, 8 of 88 Jam reviewers (9.1%) name it unprompted as their favourite thing, all 5-star | **Strong on reasoning, thin on precedent.** No large incumbent has won with it, and 0 of 3,917 mainstream reviewers mention it when it is buried in settings | Manual forwarding, which parents already do ad hoc | Fewer than ~15% of families complete a forwarding rule on a phone |
| **Dictation** | 161.20 vs 53.46 WPM with 20.4% fewer errors for transcription (Ruan et al. 2016, n=32, Tier A) | **Strong lab evidence, near-zero stated demand.** Requests for speech-to-event total four quotes in 4,073 reviews | The iOS keyboard mic, already on all 58 fields | Mic-tap rate stays under ~10% of field engagements after four weeks |
| **Conversational voice** | None | **None.** Zero instances in ~2,300 comments | Siri, Alexa, Gemini, all free and better at it | Already effectively falsified. Keep the code, fund nothing |

[CHART: resonance_ranking.csv - candidate moves ranked by strength of evidence that users want them, with the free substitute each competes against.]

Where the evidence is strong and the competition is free. Camera and manual capture both compete with pre-installed software that is nearer than any app, and the offloading experiment that anchors the capture case says the winner is whatever costs fewest gestures, which is the OS. The version that survives is narrower: capture is the on-ramp to durable structured state that something acts on without being asked. Apple Reminders does not arm a registration watch, detect a coverage gap or hold state across two adults. A capture surface justified on its own is competing with Siri and will lose.

Where the product already does the thing and the parent cannot get to it. This is the cheapest class of move and should be read as its own category: everything named below is already built and paid for, and what it needs is a route to the parent rather than an engineering programme. A parent can be told the day before registration opens, and to get there they first have to work through a discovery tab with twelve knobs on it (`mvp-backend/app/watchlist/`, 411 lines, durable-first with catch-up semantics). A parent still cannot write down a dentist appointment, even though the database will hold a reminder that belongs to no activity and the agent can already create one, because the board throws exactly those rows away before it draws (`todo_items.activity_id` is nullable, `duckdb_storage.py:929`; the bare `if aid:` at `app/cos/lifecycle.py:302-315`). One line decides that, which is the whole cost of showing it. A parent can photograph a flyer inside the app while signing up and nowhere afterwards, where the app sends them to their photo library instead (`mvp/MVP/OnboardingHeismanExtract.swift:482` against `IngestView.swift:146`). A parent can speak instead of type on 3 of the app's 61 text fields, all of them during sign-up (`DictationController.swift`*, 140 lines). Two doors parents have demand for are built and shut (flags defaulting off*). And the other adult can already be handed a link that needs no install and no account, which is filed under export (`POST /cos/plan/share`).

The picture below is the whole capture argument in one frame: the ways a parent actually receives an obligation, against the ways this app can accept one.

[DIAGRAM: capture-gap - the two ways information reaches a parent, and which ones the app can receive]

What resonance evidence does not exist. No US study measures willingness to pay* for AI household help at any tier. No probability sample counts parent app sprawl; the only parent-level figure in existence is n=125, vendor-sponsored and North American. No vendor publishes an inbound-address activation rate. And nobody has measured what share of US households sustain a shared digital family calendar over time, which is the denominator under the entire capture thesis.

---

## 3. Inputs to go-to-market

Evidence for audience, timing, channel, language and price anchors. Not a plan.

### 3.1 Which population first

Three independent signals converge on the same household, and none of them is a parent generation.

| Signal | Figure | Source |
|---|---|---|
| Size | Millennial parents are 61.0% of parent households (20.32M) | Census Table F1 2023 on 2026 bands, Tier A |
| Load | Planning load peaks among **employed** parents of school-age children: 8.4 vs 4.8 min/day, 1.75x | BLS ATUS* 2025 Table 8B, Tier A |
| Structure | 66.3% of married-couple families with children have both parents employed | BLS Employment Characteristics of Families 2025, Tier A |
| Ability to pay | 52.7% of families with a child under 18 had $100K+ income in 2024, about 19.4M families; median $105,400 | Census FINC-03, CPS ASEC* March 2025, Tier A |

The first audience is defined by **child age 6-12 plus employment**, not by parent generation. Gen Z parents are ~3.63M / 10.9% and 56.4% of that band's households contain a child under 3, so the camp and activity job has not started for them: retention through aging-in, not acquisition.

One counter-signal to price in. The two-household segment has proven willingness to pay (OurFamilyWizard at $110-299.88 per parent per year, court-distributed) and it is **shrinking**: children living with one parent fell from roughly 20.5M in 2013 to 18.6M in 2025 (Census CH-1 series, Tier A). Note also that income per family member is lower in families with children ($35,960) than without ($58,360), so the willingness-to-pay case rests on time saved rather than discretionary income.

### 3.2 When to spend

The most actionable finding in the report. Next-summer camp search roughly **doubles in November, doubles again in December and triples into January**, reproduced exactly across two independent cycles (Aug 2.2, Sep 3.6, Oct 5.2, Nov 10.0, Dec 22.8, Jan 68.0 on the 2025 cycle; 2.0 / 2.8 / 4.2 / 9.4 / 18.2 / 57.0 on the 2026 cycle). Google Trends, geo=US, 261 weekly points per term, Tier C*, reproduced by V3.

Acquisition spend therefore has a hard seasonal shape. The dead window is August to October, and **it is currently August**, so a camp-led acquisition message is at its weakest point of the entire year right now, while the two doors that would cover the trough are built and shut to parents. Demand roughly doubles in November, doubles again in December and triples in January: that is when the spend belongs. The trough is covered almost exactly by jobs the product can already run, which are school admin, fall registration, medical and dental, and birthday parties. See the `camp_forward_search.csv` chart in section 8.

### 3.3 Where to reach them

Pew Social Media Fact Sheet 2025, n=5,022 US adults, address-based sample, fielded 2025-02-05 to 06-18, Tier B*. Age bands are adults, not parents, so every cohort mapping is a substitution and every Millennial-versus-Gen-X gap is a floor rather than a point estimate.

| Platform | 18-29 | 30-49 | 50-64 |
|---|---|---|---|
| YouTube | 95% | 92% | 85% |
| Facebook | 68% | 80% | 74% |
| Instagram | 80% | 62% | 40% |
| TikTok | 63% | 44% | 30% |
| Reddit | 48% | 35% | 16% |

[CHART: channel_by_cohort.csv - platform reach by age band, Gen Z / Millennial / Gen X proxies. Read YouTube's near-parity and Facebook's inversion.]

Two non-obvious facts. YouTube is the only near-parity channel, so it is the single place one asset reaches all three cohorts. Facebook **inverts**: it peaks at 30-49 (80%) and is lowest among the youngest parents (68%), so a Facebook-group strategy is the Gen X and older-Millennial play and under-reaches Gen Z parents. Reddit skews heavily young (48/35/16), and the M5 corpus itself came back skewed to r/adhdwomen and r/ADHD, which is a sampling defect for the research and a real observation for positioning: executive-function self-identification appears unprompted about 38 times across M1's 4,073 reviews, and no competitor names that segment in its positioning.

Where each generation gets parenting information, and where each discovers apps, is a confirmed hole. Pew's flagship parenting study (n=3,757, fielded 2022) publishes zero parent-age crosstabs, verified at the publisher. Nothing at any tier covers visual style, tone or dark-mode expectation by generation.

### 3.4 What language to use, and what repels

The parents' own words, attributed. On the mental load: "those are all different things because they're different tabs you have to keep open in your brain" (u/phoebe-buffey, r/workingmoms, ~Aug 2026). On the registration race: "Our town summer camp registration opened at 8am and was sold out by 8:09am" (u/RImom123, r/Parenting, ~May 2026) and "you don't have to panic register right when it opens" (u/chuffalupagus, r/workingmoms, ~Mar 2026), where M5's gloss is the sharpest line in the corpus: **"panic register" is "a verb they have coined. This is the emotional peak of the whole category."** Also recurring: "another thing to maintain" (the most repeated phrase, more than a dozen unrelated threads), "if it's not on the calendar, it's not happening," "I text myself," "I take a picture of it," and "the flyer in the backpack."

The three stated reasons apps fail are the objections any message has to survive. It becomes another thing to maintain. "no one else got onboard with it" and "I was the only one using it." And "most apps want you to build out a whole system before you get any value out of them."

The repulsion finding matters as much as the attraction one, because the same capability draws opposite reactions depending on framing.

> "the Dec 2025 update now has an AI scheduler feature that takes up the top quarter of the screen. I don't want it trolling through my emails offering nonsense appointments. I will NEVER pay for this feature." (Cozi, 1 star, 2025-12-12)

> "I love the fact that I can just forward emails with event details to Jam, and it puts them in my calendar for me!" (Jam, 5 stars, 2024-03-20)

Same job, same category, opposite valence. Inbox access reads as surveillance; forwarding reads as delegation. Two reviewers said flatly "No one wants AI" (TimeTree, 1 star, 2026-07-31). Leading with "AI" is a liability with part of this audience, and 84% of parents are concerned about AI misusing young people's data with 81% concerned about collection without their knowledge (Common Sense Media / Lake Research Partners and Echelon Insights, base n=843 parents, fielded 2025-11-17 to 11-26, Tier B). The boundary the corpus draws is narrow and useful: parents object to AI producing artifacts they then have to read, and do not object to AI doing the reading for them.

One frame does not convert fathers. Fairness does not land, because fathers are markedly more satisfied with the identical split (55% vs 36% on parenting, 49% vs 26% on chores; Pew, n=2,242, fielded 2026-03, Tier B). The frame with evidence behind it is **coverage**: **70%** of parents call schedule flexibility a major factor in who covers a childcare emergency, and only **16%** say it goes to "who does a better job caring for their children" (Pew Research Center, n=2,242 US working parents, fielded 2026-03, ATP, Tier B). That is a scheduling problem, not a gender problem, and it is gender-neutral copy. Fairness is an argument; coverage is a job.

### 3.5 Price anchors that exist in the market

Observed anchors, not a pricing recommendation.

| Anchor | Figure | Caveat |
|---|---|---|
| The registration-watch job done by humans | Camperoni Concierge **$295/yr** (1 week free), staffed by local camp-planning experts, 5 active metros | Verbatim from Camperoni's own CMS post, confirmed by V5. It is a services business in 5 metros, which is also an argument that the job may not support software economics |
| The same vendor's software tier | Pay-what-you-can at **$60 / $100 / $200 per year**, framed explicitly as hours saved times $20/hr | Vendor framing, useful as a stated hourly value anchor |
| Incumbent subscriptions | **$39 to $99/yr** (Cozi Gold $39, Skylight Plus $79, Ohai $99, Nori ~$60/yr) | M2's read is that at this ARPU you cannot fund the model quality the reliability failure mode demands |
| Court-distributed co-parenting | OurFamilyWizard **$110-299.88 per parent per year** | The one segment with proven willingness to pay, and shrinking |
| What parents already spend on the job | **$1,490.66 per participating child** on sports; **18% of youth-sports parents took on debt** | Aspen/Utah State 2024 n=1,848 Tier B; Harris Poll for Good Sports n=741 parents, fielded 2024-10-16 to 10-18, weighted, +/-4.2pp, exact question wording published. The 18% is the best-sourced figure in its domain; LendingTree's competing 79% is the unusable one |

**No US study measures willingness to pay for AI household or family assistance at any tier.** Every price hypothesis currently in the repo is untested.

### 3.6 Claims that must not appear in marketing copy

Full detail and confidence marks are in the appendix.

The repo's own cleared-for-marketing list in `gtm-strategy.md` carries the Bright Horizons summer sleep-loss figures under the wrong year: they are **2026, not 2025** (Harris Poll for Bright Horizons, fielded 2026-04-14 to 04-16, n=2,030 US adults), and **the 90% rests on n=479 employed parents while the 85% rests on n=616 parents of under-18s**, so neither may be presented on the full 2,030 sample. Modern Family Index is multi-wave; always name the wave.

Pew's **"37 million Millennial parents" is fabricated** and appears in this repo's own `gtm-research.md`. Pew published 17M and 19M Millennial *mothers*; 37M looks like 19M doubled. Attributing a fabricated number to the most-trusted publisher in the space is the highest reputational risk in the corpus.

ActivityHero's "4 million families" and "400k subscribers" are rate-card marketing with no counting-unit definition, so cite only as "ActivityHero says." TeamSnap's 30M is a mixed-role lifetime platform total against 2M daily actives, a 15x gap, and is never households. Skylight's "$60,000 mental load" is derived (hours times a $35.86 wage), never an earnings finding. "70% of kids quit sports by 13" is unsourceable and the real measured value is 35%. And do not repeat "71% of consumers prefer voice over typing": the figure does not appear in the PwC report the corpus cited, and Pew's real comparator is 22%.

---

## 4. The case against this report

Published unsoftened, from S4.

**The central claim is arithmetically right and substantively hollow.** One row is the finding: weekly sports logistics is 200 of the corrected 264, and the ratio moves by a factor of eleven on it. Those 200 are attendances, not capture events. The sensitivity that could have changed the answer was never run; the one that was run (dropping permission slips and birthday parties, 280 to 250) could not have.

**Count is not value, and the report says so and proceeds anyway.** Money is in the campaigns, there is no willingness-to-pay evidence for capture anywhere in the corpus, and the paywall stays at funnel step 11 while the product's centre of gravity moves to the jobs with no measured WTP.

**The corpus contains the refutation of the capture thesis and files it as support.** The 2017 "digital assistants did not surface at all" citation does load-bearing work that the program's own 2026 evidence falsifies. The report searched for assistants as a **planning** tool, correctly found absence, and recommended building a **capture** tool, which is the one thing the same search shows is saturated.

**The empty Q4 is a definitional artifact.** Any deep-and-frequent job can be moved out by decomposing it into episodes and any shallow-frequent job moved in by aggregating. The axes are analyst-chosen with no justification for either cut point.

**The watchlist is the best idea in the report resting on the weakest measurement.** Verified absence is not verified whitespace: a category where every consumer app failed to get traction is at least as likely to be a bad market as an empty one, and Care.com's Activities and Camps app has 21 lifetime ratings. Camperoni at $295/yr with humans in 5 metros, still not automated after years, is the shape of a small human-scale services business rather than a moat. The V5 correction moved Camperoni from ~1/18th to **~1/2** of ActivityHero's live inventory, and S2 converted that into support ("strengthens the underlying point"), which is the clearest instance of momentum bias in the corpus. The honest restatement: inside the metros that matter, the named competitor is dense, human-operated, and produces better registration-date data than a scraper will. The thin-market premise rests on one August day whose own metro gradient is internally inconsistent. The moat depends on the app knowing the date registration opens, which nothing but the discovery search can supply, and the municipal rec catalogs holding those dates are JavaScript-rendered pages the probes could not read. And the competitive claim that a general assistant cannot watch a page and push you is sourced **solely to usecarly.com**, killed as Tier D* and a competitor's SEO site. A 20-minute in-product check settles it and has not been run.

**Self-serving research design, six places.** The finding was in the brief, which lists under Absent "any general add an appointment / remind me capture surface," and the top recommendation is a general add surface, read by twelve collectors before they collected. Willingness to pay was declared out of scope. The step-count convention that produces the 200 row was authored by the party with the thesis and no collector supplied it. The quadrant* cut points are unjustified. The winning email option was invented, weighted and scored by the same analyst mid-draft and won by 2 points on a subjective 5-point scale with no adversarial scorer. And "no data found" was pre-cleared as the expected answer for the one cohort the founder wants to reach.

**Recommendations the research never actually tested.** These may be right; they carry no evidential weight and must not be presented as research conclusions: cutting the kid companion (regulatory, true with or without demand data, and a closed-beta feature's demand is unfalsifiable); cutting trips, a door already shut to parents; clearing out the screens no parent can reach and showing the reminders the board drops, which are bugs (`if aid:`); letting parents speak instead of type, justified on cost and recommended at any evidence level; opening two doors during the window when the doors that are open have nothing to offer; stopping the second setup form presenting itself; and rejecting Option B, decided by structural facts. Almost every cut and every trivially cheap double-down was pre-decided. The four the research actually drove are capture, the forwarding address, the watchlist promotion and inverting the atom, and those are the four the red team attacked hardest.

**Product measurements are stale everywhere except S2**, and one stale number was still setting the highest weight in the email scorecard: the banned "SEVERE OUTLIER on five separate measures," describing a funnel that no longer exists.

**What the red team could not break:** the Gmail 100-user lifetime cap and the 7-day test-user expiry; the audit showing the built email sync cannot discover anything new; the ActivityHero measurement itself; M4's counted co-parenting analysis; the kid-companion regulatory exposure; and the verification program's decision to publish its own residual error rate.

---

## 5. What to do next

**ACT.** The evidence or logic is independent of the contested claims.

1. Cut or dark-flag the kid voice companion this week.
2. Stop doing trips. Stop letting parents bookmark into a screen nothing opens, and delete the chat screen no parent can reach (`SavedView`, the orphaned third `ChatView`). Show a reminder that belongs to no activity, which is the one line `if aid:` in `lifecycle.py`.
3. Let a parent speak instead of type wherever the app asks them for something, the 18 profile fields included. Zero marginal cost.
4. Stop the second setup form putting itself in front of a parent at Home. Let them tap it when they want it (`SetupTailView`).
5. Open the school-event door (`school_event`). Its frequency evidence is the best-sourced number in the corpus, and it is the only door that builds a real chain of tasks for its kind of job and the only one whose date handling renders a one-off correctly.
6. Add nobody to the Gmail OAuth allowlist. Do not launch on that Google Cloud project.
7. Reject Option B.
8. Reframe the existing expiring share link as how a parent brings in the other adult: they open a link, install nothing and create no account. That displaces 792 lines of Circle* conversation code competing with iMessage.

**TEST FIRST.** Pre-register every threshold.

| # | Question | Test | Threshold |
|---|---|---|---|
| 9 | Is capture the product? | One manual-add field and one to-do row, no board, no discovery, no lifecycle. Run in September or October. Project the denominator **excluding weekly sports logistics**. Report **week-4** captures per active user | Confirms if shallow captures exceed tracked activities by ~4x, not the 10x the inflated ratio implied. Below that, the board is the centre of the product |
| 10 | Will parents complete a forwarding rule? | Five parents, an address, watch. **Before** the two-week build | Share completing a Gmail forwarding rule on a phone, plus reaction to Google's week-long security banner. Strike the pre-commitment that a poor result means design rather than architecture |
| 11 | Is the watchlist whitespace or a bad market? | (a) 20-minute in-product test of whether ChatGPT or Gemini scheduled tasks can watch a page and push. (b) Re-run the ActivityHero metro counts in **February**. (c) ParentSquare first-party content test, $0, one day | (a) settles a killed source. (b) settles the August trough. (c) bears on B's coverage more than on Option B |
| 12 | Does `extracurricular` earn its door? | Flag ON, instrument `door_opened` against camp's rate during Aug-Oct | Below camp's rate over four weeks, the volume argument is wrong |
| 13 | Are the AAP schedule and the sports physical real jobs? | Ten families each before either goes on a roadmap | The sports physical has no citable US frequency at any tier |
| 14 | Should the atom be inverted? | Do not migrate until #9 returns | Simply showing the reminders the board already drops buys the same visibility at 1% of the risk (the one line `if aid:`) |
| 15 | Hip to younger parents? | Five parents aged 25-29, two visual directions | This report gives it no support and one datum against |

Instrumentation, for whoever builds the tests above: emit `capture_started` / `capture_committed` / `capture_abandoned` with `modality` (camera / dictation / typing / paste / forward), `surface`, `local_hour` and `edited_before_commit`; `extraction_confirmed` with `items_returned`, `items_kept` and `fields_corrected[]`; `voice_call_started` with `entry_point` and `abandoned_within_15s`. Cut by modality x surface x local hour x week-since-install x child-age band. Never measure "voice usage" as one number: merging dictation, the Coach* call and assistant commands reproduces the bucket error that makes all published research useless here.

---

# PART II - EVIDENCE

Each section is its conclusion, the numbers that carry it, and its charts. Bulk that is reference rather than argument has moved to Part III with a pointer.

## 6. Who plans

33.29M US family households with own children under 18 (Census Table F1 2023, CPS ASEC March 2023, ~60,000 addresses, Tier A). On 2026 age bands: Gen Z (18-29) **3.63M / 10.9%**, Millennial (30-45) **20.32M / 61.0%**, Gen X (46-61) **8.41M / 25.3%**. The circulating 2.0M / 6.0% for Gen Z is a 2023 householder-age snapshot read against 2026 bands, wrong by ~80%; 84.1% of 25-29-headed parent households contain a child under 6, so the child-age argument is unaffected. All of it is 2023 vintage and the child-age distributions were not independently recomputed.

[CHART: cohort_population.csv - US parent households by cohort on 2026 age bands, with the superseded 2023 snapshot for contrast.]

Household management, minutes/day (BLS ATUS 2025 annual averages, Tables 8A/8B/8C, released 2026-06-25 USDL-26-1022, ~6,100 diaries, Tier A; collection suspended 2025-10-01 to 2025-11-12 and Q4 reweighted, effect not quantifiable per BLS). Lead with employed parents; the buyer is one.

| Population | Mothers | Fathers | Ratio |
|---|---|---|---|
| **Employed, youngest 6-17** | **8.4** | **4.8** | **1.75x** |
| Employed, child under 18 | 7.2 | 5.4 | 1.33x |
| All parents (separate series) | 12.0 | 6.0 | 2.00x |
| All parents, youngest 6-17 | 16.2 | 5.4 | 3.00x |
| All parents, youngest under 6 | 5.4 | 6.6 | 0.82x |

The 2x/3x headline is levered by non-employed mothers (3.09x); under age 6 the sign flips and fathers do more, so the gap is a school-age phenomenon. Do not build a widening-trend claim on three cross-sections.

[CHART: planning_labor_by_employment.csv - household-management minutes/day, employed-parent series as headline, all-parents as a separate labelled series.]

Daminger (ASR 2019, 70 interviews / 35 couples, Tier A, qualitative) splits cognitive labour into anticipating, identifying options, deciding, monitoring, and **only deciding is established as roughly equal**, so the noticing and the tracking are hers and the Planner cannot be argued into a gender-neutral middle. Gallup (n=3,062, dual-full-time-with-kids subgroup n=566, MoE* +/-5, fielded 2019, dated) has women leading **6 of 12** tasks and names family activity planning as shared, so the one job Gallup says couples share is the one the Planner is built around. The marketing anchor is the satisfaction cliff: **22%** of mothers who do more parenting are satisfied with the split against **65%** of mothers who split equally, 11% vs 54% on chores (Pew, n=2,242 US working parents, fielded 2026-03, ATP, Tier B). "88% of mothers own scheduling" is not a population number: n=393 mostly graduate-degreed mothers, convenience-recruited, fielded 2005-2010 (Ciciolla and Luthar, Sex Roles 2019).

---

## 7. What they plan

**Use ~23 scheduled obligations/yr for a two-kid family, band 20 to 26.** Never a decimal: NCES publishes the school-attendance mean as a rounded integer.

| Line | Per child | Two-kid | Source | Tier |
|---|---|---|---|---|
| Office-based physician visits | 1.53 | 3.06 | NCHS Data Brief 408, NAMCS* 2018 | A |
| School meetings/activities attended | 6 | 12 | NCES NHES:PFI 2023, n=19,562 | A |
| Dental visits | 1.35 (band 0.9-1.8) | 2.70 | NHIS* 2023 via childstats | A |
| Therapy sessions | 1.5 | 2.93 | NSCH* 2023 n=55,162 x an **unsourced** cadence | A/estimate |
| Sports physical | 0.50 (a ceiling) | 1.00 | Pediatrics 2015;135(1):26-32 + AFP 2021 | A/estimate |
| Orthodontic adjustments | 0.22 | 0.44 | NHANES III via Proffit x 9.1/yr | A/corrected |
| **Total scheduled** | 11.55 | **~23** | V2 recomputation | mixed |

Dental 1.8 is a ceiling (0.90 x exactly 2), not a midpoint; orthodontia corrected from 0.288 to 0.22; ED (0.48) and urgent care (0.40) excluded from anything labelled scheduled. Sourced-only floor **15.06**, not the 15.96 collectors published, and **9.06** if siblings share a school. Every one of those corrections moves the count down, so the number that survives is the conservative one: the case for a lightweight obligation object rests on about 23 a year, not on the larger figure the collectors first returned.

[CHART: obligations_per_year.csv - scheduled obligations for a two-kid family by line item, with both floors marked.]

**Do not publish the 18:1 shallow-to-deep headline.**

| Basis | Shallow | Deep | Ratio |
|---|---|---|---|
| As originally counted | 286.25 | 15.94 | 18.0:1 |
| **Corrected** (two unsourced rows dropped) | **264.25** | 15.94 | 16.6:1 |
| **Minus weekly sports logistics** | **64.25** | 15.94 | **4.0:1** |
| Camp as 1 cycle, not 7.5 sub-bookings | . | 9.44 | 28:1 |

Publish 264 with weekly sports logistics broken out: that row alone is **200 of the 264**, so the headline moves by a factor of eleven on one analyst-defined line, and always name the camp convention. The 200 row is not a capture job either: under the step convention in use attending is a step, so those are **attendances**, entered once per season. Permission slips and birthday parties attended are unplotted for want of any frequency source after two targeted searches. "Q4 is empty" is likewise an artifact: orthodontia (12 to 26 visits per treated child over 18 to 24 months) leaves that quadrant only because the series is recorded as booked once, and the cut points (N>=4, freq>=8) have no derivation. What follows for a reader is that the empty quadrant carries no product implication at all. It is a consequence of where the lines were drawn, so no roadmap decision should rest on it.

[CHART: job_quadrants.csv - step count* vs annual frequency, log scale. Weekly sports logistics is drawn apart because it alone is 200 of the 264 shallow steps. Permission slips and birthday parties attended are omitted: neither has a frequency source at any tier.]

What the axes are really separating is one planning object at two very different sizes, which the picture below sets side by side: a dentist appointment a parent writes down once, and a summer of camp they work at for weeks.

[DIAGRAM: workflow-spectrum - the same planning object at one step and at eight steps]

Money sits in the campaigns (camp $893-954/child, LendingTree 2025 Tier C; sports $1,490.66/participating child, Aspen/Utah State 2024 n=1,848 Tier B), and there is **no willingness-to-pay evidence for capture anywhere in this corpus**.

---

## 8. Seasonality

Flatness never appears without volume. On a shared Google Trends scale anchored to summer camp: summer camps **36.6**, school admin 30.7, birthday parties 9.3, fall registration 4.5, weekend outings 3.5, **medical/dental 1.5**, holiday 0.88, vacations 0.71, break coverage 0.45, spring registration 0.10, so summer camp's worst month beats medical/dental's best by ~4.5x. (Google Trends pulled 2026-08-21, reproduced by V3; geo=US, 261 weekly points per term, **Tier C**, no parent or age filter, so the medical, birthday and vacation rows are not parent-specific.) Only the coarse flat-versus-spiky separation survives quantisation, and two rows describe different terms than they appear to: fall registration's volume is almost all the flat browse term "after school program," and school admin at 30.7 is dominated by "back to school," a retail term. **Do not publish** the "aggregate load varies only 1.47x" figure, an artifact of row normalisation plus ordinal truncation.

[CHART: seasonality_month_x_task.csv - month x task heatmap with the shared-scale volume bar beside every row. Never render the heatmap alone.]

**The publishable finding is the forward-year experiment.** Searches for a specific future summer, tracked across the preceding twelve months, replicate across two cycles: Aug 2.2, Sep 3.6, Oct 5.2, **Nov 10.0, Dec 22.8, Jan 68.0** (2025 cycle); 2.0 / 2.8 / 4.2 / 9.4 / 18.2 / 57.0 (2026 cycle). **The dead window is August, September and October: three months, not six**, and the jobs that fill it are ones the app can already run and does not offer, because those two doors are shut, while the two doors a parent can see both want to run a web search against a market with nothing to sell. Acquisition consequences in section 3.2.

Which of the five kinds of planning job a parent can actually find a way into, and which are shut, is the picture below.

[DIAGRAM: doors-open - the five kinds of planning job, and which doors a parent can currently see]

[CHART: camp_forward_search.csv - forward-year camp search across the preceding twelve months, two cycles overlaid, Aug-Oct shaded.]

---

## 9. Voice or typing

Voice belongs at the two ends, emptying a formed thought in and hearing a reminder out. Everything between capture and reminder is screen work. The capture-gap diagram in section 2 is the frame for this whole section: it is the same picture of what reaches a parent and what the app can take. Full evidence chain in `raw/S3-modality-prescription.md`; the parent-voice verbatims are in Appendix A.

| Rank | Mechanism | Evidence | Weakness |
|---|---|---|---|
| 1 | Camera | Parents' verb is exclusive ("I take a picture of it," never "I scan it"). Where a product ships capture, praise runs 7.95% of reviews (Jam) vs 0% voice in the same app | Extraction reliability is a cliff, not a gradient |
| 2 | Tap-confirm | Users prefer the keyboard for repair and it significantly improves performance. Five extra clicks measurably suppress whether an offload happens at all (n=52x2 within-subject, dz 0.71-1.29, Tier A) | Only exists downstream of another mechanism |
| 3 | Email-forward | Eight of eleven live competitors take email as primary intake; the only mechanism reaching the second parent with no install | No large-incumbent precedent. Desktop-web setup on a phone-first product |
| 4 | Dictation | 161.20 vs 53.46 WPM, 20.4% fewer errors, for transcription (Ruan et al. 2016, n=32, Tier A) | Composition collapses to 7.8 vs 32.5 WPM. Quiet room, 2016 phone. **No parent in either corpus asks for it** |
| 5 | Conversational voice | None | Zero conversational voice planning in ~2,300 comments. Smart-speaker owners issue 12.4 requests/week, mostly music, lights, timers (Edison/NPR, n=2,334, 2022, Tier B). Amazon Devices lost >$25B 2017-21 |

Restored context-of-use data (PwC, fielded Feb 2018, n=1,000 US adults 18-64; cite as 2018 and flag as dated, PDF retired, values via Voicebot and TechCrunch): 65% cooking, 62% multitasking, 57% watching TV, 74% in the home, and **0% driving on a smart speaker vs 40% driving on a smartphone**. The device split is the whole finding: voice in the car is a phone behaviour and this is a phone app. Every one of those is a capture or listening context; none is a comparison context. Adoption peaks at 30-49 (smart speakers 41%, daily chatbot use 34%, against 33% and 31% at 18-29; Pew, n=5,119, fielded 2026-02, ATP, Tier B), and that band is **less** self-confident with chatbots than 18-29s (23% vs 31%), which argues for forgiving low-stakes voice on an editable field. 18-24s use voice daily less than 25-49s (59% vs 65%) because in public it "just looks weird"; Kowalczuk and Musial (n=860, German, intention not behaviour) find continuance intention significantly lower in public. No US behavioural measure exists.

[CHART: voice_adoption_by_cohort.csv - smart-speaker ownership, chatbot use and self-confidence by age band. Read the 30-49 peak and the confidence inversion.]

**S4's counter, the strongest attack in the program.** The claim that capture is unserved leans partly on a 2017 tool inventory (ACM IMWUT, n=280, Tier A, dated) in which digital assistants did not surface at all, and the program's own 2026 corpus says the opposite about the exact job being recommended: "Hey Siri, remind me to..." appears verbatim in at least six unrelated comments, with the quotes in Appendix A. The job has been available for fifteen years and nobody won it standalone; the offloading-tax experiment that anchors the capture case argues against our surface, since opening an app costs more clicks than raising a wrist; and Apple's personal-context Siri is in beta later in 2026. Corpus-wide, capture mentions run **0.43% against voice's 0.68%**, so "capture is mentioned far more than voice" is false as stated and holds only inside products that ship capture. What survives is narrower, because Siri Reminders does not arm a registration watch, detect a coverage gap or hold state across two adults. **Capture is the on-ramp. "Capture is the product" is not supported.**

---

## 10. Complexity tolerance

Every judgement here is an **analyst call** with an explicit evidence strength. No screens-to-completion distribution exists at any tier, so "outlier" is unavailable and "SEVERE OUTLIER" is banned from this report and any deck built on it.

**The sign-up walk measured here has been replaced, so this is past tense.** What a parent faced as measured 2026-08-20: 8+N screens, 14 things to fill in for one child and 19 for two, against an average e-commerce checkout of 11.3 (Baymard 2024, Tier C, site count and participant n not disclosed) and Baymard's ~8-field recommendation; 58 places to type across the whole app, 18 open boxes on a single profile screen, about 34 taps to get through. Evidence strength: adjacent for the field comparisons, none for the screen and tap counts; five tabs and three of five doors shut are both within norm. The old wizard was then deleted, and a parent now walks 13 steps before an account is asked for, watching the coach pull real details out of what they typed at step 4, with the account wall at step 10 (`OnboardingView.swift`, commit `b850a3e`) against day-zero data that makes it urgent (82% of trial starts on install day; 55.4% of **three-day-trial** cancellations on Day 0; RevenueCat 2025, Tier B, corrected scoping). The sprint fixed what happens inside the walk, not how long it is, and left the second setup form still presenting itself.

Two findings still live: the Planner's 1 to 2 minute wait is **6 to 12x Nielsen's verified 10-second limit**, which is the point past which a user stops holding their attention on the task they came to do (Nielsen 1993 from Miller 1968 / Card et al. 1991, Tier A, with Nah 2004's verified 38-second tolerance, n=70, fielded 2003, dated), and the field-count comparison **understates** our burden because checkout fields are largely autofillable while ours are generative. **No onboarding-completion benchmark exists at any tier**, re-confirmed twice, so the case rests on Nielsen and the field comparison, never on a completion slope.

---

## 11. The three cohorts

Keep the generational frame for channel and messaging (section 3.3, Part I). **The actionable product segmentation is child age.**

| Child age | Discovery | Board | Coverage gaps | Watchlist | Ship |
|---|---|---|---|---|---|
| 0-5 | Off | Off | Off | Off | DOB-generated AAP well-visit and immunization schedule: a published deterministic table, not a search problem, so a year of dated obligations comes from one field onboarding already collects, at zero taps |
| 6-12 | On | On, campaigns only | On, highest-pain job | On | One-gesture capture underneath the campaign layer |
| 13-17 | Background utility | Rarely populated | Partial | On | Sports physical as a first-class gating obligation, plus transport assignment |

At 0-5 organized-activity load is effectively zero (the federal instrument does not ask below age 6) while medical recurrence peaks: infants under 1 make 5.96 office visits/yr vs 1.53 at ages 1-17 (NCHS NAMCS 2018, Tier A), so build for 0-5 as retention through aging-in. At 13-17 the modal summer activity flips to a job or internship (32%), a primary sport alone spans 1.86 organizational settings, urgent-care use peaks (30.3%), single-mother share rises to 22.2% at 15-17 vs 18.2% under 6, and the average age a child quits sports is 12 (Aspen/Project Play), exactly this band's boundary. The teen may receive logistics and must never be handled by the product. "Make it hip to younger parents" is an untested hypothesis: nothing here measures design response by age, the one relevant datum runs against it, and it aims at the cohort with no campaign load.

---

## 12. Competitive position and the verbatim corpus

Provenance, stated once. M1/M2/M4 quotes are Apple US App Store review RSS pulled 2026-08-21; V5 rebuilt a ~19,000-review corpus from a different live Apple endpoint and located **141 of 142 quoted verbatims word for word**, star ratings 100% correct, date offsets all +/-1 day. Two conventions must be declared: M1 and M2 sometimes splice a review **title onto its body inside one pair of quotes**, and M2's Duckbill 5-star line was a paraphrase inside quotation marks. The four quotes below do the most work; **the rest of the corpus, organised by theme and with its sampling caveats, is in Appendix A.**

> "the iOS app is clunky and inconvenient to add events to... Ultimately these extra steps. Have been a barrier to wider use in our family." (Cozi, 2 stars, 2026-01-15)

> "The new feature that allows you to create events from your camera or from pictures you have taken already of flyers or posters etc. is genius." (TimeTree, 5 stars, 2024-07-08)

> "I love the fact that I can just forward emails with event details to Jam, and it puts them in my calendar for me!" (Jam, 5 stars, 2024-03-20)

> "Just a shared family Google Calendar. I tried skylight but hated it, plus no one else got onboard with it." (r/nycparents, ~2025)

**Counting discipline.** Some of the corpus figures in this report were counted with a published pattern over a stated denominator and can be checked by anyone; others are an analyst's impression of what a pile of reviews said. The two are not interchangeable and are labelled separately here. M1's complaint-theme **ranking is analyst judgement at the point of use**, not measurement: no regex, numerator or denominator, and its two rankings contradict each other. V5's counted figures over 5,847 sub-4-star reviews of the same seven apps are **price 14.2%, sync 6.8%**. M4 publishes regexes and denominators and all replicated, so it may be cited as counted: reviews turning on the other parent's participation are OFW 4% (28/641), AppClose 3% (14/534), 2houses 2%, TalkingParents 2%, and the dominant concrete refusal is that the ex will not **pay**, not that they will not install. M4 covers 6 apps, not 7. M1's counted claims are two: voice in 51 of 4,073 reviews (~1.3%), and no reviewer describing voice as a reason they chose, kept or left.

**The category's death pattern** is in Appendix A: four compounding killers, three products dead or sunsetting inside twelve months.

**Supply measurement.** ActivityHero's entire live national inventory is **9,008 bookable sessions of 94,848 records** (90% expired), California 4,299 live, 20 states under 50 live sessions, reproduced cell for cell by V5. ActivityHero's Terms of Use bar copying or disclosing any part of the Service including by scraping; the Algolia application ID and search key are redacted everywhere and must stay redacted, every query used `hitsPerPage=0`, meaning it asked the search index for a count and took back no listings, so nothing was copied, and queries bill to ActivityHero's account, so do not automate a re-run. Keep the vendor's name inside every headline number: this is ActivityHero's index, not US kids' activities. **The metro gradient is not structural**, being measured at the annual August trough: LA has more providers than SF (5,686 vs 4,299) but only **329 live sessions against SF's 969**, and NYC's 2,827 providers yield 112. Provider rank and live-session rank disagree across the top three metros, thin metros (3 to 8 live) move by tens of percent on churn, and this stays a dated snapshot until a February re-run.

[CHART: activity_supply_by_metro.csv - ActivityHero providers vs live sessions within 25 miles, 15 metros, single August-2026 snapshot. Show both bars; do not rank thin metros against each other.]

---

## 13. Email ingestion: OAuth vs a dedicated address

Four architectures. A = Gmail OAuth (`gmail.readonly`, built). B = register our address with each school and provider. B' = a parent-side auto-forward rule into a per-family inbound address. C = A + B'.

**Ship B'. Reject B. Keep A off the critical path, and pursue it only if a four-part gate clears** (counsel confirms Limited Use* compliance; lab quotes land at Tier 2 and roughly $1,500/yr or less; B' is already live and measured; measured B' coverage shows a gap only passive Gmail capture closes). If any of the four fails, do not pursue A at all.

| Criterion | Wt | A | B | **B'** | C |
|---|---|---|---|---|---|
| C1 Time to broad availability | 2 | 1 | 2 | 5 | 5 |
| C2 Compliance cost and burden | 2 | 1 | 1 | 5 | 3 |
| C3 Onboarding friction | 3 | 4 | 1 | **2 (re-scored)** | 4 |
| C4 Coverage | 2 | 3 | 2 | 4 | 5 |
| C5 Reliability | 1.5 | 2 | 2 | 3 | 3.5 |
| C6 Privacy, trust, legal | 1.5 | 2 | 1 | 5 | 4.5 |
| C7 Running cost | 0.5 | 4 | 4 | 5 | 5 |
| C8 Multi-adult | 1 | 1 | 2 | 5 | 5 |
| C9 Addressable users | 2 | 2 | 2 | 5 | 5 |
| **Weighted total (max 77.5)** | | **35.0** | **25.5** | **63.5** | **67.5** |

**Analyst judgement**\*, not a measurement, produced by the same analyst who invented the winning option mid-draft, set the weights and assigned the scores. No adversarial scorer ran. B' re-scored from 69.5 to 63.5 because C3, the highest-weighted criterion, rested on a claimed design unlock that V6 falsified: the source user must still return to Gmail and click Save Changes, and **Google shows a week-long banner warning that unexplained forwarding may mean someone else has access to the account**, arriving at exactly the trust moment B's thesis depends on. **The ranking holds; "B' wins on the highest-weighted criterion" no longer does.**

[CHART: email_options_scoring.csv - weighted scores by criterion for A / B / B' / C, with the corrected C3 row flagged. Label the chart Analyst judgement.]

What the four options come down to is where a school or camp email physically goes, and who has to do something for it to get there, which the picture below traces end to end.

[DIAGRAM: email-paths - where a school or camp email travels under each of the four options]

Three facts carry the decision regardless. The Gmail OAuth cap is **100 users over the project's lifetime**, non-resettable, documented twice by Google; exhausting it disables Google sign-in; and Testing is not a holding pattern because test-user authorizations expire every 7 days, taking the refresh token with them, so every connected family would have to grant access again each week. CASA* is annual forever, the developer does not choose the tier, and self-start forces Tier 3, meaning annual read-only auditor access to production over a database of families' children, so plan for $4,500/yr, not $675. Option B dies on three independent grounds, any one disqualifying: ToS blast radius landing on the parent's school district, plausible FERPA* 99.33(a) attachment, and 13 to 18 setup actions.

**The most decision-relevant fact in the audit:** a parent who connects their Gmail is shown nothing they had not already entered themselves. The sync only goes looking for mail from providers attached to activities the parent has already registered and marked as watched, over the past fourteen days, and it comes back with nothing at all when no such activity carries a contact address (`from:(...) newer_than:14d`). The flagship "your inbox fills your planner" experience is not what sits behind the CASA gate.

**Five honest defects travel with B', and any one of them can change the call. They are set out in Appendix B**, with the full memo in `raw/S1-email-decision-memo.md`.

---

## 14. Product fit

| Surface | Verdict | Why, in one line |
|---|---|---|
| Registration watchlist | DOUBLE DOWN | The expensive half of the camp job. Camperoni sells it at $295/yr performed by humans in 5 metros. Worth more in thin markets, where discovery is worth least |
| Photo/flyer ingest | DOUBLE DOWN, promote out of the Planner | The only surface with direct counted customer language praising it |
| Dictation | DOUBLE DOWN, extend | A parent can speak instead of type on 3 of the app's 61 text fields, all of them during sign-up. 140 lines of code and the correct architecture |
| The after-school and school-event doors (`extracurricular`, `school_event`) | DOUBLE DOWN, open them | 72.7% of US children 6-17 did an organized activity in the past 12 months (NSCH via HRSA/Census, n=26,488, Tier A). 6.0 parent-attended school occasions/child (NHES:PFI 2023, n=19,562, Tier A). Both dark during the Aug-Oct window |
| Two-way calendar sync | DOUBLE DOWN, turn the schedule on, add Apple/Outlook | The one subsystem already built at the right altitude |
| Home | DOUBLE DOWN | Correct centre of gravity. It needs something to show |
| Discovery engine | SIMPLIFY and re-aim | Keep it (1,185 LOC, 4.2% of backend). The most valuable thing it returns is the date registration opens, not a list of candidate programs |
| The six-stage* board | SIMPLIFY | Six places for a thing to be fits a camp and buries a dentist appointment. Keep the stages as a view over the things that really do take many steps; stop making every object live in them |
| Circle | SIMPLIFY hard | Right seam, wrong mechanism. Both ways of linking to another adult make that adult create an account first, which is precisely what the counted evidence says they refuse |
| The second setup form, the chat surfaces, the doors | SIMPLIFY | Stop the setup form presenting itself; one place to talk to the app, under one name; re-cut the doors by what triggers them and how deep they go, which is a list and a prompt edit |
| Kid voice companion | CUT | A child talking to the app, with web search wired into that conversation. The FTC's September 2025 Section 6(b) inquiry ordered seven companies including Alphabet, Meta, OpenAI, Snap, xAI and Character.AI to hand over information on chatbots acting as companions; COPPA* is amended; and the app's own consent screen says "not yet COPPA-compliant." Zero demand evidence at any tier in a corpus that looked. ~3,300 iOS LOC + ~760 backend |
| The trip door (`trip`) | CUT | Within-battery, "planning the trip" ranks 27%, 6th of 17 obstacles. 59% of travellers with children already use ChatGPT or similar for trip planning (MMGY Fall 2025, n=4,503, Tier C) |
| Conversational parent voice | CUT as a roadmap item, keep the code | Zero corpus support. Costs nothing to leave |
| Bookmarks that cannot be reopened, the chat screen nobody reaches | CUT | Saving works, reading back does not (`SavedView`, the third `ChatView`) |
| Writing a dated obligation down by hand | BUILD-NEW | A parent cannot do it anywhere in the app |
| Inbound forwarding address | BUILD-NEW | Section 10 |
| DOB-generated AAP schedule; sports physical | BUILD-NEW | Both strong-logic, zero-data. Label them that way |

---

# PART III - REFERENCE

## Appendix A: the verbatim corpus

**The death pattern.** Yohana ended US service 2025-09-30 and Japan 2026-01-30; Milo announced shutdown 2026-01-12; Maple sunsets 2026-12-31, team acquihired by a travel company. Four killers (`raw/M2-ai-assistants.md`): the mental-load paradox, where the most overloaded person pays the setup debt up front for a probabilistic later payoff; reliability is binary rather than gradual, so one wrong entry sends the parent back to manual permanently; single-player adoption in a multi-player job; and unit economics with no middle, since human-in-loop earns the warmest reviews at a 10-40x premium but forces metering, the top complaint. Milo's founder, after six years of research and three of building: the problem she could not solve is that "someone has to run point."

**Sampling caveats, which govern every quote below.** Qualitative and non-representative. Reddit blocked all API and mirror paths, so this is browser-driven comment search returning individual comments rather than threads, and it **skews heavily to r/adhdwomen and r/ADHD**. There are no BabyCenter, What to Expect or Substack sources. The "what they wish existed" theme yielded only four usable quotes. App Store corpora are separately verified: V5 located 141 of 142 quoted verbatims word for word. Do not compute percentages from the Reddit material. Full corpora: `raw/M5-verbatim-corpus.md`, `raw/M1-organizers.md`, `raw/M2-ai-assistants.md`, `raw/M4-coparenting.md`.

**Entry friction**

> "the iOS app is clunky and inconvenient to add events to... Ultimately these extra steps. Have been a barrier to wider use in our family." (Cozi, 2 stars, 2026-01-15)

> "Too many steps to submit an event... After I submit the even for a given day I'm given yet another notification and to confirm what I just did." (TimeTree, 2 stars, 2024-05-06)

That second review describes what this product does to a parent today. The moment something they have just recorded enters the watched stage, the app writes them a to-do asking them to confirm the very thing they were standing there doing (`on_enter_watched`).

**Capture**

> "The new feature that allows you to create events from your camera or from pictures you have taken already of flyers or posters etc. is genius." (TimeTree, 5 stars, 2024-07-08)

> "I love the fact that I can just forward emails with event details to Jam, and it puts them in my calendar for me!" (Jam, 5 stars, 2024-03-20)

**The seam between two adults**

> "Just a shared family Google Calendar. I tried skylight but hated it, plus no one else got onboard with it." (r/nycparents, ~2025)

> "we tried a method where I'd send a calendar invite to him, but then he'd have to actually see it in his email and 'accept' the invite, and that didn't work for us because he never saw them" (r/beyondthebump, ~2025)

**The registration race**

> "Our town summer camp registration opened at 8am and was sold out by 8:09am. Hundreds of spots gone in a matter of minutes. It's absolutely brutal." (u/RImom123, r/Parenting, ~May 2026)

> "Registration doesn't fill up in 3 minutes so you don't have to panic register right when it opens." (u/chuffalupagus, r/workingmoms, ~Mar 2026)

M5's gloss is the sharpest line in the corpus: **"panic register" is "a verb they have coined. This is the emotional peak of the whole category."**

**The mental load**

> "those are all different things because they're different tabs you have to keep open in your brain" (u/phoebe-buffey, r/workingmoms, ~Aug 2026)

**Abandonment.** The most repeated exact phrase in the corpus, across more than a dozen unrelated threads, is "another thing to maintain." The three stated reasons apps fail are that it becomes another thing to maintain, that "no one else got onboard with it" or "I was the only one using it," and that "most apps want you to build out a whole system before you get any value out of them."

**Voice, as parents actually use it**

> "I heavily rely on Siri. My phone, watch, homepod and car. Reminders for EVERYTHING and adding things to lists instantly as I think of them... Means that when my hands are busy I can still make reminders."

> "i have one on my watch, one on calendar, and two warnings on an Alexa"

> "My Alexa reads me my events from the calendar the night before. And then announces everything 1 hour ahead"

"Hey Siri, remind me to..." appears verbatim in at least six unrelated comments. There are **zero instances of conversational voice planning in ~2,300 comments**.

**Privacy refusal**

> "the Dec 2025 update now has an AI scheduler feature that takes up the top quarter of the screen. I don't want it trolling through my emails offering nonsense appointments. I will NEVER pay for this feature." (Cozi, 1 star, 2025-12-12)

> "No one wants AI" (TimeTree, 1 star, 2026-07-31)

Set the Cozi line against the Jam line above: same job, same category, opposite valence. Inbox access reads as surveillance; forwarding reads as delegation.

**Capture versus reference.** Recurring across the corpus: "if it's not on the calendar, it's not happening," "I text myself," "I take a picture of it," and "the flyer in the backpack." Every parent in this corpus with a working system has both a capture channel and a reference surface, and transposes between them by hand, weekly.

---

## Appendix B: the five defects in the email recommendation

Moved out of section 13 so the decision stays readable. Any one of these can change the call. Full argument in `raw/S1-email-decision-memo.md` and `raw/S4-redteam.md` section 3.

**1. No large-incumbent precedent exists.** `add@cozi.com` does not exist and never did, verified against Cozi's full current FAQ and a Wayback CDX sweep of every archived cozi.com "email" URL 2007-2025; the claim traces to usecarly.com, a competitor's SEO site, killed as Tier D. The only precedents are Sense and Schoolcase, both small.

**2. ParentSquare's BLOCKED verdict is unsourceable**, because its help centre is behind a ParentSquare login, so a strategy-critical verdict rests on a citation no reader can check. It needs a first-party test.

**3. ParentSquare's digest default may reduce B' to envelopes.** New accounts default to a 6pm digest, and a digest is content-poor, so for the largest school install base (22M students) B' may forward an envelope saying "you have 4 new messages" rather than content. C4 was scored on the content reading. Combine with the finding that ClassDojo, Remind and Seesaw silently disable email once the parent installs the app, which is how essentially every parent uses them, and B's school coverage in practice may be a fraction of its score.

**4. The 0-of-3,917 count has a demand reading nobody argued.** Cozi, Todoist and Evernote shipped inbound addresses to tens of millions of users and produced zero organic mentions across 3,917 reviews, while Jam's 8 of 88 (9.1%) comes from reviewers self-selected for that feature, the purest survivorship sample in the corpus. Absent an incumbent precedent, that is at least as much a demand signal as a placement signal. Compounding it: no vendor anywhere publishes an inbound-address activation rate, no public funnel comparison of forwarding against OAuth exists, and no survey has ever asked a US parent about comfort with third-party school-comms access.

**5. Silent failure is the documented killer, and the mitigations are not optional.** One Skylight user went eighteen months and multiple missed events before noticing, despite receiving confirmation emails with an Undo button, so confirmation emails are not a sufficient feedback loop. Required in v1: liveness signalling ("last message received N hours ago"), a quiet-stream nag when a family's stream goes silent, a non-email fallback channel, SPF/DKIM/DMARC plus ARC with no rejection on DMARC failure since forwarding breaks DMARC by protocol, and "every message is also forwarded to your regular inbox."

---

## Appendix C: what this research cannot answer

| Gap | Cheapest field test |
|---|---|
| Share of US households sustaining a shared digital family calendar. No data at any tier; the single most decision-relevant unknown in the study | Ten-family diary over four weeks, or instrument connect-rate in-product |
| Willingness to pay for capture, or for AI household assistance. No data at any tier | Price test at the existing paywall with a capture-only value proposition |
| Any US study separating dictation, assistant commands and conversational LLM voice | Instrument all three separately from day one |
| A probability-sampled count of apps or portals a family juggles per child. Only a vendor n=125 exists | Ask 20 beta families to list theirs |
| Parent comfort granting a consumer app inbox access, or a third party receiving a child's school comms. Never asked | Two questions in the beta onboarding survey |
| Onboarding completion benchmarks at any tier | Own funnel telemetry is the only source that will ever exist |
| Sports-physical frequency, permission slips per year, birthday parties attended, orthodontia cadence, non-summer closure days | Ten families each; NCES NHES:PFI and state education agencies are the highest-value paid-search targets |
| Parent trust in AI advice ranked against a pediatrician, teacher, friend and influencer | Never measured 2025-26. Commission it or drop the claim |

`DESKTOP-RESEARCH-PROMPT.md` is the ready-to-paste brief for the 23 gaps a broader-crawling tool could close, split by access-blocked (BLS, NCES, CDC and ACA all 403 automated fetchers), paywalled, or probably nonexistent. Only the first class is fixable by better crawling.

---

## Appendix D: statistics we refused to use (the kill list*)

Confidence key. **High**: the origin publisher's own document or full-text index was checked directly. **Medium**: every reachable path was exhausted but one route stayed closed (paywall, image-only publication, retired PDF), named in the row. Per the Method section, roughly one in four of the **re-traced** kills was overturned; that rate applies to the re-traced subset, not to this list as a whole.

Three further sources were reviewed by the bibliography pass and **excluded without a formal kill**, because nothing in this report ever rested on them: the Cigna loneliness survey, cited only through the Surgeon General's advisory, which restates neither n nor fielding window; Wikipedia citing Axios for Ohai's $6M seed; and competitor-written "best AI family organizer" roundups used for lead generation.

### Worked example 1: Pew's fabricated "37 million Millennial parents"

A false kill here was the expected outcome. Instead this is the most clearly fabricated item found. A full-text search of Pew's own REST API for "Millennial parents," "largest generation of parents" and "37 million Millennials" returns nothing. What Pew actually published: **17 million** Millennial women had become mothers as of 2016, and **19 million** had given birth as of 2018. Mothers only, both times. **37M looks like someone doubled 19M to add fathers**, which is invalid arithmetic and not Pew's. Pew changed its generational-reporting policy in May 2023, so no newer figure rescues it. The laundering* move is fabricated attribution, the rarest and worst category: a real institution's name bolted onto a number it never published. It appears in this repo's own `gtm-research.md`. Verified by V6. Confidence High.

### Worked example 2: "70% quit sports by 13"

The laundering event is documented on the record. The Washington Post, Julianna W. Miner, 2016-06-01, headlined "Why 70 percent of kids quit sports by age 13," opening "According to a poll from the National Alliance for Youth Sports." The hyperlink behind that attribution points to **nays.org, the bare homepage**. No study, no page, no date, no n. **NAYS has never published such a poll**, and a Wayback sweep of the domain finds nothing.

The real measured value is **35%**. Ewing and Seefeldt, Michigan State University, funded by the Athletic Footwear Council of the SGMA, free full text at ERIC ED360267: n ~26,000 youth aged 10-18, with the attrition analysis covering ~8,000 youth across 17 regional sites. Verbatim: "The attrition rate for youth between the ages of 11 and 18 was reported to be 35%... Gould (1987) synthesized several studies... and found that the average attrition rate was also 35%. There was considerable variance... varying from 22 to 59%."

Where 70 came from: the same report notes ~42% of 10-year-olds vs 12.0% of 18-year-olds on agency-sponsored teams, a 71% relative decline. Four qualifiers were stripped to get from that to the circulating claim. It is the report's explicitly cherry-picked "most dramatic display" (baseball and swimming only); it is ages 10 to 18, not "by 13"; it is agency-sponsored teams only, excluding school sports; and it is a cross-sectional participation gradient, not longitudinal dropout.

Two named researchers independently reached the same conclusion in 2026, which supplies a citable current debunk: Marty Fox of the Aspen Institute Sports and Society Program and Joseph Janosky of Lasell University, reported by USA TODAY 2026-04-11. Janosky: "One of the most repeated statistics in youth sports may not have a clear primary source... What I found instead was a chain of secondary sources. Each one pointing to another. None clearly anchored to a transparent, verifiable study. There's a term for this: citation drift." CDC's Youth Risk Behavior Survey contradicts it by measurement: organized-sport participation among US high-school students has been above 50% consistently since 2000, except during COVID. Usable replacement: **the average age at which a child quits sports is 12** (Aspen/Project Play). Verified by V6 and V7. Confidence High.

### The list

Fabricated: no origin publisher, or the named publisher never said it. All KILL.

| ID | Statistic | Claimed source | True origin | By | Conf |
|---|---|---|---|---|---|
| K1 | "37M Millennial parents" | Pew | None. Pew published 17M/19M Millennial **mothers** | V6 | High |
| K2 | "30%+ secure summer childcare before the prior year ends" | BLS 2023 | None. BLS publishes nothing on booking timing, no aggregator trail at all | V6 | High |
| K3 | "15% completion drop per onboarding screen beyond five" | Appcues | Absent from Appcues' sitemap. Footprint is one blog post | V6 | High |
| K4 | "4-6% completion drop per form field beyond the eighth" | Baymard | No per-field percentage exists. Baymard's method structurally cannot produce a slope | V6 | High |
| K5 | "$150B cost of missed US appointments" | "industry", now peer-reviewed papers | A 2017 trade-magazine op-ed by a scheduling vendor's CMO. Competing published figure: $50B | V6 | High |
| K6 | "60% / 74% of parents feel guilty about screen time" | various | None. Publishers measure concern, not guilt. Pew Oct 2025 n=3,054: 42% say they could do better | V6 | High |
| K7 | "Child attends 8-12 birthday parties/year" | various | None. Only hosting-side vendor artifacts. Construct measured nowhere | V7 | High |
| K9 | "20.5% of people globally use voice search" | . | No textual origin. **Route not closed: image-baked DataReportal/GWI slides were not OCR'd** | V7 | Medium |
| K10 | "24% / 26% / 38% voice while cooking / chores / relaxing" | . | Invented. The real measurement exists and is ~2.5x higher (see K27b) | V7 | High |
| K11 | "Districts use 3-7 apps parents must download" | "studies" | Back-formed from response buckets. **Do not substitute LearnPlatform's 2,739 to 2,982 tools/district: that measures district access, not parent installs, and swapping it in is us doing the laundering** | V7 | High |
| K12 | "60% of parents miss important events" | Cornerstone/Edsby | Not in the Cornerstone PDF. Accepted on V6/V2's evidence, not re-fetched | V6 | High |
| K13 | "70% quit sports by 13" | NAYS / various | See worked example 2. Real value 35% | V6, V7 | High |
| K14 | "14,000+ AI startups launched 2024, 3,800 shut 2025 = 40%" | . | One Medium post. Arithmetic is incoherent: 3,800/14,000 = 27% | V6, V7 | High |
| K15 | "19.2% complete onboarding; 8.4% after 30 days" | . | None. **No onboarding-completion benchmark exists at any tier.** The 8.4% is Airship Day-30 app **retention** over ~2.6bn **devices**, fielded Jan-Jun 2023, relabelled. Four laundering moves in one number: measurement substitution, devices as people, date stripping, metric relabelling | V7 | High |
| K16 | "Friends and family is the #1 way parents find a camp" | ACA | Not on ACA's site. No n, no window | V6 | High |
| K17 | ActivityHero "4M families" / "400k subscribers" | ActivityHero | Rate card only. No counting-unit definition. Cite only as "ActivityHero says" | V6 | High |
| K18 | **Anything sourced to usecarly.com** | usecarly | SEO site for a competing AI assistant. ~200 listicles, no method page. Publisher-level kill | V6 | High |
| K19 | "Voice-AI startups raised $7B+ in Q1 2026" | . | No dataset named. Crunchbase publishes no voice-AI cut at all | V7 | High |
| K21 | "Voice assistant market to $59.9B by 2033" | Astute Analytica | Market-sizing press release, no methodology | V6, V7 | High |
| K22 | "TeamSnap 24 million users" | TeamSnap | No origin. TeamSnap's own releases say 25M (2021) and 30M (2025), and 30M is "parents, players, coaches and administrators," a mixed-role lifetime total against 2M daily actives | V7 | High |
| K23 | "8.2 subscriptions / $118 per month" vs "4.5 subscriptions" | . | Neither has an origin. The self-contradiction is the tell. Real comparator: West Monroe n=2,500 US, June 2021, $273/mo across 21 categories, with 100% underestimating their own spend and 66% by more than $200 | V7 | High |
| K24 | "~50 days off school excluding summer" | . | No origin. **Measured from actual district calendars the answer is 30-38 days, median ~34** (NYC 34, LAUSD 35, Chicago 33, Fairfax 38; CAP's 29 for large districts). The circulating 50 is high by ~50% | V6 supersedes V7 | High |
| K25 | **"add@cozi.com"** | Cozi | Cozi has no inbound email-to-calendar feature and never has. Verified against the full current FAQ and a Wayback CDX sweep of every archived cozi.com "email" URL 2007-2025. Probable propagation source: usecarly.com | V7 | High |
| KX2 | "Youth sports in-season" seasonality row | Analyst construction | Aspen State of Play 2025 verified to contain no season-timing data. Excluded from the chart dataset | Q1/V6 | High |
| KX4 | "Ollie" as a competitor | M2 competitive set | Phantom. Five plausible domains, five unrelated products | V5 | High |

Real origin, laundered beyond use. Cite only with every qualifier restored, or not at all.

| ID | Statistic | The correction | By | Conf |
|---|---|---|---|---|
| K26 | "8.4bn voice assistants by 2026" | Juniper 2020 forecast of 8.4bn **devices worldwide by 2024**. Forecast to measurement, devices to people, global to US, and the year moved. **Overturned as a kill: the origin exists** | V6 | High |
| K27 | "71% prefer voice over typing" | PwC 2018, n=1,000 US 18-64. A hypothetical forced binary, **for search only**, on a base of assistant owners. **The figure does not appear in the PwC report the corpus cited at all**: misattribution, not a stripped qualifier. Pew's real comparator is 22% | V6, V7 | High |
| K27b | The context triple's real values | Same PwC 2018 study: 65% cooking, 62% multitasking, 57% TV, 29% working, 74% at home, 0% driving on a speaker vs 40% on a phone. Plus 18-24s using voice daily **less** than 25-49s (59% vs 65%), because in public it "just looks weird." **Restored as usable.** Route not fully closed: PwC's PDF is retired, values via Voicebot 2018-05-02 and TechCrunch 2018-04-30 | V7 | Medium |
| K28 | "92% of families will travel with kids next year" | No FTA year reads 92% (real series 93/93/88/79/70/88/81%), and non-travellers are filtered out at the end of the first question block, so **no year is a population estimate**. The most dangerous item in the appendix: real association, real university partner, real n=3,370 | V6 | High |
| K29 | "Fathers get 35% of custody time" | A 2018 vendor **model**: attorneys surveyed on typical state guideline schedules, run through the vendor's own software. Verbatim: "No customer data was used." Method **is** disclosed, self-described as more anecdotal, so the kill must read "method disclosed but not survey-based," not "no method" | V6 | High |
| K30 | "30% pediatric no-show rate" | No US national rate exists. Literature spans 1.5-24%; Boston Children's 20%. Above 30-50% only in urban safety-net subgroups. Honest range 10-25% | V6 | High |
| K31 | "Gen Z spends $377/month on subscriptions" | US origin is a coupon-affiliate site, n=1,030 on MTurk, Oct 2021, failing Tier C on method. Separately Visa/Basis measured **GBP 305/mo in the UK** (n=4,152), independently relabelled into USD | V6 | High |
| K32 | ACA "26 million campers" | ACA's published figure was 14 million (2013 basis), never 26M; the page is deleted. **Use Gallup/NSLA's 30M (55% of K-12) instead**, and note that survey was fielded May 2024 but asked about **summer 2023** | V6 | High |
| K33 | ACA "more than 14,000 camps" | Real: ACA 2017 Sites, Facilities and Programs Report (8,400 resident / 5,600 day). Nine years stale, hosting page deleted. **Overturned as a kill.** Citable only as "ACA, 2017" | V6 | High |
| K34 | "Over 62% of US adults use a voice assistant," dated 2025 or 2026 | Real: NPR/Edison Smart Audio Report, fielded 2022-02-28 to 04-18, n=2,334. **Pure date-stripping.** Cite as 2022 or not at all | V7 | High |
| K8 | "57% of voice search users use voice commands daily" | **Base swap, not fabrication.** Edison's real sentence: "57% of voice **command** users use voice commands daily." **Reclassified out of the fabricated tier**, because the appendix must not accuse a real publisher of the wrong offence. Note Edison's own marketing page says "57% of Americans," which is internally impossible against its own 62% ever-use figure, so the publisher may be laundering its own statistic | V7 | High |
| K20 | "153.5M US voice assistant users 2025" | **Reclassified from fabricated to unverifiable at origin, paywalled, forecast presented as measurement.** The 2024 eMarketer vintage gives 145.1M (2023) to 170.3M (2028), so ~154.9M in 2025 sits on their own curve. Separately, the same figure circulates attributed to **Astute Analytica** framed as "engaged daily," from the same press release as their $59.9B forecast. Still not citable. Route not closed: chart is paywalled | V7 | Medium |
| K35 | Edsby "85% rate their setup 5/10 or below" | Arithmetically correct, but **North American (US and Canada), n=125 parents**, vendor-commissioned, fielded Dec 2024 to Jan 2025. The GovTech, eSchool News and PRNewswire "corroborations" are re-reports of one release. The "10 to 15 apps" figure was **curriculum leaders** describing their district, not families | V6 | High |
| K36 | Birthday party "$314 average" | What to Expect / Everyday Health poll, fielded 2024-04-25 to 04-26, n=404 women 18-44 **pregnant or with a child under 5**, no probability sample, no MoE. Do not build any generational claim on its $329/$276 split | V6 | High |
| K37 | Bright Horizons "85% / 90% summer sleep-loss" | Harris Poll for Bright Horizons, fielded **2026-04-14 to 04-16** (not 2025), n=2,030 US adults. **90% rests on n=479 employed parents and 85% on n=616 parents of under-18s.** Never present either on the full 2,030. MFI is multi-wave: always name the wave. This repo's `gtm-strategy.md` carries the wrong year | V6 | High |
| K38 | Google "63% of Gemini users use voice" | Global vendor telemetry, zero disclosed method, no definition of a voice user. Never use the adjacent "busy parents are 43% more likely to use voice": no base, no comparison group | V6 | High |
| K39 | eMarketer "139.8M to 168.2M US voice users" | A forecast at both endpoints. Definition is individuals of **any age** using an assistant monthly on any device | V6 | High |
| K40 | US Travel "1.99B trips in 2026" | 2025's 1.95B is an actual; 2026's 1.99B is a forecast. Unit is **person-trips, not people** | V6 | High |
| K41 | Skylight "mental load worth $60,000/year"; Forbes' "$3.8 trillion" | The underlying Harris survey is sound and citable (n=2,005 US parents, fielded 2024-05-15 to 05-22, +/-2.9pp). **$60,000 is derived** (hours x a $35.86 wage) and Forbes' national extrapolation is unsupported. Our own best source, laundered downstream | V6 | High |
| K42 | Klook "91% of travelers rely on AI travel planners" | n=11,000 across 20 markets, **15 of them APAC**, on **Klook's own customer base**, and "used AI for tasks" was corrupted into "rely on." Kill stands for US use | V7 | High |
| K43 | Litmus email-client share read as mailbox-provider share | Litmus measures the **rendering client's user agent**. Apple is 62.3% of opens vs 3.6% of mailboxes vs 17% of US adults on iCloud Mail. Roughly 90%+ of "Apple" opens are Apple's app reading someone else's mailbox. The purest devices-as-people case in the corpus, caught before it shipped | S1, V6 | High |
| K44 | "CASA costs $15,000+" | Traces to a pre-CASA Ask HN thread and to Google fee language removed from its own docs between June 2022 and June 2023. Live lab prices are $675 to $8,000 | V6 | High |
| KX1 | "Aggregate planning load varies only 1.47x across the year" | Arithmetically correct over the collector's table and an artifact of row normalisation plus ordinal truncation. Do not publish. The chart dataset carries no aggregate row | Q1, V3 | High |
| KX6 | "Camperoni is ~1/18th of ActivityHero's live inventory" | The ~500-listing input was Feb 2025 trade press, 18 months stale. Camperoni's live index holds ~4,324 against ActivityHero's 9,008 live: **roughly one half**. This weakens our position; do not spin it | V5 | High |
| KX7 | "Capture is mentioned far more often than voice" | Refuted as stated. Corpus-wide across seven organiser apps: voice 106 mentions (0.68%) vs capture 68 (0.43%). True only within products that ship capture | V5 | High |
| KX8 | M1's complaint-theme rankings as measurement | No regex, numerator or denominator, and the file's two rankings contradict each other. Label as judgement at the point of use. Counted values over 5,847 sub-4-star reviews: price 14.2%, sync 6.8% | V5 | High |
| KX9 | "Distel et al." (public voice-shame study, n=860) | **The author does not exist.** The DOI is real; the paper is Kowalczuk and Musial | V5 | High |
| KX10 | "Women lead on 8 of 12 Gallup tasks" | Six of 12 in dual-full-time households | V1 | High |
| KX11 | "Only two of Daminger's four components are gendered" | The paper exempts **decision-making only**. Women do more cognitive labour overall | V1 | High |
| KX12 | "88% of mothers own scheduling" as a population figure | Real but non-probability: n=393 US mothers, online convenience recruitment, fielded 2005-2010, roughly half graduate-degreed | V1 | High |
| KX13 | "The gap widened from 1.40x (2015) to 2.00x (2025)" | Point estimates real and exact; the inference is not defensible from three cross-sections | V1 | High |
| KX14 | "Affordability (73%) outranks planning difficulty (43%)" for trips | Apples to oranges: two different survey batteries. Within-battery, "planning the trip" ranks **27%, 6th of 17** obstacles, and 6% among parents unlikely to travel. This makes the trip rejection stronger | V3 | High |
| KX15 | "55% of trial cancellations occur on Day 0" | **55.4% of three-day-trial cancellations** | V4 | High |
| KX16 | "Model an annual product at AI-app retention (~21%)" | The 21.1% figure is monthly-plan scoped. Model an annual product from **44.1% yearly vs 17.0% monthly**, a 2.6x plan-type effect that dwarfs the ~1.4x AI effect, with an explicit sensitivity-tested haircut | V4 | High |
| KX17 | "Apple's personal-context Siri ships September 2026, free" | Apple Newsroom (2026-06-08) says **beta later in 2026**. No September date, no pricing statement | V4 | High |
| KX18 | "AP-NORC youth-sports poll" | It is AP with **Ipsos KnowledgePanel**. NORC is not named. And the "logistics above cost" gap is directional only: at +/-4.9 on n=510, 76 vs 74 round identically. State it as "logistics is named at least as often as cost" | V4 | High |
| KX19 | "The Gallup/NSLA/ACA summer survey describes summer 2024" | Fielded May 2024, **asked about summer 2023**. Label the reference year | V5 | High |
| KX20 | "Mommy Poppins covers 12 US metros" | Sixteen | V5 | High |
| KX21 | "2,006 co-parenting reviews across 7 apps" | The **sample size is correct and must not be "fixed"**: Apple's RSS cap is ~500 per sort order, not per app. The app count is wrong: **6, not 7** | V5 | High |
| KX22 | ParentSquare "BLOCKED" in the feasibility matrix | **Unsourceable.** The help centre is behind a ParentSquare login, so a strategy-critical verdict rests on a citation no reader can check. Needs a first-party test | V6 | High |
| . | Brightwheel "provider must add the address" | **Inverted.** The guardian can edit; providers cannot | V6 | High |
| . | "Gmail forwarding is a collapsed step" | It is not. The source user must return and click Save Changes, and Google shows a week-long banner warning that unexplained forwarding may mean someone else has account access | V6 | High |
| . | "Free CASA tier 2 self-scan died May 2024" | It died in **2026**. And "all body-reading scopes are restricted" is too broad: `gmail.metadata` is restricted and reads no body, while `gmail.addons.current.message.readonly` reads content and is only sensitive. The `gmail.modify` conclusion is unaffected. Drop "Google-named preferred partner" | V6 | High |

Identified by the bibliography pass rather than by V6 or V7. These are cited inside `raw/` but fit no tier, so a reader who goes looking would otherwise find them with no verdict attached.

| ID | Source | Verdict | Confidence |
|---|---|---|---|
| B1 | **SFIA sports participation tracking** | Relayed inside Aspen Institute's State of Play 2025, which explicitly states the method is undisclosed, and no SFIA publisher page was ever reached. **Not citable on its own.** It sits behind a Tier B relay but is not itself tierable, so any figure resting on it inherits the relay's caveat and must never be presented as SFIA data | High on the relay, unresolved at origin |
| B2 | **Juniper Research device forecast** (behind "8.4 billion voice assistants") | V6 correctly overturned the claim that no origin exists and V7 corrected the target year to **2024**, but the forecast itself was never retrieved at origin. Same failure class as the reclassified eMarketer and Astute Analytica points: forecast presented as measurement, devices counted as people, global relabelled US. **Not citable** | Medium, origin never retrieved |
| B3 | **Bango "5.4 subscriptions per person"** (2025, n=5,000) | Appears only inside V6's comparator list and was never independently retrieved. **Unverified at origin, not citable** | Medium, origin never retrieved |

Restored, and usable. **18% of youth-sports parents took on debt** (Harris Poll for Good Sports, n=741 parents, fielded 2024-10-16 to 10-18, weighted, +/-4.2pp, exact question wording published; the 18% base is the 688 whose children ever played). P4 killed it on a 4x gap with LendingTree's 79%. That is a denominator and vintage difference, not a contradiction, and **LendingTree's 79% is the unusable one**: its base excludes non-competitive families, and LendingTree's own 2023 re-run measures 42%. Also restored: the Ewing and Seefeldt study itself (ERIC ED360267), discarded along with a bad number derived from it; and Nah (2004), confirmed including the 38-second tolerance figure, so the wait-tolerance argument may cite it directly.

Measured nowhere, at any tier. Stating these is what stops the next person fabricating them: hours a US parent spends researching or booking summer care; trips per year for US households with children; time spent deciding a weekend activity; share of US households sustaining a shared digital family calendar; apps and portals per family, probability-sampled; any mobile-onboarding completion benchmark; parties attended per child per year; permission slips per year; parents' comfort granting a consumer app inbox access; any funnel comparison of email-forwarding onboarding against OAuth; D1/D7/D30* retention benchmarks for the relevant categories.
