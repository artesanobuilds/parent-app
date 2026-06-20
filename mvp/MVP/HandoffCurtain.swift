import SwiftUI

/// Wraps the parent UI and presents kid mode (full-screen) when the parent
/// triggers the handoff.
///
/// v0 trigger: small "Hand to kid" button on Home (added by HandoffEntryButton).
/// The two-finger swipe-down gesture is wired here as well — gesture runs at
/// the root, presents the picker. Either path produces the same KidAgentView.
///
/// Exit from kid mode: long-press on the small chevron in KidAgentView's top-
/// right corner triggers a confirm dialog. v1 will add a parent-PIN gate.
struct HandoffCurtain<Content: View>: View {
    let userID: String
    let baseURL: URL
    @ViewBuilder var content: () -> Content

    @State private var presented: Bool = false
    @State private var selectedKid: KidAgentConfig?

    var body: some View {
        ZStack {
            content()
                .gesture(twoFingerSwipeDown)
                .environment(\.triggerKidHandoff, { presented = true })
        }
        .fullScreenCover(isPresented: $presented) {
            ZStack {
                if let kid = selectedKid {
                    KidAgentView(
                        userID: userID, baseURL: baseURL, kid: kid,
                        onExit: {
                            selectedKid = nil
                            presented = false
                        }
                    )
                } else {
                    KidPickerView(
                        userID: userID, baseURL: baseURL,
                        onSelected: { kid in self.selectedKid = kid },
                        onCancel: {
                            selectedKid = nil
                            presented = false
                        }
                    )
                }
            }
            .preferredColorScheme(.dark)
        }
    }

    /// Two-finger downward drag gesture that triggers kid mode.
    private var twoFingerSwipeDown: some Gesture {
        // SwiftUI doesn't natively expose multi-touch in DragGesture. v0
        // approximates with a long downward drag with high translation and
        // moderate velocity. v1 wires a UIKit gesture recognizer to count
        // fingers explicitly.
        DragGesture(minimumDistance: 80, coordinateSpace: .global)
            .onEnded { value in
                let dy = value.translation.height
                let dx = abs(value.translation.width)
                if dy > 220 && dx < 80 {
                    presented = true
                }
            }
    }
}

// Environment-injected trigger so the entry button (which lives inside the
// curtain's content) can flip the curtain's @State. Avoids prop-drilling a
// binding from MainTabView through every wrapped view.
private struct TriggerKidHandoffKey: EnvironmentKey {
    static let defaultValue: () -> Void = {}
}
extension EnvironmentValues {
    var triggerKidHandoff: () -> Void {
        get { self[TriggerKidHandoffKey.self] }
        set { self[TriggerKidHandoffKey.self] = newValue }
    }
}

/// Small button rendered on Home so the handoff is discoverable. Long-press
/// version of the gesture above.
struct HandoffEntryButton: View {
    let onTrigger: () -> Void
    var body: some View {
        Button(action: onTrigger) {
            HStack(spacing: 8) {
                Image(systemName: "hand.wave")
                Text("Hand to kid")
                    .lineLimit(1)
                    .fixedSize(horizontal: true, vertical: false)
            }
            .font(.hearthBodyMD.weight(.semibold))
            .foregroundColor(.accentDefault)
            .padding(.horizontal, 18).padding(.vertical, 10)
            .background(Color.accentTint)
            .overlay(
                Capsule().stroke(Color.accentDefault.opacity(0.35), lineWidth: 1)
            )
            .clipShape(Capsule())
        }
    }
}
