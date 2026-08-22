import SwiftUI

/// The avatar / account sheet — beta-v1 sprint-1 `account01` / `account 02` /
/// `account 03`, presented from `HomeView`'s header avatar.
///
/// THREE STATES, all built, and the segmented control really switches them:
///
///   `account01` — nothing yet. "No recent activity. Your history and saved
///                 articles can be found here.", neither segment filled, then
///                 Family interests, then the Account card + Cancel / Sign out.
///   `account 02` — **Saved** selected: the teal r18 article cards, each with an
///                 eyebrow (`Care · 2 min`), a Fraunces 38/40 headline and a
///                 working bookmark, then Family interests, then Account.
///   `account 03` — **History** selected: `In your Circle` rows (title, "M
///                 started this — 4 replies", an avatar stack) with a
///                 **Go to Circle** link, then `Coach advice` rows with a
///                 **Chat with the coach** link, then Family interests, Account.
///
/// Family interests is ALWAYS shown (Miguel's 2026-08-09 rule) — a family with
/// no preferences yet sees every tile unselected and tappable, not a hidden
/// section. `account 03`'s measured grid (`round3_spec.txt`, node
/// `I1008:5182;1008:4889`) is the fidelity target for `InterestTile` regardless
/// of which account state is showing.
///
/// History is REAL history now, not a re-ordering of Saved: the Circle rows are
/// the parent's own conversations (`GET /circle/conversations`) and the coach
/// rows are their past coach threads (`GET /coach/threads`). Every row opens the
/// thing it names, in this sheet's own navigation stack.
struct AccountSheetView: View {
    let userID: String
    let parentDisplayName: String

    @EnvironmentObject private var contentVM: ContentViewModel
    @EnvironmentObject private var configuration: ServerConfiguration
    @EnvironmentObject private var session: AppSession
    @Environment(\.dismiss) private var dismiss
    // Smoke-and-mirrors paywall pick, persisted at Buy-tap (PaywallView) —
    // display-only, nothing charged. Same keys FamilySettingsView reads.
    @AppStorage("picked_plan_name") private var pickedPlanName = ""
    @AppStorage("picked_plan_billing") private var pickedPlanBilling = ""

    enum Tab { case saved, history }

    /// nil = `account01`'s "nothing picked yet". Resolved to `.saved` the moment
    /// the parent taps a segment.
    @State private var tab: Tab?
    @State private var savedItems: [SavedItem] = []
    @State private var articleMeta: [String: APIArticle] = [:]
    @State private var conversations: [CircleConversation] = []
    @State private var coachThreads: [CoachThreadSummary] = []
    @State private var loading = true
    @State private var selectedInterests: Set<String> = []
    @State private var interestError: String?
    @State private var showingLogoutConfirm = false
    /// The in-sheet coach surface, built lazily so opening the sheet doesn't
    /// spin up a chat view model nobody asked for.
    @State private var coachVM: ChatViewModel?
    @State private var openingThreadID: String?
    @State private var route: AccountRoute?

    /// Where a History row goes. Both destinations live in THIS sheet's stack —
    /// the sheet can't switch tabs, and a row that silently did nothing would be
    /// exactly the dead affordance this pass exists to remove.
    private enum AccountRoute: Hashable {
        case circleThread(String)
        case coach
    }

    private var firstName: String {
        parentDisplayName.split(separator: " ").first.map(String.init) ?? ""
    }

    /// Only articles render as cards (the design's full-bleed teal treatment
    /// is article-specific); community posts / coach replies / plan rows stay
    /// in the existing Saved TAB under Settings.
    private var savedArticles: [SavedItem] {
        savedItems.filter { $0.itemType == "article" }
    }

    /// `account01` is the state where there is nothing in EITHER segment.
    private var hasActivity: Bool {
        !savedArticles.isEmpty || !conversations.isEmpty || !coachThreads.isEmpty
    }

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
            .navigationDestination(item: $route) { destination in
                routeDestination(destination)
            }
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

    @ViewBuilder
    private func routeDestination(_ destination: AccountRoute) -> some View {
        switch destination {
        case .circleThread(let id):
            CircleThreadView(conversationId: id, userID: userID,
                             baseURL: configuration.baseURL,
                             onNotFound: { route = nil })
        case .coach:
            if let coachVM {
                AgentView(viewModel: coachVM, configuration: configuration)
            }
        }
    }

    // MARK: - Load

    private func load() async {
        guard let baseURL = configuration.baseURL, !userID.isEmpty else { loading = false; return }
        async let itemsTask = try? SavedService.list(userID: userID, baseURL: baseURL)
        async let profileTask = try? ProfileService.getProfile(baseURL: baseURL, userID: userID)
        async let conversationsTask = try? CircleService.conversations(userID: userID,
                                                                      baseURL: baseURL)
        async let threadsTask = try? CoachThreadService.threads(userID: userID, baseURL: baseURL)
        let items = await itemsTask ?? []
        savedItems = items
        conversations = await conversationsTask ?? []
        coachThreads = await threadsTask ?? []
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
            // Fraunces w700 38/40 — the design's editorial headline.
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
            tabButton(.saved, label: "Saved", symbol: "bookmark")
            tabButton(.history, label: "History", symbol: "clock.arrow.circlepath")
        }
    }

    /// Radius 10; selected = the pale `#DAE0DF` ground with a teal label, per
    /// `account 02`/`03`. In `account01` NEITHER is filled, which is exactly
    /// what `tab == nil` renders.
    private func tabButton(_ value: Tab, label: String, symbol: String) -> some View {
        Button { tab = value } label: {
            HStack(spacing: .hearth300) {
                Image(systemName: symbol)
                    .font(.system(size: 14, weight: .regular))
                Text(label)
                    .font(.hearthButtonLabel)
            }
            .foregroundColor(.accentOnCanvas)
            .frame(maxWidth: .infinity)
            .padding(.horizontal, .hearth400)
            .padding(.vertical, .hearth300)
            .background(
                RoundedRectangle(cornerRadius: .hearthRadiusControl, style: .continuous)
                    .fill(tab == value ? Color.bgSelected : Color.bgElevated)
                    .overlay(
                        RoundedRectangle(cornerRadius: .hearthRadiusControl, style: .continuous)
                            .stroke(Color.accentDefault, lineWidth: 0.83)
                    )
            )
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(tab == value ? [.isSelected] : [])
    }

    // MARK: - Saved / History content

    @ViewBuilder
    private var activityContent: some View {
        if loading {
            ProgressView().frame(maxWidth: .infinity).padding(.vertical, .hearth600)
        } else {
            switch tab {
            case .none:      EmptyView()          // `account01`
            case .saved:     savedList            // `account 02`
            case .history:   historyList          // `account 03`
            }
        }
    }

    // MARK: `account 02` — Saved

    @ViewBuilder
    private var savedList: some View {
        if savedArticles.isEmpty {
            Text("Nothing saved yet. Tap the bookmark on any article and it'll wait for you here.")
                .font(.hearthBodySM)
                .foregroundColor(.inkMuted)
        } else {
            VStack(alignment: .leading, spacing: .hearth400) {
                ForEach(savedArticles) { item in
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

    private func unsave(_ item: SavedItem) {
        savedItems.removeAll { $0.id == item.id }
        contentVM.toggleSaved(itemType: "article", itemRef: item.itemRef, surface: "account_sheet") { message in
            interestError = message
        }
    }

    // MARK: `account 03` — History

    @ViewBuilder
    private var historyList: some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            if conversations.isEmpty && coachThreads.isEmpty {
                Text("Nothing here yet. Your Circle conversations and coach chats show up as you go.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
            }
            if !conversations.isEmpty { circleSection }
            if !coachThreads.isEmpty { coachSection }
        }
    }

    private var circleSection: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            historyHeader("In your Circle", link: "Go to Circle", action: goToCircle)
            ForEach(conversations) { conversation in
                circleRow(conversation)
            }
        }
    }

    private func circleRow(_ conversation: CircleConversation) -> some View {
        Button { route = .circleThread(conversation.id) } label: {
            historyCard {
                VStack(alignment: .leading, spacing: 9) {
                    Text(conversation.title)
                        .font(.hearthChipLabel)
                        .tracking(-0.14)
                        .foregroundColor(.inkHeader)
                        .multilineTextAlignment(.leading)
                    Text(conversationSubtitle(conversation))
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkSecondary)
                        .multilineTextAlignment(.leading)
                    AvatarStack(initials: conversation.participants?.map(\.initials) ?? [])
                }
            }
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(conversation.title). \(conversationSubtitle(conversation))")
    }

    /// The design's "M started this — 4 replies", from the server's own
    /// `starter_name` / `reply_count`.
    private func conversationSubtitle(_ conversation: CircleConversation) -> String {
        let starter = (conversation.starterIsMe ?? false)
            ? "You"
            : (conversation.starterName ?? "Someone")
        let replies = conversation.replyCount ?? 0
        let repliesText = replies == 1 ? "1 reply" : "\(replies) replies"
        return "\(starter) started this — \(repliesText)"
    }

    private var coachSection: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            historyHeader("Coach advice", link: "Chat with the coach",
                          action: { Task { await openCoach(thread: nil) } })
            ForEach(coachThreads) { thread in
                coachRow(thread)
            }
        }
    }

    private func coachRow(_ thread: CoachThreadSummary) -> some View {
        Button { Task { await openCoach(thread: thread) } } label: {
            historyCard {
                HStack(alignment: .top, spacing: .hearth400) {
                    VStack(alignment: .leading, spacing: 9) {
                        Text(thread.title)
                            .font(.hearthChipLabel)
                            .tracking(-0.14)
                            .foregroundColor(.inkHeader)
                            .multilineTextAlignment(.leading)
                        if !thread.summary.isEmpty {
                            Text(thread.summary)
                                .font(.hearthBodyMD)
                                .foregroundColor(.inkSecondary)
                                .multilineTextAlignment(.leading)
                        }
                    }
                    Spacer(minLength: .hearth400)
                    if openingThreadID == thread.conversationId {
                        ProgressView().scaleEffect(0.7)
                    }
                }
            }
        }
        .buttonStyle(.plain)
        .disabled(openingThreadID != nil)
        .accessibilityLabel("\(thread.title). \(thread.summary)")
    }

    private func historyHeader(_ title: String, link: String,
                               action: @escaping () -> Void) -> some View {
        HStack {
            Text(title)
                .font(.hearthBodySMBold)
                .foregroundColor(.inkHeader)
            Spacer(minLength: .hearth400)
            Button(action: action) {
                Text(link)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkHeader)
            }
            .buttonStyle(.plain)
        }
    }

    /// The measured history card: white, r12, 9pt padding, 1px `#A4A4A4`
    /// stroke. `borderStrong` (#8A8275) is the nearest token — a touch warmer
    /// and slightly darker, which reads correctly on this cream.
    private func historyCard<Content: View>(@ViewBuilder content: () -> Content) -> some View {
        content()
            .padding(9)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                    .fill(Color.bgElevated)
                    .overlay(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .stroke(Color.borderStrong, lineWidth: 1)
                    )
            )
    }

    /// Open the coach. `thread == nil` is the "Chat with the coach" link — the
    /// current conversation, untouched. A thread opens THAT conversation, which
    /// the server also makes active, so the parent's next message continues it.
    private func openCoach(thread: CoachThreadSummary?) async {
        guard let baseURL = configuration.baseURL else { return }
        if coachVM == nil {
            let vm = ChatViewModel(configuration: configuration, mode: .coaching)
            vm.setUserID(userID)
            coachVM = vm
        }
        if let thread {
            openingThreadID = thread.conversationId
            defer { openingThreadID = nil }
            guard let stored = try? await CoachThreadService.open(
                conversationID: thread.conversationId, userID: userID, baseURL: baseURL
            ) else {
                interestError = "Couldn't open that conversation. Try again."
                return
            }
            coachVM?.replaceMessages(stored.map {
                ChatMessage(role: $0.role == "user" ? .user : .assistant, content: $0.content)
            })
        }
        route = .coach
    }

    /// "Go to Circle" — the sheet can't switch tabs itself, so it uses the SAME
    /// deep-link path a tapped Circle push takes: stash the conversation id and
    /// post the notification `MainTabView` already listens for. Closing the
    /// sheet first is what lets the tab change be visible.
    ///
    /// It needs a conversation to route to, which is why the link only renders
    /// when the parent has at least one.
    private func goToCircle() {
        guard let newest = conversations.first else { return }
        UserDefaults.standard.set(newest.id, forKey: AppDelegate.pendingDMDeeplinkKey)
        dismiss()
        NotificationCenter.default.post(name: .dmPushTapped, object: nil)
    }

    // MARK: - Family interests

    private var interestsSection: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            // Inter w700 13, `inkHeader`, mixed case, NO icon — the sheet's own
            // header style, which differs from the dashboard masthead
            // (`hearthSectionHeader`). Verified separately against `account 02`.
            //
            // The design's "See all" is deliberately NOT drawn: every known
            // option already fits the grid below, so the link would have nothing
            // to open. A dead "See all" is the exact class of control this pass
            // is removing.
            Text("Family interests")
                .font(.hearthBodySMBold)
                .foregroundColor(.inkHeader)
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

    /// The design's five rows are Username / MVP Email / Password / Plan /
    /// Billing. Real-data-only (Miguel's call, 2026-08-09): MVP has no
    /// account email endpoint and no password concept (Apple/Google sign-in
    /// only), so those two rows are OMITTED rather than shown as "Not set" —
    /// a fabricated-looking blank still implies the field exists. Plan and
    /// Billing show the smoke-and-mirrors plan picked at the onboarding
    /// paywall, IF one was ever persisted (`@AppStorage`, set at Buy-tap);
    /// existing installs that never saw the paywall show neither row.
    private var accountCard: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            accountRow(label: "Username", value: parentDisplayName)
            if !pickedPlanName.isEmpty {
                accountRow(label: "Plan", value: pickedPlanName)
            }
            if !pickedPlanBilling.isEmpty {
                accountRow(label: "Billing", value: pickedPlanBilling)
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
        HStack(alignment: .top, spacing: .hearth700) {
            Text(label)
                .font(.hearthBodyMD)
                .foregroundColor(.inkMuted)
            Spacer(minLength: .hearth400)
            Text(value.isEmpty ? "Not set" : value)
                .font(.hearthBodyMD)
                .foregroundColor(value.isEmpty ? .inkPlaceholder : .inkMuted)
                .multilineTextAlignment(.trailing)
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

// MARK: - Avatar stack (the Circle rows' participants)

/// The measured 28pt teal circles with a white w900 initial. Drawn edge to edge
/// rather than overlapped, per `account 03`.
private struct AvatarStack: View {
    let initials: [String]

    var body: some View {
        HStack(spacing: .hearth300) {
            ForEach(Array(initials.prefix(4).enumerated()), id: \.offset) { _, letter in
                Circle()
                    .fill(Color.accentDefault)
                    .frame(width: 28, height: 28)
                    .overlay(
                        Text(String(letter.prefix(1)).uppercased())
                            .font(.hearthBodySM.weight(.black))
                            .foregroundColor(.inkOnCard)
                    )
            }
        }
        .accessibilityHidden(true)
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
                // Unselected tiles carry a top-trailing "+" badge (measured
                // `account 03` grid, node `I1008:5182;1008:4896`) — the
                // visual cue that tapping ADDS this interest. Selected tiles
                // have no badge, but this row ALWAYS renders (invisible, not
                // removed) — a conditional row made selected/unselected
                // tiles different heights within the same grid row, since
                // `LazyVGrid` does not force its cells to a shared height.
                HStack {
                    Spacer()
                    Image("InterestIcon-plus")
                        .renderingMode(.template)
                        .resizable()
                        .scaledToFit()
                        .frame(width: 20, height: 20)
                        .opacity(selected ? 0 : 1)
                        .accessibilityHidden(true)
                }
                // Same Figma-exported vector set as the onboarding free-time
                // grid (`ProfileOptions.interestIconName`); SF Symbol
                // fallback for any option without a matching icon export.
                // Measured 35x33 (`account 03` grid) — was 20x20.
                if let iconName = ProfileOptions.interestIconName(for: label) {
                    Image(iconName)
                        .renderingMode(.template)
                        .resizable()
                        .scaledToFit()
                        .frame(width: 35, height: 33)
                } else {
                    Image(systemName: symbol)
                        .font(.system(size: 28, weight: .medium))
                        .frame(width: 35, height: 33)
                }
                // Inter 400 ~14/22 in the frame — regular weight, NOT bold.
                // The frame fits every label, including "Arts & crafts", on
                // ONE line — a fixed 2-line reservation (tried earlier this
                // round) made every tile noticeably taller than the frame's
                // near-square 109x120 and stretched the whole grid. Force a
                // single line and let it shrink rather than wrap, so every
                // tile's label consumes the same one-line height regardless
                // of word count.
                Text(label)
                    .font(.hearthBodyMD)
                    .multilineTextAlignment(.center)
                    .lineLimit(1)
                    .minimumScaleFactor(0.7)
            }
            // Selected = teal fill + white icon/label, no stroke, invisible
            // badge. Unselected = white card, teal stroke ~0.9, teal
            // icon/label, visible "+" badge. Same pass ratio as the
            // onboarding free-time grid this reuses (`accentDefault` as ink
            // on `bg/elevated` paper is a declared AA pass there).
            .foregroundColor(selected ? .inkOnCard : .accentDefault)
            // The design's tiles HUG their content (vertical auto-layout, no
            // fixed height) — pinning `minHeight` floated content and left
            // dead space in the ORIGINAL Figma-only measurement, but this
            // grid needs every tile the SAME height regardless of selection
            // state or label line count, so padding is now identical for
            // both states (the badge-row + fixed-height label above absorb
            // what used to be state-dependent padding).
            .frame(maxWidth: .infinity)
            .padding(.top, .hearth300)
            .padding(.bottom, .hearth500)
            .padding(.horizontal, .hearth500)
            .background(selected ? Color.accentDefault : Color.bgElevated)
            .overlay(
                RoundedRectangle(cornerRadius: .hearthRadiusControl, style: .continuous)
                    .strokeBorder(Color.accentDefault, lineWidth: selected ? 0 : 0.9)
            )
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusControl, style: .continuous))
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(selected ? [.isSelected] : [])
    }
}
