# Parenting app value and safety strategy

Research date: 13 October 2026. Product strategy for Miguel. This is a research-informed design recommendation, not a clinical validation or a legal compliance opinion. All child and family examples below are synthetic.

## Recommendation

Build around helping parents know their children more accurately and respond with more curiosity. Cut the administrative surface and the generic article feed. Keep a small, carefully reviewed knowledge base behind the conversation.

The durable asset should be an evolving, parent-correctable record of meaningful moments, strengths, interests, expressed preferences, relationships, contexts, and things that helped. The compelling experience is: “You remembered something important, connected it carefully to today, and helped me understand my child a little better.” A hidden neuroscience profile is a poor scientific and trust foundation. Invisible data entry can make the product feel effortless; invisible judgments about a child should not be the mechanism.

The strongest initial concept is a relationship-focused curiosity companion, with a portable context layer that can later support Dots or Muse. Do not assume either platform currently supports a particular integration, permission scope, deletion workflow, or retention guarantee. Verify those capabilities before promising them.

Three separate hypotheses need testing:

1. Parents value a child-specific history enough to return and pay.
2. That history improves the usefulness of the next conversation beyond a capable general assistant with ordinary memory.
3. The resulting experience improves understanding or connection without creating labels, anxiety, surveillance, or overconfidence.

More accumulated data is not proof of any of these. The proposed advantage is trustworthy continuity and useful learning, not the mere existence of a large profile.

## What science supports and what it does not

### Support for the underlying activity

Responsive, reciprocal interactions between a child and caring adult are important to development. Developmental neuroscience provides a reason to support attentive relationships; it does not provide a method for reading an individual child's brain from a parent's account. The Harvard Center on the Developing Child describes responsive back-and-forth exchanges and their developmental role. Use this as background for useful interaction design, not as evidence that the app can measure neural circuitry. [Harvard Center on the Developing Child](https://developingchild.harvard.edu/key-concept/serve-and-return/)

WHO recommends evidence-based parenting interventions intended to strengthen parent–child relationships and reduce harmful parenting and related difficulties. This supports investing in practical skills and reflection rather than a content feed alone. It does not establish that an unrestricted AI conversation, a few extracted traits, or a shortened adaptation has the benefits of the evaluated interventions. [WHO parenting intervention guideline](https://www.who.int/publications/i/item/9789240065505)

Structured online parenting interventions have been studied, including a randomized trial of an internet-assisted program for parents of four-year-olds with disruptive behavior. That intervention was a structured program, not a general conversational profile engine. Its clinical population and delivery model should not be silently generalized to all families or all ages. [Sourander and colleagues, 2016](https://jamanetwork.com/journals/jamapsychiatry/fullarticle/2494708)

### Observation is not screening or diagnosis

CDC distinguishes everyday developmental monitoring from formal screening with validated tools. Its milestone checklists are not substitutes for standardized developmental screening. A chat system can organize what a parent noticed and support a discussion with a professional; extracting attributes from conversation does not convert that history into a validated assessment. [CDC developmental monitoring and screening](https://www.cdc.gov/act-early/about/developmental-monitoring-and-screening.html), [CDC guidance when there is a concern](https://www.cdc.gov/concerned)

NIMH describes child mental-health assessment as involving developmental and medical history, information from school, and, when appropriate, interviews, testing, and observations of the child. CDC similarly emphasizes multiple settings and alternative explanations in ADHD assessment. This is an important reason not to infer ADHD, autism, anxiety, attachment classifications, trauma, intelligence, or an “executive function age” from ordinary parent chat. [NIMH assessment overview](https://www.nimh.nih.gov/health/publications/children-and-mental-health), [CDC ADHD diagnosis](https://www.cdc.gov/adhd/diagnosis/index.html)

This review found no basis in the cited sources for validating this proposed app's child-specific neuroscience scores or diagnostic predictions. That is an evidence gap for this product claim, not a claim that no relevant research exists anywhere.

### Useful distinctions for the product

- Supported observation: “You reported that she chose drawing on three recent afternoons.”
- Tentative interpretation: “Drawing might be one way she likes to settle after school. Would that fit, or have you noticed something different?”
- Question that improves understanding: “What does she say she enjoys about it?”
- Unsupported leap: “She has a visually dominant brain and elevated sensory sensitivity.”
- Incorrect causal conclusion: “The new routine improved her neural regulation.”

A child may behave differently with different people and in different environments. Disagreement is not automatically evidence that one caregiver is wrong. A research literature on informant discrepancies reinforces the need to preserve source and context instead of averaging accounts into one supposedly objective truth. [De Los Reyes and Kazdin](https://pubmed.ncbi.nlm.nih.gov/16060799/), [De Los Reyes and colleagues](https://pubmed.ncbi.nlm.nih.gov/25915035/)

## Three lean concepts

These are differentiated product directions, not assertions that no competitor offers similar features. Separate market research has identified direct overlap in conversation, developmental profiles, and strategy tracking. Each direction still needs a concrete advantage over existing products and general assistants.

### 1 Curiosity companion

**Promise:** Understand a little more about your child through the moments you already share.

**Initial audience:** Parents of preschool and early-primary children, narrowed to one age band and language for the first pilot. Ages 3–6 are a proposed discovery segment, not an evidence-backed boundary for efficacy. Adult-facing use only initially.

**Core loop:** A parent describes a meaningful moment, positive or difficult. The app reflects what was actually reported, brings in one relevant prior observation, offers two plausible interpretations when appropriate, and suggests one question or shared activity. At the next natural opportunity it asks what the parent noticed and updates the record.

**Memory:** Interests, enjoyable shared activities, ways the child expresses preferences, strengths, contexts that make participation easier, important relationships, changes, exceptions, and the parent's own goals or constraints. Difficult moments are one category, not the organizing identity.

**Example:** “She spent ages building a fort, then got upset when her cousin joined.” The assistant remembers that she enjoys designing spaces and that, according to the parent, she recently said she wanted to finish her plan first. It might suggest asking her to show where someone else could contribute, while leaving room for her to prefer solo play. It must not conclude that she is inflexible, socially anxious, autistic, or gifted.

**Lean surface:** Conversation, a compact “What we're learning” view, and a parent-controlled list of saved moments. No feed, growth score, child ranking, or daily streak.

**Value test:** Does remembered context yield a more useful question and a better real-world interaction? Would the parent miss this continuity if it disappeared?

**Risk:** Attractive-sounding interpretations may flatter the parent or become labels. Require visible evidence, alternatives, and easy correction.

### 2 Family fieldbook and portable context

**Promise:** Carry the important things you have learned about your child into the tools and conversations where they help.

**Audience:** Families already using assistants such as Dots or Muse and frustrated by repeatedly explaining family context.

**Core loop:** Conversation produces proposed observations. The parent reviews a short collection, selects a purpose, and approves a minimal context packet for a named destination. A new result can return as a proposed observation; it does not silently rewrite the child's history.

**Examples:** A play-planning assistant receives age band, current interests, accessibility needs the parent explicitly chose to share, and activities enjoyed previously. It does not receive the complete developmental or relationship history. A parent preparing a school conversation selects recent examples and questions, excluding unrelated family material.

**Lean surface:** The same child record plus export and an explicit preview. Start with a user-mediated text export if secure integration capabilities are absent. Add an API only when there is demonstrated usage.

**Value test:** Does the parent save time and obtain more fitting help in a second tool, while understanding what was shared? Is this materially better than copying a short note?

**Risk:** Portability creates new disclosure routes, stale copies, and contested caregiver access. Parent-controlled stewardship does not mean the child has no privacy rights or future agency. Destination, exact fields, purpose, expiry, and revocation must be visible. Do not promise deletion of a copy in another service unless it is actually enforceable.

### 3 Development conversation companion

**Promise:** Bring a clearer, balanced account of your child to the next conversation with a pediatrician, teacher, or caregiver.

**Audience:** Parents who have a specific question about a change, learning experience, strength, or developmental concern.

**Core loop:** Gather a few dated examples and what the child or other adults reportedly said; ask about context and counterexamples; produce a parent-reviewed one-page summary with strengths, questions, changes, and missing information. The parent decides whether and with whom to share it.

**Lean surface:** Conversation and an editable, source-linked brief. No diagnosis or automatic clinician messaging.

**Value test:** Do parents feel better prepared, and do independent professionals rate the summary as accurate, balanced, and useful? Measure preparation time and clarity rather than “conditions detected.”

**Risk:** A polished brief can make weak inferences look medically authoritative. Label parent reports explicitly, keep interpretation separate, and do not turn school or clinician comments into verified facts without the actual source and permission.

**Tradeoff:** This has a clear event-based value but lower natural frequency, and it pulls the product closer to healthcare and school workflows. It is a good optional output of the core record, not necessarily the initial whole product.

## Recommended wedge and product boundary

Start with Concept 1. Design the record so Concept 2 can follow without a rebuild. Use Concept 3 as an occasional parent-requested export after the basics work.

Positioning to test: “A place to notice who your child is becoming, remember what matters, and find new ways to connect.” This is a proposed promise to validate, not a claim of measured benefit.

The first session should help before collecting a comprehensive history. Ask what the parent noticed recently and what they want to understand. Ask for age band only when needed. Offer something useful immediately. Let the record grow through relevant moments, not a long intake or a simulated clinical interview.

Keep three visible controls close to every meaningful observation: “That fits,” “Change this,” and “Forget this.” Parent agreement verifies that the summary reflects the parent's account; it does not make an inference clinically true.

Every few interactions, invite an exception or update: “Is this still true?” or “When is it different?” A record that only accumulates confirmations will get more confident without necessarily getting more accurate.

Do not make successful use depend on constant logging. The desired loop ends with attention returning to the real child. Avoid coaching toward obedience as the universal outcome. Enjoyment, agency, feeling heard, less misunderstanding, and a parent's changed interpretation can all be valid outcomes.

## The minimum trustworthy child record

Use separate record types. Never flatten them into one undifferentiated profile paragraph.

1. **Parent observation:** What happened, reported date, event date if known, setting, who observed it, and any uncertainty.
2. **Child perspective as reported:** The child's words or preference, with provenance such as “parent reports child said.” Do not present this as direct testimony when it is not.
3. **Caregiver interpretation:** Explicitly attributed to that caregiver; optionally contested or context-dependent.
4. **Working hypothesis:** A tentative, revisable explanation, linked to supporting and conflicting observations, with a review date. No clinical or neural trait inference in the first product.
5. **Activity and outcome:** What the parent tried, whether it was actually tried, what happened, who reported the outcome, and other relevant changes. “Helpful that day” is not causation or a permanent rule.
6. **Preference or constraint:** Parent-selected, relevant to giving useful support. Keep parent needs separate from child attributes.
7. **Professional finding if introduced later:** Distinguish a parent saying a professional diagnosed something from an authenticated document. Store only what is necessary and authorized. Do not reinterpret or overturn professional advice.

Suggested metadata: pseudonymous child ID, source speaker, source event, time, context, record type, confirmation status, conflicting record IDs, last checked date, visibility, allowed purposes, retention category, and version. A self-assigned model confidence percentage is not a calibrated clinical probability. In the interface prefer evidence descriptions such as “reported twice at home; no information from school.”

Positive and ordinary moments must be first-class. If the app sees only moments of crisis, say that its view is incomplete. Silence is missing information, not evidence that a problem resolved or a skill is absent.

If caregivers disagree, retain “A reports this at bedtime” and “B reports something different on weekends.” Do not create a majority-vote truth, rank caregivers' credibility, infer deception, or share one caregiver's private account automatically with another. Avoid importing custody disputes or accusations into a neutral-looking child profile.

## Content should be useful in the moment

Keep a small reviewed library of explanations, questions, connection activities, communication examples, and support-seeking guidance. Attach each item to an age/developmental range, intended use, source, review date, and situations where it is inappropriate. Have a qualified child-development professional review adaptations and a diverse group of parents assess language and feasibility.

The conversation should ordinarily offer one relevant idea with a short reason and an optional source. A browseable encyclopedia can wait. Content remains important as a quality-controlled foundation even if it is no longer the product's main screen.

For example, CDC's practical parenting material discusses making routines predictable, considering a child's abilities, and using age-appropriate directions. Those principles can inform specific, reviewed suggestions. They are not a license to prescribe one universal approach or blame a parent when it does not help. Adapt accessibly and do not equate inability, distress, or communication differences with deliberate misbehavior. [CDC routines](https://www.cdc.gov/parenting-toddlers/structure-rules/), [CDC directions](https://www.cdc.gov/parenting-toddlers/communication/giving-directions.html)

Do not claim that citing research makes an individualized recommendation proven. Do not reproduce proprietary questionnaires or modified clinical scales without confirming license, population, scoring, administration, and referral requirements.

## Safety and escalation

The product should explain early that it supports reflection and everyday parenting; it does not continuously monitor a child or replace professional assessment. A disclaimer cannot compensate for diagnostic functionality or diagnostic marketing.

- **Ordinary reflection:** Help the parent clarify context, consider the child's perspective, and choose a low-risk next interaction. Avoid punishment, coercion, or advice that ignores pain or disability.
- **Developmental concern or skill loss:** Encourage a conversation with the child's healthcare professional and provide the parent's observations in a reviewable format. Do not require completion of an app experiment before seeking help. CDC advises acting on concerns and seeking evaluation. [CDC concerned guidance](https://www.cdc.gov/concerned)
- **Persistent distress or impact on everyday functioning:** Encourage professional help rather than repeatedly refining a personality model. NIMH identifies persistence, distress, and interference in home, school, or relationships as reasons to seek help. [NIMH assessment overview](https://www.nimh.nih.gov/health/publications/children-and-mental-health)
- **Immediate danger, threats of harm, serious injury, or suspected abuse:** Interrupt ordinary coaching, encourage immediate appropriate human help, and use clinically reviewed, location-appropriate crisis guidance. Do not promise real-time detection, contact third parties automatically, or imply that a human is watching when no one is. Any actual reporting duty or staffed service needs jurisdiction-specific review.

Implement safety routing before and after generation, with a reviewed response library, logging that minimizes sensitive content, and a manual incident process for the pilot. Evaluate indirect language, ambiguous stories, historical versus current risk, and false reassurance. Rules plus a model reduce some failure modes; neither makes triage reliable without validation.

## Privacy and consent design

Choose launch jurisdiction, age range, adult-only use, business model, and data processors before a real-family pilot. The following is a risk map for counsel and product design, not a conclusion that the app complies or that any one law necessarily applies.

**United States:** COPPA does not automatically apply merely because an adult enters information about a child. FTC guidance distinguishes collection from adults from collection from children; actual audience, direct child interaction, tracking, and product design still matter. The 2025 amended rule generally had an April 22, 2026 compliance date, with specified exceptions. If covered, requirements include stronger controls on retention, security, and certain third-party disclosures. Do not rely on an old COPPA checklist. [FTC FAQ](https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions), [2025 final rule](https://www.govinfo.gov/content/pkg/FR-2025-04-22/html/2025-05904.htm)

**Health information:** A consumer app is not automatically subject to HIPAA simply because its data concerns health; relationships with healthcare entities and the service performed matter. Other protections can still apply. The FTC's amended Health Breach Notification Rule clarifies coverage of many health apps and can encompass unauthorized disclosures, not only hacking. Washington's My Health My Data Act is one example of additional state-level health-data exposure, including some inferred health information. Obtain an actual applicability review. [HHS app guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/health-apps/index.html), [FTC health breach rule](https://www.ftc.gov/news-events/news/press-releases/2024/04/ftc-finalizes-changes-health-breach-notification-rule), [Washington attorney general guidance](https://www.atg.wa.gov/protecting-washingtonians-personal-health-data-and-privacy)

**Europe and United Kingdom:** Assess lawful basis, data minimization, health-data conditions, transparency to the relevant people, access/correction/erasure, processors and international transfers, and whether a data-protection impact assessment is required. GDPR Article 8's child-consent provision concerns consent-based information-society services offered directly to a child; it is not a universal permission rule for every parent-facing record. The UK's Children's Code profiling guidance is important if the service is in its scope, including services likely to be accessed by children. Parent-only design should be assessed rather than assumed to settle applicability. [GDPR official text](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX%3A32016R0679), [EDPB legal bases](https://www.edpb.europa.eu/topics/key-gdpr-concepts/legal-basis_en), [ICO profiling guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/childrens-information/childrens-code-guidance-and-resources/age-appropriate-design-a-code-of-practice-for-online-services/12-profiling)

**Medical product claims:** FDA's January 2026 general-wellness guidance distinguishes low-risk wellness functions and certain healthy-lifestyle software from disease diagnosis and treatment functions. Actual intended use and claims need review; renaming a diagnostic feature “wellness” is not a strategy. Other jurisdictions have their own medical-device frameworks. [FDA general wellness guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/general-wellness-policy-low-risk-devices)

Minimum product commitments to implement and verify:

- No ads, sale of child profiles, audience targeting, or third-party tracking SDKs in child-history surfaces.
- No model training or secondary research on family conversations by default; contractually verify processor behavior. Do not claim zero retention without verifying it for every relevant processor.
- Separate consent or controls for saving long-term observations, optional raw-history retention, another caregiver's access, a named external assistant, and research participation. Essential processing must still be explained plainly.
- Allow a useful short-lived conversation without requiring a comprehensive persistent dossier where technically and legally feasible.
- Use a nickname and age band where enough; avoid exact birth date, school, address, images, recordings, health records, and third-party messages until genuinely needed.
- A parent can review, correct, export, and delete records. Deletion propagates to derived summaries, search indexes, caches, processor copies where applicable, and backup lifecycles. Clearly disclose limits and timing.
- Distinguish deleting raw conversation from deleting the derived observation. Show retention choices without misleading “forever memory” language.
- Do not auto-grant access because someone claims to be a co-parent. Handle invitation identity, scope, revocation, safeguarding, and disputed authority.
- Plan for age-appropriate child awareness and agency as the child matures. A parent's permission to use an app is not a philosophical blank check to preserve every private detail forever.

## Dots and Muse context exchange

This is a proposed interface contract, contingent on supported integrations and permission review:

1. A parent chooses a named destination and purpose.
2. The app constructs the smallest useful packet, with only selected child and parent fields.
3. The parent sees a plain-language preview, including sensitive items and which destination will receive them.
4. If a live integration exists, use narrowly scoped, revocable access rather than an unrestricted profile credential. Otherwise provide an intentional copy/export flow.
5. Mark the packet with provenance, last-reviewed dates, uncertainty, permitted purpose, and expiry expectations. Avoid implying that a receiving service will obey technical controls it does not support.
6. Any returned interpretation is a new proposal with its own source; it cannot overwrite observations or automatically become a clinical fact.

Example synthetic packet for planning a weekend activity: “Age 5; parent reports current interest in insects and drawing; enjoyed quiet outdoor exploration last month; prefers choosing between two activities.” Exclude unrelated school concerns, family conflict, diagnosis history, or a full transcript. The parent must intentionally approve transmitting child information; generic permission to connect an assistant should not silently mean sharing everything.

## Lean implementation

Use one application backend and a normal relational database initially. A knowledge graph, multi-agent clinical system, or vector database is not required to test value.

- A conversation service receives adult input and applies safety routing.
- An extraction step produces structured candidate observations with source references; it cannot directly mint diagnoses or permanent traits.
- A validation layer checks allowed record types, provenance, child identity, scope, and conflicts.
- A compact parent-approved memory view supplies only relevant context to answer generation.
- A versioned, professionally reviewed content set supplies grounded suggestions. Retrieval is bounded to relevant items rather than arbitrary live web content.
- A renderer exposes the observation and interpretation separately and offers correction or forgetting.
- An outcome check records what was actually tried and what was reported, including “not tried,” “did not help,” and “changed my interpretation.”
- A consent/access ledger gates exports and any future integrations. Export previews and privacy controls are core functionality, not postponed administrative features.

Keep raw chat short-lived by default under a clearly disclosed retention choice. A proposed pilot policy might remove unneeded raw history after 30 days while retaining explicitly approved observations for the user's chosen purpose; the exact period must be justified and checked with counsel. Preserve enough minimal evidence for correction without making every chat permanent. Treat embeddings, summaries, and metadata as sensitive records too.

Build household isolation, server-side authorization, encryption, redacted diagnostics, access auditing, deletion verification, and prompt-injection resistance into the first real-data build. A generated observation must never determine its own access permissions. Separate children explicitly and test for cross-child and cross-family contamination.

## Falsifiable validation plan

All numbers below are proposed product decision thresholds, not clinical benchmarks. Predeclare them before observing results and report uncertainty and missing data. No real child records are needed for the initial synthetic work.

### Gate 1 Does the framing match a real need

Interview 12–15 parents in the chosen age band and language. Show the three concepts with synthetic examples. Ask them to explain a recent moment they wished they understood better, what they did, and how they currently use assistants. Avoid leading with “Would you like an app that understands your child?”

Success signal: at least half identify a recurring, specific need and choose to try the curiosity loop over a generic advice/chat demonstration. Failure signal: enthusiasm centers on a neuroscience score, passive tracking, or novelty rather than a concrete interaction the product can improve. Reframe or stop before building a large profile system.

### Gate 2 Can the system remember without inventing

Create 100 synthetic multi-session family histories covering strengths, pleasant moments, ambiguous behavior, multilingual households, disability, mixed caregiver accounts, changing interests, second-hand professional statements, corrections, and deletion requests. Have reviewers label what is supported and what should remain unknown.

Proposed release gates: every saved observation has provenance and a correct child identity; no unsupported diagnostic/neural label; no cross-family disclosure; all seeded critical safety scenarios receive the required escalation; corrections and deletions remove obsolete derived context. Target at least 95% supported extraction precision, with zero severe unsafe errors in the test set. Zero failures in a finite set is a gate, not proof of safety. If the gate fails, fix the system and rerun independent cases.

### Gate 3 Does the memory improve the next interaction

Use blinded paired evaluation on synthetic follow-up questions: identical model and reviewed content, once with the approved longitudinal record and once with current-conversation context only. Reviewers score supported specificity, practical usefulness, child agency, balanced interpretation, and overconfidence. Parents can assess usefulness, while expert reviewers assess unsupported or unsafe claims.

Proposed decision: memory should be preferred on usefulness in at least 65% of relevant pairs, with no increase in unsupported interpretation. Include cases where prior information is stale, contradictory, irrelevant, or absent. If memory mostly adds the child's name or decorative empathy, do not invest in more profile depth. Follow with a benchmark against a capable general assistant's ordinary memory, not only a deliberately weak stateless comparator.

### Gate 4 Does it help families in use

Only after safety/privacy review, run an opt-in, adult-facing four-week feasibility pilot with about 40–60 households. This is not powered to demonstrate clinical efficacy. Compare two parallel groups receiving the same reviewed support: current-conversation-only assistance and assistance using the transparent longitudinal record. Use a short baseline period, similar contact frequency, and a clear safety path in both arms. Avoid a crossover design where earlier advice or memory carries into the comparison.

Measure:

- Parent completes at least two notice–reflect–try–revisit loops.
- Parent can name one useful revised understanding supported by an actual interaction, including cases where an initial hypothesis was wrong.
- Self-reported connection, confidence about the next conversation, and reduced repetition, with clear labels that these are subjective product outcomes.
- Quality of child agency and perspective in the reported interaction; do not equate compliance with success.
- Burden, increased worry, feeling judged, dependence on the app, unsupported label formation, and delayed help-seeking.
- Whether the parent can explain, edit, and delete what is stored and accurately identify what would be shared.
- Parent's voluntary continued use and willingness to pay for a subsequent clearly priced period; do not confuse study compensation with demand.

Proposed continuation gate: at least 60% complete two loops; most completers can identify a concrete useful learning; the memory arm shows a practically worthwhile directional advantage in useful continuity without worse worry or overconfidence. Use confidence intervals and treat inconclusive comparisons as a reason to refine or collect adequate evidence, not as proof. Predefine serious safety/privacy events that pause enrollment immediately.

### Gate 5 Validate the portable layer separately

Use synthetic packets first. Give parents five sharing scenarios. At least 90% should correctly identify which fields and destination are approved; no scenario should unintentionally send health or family-conflict material. Verify revocation/deletion behavior technically and document any downstream limits.

Then test whether selected context saves meaningful re-explanation time and improves the external assistant's result. If a short manual note works just as well, keep export simple and avoid building a complex integration platform.

### What would falsify the business thesis

- Parents prefer generic support and rarely revisit child-specific observations.
- Accurate memory creates no material usefulness advantage over an existing assistant with memory.
- Useful results require hidden diagnostic inferences, broad data collection, or intensive clinical labor that the intended product cannot support.
- Parents like the reflection but find saving a child record intrusive or burdensome.
- The system reinforces labels or increases worry despite corrections and visible uncertainty.
- Cross-tool portability creates more consent burden and privacy risk than value.

If the first three are true, a smaller guided reflection product may still be worthwhile. The longitudinal profile should earn its complexity through evidence.

## Immediate product decisions

1. Choose a first age band, language, and launch jurisdiction.
2. Write the allowed and prohibited claims before designing the profile screen.
3. Prototype one positive-moment loop and one difficult-moment loop with synthetic families.
4. Make provenance, corrections, contradictions, sharing preview, and forgetting work before expanding memory depth.
5. Recruit a qualified child-development reviewer and diverse parent testers.
6. Test value against ordinary assistant memory, not against generic articles alone.
7. Add Dots or Muse connectivity only after actual capability and permission verification.

The strategic bet is that a trustworthy record helps a parent ask better questions and notice their child more clearly over time. It should remain possible for the record to say, “We do not know yet,” and for the child to keep surprising it.
