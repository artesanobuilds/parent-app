import SwiftUI

/// A Circle conversation thread (Circle-003 / Circle-004): the original post,
/// replies with an initial avatar + a per-reply "Reply" affordance, and a
/// composer at the bottom. Fetches by id so it can be pushed directly from a
/// deep link without the caller already holding the full `CircleConversation`.
struct CircleThreadView: View {
    let conversationId: String
    let userID: String
    let baseURL: URL?
    /// Called when the fetch 404s — a stale push deep link lands back on the
    /// Circle list instead of crashing into a dead thread.
    var onNotFound: () -> Void = {}

    @State private var conversation: CircleConversation?
    @State private var messages: [CircleMessage] = []
    @State private var loading = true
    @State private var draft = ""
    @State private var sending = false
    @State private var errorMessage: String?
    @State private var pendingDelete = false
    @State private var showingEdit = false
    @State private var showingAddToTeam = false
    @State private var roster: [HouseholdMember] = []
    @FocusState private var composerFocused: Bool
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 0) {
            if loading && conversation == nil {
                ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if let conversation {
                threadBody(conversation)
            } else {
                Text(errorMessage ?? "This conversation isn't available.")
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkMuted)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .background(Color.bgCanvas.ignoresSafeArea())
        .navigationTitle(conversation?.title ?? "Circle")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            if let conversation {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        if conversation.isOwned(by: userID) {
                            Button("Edit") { showingEdit = true }
                            Button("Delete", role: .destructive) { pendingDelete = true }
                        }
                        Button("Add to team") {
                            Task { await loadRosterThenPresent() }
                        }
                    } label: {
                        Image(systemName: "ellipsis").foregroundColor(.inkPrimary)
                    }
                    .accessibilityLabel("Conversation options")
                }
            }
        }
        .sheet(isPresented: $showingEdit) {
            if let conversation, let baseURL {
                EditConversationSheet(conversation: conversation, userID: userID, baseURL: baseURL) { updated in
                    self.conversation = updated
                }
            }
        }
        .sheet(isPresented: $showingAddToTeam) {
            if let conversation, let baseURL {
                AddToTeamSheet(conversation: conversation, userID: userID, baseURL: baseURL, roster: roster) { updated in
                    self.conversation = updated
                    showingAddToTeam = false
                }
            }
        }
        .alert("Delete this conversation?", isPresented: $pendingDelete) {
            Button("Delete", role: .destructive) { Task { await deleteConversation() } }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This removes it for everyone in the conversation.")
        }
        .task { await load() }
        .trackScreen("circle_thread")
    }

    // MARK: - Pieces

    private func threadBody(_ conversation: CircleConversation) -> some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: .hearth500) {
                        if let errorMessage {
                            Text(errorMessage).font(.hearthBodySM).foregroundColor(.statusError)
                        }
                        // Original post.
                        threadEntry(
                            initials: starterInitials(conversation),
                            name: conversation.starterName ?? "Someone",
                            body: conversation.body,
                            showReply: true
                        )
                        ForEach(messages) { message in
                            threadEntry(initials: message.initials, name: message.authorName,
                                       body: message.body, showReply: true)
                                .id(message.id)
                        }
                    }
                    .padding(.hearth500)
                }
                .onChange(of: messages.last?.id) { _, lastId in
                    if let lastId { withAnimation(.hearthFast) { proxy.scrollTo(lastId, anchor: .bottom) } }
                }
            }
            composer
        }
    }

    private func threadEntry(initials: String, name: String, body: String, showReply: Bool) -> some View {
        HStack(alignment: .top, spacing: .hearth400) {
            Circle()
                .fill(Color.accentTint)
                .frame(width: 36, height: 36)
                .overlay(Text(initials).font(.hearthLabel).foregroundColor(.accentOnCanvas))
            VStack(alignment: .leading, spacing: .hearth300) {
                Text(name).font(.hearthBodySM.weight(.semibold)).foregroundColor(.inkPrimary)
                Text(body).font(.hearthBodyMD).foregroundColor(.inkPrimary)
                if showReply {
                    Button {
                        draft = "@\(name) "
                        composerFocused = true
                    } label: {
                        Text("Reply").font(.hearthLabel).foregroundColor(.accentOnCanvas)
                    }
                }
            }
        }
    }

    private var composer: some View {
        HStack(spacing: .hearth400) {
            TextField("Reply…", text: $draft, axis: .vertical)
                .focused($composerFocused)
                .lineLimit(1...5)
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth300)
                .background(Color.bgElevated)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                .disabled(sending)
            Button {
                Task { await send() }
            } label: {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.system(size: 30))
                    .foregroundColor(canSend ? .accentDefault : .inkMuted)
            }
            .disabled(!canSend)
            .accessibilityLabel("Send")
        }
        .padding(.horizontal, .hearth500)
        .padding(.vertical, .hearth300)
        .background(Color.bgCanvas)
    }

    private var canSend: Bool {
        !sending && !draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    /// The OP's avatar initials — matched off the participant list by name
    /// when possible, else derived from `starterName` directly.
    private func starterInitials(_ conversation: CircleConversation) -> String {
        if let match = (conversation.participants ?? []).first(where: { $0.displayName == conversation.starterName }) {
            return match.initials
        }
        let parts = (conversation.starterName ?? "?").split(separator: " ")
        return String(parts.prefix(2).compactMap(\.first)).uppercased()
    }

    // MARK: - Actions

    private func load() async {
        guard let baseURL else { loading = false; return }
        loading = true
        defer { loading = false }
        do {
            let result = try await CircleService.thread(id: conversationId, userID: userID, baseURL: baseURL)
            conversation = result.conversation
            messages = result.messages
            errorMessage = nil
            await CircleService.markRead(conversationId: conversationId, userID: userID, baseURL: baseURL)
        } catch let error as CircleService.CircleServiceError where error.isNotFound {
            onNotFound()
        } catch {
            errorMessage = "Couldn't load this conversation. Pull to retry."
        }
    }

    private func send() async {
        guard let baseURL else { return }
        let body = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !body.isEmpty else { return }
        sending = true
        defer { sending = false }
        do {
            let message = try await CircleService.sendMessage(conversationId: conversationId, body: body,
                                                               userID: userID, baseURL: baseURL)
            messages.append(message)
            draft = ""
            Analytics.capture("circle_message_sent", [:])
        } catch {
            errorMessage = "That message didn't send. Try again."
        }
    }

    private func loadRosterThenPresent() async {
        guard let baseURL else { return }
        roster = (try? await CircleService.householdMembers(userID: userID, baseURL: baseURL)) ?? []
        showingAddToTeam = true
    }

    private func deleteConversation() async {
        guard let baseURL else { return }
        do {
            try await CircleService.deleteConversation(id: conversationId, userID: userID, baseURL: baseURL)
            Analytics.capture("circle_conversation_deleted", ["source": "thread"])
            dismiss()
        } catch {
            errorMessage = "Couldn't delete that conversation. Try again."
        }
    }
}

// MARK: - Edit sheet (title / body)

private struct EditConversationSheet: View {
    let conversation: CircleConversation
    let userID: String
    let baseURL: URL
    var onSaved: (CircleConversation) -> Void

    @State private var title: String
    @State private var messageBody: String
    @State private var saving = false
    @Environment(\.dismiss) private var dismiss

    init(conversation: CircleConversation, userID: String, baseURL: URL, onSaved: @escaping (CircleConversation) -> Void) {
        self.conversation = conversation
        self.userID = userID
        self.baseURL = baseURL
        self.onSaved = onSaved
        _title = State(initialValue: conversation.title)
        _messageBody = State(initialValue: conversation.body)
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Title") {
                    TextField("Title", text: $title)
                }
                Section("Message") {
                    TextEditor(text: $messageBody).frame(minHeight: 120)
                }
            }
            .navigationTitle("Edit conversation")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button(saving ? "Saving…" : "Save") { Task { await save() } }
                        .disabled(title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || saving)
                }
            }
        }
    }

    private func save() async {
        saving = true
        defer { saving = false }
        if let updated = try? await CircleService.updateConversation(
            id: conversation.id, title: title, body: messageBody, userID: userID, baseURL: baseURL
        ) {
            onSaved(updated)
            dismiss()
        }
    }
}
