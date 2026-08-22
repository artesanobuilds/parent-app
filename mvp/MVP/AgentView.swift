import SwiftUI
import MarkdownUI

struct AgentView: View {
    @ObservedObject var viewModel: ChatViewModel
    @ObservedObject var configuration: ServerConfiguration
    @State private var messageText: String = ""
    @State private var isShowingVoice: Bool = false

    @EnvironmentObject private var contentVM: ContentViewModel

    /// Tracks which assistant message IDs have had content cards generated.
    /// Maps message ID -> library items so content is stable.
    @State private var contentCards: [UUID: [APIArticle]] = [:]

    /// Programmatic pushes for the coach's inline mvp:// citations — the
    /// OpenURLAction below appends routes here and the destinations registered
    /// by withContentNavigationDestinations() render them.
    @State private var navPath = NavigationPath()

    /// Message ids whose reply was saved this session (fills the bookmark).
    @State private var savedReplyIds: Set<UUID> = []

    /// Presents the past-conversations list (coach-002).
    @State private var isShowingHistory = false

    /// True while `POST /coach/threads/close` is in flight, so a double tap on
    /// "new conversation" can't open two threads.
    @State private var isClosingConversation = false

    private var lastAssistantMessage: ChatMessage? {
        viewModel.messages.last(where: {
            $0.role == .assistant && !$0.content.isEmpty && !$0.isStreaming
        })
    }

    private var lastReplySaved: Bool {
        lastAssistantMessage.map { savedReplyIds.contains($0.id) } ?? false
    }

    /// Save Coach's most recent reply. The snapshot IS the copy — coach chat
    /// has no durable server row — so the body ships with the save, keyed by
    /// the client message id (the /feedback convention).
    private func saveLastReply() {
        guard let message = lastAssistantMessage,
              let baseURL = configuration.baseURL else { return }
        savedReplyIds.insert(message.id)   // optimistic
        Task {
            do {
                try await SavedService.save(
                    itemType: "coach_reply", itemRef: message.id.uuidString,
                    body: message.content, surface: "coach",
                    userID: viewModel.currentUserID, baseURL: baseURL
                )
            } catch {
                savedReplyIds.remove(message.id)
                viewModel.errorMessage = "Couldn't save that reply. Try again."
            }
        }
    }

    var body: some View {
        NavigationStack(path: $navPath) {
            VStack(spacing: 0) {
                Divider()
                    .background(Color.borderHairline)
                // The Coach tab's own empty state (coach-000). Home's inline
                // coachSection banner is a different surface and is untouched.
                if viewModel.messages.isEmpty {
                    ScrollView {
                        CoachFirstRunView(
                            userID: viewModel.currentUserID,
                            baseURL: configuration.baseURL,
                            onSend: { prompt in viewModel.send(prompt) }
                        )
                        .padding(.top, .hearth700)
                    }
                    .background(Color.bgCanvas)
                } else {
                    messageList
                }
                inputArea
            }
            // The coach cites content as [Title](mvp://library/{id}) (see
            // agent.py + the content catalog). These links were DEAD until
            // this handler: no mvp:// scheme is registered anywhere, so taps
            // did nothing. Route them in-app; the learn-more disclaimer opens
            // the public coach doc; real web links (search citations) fall
            // through to Safari.
            //
            // `mvp://community/` was the second host until the public board
            // was retired in beta-v1 sprint 2. The catalog no longer emits it,
            // and the `default` case below swallows any stale link rather than
            // bouncing the parent to a "cannot open" alert. Locked by
            // tests/test_coach_citation_contract.py.
            .environment(\.openURL, OpenURLAction { url in
                guard url.scheme == "mvp" else { return .systemAction }
                let id = url.lastPathComponent
                switch url.host {
                case "library" where !id.isEmpty:
                    navPath.append(ArticleRoute(id: id))
                    return .handled
                case "learn-more":
                    if let base = configuration.baseURL {
                        return .systemAction(base.appendingPathComponent("dashboard/docs/coach"))
                    }
                    return .discarded
                default:
                    // An mvp:// link shape we don't know — swallow it rather
                    // than bounce the parent to a "cannot open" system alert.
                    return .discarded
                }
            })
            .onAppear { Analytics.capture("chat_opened", ["agent_kind": "coach"]) }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    Text("Coach")
                        .font(.hearthTitleLG)
                        .foregroundColor(.inkPrimary)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack(spacing: .hearth500) {
                        Button {
                            isShowingVoice = true
                        } label: {
                            Image(systemName: "waveform")
                                .font(.system(size: 17, weight: .medium))
                                .foregroundColor(.inkPrimary)
                                .frame(width: 44, height: 44)
                                .contentShape(Rectangle())
                        }
                        .accessibilityLabel("Talk to your coach")
                        Button {
                            isShowingHistory = true
                        } label: {
                            Image(systemName: "clock.arrow.circlepath")
                                .font(.system(size: 17, weight: .medium))
                                .foregroundColor(.inkPrimary)
                                .frame(width: 44, height: 44)
                                .contentShape(Rectangle())
                        }
                        .accessibilityLabel("Past conversations")
                        Button {
                            startNewConversation()
                        } label: {
                            Image(systemName: "square.and.pencil")
                                .font(.system(size: 17, weight: .medium))
                                .foregroundColor(.inkPrimary)
                                .frame(width: 44, height: 44)
                                .contentShape(Rectangle())
                        }
                        .disabled(isClosingConversation)
                        .accessibilityLabel("New conversation")
                        Button {
                            saveLastReply()
                        } label: {
                            Image(systemName: lastReplySaved ? "bookmark.fill" : "bookmark")
                                .font(.system(size: 17, weight: .medium))
                                .foregroundColor(lastReplySaved ? .accentDefault : .inkPrimary)
                                .frame(width: 44, height: 44)
                                .contentShape(Rectangle())
                        }
                        .disabled(lastAssistantMessage == nil)
                        .accessibilityLabel(lastReplySaved ? "Reply saved" : "Save Coach's last reply")
                    }
                }
            }
            .toolbarBackground(Color.bgCanvas, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .fullScreenCover(isPresented: $isShowingVoice) {
                if let baseURL = configuration.baseURL {
                    ParentVoiceView(
                        userID: viewModel.currentUserID,
                        baseURL: baseURL,
                        onClose: { transcript in
                            viewModel.importMessages(transcript)
                            isShowingVoice = false
                        }
                    )
                    .environmentObject(contentVM)
                }
            }
            .sheet(isPresented: $isShowingHistory) {
                if let baseURL = configuration.baseURL {
                    NavigationStack {
                        CoachHistoryView(
                            userID: viewModel.currentUserID,
                            baseURL: baseURL,
                            onOpen: { stored in
                                // Replace the visible transcript with the
                                // reopened conversation's. The server already
                                // made it the active thread, so the next
                                // message continues THIS conversation.
                                viewModel.replaceMessages(
                                    stored.map {
                                        ChatMessage(
                                            role: $0.role == "user" ? .user : .assistant,
                                            content: $0.content
                                        )
                                    }
                                )
                                contentCards = [:]
                                savedReplyIds = []
                            }
                        )
                    }
                }
            }
            .alert(
                "Error",
                isPresented: Binding<Bool>(
                    get: { viewModel.errorMessage != nil },
                    set: { if !$0 { viewModel.errorMessage = nil } }
                )
            ) {
                Button("OK") { viewModel.errorMessage = nil }
            } message: {
                Text(viewModel.errorMessage ?? "")
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .withContentNavigationDestinations()
        }
    }

    // MARK: - Message List

    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 0) {
                    ForEach(viewModel.messages) { message in
                        if message.role == .user {
                            userMessageRow(message)
                                .id(message.id)
                        } else {
                            assistantMessageRow(message)
                                .id(message.id)

                            // Show content cards after the response finishes streaming
                            if !message.isStreaming && !message.content.isEmpty {
                                contentCardBlock(for: message)
                            }
                        }
                    }
                }
                .padding(.vertical, .hearth300)
            }
            .background(Color.bgCanvas)
            // Tap anywhere on the message list to dismiss the keyboard.
            // .contentShape ensures empty space inside the ScrollView is
            // tappable; .scrollDismissesKeyboard covers the drag-to-dismiss
            // gesture as a complementary path.
            .contentShape(Rectangle())
            .onTapGesture {
                UIApplication.shared.sendAction(
                    #selector(UIResponder.resignFirstResponder),
                    to: nil, from: nil, for: nil,
                )
            }
            .scrollDismissesKeyboard(.interactively)
            .onChange(of: viewModel.messages) { _, newValue in
                guard newValue.last?.isStreaming == true else { return }
                scrollToBottom(proxy: proxy)
            }
            .onAppear {
                scrollToBottom(proxy: proxy, animated: false)
            }
        }
    }

    // MARK: - User Message (Pill Style)

    /// Measured `coach-001`: the parent's bubble is the DEEP teal (`#0A5570`),
    /// pad 16 all round, radius 12 with an 8pt bottom-LEADING corner (the
    /// speech-tail), body 14 in the warm cream — not the mid teal at r=20 this
    /// shipped with.
    private func userMessageRow(_ message: ChatMessage) -> some View {
        HStack {
            Spacer(minLength: 60)
            Text(message.content)
                .font(.hearthBodySM)
                .foregroundColor(.inkOnCard)
                .padding(.hearth500)
                .background(Color.accentDeep)
                .clipShape(
                    UnevenRoundedRectangle(
                        topLeadingRadius: .hearthRadiusTile,
                        bottomLeadingRadius: .hearthRadiusButton,
                        bottomTrailingRadius: .hearthRadiusTile,
                        topTrailingRadius: .hearthRadiusTile,
                        style: .continuous
                    )
                )
        }
        .padding(.horizontal, .hearth500)
        .padding(.vertical, .hearth300)
    }

    // MARK: - Assistant Message

    private func assistantMessageRow(_ message: ChatMessage) -> some View {
        HStack(alignment: .top, spacing: .hearth400) {
            // Coach avatar: the product's typographic mark (Fraunces "M"),
            // not an ad-hoc label — one mark everywhere (see MVPLogoView).
            Circle()
                .fill(Color.accentDefault)
                .frame(width: 30, height: 30)
                .overlay(
                    HearthMark(size: 18, tint: .inkOnPhotoLight)
                )
                .padding(.top, 2)

            VStack(alignment: .leading, spacing: .hearth300) {
                Markdown(message.content.isEmpty ? "..." : message.content)
                    .markdownTextStyle {
                        FontFamily(.custom(HearthFontFamily.sans))
                        FontSize(15)
                        ForegroundColor(Color.inkPrimary)
                    }
                    .markdownBlockStyle(\.heading2) { configuration in
                        configuration.label
                            .markdownTextStyle {
                                FontFamily(.custom(HearthFontFamily.displaySerif))
                                FontWeight(.semibold)
                                FontSize(18)
                                ForegroundColor(Color.inkPrimary)
                            }
                    }

                if message.isStreaming {
                    HStack(spacing: .hearth300) {
                        ProgressView()
                            .scaleEffect(0.6)
                        Text("Thinking…")
                            .font(.hearthBodySM)
                            .foregroundColor(.inkMuted)
                    }
                }
            }

            Spacer(minLength: 16)
        }
        .padding(.horizontal, .hearth500)
        .padding(.vertical, .hearth300)
    }

    // MARK: - Input Area

    /// Measured `coach-001`/`coach-000` (round 2), re-verified round 3
    /// against `754:5568`/`1026:10542` `chatinput` instances: the composer
    /// sits on the DEEP teal strip (`#0A5570`) with 16pt top corners — not a
    /// hairline divider on canvas. A leading `icon.attach` (⊕, white, ~26pt)
    /// sits OUTSIDE the field; the field itself is white at r=8, body 14,
    /// with the send affordance INSIDE its own trailing edge — not a
    /// separate circle floating outside the field. The disclaimer stays
    /// below the strip on canvas (it isn't part of the frame's strip).
    private var inputArea: some View {
        VStack(spacing: 0) {
            HStack(alignment: .center, spacing: .hearth400) {
                // Leading ⊕ — the frame's `icon.attach`; no attach action
                // exists in this build yet, so it's decorative chrome that
                // matches the composer shared with Planner (round 3) rather
                // than a live control.
                Image(systemName: "plus.circle")
                    .font(.system(size: 24, weight: .regular))
                    .foregroundColor(.inkOnPhotoLight)

                // Text field, with the send arrow inside its trailing edge.
                HStack(spacing: .hearth300) {
                    TextField("Ask the coach for help", text: $messageText, axis: .vertical)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkPrimary)
                        .lineLimit(1...4)
                        .disabled(viewModel.isSending || configuration.baseURL == nil || viewModel.isUserIDMissing)
                        .textInputAutocapitalization(.sentences)
                        .onSubmit(sendMessage)

                    // Measured `icon.microphone` instance (`754:5587`,
                    // `1026:10542`) swaps to this arrow glyph once there's
                    // text to send — plain green (`statusSuccess`, #3D6B3D),
                    // NO circle background. An earlier pass added a filled
                    // circle behind it that the frame doesn't draw.
                    Button {
                        sendMessage()
                    } label: {
                        Image(systemName: "arrow.up")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundColor(canSend ? .statusSuccess : .inkMuted)
                    }
                    .disabled(!canSend)
                }
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth400)
                .background(
                    RoundedRectangle(cornerRadius: .hearthRadiusButton, style: .continuous)
                        .fill(Color.bgElevated)
                )
            }
            // Measured strip padding: 12 top / 18 sides.
            .padding(.horizontal, .hearth600)
            .padding(.vertical, .hearth400)
            .background(
                UnevenRoundedRectangle(
                    topLeadingRadius: .hearthRadiusCard,
                    bottomLeadingRadius: 0,
                    bottomTrailingRadius: 0,
                    topTrailingRadius: .hearthRadiusCard,
                    style: .continuous
                )
                .fill(Color.accentDeep)
                .ignoresSafeArea(edges: .bottom)
            )

            // Disclaimer — wrap, don't truncate. "Learn more" sits inline at
            // the end via Markdown so the whole disclaimer stays one logical
            // sentence that can break at the page gutter. Rendered ON the deep
            // strip (cream ink, 7.44:1) so the strip owns the bottom edge as in
            // the frame.
            Text((try? AttributedString(
                markdown: "Coach can make mistakes and is not a crisis line. [Learn more](mvp://learn-more)"
            )) ?? AttributedString("Coach can make mistakes and is not a crisis line."))
                .font(.hearthCaptionMono)
                .foregroundColor(.inkOnCard)
                .tint(.inkOnCard)
                .multilineTextAlignment(.center)
                .frame(maxWidth: .infinity)
                .padding(.horizontal, .hearth500)
                .padding(.bottom, .hearth300)
                .background(Color.accentDeep.ignoresSafeArea(edges: .bottom))
        }
    }

    // MARK: - Helpers

    /// Close the current conversation (keeping it) and start a new one.
    ///
    /// This used to be `viewModel.resetConversation()`, which WIPED the thread.
    /// The server is the source of truth for which conversation is active, so
    /// the local transcript is only cleared once the close is confirmed —
    /// otherwise a failed call would leave the app showing an empty chat that
    /// still appends to the old conversation (CLAUDE.md: don't navigate away
    /// assuming success).
    private func startNewConversation() {
        guard !isClosingConversation,
              let baseURL = configuration.baseURL,
              !viewModel.currentUserID.isEmpty else { return }
        isClosingConversation = true
        Task {
            do {
                _ = try await CoachThreadService.closeCurrent(
                    userID: viewModel.currentUserID, baseURL: baseURL
                )
                withAnimation(.hearthBase) { viewModel.clearVisibleMessages() }
                contentCards = [:]
                savedReplyIds = []
            } catch {
                viewModel.errorMessage = "Couldn't start a new conversation. Try again."
            }
            isClosingConversation = false
        }
    }

    private var canSend: Bool {
        !messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !viewModel.isSending
            && configuration.baseURL != nil
            && !viewModel.isUserIDMissing
    }

    private func sendMessage() {
        let text = messageText
        viewModel.send(text)
        if !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            messageText = ""
        }
    }

    private func scrollToBottom(proxy: ScrollViewProxy, animated: Bool = true) {
        guard let lastID = viewModel.messages.last?.id else { return }
        if animated {
            withAnimation(.hearthBase) { proxy.scrollTo(lastID, anchor: .bottom) }
        } else {
            proxy.scrollTo(lastID, anchor: .bottom)
        }
    }

    /// The library cards + feedback row shown under a finished assistant reply.
    ///
    /// Extracted out of `messageList` deliberately: inlined, the surrounding
    /// ForEach expression grew past what the Swift type-checker will solve in
    /// reasonable time and the build failed with a timeout rather than a real
    /// error. Keep this a separate `@ViewBuilder`.
    @ViewBuilder
    private func contentCardBlock(for message: ChatMessage) -> some View {
        let cards = cardsForMessage(message)
        if !cards.isEmpty {
            VStack(alignment: .leading, spacing: .hearth600) {
                LibrarySection(items: cards)
                FeedbackRow(
                    feedback: message.feedback,
                    onThumbsUp: { viewModel.submitFeedback(messageID: message.id, feedback: .thumbsUp) },
                    onThumbsDown: { viewModel.submitFeedback(messageID: message.id, feedback: .thumbsDown) }
                )
            }
            .padding(.horizontal, .hearth500)
            .padding(.top, .hearth500)
            .padding(.bottom, .hearth300)
            .transition(.opacity.combined(with: .move(edge: .bottom)))
        }
    }

    /// Returns stable content cards for a given message, generating them once.
    private func cardsForMessage(_ message: ChatMessage) -> [APIArticle] {
        if let existing = contentCards[message.id] {
            return existing
        }
        let items = contentVM.randomLibraryItems()
        // Schedule state mutation outside of the view body
        DispatchQueue.main.async {
            contentCards[message.id] = items
        }
        return items
    }
}
