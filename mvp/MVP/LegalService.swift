import Foundation

/// Client for the versioned legal documents (privacy policy / terms).
///
/// The REQUIRED version lives server-side (the CMS-published current row), so
/// the client never hardcodes versions: it fetches `/legal/status`, shows the
/// docs it was told about, and echoes those exact versions back on accept.
/// A 409 means a new version was published mid-flight — re-fetch and retry
/// once so the user never accepts text they weren't shown.
struct LegalDocStatus: Decodable {
    let slug: String
    let title: String
    let requiredVersion: String
    let requiresReacceptance: Bool
    let acceptedVersion: String?
    let accepted: Bool

    enum CodingKeys: String, CodingKey {
        case slug, title, accepted
        case requiredVersion = "required_version"
        case requiresReacceptance = "requires_reacceptance"
        case acceptedVersion = "accepted_version"
    }
}

struct LegalStatus: Decodable {
    let documents: [LegalDocStatus]
    let acceptedAll: Bool
    let needs: [String]

    enum CodingKeys: String, CodingKey {
        case documents, needs
        case acceptedAll = "accepted_all"
    }
}

enum LegalService {

    /// Durable marker: the user agreed (onboarding checkbox) but the POST may
    /// not have landed yet. Flushed on every launch — same self-heal philosophy
    /// as the pending onboarding seed. Cleared by AppSession.signOut so the
    /// next account on this device never inherits an agreement.
    static let acceptPendingKey = "legal_accept_pending"

    @MainActor
    static func fetchStatus(userID: String, baseURL: URL) async throws -> LegalStatus {
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        var request = URLRequest(url: baseURL.appendingPathComponent("legal/status"))
        request.timeoutInterval = 15
        for (k, v) in AuthService.shared.header(for: userID) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        let (data, response) = try await URLSession.shared.data(for: request)
        guard (response as? HTTPURLResponse)?.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(LegalStatus.self, from: data)
    }

    /// Accept the CURRENT versions of every doc the server says needs it.
    /// Returns the refreshed status on success, nil on failure (caller retries
    /// later — the pending flag stays set).
    @MainActor
    @discardableResult
    static func acceptCurrent(userID: String, baseURL: URL, surface: String) async -> LegalStatus? {
        for attempt in 0..<2 {
            guard let status = try? await fetchStatus(userID: userID, baseURL: baseURL) else { return nil }
            if status.acceptedAll {
                return status
            }
            let versions = Dictionary(
                uniqueKeysWithValues: status.documents
                    .filter { !$0.accepted }
                    .map { ($0.slug, $0.requiredVersion) }
            )
            var request = URLRequest(url: baseURL.appendingPathComponent("legal/accept"))
            request.httpMethod = "POST"
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.timeoutInterval = 15
            for (k, v) in AuthService.shared.header(for: userID) {
                request.setValue(v, forHTTPHeaderField: k)
            }
            request.httpBody = try? JSONSerialization.data(
                withJSONObject: ["versions": versions, "platform": "ios"]
            )
            guard let (_, response) = try? await URLSession.shared.data(for: request),
                  let http = response as? HTTPURLResponse else { return nil }
            if http.statusCode == 200 {
                Analytics.capture("legal_accepted", ["surface": surface])
                return try? await fetchStatus(userID: userID, baseURL: baseURL)
            }
            // 409 = a new version was published between fetch and accept.
            // Loop re-fetches so the retry echoes the versions now current.
            if http.statusCode != 409 || attempt == 1 { return nil }
        }
        return nil
    }
}
