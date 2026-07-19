import Foundation

// MARK: - DTOs (parent-to-parent direct messages)

struct DMMember: Codable, Identifiable, Hashable {
    let userId: String
    let displayName: String
    let initials: String
    var id: String { userId }

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case displayName = "display_name"
        case initials
    }
}

struct DMConversation: Codable, Identifiable, Hashable {
    let id: String
    let peerId: String
    let peerName: String
    let peerInitials: String
    let lastMessageAt: String?
    let lastMessagePreview: String
    let unreadCount: Int?
    let iBlocked: Bool?

    enum CodingKeys: String, CodingKey {
        case id
        case peerId = "peer_id"
        case peerName = "peer_name"
        case peerInitials = "peer_initials"
        case lastMessageAt = "last_message_at"
        case lastMessagePreview = "last_message_preview"
        case unreadCount = "unread_count"
        case iBlocked = "i_blocked"
    }
}

struct DMReaction: Codable, Hashable {
    let userId: String
    let emoji: String

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case emoji
    }
}

struct DMMessage: Codable, Identifiable, Hashable {
    let id: String
    let senderId: String
    let body: String
    let createdAt: String
    // Optional: the send response carries no reactions field, only the list.
    var reactions: [DMReaction]?

    enum CodingKeys: String, CodingKey {
        case id, body, reactions
        case senderId = "sender_id"
        case createdAt = "created_at"
    }
}

/// The classic six tapbacks — must match the server's DM_REACTION_EMOJI
/// allowlist (an out-of-set emoji is a 400).
enum DMTapback {
    static let all = ["❤️", "👍", "👎", "😂", "‼️", "❓"]
}

private struct DMMembersResponse: Codable { let members: [DMMember] }
private struct DMInboxResponse: Codable {
    let conversations: [DMConversation]
    let totalUnread: Int
    enum CodingKeys: String, CodingKey {
        case conversations
        case totalUnread = "total_unread"
    }
}
private struct DMMessagesResponse: Codable { let messages: [DMMessage] }
private struct DMReactionResponse: Codable {
    let messageId: String
    let reactions: [DMReaction]
    enum CodingKeys: String, CodingKey {
        case messageId = "message_id"
        case reactions
    }
}

// MARK: - Service

/// REST client for the DM endpoints. Same shape as ProfileService: static
/// funcs, Bearer via AuthService. Delivery is client polling (ConversationView
/// re-fetches on a timer while open) — no SSE in v1.
enum DMService {

    @MainActor
    private static func request(_ path: String, method: String = "GET",
                                body: [String: Any]? = nil,
                                userID: String, baseURL: URL) async throws -> Data {
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
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
    static func members(userID: String, baseURL: URL) async throws -> [DMMember] {
        let data = try await request("dm/members", userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(DMMembersResponse.self, from: data).members
    }

    @MainActor
    static func inbox(userID: String, baseURL: URL) async throws -> (conversations: [DMConversation], totalUnread: Int) {
        let data = try await request("dm/conversations", userID: userID, baseURL: baseURL)
        let decoded = try JSONDecoder().decode(DMInboxResponse.self, from: data)
        return (decoded.conversations, decoded.totalUnread)
    }

    @MainActor
    static func startConversation(peerId: String, userID: String, baseURL: URL) async throws -> DMConversation {
        let data = try await request("dm/conversations", method: "POST",
                                     body: ["peer_user_id": peerId],
                                     userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(DMConversation.self, from: data)
    }

    @MainActor
    static func messages(conversationId: String, before: String? = nil,
                         userID: String, baseURL: URL) async throws -> [DMMessage] {
        var path = "dm/conversations/\(conversationId)/messages"
        if let before {
            path += "?before=\(before.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? before)"
        }
        let data = try await request(path, userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(DMMessagesResponse.self, from: data).messages
    }

    @MainActor
    @discardableResult
    static func send(conversationId: String, body: String,
                     userID: String, baseURL: URL) async throws -> DMMessage {
        let data = try await request("dm/conversations/\(conversationId)/messages",
                                     method: "POST", body: ["body": body],
                                     userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(DMMessage.self, from: data)
    }

    /// Tapback: set/replace my one reaction on a message; the SAME emoji (or
    /// nil) removes it. Returns the message's authoritative reaction list.
    @MainActor
    static func setReaction(messageId: String, emoji: String?, conversationId: String,
                            userID: String, baseURL: URL) async throws -> [DMReaction] {
        let body: [String: Any] = ["message_id": messageId, "emoji": emoji ?? NSNull()]
        let data = try await request("dm/conversations/\(conversationId)/reactions",
                                     method: "POST", body: body,
                                     userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(DMReactionResponse.self, from: data).reactions
    }

    @MainActor
    static func markRead(conversationId: String, userID: String, baseURL: URL) async {
        _ = try? await request("dm/conversations/\(conversationId)/read",
                               method: "POST", body: [:], userID: userID, baseURL: baseURL)
    }

    @MainActor
    static func setBlocked(_ blocked: Bool, conversationId: String,
                           userID: String, baseURL: URL) async throws {
        _ = try await request("dm/conversations/\(conversationId)/\(blocked ? "block" : "unblock")",
                              method: "POST", body: [:], userID: userID, baseURL: baseURL)
    }

    @MainActor
    static func report(conversationId: String, note: String?,
                       userID: String, baseURL: URL) async throws {
        _ = try await request("dm/conversations/\(conversationId)/report",
                              method: "POST", body: ["note": note ?? ""],
                              userID: userID, baseURL: baseURL)
    }
}
