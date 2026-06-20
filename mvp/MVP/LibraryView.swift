import SwiftUI

/// LibraryView — editorial-first browse.
///
/// Redesign (June 2026, after Rams/Pentagram critique + UXR research):
/// - No top filter strips. The previous design stacked category chips +
///   auto-derived tag pills — two navigation rows pretending to be filters.
///   Chips/pills filter within a context (Material 3) but here they were
///   doing two different jobs.
/// - Editorial-first single scroll: hero "This Week" → 11 parent tiles →
///   recently published. The grid IS the navigation; no carousel chip row.
/// - Tags disappear from the top. They live on article detail + (future)
///   a Search sheet from the nav-bar magnifying-glass icon.
/// - Community lives at its own CIRCLE tab; LibraryView is editorial only.
struct LibraryView: View {
    @EnvironmentObject private var contentVM: ContentViewModel
    @EnvironmentObject private var configuration: ServerConfiguration


    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: .hearth1000) {
                    heroCard
                        .padding(.horizontal, .hearth700)
                        .padding(.top, .hearth500)

                    parentGrid
                        .padding(.horizontal, .hearth700)

                    recentlyPublished
                        .padding(.horizontal, .hearth700)

                    Spacer(minLength: .hearth700)
                }
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .navigationTitle("Library")
            .navigationBarTitleDisplayMode(.inline)
            .toolbarBackground(Color.bgCanvas, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .withContentNavigationDestinations()
        }
    }

    // MARK: - Hero "This Week"

    @ViewBuilder
    private var heroCard: some View {
        if let item = featuredItem {
            NavigationLink(value: ArticleRoute(id: item.id)) {
                VStack(alignment: .leading, spacing: 0) {
                    ZStack(alignment: .bottomLeading) {
                        if let assetName = articleImageAssets[item.id] {
                            Image(assetName)
                                .resizable()
                                .aspectRatio(contentMode: .fill)
                                .frame(height: 200)
                                .clipped()
                        } else {
                            Color.photoSaffron
                                .frame(height: 200)
                            Text(item.emoji)
                                .font(.system(size: 64))
                                .padding(.hearth600)
                        }
                    }
                    .frame(height: 200)

                    VStack(alignment: .leading, spacing: .hearth300) {
                        Text("This week")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        Text(item.title)
                            .font(.hearthDisplayMD)
                            .foregroundColor(.inkPrimary)
                            .multilineTextAlignment(.leading)

                        Text(item.subtitle)
                            .font(.hearthBodyMD)
                            .foregroundColor(.inkSecondary)
                            .lineLimit(3)
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

    // MARK: - 11 parent-category tiles

    private var parentGrid: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            Text("Browse by topic")
                .font(.hearthLabel)
                .foregroundColor(.inkMuted)
                .tracking(0.66)
                .textCase(.uppercase)

            LazyVGrid(
                columns: [GridItem(.flexible(), spacing: .hearth400), GridItem(.flexible())],
                spacing: .hearth400
            ) {
                ForEach(contentVM.topLevelCategories) { category in
                    NavigationLink(value: category.id) {
                        CategoryTile(category: category)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    // MARK: - Recently published

    private var recentlyPublished: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            Text("Recently published")
                .font(.hearthLabel)
                .foregroundColor(.inkMuted)
                .tracking(0.66)
                .textCase(.uppercase)

            // We don't have a real "published_at" wire field yet — take the
            // last 6 articles by load order as a stand-in. When backend
            // ships a published_at, sort by that descending here.
            let recent = Array(contentVM.libraryItems.prefix(6))
            VStack(spacing: .hearth400) {
                ForEach(recent) { item in
                    NavigationLink(value: ArticleRoute(id: item.id)) {
                        LibraryItemCard(item: item)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    // MARK: - Helpers

    /// Pick a featured article for the "This week" hero. Prefers an article
    /// in the Inner Life / Raising Kids parents; falls back to the first
    /// available. Stable across loads (no shuffle) so the hero doesn't
    /// flicker between scrolls.
    private var featuredItem: APIArticle? {
        let priorities = ["raising-kids", "family-life", "inner-life", "emotional-wellness"]
        for p in priorities {
            if let match = contentVM.libraryItems.first(where: { $0.category == p }) {
                return match
            }
        }
        return contentVM.libraryItems.first
    }
}
