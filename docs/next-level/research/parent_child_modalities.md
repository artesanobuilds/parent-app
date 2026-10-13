# Child participation without requiring a child-owned phone

Research date: 13 October 2026. U.S.-first product recommendation, with a UK cross-check. This is product research and issue-spotting, not a legal opinion or evidence that the proposed app improves child development. No child accounts were created, no families were contacted, and no child data was collected.

## Recommendation

Build **one parent-led product with several ways for a child to participate**, initially targeting ages 5–8 as a testable segment. A child experience is a distinct permission boundary; it does not have to be a separately installed app.

Start with parent reflection, brief parent–child co-use, and offline activities. Add an isolated child turn on the parent's phone and a paired family-tablet/browser session only after testing whether direct child input adds value. Defer a separate child-device app until repeated use, household device availability, and the value of independent participation justify its distribution and safety costs.

The central question is not “Does this child own a phone?” It is “What device can this family actually use, with whose permission, at the moment this activity helps?” Do not encourage parents to buy a device or increase screen time to use the product.

## What device research establishes

### U.S. evidence

Common Sense's 2025 census uses a nationally representative, probability-based survey of 1,578 parents and reports 2024 data. Among ages 5–8, **58% own a tablet and 13% own a cellphone**. At age 8 specifically, cellphone ownership is 23%. The 2–4 group has 45% tablet and 5% cellphone ownership; that is not an exact estimate for ages 3–4. Across households with children 0–8, 96% have a smartphone and 75% a tablet. Cellphones in this report include restricted and basic phones, so ownership is not equivalent to a compatible app device. [Full census, printed pp. 17 and 35](https://www.commonsensemedia.org/sites/default/files/research/report/2025-common-sense-census-web-2.pdf).

Pew's May 2025 U.S. parent survey provides a newer smartphone-specific age breakdown: **12% of 5–7s, 29% of 8–10s, and 57% of 11–12s own a smartphone**. Across children 12 and under, 61% ever use a smartphone but only 23% own one; 68% ever use a tablet. Those are different concepts and denominators, not a conversion funnel. Parents answered about one randomly selected eligible child. [Pew report, ownership chart on printed p. 18](https://www.pewresearch.org/wp-content/uploads/sites/20/2025/10/PI_2025.10.08_Parents-Kids-Screens_REPORT.pdf), [report overview](https://www.pewresearch.org/internet/2025/10/08/how-parents-manage-screen-time-for-kids/).

### Useful international cross-check, not a U.S. estimate

Ofcom's May 2026 UK report distinguishes ownership from access: among ages 8–17, 78% own a mobile phone and 91% have overall access, including someone else's or a shared household phone. Ownership rises from 56% at age 10 to 83% at age 11. Tablets are the most common way to go online for younger children other than the youngest group; 77% of ages 8–9 use a tablet online. Method changes limit trend comparisons. [Ofcom, printed pp. 13–15](https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/media-literacy-research/children/2026-children-and-parents-report/children-and-parents-media-use-and-attitudes-report-2025-6.pdf?v=418231).

### What these surveys do not establish

They do not show willingness to install this app, permission to use a parent device, a free device at bedtime, app-store restrictions, broadband reliability, independent reading ability, or willingness to disclose feelings. Household possession is not child access, and “ever uses” is not dependable access. Do not blend countries, age bands, cellphone/smartphone definitions, or survey years into a single market-size percentage.

At onboarding or adult-only research, separately ask: device available; shared versus personal; operating system; permitted contexts; adult availability; input/accessibility needs; and whether the family prefers screen-free participation. Do not collect exact birth dates, school names, or sensitive family detail merely to answer this distribution question.

## Five modalities compared

| Modality | When it fits | What it contributes | Principal friction/risk | Lean implementation |
|---|---|---|---|---|
| Parent's phone, isolated child turn | A short, intentional response while the parent is nearby | The child's selection or words, separately attributable | Parent loses phone; ambiguous handback; accidental access to adult journal; notifications; sibling mix-ups | Bounded child session with child-only token, explicit finish screen, adult reauthentication to return |
| Shared family tablet or browser | Families with reliable shared access, especially after school | Same child activity without occupying the parent's phone | Pairing friction; cached logins; shared history; wrong child; device not always available | Responsive child-only client, paired by an adult with a short-lived one-time code; no adult account token on tablet |
| Separate child-device app | Older children or families repeatedly requesting independent access | Asynchronous input and continuity | Ownership excludes many younger families; installs and recovery; unsupervised use; relational-AI risks | Later wrapper/client on the same child-session API; bounded tasks rather than always-open chatbot |
| Parent + child co-use | Good initial fit for ages 3–8; also useful for older children who choose it | Shared language, observation, mutual understanding, adult scaffolding | Child may please the parent; parent may answer for child; both must be available | One short prompt, turn-taking, child can point/choose/skip, then leave the screen together |
| Offline activity, later parent reflection | Screen-averse families; transitions; low connectivity; no second device | Real-world observation and a shared experience | Parent interpretation/recall bias; no independent child report | An activity card or spoken instruction; optional structured parent reflection, clearly labeled as parent-observed |

“Child turn,” “together,” and “offline” should be options for the same activity, not five different products or five new navigation systems.

## Age/use matrix

These are design hypotheses; individual literacy, disability, language, family context, and preference matter more than a rigid birthday cutoff.

| Age | Default participation | Input style to test | Adult role | Device assumption |
|---|---|---|---|---|
| 3–4 | Offline play or co-use | Pointing, choosing pictures, physical play; adult records observations if useful | Present, models and helps; do not frame child as independent respondent | No owned device or reading assumed |
| 5–6 | Co-use, optional brief child turn | One concrete question; large choices; “something else” and “skip”; spoken output optional | Starts session, explains visibility, supports without supplying answers | Parent phone or family tablet; no child email |
| 7–8 | Choice of co-use or bounded child turn | Short choices and optional brief text; child checks what will be saved | Available; explicit return to adult mode | Same-phone and shared-device routes equally supported |
| 9–10 | Child chooses shared or separate session | More independent response; concrete examples; transparent review of saved answers | Clear household agreement; no silent surveillance | Still do not require a smartphone: Pew's 8–10 ownership is 29% |
| 11–12 | Optional linked child app if it earns its place | Greater agency over participation and corrections; accessible alternatives | Explain access and safety limits without pretending the product is a private confidant | More ownership, still not universal: Pew's 11–12 ownership is 57% |

## What co-use evidence supports, and what it does not

AAP guidance recommends exploring media together to support conversation and help children connect media to their experiences. It treats co-use as curious engagement, rather than policing. This supports designing for adult participation; it does not validate this app's effectiveness. [AAP, co-viewing guidance, updated June 2026](https://www.healthychildren.org/English/family-life/Media/Pages/why-co-viewing-is-important-tips-to-share-screen-time-with-your-kids.aspx).

A randomized study of 51 parent–child pairs aged 4–5 found that brief parent guidance during a numerical tablet game increased math-related talk. That is evidence for carefully designed scaffolding in a particular task, not proof of better emotional insight or general developmental benefit. [Zippert et al., 2019](https://pubmed.ncbi.nlm.nih.gov/31192643/).

Other work cautions against assuming a shared screen automatically produces shared attention. A within-family toddler reading study found more control behaviors and less social reciprocity with tablet-based books than print books. Its younger sample and reading context limit extrapolation, but the design lesson is relevant: avoid making possession and tapping the central activity. [Munzer et al., 2019](https://pubmed.ncbi.nlm.nih.gov/31566689/).

**Design inference:** the interface should help adults and children notice and talk to each other, then get out of the way. Measure the quality of the resulting interaction, not just time spent in the app. Independent child input may reduce one kind of parent filtering while creating other risks; “more candid” is a hypothesis to test, not a guarantee.

## What child input should add

Useful, modest contributions:

- A preference the parent might mispredict: “Would you like a plan, company, or a little space before starting?”
- A specific account of an experience: “Which part of getting ready was hard today?”
- A correction: “That isn't what I meant,” or “It was different today.”
- A choice of next step the family can try together.
- A child-approved artifact or response to revisit, when retention is genuinely useful.

Keep parent interpretation and child contribution separate. Store source, date, context, and uncertainty; do not convert one answer into a stable trait. A parent summary should say “They chose X in this activity,” not “Your child is anxious/avoidant/manipulative.” Do not infer diagnosis, personality, attachment style, emotions from facial/voice biometrics, or family relationship quality from incidental behavior.

An example insight card: “You predicted they wanted help starting. They chose a two-minute pause. One thing to try: ask before stepping in.” This is a conversation aid, not a clinical assessment. If child input does not reliably change a useful next action, the simpler parent/offline product may be better.

## Practical diagram specification

Create one diagram with three horizontal lanes: **Adult private space**, **Child-safe participation**, and **Family action**. Use a solid trust boundary between adult-private and child-safe areas. Label arrows with what crosses the boundary.

1. Adult lane: Parent signs in → selects child/profile → chooses one concrete goal → reviews the child-visible activity.
2. A decision node offers “Together,” “Child's turn,” or “Offline.”
3. Together: open a child-safe shared canvas; the private adult journal is unavailable.
4. Child's turn: an adult initiates a restricted session on this phone OR pairs a child-only session to a tablet/browser. Both point to the same bounded activity node.
5. Offline: provide activity instructions → do activity away from the device → optional parent-observed reflection.
6. Child-safe lane: explain who sees answers and what the tool is → invite assent → response or skip → review/save choice → finish. Show a visible “Stop” route from every step.
7. Family-action lane: parent reflection + optional child-approved contribution → evidence-labeled summary → one jointly chosen next step → later check whether it helped.
8. Adult-private return requires reauthentication. Draw no direct child-to-adult-journal arrow.

Callouts: “No child-owned device required”; “Child identity is separate from device identity”; “Adult private notes never enter child model context”; “No raw microphone/camera input in first prototype”; “No open-ended companion in initial scope.”

## Identity, visibility, and safety requirements

### Separate security concepts

- Device possession does not verify age, parental status, or guardianship. A phone unlocked by a child remains a parent-phone risk.
- Initial lawful consent, adult account authentication, per-session role switching, and child assent are different steps. A math puzzle or long-press gate is neither identity proof nor verifiable parental consent.
- Use server-enforced adult/child scopes. Hiding tabs is insufficient. Child sessions cannot fetch parent notes, adult conversation history, billing, exports, invitations, sibling records, or credentials.
- Use a stable child profile with a clearly visible avatar/name cue, but do not pretend the avatar proves who is answering. Attribute responses to a confirmed session, and permit correction of misattribution.
- Pair devices through an adult-authorized, short-lived, single-use code. A paired child's session cannot add another adult. Expire sessions and provide remote revocation.

### Return and accidental access

Test Back gestures, deep links, app switching, task-switcher previews, refresh, crashes, offline reconnect, screen rotation, expired sessions, push notifications, and OS account restoration. On interruption, reopen the child-safe finish screen or locked adult entry; never the last sensitive parent page. Avoid sensitive notification text. Where useful, explain OS guided-access/pinning options, while acknowledging an app cannot fully hide the rest of an unlocked phone. Reauthentication should not silently fall back to a device passcode the child knows.

### Honest visibility and assent

Give a concrete child-readable explanation: “Your grown-up can see the answers you save here. You can skip or stop.” Use teach-back rather than a long privacy wall. Do not call the experience secret, private, or confidential when adults or the service can access it. Minimize what is logged so this promise is meaningful. Let the child review/correct an answer before saving; if an adult later annotates it, preserve the distinction. Provide legally appropriate caregiver access, deletion, and consent withdrawal mechanisms. Do not promise a child's deletion button overrides every legal retention duty.

### More than one household or caregiver

No automatic sharing with a second parent, partner, school, or professional. Authenticate invitations and scope them per child and data category. A second adult joining must not expose the first adult's private journal. Do not merge households based on surname, address, or a claimed relationship. Define a human support route for disputed authority, custody restrictions, foster/kinship arrangements, revocation, and account recovery. Pause disputed sharing instead of choosing a side algorithmically.

### Relational and safeguarding boundaries

Use a warm activity facilitator, not a best friend, therapist, substitute parent, or attachment target. No guilt for leaving, streak loss, variable-reward loops, “I missed you,” secrecy, exclusivity, romantic framing, or rewards for sensitive disclosure. No covert profiling from dwell time, hesitation, voice tone, or drawings. No persuasive optimization for maximum disclosure or time spent.

A safety plan needs expert review before open-ended child content: age-appropriate handling of abuse/self-harm disclosures, predictable escalation, documented human responsibilities, reporting requirements, and limits on availability. Do not default to sending raw allegations to every caregiver, especially if one may be implicated. Reconcile notification duties and child safeguarding with counsel; do not promise the app monitors continuously or can ensure safety.

## Current legal, platform, and provider considerations

### U.S. federal: COPPA

COPPA applies to covered child-directed services and services with actual knowledge of collecting personal information from under-13s. The amended rule is effective, with the principal compliance deadline having passed on April 22, 2026. A “parent app” label or parent-owned phone does not resolve the classification when a child-facing feature collects child data. Voice, identifiers, recordings, and third-party SDK behavior require assessment, not only typed names. [FTC final rule and dates](https://www.govinfo.gov/content/pkg/FR-2025-04-22/html/2025-05904.htm).

For a covered flow, plan notice and verifiable parental consent before collection except where a specific exception applies; parent access/deletion rights; data minimization; reasonable security; purpose-limited retention/deletion policies; and separate consent for non-integral third-party disclosures. Consent methods must be reasonably calculated to establish that the consenting person is the child's parent. An adult gate does not meet that standard automatically. [Current 16 CFR Part 312, especially §§312.4–312.10](https://www.ecfr.gov/current/title-16/chapter-I/subchapter-C/part-312).

Parent-entered information about a child is not automatically treated identically to direct collection from a child under COPPA. That distinction does not eliminate other privacy duties or make sensitive family data safe to collect freely. [FTC guidance](https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions). Have counsel classify each actual flow; use the current rule if older FAQs conflict with amended provisions.

### California: do not use a stale launch checklist

- CCPA/CPRA scope and applicable business thresholds must be assessed. Covered businesses face additional restrictions for sale/sharing of known under-16 users' data, including parental authorization for under-13s. A no-advertising/no-sale/no-sharing business model simplifies exposure but does not erase access/deletion/security duties. [California AG CCPA guidance](https://oag.ca.gov/privacy/ccpa).
- AADC litigation remains nuanced. On March 12, 2026, the Ninth Circuit vacated the blanket injunction and the age-estimation injunction, while affirming injunctions on challenged data-use/dark-pattern restrictions and remanding. Do not say either “the entire Act is blocked” or “every provision is enforceable.” Launch counsel should check later docket orders and the exact features/business covered. [Court opinion](https://cdn.ca9.uscourts.gov/datastore/opinions/2026/03/12/25-2366.pdf).
- California's existing SB 243 companion-chatbot framework includes disclosure and safety obligations; applicability depends on behavior, not simply whether marketing calls it a companion. [2026 legislative analysis summarizing SB 243](https://sjud.senate.ca.gov/system/files/2026-06/ab-2023-wicks-sjud-analysis.pdf).
- **Recent change:** California signed SB 1119, Adam's Law, in September 2026. Official summaries describe stronger child-chatbot protections, age signals, risk assessments, limits on manipulative outputs/memory, parental controls, and independent audits. This research verified enactment, but did not verify every operative date or applicability condition in chaptered text because the legislative text endpoint failed. Treat those details as a required counsel check before launch; do not imply all newly signed duties apply today. [Governor's September 10, 2026 announcement](https://www.gov.ca.gov/2026/09/10/governor-newsom-signs-the-strongest-child-safety-chatbot-and-social-media-laws-in-the-nation/), [author's summary](https://sd18.senate.ca.gov/news/governor-newsom-signs-adams-law).

Other states and countries may impose additional obligations. A browser client avoids an app installation; it does not avoid children's privacy laws.

### App stores

Apple Kids Category requirements include age bands, parental gates for external links/purchases, and strong limits on third-party advertising/analytics and data transmission. Apple's review guidelines explicitly distinguish a parental gate from legal parental consent. They also require disclosure and explicit permission before sharing personal data with third-party AI. A separate kids app adds review/distribution work, but a child-directed feature in the parent app still needs an honest classification and compliant design. [Apple guidelines §§1.3, 5.1.2, 5.1.4](https://developer.apple.com/app-store/review/guidelines/), [Kids design guidance](https://developer.apple.com/kids/).

Google Play Families rules apply if the app's target audience includes children; accurate audience/data declarations, child-appropriate content, and SDK/data practices matter. AI-generated-content policy requires prohibited-content prevention and in-app reporting/flagging. Avoid assuming that a neutral age screen removes duties in a child-directed experience. [Families policy](https://support.google.com/googleplay/android-developer/answer/9893335?hl=en), [AI content policy](https://support.google.com/googleplay/android-developer/answer/13985936?hl=en).

### AI providers and data controls

Review every processor, speech service, safety service, analytics SDK, log sink, and backup. Parent-only journaling can still contain a child’s personal data; moving the input to the adult interface does not remove provider data restrictions. If using OpenAI's API, current under-18 guidance says not to process personal data of under-13s or those below the applicable digital-consent age without first implementing API zero data retention; it also calls for age-appropriate disclosure, filtering, monitoring/reporting, and escalation. Verify approval/configuration and endpoint eligibility. ZDR is not a substitute for lawful consent or security in the app's own systems. [OpenAI under-18 API guidance](https://developers.openai.com/api/docs/guides/safety-checks/under-18-api-guidance).

UNICEF's 2025 child-centered AI guidance emphasizes safety, privacy, transparency, inclusion, and children's best interests. Its June 2026 companion-chatbot brief highlights distinct relational risks. These are useful design standards, not a compliance certificate or proof that long-term developmental risks are settled. [UNICEF guidance](https://www.unicef.org/innocenti/reports/policy-guidance-ai-children), [companion brief](https://www.unicef.org/documents/when-ai-becomes-friend-child-rights-risks).

## Lean sequence and falsifiable experiments

The following are proposed studies, not authorization to recruit or test with children. Thresholds are provisional product decision rules, not validated clinical cutoffs.

### Phase 0: validate the parent problem and access constraints

Use adult-only interviews and fictional clickable scenarios. Approximately 12–15 diverse caregivers can reveal usability problems; this is not representative market research. Include single-device, shared-tablet, separated-household, multilingual, accessibility, and screen-limiting families.

- Hypothesis: handoff friction blocks meaningful use. Compare the same task as parent-phone turn, shared-tablet link, co-use, and offline card, with order counterbalanced.
- Measures: successful start/finish, time and steps, moments of uncertainty, interruption/handback failure, available-device reality, and preferred option for a named real situation.
- Falsification: if at least one-quarter cannot or will not make the required device available, do not make that modality the only route. Treat stated preference as weaker evidence than observed usability.
- Separate question: can parents explain who sees each note and who is currently “speaking”? Any adult-private-data exposure is a stop-ship issue, not an acceptable conversion tradeoff.

### Phase 1: one activity, co-use plus offline route

Use human-reviewed activities and synthetic data in prototypes. Parent-only AI support can be explored separately from child-facing generation. Do not begin with a live conversational companion, voice collection, or camera analysis.

After a separately approved, appropriately consented/assented study:

- Hypothesis: a small child contribution improves the parent's next action beyond parent reflection alone.
- Compare matched activities with and without direct child input. Ask the parent to predict the child's preferred support first; allow the child to answer or skip; assess whether the parent identifies a concrete, child-confirmed useful difference.
- Candidate go/no-go rule: at least half of participating families can name a specific actionable discovery on repeated occasions, without increased pressure or conflict. If not, retain the simpler parent/offline model rather than collect richer child data to rescue it.
- Measure completion of the real-world activity and perceived usefulness, not chat turns, disclosure volume, or child retention alone. Do not make developmental or mental-health efficacy claims from a small usability pilot.

### Phase 2: optional isolated child turn and shared tablet/browser

- Hypothesis: a child-only session increases usable participation without sacrificing trust or comprehension.
- Test both routes with the same content. Record setup abandonment, wrong-profile errors, device unavailability, requests for help, skip/stop success, and adult/child understanding of visibility.
- Safety gate: all tested cross-role and recovery paths pass; one reproducible leakage issue blocks release. Require every participating child to demonstrate the ability to stop and understand the basic sharing rule before proceeding with data collection; revise the design when they cannot.
- Product gate: independent input should add a useful contribution more often than co-use while remaining acceptable to the family. If it merely adds screen time and setup, do not prioritize it.

### Phase 3: decide whether a separate child app is justified

Only consider it after families are successfully using the child session on existing devices and repeatedly request direct entry or native features.

- Hypothesis: installation solves a demonstrated access/reentry problem rather than creating a second acquisition funnel.
- Compare an optional install against the paired browser experience in the eligible segment. Predefine the meaningful improvement in repeat task completion and reduced adult setup before running the test.
- Require no meaningful worsening of comprehension, safety incidents, family conflict, or screen displacement. A lift in time spent alone is not success.
- Keep parent-phone, shared-device, co-use, and offline alternatives. Device ownership should never become a prerequisite for benefiting from the parent product.

## Unresolved decisions worth settling before implementation

1. What exact parent job is this solving: a difficult transition, better conversations, activity planning, or something else? Modality follows that job.
2. Is the first cohort genuinely ages 5–8, and in which launch jurisdictions?
3. What new information must come directly from the child to change a useful next action?
4. Is any open-ended child text/audio necessary? Can structured choices provide the value with substantially less exposure?
5. Who can see which contributions, for how long, in single- and multi-household families?
6. Is the team prepared to operate safeguarding, deletion, incident reporting, provider controls, and support, not merely build the interface?

Bottom line: validate **child participation** before investing in **a separate child app**. Treat access, consent, identity, and parent–child interaction as distinct design problems. The app should earn a small place in family life by improving what happens away from the screen.
