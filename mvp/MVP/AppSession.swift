import Foundation
import SwiftUI

/// The seam between a deeply-nested Settings screen and the app-launch gate.
///
/// The gate keys (`onboarding_completed`, `user_name`, `parent_display_name`)
/// are `@AppStorage` on `MVPApp` — a Settings sheet three levels down can't
/// reach those bindings directly. `AppSession` writes the same `UserDefaults`
/// keys, which `@AppStorage` observes, so flipping them here re-routes the app
/// back to `SignInView` on the next render. Injected via `.environmentObject`.
@MainActor
final class AppSession: ObservableObject {

    /// UserDefaults keys that gate the launch flow + the durable onboarding seed.
    /// Kept in sync with the `@AppStorage` keys in `MVPApp` and the pending-seed
    /// keys in the same file. `chat.base_url` is deliberately NOT cleared — a
    /// developer's server override should survive sign-out.
    private enum Key {
        static let onboardingCompleted = "onboarding_completed"
        static let userName = "user_name"
        static let parentDisplayName = "parent_display_name"
        static let pendingSeedBody = "pending_seed_body"
        static let pendingSeedUser = "pending_seed_user"
    }

    /// Set while a sign-out or delete is in flight so the UI can disable buttons.
    @Published var isWorking = false

    /// Latest /legal/status. Nil until fetched. Drives the Home re-accept
    /// banner when a CMS publish flagged "requires re-acceptance".
    @Published var legalStatus: LegalStatus?

    var needsLegalAcceptance: Bool {
        guard let status = legalStatus else { return false }
        return !status.acceptedAll
    }

    /// Launch-time legal bookkeeping, called from the MainTabView task:
    /// 1) flush a pending onboarding agreement (durable retry — an offline
    ///    accept self-heals here instead of stranding the user on the banner),
    /// 2) refresh the status that drives the banner.
    func refreshLegal(userID: String, baseURL: URL?) async {
        guard let baseURL else { return }
        let defaults = UserDefaults.standard
        if defaults.bool(forKey: LegalService.acceptPendingKey) {
            if await LegalService.acceptCurrent(userID: userID, baseURL: baseURL,
                                               surface: "onboarding") != nil {
                defaults.removeObject(forKey: LegalService.acceptPendingKey)
            }
        }
        legalStatus = try? await LegalService.fetchStatus(userID: userID, baseURL: baseURL)
    }

    /// One-tap Agree from the Home banner.
    func acceptLegal(userID: String, baseURL: URL?) async {
        guard let baseURL else { return }
        if let refreshed = await LegalService.acceptCurrent(userID: userID, baseURL: baseURL,
                                                           surface: "banner") {
            legalStatus = refreshed
        }
    }

    /// Log out: revoke the session server-side (best-effort), drop analytics
    /// identity, clear any un-flushed onboarding seed, then flip the gate keys.
    ///
    /// Order matters. The pending-seed clear is load-bearing: `flushPendingSeed`
    /// re-POSTs a stashed payload under the LEGACY token path, which mints a
    /// token for any claimed `user_id`. If the next person signs in on this
    /// device with the previous parent's seed still stashed, their profile would
    /// be re-seeded onto the wrong account. Clearing it here closes that hole.
    func signOut(userID: String, baseURL: URL?) async {
        isWorking = true
        defer { isWorking = false }

        await AuthService.shared.logout(for: userID, baseURL: baseURL)
        Analytics.reset()

        let defaults = UserDefaults.standard
        defaults.removeObject(forKey: Key.pendingSeedBody)
        defaults.removeObject(forKey: Key.pendingSeedUser)
        // A pending legal agreement is THIS user's — the next account on this
        // device must never inherit it (it would silently auto-accept for them).
        defaults.removeObject(forKey: LegalService.acceptPendingKey)
        legalStatus = nil

        // Flip the gate LAST — this is what re-renders the app to SignInView.
        defaults.set(false, forKey: Key.onboardingCompleted)
        defaults.set("", forKey: Key.userName)
        defaults.set("", forKey: Key.parentDisplayName)
    }

    /// Permanently delete the family's account + data, then sign out locally.
    ///
    /// Hits `DELETE /family/{user_id}` (cascades every kid-data table, purges the
    /// analytics person, re-exports the parquet snapshots so backups forget too,
    /// and writes one audit row that survives). Refreshes the token first so an
    /// expired access token doesn't fail the delete. Throws on a non-2xx so the
    /// UI can surface it — deletion must NOT navigate away assuming success.
    func deleteAccount(userID: String, baseURL: URL) async throws {
        isWorking = true
        defer { isWorking = false }

        // Ensure a live token: an expired access token would 401 the delete.
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)

        var request = URLRequest(url: baseURL.appendingPathComponent("family/\(userID)"))
        request.httpMethod = "DELETE"
        request.timeoutInterval = 30
        for (k, v) in AuthService.shared.header(for: userID) {
            request.setValue(v, forHTTPHeaderField: k)
        }

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }
        guard (200..<300).contains(http.statusCode) else {
            let detail = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["detail"] as? String
                ?? "Delete failed (\(http.statusCode))."
            throw AuthService.AuthError(status: http.statusCode, detail: detail)
        }

        // Server data is gone — now clear this device.
        await signOut(userID: userID, baseURL: baseURL)
    }
}
