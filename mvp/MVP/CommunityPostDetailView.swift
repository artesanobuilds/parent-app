import SwiftUI

struct CommunityPostDetailView: View {
    let postId: String

    private var post: PostData? {
        ContentStore.shared.postData(postId)
    }

    var body: some View {
        Group {
            if let post = post {
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        // Author header
                        HStack(spacing: 12) {
                            Circle()
                                .fill(Color.brandCoral.opacity(0.15))
                                .frame(width: 48, height: 48)
                                .overlay(
                                    Text(post.initials)
                                        .font(.system(size: 18, weight: .semibold))
                                        .foregroundColor(.brandCoral)
                                )

                            VStack(alignment: .leading, spacing: 2) {
                                Text(post.name)
                                    .font(.headline)
                                    .foregroundColor(.brandNavy)

                                if let category = MockContentProvider.categories.first(where: { $0.id == post.category }) {
                                    Text("\(category.emoji) \(category.name)")
                                        .font(.caption)
                                        .foregroundColor(.brandGray)
                                }
                            }
                        }

                        // Title
                        Text(post.title)
                            .font(.title3.weight(.bold))
                            .foregroundColor(.brandNavy)

                        // Full post text
                        Text(post.preview)
                            .font(.body)
                            .foregroundColor(.brandNavy.opacity(0.85))
                            .lineSpacing(4)

                        // Conversation CTA
                        VStack(spacing: 12) {
                            Divider()

                            HStack(spacing: 8) {
                                Image(systemName: "bubble.left.and.bubble.right")
                                    .foregroundColor(.brandCoral)
                                Text("Join the conversation on this topic with the MVP community")
                                    .font(.subheadline)
                                    .foregroundColor(.brandGray)
                            }
                            .padding(.vertical, 8)
                        }
                        .padding(.top, 8)
                    }
                    .padding()
                    .padding(.top, 8)
                }
                .background(Color.brandBackground.ignoresSafeArea())
                .navigationTitle("")
                .navigationBarTitleDisplayMode(.inline)
            } else {
                notFound
            }
        }
    }

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
