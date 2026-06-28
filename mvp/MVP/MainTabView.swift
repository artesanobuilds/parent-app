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

    enum Tab: String {
        case home, library, agent, circle, planning
    }

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
        }
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
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            // Add bottom padding so content doesn't hide behind the tab bar
            .padding(.bottom, .hearth1000)

            // Custom bottom tab bar
            customTabBar
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
            tabBarItem(tab: .circle, icon: "person.2", activeIcon: "person.2.fill", label: "Circle")
            tabBarItem(tab: .planning, icon: "calendar", activeIcon: "calendar", label: "Plan")
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

    private func tabBarItem(tab: Tab, icon: String, activeIcon: String, label: String) -> some View {
        Button {
            withAnimation(.hearthFast) {
                selectedTab = tab
            }
        } label: {
            VStack(spacing: 3) {
                Image(systemName: selectedTab == tab ? activeIcon : icon)
                    .font(.system(size: 22, weight: .medium))
                    .frame(height: 26)

                Text(label)
                    .font(.hearthLabel)
                    .tracking(0.66)
                    .textCase(.uppercase)
            }
            .foregroundColor(selectedTab == tab ? .accentDefault : .inkMuted)
            .frame(maxWidth: .infinity, minHeight: 56)
            .padding(.vertical, .hearth300)
            .contentShape(Rectangle())
        }
        .accessibilityLabel(label)
    }
}
