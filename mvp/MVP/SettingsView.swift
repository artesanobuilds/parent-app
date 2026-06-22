import SwiftUI

/// Tabbed settings sheet: Profile (edit parent info incl. ZIP) + Server. Opened
/// from the name-initial avatar on the Home screen. Wraps the existing
/// ServerSettingsView and the new ProfileSettingsView behind a segmented control.
struct SettingsView: View {
    @ObservedObject var configuration: ServerConfiguration
    let userID: String

    @State private var tab: Tab = .profile

    enum Tab: String, CaseIterable, Identifiable {
        case profile, integrations, server
        var id: String { rawValue }
        var label: String {
            switch self {
            case .profile: return "Profile"
            case .integrations: return "Integrations"
            case .server: return "Server"
            }
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            Picker("Settings section", selection: $tab) {
                ForEach(Tab.allCases) { Text($0.label).tag($0) }
            }
            .pickerStyle(.segmented)
            .padding(.horizontal, .hearth700)
            .padding(.top, .hearth400)
            .padding(.bottom, .hearth300)
            .background(Color.bgCanvas)

            switch tab {
            case .profile:
                ProfileSettingsView(configuration: configuration, userID: userID)
            case .integrations:
                IntegrationsSettingsView(configuration: configuration, userID: userID)
            case .server:
                ServerSettingsView(configuration: configuration)
            }
        }
        .background(Color.bgCanvas.ignoresSafeArea())
    }
}
