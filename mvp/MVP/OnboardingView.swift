import SwiftUI

// MARK: - Onboarding Data (sent to backend)
//
// UNCHANGED SHAPE, deliberately. beta-v1 cut three screens from the funnel
// (demographics, energy/dread, support crew) but the backend fields STAY —
// the Coach now learns them conversationally. So every property below survives
// and the ones the funnel no longer asks simply arrive empty. `/profile/seed`'s
// wire contract is pinned by tests/test_onboarding_seed_contract.py; do not
// drop keys here to "tidy up".

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
    let postalCode: String          // Phase-3 Figma delta: RESTORED — Chief-of-Staff activity discovery needs it
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
}

// MARK: - Onboarding View

/// The beta-v1 funnel. Nine *kinds* of screen, but a DYNAMIC number of them:
/// the parent says how many children they have and the flow grows one screen
/// per child.
///
///   plan → signIn → splash → acquainted → kidCount → kid(0) … kid(n-1)
///        → mind → freeTime → warmup (the progress ring) → allSet
///
/// 2026-08-09: the entry order INVERTED again. Miguel's 1:47pm Figma
/// screenshot showed the canvas order as `choose a plan` → `create your
/// account` → `Onboarding - 001` — the paywall and sign-in now come FIRST,
/// with the branded splash as a post-auth interstitial before the actual
/// questions start. This retires the "sign-in at the end" architecture from
/// the prior pass; see the deleted `cameToSignInFromSplash` machinery this
/// replaced.
///
/// Two structural rules make the dynamic count safe:
///
///  1. `flow` is COMPUTED from `draft.kids.count`, and `draft.stepIndex` is a
///     position in it. Forward moves name their destination (`goTo(.mind)`)
///     rather than incrementing, so reshaping the flow can never land the
///     parent on the wrong screen. Back is `stepIndex - 1`, which walks the
///     computed array and therefore handles n children for free.
///  2. `includesSignInStep` is captured ONCE at init. It must not be derived
///     from live auth state: signing in would shrink the flow underneath the
///     current index.
///
/// Sign-in now lives INSIDE the funnel (Greg's "Securing your family's space"),
/// which means every answer is collected before an account exists. That is only
/// safe because of `OnboardingDraft` — see the durability notes on that type.
struct OnboardingView: View {

    // MARK: Inputs

    /// Whether the funnel must present the sign-in screen. Captured into state
    /// at init; see rule 2 above.
    var signInRequired: Bool

    /// Called the moment sign-in resolves an account. The app persists the
    /// account id, and when the account ALREADY has a profile (same parent, new
    /// device or reinstall) it ends onboarding immediately — this view is torn
    /// down mid-funnel by design.
    var onSignedIn: (AuthService.SignInOutcome) -> Void

    /// Stash + POST `/profile/seed`. Returns true once the server confirmed a
    /// 200. Called from the ring screen, which is the beat Greg labels "Getting
    /// to know your family". A false return is NOT fatal: the payload stays
    /// durable in `pending_seed_body` and the next launch retries it.
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
        _includesSignInStep = State(initialValue: signInRequired)
        // Resume an abandoned funnel. `load` returns nil on a clean install and
        // on an undecodable draft, both of which mean "start at the splash"…
        // except `flow`'s very first step is `.plan` now, not `.splash` — see
        // `isFreshDraft`.
        let loaded = OnboardingDraft.load()
        _draft = State(initialValue: loaded ?? OnboardingDraft())
        _isFreshDraft = State(initialValue: loaded == nil)
    }

    // MARK: State

    /// The ONE piece of funnel state. Every answer and the current position
    /// live here, and a single `.onChange` below persists the whole thing on
    /// every mutation — so there is no way to add a field that isn't durable.
    @State private var draft: OnboardingDraft
    @State private var includesSignInStep: Bool

    /// True when `init` found NOTHING on disk — a genuinely fresh install,
    /// not a draft resuming from some earlier version of `flow`. A brand-new
    /// `OnboardingDraft()` and a STORED v1/v2 draft that happens to read
    /// `stepIndex == 0, flowVersion == 1` are otherwise indistinguishable at
    /// the struct level (both are Swift's default values), and `resumeIfNeeded`
    /// used to treat every `flowVersion < current` draft as something to
    /// migrate. That was harmless before 2026-08-09 because `.splash` sat at
    /// index 0 in every prior flow, so remapping a fresh `stepIndex == 0`
    /// onto "wherever `.splash` is now" was a no-op. It stopped being a no-op
    /// the moment `.plan` took index 0 instead: a brand-new install got
    /// migrated straight past the paywall and sign-in onto the splash. Real
    /// migrations only make sense for a draft that was actually SAVED under
    /// an older `flow` shape; this flag lets `resumeIfNeeded` skip them
    /// entirely for one that wasn't.
    @State private var isFreshDraft: Bool

    /// The resolved account id, written by `onSignedIn` via SwayApp. Read here
    /// (never written) so the warm-up can authenticate.
    @AppStorage("user_name") private var accountID = ""

    // Ring state
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
    // Reused verbatim from the pre-beta funnel; their labels already match
    // Greg's chips. The lists the redesign STOPPED asking (parent age,
    // employment, pronouns, energy, dread, support crew) are gone from this
    // file entirely — the Coach gathers them conversationally now.

    // Language is NOT asked by any sprint-1 frame. `draft.primaryLanguage` /
    // `draft.secondaryLanguage` stay on the draft and keep being seeded — the
    // parent-profile editor is where they are edited now (Miguel's call
    // 2026-08-08: match the screens, keep the data). No options list is needed
    // here because no funnel screen renders a language picker.

    private let householdOptions = [
        "Two-parent home", "Single parent", "Co-parenting",
        "Blended family", "Extended family", "It's complicated"
    ]

    /// "Education style" on "Let's get acquainted". The design's own option list
    /// is a loose note on the Figma page (it appears in no frame):
    /// `Public Private Home school Charter Montessori Waldorf Forest Other`.
    /// Charter and Forest were missing and are added; the existing labels keep
    /// their exact spelling so a value a beta parent already picked still
    /// matches an option.
    private let educationStyleOptions = [
        "Public school", "Private school", "Homeschool", "Charter",
        "Montessori", "Waldorf", "Forest school", "Other"
    ]

    private let gradeBandOptions = [
        "Pre-K", "K", "1", "2", "3", "4", "5",
        "6", "7", "8", "9", "10", "11", "12", "N/A"
    ]

    /// Phase-3 Figma delta — the new "free time" screen's 3x3 icon grid.
    /// Greg's frame repeats Nature and Parks twice; that's a Figma placeholder
    /// artifact, not a spec — this is the clean, distinct list. SINGLE SOURCE:
    /// `ProfileOptions.familyActivityOptions`, which the beta-v1 account
    /// sheet's "Family interests" grid also reads (see
    /// `patterns_onboarding_parity`).
    private var freeTimeOptions: [(label: String, symbol: String)] {
        ProfileOptions.familyActivityOptions
    }

    /// Phase-3 Figma delta — "Set up how you want the coach to respond" on the
    /// final "all set" screen.
    private let coachVoiceOptions = [
        "Default - Male", "Default - Female", "Warm - Male", "Warm - Female"
    ]
    private let coachPersonalityOptions = [
        "Default - Genuine", "Direct - Coach", "Gentle - Nurturing", "Playful - Upbeat"
    ]

    /// Personality chips. SINGLE SOURCE: `ProfileOptions.temperamentChips` in
    /// ProfileEditorViews.swift, which the kid-settings sheet also reads. The
    /// funnel must not keep its own copy — a temperament picked at signup has to
    /// still be findable when the parent later edits it, and two independently
    /// maintained lists are exactly how that drifts apart
    /// (see `patterns_onboarding_parity`).
    ///
    /// The kid frames (`kids c` / `kids f`) show exactly three chips, in this
    /// order. FILTER, never a second array: the shared list keeps all six for
    /// the kid-settings sheet, and a temperament set there still renders here.
    private static let funnelTemperamentLabels = ["Easy-going", "Sensitive", "Spirited"]

    private var temperamentOptions: [(label: String, symbol: String)] {
        Self.funnelTemperamentLabels.compactMap { label in
            ProfileOptions.temperamentChips.first { $0.label == label }
        }
    }

    /// `Onboarding - need help with dynamics` shows six tag items in ONE
    /// section. FILTER of `ProfileOptions.challengeChips`, which keeps all ten —
    /// the other four (picky eating, sibling rivalry, behavior changes,
    /// work-life balance) still feed Coach context and are edited in the
    /// parent-profile editor.
    private static let funnelChallengeLabels = [
        "Morning routines", "Bedtime battles", "Big emotions",
        "Screen time", "School struggles", "Feeling alone in it"
    ]

    private var challengeOptions: [(label: String, symbol: String)] {
        Self.funnelChallengeLabels.compactMap { label in
            ProfileOptions.challengeChips.first { $0.label == label }
        }
    }

    // The "What would help" goals section appears in NO sprint-1 frame, so the
    // funnel no longer renders it. `draft.goals` stays on the draft, keeps being
    // seeded, and is edited via the parent-profile editor's "Goals" chip row;
    // the suggested labels live on `ProfileOptions.goalChips`.

    // MARK: - Flow

    enum Step: Equatable {
        /// "choose a plan" (`754:4897`) — Miguel's explicit smoke-and-mirrors
        /// ask, 2026-08-09. Now the FIRST screen a fresh install ever sees; see
        /// `planScreen`. UNCONDITIONAL — inserted whether or not `.signIn` is
        /// in this run's flow (a returning parent mid-funnel still sees it).
        case plan
        case signIn
        case splash
        case acquainted
        case kidCount
        case kid(Int)
        case mind
        case freeTime
        case warmup
        case allSet
    }

    /// The screen order, recomputed from the collected child count.
    ///
    /// 2026-08-09: re-inverted to match the current Figma canvas order —
    /// `choose a plan` → `create your account` → `Onboarding - 001` (splash)
    /// → the questionnaire. The paywall and sign-in now happen BEFORE any
    /// question is asked, and the branded splash is a post-auth interstitial,
    /// not a fork with its own CTAs.
    private var flow: [Step] {
        var steps: [Step] = [.plan]
        // Conditional exactly as before — an already-authenticated parent
        // resuming mid-funnel (stored credential on this device) skips it.
        if includesSignInStep { steps.append(.signIn) }
        steps.append(contentsOf: [.splash, .acquainted, .kidCount])
        for index in draft.kids.indices { steps.append(.kid(index)) }
        // Order per the frames' own "Next:" hints — the last kid screen says
        // "Next: Family Challenges" (`.mind`), and BOTH "need help with…" frames
        // say "Next: Meet the coach". `.freeTime` used to sit here, ahead of
        // `.mind`, while the kid screen's Continue jumped straight to `.mind` —
        // so the free-time screen was unreachable going forward and could only
        // be seen by pressing Back.
        steps.append(contentsOf: [.mind, .freeTime, .warmup, .allSet])
        return steps
    }

    private var currentStep: Step {
        let steps = flow
        guard !steps.isEmpty else { return .splash }
        return steps[min(max(draft.stepIndex, 0), steps.count - 1)]
    }

    private func goTo(_ step: Step) {
        guard let index = flow.firstIndex(of: step) else { return }
        withAnimation(.hearth(.hearthSlow, reduceMotion: reduceMotion)) {
            draft.stepIndex = index
        }
    }

    /// Advances to the step immediately AFTER the current one in the computed
    /// flow. Used by every "just continue, nothing else happens" callback
    /// (`.plan`'s Buy buttons, `.splash`'s auto-advance and tap-to-skip,
    /// `.signIn`'s post-auth hand-off) so none of them hardcode a destination
    /// that a flow reshape could silently invalidate. Clamped to the last step
    /// rather than going out of bounds.
    private func goToNext() {
        let steps = flow
        let next = min(draft.stepIndex + 1, steps.count - 1)
        withAnimation(.hearth(.hearthSlow, reduceMotion: reduceMotion)) {
            draft.stepIndex = next
        }
    }

    /// Back walks the computed flow, so it handles n children with no special
    /// cases: from `kid(0)` it lands on `kidCount`, from `mind` it lands on the
    /// LAST child (or on `kidCount` when there are none).
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
            Color.bgCanvas.ignoresSafeArea()

            Group {
                switch currentStep {
                case .splash:      splashScreen
                case .acquainted:  acquaintedScreen
                case .kidCount:    kidCountScreen
                case .kid(let i):  kidScreen(i)
                case .freeTime:    freeTimeScreen
                case .mind:        mindScreen
                case .signIn:      signInScreen
                case .plan:        planScreen
                case .warmup:      warmupScreen
                case .allSet:      allSetScreen
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

    /// Clamps a resumed `stepIndex` back onto a screen it is safe to land on.
    /// Two hazards, both only reachable by relaunching mid-funnel:
    ///
    ///  1. **Never past the ring.** The ring screen is what fires the seed. A
    ///     draft saved at `.allSet`, or one whose index drifted because this
    ///     launch no longer needs the sign-in screen (the flow is one shorter),
    ///     would otherwise land on the landing page with the family never
    ///     POSTed. Re-entering the ring is cheap and idempotent: a confirmed
    ///     seed flushes as a no-op and the warm-up dedupes onto its live run.
    ///  2. **Never past sign-in without an account.** Nothing downstream has an
    ///     identity to authenticate with.
    private func resumeIfNeeded() {
        guard !didResume else { return }
        didResume = true

        // Both migrations below exist to correct a STORED draft written under
        // an older `flow` shape. A brand-new `OnboardingDraft()` — nothing on
        // disk at all — is indistinguishable from one of those at the struct
        // level (both read `stepIndex == 0, flowVersion == 1`, Swift's default
        // values), and until 2026-08-09 that ambiguity was harmless: `.splash`
        // sat at index 0 in every flow shape this app has ever shipped, so
        // "migrating" a fresh stepIndex of 0 was a no-op. It stopped being a
        // no-op the moment `.plan` took index 0 instead — the v2→v3 block
        // below would otherwise walk a genuinely fresh install straight past
        // the paywall and sign-in onto the splash. `isFreshDraft` (set once,
        // in `init`, from whether `OnboardingDraft.load()` found anything)
        // is what tells these two apart; skip both migrations entirely for a
        // fresh draft; it already reads `flowVersion == 1` correctly, so its
        // ONLY job here is to be stamped up to the current version.
        if isFreshDraft {
            draft.flowVersion = 3
        } else {
            // v1 → v2 draft migration (2026-08-09): the `.plan` step landed
            // directly before `.warmup`, so any v1 index that meant "at warmup"
            // or "at allSet" now points one step EARLY in the v2 `flow` (at
            // `.plan` or `.warmup` respectively) unless corrected. `flowVersion`
            // defaults to 1 for any draft saved before this change (the key is
            // simply absent from its JSON — see the field's doc comment), so
            // this block only ever fires once per draft, and only for
            // pre-`.plan` drafts.
            if draft.flowVersion < 2 {
                if let warmupIndex = flow.firstIndex(of: .warmup) {
                    let oldWarmupIndex = warmupIndex - 1 // `.plan`'s new slot == where `.warmup` used to sit
                    if draft.stepIndex >= oldWarmupIndex {
                        draft.stepIndex += 1
                    }
                }
                draft.flowVersion = 2
            }

            // v2 → v3 draft migration (2026-08-09): `.plan` and `.signIn` moved
            // from the END of the funnel to the START, with `.splash` becoming
            // a post-auth interstitial in between. This is a REORDER, not an
            // insertion, so a positional shift (like the v1→v2 block above)
            // can't work — every v2 index has to be re-homed onto the SAME
            // NAMED STEP in the new flow. Reconstructing the OLD v2 order here
            // (rather than storing it) keeps there being exactly one `flow`
            // definition to maintain.
            if draft.flowVersion < 3 {
                var old: [Step] = [.splash, .acquainted, .kidCount]
                for i in draft.kids.indices { old.append(.kid(i)) }
                old.append(contentsOf: [.mind, .freeTime])
                if includesSignInStep { old.append(.signIn) }
                old.append(contentsOf: [.plan, .warmup, .allSet])

                let clamped = min(max(draft.stepIndex, 0), old.count - 1)
                let oldStep = old[clamped]
                // `includesSignInStep` is THIS run's value, which can differ
                // from the run that saved the draft (e.g. they authenticated
                // mid-funnel, then relaunched with a stored credential —
                // `.signIn` drops out of both the old and new reconstructions
                // the same way). Same approximation the v1→v2 migration
                // already makes. Worst case the parent lands one screen early
                // in the new order — never on a step that no longer exists,
                // since every v2 step name still exists in v3's `flow`.
                draft.stepIndex = flow.firstIndex(of: oldStep) ?? 0
                draft.flowVersion = 3
            }
        }

        if let warmupIndex = flow.firstIndex(of: .warmup), draft.stepIndex > warmupIndex {
            draft.stepIndex = warmupIndex
        }
        if accountID.isEmpty, includesSignInStep,
           let signInIndex = flow.firstIndex(of: .signIn),
           draft.stepIndex > signInIndex {
            draft.stepIndex = signInIndex
        }
    }

    // MARK: - Screen: splash

    /// `Onboarding - 001` (`754:4312`), re-extracted 2026-08-09 after the
    /// design changed since the morning pass (the pencils-in-a-cup
    /// illustration is gone; this is a different trophy-mug mark). The splash
    /// is now a POST-AUTH interstitial, not a fork with its own CTAs — the
    /// frame draws no buttons, and it no longer needs any: sign-in and the
    /// paywall both happen BEFORE this screen now (see `flow`), so there is
    /// no "returning parent stranded" case left to solve with a second CTA.
    /// It auto-advances after a beat, and a tap skips the wait — the same
    /// self-guarding pattern (`currentStep == .splash` re-checked inside the
    /// sleep) means the two triggers can never double-advance.
    ///
    /// This is the ONE designed splash. The native `LaunchScreen.storyboard`
    /// (shown before this SwiftUI view even mounts) is a separate concern —
    /// it targets `PaywallView.titleBlock`'s wordmark position now, not this
    /// screen, since the paywall is the first SwiftUI screen on a fresh
    /// install. If `flow`'s first step changes again, re-anchor the
    /// storyboard to match — see its own comment for why.
    private var splashScreen: some View {
        ZStack {
            Color.bgSober.ignoresSafeArea()
            RadialGradient(
                colors: [Color.bgElevated, Color.bgSober],
                center: .center, startRadius: 0, endRadius: 300
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

                // Measured `Layer_1` (`1099:5262`) 276x375: the trophy-mug
                // mark and the "MVP" wordmark are ONE flattened vector graphic
                // in the current file — not separable text + icon the way the
                // morning's illustration was. Exported once via the Images
                // API at @3x.
                Image("OnboardingSplashMark")
                    .resizable()
                    .scaledToFit()
                    .frame(width: 276, height: 375)
                    .accessibilityHidden(true)

                // Measured `Frame 204973884`: Inter w700 **30.68/25.1**,
                // UPPERCASE, centered, `#1E1E1E` (`inkDisplay`). No existing
                // token sits at this size — composed directly, same pattern as
                // `SignInView.cardTitleFont` for a measured-but-untokenized
                // size. `hearth600` gap to the mark above is a visual judgment
                // call (the two are independent layers with no measured gap
                // between them), same as before.
                Text("Most Valuable Parent")
                    .font(.custom(HearthFontFamily.sans, size: 31, relativeTo: .title2).weight(.bold))
                    .textCase(.uppercase)
                    .foregroundColor(.inkDisplay)
                    .multilineTextAlignment(.center)
                    .padding(.top, .hearth600)
                    .accessibilityAddTraits(.isHeader)

                Spacer()
            }
        }
        .contentShape(Rectangle())
        .onTapGesture { goToNext() }
        .task {
            try? await Task.sleep(for: .seconds(1.7))
            if currentStep == .splash { goToNext() }
        }
        .trackScreen("onboarding_splash")
    }

    // MARK: - Screen: "Let's get acquainted"

    private var acquaintedScreen: some View {
        funnelScreen(
            caption: nil,
            showsHeader: false,
            hint: "Next: Your Children",
            continueDisabled: draft.parentName.trimmed.isEmpty,
            disabledHint: "Add your name to continue",
            onContinue: { goTo(.kidCount) }
        ) {
            funnelTitle("Let's get acquainted")
            funnelSubtitle("A few quick questions so we can make MVP feel like it was made for your family.")

            // FOUR fields, in the frame's order. The name field alone sits on
            // the cream ground (`#FCFBF8`); the three dropdowns are paper.
            fieldGroup("What should we call you?") {
                pillField(
                    "Your first name",
                    text: $draft.parentName,
                    ground: .cream,
                    textContentType: .givenName
                )
            }

            fieldGroup("Your household") {
                pillSelect(
                    placeholder: "Your situation",
                    value: draft.household,
                    options: householdOptions
                ) { draft.household = $0 }
            }

            fieldGroup("Education style") {
                pillSelect(
                    placeholder: "Choose",
                    value: draft.educationStyle,
                    options: educationStyleOptions
                ) { draft.educationStyle = $0 }
            }

            fieldGroup("Location") {
                pillField(
                    "000000",
                    text: $draft.postalCode,
                    ground: .paper,
                    keyboard: .numbersAndPunctuation,
                    textContentType: .postalCode
                )
            }
        }
        .trackScreen("onboarding_acquainted")
    }

    // MARK: - Screen: "Hi {name}!"

    private var kidCountScreen: some View {
        funnelScreen(
            caption: "\(firstName)'s children",
            hint: "Next: Child One",
            continueDisabled: !(1...12).contains(kidCountValue),
            // Measured (`kids a` Frame1 gap22): title, subtitle, the count
            // field, and its caption are FOUR siblings under one uniform gap —
            // `hearth600` (20) is the nearest reachable step. The shipped
            // build used the funnel's default `hearth500` (16) PLUS a
            // redundant per-field top pad, which pulled the count field much
            // too far from the subtitle above it.
            spacing: .hearth600,
            onContinue: {
                syncKidsToCount()
                goTo(.kid(0))
            }
        ) {
            Spacer(minLength: .hearth900)
            funnelTitle("Hi \(firstName)!")
            funnelSubtitle("Now let's meet your kids. We just need their names, ages, and a sense of who they are.")

            pillField("0", text: $draft.kidCountText, ground: .paper, keyboard: .numberPad)

            Text("How many children?")
                .font(.hearthBodyMD)
                .foregroundColor(.inkSecondary)
                .frame(maxWidth: .infinity)

            Spacer(minLength: .hearth900)
        }
        .trackScreen("onboarding_kid_count")
    }

    private var kidCountValue: Int { Int(draft.kidCountText.trimmed) ?? 0 }

    /// Grow/shrink the collected children to match the typed count, preserving
    /// anything already entered. Called on the way OUT of the count screen, so
    /// `flow` only ever reshapes between screens.
    private func syncKidsToCount() {
        let target = min(max(kidCountValue, 0), 12)
        if draft.kids.count < target {
            draft.kids.append(contentsOf: (draft.kids.count..<target).map { _ in OnboardingDraft.Kid() })
        } else if draft.kids.count > target {
            draft.kids.removeLast(draft.kids.count - target)
        }
    }

    // MARK: - Screen: one per child

    private func kidScreen(_ index: Int) -> some View {
        // Defensive: `flow` and `draft.kids` are derived from the same array, so
        // this can only trip if state is mutated between the two reads.
        let safeIndex = min(index, max(draft.kids.count - 1, 0))

        return funnelScreen(
            caption: Self.childLabel(safeIndex),
            // `kids f` / `kids g` label the last child's hint "Next: Family
            // Challenges" — the free-time screen sits between them in the app's
            // flow, so name the screen the parent actually lands on.
            hint: safeIndex + 1 < draft.kids.count
                ? "Next: \(Self.childLabel(safeIndex + 1))"
                : "Next: Family Challenges",
            continueDisabled: draft.kids.indices.contains(safeIndex)
                ? draft.kids[safeIndex].name.trimmed.isEmpty
                : true,
            disabledHint: "Add their name to continue",
            onContinue: {
                if safeIndex + 1 < draft.kids.count {
                    goTo(.kid(safeIndex + 1))
                } else {
                    goTo(.mind)
                }
            }
        ) {
            // Measured (`kids c` Frame21 gap12): title → subtitle. The funnel's
            // default content spacing (`hearth500`, 16) is tuned for the
            // BLOCK-level gaps below (subtitle → rule → fields, all 24 in the
            // frame) — grouping title+subtitle here keeps their own tighter
            // gap from being swallowed by that outer rhythm.
            VStack(spacing: .hearth400) {
                funnelTitle("Tell us about\nyour \(Self.ordinalWord(safeIndex))")
                funnelSubtitle(
                    safeIndex == 0
                        ? "Just the basics for now — we'll learn more as we go."
                        : "Same deal — name, age, and a little of their personality.",
                    maxWidth: 320
                )
            }
            centeredRule

            if draft.kids.indices.contains(safeIndex) {
                kidFields(safeIndex)
            }
        }
        .trackScreen("onboarding_child")
    }

    /// Extracted so the kid screen's body stays short enough for the type
    /// checker (a long `funnelScreen` closure is what makes it time out).
    @ViewBuilder
    private func kidFields(_ index: Int) -> some View {
        // Inter w900 24 in the frame; `hearthTitleLG` is the 20pt Inter step —
        // see the report note, there is no 24pt Inter token.
        Text(Self.childLabelSentence(index).capitalizedFirst)
            .font(.hearthTitleLG.weight(.black))
            .foregroundColor(.inkDisplay)
            .frame(maxWidth: .infinity)

        // Measured (`kids c` Frame1 gap22): heading → the fields block below.
        // The outer content VStack already contributes the funnel's default
        // `hearth500` (16); `hearth200` (4) composes to 20, the nearest
        // reachable step to 22 — the shipped `hearth500` top-pad here doubled
        // up with that outer spacing and landed at 32, nearly 50% too loose.
        VStack(spacing: .hearth300) {
            subFieldLabel("What should we call them?")
            pillField(
                "Name",
                text: $draft.kids[index].name,
                ground: .paper,
                textContentType: .givenName
            )
        }
        .padding(.top, .hearth200)

        // Frame10 measures 45 here — but the frame is 956pt on an 874pt phone,
        // and honoring all three 45s pushes the temperament chips under the
        // footer. 16+outer 16 = 32 is the largest equal gap that keeps the whole
        // screen above the fold; the three block gaps stay EQUAL, which is the
        // rhythm the frame actually encodes.
        VStack(spacing: .hearth300) {
            subFieldLabel("How old are they?")
            pillField("0", text: $draft.kids[index].age, ground: .paper, keyboard: .numberPad)
        }
        .padding(.top, .hearth500)

        // The "About child N" eyebrow and its two tag rows are ONE tight
        // group in the frame (`Frame204973871` gap6) — they used to be three
        // loose top-level items sharing the outer content VStack's `hearth500`
        // spacing, which read as three separate sections instead of one.
        // `hearth200` (4) is the nearest token to the measured 6. The group's
        // own top pad composes with the outer `hearth500` to 48, matching the
        // age-group gap above (measured 45, same as the name→age gap).
        VStack(alignment: .leading, spacing: .hearth200) {
            Text("About \(Self.childLabelSentence(index))")
                .font(.hearthBodySMBold)
                .foregroundColor(.inkDisplay)
                .frame(maxWidth: .infinity, alignment: .leading)

            HStack(spacing: .hearth300) {
                tagSelect(
                    value: draft.kids[index].gradeBand,
                    placeholder: "Grade",
                    symbol: "graduationcap.fill",
                    options: gradeBandOptions
                ) { draft.kids[index].gradeBand = $0 }

                tagSelect(
                    value: draft.kids[index].gender.capitalizedFirst,
                    placeholder: "Gender",
                    symbol: "figure.child",
                    options: Self.genderOptions
                ) { draft.kids[index].gender = $0.lowercased() }
            }

            HStack(spacing: .hearth300) {
                ForEach(temperamentOptions, id: \.label) { option in
                    let selected = draft.kids[index].temperament == option.label
                    tagItem(label: option.label, symbol: option.symbol, selected: selected) {
                        draft.kids[index].temperament = selected ? "" : option.label
                    }
                }
            }
        }
        // Same 45→32 squeeze as the name→age gap above — the three must stay equal.
        .padding(.top, .hearth500)
    }

    /// Gender is a DROPDOWN in the frames, not a pair of chips — `kids e` / `kids g`
    /// render it as the same "tag choice" component as Grade, selected, reading
    /// "Boy" / "Girl" with a chevron. Stored lowercase, as before.
    private static let genderOptions = ["Boy", "Girl"]

    /// The frames' "tag choice": a tag-shaped dropdown. Unselected (no value) is
    /// the cream ground with a 0.5px teal outline; a chosen value flips to the
    /// teal FILL with the cream label — the same treatment as `tagItem`, so the
    /// two rows read as one control family.
    private func tagSelect(
        value: String,
        placeholder: String,
        symbol: String,
        options: [String],
        onPick: @escaping (String) -> Void
    ) -> some View {
        let chosen = !value.isEmpty
        return Menu {
            ForEach(options, id: \.self) { option in
                Button(option) { onPick(option) }
            }
        } label: {
            HStack(spacing: .hearth300) {
                Image(systemName: symbol)
                    .font(.system(size: 14, weight: .regular))
                    .foregroundColor(chosen ? .inkOnCard : .accentOnCanvas)
                Text(chosen ? value : placeholder)
                    .font(.hearthBodySM)
                    .foregroundColor(chosen ? .inkOnCard : .accentOnCanvas)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
                Image(systemName: "chevron.down")
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(chosen ? .inkOnCard : .accentOnCanvas)
            }
            .padding(.horizontal, .hearth500)
            .padding(.vertical, .hearth400)
            .frame(maxWidth: .infinity)
            .background(chosen ? Color.accentDefault : Color.bgCoachBanner)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusSheet, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: .hearthRadiusSheet, style: .continuous)
                    .stroke(Color.accentDefault, lineWidth: 0.5)
            )
        }
        .accessibilityLabel(chosen ? "\(placeholder): \(value)" : placeholder)
    }

    /// The frames' "tag item" on the kid screens: `#FCFBF8` fill, r=24,
    /// pad 12/16, a **0.5px** teal stroke, Inter w400 13 label in the accent.
    /// Selected is the teal fill with the cream label (`inkOnCard`, 4.74:1).
    ///
    /// Distinct from `mindTagItem`, which is the wider single-column variant on
    /// "What's on your mind?" — same shape, 17pt label, and a 1px
    /// `borderChipOutline` instead of the teal hairline.
    private func tagItem(
        label: String,
        symbol: String,
        selected: Bool,
        action: @escaping () -> Void
    ) -> some View {
        Button {
            withAnimation(.hearth(.hearthFast, reduceMotion: reduceMotion)) { action() }
        } label: {
            HStack(spacing: .hearth200) {
                Image(systemName: symbol)
                    .font(.system(size: 14, weight: .regular))
                    .foregroundColor(selected ? .inkOnCard : .accentOnCanvas)
                Text(label)
                    .font(.hearthBodySM)
                    .foregroundColor(selected ? .inkOnCard : .accentOnCanvas)
                    .lineLimit(1)
                    .minimumScaleFactor(0.7)
            }
            .padding(.horizontal, .hearth500)
            .padding(.vertical, .hearth400)
            .frame(maxWidth: .infinity)
            .background(selected ? Color.accentDefault : Color.bgCoachBanner)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusSheet, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: .hearthRadiusSheet, style: .continuous)
                    .stroke(Color.accentDefault, lineWidth: 0.5)
            )
        }
        .accessibilityAddTraits(selected ? [.isSelected] : [])
    }

    // MARK: - Screen: "What do you do in your free time?" (Phase-3 Figma delta)
    //
    // Greg's frame reads "What do you in your free time?" — missing a word.
    // This reproduces the intent, not the typo. Feeds Chief-of-Staff activity
    // discovery via `family_activities` in the seed body. Unlike every other
    // funnel screen this one has a Skip alongside Continue, so it gets its own
    // footer rather than reusing `funnelScreen`.

    private var freeTimeScreen: some View {
        VStack(spacing: 0) {
            funnelHeader(caption: "Almost there")

            ScrollView {
                // Measured (`need help with acitivities` Frame1 gap10): title →
                // subtitle. `hearth400` (12) is the nearest reachable step,
                // tighter than the funnel's default `hearth500`.
                VStack(spacing: .hearth400) {
                    funnelTitle("What do you do in your free time?", scale: .compact)
                    funnelSubtitle("Looking for more? Select what describes your family routine.")

                    LazyVGrid(
                        columns: Array(repeating: GridItem(.flexible(), spacing: .hearth300), count: 3),
                        spacing: .hearth300
                    ) {
                        ForEach(freeTimeOptions, id: \.label) { option in
                            let selected = draft.familyActivities.contains(option.label)
                            activityTile(label: option.label, symbol: option.symbol, selected: selected) {
                                if selected {
                                    draft.familyActivities.removeAll { $0 == option.label }
                                } else {
                                    draft.familyActivities.append(option.label)
                                }
                            }
                        }
                    }
                }
                .padding(.horizontal, .hearth700)
                .padding(.top, .hearth700)
                .padding(.bottom, .hearth700)
            }
            .scrollDismissesKeyboard(.interactively)
        }
        // Same never-overlaps contract as `funnelScreen` — this screen has its
        // own Skip button so it can't reuse `funnelFooter` directly, but the
        // failure mode (footer sibling appearing to clip scroll content) is
        // identical and gets the identical fix.
        .safeAreaInset(edge: .bottom) {
            VStack(spacing: .hearth400) {
                // `.plan` is unconditional in `flow` (see its doc comment) —
                // route there directly when this run has no `.signIn` step,
                // rather than skipping straight to `.warmup` and leaving the
                // new paywall step unreachable for a parent who is already
                // signed in mid-funnel.
                primaryButton("Continue", disabled: draft.familyActivities.isEmpty) {
                    goTo(includesSignInStep ? .signIn : .plan)
                }
                secondaryButton("Skip") { goTo(includesSignInStep ? .signIn : .plan) }
                Text("Next: Meet the coach")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkDisplay)
            }
            .padding(.horizontal, .hearth700)
            .padding(.top, .hearth400)
            .padding(.bottom, .hearth800)
            .background(Color.bgCanvas)
        }
        .trackScreen("onboarding_free_time")
    }

    /// The free-time grid tile. Selected = teal fill + white icon/label
    /// (matches the primary-button pass ratio). Unselected = white card with
    /// teal icon/label — `accentDefault` is the correct token here (not
    /// `accentOnCanvas`): the tile sits on `bg/elevated` (white), not the cream
    /// canvas, and "accent/default as text on paper" is a declared AA pass.
    /// Unselected tiles also carry a small ⊕ badge per the design.
    private func activityTile(
        label: String,
        symbol: String,
        selected: Bool,
        action: @escaping () -> Void
    ) -> some View {
        Button {
            withAnimation(.hearth(.hearthFast, reduceMotion: reduceMotion)) { action() }
        } label: {
            VStack(spacing: .hearth300) {
                // Figma-exported vector where one exists (round-2 addendum,
                // `docs/design/beta-v1-sprint2.md`); SF Symbol fallback for
                // any option without a matching icon export.
                if let iconName = ProfileOptions.interestIconName(for: label) {
                    Image(iconName)
                        .renderingMode(.template)
                        .resizable()
                        .scaledToFit()
                        .frame(width: 22, height: 22)
                        .foregroundColor(selected ? .inkOnPhotoLight : .accentDefault)
                } else {
                    Image(systemName: symbol)
                        .font(.system(size: 22, weight: .regular))
                        .foregroundColor(selected ? .inkOnPhotoLight : .accentDefault)
                }
                Text(label)
                    .font(.hearthBodySM.weight(.medium))
                    .foregroundColor(selected ? .inkOnPhotoLight : .inkPrimary)
                    .multilineTextAlignment(.center)
                    .lineLimit(2)
                    .minimumScaleFactor(0.8)
            }
            .frame(maxWidth: .infinity, minHeight: 88)
            .padding(.hearth400)
            .background(selected ? Color.accentDefault : Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
            .hearthCardElevation()
            .overlay(alignment: .topTrailing) {
                if !selected {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 16))
                        .foregroundColor(.accentDefault)
                        .background(Circle().fill(Color.bgElevated))
                        .padding(.hearth300)
                }
            }
        }
        .accessibilityLabel(label)
        .accessibilityAddTraits(selected ? [.isSelected] : [])
    }

    // MARK: - Screen: "What's on your mind?"

    private var mindScreen: some View {
        funnelScreen(
            caption: "Almost there",
            hint: "Next: Meet the coach",
            continueDisabled: false,
            // Measured (`need help with dynamics` Frame1 gap10): title →
            // subtitle. `hearth400` (12) is the nearest reachable step to 10,
            // tighter than the funnel's default `hearth500`.
            spacing: .hearth400,
            onContinue: { goTo(.freeTime) }
        ) {
            funnelTitle("What's on your mind?", scale: .compact)
            funnelSubtitle("Pick what feels true right now. No right answers — just your reality.")

            // ONE section, six items, single column — the frame shows no
            // "What's hardest?" heading, no divider, and no second section.
            // (`draft.goals` still ships; see the note on the option lists.)
            VStack(spacing: .hearth300) {
                ForEach(challengeOptions, id: \.label) { option in
                    let selected = draft.challenges.contains(option.label)
                    mindTagItem(label: option.label, symbol: option.symbol, selected: selected) {
                        if selected {
                            draft.challenges.removeAll { $0 == option.label }
                        } else {
                            draft.challenges.append(option.label)
                        }
                    }
                }
            }
            .padding(.top, .hearth400)
        }
        .trackScreen("onboarding_mind")
    }

    /// "What's on your mind?" tag item, measured: `#FCFBF8` fill
    /// (`bgCoachBanner`), r=**24** (`hearthRadiusSheet`), pad **12/16**, a **1px**
    /// `border/chipOutline` stroke, label Inter **w400 17** (`hearthBodyLG`) in
    /// the accent, with a 28pt leading icon. Full-bleed, left-aligned.
    ///
    /// Selected flips to the accent fill with the cream label (`inkOnCard`,
    /// 4.74:1) — the frames only show the unselected state, but the row is a
    /// real multi-select and has to say so.
    private func mindTagItem(
        label: String,
        symbol: String,
        selected: Bool,
        action: @escaping () -> Void
    ) -> some View {
        Button {
            withAnimation(.hearth(.hearthFast, reduceMotion: reduceMotion)) { action() }
        } label: {
            HStack(spacing: .hearth200) {
                Image(systemName: symbol)
                    .font(.system(size: 20, weight: .regular))
                    .frame(width: 28, height: 28)
                    .foregroundColor(selected ? .inkOnCard : .accentOnCanvas)
                Text(label)
                    .font(.hearthBodyLG)
                    .foregroundColor(selected ? .inkOnCard : .accentOnCanvas)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
                Spacer(minLength: 0)
            }
            .padding(.horizontal, .hearth500)
            .padding(.vertical, .hearth400)
            .frame(maxWidth: .infinity)
            .background(selected ? Color.accentDefault : Color.bgCoachBanner)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusSheet, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: .hearthRadiusSheet, style: .continuous)
                    .stroke(Color.borderChipOutline, lineWidth: 1)
            )
        }
        .accessibilityAddTraits(selected ? [.isSelected] : [])
    }

    // MARK: - Screen: sign in
    //
    // `create your account` (`754:4943`), re-extracted 2026-08-09. Greg's
    // "Securing your family's space" beat — now the SECOND screen a fresh
    // install sees, right after `.plan` (see `flow`). `SignInView` keeps ALL
    // of its auth logic (Apple nonce, the Google ASWebAuthenticationSession
    // flow, the legacy-account claim) and is restyled internally to match the
    // frame's card; this wrapper supplies the one piece the frame draws
    // OUTSIDE that card — the trophy mark peeking out above it.
    //
    // The frame shows no back chevron and no progress rail at all (unlike
    // every other funnel screen), so `funnelHeader` is deliberately NOT used
    // here — Miguel's "exactly like the design" call for this frame.

    private var signInScreen: some View {
        ZStack(alignment: .top) {
            Color.bgSober.ignoresSafeArea()

            // Measured `mvptrophy 1` (`1085:2766`): a RASTER image, 340x425,
            // positioned x=50 y=162 in the 440x956 frame — deliberately
            // overlapping the card below it (card top edge measures y=403), so
            // the image's lower portion (which has "MVP" text baked into the
            // same asset) sits BEHIND the card's opaque white background,
            // exactly as in the frame. This is a DIFFERENT asset from the
            // splash's mark (a distinct trophy illustration, not the
            // coffee-mug one) — fetched via the raw image-fill endpoint so the
            // pixels are exact, not a re-render.
            Image("OnboardingTrophy")
                .resizable()
                .scaledToFit()
                .frame(width: 340, height: 425)
                .padding(.top, 162)
                .accessibilityHidden(true)

            VStack(spacing: 0) {
                Spacer()

                SignInView(
                    onSignedIn: { outcome in
                        onSignedIn(outcome)
                        // A profile already on the account means this is a returning
                        // parent — SwayApp flips `onboarding_completed` and tears
                        // this whole view down, so there is nothing to route.
                        guard !outcome.hasProfile else { return }
                        // No profile — advance to whatever comes next in `flow`
                        // (the branded splash). Sign-in is now the SECOND screen
                        // in the funnel, before any question has been asked, so
                        // `draft.parentName` is always empty here in practice —
                        // no need to branch on it the way the end-of-funnel sign
                        // in used to.
                        goToNext()
                    }
                )
                // Measured `[sign up]`: r=**16** TOP corners only (it's flush
                // to the bottom edge), `DROP_SHADOW r30`
                // (`hearthOverlayElevation`). `SignInView` supplies its own
                // measured horizontal inset; not doubled here.
                .background(Color.bgElevated)
                .clipShape(
                    UnevenRoundedRectangle(
                        topLeadingRadius: .hearthRadiusLg,
                        bottomLeadingRadius: 0,
                        bottomTrailingRadius: 0,
                        topTrailingRadius: .hearthRadiusLg,
                        style: .continuous
                    )
                )
                .hearthOverlayElevation()
                .ignoresSafeArea(edges: .bottom)
            }
        }
    }

    // MARK: - Screen: choose a plan (smoke-and-mirrors paywall)
    //
    // `choose a plan` (`754:4897`). Miguel's explicit ask, 2026-08-09: insert
    // this step and make it "do nothing, just let you go to the next step" —
    // no purchase, no Stripe, no StoreKit. `PaywallView` already matches the
    // frame (built for a future Settings-menu entry point, gated behind
    // `PaywallFeatureFlag`); this reuses it rather than building a second
    // paywall, calling its own `.screen` directly to bypass that flag — the
    // flag gates the SETTINGS entry point, not this funnel step, per Miguel's
    // instruction. `onContinue` is the ONLY thing either Buy button does.
    //
    // 2026-08-09: this is now the FIRST screen in `flow` (Miguel: "you did
    // miss adding the cost screen first" — the design's canvas order is
    // `choose a plan` → `create your account` → the splash). `goToNext()`
    // rather than a hardcoded destination, since what follows depends on
    // whether `.signIn` is in this run's flow.
    private var planScreen: some View {
        PaywallView(
            onContinue: { goToNext() },
            showsCloseButton: false,
            buyAccessibilityHint: "Continues to the next step"
        )
            .screen
            .trackScreen("onboarding_plan")
    }

    // MARK: - Screen: the progress ring

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

    /// `Onboarding - welcome` (`754:4458`). Everything on this frame is
    /// LEFT-aligned, the section headers are Fraunces **w600 28/32**
    /// (`hearthDisplayMD`) in sentence case, the recap lines are Inter 17/26 and
    /// the "waiting for you" lines Inter 15/22. No centered rules, no uppercase,
    /// and the CTA is the **teal** button (`accentDefault`) — the one funnel
    /// screen where it isn't charcoal.
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
        // Same never-overlaps contract as `funnelScreen`.
        .safeAreaInset(edge: .bottom) {
            primaryButton("Take me home", disabled: false, fill: .accent) { onFinish() }
                .padding(.horizontal, .hearth700)
                .padding(.bottom, .hearth800)
                .padding(.top, .hearth400)
                .background(Color.bgCanvas)
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
                // 15/22 on this list, per the frame — a step down from the
                // recap lines above it.
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

    /// The coach voice/personality pickers. `Onboarding - welcome` (`754:6516`)
    /// renders them as a settings card rather than on this screen, but the
    /// values are real and there is no other funnel surface for them, so they
    /// stay here under the frame's own label.
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

    /// "Single parent" — the household line. Language is no longer asked in the
    /// funnel, so it is only appended when a value actually exists (a resumed
    /// draft, or one edited in the profile editor).
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

    // MARK: - Shared scaffold

    /// The common question-screen composition: header (back chevron + progress
    /// bar + caption), a scrolling body, then the CTA and Greg's quiet
    /// "Next: …" hint.
    private func funnelScreen<Content: View>(
        caption: String?,
        showsHeader: Bool = true,
        hint: String,
        continueDisabled: Bool,
        // Shown under the Continue button ONLY while it's disabled — tells
        // the parent WHAT is blocking, not just that something is. Added
        // after Miguel's screenshot showed age/grade/gender/personality all
        // filled on a kid screen with Continue still greyed out and no
        // explanation; the name field (the actual gate) was empty but
        // nothing on screen said so.
        disabledHint: String? = nil,
        // Different screens measure different intra-title and block rhythms
        // (see the per-screen call sites) — `hearth500` is the funnel's own
        // default, matching `Onboarding - 2` / `kids c`'s block-level gaps.
        spacing: CGFloat = .hearth500,
        onContinue: @escaping () -> Void,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(spacing: 0) {
            if showsHeader {
                funnelHeader(caption: caption)
            }

            ScrollView {
                VStack(spacing: spacing) {
                    content()
                }
                .padding(.horizontal, .hearth700)
                // Measured caption→title is 13 (`kids c`: caption ends 120, title 133)
                // — `hearth400` (12) is the nearest step; `hearth700` (24) read loose
                // AND cost fold height the 956→874 canvas squeeze can't spare.
                .padding(.top, showsHeader ? .hearth400 : .hearth1000)
                .padding(.bottom, .hearth700)
            }
            // .immediately (not .interactively): any scroll drops the
            // keyboard right away, same as PlanView's funnel-adjacent
            // scroll — a drag-based dismiss alone left the keyboard up when
            // a dropdown (Menu) consumed the tap instead of scrolling.
            .scrollDismissesKeyboard(.immediately)
        }
        // The footer used to be a plain VStack sibling below the ScrollView.
        // Sequentially stacked views shouldn't overlap — but Miguel's sim
        // screenshot showed "About child one"'s Grade/Gender + personality
        // chips clipped behind the grey Continue bar. `.safeAreaInset`
        // eliminates the failure mode structurally: it reserves exactly the
        // footer's real, measured height as bottom inset for the ScrollView
        // above it — the same "measure and reserve" contract `MainTabView`
        // uses for its custom tab bar (`tabBarHeight` via `GeometryReader`),
        // just via the built-in modifier since there's only one inset
        // consumer here. Every funnel screen built on `funnelScreen` inherits
        // the fix from this one call site.
        .safeAreaInset(edge: .bottom) {
            funnelFooter(
                hint: hint,
                continueDisabled: continueDisabled,
                disabledHint: disabledHint,
                onContinue: onContinue
            )
        }
    }

    /// The funnel's standard footer: Continue + Greg's quiet "Next: …" hint.
    /// Extracted so `freeTimeScreen` (its own Skip button) and `allSetScreen`
    /// can reuse the identical `.safeAreaInset` never-overlaps contract.
    private func funnelFooter(
        hint: String,
        continueDisabled: Bool,
        disabledHint: String? = nil,
        onContinue: @escaping () -> Void
    ) -> some View {
        VStack(spacing: .hearth400) {
            primaryButton("Continue", disabled: continueDisabled) {
                hideKeyboard()
                onContinue()
            }
            if continueDisabled, let disabledHint {
                Text(disabledHint)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
            }
            Text(hint)
                .font(.hearthBodySM)
                .foregroundColor(.inkDisplay)
        }
        .padding(.horizontal, .hearth700)
        .padding(.top, .hearth300)
        // 12 + the 34pt home-indicator inset ≈ the frame's 36 to the hard edge;
        // the shipped 32 pushed the whole footer up and stole fold height.
        .padding(.bottom, .hearth400)
        .background(Color.bgCanvas)
    }

    /// `showsProgress: false` is for screens that are NOT a funnel step — the
    /// returning-parent sign-in reached from the splash. It sits at the same
    /// index as the funnel's own sign-in step, so the bar would read 100% and
    /// the caption "Almost there" to someone who has not answered a single
    /// question. Back chevron stays; the progress affordance goes.
    /// Measured: the back affordance is a **31pt** circle on the sober cream
    /// (`#F3F0EB` = `bgSober`) with a 16x13 arrow, gap **4** to the rail; the
    /// caption sits BELOW the rail at gap **6..11**, Inter **w700 13**
    /// (`hearthBodySMBold` — the shipped `hearthBodySM.weight(.semibold)` is a
    /// visibly lighter stroke).
    private func funnelHeader(caption: String?, showsProgress: Bool = true) -> some View {
        VStack(spacing: .hearth300) {
            HStack(spacing: .hearth200) {
                Button(action: goBack) {
                    Image(systemName: "arrow.left")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.inkPrimary)
                        .frame(width: 31, height: 31)
                        .background(Circle().fill(Color.bgSober))
                }
                .accessibilityLabel("Back")

                if showsProgress {
                    progressBar
                } else {
                    Spacer()
                }
            }

            if let caption {
                Text(caption)
                    .font(.hearthBodySMBold)
                    .foregroundColor(.inkDisplay)
            }
        }
        .padding(.horizontal, .hearth700)
        .padding(.top, .hearth400)
    }

    /// The progress rail, measured: a **30pt** white pill track (r=100) with a
    /// **2pt** inset, and a `#1B7498` pill fill inside it. The shipped bar was a
    /// 16pt flush two-capsule stack — no inset, so the fill met the track edge
    /// and the whole rail read as a thin generic slider.
    ///
    /// The denominator is the LAST question screen ("What's on your mind?"), not
    /// the flow length — the ring and the landing aren't questions, so the rail
    /// reads full by the time the parent is done answering.
    private var progressBar: some View {
        let steps = flow
        // Rebased 2026-08-09: `.plan`, `.signIn` and `.splash` now sit BEFORE
        // `.acquainted` (see `flow`'s new order), and none of them render this
        // rail — but dividing by the raw `stepIndex` would still start the
        // first QUESTION screen at ~30% done. The rail now spans only the
        // questionnaire itself: `.acquainted` (the first rail-bearing screen)
        // to `.freeTime` (the last question screen), so it reads ~4% on the
        // first question and full exactly when the parent stops answering.
        let start = Double(steps.firstIndex(of: .acquainted) ?? 0)
        let end = Double(steps.firstIndex(of: .freeTime) ?? 1)
        let fraction = min(1.0, max(0.04, (Double(draft.stepIndex) - start) / max(end - start, 1)))
        // The rail is DELIBERATELY pale, and it deepens as the parent advances.
        // Measured opacities off the frames (the flat extract misses these —
        // they live on the node, not the fill):
        //   track  `Frame 2` — #FFFFFF at **0.5** on every frame that has a rail
        //   fill   `Frame 4` — #1B7498 at **0.1** on `kids a`/`kids c`, **0.9**
        //                      on both "need help…" screens
        // So the fill's own alpha carries progress alongside its width, easing
        // in rather than ramping linearly (0.46 of the way through still
        // measured 0.1). A solid teal on solid white — what shipped — reads as a
        // heavy loading bar from step one instead of the design's quiet wash.
        let fillOpacity = 0.1 + 0.8 * (fraction * fraction)
        return GeometryReader { geo in
            Capsule()
                .fill(Color.accentDefault.opacity(fillOpacity))
                .frame(width: max(0, geo.size.width - 4) * fraction)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(2)
        }
        .frame(height: 30)
        .background(Capsule().fill(Color.bgElevated.opacity(0.5)))
        .animation(.hearth(.hearthSlow, reduceMotion: reduceMotion), value: fraction)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Step \(Int(Double(draft.stepIndex) - start)) of \(Int(end - start))")
    }

    // MARK: - Shared components

    /// The funnel runs TWO display scales and one shared token cannot serve
    /// both. Measured: the funnel + person-name titles are 56/60 ls-1.12
    /// (`hearthDisplayXL`); the two "need help with…" screens are 38/40
    /// ls-0.38 (`hearthDisplaySM`). Shipping everything at `hearthDisplayLG`
    /// (40) was the single biggest reason the funnel read wrong — the hero
    /// titles were a step and a half small and the two smaller ones a hair big.
    private enum FunnelTitleScale {
        /// 56 / 60, ls -1.12 — "Let's get acquainted", "Hi Gregory!",
        /// "Tell us about your first", "You're all set, Gregory."
        case hero
        /// 38 / 40, ls -0.38 — "What's on your mind?",
        /// "What do you do in your free time?"
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
            // NOT `.hearthLineDisplayXL` (4): SwiftUI lineSpacing ADDS to the
            // font's natural line height, and Fraunces at 56 is already ~67/line
            // against the frame's 60. Zero is the closest a SwiftUI Text can get
            // (a negative is clamped); the residual +14/line is part of why the
            // 956pt frame must be compressed onto an 874pt device at all.
            case .hero:    return 0
            // 38 → 40 line-height. No token: the 38pt step is measured only on
            // these two frames, and `hearthLineDisplayLG` (4) is for the 40pt step.
            case .compact: return 2
            }
        }
    }

    /// Every funnel frame centers its title EXCEPT the landing
    /// (`Onboarding - welcome`), which is left-aligned throughout.
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
        // The kid screens' text box measures ~320pt wide in the frame (`kids c`
        // `Frame 21` is 380 wide, but the subtitle's own glyph run wraps at
        // "we'll learn more as we go." well short of that) — the sim let it run
        // the full content width instead, so the line broke later than the
        // design. `nil` (every other screen) keeps the old full-width behavior.
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

    /// Measured on the kid frames (`Frame 23`): **42x1**, `#6E6A62`. That hex is
    /// not a token; `inkMuted` (`#666157`) is the nearest and a hair darker on a
    /// 1px decorative rule. The shipped rule was 44 wide in `inkPlaceholder`.
    ///
    /// The kid screens are the ONLY sprint-1 frames that draw it — it has been
    /// removed from "Let's get acquainted", both "need help" screens and the
    /// landing, none of which show one.
    private var centeredRule: some View {
        Rectangle()
            .fill(Color.inkMuted)
            .frame(width: 42, height: 1)
            // 4/side, not 8 — the outer block spacing already carries the gap,
            // and the doubled padding cost fold height on the kid screen.
            .padding(.vertical, .hearth200)
    }

    /// Measured: label is Inter **w800 16** (`hearthSectionHeader`, NOT the 20/600
    /// `hearthTitleLG` that shipped), centered, gap **3** to its input —
    /// `hearth200` (4) is the nearest token and the only one under the 8pt step.
    /// The `hearth300` top pad composes with the screen's `hearth500` row spacing
    /// to the frame's 23pt gap between groups.
    @ViewBuilder
    private func fieldGroup<Content: View>(
        _ label: String,
        helper: String? = nil,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(spacing: .hearth200) {
            Text(label)
                .font(.hearthSectionHeader)
                .foregroundColor(.inkPrimary)
                .multilineTextAlignment(.center)
            content()
            if let helper {
                Text(helper)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
            }
        }
        .padding(.top, .hearth300)
    }

    /// Kid-screen field label — Inter w400 15/22 in `#1E1E1E`, centered, gap 8
    /// to its input. Note the ink: the frames use the same ink as the headline
    /// here, not a muted secondary.
    private func subFieldLabel(_ text: String) -> some View {
        Text(text)
            .font(.hearthBodyMD)
            .foregroundColor(.inkDisplay)
            .frame(maxWidth: .infinity)
    }

    // MARK: Funnel input chrome
    //
    // Measured on every sprint-1 funnel frame: r=**32**, a **1px** stroke in
    // `border/inputPill`, and NO shadow. The shipped controls had this exactly
    // inverted — a `hearthCardElevation()` shadow and no stroke — which is why
    // the fields read as floating cards rather than as the design's flat pills.
    //
    // The radius needs no new token: these fields are 48–56pt tall, so r32
    // clamps to half the height and a `Capsule` renders identically. Keeping
    // `Capsule` also means a field that grows with Dynamic Type stays a pill
    // instead of developing corners.
    //
    // Placeholder ink is `inkMuted`. The frames say `#6E6A62`, which is not a
    // token; `inkMuted` (`#666157`) is a hair darker and passes AA either way.
    // Do NOT add a primitive for the Figma value.

    /// The two grounds the frames use: the name field is `#FCFBF8`
    /// (`bgCoachBanner`), every dropdown is `#FFFFFF` (`bgElevated`).
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
    /// `hearthTitleLG` is the 20pt Inter step; the design's light weight is the
    /// call-site override.
    private static let pillInputFont = Font.hearthTitleLG.weight(.light)

    private func pillField(
        _ placeholder: String,
        text: Binding<String>,
        ground: PillGround = .cream,
        keyboard: UIKeyboardType = .default,
        textContentType: UITextContentType? = nil
    ) -> some View {
        TextField("", text: text, prompt: Text(placeholder).foregroundColor(.inkMuted))
            .font(Self.pillInputFont)
            .foregroundColor(.inkPrimary)
            .multilineTextAlignment(.center)
            .keyboardType(keyboard)
            .textContentType(textContentType)
            .autocorrectionDisabled()
            .padding(.horizontal, .hearth800)
            .padding(.vertical, .hearth400)
            .frame(maxWidth: .infinity)
            .background(ground.fill)
            .clipShape(Capsule())
            .overlay(Capsule().stroke(Color.borderInputPill, lineWidth: 1))
    }

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
                // responder status, so the keyboard used to stay up behind
                // the picker. Every funnel dropdown goes through this one
                // helper, so dismissing here covers all of them.
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
        // Belt-and-braces: this covers the OPEN tap (before a selection is
        // even made), since the Button action above only fires on selection.
        .simultaneousGesture(TapGesture().onEnded { hideKeyboard() })
        .accessibilityLabel(value.isEmpty ? placeholder : value)
    }

    /// Measured: fill `bg/buttonFunnel` (`#4A4741`), r=**12**, label Inter
    /// **w800 16**, white. The funnel button is deliberately charcoal, not the
    /// teal accent — white on it is 9.26:1.
    ///
    /// The DISABLED treatment stays `bg/disabled` + `ink/secondary`. No frame
    /// shows a disabled state, and white on `bgDisabled` is 2.07:1 — never
    /// "fix" this to white for consistency with the enabled label.
    /// Every funnel CTA is charcoal EXCEPT the landing's "Take me home", which
    /// the frame draws in `#1B7498` — the moment the parent crosses into the app.
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

    /// The secondary CTA — the free-time screen's "Skip". Measured: `#F5F3EF`
    /// fill (`bgCard`), a **1px** teal stroke, r=12, Inter **w800 16** teal label.
    /// The shipped version was a bare text button.
    private func secondaryButton(_ label: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(label)
                .font(.hearthSectionHeader)
                .foregroundColor(.accentOnCanvas)
                .frame(maxWidth: .infinity)
                .padding(.vertical, .hearth400)
                .background(Color.bgCard)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                        .stroke(Color.accentDefault, lineWidth: 1)
                )
        }
    }

    // `multiSelectGrid` + the generic `chip` are GONE. No sprint-1 frame draws a
    // two-column capsule-chip grid: the kid screens use `tagItem` (r24, teal
    // hairline, 13pt label) and "What's on your mind?" uses `mindTagItem` (r24,
    // `borderChipOutline`, 17pt label, full width). Deleted rather than left
    // unused so a new call site cannot reach the wrong shape.

    // MARK: - Derived values

    private var firstName: String {
        let trimmed = draft.parentName.trimmed
        return trimmed.isEmpty ? "there" : trimmed
    }

    /// Builds the `/profile/seed` payload. The fields the funnel stopped asking
    /// go out EMPTY rather than disappearing — the contract test pins the keys.
    private func collectedData() -> OnboardingData {
        let kidData = draft.kids
            .filter { !$0.name.trimmed.isEmpty }
            .map { kid in
                (
                    name: kid.name.trimmed,
                    age: kid.age.trimmed,
                    temperament: kid.temperament,
                    pronouns: "",
                    gradeBand: kid.gradeBand,
                    gender: kid.gender
                )
            }
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
            coachPersonality: draft.coachPersonality
        )
    }

    private static let childWords = [
        "One", "Two", "Three", "Four", "Five", "Six",
        "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve"
    ]

    private static let ordinalWords = [
        "first", "second", "third", "fourth", "fifth", "sixth",
        "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth"
    ]

    static func childLabel(_ index: Int) -> String {
        childWords.indices.contains(index) ? "Child \(childWords[index])" : "Child \(index + 1)"
    }

    /// "Child one" — the frames' sentence-case form for the in-body heading and
    /// the "About child one" eyebrow. The header caption keeps title case
    /// ("Child One"), matching the frames.
    static func childLabelSentence(_ index: Int) -> String {
        childWords.indices.contains(index)
            ? "child \(childWords[index].lowercased())"
            : "child \(index + 1)"
    }

    static func ordinalWord(_ index: Int) -> String {
        ordinalWords.indices.contains(index) ? ordinalWords[index] : "child number \(index + 1)"
    }

}

// MARK: - String Helper

private extension String {
    var trimmed: String { trimmingCharacters(in: .whitespacesAndNewlines) }
    // `capitalizedFirst` lives on the app-wide `String` extension in
    // HomeDashboardService.swift — do not redeclare it here.
}
