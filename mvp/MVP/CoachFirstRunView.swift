import SwiftUI

/// The Coach TAB's own empty state (frame `coach-000`).
///
/// Deliberately NOT the same thing as `HomeView`'s inline `coachSection`
/// first-run copy — that is a banner on the dashboard; this is what the Coach
/// tab shows when the parent has no messages yet.
///
/// The three starter prompts SEND (they don't prefill): tapping one is the
/// parent's first message. A prefill would leave them staring at a filled box
/// wondering whether to edit it.
struct CoachFirstRunView: View {
    let userID: String
    let baseURL: URL?
    /// Sends the tapped prompt as the first message.
    let onSend: (String) -> Void

    /// The kid name woven into the third prompt. Loaded from the real profile —
    /// never hardcoded — so a family with no "Lily" doesn't get a stranger's
    /// child's name. Nil until the profile lands (or if there are no kids), in
    /// which case the prompt falls back to a name-free phrasing.
    @State private var kidName: String?

    private static let dinnerPrompt = "Easy dinner ideas for tonight"
    private static let bedtimePrompt = "Bedtime is a fight right now"

    /// The third prompt, personalized. The `…` matches the frame; the parent
    /// finishes the thought in the chat.
    private var kidPrompt: String {
        if let kidName, !kidName.isEmpty {
            return "How do I talk to \(kidName) about…"
        }
        return "How do I talk to my kid about…"
    }

    /// Subhead. Names the family's kids when we know them, matching the frame's
    /// "your coach knows Ben and Lily and remembers what you've already tried."
    private var subhead: String {
        let opener = "Sleep, tantrums, dinner, the days that feel like too much."
        if let kidName, !kidName.isEmpty {
            return "\(opener) Your coach knows \(kidName) and remembers what you've already tried."
        }
        return "\(opener) Your coach remembers what you've already tried."
    }

    var body: some View {
        VStack(spacing: .hearth500) {
            HearthMark(size: 80, tint: .accentOnCanvas)

            Text("Meet your coach")
                .font(.hearthDisplaySM)          // Fraunces w700 38/40
                .tracking(-0.38)
                // inkDisplay is the frame's headline ink (ink-800).
                .foregroundColor(.inkDisplay)
                .multilineTextAlignment(.center)

            Text(subhead)
                .font(.hearthBodyMD)             // Inter w400 15/22
                .foregroundColor(.inkDisplay)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)

            starterPrompts
        }
        .padding(.horizontal, .hearth600)
        .frame(maxWidth: .infinity)
        .task { await loadKidName() }
    }

    /// The three tappable prompts. Extracted rather than inlined: the button
    /// stack inside the surrounding VStack is exactly the shape that trips
    /// "unable to type-check this expression in reasonable time".
    @ViewBuilder
    private var starterPrompts: some View {
        VStack(spacing: .hearth300) {
            promptButton(Self.dinnerPrompt)
            promptButton(Self.bedtimePrompt)
            promptButton(kidPrompt)
        }
        .padding(.top, .hearth300)
    }

    @ViewBuilder
    private func promptButton(_ text: String) -> some View {
        Button {
            onSend(text)
        } label: {
            Text(text)
                .font(.hearthSectionHeader)      // Inter w800 16/22
                .foregroundColor(.inkOnPhotoLight)
                .multilineTextAlignment(.center)
                .padding(.vertical, .hearth400)
                .padding(.horizontal, .hearth500)
                .frame(maxWidth: .infinity)
                .background(
                    RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                        .fill(Color.accentDefault)
                )
        }
        .buttonStyle(.plain)
        .accessibilityHint("Sends this as your first message")
    }

    /// First kid name from the family profile. Best-effort: a failed fetch just
    /// leaves the name-free phrasing rather than blocking the empty state.
    private func loadKidName() async {
        guard kidName == nil, let baseURL, !userID.isEmpty else { return }
        guard let profile = try? await ProfileService.getProfile(
            baseURL: baseURL, userID: userID
        ) else { return }
        // Prefer the child's own `name` field; fall back to the profile key,
        // which is the kid's name for every family seeded through onboarding.
        let children = profile.children ?? [:]
        let firstKey = children.keys.sorted().first
        kidName = children[firstKey ?? ""]?.name ?? firstKey
    }
}
