import SwiftUI

struct CommunityPostDetailView: View {
    let postId: String
    @EnvironmentObject private var contentVM: ContentViewModel
    @State private var replyText: String = ""
    @State private var isSendingReply = false
    // Set when the reader taps Message on an author row — presents the thread.
    @State private var dmConversation: DMConversation?

    private var post: APICommunityPost? {
        contentVM.postData(postId)
    }

    private var replies: [APIReply] {
        contentVM.repliesCache[postId] ?? []
    }

    var body: some View {
        Group {
            if let post = post {
                VStack(spacing: 0) {
                    ScrollView {
                        VStack(alignment: .leading, spacing: .hearth600) {
                            postHeader(post)
                            postBody(post)
                            repliesSection
                        }
                        .padding(.hearth700)
                        .padding(.top, .hearth300)
                    }

                    replyInputBar
                }
                .background(Color.bgCanvas.ignoresSafeArea())
                .navigationTitle("")
                .navigationBarTitleDisplayMode(.inline)
                .toolbarBackground(Color.bgCanvas, for: .navigationBar)
                .toolbarBackground(.visible, for: .navigationBar)
                .task {
                    Analytics.capture("content_opened", ["type": "community_post"])
                    if let url = contentVM.baseURL {
                        await contentVM.loadReplies(baseURL: url, postId: postId)
                    }
                }
                .sheet(item: $dmConversation) { conv in
                    if let url = contentVM.baseURL {
                        NavigationStack {
                            ConversationView(conversation: conv,
                                             userID: contentVM.userId, baseURL: url)
                        }
                    }
                }
            } else {
                notFound
            }
        }
    }

    // MARK: - Post Header

    private func postHeader(_ post: APICommunityPost) -> some View {
        HStack(spacing: .hearth400) {
            Circle()
                .fill(Color.accentTint)
                .frame(width: 48, height: 48)
                .overlay(
                    Text(post.initials)
                        .font(.hearthTitleMD)
                        .foregroundColor(.accentDefault)
                )

            VStack(alignment: .leading, spacing: 2) {
                Text(post.name)
                    .font(.hearthTitleMD)
                    .foregroundColor(.inkPrimary)

                if let category = contentVM.categories.first(where: { $0.id == post.category }) {
                    Text("\(category.emoji) \(category.name)")
                        .font(.hearthCaptionMono)
                        .foregroundColor(.inkMuted)
                }
            }

            Spacer()
            messageButton(authorId: post.userId, source: "post")
        }
    }

    /// Envelope button shown when the author is another signed-in parent
    /// (their user_id only reaches us on authed reads — it's the DM handle).
    @ViewBuilder
    private func messageButton(authorId: String?, source: String) -> some View {
        if let authorId, !authorId.isEmpty,
           authorId != contentVM.userId, !contentVM.userId.isEmpty {
            Button {
                Task { await openConversation(with: authorId, source: source) }
            } label: {
                Image(systemName: "envelope")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.accentDefault)
                    .frame(width: 32, height: 32)
                    .background(Color.accentTint)
                    .clipShape(Circle())
            }
            .accessibilityLabel("Message this parent")
        }
    }

    private func openConversation(with peerId: String, source: String) async {
        guard let url = contentVM.baseURL else { return }
        if let conv = try? await DMService.startConversation(
            peerId: peerId, userID: contentVM.userId, baseURL: url
        ) {
            Analytics.capture("dm_conversation_started", ["source": source])
            dmConversation = conv
        }
    }

    // MARK: - Post Body

    private func postBody(_ post: APICommunityPost) -> some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            Text(post.title)
                .font(.hearthDisplayMD)
                .foregroundColor(.inkPrimary)

            Text(post.preview)
                .font(.hearthBodyLG)
                .foregroundColor(.inkPrimary)
                .lineSpacing(.hearthLineBodyLG)
        }
    }

    // MARK: - Replies Section

    private var repliesSection: some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            Divider().background(Color.borderHairline)

            let count = replies.count
            Text(count == 0 ? "No replies yet" : "\(count) \(count == 1 ? "reply" : "replies")")
                .font(.hearthLabel)
                .foregroundColor(.inkMuted)
                .tracking(0.66)
                .textCase(.uppercase)

            ForEach(replies) { reply in
                replyCard(reply)
            }
        }
        .padding(.top, .hearth300)
    }

    private func replyCard(_ reply: APIReply) -> some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            HStack(spacing: .hearth400) {
                Circle()
                    .fill(Color.accentTint)
                    .frame(width: 32, height: 32)
                    .overlay(
                        Text(reply.initials)
                            .font(.hearthLabel)
                            .foregroundColor(.accentDefault)
                    )

                Text(reply.authorName)
                    .font(.hearthTitleMD)
                    .foregroundColor(.inkPrimary)

                Spacer()
                messageButton(authorId: reply.userId, source: "reply")
            }

            Text(reply.body)
                .font(.hearthBodyMD)
                .foregroundColor(.inkPrimary)
                .lineSpacing(.hearthLineBodyMD)
        }
        .padding(.hearth400)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                .stroke(Color.borderHairline, lineWidth: 1)
        )
    }

    // MARK: - Reply Input Bar

    private var replyInputBar: some View {
        VStack(spacing: 0) {
            Divider().background(Color.borderHairline)

            HStack(spacing: .hearth400) {
                TextField("Write a reply…", text: $replyText, axis: .vertical)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkPrimary)
                    .padding(.horizontal, .hearth500)
                    .padding(.vertical, .hearth400)
                    .background(Color.accentTint)
                    .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
                    .lineLimit(1...4)

                Button {
                    sendReply()
                } label: {
                    if isSendingReply {
                        ProgressView()
                            .scaleEffect(0.7)
                            .frame(width: 44, height: 44)
                    } else {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.system(size: 30))
                            .foregroundColor(canSendReply ? .accentDefault : .inkPlaceholder)
                            .frame(width: 44, height: 44)
                            .contentShape(Rectangle())
                    }
                }
                .disabled(!canSendReply)
            }
            .padding(.horizontal, .hearth500)
            .padding(.vertical, .hearth300)
        }
        .background(Color.bgElevated)
    }

    private var canSendReply: Bool {
        !replyText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !isSendingReply
    }

    private func sendReply() {
        let text = replyText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, let url = contentVM.baseURL else { return }
        isSendingReply = true
        replyText = ""
        Task {
            await contentVM.createReply(
                baseURL: url,
                postId: postId,
                authorName: contentVM.userId,
                body: text
            )
            isSendingReply = false
        }
    }

    // MARK: - Not Found

    private var notFound: some View {
        VStack(spacing: .hearth400) {
            Image(systemName: "doc.questionmark")
                .font(.system(size: 40))
                .foregroundColor(.inkPlaceholder)
            Text("Post not found")
                .font(.hearthBodyMD)
                .foregroundColor(.inkMuted)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.bgCanvas.ignoresSafeArea())
    }
}
