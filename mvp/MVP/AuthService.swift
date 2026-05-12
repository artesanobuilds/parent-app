import Foundation

/// Manages opaque session tokens for the parent's account.
///
/// Flow:
///  1. After onboarding completes, `obtainToken(for:baseURL:)` calls
///     POST /auth/issue-token and stores the result in Keychain.
///  2. `header(for:)` returns the Authorization dict for outbound requests.
///  3. Force-fetch (e.g., 401 retry) by calling `obtainToken(...)` again.
@MainActor
final class AuthService: ObservableObject {

    static let shared = AuthService()

    /// In-memory cache so we don't hit the keychain on every request.
    private var cache: [String: String] = [:]

    /// Tracks an in-flight issuance per user so concurrent callers awaiting a
    /// token coalesce onto a single network request instead of stampeding
    /// /auth/issue-token (which is also rate-limited at 5/hour/IP).
    private var pendingIssuance: [String: Task<String, Error>] = [:]

    private init() {}

    func token(for userID: String) -> String? {
        if let cached = cache[userID] { return cached }
        let value = Keychain.get(keychainAccount(userID: userID))
        cache[userID] = value
        return value
    }

    func header(for userID: String) -> [String: String] {
        if let token = token(for: userID) {
            return ["Authorization": "Bearer \(token)"]
        }
        return [:]
    }

    /// Calls /auth/issue-token, persists the result, and returns it.
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

    /// Returns a valid token for userID. Uses the cached one when present;
    /// otherwise issues a new one. Concurrent callers coalesce onto a single
    /// in-flight issuance via `pendingIssuance`.
    ///
    /// Use this from anything that needs to be authed BEFORE its first request
    /// (e.g., KidsHomeSection.refresh()), to avoid the bootstrap race where a
    /// view's .task fires before SwayApp.ensureAuthToken finishes.
    func ensureToken(for userID: String, baseURL: URL) async throws -> String {
        if let cached = token(for: userID) { return cached }
        if let inflight = pendingIssuance[userID] {
            return try await inflight.value
        }
        let task = Task { [weak self] () -> String in
            defer { Task { @MainActor in self?.pendingIssuance[userID] = nil } }
            return try await (self?.obtainToken(for: userID, baseURL: baseURL) ?? "")
        }
        pendingIssuance[userID] = task
        return try await task.value
    }

    func clear(for userID: String) {
        cache.removeValue(forKey: userID)
        Keychain.delete(keychainAccount(userID: userID))
    }

    private func keychainAccount(userID: String) -> String {
        "auth.token.\(userID)"
    }
}
