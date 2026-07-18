import Foundation
import AuthenticationServices

/// Session credential returned by the Phase 2 auth endpoints (/auth/login,
/// /auth/refresh, /auth/exchange-code). Stored in the Keychain as JSON.
struct AuthCredential: Codable {
    var accessToken: String
    var refreshToken: String
    var userId: String
    var analyticsId: String?
    /// Absolute expiry of `accessToken`, computed from the server's expires_in.
    var accessExpiresAt: Date

    var isAccessExpiringSoon: Bool {
        // Refresh a minute early so an in-flight request never rides an
        // about-to-expire token.
        accessExpiresAt.timeIntervalSinceNow < 60
    }
}

/// Manages the parent's session tokens.
///
/// Two eras coexist during the Phase 2 migration:
///  - **v1 (preferred):** a JWT `accessToken` + rotating `refreshToken` from
///    Sign in with Apple / Google, stored as an `AuthCredential`. `header(for:)`
///    returns the access token; `ensureToken` refreshes it when expiring.
///  - **v0 (legacy):** an opaque token from /auth/issue-token. Still honored so
///    existing installs keep working until they sign in. When a v1 credential
///    exists for a user, it wins.
@MainActor
final class AuthService {

    static let shared = AuthService()

    /// In-memory cache of legacy opaque tokens so we don't hit the keychain on
    /// every request.
    private var cache: [String: String] = [:]

    /// In-memory cache of v1 credentials, keyed by userID.
    private var credentials: [String: AuthCredential] = [:]

    /// Tracks an in-flight issuance/refresh per user so concurrent callers
    /// coalesce onto a single network request.
    private var pendingIssuance: [String: Task<String, Error>] = [:]

    private init() {}

    // MARK: - Read

    /// The v1 credential for a user, from memory or keychain.
    func credential(for userID: String) -> AuthCredential? {
        if let cached = credentials[userID] { return cached }
        guard let json = Keychain.get(credentialAccount(userID: userID)),
              let data = json.data(using: .utf8),
              let cred = try? JSONDecoder().decode(AuthCredential.self, from: data) else {
            return nil
        }
        credentials[userID] = cred
        return cred
    }

    func token(for userID: String) -> String? {
        // Prefer a v1 access token when we have one.
        if let cred = credential(for: userID) { return cred.accessToken }
        if let cached = cache[userID] { return cached }
        let value = Keychain.get(keychainAccount(userID: userID))
        cache[userID] = value
        return value
    }

    /// The RAW legacy opaque token from the old /auth/issue-token flow, if any.
    /// This is the ONLY thing valid as legacy claim proof — it must never be a
    /// v1 JWT (the server's `lookup_auth_token` can't validate a JWT, so the
    /// claim would silently fail and the user would get a fresh duplicate
    /// account). So read the legacy Keychain entry directly, bypassing the v1
    /// preference in `token(for:)`.
    func legacyToken(for userID: String) -> String? {
        Keychain.get(keychainAccount(userID: userID))
    }

    func header(for userID: String) -> [String: String] {
        if let token = token(for: userID) {
            return ["Authorization": "Bearer \(token)"]
        }
        return [:]
    }

    var analyticsId: String? {
        credentials.values.first?.analyticsId
    }

    // MARK: - v1 sign-in (Apple / Google)

    /// Outcome of a successful sign-in. `hasProfile` drives routing: a returning
    /// user (has a profile on the server) skips onboarding; a fresh account
    /// goes through it.
    struct SignInOutcome {
        let userId: String
        let hasProfile: Bool
    }

    /// Persist a session returned by /auth/login (or /auth/exchange-code) and
    /// return the outcome, or nil if the response was malformed.
    func completeSignIn(_ session: [String: Any]) -> SignInOutcome? {
        guard let userId = session["user_id"] as? String,
              let access = session["access_token"] as? String,
              let refresh = session["refresh_token"] as? String else {
            return nil
        }
        let expiresIn = (session["expires_in"] as? Double) ?? 1800
        let cred = AuthCredential(
            accessToken: access,
            refreshToken: refresh,
            userId: userId,
            analyticsId: session["analytics_id"] as? String,
            accessExpiresAt: Date().addingTimeInterval(expiresIn)
        )
        store(cred)
        return SignInOutcome(userId: userId, hasProfile: session["has_profile"] as? Bool ?? false)
    }

    /// POST /auth/login with a provider id_token (Apple native, or Google native
    /// if we ever add the SDK). `legacyUserID`/`legacyToken` claim an existing
    /// account so its family data carries over under the same user_id.
    @discardableResult
    func loginWithProvider(
        provider: String,
        idToken: String,
        nonce: String? = nil,
        baseURL: URL,
        legacyUserID: String? = nil,
        legacyToken: String? = nil
    ) async throws -> SignInOutcome {
        var body: [String: Any] = [
            "provider": provider,
            "id_token": idToken,
            "platform": "ios",
        ]
        if let nonce { body["nonce"] = nonce }
        if let legacyUserID { body["legacy_user_id"] = legacyUserID }
        if let legacyToken { body["legacy_token"] = legacyToken }

        let session = try await postJSON(baseURL.appendingPathComponent("auth/login"), body: body)
        guard let outcome = completeSignIn(session) else { throw URLError(.cannotParseResponse) }
        return outcome
    }

    /// Swap a one-time login_code (from the Google web-redirect callback) for a
    /// session. Forwards the legacy proof so a Google login CLAIMS an existing
    /// account (binds the Google identity to it) instead of creating a fresh one.
    @discardableResult
    func exchangeLoginCode(
        _ code: String, baseURL: URL,
        legacyUserID: String? = nil, legacyToken: String? = nil
    ) async throws -> SignInOutcome {
        var body: [String: Any] = ["login_code": code, "platform": "ios"]
        if let legacyUserID { body["legacy_user_id"] = legacyUserID }
        if let legacyToken { body["legacy_token"] = legacyToken }
        let session = try await postJSON(
            baseURL.appendingPathComponent("auth/exchange-code"), body: body
        )
        guard let outcome = completeSignIn(session) else { throw URLError(.cannotParseResponse) }
        return outcome
    }

    /// Refresh the access token using the stored refresh token (rotating).
    /// Returns the fresh access token. Throws on an invalid/reused refresh
    /// token — the caller should route the user back to sign-in.
    @discardableResult
    func refresh(for userID: String, baseURL: URL) async throws -> String {
        guard let cred = credential(for: userID) else { throw URLError(.userAuthenticationRequired) }
        let session = try await postJSON(
            baseURL.appendingPathComponent("auth/refresh"),
            body: ["refresh_token": cred.refreshToken]
        )
        guard let access = session["access_token"] as? String,
              let newRefresh = session["refresh_token"] as? String else {
            throw URLError(.cannotParseResponse)
        }
        let expiresIn = (session["expires_in"] as? Double) ?? 1800
        var updated = cred
        updated.accessToken = access
        updated.refreshToken = newRefresh
        updated.accessExpiresAt = Date().addingTimeInterval(expiresIn)
        store(updated)
        return access
    }

    // MARK: - Legacy v0 (/auth/issue-token)

    /// Calls /auth/issue-token, persists the result, and returns it.
    /// LEGACY — retained so pre-sign-in installs keep working during migration.
    @discardableResult
    func obtainToken(for userID: String, baseURL: URL) async throws -> String {
        var request = URLRequest(url: baseURL.appendingPathComponent("auth/issue-token"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 15
        request.httpBody = try JSONSerialization.data(withJSONObject: ["user_id": userID])

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.userAuthenticationRequired)
        }
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let token = json["token"] as? String else {
            throw URLError(.cannotParseResponse)
        }
        cache[userID] = token
        Keychain.set(token, for: keychainAccount(userID: userID))
        return token
    }

    /// Returns a valid token for userID. Prefers a live v1 access token
    /// (refreshing it when expiring); else the cached legacy token; else issues
    /// a legacy one. Concurrent callers coalesce via `pendingIssuance`.
    @discardableResult
    func ensureToken(for userID: String, baseURL: URL) async throws -> String {
        // v1: refresh a soon-to-expire access token, else return it.
        if let cred = credential(for: userID) {
            if cred.isAccessExpiringSoon {
                if let inflight = pendingIssuance[userID] { return try await inflight.value }
                let task = Task { [weak self] () -> String in
                    defer { Task { @MainActor in self?.pendingIssuance[userID] = nil } }
                    return try await (self?.refresh(for: userID, baseURL: baseURL) ?? "")
                }
                pendingIssuance[userID] = task
                return try await task.value
            }
            return cred.accessToken
        }

        // v0 legacy path.
        if let cached = token(for: userID) { return cached }
        if let inflight = pendingIssuance[userID] { return try await inflight.value }
        let task = Task { [weak self] () -> String in
            defer { Task { @MainActor in self?.pendingIssuance[userID] = nil } }
            return try await (self?.obtainToken(for: userID, baseURL: baseURL) ?? "")
        }
        pendingIssuance[userID] = task
        return try await task.value
    }

    // MARK: - Clear

    func clear(for userID: String) {
        cache.removeValue(forKey: userID)
        credentials.removeValue(forKey: userID)
        Keychain.delete(keychainAccount(userID: userID))
        Keychain.delete(credentialAccount(userID: userID))
    }

    /// Sign out: best-effort server-side revocation, then always clear locally.
    ///
    /// A parent who can't reach the server must STILL be able to log out — the
    /// refresh token expires on its own — so a network/HTTP failure here is
    /// non-fatal and the local `clear(for:)` runs regardless. The refresh token
    /// (when present) is sent so the server can revoke that specific session;
    /// legacy v0 accounts have none and the server revokes nothing, which is fine.
    func logout(for userID: String, baseURL: URL?) async {
        if let baseURL {
            var body: [String: Any] = [:]
            if let refresh = credential(for: userID)?.refreshToken {
                body["refresh_token"] = refresh
            }
            var request = URLRequest(url: baseURL.appendingPathComponent("auth/logout"))
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.timeoutInterval = 10
            for (k, v) in header(for: userID) {
                request.setValue(v, forHTTPHeaderField: k)
            }
            request.httpBody = try? JSONSerialization.data(withJSONObject: body)
            _ = try? await URLSession.shared.data(for: request)
        }
        clear(for: userID)
    }

    // MARK: - Internals

    private func store(_ cred: AuthCredential) {
        credentials[cred.userId] = cred
        if let data = try? JSONEncoder().encode(cred),
           let json = String(data: data, encoding: .utf8) {
            Keychain.set(json, for: credentialAccount(userID: cred.userId))
        }
    }

    /// An auth request failed with a server-provided reason. Surfaced so the
    /// UI can show something more useful than "try again".
    struct AuthError: LocalizedError {
        let status: Int
        let detail: String
        var errorDescription: String? { "auth \(status): \(detail)" }
    }

    private func postJSON(_ url: URL, body: [String: Any]) async throws -> [String: Any] {
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 20
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }
        guard (200..<300).contains(http.statusCode) else {
            let detail = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["detail"] as? String
                ?? String(data: data, encoding: .utf8) ?? "request failed"
            throw AuthError(status: http.statusCode, detail: detail)
        }
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw URLError(.cannotParseResponse)
        }
        return json
    }

    private func keychainAccount(userID: String) -> String { "auth.token.\(userID)" }
    private func credentialAccount(userID: String) -> String { "auth.session.\(userID)" }
}
