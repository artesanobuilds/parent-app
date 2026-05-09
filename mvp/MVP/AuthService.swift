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

    func clear(for userID: String) {
        cache.removeValue(forKey: userID)
        Keychain.delete(keychainAccount(userID: userID))
    }

    private func keychainAccount(userID: String) -> String {
        "auth.token.\(userID)"
    }
}
