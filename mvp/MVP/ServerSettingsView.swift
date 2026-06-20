import SwiftUI

struct ServerSettingsView: View {
    @ObservedObject var configuration: ServerConfiguration
    @State private var draftBaseURL: String = ""
    @State private var draftThreadID: String = ""
    @State private var showingReport = false

    /// Which preset the current draft URL matches. `custom` whenever the URL is
    /// neither the canonical local nor production address — i.e. a hand-typed
    /// override (e.g. a Mac's LAN IP for testing on a physical device).
    private enum Mode: String, CaseIterable, Identifiable {
        case local, production, custom
        var id: String { rawValue }
        var label: String {
            switch self {
            case .local: return "Local"
            case .production: return "Production"
            case .custom: return "Custom"
            }
        }
    }

    private var currentMode: Mode {
        switch draftBaseURL.trimmingCharacters(in: .whitespacesAndNewlines) {
        case ServerConfiguration.localURL: return .local
        case ServerConfiguration.productionURL: return .production
        default: return .custom
        }
    }

    var body: some View {
        Form {
            Section("Environment") {
                // Dropdown: picking Local/Production fills the URL below.
                // Picking Custom leaves whatever you've typed untouched.
                Picker("Server", selection: Binding(
                    get: { currentMode },
                    set: { mode in
                        switch mode {
                        case .local:      draftBaseURL = ServerConfiguration.localURL
                        case .production: draftBaseURL = ServerConfiguration.productionURL
                        case .custom:     break  // keep the typed override
                        }
                    }
                )) {
                    ForEach(Mode.allCases) { mode in
                        Text(mode.label).tag(mode)
                    }
                }
                .pickerStyle(.menu)

                LabeledContent("Local", value: ServerConfiguration.localURL)
                    .font(.hearthCaptionMono)
                    .foregroundColor(.inkMuted)
                LabeledContent("Production", value: ServerConfiguration.productionURL)
                    .font(.hearthCaptionMono)
                    .foregroundColor(.inkMuted)
            }

            Section("Server URL") {
                // Always editable. Type any URL to override the presets — the
                // dropdown above flips to "Custom" automatically.
                TextField(
                    "Server URL",
                    text: $draftBaseURL,
                    prompt: Text("e.g. http://192.168.1.50:8904")
                )
                .keyboardType(.URL)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .textContentType(.URL)

                if !isValidURL(draftBaseURL) {
                    Text("Enter a valid URL including scheme (http/https).")
                        .font(.hearthBodySM)
                        .foregroundColor(.statusError)
                }
                Text("On a physical device, \"Local\" (127.0.0.1) won't reach your Mac — use your Mac's LAN IP, e.g. http://192.168.x.x:8904.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
            }

            Section("Conversation") {
                TextField("Thread ID", text: $draftThreadID)
                Button("Reset Thread ID") {
                    configuration.resetThread()
                    draftThreadID = configuration.threadID
                }
            }

            Section {
                Button("Save Changes") {
                    save()
                }
                .disabled(!isValidURL(draftBaseURL))
            }

            Section {
                Button("Send debug data") { showingReport = true }
            } footer: {
                Text("Sends app/device/server diagnostics and recent logs to help debug an issue.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
            }
        }
        .scrollContentBackground(.hidden)
        .background(Color.bgCanvas.ignoresSafeArea())
        .onAppear {
            draftBaseURL = configuration.baseURLString
            draftThreadID = configuration.threadID
        }
        .sheet(isPresented: $showingReport) {
            if let url = configuration.baseURL {
                ReportProblemView(baseURL: url)
            }
        }
    }

    private func save() {
        configuration.baseURLString = draftBaseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        configuration.threadID = draftThreadID.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func isValidURL(_ value: String) -> Bool {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URL(string: trimmed) else { return false }
        return ["http", "https"].contains(url.scheme?.lowercased() ?? "")
    }
}
