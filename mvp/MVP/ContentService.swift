import Foundation

// MARK: - API Response Models

struct APICategory: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let emoji: String
    let description: String
    /// Soft self-reference into another category's `id`. `nil` = top-level
    /// parent; non-nil = child. Phase 0 added the column server-side; iOS
    /// uses it to filter browse views to top-level only until the
    /// hierarchical browse UX (Phase 3) lands.
    let parentID: String?

    enum CodingKeys: String, CodingKey {
        case id, name, emoji, description
        case parentID = "parent_id"
    }
}

struct APIArticle: Codable, Identifiable, Hashable {
    let id: String
    let category: String
    let title: String
    let subtitle: String
    let emoji: String
    let author: String
    let readTime: String
    let summary: String
    let tags: [String]
    let content: String?

    enum CodingKeys: String, CodingKey {
        case id, category, title, subtitle, emoji, author
        case readTime = "read_time"
        case summary, tags, content
    }
}

struct APICommunityPost: Codable, Identifiable, Hashable {
    let id: String
    let category: String
    let initials: String
    let name: String
    let title: String
    let preview: String
    let userId: String?
    let replyCount: Int?

    enum CodingKeys: String, CodingKey {
        case id, category, initials, name, title, preview
        case userId = "user_id"
        case replyCount = "reply_count"
    }
}

struct APIReply: Codable, Identifiable, Hashable {
    let id: String
    let postId: String
    let userId: String
    let authorName: String
    let initials: String
    let body: String

    enum CodingKeys: String, CodingKey {
        case id, initials, body
        case postId = "post_id"
        case userId = "user_id"
        case authorName = "author_name"
    }
}

// MARK: - Content Service

enum ContentServiceError: LocalizedError {
    case httpError(Int)
    case invalidResponse

    var errorDescription: String? {
        switch self {
        case .httpError(let code): return "The server returned status \(code)."
        case .invalidResponse:     return "The server response was not valid."
        }
    }
}

enum ContentService {

    // MARK: Request helpers (centralized HTTP-status validation)

    /// Validate that a response is a 2xx HTTPURLResponse. Without this a 404 /
    /// 500 surfaces as a confusing DecodingError instead of an HTTP error.
    private static func validate(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else {
            throw ContentServiceError.invalidResponse
        }
        guard (200..<300).contains(http.statusCode) else {
            throw ContentServiceError.httpError(http.statusCode)
        }
    }

    private static func getDecoded<T: Decodable>(_ url: URL) async throws -> T {
        let (data, response) = try await URLSession.shared.data(from: url)
        try validate(response)
        return try JSONDecoder().decode(T.self, from: data)
    }

    private static func sendDecoded<T: Decodable>(_ request: URLRequest) async throws -> T {
        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response)
        return try JSONDecoder().decode(T.self, from: data)
    }

    /// Ensure a Bearer token for userID and return the Authorization header.
    @MainActor
    private static func authHeader(userID: String, baseURL: URL) async -> [String: String] {
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        return AuthService.shared.header(for: userID)
    }

    // MARK: Reads

    static func fetchCategories(baseURL: URL) async throws -> [APICategory] {
        try await getDecoded(baseURL.appendingPathComponent("content/categories"))
    }

    static func fetchArticles(baseURL: URL, category: String? = nil, tag: String? = nil) async throws -> [APIArticle] {
        var components = URLComponents(url: baseURL.appendingPathComponent("content/articles"), resolvingAgainstBaseURL: false)!
        var items: [URLQueryItem] = []
        if let category = category {
            items.append(URLQueryItem(name: "category", value: category))
        }
        if let tag = tag {
            items.append(URLQueryItem(name: "tag", value: tag))
        }
        if !items.isEmpty {
            components.queryItems = items
        }
        guard let url = components.url else { throw ContentServiceError.invalidResponse }
        return try await getDecoded(url)
    }

    static func fetchArticle(baseURL: URL, id: String) async throws -> APIArticle {
        try await getDecoded(baseURL.appendingPathComponent("content/articles/\(id)"))
    }

    static func fetchReplies(baseURL: URL, postId: String) async throws -> [APIReply] {
        try await getDecoded(baseURL.appendingPathComponent("content/community/\(postId)/replies"))
    }

    static func fetchCommunityPosts(baseURL: URL, category: String? = nil) async throws -> [APICommunityPost] {
        var components = URLComponents(url: baseURL.appendingPathComponent("content/community"), resolvingAgainstBaseURL: false)!
        if let category = category {
            components.queryItems = [URLQueryItem(name: "category", value: category)]
        }
        guard let url = components.url else { throw ContentServiceError.invalidResponse }
        return try await getDecoded(url)
    }

    // MARK: Writes

    static func createReply(baseURL: URL, postId: String, userId: String, authorName: String, body: String) async throws -> APIReply {
        let url = baseURL.appendingPathComponent("content/community/\(postId)/replies")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userId, baseURL: baseURL) { request.setValue(v, forHTTPHeaderField: k) }
        request.httpBody = try JSONSerialization.data(withJSONObject:
            ["user_id": userId, "author_name": authorName, "body": body])
        return try await sendDecoded(request)
    }

    static func createCommunityPost(baseURL: URL, category: String, title: String, preview: String, userId: String, authorName: String) async throws -> APICommunityPost {
        let url = baseURL.appendingPathComponent("content/community/new")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userId, baseURL: baseURL) { request.setValue(v, forHTTPHeaderField: k) }
        request.httpBody = try JSONSerialization.data(withJSONObject: [
            "category": category, "title": title, "preview": preview,
            "user_id": userId, "author_name": authorName,
        ])
        return try await sendDecoded(request)
    }
}
