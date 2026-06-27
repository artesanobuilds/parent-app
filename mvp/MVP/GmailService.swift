import AuthenticationServices
import Foundation
import UIKit

// MARK: - DTOs (mirror app/oauth/router.py)

/// A connected Google account (one per kind). Never carries the token.
struct GoogleAccount: Codable, Identifiable, Hashable {
    let provider: String
    let kind: String           // email | calendar
    let accountEmail: String?
    let status: String         // connected | revoked | error
    let connectedAt: String?
    let lastSyncAt: String?

    var id: String { "\(provider):\(kind)" }
    var isConnected: Bool { status == "connected" }

    enum CodingKeys: String, CodingKey {
        case provider, kind, status
        case accountEmail = "account_email"
        case connectedAt = "connected_at"
        case lastSyncAt = "last_sync_at"
    }
}

struct GoogleStatus: Codable {
    let configured: Bool
    let accounts: [GoogleAccount]
}

enum GmailServiceError: LocalizedError {
    case httpError(Int)
    case invalidResponse
    case notConfigured       // backend has no Google OAuth client yet (503)
    case authCancelled
    case authFailed(String)

    var errorDescription: String? {
        switch self {
        case .httpError(let c): return "The server returned status \(c)."
        case .invalidResponse: return "The server response was not valid."
        case .notConfigured:
            return "Gmail connection isn't available yet. Please try again later."
        case .authCancelled: return "Connection canceled."
        case .authFailed(let m): return m
        }
    }
}

// MARK: - Service

/// Networking for the Google OAuth flow (/oauth/google/*). Mirrors PlanService:
/// static funcs, Bearer auth via `authHeader`, a `sendDecoded` helper.
enum GmailService {

    private static func validate(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else {
            throw GmailServiceError.invalidResponse
        }
        if http.statusCode == 503 { throw GmailServiceError.notConfigured }
        guard (200..<300).contains(http.statusCode) else {
            throw GmailServiceError.httpError(http.statusCode)
        }
    }

    private static func sendDecoded<T: Decodable>(_ request: URLRequest) async throws -> T {
        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response)
        return try JSONDecoder().decode(T.self, from: data)
    }

    @MainActor
    private static func authHeader(userID: String, baseURL: URL) async -> [String: String] {
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        return AuthService.shared.header(for: userID)
    }

    /// Fetch the Google consent URL to open in the in-app browser.
    static func authorizeURL(
        baseURL: URL, userID: String, kinds: [String] = ["email", "calendar"]
    ) async throws -> URL {
        var components = URLComponents(
            url: baseURL.appendingPathComponent("oauth/google/authorize-url"),
            resolvingAgainstBaseURL: false
        )!
        components.queryItems = [URLQueryItem(name: "kinds", value: kinds.joined(separator: ","))]
        guard let url = components.url else { throw GmailServiceError.invalidResponse }
        var request = URLRequest(url: url)
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        let resp: AuthorizeURLResponse = try await sendDecoded(request)
        guard let authURL = URL(string: resp.authorizationURL) else {
            throw GmailServiceError.invalidResponse
        }
        return authURL
    }

    static func status(baseURL: URL, userID: String) async throws -> GoogleStatus {
        let url = baseURL.appendingPathComponent("oauth/google/status")
        var request = URLRequest(url: url)
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        return try await sendDecoded(request)
    }

    /// Queue a two-way Google Calendar sync for this parent (POST /cos/calendar/sync).
    /// The backend runs it on its worker; this returns once the run is enqueued.
    static func syncCalendar(baseURL: URL, userID: String) async throws {
        let url = baseURL.appendingPathComponent("cos/calendar/sync")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        request.httpBody = try JSONSerialization.data(withJSONObject: ["user_id": userID])
        let (_, response) = try await URLSession.shared.data(for: request)
        try validate(response)
    }

    static func disconnect(baseURL: URL, userID: String, kind: String) async throws {
        let url = baseURL.appendingPathComponent("oauth/google/disconnect")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        request.httpBody = try JSONSerialization.data(withJSONObject: ["user_id": userID, "kind": kind])
        let (_, response) = try await URLSession.shared.data(for: request)
        try validate(response)
    }

    private struct AuthorizeURLResponse: Decodable {
        let authorizationURL: String
        enum CodingKeys: String, CodingKey { case authorizationURL = "authorization_url" }
    }
}

// MARK: - Web auth

/// Drives an `ASWebAuthenticationSession` for the OAuth consent. The callback
/// scheme is intercepted by the session itself (no Info.plist registration
/// needed). Returns the `status` query value from the `mvparent://` redirect.
@MainActor
final class WebAuthRunner: NSObject, ASWebAuthenticationPresentationContextProviding {
    static let callbackScheme = "mvparent"
    private var session: ASWebAuthenticationSession?

    /// Run the flow; returns the parsed `status` (e.g. "success") + email, or
    /// throws on cancel/failure.
    func run(authorizationURL: URL) async throws -> (status: String, email: String?) {
        let callback: URL = try await withCheckedThrowingContinuation { cont in
            let session = ASWebAuthenticationSession(
                url: authorizationURL, callbackURLScheme: Self.callbackScheme
            ) { url, error in
                if let url = url {
                    cont.resume(returning: url)
                } else if let asError = error as? ASWebAuthenticationSessionError,
                          asError.code == .canceledLogin {
                    cont.resume(throwing: GmailServiceError.authCancelled)
                } else {
                    cont.resume(throwing: GmailServiceError.authFailed(
                        error?.localizedDescription ?? "Connection failed."))
                }
            }
            session.presentationContextProvider = self
            session.prefersEphemeralWebBrowserSession = false
            self.session = session
            if !session.start() {
                cont.resume(throwing: GmailServiceError.authFailed("Couldn't open the consent screen."))
            }
        }

        let items = URLComponents(url: callback, resolvingAgainstBaseURL: false)?.queryItems ?? []
        let status = items.first { $0.name == "status" }?.value ?? "error"
        let email = items.first { $0.name == "email" }?.value
        if status != "success" {
            let reason = items.first { $0.name == "reason" }?.value ?? status
            throw GmailServiceError.authFailed("Couldn't connect Gmail (\(reason)).")
        }
        return (status, email)
    }

    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        let scene = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first { $0.activationState == .foregroundActive }
        return scene?.keyWindow ?? ASPresentationAnchor()
    }
}
