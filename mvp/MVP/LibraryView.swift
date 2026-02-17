import SwiftUI

struct LibraryView: View {
    @State private var selectedCategory: String? = nil

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Category filter chips
                    categoryChips
                        .padding(.top, 8)

                    if let selected = selectedCategory {
                        // Filtered view: show items for selected category
                        let items = MockContentProvider.libraryItems(for: selected)
                        let posts = MockContentProvider.communityPosts(for: selected)
                        let categoryName = MockContentProvider.categories.first { $0.id == selected }?.name ?? ""

                        if !items.isEmpty {
                            sectionHeader("Articles", subtitle: categoryName)
                                .padding(.horizontal)

                            ForEach(items) { item in
                                LibraryItemCard(item: item)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .padding(.horizontal)
                            }
                        }

                        if !posts.isEmpty {
                            sectionHeader("Community", subtitle: categoryName)
                                .padding(.horizontal)
                                .padding(.top, 8)

                            ForEach(posts) { post in
                                CommunityPostCard(post: post)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .padding(.horizontal)
                            }
                        }

                        if items.isEmpty && posts.isEmpty {
                            emptyState(categoryName)
                        }
                    } else {
                        // All categories view: horizontal scroll per category
                        ForEach(MockContentProvider.categories) { category in
                            let items = MockContentProvider.libraryItems(for: category.id)
                            if !items.isEmpty {
                                VStack(alignment: .leading, spacing: 10) {
                                    HStack(spacing: 6) {
                                        Text(category.emoji)
                                            .font(.system(size: 16))
                                        Text(category.name)
                                            .font(.footnote.weight(.semibold))
                                            .foregroundColor(.brandGray)
                                            .textCase(.uppercase)
                                            .tracking(0.5)
                                    }
                                    .padding(.leading)

                                    ScrollView(.horizontal, showsIndicators: false) {
                                        HStack(spacing: 12) {
                                            ForEach(items) { item in
                                                LibraryItemCard(item: item)
                                                    .frame(width: 240)
                                            }
                                        }
                                        .padding(.horizontal)
                                    }
                                }
                            }
                        }
                    }

                    Spacer(minLength: 20)
                }
            }
            .background(Color.brandBackground.ignoresSafeArea())
            .navigationTitle("Library")
            .toolbarBackground(Color.brandBackground, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
        }
    }

    // MARK: - Category Chips

    private var categoryChips: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                chipButton(label: "All", emoji: nil, isSelected: selectedCategory == nil) {
                    withAnimation(.easeInOut(duration: 0.2)) { selectedCategory = nil }
                }

                ForEach(MockContentProvider.categories) { category in
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
            .background(isSelected ? Color.brandCoral : Color.brandCardBackground)
            .foregroundColor(isSelected ? .white : .brandNavy)
            .clipShape(Capsule())
            .overlay(
                Capsule()
                    .stroke(isSelected ? Color.clear : Color.brandNavy.opacity(0.12), lineWidth: 1)
            )
        }
    }

    // MARK: - Helpers

    private func sectionHeader(_ title: String, subtitle: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title)
                .font(.footnote.weight(.semibold))
                .foregroundColor(.brandGray)
                .textCase(.uppercase)
                .tracking(0.5)
            Text(subtitle)
                .font(.headline.weight(.bold))
                .foregroundColor(.brandNavy)
        }
    }

    private func emptyState(_ categoryName: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: "tray")
                .font(.system(size: 32))
                .foregroundColor(.brandGray.opacity(0.5))
            Text("No content yet for \(categoryName)")
                .font(.subheadline)
                .foregroundColor(.brandGray)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }
}
