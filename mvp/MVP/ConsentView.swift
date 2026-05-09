import SwiftUI

/// Closed-beta v0 informed-consent screen. Shown when the parent first enters
/// the kid-agent flow and `/consent/status.accepted == false` (or when the
/// agreement_version has bumped).
///
/// This DOES NOT meet COPPA's "verifiable parental consent" bar — that's v1
/// (see docs/roadmap.md). For v0 closed beta, an in-app agreement signed by
/// participating parents is the gate.
struct ConsentView: View {
    let userID: String
    let baseURL: URL
    let agreementVersion: String
    let onAccepted: () -> Void

    @State private var parentName: String = ""
    @State private var parentEmail: String = ""
    @State private var kidAgeBand: String = "middle"
    @State private var submitting = false
    @State private var error: String?

    private let ageBands: [(label: String, value: String)] = [
        ("4–6 (early)", "early"),
        ("7–9 (middle)", "middle"),
        ("10–12 (tween)", "tween"),
        ("13+ (teen)", "teen"),
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Closed beta")
                    .font(.caption.weight(.semibold))
                    .foregroundColor(.brandGold)
                    .textCase(.uppercase)
                    .tracking(0.6)

                Text("Before we set up your kid's companion")
                    .font(.title2.weight(.semibold))
                    .foregroundColor(.white)

                Text("""
                You're trying something early. A few honest things you should know:

                • The companion is shaped by what you tell us — its personality, what \
                it can talk about, what tools it has.
                • Every conversation between your kid and this companion is visible to \
                you. There are no private chats.
                • Moderation runs on every message in and out. Crisis topics (self-harm, \
                abuse) immediately alert you.
                • This is closed beta — not yet COPPA-compliant. We don't list publicly \
                or run marketing aimed at kids. Public release will require additional \
                compliance work.
                • You can revoke this companion or delete its history at any time.
                """)
                    .font(.callout)
                    .foregroundColor(.white.opacity(0.85))
                    .lineSpacing(4)

                VStack(alignment: .leading, spacing: 12) {
                    field("Your name", text: $parentName)
                    field("Your email", text: $parentEmail)
                    Text("Kid's age band")
                        .font(.subheadline.weight(.medium))
                        .foregroundColor(.white.opacity(0.8))
                    Picker("Age band", selection: $kidAgeBand) {
                        ForEach(ageBands, id: \.value) { band in
                            Text(band.label).tag(band.value)
                        }
                    }
                    .pickerStyle(.segmented)
                }

                if let error {
                    Text(error)
                        .font(.footnote)
                        .foregroundColor(.red)
                }

                Button(action: submit) {
                    HStack {
                        if submitting { ProgressView().tint(.brandBlack) }
                        Text(submitting ? "Recording…" : "I understand and agree")
                            .font(.headline.weight(.semibold))
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(canSubmit ? Color.brandGold : Color.brandGold.opacity(0.4))
                    .foregroundColor(.brandBlack)
                    .clipShape(Capsule())
                }
                .disabled(!canSubmit || submitting)

                Text("Agreement version: \(agreementVersion)")
                    .font(.caption2)
                    .foregroundColor(.brandGray)
                    .padding(.top, 4)
            }
            .padding(20)
        }
        .background(Color.brandBackground.ignoresSafeArea())
    }

    private var canSubmit: Bool {
        !parentName.trimmingCharacters(in: .whitespaces).isEmpty &&
        parentEmail.contains("@")
    }

    private func field(_ label: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(label)
                .font(.subheadline.weight(.medium))
                .foregroundColor(.white.opacity(0.8))
            TextField("", text: text)
                .padding(12)
                .background(Color.brandSurface)
                .foregroundColor(.white)
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                .autocorrectionDisabled()
                .textInputAutocapitalization(.never)
        }
    }

    private func submit() {
        submitting = true
        error = nil
        Task {
            do {
                let service = KidAgentService(baseURL: baseURL, userID: userID)
                try await service.submitConsent(
                    parentName: parentName,
                    parentEmail: parentEmail,
                    kidAgeBand: kidAgeBand,
                    agreementVersion: agreementVersion
                )
                submitting = false
                onAccepted()
            } catch {
                submitting = false
                self.error = error.localizedDescription
            }
        }
    }
}
