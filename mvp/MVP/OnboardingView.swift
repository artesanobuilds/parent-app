import SwiftUI

// MARK: - Onboarding Data (sent to backend)
//
// UNCHANGED LEGACY SHAPE + additive Heisman keys. beta-v1 cut three screens
// from the funnel (demographics, energy/dread, support crew) and Heisman
// sprint-01 cut the rest of the questionnaire (household, education,
// challenges chips, free-time grid) — but the backend fields STAY: the Coach
// learns them conversationally and the profile editors edit them. So every
// property below survives and the ones the funnel no longer asks simply
// arrive empty. `/profile/seed`'s wire contract is pinned by
// tests/test_onboarding_seed_contract.py; do not drop keys here to "tidy up".
//
// Heisman additions (2026-08-21, additive only): `topic`,
// `parentWeekTasks` → `parent_week_tasks`, `extractedActivities` →
// `extracted_activities` ([{who,what,when,where,notes}]).

struct OnboardingData {
    let parentName: String
    let kids: [(name: String, age: String, temperament: String, pronouns: String, gradeBand: String, gender: String)]
    let household: String
    let supportSystem: String       // no longer asked — Coach learns it
    let energyPattern: String       // no longer asked — Coach learns it
    let dreadedMoment: String       // no longer asked — Coach learns it
    let challenges: [String]
    let goals: [String]
    // Demographic additions
    let postalCode: String          // the Heisman cold open's "Location / Zip Code"
    let country: String             // no longer asked — Coach learns it
    let primaryLanguage: String
    let parentAgeRange: String      // no longer asked — Coach learns it
    let adultsInHousehold: Int?     // no longer asked — omitted from the body
    let employment: String          // no longer asked — Coach learns it
    let culturalBackground: String  // no longer asked — Coach learns it
    let pronouns: String            // no longer asked — Coach learns it
    // Phase-3 Figma deltas (additive — new keys only, nothing renamed)
    let secondaryLanguage: String
    let educationStyle: String
    let familyActivities: [String]
    let coachVoice: String
    let coachPersonality: String
    // Heisman sprint-01 (additive)
    /// One value: a topic-card id (`HeismanTopic.id`) or the parent's free
    /// string as typed — spec: "an enum for the six cards or a free string".
    let topic: String
    /// Step-05 own-to-dos; the free-text note rides as one more entry.
    let parentWeekTasks: [String]
    /// Step-04's real extraction result (empty when skipped/failed — the
    /// static sample fallback is never seeded as real data).
    let extractedActivities: [OnboardingDraft.ExtractedActivity]
}

// MARK: - Onboarding View

/// The Heisman sprint-01 funnel (2026-08-21). The big inversion this sprint:
/// the parent answers EVERYTHING — and watches the coach perform a real
/// extraction — before the account wall, which now sits at the tail:
///
///   splash → coldOpen (name+location) → children → topic → sampleProblem
///          → extractionCheck → parentTasks → gettingReady (theatrical)
///          → coachDemo → accountWall → plan (paywall) → warmup (the real
///            seed + ring) → allSet
///
/// This retires the 2026-08-09 "plan/sign-in first" architecture (v4) and,
/// with it, the `includesSignInStep` capture-once machinery: `.accountWall`
/// is UNCONDITIONAL, and a parent who is already signed in (a resumed v4
/// draft, or the DEBUG `UITEST_SKIP_SIGNIN` bypass) auto-advances past it
/// from the wall's own `.task` rather than the flow reshaping underneath the
/// current index. `git log -S cameToSignInFromSplash` has the previous
/// sign-in-at-end architecture for reference.
///
/// The structural rules that survive every reshape:
///
///  1. `flow` is COMPUTED, and `draft.stepIndex` is a position in it.
///     Forward moves name their destination (`goTo(.topic)`) rather than
///     incrementing, so reshaping the flow can never land the parent on the
///     wrong screen. Back is `stepIndex - 1`, which walks the computed array.
///  2. Every answer collected before an account exists lives in
///     `OnboardingDraft` (durable on every mutation) — see that type's notes.
///  3. The seed still fires from the ring (`.warmup`) screen, now POST-auth:
///     stash + POST `/profile/seed`, durable retry, cleared only on 200.
struct OnboardingView: View {

    // MARK: Inputs

    /// False ONLY under the DEBUG `UITEST_SKIP_SIGNIN` harness (SwayApp) —
    /// the account wall auto-advances without real OAuth so headless
    /// simulator driving can cross it. Unlike v4 this does NOT reshape the
    /// flow: the wall is always a step; this just lets it wave you through.
    var signInRequired: Bool

    /// Called the moment sign-in resolves an account. The app persists the
    /// account id, and when the account ALREADY has a profile (same parent,
    /// new device or reinstall) it ends onboarding immediately — this view
    /// is torn down mid-funnel by design.
    var onSignedIn: (AuthService.SignInOutcome) -> Void

    /// Stash + POST `/profile/seed`. Returns true once the server confirmed
    /// a 200. Called from the ring screen (post-auth). A false return is NOT
    /// fatal: the payload stays durable in `pending_seed_body` and the next
    /// launch retries it.
    var onSeed: (OnboardingData) async -> Bool

    /// "Take me home" — flips `onboarding_completed`.
    var onFinish: () -> Void

    init(
        signInRequired: Bool,
        onSignedIn: @escaping (AuthService.SignInOutcome) -> Void,
        onSeed: @escaping (OnboardingData) async -> Bool,
        onFinish: @escaping () -> Void
    ) {
        self.signInRequired = signInRequired
        self.onSignedIn = onSignedIn
        self.onSeed = onSeed
        self.onFinish = onFinish
        // Resume an abandoned funnel. `load` returns nil on a clean install
        // and on an undecodable draft, both of which mean "start at the
        // splash" — which is index 0 again as of v5 (see `isFreshDraft`).
        let loaded = OnboardingDraft.load()
        _draft = State(initialValue: loaded ?? OnboardingDraft())
        _isFreshDraft = State(initialValue: loaded == nil)
    }

    // MARK: State

    /// The ONE piece of funnel state. Every answer and the current position
    /// live here, and a single `.onChange` below persists the whole thing on
    /// every mutation — so there is no way to add a field that isn't durable.
    @State private var draft: OnboardingDraft

    /// True when `init` found NOTHING on disk — a genuinely fresh install,
    /// not a draft resuming from some earlier version of `flow`. A brand-new
    /// `OnboardingDraft()` and a STORED older draft that happens to read
    /// `stepIndex == 0, flowVersion == 1` are otherwise indistinguishable at
    /// the struct level (both are Swift's default values). Real migrations
    /// only make sense for a draft that was actually SAVED under an older
    /// `flow` shape; this flag lets `resumeIfNeeded` skip them entirely for
    /// one that wasn't, and just stamp it to the current version.
    @State private var isFreshDraft: Bool

    /// The resolved account id, written by `onSignedIn` via SwayApp. Read
    /// here (never written) so the post-auth tail can authenticate.
    @AppStorage("user_name") private var accountID = ""

    // Ring state (the post-auth `.warmup` beat — unchanged machinery).
    @State private var ringSteps: [WarmupStep] = OnboardingWarmupService.placeholderSteps
    @State private var ringPercent: Int = 0
    @State private var warmupStarted = false

    @State private var didResume = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    // MARK: Tunables

    /// Hard ceiling on the ring, measured from the moment it appears. The
    /// backend bounds each beat at 25s and there are four of them, so a fully
    /// pathological run outlives this — deliberately. A parent stuck behind a
    /// spinner because an LLM call timed out is strictly worse than an
    /// unpersonalised Home.
    private static let ringDeadline: TimeInterval = 32
    /// Floor, so a fast warm-up doesn't strobe past.
    private static let ringMinimumDwell: TimeInterval = 2.2
    private static let ringPollInterval: TimeInterval = 0.7

    // MARK: - Option lists
    //
    // Heisman removed every questionnaire chip screen. The ONLY lists left
    // here feed the "You're all set" coach-settings card; everything else
    // (temperament, challenges, interests, household, education) is edited
    // post-auth in the profile editors, whose option lists live on
    // `ProfileOptions` (see `patterns_onboarding_parity`).

    private let coachVoiceOptions = [
        "Default - Male", "Default - Female", "Warm - Male", "Warm - Female"
    ]
    private let coachPersonalityOptions = [
        "Default - Genuine", "Direct - Coach", "Gentle - Nurturing", "Playful - Upbeat"
    ]

    // MARK: - Flow

    enum Step: Equatable {
        case splash
        case coldOpen
        case children
        case topic
        case sampleProblem
        case extractionCheck
        case parentTasks
        case gettingReady
        case coachDemo
        case accountWall
        /// "choose a plan" — the smoke-and-mirrors paywall (existing screen,
        /// now POST-auth). Both Buy buttons only advance.
        case plan
        /// The real seed + warm-up ring (existing screen, post-auth).
        case warmup
        /// "You're all set" — the one-last-thing recap + coach settings.
        case allSet
    }

    /// The screen order. v5 is a FIXED sequence — no conditional sign-in
    /// step, no per-child screen growth (children are rows on one screen).
    /// Still computed (not a constant) so a future reshape keeps rule 1's
    /// name-your-destination discipline meaningful.
    private var flow: [Step] {
        [.splash, .coldOpen, .children, .topic, .sampleProblem,
         .extractionCheck, .parentTasks, .gettingReady, .coachDemo,
         .accountWall, .plan, .warmup, .allSet]
    }

    private var currentStep: Step {
        let steps = flow
        return steps[min(max(draft.stepIndex, 0), steps.count - 1)]
    }

    private func goTo(_ step: Step) {
        guard let index = flow.firstIndex(of: step) else { return }
        withAnimation(.hearth(.hearthSlow, reduceMotion: reduceMotion)) {
            draft.stepIndex = index
        }
    }

    /// Advances to the step immediately AFTER the current one in the
    /// computed flow. Used by the "just continue" callbacks (splash
    /// auto-advance, the paywall's Buy buttons, the wall's post-auth
    /// hand-off) so none of them hardcode a destination that a flow reshape
    /// could silently invalidate. Clamped to the last step.
    private func goToNext() {
        let steps = flow
        let next = min(draft.stepIndex + 1, steps.count - 1)
        withAnimation(.hearth(.hearthSlow, reduceMotion: reduceMotion)) {
            draft.stepIndex = next
        }
    }

    private func goBack() {
        guard draft.stepIndex > 0 else { return }
        hideKeyboard()
        withAnimation(.hearth(.hearthSlow, reduceMotion: reduceMotion)) {
            draft.stepIndex -= 1
        }
    }

    // MARK: - Body

    var body: some View {
        ZStack {
            Color.bgSober.ignoresSafeArea()

            Group {
                switch currentStep {
                case .splash:
                    splashScreen
                case .coldOpen:
                    HeismanColdOpenView(draft: $draft, onBack: goBack, onContinue: { goTo(.children) })
                case .children:
                    HeismanChildrenView(draft: $draft, onBack: goBack, onContinue: { goTo(.topic) })
                case .topic:
                    HeismanTopicView(draft: $draft, onBack: goBack, onContinue: { goTo(.sampleProblem) })
                case .sampleProblem:
                    HeismanSampleProblemView(draft: $draft, onBack: goBack, onContinue: { goTo(.extractionCheck) })
                case .extractionCheck:
                    HeismanExtractionCheckView(draft: $draft, onBack: goBack, onContinue: { goTo(.parentTasks) })
                case .parentTasks:
                    HeismanParentTasksView(
                        draft: $draft,
                        onBack: goBack,
                        onContinue: { goTo(.gettingReady) },
                        // D2/D4: skip commits no task data and lands in the
                        // same place as Continue.
                        onSkip: { goTo(.gettingReady) }
                    )
                case .gettingReady:
                    HeismanGettingReadyView(parentName: firstName, onDone: { goTo(.coachDemo) })
                case .coachDemo:
                    HeismanCoachDemoView(
                        draft: $draft,
                        // Back skips OVER the theatrical interstitial —
                        // landing on `.gettingReady` would replay a 4-second
                        // performance just to go further back.
                        onBack: { goTo(.parentTasks) },
                        onContinue: { goTo(.accountWall) }
                    )
                case .accountWall:
                    HeismanAccountWallView(
                        draft: $draft,
                        signInRequired: signInRequired,
                        accountID: accountID,
                        onBack: goBack,
                        onSignedIn: { outcome in
                            onSignedIn(outcome)
                            if outcome.hasProfile {
                                // Returning parent: the account already has a
                                // family. MERGE the funnel's fresh answers into
                                // it instead of discarding the draft —
                                // 2026-08-22: Miguel walked the new funnel with
                                // real data (kids, topic, an image-extracted
                                // event), signed in with his existing Google
                                // account, and it all silently vanished; Home
                                // showed only the old family. Same-name kids
                                // merge server-side, new names add, board rows
                                // dedupe. onSeed stashes durably BEFORE the
                                // POST, so a kill mid-flight retries on the
                                // next launch. Then finish directly — a
                                // returning parent skips paywall + warmup.
                                Task {
                                    _ = await onSeed(collectedData())
                                    onFinish()
                                }
                                return
                            }
                            goToNext()
                        },
                        onAdvance: {
                            if currentStep == .accountWall { goToNext() }
                        }
                    )
                case .plan:
                    planScreen
                case .warmup:
                    warmupScreen
                case .allSet:
                    allSetScreen
                }
            }
            .transition(.asymmetric(
                insertion: .opacity.combined(with: .move(edge: .trailing)),
                removal: .opacity.combined(with: .move(edge: .leading))
            ))
        }
        // beta-v1 is light-locked; the only dark surface is bg/voice.
        .preferredColorScheme(.light)
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                Button("Done") { hideKeyboard() }
                    .font(.hearthTitleMD)
                    .foregroundColor(.accentOnCanvas)
            }
        }
        // THE durability hook: one write per mutation, covering every field.
        .onChange(of: draft) { _, updated in updated.save() }
        .task { resumeIfNeeded() }
    }

    /// Resume + migrate a stored draft, then clamp the landing index.
    ///
    /// Clamp rules (v5):
    ///  1. **Never past `.accountWall` without an account.** Nothing
    ///     downstream has an identity to seed or authenticate with. (The
    ///     DEBUG `signInRequired == false` bypass is exempt — that harness
    ///     deliberately runs the tail without OAuth.)
    ///  2. **Never past the ring.** The ring fires the seed; a draft saved
    ///     at `.allSet` whose seed never confirmed would otherwise land on
    ///     the landing page with the family never POSTed. Re-entering the
    ///     ring is cheap and idempotent: a confirmed seed flushes as a no-op
    ///     and the warm-up dedupes onto its live run.
    private func resumeIfNeeded() {
        guard !didResume else { return }
        didResume = true

        // Migrations correct a STORED draft written under an older `flow`
        // shape. A genuinely fresh install (nothing on disk) must skip them
        // — see `isFreshDraft` — and only be stamped to the current version.
        if isFreshDraft {
            draft.flowVersion = 5
        } else {
            migrateThroughV4()

            // v4 → v5 (2026-08-21, Heisman sprint-01): the questionnaire is
            // REPLACED and sign-in moves from the head to the tail, so this
            // is a REORDER — every v4 index re-homes onto a named step.
            //
            // Old v4 order: plan, [signIn], acquainted, kidCount,
            //               kid(0..n-1), mind, freeTime, warmup, allSet
            // Mapping:
            //   plan/signIn        → splash      (nothing answered yet — the
            //                                     paywall/wall moved to the
            //                                     tail; restart the intro)
            //   acquainted         → coldOpen    (name+location live there)
            //   kidCount / kid(i)  → children    (rows on one screen now)
            //   mind / freeTime    → topic       (their answers persist on
            //                                     the draft and still seed;
            //                                     topic is the first NEW
            //                                     question they haven't seen)
            //   warmup             → accountWall (they signed in at the old
            //                                     head, so the wall's
            //                                     already-signed-in task
            //                                     advances them into the
            //                                     post-auth tail, where the
            //                                     ring re-fires the seed
            //                                     idempotently)
            //   allSet             → allSet
            if draft.flowVersion < 5 {
                // Reconstruct the OLD v4 flow's landmark indices. Whether
                // the saved run included `.signIn` is approximated from the
                // CURRENT auth state — same approximation the v2→v3
                // migration made; worst case the parent lands one screen
                // early, never on a step that no longer exists.
                let oldIncludedSignIn = accountID.isEmpty
                    || AuthService.shared.credential(for: accountID) == nil
                var old: [Step?] = [.splash]                    // old .plan
                if oldIncludedSignIn { old.append(.splash) }    // old .signIn
                old.append(.coldOpen)                           // old .acquainted
                old.append(.children)                           // old .kidCount
                for _ in draft.kids.indices { old.append(.children) } // old .kid(i)
                old.append(.topic)                              // old .mind
                old.append(.topic)                              // old .freeTime
                old.append(.accountWall)                        // old .warmup
                old.append(.allSet)                             // old .allSet

                let clamped = min(max(draft.stepIndex, 0), old.count - 1)
                let target = old[clamped] ?? .splash
                draft.stepIndex = flow.firstIndex(of: target) ?? 0
                draft.flowVersion = 5
            }
        }

        // Clamp 1 — never past the wall without an account.
        if signInRequired, accountID.isEmpty,
           let wallIndex = flow.firstIndex(of: .accountWall),
           draft.stepIndex > wallIndex {
            draft.stepIndex = wallIndex
        }
        // Clamp 2 — never past the ring (the seed-firing beat).
        if let warmupIndex = flow.firstIndex(of: .warmup), draft.stepIndex > warmupIndex {
            draft.stepIndex = warmupIndex
        }
    }

    /// The pre-v5 positional migrations (v1→v2, v2→v3, v3→v4), preserved
    /// verbatim in effect so an ancient draft still lands on a correct v4
    /// index before the v4→v5 re-home above runs. These operate on the OLD
    /// v4 flow shape, reconstructed locally — the live `flow` no longer
    /// contains those steps.
    private func migrateThroughV4() {
        // Reconstruct the v4 flow's INDICES (not steps): plan, [signIn],
        // acquainted, kidCount, kid(i)..., mind, freeTime, warmup, allSet.
        let oldIncludedSignIn = accountID.isEmpty
            || AuthService.shared.credential(for: accountID) == nil
        let signInCount = oldIncludedSignIn ? 1 : 0
        let v4WarmupIndex = 1 + signInCount + 2 + draft.kids.count + 2

        // v1 → v2 (2026-08-09): `.plan` inserted directly before `.warmup`
        // at the END; v1 indices at/after the old warmup slot shift +1.
        if draft.flowVersion < 2 {
            // v1 order: splash, acquainted, kidCount, kid(i)..., mind,
            // freeTime, [signIn], warmup, allSet — warmup sat at:
            let v1WarmupIndex = 3 + draft.kids.count + 2 + signInCount
            if draft.stepIndex >= v1WarmupIndex {
                draft.stepIndex += 1
            }
            draft.flowVersion = 2
        }

        // v2 → v3 (2026-08-09): `.plan` and `.signIn` moved to the START.
        // REORDER — re-home each v2 index onto the same named slot in v3/v4
        // terms. v2 order: splash, acquainted, kidCount, kid(i)..., mind,
        // freeTime, [signIn], plan, warmup, allSet.
        if draft.flowVersion < 3 {
            let kidCount = draft.kids.count
            let v2Index = min(max(draft.stepIndex, 0), 3 + kidCount + 2 + signInCount + 3 - 1)
            // Name the v2 slot, then find its v4 index (v4 order: plan,
            // [signIn], acquainted, kidCount, kid(i)..., mind, freeTime,
            // warmup, allSet — the splash is gone by v4, mapping to
            // acquainted's slot).
            let v4Base = 1 + signInCount // first questionnaire slot in v4
            let v4Index: Int
            switch v2Index {
            case 0:                      v4Index = v4Base                    // splash → acquainted
            case 1:                      v4Index = v4Base                    // acquainted
            case 2:                      v4Index = v4Base + 1                // kidCount
            case 3..<(3 + kidCount):     v4Index = v4Base + 2 + (v2Index - 3) // kid(i)
            case (3 + kidCount):         v4Index = v4Base + 2 + kidCount     // mind
            case (3 + kidCount + 1):     v4Index = v4Base + 2 + kidCount + 1 // freeTime
            default:                     v4Index = v4WarmupIndex             // signIn/plan/warmup/allSet → warmup-ish
            }
            draft.stepIndex = v4Index
            draft.flowVersion = 4 // v3→v4's splash deletion is already baked in
        }

        // v3 → v4 (2026-08-10): `.splash` removed from the flow — a
        // positional shift back by one for indices at/past the old splash
        // slot. (Drafts migrated by the v2→v3 block above jumped straight to
        // v4 and skip this.)
        if draft.flowVersion < 4 {
            let oldSplashIndex = 1 + signInCount
            if draft.stepIndex >= oldSplashIndex {
                draft.stepIndex = max(oldSplashIndex, draft.stepIndex - 1)
            }
            draft.flowVersion = 4
        }
    }

    // MARK: - Screen: splash ("Onboarding - 0")

    /// The new black-tumbler "MVP — Most Valuable Parent" mark
    /// (`29:2778`/`29:2779`) on the `bg/sober` cream. Unlike the previous
    /// splash art this one IS a vector in Figma — it ships as a true SVG
    /// imageset (`OnboardingHeismanMark`), not a flattened PNG.
    ///
    /// One-splash rule: `LaunchScreen.storyboard` shows the SAME asset on
    /// the same ground, so a cold launch reads as one continuous splash. It
    /// auto-advances after a beat, and a tap skips the wait — the
    /// `currentStep == .splash` re-check inside the sleep means the two
    /// triggers can never double-advance.
    private var splashScreen: some View {
        ZStack {
            Color.bgSober.ignoresSafeArea()

            Image("OnboardingHeismanMark")
                .resizable()
                .scaledToFit()
                // Frame: 405×498 in a 440-wide canvas → 92% of width.
                .frame(maxWidth: .infinity)
                .padding(.horizontal, 17)
                .accessibilityHidden(true)
                .accessibilityLabel("MVP — Most Valuable Parent")
        }
        .contentShape(Rectangle())
        .onTapGesture { goToNext() }
        .task {
            try? await Task.sleep(for: .seconds(1.7))
            if currentStep == .splash { goToNext() }
        }
        .trackScreen("onboarding_splash")
    }

    // MARK: - Screen: choose a plan (smoke-and-mirrors paywall)
    //
    // `choose a plan`. Miguel's explicit ask, 2026-08-09: this step does
    // nothing but let you continue — no purchase, no Stripe, no StoreKit.
    // `PaywallView` already matches the frame; `.screen` bypasses the
    // Settings-entry feature flag deliberately (the flag gates the SETTINGS
    // entry point, not this funnel step). Heisman moved it POST-auth (it
    // "secures" the account the parent just created).
    private var planScreen: some View {
        PaywallView(
            onContinue: { goToNext() },
            showsCloseButton: false,
            buyAccessibilityHint: "Continues to the next step"
        )
            .screen
            .trackScreen("onboarding_plan")
    }

    // MARK: - Screen: the progress ring (post-auth seed)

    private var warmupScreen: some View {
        VStack(spacing: .hearth700) {
            Spacer(minLength: .hearth500)

            progressRing

            Text("Getting everything\nready for you, \(firstName).")
                .font(.hearthDisplayMD)
                .foregroundColor(.inkPrimary)
                .multilineTextAlignment(.center)
                .lineSpacing(.hearthLineDisplayMD)
                .minimumScaleFactor(0.7)

            VStack(spacing: .hearth600) {
                ForEach(ringSteps) { step in
                    warmupRow(step)
                }
            }

            Spacer(minLength: .hearth500)
        }
        .padding(.horizontal, .hearth700)
        .task { await runWarmup() }
        .trackScreen("onboarding_warmup")
    }

    private var progressRing: some View {
        ZStack {
            Circle()
                .stroke(Color.bgElevated, lineWidth: 10)
            Circle()
                .trim(from: 0, to: max(0.02, Double(ringPercent) / 100.0))
                .stroke(Color.accentOnCanvas, style: StrokeStyle(lineWidth: 10, lineCap: .round))
                .rotationEffect(.degrees(-90))

            HStack(alignment: .lastTextBaseline, spacing: 0) {
                Text("\(ringPercent)")
                    .font(.hearthDisplayHero)
                Text("%")
                    .font(.hearthDisplayMD)
            }
            .foregroundColor(.inkPrimary)
            .monospacedDigit()
        }
        .frame(width: 220, height: 220)
        .animation(.hearth(.hearthSlow, reduceMotion: reduceMotion), value: ringPercent)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Setting up your family, \(ringPercent) percent complete")
    }

    private func warmupRow(_ step: WarmupStep) -> some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            HStack(spacing: .hearth400) {
                Text(step.label)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkPrimary)
                Spacer(minLength: .hearth300)
                if step.isSucceeded {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 22))
                        .foregroundColor(.statusInfo)
                }
            }

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(Color.borderHairline)
                    Capsule()
                        .fill(Color.accentOnCanvas)
                        .frame(width: geo.size.width * rowFraction(step))
                }
            }
            .frame(height: 4)
        }
        .animation(.hearth(.hearthBase, reduceMotion: reduceMotion), value: step)
    }

    private func rowFraction(_ step: WarmupStep) -> Double {
        if step.isFinished { return 1 }
        if step.isRunning { return 0.35 }
        return 0
    }

    /// Drives the ring. Built failure-first: EVERY branch below falls through
    /// to the same landing, and an absolute deadline bounds the whole screen —
    /// a missing endpoint, a dead network, or a wedged LLM call all end with
    /// the parent on "You're all set".
    private func runWarmup() async {
        guard !warmupStarted else { return }
        warmupStarted = true

        let started = Date()
        let deadline = started.addingTimeInterval(Self.ringDeadline)

        // Beat 1 IS the durable seed — mark it running so the ring shows real
        // motion (12%, the same maths the server uses) rather than a fake one.
        setLocalStep("family", to: "running")
        let seeded = await onSeed(collectedData())
        setLocalStep("family", to: seeded ? "done" : "failed")

        // Beats 2-4 are server-side. From here the payload drives the ring.
        if Date() < deadline, !accountID.isEmpty,
           let runID = await OnboardingWarmupService.enqueue(userID: accountID) {
            while Date() < deadline {
                if let status = await OnboardingWarmupService.status(runID: runID, userID: accountID) {
                    if !status.steps.isEmpty { ringSteps = status.steps }
                    ringPercent = status.percent
                    if status.isTerminal { break }
                }
                try? await Task.sleep(nanoseconds: UInt64(Self.ringPollInterval * 1_000_000_000))
            }
        }

        let elapsed = Date().timeIntervalSince(started)
        if elapsed < Self.ringMinimumDwell {
            try? await Task.sleep(nanoseconds: UInt64((Self.ringMinimumDwell - elapsed) * 1_000_000_000))
        }

        // Land at 100 whatever happened. This mirrors the backend, which also
        // reports 100 for a terminal run with failed beats: ONBOARDING is
        // complete either way — a degraded Home is the accepted failure mode.
        ringPercent = 100
        try? await Task.sleep(nanoseconds: 450_000_000)
        goTo(.allSet)
    }

    /// Local, pre-server step bookkeeping. Recomputes the percentage with the
    /// server's own formula (finished = 1, running = ½) so the number never
    /// jumps when the real payload takes over.
    private func setLocalStep(_ key: String, to state: String) {
        guard let index = ringSteps.firstIndex(where: { $0.key == key }) else { return }
        ringSteps[index] = WarmupStep(key: ringSteps[index].key, label: ringSteps[index].label, state: state)
        var score = 0.0
        for step in ringSteps {
            if step.isFinished { score += 1 } else if step.isRunning { score += 0.5 }
        }
        ringPercent = Int((100 * score / Double(max(ringSteps.count, 1))).rounded())
    }

    // MARK: - Screen: "You're all set"

    /// `Onboarding - welcome`. Everything on this frame is LEFT-aligned, the
    /// section headers are Fraunces **w600 28/32** (`hearthDisplayMD`) in
    /// sentence case, the recap lines are Inter 17/26 and the "waiting for
    /// you" lines Inter 15/22. The CTA is the **teal** button.
    private var allSetScreen: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: .hearth500) {
                funnelTitle("You're all set, \(firstName).", alignment: .leading)
                funnelSubtitle(
                    "Here's what we've got — and what's waiting for you and your family!",
                    alignment: .leading
                )

                allSetFamilySection
                allSetWaitingSection
                allSetCoachSection
            }
            .padding(.horizontal, .hearth700)
            .padding(.top, .hearth900)
            .padding(.bottom, .hearth700)
        }
        // Same never-overlaps contract as the Heisman scaffold.
        .safeAreaInset(edge: .bottom) {
            primaryButton("Take me home", disabled: false, fill: .accent) { onFinish() }
                .padding(.horizontal, .hearth700)
                .padding(.bottom, .hearth800)
                .padding(.top, .hearth400)
                .background(Color.bgSober)
        }
        .trackScreen("onboarding_all_set")
    }

    /// Fraunces w600 28/32, left. Reused by all three "all set" sections.
    private func allSetSectionHeader(_ text: String) -> some View {
        Text(text)
            .font(.hearthDisplayMD)
            .foregroundColor(.inkDisplay)
            .lineSpacing(.hearthLineDisplayMD)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    @ViewBuilder
    private var allSetFamilySection: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            allSetSectionHeader("Your family")
            if !familyLine.isEmpty { recapLine(familyLine) }
            if !kidsLine.isEmpty { recapLine(kidsLine) }
            if !draft.postalCode.trimmed.isEmpty { recapLine(draft.postalCode.trimmed) }
        }
        .padding(.top, .hearth400)
    }

    @ViewBuilder
    private var allSetWaitingSection: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            allSetSectionHeader("Here's what's waiting for you:")
            ForEach(waitingForYou, id: \.self) { line in
                Text(line)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkDisplay)
                    .lineSpacing(.hearthLineBodyMD)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding(.top, .hearth500)
    }

    /// The coach voice/personality pickers — the values are real and there
    /// is no other funnel surface for them, so they stay here.
    @ViewBuilder
    private var allSetCoachSection: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            allSetSectionHeader("MVP coach settings")
            Text("Set up how you want the coach to respond")
                .font(.hearthBodySM)
                .foregroundColor(.inkDisplay)
            pillSelect(
                placeholder: "Voice",
                value: draft.coachVoice,
                options: coachVoiceOptions
            ) { draft.coachVoice = $0 }
            pillSelect(
                placeholder: "Personality",
                value: draft.coachPersonality,
                options: coachPersonalityOptions
            ) { draft.coachPersonality = $0 }
        }
        .padding(.top, .hearth500)
    }

    private func recapLine(_ text: String) -> some View {
        Text(text)
            .font(.hearthBodyLG)
            .foregroundColor(.inkDisplay)
            .lineSpacing(.hearthLineBodyLG)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    /// "Single parent" — the household line. Household is no longer asked in
    /// the funnel, so it is only appended when a value actually exists (a
    /// resumed v4 draft, or one edited in the profile editor).
    private var familyLine: String {
        [draft.household, draft.primaryLanguage]
            .map { $0.trimmed }
            .filter { !$0.isEmpty }
            .joined(separator: " · ")
    }

    /// "Ben, 5 · Lily, 2"
    private var kidsLine: String {
        draft.kids
            .filter { !$0.name.trimmed.isEmpty }
            .map { kid in
                let age = kid.age.trimmed
                return age.isEmpty ? kid.name.trimmed : "\(kid.name.trimmed), \(age)"
            }
            .joined(separator: " · ")
    }

    private var waitingForYou: [String] {
        let names = draft.kids.map { $0.name.trimmed }.filter { !$0.isEmpty }
        let coachLine: String
        switch names.count {
        case 0:  coachLine = "A coach who already knows your family"
        case 1:  coachLine = "A coach who already knows \(names[0])"
        case 2:  coachLine = "A coach who already knows \(names[0]) and \(names[1])"
        default: coachLine = "A coach who already knows \(names.dropLast().joined(separator: ", ")) and \(names[names.count - 1])"
        }
        return [
            coachLine,
            "Expert-backed articles, filtered for your family",
            "A community of parents who get it",
            "Advice built around what you're actually dealing with"
        ]
    }

    // MARK: - Shared components (post-auth tail screens)

    /// The tail runs TWO display scales and one shared token cannot serve
    /// both — see the beta-v1 fidelity notes.
    private enum FunnelTitleScale {
        /// 56 / 60, ls -1.12 — "You're all set, Gregory."
        case hero
        /// 38 / 40, ls -0.38
        case compact

        var font: Font {
            switch self {
            case .hero:    return .hearthDisplayXL
            case .compact: return .hearthDisplaySM
            }
        }

        var tracking: CGFloat {
            switch self {
            case .hero:    return -1.12
            case .compact: return -0.38
            }
        }

        var lineSpacing: CGFloat {
            switch self {
            // SwiftUI lineSpacing ADDS to the font's natural line height, and
            // Fraunces at 56 is already ~67/line against the frame's 60. Zero
            // is the closest a SwiftUI Text can get (a negative is clamped).
            case .hero:    return 0
            case .compact: return 2
            }
        }
    }

    private func funnelTitle(
        _ text: String,
        scale: FunnelTitleScale = .hero,
        alignment: HorizontalAlignment = .center
    ) -> some View {
        Text(text)
            .font(scale.font)
            .tracking(scale.tracking)
            .foregroundColor(.inkDisplay)
            .multilineTextAlignment(alignment == .leading ? .leading : .center)
            .lineSpacing(scale.lineSpacing)
            .lineLimit(3)
            .minimumScaleFactor(0.6)
            .frame(maxWidth: .infinity, alignment: alignment == .leading ? .leading : .center)
    }

    private func funnelSubtitle(
        _ text: String,
        alignment: HorizontalAlignment = .center,
        maxWidth: CGFloat? = nil
    ) -> some View {
        Text(text)
            .font(.hearthBodyMD)
            .foregroundColor(.inkDisplay)
            .multilineTextAlignment(alignment == .leading ? .leading : .center)
            .lineSpacing(.hearthLineBodyMD)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: maxWidth ?? .infinity, alignment: alignment == .leading ? .leading : .center)
            .frame(maxWidth: .infinity, alignment: alignment == .leading ? .leading : .center)
    }

    // MARK: Funnel input chrome (the "all set" dropdowns)

    /// The two grounds the pre-Heisman frames used; the "all set" dropdowns
    /// are paper.
    private enum PillGround {
        case cream
        case paper

        var fill: Color {
            switch self {
            case .cream: return .bgCoachBanner
            case .paper: return .bgElevated
            }
        }
    }

    /// Placeholder + value type on the funnel inputs: Inter 20, weight 300.
    private static let pillInputFont = Font.hearthTitleLG.weight(.light)

    private func pillSelect(
        placeholder: String,
        value: String,
        options: [String],
        ground: PillGround = .paper,
        onPick: @escaping (String) -> Void
    ) -> some View {
        Menu {
            ForEach(options, id: \.self) { option in
                // A `Menu` tap never resigns a focused TextField's first-
                // responder status, so dismiss the keyboard here.
                Button(option) { hideKeyboard(); onPick(option) }
            }
        } label: {
            HStack(spacing: .hearth400) {
                Spacer(minLength: 0)
                Text(value.isEmpty ? placeholder : value)
                    .font(Self.pillInputFont)
                    .foregroundColor(value.isEmpty ? .inkMuted : .inkPrimary)
                    .lineLimit(1)
                Spacer(minLength: 0)
                Image(systemName: "chevron.down")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.inkMuted)
            }
            .padding(.horizontal, .hearth800)
            .padding(.vertical, .hearth400)
            .frame(maxWidth: .infinity)
            .background(ground.fill)
            .clipShape(Capsule())
            .overlay(Capsule().stroke(Color.borderInputPill, lineWidth: 1))
        }
        .simultaneousGesture(TapGesture().onEnded { hideKeyboard() })
        .accessibilityLabel(value.isEmpty ? placeholder : value)
    }

    /// The charcoal/teal primary button the post-auth tail keeps.
    private enum ButtonFill {
        case funnel
        case accent

        var color: Color {
            switch self {
            case .funnel: return .bgButtonFunnel
            case .accent: return .accentDefault
            }
        }
    }

    private func primaryButton(
        _ label: String,
        disabled: Bool,
        fill: ButtonFill = .funnel,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            Text(label)
                .font(.hearthSectionHeader)
                .foregroundColor(disabled ? .inkSecondary : .inkOnPhotoLight)
                .frame(maxWidth: .infinity)
                .padding(.vertical, .hearth400)
                .background(disabled ? Color.bgDisabled : fill.color)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous))
        }
        .disabled(disabled)
    }

    // MARK: - Derived values

    private var firstName: String {
        let trimmed = draft.parentName.trimmed
        return trimmed.isEmpty ? "there" : trimmed
    }

    /// Builds the `/profile/seed` payload. The fields the funnel stopped
    /// asking go out EMPTY rather than disappearing — the contract test pins
    /// the keys; the Heisman additions are additive.
    private func collectedData() -> OnboardingData {
        let kidData = draft.kids
            .filter { !$0.name.trimmed.isEmpty }
            .map { kid in
                (
                    name: kid.name.trimmed,
                    age: kid.age.trimmed,   // age stays a STRING — pinned
                    temperament: kid.temperament,
                    pronouns: "",
                    gradeBand: kid.gradeBand,
                    gender: kid.gender
                )
            }
        // The free-text note rides as one more task string.
        var weekTasks = draft.parentTasks
        let note = draft.parentTasksNote.trimmed
        if !note.isEmpty { weekTasks.append(note) }
        return OnboardingData(
            parentName: draft.parentName.trimmed,
            kids: kidData,
            household: draft.household,
            supportSystem: "",
            energyPattern: "",
            dreadedMoment: "",
            challenges: draft.challenges,
            goals: draft.goals,
            postalCode: draft.postalCode.trimmed,
            country: "",
            primaryLanguage: draft.primaryLanguage,
            parentAgeRange: "",
            adultsInHousehold: nil,
            employment: "",
            culturalBackground: "",
            pronouns: "",
            secondaryLanguage: draft.secondaryLanguage,
            educationStyle: draft.educationStyle,
            familyActivities: draft.familyActivities,
            coachVoice: draft.coachVoice,
            coachPersonality: draft.coachPersonality,
            topic: draft.topic,
            parentWeekTasks: weekTasks,
            extractedActivities: draft.extractedActivities
        )
    }
}

// MARK: - String Helper

private extension String {
    var trimmed: String { trimmingCharacters(in: .whitespacesAndNewlines) }
    // `capitalizedFirst` lives on the app-wide `String` extension in
    // HomeDashboardService.swift — do not redeclare it here.
}
