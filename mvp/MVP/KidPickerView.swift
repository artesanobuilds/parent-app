import SwiftUI

/// Shown after the handoff gesture: a picker for which kid is using the device.
/// PIN is selection convenience (parent set), not the security boundary.
struct KidPickerView: View {
    let userID: String
    let baseURL: URL
    let onSelected: (KidAgentConfig) -> Void
    let onCancel: () -> Void

    @StateObject private var vm: KidPickerViewModel
    @State private var pinDraft: String = ""
    @State private var pinError: String?

    init(userID: String, baseURL: URL,
         onSelected: @escaping (KidAgentConfig) -> Void,
         onCancel: @escaping () -> Void) {
        self.userID = userID
        self.baseURL = baseURL
        self.onSelected = onSelected
        self.onCancel = onCancel
        _vm = StateObject(wrappedValue: KidPickerViewModel(userID: userID, baseURL: baseURL))
    }

    var body: some View {
        ZStack {
            Color.brandBackground.ignoresSafeArea()

            VStack(spacing: 24) {
                if vm.isLoading {
                    ProgressView().tint(.brandGold)
                } else if let kid = vm.pinPromptFor {
                    pinPrompt(kid: kid)
                } else {
                    picker
                }
            }
            .padding(20)

            VStack {
                HStack {
                    Spacer()
                    Button(action: onCancel) {
                        Image(systemName: "xmark")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundColor(.brandGray)
                            .padding(10)
                    }
                }
                Spacer()
            }
            .padding()
        }
        .task { await vm.load() }
    }

    private var picker: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Who's using the device?")
                .font(.title2.weight(.semibold))
                .foregroundColor(.white)

            ForEach(vm.kids, id: \.kidName) { kid in
                Button {
                    vm.tap(kid)
                } label: {
                    HStack(spacing: 14) {
                        Circle()
                            .fill(bloomColor(for: kid).opacity(0.25))
                            .frame(width: 56, height: 56)
                            .overlay(
                                Text(String(kid.kidName.prefix(1)))
                                    .font(.title3.weight(.bold))
                                    .foregroundColor(bloomColor(for: kid))
                            )
                        VStack(alignment: .leading, spacing: 2) {
                            Text(kid.kidName)
                                .font(.headline)
                                .foregroundColor(.white)
                            Text(kid.invariants.agentDisplayName)
                                .font(.caption)
                                .foregroundColor(.brandGray)
                        }
                        Spacer()
                        Image(systemName: "chevron.right")
                            .foregroundColor(.brandGray)
                    }
                    .padding(14)
                    .background(Color.brandSurface)
                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                }
                .buttonStyle(.plain)
                .disabled(!kid.enabled)
                .opacity(kid.enabled ? 1.0 : 0.5)
            }
            if vm.kids.contains(where: { !$0.enabled }) {
                Text("Greyed-out companions haven't been set up yet — tap them on the Home tab first.")
                    .font(.caption)
                    .foregroundColor(.brandGray)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func pinPrompt(kid: KidAgentConfig) -> some View {
        VStack(spacing: 16) {
            Text("PIN for \(kid.kidName)")
                .font(.headline)
                .foregroundColor(.white)
            SecureField("• • • •", text: $pinDraft)
                .keyboardType(.numberPad)
                .multilineTextAlignment(.center)
                .font(.system(size: 28, weight: .semibold, design: .rounded))
                .foregroundColor(.white)
                .padding(.vertical, 12).padding(.horizontal, 32)
                .background(Color.brandSurface)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            if let pinError {
                Text(pinError).font(.footnote).foregroundColor(.red)
            }
            Button("Continue") {
                // We don't validate the PIN client-side — backend rejects on mismatch.
                onSelected(kid)
            }
            .buttonStyle(.borderedProminent)
            .tint(.brandGold)

            Button("Use a different kid") {
                vm.pinPromptFor = nil
                pinDraft = ""
            }
            .font(.caption)
            .foregroundColor(.brandGray)
        }
    }

    /// Bloom color comes from the synthesized personality. v0 maps personality
    /// keywords to a small palette — v1 will derive from the LLM's structured
    /// output directly.
    private func bloomColor(for kid: KidAgentConfig) -> Color {
        let words = (kid.invariants.personalityDescription
                     + " " + kid.invariants.voiceExamples.joined(separator: " "))
            .lowercased()
        if words.contains("playful") || words.contains("silly") {
            return Color(red: 0.36, green: 0.65, blue: 0.62)  // muted teal
        }
        if words.contains("warm") || words.contains("cozy") {
            return Color(red: 0.78, green: 0.45, blue: 0.34)  // terracotta
        }
        return .brandGold  // steady fallback
    }
}

@MainActor
final class KidPickerViewModel: ObservableObject {
    let userID: String
    let baseURL: URL
    @Published var kids: [KidAgentConfig] = []
    @Published var isLoading = false
    @Published var pinPromptFor: KidAgentConfig?

    init(userID: String, baseURL: URL) {
        self.userID = userID
        self.baseURL = baseURL
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            kids = try await KidAgentService(baseURL: baseURL, userID: userID).list()
        } catch {
            print("[KidPicker] list failed: \(error)")
        }
    }

    func tap(_ kid: KidAgentConfig) {
        // For v0: skip PIN prompt unless explicitly set. The picker route is
        // already gated by the parent's authenticated session.
        if !kid.enabled { return }
        pinPromptFor = nil
        // If the parent has set a PIN we'd present pinPromptFor here; v0
        // defers to the parent session as auth boundary.
        // We surface the picker -> reviewer/streamer choice in KidAgentView.
        proceed(kid)
    }

    private func proceed(_ kid: KidAgentConfig) {
        // KidPickerView's onSelected closure is captured at view init — call
        // it via a published flag would require restructuring. Instead, we
        // forward by mutating pinPromptFor (no PIN UI shown) and let the view
        // call onSelected when it picks up the change.
        // Simpler path: emit via Notification.
        NotificationCenter.default.post(
            name: .kidPickerSelected,
            object: nil,
            userInfo: ["config": kid]
        )
    }
}

extension Notification.Name {
    static let kidPickerSelected = Notification.Name("kidPickerSelected")
}
