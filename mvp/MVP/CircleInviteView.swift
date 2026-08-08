import SwiftUI

/// Invite flow ("invite preview" frames). Ships "Copy link to invite" +
/// share-preview card and a manual "add contact" entry. CSV import and the
/// LinkedIn connect button are explicitly OUT of scope for this pass.
struct CircleInviteView: View {
    let userID: String
    let baseURL: URL

    @State private var invite: CircleInvite?
    @State private var creating = false
    @State private var errorMessage: String?
    @State private var copied = false
    @State private var showingAddContact = false
    @State private var contactName = ""
    @State private var addedContacts: [String] = []
    @Environment(\.dismiss) private var dismiss

    private var inviterName: String {
        let stored = UserDefaults.standard.string(forKey: "parent_display_name") ?? ""
        return stored.isEmpty ? "Your friend" : stored
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: .hearth600) {
                    VStack(alignment: .leading, spacing: .hearth300) {
                        Text("Add contacts")
                            .font(.hearthTitleLG)
                            .foregroundColor(.inkPrimary)
                        Text("Bring someone into your circle by link, or add them manually.")
                            .font(.hearthBodyMD)
                            .foregroundColor(.inkMuted)
                    }

                    Button {
                        showingAddContact = true
                    } label: {
                        HStack(spacing: .hearth400) {
                            Image(systemName: "person.crop.circle.badge.plus")
                                .foregroundColor(.accentOnCanvas)
                            Text("add contact")
                                .font(.hearthBodyMD)
                                .foregroundColor(.inkPrimary)
                            Spacer()
                        }
                        .padding(.hearth500)
                        .background(Color.bgElevated)
                        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                    }

                    if !addedContacts.isEmpty {
                        VStack(alignment: .leading, spacing: .hearth300) {
                            ForEach(addedContacts, id: \.self) { name in
                                HStack(spacing: .hearth400) {
                                    Circle()
                                        .fill(Color.accentTint)
                                        .frame(width: 32, height: 32)
                                        .overlay(Text(initials(for: name)).font(.hearthLabel).foregroundColor(.accentOnCanvas))
                                    Text(name).font(.hearthBodyMD).foregroundColor(.inkPrimary)
                                    Spacer()
                                    Text("Invited").font(.hearthBodySM).foregroundColor(.statusSuccess)
                                }
                            }
                        }
                    }

                    Divider().background(Color.borderHairline)

                    linkSection

                    if let errorMessage {
                        Text(errorMessage).font(.hearthBodySM).foregroundColor(.statusError)
                    }
                }
                .padding(.hearth700)
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .navigationTitle("Circle")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .alert("Add contact", isPresented: $showingAddContact) {
                TextField("Contact name", text: $contactName)
                Button("Add") { Task { await addContact() } }
                Button("Cancel", role: .cancel) { contactName = "" }
            } message: {
                Text("We'll generate a personal invite link for them.")
            }
            .task { await ensureInvite() }
            .trackScreen("circle_invite")
        }
    }

    private var linkSection: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            Button {
                Task { await copyLink() }
            } label: {
                HStack(spacing: .hearth400) {
                    Image(systemName: "link")
                        .foregroundColor(.accentOnCanvas)
                    Text(copied ? "Copied!" : "Copy link to invite")
                        .font(.hearthBodyMD.weight(.semibold))
                        .foregroundColor(.inkPrimary)
                    Spacer()
                    if creating { ProgressView() }
                }
                .padding(.hearth500)
                .background(Color.bgElevated)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
            }
            .disabled(creating)

            // Share-preview card — mirrors the invite-preview frame's link
            // card (domain + personalized message).
            if let invite {
                VStack(alignment: .leading, spacing: .hearth300) {
                    Text(invite.url)
                        .font(.hearthBodySM)
                        .foregroundColor(.accentOnCanvas)
                        .lineLimit(1)
                        .truncationMode(.middle)
                    Text("\(inviterName) wants you in their circle on MVP")
                        .font(.hearthBodyMD.weight(.semibold))
                        .foregroundColor(.inkPrimary)
                    Text("\(inviterName) wants you in their circle — a place to share what works for the kids.")
                        .font(.hearthBodySM)
                        .foregroundColor(.inkMuted)
                    Text("MVP")
                        .font(.hearthCaptionMono)
                        .foregroundColor(.inkMuted)
                }
                .padding(.hearth500)
                .background(Color.bgSober)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))

                ShareLink(item: URL(string: invite.url) ?? baseURL,
                         subject: Text("Join my circle on MVP"),
                         message: Text("\(inviterName) invited you to their circle on MVP")) {
                    Label("Share invite", systemImage: "square.and.arrow.up")
                        .font(.hearthBodyMD)
                        .foregroundColor(.accentOnCanvas)
                }
            }
        }
    }

    private func initials(for name: String) -> String {
        let parts = name.split(separator: " ")
        let letters = parts.prefix(2).compactMap { $0.first }
        return letters.isEmpty ? "?" : String(letters).uppercased()
    }

    private func ensureInvite() async {
        guard invite == nil else { return }
        creating = true
        defer { creating = false }
        invite = try? await CircleService.createInvite(userID: userID, baseURL: baseURL)
        if invite == nil { errorMessage = "Couldn't create an invite link. Try again." }
    }

    private func copyLink() async {
        if invite == nil { await ensureInvite() }
        guard let invite else { return }
        UIPasteboard.general.string = invite.url
        Analytics.capture("circle_invite_link_copied", [:])
        withAnimation(.hearthFast) { copied = true }
        try? await Task.sleep(nanoseconds: 1_500_000_000)
        withAnimation(.hearthFast) { copied = false }
    }

    /// Generates a personalized invite for a manually-added contact. There is
    /// no backend endpoint yet to persist a named household member from iOS
    /// (`/circle/invites` only accepts an OPTIONAL existing `member_id`), so
    /// this mints a fresh link and tracks the name locally for this sheet's
    /// lifetime — the recipient still lands on the same claim flow.
    private func addContact() async {
        let name = contactName.trimmingCharacters(in: .whitespacesAndNewlines)
        contactName = ""
        guard !name.isEmpty else { return }
        if let created = try? await CircleService.createInvite(userID: userID, baseURL: baseURL) {
            invite = created
            addedContacts.append(name)
            Analytics.capture("circle_invite_contact_added", [:])
        }
    }
}
