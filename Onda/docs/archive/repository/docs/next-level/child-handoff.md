# Child handoff: local static audit and launch recommendation

2026-10-12 · Current `next-level` worktree · HEAD `5e5cacae8a9db3a84f241651d1a999e56a2d41f4`

**Recommend a parent-only launch, with deliberate parent-child co-use as the first child-input experiment.** Direct child use has a plausible benefit—hearing a child's preferences in their own words—but sufficient incremental benefit is not established here. The current handoff gives the child a surface inside the parent's authenticated app, not an isolated child session. Turning it into independent child use adds substantial access-control, consent, crisis-response, and memory-lifecycle work.

This is a recommendation, not an adopted pivot decision or an implementation change. Only this document was authored. Read `.bb/AGENTS.md`, `AGENTS.md`, and the required project context/handoff documents. Source references describe the current local files, not an assertion about the deployed build. No production, credentials, live records, connectors, network requests, app startup, commits, or branch switches were used. Synthetic scenarios below are source walkthroughs, not executed UI or exploitation tests. Existing test source was inspected; tests were not run.

## What the handoff actually does

The authenticated app wraps all five parent tabs in `HandoffCurtain`. A handoff presents a full-screen child picker; choosing an enabled companion opens `KidAgentView` with the same parent `userID`. The child service attaches the parent's bearer token. There is no credential exchange that creates a restricted child principal. Sources: [MainTabView.swift:79–87](../../mvp/MVP/MainTabView.swift#L79), [HandoffCurtain.swift:17–48](../../mvp/MVP/HandoffCurtain.swift#L17), [KidAgentService.swift:19–40](../../mvp/MVP/KidAgentService.swift#L19).

The server verifies account ownership on the reviewed parent-token routes. JWTs identify a `sub`; `current_user` returns that user ID, and the reviewed child routes do not enforce a child/adult role or child-specific capability. That protects one authenticated account from simply naming another account; it does not distinguish the parent from a child holding the parent's unlocked app. Sources: [auth.py:47–68,95–123,149–172](../../mvp-backend/app/auth.py#L47).

The normal login route invokes provider-token verification and issues an access/refresh pair; refresh rotates the refresh token and rejects failed rotation. iOS stores the credential in Keychain and reuses it for requests. Logout revokes refresh tokens, while JWT validation does not consult session revocation: an already issued valid access token remains acceptable until expiry (source default: 30 minutes). This is relevant to future immediate child-session revocation, not evidence that a child extracted a token. Sources: [auth_router.py:129–157,193–216](../../mvp-backend/app/auth_router.py#L129), [AuthService.swift:50–85](../../mvp/MVP/AuthService.swift#L50), [auth.py:34,62–68,107–118](../../mvp-backend/app/auth.py#L34).

## Verified gaps and their limits

### 1. A child can return to parent screens through the intended UI

Trace: long-press the exit icon for 0.6 seconds → select “Yes” → coordinator tears down voice → `onExit` clears `selectedKid` and dismisses the cover → the parent tab content is visible. No PIN, biometric check, or parent reauthentication occurs in that chain. The picker also has an immediate cancel button. The exposed tabs are Home, Coach, Planner, Circle, and Settings. This is a directly traced UI access path, not a conjectured token theft or an unauthenticated remote attack.

Sources: [KidAgentView.swift:86–123](../../mvp/MVP/KidAgentView.swift#L86), [KidCompanionCoordinator.swift:116–124](../../mvp/MVP/KidCompanionCoordinator.swift#L116), [HandoffCurtain.swift:26–44](../../mvp/MVP/HandoffCurtain.swift#L26), [KidPickerView.swift:44–53](../../mvp/MVP/KidPickerView.swift#L44), [MainTabView.swift:149–168,255–262](../../mvp/MVP/MainTabView.swift#L149).

There is also no durable child-mode launch gate in the reviewed root: handoff is transient `@State`, initially false, while launch uses the persisted onboarding/account keys to choose `MainTabView`. A newly constructed view tree therefore selects the parent shell. Actual force-quit, OS restoration, notification, and app-switcher behavior were not device-tested. Sources: [HandoffCurtain.swift:17–18](../../mvp/MVP/HandoffCurtain.swift#L17), [SwayApp.swift:8–9,62–68](../../mvp/MVP/SwayApp.swift#L62).

### 2. The child-selection PIN is disconnected from the iOS flow

The backend correctly denies chat when a PIN is configured but omitted, and bcrypt-verifies a supplied PIN. No PIN configured means allow. This is a child-selection check, not the missing parent-return gate. The setter accepts 3–8 digits despite a model comment saying four. Sources: [server.py:1765–1792,1920–1931](../../mvp-backend/app/server.py#L1765).

The picker directly calls `onSelected(kid)`. Its PIN screen is unreachable through the reviewed code: `pinPromptFor` has no assignment selecting a child, and even that screen's “Continue” discards `pinDraft`. `setKidPin` has no Swift call site. The chat view omits `kidPin`, and voice-token requests never send `X-Kid-Pin`. Thus a configured PIN blocks both new text turns and voice-token issuance in this client; it is not silently bypassed for those requests. Sources: [KidPickerView.swift:69–74,117–179](../../mvp/MVP/KidPickerView.swift#L69), [KidAgentView.swift:632–634](../../mvp/MVP/KidAgentView.swift#L632), [KidAgentService.swift:226–239,282–285,352–363](../../mvp/MVP/KidAgentService.swift#L226), [server.py:2202–2209,2269–2270](../../mvp-backend/app/server.py#L2202).

### 3. A sibling's existing transcript is reachable before a PIN check

Synthetic trace: an authenticated family has two enabled companions, “River” and “Sky,” and Sky has saved history. A child selects Sky in the picker. `start()` awaits `loadHistory()` **before** attempting voice. `loadHistory()` calls the parent transcript endpoint with Sky's name and `thread_id="default"`. That endpoint checks the parent account match, resolves Sky's current config, and returns its messages without a PIN check. The child view passes that history to its voice/crisis surfaces or renders the same view-model messages in text fallback. A PIN rejection on the later voice/chat request does not undo the history read.

This establishes a same-account sibling-history access path, conditional on an enabled selectable config and available history. It does not establish cross-family access. Sources: [KidPickerView.swift:69–106](../../mvp/MVP/KidPickerView.swift#L69), [KidCompanionCoordinator.swift:73–89,107–109](../../mvp/MVP/KidCompanionCoordinator.swift#L73), [KidAgentView.swift:43–68,593–609](../../mvp/MVP/KidAgentView.swift#L43), [KidAgentService.swift:342–349](../../mvp/MVP/KidAgentService.swift#L342), [server.py:2449–2459](../../mvp-backend/app/server.py#L2449).

### 4. “Parent-only” crisis reactivation relies on possession of the parent session

The revive endpoint checks that the authenticated user owns the lock, requires current consent, clears the durable/in-process lock, enables the config, and records an audit event. Those are real protections against another account. Sources: [server.py:2577–2608](../../mvp-backend/app/server.py#L2577).

However, after the exit in gap 1, Home exposes a locked child's review action and “Reactivate companion.” That calls the service with the same parent token, with no fresh adult check. A child who has been handed the unlocked app can follow this UI chain when Home has loaded the locked state and consent remains current. “Parent-only” is therefore an account-ownership assumption, not verified presence of an adult. Sources: [KidsHomeSection.swift:239–243,274–277,326–333,586–593](../../mvp/MVP/KidsHomeSection.swift#L239), [KidAgentService.swift:200–206](../../mvp/MVP/KidAgentService.swift#L200).

### 5. Saving a configuration changes the identity used by crisis locks and transcripts

Each save inserts a new version with a new UUID; reads select the highest version. Locks are keyed by config `agent_id`, and lock creation disables only that ID. `POST /kid-agent/config` does not check an existing crisis lock before saving `enable=True`. The review screen's “Introduce them” does exactly that. The Home menu exposes the review destination even for a locked companion. Sources: [duckdb_storage.py:1719–1745,1758–1769,2741–2779](../../mvp-backend/app/duckdb_storage.py#L1719), [server.py:1795–1815](../../mvp-backend/app/server.py#L1795), [KidsHomeSection.swift:254–278,93–95](../../mvp/MVP/KidsHomeSection.swift#L254), [ReviewLetterView.swift:55–64,419–432](../../mvp/MVP/ReviewLetterView.swift#L419).

Consequent source trace: locked config A → successful reviewed save creates enabled config B → runtime/status load B → lock lookup for B finds no lock on A. The old lock need not have been revived. This is a verified lifecycle gap in the code, conditional on a successful save; no live or runtime bypass was attempted. Runtime checks: [server.py:1979–2001,2232–2236](../../mvp-backend/app/server.py#L1979), [convai_endpoint.py:304–323](../../mvp-backend/app/convai_endpoint.py#L304).

The same identity split affects memory: transcript reads use the **latest config ID**, so messages stored under A are absent from B's transcript response. The LangGraph key instead remains `kid:{user_id}:{kid_name}:{thread_id}`, so editing configuration does not inherently start a new model-memory thread. Visible history and model context can diverge. This is not evidence that another family receives either history. Sources: [server.py:2076–2080,2449–2459](../../mvp-backend/app/server.py#L2076), [duckdb_storage.py:1846–1863](../../mvp-backend/app/duckdb_storage.py#L1846).

### 6. Consent records account-level agreement, not the identity of the adult at handoff

Submission requires a bearer token and the current agreement version, then records the supplied name, email, and age band. Enforcement checks the latest agreement for `user_id`; there is no child ID in the submission or fresh proof of adult presence in these routes. A current agreement can therefore cover access to multiple companions under that account. This is a description of the implementation, not a legal determination. The UI itself describes the closed-beta agreement as not yet meeting verifiable parental consent requirements. Sources: [server.py:855–902](../../mvp-backend/app/server.py#L855), [KidAgentService.swift:97–105](../../mvp/MVP/KidAgentService.swift#L97), [ConsentView.swift:3–13,48–60,129–132](../../mvp/MVP/ConsentView.swift#L3).

A consent-required voice failure falls back to text, where `/kid-chat` still enforces consent; this is an awkward recovery flow, **not** a traced consent bypass. Sources: [KidCompanionCoordinator.swift:98–104](../../mvp/MVP/KidCompanionCoordinator.swift#L98), [server.py:2203–2209](../../mvp-backend/app/server.py#L2203).

### 7. Voice callback authority is broader than a child session

`/voice/convai-token` requires parent authentication, current consent, a valid configured PIN, and no crisis lock. It does not check `enabled` before requesting a vendor token. The callback runtime does check `enabled`, so this does not establish that a disabled companion can conduct an agent conversation. Sources: [server.py:2250–2318](../../mvp-backend/app/server.py#L2250), [convai_endpoint.py:304–310](../../mvp-backend/app/convai_endpoint.py#L304).

`/v1/chat/completions` authenticates the vendor shared secret, then takes `user_id`, `kid_name`, and `thread_id` from `elevenlabs_extra_body`. It does not validate a per-child session credential, recheck consent/PIN, or bind those fields to the token-minting event. The emitted `kid_pin` and `agent_id` are not used to establish callback identity. Per-turn enabled/lock checks remain present. This establishes a local trust-boundary gap; whether an ordinary client can alter vendor-forwarded identity fields was **not** established. Do not describe this as a demonstrated cross-family exploit. Sources: [server.py:2302–2308](../../mvp-backend/app/server.py#L2302), [convai_endpoint.py:173–225,304–323](../../mvp-backend/app/convai_endpoint.py#L173).

### 8. Durable crisis protection and child-facing state do not fully agree

Input crisis handling persists a lock before alerting and skips the agent response. Storage also sets `enabled=False`. These are meaningful protections. But the triggering text stream emits `crisis`, while the iOS decoder handles only `token` and `frozen`. On the next turn the backend checks `enabled` before the lock and emits `error`; the decoder drops that too. Consequently this path need not transition the text UI into its intended frozen state, although backend conversation remains blocked. Sources: [server.py:1979–2001,2018–2052](../../mvp-backend/app/server.py#L1979), [duckdb_storage.py:2765–2769](../../mvp-backend/app/duckdb_storage.py#L2765), [KidAgentService.swift:367–380](../../mvp/MVP/KidAgentService.swift#L367), [KidAgentView.swift:632–648](../../mvp/MVP/KidAgentView.swift#L632).

Likewise, the server emits `retract` for a late output moderation replacement; iOS drops it. Earlier rendered text will not be replaced through that event even though the stored assistant message uses the replacement. Actual harmful output reaching a child was not observed. Sources: [server.py:2169–2185](../../mvp-backend/app/server.py#L2169), [KidAgentService.swift:367–380](../../mvp/MVP/KidAgentService.swift#L367).

### 9. Crisis notification is an attempt, not confirmed adult receipt

Text/voice crisis messages say the grown-up is being told. Both push helpers can return without dispatch when APNs is unconfigured or an exception occurs; neither waits for adult acknowledgment. The same logged-in device handed to the child may be a registered parent device. The reviewed routing chooses the account owner for crisis notifications, including abuse-related flags; no alternative trusted-adult selection appears in that path. These are response-design gaps, not a claim about notification delivery or a particular family. Sources: [server.py:737–762,2023–2047](../../mvp-backend/app/server.py#L737), [convai_endpoint.py:32–43,362–384](../../mvp-backend/app/convai_endpoint.py#L32), [prompt_synthesis.py:413–427](../../mvp-backend/app/prompt_synthesis.py#L413).

The push helper starts a daemon thread, so `parent_notified_at` can represent scheduling an attempt, not a completed APNs delivery or a parent reading it. Source: [push/__init__.py:196–211](../../mvp-backend/app/push/__init__.py#L196).

There is also a conditional external data path: crisis handlers pass the input message to `telemetry.alert_crisis`, which formats user ID, child name, and up to 240 excerpt characters into a Slack webhook payload when configured (or logs up to 100 characters when unconfigured). Truncation is not redaction. This audit did not invoke that path, inspect webhook configuration, or share anything. Sources: [server.py:2044–2047](../../mvp-backend/app/server.py#L2044), [convai_endpoint.py:381–384](../../mvp-backend/app/convai_endpoint.py#L381), [telemetry.py:99–126,129–140](../../mvp-backend/app/telemetry.py#L99).

### 10. Legacy account issuance remains a conditional authentication concern

The legacy issue-token route takes a claimed user ID without sign-in proof, is rate limited, rejects accounts with a linked sign-in identity, and returns 410 when its retirement flag is off. Its source default is enabled; legacy-token acceptance also defaults on. For an unclaimed synthetic account with issuance enabled, knowing its ID is enough to request its parent credential. This is separate from the ordinary child handoff and does not establish current production exposure: configuration and account state were not inspected. Sources: [server.py:702–726](../../mvp-backend/app/server.py#L702), [auth.py:71–78,95–123](../../mvp-backend/app/auth.py#L71).

## Route boundary summary

| Route | Verified boundary | Limitation for direct child use |
|---|---|---|
| `/kid-agent/config`, `/kid-agent/list`, `/kid-agent/preview` | Parent bearer, account match, current consent | Same authority remains on the handed-over device; config save can create a new identity past an old lock |
| `/kid-auth/set-pin` | Parent bearer, account match, PIN validation/hash | No fresh adult check; no iOS setter call site |
| `/kid-chat` | Parent bearer, account match, consent, rate limit, configured PIN; enabled/lock and moderation in stream | iOS omits PIN and drops safety-state events |
| `/voice/convai-token` | Parent bearer, consent, configured PIN, crisis-lock check | No child principal or enabled check at mint |
| `/v1/chat/completions` | Vendor shared secret; runtime enabled/lock checks | Supplied identity fields not bound to an application child session |
| `/kid-chat/transcripts` | Parent bearer, account match | Deliberately parent-readable without PIN/consent; reused on child screen |
| `/kid-agent/status` | Parent bearer; lookup within that account | Status probe, not a child authorization boundary |
| `/consent/submit`, `/consent/status` | Parent bearer; version recorded/compared | Account agreement, not per-child session or fresh adult verification |
| `/kid-agent/crisis-locks`, `/{agent_id}/revive` | Parent bearer, consent; ownership checks | Child holding the parent UI can reach revive |
| `/chat`, `/memory/{user_id}` | Parent bearer and account match | Parent authority includes coaching and family memory after UI exit |

Route sources are linked in the findings above; parent routes: [server.py:1120–1137,1198–1210](../../mvp-backend/app/server.py#L1120). Crisis list/status: [server.py:2222–2236,2569–2574](../../mvp-backend/app/server.py#L2222).

## Memory boundaries: what is separated and what is not

**Between accounts:** reviewed reads constrain by authenticated owner. Config queries use both user ID and child name; transcript queries use the resolved config ID and thread ID. No cross-account transcript disclosure was demonstrated. Legacy issuance and vendor identity binding have the specific conditional limitations above; neither justifies a blanket claim that all family memory is exposed.

**Between children:** the runtime selects the named child's profile; cache keys include user ID and child name. Text and voice both use `kid:{user_id}:{kid_name}:{thread_id}` and a shared durable checkpointer. Thus the current default child text/voice thread is shared, unlike the parent text/voice split described elsewhere in older project context. Parent thread construction is separate for ordinary IDs. None of these namespace choices authenticates which sibling holds the device. Sources: [kid_agent.py:46–61,89–101,129–144](../../mvp-backend/app/kid_agent.py#L46), [server.py:2076–2080](../../mvp-backend/app/server.py#L2076), [convai_endpoint.py:405–409](../../mvp-backend/app/convai_endpoint.py#L405), [agent.py:118–140](../../mvp-backend/app/agent.py#L118).

**Parent context entering child configuration:** synthesis receives the selected child's full profile, the parent's profile object, the free-text brief, and prior invariants. `_prune_empty` removes empty values, not sensitive fields. The runtime then renders selected child fields and synthesized personality/goals/examples. This is a real data flow from parent context into child-agent configuration; a specific secret appearing in a child response was not demonstrated. No field-level privacy approval filter is present in this synthesis path. Sources: [kid_agent.py:172–195](../../mvp-backend/app/kid_agent.py#L172), [prompt_synthesis.py:213–243,287–363,511–519](../../mvp-backend/app/prompt_synthesis.py#L213).

**Child conversation becoming “understanding”:** the reviewed runtime has a child transcript and persistent conversation context. Its tool wiring supplies only optional Tavily search, not parent-profile retrieval or profile-update tools. These sources do not establish a validated child-observation → parent-approved insight → better recommendation loop. Calling the stored dialogue a richer or more accurate child model would overstate what has been shown. Sources: [kid_agent.py:67–83,140–145](../../mvp-backend/app/kid_agent.py#L67), [server.py:2071–2080,2182–2193](../../mvp-backend/app/server.py#L2071).

**Identity lifetime:** child names participate in configuration, PIN, cache, and checkpoint keys; configuration versions separately mint new IDs. A stable child principal is absent from these paths. Gap 5 demonstrates a concrete history/lock inconsistency; broader rename, delimiter-collision, deletion, and stale-checkpoint behavior needs focused follow-up before making further claims.

## Compare the four product modes

| Mode | Possible child-understanding benefit | Boundary and operational cost | Recommendation |
|---|---|---|---|
| Shared family tablet | Child can contribute without borrowing a parent's phone; potentially frequent use | Requires restricted child credentials, authenticated sibling switching/history, protected adult return, durable relaunch state, and an adult reachable on a separate device. Current picker/session does not provide this. | Defer independent use |
| Isolated child mode on the parent's phone | Convenient brief handoff; captures the child's own words | Must actually suspend parent authority and protect return, restart, links, notifications, caches, and sibling history. The phone may also be the parent's crisis-alert endpoint. Current full-screen cover is insufficient. | Defer until benefit warrants isolation work |
| Separate child app | Can keep parent screens and credentials out of the child installation; supports independent use | Still needs scoped backend identity, enrollment/revocation, shared-device switching, consent/assent, crisis response, and bounded memory. A second binary alone fixes none of the server gaps. Adds installation and release overhead. | Consider only after independent-use value is established |
| Parent-child co-use | Child can correct the parent's assumptions during a short preference conversation; parent can confirm attribution | Parent stays present and controls the session. Needs clear speaker attribution and deliberate approval before saving an observation; should not promise private child conversation. Still requires approved processing/data handling. | Best first child-input experiment, after a parent-only baseline |

The distinction that matters is whether the child supplies useful new information, not whether the child has an independent AI companion. Co-use can capture direct preferences such as “I like swimming, but not racing.” It cannot establish how candid a child would be without the parent present. Conversely, this implementation tells parents they can read all conversations, so independent interaction must not be presented as confidential. Sources: [ConsentView.swift:51–60](../../mvp/MVP/ConsentView.swift#L51), [prompt_synthesis.py:409–411](../../mvp-backend/app/prompt_synthesis.py#L409).

## Benefit evidence and a bounded next step

The local research recommends cutting the companion and reports no demand evidence in its reviewed corpus. Its own red team explicitly says that cut was not tested and that demand for a closed-beta feature was not falsified. Therefore the supported conclusion is **benefit unproven**, not “children do not want this” or “it cannot improve understanding.” Sources: [feature-fit verdict:98](../GTM/research/2026-08-parent-planning-behavior/raw/S2-feature-fit-verdict.md#L98), [research report:321](../GTM/research/2026-08-parent-planning-behavior/report.md#L321).

For this workstream, keep the next evaluation synthetic and local. Use fictional parent River, children Sky and Lane, and a second fictional family. Give each persona different interests and a unique private marker. Compare a parent-only summary, a parent-child co-use correction, and a hypothetical independent-child statement against a predefined preference ground truth. Score whether each changes the recommendation correctly, whether speaker/child attribution is retained, and whether irrelevant private markers cross into another surface. Synthetic results can expose implementation mistakes; they cannot establish real demand, child trust, developmental benefit, or willingness to pay.

Before reopening independent child use, require evidence of a material improvement over co-use on a specified parent job—not session volume alone—and a separately authorized evaluation designed for the intended ages. Also require the direct-use boundary to pass synthetic checks: parent exit and relaunch locked; sibling reads denied without proper child scope; child credentials rejected by parent/config/consent/revive routes; voice identity bound to the minted session; consent/PIN changes effective during sessions; crisis state survives config edits; retract/freeze events handled; transcript/checkpoint identity and deletion consistent. These are future acceptance conditions, not completed fixes or permission to run a child study.

Treat the user's current external-policy research as a constraint: connectors may restrict PHI and sensitive inference. This audit did not re-research policy or make a compliance determination. Do not solve a connector limitation by relabeling sensitive child data or routing it elsewhere. No sharing is part of this recommendation. A future feature must establish permitted processing for the actual service and data, and must not infer diagnoses or sensitive traits from a child's conversational style. The conditional telemetry and synthesis flows above need explicit data-minimization decisions before child use expands.

## Verification and remaining uncertainty

Performed source-level route/call tracing and Python AST parsing without importing the application. Swift searches found exactly one `setKidPin(` occurrence (its definition), one `pinPromptFor =` assignment (clearing it), one `kidPin:` occurrence (the service parameter), and no `X-Kid-Pin` occurrence. These corroborate the disconnected PIN flow; they do not substitute for a device test.

Existing backend tests cover crisis locking and output replacement, including [test_kid_runtime_policies.py:79–108](../../mvp-backend/tests/test_kid_runtime_policies.py#L79). They do not prove the Swift decoder handles those events or that a child cannot navigate to parent reactivation. No test-pass claim is made here.

Not established: deployed flags or build, real-device restoration and notification behavior, vendor enforcement of forwarded identity fields, actual adult receipt of alerts, specific model disclosure of private context, or incremental real-family benefit from direct child use. Those uncertainties do not weaken the traced return-to-parent and sibling-history gaps. They do prevent labeling this a completed runtime penetration test or a public-launch approval.
