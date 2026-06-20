import SwiftUI

/// Shown after the handoff gesture: a picker for which kid is using the device.
/// PIN is selection convenience (parent set), not the security boundary.
///
/// Soft-sober treatment: this is a transient picker in front of the sober
/// kid-agent surface, so it uses `bg/canvas` (not sober — the picker is part
/// of the parent-mode chrome between handoff and child mode).
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
            Color.bgCanvas.ignoresSafeArea()

            VStack(spacing: .hearth700) {
                if vm.isLoading {
                    ProgressView().tint(.accentDefault)
                } else if let kid = vm.pinPromptFor {
                    pinPrompt(kid: kid)
                } else {
                    picker
                }
            }
            .padding(.hearth600)

            VStack {
                HStack {
                    Spacer()
                    Button(action: onCancel) {
                        Image(systemName: "xmark")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundColor(.inkMuted)
                            .frame(width: 44, height: 44)
                            .contentShape(Rectangle())
                    }
                }
                Spacer()
            }
            .padding(.hearth500)
        }
        .task { await vm.load() }
    }

    private var picker: some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            Text("Who's using the device?")
                .font(.hearthDisplayMD)
                .foregroundColor(.inkPrimary)

            ForEach(vm.kids, id: \.kidName) { kid in
                Button {
                    // Disabled kids can't be tapped (.disabled below); call the
                    // selection closure directly — no NotificationCenter detour.
                    onSelected(kid)
                } label: {
                    HStack(spacing: .hearth500) {
                        Circle()
                            .fill(Color.accentTint)
                            .frame(width: 56, height: 56)
                            .overlay(
                                Text(String(kid.kidName.prefix(1)))
                                    .font(.hearthTitleLG)
                                    .foregroundColor(.accentDefault)
                            )
                        VStack(alignment: .leading, spacing: 2) {
                            Text(kid.kidName)
                                .font(.hearthTitleMD)
                                .foregroundColor(.inkPrimary)
                            Text(kid.invariants.agentDisplayName)
                                .font(.hearthBodySM)
                                .foregroundColor(.inkMuted)
                        }
                        Spacer()
                        Image(systemName: "chevron.right")
                            .foregroundColor(.inkMuted)
                    }
                    .padding(.hearth500)
                    .background(Color.bgElevated)
                    .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .stroke(Color.borderHairline, lineWidth: 1)
                    )
                }
                .buttonStyle(.plain)
                .disabled(!kid.enabled)
                .opacity(kid.enabled ? 1.0 : 0.5)
            }
            if vm.kids.contains(where: { !$0.enabled }) {
                Text("Greyed-out companions haven't been set up yet — tap them on the Home tab first.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func pinPrompt(kid: KidAgentConfig) -> some View {
        VStack(spacing: .hearth500) {
            Text("PIN for \(kid.kidName)")
                .font(.hearthTitleLG)
                .foregroundColor(.inkPrimary)
            SecureField("• • • •", text: $pinDraft)
                .keyboardType(.numberPad)
                .multilineTextAlignment(.center)
                .font(.system(size: 28, weight: .semibold, design: .rounded))
                .foregroundColor(.inkPrimary)
                .padding(.vertical, .hearth400).padding(.horizontal, .hearth800)
                .background(Color.bgElevated)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                        .stroke(Color.borderStrong, lineWidth: 1)
                )
            if let pinError {
                Text(pinError)
                    .font(.hearthBodySM)
                    .foregroundColor(.statusError)
            }
            Button("Continue") {
                // We don't validate the PIN client-side — backend rejects on mismatch.
                onSelected(kid)
            }
            .buttonStyle(.borderedProminent)
            .tint(.accentDefault)

            Button("Use a different kid") {
                vm.pinPromptFor = nil
                pinDraft = ""
            }
            .font(.hearthBodySM)
            .foregroundColor(.inkMuted)
        }
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

}
