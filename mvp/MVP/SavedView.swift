import SwiftUI

/// The Saved tab: everything the parent bookmarked — articles, community
/// posts, coach replies — merged with the Plan tab's shortlist (origin
/// "plan"). Articles/posts push their detail views via the shared content
/// destinations; coach replies expand inline (their snapshot is the only
/// copy); plan rows hop to the Plan tab (unsaving those is a status change
/// there, not a bookmark).
struct SavedView: View {
    let username: String
    /// Bumped by MainTabView every time this tab is selected, so a save made
    /// elsewhere shows up without a relaunch (the .task(id:) re-fetch rule).
    let refreshToken: Int
    var onOpenPlan: () -> Void

    @EnvironmentObject private var contentVM: ContentViewModel
    @EnvironmentObject private var configuration: ServerConfiguration
    @State private var items: [SavedItem] = []
    @State private var loading = true
    @State private var errorMessage: String?
    @State private var expandedReplies: Set<String> = []

    var body: some View {
        // No NavigationStack of its own. beta-v1 moved Saved out of the tab bar
        // and behind Settings, which already supplies a stack — nesting a
        // second one renders two stacked nav bars. The title and the
        // destination registrations below attach to the enclosing stack.
        Group {
            if loading && items.isEmpty {
                ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if items.isEmpty {
                emptyState
            } else {
                savedList
            }
        }
        .background(Color.bgCanvas.ignoresSafeArea())
        .navigationTitle("Saved")
        .navigationBarTitleDisplayMode(.inline)
        // iOS 26.4 glass chrome: repaint the nav container too — see HearthNavGround.swift.
        .hearthNavGround(.bgCanvas)
        .toolbarBackground(Color.bgCanvas, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
        .withContentNavigationDestinations()
        .task(id: refreshToken) { await load() }
    }

    private var emptyState: some View {
        VStack(spacing: .hearth400) {
            Image(systemName: "bookmark")
                .font(.system(size: 40, weight: .light))
                .foregroundColor(.inkMuted)
            Text("Nothing saved yet")
                .font(.hearthTitleMD)
                .foregroundColor(.inkPrimary)
            Text("Tap the bookmark on any article, community post, or coach reply and it'll wait for you here.")
                .font(.hearthBodySM)
                .foregroundColor(.inkMuted)
                .multilineTextAlignment(.center)
                .padding(.horizontal, .hearth800)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var savedList: some View {
        List {
            if let errorMessage {
                Text(errorMessage).font(.hearthBodySM).foregroundColor(.statusError)
            }
            ForEach(items) { item in
                savedRow(item)
            }
        }
        .listStyle(.plain)
        .refreshable { await load() }
    }

    @ViewBuilder
    private func savedRow(_ item: SavedItem) -> some View {
        switch item.itemType {
        case "article":
            NavigationLink(value: ArticleRoute(id: item.itemRef)) {
                rowLabel(item, icon: "book")
            }
            .swipeActions(edge: .trailing) { unsaveButton(item) }
        // "community_post" rows are deliberately NOT rendered. The public board
        // was retired in beta-v1 sprint 2, so the post can no longer be opened —
        // but the saved rows are the parent's data and are left untouched in
        // DuckDB rather than deleted. They simply don't list.
        case "coach_reply":
            Button {
                withAnimation(.hearthFast) {
                    if expandedReplies.contains(item.id) {
                        expandedReplies.remove(item.id)
                    } else {
                        expandedReplies.insert(item.id)
                    }
                }
            } label: {
                VStack(alignment: .leading, spacing: .hearth300) {
                    rowLabel(item, icon: "message")
                    if expandedReplies.contains(item.id) {
                        Text(item.body)
                            .font(.hearthBodyMD)
                            .foregroundColor(.inkPrimary)
                            .padding(.hearth400)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color.bgElevated)
                            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                    }
                }
            }
            .swipeActions(edge: .trailing) { unsaveButton(item) }
        default:  // "activity" — lives in the Plan tab
            Button {
                onOpenPlan()
            } label: {
                HStack {
                    rowLabel(item, icon: "calendar")
                    Spacer()
                    Text("In Plan")
                        .font(.hearthLabel)
                        .foregroundColor(.inkMuted)
                }
            }
        }
    }

    private func rowLabel(_ item: SavedItem, icon: String) -> some View {
        HStack(spacing: .hearth400) {
            Image(systemName: icon)
                .foregroundColor(.accentDefault)
                .frame(width: 24)
            VStack(alignment: .leading, spacing: 2) {
                Text(item.title)
                    .font(.hearthBodyMD.weight(.semibold))
                    .foregroundColor(.inkPrimary)
                    .lineLimit(2)
                if !item.snippet.isEmpty && item.itemType != "coach_reply" {
                    Text(item.snippet)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkMuted)
                        .lineLimit(1)
                }
                if let kid = item.kidName, !kid.isEmpty {
                    Text("For \(kid)")
                        .font(.hearthCaptionMono)
                        .foregroundColor(.inkMuted)
                }
            }
        }
    }

    private func unsaveButton(_ item: SavedItem) -> some View {
        Button(role: .destructive) {
            Task { await unsave(item) }
        } label: {
            Label("Unsave", systemImage: "bookmark.slash")
        }
    }

    // MARK: - Data

    private func load() async {
        guard let baseURL = configuration.baseURL, !username.isEmpty else { return }
        loading = true
        defer { loading = false }
        do {
            items = try await SavedService.list(userID: username, baseURL: baseURL)
            errorMessage = nil
        } catch {
            errorMessage = "Couldn't load your saved items. Pull to retry."
        }
    }

    private func unsave(_ item: SavedItem) async {
        guard let baseURL = configuration.baseURL else { return }
        let before = items
        items.removeAll { $0.id == item.id }   // optimistic
        do {
            try await SavedService.unsave(itemType: item.itemType, itemRef: item.itemRef,
                                          surface: "saved_tab",
                                          userID: username, baseURL: baseURL)
            contentVM.noteUnsaved(itemType: item.itemType, itemRef: item.itemRef)
        } catch {
            items = before                     // revert + surface, never silent
            errorMessage = "Couldn't remove that. Try again."
        }
    }
}
