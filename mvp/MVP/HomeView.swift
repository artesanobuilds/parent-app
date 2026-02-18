import SwiftUI

struct HomeView: View {
    let username: String

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Greeting header
                    greetingHeader
                        .padding(.horizontal)
                        .padding(.top, 8)

                    // Featured hero card
                    featuredCard
                        .padding(.horizontal)

                    // Community section
                    CommunitySection(posts: MockContentProvider.randomCommunityPosts())
                        .padding(.leading)

                    // Library section
                    LibrarySection(items: MockContentProvider.randomLibraryItems())
                        .padding(.leading)

                    // Category grid
                    categoriesSection
                        .padding(.horizontal)

                    Spacer(minLength: 20)
                }
            }
            .background(Color.brandBackground.ignoresSafeArea())
            .navigationBarHidden(true)
            .withContentNavigationDestinations()
        }
    }

    // MARK: - Greeting Header

    private var greetingHeader: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(greeting)
                    .font(.caption)
                    .foregroundColor(.brandGray)
                Text(username.isEmpty ? "Welcome" : username)
                    .font(.title2.weight(.bold))
                    .foregroundColor(.brandNavy)
            }
            Spacer()
            Circle()
                .fill(Color.brandCoral.opacity(0.15))
                .frame(width: 40, height: 40)
                .overlay(
                    Text(username.isEmpty ? "?" : String(username.prefix(1)).uppercased())
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.brandCoral)
                )
        }
    }

    // MARK: - Featured Card

    private var featuredCard: some View {
        let item = MockContentProvider.featuredItem
        return NavigationLink(value: ArticleRoute(id: item.id)) {
            VStack(alignment: .leading, spacing: 0) {
                // Colored top area with emoji
                ZStack(alignment: .bottomLeading) {
                    LinearGradient(
                        colors: [Color.brandCoral.opacity(0.15), Color.brandCoral.opacity(0.08)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                    .frame(height: 160)

                    Text(item.emoji)
                        .font(.system(size: 56))
                        .padding(20)
                }

                // Text area
                VStack(alignment: .leading, spacing: 8) {
                    Text("Start Here Today")
                        .font(.footnote.weight(.semibold))
                        .foregroundColor(.brandCoral)
                        .textCase(.uppercase)
                        .tracking(0.5)

                    Text(item.title)
                        .font(.title3.weight(.bold))
                        .foregroundColor(.brandNavy)
                        .multilineTextAlignment(.leading)

                    Text(item.subtitle)
                        .font(.subheadline)
                        .foregroundColor(.brandGray)

                    Text("Start Here")
                        .font(.subheadline.weight(.semibold))
                        .foregroundColor(.white)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 10)
                        .background(Color.brandNavy)
                        .clipShape(Capsule())
                        .padding(.top, 4)
                }
                .padding(16)
            }
            .background(Color.brandCardBackground)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            .shadow(color: Color.black.opacity(0.06), radius: 12, y: 4)
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(Color.brandNavy.opacity(0.06), lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }

    // MARK: - Categories Section

    private var categoriesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Browse by topic")
                .font(.footnote.weight(.semibold))
                .foregroundColor(.brandGray)
                .textCase(.uppercase)
                .tracking(0.5)
                .padding(.leading, 4)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                ForEach(MockContentProvider.categories) { category in
                    NavigationLink(value: category.id) {
                        HStack(spacing: 8) {
                            Text(category.emoji)
                                .font(.system(size: 20))
                            Text(category.name)
                                .font(.subheadline.weight(.medium))
                                .foregroundColor(.brandNavy)
                                .lineLimit(1)
                            Spacer()
                        }
                        .padding(12)
                        .background(Color.brandCardBackground)
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                        .overlay(
                            RoundedRectangle(cornerRadius: 12, style: .continuous)
                                .stroke(Color.brandNavy.opacity(0.08), lineWidth: 1)
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .navigationDestination(for: String.self) { categoryId in
            CategoryDetailView(categoryId: categoryId)
        }
    }

    // MARK: - Helpers

    private var greeting: String {
        let hour = Calendar.current.component(.hour, from: Date())
        switch hour {
        case 5..<12: return "Good morning"
        case 12..<17: return "Good afternoon"
        default: return "Good evening"
        }
    }
}

// MARK: - Category Detail View

struct CategoryDetailView: View {
    let categoryId: String

    private var category: ContentCategory? {
        MockContentProvider.categories.first { $0.id == categoryId }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                let items = MockContentProvider.libraryItems(for: categoryId)
                let posts = MockContentProvider.communityPosts(for: categoryId)

                if !items.isEmpty {
                    Text("Articles")
                        .font(.footnote.weight(.semibold))
                        .foregroundColor(.brandGray)
                        .textCase(.uppercase)
                        .tracking(0.5)
                        .padding(.horizontal)

                    ForEach(items) { item in
                        NavigationLink(value: ArticleRoute(id: item.id)) {
                            LibraryItemCard(item: item)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal)
                        }
                        .buttonStyle(.plain)
                    }
                }

                if !posts.isEmpty {
                    Text("Community")
                        .font(.footnote.weight(.semibold))
                        .foregroundColor(.brandGray)
                        .textCase(.uppercase)
                        .tracking(0.5)
                        .padding(.horizontal)
                        .padding(.top, 8)

                    ForEach(posts) { post in
                        NavigationLink(value: PostRoute(id: post.id)) {
                            CommunityPostCard(post: post)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal)
                        }
                        .buttonStyle(.plain)
                    }
                }

                Spacer(minLength: 20)
            }
            .padding(.top, 8)
        }
        .background(Color.brandBackground.ignoresSafeArea())
        .navigationTitle(category.map { "\($0.emoji) \($0.name)" } ?? "Category")
        .navigationBarTitleDisplayMode(.large)
        .withContentNavigationDestinations()
    }
}
