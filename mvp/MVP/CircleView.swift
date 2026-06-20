import SwiftUI

struct CircleView: View {
    @EnvironmentObject private var contentVM: ContentViewModel
    @State private var selectedCategory: String? = nil
    @State private var showingNewPost = false

    private var filteredPosts: [APICommunityPost] {
        if let selected = selectedCategory {
            return contentVM.communityPosts.filter { $0.category == selected }
        }
        return contentVM.communityPosts
    }

    /// Categories that actually have community posts.
    private var activeCategories: [APICategory] {
        let postCategoryIds = Set(contentVM.communityPosts.map { $0.category })
        return contentVM.categories.filter { postCategoryIds.contains($0.id) }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Header text
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Real parents. Real questions.")
                            .font(.title3.weight(.bold))
                            .foregroundColor(.inkPrimary)
                        Text("You're not alone in this.")
                            .font(.subheadline)
                            .foregroundColor(.brandGray)
                    }
                    .padding(.horizontal)
                    .padding(.top, 4)

                    // Category filter chips
                    categoryChips

                    // Posts
                    if filteredPosts.isEmpty {
                        emptyState
                    } else {
                        LazyVStack(spacing: 12) {
                            ForEach(filteredPosts) { post in
                                NavigationLink(value: PostRoute(id: post.id)) {
                                    CirclePostCard(post: post)
                                        .padding(.horizontal)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    Spacer(minLength: 20)
                }
                .padding(.top, 8)
            }
            .background(Color.brandBackground.ignoresSafeArea())
            .navigationTitle("Circle")
            .navigationBarTitleDisplayMode(.inline)
            .toolbarBackground(Color.brandBackground, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showingNewPost = true
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .font(.system(size: 22))
                            .foregroundColor(.brandGold)
                    }
                }
            }
            .sheet(isPresented: $showingNewPost) {
                if let url = contentVM.baseURL {
                    NewPostView(baseURL: url)
                }
            }
            .withContentNavigationDestinations()
        }
    }

    // MARK: - Category Chips

    private var categoryChips: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                chipButton(label: "All", emoji: nil, isSelected: selectedCategory == nil) {
                    withAnimation(.easeInOut(duration: 0.2)) { selectedCategory = nil }
                }

                ForEach(activeCategories) { category in
                    chipButton(label: category.name, emoji: category.emoji, isSelected: selectedCategory == category.id) {
                        withAnimation(.easeInOut(duration: 0.2)) {
                            selectedCategory = selectedCategory == category.id ? nil : category.id
                        }
                    }
                }
            }
            .padding(.horizontal)
        }
    }

    private func chipButton(label: String, emoji: String?, isSelected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 4) {
                if let emoji = emoji {
                    Text(emoji).font(.system(size: 14))
                }
                Text(label)
                    .font(.caption.weight(.medium))
                    .lineLimit(1)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(isSelected ? Color.accentDefault : Color.bgElevated)
            .foregroundColor(isSelected ? .inkOnPhotoLight : .inkPrimary)
            .clipShape(Capsule())
            .overlay(
                Capsule()
                    .stroke(isSelected ? Color.clear : Color.brandStroke, lineWidth: 1)
            )
        }
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "bubble.left.and.bubble.right")
                .font(.system(size: 32))
                .foregroundColor(.brandGray.opacity(0.5))
            Text("No posts in this category yet")
                .font(.subheadline)
                .foregroundColor(.brandGray)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }
}

// MARK: - Circle Post Card (full-width community card)

struct CirclePostCard: View {
    let post: APICommunityPost
    @EnvironmentObject private var contentVM: ContentViewModel

    private var category: APICategory? {
        contentVM.categories.first { $0.id == post.category }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Author row
            HStack(spacing: 10) {
                Circle()
                    .fill(Color.brandGold.opacity(0.15))
                    .frame(width: 40, height: 40)
                    .overlay(
                        Text(post.initials)
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.brandGold)
                    )

                VStack(alignment: .leading, spacing: 1) {
                    Text(post.name)
                        .font(.subheadline.weight(.semibold))
                        .foregroundColor(.brandNavy)

                    if let category = category {
                        Text("\(category.emoji) \(category.name)")
                            .font(.caption2)
                            .foregroundColor(.brandGray)
                    }
                }

                Spacer()
            }

            // Title
            Text(post.title)
                .font(.headline)
                .foregroundColor(.brandNavy)
                .multilineTextAlignment(.leading)

            // Preview
            Text(post.preview)
                .font(.subheadline)
                .foregroundColor(.brandNavy.opacity(0.75))
                .lineSpacing(2)
                .multilineTextAlignment(.leading)

            // Engagement row
            HStack(spacing: 20) {
                let count = post.replyCount ?? 0
                Label(count > 0 ? "\(count) \(count == 1 ? "reply" : "replies")" : "Reply", systemImage: "bubble.left")
                Label("Support", systemImage: "heart")
            }
            .font(.caption)
            .foregroundColor(.brandGray)
            .padding(.top, 2)
        }
        .padding(16)
        .background(Color.brandCardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .shadow(color: Color.black.opacity(0.3), radius: 8, y: 3)
        .overlay(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .stroke(Color.brandStroke, lineWidth: 1)
        )
    }
}
