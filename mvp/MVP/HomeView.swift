import SwiftUI

struct HomeView: View {
    let username: String
    @EnvironmentObject private var contentVM: ContentViewModel
    @Environment(\.triggerKidHandoff) private var triggerKidHandoff

    var body: some View {
        NavigationStack {
            Group {
                if contentVM.isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    ScrollView {
                        VStack(alignment: .leading, spacing: 24) {
                            greetingHeader
                                .padding(.horizontal)
                                .padding(.top, 8)

                            featuredCard
                                .padding(.horizontal)

                            if let baseURL = ServerConfiguration().baseURL, !username.isEmpty {
                                KidsHomeSection(userID: username, baseURL: baseURL)
                                    .padding(.horizontal)
                            }

                            CommunitySection(posts: contentVM.randomCommunityPosts())
                                .padding(.leading)

                            LibrarySection(items: contentVM.randomLibraryItems())
                                .padding(.leading)

                            categoriesSection
                                .padding(.horizontal)

                            Spacer(minLength: 20)
                        }
                    }
                }
            }
            .background(Color.brandBackground.ignoresSafeArea())
            .navigationBarHidden(true)
            .withContentNavigationDestinations()
        }
    }

    // MARK: - Greeting Header

    private var greetingHeader: some View {
        HStack(spacing: 10) {
            VStack(alignment: .leading, spacing: 2) {
                Text(greeting)
                    .font(.caption)
                    .foregroundColor(.brandGray)
                Text(username.isEmpty ? "Welcome" : username)
                    .font(.title2.weight(.bold))
                    .foregroundColor(.white)
            }
            Spacer()
            if !username.isEmpty {
                HandoffEntryButton { triggerKidHandoff() }
            }
            Circle()
                .fill(Color.brandGold.opacity(0.2))
                .frame(width: 40, height: 40)
                .overlay(
                    Text(username.isEmpty ? "?" : String(username.prefix(1)).uppercased())
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.brandGold)
                )
        }
    }

    // MARK: - Featured Card

    @ViewBuilder
    private var featuredCard: some View {
        if let item = contentVM.featuredItem {
            NavigationLink(value: ArticleRoute(id: item.id)) {
                VStack(alignment: .leading, spacing: 0) {
                    ZStack(alignment: .bottomLeading) {
                        LinearGradient(
                            colors: [Color.brandGold.opacity(0.25), Color.brandGold.opacity(0.10)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                        .frame(height: 160)

                        Text(item.emoji)
                            .font(.system(size: 56))
                            .padding(20)
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        Text("Start Here Today")
                            .font(.footnote.weight(.semibold))
                            .foregroundColor(.brandGold)
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
                            .foregroundColor(.brandBlack)
                            .padding(.horizontal, 20)
                            .padding(.vertical, 10)
                            .background(Color.brandGold)
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
                        .stroke(Color.white.opacity(0.06), lineWidth: 1)
                )
            }
            .buttonStyle(.plain)
        }
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
                ForEach(contentVM.categories) { category in
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
                                .stroke(Color.white.opacity(0.08), lineWidth: 1)
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
    @EnvironmentObject private var contentVM: ContentViewModel

    private var category: APICategory? {
        contentVM.categories.first { $0.id == categoryId }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                let items = contentVM.libraryItems(for: categoryId)
                let posts = contentVM.communityPosts(for: categoryId)

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
