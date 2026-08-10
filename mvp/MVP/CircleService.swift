import Foundation

private struct CircleConversationsResponse: Codable { let conversations: [CircleConversation] }
private struct CircleThreadResponse: Codable {
    let conversation: CircleConversation
    let messages: [CircleMessage]
}
private struct HouseholdMembersResponse: Codable { let members: [HouseholdMember] }
private struct CircleRequestsResponse: Codable { let requests: [CircleRequest] }

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
        /// The only 400 `POST /circle/contacts` returns: a malformed email.
        var isBadRequest: Bool { if case .status(400) = self { return true }; return false }
        /// 409. Two meanings, both non-alarming: a circle request somebody
        /// ALREADY answered (another device, or a double tap — refresh, don't
        /// alert), and "that MVP name is already used in your household".
        var isConflict: Bool { if case .status(409) = self { return true }; return false }
        /// Alias for the request-inbox reading of a 409.
        var isAlreadyAnswered: Bool { isConflict }
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
    static func member(id: String, userID: String, baseURL: URL) async throws -> HouseholdMember {
        let data = try await request("household/members/\(id)", userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(HouseholdMemberEnvelope.self, from: data).member
    }

    /// PATCH one member. Partial update: ONLY the keys in `fields` are touched,
    /// so a Basics-only save can't blank the attributes the coach learned. The
    /// `attributes` bag, when sent, must be the WHOLE decoded object for the
    /// keys being changed — never spliced strings (the server role-scopes it and
    /// 400s on a key that doesn't belong to the role).
    @MainActor
    static func updateMember(id: String, fields: [String: Any],
                             userID: String, baseURL: URL) async throws -> HouseholdMember {
        let data = try await request("household/members/\(id)", method: "PATCH", body: fields,
                                     userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(HouseholdMemberEnvelope.self, from: data).member
    }

    /// Remove a roster row. The server cascades the mirrored caregivers row and
    /// the member's avatar blob (CLAUDE.md: deletes cascade).
    @MainActor
    static func deleteMember(id: String, userID: String, baseURL: URL) async throws {
        _ = try await request("household/members/\(id)", method: "DELETE",
                              userID: userID, baseURL: baseURL)
    }

    /// Add a contact by email. 200 on every path with a body that is always
    /// `{"status": "sent"}`; only a malformed email is a 400. Callers MUST NOT
    /// branch their copy on the result — see `CircleContactAck`.
    @MainActor
    @discardableResult
    static func addContact(email: String, displayName: String? = nil,
                           userID: String, baseURL: URL) async throws -> CircleContactAck {
        var payload: [String: Any] = ["email": email]
        if let displayName, !displayName.isEmpty { payload["display_name"] = displayName }
        let data = try await request("circle/contacts", method: "POST", body: payload,
                                     userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(CircleContactAck.self, from: data)
    }

    /// My pending INBOUND requests — the ones I can act on.
    @MainActor
    static func requests(userID: String, baseURL: URL) async throws -> [CircleRequest] {
        let data = try await request("circle/requests", userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(CircleRequestsResponse.self, from: data).requests
    }

    /// Accept (`accept: true`) or decline an inbound request. A 409 means it was
    /// already answered — `isAlreadyAnswered`, handled as "refresh", not an error.
    @MainActor
    @discardableResult
    static func respondToRequest(id: String, accept: Bool,
                                 userID: String, baseURL: URL) async throws -> CircleRequestAction {
        let verb = accept ? "accept" : "decline"
        let data = try await request("circle/requests/\(id)/\(verb)", method: "POST", body: [:],
                                     userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(CircleRequestAction.self, from: data)
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
