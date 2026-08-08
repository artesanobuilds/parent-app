import SwiftUI

/// Settings, presented from the Home greeting-header avatar (inside Home's
/// NavigationStack, so rows push). Rebuilt for beta: a plain grouped List whose
/// account/support/legal rows sit alongside the two session controls the app
/// was missing — **Log out** and **Delete account**. The developer console
/// (server URL, environment switch, thread IDs) is no longer a peer tab a beta
/// parent sees; it's tucked behind a 7-tap reveal on the version row (and always
/// visible in DEBUG) so the founders keep it on TestFlight builds.
struct SettingsView: View {
    @ObservedObject var configuration: ServerConfiguration
    let userID: String
    /// Switches the app to the Plan tab. SavedView's "In Plan" rows hand off to
    /// it. Defaults to a no-op so callers that don't own the tab selection
    /// (e.g. a sheet presentation) keep compiling unchanged.
    var onOpenPlan: () -> Void = {}

    @EnvironmentObject private var session: AppSession
    @AppStorage("parent_display_name") private var parentDisplayName = ""
    // Release-only developer reveal. In DEBUG the tools are always visible.
    @AppStorage("developer_mode") private var developerMode = false

    @State private var showingReport = false
    @State private var showingLogoutConfirm = false
    @State private var showingDelete = false
    @State private var deleteConfirmText = ""
    @State private var errorMessage: String?
    @State private var versionTapCount = 0

    private var showDeveloper: Bool {
        #if DEBUG
        return true
        #else
        return developerMode
        #endif
    }

    private var appVersion: String {
        let short = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "?"
        let build = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "?"
        return "Version \(short) (\(build))"
    }

    // Public docs served outside the auth guard at /dashboard/docs (Phase 3
    // adds the actual pages). Resolved ONLY through ServerConfiguration.baseURL,
    // never a hardcoded host.
    private var privacyURL: URL? { configuration.baseURL?.appendingPathComponent("dashboard/docs/privacy-policy") }
    private var termsURL: URL? { configuration.baseURL?.appendingPathComponent("dashboard/docs/terms") }

    var body: some View {
        List {
            Section("Account") {
                NavigationLink {
                    ProfileSettingsView(configuration: configuration, userID: userID)
                } label: {
                    Label(parentDisplayName.isEmpty ? "Profile" : parentDisplayName,
                          systemImage: "person.crop.circle")
                }
                NavigationLink {
                    IntegrationsSettingsView(configuration: configuration, userID: userID)
                } label: {
                    Label("Connections", systemImage: "link")
                }
            }

            // beta-v1: Library left the tab bar (6 tabs → 5) and lives here. Pushed
            // UNCHANGED — it owns its own NavigationStack, so this row's own
            // nav bar stays title-less to keep the chrome to a single back
            // chevron. Saved moved to the Home-header avatar sheet
            // (`AccountSheetView`, Sprint-1 gap) and no longer lives here.
            Section("Reading") {
                NavigationLink {
                    LibraryView()
                        .navigationBarTitleDisplayMode(.inline)
                } label: {
                    Label("Library", systemImage: "books.vertical")
                }
            }

            Section("Support") {
                Button { showingReport = true } label: {
                    Label("Report a problem", systemImage: "exclamationmark.bubble")
                }
            }

            Section("Legal") {
                if let privacyURL {
                    Link(destination: privacyURL) { Label("Privacy Policy", systemImage: "hand.raised") }
                }
                if let termsURL {
                    Link(destination: termsURL) { Label("Terms of Service", systemImage: "doc.text") }
                }
            }

            if showDeveloper {
                Section("Developer") {
                    NavigationLink {
                        ServerSettingsView(configuration: configuration)
                    } label: {
                        Label("Server & diagnostics", systemImage: "wrench.and.screwdriver")
                    }
                }
            }

            Section {
                HStack {
                    Text(appVersion)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkMuted)
                    Spacer()
                }
                .contentShape(Rectangle())
                .onTapGesture { revealDeveloperOnTaps() }
            }

            Section {
                Button(role: .destructive) {
                    showingLogoutConfirm = true
                } label: {
                    Text("Log out").frame(maxWidth: .infinity)
                }
                Button(role: .destructive) {
                    deleteConfirmText = ""
                    showingDelete = true
                } label: {
                    Text("Delete account").frame(maxWidth: .infinity)
                }
            }
            .disabled(session.isWorking)
        }
        .scrollContentBackground(.hidden)
        .background(Color.bgCanvas.ignoresSafeArea())
        // No `.trackScreen("settings")` here: Settings is a TAB now, and
        // MainTabView already emits `screen_viewed{screen:settings}` on tab
        // change like it does for every other tab. Keeping both double-counted
        // every Settings open.
        .sheet(isPresented: $showingReport) {
            if let url = configuration.baseURL { ReportProblemView(baseURL: url) }
        }
        .sheet(isPresented: $showingDelete) { deleteSheet }
        .confirmationDialog("Log out of MVP?",
                            isPresented: $showingLogoutConfirm,
                            titleVisibility: .visible) {
            Button("Log out", role: .destructive) {
                Task { await session.signOut(userID: userID, baseURL: configuration.baseURL) }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("You'll need to sign in again to get back to your family's plan.")
        }
        .alert("Something went wrong",
               isPresented: Binding(get: { errorMessage != nil },
                                    set: { if !$0 { errorMessage = nil } })) {
            Button("OK") { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
    }

    // MARK: - Delete confirmation

    private var deleteSheet: some View {
        NavigationStack {
            Form {
                Section {
                    Text("This permanently deletes your account and your family's data — your plan, chat history, kid companions, and profile. It can't be undone.")
                    Text("One anonymous entry (that a deletion happened, and when) is kept for our records. It contains none of your family's content.")
                        .font(.hearthBodySM)
                        .foregroundColor(.inkMuted)
                }
                Section("Type DELETE to confirm") {
                    TextField("DELETE", text: $deleteConfirmText)
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.characters)
                }
                Section {
                    Button(role: .destructive) {
                        Task { await performDelete() }
                    } label: {
                        if session.isWorking {
                            ProgressView().frame(maxWidth: .infinity)
                        } else {
                            Text("Delete my account").frame(maxWidth: .infinity)
                        }
                    }
                    .disabled(!isDeleteConfirmed || session.isWorking)
                }
            }
            .scrollContentBackground(.hidden)
            .background(Color.bgCanvas.ignoresSafeArea())
            .navigationTitle("Delete account")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { showingDelete = false }.disabled(session.isWorking)
                }
            }
        }
    }

    private var isDeleteConfirmed: Bool {
        deleteConfirmText.trimmingCharacters(in: .whitespaces).uppercased() == "DELETE"
    }

    private func performDelete() async {
        guard let baseURL = configuration.baseURL else {
            errorMessage = "No server is configured, so we can't reach your account to delete it."
            return
        }
        do {
            try await session.deleteAccount(userID: userID, baseURL: baseURL)
            // On success the launch gate flips and this whole tree is torn down;
            // nothing else to do here.
        } catch {
            showingDelete = false
            errorMessage = (error as? LocalizedError)?.errorDescription
                ?? "We couldn't delete your account. Please check your connection and try again."
        }
    }

    private func revealDeveloperOnTaps() {
        guard !showDeveloper else { return }
        versionTapCount += 1
        if versionTapCount >= 7 { developerMode = true }
    }
}
