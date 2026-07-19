import SwiftUI

/// One DM thread: message list (newest at the bottom), composer, block/report
/// menu. Delivery is polling — re-fetches every ~15s while the thread is open
/// (no SSE in v1). Marks the thread read on load and after each fetch.
struct ConversationView: View {
    let conversation: DMConversation
    let userID: String
    let baseURL: URL

    @State private var messages: [DMMessage] = []   // oldest → newest for display
    @State private var draft = ""
    @State private var sending = false
    @State private var blocked: Bool
    @State private var errorMessage: String?
    @State private var showingReport = false
    @State private var reportNote = ""
    // One-time privacy notice above the composer (first DM use ever).
    @AppStorage("dm_notice_dismissed") private var noticeDismissed = false

    init(conversation: DMConversation, userID: String, baseURL: URL) {
        self.conversation = conversation
        self.userID = userID
        self.baseURL = baseURL
        _blocked = State(initialValue: conversation.iBlocked ?? false)
    }

    var body: some View {
        VStack(spacing: 0) {
            messageList
            if !noticeDismissed {
                privacyNotice
            }
            composer
        }
        .background(Color.bgCanvas.ignoresSafeArea())
        .navigationTitle(conversation.peerName)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Menu {
                    if blocked {
                        Button("Unblock") { Task { await setBlocked(false) } }
                    } else {
                        Button("Block", role: .destructive) { Task { await setBlocked(true) } }
                    }
                    Button("Report conversation", role: .destructive) { showingReport = true }
                } label: {
                    Image(systemName: "ellipsis.circle")
                        .foregroundColor(.inkPrimary)
                }
                .accessibilityLabel("Conversation options")
            }
        }
        .task {
            await refresh()
            await DMService.markRead(conversationId: conversation.id, userID: userID, baseURL: baseURL)
            // Poll while the thread stays open. The task is cancelled by
            // SwiftUI when the view disappears, ending the loop.
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 15_000_000_000)
                if Task.isCancelled { break }
                await refresh()
            }
        }
        .alert("Report this conversation?", isPresented: $showingReport) {
            TextField("What's wrong? (optional)", text: $reportNote)
            Button("Report", role: .destructive) { Task { await report() } }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("The recent messages will be sent to the MVP team for review.")
        }
        .trackScreen("dm_conversation")
    }

    // MARK: - Pieces

    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: .hearth300) {
                    if let errorMessage {
                        Text(errorMessage).font(.hearthBodySM).foregroundColor(.statusError)
                    }
                    ForEach(messages) { message in
                        messageBubble(message)
                            .id(message.id)
                    }
                }
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth400)
            }
            .onChange(of: messages.last?.id) { _, lastId in
                if let lastId {
                    withAnimation(.hearthFast) { proxy.scrollTo(lastId, anchor: .bottom) }
                }
            }
        }
    }

    private func messageBubble(_ message: DMMessage) -> some View {
        let mine = message.senderId == userID
        return HStack {
            if mine { Spacer(minLength: 48) }
            Text(message.body)
                .font(.hearthBodyMD)
                .foregroundColor(mine ? .inkOnPhotoLight : .inkPrimary)
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth300)
                .background(mine ? Color.accentDefault : Color.bgElevated)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                .frame(maxWidth: .infinity, alignment: mine ? .trailing : .leading)
            if !mine { Spacer(minLength: 48) }
        }
    }

    private var privacyNotice: some View {
        HStack(alignment: .top, spacing: .hearth300) {
            Text("Messages are visible to the parent you send them to and stored until either of you deletes your account. Report or block anytime.")
                .font(.hearthBodySM)
                .foregroundColor(.inkMuted)
            Button {
                noticeDismissed = true
            } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(.inkMuted)
            }
            .accessibilityLabel("Dismiss notice")
        }
        .padding(.hearth400)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
        .padding(.horizontal, .hearth500)
    }

    private var composer: some View {
        HStack(spacing: .hearth400) {
            TextField(blocked ? "Conversation blocked" : "Message…", text: $draft, axis: .vertical)
                .lineLimit(1...5)
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth300)
                .background(Color.bgElevated)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                .disabled(blocked || sending)
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
        !blocked && !sending && !draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    // MARK: - Actions

    private func refresh() async {
        if let fetched = try? await DMService.messages(
            conversationId: conversation.id, userID: userID, baseURL: baseURL
        ) {
            let ordered = fetched.reversed()  // API is newest-first
            if messages.map(\.id) != ordered.map(\.id) {
                messages = Array(ordered)
                await DMService.markRead(conversationId: conversation.id,
                                         userID: userID, baseURL: baseURL)
            }
            errorMessage = nil
        }
    }

    private func send() async {
        let body = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !body.isEmpty else { return }
        sending = true
        defer { sending = false }
        do {
            _ = try await DMService.send(conversationId: conversation.id, body: body,
                                         userID: userID, baseURL: baseURL)
            Analytics.capture("dm_message_sent", [:])
            draft = ""
            await refresh()
        } catch {
            errorMessage = "That message didn't send. Try again."
        }
    }

    private func setBlocked(_ value: Bool) async {
        do {
            try await DMService.setBlocked(value, conversationId: conversation.id,
                                           userID: userID, baseURL: baseURL)
            blocked = value
            if value { Analytics.capture("dm_blocked", [:]) }
        } catch {
            errorMessage = "Couldn't update the block. Try again."
        }
    }

    private func report() async {
        do {
            try await DMService.report(conversationId: conversation.id,
                                       note: reportNote.isEmpty ? nil : reportNote,
                                       userID: userID, baseURL: baseURL)
            Analytics.capture("dm_reported", [:])
            reportNote = ""
        } catch {
            errorMessage = "Couldn't send the report. Try again."
        }
    }
}
