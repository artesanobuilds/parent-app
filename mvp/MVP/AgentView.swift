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
                messageList
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
                            withAnimation(.hearthBase) { viewModel.resetConversation() }
                            contentCards = [:]
                        } label: {
                            Image(systemName: "square.and.pencil")
                                .font(.system(size: 17, weight: .medium))
                                .foregroundColor(.inkPrimary)
                                .frame(width: 44, height: 44)
                                .contentShape(Rectangle())
                        }
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

    private func userMessageRow(_ message: ChatMessage) -> some View {
        HStack {
            Spacer(minLength: 60)
            Text(message.content)
                .font(.hearthBodyMD)
                .foregroundColor(.inkOnPhotoLight)
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth400)
                .background(Color.accentDefault)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
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

    private var inputArea: some View {
        VStack(spacing: .hearth300) {
            Divider()
                .background(Color.borderHairline)

            HStack(alignment: .bottom, spacing: .hearth400) {
                // Text field
                TextField("Type your question", text: $messageText, axis: .vertical)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkPrimary)
                    .padding(.horizontal, .hearth500)
                    .padding(.vertical, .hearth400)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                            .fill(Color.bgElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                                    .stroke(Color.borderStrong, lineWidth: 1)
                            )
                    )
                    .lineLimit(1...4)
                    .disabled(viewModel.isSending || configuration.baseURL == nil || viewModel.isUserIDMissing)
                    .textInputAutocapitalization(.sentences)
                    .onSubmit(sendMessage)

                // Send button
                Button {
                    sendMessage()
                } label: {
                    Image(systemName: "arrow.up")
                        .font(.system(size: 16, weight: .bold))
                        .foregroundColor(canSend ? .inkOnPhotoLight : .inkMuted)
                        .frame(width: 44, height: 44)
                        .background(
                            Circle()
                                .fill(canSend ? Color.accentDefault : Color.bgElevated)
                                .overlay(Circle().stroke(Color.borderHairline, lineWidth: canSend ? 0 : 1))
                        )
                }
                .disabled(!canSend)
            }
            .padding(.horizontal, .hearth500)
            .padding(.top, .hearth300)

            // Disclaimer — wrap, don't truncate. "Learn more" sits inline at
            // the end via Markdown so the whole disclaimer stays one logical
            // sentence that can break at the page gutter.
            Text((try? AttributedString(
                markdown: "Coach can make mistakes and is not a crisis line. [Learn more](mvp://learn-more)"
            )) ?? AttributedString("Coach can make mistakes and is not a crisis line."))
                .font(.hearthCaptionMono)
                .foregroundColor(.inkMuted)
                .tint(.inkMuted)
                .multilineTextAlignment(.center)
                .frame(maxWidth: .infinity)
                .padding(.horizontal, .hearth500)
                .padding(.bottom, .hearth300)
        }
        .background(Color.bgCanvas)
    }

    // MARK: - Helpers

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
