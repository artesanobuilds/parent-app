import SwiftUI

// MARK: - Community Post Card

struct CommunityPostCard: View {
    let post: CommunityPost

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Avatar + name row
            HStack(spacing: 8) {
                Circle()
                    .fill(Color.brandCoral.opacity(0.15))
                    .frame(width: 32, height: 32)
                    .overlay(
                        Text(post.initials)
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(.brandCoral)
                    )
                Text(post.name)
                    .font(.subheadline.weight(.semibold))
                    .foregroundColor(.brandNavy)
            }

            // Title
            Text(post.title)
                .font(.subheadline.weight(.bold))
                .foregroundColor(.brandNavy)
                .lineLimit(2)

            // Preview text
            Text(post.preview)
                .font(.caption)
                .foregroundColor(.brandGray)
                .lineLimit(3)
        }
        .padding(14)
        .background(Color.brandCardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .shadow(color: Color.black.opacity(0.06), radius: 8, y: 3)
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .stroke(Color.brandNavy.opacity(0.08), lineWidth: 1)
        )
    }
}

// MARK: - Library Item Card

struct LibraryItemCard: View {
    let item: LibraryItem

    var body: some View {
        HStack(spacing: 12) {
            // Emoji thumbnail
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .fill(Color.brandLightBlue)
                .frame(width: 56, height: 56)
                .overlay(
                    Text(item.emoji)
                        .font(.system(size: 26))
                )

            // Title + Subtitle
            VStack(alignment: .leading, spacing: 2) {
                Text(item.title)
                    .font(.subheadline.weight(.semibold))
                    .foregroundColor(.brandNavy)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)
                Text(item.subtitle)
                    .font(.caption)
                    .foregroundColor(.brandGray)
                    .lineLimit(1)
            }

            Spacer(minLength: 0)
        }
        .padding(10)
        .background(Color.brandCardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .shadow(color: Color.black.opacity(0.06), radius: 8, y: 3)
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .stroke(Color.brandNavy.opacity(0.08), lineWidth: 1)
        )
    }
}

// MARK: - Content Sections

struct CommunitySection: View {
    let posts: [CommunityPost]

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Connect in the community")
                .font(.footnote.weight(.semibold))
                .foregroundColor(.brandGray)
                .textCase(.uppercase)
                .tracking(0.5)
                .padding(.leading, 4)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(posts) { post in
                        NavigationLink(value: PostRoute(id: post.id)) {
                            CommunityPostCard(post: post)
                                .frame(width: 220)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }
}

struct LibrarySection: View {
    let items: [LibraryItem]

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Explore the library")
                .font(.footnote.weight(.semibold))
                .foregroundColor(.brandGray)
                .textCase(.uppercase)
                .tracking(0.5)
                .padding(.leading, 4)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(items) { item in
                        NavigationLink(value: ArticleRoute(id: item.id)) {
                            LibraryItemCard(item: item)
                                .frame(width: 240)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }
}

// MARK: - Navigation Destination Modifier

extension View {
    func withContentNavigationDestinations() -> some View {
        self
            .navigationDestination(for: ArticleRoute.self) { route in
                ArticleDetailView(articleId: route.id)
            }
            .navigationDestination(for: PostRoute.self) { route in
                CommunityPostDetailView(postId: route.id)
            }
    }
}

// MARK: - Feedback Row

struct FeedbackRow: View {
    var body: some View {
        HStack(spacing: 16) {
            Spacer()
            Button {
                // Placeholder action
            } label: {
                Image(systemName: "hand.thumbsup")
                    .font(.system(size: 18))
                    .foregroundColor(.brandGray.opacity(0.7))
            }
            Button {
                // Placeholder action
            } label: {
                Image(systemName: "hand.thumbsdown")
                    .font(.system(size: 18))
                    .foregroundColor(.brandGray.opacity(0.7))
            }
            Spacer()
        }
        .padding(.vertical, 4)
    }
}
