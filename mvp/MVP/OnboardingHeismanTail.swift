import SwiftUI

// MARK: - Heisman step 05 + interstitials: parent tasks, getting ready,
// coach demonstration, account wall

// MARK: Parent tasks ("Onboarding - 6", step 05)

struct HeismanParentTasksView: View {
    @Binding var draft: OnboardingDraft
    let onBack: () -> Void
    let onContinue: () -> Void
    /// The ONLY skippable step (D2). Skip commits no task data.
    let onSkip: () -> Void

    @StateObject private var dictation = DictationController()

    /// The frame's eight own-to-do options, reading order.
    private static let options = [
        "A gift to buy", "Grocery or dinner run",
        "An errand to fit in", "House work",
        "Medical appointment", "Date night",
        "Exercise or gym", "Social commitment",
    ]

    private var hasAnswer: Bool {
        !draft.parentTasks.isEmpty
            || !draft.parentTasksNote.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var body: some View {
        HeismanScreen(step: .parentTasks, onBack: onBack) {
            Spacer(minLength: .hearth700)

            VStack(alignment: .leading, spacing: 15) {
                heismanMonoEyebrow("From your MVP Coach")
                Text("What about you — what's your to-do this week?")
                    .font(.custom(HearthFontFamily.sans, size: 17, relativeTo: .body).weight(.bold))
                    .foregroundColor(.inkDisplay)
                    .lineSpacing(.hearthLineBodyLG)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }

            VStack(spacing: .hearth300) {
                ForEach(0..<4, id: \.self) { row in
                    HStack(spacing: .hearth300) {
                        taskCard(Self.options[row * 2])
                        taskCard(Self.options[row * 2 + 1])
                    }
                }

                HeismanTextCard(
                    placeholder: "Add a note or share something else...",
                    text: $draft.parentTasksNote,
                    dictation: dictation,
                    minEditorHeight: 80
                )
            }
        } footer: {
            // The frame's CTA reads "add"; spec: Continue is enabled with
            // zero selections (skip and proceed lead to the same place), so
            // the pill stays tappable — it just wears the quiet gray until
            // the step has an answer, exactly as drawn.
            Button {
                hideKeyboard()
                dictation.stop()
                onContinue()
            } label: {
                Text("add")
            }
            .buttonStyle(HeismanCTAStyle(enabled: hasAnswer))

            Button {
                dictation.stop()
                onSkip()
            } label: {
                Text("Skip")
                    .font(.hearthBodySM)
                    .underline()
                    .foregroundColor(.accentDefault)
            }
            .accessibilityLabel("Skip this step")
        }
        .onDisappear { dictation.stop() }
        .trackScreen("onboarding_parent_tasks")
    }

    /// Task card, measured off the frame's DRAWN selected state: unselected
    /// is cream-50 + 1px `border/strong` + Inter 13 in `ink/placeholder`;
    /// selected is `cerulean-100` (`accentTint`) + 2px accent border + Inter
    /// BOLD 13 in the accent. Multi-select (D1, acceptance #5).
    private func taskCard(_ label: String) -> some View {
        let selected = draft.parentTasks.contains(label)
        return Button {
            withAnimation(.hearth(.hearthFast, reduceMotion: false)) {
                if selected {
                    draft.parentTasks.removeAll { $0 == label }
                } else {
                    draft.parentTasks.append(label)
                }
            }
        } label: {
            Text(label)
                .font(selected ? .hearthBodySMBold : .hearthBodySM)
                .foregroundColor(selected ? .accentDefault : .inkMuted)
                .multilineTextAlignment(.leading)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.hearth300)
                .frame(maxWidth: .infinity, alignment: .leading)
                .frame(height: 86)
                .background(selected ? Color.accentTint : Color.bgCoachBanner)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                        .stroke(selected ? Color.accentDefault : Color.borderStrong, lineWidth: selected ? 2 : 1)
                )
        }
        .accessibilityAddTraits(selected ? [.isSelected] : [])
    }
}

// MARK: Getting ready ("Onboarding - creating account" interstitial)

/// The theatrical beat between the questionnaire and the coach
/// demonstration. ENTIRELY client-side (no server, no seed — the seed fires
/// after the account wall): a Fraunces percent counts up while four
/// checklist beats fill in sequence, per the `creating account` frame. The
/// beat copy is the frame's own.
struct HeismanGettingReadyView: View {
    let parentName: String
    let onDone: () -> Void

    @State private var percent = 0
    @State private var beatProgress: [Double] = [0, 0, 0, 0]
    @State private var started = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private static let beats = [
        "Getting to know your family",
        "Bringing your coach up to speed",
        "Sketching your first plan",
        "Securing your family's space",
    ]
    /// Wall-clock for the whole performance. Long enough to feel like work,
    /// short enough to never annoy; reduce-motion collapses it.
    private static let duration: TimeInterval = 4.4

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            // The ring: a soft cream-50 circle behind an oversized Fraunces
            // numeral (frame: 144pt digits + 78pt "%", scaled to the device
            // column). `photo/royal` in the frame is #1B7498 — the accent.
            ZStack {
                Circle()
                    .stroke(Color.bgCoachBanner, lineWidth: 14)
                    .frame(width: 253, height: 253)
                    .shadow(color: Color.inkPrimary.opacity(0.06), radius: 20, y: 8)
                HStack(alignment: .lastTextBaseline, spacing: 2) {
                    Text("\(percent)")
                        .font(.custom(HearthFontFamily.displaySerif, fixedSize: 118).weight(.bold))
                        .tracking(-4.7)
                    Text("%")
                        .font(.custom(HearthFontFamily.displaySerif, fixedSize: 64).weight(.bold))
                        .tracking(-3.2)
                }
                .foregroundColor(.inkDisplay)
                .monospacedDigit()
            }
            .accessibilityElement(children: .ignore)
            .accessibilityLabel("Getting ready, \(percent) percent")

            Text("Getting everything ready for you, \(parentName).")
                .font(.hearthDisplaySM)
                .tracking(-0.38)
                .foregroundColor(.inkDisplay)
                .multilineTextAlignment(.center)
                .lineSpacing(2)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.top, HeismanLayout.gutter)
                .padding(.horizontal, HeismanLayout.gutter)

            VStack(alignment: .leading, spacing: 36) {
                ForEach(Self.beats.indices, id: \.self) { index in
                    beatRow(Self.beats[index], progress: beatProgress[index])
                }
            }
            .padding(.horizontal, 42)
            .padding(.top, 56)

            Spacer()
        }
        .frame(maxWidth: .infinity)
        .background(Color.bgSober.ignoresSafeArea())
        .task { await run() }
        .trackScreen("onboarding_getting_ready")
    }

    /// One checklist beat: Inter 17 label, a 6pt bar (track = the design's
    /// `ink-500` #4A4741 at 20% — `bgButtonFunnel` is that exact primitive,
    /// used here AS a fill; accent fill grows with progress), and the 34pt
    /// accent check circle once the beat completes.
    private func beatRow(_ label: String, progress: Double) -> some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            HStack {
                Text(label)
                    .font(.hearthBodyLG)
                    .foregroundColor(.inkDisplay)
                Spacer(minLength: .hearth300)
                ZStack {
                    Circle().fill(Color.accentDefault)
                    Image(systemName: "checkmark")
                        .font(.system(size: 15, weight: .bold))
                        .foregroundColor(.inkOnPhotoLight)
                }
                .frame(width: 34, height: 34)
                .opacity(progress >= 1 ? 1 : 0)
                .animation(.hearth(.hearthBase, reduceMotion: reduceMotion), value: progress >= 1)
            }
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Rectangle().fill(Color.bgButtonFunnel.opacity(0.2))
                    Rectangle()
                        .fill(Color.accentDefault)
                        .frame(width: geo.size.width * progress)
                }
            }
            .frame(height: 6)
        }
    }

    private func run() async {
        guard !started else { return }
        started = true
        if reduceMotion {
            percent = 100
            beatProgress = [1, 1, 1, 1]
            try? await Task.sleep(for: .seconds(0.8))
            onDone()
            return
        }
        let steps = 100
        let tick = Self.duration / Double(steps)
        for i in 1...steps {
            try? await Task.sleep(for: .seconds(tick))
            percent = i
            // Each beat owns a quarter of the run and fills within it.
            let position = Double(i) / Double(steps) * 4.0
            for beat in 0..<4 {
                beatProgress[beat] = min(1, max(0, position - Double(beat)))
            }
        }
        try? await Task.sleep(for: .seconds(0.5))
        onDone()
    }
}

// MARK: Coach demonstration ("Onboarding - 7")

/// The coach performs before the account wall. The dialogue skeleton is the
/// frame's LOCKED copy (the sprint spec points at DESIGN.md for it; the
/// frame text is the artifact that actually exists — flagged in the
/// appendix drift log). It is templated with the draft's real names and
/// extraction exactly where the frame shows data, and falls back to the
/// frame's sample sentences when extraction was skipped/failed.
struct HeismanCoachDemoView: View {
    @Binding var draft: OnboardingDraft
    let onBack: () -> Void
    let onContinue: () -> Void

    @State private var remindMe = true

    private var firstName: String {
        let trimmed = draft.parentName.trimmingCharacters(in: .whitespaces)
        return trimmed.isEmpty ? "there" : trimmed
    }

    /// The demonstration lines. Frame skeleton, real data where available.
    private var lines: [String] {
        var result = ["Nice to meet you \(firstName)!"]
        let real = draft.extractedActivities
        if real.isEmpty {
            // Sample fallback — the frame's own sentences, verbatim.
            result.append("You need to be at the Northgate Aquatic Center with Lily, ready to go by 4:15 on Tuesday.")
            result.append("Benjamin has soccer at Cedar Field at 9am Saturday — bring snacks and warm clothes, it'll be chilly.")
        } else {
            for (index, activity) in real.prefix(2).enumerated() {
                result.append(Self.activityLine(activity, first: index == 0))
            }
        }
        if let task = draft.parentTasks.first {
            result.append("That leaves you time this week for \(task.lowercased()).")
        } else {
            result.append("That leaves you Saturday afternoon to catch your breath.")
        }
        return result
    }

    /// One activity sentence in the frame's two shapes: the first is the
    /// "You need to be at…" form, the second the "{kid} has {what}…" form.
    private static func activityLine(_ a: OnboardingDraft.ExtractedActivity, first: Bool) -> String {
        let who = a.who.isEmpty ? "your kid" : a.who
        let what = a.what.isEmpty ? "the activity" : a.what
        var line: String
        if first {
            line = a.where.isEmpty
                ? "\(who) has \(what.lowercased()) coming up"
                : "You need to be at \(a.where) with \(who)"
            if !a.when.isEmpty { line += ", ready to go \(a.when)" }
            line += "."
        } else {
            line = "\(who) has \(what.lowercased())"
            if !a.where.isEmpty { line += " at \(a.where)" }
            if !a.when.isEmpty { line += " \(a.when)" }
            line += "."
        }
        if !a.notes.isEmpty { line += " \(a.notes.hasSuffix(".") ? a.notes : a.notes + ".")" }
        return line
    }

    private var reminderLabel: String {
        if let task = draft.parentTasks.first {
            return "Remind me Friday about \(task.lowercased())"
        }
        return "Remind me Friday about the gift"
    }

    var body: some View {
        VStack(spacing: 0) {
            ScrollView {
                VStack(alignment: .leading, spacing: 17) {
                    // 37pt cream-50 back circle with the accent chevron —
                    // this screen's own header (no rail; acceptance #9).
                    Button(action: onBack) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundColor(.accentOnCanvas)
                            .frame(width: 37, height: 37)
                            .background(Circle().fill(Color.bgCoachBanner))
                    }
                    .accessibilityLabel("Back")

                    // `ink/muted` in the design file is #4A4741 here; the
                    // app's nearest INK token is `inkSecondary` (#2D2D2D) —
                    // hex drift flagged in the report.
                    heismanMonoEyebrow("your coach · just now", ink: .inkSecondary)

                    // Fraunces SemiBold 28, line-height 1.5, tracking −0.29:
                    // `hearthDisplayMD` is the 28/semibold token; 1.5 line
                    // height = +14 line spacing at this size.
                    ForEach(lines.indices, id: \.self) { index in
                        Text(lines[index])
                            .font(.hearthDisplayMD)
                            .tracking(-0.29)
                            .foregroundColor(.inkSecondary)
                            .lineSpacing(14)
                            .fixedSize(horizontal: false, vertical: true)
                    }

                    heismanMonoEyebrow("Time saved: 20 minutes", ink: .inkSecondary)
                }
                .padding(.horizontal, HeismanLayout.gutter + 15)
                .padding(.top, .hearth600)
                .padding(.bottom, .hearth700)
            }
        }
        .background(Color.bgSober.ignoresSafeArea())
        .safeAreaInset(edge: .bottom) {
            VStack(spacing: .hearth600) {
                HeismanCTA(label: "next", action: onContinue)

                // The frame's checked reminder row. Client-side only this
                // sprint — the coach picks the intent up from the seeded
                // tasks; the checkbox is the parent's ask, not a scheduled
                // notification (no push plumbing in this flow).
                Button {
                    remindMe.toggle()
                } label: {
                    HStack(spacing: .hearth300) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 4, style: .continuous)
                                .fill(remindMe ? Color.accentDefault : Color.bgCoachBanner)
                            if remindMe {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 9, weight: .bold))
                                    .foregroundColor(.inkOnPhotoLight)
                            } else {
                                RoundedRectangle(cornerRadius: 4, style: .continuous)
                                    .stroke(Color.accentDefault, lineWidth: 1)
                            }
                        }
                        .frame(width: 14, height: 14)
                        Text(reminderLabel)
                            .font(.hearthBodySM)
                            .underline()
                            .foregroundColor(.accentDefault)
                    }
                }
                .accessibilityAddTraits(remindMe ? [.isSelected] : [])
            }
            .padding(.horizontal, HeismanLayout.gutter)
            .padding(.top, .hearth300)
            .padding(.bottom, .hearth400)
            .background(Color.bgSober)
        }
        .trackScreen("onboarding_coach_demo")
    }
}

// MARK: Account wall ("Onboarding - 8")

/// The wall, AFTER the demonstration (the sprint's whole thesis). Auth
/// mechanics stay in `SignInView` (Apple nonce, the Google
/// ASWebAuthenticationSession flow, the legacy-account claim, the blocking
/// legal consent) — restyled to this frame; this wrapper draws the copy
/// above it and handles the already-signed-in resume.
struct HeismanAccountWallView: View {
    @Binding var draft: OnboardingDraft
    /// False only for the DEBUG `UITEST_SKIP_SIGNIN` harness — the wall
    /// auto-advances without real OAuth so headless driving can cross it.
    let signInRequired: Bool
    let accountID: String
    let onBack: () -> Void
    let onSignedIn: (AuthService.SignInOutcome) -> Void
    /// Advance past the wall (sign-in resolved, or legitimately bypassed).
    let onAdvance: () -> Void

    private var subtitle: String {
        let kids = draft.kids.filter { !$0.name.trimmingCharacters(in: .whitespaces).isEmpty }
        let schedules: String
        switch kids.count {
        case 0:  schedules = "your family's schedule"
        case 1:  schedules = "\(kids[0].name)'s schedule"
        case 2:  schedules = "both kids' schedules"
        default: schedules = "your kids' schedules"
        }
        return "I'm holding \(schedules) and your Saturday. Sign in and it all stays with you."
    }

    var body: some View {
        VStack(spacing: 0) {
            ScrollView {
                VStack(alignment: .leading, spacing: HeismanLayout.gutter) {
                    Button(action: onBack) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundColor(.accentOnCanvas)
                            .frame(width: 37, height: 37)
                            .background(Circle().fill(Color.bgCoachBanner))
                    }
                    .accessibilityLabel("Back")

                    Spacer(minLength: .hearth1000)

                    VStack(alignment: .leading, spacing: 17) {
                        heismanMonoEyebrow("your coach · just now")
                        VStack(alignment: .leading, spacing: 9) {
                            Text("Save this so I don't forget it.")
                                .font(.hearthDisplayMD)
                                .foregroundColor(.inkPrimary)
                                .lineSpacing(14)
                                .fixedSize(horizontal: false, vertical: true)
                            heismanSubtitle(subtitle)
                        }
                    }

                    // Apple/Google ONLY this sprint (Appendix A1: the email
                    // wall's states pass is deferred, so the frame's "Use
                    // email instead" link is deliberately omitted).
                    SignInView(onSignedIn: onSignedIn)
                }
                .padding(.horizontal, HeismanLayout.gutter)
                .padding(.top, .hearth600)
                .padding(.bottom, .hearth700)
            }
        }
        .background(Color.bgSober.ignoresSafeArea())
        .task {
            // Two legitimate ways to already be past auth here: the DEBUG
            // UITEST bypass, and a resumed draft whose parent signed in on a
            // previous session (v4 signed in at the START of the funnel).
            let alreadySignedIn = !accountID.isEmpty && AuthService.shared.credential(for: accountID) != nil
            if !signInRequired || alreadySignedIn {
                onAdvance()
            }
        }
        .trackScreen("onboarding_account_wall")
    }
}
