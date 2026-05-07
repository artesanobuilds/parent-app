import SwiftUI

struct CommunityPostDetailView: View {
    let postId: String
    @EnvironmentObject private var contentVM: ContentViewModel
    @State private var replyText: String = ""
    @State private var isSendingReply = false

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
                        VStack(alignment: .leading, spacing: 20) {
                            postHeader(post)
                            postBody(post)
                            repliesSection
                        }
                        .padding()
                        .padding(.top, 8)
                    }

                    replyInputBar
                }
                .background(Color.brandCardBackground.ignoresSafeArea())
                .navigationTitle("")
                .navigationBarTitleDisplayMode(.inline)
                .task {
                    if let url = contentVM.baseURL {
                        await contentVM.loadReplies(baseURL: url, postId: postId)
                    }
                }
            } else {
                notFound
            }
        }
    }

    // MARK: - Post Header

    private func postHeader(_ post: APICommunityPost) -> some View {
        HStack(spacing: 12) {
            Circle()
                .fill(Color.brandGold.opacity(0.15))
                .frame(width: 48, height: 48)
                .overlay(
                    Text(post.initials)
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(.brandGold)
                )

            VStack(alignment: .leading, spacing: 2) {
                Text(post.name)
                    .font(.headline)
                    .foregroundColor(.brandNavy)

                if let category = contentVM.categories.first(where: { $0.id == post.category }) {
                    Text("\(category.emoji) \(category.name)")
                        .font(.caption)
                        .foregroundColor(.brandGray)
                }
            }
        }
    }

    // MARK: - Post Body

    private func postBody(_ post: APICommunityPost) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(post.title)
                .font(.title3.weight(.bold))
                .foregroundColor(.brandNavy)

            Text(post.preview)
                .font(.body)
                .foregroundColor(.brandNavy.opacity(0.85))
                .lineSpacing(4)
        }
    }

    // MARK: - Replies Section

    private var repliesSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Divider()

            let count = replies.count
            Text(count == 0 ? "No replies yet" : "\(count) \(count == 1 ? "reply" : "replies")")
                .font(.subheadline.weight(.semibold))
                .foregroundColor(.brandGray)

            ForEach(replies) { reply in
                replyCard(reply)
            }
        }
        .padding(.top, 4)
    }

    private func replyCard(_ reply: APIReply) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 10) {
                Circle()
                    .fill(Color.brandGold.opacity(0.15))
                    .frame(width: 32, height: 32)
                    .overlay(
                        Text(reply.initials)
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(.brandGold)
                    )

                Text(reply.authorName)
                    .font(.subheadline.weight(.semibold))
                    .foregroundColor(.brandNavy)

                Spacer()
            }

            Text(reply.body)
                .font(.body)
                .foregroundColor(.brandNavy.opacity(0.85))
                .lineSpacing(3)
        }
        .padding(12)
        .background(Color.brandNavy.opacity(0.03))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    // MARK: - Reply Input Bar

    private var replyInputBar: some View {
        VStack(spacing: 0) {
            Divider()

            HStack(spacing: 10) {
                TextField("Write a reply...", text: $replyText, axis: .vertical)
                    .font(.body)
                    .foregroundColor(.brandNavy)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(Color.brandNavy.opacity(0.05))
                    .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
                    .lineLimit(1...4)

                Button {
                    sendReply()
                } label: {
                    if isSendingReply {
                        ProgressView()
                            .scaleEffect(0.7)
                            .frame(width: 32, height: 32)
                    } else {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.system(size: 30))
                            .foregroundColor(canSendReply ? .brandGold : .brandGray.opacity(0.4))
                    }
                }
                .disabled(!canSendReply)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
        }
        .background(Color.brandCardBackground)
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
        VStack(spacing: 12) {
            Image(systemName: "doc.questionmark")
                .font(.system(size: 40))
                .foregroundColor(.brandGray.opacity(0.5))
            Text("Post not found")
                .font(.subheadline)
                .foregroundColor(.brandGray)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.brandBackground.ignoresSafeArea())
    }
}
