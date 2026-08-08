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

/// The beta-v1 funnel. Eight *kinds* of screen, but a DYNAMIC number of them:
/// the parent says how many children they have and the flow grows one screen
/// per child.
///
///   splash → acquainted → kidCount → kid(0) … kid(n-1) → freeTime → mind
///          → signIn → warmup (the progress ring) → allSet
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
        // on an undecodable draft, both of which mean "start at the splash".
        _draft = State(initialValue: OnboardingDraft.load() ?? OnboardingDraft())
    }

    // MARK: State

    /// The ONE piece of funnel state. Every answer and the current position
    /// live here, and a single `.onChange` below persists the whole thing on
    /// every mutation — so there is no way to add a field that isn't durable.
    @State private var draft: OnboardingDraft
    @State private var includesSignInStep: Bool

    /// The resolved account id, written by `onSignedIn` via SwayApp. Read here
    /// (never written) so the warm-up can authenticate.
    @AppStorage("user_name") private var accountID = ""

    /// True when the parent reached sign-in via the splash's "I already have an
    /// account" rather than by walking the funnel. It changes what happens on a
    /// successful sign-in whose account turns out to have NO profile: the
    /// normal path goes to the ring (every answer already collected), but a
    /// splash jumper has answered nothing, so sending them to the ring would
    /// seed an empty family. They go to the first question instead.
    @State private var cameToSignInFromSplash = false

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

    private let languageOptions = ["English", "Spanish", "Mandarin", "Other"]

    private let householdOptions = [
        "Two-parent home", "Single parent", "Co-parenting",
        "Blended family", "Extended family", "It's complicated"
    ]

    /// Phase-3 Figma delta — "Education style" on "Let's get acquainted".
    private let educationStyleOptions = [
        "Public school", "Private school", "Homeschool", "Montessori", "Waldorf", "Other"
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
    /// Greg's kid frames show "Spirited" twice; that's a Figma artifact, not a
    /// seventh option.
    private var temperamentOptions: [(label: String, symbol: String)] {
        ProfileOptions.temperamentChips
    }

    private let challengeOptions: [(label: String, symbol: String)] = [
        ("Morning routines", "sunrise"),
        ("Bedtime battles", "moon.zzz"),
        ("Big emotions", "wave.3.left"),
        ("Picky eating", "fork.knife"),
        ("Screen time", "iphone"),
        ("Sibling rivalry", "person.2"),
        ("School struggles", "book.closed"),
        ("Behavior changes", "arrow.triangle.2.circlepath"),
        ("Work-life balance", "scale.3d"),
        ("Feeling alone in it", "person")
    ]

    private let goalOptions: [(label: String, symbol: String)] = [
        ("Expert guidance", "book"),
        ("Daily strategies", "list.bullet"),
        ("Understanding my child", "magnifyingglass"),
        ("Community support", "person.3"),
        ("Managing my stress", "heart.circle"),
        ("Building confidence", "figure.stand")
    ]

    // MARK: - Flow

    enum Step: Equatable {
        case splash
        case acquainted
        case kidCount
        case kid(Int)
        case freeTime
        case mind
        case signIn
        case warmup
        case allSet
    }

    /// The screen order, recomputed from the collected child count.
    private var flow: [Step] {
        var steps: [Step] = [.splash, .acquainted, .kidCount]
        for index in draft.kids.indices { steps.append(.kid(index)) }
        steps.append(.freeTime)
        steps.append(.mind)
        if includesSignInStep { steps.append(.signIn) }
        steps.append(.warmup)
        steps.append(.allSet)
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

    /// Back walks the computed flow, so it handles n children with no special
    /// cases: from `kid(0)` it lands on `kidCount`, from `mind` it lands on the
    /// LAST child (or on `kidCount` when there are none).
    private func goBack() {
        guard draft.stepIndex > 0 else { return }
        dismissKeyboard()
        // A parent who jumped splash → sign-in never walked the funnel, so the
        // step physically before `.signIn` (`.mind`) is not where they came
        // from. Stepping back by index would strand them mid-questionnaire.
        if cameToSignInFromSplash, currentStep == .signIn {
            cameToSignInFromSplash = false
            goTo(.splash)
            return
        }
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
                Button("Done") { dismissKeyboard() }
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

    /// The splash is a FORK, not a timed interstitial.
    ///
    /// It used to auto-advance into the funnel after 1.7s. That stranded every
    /// returning parent: sign-in now lives at the END of the funnel, so a
    /// reinstall, a new device, or a sign-out left no way to reach it without
    /// re-answering the whole questionnaire first. The second CTA jumps
    /// straight to the sign-in step.
    private var splashScreen: some View {
        ZStack {
            RadialGradient(
                colors: [Color.bgElevated, Color.bgCanvas],
                center: .center, startRadius: 0, endRadius: 300
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

                VStack(spacing: .hearth400) {
                    MVPLogoView(variant: .lockup, size: 240, tint: .inkPrimary)
                    Text("Most Valuable Parent")
                        .font(.hearthLabel)
                        .tracking(0.66)
                        .foregroundColor(.inkSecondary)
                }

                Spacer()

                VStack(spacing: .hearth400) {
                    primaryButton("Get started", disabled: false) {
                        goTo(.acquainted)
                    }

                    // Only offered when signing in is actually reachable. When
                    // `signInRequired` is false the parent already has an
                    // account and is mid-onboarding — there is no `.signIn`
                    // step in `flow`, so this would jump nowhere.
                    if includesSignInStep {
                        Button {
                            cameToSignInFromSplash = true
                            goTo(.signIn)
                        } label: {
                            Text("I already have an account")
                                .font(.hearthTitleMD)
                                .foregroundColor(.accentOnCanvas)
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, .hearth500)
                        }
                    }
                }
                .padding(.horizontal, .hearth700)
                .padding(.bottom, .hearth900)
            }
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
            onContinue: { goTo(.kidCount) }
        ) {
            funnelTitle("Let's get acquainted")
            funnelSubtitle("A few quick questions so we can make MVP feel like it was made for your family.")
            centeredRule

            fieldGroup("What should we call you?", helper: "Your first name") {
                pillField("Name", text: $draft.parentName, textContentType: .givenName)
            }

            fieldGroup("Your household") {
                pillSelect(
                    placeholder: "Select your situation",
                    value: draft.household,
                    options: householdOptions
                ) { draft.household = $0 }
            }

            fieldGroup("Language at home") {
                VStack(spacing: .hearth400) {
                    pillSelect(
                        placeholder: "Primary language",
                        value: draft.primaryLanguage,
                        options: languageOptions
                    ) { draft.primaryLanguage = $0 }
                    pillSelect(
                        placeholder: "Secondary language (optional)",
                        value: draft.secondaryLanguage,
                        options: languageOptions
                    ) { draft.secondaryLanguage = $0 }
                }
            }

            fieldGroup("Location", helper: "Helps us find local camps and activities near you") {
                pillField(
                    "ZIP / postal code",
                    text: $draft.postalCode,
                    keyboard: .numbersAndPunctuation,
                    textContentType: .postalCode
                )
            }

            fieldGroup("Education style") {
                pillSelect(
                    placeholder: "Select your approach",
                    value: draft.educationStyle,
                    options: educationStyleOptions
                ) { draft.educationStyle = $0 }
            }

            Text("You can update any of this later in your profile.")
                .font(.hearthBodyMD)
                .foregroundColor(.inkSecondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: .infinity)
                .padding(.top, .hearth300)
        }
        .trackScreen("onboarding_acquainted")
    }

    // MARK: - Screen: "Hi {name}!"

    private var kidCountScreen: some View {
        funnelScreen(
            caption: "\(firstName)'s children",
            hint: "Next: Child One",
            continueDisabled: !(1...12).contains(kidCountValue),
            onContinue: {
                syncKidsToCount()
                goTo(.kid(0))
            }
        ) {
            Spacer(minLength: .hearth900)
            funnelTitle("Hi \(firstName)!")
            funnelSubtitle("Now let's meet your kids. We just need their names, ages, and a sense of who they are.")

            pillField("0", text: $draft.kidCountText, keyboard: .numberPad)
                .padding(.top, .hearth600)

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
            hint: safeIndex + 1 < draft.kids.count
                ? "Next: \(Self.childLabel(safeIndex + 1))"
                : "Next: Free time",
            continueDisabled: draft.kids.indices.contains(safeIndex)
                ? draft.kids[safeIndex].name.trimmed.isEmpty
                : true,
            onContinue: {
                if safeIndex + 1 < draft.kids.count {
                    goTo(.kid(safeIndex + 1))
                } else {
                    goTo(.mind)
                }
            }
        ) {
            funnelTitle("Tell us about\nyour \(Self.ordinalWord(safeIndex))")
            funnelSubtitle(safeIndex == 0
                ? "Just the basics for now — we'll learn more as we go."
                : "Same deal — name, age, and a little of their personality.")
            centeredRule

            if draft.kids.indices.contains(safeIndex) {
                Text(Self.childLabel(safeIndex))
                    .font(.hearthDisplayMD)
                    .foregroundColor(.inkPrimary)
                    .frame(maxWidth: .infinity)

                subFieldLabel("What should we call them?")
                pillField("Name", text: $draft.kids[safeIndex].name, textContentType: .givenName)

                subFieldLabel("How old are they?")
                    .padding(.top, .hearth500)
                pillField("0", text: $draft.kids[safeIndex].age, keyboard: .numberPad)

                subFieldLabel("Gender")
                    .padding(.top, .hearth500)
                HStack(spacing: .hearth300) {
                    genderChip(label: "Boy", index: safeIndex)
                    genderChip(label: "Girl", index: safeIndex)
                }

                Text("Personality or vibe")
                    .font(.hearthBodySM.weight(.semibold))
                    .foregroundColor(.inkPrimary)
                    .frame(maxWidth: .infinity)
                    .padding(.top, .hearth600)

                FlowLayout(spacing: .hearth300) {
                    gradeChip(index: safeIndex)
                    ForEach(temperamentOptions, id: \.label) { option in
                        let selected = draft.kids[safeIndex].temperament == option.label
                        chip(label: option.label, symbol: option.symbol, selected: selected) {
                            draft.kids[safeIndex].temperament = selected ? "" : option.label
                        }
                    }
                }
            }
        }
        .trackScreen("onboarding_child")
    }

    /// Phase-3 Figma delta — the "boy" / "girl" tag choice on each child
    /// screen. Single-select, stored lowercase; tapping the active tag clears
    /// it, matching the temperament chip's toggle behavior.
    private func genderChip(label: String, index: Int) -> some View {
        let value = label.lowercased()
        let selected = draft.kids[index].gender == value
        return chip(label: label, symbol: "", selected: selected) {
            draft.kids[index].gender = selected ? "" : value
        }
    }

    private func gradeChip(index: Int) -> some View {
        Menu {
            ForEach(gradeBandOptions, id: \.self) { band in
                Button(band) { draft.kids[index].gradeBand = band }
            }
        } label: {
            HStack(spacing: .hearth300) {
                Image(systemName: "graduationcap.fill")
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(.inkPrimary)
                Text(draft.kids[index].gradeBand.isEmpty ? "Grade" : draft.kids[index].gradeBand)
                    .font(.hearthBodyMD.weight(.medium))
                    .foregroundColor(.inkPrimary)
                Image(systemName: "chevron.down")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(.inkMuted)
            }
            .padding(.horizontal, .hearth500)
            .padding(.vertical, .hearth400)
            .background(Color.bgElevated)
            .clipShape(Capsule())
            .hearthCardElevation()
        }
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
                VStack(spacing: .hearth500) {
                    funnelTitle("What do you do in your free time?")
                    funnelSubtitle("Looking for more? Select what describes your family routine.")
                    centeredRule

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

            VStack(spacing: .hearth400) {
                primaryButton("Continue", disabled: draft.familyActivities.isEmpty) {
                    goTo(.mind)
                }
                Button("Skip") { goTo(.mind) }
                    .font(.hearthBodyMD.weight(.medium))
                    .foregroundColor(.accentOnCanvas)
                Text("Next: Meet the coach")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
            }
            .padding(.horizontal, .hearth700)
            .padding(.top, .hearth400)
            .padding(.bottom, .hearth800)
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
                Image(systemName: symbol)
                    .font(.system(size: 22, weight: .regular))
                    .foregroundColor(selected ? .inkOnPhotoLight : .accentDefault)
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
            onContinue: { goTo(includesSignInStep ? .signIn : .warmup) }
        ) {
            funnelTitle("What's on your mind?")
            funnelSubtitle("Pick what feels true right now. No right answers — just your reality.")
            centeredRule

            Text("What's hardest?")
                .font(.hearthDisplayMD)
                .foregroundColor(.inkPrimary)
                .frame(maxWidth: .infinity)

            multiSelectGrid(options: challengeOptions, selection: $draft.challenges)

            Text("What would help")
                .font(.hearthDisplayMD)
                .foregroundColor(.inkPrimary)
                .frame(maxWidth: .infinity)
                .padding(.top, .hearth500)

            multiSelectGrid(options: goalOptions, selection: $draft.goals)
        }
        .trackScreen("onboarding_mind")
    }

    // MARK: - Screen: sign in
    //
    // Greg's "Securing your family's space" beat. `SignInView` keeps ALL of its
    // auth logic (Apple nonce, the Google ASWebAuthenticationSession flow, the
    // legacy-account claim); only its chrome moved onto the Hearth tokens.

    private var signInScreen: some View {
        VStack(spacing: 0) {
            funnelHeader(
                caption: cameToSignInFromSplash ? nil : "Almost there",
                showsProgress: !cameToSignInFromSplash
            )

            SignInView(
                onSignedIn: { outcome in
                    onSignedIn(outcome)
                    // A profile already on the account means this is a returning
                    // parent — SwayApp flips `onboarding_completed` and tears
                    // this whole view down, so there is nothing to route.
                    guard !outcome.hasProfile else { return }
                    // No profile — so this account has nothing to restore and
                    // the funnel still has to be answered. Route on what is
                    // actually IN THE DRAFT, not on `cameToSignInFromSplash`:
                    // that flag is @State and does not survive a relaunch, so a
                    // parent who jumped splash → sign-in and then killed the app
                    // would come back with it false and get sent to the ring —
                    // seeding a family with no parent and no kids. The draft is
                    // the only trustworthy answer to "did they fill this in?".
                    goTo(draft.parentName.trimmed.isEmpty ? .acquainted : .warmup)
                },
                titleOverride: cameToSignInFromSplash
                    ? "Welcome back."
                    : "One last thing, \(firstName).",
                subtitleOverride: cameToSignInFromSplash
                    ? "Sign in and we'll pick up your family right where you left off."
                    : "Sign in to secure your family's space and keep everything in sync across your devices."
            )
        }
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

    private var allSetScreen: some View {
        VStack(spacing: 0) {
            ScrollView {
                VStack(spacing: .hearth500) {
                    funnelTitle("You're all set, \(firstName).")
                    funnelSubtitle("Here's what we've got — and what's waiting for you.")
                    centeredRule

                    Text("Your family")
                        .font(.hearthTitleLG)
                        .tracking(0.52)
                        .textCase(.uppercase)
                        .foregroundColor(.inkPrimary)

                    if !familyLine.isEmpty {
                        recapLine(familyLine)
                    }
                    if !kidsLine.isEmpty {
                        recapLine(kidsLine)
                    }

                    centeredRule
                        .padding(.vertical, .hearth400)

                    Text("Here's what's waiting for you")
                        .font(.hearthDisplayMD)
                        .foregroundColor(.inkPrimary)
                        .multilineTextAlignment(.center)
                        .textCase(.uppercase)
                        .lineSpacing(.hearthLineDisplayMD)

                    VStack(spacing: .hearth500) {
                        ForEach(waitingForYou, id: \.self) { line in
                            recapLine(line)
                        }
                    }
                    .padding(.top, .hearth300)

                    centeredRule
                        .padding(.vertical, .hearth400)

                    Text("Set up how you want the coach to respond")
                        .font(.hearthTitleLG)
                        .foregroundColor(.inkPrimary)
                        .multilineTextAlignment(.center)

                    VStack(spacing: .hearth400) {
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
                    .padding(.top, .hearth300)
                }
                .padding(.horizontal, .hearth700)
                .padding(.top, .hearth900)
                .padding(.bottom, .hearth700)
            }

            VStack(spacing: 0) {
                primaryButton("Take me home", disabled: false) { onFinish() }
            }
            .padding(.horizontal, .hearth700)
            .padding(.bottom, .hearth800)
            .padding(.top, .hearth400)
        }
        .trackScreen("onboarding_all_set")
    }

    private func recapLine(_ text: String) -> some View {
        Text(text)
            .font(.hearthBodyLG)
            .foregroundColor(.inkSecondary)
            .multilineTextAlignment(.center)
            .lineSpacing(.hearthLineBodyLG)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity)
    }

    /// "Single parent · English"
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
        onContinue: @escaping () -> Void,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(spacing: 0) {
            if showsHeader {
                funnelHeader(caption: caption)
            }

            ScrollView {
                VStack(spacing: .hearth500) {
                    content()
                }
                .padding(.horizontal, .hearth700)
                .padding(.top, showsHeader ? .hearth700 : .hearth1000)
                .padding(.bottom, .hearth700)
            }
            .scrollDismissesKeyboard(.interactively)

            VStack(spacing: .hearth400) {
                primaryButton("Continue", disabled: continueDisabled) {
                    dismissKeyboard()
                    onContinue()
                }
                Text(hint)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
            }
            .padding(.horizontal, .hearth700)
            .padding(.top, .hearth400)
            .padding(.bottom, .hearth800)
        }
    }

    /// `showsProgress: false` is for screens that are NOT a funnel step — the
    /// returning-parent sign-in reached from the splash. It sits at the same
    /// index as the funnel's own sign-in step, so the bar would read 100% and
    /// the caption "Almost there" to someone who has not answered a single
    /// question. Back chevron stays; the progress affordance goes.
    private func funnelHeader(caption: String?, showsProgress: Bool = true) -> some View {
        VStack(spacing: .hearth300) {
            HStack(spacing: .hearth400) {
                Button(action: goBack) {
                    Image(systemName: "arrow.left")
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(.accentOnCanvas)
                        .frame(width: 36, height: 36)
                        .background(Circle().fill(Color.bgElevated))
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
                    .font(.hearthBodySM.weight(.semibold))
                    .foregroundColor(.inkPrimary)
            }
        }
        .padding(.horizontal, .hearth700)
        .padding(.top, .hearth400)
    }

    /// Replaces the pre-beta `progressDots`. The denominator is the LAST
    /// question screen ("What's on your mind?"), not the flow length — the
    /// ring and the landing aren't questions, so Greg's bar reads full by the
    /// time the parent is done answering.
    private var progressBar: some View {
        let steps = flow
        let denominator = Double(steps.firstIndex(of: .mind) ?? 1)
        let fraction = min(1.0, max(0.04, Double(draft.stepIndex) / max(denominator, 1)))
        return GeometryReader { geo in
            ZStack(alignment: .leading) {
                Capsule().fill(Color.bgElevated)
                Capsule()
                    .fill(Color.accentOnCanvas)
                    .frame(width: geo.size.width * fraction)
            }
        }
        .frame(height: 16)
        .animation(.hearth(.hearthSlow, reduceMotion: reduceMotion), value: fraction)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Step \(draft.stepIndex) of \(Int(denominator))")
    }

    // MARK: - Shared components

    private func funnelTitle(_ text: String) -> some View {
        Text(text)
            .font(.hearthDisplayLG)
            .foregroundColor(.inkPrimary)
            .multilineTextAlignment(.center)
            .lineSpacing(.hearthLineDisplayLG)
            .lineLimit(3)
            .minimumScaleFactor(0.6)
            .frame(maxWidth: .infinity)
    }

    private func funnelSubtitle(_ text: String) -> some View {
        Text(text)
            .font(.hearthBodyMD)
            .foregroundColor(.inkSecondary)
            .multilineTextAlignment(.center)
            .lineSpacing(.hearthLineBodyMD)
            .fixedSize(horizontal: false, vertical: true)
            .frame(maxWidth: .infinity)
    }

    private var centeredRule: some View {
        Rectangle()
            .fill(Color.inkPlaceholder)
            .frame(width: 44, height: 1)
            .padding(.vertical, .hearth300)
    }

    @ViewBuilder
    private func fieldGroup<Content: View>(
        _ label: String,
        helper: String? = nil,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(spacing: .hearth400) {
            Text(label)
                .font(.hearthTitleLG)
                .foregroundColor(.inkPrimary)
                .multilineTextAlignment(.center)
            content()
            if let helper {
                Text(helper)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
            }
        }
        .padding(.top, .hearth400)
    }

    private func subFieldLabel(_ text: String) -> some View {
        Text(text)
            .font(.hearthBodyMD)
            .foregroundColor(.inkSecondary)
            .frame(maxWidth: .infinity)
    }

    private func pillField(
        _ placeholder: String,
        text: Binding<String>,
        keyboard: UIKeyboardType = .default,
        textContentType: UITextContentType? = nil
    ) -> some View {
        TextField("", text: text, prompt: Text(placeholder).foregroundColor(.inkPlaceholder))
            .font(.hearthBodyLG)
            .foregroundColor(.inkPrimary)
            .multilineTextAlignment(.center)
            .keyboardType(keyboard)
            .textContentType(textContentType)
            .autocorrectionDisabled()
            .padding(.horizontal, .hearth600)
            .padding(.vertical, .hearth500)
            .frame(maxWidth: .infinity)
            .background(Color.bgElevated)
            .clipShape(Capsule())
            .hearthCardElevation()
    }

    private func pillSelect(
        placeholder: String,
        value: String,
        options: [String],
        onPick: @escaping (String) -> Void
    ) -> some View {
        Menu {
            ForEach(options, id: \.self) { option in
                Button(option) { onPick(option) }
            }
        } label: {
            HStack(spacing: .hearth400) {
                Spacer(minLength: 0)
                Text(value.isEmpty ? placeholder : value)
                    .font(.hearthBodyLG)
                    .foregroundColor(value.isEmpty ? .inkPlaceholder : .inkPrimary)
                    .lineLimit(1)
                Spacer(minLength: 0)
                Image(systemName: "chevron.down")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.inkMuted)
            }
            .padding(.horizontal, .hearth600)
            .padding(.vertical, .hearth500)
            .frame(maxWidth: .infinity)
            .background(Color.bgElevated)
            .clipShape(Capsule())
            .hearthCardElevation()
        }
        .accessibilityLabel(value.isEmpty ? placeholder : value)
    }

    /// The disabled CTA uses `bg/disabled` + `ink/secondary`. White on that
    /// fill is 2.07:1 — never pair them.
    private func primaryButton(
        _ label: String,
        disabled: Bool,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            Text(label)
                .font(.hearthTitleMD)
                .foregroundColor(disabled ? .inkSecondary : .inkOnPhotoLight)
                .frame(maxWidth: .infinity)
                .padding(.vertical, .hearth500)
                .background(disabled ? Color.bgDisabled : Color.accentDefault)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusButton, style: .continuous))
        }
        .disabled(disabled)
    }

    private func multiSelectGrid(
        options: [(label: String, symbol: String)],
        selection: Binding<[String]>
    ) -> some View {
        LazyVGrid(
            columns: [GridItem(.flexible(), spacing: .hearth300), GridItem(.flexible(), spacing: .hearth300)],
            spacing: .hearth300
        ) {
            ForEach(options, id: \.label) { option in
                let selected = selection.wrappedValue.contains(option.label)
                chip(label: option.label, symbol: option.symbol, selected: selected, fills: true) {
                    if selected {
                        selection.wrappedValue.removeAll { $0 == option.label }
                    } else {
                        selection.wrappedValue.append(option.label)
                    }
                }
            }
        }
    }

    /// Greg's chip: white pill, teal leading icon, ink label. Selected flips to
    /// the accent FILL (white on it is 5.25:1 — the one place the fill token is
    /// allowed under text).
    private func chip(
        label: String,
        symbol: String,
        selected: Bool,
        fills: Bool = false,
        action: @escaping () -> Void
    ) -> some View {
        Button {
            withAnimation(.hearth(.hearthFast, reduceMotion: reduceMotion)) { action() }
        } label: {
            HStack(spacing: .hearth300) {
                if !symbol.isEmpty {
                    Image(systemName: symbol)
                        .font(.system(size: 13, weight: .regular))
                        .symbolRenderingMode(.monochrome)
                        .foregroundColor(selected ? .inkOnPhotoLight : .accentOnCanvas)
                }
                Text(label)
                    .font(.hearthBodyMD.weight(.medium))
                    .foregroundColor(selected ? .inkOnPhotoLight : .inkPrimary)
                    .lineLimit(1)
                    .minimumScaleFactor(0.75)
            }
            .padding(.horizontal, .hearth500)
            .padding(.vertical, .hearth400)
            .frame(maxWidth: fills ? .infinity : nil)
            .background(selected ? Color.accentDefault : Color.bgElevated)
            .clipShape(Capsule())
            .hearthCardElevation()
        }
        .accessibilityAddTraits(selected ? [.isSelected] : [])
    }

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

    static func ordinalWord(_ index: Int) -> String {
        ordinalWords.indices.contains(index) ? ordinalWords[index] : "child number \(index + 1)"
    }

    private func dismissKeyboard() {
        UIApplication.shared.sendAction(
            #selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil
        )
    }
}

// MARK: - String Helper

private extension String {
    var trimmed: String { trimmingCharacters(in: .whitespacesAndNewlines) }
}
