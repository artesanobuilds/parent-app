import SwiftUI
import MarkdownUI

struct AgentView: View {
    @ObservedObject var viewModel: ChatViewModel
    @ObservedObject var configuration: ServerConfiguration
    @State private var messageText: String = ""
    @State private var isShowingVoice: Bool = false

    @EnvironmentObject private var contentVM: ContentViewModel

    /// Tracks which assistant message IDs have had content cards generated.
    /// Maps message ID -> (community posts, library items) so content is stable.
    @State private var contentCards: [UUID: ([APICommunityPost], [APIArticle])] = [:]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                Divider()
                    .background(Color.borderHairline)
                messageList
                inputArea
            }
            .onAppear { Analytics.capture("chat_opened", ["agent_kind": "coach"]) }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    Text("MVP")
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
                            // Bookmark placeholder
                        } label: {
                            Image(systemName: "bookmark")
                                .font(.system(size: 17, weight: .medium))
                                .foregroundColor(.inkPrimary)
                                .frame(width: 44, height: 44)
                                .contentShape(Rectangle())
                        }
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
                                let cards = cardsForMessage(message)
                                if !cards.0.isEmpty || !cards.1.isEmpty {
                                    VStack(alignment: .leading, spacing: .hearth600) {
                                        CommunitySection(posts: cards.0)
                                        LibrarySection(items: cards.1)
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
            // Accent-tinted avatar
            Circle()
                .fill(Color.accentDefault)
                .frame(width: 30, height: 30)
                .overlay(
                    Text("M")
                        .font(.hearthLabel)
                        .foregroundColor(.inkOnPhotoLight)
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
            Text(try! AttributedString(
                markdown: "AI can make mistakes and is not a crisis line. [Learn more](mvp://learn-more)"
            ))
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

    /// Returns stable content cards for a given message, generating them once.
    private func cardsForMessage(_ message: ChatMessage) -> ([APICommunityPost], [APIArticle]) {
        if let existing = contentCards[message.id] {
            return existing
        }
        let posts = contentVM.randomCommunityPosts()
        let items = contentVM.randomLibraryItems()
        // Schedule state mutation outside of the view body
        DispatchQueue.main.async {
            contentCards[message.id] = (posts, items)
        }
        return (posts, items)
    }
}
