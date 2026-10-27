# S1 — DECISION MEMO: How kid-related information gets into the app

**Analyst:** S1 · **Date:** 2026-08-21 · **Status:** decision-ready
**Question:** How should kid-related information reach the app? Four candidate architectures,
scored, with a decision rule.

**Revision note.** This memo was drafted against a two-option framing (Gmail OAuth vs. a
"Trojan horse" address registered with schools). `raw/P12-aggregation-email.md` landed
mid-draft and falsified the second option as specified. The memo has been restructured around
**four** options. Where P12 and my own commissioned research disagree, I say so and adjudicate.

---

## 0. The options, and the bottom line

| | Option | One-line definition |
|---|---|---|
| **A** | Gmail OAuth | `gmail.readonly` on the parent's Google account. **Built** (§ 1.1). |
| **B** | Registered address | Parent registers our address as a contact **at each school/provider**. |
| **B′** | **Parent-side auto-forward** | Parent sets **one forwarding rule in their own mailbox** → our address. |
| **C** | **A + B′** | Both, sequenced, with B′ as the default and A as an earned upgrade. |

**Recommendation: ship B′ now. Reject B outright. Pursue A only if it clears a four-part gate
(§ 11.2), and never on the critical path.** On the § 10 scoring B′ alone (69.5/77.5) and C (67.5)
are equivalent, and both dominate A (35.0) and B (25.5) — almost all of C's value is B′'s value.

Three facts carry the decision, and each is individually close to sufficient:

1. **Option A cannot leave beta.** An unverified restricted-scope app is capped at **100 users
   over the GCP project's entire lifetime, non-resettable** (P12 #25), and the "Testing" holding
   pattern is unusable because **test-user authorizations expire after 7 days**, taking the refresh
   token with them — a Gmail integration in Testing breaks for every user, weekly
   ([Google, manage app audience](https://support.google.com/cloud/answer/15549945);
   [OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)). There is no holding
   pattern. A is not "working" — it is running out a clock.
2. **Option B is blocked where it matters and contractually hostile.** P12's matrix: **6–7 BLOCKED
   vs. 5 clean wins**, and the blocked set contains ParentSquare and Infinite Campus — the two
   largest school install bases. Several platforms' terms **run against the school, not the
   parent**, so a violation notice lands on the parent's district. Reject.
3. **Option B′ has none of those problems.** It operates downstream of every platform, needs no
   platform cooperation, violates **no ToS in P12's entire matrix**, keeps the FERPA chain severed
   at the parent exactly as OAuth does, costs **$0–20/month with no reviewer**, and — per § 1.3 —
   sits on an extraction pipeline that is already built and deployed.

The most important correction to my own earlier draft: I had treated the alternative to OAuth as
*manual per-message forwarding*, and priced its weakness as "per-email opt-in, therefore worse than
set-and-forget." **B′ is a persistent mailbox rule, so it is also set-and-forget.** That was the
main thing Option A uniquely bought, and B′ takes most of it back. The conclusion below is
correspondingly stronger than the one I started with.

---
## 1. What is actually built today (code audit)

I read the code. Both options are further along than the roadmap implies, but in opposite halves.

### 1.1 Option A — built, and unshippable

| Component | File | State |
|---|---|---|
| Scope declaration | `mvp-backend/app/oauth/google_flow.py:34` | `SCOPE_FOR_KIND["email"] = "https://www.googleapis.com/auth/gmail.readonly"`. Line 32 comment: *"email = restricted (needs verification + CASA)"*. Plus `BASE_SCOPES = ["openid", ".../userinfo.email"]` and `calendar.events` for the calendar kind. |
| OAuth flow | `mvp-backend/app/oauth/google_flow.py`, `mvp-backend/app/oauth/__init__.py` | Complete: PKCE verifier carried in a signed `state`, stateless callback, token logging pinned to WARNING so refresh tokens never hit Railway logs. Module docstring: *"gated behind verification for the restricted gmail.readonly scope; **until then only test users can complete it**."* |
| Gmail API adapter | `mvp-backend/app/integrations/google.py:8` | `GoogleEmailProvider` written against documented API shapes but flagged *"UNTESTED end-to-end pending the OAuth flow + Google verification (R3)"*. Unit-tested only with an injected fake. |
| Token storage | `mvp-backend/app/duckdb_storage.py:985` | `integration_accounts` table — `encrypted_refresh_token`, `scopes`, `status`, unique on `(user_id, provider, kind)`. |
| Sync unit of work | `mvp-backend/app/email_sync/sync.py` | See § 1.2 — narrower than "read the inbox". |
| Daily daemon | `mvp-backend/app/email_sync/worker.py` | Claim → run → mark, plus a once-daily schedule tick at an operator-set hour. **Defaults to `{"enabled": False}`** (`email_sync/router.py`, `_DEFAULT_SCHEDULE`). |
| Operator controls | `mvp-backend/app/email_sync/router.py` | `/cms/email-sync/{config,run,runs}`, all behind `require_admin_token`. **There is no user-facing "sync my email now" control anywhere** — only an operator can force a run. |
| Connect UI | `mvp/MVP/IntegrationsSettingsView.swift` | "Connect Gmail & Calendar" button → `ASWebAuthenticationSession`. Copy: *"Read-only — nothing is sent on your behalf, and you can disconnect anytime."* |
| Beta allowlist | `mvp/MVP/IntegrationsSettingsView.swift` (connect card footnote) | **The allowlist is a sentence, not code**: *"While in beta, only approved Google accounts can connect."* No allowlist logic exists in the repo — enforcement lives entirely in the Google Cloud Console OAuth test-user list. That matters: the gate is external, and it is Google's to move. |

### 1.2 The critical, under-appreciated limitation of what is built

`email_sync/sync.py` does **not** read the parent's inbox. It:

1. Loads activities whose status is in `app.cos.lifecycle.WATCHED` (registered/confirmed).
2. Extracts the `contact.email` of each, and its domain, as match tokens.
3. Builds a Gmail query `from:(<those addresses/domains>) newer_than:14d`, `max_results=50`.
4. If no registered activity carries a contact email, it returns zero with the note
   *"no registered camps with a contact email to search"*.

**Consequence: the built Gmail integration cannot discover anything new.** It can only enrich
activities the parent has *already* manually entered, with a contact email attached, within a
14-day window. The flagship "your inbox fills your planner" experience — the thing CASA is
allegedly gating — **is not what is behind the gate.** What is behind the gate is a 14-day
enrichment sweep over senders the parent already told us about. This substantially lowers the
value of clearing CASA on the current implementation, and it is the single most decision-relevant
fact in this audit.

It is also, to be fair, an unusually *good* privacy posture — a sender-scoped query rather than a
full-mailbox read. Google's restricted-scope classification does not care: `gmail.readonly` is
restricted regardless of how narrowly you query with it.

### 1.3 The inbound pipe (Options B and B′) — the pipe is 0%, the brain is ~85%

`grep -rni "mailgun|postmark|sendgrid|ses|cloudflare|inbound_email"` over `mvp-backend/app`
returns **no matches**. There is no inbound-email infrastructure of any kind.

But the expensive half already exists and is deployed:

- **`mvp-backend/app/duckdb_storage.py:949`** — `ingest_artifacts.source` is already enumerated
  `paste|imessage|photo|screenshot|pdf|gmail|**forward**`. The schema anticipated this path.
- **`mvp-backend/app/ingest/router.py`** — `IngestTextRequest.source` default comment is literally
  `# paste|imessage|forward|gmail`.
- **`mvp-backend/app/ingest/extract.py`** — the 2-stage extractor: LLM structured-output →
  deterministic `materialize()`. Prompt-injection hardened with `<<<INGEST>>>` delimiters and an
  explicit `_SECURITY` preamble, *because forwarded email was always assumed to be attacker-
  influenceable*. Handles the many-objects school case (`materialize_all`, cap-and-park), locked
  by `mvp-backend/tests/test_school_ingest.py`.
- **`mvp-backend/app/email_sync/sync.py`** calls `ingest_extract.extract_from_text(...)` then
  `ingest_extract.materialize(...)` — **the exact same two functions** `POST /ingest/text` calls.
  The pipeline is already source-agnostic.

**What the inbound path still needs:** an address-allocation table, an inbound webhook route, a
sender→user mapping, SPF/DKIM/DMARC verification on the inbound envelope, and a UI surface that
shows and copies the address. Estimate **1–2 engineer-weeks**, versus Option A's remaining work
which is not engineering at all.

### 1.4 Today's actual manual capture path, for comparison

`mvp/MVP/IngestView.swift` offers Paste (a `TextEditor`) or Photo (`PhotosPicker`, no camera).
There is **no iOS share extension** (`grep NSExtension` over the pbxproj: no matches). So a parent
who wants to capture a camp email today must: leave Mail → open the app → Planner → open the
Ingest sheet → Paste tab → paste → submit. Option B′ replaces that with *nothing at all* — a
standing mailbox rule delivers it without the parent touching anything. Hold that against § 6.3's causal friction evidence.

---

## 2. Decision criteria

Weights reflect this product's actual situation: pre-revenue, closed beta, solo-developer capacity,
and — per `P9-complexity.md` — an onboarding funnel already rated a **SEVERE OUTLIER on five
separate measures**. That last fact promotes *onboarding friction* to the highest weight; this
product cannot afford to add setup steps, whatever the coverage payoff.

| # | Criterion | Weight |
|---|---|---|
| C1 | Time-to-broad-availability (can it ship to a non-allowlisted user?) | **High** |
| C2 | Compliance cost + recurring burden | **High** |
| C3 | Onboarding friction (steps to first value) | **Highest** |
| C4 | Coverage (what it can see) | High |
| C5 | Reliability / silent-failure modes | Medium-High |
| C6 | Privacy posture, parent trust, legal exposure | Medium-High |
| C7 | Running cost at scale | Low |
| C8 | Multi-adult / second parent | Medium |
| C9 | Addressable users | High |

---

## 3. The CASA gate, quantified

I commissioned primary research on this in parallel with P12; the two agree on the substance and
each supplies facts the other missed. Both are cited.

**Scope classification — no way around it.** `gmail.readonly` is Restricted
([Gmail scopes](https://developers.google.com/gmail/api/auth/scopes)). So is `gmail.metadata`
("headers, but not the email body") — and P12 #20 confirms **no Gmail body-reading scope escapes
restricted classification**, which kills the circulating "just use `gmail.modify`" workaround.
(P12's WEAK SIGNAL correctly flags the Orbis engineering blog's contrary claim as factually wrong.)
Restricted scope + *"the ability to access data from or through a third-party server"* triggers a
mandatory independent security assessment
([restricted-scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification)).
Our FastAPI backend is squarely a third-party server, so the exemption some developers read into
that clause does not apply to us.

**Cost — a range, plus a risk P12 did not surface.**

| Source | Figure | Status |
|---|---|---|
| Google's own fee | **$0** — *"Google does not charge the developer any fees for security assessment"* ([verification FAQ](https://support.google.com/cloud/answer/13463817)) | Documented |
| Lab prices (P12 #24) | **$675 (Tier 2) – $4,500 (Tier 3)**/yr; Orbis reports passing Tier 2 for $540 after self-remediating with free scanners | Reported, current |
| The "$15,000+" figure | Traces to a **2019 Ask HN thread predating CASA** and to Google fee language **removed from its docs between June 2022 and June 2023** | **Stale — do not cite.** P12 independently reached the same verdict |

**The risk neither the $675 figure nor P12 accounts for:** the developer does not choose the tier.
*"The framework users (Google…) and not the application developer calculate and determine which
assurance level is required"* ([casa-tiering](https://appdefensealliance.dev/casa/casa-tiering)).
Worse, Tier 2 is **entry-by-invitation** — *"you must receive a notification from the Framework User
indicating that you are required to complete a CASA assessment"*
([casa-start](https://appdefensealliance.dev/casa/casa-start)) — and a developer who initiates their
own assessment gets **Tier 3 only** ([casa-self-start](https://appdefensealliance.dev/casa/casa-self-start)).
Tier 3 means an authorized lab tests *"the application, the application deployment infrastructure and
any user data storage location"* — i.e. **annual read-only auditor access to production**, which for
a database of families' children is a meaningful thing to grant. **Plan for $4,500/yr and a
production audit, not $675.** Also: the free self-scan was **deprecated/eliminated in May 2024**
(ADA tier-2 overview; P12 #23), though Google's FAQ still contains stale "free tier 2" text — P12
flags the contradiction and I confirm it is unresolved.

**Timeline.** Google's own estimates: restricted scopes **6 weeks**, *"not guaranteed"*; the
restricted-scope page hedges to *"potentially several weeks"* (verification FAQ). That clock covers
**Google's review only** — it excludes the CASA engagement (lab scheduling, testing, remediation,
Letter of Assessment), which is bilateral and unbounded. P12 puts realistic end-to-end at **6 weeks
to several months**. Nobody publishes a committed date.

**Annual, forever.** *"Apps must be reverified for compliance and complete a security assessment
**at least every 12 months** after your assessor's LOA approval date."* A full re-test every year
regardless of whether anything changed. This is a perpetual tax on a solo developer, not a one-off.

**The decisive constraint — there is no holding pattern.** Two limits interlock:

- **Testing status:** up to 100 hand-listed test users, and *"authorizations by a test user will
  expire **seven days** from the time of consent."* The refresh token dies with it. **A Gmail
  integration parked in Testing breaks for every user, every week.** This is not a viable beta
  posture; it is a demo posture.
- **Production, unverified:** *"100 new users in total"* — a **lifetime** cap on the GCP project
  that *"cannot be reset"* ([answer/7454865](https://support.google.com/cloud/answer/7454865)).
  P12 #25 reaches the same conclusion and calls it decisive. I agree.

**And if verification is never completed or fails:** *"users' access to the unapproved sensitive or
restricted scopes in the app via OAuth will no longer work."* Already-connected beta users are
**not grandfathered** — they lose the scope.

**Can a solo developer clear it?** Procedurally, yes: no legal entity, named security officer, or
minimum company size is required. The gates are all satisfiable alone — Search Console domain
verification, a homepage that *"cannot be only a login page,"* a privacy policy on the same domain,
and an English demo video showing the complete consent flow
([verification requirements](https://support.google.com/cloud/answer/13464321)). The real blocker is
commercial and recurring, not procedural: an annual lab engagement plus production audit access.

**One unresolved policy risk, and for this product it is the scariest item.** P12 #27 flags an
open question about whether an LLM pipeline over Gmail content complies with Google's **Limited Use**
requirement at all. Our `mvp-backend/app/ingest/extract.py` sends message bodies to an OpenAI model.
That is exactly the pattern in question. This should be resolved *before* spending on a lab, not
after.

**The comparison that ends the section.** Inbound mail: **$0–20/month, no reviewer, no approval, no
annual re-test, no user cap** (P12 #30). Microsoft Graph `Mail.Read` on consumer Outlook: **no admin
consent, no CASA analogue, free publisher verification** (P12 #28). Apple: **a flat no** — no iCloud
Mail API, only IMAP with an app-specific password (P12 #29), product-hostile and in tension with
iCloud ToS for server-side use.

---

## 4. Addressable users — who does Option A even serve?

Established finding, refined by my commissioned research: **do not use Litmus to size mailbox
providers.** Litmus measures the *rendering client's user agent*, so every message opened in iOS
Mail counts as "Apple" regardless of which mailbox it lives in. The gap is enormous — Apple is
**62.3% of opens** (Litmus, July 2026, worldwide) versus **3.6% of mailboxes** (Validity 2026
Benchmark, global) versus **17% of US adults using iCloud Mail** (Statista Consumer Insights,
n=1,249 US, reported Apr 2025). On the order of 90%+ of "Apple" opens are Apple's app reading
someone else's mailbox.

**There is no clean US number for "primary personal email is Gmail."** The defensible bound: between
~40% (AtData US domain mix — but 2016 and stale) and 75% (Statista *usage*, multi-select, an upper
bound). **Plan on roughly half of US parents on Gmail**, with iCloud/Outlook/Yahoo/ISP tails each in
the 5–20% range. Any single-number claim circulating on stat-aggregator blogs is untraceable.

**So Option A, fully verified and working perfectly, serves about half the market.** B′ serves all
of it. That is a permanent, structural ceiling on A that no amount of CASA spending moves.

Worth noting on the demand side: schools do reach parents by email — **72% of US families favor
email** for school communication (SchoolStatus 2024, n=1,050, Tier C) — and US parents of
school-age children receive **~4 kid/school emails a day (80+/month)** with **62% having missed an
important event or detail** (Yahoo/Censuswide, June 2024, n=2,004 US parents, Tier C; already known
per the brief). The inbox is the right target. The question is only how we get to it.

---
## 5. Option B — register our address with providers: **REJECT**

I was asked to confront this option's registration burden without softening it. P12's evidence goes
further than burden: the option does not work where it needs to, and where it does work it is
contractually and legally hostile. I recommend rejecting it as a *requirement* and keeping only a
narrow, opt-in residue (§ 5.4).

### 5.1 It is blocked on the platforms that matter

P12's feasibility matrix, scored for the register-our-address path specifically:

| Verdict | Platforms |
|---|---|
| **WORKS (5)** | PowerSchool (cleanest — "Additional Notification Emails," comma-separated, parent-controlled), Remind, TeamSnap, SportsEngine, Sawyer |
| PARTIAL / UNKNOWN / gated (3) | Blackbaud (newsletters only, low value), Jumbula (undetermined), Brightwheel (provider must add it) |
| **BLOCKED (6–7)** | **ParentSquare** (SIS-gated; *"contact your school office"*; **nightly sync overwrites parent edits**), **Infinite Campus** (district-gated, approval queue; grades/attendance **push-only at every configuration**), ClassDojo (email *is* the login), Seesaw (*"one email address at a time"*), TalkingPoints (phone-number login; a parent **cannot cause a single email** to reach an address of their choosing), BAND, GameChanger |

**The five wins skew to sports and one SIS. The blocked set contains the two largest school install
bases.** Since `P5-appointments.md`-class school activity is where the volume originates, the option
fails precisely at its stated purpose.

And even where registration is mechanically possible, the platform default fights it: P12 #18 finds
**ClassDojo, Remind and Seesaw silently disable email the moment the parent installs the app** —
which is how essentially every parent uses them. GameChanger inverts it, mailing only addresses that
have *never* registered. So "WORKS" often means "works until the parent installs the app."

### 5.2 It is contractually hostile, and the blast radius lands on the district

- **Seesaw** flatly prohibits using Service content *"for any machine learning and/or artificial
  intelligence training or development purposes."* That points directly at an LLM extraction pipeline.
- **ClassDojo** bans automated access, restricts to personal non-commercial use, and forbids
  supporting *"products or services in competition with ClassDojo."*
- **GameChanger** names the pattern: you *"may not share it with a third party service so they can
  access your Account,"* with stated escalation to legal action.
- **ParentSquare and Blackbaud**: the contract's "You" is **the school**. A violation notice lands on
  the parent's district, not on us.
- **Infinite Campus** has **no parent-facing ToS at all** — a different district AUP per user,
  unknowable at scale. That is not permission; it is unquantifiable risk.

Shipping a consumer feature whose failure mode is *"your child's school district receives a terms
violation notice"* is not acceptable at any coverage payoff. This alone is disqualifying.

### 5.3 It is the riskier FERPA architecture — the opposite of the intuition

Counterintuitive and important (P12 #52–#55). Neither approach makes us a FERPA-regulated entity.
But:

- **OAuth / B′:** the disclosure chain is **expressly severed at the parent** by 34 CFR §99.31(a)(12)
  and §99.33(c). The parent received the mail; what they do with their own mailbox is their business.
- **B (registration):** plausibly attaches §99.33(a)'s **redisclosure restriction to us**, exposes us
  to direct state SPPO investigation, and carries a **five-year district access ban** as a sanction.
  **Illinois SOPPA §26(2)** arguably forces an actual school contract for this path specifically.

**Open legal question, flagged not resolved:** whether §99.30 parental consent displaces §99.33(a).
P12 could not resolve it and neither can I. **This needs counsel before anyone builds B.** I note
separately that P12 #54 finds the state student-privacy trigger is **marketing, not contracting** —
positioning the product as *"manage your child's school communications"* invites the argument;
general-audience family positioning avoids it. That is a copywriting decision with legal
consequences and it should be made deliberately, whichever option ships.

### 5.4 The registration burden, for completeness

Even setting aside § 5.1–5.3, the burden is what I estimated before P12 arrived, and P12's matrix
makes it worse rather than better. Building from `P4-extracurriculars.md` and `P3-camps.md`:
2 kids × 2.01 sports each × **1.86 organizational settings per sport** (Aspen/Utah State 2024,
Tier B, P4 #9 — each setting is *"a separate registration, roster, comms channel and calendar"*)
≈ **7–8 sports registrations**, plus 2 schools, 3–5 camp providers, and 1–3 music/arts providers =
**13–18 separate registration actions**. Cross-check: Cornerstone/Edsby 2025 (**n=125, vendor,
North American not US, non-probability, Tier C — directional only**, and P12 corrects P4's carry of
this figure on both n and population) finds 44% of parents manage 7–9 apps *per child*, i.e. 14–18
destinations for two kids. Two methods, same range.

Against that: the strongest causal evidence in the whole corpus says small increments of setup
effort suppress the behavior outright — raising the physical cost of setting a reminder cut
reminder-setting by **0.29–0.50 per trial (dz 0.71–1.29)**, Psychon Bull Rev / PMC11103908, n=52 × 2,
Tier A. And the market's most focused competitor agrees: P12 #40 finds **Sense uses a single shared
address that structurally cannot be registered with a school**, and its own guidance is *"turn on
email in each app, then forward."* **A competitor with every incentive to find this shortcut has
examined it and declined to take it.**

**Verdict: REJECT B as a requirement.** Keep one narrow residue: for the five clean-win platforms —
above all **PowerSchool's "Additional Notification Emails," which is an official product feature
raising no ToS question** — offer registration as an **opt-in power-user upgrade**, surfaced only
after the parent is already succeeding with B′. Never depend on it, never put it in onboarding.

---

## 6. Option B′ — the parent-side auto-forward rule: the real candidate

**Mechanism:** the parent creates one filter/forwarding rule in their own mailbox (Gmail, Outlook,
iCloud, Yahoo) pointing at their family's address on our domain. Set once, per mailbox.

### 6.1 Why it dominates B on every axis

| | B (register with providers) | B′ (parent-side rule) |
|---|---|---|
| Platform cooperation | Required; **6–7 BLOCKED** | **None** — operates downstream of every platform |
| Coverage of email-borne content | Partial, skewed to sports | **~100% of what reaches that mailbox** |
| ToS | Hostile on 4+; blast radius on the district | **Violates no ToS in P12's entire matrix** |
| FERPA | Riskier — plausible §99.33(a) attachment, 5-yr ban | **Chain severed at the parent**, same as OAuth |
| Setup actions | **13–18**, several not self-serve | **One per mailbox** |
| Revocable by parent | Partly (nightly SIS overwrite) | **Fully, unilaterally, any time** |
| Works on iOS and Android | Yes | **Identically** |

### 6.2 The setup friction is lower than it looks — a real design unlock

Gmail's forwarding setup is desktop-web-only and requires a verification handshake. But **the
confirmation link lands in *our* inbox, because we own the destination** (P12 #31). We can auto-click
it and collapse the hardest step. P12 calls this *"a genuine design unlock hiding in a documentation
footnote,"* and I agree — it converts the setup from a copy-paste chore into something close to
one-tap.

Two honest caveats. First, the desktop-web requirement is real: a parent who only ever touches Gmail
on a phone has a genuine obstacle, and this is the single biggest execution risk in B′. Second,
**Microsoft 365 disables external forwarding by default** (P12 #32) — which matters for the parent
reading school mail on a work account, and is exactly the population B′ was supposed to rescue.
Neither is fatal; both need design attention.

### 6.3 It is the mechanism the market has already validated

- `M1-organizers.md`: **"capture-without-typing (photo / email forwarding) is the #1 delight
  driver"** — a *switching* reason, where voice is only a nice-to-have. Verbatim (Jam, 5★): *"I love
  the fact that I can just forward emails with event details to Jam... **I hate having to sit there
  typing all my events into my calendar**."*
- `M2-ai-assistants.md`: **eight competitors accept email forwarding as a primary intake.**
  **Schoolcase charges $9/month for forwarding-to-a-private-inbox and nothing else.** Sense's
  positioning is the whole thesis: *"The right test is not 'is the chatbot smart?' It is **can I
  forward one email and forget it**."*
- P12 #42, an original count across **4,193 reviews**, is bimodal and instructive: where the address
  **is** the product, ~1 in 11 reviewers names it unprompted as their favourite feature, all
  five-star; where it is a settings-screen utility, **0 of 3,917** mainstream Cozi/Todoist/Evernote
  reviewers mention it once. **The address has to be the front door, not a settings toggle.** That is
  a direct instruction for our onboarding.
- P12 #45: it survives conditions OAuth cannot — locked-down work accounts, and parents who
  explicitly refuse inbox access.

### 6.4 The failure mode that must be designed against

P12 #44 is the most important operational finding in this memo. The very property that makes
forwarding delightful — *"once I forwarded it, it was out of my head"* — makes **silent failure
invisible**. A Skylight user went **eighteen months and multiple missed events** before noticing,
*despite* receiving confirmation emails with an Undo button. **Confirmation emails are not a
sufficient feedback loop.**

Required in v1, not v2:

1. **Positive liveness signalling** — a visible *"last message received N hours ago"* on Home.
2. **A quiet-stream nag** — proactive alert when a family's stream goes silent for longer than their
   established baseline.
3. **A non-email fallback channel** — Expensify ships one because Proofpoint silently eats forwarded
   mail (P12 #48).
4. **Deliverability hygiene** — forwarding **breaks DMARC by protocol** (P12 #33). We must publish
   SPF/DKIM/DMARC on the ingest domain, implement ARC, and **never reject inbound on DMARC failure**,
   or we will silently drop exactly the school mail we exist to parse.
5. **Copy Ohai's move** (P12 #39): *"every message scanned is also forwarded to your regular inbox"* —
   this removes the *"will I stop seeing my own mail?"* objection at a stroke.

### 6.5 Address design

Per the established findings: a dedicated receiving subdomain with a **domain-level catch-all and
opaque local parts** (not one alias/rule per family — SES caps at 200 rules × 500 recipients,
Cloudflare at 200/200). **No plus-addressing** — school and camp forms routinely reject "+". Cost at
50,000 families × 20 emails/month: **~$5/mo on Cloudflare Email Workers**, ~$135 on SES,
~$1,290 on Postmark. Cost is not a decision input.

---
## 7. The link-only question — verdict: **not fatal, and better than assumed**

This was flagged as the risk that could void the whole approach: if platforms email *"you have a
new message, sign in to read,"* the forwarded envelope carries nothing. I had this verified
independently of P12, from vendor help documentation only. **The two investigations agree, and the
answer is favourable.**

| Platform | Content in the email body? | Attachments | Source |
|---|---|---|---|
| **ClassDojo** | **FULL** — *"Email delivery will include the **full text** of the announcement with images displayed in-line"* | In-line *"where possible"* | [announcements FAQ](https://help.classdojo.com/hc/en-us/articles/47235978135565-School-Announcements-FAQ) |
| **Infinite Campus** | **FULL** via Message Builder — *"Message Body… the text contained in the message"* | **Email only** — *"File attachments are **not** sent to Messenger Inbox or Portal Inbox. File attachments are only received in email."* | [message builder](https://kb.infinitecampus.com/help/message-builder) |
| **TeamSnap** | Direct to the parent's own mail client, no login gate | **True attachments** — *"PDFs, images, schedules… recipients can view directly from the email"* | [mass message](https://helpme-teams.teamsnap.com/article/2777-how-to-send-a-mass-message) |
| **PowerSchool** | Real content — grades, assignments, attendance, balances | Undetermined | [email notifications](https://ps.powerschool-docs.com/pssis-student-parent/latest/email-notifications) |
| **Remind** | Full content, two-way by email (voice clips/surveys link-only) | Behind login, revocable links | [notif prefs](https://help.remind.com/hc/en-us/articles/206430755) |
| **Schoology** | Digest carries full content | Undetermined | [parent settings](https://uc.powerschool-docs.com/en/schoology/latest/personal-account-parents-settings) |
| **Seesaw** | **LINK-ONLY** — digest recipients *"will **not** see message content"* | View-in-app | [notifications](https://help.seesaw.me/hc/en-us/articles/203729375) |
| **ParentSquare** | **UNRESOLVED** — help center is login-gated. P12 reports *body, but Digest (daily 6pm summary) is the default for new accounts* | Links, not attachments | P12; [help center](https://www.parentsquare.com/resources/help-center/) |
| **Blackbaud** | Weakest — Blackbaud instructs schools that templates *"should be generic… Placeholders are used"* | — | P12 |

**Verdict.** Full content in the email body is **common, not rare**. Seesaw is the clean
counter-example; Blackbaud is weak by design; ParentSquare is the one genuinely unresolved gap and
it matters most, given its 22M-student install base — its *digest-by-default* posture is the real
risk there, not link-only per se, and a digest is a content-poor artifact even when it is not a bare
link.

Two findings sharpen this in B′'s favour:

- **Infinite Campus is the asymmetry worth banking:** attachments exist **only in email, never in
  the portal.** There, email is not a convenience copy — it is load-bearing, and a parent who misses
  it has no in-app fallback for the flyer. (Note a partial tension with P12, which reports IC grades
  and attendance as push-only at every configuration. Both are consistent: different message classes
  behave differently. Neither report contradicts the other on Message Builder email.)
- **The real content-killer is not link-only, it is app-install:** P12 #18 finds ClassDojo, Remind
  and Seesaw **silently disable email once the parent installs the app.** That degrades A, B and B′
  *equally* — it is a channel-existence problem, not an architecture problem, and no option in this
  memo solves it. It does, however, argue for our onboarding to include one line of guidance
  ("keep email notifications on in your school app"), which is what Sense already tells its users.

**Provenance caveat, stated because it affects confidence:** Seesaw's live help center 403s
automated fetchers, so those quotes came from archived captures of the vendor's own URLs — accurate
as of capture, worth confirming in a browser. ParentSquare's is login-gated and unresolved. Do not
present the ParentSquare row as settled.

---

## 8. Option C — A + B′ together

C is the right *destination*. But "both" is only a strategy with a sequence and a trigger, or it is
indecision wearing a strategy costume. § 11 supplies both.

### 8.1 Coverage union — source by source

The data will not support percentages. No study partitions a family's kid-related information by
arrival channel; P12 searched for a parent-side login count and **found none**, and NHES:2023 —
the federal instrument that should answer it — **contains no such item at all**. Anyone quoting a
"% of family information captured" figure is fabricating. So: a source table.

| Information source | A alone | B′ alone | Union (C) | Who wins |
|---|---|---|---|---|
| Kid mail in the parent's **Gmail** | ✅ | ✅ | ✅ | tie |
| **The history from before signup** | ✅ | ❌ (nothing was forwarded then) | ✅ | **A only — its one exclusive capability** |
| Mail to **iCloud / Outlook / Yahoo** | ❌ | ✅ | ✅ | **B′ only** |
| Mail to a **work account** | ❌ | ✅ (unless M365 blocks external forwarding, P12 #32) | ✅ | **B′ mostly** |
| Mail to the **second parent** | ❌ | ✅ — they set their own rule, no account | ✅ | **B′ only** |
| Mail to a **grandparent / nanny** | ❌ | ✅ | ✅ | **B′ only** |
| From an account the parent **refuses to connect** | ❌ | ✅ (P12 #45) | ✅ | **B′ only** |
| A one-off the parent **chooses** to send | ❌ | ✅ (manual forward to the same address) | ✅ | **B′ only** |
| Paper flyer, SMS, push-only, Facebook, municipal PDF | ❌ | ❌ | ❌ | **neither — § 8.2** |

**Bounding the overlap honestly:** for a single-parent, single-Gmail household, A is close to a
superset of B′ and C's marginal gain is modest. The union grows exactly as the household departs
that profile — a second adult, a non-Gmail mailbox, a work address. Since multi-adult households are
the norm, **the union is materially larger than either alone for most families.** They are
complements, not substitutes.

The decisive asymmetry: **retroactive history is A's only genuinely exclusive capability, and it is
a one-time benefit at signup.** Everything else A does, B′ also does — passively, once the rule is
set. Conversely, everything B′ does that A cannot, **A can never do, at any price, after any amount
of verification.**

### 8.2 The ceiling neither option clears

`M3-discovery.md` is emphatic that the highest-value datum in this product's core job —
**registration-open dates** — is *"the least-structured data in this entire space… they live in a
PDF, a Facebook post, last year's page that hasn't been updated, or nowhere at all until a provider
decides,"* across ~19,000 US municipalities' rec portals, YMCAs, libraries and churches, *"with no
syndication feed. Nobody is ever going to integrate them."*

**Neither A nor B′ sees any of it.** Email is an excellent *enrichment and follow-through*
mechanism and a poor *discovery* mechanism. That is an argument for spending as little as possible
to get email working — which is itself an argument for B′ over A.

### 8.3 Privacy segmentation as a conversion lever

This is the strongest argument for C. One correction first, per the brief's honesty bar.

**Correction.** The "Gen X is the hardest consent case, 56% object to data collection" framing
overstates its source. `P10-generations.md` #20 says 56% of **50+** adults find **social-media
personalization analysis** unacceptable vs. 41% of under-50s — Pew, n=5,101, ATP Wave 127,
**fielded May 15–21 2023 and flagged dated in P10 itself**. Not about data collection generally, not
about email, three years old. Directionally useful; not load-bearing.

**The solid number** is `P11-ai-parenting.md` #18: **84% of US parents are concerned about AI
misusing young people's data**; 81% about collection without their knowledge (Common Sense Media /
LRP + Echelon, 2026, Tier B).

**On OAuth consent drop-off for restricted scopes: no citable rate exists.** I looked; P12 looked
independently and reached the same conclusion, adding that **no funnel comparison of forwarding vs.
OAuth onboarding exists in public** (searched Lenny's, Reforge, First Round, YC, Mixpanel,
Amplitude) and **no vendor publishes an inbound-address activation rate.** Put no number on this.

What the corpus *does* carry is revealed preference, and it is unambiguous:

> **"I don't want it trolling through my emails offering nonsense appointments. I will NEVER pay for
> this feature."** — Cozi, 1★, 2025-12-12

`M1-organizers.md` annotates that review, unprompted, as ***"direct read on our Gmail-ingestion
feature."*** A competitor shipped Option A into an installed base of millions and generated a paying
customer refusing to pay. Set beside the same corpus's reaction to the other mechanism — *"I love
the fact that I can just forward emails with event details to Jam"* (5★) — the contrast is stark:
**same job, same category, opposite emotional valence.** One mechanism reads as surveillance, the
other as delegation.

That contrast is, I agree, the single most important piece of evidence in this memo, and it licenses
a stronger claim than "B′ is an acceptable fallback": **"we never read your inbox" is a marketing
asset.** It is a differentiator against Cozi's own shipped feature, available free, today, without
anyone's permission.

I cannot size the refuse-OAuth-but-accept-forwarding segment — no data supports a number, and P12
confirms **no survey has ever asked a US parent about comfort with third-party school-comms access**.
But the segment is certainly non-trivial, and **C converts it at zero incremental acquisition cost**:
the refuser is already in the funnel, and B′ is what keeps them.

### 8.4 The second-parent connection — B′ is a *participation* feature

`M4-coparenting.md` validates the hypothesis on its own evidence:

- The dominant concrete refusal is **"the ex won't *pay*"** — *"the single most common concrete
  refusal in the corpus"* — **not** "the ex won't install."
- M4's own verdict on the strategy's mitigation (invite the second parent *"via a calendar invite
  plus a forwarding email, never an app install"*): it **"directly and correctly dodges failure mode
  (a), which is the biggest one."**
- Mechanism evidence: **AppClose accumulated 1M+ Android installs while free**, and reviewers say so
  explicitly — *"I chose it because it was free and accessible for both parents."* **Free/no-install
  is demonstrably the adoption mechanism in this category.**
- The incumbents fail here in their own words: SportsEngine states there is *"no way for divorced
  parents to have separate accounts/logins/passwords connected to the same children… **We suggest
  the parents get a shared free email account.**"*

That last quote is the product spec. **A per-family inbound address IS the shared free email account,
done properly** — and it is the implementing mechanism for the canonical strategy's biggest
unfalsified assumption. **Under Option A alone that assumption has no mechanism at all:** OAuth
cannot be delegated to a second adult without their own Google account and their own consent.

So yes — C materially strengthens the multi-adult story, and it converts the address from an
ingestion feature into a **participation** feature. M4's caution stands and I echo it: a
passive-recipient second parent is not demonstrated to produce a *coordinated outcome*. Forwarding
gets their information in; it does not get them to drive to the camp.

### 8.5 Value-prop reframe

| | Option A framing | Option B′ / C framing |
|---|---|---|
| The ask | *"Connect your Gmail"* — read access to everything | *"Here is your family's inbox"* |
| Speech act | An anxious **permission request** | Handing over an **artifact the family owns** |
| Mental model | Surveillance — *"trolling through my emails"* | Delegation — *"forward it and forget it"* |
| Shareable? | No — per-adult OAuth, Gmail only | Yes — give it to anyone, free, no install |
| Evidence | Cozi 1★, *"I will NEVER pay for this feature"* | Jam 5★, *"I love that I can just forward emails"* |

The second framing is also the one we can deliver on day one; the first we cannot deliver at all
until an external body says so. When the cheaper option is also the better-testing option, the
analysis is not close.

---
## 9. The costs of C — stated without discount

### 9.1 Deduplication — a real gap, named precisely

If a parent connects Gmail *and* forwards, the same message arrives twice. Today's idempotency is
`get_ingest_artifact_by_external(user_id, external_id)`
(`mvp-backend/app/duckdb_storage.py`, ~line 5503), checked in
`mvp-backend/app/email_sync/sync.py` before insert. Two defects:

1. **Namespace mismatch.** For path A, `external_id` is the **Gmail API message id**. For path B′
   the natural key is the **RFC 5322 `Message-ID`** of the forwarded original. Different identifier
   spaces — so the existing check **would not catch the duplicate**, and the same email would
   materialize two activities.
2. **No DB constraint.** `mvp-backend/app/migrations.py:84-87` (migration v6) creates
   `idx_ingest_artifacts_ext` as a plain **`CREATE INDEX`, not `UNIQUE`**. Dedup is advisory
   application logic; a race or a namespace miss writes a duplicate with nothing to stop it.

**Fix, and it is small:** normalize `external_id` to the RFC `Message-ID` for **both** paths (Gmail's
API exposes it in the message headers, so A can adopt the same key), plus a content-hash fallback
(`sha256` over normalized subject + sender + body) for forwards whose headers are stripped — some
clients do strip them. Then make the index `UNIQUE` in a new migration. **~1–2 days**, and it makes
path A's dedup better than it is today as a side effect. Per `CLAUDE.md`, a migration means a prod
backup first; note also that `materialize()` already refuses to auto-confirm, which bounds the blast
radius of any duplicate that slips through.

### 9.2 UX complexity — the serious objection, and its answer

`P9-complexity.md` rates this app a **SEVERE OUTLIER on five measures** and names the second forced
setup sequence *"the highest-leverage single cut in the report."* Adding a *choice* between two
ingestion methods to onboarding would violate that finding directly, and I would reject C if that
were the only way to ship it.

It is not. **Progressive disclosure — B′ as the default, A as an earned upgrade:**

1. **Onboarding shows one thing:** the family's address, with one instruction. This matches the
   one-step intake `M2-ai-assistants.md` calls *"the category's competitive frontier,"* and it
   satisfies P12 #42's finding that the address must be **the front door, not a settings toggle**
   (0 of 3,917 mainstream reviewers ever mentioned it when it was buried in settings).
2. **Option A never appears in onboarding.** It surfaces later, contextually, as an offer — after
   the parent has seen the address work: *"Want us to catch these automatically? Connect Gmail."*
   Trust has been earned by then, which is the only condition under which a full-inbox ask is
   reasonable.
3. **Never a fork.** The parent is never asked to choose. B′ is the floor; A is an accelerator.

This *reduces* net onboarding burden versus today, because the address replaces the copy-paste
`IngestView` path (§ 1.4) rather than adding to it. The support surface genuinely doubles — a real
cost I am not discounting — but both paths share one extraction pipeline, so there is one class of
extraction bug, not two.

### 9.3 Engineering

| Work | Estimate |
|---|---|
| Path B′ — webhook, address table, sender→user mapping, SPF/DKIM/DMARC + ARC, one UI surface | **1–2 engineer-weeks** |
| Liveness signalling + quiet-stream nag + "also forwarded to your inbox" (§ 6.4) | **~3–4 days** — non-optional |
| Dedup convergence (§ 9.1) | **1–2 days** |
| Gmail auto-confirm handshake (§ 6.2) | **~1 day** |
| Path A | **~0 additional engineering** — it is built (§ 1.1); its cost is compliance, not code |

**Incremental cost of C over B′ alone: about two days.** This is the fact that makes C cheap — we
are not building two systems, we are building one inbound pipe onto a pipeline that already serves
both (§ 1.3).

---

## 10. Scoring

Scale: **5 = strong, 1 = weak.** Weighted total uses § 2 weights (Highest 3, High 2, Medium-High 1.5,
Medium 1, Low 0.5).

| Criterion | Wt | **A** Gmail OAuth | **B** Register | **B′** Auto-forward | **C** A + B′ |
|---|---|---|---|---|---|
| C1 Time-to-broad-availability | 2 | **1** — 6 wks–several months, no committed date; **100-user lifetime cap**; no viable holding pattern | 2 — no gate, but blocked on top platforms | **5** — ships in 2 wks, no reviewer | **5** — B′ carries launch; A arrives later |
| C2 Compliance cost/burden | 2 | **1** — $675–$4,500/yr **annual forever**, likely Tier 3 + production audit; unresolved Limited-Use question | **1** — hostile ToS, district blast radius, FERPA §99.33(a) risk, IL SOPPA | **5** — none | 3 — inherits A's burden if pursued, but off critical path |
| C3 Onboarding friction | 3 | 4 — one tap (once permitted) | **1** — 13–18 actions, several not self-serve | **4** — one rule per mailbox; auto-confirm; desktop-web caveat | **4** — progressive disclosure, no fork |
| C4 Coverage | 2 | 3 — Gmail only (~half of parents); **but retroactive history**; §1.2 limits today's build to registered senders | 2 — 5 works / 6–7 blocked; skews to sports | 4 — ~100% of email-borne, any provider, any adult | **5** — the union |
| C5 Reliability | 1.5 | 2 — silent + correlated failure (token revocation, policy change) | 2 — nightly SIS overwrite; app-install disables email | 3 — **silent-failure risk is real** (18-month Skylight case); needs § 6.4 mitigations | 3.5 — two independent paths degrade gracefully |
| C6 Privacy / trust / legal | 1.5 | 2 — Cozi 1★; consent screen says "read all your email"; 84% parental data concern | **1** — riskiest FERPA posture; 5-yr district ban exposure | **5** — scoped by construction; chain severed at parent; a marketing asset | 4.5 — B′ default preserves the posture |
| C7 Running cost | 0.5 | 4 — free API | 4 | 5 — ~$5/mo at 1M inbound | 5 |
| C8 Multi-adult | 1 | 1 — per-adult OAuth, Gmail only; **no mechanism** | 2 | **5** — free, no install, no account | **5** |
| C9 Addressable users | 2 | 2 — ~half of US parents | 2 | **5** — every mailbox | **5** |
| **Weighted total** (max 77.5) | **15.5** | **35.0** | **25.5** | **69.5** | **67.5** |

**The result is sharper than I expected, and I am reporting it as it fell out: B′ alone (69.5)
scores marginally ABOVE C (67.5).** Adding Option A buys coverage (C4 3→5) and reliability (C5
3→3.5), but it drags in an annual third-party audit, a likely Tier 3 production-access requirement,
and an unresolved Limited-Use question (C2 5→3). On these weights the compliance drag slightly
exceeds the coverage gain.

Do not over-read a 2-point gap on a subjective scale — the honest conclusion is **B′ and C are
equivalent, and both dominate A (35.0) and B (25.5) decisively.** But the direction is the memo's
central quantitative point: **almost all of C's value is B′'s value.** Option A contributes
retroactive history, passive capture for the Gmail half, and little else. **A is a nice-to-have on
a critical-path-free schedule. It must never become the gate** — and if the § 11.2 gate fails, the
scoring says we lose almost nothing by dropping it.

---

## 11. RECOMMENDATION

### 11.1 The call

**Ship B′ now. Reject B. Treat A as an optional later upgrade, explicitly off the critical path.
Converge on C only if A clears cheaply.**

### 11.2 The decision rule

> **Ship B′ unconditionally** — it wins on the highest-weighted criterion (onboarding friction),
> has no gate, serves every mailbox provider, and is the only option with a mechanism for the second
> parent. Nothing in the evidence argues against it.
>
> **Reject B outright** — it is BLOCKED on the two largest school platforms, its ToS blast radius
> lands on the parent's school district, and it is the *riskier* FERPA architecture. Keep only an
> opt-in power-user residue on the five clean-win platforms (above all **PowerSchool's "Additional
> Notification Emails,"** an official product feature raising no ToS question), surfaced **after**
> the parent is already succeeding with B′.
>
> **Pursue A only if ALL FOUR hold:**
> 1. Counsel confirms an LLM pipeline over Gmail content satisfies Google's **Limited Use** policy
>    (P12 #27) — resolve this *before* spending a dollar on a lab;
> 2. two or three lab quotes land at **Tier 2 / ≤ ~$1,500/yr**, not self-start Tier 3 with annual
>    production auditor access;
> 3. B′ is already live and measured, so A is an *upgrade* to a working product rather than a gate
>    on shipping one; and
> 4. measured B′ coverage shows a real gap that only passive Gmail capture closes.
>
> **If any of the four fails, do not pursue A at all.** Ship B′, add Microsoft Graph `Mail.Read` for
> Outlook users instead (no admin consent, no CASA analogue, free publisher verification — P12 #28),
> and treat *"we never read your inbox"* as positioning rather than a limitation.
>
> **Do not, under any circumstances, launch on the current GCP project without verification.** The
> 100-user cap is lifetime and non-resettable; burning it forecloses A permanently on that project.

### 11.3 Does the product still work if CASA fails or stalls? **Yes — completely.**

Under this sequence CASA is not on the critical path for anything. If verification never clears,
every parent still has a working inbound address on every mailbox provider, the second-parent and
grandparent story is intact, and the product ships to general availability on schedule. What is lost
is passive capture and retroactive history for the Gmail subset — a degradation, not a failure.

Invert it. Under Option A alone, if CASA stalls, the flagship ingestion feature **does not exist for
anyone outside the Google Cloud Console test-user list** — and per § 1.1 that list is the *entire*
enforcement mechanism, external to the repo and outside our control. Worse, per § 3, that posture is
not even stable: 7-day token expiry breaks it weekly.

**Building the flagship feature on a permission an external body can withhold, when an un-gated
mechanism with better trust characteristics ships in two weeks, is not a defensible allocation of a
solo developer's runway.** That sentence is the memo.

### 11.4 Sequence and triggers

| Phase | Work | Duration | Trigger to advance |
|---|---|---|---|
| **0. Now** | Cheapest tests (§ 11.5). Freeze A at its current beta allowlist — **do not add users** | **~1 week**, ~$50 | Tests return |
| **1** | Build B′: inbound pipe, address allocation, Gmail auto-confirm, SPF/DKIM/DMARC+ARC. Onboarding = the address, one step. Retire the copy-paste path | **2 weeks** | Ships |
| **1b** | § 6.4 liveness: "last message N hours ago," quiet-stream nag, "also forwarded to your inbox," non-email fallback | **+3–4 days**, same release | **Non-optional** — do not ship 1 without it |
| **2** | Measure: what share of families set the rule; what arrives; where the gaps are. In parallel, **counsel on Limited Use** + 2–3 lab quotes | **4–6 weeks** | The § 11.2 four-part gate |
| **3a** | *If gate passes:* CASA + verification, then A as a contextual in-app upgrade. Converge on C. Dedup convergence (§ 9.1) ships **before** A | 6 wks–several months | LOA issued |
| **3b** | *If gate fails:* Microsoft Graph `Mail.Read` for Outlook. Opt-in PowerSchool/TeamSnap/SportsEngine registration for power users | 1–2 weeks | — |

### 11.5 The cheapest tests that resolve the remaining uncertainty

Ranked by cost-to-information. Total **under $100 and about a week.**

1. **The B′ setup-completion test — the one that matters most (~$0, 5 parents, 2 days).** Every
   quantitative unknown here is genuinely unmeasured: P12 confirms **no public funnel comparison of
   forwarding vs. OAuth onboarding exists**, **no vendor publishes an inbound-address activation
   rate**, and **no probability-sampled parent-side login count exists**. So measure it ourselves.
   Give five real beta parents an address and the instruction; watch. **The single number to get is
   what share complete a Gmail forwarding rule on a phone** — § 6.2's desktop-web requirement is
   B′'s biggest execution risk, and it is answerable this week. If completion is poor, the fix is
   design (auto-confirm, a desktop hand-off link, a QR code), not a change of architecture.
2. **The ParentSquare content test (~$0, 1 day).** The one unresolved cell in § 7, and the platform
   with 22M students. A single beta parent on ParentSquare forwards one week of its email. Settles
   digest-vs-instant and content-vs-link with primary evidence instead of a login-gated help center.
3. **Two or three CASA lab quotes (~$0, 1–2 weeks elapsed).** The $675-vs-$4,500 spread and the
   Tier 2-by-invitation problem (§ 3) are the difference between "worth it" and "never." Ask
   explicitly: *which tier applies to us, and does self-start force Tier 3?* Ask Google's
   verification thread the same question about the stale "free tier 2" FAQ text.
4. **Counsel on Limited Use + the §99.30/§99.33(a) question (a few hundred dollars, 1 week).** Both
   are unresolved and both are cheap to ask. The second only matters if B is revived; the first
   gates all of A.
5. **The $1.15 SMS test P12 recommends** — buy one Twilio number, register it with a live Remind or
   TeamSnap account, watch whether A2P-to-A2P long-code traffic silently fails. Out of scope for
   this decision, but it is the cheapest open question in the adjacent space and worth running in
   the same week.

---

## 12. Honest unknowns

Named because a memo that hides these is worth less than one that doesn't:

- **No funnel comparison of forwarding vs. OAuth onboarding exists in public.** P12 searched
  Lenny's, Reforge, First Round, YC, Mixpanel, Amplitude. I searched independently. **Put no number
  on this** — test 1 in § 11.5 is the answer.
- **No vendor publishes an inbound-address activation rate** (Evernote, Todoist, Trello, Slack,
  Expensify, Readwise). None.
- **No probability-sampled parent-side login/app count exists.** NHES:2023 has no such item. The
  Edsby n=125 (vendor, North American, non-probability) is the only parent-level figure in
  existence, and P12 corrects P4's carry of it on both n and population.
- **No survey has ever asked a US parent about comfort with third-party school-comms access**, and
  none measures OAuth consent-screen drop-off for `gmail.readonly`. P10 and P12 reached this
  independently.
- **ParentSquare's email content posture is unresolved** (login-gated help center) — § 11.5 test 2.
- **Whether §99.30 parental consent displaces §99.33(a)** — needs counsel; do not resolve internally.
- **Whether an LLM pipeline over Gmail content satisfies Google's Limited Use policy** — unresolved,
  and it gates all of Option A.
- **Google's FAQ still contains "free tier 2 assessment" text** contradicting ADA's deprecation
  banner and Google's own May-2024 notice. Plan for paid; ask in the verification thread.
- **Do not cite `add@cozi.com`.** P12 could not confirm it exists — absent from Cozi's live site,
  help sitemap, Wayback FAQ snapshots (2014/2017/2020/2023), and all 1,917 Cozi reviews.
- **Do not cite "CASA costs $15,000+."** Traces to a 2019 Ask HN thread predating CASA, plus Google
  fee language removed from its own docs between June 2022 and June 2023.
- **Do not use Litmus to size mailbox providers** (§ 4) — it measures rendering clients, and ~90%+ of
  its "Apple" share is Apple's app reading someone else's mailbox.
