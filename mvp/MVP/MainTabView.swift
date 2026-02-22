import SwiftUI

struct MainTabView: View {
    @StateObject private var configuration = ServerConfiguration()
    @StateObject private var viewModel: ChatViewModel
    @State private var selectedTab: Tab = .home
    @State private var isShowingUsernamePrompt: Bool = true
    @State private var username: String = ""

    enum Tab: String {
        case home, library, agent, circle
    }

    init() {
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
        .ignoresSafeArea(.keyboard, edges: .bottom)
        .preferredColorScheme(.light)
        .sheet(isPresented: $isShowingUsernamePrompt) {
            NavigationStack {
                Form {
                    Section(header: Text("Enter your username")) {
                        TextField("Username", text: $username)
                            .textInputAutocapitalization(.none)
                            .autocorrectionDisabled()
                    }
                }
                .navigationTitle("Welcome")
                .toolbar {
                    ToolbarItem(placement: .confirmationAction) {
                        Button("Continue") {
                            let trimmed = username.trimmingCharacters(in: .whitespacesAndNewlines)
                            viewModel.setUserID(trimmed)
                            username = trimmed
                            isShowingUsernamePrompt = false
                        }
                        .disabled(username.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    }
                }
            }
        }
        .onAppear {
            if viewModel.isUserIDMissing {
                isShowingUsernamePrompt = true
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
                    .fill(Color.brandNavy.opacity(0.08))
                    .frame(height: 0.5)
                Color.white
            }
            .shadow(color: Color.black.opacity(0.04), radius: 8, y: -2)
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
            .foregroundColor(selectedTab == tab ? .brandNavy : .brandGray)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 4)
        }
        .accessibilityLabel(label)
    }
}
