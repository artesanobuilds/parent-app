import SwiftUI
import MarkdownUI

struct AgentView: View {
    @ObservedObject var viewModel: ChatViewModel
    @ObservedObject var configuration: ServerConfiguration
    @State private var messageText: String = ""
    @State private var isShowingSettings: Bool = false

    @EnvironmentObject private var contentVM: ContentViewModel

    /// Tracks which assistant message IDs have had content cards generated.
    /// Maps message ID -> (community posts, library items) so content is stable.
    @State private var contentCards: [UUID: ([APICommunityPost], [APIArticle])] = [:]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                Divider()
                    .overlay(Color.white.opacity(0.08))
                messageList
                inputArea
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button {
                        isShowingSettings = true
                    } label: {
                        Image(systemName: "line.3.horizontal")
                            .font(.system(size: 18, weight: .medium))
                            .foregroundColor(.white)
                    }
                }
                ToolbarItem(placement: .principal) {
                    Text("MVP")
                        .font(.headline.weight(.semibold))
                        .foregroundColor(.white)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack(spacing: 16) {
                        Button {
                            withAnimation { viewModel.resetConversation() }
                            contentCards = [:]
                        } label: {
                            Image(systemName: "square.and.pencil")
                                .font(.system(size: 17, weight: .medium))
                                .foregroundColor(.white)
                        }
                        Button {
                            // Bookmark placeholder
                        } label: {
                            Image(systemName: "bookmark")
                                .font(.system(size: 17, weight: .medium))
                                .foregroundColor(.white)
                        }
                    }
                }
            }
            .toolbarBackground(Color.brandBackground, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .sheet(isPresented: $isShowingSettings) {
                NavigationStack {
                    ServerSettingsView(configuration: configuration)
                        .navigationTitle("Server Settings")
                        .toolbar {
                            ToolbarItem(placement: .confirmationAction) {
                                Button("Done") { isShowingSettings = false }
                            }
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
            .background(Color.brandBackground.ignoresSafeArea())
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
                                    VStack(alignment: .leading, spacing: 20) {
                                        CommunitySection(posts: cards.0)
                                        LibrarySection(items: cards.1)
                                        FeedbackRow(
                                            feedback: message.feedback,
                                            onThumbsUp: { viewModel.submitFeedback(messageID: message.id, feedback: .thumbsUp) },
                                            onThumbsDown: { viewModel.submitFeedback(messageID: message.id, feedback: .thumbsDown) }
                                        )
                                    }
                                    .padding(.horizontal, 16)
                                    .padding(.top, 16)
                                    .padding(.bottom, 8)
                                    .transition(.opacity.combined(with: .move(edge: .bottom)))
                                }
                            }
                        }
                    }
                }
                .padding(.vertical, 8)
            }
            .background(Color.brandBackground)
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
                .font(.body)
                .foregroundColor(.white)
                .padding(.horizontal, 18)
                .padding(.vertical, 12)
                .background(Color.brandLightBlue)
                .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 6)
    }

    // MARK: - Assistant Message (GiGi Style)

    private func assistantMessageRow(_ message: ChatMessage) -> some View {
        HStack(alignment: .top, spacing: 10) {
            // Gold branded avatar
            Circle()
                .fill(Color.brandGold)
                .frame(width: 30, height: 30)
                .overlay(
                    Text("M")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(.white)
                )
                .padding(.top, 2)

            VStack(alignment: .leading, spacing: 6) {
                Markdown(message.content.isEmpty ? "..." : message.content)
                    .markdownTextStyle {
                        FontSize(15)
                        ForegroundColor(.white)
                    }
                    .markdownBlockStyle(\.heading2) { configuration in
                        configuration.label
                            .markdownTextStyle {
                                FontWeight(.bold)
                                FontSize(17)
                                ForegroundColor(.white)
                            }
                    }

                if message.isStreaming {
                    HStack(spacing: 4) {
                        ProgressView()
                            .scaleEffect(0.6)
                        Text("Thinking...")
                            .font(.caption)
                            .foregroundColor(.brandGray)
                    }
                }
            }

            Spacer(minLength: 16)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 8)
    }

    // MARK: - Input Area

    private var inputArea: some View {
        VStack(spacing: 6) {
            Divider()
                .overlay(Color.white.opacity(0.08))

            HStack(alignment: .bottom, spacing: 10) {
                // Text field
                TextField("Type your question", text: $messageText, axis: .vertical)
                    .font(.body)
                    .foregroundColor(.white)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(
                        RoundedRectangle(cornerRadius: 22, style: .continuous)
                            .fill(Color.brandSurface)
                            .overlay(
                                RoundedRectangle(cornerRadius: 22, style: .continuous)
                                    .stroke(Color.brandStroke, lineWidth: 1)
                            )
                    )
                    .lineLimit(1...4)
                    .disabled(viewModel.isSending || configuration.baseURL == nil || viewModel.isUserIDMissing)
                    .textInputAutocapitalization(.sentences)
                    .onSubmit(sendMessage)

                // Microphone button (decorative)
                Button {
                    // Voice input placeholder
                } label: {
                    Image(systemName: "mic")
                        .font(.system(size: 18, weight: .medium))
                        .foregroundColor(.brandGray)
                }
                .disabled(true)
                .opacity(0.6)

                // Send button
                Button {
                    sendMessage()
                } label: {
                    Image(systemName: "arrow.up")
                        .font(.system(size: 16, weight: .bold))
                        .foregroundColor(canSend ? .brandBlack : .brandGray)
                        .frame(width: 34, height: 34)
                        .background(
                            Circle()
                                .fill(canSend ? Color.brandGold : Color.brandSurface)
                        )
                }
                .disabled(!canSend)
            }
            .padding(.horizontal, 16)
            .padding(.top, 8)

            // Disclaimer
            HStack(spacing: 4) {
                Text("AI can make mistakes and is not a crisis line.")
                    .font(.caption2)
                    .foregroundColor(.brandGray)
                Text("Learn More")
                    .font(.caption2)
                    .foregroundColor(.brandGray)
                    .underline()
            }
            .padding(.bottom, 6)
        }
        .background(Color.brandBackground)
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
            withAnimation { proxy.scrollTo(lastID, anchor: .bottom) }
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
