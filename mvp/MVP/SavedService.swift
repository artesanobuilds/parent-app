import Foundation

// MARK: - DTOs

struct SavedItem: Codable, Identifiable, Hashable {
    let id: String
    let itemType: String       // article | community_post | coach_reply | activity
    let itemRef: String
    let title: String
    let snippet: String
    let body: String
    let kidName: String?
    let savedAt: String?
    let origin: String?        // "saved" | "plan" (plan rows live in the Plan tab)

    enum CodingKeys: String, CodingKey {
        case id, title, snippet, body, origin
        case itemType = "item_type"
        case itemRef = "item_ref"
        case kidName = "kid_name"
        case savedAt = "saved_at"
    }
}

private struct SavedListResponse: Codable { let items: [SavedItem] }
private struct SavedRefsResponse: Codable { let refs: [String] }

// MARK: - Service

/// REST client for the Saved tab. Same shape as ProfileService/DMService.
enum SavedService {

    @MainActor
    private static func request(_ path: String, method: String = "GET",
                                body: [String: Any]? = nil,
                                userID: String, baseURL: URL) async throws -> Data {
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        guard var components = URLComponents(url: baseURL.appendingPathComponent(
            path.components(separatedBy: "?").first ?? path
        ), resolvingAgainstBaseURL: false) else { throw URLError(.badURL) }
        if let query = path.components(separatedBy: "?").dropFirst().first {
            components.query = query
        }
        guard let url = components.url else { throw URLError(.badURL) }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.timeoutInterval = 15
        for (k, v) in AuthService.shared.header(for: userID) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        if let body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
        }
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
        return data
    }

    @MainActor
    static func list(userID: String, baseURL: URL) async throws -> [SavedItem] {
        let data = try await request("saved", userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(SavedListResponse.self, from: data).items
    }

    @MainActor
    static func refs(itemType: String, userID: String, baseURL: URL) async throws -> Set<String> {
        let data = try await request("saved/refs?item_type=\(itemType)",
                                     userID: userID, baseURL: baseURL)
        return Set(try JSONDecoder().decode(SavedRefsResponse.self, from: data).refs)
    }

    /// Save a content item (article/community_post — server snapshots the
    /// title/tags) or a coach reply (body required — the snapshot's only copy).
    @MainActor
    static func save(itemType: String, itemRef: String, body: String? = nil,
                     surface: String, userID: String, baseURL: URL) async throws {
        var payload: [String: Any] = [
            "item_type": itemType, "item_ref": itemRef,
            "context": ["surface": surface],
        ]
        if let body { payload["body"] = body }
        _ = try await request("saved", method: "POST", body: payload,
                              userID: userID, baseURL: baseURL)
        Analytics.capture("item_saved", ["item_type": itemType, "surface": surface])
    }

    @MainActor
    static func unsave(itemType: String, itemRef: String, surface: String,
                       userID: String, baseURL: URL) async throws {
        _ = try await request("saved?item_type=\(itemType)&item_ref=\(itemRef)",
                              method: "DELETE", userID: userID, baseURL: baseURL)
        Analytics.capture("item_unsaved", ["item_type": itemType, "surface": surface])
    }
}
