import Foundation

// MARK: - API Response Models

struct APICategory: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let emoji: String
    let description: String
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

enum ContentService {
    static func fetchCategories(baseURL: URL) async throws -> [APICategory] {
        let url = baseURL.appendingPathComponent("content/categories")
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode([APICategory].self, from: data)
    }

    static func fetchArticles(baseURL: URL, category: String? = nil) async throws -> [APIArticle] {
        var components = URLComponents(url: baseURL.appendingPathComponent("content/articles"), resolvingAgainstBaseURL: false)!
        if let category = category {
            components.queryItems = [URLQueryItem(name: "category", value: category)]
        }
        let (data, _) = try await URLSession.shared.data(from: components.url!)
        return try JSONDecoder().decode([APIArticle].self, from: data)
    }

    static func fetchArticle(baseURL: URL, id: String) async throws -> APIArticle {
        let url = baseURL.appendingPathComponent("content/articles/\(id)")
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(APIArticle.self, from: data)
    }

    static func fetchReplies(baseURL: URL, postId: String) async throws -> [APIReply] {
        let url = baseURL.appendingPathComponent("content/community/\(postId)/replies")
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode([APIReply].self, from: data)
    }

    static func createReply(baseURL: URL, postId: String, userId: String, authorName: String, body: String) async throws -> APIReply {
        let url = baseURL.appendingPathComponent("content/community/\(postId)/replies")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userId, baseURL: baseURL) { request.setValue(v, forHTTPHeaderField: k) }
        let payload: [String: String] = ["user_id": userId, "author_name": authorName, "body": body]
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(APIReply.self, from: data)
    }

    static func createCommunityPost(baseURL: URL, category: String, title: String, preview: String, userId: String, authorName: String) async throws -> APICommunityPost {
        let url = baseURL.appendingPathComponent("content/community/new")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userId, baseURL: baseURL) { request.setValue(v, forHTTPHeaderField: k) }
        let payload: [String: String] = [
            "category": category,
            "title": title,
            "preview": preview,
            "user_id": userId,
            "author_name": authorName
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(APICommunityPost.self, from: data)
    }

    /// Ensure a Bearer token for userID and return the Authorization header.
    /// Empty if issuance fails (old backend ignores it; the new backend will
    /// 401 once the community-write lock ships, surfacing the issue).
    @MainActor
    private static func authHeader(userID: String, baseURL: URL) async -> [String: String] {
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        return AuthService.shared.header(for: userID)
    }

    static func fetchCommunityPosts(baseURL: URL, category: String? = nil) async throws -> [APICommunityPost] {
        var components = URLComponents(url: baseURL.appendingPathComponent("content/community"), resolvingAgainstBaseURL: false)!
        if let category = category {
            components.queryItems = [URLQueryItem(name: "category", value: category)]
        }
        let (data, _) = try await URLSession.shared.data(from: components.url!)
        return try JSONDecoder().decode([APICommunityPost].self, from: data)
    }
}
