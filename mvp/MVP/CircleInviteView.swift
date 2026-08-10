import SwiftUI

/// Invite flow ("invite preview" frames). Ships "Copy link to invite" +
/// share-preview card, an "add contact" entry that goes through
/// `POST /circle/contacts`, and a way into the full Contacts screen.
/// CSV import and the LinkedIn connect button are drawn in the frames and
/// explicitly NOT rendered — a control that does nothing reads as broken.
struct CircleInviteView: View {
    let userID: String
    let baseURL: URL
    /// Bubbled up so the presenting surface re-fetches its roster after a
    /// contact is added here (CLAUDE.md: after a mutation the source-of-truth
    /// view re-fetches).
    var onRosterChanged: () -> Void = {}

    @State private var invite: CircleInvite?
    @State private var creating = false
    @State private var errorMessage: String?
    @State private var copied = false
    @State private var showingAddContact = false
    @State private var showingContacts = false
    /// The single identical confirmation from `POST /circle/contacts` — see
    /// `AddContactSheet`. Never personalised with what the server "found".
    @State private var contactNotice: String?
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

                    tile(symbol: "person.crop.circle.badge.plus", label: "add contact",
                         chevron: false) { showingAddContact = true }

                    tile(symbol: "person.2", label: "See all contacts",
                         chevron: true) { showingContacts = true }

                    if let contactNotice { noticeBanner(contactNotice) }

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
            .sheet(isPresented: $showingAddContact) {
                AddContactSheet(userID: userID, baseURL: baseURL) { message in
                    contactNotice = message
                    onRosterChanged()
                }
            }
            .sheet(isPresented: $showingContacts) {
                CircleContactsView(userID: userID, baseURL: baseURL,
                                   onRosterChanged: onRosterChanged)
            }
            .task { await ensureInvite() }
            .trackScreen("circle_invite")
        }
    }

    /// One tappable row in the `invite preview` action list. Extracted so the
    /// body stays short (SwiftUI's "unable to type-check in reasonable time" is
    /// usually an over-long body).
    @ViewBuilder
    private func tile(symbol: String, label: String, chevron: Bool,
                      action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: .hearth400) {
                Image(systemName: symbol)
                    .foregroundColor(.accentOnCanvas)
                Text(label)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkPrimary)
                Spacer()
                if chevron {
                    Image(systemName: "chevron.right")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.inkSecondary)
                }
            }
            .padding(.hearth500)
            .background(Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    private func noticeBanner(_ message: String) -> some View {
        Text(message)
            .font(.hearthBodySM)
            .foregroundColor(.inkPrimary)
            .padding(.hearth400)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                    .fill(Color.bgCard)
            )
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

}
