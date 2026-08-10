import SwiftUI

// Contacts (beta-v1 sprint 2, Greg's `contacts` + `invite preview` frames).
//
// The address book behind Circle: everyone on the household roster, whether or
// not the link is mutual yet. Rows open `MemberProfileSheet`; the ⋯ menu shares
// a personal invite link; multi-select mints links for several people at once.
//
// TWO copy rules this screen exists to hold:
//
//  1. `POST /circle/contacts` answers 200 `{"status":"sent"}` on EVERY path —
//     matched, unmatched, yourself, already-a-peer, duplicate. The UI says the
//     SAME honest thing every time. Branching the copy ("Greg is already on
//     MVP!") would turn the route into an email-enumeration oracle, which is
//     precisely what its one-shape response is designed to prevent.
//
//  2. A pending contact is told apart from a connected one by the SERVER's
//     `in_circle` boolean (see `HouseholdMember.isConnected`), never by parsing
//     the roster row's `notes` prose — and the two pending paths (a request sent
//     to an existing account vs. an email invite) render IDENTICALLY, for the
//     same reason as rule 1.
//
// "Import CSV" and "Connect to LinkedIn" are drawn in the frames and are
// deliberately NOT rendered: a control that does nothing reads as a broken app.

struct CircleContactsView: View {
    let userID: String
    let baseURL: URL

    /// Called after any mutation (contact added, member edited, member removed)
    /// so the presenting surface's source-of-truth re-fetches rather than going
    /// stale — the `.task(id:)` token rule from CLAUDE.md.
    var onRosterChanged: () -> Void = {}

    @State private var members: [HouseholdMember] = []
    @State private var loading = true
    @State private var errorMessage: String?
    @State private var notice: String?

    @State private var selecting = false
    @State private var selected: Set<String> = []

    @State private var showingAdd = false
    @State private var editing: HouseholdMember?
    @State private var pendingRemove: HouseholdMember?
    @State private var shareLinks: ContactShareLinks?
    @State private var working = false
    /// Bumped on every mutation + on sheet dismissal, driving `.task(id:)`.
    @State private var refreshToken = 0

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if selecting { inviteSelectedBar }
                ScrollView {
                    VStack(alignment: .leading, spacing: .hearth500) {
                        headerRow
                        if let notice { noticeBanner(notice) }
                        if let errorMessage {
                            Text(errorMessage)
                                .font(.hearthBodySM)
                                .foregroundColor(.statusError)
                        }
                        if loading && members.isEmpty {
                            ProgressView().frame(maxWidth: .infinity)
                        } else if members.isEmpty {
                            emptyState
                        } else {
                            contactList
                        }
                        addContactAction
                        copyLinkAction
                    }
                    .padding(.horizontal, .hearth600)
                    .padding(.vertical, .hearth600)
                }
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .navigationTitle("Circle")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Done") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) { selectToggle }
            }
            .sheet(isPresented: $showingAdd) {
                AddContactSheet(userID: userID, baseURL: baseURL) { message in
                    notice = message
                    bumpAndNotify()
                }
            }
            .sheet(item: $editing, onDismiss: { bumpAndNotify() }) { member in
                MemberProfileSheet(userID: userID, baseURL: baseURL, memberId: member.id,
                                   member: member)
            }
            .sheet(item: $shareLinks) { payload in
                ContactShareSheet(payload: payload)
            }
            .alert("Remove this contact?", isPresented: Binding(
                get: { pendingRemove != nil }, set: { if !$0 { pendingRemove = nil } }
            )) {
                Button("Remove", role: .destructive) {
                    if let member = pendingRemove { Task { await remove(member) } }
                }
                Button("Cancel", role: .cancel) { pendingRemove = nil }
            } message: {
                Text("They stay in any conversation they've already joined. You can add them again by email.")
            }
            .refreshable { await load() }
            .task(id: refreshToken) { await load() }
            .trackScreen("circle_contacts")
        }
    }

    // MARK: - Header + toolbar

    private var headerRow: some View {
        HStack(spacing: .hearth400) {
            Text("Contacts")
                .font(.hearthTitleLG)
                .foregroundColor(.inkPrimary)
            Spacer()
            Button { showingAdd = true } label: {
                HStack(spacing: 6) {
                    Text("Add")
                        .font(.hearthBodySMBold)
                        .foregroundColor(.inkPrimary)
                    Image(systemName: "plus.circle")
                        .font(.system(size: 18, weight: .regular))
                        .foregroundColor(.accentOnCanvas)
                }
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Add a contact")
        }
    }

    @ViewBuilder
    private var selectToggle: some View {
        if members.isEmpty {
            EmptyView()
        } else {
            Button(selecting ? "Cancel" : "Select") {
                selecting.toggle()
                if !selecting { selected.removeAll() }
            }
            .font(.hearthBodyMD)
            .foregroundColor(.accentOnCanvas)
        }
    }

    /// The frames' grey "Invite selected" bar — enabled only once something is
    /// selected, so it never sits there looking tappable and doing nothing.
    private var inviteSelectedBar: some View {
        Button {
            Task { await inviteSelected() }
        } label: {
            Text(working ? "Preparing…" : "Invite selected")
                .font(.hearthButtonLabel)
                .foregroundColor(.inkOnPhotoLight)
                .frame(maxWidth: .infinity)
                .padding(.vertical, .hearth400)
                .background(
                    RoundedRectangle(cornerRadius: .hearthRadiusButton, style: .continuous)
                        .fill(selected.isEmpty || working ? Color.bgDisabled : Color.accentDefault)
                )
        }
        .buttonStyle(.plain)
        .disabled(selected.isEmpty || working)
        .padding(.horizontal, .hearth600)
        .padding(.vertical, .hearth400)
        .background(Color.bgCard)
    }

    // MARK: - List

    /// The 1px-stroked list from the frame. One stroke around the whole block,
    /// hairlines between rows.
    private var contactList: some View {
        VStack(spacing: 0) {
            ForEach(Array(members.enumerated()), id: \.element.id) { index, member in
                if index > 0 {
                    Rectangle().fill(Color.borderHairline).frame(height: 1)
                }
                contactRow(member)
            }
        }
        .overlay(
            RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                .stroke(Color.borderHairline, lineWidth: 1)
        )
    }

    private func contactRow(_ member: HouseholdMember) -> some View {
        HStack(spacing: .hearth400) {
            if selecting {
                Image(systemName: selected.contains(member.id) ? "checkmark.circle.fill" : "circle")
                    .foregroundColor(selected.contains(member.id) ? .accentDefault : .inkPlaceholder)
            }
            avatar(member)
            Button {
                if selecting { toggle(member) } else { editing = member }
            } label: {
                VStack(alignment: .leading, spacing: 2) {
                    Text(member.displayName)
                        .font(.hearthBodyMD)
                        .foregroundColor(.accentOnCanvas)
                        .lineLimit(1)
                    if member.isPending { pendingChip }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            rowMenu(member)
        }
        .padding(.horizontal, .hearth500)
        .padding(.vertical, .hearth400)
    }

    private func avatar(_ member: HouseholdMember) -> some View {
        Circle()
            .fill(Color.inkPrimary)
            .frame(width: 36, height: 36)
            .overlay(
                Text(member.resolvedInitials)
                    .font(.hearthTitleMD)
                    .foregroundColor(.inkOnPhotoLight)
            )
            // Pending contacts read as lighter-weight without a second colour:
            // the same treatment for BOTH pending paths (request sent / invited).
            .opacity(member.isPending ? 0.55 : 1)
    }

    /// One chip for both pending paths, on purpose. It says what's true without
    /// saying whether the person was found on MVP.
    private var pendingChip: some View {
        Text("Waiting on them")
            .font(.hearthLabel)
            .tracking(0.66)
            .textCase(.uppercase)
            .foregroundColor(.inkMuted)
    }

    @ViewBuilder
    private func rowMenu(_ member: HouseholdMember) -> some View {
        Menu {
            Button("Edit profile") { editing = member }
            Button("Copy link to invite") { Task { await copyLink(for: member) } }
            Button("Remove from contacts", role: .destructive) { pendingRemove = member }
        } label: {
            Image(systemName: "ellipsis")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.inkMuted)
                .frame(width: 36, height: 36)
        }
        .accessibilityLabel("Options for \(member.displayName)")
    }

    private var emptyState: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text("No contacts yet")
                .font(.hearthTitleMD)
                .foregroundColor(.inkPrimary)
            Text("Add the people who show up for your kids — by email, or by sharing your invite link.")
                .font(.hearthBodyMD)
                .foregroundColor(.inkMuted)
        }
        .padding(.vertical, .hearth500)
    }

    // MARK: - Actions from the `invite preview` frame

    private var addContactAction: some View {
        Button { showingAdd = true } label: {
            HStack(spacing: .hearth400) {
                Image(systemName: "person.crop.circle.badge.plus")
                    .foregroundColor(.accentOnCanvas)
                Text("add contact")
                    .font(.hearthBodyMD)
                    .foregroundColor(.accentOnCanvas)
                Spacer()
            }
        }
        .buttonStyle(.plain)
    }

    private var copyLinkAction: some View {
        Button { Task { await copyLink(for: nil) } } label: {
            HStack(spacing: .hearth400) {
                Image(systemName: "link")
                    .foregroundColor(.accentOnCanvas)
                Text("Copy link to invite")
                    .font(.hearthBodyMD)
                    .foregroundColor(.accentOnCanvas)
                Spacer()
                if working { ProgressView() }
            }
        }
        .buttonStyle(.plain)
        .disabled(working)
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

    // MARK: - Behaviour

    private func toggle(_ member: HouseholdMember) {
        if selected.contains(member.id) { selected.remove(member.id) }
        else { selected.insert(member.id) }
    }

    private func bumpAndNotify() {
        refreshToken += 1
        onRosterChanged()
    }

    private func load() async {
        guard !userID.isEmpty else { loading = false; return }
        loading = true
        defer { loading = false }
        do {
            members = try await CircleService.householdMembers(userID: userID, baseURL: baseURL)
            errorMessage = nil
        } catch {
            errorMessage = "Couldn't load your contacts. Pull to retry."
        }
        selected = selected.intersection(Set(members.map(\.id)))
    }

    /// A shareable URL for ONE roster row. `POST /circle/contacts` deliberately
    /// returns no URL (present on one branch, absent on the other, would be the
    /// tell), so the link is fetched here, when the parent asks to share it.
    private func copyLink(for member: HouseholdMember?) async {
        working = true
        defer { working = false }
        guard let invite = try? await CircleService.createInvite(
            memberId: member?.id, userID: userID, baseURL: baseURL
        ) else {
            errorMessage = "Couldn't create an invite link. Try again."
            return
        }
        UIPasteboard.general.string = invite.url
        Analytics.capture("circle_invite_link_copied", [:])
        if let member {
            notice = "Invite link for \(member.displayName) copied."
        } else {
            notice = "Invite link copied."
        }
    }

    /// One personal link per selected contact, handed to the system share sheet
    /// as a single message. Sequential rather than concurrent: each is a write
    /// (it mints a token server-side) and a partial failure must be visible.
    private func inviteSelected() async {
        working = true
        defer { working = false }
        var lines: [String] = []
        var failed = 0
        for member in members where selected.contains(member.id) {
            if let invite = try? await CircleService.createInvite(
                memberId: member.id, userID: userID, baseURL: baseURL
            ) {
                lines.append("\(member.displayName): \(invite.url)")
            } else {
                failed += 1
            }
        }
        guard !lines.isEmpty else {
            errorMessage = "Couldn't create those invite links. Try again."
            return
        }
        errorMessage = failed > 0
            ? "\(failed) link\(failed == 1 ? "" : "s") couldn't be created — try those again."
            : nil
        Analytics.capture("circle_invite_selected", ["count": lines.count])
        shareLinks = ContactShareLinks(text: lines.joined(separator: "\n"))
        selecting = false
        selected.removeAll()
    }

    private func remove(_ member: HouseholdMember) async {
        pendingRemove = nil
        do {
            try await CircleService.deleteMember(id: member.id, userID: userID, baseURL: baseURL)
            members.removeAll { $0.id == member.id }
            selected.remove(member.id)
            bumpAndNotify()
        } catch {
            errorMessage = "Couldn't remove \(member.displayName). Try again."
        }
    }
}

// MARK: - Multi-invite share payload

/// Identifiable so it can drive `.sheet(item:)` — a plain String can't.
struct ContactShareLinks: Identifiable {
    let id = UUID()
    let text: String
}

private struct ContactShareSheet: View {
    let payload: ContactShareLinks
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: .hearth500) {
                Text("Personal invite links")
                    .font(.hearthTitleLG)
                    .foregroundColor(.inkPrimary)
                Text(payload.text)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
                    .textSelection(.enabled)
                ShareLink(item: payload.text) {
                    Label("Share", systemImage: "square.and.arrow.up")
                        .font(.hearthBodyMD)
                        .foregroundColor(.accentOnCanvas)
                }
                Spacer()
            }
            .padding(.hearth700)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.bgCanvas.ignoresSafeArea())
            .toolbar {
                ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } }
            }
        }
    }
}

// MARK: - Add contact by email

/// `POST /circle/contacts`. The confirmation copy is IDENTICAL on every
/// outcome — see the file header. Only a malformed email (the endpoint's one
/// 400) produces a different message, and that's about the input, not about
/// whether the person exists.
struct AddContactSheet: View {
    let userID: String
    let baseURL: URL
    /// Handed the confirmation line to show on the contacts screen.
    var onSent: (String) -> Void

    @State private var email = ""
    @State private var name = ""
    @State private var sending = false
    @State private var error: String?
    @Environment(\.dismiss) private var dismiss

    private var canSend: Bool {
        let trimmed = email.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.contains("@") && !trimmed.hasPrefix("@") && !sending
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Email", text: $email)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.emailAddress)
                        .autocorrectionDisabled()
                    TextField("Name (optional)", text: $name)
                } footer: {
                    Text("We'll ask them to join your circle. If they're not on MVP yet, they'll get an invite instead.")
                        .font(.hearthBodySM)
                        .foregroundColor(.inkMuted)
                }
                if let error {
                    Text(error).font(.hearthBodySM).foregroundColor(.statusError)
                }
            }
            .scrollContentBackground(.hidden)
            .background(Color.bgCanvas.ignoresSafeArea())
            .navigationTitle("Add contact")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button(sending ? "Sending…" : "Send") { Task { await send() } }
                        .disabled(!canSend)
                }
            }
            .trackScreen("circle_add_contact")
        }
    }

    private func send() async {
        sending = true
        defer { sending = false }
        error = nil
        let trimmedEmail = email.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedName = name.trimmingCharacters(in: .whitespacesAndNewlines)
        do {
            _ = try await CircleService.addContact(
                email: trimmedEmail,
                displayName: trimmedName.isEmpty ? nil : trimmedName,
                userID: userID, baseURL: baseURL
            )
            Analytics.capture("circle_contact_requested", [:])
            // ONE sentence for every outcome. Do not personalise it with what
            // the server "found" — it deliberately doesn't tell us.
            onSent("Request sent. If they're on MVP they'll see it in their Circle; otherwise share the invite link with them.")
            dismiss()
        } catch let serviceError as CircleService.CircleServiceError where serviceError.isBadRequest {
            error = "That email doesn't look right. Check it and try again."
        } catch {
            self.error = "Couldn't send that. Check your connection and try again."
        }
    }
}
