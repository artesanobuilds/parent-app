import SwiftUI

struct MainTabView: View {
    let username: String

    @StateObject private var configuration = ServerConfiguration()
    @StateObject private var viewModel: ChatViewModel
    @StateObject private var contentVM = ContentViewModel()
    @State private var selectedTab: Tab = .home

    enum Tab: String {
        case home, library, agent, circle
    }

    init(username: String = "") {
        self.username = username
        let config = ServerConfiguration()
        _configuration = StateObject(wrappedValue: config)
        _viewModel = StateObject(wrappedValue: ChatViewModel(configuration: config, mode: .coaching))
    }

    var body: some View {
        ZStack(alignment: .bottom) {
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
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            // Add bottom padding so content doesn't hide behind the tab bar
            .padding(.bottom, 56)

            // Custom bottom tab bar
            customTabBar
        }
        .environmentObject(contentVM)
        .environmentObject(configuration)
        .ignoresSafeArea(.keyboard, edges: .bottom)
        .preferredColorScheme(.dark)
        .onAppear {
            viewModel.setUserID(username)
            contentVM.userId = username
        }
        .task {
            if let url = configuration.baseURL {
                contentVM.baseURL = url
                await contentVM.loadAllContent(baseURL: url)
            }
        }
    }

    // MARK: - Custom Tab Bar

    private var customTabBar: some View {
        HStack(spacing: 0) {
            tabBarItem(tab: .home, icon: "house", activeIcon: "house.fill", label: "Home")
            tabBarItem(tab: .library, icon: "book", activeIcon: "book.fill", label: "Library")
            tabBarItem(tab: .agent, icon: "message", activeIcon: "message.fill", label: "MVP")
            tabBarItem(tab: .circle, icon: "person.2", activeIcon: "person.2.fill", label: "Circle")
        }
        .padding(.top, 8)
        .padding(.bottom, 2)
        .background(
            VStack(spacing: 0) {
                Rectangle()
                    .fill(Color.white.opacity(0.08))
                    .frame(height: 0.5)
                Color.brandBlack
            }
            .shadow(color: Color.black.opacity(0.20), radius: 8, y: -2)
        )
    }

    private func tabBarItem(tab: Tab, icon: String, activeIcon: String, label: String) -> some View {
        Button {
            withAnimation(.easeInOut(duration: 0.15)) {
                selectedTab = tab
            }
        } label: {
            VStack(spacing: 3) {
                Image(systemName: selectedTab == tab ? activeIcon : icon)
                    .font(.system(size: 22, weight: .medium))
                    .frame(height: 26)

                Text(label)
                    .font(.system(size: 10, weight: .medium))
            }
            .foregroundColor(selectedTab == tab ? .brandGold : .brandGray)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 4)
        }
        .accessibilityLabel(label)
    }
}
