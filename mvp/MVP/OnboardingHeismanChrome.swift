import SwiftUI

// MARK: - Heisman sprint-01 shared chrome
//
// Every measured value here comes from the sprint-01 frames (Figma
// `nAXZQhmvwEpzq3rkBisok7`, section "Heisman"), pulled 2026-08-21 via the
// Figma MCP. The frames are 440pt wide with a 380pt content column (30pt
// gutters) on the `bg/sober` cream (`#F3F0EB` — the design file calls it
// `bg/canvas`, but its VALUE is this app's `bgSober` token; the app's own
// `bgCanvas` is the darker `#E9E4DC` and is NOT what these frames draw).
//
// Recurring hex → token mapping (used consistently across all Heisman files):
//   #F3F0EB → .bgSober          #FCFBF8 → .bgCoachBanner (cream-50)
//   #151412 → .inkPrimary       #1E1E1E → .inkDisplay
//   #6E6A62 → .inkMuted         #C8C3B8 → .borderInputPill (#C9C5BE, nearest)
//   #1B7498 → .accentDefault    #DCE9EF → .accentTint
//   #4A4741 → (see note)        #2B2925 → .inkHeader
//
// The #4A4741 note: the design file's `border/strong` primitive resolves to
// #4A4741, which is this app's `charcoalBtn` (bgButtonFunnel, "FILL only").
// The app's `borderStrong` token is #8A8275 — a real hex drift between the
// two systems. Per the sprint instruction the existing semantic token wins:
// card borders here use `.borderStrong`; flagged in the hand-off report.

// MARK: Step model

/// The five numbered steps ("0X of 05"), exactly as the frames stamp them:
/// cold open = 01, children = 02, topic AND sample problem = 03 (D3: the 4x
/// variants share the topic's step), extraction check = 04, parent tasks =
/// 05. Screens 0 (splash), gettingReady, 7, 8 show no rail (acceptance #9).
enum HeismanStep: Int {
    case coldOpen = 1
    case children = 2
    case topic = 3          // also stamped on the 4a/4b sample-problem frames
    case extractionCheck = 4
    case parentTasks = 5

    /// Measured fill widths on the 365pt rail: 77, 77, 154, 264, 365.
    var fillFraction: CGFloat {
        switch self {
        case .coldOpen:        return 77.0 / 365.0
        case .children:        return 77.0 / 365.0
        case .topic:           return 154.0 / 365.0
        case .extractionCheck: return 264.0 / 365.0
        case .parentTasks:     return 1.0
        }
    }

    var label: String { "0\(rawValue) of 05" }

    /// The mono stamp's ink: `#6E6A62` on steps 01–02, `#C8C3B8` from 03 on
    /// (measured per frame — the lighter ink sits over the longer fill).
    var monoInk: Color { rawValue <= 2 ? .inkMuted : .borderInputPill }

    /// The rail track (`bg/elevated` cream-50) renders at 50% opacity on the
    /// 01/02 frames and full opacity from 03 — measured, not invented.
    var trackOpacity: CGFloat { rawValue <= 2 ? 0.5 : 1.0 }
}

// MARK: Layout constants

enum HeismanLayout {
    /// 440pt frame, 380pt content column.
    static let gutter: CGFloat = 30
    /// Header inset (`Header Component` px-20).
    static let headerGutter: CGFloat = 20
}

// MARK: Header — back circle + progress rail

/// Measured: 31pt back circle (fill = the canvas itself, so it reads as a
/// bare arrow until pressed), gap 4 to a 30pt-tall pill rail (track cream-50,
/// 2pt inset, `accent/default` fill at 30% opacity), "0X of 05" JetBrains
/// Mono 12 right-aligned inside the rail.
///
/// The 16×13 back arrow is drawn in the frames as a two-layer vector that is
/// visually identical to SF `arrow.left` at this size — a generic system
/// glyph, so per the fidelity playbook's SF-symbol carve-out it ships as the
/// SF symbol rather than an export.
struct HeismanHeader: View {
    let step: HeismanStep
    let onBack: () -> Void

    var body: some View {
        HStack(spacing: .hearth200) {
            Button(action: onBack) {
                Image(systemName: "arrow.left")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.accentOnCanvas)
                    .frame(width: 31, height: 31)
                    .background(Circle().fill(Color.bgSober))
            }
            .accessibilityLabel("Back")

            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(Color.bgCoachBanner.opacity(step.trackOpacity))
                    Capsule()
                        .fill(Color.accentDefault.opacity(0.3))
                        .frame(width: max(0, geo.size.width - 4) * step.fillFraction)
                        .padding(2)
                    Text(step.label)
                        .font(.hearthCaptionMono)
                        .foregroundColor(step.monoInk)
                        .frame(maxWidth: .infinity, alignment: .trailing)
                        .padding(.trailing, .hearth400)
                }
            }
            .frame(height: 30)
            .animation(.hearth(.hearthSlow, reduceMotion: false), value: step)
            .accessibilityElement(children: .ignore)
            .accessibilityLabel("Step \(step.rawValue) of 5")
        }
        .padding(.horizontal, HeismanLayout.headerGutter)
        .padding(.top, .hearth400)
    }
}

// MARK: Type helpers

/// Fraunces Bold 38/40, tracking −0.38 — `type/display-lg`, every Heisman
/// headline. `hearthDisplaySM` is exactly this token.
func heismanTitle(_ text: String) -> some View {
    Text(text)
        .font(.hearthDisplaySM)
        .tracking(-0.38)
        .foregroundColor(.inkPrimary)
        .lineSpacing(2)
        .fixedSize(horizontal: false, vertical: true)
        .frame(maxWidth: .infinity, alignment: .leading)
}

/// Inter 17/26 — `type/body-lg`. Note the ink: the frames set body copy in
/// the PRIMARY ink, not a muted secondary.
func heismanSubtitle(_ text: String) -> some View {
    Text(text)
        .font(.hearthBodyLG)
        .foregroundColor(.inkPrimary)
        .lineSpacing(.hearthLineBodyLG)
        .fixedSize(horizontal: false, vertical: true)
        .frame(maxWidth: .infinity, alignment: .leading)
}

/// JetBrains Mono 12/16 — `type/caption-mono` eyebrows ("From your MVP
/// Coach", the step-04 topic echo).
func heismanMonoEyebrow(_ text: String, ink: Color = .inkPrimary) -> some View {
    Text(text)
        .font(.hearthCaptionMono)
        .foregroundColor(ink)
        .frame(maxWidth: .infinity, alignment: .leading)
}

// MARK: CTA

/// The Heisman CTA pill. Measured: full-width capsule (r100), py 12, label
/// Inter ExtraBold 16 (`type/title-md-bold` → `hearthSectionHeader`) in
/// `ink/onphoto-light`. Enabled fill `accent/default`; pressed `accent/press`
/// (spec §3 states table); disabled fill = the design's `ink-100` gray
/// (#C8C3B8 → nearest fill token `bgDisabled`) with the label at 50%.
struct HeismanCTAStyle: ButtonStyle {
    var enabled: Bool
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.hearthSectionHeader)
            .foregroundColor(enabled ? .inkOnPhotoLight : .inkOnPhotoLight.opacity(0.5))
            .frame(maxWidth: .infinity)
            .padding(.vertical, .hearth400)
            .background(
                enabled
                    ? (configuration.isPressed ? Color.accentPress : Color.accentDefault)
                    : Color.bgDisabled
            )
            .clipShape(Capsule())
    }
}

struct HeismanCTA: View {
    let label: String
    var enabled: Bool = true
    var busy: Bool = false
    let action: () -> Void

    var body: some View {
        Button {
            hideKeyboard()
            action()
        } label: {
            ZStack {
                Text(label).opacity(busy ? 0 : 1)
                if busy {
                    ProgressView().tint(.inkOnPhotoLight)
                }
            }
        }
        .buttonStyle(HeismanCTAStyle(enabled: enabled))
        .disabled(!enabled || busy)
    }
}

// MARK: Screen scaffold

/// The common Heisman composition: sober ground, optional stepped header, a
/// scrolling content column, and a footer pinned with the same
/// `.safeAreaInset` never-overlaps contract the beta-v1 funnel proved out.
struct HeismanScreen<Content: View, Footer: View>: View {
    var step: HeismanStep?
    var onBack: (() -> Void)?
    @ViewBuilder var content: () -> Content
    @ViewBuilder var footer: () -> Footer

    var body: some View {
        VStack(spacing: 0) {
            if let step, let onBack {
                HeismanHeader(step: step, onBack: onBack)
            }
            ScrollView {
                VStack(alignment: .leading, spacing: .hearth500) {
                    content()
                }
                .padding(.horizontal, HeismanLayout.gutter)
                .padding(.top, .hearth700)
                .padding(.bottom, .hearth700)
            }
            .scrollDismissesKeyboard(.immediately)
        }
        .background(Color.bgSober.ignoresSafeArea())
        .safeAreaInset(edge: .bottom) {
            VStack(spacing: .hearth500) {
                footer()
            }
            .padding(.horizontal, HeismanLayout.gutter)
            .padding(.top, .hearth300)
            .padding(.bottom, .hearth400)
            .background(Color.bgSober)
        }
    }
}

// MARK: Input pill (single line)

/// The r12 input card: cream-50 fill, 1px `ink-100` stroke, pad 15/20, value
/// type Inter Light 20 (the design's own input style; placeholder is the
/// same face in `ink/placeholder`).
struct HeismanField: View {
    let placeholder: String
    @Binding var text: String
    var keyboard: UIKeyboardType = .default
    var textContentType: UITextContentType?

    /// Inter Light 20/24 — the measured input face on every Heisman field.
    static let inputFont = Font.custom(HearthFontFamily.sans, size: 20, relativeTo: .title3).weight(.light)

    var body: some View {
        TextField("", text: $text, prompt: Text(placeholder).foregroundColor(.inkMuted))
            .font(Self.inputFont)
            .foregroundColor(.inkPrimary)
            .keyboardType(keyboard)
            .textContentType(textContentType)
            .autocorrectionDisabled()
            .padding(.horizontal, 15)
            .padding(.vertical, .hearth600)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.bgCoachBanner)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                    .stroke(Color.borderInputPill, lineWidth: 1)
            )
    }
}

// MARK: Free-text card with mic accessory

/// The waveform + mic pair every Heisman free-text card draws bottom-right
/// (24pt mic, 14×19 waveform — Figma exports `OnbIcon-mic` /
/// `OnbIcon-waveform`). The mic is REAL (Appendix A2): tapping it starts
/// on-device dictation and the finished transcript lands in `text`.
struct HeismanMicAccessory: View {
    @ObservedObject var dictation: DictationController
    @Binding var text: String

    var body: some View {
        VStack(alignment: .trailing, spacing: .hearth200) {
            HStack(spacing: .hearth300) {
                Spacer(minLength: 0)
                Image("OnbIcon-waveform")
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 14, height: 19)
                    .foregroundColor(dictation.isRecording ? .accentDefault : .borderInputPill)
                Button {
                    dictation.toggle { final in
                        text = text.isEmpty ? final : text + " " + final
                    }
                } label: {
                    Image("OnbIcon-mic")
                        .renderingMode(.template)
                        .resizable()
                        .scaledToFit()
                        .frame(width: 24, height: 24)
                        .foregroundColor(dictation.isRecording ? .accentDefault : .borderInputPill)
                }
                .accessibilityLabel(dictation.isRecording ? "Stop dictation" : "Dictate")
            }
            if dictation.isRecording, !dictation.transcript.isEmpty {
                Text(dictation.transcript)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                    .lineLimit(2)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            if let message = dictation.errorMessage {
                Text(message)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }
}

/// A multi-line free-text card: cream-50 ground, stroked, radius per call
/// site (r24 on the topic/tasks cards, r12 on the step-04 scrap card),
/// placeholder Inter 13, the mic accessory pinned to the bottom edge.
struct HeismanTextCard: View {
    let placeholder: String
    @Binding var text: String
    @ObservedObject var dictation: DictationController
    var radius: CGFloat = .hearthRadiusSheet
    var stroke: Color = .borderInputPill
    var strokeWidth: CGFloat = 1
    var placeholderInk: Color = .borderInputPill
    var minEditorHeight: CGFloat = 64
    var onEdit: (() -> Void)?

    var body: some View {
        VStack(spacing: .hearth300) {
            TextEditor(text: $text)
                .font(.hearthBodySM)
                .foregroundColor(.inkPrimary)
                .scrollContentBackground(.hidden)
                .frame(minHeight: minEditorHeight)
                .overlay(alignment: .topLeading) {
                    if text.isEmpty {
                        Text(placeholder)
                            .font(.hearthBodySM)
                            .foregroundColor(placeholderInk)
                            .padding(.top, 8)
                            .padding(.leading, 5)
                            .allowsHitTesting(false)
                    }
                }
                .onChange(of: text) { _, _ in onEdit?() }
            HeismanMicAccessory(dictation: dictation, text: $text)
                .padding(.horizontal, 5)
                .padding(.bottom, 2)
        }
        .padding(.hearth600)
        .background(Color.bgCoachBanner)
        .clipShape(RoundedRectangle(cornerRadius: radius, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: radius, style: .continuous)
                .stroke(stroke, lineWidth: strokeWidth)
        )
    }
}

// MARK: Topic model

/// The six topic cards on "Onboarding - 3", in the frame's reading order.
/// `id` is the stable value stored in `draft.topic` and seeded as `topic`;
/// `label` is display copy; `icon` names the exported Figma vector.
struct HeismanTopic: Identifiable, Equatable {
    let id: String
    let label: String
    let icon: String

    static let all: [HeismanTopic] = [
        .init(id: "dinner",      label: "Tonight's dinner",                  icon: "OnbTopicIcon-dinner"),
        .init(id: "practice",    label: "A practice or lesson schedule",     icon: "OnbTopicIcon-practice"),
        .init(id: "appointment", label: "An appointment coming up",          icon: "OnbTopicIcon-appointment"),
        .init(id: "playdate",    label: "A playdate to arrange",             icon: "OnbTopicIcon-playdate"),
        .init(id: "school",      label: "Something a school or program sent", icon: "OnbTopicIcon-school"),
        .init(id: "birthday",    label: "A birthday or event on the horizon", icon: "OnbTopicIcon-birthday"),
    ]

    /// Display label for a stored `draft.topic` value — a card's label when
    /// the value is a card id, otherwise the free text as typed. Feeds the
    /// step-04 mono eyebrow and the coach demonstration.
    static func displayLabel(for stored: String) -> String {
        all.first(where: { $0.id == stored })?.label ?? stored
    }
}

// MARK: Static sample extraction (fallback)

extension OnboardingDraft.ExtractedActivity {
    /// The frame's own sample cards ("Onboarding - 5") — the sanctioned
    /// STATIC fallback when extraction was skipped or failed (Appendix A2).
    /// Sample content, clearly the demo's: never seeded as real activities —
    /// `collectedData()` only seeds `draft.extractedActivities`, which stays
    /// empty on the fallback path.
    static let sampleFallback: [OnboardingDraft.ExtractedActivity] = [
        .init(who: "Lily", what: "Swim lessons", when: "Tuesdays · 4:15 pm", where: "Northgate Aquatic Center"),
        .init(who: "Benjamin", what: "Peewee soccer", when: "Saturdays · 9:00 am", where: "Cedar Field"),
    ]
}
