import SwiftUI

/// The avatar / account sheet — Sprint-1 gap in `docs/design/beta-v1-sprint2.md`
/// ("the avatar / account sheet"). Presented from `HomeView`'s header avatar.
///
/// The Figma spec shows three states (account01/02/03); this is ONE view that
/// adapts — the greeting subtitle and the Saved/History content change with
/// what's actually loaded, rather than three near-duplicate screens. The
/// "In your Circle" section from account03 is deliberately NOT built here:
/// Circle's DM data model lives in `CircleView.swift`, which this slice must
/// not touch — folding it in would mean a second, parallel read of Circle
/// state (see `feedback_standalone_flows`).
///
/// HISTORY IS A PROXY: this app has no article-view log today. "History"
/// renders the same saved articles as "Saved", just ordered by recency —
/// there is nothing else to show it. See the PR report for the flag to the
/// orchestrator.
struct AccountSheetView: View {
    let userID: String
    let parentDisplayName: String

    @EnvironmentObject private var contentVM: ContentViewModel
    @EnvironmentObject private var configuration: ServerConfiguration
    @EnvironmentObject private var session: AppSession
    @Environment(\.dismiss) private var dismiss

    enum Tab { case saved, history }

    @State private var tab: Tab = .saved
    @State private var savedItems: [SavedItem] = []
    @State private var articleMeta: [String: APIArticle] = [:]
    @State private var loading = true
    @State private var selectedInterests: Set<String> = []
    @State private var interestError: String?
    @State private var showingLogoutConfirm = false

    private var firstName: String {
        parentDisplayName.split(separator: " ").first.map(String.init) ?? ""
    }

    /// Only articles render as cards (the design's full-bleed teal treatment
    /// is article-specific); community posts / coach replies / plan rows stay
    /// in the existing Saved TAB under Settings.
    private var savedArticles: [SavedItem] {
        savedItems.filter { $0.itemType == "article" }
    }

    private var historyArticles: [SavedItem] {
        savedArticles.sorted { ($0.savedAt ?? "") > ($1.savedAt ?? "") }
    }

    private var hasActivity: Bool { !savedArticles.isEmpty }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: .hearth700) {
                    header
                    tabToggle
                    activityContent
                    interestsSection
                    accountSection
                }
                // ~30pt on every edge, per the Figma sheet (`account 02`).
                .padding(.horizontal, .hearth800)
                .padding(.top, .hearth800)
                .padding(.bottom, .hearth800)
            }
            // `bgCard` (#F5F3EF), NOT `bgCanvas` — the sheet reads as lifted off
            // the page behind it, and the design uses a lighter cream to do it.
            .background(Color.bgCard.ignoresSafeArea())
            .toolbar(.hidden, for: .navigationBar)
            .withContentNavigationDestinations()
            .safeAreaInset(edge: .bottom) { footer }
        }
        .task { await load() }
        .alert("Something went wrong",
               isPresented: Binding(get: { interestError != nil },
                                    set: { if !$0 { interestError = nil } })) {
            Button("OK") { interestError = nil }
        } message: {
            Text(interestError ?? "")
        }
        .confirmationDialog("Log out of MVP?",
                            isPresented: $showingLogoutConfirm,
                            titleVisibility: .visible) {
            Button("Log out", role: .destructive) {
                dismiss()
                Task { await session.signOut(userID: userID, baseURL: configuration.baseURL) }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("You'll need to sign in again to get back to your family's plan.")
        }
        .onAppear { Analytics.capture("account_sheet_shown", [:]) }
    }

    // MARK: - Load

    private func load() async {
        guard let baseURL = configuration.baseURL, !userID.isEmpty else { loading = false; return }
        async let itemsTask = try? SavedService.list(userID: userID, baseURL: baseURL)
        async let profileTask = try? ProfileService.getProfile(baseURL: baseURL, userID: userID)
        let items = await itemsTask ?? []
        savedItems = items
        if let activities = await profileTask?.parent?.familyActivities {
            selectedInterests = Set(activities)
        }
        // Resolve category/read-time for each saved article. Small N (a
        // parent's saved list), sequential awaits are fine — no need for a
        // TaskGroup here.
        for item in items where item.itemType == "article" {
            if let cached = contentVM.articleData(item.itemRef) {
                articleMeta[item.itemRef] = cached
            } else if let fetched = await contentVM.fetchArticleDetail(baseURL: baseURL, id: item.itemRef) {
                articleMeta[item.itemRef] = fetched
            }
        }
        loading = false
    }

    private func categoryName(for id: String) -> String {
        contentVM.categories.first(where: { $0.id == id })?.name ?? id.capitalized
    }

    // MARK: - Header

    private var header: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            // Fraunces w700 38/40 — the design's editorial headline. Was
            // `hearthDisplayMD` (28/600), two steps too small.
            Text(firstName.isEmpty ? "Hi there!" : "Hi \(firstName)!")
                .font(.hearthDisplaySM)
                .tracking(-0.38)
                .foregroundColor(.inkDisplay)
            Text(hasActivity
                 ? "Browse your recent activity"
                 : "No recent activity. Your history and saved articles can be found here.")
                .font(.hearthBodySM)
                .foregroundColor(.inkDisplay)
        }
    }

    // MARK: - Saved | History toggle

    private var tabToggle: some View {
        HStack(spacing: .hearth300) {
            tabButton(.saved, label: "Saved")
            tabButton(.history, label: "History")
        }
    }

    /// Label-only, radius 10, selected = `bgSelected` with a TEAL label.
    ///
    /// Three corrections off the Figma: the design's buttons carry no leading
    /// icon, the corner is a 10pt radius rather than a capsule, and the selected
    /// state is the pale `#DAE0DF` ground with teal text — not a solid teal fill
    /// with white text, which read far heavier than the design.
    private func tabButton(_ value: Tab, label: String) -> some View {
        Button { tab = value } label: {
            Text(label)
                .font(.hearthButtonLabel)
                .foregroundColor(.accentOnCanvas)
                .frame(maxWidth: .infinity)
                .padding(.horizontal, .hearth400)
                .padding(.vertical, .hearth300)
                .background(
                    RoundedRectangle(cornerRadius: .hearthRadiusControl, style: .continuous)
                        .fill(tab == value ? Color.bgSelected : Color.bgElevated)
                )
        }
        .buttonStyle(.plain)
    }

    // MARK: - Saved / History content

    @ViewBuilder
    private var activityContent: some View {
        if loading {
            ProgressView().frame(maxWidth: .infinity).padding(.vertical, .hearth600)
        } else {
            let list = tab == .saved ? savedArticles : historyArticles
            if list.isEmpty {
                Text("Nothing saved yet. Tap the bookmark on any article and it'll wait for you here.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
            } else {
                VStack(alignment: .leading, spacing: .hearth400) {
                    // History has no article-view log today — this is the
                    // saved list, just ordered by recency. Said out loud so a
                    // parent seeing identical cards in both tabs isn't
                    // confused into thinking something's broken.
                    if tab == .history {
                        Text("Showing your saved articles, most recent first")
                            .font(.hearthCaptionMono)
                            .foregroundColor(.inkMuted)
                    }
                    ForEach(list) { item in
                        SavedArticleCard(
                            item: item,
                            meta: articleMeta[item.itemRef],
                            categoryName: categoryName(for:),
                            onUnsave: { unsave(item) }
                        )
                    }
                }
            }
        }
    }

    private func unsave(_ item: SavedItem) {
        savedItems.removeAll { $0.id == item.id }
        contentVM.toggleSaved(itemType: "article", itemRef: item.itemRef, surface: "account_sheet") { message in
            interestError = message
        }
    }

    // MARK: - Family interests

    private var interestsSection: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            // Inter w700 13, `inkHeader`, mixed case, NO icon — the sheet's own
            // header style, which differs from the dashboard masthead
            // (`hearthSectionHeader`). Verified separately against `account 02`.
            HStack {
                Text("Family interests")
                    .font(.hearthBodySMBold)
                    .foregroundColor(.inkHeader)
                Spacer(minLength: .hearth400)
                // Every known option already fits in the grid below — no
                // destination to push to yet. Same stubbed-CTA pattern as
                // HomeView's first-run "Add event" row.
                Text("See all")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkHeader)
                    .accessibilityHint("Not yet available")
            }
            LazyVGrid(
                columns: Array(repeating: GridItem(.flexible(), spacing: .hearth300), count: 3),
                spacing: .hearth300
            ) {
                ForEach(ProfileOptions.familyActivityOptions, id: \.label) { option in
                    InterestTile(
                        label: option.label,
                        symbol: option.symbol,
                        selected: selectedInterests.contains(option.label),
                        action: { toggleInterest(option.label) }
                    )
                }
            }
        }
    }

    private func toggleInterest(_ label: String) {
        guard let baseURL = configuration.baseURL, !userID.isEmpty else { return }
        let wasSelected = selectedInterests.contains(label)
        if wasSelected { selectedInterests.remove(label) } else { selectedInterests.insert(label) }
        let updated = Array(selectedInterests)
        Task {
            do {
                try await ProfileService.updateParent(
                    baseURL: baseURL, userID: userID, fields: ["family_activities": updated]
                )
            } catch {
                if wasSelected { selectedInterests.insert(label) } else { selectedInterests.remove(label) }
                interestError = "Couldn't update your family interests. Try again."
            }
        }
    }

    // MARK: - Account

    private var accountSection: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            Text("Account")
                .font(.hearthBodySMBold)
                .foregroundColor(.inkHeader)
            accountCard
        }
    }

    private var accountCard: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            // MVP Email / Password / Plan / Billing have no backing field
            // anywhere in the app today (no auth email, no billing state) —
            // per CLAUDE.md, omitted rather than faked. Username is the
            // parent's profile display name, the closest real identity value.
            if !parentDisplayName.isEmpty {
                accountRow(label: "Username", value: parentDisplayName)
            }
        }
        .padding(.hearth600)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: .hearthRadiusCard, style: .continuous)
                .fill(Color.bgElevated)
        )
    }

    private func accountRow(label: String, value: String) -> some View {
        HStack {
            Text(label)
                .font(.hearthBodySM)
                .foregroundColor(.inkMuted)
            Spacer()
            Text(value)
                .font(.hearthBodyMD.weight(.semibold))
                .foregroundColor(.inkPrimary)
        }
    }

    // MARK: - Footer

    private var footer: some View {
        HStack(spacing: .hearth400) {
            // Solid teal fill with a white w800 label, per the design — the
            // `.bordered` style rendered a tinted-translucent button instead.
            Button { dismiss() } label: {
                Text("Cancel")
                    .font(.hearthButtonLabel)
                    .foregroundColor(.inkOnPhotoLight)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, .hearth300)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusControl, style: .continuous)
                            .fill(Color.accentDefault)
                    )
            }
            .buttonStyle(.plain)

            // Grey, per the design — NOT `.statusError`. Flagged to Greg: a grey
            // button reads as DISABLED on iOS, where destructive actions are
            // conventionally red. Implemented as drawn pending his answer.
            Button { showingLogoutConfirm = true } label: {
                Text("Sign out")
                    .font(.hearthButtonLabel)
                    .foregroundColor(.inkOnPhotoLight)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, .hearth300)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusControl, style: .continuous)
                            .fill(Color.bgNeutral)
                    )
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, .hearth800)
        .padding(.vertical, .hearth500)
        .background(Color.bgCard)
        .disabled(session.isWorking)
    }
}

// MARK: - Saved article card (full-bleed teal)

private struct SavedArticleCard: View {
    let item: SavedItem
    let meta: APIArticle?
    let categoryName: (String) -> String
    let onUnsave: () -> Void

    private var eyebrow: String {
        guard let meta else { return "" }
        return "\(categoryName(meta.category)) · \(meta.readTime)"
    }

    var body: some View {
        NavigationLink(value: ArticleRoute(id: item.itemRef)) {
            VStack(alignment: .leading, spacing: .hearth300) {
                HStack(alignment: .top) {
                    if !eyebrow.isEmpty {
                        // Inter w700 13, SOLID `cardCream`. The 0.85 opacity this
                        // carried is what made the cards look washed — the design
                        // has no transparency on card text.
                        Text(eyebrow)
                            .font(.hearthBodySMBold)
                            .foregroundColor(.inkOnCard)
                    }
                    Spacer(minLength: .hearth300)
                    Button(action: onUnsave) {
                        Image(systemName: "bookmark.fill")
                            .foregroundColor(.inkOnCard)
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("Remove from saved")
                }
                Text(meta?.title ?? item.title)
                    .font(.hearthDisplaySM)
                    .tracking(-0.38)
                    .foregroundColor(.inkOnCard)
                    .lineLimit(3)
                if !item.snippet.isEmpty {
                    Text(item.snippet)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkOnCard)
                        .lineLimit(2)
                }
            }
            .padding(.hearth600)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.accentDefault)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusCard, style: .continuous))
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Family interest tile

private struct InterestTile: View {
    let label: String
    let symbol: String
    let selected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: .hearth300) {
                Image(systemName: symbol)
                    .font(.system(size: 20, weight: .medium))
                Text(label)
                    .font(.hearthBodySMBold)
                    .multilineTextAlignment(.center)
                    .lineLimit(2)
                    .fixedSize(horizontal: false, vertical: true)
            }
            // Selected = teal fill + white icon/label; unselected = white
            // card with teal icon/label. Same pass ratio as the onboarding
            // free-time grid this reuses (`accentDefault` as ink on `bg/
            // elevated` paper is a declared AA pass there).
            .foregroundColor(selected ? .inkOnCard : .accentDefault)
            // The design's tiles HUG their content (~27pt above / 20pt below,
            // vertical auto-layout, no fixed height) — the 119.8pt in the file is
            // the result, not a constraint. Pinning `minHeight: 120` floated the
            // icon and label to the top and left dead space beneath them.
            .frame(maxWidth: .infinity)
            .padding(.top, .hearth700)
            .padding(.bottom, .hearth600)
            .background(selected ? Color.accentDefault : Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusControl, style: .continuous))
        }
        .buttonStyle(.plain)
    }
}
