import SwiftUI

// MARK: - Home refresh contract (cross-agent)
//
// Settings used to be a SHEET presented by HomeView, and HomeView bumped its
// own `homeRefreshToken` in that sheet's `onDismiss` — which re-ran
// `.task(id: homeRefreshToken)` and re-fetched the profile + kid companions.
// That is what stops a kid deleted/renamed in Settings from lingering on Home
// until relaunch (CLAUDE.md: "after a mutation, the source-of-truth view
// re-fetches").
//
// beta-v1 makes Settings a TAB, which destroys that trigger. This environment
// value replaces it: `MainTabView` bumps it every time `selectedTab` returns to
// `.home`, so any tab round-trip through Settings re-fetches exactly as the
// sheet dismissal used to.
//
// HOW HomeView ADOPTS IT (two lines, no other change):
//
//     @Environment(\.homeRefreshToken) private var homeRefreshToken
//     ...
//     .task(id: homeRefreshToken) { ... }            // already present
//     KidsHomeSection(..., refreshToken: homeRefreshToken)   // already present
//
// i.e. delete the `@State private var homeRefreshToken = 0` line and read the
// environment instead; every existing `.task(id:)` / pass-through stays as-is.
// Until HomeView adopts it the app still builds — the value is simply ignored.
private struct HomeRefreshTokenKey: EnvironmentKey {
    static let defaultValue: Int = 0
}

extension EnvironmentValues {
    /// Bumped by `MainTabView` whenever the Home tab is re-selected. See the
    /// note above — this is the replacement for the removed Settings-sheet
    /// `onDismiss` refresh.
    var homeRefreshToken: Int {
        get { self[HomeRefreshTokenKey.self] }
        set { self[HomeRefreshTokenKey.self] = newValue }
    }
}

struct MainTabView: View {
    let username: String

    @StateObject private var configuration: ServerConfiguration  // set in init (viewModel depends on it)
    @StateObject private var viewModel: ChatViewModel
    @StateObject private var contentVM = ContentViewModel()
    @StateObject private var planVM = PlanViewModel()
    // The Chief-of-Staff chat VM is owned here (not by CosChatView) so the
    // conversation survives switching between the Plan hub's segments.
    @StateObject private var cosVM: CosChatViewModel
    @State private var selectedTab: Tab = .home
    /// Measured height of `customTabBar`, used to reserve exactly that much room
    /// under the tab content. Seeded at the bar's nominal height so the first
    /// frame isn't clipped before `GeometryReader` reports.
    @State private var tabBarHeight: CGFloat = .hearth1000
    // Drives the Circle tab's unread badge + the push deep link.
    @EnvironmentObject private var session: AppSession
    @Environment(\.scenePhase) private var scenePhase

    /// beta-v1: five tabs, in Greg's order — HOME / COACH / PLAN / CIRCLE /
    /// SETTINGS. `library` and `saved` are no longer tabs; they are rows inside
    /// Settings (`SettingsView`), and Settings is no longer a sheet.
    enum Tab: String {
        case home, agent, planning, circle, settings
    }

    // Bumped when the Home tab is re-selected, replacing the Settings-sheet
    // `onDismiss` bump that used to drive HomeView's re-fetch. Published to the
    // tree through `\.homeRefreshToken` (see the contract note at the top).
    @State private var homeRefreshToken = 0
    init(username: String = "") {
        self.username = username
        let config = ServerConfiguration()
        _configuration = StateObject(wrappedValue: config)
        _viewModel = StateObject(wrappedValue: ChatViewModel(configuration: config, mode: .coaching))
        _cosVM = StateObject(wrappedValue: CosChatViewModel(configuration: config))
    }

    var body: some View {
        Group {
            if !username.isEmpty, let baseURL = configuration.baseURL {
                HandoffCurtain(userID: username, baseURL: baseURL) {
                    tabContent
                }
            } else {
                tabContent
            }
        }
        .environmentObject(contentVM)
        .environmentObject(configuration)
        .environment(\.homeRefreshToken, homeRefreshToken)
        .ignoresSafeArea(.keyboard, edges: .bottom)
        // Phase 1: light mode locked until dark-mode tokens land in Phase 2.
        .preferredColorScheme(.light)
        .onAppear {
            viewModel.setUserID(username)
            contentVM.userId = username
            planVM.userId = username
            cosVM.setUserID(username)
        }
        .task {
            if let url = configuration.baseURL {
                contentVM.baseURL = url
                planVM.baseURL = url
                await contentVM.loadAllContent(baseURL: url)
            }
            // A push tapped before this tree existed (cold launch) is
            // waiting in UserDefaults — route it now.
            consumePendingCircleDeeplink()
            await session.refreshCircleUnread(userID: username, baseURL: configuration.baseURL)
        }
        .onReceive(NotificationCenter.default.publisher(for: .dmPushTapped)) { _ in
            consumePendingCircleDeeplink()
        }
        .onReceive(NotificationCenter.default.publisher(for: .dmPushReceived)) { _ in
            Task { await session.refreshCircleUnread(userID: username, baseURL: configuration.baseURL) }
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active {
                consumePendingCircleDeeplink()
                Task { await session.refreshCircleUnread(userID: username, baseURL: configuration.baseURL) }
            }
        }
    }

    /// Route a tapped push into its Circle thread by id. The stash survives
    /// the cold-launch race where the tap precedes the view tree. (The push
    /// payload/notification names still say "DM" — `AppDelegate`/`SwayApp.swift`
    /// predate Circle and are out of this rebuild's scope — but the
    /// conversation id they carry is now interpreted as a Circle conversation.)
    private func consumePendingCircleDeeplink() {
        guard let conversationId = UserDefaults.standard.string(forKey: AppDelegate.pendingDMDeeplinkKey)
        else { return }
        UserDefaults.standard.removeObject(forKey: AppDelegate.pendingDMDeeplinkKey)
        session.pendingCircleConversationId = conversationId
        withAnimation(.hearthFast) { selectedTab = .circle }
    }

    private var tabContent: some View {
        ZStack(alignment: .bottom) {
            // Page ground for every tab. Deliberately `bgCanvas`, NOT the tab
            // bar's lighter `bgCard`: this sits behind the whole screen, so
            // making it bgCard let the lighter tone show through as vertical
            // strips down the left/right edges of any tab whose own
            // background doesn't bleed to the safe-area edges (Circle did).
            // The light band belongs to the BAR, and is painted there.
            Color.bgCanvas.ignoresSafeArea()

            // Tab content
            Group {
                switch selectedTab {
                case .home:
                    // `onOpenPlanner` gives Dashboard 1's COMING UP "Add event"
                    // row a real destination without Home owning a second
                    // plan-mutation path — `planVM` lives here, and the Planner
                    // tab is where the add-to-plan flows already are.
                    HomeView(username: username,
                             onOpenPlanner: { withAnimation(.hearthFast) { selectedTab = .planning } },
                             onOpenSettings: { withAnimation(.hearthFast) { selectedTab = .settings } })
                case .agent:
                    AgentView(viewModel: viewModel, configuration: configuration)
                case .planning:
                    PlanView(viewModel: planVM, cosVM: cosVM, configuration: configuration, userID: username)
                case .circle:
                    CircleView()
                case .settings:
                    settingsTab
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            // Reserve exactly the tab bar's MEASURED height, not a guess. This
            // was a fixed 56pt, which the taller beta-v1 bar overflowed — it
            // sliced the last line off Coach's "not a crisis line" disclaimer.
            // A literal will drift again the next time the bar's metrics change;
            // reading the real height cannot.
            .padding(.bottom, tabBarHeight)

            // Custom bottom tab bar
            customTabBar
                .background(
                    GeometryReader { proxy in
                        Color.clear.onAppear { tabBarHeight = proxy.size.height }
                            .onChange(of: proxy.size.height) { _, h in tabBarHeight = h }
                    }
                )
        }
        // Engagement: which tabs parents use. Tab name only, no content. Deeper
        // (pushed/presented) screens self-report via `.trackScreen(...)`.
        .onAppear { Analytics.capture("screen_viewed", ["screen": selectedTab.rawValue]) }
        .onChange(of: selectedTab) { _, tab in
            Analytics.capture("screen_viewed", ["screen": tab.rawValue])
            // Returning to Home re-fetches its server-backed sections — the
            // replacement for the Settings-sheet `onDismiss` bump.
            if tab == .home { homeRefreshToken += 1 }
        }
    }

    // MARK: - Settings tab
    //
    // Settings is a tab now, not a sheet. It hosts its own NavigationStack so
    // its rows (Profile, Connections, Library, Saved, …) push.

    private var settingsTab: some View {
        NavigationStack {
            FamilySettingsView(configuration: configuration,
                         userID: username,
                         onOpenPlan: { withAnimation(.hearthFast) { selectedTab = .planning } })
                .navigationTitle("Settings")
                .navigationBarTitleDisplayMode(.inline)
                // iOS 26.4 glass chrome: repaint the nav container too — see
                // HearthNavGround.swift. Settings' body ground is bgSober
                // (FamilySettingsView:116), so its chrome matches THAT token —
                // bgCanvas here left a visible darker band across the top.
                .hearthNavGround(.bgSober)
                .toolbarBackground(Color.bgSober, for: .navigationBar)
                .toolbarBackground(.visible, for: .navigationBar)
        }
    }

    // MARK: - Custom Tab Bar
    //
    // Rebuilt 2026-08-08 to match the Figma component (`1014:7078`), then
    // re-verified 2026-08-09 (round 3) against the measured Tab Bar instance
    // `890:2780` (also present, identically, in the Dashboard 1, coach-000,
    // and planner 01/02 frames — this component is shared everywhere):
    //
    //   * container padding top 16 / bottom 25 / horizontal 20, itemSpacing 8,
    //     SPACE_BETWEEN
    //   * the selected tab is a CAPSULE (67×52, r=100) `bgSelected` (#DAE0DF)
    //     fill wrapping the icon AND label together — round 3 built this as a
    //     r=26 rounded rect, which is visibly tighter/squarer than the frame's
    //     fully-stadium pill
    //   * EVERY label and icon is the same teal. The design has no muted
    //     inactive state; selection is carried by the pill only
    //   * bar ground is `bgCard` (#F5F3EF), the same light surface every
    //     measured frame's Tab Bar instance sits on — NOT each screen's own
    //     canvas (round 3 used `bgCanvas`, which read as a mismatched darker
    //     band depending which tab you were on)
    //   * a 1pt top hairline (`borderHairline`) — round 3's "no top hairline"
    //     note was wrong; every measured frame's bar instance carries
    //     `stroke=#F5F3EF w=1.0` at its top edge (round 4, 2026-08-10)
    //   * icons are the Figma-exported `TabIcon-*` vectors (round 3), not SF
    //     Symbols — the shapes (house, coach mark, calendar, family group,
    //     gear) are custom-drawn in the frame and don't match their SF
    //     counterparts closely enough at this size
    //
    // The component ships six tabs with CIRCLE duplicated — a Figma artifact. The
    // render shows five, which is what this builds.
    //
    // Contrast, knowingly: teal on `bgCanvas` is 4.15:1, which fails AA for 11pt
    // labels. Miguel chose exact-Figma fidelity over the AA-safe #186A8B on
    // 2026-08-07; see the note on `HearthPrimitives.teal600` and the waiver in
    // tools/lint-design-tokens.py.

    private var customTabBar: some View {
        HStack(spacing: .hearth300) {
            tabBarItem(tab: .home, icon: "TabIcon-home", label: "HOME", size: CGSize(width: 16, height: 18))
            tabBarItem(tab: .agent, icon: "TabIcon-coach", label: "COACH", size: CGSize(width: 18, height: 18))
            tabBarItem(tab: .planning, icon: "TabIcon-planner", label: "PLANNER", size: CGSize(width: 19, height: 21))
            tabBarItem(tab: .circle, icon: "TabIcon-circle", label: "CIRCLE", size: CGSize(width: 25, height: 21),
                       badge: session.circleUnread)
            tabBarItem(tab: .settings, icon: "TabIcon-settings", label: "SETTINGS", size: CGSize(width: 20, height: 21))
        }
        .padding(.top, .hearth500)
        .padding(.horizontal, .hearth600)
        // Bottom padding is 25 in the design, which INCLUDES the home-indicator
        // area on a notched phone. SwiftUI's safe-area inset already covers that,
        // so a literal 25 here would double it and float the bar.
        .padding(.bottom, .hearth200)
        // The light band is the BAR's, not the page's — bleeding it into the
        // bottom safe area covers the home-indicator strip without tinting
        // the sides of every screen (see the ZStack base's note).
        .background(Color.bgCard.ignoresSafeArea(edges: .bottom))
        .overlay(alignment: .top) {
            Rectangle().fill(Color.borderHairline).frame(height: 1)
        }
    }

    private func tabBarItem(tab: Tab, icon: String, label: String, size: CGSize,
                            badge: Int = 0) -> some View {
        let isActive = selectedTab == tab
        return Button {
            withAnimation(.hearthFast) {
                selectedTab = tab
            }
        } label: {
            VStack(spacing: .hearth200) {
                Image(icon)
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: size.width, height: size.height)
                    // Level-1 unread signal: visible from ANY tab. The louder
                    // level-2 signal is the envelope inside Circle itself. Not in
                    // the design — the component predates the unread feature —
                    // but dropping a shipped signal would be a regression, so it
                    // is restyled onto the new geometry rather than removed.
                    .overlay(alignment: .topTrailing) {
                        if badge > 0 {
                            Text(badge > 9 ? "9+" : "\(badge)")
                                .font(.system(size: 10, weight: .bold))
                                .foregroundColor(.inkOnPhotoLight)
                                .padding(.horizontal, 4)
                                .padding(.vertical, 2)
                                .background(Color.accentDefault)
                                .clipShape(Capsule())
                                .offset(x: 10, y: -4)
                        }
                    }

                // The design's labels are 11pt with +6% tracking. The Dynamic
                // Type cap and `minimumScaleFactor` are NOT in the design (it's a
                // fixed-width mock with no opinion on accessibility sizes) and
                // stay as the guard against "SETTINGS" wrapping at .xxxLarge.
                Text(label)
                    .font(.hearthLabel)
                    .tracking(0.66)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
                    .dynamicTypeSize(...DynamicTypeSize.xxxLarge)
            }
            // One colour for both states — see the note above `customTabBar`.
            .foregroundColor(.accentOnCanvas)
            .frame(maxWidth: .infinity, minHeight: 52)
            // Measured pill pad (8, 8, 9, 8) — hearth300 (8) on every edge is
            // within a point of the frame on all four sides.
            .padding(.vertical, .hearth300)
            .padding(.horizontal, .hearth300)
            // The selected pill wraps icon + label together as a full
            // capsule (67×52, r=100 in the frame) — a stadium shape, not a
            // fixed-radius rounded rect, so it stays fully rounded regardless
            // of label width.
            .background(
                Capsule(style: .continuous)
                    .fill(isActive ? Color.bgSelected : Color.clear)
            )
            .contentShape(Rectangle())
        }
        .accessibilityLabel(badge > 0 ? "\(label), \(badge) unread messages" : label)
        .accessibilityAddTraits(isActive ? [.isSelected] : [])
    }
}
