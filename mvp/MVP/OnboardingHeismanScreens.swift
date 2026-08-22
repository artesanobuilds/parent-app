import SwiftUI

// MARK: - Heisman screens 1–3: cold open, children, topic
//
// Each screen is a standalone struct over `Binding<OnboardingDraft>` plus
// navigation closures — `OnboardingView` stays the flow/migration core and
// these stay pure presentation + local input state. Measured specs are cited
// per element; the hex→token map lives in OnboardingHeismanChrome.swift.

// MARK: Cold open ("Onboarding - 1", step 01)

struct HeismanColdOpenView: View {
    @Binding var draft: OnboardingDraft
    let onBack: () -> Void
    let onContinue: () -> Void

    var body: some View {
        HeismanScreen(step: .coldOpen, onBack: onBack) {
            Spacer(minLength: .hearth900)

            // The small tumbler mark, 51×97 (frame node 29:2299) — the same
            // multi-color vector as the splash, exported separately at the
            // frame's own crop.
            Image("OnboardingHeismanMarkSM")
                .resizable()
                .scaledToFit()
                .frame(width: 51, height: 97)
                .accessibilityHidden(true)

            VStack(alignment: .leading, spacing: 15) {
                heismanTitle("Busy parents are experts at spinning plates. Hand one over.")
                heismanSubtitle("Share your first name and some logistics with your MVP Coach.")
            }

            // Name — gap 26 between the copy block and the field blocks in
            // the frame; the scaffold's default 16 + the field block's own
            // structure reads the same rhythm on the shorter device canvas.
            VStack(alignment: .leading, spacing: 0) {
                HeismanField(
                    placeholder: "Your name",
                    text: $draft.parentName,
                    textContentType: .givenName
                )
                Text("Helps the coach know who’s talking")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkPrimary)
                    .frame(height: 40, alignment: .center)
            }

            // Location / zip. Stored on `draft.postalCode` (the pinned seed
            // key). Deliberately optional: the spec gates Continue on "the
            // step has an answer" and the name is the answer this screen is
            // titled around; location quietly improves discovery.
            VStack(alignment: .leading, spacing: 0) {
                HeismanField(
                    placeholder: "Location / Zip Code",
                    text: $draft.postalCode,
                    keyboard: .numbersAndPunctuation,
                    textContentType: .postalCode
                )
                Text("Helps the coach find activities near you")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkPrimary)
                    .frame(height: 40, alignment: .center)
            }
        } footer: {
            HeismanCTA(
                label: "Continue",
                enabled: !draft.parentName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
                action: onContinue
            )
        }
        .trackScreen("onboarding_cold_open")
    }
}

// MARK: Children ("Onboarding - 2", step 02)

struct HeismanChildrenView: View {
    @Binding var draft: OnboardingDraft
    let onBack: () -> Void
    let onContinue: () -> Void

    /// At least one child with BOTH a name and an age (spec: "Continue is
    /// disabled until at least one child has both a name and an age").
    private var hasCompleteChild: Bool {
        draft.kids.contains {
            !$0.name.trimmingCharacters(in: .whitespaces).isEmpty
                && !$0.age.trimmingCharacters(in: .whitespaces).isEmpty
        }
    }

    var body: some View {
        HeismanScreen(step: .children, onBack: onBack) {
            Spacer(minLength: .hearth1000)

            VStack(alignment: .leading, spacing: 15) {
                heismanTitle("Who’s on your calendar?")
                heismanSubtitle("Help the MVP coach get to know how you manage your kids busy day. Let’s start by adding your children.")
            }

            VStack(alignment: .leading, spacing: .hearth300) {
                Text("Ages tell the coach a lot — a five-year-old's Saturday looks nothing like a two-year-old's.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkPrimary)
                    .fixedSize(horizontal: false, vertical: true)

                ForEach($draft.kids) { $kid in
                    childRow($kid)
                }

                // "+ add another child" — Inter 17, the phrase underlined.
                Button {
                    withAnimation(.hearth(.hearthFast, reduceMotion: false)) {
                        draft.kids.append(OnboardingDraft.Kid())
                    }
                } label: {
                    (Text("+ ").font(.hearthBodyLG)
                        + Text("add another child").font(.hearthBodyLG).underline())
                        .foregroundColor(.inkPrimary)
                }
                .padding(.top, .hearth200)
                .accessibilityLabel("Add another child")
            }
        } footer: {
            HeismanCTA(label: "Continue", enabled: hasCompleteChild, action: onContinue)
        }
        .task {
            // The frame opens with one empty row already present — adding a
            // child appends a row rather than advancing.
            if draft.kids.isEmpty { draft.kids.append(OnboardingDraft.Kid()) }
        }
        .trackScreen("onboarding_children")
    }

    /// One child row: name field (flexible) + age field (91pt) — measured
    /// r12 cards side by side. Rows are removable (acceptance #1); the frame
    /// draws no remove affordance, so a quiet ⓧ ships next to the age field
    /// on every row after the first (flagged in the hand-off report).
    private func childRow(_ kid: Binding<OnboardingDraft.Kid>) -> some View {
        HStack(spacing: .hearth300) {
            HeismanField(placeholder: "Child name", text: kid.name, textContentType: .givenName)
            HeismanField(placeholder: "Age", text: kid.age, keyboard: .numberPad)
                .frame(width: 91)
            if draft.kids.count > 1 {
                Button {
                    withAnimation(.hearth(.hearthFast, reduceMotion: false)) {
                        draft.kids.removeAll { $0.id == kid.wrappedValue.id }
                    }
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 18))
                        .foregroundColor(.inkMuted)
                }
                .accessibilityLabel("Remove this child")
            }
        }
    }
}

// MARK: Topic ("Onboarding - 3", step 03)

struct HeismanTopicView: View {
    @Binding var draft: OnboardingDraft
    let onBack: () -> Void
    let onContinue: () -> Void

    @StateObject private var dictation = DictationController()
    /// Local mirror of the free-text route. `draft.topic` holds ONE value —
    /// a card id or the free string — so the text lives here and is written
    /// through on every edit (which also clears any card selection: the two
    /// routes are alternatives, not additive).
    @State private var freeText = ""

    private var selectedCard: HeismanTopic? {
        HeismanTopic.all.first { $0.id == draft.topic }
    }

    private var canContinue: Bool {
        selectedCard != nil || !freeText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var body: some View {
        HeismanScreen(step: .topic, onBack: onBack) {
            Spacer(minLength: .hearth700)

            VStack(alignment: .leading, spacing: 15) {
                heismanTitle("What can the coach take off your hands?")
                heismanSubtitle("Pick what’s closest. You’ll hand over the details next.")
            }

            // Six cards, 2-up, gap 8. Single-select: tapping a second card
            // moves the selection (acceptance #3).
            VStack(spacing: .hearth300) {
                ForEach(0..<3, id: \.self) { row in
                    HStack(spacing: .hearth300) {
                        topicCard(HeismanTopic.all[row * 2])
                        topicCard(HeismanTopic.all[row * 2 + 1])
                    }
                }

                // Free text, r24 card, "Something else..." — no character
                // limit (D5). Typing clears any card selection (acceptance #4).
                HeismanTextCard(
                    placeholder: "Something else...",
                    text: $freeText,
                    dictation: dictation,
                    minEditorHeight: 96,
                    onEdit: {
                        // Typing IS the free-text route: writing it through
                        // replaces (and therefore clears) any card selection.
                        draft.topic = freeText
                    }
                )
            }
        } footer: {
            HeismanCTA(label: "Continue", enabled: canContinue) {
                dictation.stop()
                // Persist whichever route answered (cards already wrote
                // through; the free text wins when a card isn't selected).
                if selectedCard == nil { draft.topic = freeText.trimmingCharacters(in: .whitespacesAndNewlines) }
                onContinue()
            }
        }
        .onAppear {
            // Resume: a stored free-text topic re-populates the field.
            if selectedCard == nil { freeText = draft.topic }
        }
        .onDisappear { dictation.stop() }
        .trackScreen("onboarding_topic")
    }

    /// Topic card, measured: h86, r12, p8, cream-50 fill, 1px `border/strong`
    /// stroke, 15pt icon above an Inter 13 label in `ink/placeholder`.
    /// Selected (spec §3 states table): `accent/tint` fill, `accent/default`
    /// border — icon + label follow into the accent, bold label (matching
    /// the step-05 frame's drawn selected state, the one selected-card state
    /// the design actually renders).
    private func topicCard(_ topic: HeismanTopic) -> some View {
        let selected = draft.topic == topic.id
        return Button {
            withAnimation(.hearth(.hearthFast, reduceMotion: false)) {
                // Using a card clears the free-text route and vice versa.
                draft.topic = selected ? "" : topic.id
                if !selected { freeText = "" }
            }
        } label: {
            VStack(alignment: .leading, spacing: 6) {
                Image(topic.icon)
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 15, height: 15)
                    .foregroundColor(selected ? .accentDefault : .inkSecondary)
                Text(topic.label)
                    .font(selected ? .hearthBodySMBold : .hearthBodySM)
                    .foregroundColor(selected ? .accentDefault : .inkMuted)
                    .multilineTextAlignment(.leading)
                    .fixedSize(horizontal: false, vertical: true)
            }
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
