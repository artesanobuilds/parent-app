import SwiftUI

/// Closed-beta v0 informed-consent screen. Shown when the parent first enters
/// the kid-agent flow and `/consent/status.accepted == false` (or when the
/// agreement_version has bumped).
///
/// SOBER VARIANT: this is a safety surface. Uses `bg/sober`, no photo tiles,
/// no decorative serif, restrained type. The quiet treatment is intentional —
/// the screen sits between the parent and a permission decision.
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
            VStack(alignment: .leading, spacing: .hearth600) {
                Text("Closed beta")
                    .font(.hearthLabel)
                    .foregroundColor(.accentDefault)
                    .tracking(0.66)
                    .textCase(.uppercase)

                // Sober variant forbids decorative serif on titles; use Inter
                // title-lg here instead of Fraunces display.
                Text("Before we set up your kid's companion")
                    .font(.hearthTitleLG)
                    .foregroundColor(.inkPrimary)

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
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkPrimary)
                    .lineSpacing(.hearthLineBodyMD)

                VStack(alignment: .leading, spacing: .hearth400) {
                    field("Your name", text: $parentName)
                    field("Your email", text: $parentEmail)
                    Text("Kid's age band")
                        .font(.hearthLabel)
                        .foregroundColor(.inkMuted)
                        .tracking(0.66)
                        .textCase(.uppercase)
                    Picker("Age band", selection: $kidAgeBand) {
                        ForEach(ageBands, id: \.value) { band in
                            Text(band.label).tag(band.value)
                        }
                    }
                    .pickerStyle(.segmented)
                }

                if let error {
                    Text(error)
                        .font(.hearthBodySM)
                        .foregroundColor(.statusError)
                        .padding(.hearth400)
                        .background(Color.statusErrorTint)
                        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                }

                Button(action: submit) {
                    HStack {
                        if submitting { ProgressView().tint(.inkOnPhotoLight) }
                        Text(submitting ? "Recording…" : "I understand and agree")
                            .font(.hearthTitleMD)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, .hearth500)
                    .background(canSubmit ? Color.accentDefault : Color.accentDefault.opacity(0.4))
                    .foregroundColor(.inkOnPhotoLight)
                    .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                }
                .disabled(!canSubmit || submitting)

                Text("Agreement version: \(agreementVersion)")
                    .font(.hearthCaptionMono)
                    .foregroundColor(.inkMuted)
                    .padding(.top, .hearth300)
            }
            .padding(.hearth600)
        }
        .background(Color.bgSober.ignoresSafeArea())
    }

    private var canSubmit: Bool {
        !parentName.trimmingCharacters(in: .whitespaces).isEmpty &&
        parentEmail.contains("@")
    }

    private func field(_ label: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text(label)
                .font(.hearthLabel)
                .foregroundColor(.inkMuted)
                .tracking(0.66)
                .textCase(.uppercase)
            TextField("", text: text)
                .padding(.hearth400)
                .background(Color.bgElevated)
                .foregroundColor(.inkPrimary)
                .font(.hearthBodyMD)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                        .stroke(Color.borderStrong, lineWidth: 1)
                )
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
