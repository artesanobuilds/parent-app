import Foundation

private struct CircleConversationsResponse: Codable { let conversations: [CircleConversation] }
private struct CircleThreadResponse: Codable {
    let conversation: CircleConversation
    let messages: [CircleMessage]
}
private struct HouseholdMembersResponse: Codable { let members: [HouseholdMember] }

/// REST client for the `/circle/*` + `/household/members` endpoints. Same
/// shape as the other REST clients: static funcs, Bearer via `AuthService`, base URL
/// resolved ONLY through the caller-supplied `baseURL` (itself sourced from
/// `ServerConfiguration` upstream) — never a hardcoded fallback.
enum CircleService {

    enum CircleServiceError: Error {
        case status(Int)
        /// A conversation that's been deleted, or a stale push deep link —
        /// callers fall back to the conversation LIST, never crash.
        var isNotFound: Bool { if case .status(404) = self { return true }; return false }
    }

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
        guard let http = response as? HTTPURLResponse else { throw URLError(.badServerResponse) }
        guard (200..<300).contains(http.statusCode) else {
            throw CircleServiceError.status(http.statusCode)
        }
        return data
    }

    @MainActor
    static func conversations(userID: String, baseURL: URL) async throws -> [CircleConversation] {
        let data = try await request("circle/conversations", userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(CircleConversationsResponse.self, from: data).conversations
    }

    @MainActor
    static func createConversation(title: String, body: String, memberIds: [String],
                                   userID: String, baseURL: URL) async throws -> CircleConversation {
        let payload: [String: Any] = ["title": title, "body": body, "member_ids": memberIds]
        let data = try await request("circle/conversations", method: "POST", body: payload,
                                     userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(CircleConversation.self, from: data)
    }

    @MainActor
    static func thread(id: String, userID: String, baseURL: URL) async throws
        -> (conversation: CircleConversation, messages: [CircleMessage]) {
        let data = try await request("circle/conversations/\(id)", userID: userID, baseURL: baseURL)
        let decoded = try JSONDecoder().decode(CircleThreadResponse.self, from: data)
        return (decoded.conversation, decoded.messages)
    }

    @MainActor
    static func updateConversation(id: String, title: String? = nil, body: String? = nil,
                                   userID: String, baseURL: URL) async throws -> CircleConversation {
        var payload: [String: Any] = [:]
        if let title { payload["title"] = title }
        if let body { payload["body"] = body }
        let data = try await request("circle/conversations/\(id)", method: "PATCH", body: payload,
                                     userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(CircleConversation.self, from: data)
    }

    @MainActor
    static func deleteConversation(id: String, userID: String, baseURL: URL) async throws {
        _ = try await request("circle/conversations/\(id)", method: "DELETE",
                              userID: userID, baseURL: baseURL)
    }

    @MainActor
    @discardableResult
    static func sendMessage(conversationId: String, body: String,
                            userID: String, baseURL: URL) async throws -> CircleMessage {
        let data = try await request("circle/conversations/\(conversationId)/messages",
                                     method: "POST", body: ["body": body],
                                     userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(CircleMessage.self, from: data)
    }

    @MainActor
    static func addParticipants(conversationId: String, memberIds: [String],
                                userID: String, baseURL: URL) async throws -> CircleConversation {
        let data = try await request("circle/conversations/\(conversationId)/participants",
                                     method: "POST", body: ["member_ids": memberIds],
                                     userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(CircleConversation.self, from: data)
    }

    @MainActor
    static func markRead(conversationId: String, userID: String, baseURL: URL) async {
        _ = try? await request("circle/conversations/\(conversationId)/read",
                               method: "POST", body: [:], userID: userID, baseURL: baseURL)
    }

    @MainActor
    static func householdMembers(userID: String, baseURL: URL) async throws -> [HouseholdMember] {
        let data = try await request("household/members", userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(HouseholdMembersResponse.self, from: data).members
    }

    @MainActor
    static func createInvite(memberId: String? = nil, userID: String, baseURL: URL) async throws -> CircleInvite {
        var payload: [String: Any] = [:]
        if let memberId { payload["member_id"] = memberId }
        let data = try await request("circle/invites", method: "POST", body: payload,
                                     userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(CircleInvite.self, from: data)
    }

    @MainActor
    static func invitePreview(token: String, userID: String, baseURL: URL) async throws -> CircleInvitePreview {
        let data = try await request("circle/invites/\(token)", userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(CircleInvitePreview.self, from: data)
    }
}
