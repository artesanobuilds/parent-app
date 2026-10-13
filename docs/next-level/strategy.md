# Next Level — morning decision memo

**Recommendation: do not finish the old MVP feature list. Test a much smaller, parent-owned child-understanding companion, and earn the case for a standalone app.** The opportunity is helping a parent notice their child more accurately and choose a fitting response with less effort. It is not a brain profile, a better compliance dashboard, or a unique chat-memory loop.

Working name: Next Level (branch title, not cleared consumer brand). Possible brand directions for later clearance: a relationship-centered name, a noticing/journal metaphor, or a quietly capable companion. Do not reuse former brand/design/editorial assets commercially until ownership is settled.

## What exists versus what is proposed

Current code carries a merged parent coach/planner agent, profile mutation tools, anonymous onboarding extraction, name-keyed child JSON profiles and durable checkpoints. `agent.py:275–290` explicitly directs silent learning without revealing tracking. `profiling.py:112–129` stores temperament, learning profile and neurodiversity as optional free text; that is a schema, not scientific validity. Latest base is 5e5caca with October execution service/voice fixes. September context statements about no remote and last August deploy are stale.

Proposed: visible, parent-correctable observations with source, context, uncertainty, review date and consent; separately attributed child perspective, strengths and interests; optional small experiments with outcomes that never imply causal proof. Parent approval gates durable notes. Model hypotheses remain unreviewed until validated by the parent and are never diagnoses. No stable “who this child is” score.

The synthetic prototype proves interaction mechanics only. It does not prove coaching quality, retention, safety in deployment, willingness to pay, or developmental inference validity.

## Product shape test

1. **Moment companion:** conversation when needed, one small next step, one-tap check-in, visible working notes. Best if the recurring interaction feels lighter than a general assistant.
2. **Portable understanding notebook:** parent-owned observations, strengths, perspective and context; concise user-selected brief for whichever assistant they already use. Best if the notebook supplies the durable value and chat is replaceable.
3. **Co-use reflection card:** parent and child notice a good moment or interest together; parent records attributed perspective afterward. Best if understanding requires relationship activity rather than more AI conversation. Not a direct child chatbot.

Head-to-head each shape against a generic assistant with the same reviewed notes. Include three context conditions: full structured profile, a short parent-reviewed summary, and ordinary general-assistant memory. If the short summary performs equally well, do not build an elaborate inference graph. Randomize task order, hide product branding in scoring, and avoid comparing against an intentionally weak generic prompt. Compare completion time, cognitive effort, specificity grounded in supplied evidence, parent correction effort, ability to reject an inaccurate interpretation, export clarity and return choice. Hatley already advertises MCP access, family moments, themes and strategy/outcome history: interoperability is not unoccupied either. Marketing claims from Hatley/indi/Nurturli indicate category competition; they do not establish usage, quality or a unique moat.

## Keep, cut, defer

| Asset | Local direction | Reason / evidence threshold |
|---|---|---|
| Parent-only conversational entry | Keep as experiment | Less frontloaded form burden; must outperform equivalent generic context |
| Child facts and interests | Rebuild as reviewed notes | Existing free-text/hidden extraction lacks attribution/uncertainty |
| Execution service / cancellation lifecycle | Reuse candidate | Recent code addresses streaming ownership; avoid inventing a new agent harness |
| Durable raw coach transcript | Replace in new product design | Permission and lifecycle need explicit definition; current checkpointing contradicts zero-retention aspiration |
| Planning, calendar, camps, Gmail, Circle, CMS breadth | Cut from new launch surface | Removes integration and coordination burden; does not remove working beta functionality |
| Generic article feed | Cut | Reading is readily substitutable; relevant source-backed snippets can support a decision |
| Existing editorial playbook | Defer reuse | Rights and evidence quality unresolved |
| Child voice companion | Defer | Requires distinct safety, age, consent/session boundaries; audit is separate |
| Native voice, photos, sensors | Defer | Not needed to learn whether the notebook matters |
| Dots/Muse/Grok/plugin integration | Research only | Real surfaces, approval, policy and sensitive-data limits must be verified per target |
| Neuroscience-derived score | Reject | No validated individual measurement or incremental utility demonstrated |

## Developmental evidence as discipline

Use developmental science to constrain suggestions and calibrate uncertainty, not to dress a profile in scientific authority. Keep population findings separate from individual parent reports. Record evidence source/date, population/age fit, applicability limitations, reviewer and review date for each suggestion rule. Do not infer a child's diagnosis, neural state, learning style, attachment category or permanent trait from a chat. A child’s perspective reported by a parent remains parent-attributed. Parent reports can be biased; contradictory observations and positive moments belong in the notebook too.

Ask for a concrete episode, one contextual difference and what the parent wants to understand. Offer an optional low-risk observation or action, not an obligation to fix behavior. Use a no-own-device path; external device research is being verified and does not establish demand for child chat. Success includes a parent revising their own interpretation or noticing a strength—not only reduced crying or faster compliance. Persistent distress, harm or developmental concerns require appropriate professional support; the app is not a diagnostic triage service.

## Portability and platform boundary

Manual selected-note export first. Preview exact text before transfer; omit names, exact age, school, location, raw chat, unreviewed inference and health/neurodevelopmental notes. Separate purpose and recipient permission. Once copied externally, deletion in this app cannot recall downstream copies. Do not promise revocation, downstream retention or “private everywhere.” A synthetic filtered export is implemented, no connector is active.

External research indicates separate Sign in with ChatGPT identity and optional plan-powered Responses permissions. Hosted commercial access is eligibility-dependent; local open-source availability does not grant commercial hosted approval. Put a provider adapter behind a usage budget and default to capped platform API if permissions/eligibility are absent. Do not import ChatGPT conversations/memory or imply the subscription grants general unrestricted API credits. No credential setup was performed. Pending final external research brief should replace preliminary detail before implementation.

## Two-week validation, then build gates

**Days 1–3:** clear former partnership/IP/content boundaries before reuse or launch; review age/safety/privacy scope with qualified counsel and a developmental professional. Recruit 8–12 parents of one chosen age band with one recurring moment, not diagnostic categories. Synthetic or researcher-authored scenarios for task tests; do not send real child records to third-party model harnesses.

**Days 4–7:** compare the three product shapes with a generic assistant. Preregister an exploratory gate: at least 6/10 choose a shape for the next real moment, median task burden no greater than generic chat, no material unsupported claims, and every participant can find/correct/export a note unaided. These are small-sample decision rules, not population effect estimates. Conduct blinded qualitative review of “felt understood” versus merely warm phrasing.

**Days 8–14:** optional consented parent-only concierge pilot using a separately approved privacy process and verified provider child-data eligibility; stay synthetic if that gate is unresolved. No daily journaling requirement. Test whether at least 5/10 return voluntarily on two distinct days and 4/10 describe a specific insight or better-fitting response that the comparator did not deliver. Record opt-outs and harms. Probe price with an honest paid-pilot offer after value, not a fake paywall. No claims of validated child health benefits.

**Go:** superior parent utility, tolerable burden and correction safety; pursue the preferred shape. **Reshape:** notebook/export wins but chat does not → portability-first companion. **Stop:** generic assistant performs similarly, returns require nagging, or parent reports become labels. Do not rationalize feature expansion as solving failed demand.

## Build only after a gate passes

Before any real-child-data processing: verify the exact provider under-18 guidance and zero-data-retention eligibility for the intended route. The parent research team flags an under-13 ZDR requirement; `store:false`, SIWC or an OAuth token are not evidence of ZDR approval. Keep prototypes synthetic until scope and permissions are resolved.

Week 1: reviewed-note domain with stable IDs, versioned consent, tombstones, provenance and context; tenant tests; ephemeral conversation adapter; deletion/export contract; no legacy schema mutation. Week 2: source-reviewed suggestion rules, prompt evaluation and correction UX; capped model adapter; telemetry containing event counts, never child/chat text. Week 3: opted-in minimal reminder with idempotency and mute; encrypted notes and verified deletion across caches/checkpoints/backups. Week 4: approved restricted pilot with operational safety and support process. Native iOS and connectors follow retention evidence, not precede it.

Cost is a gate: measure tokens and latency per completed useful episode, cap daily/per-family spend, include hosting/support/expert-review cost. ChatGPT-plan eligibility is a fallback option, not the business model. Pricing and current competition remain the parent research team's responsibility.

## Unresolved launch questions

Former partnership asset rights/content authorship; consumer brand clearance; scientific claim review; privacy/child-data legal basis; handling parent custody/access disputes; connector platform policies and approval; SIWC commercial eligibility; actual willingness to pay and narrow target moment. This memo is a research recommendation, not a rights, regulatory or market clearance.

## External research handoff

The parent research team owns final current-market, science, auth and integration verification. Incoming verified sources/policy limits should be copied into `external-research.md` before build decisions. A reusable deep-research prompt on whether a learned child profile creates incremental parent value belongs in `child-understanding-research-prompt.md`; it is being prepared independently. Do not treat this memo’s competitor summaries as product-quality verification.

Preliminary official source routes supplied by parent research: [OpenAI SIWC quickstart](https://developers.openai.com/siwc/quickstart), [local open-source token sharing](https://developers.openai.com/siwc/token-sharing-open-source), [Hatley](https://hatley.ai), [Common Sense age 0–8 media study](https://www.commonsensemedia.org/research/the-common-sense-census-media-use-by-kids-zero-to-eight-2025). These links are handoff pointers, not independently verified in this local implementation task. Integration policy research flags PHI and sensitive inference limits; verify each platform policy before even synthetic connector development, and keep health/neurodevelopmental notes excluded.
