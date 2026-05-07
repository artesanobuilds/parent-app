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
    var color: Color = .brandGold

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

    @State private var step: Int = 0
    @State private var parentName: String = ""
    @State private var kids: [KidEntry] = [KidEntry()]
    @State private var household: String = ""
    @State private var supportSystem: String = ""
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

    private let totalSteps = 9  // 0=welcome, 1=name, 2=aboutYou, 3=kids, 4=world, 5=energy, 6=challenges, 7=goals, 8=preview

    private let countryOptions = [
        ("US", "\u{1F1FA}\u{1F1F8}"),
        ("MX", "\u{1F1F2}\u{1F1FD}"),
        ("CA", "\u{1F1E8}\u{1F1E6}"),
        ("GB", "\u{1F1EC}\u{1F1E7}"),
        ("Other", "\u{1F310}")
    ]

    private let languageOptions = [
        ("English", "\u{1F1FA}\u{1F1F8}"),
        ("Spanish", "\u{1F1EA}\u{1F1F8}"),
        ("Mandarin", "\u{1F1E8}\u{1F1F3}"),
        ("Other", "\u{1F310}")
    ]

    private let parentAgeOptions = [
        ("<25", "\u{1F331}"),
        ("25-34", "\u{1F33F}"),
        ("35-44", "\u{1F33E}"),
        ("45-54", "\u{1F332}"),
        ("55+", "\u{1F333}"),
        ("Prefer not to say", "\u{1F910}")
    ]

    private let employmentOptions = [
        ("Stay-at-home", "\u{1F3E1}"),
        ("Part-time", "\u{1F552}"),
        ("Full-time", "\u{1F4BC}"),
        ("Shift work", "\u{1F319}"),
        ("Self-employed", "\u{1F4BB}"),
        ("Unemployed", "\u{1F33F}"),
        ("Other", "\u{2728}")
    ]

    private let parentPronounsOptions = [
        ("she/her", "\u{1F338}"),
        ("he/him", "\u{1F343}"),
        ("they/them", "\u{1F308}"),
        ("Other", "\u{2728}")
    ]

    private let kidPronounsOptions = [
        ("she/her", "\u{1F338}"),
        ("he/him", "\u{1F343}"),
        ("they/them", "\u{1F308}")
    ]

    private let gradeBandOptions = [
        "Pre-K", "K", "1", "2", "3", "4", "5",
        "6", "7", "8", "9", "10", "11", "12", "N/A"
    ]

    private let householdOptions = [
        ("Two-parent home", "\u{1F3E0}"),
        ("Single parent", "\u{1F4AA}"),
        ("Co-parenting", "\u{1F91D}"),
        ("Blended family", "\u{1F33F}"),
        ("Extended family", "\u{1F46A}"),
        ("It's complicated", "\u{1F30A}")
    ]

    private let supportOptions = [
        ("Family nearby", "\u{2764}\u{FE0F}"),
        ("Childcare/nanny", "\u{1F476}"),
        ("Partner is hands-on", "\u{1F64C}"),
        ("Friends & neighbors", "\u{1F3E1}"),
        ("Online communities", "\u{1F4F1}"),
        ("Mostly on my own", "\u{1F331}")
    ]

    private let energyOptions = [
        ("Morning person", "\u{2600}\u{FE0F}"),
        ("Night owl", "\u{1F319}"),
        ("Afternoon peak", "\u{26A1}"),
        ("Depends on the day", "\u{1F300}")
    ]

    private let dreadedOptions = [
        ("Mornings", "\u{23F0}"),
        ("After school", "\u{1F3EB}"),
        ("Dinnertime", "\u{1F372}"),
        ("Bedtime", "\u{1F634}"),
        ("Weekends", "\u{1F3E0}"),
        ("Homework hour", "\u{1F4DA}"),
        ("Transitions", "\u{1F504}"),
        ("Honestly, all of it", "\u{1F605}")
    ]

    private let temperamentOptions = [
        ("Spirited", "\u{1F525}"),
        ("Sensitive", "\u{1F338}"),
        ("Easy-going", "\u{2600}\u{FE0F}"),
        ("Strong-willed", "\u{26A1}"),
        ("Shy/cautious", "\u{1F43A}"),
        ("Social butterfly", "\u{1F98B}")
    ]

    private let challengeOptions: [(label: String, emoji: String)] = [
        ("Morning routines", "\u{2600}\u{FE0F}"),
        ("Bedtime battles", "\u{1F319}"),
        ("Big emotions", "\u{1F30A}"),
        ("Picky eating", "\u{1F966}"),
        ("Screen time", "\u{1F4F1}"),
        ("Sibling rivalry", "\u{26A1}"),
        ("Work-life balance", "\u{2696}\u{FE0F}"),
        ("Feeling alone in it", "\u{1F49B}"),
        ("School struggles", "\u{1F4DA}"),
        ("Behavior changes", "\u{1F504}")
    ]

    private let goalOptions: [(label: String, emoji: String)] = [
        ("Expert guidance", "\u{1F9E0}"),
        ("Daily strategies", "\u{1F4CB}"),
        ("Understanding my child", "\u{1F50D}"),
        ("Community support", "\u{1F91D}"),
        ("Managing my stress", "\u{1F9D8}"),
        ("Building confidence", "\u{1F4AA}")
    ]

    var body: some View {
        ZStack {
            Color.brandBackground
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
        .preferredColorScheme(.dark)
        .onAppear { withAnimation(.easeOut(duration: 0.8)) { appearAnimation = true } }
    }

    // MARK: - Progress Indicator

    private func progressDots(current: Int) -> some View {
        HStack(spacing: 6) {
            ForEach(1..<totalSteps, id: \.self) { i in
                Capsule()
                    .fill(i <= current ? Color.brandGold : Color.brandGold.opacity(0.2))
                    .frame(width: i == current ? 24 : 8, height: 4)
                    .animation(.easeInOut(duration: 0.3), value: current)
            }
        }
        .padding(.top, 12)
    }

    // MARK: - Screen 0: Welcome

    private var welcomeScreen: some View {
        VStack(spacing: 0) {
            Spacer()

            // Whimsical illustration cluster above logo
            ZStack {
                // Floating decorative elements
                Text("\u{2728}")
                    .font(.system(size: 28))
                    .offset(x: -80, y: -40)
                    .opacity(appearAnimation ? 1 : 0)
                    .offset(y: appearAnimation ? 0 : 20)

                Text("\u{1F31F}")
                    .font(.system(size: 22))
                    .offset(x: 90, y: -30)
                    .opacity(appearAnimation ? 1 : 0)
                    .offset(y: appearAnimation ? 0 : 20)

                Text("\u{1F33F}")
                    .font(.system(size: 24))
                    .offset(x: -70, y: 50)
                    .rotationEffect(.degrees(-15))
                    .opacity(appearAnimation ? 1 : 0)

                Text("\u{2764}\u{FE0F}")
                    .font(.system(size: 20))
                    .offset(x: 75, y: 55)
                    .opacity(appearAnimation ? 1 : 0)

                // Logo badge
                GeometryReader { geo in
                    MVPLogoView(size: geo.size.width * 0.50)
                        .frame(maxWidth: .infinity)
                }
                .aspectRatio(1, contentMode: .fit)
            }
            .padding(.horizontal, 40)

            Spacer().frame(height: 24)

            // Tagline with wavy underline
            VStack(spacing: 8) {
                Text("Every parent deserves\nsomeone in their corner.")
                    .font(.system(.title3, design: .serif).italic())
                    .foregroundColor(.white.opacity(0.9))
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)

                WavyLine(width: 100, color: .brandGold.opacity(0.5))
            }

            Spacer()

            // Returning user section
            if isReturningUser {
                VStack(spacing: 16) {
                    onboardingTextField(placeholder: "Your name", text: $returningUserName)
                        .padding(.horizontal, 24)

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
                    .padding(.horizontal, 24)
                }
                .transition(.opacity.combined(with: .move(edge: .bottom)))
            } else {
                VStack(spacing: 12) {
                    brandButton(label: "I'm new here") {
                        advance(to: 1)
                    }
                    .padding(.horizontal, 24)

                    Button {
                        withAnimation(.easeInOut(duration: 0.3)) { isReturningUser = true }
                    } label: {
                        Text("Welcome back")
                            .font(.body.weight(.bold))
                            .foregroundColor(.brandGold)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                            .overlay(Capsule().stroke(Color.brandGold, lineWidth: 1.5))
                    }
                    .padding(.horizontal, 24)
                }
            }

            Spacer().frame(height: 48)
        }
    }

    // MARK: - Screen 1: Name

    private var nameScreen: some View {
        VStack(alignment: .leading, spacing: 0) {
            onboardingHeader(backTo: 0, step: 1)

            // Illustration: hand-wave collage
            HStack {
                Spacer()
                ZStack {
                    Text("\u{1F44B}")
                        .font(.system(size: 56))
                    Text("\u{2728}")
                        .font(.system(size: 20))
                        .offset(x: 35, y: -25)
                    Text("\u{1F331}")
                        .font(.system(size: 18))
                        .offset(x: -30, y: 20)
                        .rotationEffect(.degrees(-20))
                }
                Spacer()
            }
            .padding(.top, 8)
            .padding(.bottom, 16)

            VStack(alignment: .leading, spacing: 8) {
                Text("What should we\ncall you?")
                    .font(.system(.title, design: .serif).weight(.bold))
                    .foregroundColor(.white)

                Text("Just a first name is perfect.")
                    .font(.system(.subheadline, design: .serif).italic())
                    .foregroundColor(.brandGray)
            }
            .padding(.horizontal, 24)

            Spacer().frame(height: 32)

            onboardingTextField(placeholder: "Your name", text: $parentName)
                .padding(.horizontal, 24)

            Spacer()

            brandButton(label: "Next", disabled: parentName.trimmed.isEmpty) {
                advance(to: 2)
            }
            .padding(.horizontal, 24)
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
                            .font(.system(.subheadline, design: .serif).weight(.medium))
                            .foregroundColor(.brandGold)
                            .padding(.horizontal, 14)
                            .padding(.vertical, 6)
                    }
                }
                .padding(.horizontal, 12)
                .padding(.top, 8)
            }

            HStack {
                Spacer()
                ZStack {
                    Text("\u{1F30D}")
                        .font(.system(size: 44))
                    Text("\u{1F4CD}")
                        .font(.system(size: 22))
                        .offset(x: 32, y: -22)
                    Text("\u{1F5E3}\u{FE0F}")
                        .font(.system(size: 20))
                        .offset(x: -36, y: -10)
                        .rotationEffect(.degrees(-10))
                    Text("\u{2728}")
                        .font(.system(size: 16))
                        .offset(x: 30, y: 22)
                }
                Spacer()
            }
            .padding(.top, 4)
            .padding(.bottom, 12)

            VStack(alignment: .leading, spacing: 8) {
                Text("A little about\nyou")
                    .font(.system(.title, design: .serif).weight(.bold))
                    .foregroundColor(.white)

                Text("All optional. Helps us tailor advice to your world.")
                    .font(.system(.subheadline, design: .serif).italic())
                    .foregroundColor(.brandGray)
            }
            .padding(.horizontal, 24)

            Spacer().frame(height: 16)

            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Zip + Country row
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Where you are")
                            .font(.system(.subheadline, design: .serif).weight(.semibold))
                            .foregroundColor(.brandGold)

                        HStack(spacing: 12) {
                            onboardingTextField(
                                placeholder: "Zip / postal",
                                text: $postalCode,
                                keyboardType: .numbersAndPunctuation
                            )

                            Menu {
                                ForEach(countryOptions, id: \.0) { code, flag in
                                    Button {
                                        country = code
                                    } label: {
                                        Text("\(flag)  \(code)")
                                    }
                                }
                            } label: {
                                HStack(spacing: 6) {
                                    Text(countryOptions.first(where: { $0.0 == country })?.1 ?? "\u{1F310}")
                                    Text(country.isEmpty ? "Country" : country)
                                        .font(.system(.body, design: .serif))
                                    Image(systemName: "chevron.down")
                                        .font(.caption)
                                }
                                .foregroundColor(.white)
                                .padding(.horizontal, 14)
                                .padding(.vertical, 14)
                                .background(Color.brandSurface)
                                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                                        .stroke(Color.brandStroke, style: StrokeStyle(lineWidth: 1, dash: [6]))
                                )
                            }
                        }
                    }

                    // Primary language
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Primary language at home")
                            .font(.system(.subheadline, design: .serif).weight(.semibold))
                            .foregroundColor(.brandGold)

                        singleSelectGrid(options: languageOptions, selection: $primaryLanguage)
                    }

                    // Parent age range
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Your age range")
                            .font(.system(.subheadline, design: .serif).weight(.semibold))
                            .foregroundColor(.brandGold)

                        singleSelectGrid(options: parentAgeOptions, selection: $parentAgeRange)
                    }

                    // Adults in household
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Adults in your household")
                            .font(.system(.subheadline, design: .serif).weight(.semibold))
                            .foregroundColor(.brandGold)

                        HStack(spacing: 16) {
                            Button {
                                if adultsInHousehold > 1 { adultsInHousehold -= 1 }
                            } label: {
                                Image(systemName: "minus.circle")
                                    .font(.system(size: 28))
                                    .foregroundColor(.brandGold)
                            }
                            Text("\(adultsInHousehold)")
                                .font(.system(.title2, design: .serif).weight(.bold))
                                .foregroundColor(.white)
                                .frame(minWidth: 32)
                            Button {
                                if adultsInHousehold < 4 { adultsInHousehold += 1 }
                            } label: {
                                Image(systemName: "plus.circle")
                                    .font(.system(size: 28))
                                    .foregroundColor(.brandGold)
                            }
                            Spacer()
                        }
                        .padding(.vertical, 4)
                    }

                    // Employment
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Work pattern")
                            .font(.system(.subheadline, design: .serif).weight(.semibold))
                            .foregroundColor(.brandGold)

                        singleSelectGrid(options: employmentOptions, selection: $employment)
                    }

                    // Pronouns
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Your pronouns")
                            .font(.system(.subheadline, design: .serif).weight(.semibold))
                            .foregroundColor(.brandGold)

                        singleSelectGrid(options: parentPronounsOptions, selection: $pronouns)
                    }

                    // Cultural background
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Cultural background (optional)")
                            .font(.system(.subheadline, design: .serif).weight(.semibold))
                            .foregroundColor(.brandGold)

                        onboardingTextField(
                            placeholder: "e.g., Mexican-American, South Asian",
                            text: $culturalBackground
                        )
                    }
                }
                .padding(.horizontal, 24)
                .padding(.bottom, 16)
            }

            Spacer()

            brandButton(label: "Next") { advance(to: 3) }
                .padding(.horizontal, 24)
                .padding(.bottom, 48)
        }
    }

    // MARK: - Screen 3: Kids

    private var kidsScreen: some View {
        VStack(alignment: .leading, spacing: 0) {
            onboardingHeader(backTo: 2, step: 3)

            // Illustration: playful kid-themed collage
            HStack {
                Spacer()
                ZStack {
                    Text("\u{1F9F8}")
                        .font(.system(size: 44))
                        .offset(x: -30)
                        .rotationEffect(.degrees(-10))
                    Text("\u{1F3A8}")
                        .font(.system(size: 36))
                        .offset(x: 30, y: -5)
                        .rotationEffect(.degrees(8))
                    Text("\u{2B50}")
                        .font(.system(size: 16))
                        .offset(x: 0, y: -30)
                    Text("\u{1F308}")
                        .font(.system(size: 22))
                        .offset(x: 55, y: -25)
                }
                Spacer()
            }
            .padding(.top, 4)
            .padding(.bottom, 12)

            VStack(alignment: .leading, spacing: 8) {
                Text("Tell us about your\nlittle ones")
                    .font(.system(.title, design: .serif).weight(.bold))
                    .foregroundColor(.white)

                Text("Names, ages, and a peek at their personality.")
                    .font(.system(.subheadline, design: .serif).italic())
                    .foregroundColor(.brandGray)
            }
            .padding(.horizontal, 24)

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
                                .font(.body.weight(.medium))
                        }
                        .foregroundColor(.brandGold)
                    }
                    .padding(.top, 4)
                }
                .padding(.horizontal, 24)
            }

            Spacer()

            brandButton(
                label: "Next",
                disabled: !kids.contains(where: { !$0.name.trimmed.isEmpty })
            ) {
                advance(to: 4)
            }
            .padding(.horizontal, 24)
            .padding(.bottom, 48)
        }
    }

    // MARK: - Screen 4: Your World

    private var worldScreen: some View {
        VStack(alignment: .leading, spacing: 0) {
            onboardingHeader(backTo: 3, step: 4)

            // Illustration: home & family collage
            HStack {
                Spacer()
                ZStack {
                    Text("\u{1F3E1}")
                        .font(.system(size: 48))
                    Text("\u{1F343}")
                        .font(.system(size: 22))
                        .offset(x: -40, y: -15)
                        .rotationEffect(.degrees(-30))
                    Text("\u{2728}")
                        .font(.system(size: 18))
                        .offset(x: 40, y: -20)
                    Text("\u{1F49B}")
                        .font(.system(size: 16))
                        .offset(x: 35, y: 20)
                }
                Spacer()
            }
            .padding(.top, 4)
            .padding(.bottom, 12)

            VStack(alignment: .leading, spacing: 8) {
                Text("Paint us a picture\nof your world")
                    .font(.system(.title, design: .serif).weight(.bold))
                    .foregroundColor(.white)

                Text("No right answers. Just your reality.")
                    .font(.system(.subheadline, design: .serif).italic())
                    .foregroundColor(.brandGray)
            }
            .padding(.horizontal, 24)

            Spacer().frame(height: 24)

            ScrollView {
                VStack(alignment: .leading, spacing: 28) {
                    // Household
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Your household")
                            .font(.system(.subheadline, design: .serif).weight(.semibold))
                            .foregroundColor(.brandGold)

                        singleSelectGrid(options: householdOptions, selection: $household)
                    }

                    // Support system
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Your support crew")
                            .font(.system(.subheadline, design: .serif).weight(.semibold))
                            .foregroundColor(.brandGold)

                        singleSelectGrid(options: supportOptions, selection: $supportSystem)
                    }
                }
                .padding(.horizontal, 24)
            }

            Spacer()

            brandButton(label: "Next") { advance(to: 5) }
                .padding(.horizontal, 24)
                .padding(.bottom, 48)
        }
    }

    // MARK: - Screen 5: Energy & Dread

    private var energyScreen: some View {
        VStack(alignment: .leading, spacing: 0) {
            onboardingHeader(backTo: 4, step: 5)

            // Illustration: energy/time collage
            HStack {
                Spacer()
                ZStack {
                    Text("\u{23F0}")
                        .font(.system(size: 44))
                        .rotationEffect(.degrees(-8))
                    Text("\u{26A1}")
                        .font(.system(size: 24))
                        .offset(x: 35, y: -20)
                    Text("\u{1F319}")
                        .font(.system(size: 22))
                        .offset(x: -35, y: -18)
                    Text("\u{2615}")
                        .font(.system(size: 20))
                        .offset(x: -30, y: 22)
                        .rotationEffect(.degrees(10))
                }
                Spacer()
            }
            .padding(.top, 4)
            .padding(.bottom, 12)

            VStack(alignment: .leading, spacing: 8) {
                Text("When do you feel\nmost yourself?")
                    .font(.system(.title, design: .serif).weight(.bold))
                    .foregroundColor(.white)

                Text("And when does it all feel like... a lot?")
                    .font(.system(.subheadline, design: .serif).italic())
                    .foregroundColor(.brandGray)
            }
            .padding(.horizontal, 24)

            Spacer().frame(height: 24)

            ScrollView {
                VStack(alignment: .leading, spacing: 28) {
                    // Energy pattern
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Your energy sweet spot")
                            .font(.system(.subheadline, design: .serif).weight(.semibold))
                            .foregroundColor(.brandGold)

                        singleSelectGrid(options: energyOptions, selection: $energyPattern)
                    }

                    // Dreaded moment
                    VStack(alignment: .leading, spacing: 12) {
                        Text("The part of the day you dread")
                            .font(.system(.subheadline, design: .serif).weight(.semibold))
                            .foregroundColor(.brandGold)

                        singleSelectGrid(options: dreadedOptions, selection: $dreadedMoment)
                    }
                }
                .padding(.horizontal, 24)
            }

            Spacer()

            brandButton(label: "Next") { advance(to: 6) }
                .padding(.horizontal, 24)
                .padding(.bottom, 48)
        }
    }

    // MARK: - Screen 6: Challenges

    private var challengesScreen: some View {
        VStack(alignment: .leading, spacing: 0) {
            onboardingHeader(backTo: 5, step: 6)

            // Illustration
            HStack {
                Spacer()
                ZStack {
                    Text("\u{1F30A}")
                        .font(.system(size: 44))
                    Text("\u{1F9E1}")
                        .font(.system(size: 22))
                        .offset(x: 35, y: -22)
                    Text("\u{1F343}")
                        .font(.system(size: 20))
                        .offset(x: -38, y: -10)
                        .rotationEffect(.degrees(15))
                }
                Spacer()
            }
            .padding(.top, 4)
            .padding(.bottom, 12)

            VStack(alignment: .leading, spacing: 8) {
                Text("What feels hardest\nright now?")
                    .font(.system(.title, design: .serif).weight(.bold))
                    .foregroundColor(.white)

                Text("Pick as many as you want. No judgment here.")
                    .font(.system(.subheadline, design: .serif).italic())
                    .foregroundColor(.brandGray)
            }
            .padding(.horizontal, 24)

            Spacer().frame(height: 24)

            ScrollView {
                chipGrid(options: challengeOptions, selection: $challenges)
                    .padding(.horizontal, 24)
            }

            Spacer()

            brandButton(label: "Next") { advance(to: 7) }
                .padding(.horizontal, 24)
                .padding(.bottom, 48)
        }
    }

    // MARK: - Screen 7: Goals

    private var goalsScreen: some View {
        VStack(alignment: .leading, spacing: 0) {
            onboardingHeader(backTo: 6, step: 7)

            // Illustration
            HStack {
                Spacer()
                ZStack {
                    Text("\u{1F3AF}")
                        .font(.system(size: 44))
                    Text("\u{2728}")
                        .font(.system(size: 20))
                        .offset(x: -35, y: -18)
                    Text("\u{1F31F}")
                        .font(.system(size: 18))
                        .offset(x: 38, y: -15)
                    Text("\u{1F33F}")
                        .font(.system(size: 18))
                        .offset(x: 30, y: 22)
                        .rotationEffect(.degrees(20))
                }
                Spacer()
            }
            .padding(.top, 4)
            .padding(.bottom, 12)

            VStack(alignment: .leading, spacing: 8) {
                Text("What are you\nhoping for?")
                    .font(.system(.title, design: .serif).weight(.bold))
                    .foregroundColor(.white)

                Text("This helps us point you in the right direction.")
                    .font(.system(.subheadline, design: .serif).italic())
                    .foregroundColor(.brandGray)
            }
            .padding(.horizontal, 24)

            Spacer().frame(height: 24)

            ScrollView {
                chipGrid(options: goalOptions, selection: $goals)
                    .padding(.horizontal, 24)
            }

            Spacer()

            brandButton(label: "Next") { advance(to: 8) }
                .padding(.horizontal, 24)
                .padding(.bottom, 48)
        }
    }

    // MARK: - Screen 8: Preview / Launch

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
            HStack {
                Spacer()
                ZStack {
                    Text("\u{1F389}")
                        .font(.system(size: 44))
                    Text("\u{2B50}")
                        .font(.system(size: 20))
                        .offset(x: -35, y: -20)
                    Text("\u{1F38A}")
                        .font(.system(size: 26))
                        .offset(x: 38, y: -12)
                    Text("\u{2728}")
                        .font(.system(size: 18))
                        .offset(x: -25, y: 22)
                    Text("\u{1F31F}")
                        .font(.system(size: 14))
                        .offset(x: 42, y: 22)
                }
                Spacer()
            }
            .padding(.top, 4)
            .padding(.bottom, 12)

            VStack(alignment: .leading, spacing: 8) {
                Text("And here's a peek\nat the goodness")
                    .font(.system(.title, design: .serif).weight(.bold))
                    .foregroundColor(.white)

                WavyLine(width: 140, color: .brandGold.opacity(0.4))
            }
            .padding(.horizontal, 24)

            Spacer().frame(height: 32)

            VStack(alignment: .leading, spacing: 20) {
                ForEach(features, id: \.1) { emoji, text in
                    HStack(spacing: 14) {
                        Text(emoji)
                            .font(.system(size: 24))

                        Text(text)
                            .font(.system(.body, design: .serif).weight(.medium))
                            .foregroundColor(.white)
                    }
                }
            }
            .padding(.horizontal, 24)

            Spacer()

            let displayName = parentName.trimmed
            brandButton(label: "Let's go, \(displayName)!") {
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
                    household: household,
                    supportSystem: supportSystem,
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
            .padding(.horizontal, 24)
            .padding(.bottom, 48)
        }
    }

    // MARK: - Reusable Components

    private func advance(to target: Int) {
        withAnimation(.easeInOut(duration: 0.3)) { step = target }
    }

    private func onboardingHeader(backTo target: Int, step current: Int) -> some View {
        VStack(spacing: 0) {
            HStack {
                Button { advance(to: target) } label: {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(.white)
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
        TextField("", text: text, prompt: Text(placeholder).foregroundColor(.brandGray))
            .font(.system(.body, design: .serif))
            .foregroundColor(.white)
            .keyboardType(keyboardType)
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
            .background(Color.brandSurface)
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(Color.brandStroke, style: StrokeStyle(lineWidth: 1, dash: [6]))
            )
            .frame(width: width)
    }

    private func brandButton(label: String, disabled: Bool = false, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(label)
                .font(.system(.body, design: .serif).weight(.bold))
                .foregroundColor(.brandBlack)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(Color.brandGold)
                .clipShape(Capsule())
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
                            .foregroundColor(.brandGray)
                    }
                }
            }

            // Temperament picker (inline)
            if !kids[index].name.trimmed.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("What's \(kids[index].name.trimmed.isEmpty ? "their" : kids[index].name.trimmed)'s vibe?")
                        .font(.system(.caption, design: .serif).italic())
                        .foregroundColor(.brandGray)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(temperamentOptions, id: \.0) { label, emoji in
                                let isSelected = kids[index].temperament == label
                                Button {
                                    withAnimation(.easeInOut(duration: 0.15)) {
                                        kids[index].temperament = isSelected ? "" : label
                                    }
                                } label: {
                                    HStack(spacing: 4) {
                                        Text(emoji).font(.system(size: 14))
                                        Text(label)
                                            .font(.system(.caption, design: .serif).weight(.medium))
                                    }
                                    .foregroundColor(isSelected ? .brandBlack : .white)
                                    .padding(.horizontal, 12)
                                    .padding(.vertical, 8)
                                    .background(isSelected ? Color.brandGold : Color.brandSurface)
                                    .clipShape(Capsule())
                                    .overlay(
                                        Capsule().stroke(isSelected ? Color.clear : Color.brandStroke, lineWidth: 1)
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
                            ForEach(kidPronounsOptions, id: \.0) { label, emoji in
                                let isSelected = kids[index].pronouns == label
                                Button {
                                    withAnimation(.easeInOut(duration: 0.15)) {
                                        kids[index].pronouns = isSelected ? "" : label
                                    }
                                } label: {
                                    HStack(spacing: 4) {
                                        Text(emoji).font(.system(size: 12))
                                        Text(label)
                                            .font(.system(.caption2, design: .serif).weight(.medium))
                                    }
                                    .foregroundColor(isSelected ? .brandBlack : .white)
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 6)
                                    .background(isSelected ? Color.brandGold : Color.brandSurface)
                                    .clipShape(Capsule())
                                    .overlay(
                                        Capsule().stroke(isSelected ? Color.clear : Color.brandStroke, lineWidth: 1)
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
                        .foregroundColor(.white)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(Color.brandSurface)
                        .clipShape(Capsule())
                        .overlay(
                            Capsule().stroke(Color.brandStroke, lineWidth: 1)
                        )
                    }
                }
            }
        }
        .padding(16)
        .background(Color.brandSurface.opacity(0.5))
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .stroke(Color.brandStroke, lineWidth: 1)
        )
    }

    private func singleSelectGrid(options: [(String, String)], selection: Binding<String>) -> some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
            ForEach(options, id: \.0) { label, emoji in
                let isSelected = selection.wrappedValue == label
                Button {
                    withAnimation(.easeInOut(duration: 0.15)) {
                        selection.wrappedValue = isSelected ? "" : label
                    }
                } label: {
                    HStack(spacing: 6) {
                        Text(emoji).font(.system(size: 16))
                        Text(label)
                            .font(.system(.subheadline, design: .serif).weight(.medium))
                            .lineLimit(1)
                            .minimumScaleFactor(0.8)
                    }
                    .foregroundColor(isSelected ? .brandBlack : .white)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 12)
                    .frame(maxWidth: .infinity)
                    .background(isSelected ? Color.brandGold : Color.brandSurface)
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .stroke(isSelected ? Color.clear : Color.brandStroke, lineWidth: 1)
                    )
                }
            }
        }
    }

    private func chipGrid(options: [(label: String, emoji: String)], selection: Binding<Set<String>>) -> some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
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
                    HStack(spacing: 6) {
                        Text(option.emoji).font(.system(size: 16))
                        Text(option.label)
                            .font(.system(.subheadline, design: .serif).weight(.medium))
                            .lineLimit(1)
                            .minimumScaleFactor(0.8)
                    }
                    .foregroundColor(isSelected ? .brandBlack : .white)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 12)
                    .frame(maxWidth: .infinity)
                    .background(isSelected ? Color.brandGold : Color.brandSurface)
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .stroke(isSelected ? Color.clear : Color.brandStroke, lineWidth: 1)
                    )
                }
            }
        }
    }
}

// MARK: - String Helper

private extension String {
    var trimmed: String { trimmingCharacters(in: .whitespacesAndNewlines) }
}
