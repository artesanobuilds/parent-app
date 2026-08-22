import SwiftUI

/// Circle — beta-v1 sprint 2 redesign. Replaces the public community board
/// AND the 1:1 DM inbox with one surface: mutual-link GROUP conversations
/// scoped to a parent's own circle (grandparents, sitters, close friends).
///
/// Empty state is picked on ROSTER count, not conversation count — Circle-000
/// ("Gather your circle") when the household roster is empty, Circle-001
/// ("Start the conversation") when the roster is non-empty but there are no
/// conversations yet. These are deliberately different states.
struct CircleView: View {
    @EnvironmentObject private var contentVM: ContentViewModel
    // Unread count lives on AppSession — the tab-bar badge reads the SAME
    // value, so the two signal levels can never disagree.
    @EnvironmentObject private var session: AppSession

    @State private var conversations: [CircleConversation] = []
    @State private var roster: [HouseholdMember] = []
    /// Inbound pending "let me into your Circle" asks. Accepting one is what
    /// makes existing threads readable, so it sits above everything else.
    @State private var requests: [CircleRequest] = []
    /// Ids currently mid-accept/decline, so a double tap can't fire twice.
    @State private var answering: Set<String> = []
    @State private var loading = true
    @State private var errorMessage: String?
    @State private var showingNewConversation = false
    @State private var showingInvite = false
    @State private var showingAddToTeam: CircleConversation?
    @State private var pendingDelete: CircleConversation?
    @State private var navPath = NavigationPath()
    /// Bumped whenever a sheet that can mutate the roster dismisses, driving the
    /// `.task(id:)` re-fetch. A one-shot `.task` goes stale — that's the bug
    /// that kept a deleted kid on Home until relaunch.
    @State private var refreshToken = 0
    /// Personalizes Circle-000's subtitle ("…show up for {kids}…") — fetched
    /// once, best-effort. `CircleView` otherwise has no reason to know about
    /// kids at all, so this stays a one-shot local fetch rather than pulling
    /// the family profile into a shared store for one string.
    @State private var kidNames: [String] = []

    private var userID: String { contentVM.userId }
    private var baseURL: URL? { contentVM.baseURL }

    var body: some View {
        NavigationStack(path: $navPath) {
            VStack(spacing: 0) {
                // Requests sit ABOVE every other state, including the empty
                // ones: someone asking to join is the most actionable thing on
                // the screen, and a brand-new parent's first Circle event may
                // well be an inbound ask rather than anything they started.
                if !requests.isEmpty { requestsSection }
                Group {
                    if loading && conversations.isEmpty && roster.isEmpty {
                        ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else if roster.isEmpty {
                        // Requests render ABOVE this, so an inbound ask is
                        // visible even here — but the roster really is empty
                        // until one is accepted, and this is that state.
                        noCircleEmptyState
                    } else if conversations.isEmpty {
                        noConversationsEmptyState
                    } else {
                        conversationList
                    }
                }
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .navigationTitle("Circle")
            .navigationBarTitleDisplayMode(.inline)
            .toolbarBackground(Color.bgCanvas, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button {
                        showingInvite = true
                    } label: {
                        Image(systemName: "person.badge.plus")
                            .font(.system(size: 18, weight: .medium))
                            .foregroundColor(.inkPrimary)
                    }
                    .accessibilityLabel("Invite someone to your circle")
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showingNewConversation = true
                    } label: {
                        Image(systemName: "square.and.pencil")
                            .font(.system(size: 18, weight: .medium))
                            .foregroundColor(.accentOnCanvas)
                    }
                    .accessibilityLabel("New conversation")
                    .disabled(roster.isEmpty)
                }
            }
            .navigationDestination(for: String.self) { conversationId in
                CircleThreadView(conversationId: conversationId, userID: userID, baseURL: baseURL,
                                 onNotFound: {
                                     // A push for a conversation that no longer exists lands
                                     // back on the list rather than crashing.
                                     if !navPath.isEmpty { navPath.removeLast() }
                                 })
                    .environmentObject(session)
            }
            .sheet(isPresented: $showingNewConversation) {
                if let baseURL {
                    NewConversationView(userID: userID, baseURL: baseURL, roster: roster) { created in
                        showingNewConversation = false
                        conversations.insert(created, at: 0)
                        navPath.append(created.id)
                    }
                }
            }
            .sheet(isPresented: $showingInvite, onDismiss: { refreshToken += 1 }) {
                if let baseURL {
                    CircleInviteView(userID: userID, baseURL: baseURL,
                                     onRosterChanged: { refreshToken += 1 })
                }
            }
            .sheet(item: $showingAddToTeam) { conversation in
                if let baseURL {
                    AddToTeamSheet(conversation: conversation, userID: userID, baseURL: baseURL, roster: roster) { updated in
                        if let idx = conversations.firstIndex(where: { $0.id == updated.id }) {
                            conversations[idx] = updated
                        }
                        showingAddToTeam = nil
                    }
                }
            }
            .alert("Delete this conversation?", isPresented: Binding(
                get: { pendingDelete != nil }, set: { if !$0 { pendingDelete = nil } }
            )) {
                Button("Delete", role: .destructive) {
                    if let conversation = pendingDelete { Task { await delete(conversation) } }
                }
                Button("Cancel", role: .cancel) { pendingDelete = nil }
            } message: {
                Text("This removes it for everyone in the conversation.")
            }
            .refreshable { await load() }
            // Source-of-truth re-fetch on open AND on every token bump (a sheet
            // dismissing, a request answered). A one-shot `.task` goes stale.
            .task(id: refreshToken) { await load() }
            // One-shot — kid names only personalize copy, not a source of
            // truth this view otherwise needs to keep fresh.
            .task {
                guard let baseURL, kidNames.isEmpty else { return }
                if let profile = try? await ProfileService.getProfile(baseURL: baseURL, userID: userID) {
                    kidNames = (profile.children ?? [:]).values.compactMap { $0.name }.sorted()
                }
            }
            .onChange(of: session.pendingCircleConversationId) { _, pending in
                guard let pending else { return }
                session.pendingCircleConversationId = nil
                if navPath.isEmpty { navPath.append(pending) }
            }
            .onAppear {
                if let pending = session.pendingCircleConversationId {
                    session.pendingCircleConversationId = nil
                    if navPath.isEmpty { navPath.append(pending) }
                }
            }
            .trackScreen("circle_list")
        }
    }

    // MARK: - Inbound requests

    private var requestsSection: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text("Wants to join your circle")
                .font(.hearthLabel)
                .tracking(0.66)
                .textCase(.uppercase)
                .foregroundColor(.inkMuted)

            ForEach(requests) { request in
                requestRow(request)
            }
        }
        .padding(.horizontal, .hearth500)
        .padding(.top, .hearth500)
        .padding(.bottom, .hearth400)
    }

    private func requestRow(_ request: CircleRequest) -> some View {
        HStack(spacing: .hearth400) {
            Circle()
                .fill(Color.inkPrimary)
                .frame(width: 36, height: 36)
                .overlay(
                    Text(request.initials)
                        .font(.hearthTitleMD)
                        .foregroundColor(.inkOnPhotoLight)
                )
            VStack(alignment: .leading, spacing: 2) {
                Text(request.fromName)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkPrimary)
                    .lineLimit(1)
                Text("Asked to connect")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
            }
            Spacer(minLength: .hearth300)
            if answering.contains(request.id) {
                ProgressView()
            } else {
                Button("Accept") { Task { await respond(request, accept: true) } }
                    .font(.hearthBodySMBold)
                    .foregroundColor(.inkOnPhotoLight)
                    .padding(.horizontal, .hearth400)
                    .padding(.vertical, 6)
                    .background(Capsule().fill(Color.accentDefault))
                    .buttonStyle(.plain)
                Button("Decline") { Task { await respond(request, accept: false) } }
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
                    .buttonStyle(.plain)
            }
        }
        .padding(.hearth500)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
        .hearthCardElevation()
    }

    // MARK: - Empty states

    /// Circle-000 — the roster itself is empty. Measured `754:5810`: hero is
    /// the SAME family-figures vector as the CIRCLE tab icon (component
    /// `19:68`) scaled to 86×71 — not an SF Symbol; title is the Fraunces
    /// display treatment (38/40, -1% tracking), not a body-tier title; body
    /// copy is full ink `#1E1E1E`, not muted gray; button is a fixed 238×46
    /// centered pill (r=12), not full-width.
    private var noCircleEmptyState: some View {
        VStack(spacing: 15) {
            Spacer()
            Image("TabIcon-circle")
                .renderingMode(.template)
                .resizable()
                .scaledToFit()
                .frame(width: 86, height: 71)
                .foregroundColor(.accentDefault)
            Text("Gather your circle")
                .font(.hearthDisplaySM)
                .tracking(-0.38)
                .foregroundColor(.inkPrimary)
                .multilineTextAlignment(.center)
            Text(circleSubtitle)
                .font(.hearthBodyMD)
                .foregroundColor(.inkPrimary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, .hearth800)
            Button { showingInvite = true } label: {
                Text("Invite someone")
                    .font(.hearthSectionHeader)
                    .foregroundColor(.inkOnPhotoLight)
                    .frame(width: 238)
                    .padding(.vertical, .hearth500)
                    .background(Color.accentDefault)
                    .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous))
            }
            .padding(.top, .hearth300)
            Spacer()
            Spacer()
        }
    }

    private var circleSubtitle: String {
        switch kidNames.count {
        case 0:
            return "Your circle are the people who show up for your kids — grandparents, sitters, close friends. Bring them into one place."
        case 1:
            return "Your circle are the people who show up for \(kidNames[0]) — grandparents, sitters, close friends. Bring them into one place."
        default:
            let names = kidNames.dropLast().joined(separator: ", ") + " & " + kidNames.last!
            return "Your circle are the people who show up for \(names) — grandparents, sitters, close friends. Bring them into one place."
        }
    }

    /// Circle-001 — roster exists, no conversations yet.
    private var noConversationsEmptyState: some View {
        VStack(spacing: .hearth500) {
            Spacer()
            Image(systemName: "bubble.left.and.bubble.right")
                .font(.system(size: 48, weight: .light))
                .foregroundColor(.inkMuted)
            Text("Start the conversation")
                .font(.hearthTitleLG)
                .foregroundColor(.inkPrimary)
            Text("Ask your circle for advice, share a win, or just check in.")
                .font(.hearthBodyMD)
                .foregroundColor(.inkMuted)
                .multilineTextAlignment(.center)
                .padding(.horizontal, .hearth800)
            Button { showingNewConversation = true } label: {
                Text("Start a discussion")
                    .font(.hearthTitleMD)
                    .foregroundColor(.inkOnPhotoLight)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, .hearth500)
                    .background(Color.accentDefault)
                    .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusButton, style: .continuous))
            }
            .padding(.horizontal, .hearth700)
            .padding(.top, .hearth300)
            Spacer()
            Spacer()
        }
    }

    // MARK: - List

    private var conversationList: some View {
        ScrollView {
            LazyVStack(spacing: .hearth400) {
                if let errorMessage {
                    Text(errorMessage).font(.hearthBodySM).foregroundColor(.statusError)
                }
                ForEach(conversations) { conversation in
                    Button {
                        navPath.append(conversation.id)
                    } label: {
                        CircleConversationRow(conversation: conversation, userID: userID)
                    }
                    .buttonStyle(.plain)
                    .contextMenu { rowMenu(conversation) }
                    .overlay(alignment: .topTrailing) {
                        Menu { rowMenu(conversation) } label: {
                            Image(systemName: "ellipsis")
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundColor(.inkMuted)
                                .frame(width: 32, height: 32)
                        }
                        .accessibilityLabel("Conversation options")
                    }
                }
            }
            .padding(.horizontal, .hearth500)
            .padding(.vertical, .hearth500)
        }
    }

    @ViewBuilder
    private func rowMenu(_ conversation: CircleConversation) -> some View {
        if conversation.isOwned(by: userID) {
            Button("Edit") { navPath.append(conversation.id) }
            Button("Delete", role: .destructive) { pendingDelete = conversation }
        }
        Button("Send message") { navPath.append(conversation.id) }
        Button("Add to team") { showingAddToTeam = conversation }
    }

    // MARK: - Actions

    private func load() async {
        guard let baseURL, !userID.isEmpty else { loading = false; return }
        loading = true
        defer { loading = false }
        async let fetchedRoster = try? CircleService.householdMembers(userID: userID, baseURL: baseURL)
        async let fetchedConversations = try? CircleService.conversations(userID: userID, baseURL: baseURL)
        async let fetchedRequests = try? CircleService.requests(userID: userID, baseURL: baseURL)
        roster = (await fetchedRoster) ?? roster
        requests = (await fetchedRequests) ?? requests
        if let convos = await fetchedConversations {
            conversations = convos
            errorMessage = nil
        } else {
            errorMessage = "Couldn't load Circle. Pull to retry."
        }
        await session.refreshCircleUnread(userID: userID, baseURL: baseURL)
    }

    /// Accept or decline an inbound request.
    ///
    /// Accepting is what binds the mutual link, so it refreshes BOTH the roster
    /// and the conversation list — existing threads only become readable at that
    /// moment. A 409 means somebody already answered it (another device, a
    /// double tap): that is a stale list, not an error, so it refreshes silently
    /// rather than alerting.
    private func respond(_ request: CircleRequest, accept: Bool) async {
        guard let baseURL, !answering.contains(request.id) else { return }
        answering.insert(request.id)
        defer { answering.remove(request.id) }
        do {
            _ = try await CircleService.respondToRequest(
                id: request.id, accept: accept, userID: userID, baseURL: baseURL
            )
            Analytics.capture(accept ? "circle_request_accepted" : "circle_request_declined", [:])
            errorMessage = nil
        } catch let error as CircleService.CircleServiceError
                    where error.isAlreadyAnswered || error.isNotFound {
            // Already answered, or gone. Nothing is wrong — just re-read.
        } catch {
            errorMessage = accept
                ? "Couldn't accept that request. Try again."
                : "Couldn't decline that request. Try again."
            return
        }
        // The re-fetch is the source of truth for all three lists, so nothing
        // here mutates local state optimistically.
        refreshToken += 1
    }

    private func delete(_ conversation: CircleConversation) async {
        guard let baseURL else { return }
        pendingDelete = nil
        do {
            try await CircleService.deleteConversation(id: conversation.id, userID: userID, baseURL: baseURL)
            conversations.removeAll { $0.id == conversation.id }
            Analytics.capture("circle_conversation_deleted", [:])
        } catch {
            errorMessage = "Couldn't delete that conversation. Try again."
        }
    }
}

// MARK: - Row

struct CircleConversationRow: View {
    let conversation: CircleConversation
    let userID: String

    private var subtitle: String {
        let count = conversation.replyCount ?? 0
        let word = count == 1 ? "reply" : "replies"
        if conversation.starterIsMe ?? true {
            if let from = conversation.lastReplyFrom, count > 0 {
                return "\(count) \(word) · last from \(from)"
            }
            return count > 0 ? "\(count) \(word)" : "No replies yet"
        } else {
            let starter = conversation.starterName ?? "Someone"
            return count > 0 ? "\(starter) started this — \(count) \(word)" : "\(starter) started this"
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text(conversation.title)
                .font(.hearthTitleMD)
                .foregroundColor(.inkPrimary)
                .lineLimit(1)
                .padding(.trailing, 32)   // room for the overlaid ⋯ menu

            Text(subtitle)
                .font(.hearthBodySM)
                .foregroundColor(.inkMuted)

            avatarStack
        }
        // Measured (sprint-2 `Frame 204973796/797` conversation cards): pad 9,
        // r12 — `hearth300` (8) and `hearthRadiusMd` are the nearest reachable
        // steps. The shipped card used `hearth500` (16) / `hearthRadiusLg`
        // (20), a noticeably airier, rounder card than the frame draws.
        .padding(.hearth300)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
        .hearthCardElevation()
    }

    private var avatarStack: some View {
        HStack(spacing: -10) {
            ForEach(Array((conversation.participants ?? []).prefix(4).enumerated()), id: \.element.id) { pair in
                Circle()
                    .fill(Color.accentTint)
                    .frame(width: 28, height: 28)
                    .overlay(
                        Text(pair.element.initials)
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(.accentOnCanvas)
                    )
                    .overlay(Circle().stroke(Color.bgElevated, lineWidth: 2))
                    .zIndex(Double(-pair.offset))
            }
        }
    }
}

// MARK: - "Add to team" sheet (row context menu → participant picker)

/// Adds household roster members to an EXISTING conversation. Reuses the same
/// checklist idiom as `NewConversationView`'s invite list, scoped to members
/// not already participating.
struct AddToTeamSheet: View {
    let conversation: CircleConversation
    let userID: String
    let baseURL: URL
    let roster: [HouseholdMember]
    var onUpdated: (CircleConversation) -> Void

    @State private var selected: Set<String> = []
    @State private var saving = false
    @Environment(\.dismiss) private var dismiss

    private var alreadyIn: Set<String> {
        Set((conversation.participants ?? []).map(\.memberId))
    }
    private var candidates: [HouseholdMember] { roster.filter { !alreadyIn.contains($0.id) } }

    var body: some View {
        NavigationStack {
            Group {
                if candidates.isEmpty {
                    Text("Everyone in your circle is already in this conversation.")
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkMuted)
                        .multilineTextAlignment(.center)
                        .padding(.hearth700)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List(candidates) { member in
                        Button {
                            if selected.contains(member.id) { selected.remove(member.id) }
                            else { selected.insert(member.id) }
                        } label: {
                            HStack(spacing: .hearth400) {
                                Circle()
                                    .fill(Color.accentTint)
                                    .frame(width: 36, height: 36)
                                    .overlay(Text(member.resolvedInitials).font(.hearthLabel).foregroundColor(.accentOnCanvas))
                                Text(member.displayName).font(.hearthBodyMD).foregroundColor(.inkPrimary)
                                Spacer()
                                if selected.contains(member.id) {
                                    Image(systemName: "checkmark.circle.fill").foregroundColor(.accentDefault)
                                }
                            }
                        }
                    }
                    .listStyle(.plain)
                }
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .navigationTitle("Add to team")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button(saving ? "Adding…" : "Add") { Task { await add() } }
                        .disabled(selected.isEmpty || saving)
                }
            }
        }
    }

    private func add() async {
        saving = true
        defer { saving = false }
        if let updated = try? await CircleService.addParticipants(
            conversationId: conversation.id, memberIds: Array(selected), userID: userID, baseURL: baseURL
        ) {
            onUpdated(updated)
            dismiss()
        }
    }
}
