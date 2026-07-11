import SwiftUI

struct HomeView: View {
    let username: String
    @EnvironmentObject private var contentVM: ContentViewModel
    @EnvironmentObject private var configuration: ServerConfiguration
    @Environment(\.triggerKidHandoff) private var triggerKidHandoff
    // Set by KidsHomeSection's task hook after /kid-agent/list resolves.
    // Drives whether the greeting's Hand-to-kid CTA renders.
    @AppStorage("has_kid_companions") private var hasKidCompanions: Bool = false
    // The parent's display name for the greeting + avatar. `username` is now an
    // opaque account id (a UUID for sign-in accounts), so it must NOT be shown.
    // Cached across launches; set at onboarding and refreshed from the profile.
    @AppStorage("parent_display_name") private var parentDisplayName: String = ""
    @State private var isShowingSettings = false
    // Bumped when the Settings sheet closes so the Companions list re-fetches —
    // otherwise edits/adds/deletes made in Settings → Profile don't show on Home
    // until the app is relaunched (the section's .task only runs on first appear).
    @State private var homeRefreshToken = 0

    var body: some View {
        NavigationStack {
            Group {
                if contentVM.isLoading {
                    ProgressView()
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    ScrollView {
                        VStack(alignment: .leading, spacing: .hearth800) {
                            greetingHeader
                                .padding(.horizontal, .hearth700)
                                .padding(.top, .hearth300)

                            featuredCard
                                .padding(.horizontal, .hearth700)

                            if let baseURL = configuration.baseURL, !username.isEmpty {
                                KidsHomeSection(userID: username, baseURL: baseURL, refreshToken: homeRefreshToken)
                                    .padding(.horizontal, .hearth700)
                            }

                            CommunitySection(posts: contentVM.randomCommunityPosts())
                                .padding(.leading, .hearth700)

                            LibrarySection(items: contentVM.randomLibraryItems())
                                .padding(.leading, .hearth700)

                            categoriesSection
                                .padding(.horizontal, .hearth700)

                            Spacer(minLength: .hearth600)
                        }
                    }
                }
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            // iOS 17+: .navigationBarHidden(true) is deprecated and leaves
            // the nav-bar's reserved vertical space visible as a band.
            // The toolbar(.hidden) modifier fully collapses it.
            .toolbar(.hidden, for: .navigationBar)
            .withContentNavigationDestinations()
            .task(id: homeRefreshToken) {
                // Resolve the parent's display name from the profile (source of
                // truth). Covers returning users who skipped onboarding, and
                // refreshes after a Settings edit (homeRefreshToken bump).
                guard let baseURL = configuration.baseURL, !username.isEmpty else { return }
                if let profile = try? await ProfileService.getProfile(baseURL: baseURL, userID: username),
                   let name = profile.parent?.name?.trimmingCharacters(in: .whitespaces),
                   !name.isEmpty {
                    parentDisplayName = name
                }
            }
            .sheet(isPresented: $isShowingSettings, onDismiss: { homeRefreshToken += 1 }) {
                NavigationStack {
                    SettingsView(configuration: configuration, userID: username)
                        .navigationTitle("Settings")
                        .navigationBarTitleDisplayMode(.inline)
                        .toolbar {
                            ToolbarItem(placement: .confirmationAction) {
                                Button("Done") { isShowingSettings = false }
                            }
                        }
                }
            }
        }
    }

    // MARK: - Greeting Header

    private var greetingHeader: some View {
        ZStack {
            Image("HomeBanner")
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(height: 180)
                .clipped()
                .overlay(
                    LinearGradient(
                        colors: [.clear, .black.opacity(0.55)],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )

            VStack {
                // Top row: handoff + avatar
                HStack {
                    Spacer()
                    if !username.isEmpty && hasKidCompanions {
                        HandoffEntryButton { triggerKidHandoff() }
                    }
                    // Tap the initial to open Server Settings.
                    Button {
                        isShowingSettings = true
                    } label: {
                        Circle()
                            .fill(Color.white.opacity(0.9))
                            .frame(width: 36, height: 36)
                            .overlay(
                                Text(parentDisplayName.isEmpty ? "?" : String(parentDisplayName.prefix(1)).uppercased())
                                    .font(.hearthLabel)
                                    .foregroundColor(.accentDefault)
                            )
                    }
                    .accessibilityLabel("Settings")
                }

                Spacer()

                // Bottom: greeting
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(greeting)
                            .font(.hearthCaptionMono)
                            .foregroundColor(.white.opacity(0.85))
                        Text(parentDisplayName.isEmpty ? "Welcome" : parentDisplayName)
                            .font(.hearthDisplayMD)
                            .foregroundColor(.white)
                            .shadow(color: .black.opacity(0.6), radius: 3, x: 0, y: 1)
                    }
                    Spacer()
                }
            }
            .padding(.hearth500)
        }
        .frame(height: 180)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
    }

    // MARK: - Featured Card

    @ViewBuilder
    private var featuredCard: some View {
        if let item = contentVM.featuredItem {
            NavigationLink(value: ArticleRoute(id: item.id)) {
                VStack(alignment: .leading, spacing: 0) {
                    ZStack(alignment: .bottomLeading) {
                        if let assetName = articleImageAssets[item.id] {
                            Image(assetName)
                                .resizable()
                                .aspectRatio(contentMode: .fill)
                                .frame(height: 160)
                                .clipped()
                        } else {
                            Color.photoSaffron
                                .frame(height: 160)
                            Text(item.emoji)
                                .font(.system(size: 56))
                                .padding(.hearth600)
                        }
                    }
                    .frame(height: 160)

                    VStack(alignment: .leading, spacing: .hearth300) {
                        Text("Start here today")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        Text(item.title)
                            .font(.hearthTitleLG)
                            .foregroundColor(.inkPrimary)
                            .multilineTextAlignment(.leading)

                        Text(item.subtitle)
                            .font(.hearthBodyMD)
                            .foregroundColor(.inkSecondary)

                        Text("Start here")
                            .font(.hearthTitleMD)
                            .foregroundColor(.inkOnPhotoLight)
                            .padding(.horizontal, .hearth600)
                            .padding(.vertical, .hearth400)
                            .background(Color.accentDefault)
                            .clipShape(Capsule())
                            .padding(.top, .hearth300)
                    }
                    .padding(.hearth500)
                }
                .background(Color.bgElevated)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                        .stroke(Color.borderHairline, lineWidth: 1)
                )
            }
            .buttonStyle(.plain)
        }
    }

    // MARK: - Categories Section

    private var categoriesSection: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            Text("Browse by topic")
                .font(.hearthLabel)
                .foregroundColor(.inkMuted)
                .tracking(0.66)
                .textCase(.uppercase)
                .padding(.leading, .hearth300)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: .hearth400) {
                ForEach(contentVM.topLevelCategories) { category in
                    NavigationLink(value: category.id) {
                        CategoryTile(category: category)
                    }
                    .buttonStyle(.plain)
                }
            }
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
            VStack(alignment: .leading, spacing: .hearth600) {
                let items = contentVM.libraryItems(for: categoryId)
                let posts = contentVM.communityPosts(for: categoryId)

                if !items.isEmpty {
                    Text("Articles")
                        .font(.hearthLabel)
                        .foregroundColor(.inkMuted)
                        .tracking(0.66)
                        .textCase(.uppercase)
                        .padding(.horizontal, .hearth700)

                    ForEach(items) { item in
                        NavigationLink(value: ArticleRoute(id: item.id)) {
                            LibraryItemCard(item: item)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal, .hearth700)
                        }
                        .buttonStyle(.plain)
                    }
                }

                if !posts.isEmpty {
                    Text("Community")
                        .font(.hearthLabel)
                        .foregroundColor(.inkMuted)
                        .tracking(0.66)
                        .textCase(.uppercase)
                        .padding(.horizontal, .hearth700)
                        .padding(.top, .hearth300)

                    ForEach(posts) { post in
                        NavigationLink(value: PostRoute(id: post.id)) {
                            CommunityPostCard(post: post)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal, .hearth700)
                        }
                        .buttonStyle(.plain)
                    }
                }

                Spacer(minLength: .hearth600)
            }
            .padding(.top, .hearth300)
        }
        .background(Color.bgCanvas.ignoresSafeArea())
        .trackScreen("category_detail")
        .navigationTitle(category.map { "\($0.emoji) \($0.name)" } ?? "Category")
        .navigationBarTitleDisplayMode(.large)
        .toolbarBackground(Color.bgCanvas, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
        .withContentNavigationDestinations()
    }
}
