import SwiftUI

/// Settings → Integrations: connect/disconnect the parent's Google account
/// (Gmail for email ingestion, Google Calendar for sync). Drives the OAuth
/// consent via `GmailService` + `WebAuthRunner`.
@MainActor
final class IntegrationsViewModel: ObservableObject {
    @Published private(set) var accounts: [GoogleAccount] = []
    @Published private(set) var configured = true
    @Published private(set) var isLoading = false
    @Published private(set) var isConnecting = false
    @Published private(set) var isSyncingCalendar = false
    @Published var errorMessage: String?
    @Published var connectedEmail: String?
    @Published var calendarSyncMessage: String?

    private let baseURL: URL?
    private let userID: String
    private let webAuth = WebAuthRunner()

    init(configuration: ServerConfiguration, userID: String) {
        self.baseURL = configuration.baseURL
        self.userID = userID
    }

    var connectedAccounts: [GoogleAccount] { accounts.filter { $0.isConnected } }
    var isGmailConnected: Bool { connectedAccounts.contains { $0.kind == "email" } }
    var isCalendarConnected: Bool { connectedAccounts.contains { $0.kind == "calendar" } }

    func load() async {
        guard let baseURL = baseURL else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            let status = try await GmailService.status(baseURL: baseURL, userID: userID)
            configured = status.configured
            accounts = status.accounts
        } catch GmailServiceError.notConfigured {
            configured = false
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
        }
    }

    func connect() async {
        guard let baseURL = baseURL else { return }
        isConnecting = true
        errorMessage = nil
        defer { isConnecting = false }
        do {
            let authURL = try await GmailService.authorizeURL(baseURL: baseURL, userID: userID)
            let result = try await webAuth.run(authorizationURL: authURL)
            connectedEmail = result.email
            await load()
        } catch GmailServiceError.authCancelled {
            // user backed out — no error banner
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
        }
    }

    func syncCalendarNow() async {
        guard let baseURL = baseURL else { return }
        isSyncingCalendar = true
        calendarSyncMessage = nil
        errorMessage = nil
        defer { isSyncingCalendar = false }
        do {
            try await GmailService.syncCalendar(baseURL: baseURL, userID: userID)
            calendarSyncMessage = "Sync started — your calendar will update shortly."
            // Refresh once so a recently-stamped last-synced time shows; the run
            // itself completes on the backend worker (we don't poll for it).
            await load()
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
        }
    }

    func disconnect(kind: String) async {
        guard let baseURL = baseURL else { return }
        do {
            try await GmailService.disconnect(baseURL: baseURL, userID: userID, kind: kind)
            await load()
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
        }
    }
}

struct IntegrationsSettingsView: View {
    @StateObject private var viewModel: IntegrationsViewModel

    init(configuration: ServerConfiguration, userID: String) {
        _viewModel = StateObject(
            wrappedValue: IntegrationsViewModel(configuration: configuration, userID: userID)
        )
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: .hearth600) {
                intro

                if !viewModel.configured {
                    notAvailableCard
                } else if viewModel.connectedAccounts.isEmpty {
                    connectCard
                } else {
                    connectedCard
                }

                if let error = viewModel.errorMessage {
                    Text(error)
                        .font(.hearthBodySM)
                        .foregroundColor(.statusError)
                }
            }
            .padding(.horizontal, .hearth700)
            .padding(.top, .hearth600)
            .padding(.bottom, .hearth900)
        }
        .background(Color.bgCanvas.ignoresSafeArea())
        .trackScreen("integrations_settings")
        .task { await viewModel.load() }
        .refreshable { await viewModel.load() }
    }

    private var intro: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text("Connect Google")
                .font(.hearthBodyLG.weight(.semibold))
                .foregroundColor(.inkPrimary)
            Text("Let your chief of staff read camp emails and keep your calendar in sync. Read-only — nothing is sent on your behalf, and you can disconnect anytime.")
                .font(.hearthBodyMD)
                .foregroundColor(.inkSecondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var connectCard: some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            Button {
                Task { await viewModel.connect() }
            } label: {
                HStack(spacing: .hearth300) {
                    if viewModel.isConnecting {
                        ProgressView().tint(.inkOnPhotoLight)
                    } else {
                        Image(systemName: "envelope.badge.shield.half.filled")
                    }
                    Text(viewModel.isConnecting ? "Connecting…" : "Connect Gmail & Calendar")
                }
                .font(.hearthBodyMD.weight(.semibold))
                .foregroundColor(.inkOnPhotoLight)
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth400)
                .frame(maxWidth: .infinity)
                .background(viewModel.isConnecting ? Color.inkMuted : Color.accentDefault)
                .clipShape(Capsule())
            }
            .disabled(viewModel.isConnecting)

            Text("You'll sign in with Google and grant read-only access. While in beta, only approved Google accounts can connect.")
                .font(.hearthBodySM)
                .foregroundColor(.inkMuted)
        }
        .padding(.hearth600)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    private var connectedCard: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            ForEach(viewModel.connectedAccounts) { account in
                HStack(spacing: .hearth400) {
                    Image(systemName: account.kind == "email" ? "envelope.fill" : "calendar")
                        .font(.system(size: 16))
                        .foregroundColor(.accentDefault)
                        .frame(width: 28)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(account.kind == "email" ? "Gmail" : "Google Calendar")
                            .font(.hearthBodyMD.weight(.semibold))
                            .foregroundColor(.inkPrimary)
                        if let email = account.accountEmail {
                            Text(email)
                                .font(.hearthBodySM)
                                .foregroundColor(.inkSecondary)
                        }
                        if account.kind == "calendar" {
                            calendarSyncRow(account)
                        }
                    }
                    Spacer()
                    Button("Disconnect") {
                        Task { await viewModel.disconnect(kind: account.kind) }
                    }
                    .font(.hearthBodySM.weight(.semibold))
                    .foregroundColor(.statusError)
                }
                .padding(.vertical, .hearth300)
                if account.id != viewModel.connectedAccounts.last?.id {
                    Divider().background(Color.borderHairline)
                }
            }

            if let msg = viewModel.calendarSyncMessage {
                Text(msg)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
                    .padding(.top, .hearth300)
            }

            if !viewModel.isGmailConnected {
                Button {
                    Task { await viewModel.connect() }
                } label: {
                    Label("Connect Gmail too", systemImage: "plus")
                        .font(.hearthBodySM.weight(.semibold))
                        .foregroundColor(.accentDefault)
                }
                .padding(.top, .hearth300)
            }
        }
        .padding(.hearth600)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    private var notAvailableCard: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Label("Not available yet", systemImage: "clock.badge.questionmark")
                .font(.hearthBodyMD.weight(.semibold))
                .foregroundColor(.inkPrimary)
            Text("Google connection is being set up. Check back soon — your camp emails can still be added by pasting them or snapping a photo on the Plan tab.")
                .font(.hearthBodySM)
                .foregroundColor(.inkSecondary)
        }
        .padding(.hearth600)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    @ViewBuilder
    private func calendarSyncRow(_ account: GoogleAccount) -> some View {
        HStack(spacing: .hearth300) {
            Text(lastSyncedLabel(account.lastSyncAt))
                .font(.hearthBodySM)
                .foregroundColor(.inkMuted)
            Button {
                Task { await viewModel.syncCalendarNow() }
            } label: {
                if viewModel.isSyncingCalendar {
                    ProgressView().controlSize(.small)
                } else {
                    Label("Sync now", systemImage: "arrow.triangle.2.circlepath")
                        .font(.hearthBodySM.weight(.semibold))
                        .foregroundColor(.accentDefault)
                }
            }
            .disabled(viewModel.isSyncingCalendar)
        }
        .padding(.top, .hearth300)
    }

    private func lastSyncedLabel(_ iso: String?) -> String {
        guard let iso = iso, let date = Self.parseISO(iso) else {
            return "Not synced yet"
        }
        return "Last synced \(Self.relativeFormatter.localizedString(for: date, relativeTo: Date()))"
    }

    /// DuckDB's `.isoformat()` may or may not include fractional seconds, so try
    /// both ISO8601 variants.
    private static func parseISO(_ iso: String) -> Date? {
        let withFrac = ISO8601DateFormatter()
        withFrac.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let d = withFrac.date(from: iso) { return d }
        let plain = ISO8601DateFormatter()
        plain.formatOptions = [.withInternetDateTime]
        return plain.date(from: iso)
    }

    private static let relativeFormatter: RelativeDateTimeFormatter = {
        let f = RelativeDateTimeFormatter()
        f.unitsStyle = .full
        return f
    }()

    private var cardBackground: some View {
        RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
            .fill(Color.bgElevated)
            .overlay(
                RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                    .stroke(Color.borderHairline, lineWidth: 1)
            )
    }
}
