import SwiftUI

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
    // Drives the Circle tab's unread-DM badge + the push deep link.
    @EnvironmentObject private var session: AppSession
    @Environment(\.scenePhase) private var scenePhase

    enum Tab: String {
        case home, library, agent, circle, planning, saved
    }

    // Bumped every time the Saved tab is selected, so SavedView re-fetches —
    // a save made in Library/Coach/Circle must show without a relaunch.
    @State private var savedRefreshToken = 0

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
            // A DM push tapped before this tree existed (cold launch) is
            // waiting in UserDefaults — route it now.
            consumePendingDMDeeplink()
            await session.refreshDMUnread(userID: username, baseURL: configuration.baseURL)
        }
        .onReceive(NotificationCenter.default.publisher(for: .dmPushTapped)) { _ in
            consumePendingDMDeeplink()
        }
        .onReceive(NotificationCenter.default.publisher(for: .dmPushReceived)) { _ in
            Task { await session.refreshDMUnread(userID: username, baseURL: configuration.baseURL) }
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active {
                consumePendingDMDeeplink()
                Task { await session.refreshDMUnread(userID: username, baseURL: configuration.baseURL) }
            }
        }
    }

    /// Route a tapped DM push into its thread: Circle tab → (CircleView opens
    /// the Messages sheet) → (the inbox pushes the conversation). The stash
    /// survives the cold-launch race where the tap precedes the view tree.
    private func consumePendingDMDeeplink() {
        guard let conversationId = UserDefaults.standard.string(forKey: AppDelegate.pendingDMDeeplinkKey)
        else { return }
        UserDefaults.standard.removeObject(forKey: AppDelegate.pendingDMDeeplinkKey)
        session.pendingDMConversationId = conversationId
        withAnimation(.hearthFast) { selectedTab = .circle }
    }

    private var tabContent: some View {
        ZStack(alignment: .bottom) {
            // Full-bleed cream base so the bottom safe area (home-indicator strip)
            // behind the tab bar is canvas-colored, not the default white.
            Color.bgCanvas.ignoresSafeArea()

            // Tab content
            Group {
                switch selectedTab {
                case .home:
                    HomeView(username: username)
                case .library:
                    LibraryView()
                case .agent:
                    AgentView(viewModel: viewModel, configuration: configuration)
                case .circle:
                    CircleView()
                case .planning:
                    PlanView(viewModel: planVM, cosVM: cosVM, configuration: configuration, userID: username)
                case .saved:
                    SavedView(username: username, refreshToken: savedRefreshToken) {
                        withAnimation(.hearthFast) { selectedTab = .planning }
                    }
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            // Add bottom padding so content doesn't hide behind the tab bar
            .padding(.bottom, .hearth1000)

            // Custom bottom tab bar
            customTabBar
        }
        // Engagement: which tabs parents use. Tab name only, no content. Deeper
        // (pushed/presented) screens self-report via `.trackScreen(...)`.
        .onAppear { Analytics.capture("screen_viewed", ["screen": selectedTab.rawValue]) }
        .onChange(of: selectedTab) { _, tab in
            Analytics.capture("screen_viewed", ["screen": tab.rawValue])
            if tab == .saved { savedRefreshToken += 1 }
        }
    }

    // MARK: - Custom Tab Bar
    //
    // Hearth iOS surface spec: tab bar items 56pt, selected tint = accent,
    // unselected = ink/muted, top-edge hairline divider, never translucent
    // material over photography.

    private var customTabBar: some View {
        HStack(spacing: 0) {
            tabBarItem(tab: .home, icon: "house", activeIcon: "house.fill", label: "Home")
            tabBarItem(tab: .library, icon: "book", activeIcon: "book.fill", label: "Library")
            tabBarItem(tab: .agent, icon: "message", activeIcon: "message.fill", label: "Coach")
            tabBarItem(tab: .circle, icon: "person.2", activeIcon: "person.2.fill", label: "Circle",
                       badge: session.dmUnread)
            tabBarItem(tab: .planning, icon: "calendar", activeIcon: "calendar", label: "Plan")
            tabBarItem(tab: .saved, icon: "bookmark", activeIcon: "bookmark.fill", label: "Saved")
        }
        .padding(.top, .hearth300)
        .padding(.bottom, 2)
        .background(
            VStack(spacing: 0) {
                Rectangle()
                    .fill(Color.borderHairline)
                    .frame(height: 0.5)
                Color.bgCanvas
            }
        )
    }

    private func tabBarItem(tab: Tab, icon: String, activeIcon: String, label: String,
                            badge: Int = 0) -> some View {
        Button {
            withAnimation(.hearthFast) {
                selectedTab = tab
            }
        } label: {
            VStack(spacing: 3) {
                Image(systemName: selectedTab == tab ? activeIcon : icon)
                    .font(.system(size: 20, weight: .medium))
                    .frame(height: 26)
                    // Level-1 unread signal: visible from ANY tab. The louder
                    // level-2 signal is the envelope inside Circle itself.
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

                // Six tabs on a 375pt phone: the LABEL's Dynamic Type is capped
                // (icons still scale, every item keeps its accessibilityLabel)
                // and it may shrink slightly before it would ever wrap.
                Text(label)
                    .font(.hearthLabel)
                    .tracking(0.4)
                    .textCase(.uppercase)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
                    .dynamicTypeSize(...DynamicTypeSize.xLarge)
            }
            .foregroundColor(selectedTab == tab ? .accentDefault : .inkMuted)
            .frame(maxWidth: .infinity, minHeight: 56)
            .padding(.vertical, .hearth300)
            .contentShape(Rectangle())
        }
        .accessibilityLabel(badge > 0 ? "\(label), \(badge) unread messages" : label)
    }
}
