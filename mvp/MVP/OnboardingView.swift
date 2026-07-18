import SwiftUI

// MARK: - Onboarding Data (sent to backend)

struct OnboardingData {
    let parentName: String
    let kids: [(name: String, age: String, temperament: String, pronouns: String, gradeBand: String)]
    let household: String
    let supportSystem: String
    let energyPattern: String
    let dreadedMoment: String
    let challenges: [String]
    let goals: [String]
    // Demographic additions
    let postalCode: String
    let country: String
    let primaryLanguage: String
    let parentAgeRange: String
    let adultsInHousehold: Int?
    let employment: String
    let culturalBackground: String
    let pronouns: String
}

// MARK: - Kid Entry Model

struct KidEntry: Identifiable {
    let id = UUID()
    var name: String = ""
    var age: String = ""
    var temperament: String = ""
    var pronouns: String = ""
    var gradeBand: String = ""
}

// MARK: - Whimsical Illustration Compositions

/// Floating collage-style illustration using emoji and SF Symbols
/// Inspired by CHANI's playful animal collages
private struct CollageIllustration: View {
    let items: [(String, CGFloat, CGFloat, CGFloat, Double)]  // emoji, x%, y%, size, rotation

    var body: some View {
        GeometryReader { geo in
            ZStack {
                ForEach(Array(items.enumerated()), id: \.offset) { _, item in
                    Text(item.0)
                        .font(.system(size: item.3))
                        .rotationEffect(.degrees(item.4))
                        .position(
                            x: geo.size.width * item.1,
                            y: geo.size.height * item.2
                        )
                }
            }
        }
    }
}

/// Decorative sparkle cluster that floats around content
private struct SparkleCluster: View {
    let count: Int
    let color: Color

    var body: some View {
        ZStack {
            ForEach(0..<count, id: \.self) { i in
                let angle = Double(i) * (360.0 / Double(count))
                let radius: CGFloat = CGFloat.random(in: 8...22)
                Image(systemName: ["sparkle", "star.fill", "circle.fill"][i % 3])
                    .font(.system(size: CGFloat.random(in: 4...10)))
                    .foregroundColor(color.opacity(Double.random(in: 0.4...1.0)))
                    .offset(
                        x: cos(angle * .pi / 180) * radius,
                        y: sin(angle * .pi / 180) * radius
                    )
            }
        }
    }
}

/// Wavy underline decoration inspired by CHANI's squiggly dividers
private struct WavyLine: View {
    var width: CGFloat = 120
    var color: Color = .accentDefault

    var body: some View {
        WavyShape()
            .stroke(color, style: StrokeStyle(lineWidth: 2, lineCap: .round))
            .frame(width: width, height: 8)
    }
}

private struct WavyShape: Shape {
    func path(in rect: CGRect) -> Path {
        var path = Path()
        let wavelength = rect.width / 4
        let amplitude: CGFloat = 3

        path.move(to: CGPoint(x: 0, y: rect.midY))
        for i in stride(from: 0, through: rect.width, by: 1) {
            let y = rect.midY + sin(i / wavelength * .pi * 2) * amplitude
            path.addLine(to: CGPoint(x: i, y: y))
        }
        return path
    }
}

// MARK: - Onboarding View

struct OnboardingView: View {
    var onComplete: (OnboardingData) -> Void

    @State private var keyboardVisible: Bool = false
    @State private var step: Int = 0
    @State private var parentName: String = ""
    @State private var kids: [KidEntry] = [KidEntry()]
    // Multi-select: realistic households often combine (e.g. "Two-parent
    // home" + "Blended family"). Stored as Set in UI; flattened to a
    // comma-joined String when sent to the backend.
    @State private var household: Set<String> = []
    @State private var supportSystem: Set<String> = []
    @State private var energyPattern: String = ""
    @State private var dreadedMoment: String = ""
    @State private var challenges: Set<String> = []
    @State private var goals: Set<String> = []
    @State private var isReturningUser: Bool = false
    @State private var returningUserName: String = ""
    @State private var appearAnimation: Bool = false
    // Demographic additions (step 2 "About you")
    @State private var postalCode: String = ""
    @State private var country: String = "US"
    @State private var primaryLanguage: String = ""
    @State private var parentAgeRange: String = ""
    @State private var adultsInHousehold: Int = 2
    @State private var employment: String = ""
    @State private var culturalBackground: String = ""
    @State private var pronouns: String = ""
    // Legal agreement gate on the final step. Tapping "Let's go" with this
    // checked stashes a durable legal_accept_pending flag; SwayApp's launch
    // task POSTs the acceptance (and retries next launch if it fails offline).
    @State private var agreedToLegal: Bool = false

    private let totalSteps = 9  // 0=welcome, 1=name, 2=aboutYou, 3=kids, 4=world, 5=energy, 6=challenges, 7=goals, 8=preview

    // Option lists — each entry is (label, SF Symbol name). The chip renderer
    // uses `Image(systemName: symbol)` so icons stay tinted with Hearth
    // tokens and match the editorial line-art aesthetic. Replaces the
    // previous (label, emoji) tuples that read as kindergarten-app next to
    // Fraunces typography.

    private let countryOptions: [(label: String, symbol: String)] = [
        ("US", "globe.americas"),
        ("MX", "globe.americas"),
        ("CA", "globe.americas"),
        ("GB", "globe.europe.africa"),
        ("Other", "globe")
    ]

    private let languageOptions: [(label: String, symbol: String)] = [
        ("English", "text.bubble"),
        ("Spanish", "text.bubble"),
        ("Mandarin", "text.bubble"),
        ("Other", "globe")
    ]

    private let parentAgeOptions: [(label: String, symbol: String)] = [
        ("<25", "person"),
        ("25-34", "person"),
        ("35-44", "person"),
        ("45-54", "person"),
        ("55+", "person"),
        ("Prefer not to say", "lock")
    ]

    private let employmentOptions: [(label: String, symbol: String)] = [
        ("Stay-at-home", "house"),
        ("Part-time", "clock"),
        ("Full-time", "briefcase"),
        ("Shift work", "moon.stars"),
        ("Self-employed", "laptopcomputer"),
        ("Unemployed", "pause.circle"),
        ("Other", "ellipsis.circle")
    ]

    // Pronouns are text-primary; icon adds noise. Symbol kept for tuple
    // shape consistency but the chip renderer can drop it when empty.
    private let parentPronounsOptions: [(label: String, symbol: String)] = [
        ("she/her", ""),
        ("he/him", ""),
        ("they/them", ""),
        ("Other", "")
    ]

    private let kidPronounsOptions: [(label: String, symbol: String)] = [
        ("she/her", ""),
        ("he/him", ""),
        ("they/them", "")
    ]

    private let gradeBandOptions = [
        "Pre-K", "K", "1", "2", "3", "4", "5",
        "6", "7", "8", "9", "10", "11", "12", "N/A"
    ]

    private let householdOptions: [(label: String, symbol: String)] = [
        ("Two-parent home", "house.fill"),
        ("Single parent", "person.fill"),
        ("Co-parenting", "person.2.fill"),
        ("Blended family", "person.3.fill"),
        ("Extended family", "house.and.flag"),
        ("It's complicated", "questionmark.circle")
    ]

    private let supportOptions: [(label: String, symbol: String)] = [
        ("Family nearby", "heart"),
        ("Childcare/nanny", "figure.and.child.holdinghands"),
        ("Partner is hands-on", "hands.sparkles"),
        ("Friends & neighbors", "person.3"),
        ("Online communities", "bubble.left.and.bubble.right"),
        ("Mostly on my own", "person")
    ]

    private let energyOptions: [(label: String, symbol: String)] = [
        ("Morning person", "sunrise"),
        ("Night owl", "moon.stars"),
        ("Afternoon peak", "sun.max"),
        ("Depends on the day", "arrow.triangle.2.circlepath")
    ]

    private let dreadedOptions: [(label: String, symbol: String)] = [
        ("Mornings", "sunrise"),
        ("After school", "bag"),
        ("Dinnertime", "fork.knife"),
        ("Bedtime", "bed.double"),
        ("Weekends", "calendar"),
        ("Homework hour", "book"),
        ("Transitions", "arrow.triangle.swap"),
        ("Honestly, all of it", "face.smiling")
    ]

    private let temperamentOptions: [(label: String, symbol: String)] = [
        ("Spirited", "flame"),
        ("Sensitive", "heart"),
        ("Easy-going", "cloud.sun"),
        ("Strong-willed", "bolt"),
        ("Shy/cautious", "tortoise"),
        ("Social butterfly", "figure.wave")
    ]

    private let challengeOptions: [(label: String, symbol: String)] = [
        ("Morning routines", "sunrise"),
        ("Bedtime battles", "moon.zzz"),
        ("Big emotions", "wave.3.left"),
        ("Picky eating", "fork.knife"),
        ("Screen time", "iphone"),
        ("Sibling rivalry", "person.2"),
        ("Work-life balance", "scale.3d"),
        ("Feeling alone in it", "person"),
        ("School struggles", "book.closed"),
        ("Behavior changes", "arrow.triangle.2.circlepath")
    ]

    private let goalOptions: [(label: String, symbol: String)] = [
        ("Expert guidance", "book"),
        ("Daily strategies", "list.bullet"),
        ("Understanding my child", "magnifyingglass"),
        ("Community support", "person.3"),
        ("Managing my stress", "heart.circle"),
        ("Building confidence", "figure.stand")
    ]

    var body: some View {
        ZStack {
            Color.bgCanvas
                .ignoresSafeArea()

            Group {
                switch step {
                case 0: welcomeScreen
                case 1: nameScreen
                case 2: aboutYouScreen
                case 3: kidsScreen
                case 4: worldScreen
                case 5: energyScreen
                case 6: challengesScreen
                case 7: goalsScreen
                case 8: previewScreen
                default: welcomeScreen
                }
            }
            .transition(.asymmetric(
                insertion: .opacity.combined(with: .move(edge: .trailing)),
                removal: .opacity.combined(with: .move(edge: .leading))
            ))
        }
        // Phase 1: light mode locked. Dark-mode tokens arrive in Phase 2.
        .preferredColorScheme(.light)
        .onAppear { withAnimation(.hearthSlow) { appearAnimation = true } }
        .onReceive(NotificationCenter.default.publisher(for: UIResponder.keyboardWillShowNotification)) { _ in
            withAnimation(.easeOut(duration: 0.2)) { keyboardVisible = true }
        }
        .onReceive(NotificationCenter.default.publisher(for: UIResponder.keyboardWillHideNotification)) { _ in
            withAnimation(.easeOut(duration: 0.2)) { keyboardVisible = false }
        }
    }

    // MARK: - Progress Indicator

    private func progressDots(current: Int) -> some View {
        HStack(spacing: 6) {
            ForEach(1..<totalSteps, id: \.self) { i in
                Capsule()
                    .fill(i <= current ? Color.accentDefault : Color.accentDefault.opacity(0.2))
                    .frame(width: i == current ? 24 : 8, height: 4)
                    .animation(.easeInOut(duration: 0.3), value: current)
            }
        }
        .padding(.top, 12)
    }

    // MARK: - Screen 0: Welcome
    //
    // Editorial magazine-cover composition: full-bleed Hearth photo hero
    // on the upper ~55% of the screen, ink-on-cream content card below
    // with wordmark + tagline + CTAs. No emoji decorations, no wavy
    // underlines — the photo carries the warmth, type carries the brand.
    //
    // The hero image lives in Assets.xcassets/WelcomeHero.imageset and
    // is swappable: drop a different MJ generation at the same name and
    // path, rebuild, no code changes.

    private var welcomeScreen: some View {
        GeometryReader { geo in
            VStack(spacing: 0) {
                // ─── Hero photo (full-bleed, top 55%) ──────────────
                Image("WelcomeHero")
                    .resizable()
                    .scaledToFill()
                    .frame(width: geo.size.width, height: geo.size.height * 0.55)
                    .clipped()
                    .opacity(appearAnimation ? 1 : 0)

                // ─── Cream content card (bottom 45%) ───────────────
                VStack(spacing: 0) {
                    Spacer(minLength: 32)

                    // Wordmark — Fraunces ExtraBold, sits centered above the tagline
                    MVPLogoView(variant: .lockup, size: 200, tint: .inkPrimary)

                    Spacer(minLength: 20)

                    // Tagline — Fraunces italic display, ink/secondary on cream
                    Text("Every parent deserves\nsomeone in their corner.")
                        .font(.custom("Fraunces", size: 22).italic())
                        .foregroundColor(.inkSecondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 32)
                        .lineSpacing(4)

                    Spacer()

                    // CTAs
                    if isReturningUser {
                        VStack(spacing: 12) {
                            onboardingTextField(placeholder: "Your name", text: $returningUserName)
                                .padding(.horizontal, .hearth700)

                            brandButton(label: "Continue", disabled: returningUserName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty) {
                                let trimmed = returningUserName.trimmingCharacters(in: .whitespacesAndNewlines)
                                guard !trimmed.isEmpty else { return }
                                onComplete(OnboardingData(
                                    parentName: trimmed, kids: [], household: "",
                                    supportSystem: "", energyPattern: "", dreadedMoment: "",
                                    challenges: [], goals: [],
                                    postalCode: "", country: "", primaryLanguage: "",
                                    parentAgeRange: "", adultsInHousehold: nil,
                                    employment: "", culturalBackground: "", pronouns: ""
                                ))
                            }
                            .padding(.horizontal, .hearth700)
                        }
                        .transition(.opacity.combined(with: .move(edge: .bottom)))
                    } else {
                        VStack(spacing: 10) {
                            brandButton(label: "I'm new here") {
                                advance(to: 1)
                            }
                            .padding(.horizontal, .hearth700)

                            Button {
                                withAnimation(.easeInOut(duration: 0.3)) { isReturningUser = true }
                            } label: {
                                Text("Welcome back")
                                    .font(.custom("Inter", size: 15).weight(.semibold))
                                    .foregroundColor(.inkPrimary)
                                    .frame(maxWidth: .infinity)
                                    .padding(.vertical, 14)
                                    .overlay(Capsule().stroke(Color.borderStrong, lineWidth: 1))
                            }
                            .padding(.horizontal, .hearth700)
                        }
                    }

                    Spacer().frame(height: 40)
                }
                .frame(width: geo.size.width, height: geo.size.height * 0.45)
                .background(Color.bgCanvas)
            }
            .ignoresSafeArea(edges: .top)
        }
        .trackScreen("onboarding")
    }

    // MARK: - Screen 1: Name

    private var nameScreen: some View {
        VStack(alignment: .leading, spacing: 0) {
            onboardingHeader(backTo: 0, step: 1)

            // Editorial hero — replaces the previous emoji collage. The
            // photo lives in Assets.xcassets/OnboardingStep1.imageset; swap
            // the PNG at the same path to refresh without code changes.
            onboardingStepImage("OnboardingStep1")
                .padding(.top, 8)
                .padding(.bottom, 16)

            onboardingHeading("What should we\ncall you?", subtitle: "Just a first name is perfect.")

            Spacer().frame(height: .hearth700)

            onboardingTextField(placeholder: "Your name", text: $parentName)
                .padding(.horizontal, .hearth700)

            Spacer()

            brandButton(label: "Next", disabled: parentName.trimmed.isEmpty) {
                advance(to: 2)
            }
            .padding(.horizontal, .hearth700)
            .padding(.bottom, 48)
        }
    }

    // MARK: - Screen 2: About You (demographics)

    private var aboutYouScreen: some View {
        VStack(alignment: .leading, spacing: 0) {
            ZStack {
                onboardingHeader(backTo: 1, step: 2)
                HStack {
                    Spacer()
                    Button { advance(to: 3) } label: {
                        Text("Skip")
                            .font(.hearthBodyMD.weight(.medium))
                            .foregroundColor(.accentDefault)
                            .padding(.horizontal, 14)
                            .padding(.vertical, 6)
                    }
                }
                .padding(.horizontal, 12)
                .padding(.top, 8)
            }

            onboardingStepImage("OnboardingStep2")
                .padding(.top, 4)
                .padding(.bottom, 12)

            onboardingHeading("A little about\nyou", subtitle: "All optional. Helps us tailor advice to your world.")

            Spacer().frame(height: 16)

            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Zip + Country row
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Where you are")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        HStack(spacing: 12) {
                            onboardingTextField(
                                placeholder: "Zip / postal",
                                text: $postalCode,
                                keyboardType: .numbersAndPunctuation
                            )

                            Menu {
                                ForEach(countryOptions, id: \.label) { option in
                                    Button {
                                        country = option.label
                                    } label: {
                                        Label(option.label, systemImage: option.symbol)
                                    }
                                }
                            } label: {
                                HStack(spacing: 8) {
                                    Image(systemName: countryOptions.first(where: { $0.label == country })?.symbol ?? "globe")
                                        .font(.system(size: 14, weight: .regular))
                                    Text(country.isEmpty ? "Country" : country)
                                        .font(.hearthBodyMD)
                                    Image(systemName: "chevron.down")
                                        .font(.caption)
                                }
                                .foregroundColor(.inkPrimary)
                                .padding(.horizontal, 14)
                                .padding(.vertical, 14)
                                .background(Color.bgElevated)
                                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                                        .stroke(Color.borderHairline, style: StrokeStyle(lineWidth: 1, dash: [6]))
                                )
                            }
                        }
                    }

                    // Primary language
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Primary language at home")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        singleSelectGrid(options: languageOptions, selection: $primaryLanguage)
                    }

                    // Parent age range
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Your age range")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        singleSelectGrid(options: parentAgeOptions, selection: $parentAgeRange)
                    }

                    // Adults in household
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Adults in your household")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        // Pill stepper — one visual unit, single color family,
                        // sans-serif numeral matches the SF Symbol icon
                        // language. Min/max enforced via button disabled state.
                        HStack(spacing: 0) {
                            HStack(spacing: 0) {
                                Button {
                                    if adultsInHousehold > 1 { adultsInHousehold -= 1 }
                                } label: {
                                    Image(systemName: "minus")
                                        .font(.system(size: 16, weight: .medium))
                                        .foregroundColor(adultsInHousehold > 1 ? .inkPrimary : .inkMuted)
                                        .frame(width: 44, height: 44)
                                        .contentShape(Rectangle())
                                }
                                .disabled(adultsInHousehold <= 1)

                                Text("\(adultsInHousehold)")
                                    .font(.hearthBodyMD.weight(.medium))
                                    .foregroundColor(.inkPrimary)
                                    .frame(minWidth: 24)
                                    .monospacedDigit()

                                Button {
                                    if adultsInHousehold < 4 { adultsInHousehold += 1 }
                                } label: {
                                    Image(systemName: "plus")
                                        .font(.system(size: 16, weight: .medium))
                                        .foregroundColor(adultsInHousehold < 4 ? .inkPrimary : .inkMuted)
                                        .frame(width: 44, height: 44)
                                        .contentShape(Rectangle())
                                }
                                .disabled(adultsInHousehold >= 4)
                            }
                            .background(Color.bgElevated)
                            .clipShape(Capsule())
                            .overlay(Capsule().stroke(Color.borderHairline, lineWidth: 1))

                            Spacer()
                        }
                    }

                    // Employment
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Work pattern")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        singleSelectGrid(options: employmentOptions, selection: $employment)
                    }

                    // Pronouns
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Your pronouns")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        singleSelectGrid(options: parentPronounsOptions, selection: $pronouns)
                    }

                    // Cultural background
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Cultural background (optional)")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        onboardingTextField(
                            placeholder: "e.g., Mexican-American, South Asian",
                            text: $culturalBackground
                        )
                    }
                }
                .padding(.horizontal, .hearth700)
                .padding(.bottom, 16)
            }

            Spacer()

            brandButton(label: "Next") { advance(to: 3) }
                .padding(.horizontal, .hearth700)
                .padding(.bottom, 48)
        }
    }

    // MARK: - Screen 3: Kids

    private var kidsScreen: some View {
        VStack(alignment: .leading, spacing: 0) {
            onboardingHeader(backTo: 2, step: 3)

            onboardingStepImage("OnboardingStep3")
                .padding(.top, 4)
                .padding(.bottom, 12)

            onboardingHeading("Tell us about your\nlittle ones", subtitle: "Names, ages, and a peek at their personality.")

            Spacer().frame(height: 24)

            ScrollView {
                VStack(spacing: 20) {
                    ForEach(Array(kids.enumerated()), id: \.element.id) { index, _ in
                        kidCard(index: index)
                    }

                    Button {
                        kids.append(KidEntry())
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: "plus.circle")
                                .font(.body.weight(.medium))
                            Text("Add another child")
                                .font(.hearthBodyMD.weight(.medium))
                        }
                        .foregroundColor(.accentDefault)
                    }
                    .padding(.top, 4)
                }
                .padding(.horizontal, .hearth700)
            }

            Spacer()

            brandButton(
                label: "Next",
                disabled: !kids.contains(where: { !$0.name.trimmed.isEmpty })
            ) {
                advance(to: 4)
            }
            .padding(.horizontal, .hearth700)
            .padding(.bottom, 48)
        }
    }

    // MARK: - Screen 4: Your World

    private var worldScreen: some View {
        VStack(alignment: .leading, spacing: 0) {
            onboardingHeader(backTo: 3, step: 4)

            // Illustration: home & family collage
            onboardingStepImage("OnboardingStep4")
                .padding(.top, 4)
                .padding(.bottom, 12)

            onboardingHeading("Paint us a picture\nof your world", subtitle: "No right answers. Just your reality.")

            Spacer().frame(height: 24)

            ScrollView {
                VStack(alignment: .leading, spacing: 28) {
                    // Household
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Your household")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        multiSelectGrid(options: householdOptions, selection: $household)
                    }

                    // Support system
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Your support crew")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        multiSelectGrid(options: supportOptions, selection: $supportSystem)
                    }
                }
                .padding(.horizontal, .hearth700)
            }

            Spacer()

            brandButton(label: "Next") { advance(to: 5) }
                .padding(.horizontal, .hearth700)
                .padding(.bottom, 48)
        }
    }

    // MARK: - Screen 5: Energy & Dread

    private var energyScreen: some View {
        VStack(alignment: .leading, spacing: 0) {
            onboardingHeader(backTo: 4, step: 5)

            onboardingStepImage("OnboardingStep5")
                .padding(.top, 4)
                .padding(.bottom, 12)

            onboardingHeading("When do you feel\nmost yourself?", subtitle: "And when does it all feel like... a lot?")

            Spacer().frame(height: 24)

            ScrollView {
                VStack(alignment: .leading, spacing: 28) {
                    // Energy pattern
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Your energy sweet spot")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        singleSelectGrid(options: energyOptions, selection: $energyPattern)
                    }

                    // Dreaded moment
                    VStack(alignment: .leading, spacing: 12) {
                        Text("The part of the day you dread")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        singleSelectGrid(options: dreadedOptions, selection: $dreadedMoment)
                    }
                }
                .padding(.horizontal, .hearth700)
            }

            Spacer()

            brandButton(label: "Next") { advance(to: 6) }
                .padding(.horizontal, .hearth700)
                .padding(.bottom, 48)
        }
    }

    // MARK: - Screen 6: Challenges

    private var challengesScreen: some View {
        VStack(alignment: .leading, spacing: 0) {
            onboardingHeader(backTo: 5, step: 6)

            onboardingStepImage("OnboardingStep6")
                .padding(.top, 4)
                .padding(.bottom, 12)

            onboardingHeading("What feels hardest\nright now?", subtitle: "Pick as many as you want. No judgment here.")

            Spacer().frame(height: 24)

            ScrollView {
                chipGrid(options: challengeOptions, selection: $challenges)
                    .padding(.horizontal, .hearth700)
            }

            Spacer()

            brandButton(label: "Next") { advance(to: 7) }
                .padding(.horizontal, .hearth700)
                .padding(.bottom, 48)
        }
    }

    // MARK: - Screen 7: Goals

    private var goalsScreen: some View {
        VStack(alignment: .leading, spacing: 0) {
            onboardingHeader(backTo: 6, step: 7)

            onboardingStepImage("OnboardingStep7")
                .padding(.top, 4)
                .padding(.bottom, 12)

            onboardingHeading("What are you\nhoping for?", subtitle: "This helps us point you in the right direction.")

            Spacer().frame(height: 24)

            ScrollView {
                chipGrid(options: goalOptions, selection: $goals)
                    .padding(.horizontal, .hearth700)
            }

            Spacer()

            brandButton(label: "Next") { advance(to: 8) }
                .padding(.horizontal, .hearth700)
                .padding(.bottom, 48)
        }
    }

    // MARK: - Screen 8: Preview / Launch

    /// Builds compact chips of filled-in parent demographics. Empty array if nothing is set
    /// (e.g., returning user who bypassed the demographic step).
    private func parentSummaryChips() -> [String] {
        var parts: [String] = []
        // Summary chips are plain strings (no SF Symbol — they render in
        // the recap view as Fraunces text). Drop the icon entirely; the
        // country code or postal code alone is informative.
        if !postalCode.trimmed.isEmpty {
            parts.append(postalCode.trimmed)
        } else if !country.isEmpty && country != "US" {
            parts.append(country)
        }
        if !primaryLanguage.isEmpty { parts.append(primaryLanguage) }
        if !parentAgeRange.isEmpty { parts.append(parentAgeRange) }
        if !employment.isEmpty { parts.append(employment) }
        if !pronouns.isEmpty { parts.append(pronouns) }
        if !culturalBackground.trimmed.isEmpty { parts.append(culturalBackground.trimmed) }
        if !household.isEmpty { parts.append(household.sorted().joined(separator: ", ")) }
        // Only surface the adults count if the user touched any other field on the About-you step
        if !parts.isEmpty { parts.append("\(adultsInHousehold) adult\(adultsInHousehold == 1 ? "" : "s")") }
        return parts
    }

    private func kidSummaryLine(_ kid: KidEntry) -> String {
        var head = kid.name.trimmed
        if !kid.age.trimmed.isEmpty { head += " (\(kid.age.trimmed))" }
        var tail: [String] = []
        if !kid.temperament.isEmpty { tail.append(kid.temperament) }
        if !kid.pronouns.isEmpty { tail.append(kid.pronouns) }
        if !kid.gradeBand.isEmpty { tail.append("\(kid.gradeBand) grade") }
        return tail.isEmpty ? head : "\(head) · \(tail.joined(separator: " · "))"
    }

    @ViewBuilder
    private var personalizedSummary: some View {
        let parentChips = parentSummaryChips()
        let filledKids = kids.filter { !$0.name.trimmed.isEmpty }
        let hasAnything = !parentChips.isEmpty || !filledKids.isEmpty

        if hasAnything {
            VStack(alignment: .leading, spacing: 12) {
                sectionLabel("Here's what we have")

                if !parentChips.isEmpty {
                    Text(parentChips.joined(separator: " · "))
                        .font(.system(.subheadline, design: .serif))
                        .foregroundColor(.inkPrimary)
                        .fixedSize(horizontal: false, vertical: true)
                }

                ForEach(filledKids) { kid in
                    HStack(alignment: .top, spacing: 10) {
                        Text("\u{1F33F}")
                            .font(.system(size: 14))
                        Text(kidSummaryLine(kid))
                            .font(.system(.subheadline, design: .serif))
                            .foregroundColor(.inkPrimary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.bgElevated.opacity(0.5))
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(Color.borderHairline, lineWidth: 1)
            )
        }
    }

    /// Blocking agree-checkbox on the final step. The doc links open the
    /// CMS-published pages on the dashboard; the base URL resolves through the
    /// same chain as the seed (never a hardcoded host).
    private var legalAgreementRow: some View {
        let base = UserDefaults.standard.string(forKey: "chat.base_url") ?? ServerConfiguration.defaultURL
        return HStack(alignment: .top, spacing: 12) {
            Button {
                agreedToLegal.toggle()
            } label: {
                Image(systemName: agreedToLegal ? "checkmark.square.fill" : "square")
                    .font(.system(size: 22, weight: .medium))
                    .foregroundColor(agreedToLegal ? .accentDefault : .inkMuted)
            }
            .accessibilityLabel(agreedToLegal ? "Agreed to terms" : "Agree to terms")

            if let agreement = try? AttributedString(
                markdown: "I agree to the [Privacy Policy](\(base)/dashboard/docs/privacy-policy) "
                    + "and [Terms of Service](\(base)/dashboard/docs/terms)"
            ) {
                Text(agreement)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                    .tint(.accentDefault)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private var previewScreen: some View {
        let features: [(String, String)] = [
            ("\u{1F9E0}", "AI coach that knows your family"),
            ("\u{1F4AC}", "Strategies personalized to you"),
            ("\u{1F4DA}", "Library of expert articles"),
            ("\u{1F91D}", "Real parent community"),
            ("\u{1F331}", "Gets smarter the more you share"),
            ("\u{1F49B}", "No judgment, ever")
        ]

        return VStack(alignment: .leading, spacing: 0) {
            onboardingHeader(backTo: 7, step: 8)

            // Celebration collage
            onboardingStepImage("OnboardingStep8")
                .padding(.top, 4)
                .padding(.bottom, 12)

            onboardingHeading("And here's a peek\nat the goodness")

            Spacer().frame(height: .hearth700)

            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    personalizedSummary

                    VStack(alignment: .leading, spacing: 20) {
                        ForEach(features, id: \.1) { emoji, text in
                            HStack(spacing: 14) {
                                Text(emoji)
                                    .font(.system(size: 24))

                                Text(text)
                                    .font(.system(.body, design: .serif).weight(.medium))
                                    .foregroundColor(.inkPrimary)
                            }
                        }
                    }
                }
                .padding(.horizontal, .hearth700)
                .padding(.bottom, 16)
            }

            let displayName = parentName.trimmed
            legalAgreementRow
                .padding(.horizontal, .hearth700)
                .padding(.bottom, .hearth400)
            brandButton(label: "Let's go, \(displayName)!", disabled: !agreedToLegal) {
                UserDefaults.standard.set(true, forKey: LegalService.acceptPendingKey)
                let kidData = kids
                    .filter { !$0.name.trimmed.isEmpty }
                    .map { (
                        name: $0.name.trimmed,
                        age: $0.age.trimmed,
                        temperament: $0.temperament,
                        pronouns: $0.pronouns,
                        gradeBand: $0.gradeBand
                    ) }
                onComplete(OnboardingData(
                    parentName: displayName,
                    kids: kidData,
                    household: household.sorted().joined(separator: ", "),
                    supportSystem: supportSystem.sorted().joined(separator: ", "),
                    energyPattern: energyPattern,
                    dreadedMoment: dreadedMoment,
                    challenges: Array(challenges),
                    goals: Array(goals),
                    postalCode: postalCode.trimmed,
                    country: country,
                    primaryLanguage: primaryLanguage,
                    parentAgeRange: parentAgeRange,
                    adultsInHousehold: adultsInHousehold,
                    employment: employment,
                    culturalBackground: culturalBackground.trimmed,
                    pronouns: pronouns
                ))
            }
            .padding(.horizontal, .hearth700)
            .padding(.bottom, 48)
        }
    }

    // MARK: - Reusable Components

    private func advance(to target: Int) {
        withAnimation(.easeInOut(duration: 0.3)) { step = target }
    }

    /// Shared section-label style — UPPERCASE caption-mono, ink/muted,
    /// tracked. Used above every chip grid (Your household / Your support
    /// crew / Your energy sweet spot / etc.). Matches the section-label
    /// pattern in LibraryView + HomeView for cross-screen consistency.
    private func sectionLabel(_ text: String) -> some View {
        Text(text)
            .font(.hearthLabel)
            .foregroundColor(.inkMuted)
            .tracking(0.66)
            .textCase(.uppercase)
    }

    /// Shared frame for the editorial photo at the top of each onboarding
    /// step. Centered on the page. 180pt square, soft rounded corners,
    /// hairline border. Headings are centered to match (see
    /// `onboardingHeading` helper); form fields below stay leading-aligned.
    /// Each step references its own image asset by name so a designer can
    /// swap any one screen's photo without touching the other 8.
    @ViewBuilder
    private func onboardingStepImage(_ assetName: String) -> some View {
        if !keyboardVisible {
            HStack {
                Spacer()
                Image(assetName)
                    .resizable()
                    .scaledToFill()
                    .frame(width: 180, height: 180)
                    .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                            .stroke(Color.borderHairline, lineWidth: 1)
                    )
                Spacer()
            }
        }
    }

    /// Centered heading + optional subtitle pair. Used at the top of every
    /// onboarding funnel step so the title block visually aligns with the
    /// centered editorial photo above it. Form fields below the heading
    /// remain leading-aligned (chip grids + inputs scan better that way).
    private func onboardingHeading(_ title: String, subtitle: String? = nil) -> some View {
        VStack(spacing: keyboardVisible ? 2 : 6) {
            Text(title)
                .font(keyboardVisible ? .hearthTitleLG : .hearthDisplayMD)
                .foregroundColor(.inkPrimary)
                .multilineTextAlignment(.center)

            if !keyboardVisible, let subtitle = subtitle {
                Text(subtitle)
                    .font(.hearthBodyMD.italic())
                    .foregroundColor(.inkSecondary)
                    .multilineTextAlignment(.center)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.horizontal, .hearth700)
    }

    private func onboardingHeader(backTo target: Int, step current: Int) -> some View {
        VStack(spacing: 0) {
            HStack {
                Button { advance(to: target) } label: {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(.inkPrimary)
                        .frame(width: 44, height: 44)
                }
                Spacer()
            }
            .padding(.horizontal, 12)
            .padding(.top, 8)

            progressDots(current: current)
        }
    }

    private func onboardingTextField(placeholder: String, text: Binding<String>, keyboardType: UIKeyboardType = .default, width: CGFloat? = nil) -> some View {
        TextField("", text: text, prompt: Text(placeholder).foregroundColor(.inkMuted))
            .font(.hearthBodyLG)
            .foregroundColor(.inkPrimary)
            .keyboardType(keyboardType)
            .padding(.horizontal, .hearth500)
            .padding(.vertical, .hearth400)
            .background(Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                    .stroke(Color.borderStrong, lineWidth: 1)
            )
            .frame(width: width)
    }

    private func brandButton(label: String, disabled: Bool = false, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(label)
                .font(.hearthTitleMD)
                .foregroundColor(.inkOnPhotoLight)
                .frame(maxWidth: .infinity)
                .padding(.vertical, .hearth500)
                .background(Color.accentDefault)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
        }
        .disabled(disabled)
        .opacity(disabled ? 0.5 : 1.0)
    }

    private func kidCard(index: Int) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 12) {
                onboardingTextField(placeholder: "Name", text: $kids[index].name)

                onboardingTextField(
                    placeholder: "Age",
                    text: $kids[index].age,
                    keyboardType: .numberPad,
                    width: 72
                )

                if kids.count > 1 {
                    Button { kids.remove(at: index) } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.system(size: 22))
                            .foregroundColor(.inkSecondary)
                    }
                }
            }

            // Temperament picker (inline)
            if !kids[index].name.trimmed.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("What's \(kids[index].name.trimmed.isEmpty ? "their" : kids[index].name.trimmed)'s vibe?")
                        .font(.system(.caption, design: .serif).italic())
                        .foregroundColor(.inkSecondary)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(temperamentOptions, id: \.label) { option in
                                let isSelected = kids[index].temperament == option.label
                                Button {
                                    withAnimation(.easeInOut(duration: 0.15)) {
                                        kids[index].temperament = isSelected ? "" : option.label
                                    }
                                } label: {
                                    HStack(spacing: 6) {
                                        if !option.symbol.isEmpty {
                                            Image(systemName: option.symbol)
                                                .font(.system(size: 12, weight: .regular))
                                                .symbolRenderingMode(.monochrome)
                                        }
                                        Text(option.label)
                                            .font(.hearthBodySM.weight(.medium))
                                            .lineLimit(1)
                                            .fixedSize(horizontal: true, vertical: false)
                                    }
                                    .foregroundColor(isSelected ? .inkOnPhotoLight : .inkPrimary)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 8)
                                    .background(isSelected ? Color.accentDefault : Color.bgElevated)
                                    .clipShape(Capsule())
                                    .overlay(
                                        Capsule().stroke(isSelected ? Color.clear : Color.borderHairline, lineWidth: 1)
                                    )
                                }
                            }
                        }
                    }
                }

                // Pronouns + Grade band row
                HStack(spacing: 10) {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 6) {
                            ForEach(kidPronounsOptions, id: \.label) { option in
                                let isSelected = kids[index].pronouns == option.label
                                Button {
                                    withAnimation(.easeInOut(duration: 0.15)) {
                                        kids[index].pronouns = isSelected ? "" : option.label
                                    }
                                } label: {
                                    Text(option.label)
                                        .font(.hearthBodySM.weight(.medium))
                                        .lineLimit(1)
                                        .fixedSize(horizontal: true, vertical: false)
                                        .foregroundColor(isSelected ? .inkOnPhotoLight : .inkPrimary)
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 6)
                                        .background(isSelected ? Color.accentDefault : Color.bgElevated)
                                        .clipShape(Capsule())
                                        .overlay(
                                            Capsule().stroke(isSelected ? Color.clear : Color.borderHairline, lineWidth: 1)
                                        )
                                }
                            }
                        }
                    }

                    Menu {
                        ForEach(gradeBandOptions, id: \.self) { band in
                            Button { kids[index].gradeBand = band } label: { Text(band) }
                        }
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "graduationcap")
                                .font(.caption)
                            Text(kids[index].gradeBand.isEmpty ? "Grade" : kids[index].gradeBand)
                                .font(.system(.caption2, design: .serif).weight(.medium))
                            Image(systemName: "chevron.down")
                                .font(.caption2)
                        }
                        .foregroundColor(.inkPrimary)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(Color.bgElevated)
                        .clipShape(Capsule())
                        .overlay(
                            Capsule().stroke(Color.borderHairline, lineWidth: 1)
                        )
                    }
                }
            }
        }
        .padding(16)
        .background(Color.bgElevated.opacity(0.5))
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .stroke(Color.borderHairline, lineWidth: 1)
        )
    }

    private func singleSelectGrid(options: [(label: String, symbol: String)], selection: Binding<String>) -> some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
            ForEach(options, id: \.label) { option in
                let isSelected = selection.wrappedValue == option.label
                Button {
                    withAnimation(.easeInOut(duration: 0.15)) {
                        selection.wrappedValue = isSelected ? "" : option.label
                    }
                } label: {
                    chipLabel(symbol: option.symbol, label: option.label, isSelected: isSelected)
                }
            }
        }
    }

    /// Multi-select variant of singleSelectGrid. Tapping toggles each option
    /// independently — used on screens like "Your household" and "Your
    /// support crew" where multiple answers are realistic.
    private func multiSelectGrid(options: [(label: String, symbol: String)], selection: Binding<Set<String>>) -> some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
            ForEach(options, id: \.label) { option in
                let isSelected = selection.wrappedValue.contains(option.label)
                Button {
                    withAnimation(.easeInOut(duration: 0.15)) {
                        if isSelected {
                            selection.wrappedValue.remove(option.label)
                        } else {
                            selection.wrappedValue.insert(option.label)
                        }
                    }
                } label: {
                    chipLabel(symbol: option.symbol, label: option.label, isSelected: isSelected)
                }
            }
        }
    }

    /// Alias for the 2-col multi-select grid kept distinct in name for
    /// caller-readability (challenges / goals read more naturally as
    /// `chipGrid` than `multiSelectGrid`).
    private func chipGrid(options: [(label: String, symbol: String)], selection: Binding<Set<String>>) -> some View {
        multiSelectGrid(options: options, selection: selection)
    }

    /// Shared chip-button label — keeps colors + spacing consistent across
    /// all chip grids. Renders an SF Symbol prefix when `symbol` is
    /// non-empty; otherwise the chip is text-only (used for pronouns and
    /// other label-primary options where an icon would be noise).
    private func chipLabel(symbol: String, label: String, isSelected: Bool) -> some View {
        HStack(spacing: 8) {
            if !symbol.isEmpty {
                Image(systemName: symbol)
                    .font(.system(size: 14, weight: .regular))
                    .symbolRenderingMode(.monochrome)
            }
            Text(label)
                .font(.hearthBodyMD.weight(.medium))
                .lineLimit(1)
                .minimumScaleFactor(0.8)
        }
        .foregroundColor(isSelected ? .inkOnPhotoLight : .inkPrimary)
        .padding(.horizontal, .hearth500)
        .padding(.vertical, .hearth400)
        .frame(maxWidth: .infinity)
        .background(isSelected ? Color.accentDefault : Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                .stroke(isSelected ? Color.clear : Color.borderHairline, lineWidth: 1)
        )
    }
}

// MARK: - String Helper

private extension String {
    var trimmed: String { trimmingCharacters(in: .whitespacesAndNewlines) }
}
