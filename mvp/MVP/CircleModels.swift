import Foundation

// MARK: - Circle DTOs
//
// Circle (beta-v1 sprint 2) replaces the old public community board + 1:1 DM
// inbox with mutual-link GROUP conversations scoped to a parent's own
// household circle (grandparents, sitters, close friends). Every optional /
// numeric field mirrors CLAUDE.md's Codable-strictness rule: iOS Codable is
// strict, so one type mismatch would silently empty the WHOLE conversations
// or messages list — every field the backend didn't guarantee non-null stays
// optional here.

struct CircleParticipant: Codable, Identifiable, Hashable {
    let userId: String?
    let memberId: String
    let displayName: String
    let initials: String

    var id: String { memberId }

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case memberId = "member_id"
        case displayName = "display_name"
        case initials
    }
}

struct CircleConversation: Codable, Identifiable, Hashable {
    let id: String
    let title: String
    let body: String
    let ownerUserId: String?
    let createdAt: String?
    let lastReplyAt: String?
    let replyCount: Int?
    let lastReplyFrom: String?
    let starterName: String?
    let starterIsMe: Bool?
    let unread: Int?
    let participants: [CircleParticipant]?

    enum CodingKeys: String, CodingKey {
        case id, title, body, participants
        case ownerUserId = "owner_user_id"
        case createdAt = "created_at"
        case lastReplyAt = "last_reply_at"
        case replyCount = "reply_count"
        case lastReplyFrom = "last_reply_from"
        case starterName = "starter_name"
        case starterIsMe = "starter_is_me"
        case unread
    }

    /// True when `userID` owns this conversation — gates Edit/Delete in the
    /// row context menu. Falls back to `starterIsMe` if the backend ever
    /// omits `owner_user_id` (both should agree; owner is the load-bearing
    /// signal since a conversation could theoretically be transferred later).
    func isOwned(by userID: String) -> Bool {
        if let ownerUserId { return ownerUserId == userID && !userID.isEmpty }
        return starterIsMe ?? false
    }
}

struct CircleMessage: Codable, Identifiable, Hashable {
    let id: String
    let userId: String?
    let authorName: String
    let initials: String
    let body: String
    let createdAt: String?
    let isMe: Bool?

    enum CodingKeys: String, CodingKey {
        case id, body, initials
        case userId = "user_id"
        case authorName = "author_name"
        case createdAt = "created_at"
        case isMe = "is_me"
    }
}

/// A household roster entry — feeds the "Invite to the conversation" /
/// "Add circle members" pickers. `GET /household/members` already exists on
/// the backend; Circle is the first iOS surface to consume it.
struct HouseholdMember: Codable, Identifiable, Hashable {
    let id: String
    let displayName: String
    let role: String?
    let relation: String?
    let initials: String?
    let avatarKey: String?

    enum CodingKeys: String, CodingKey {
        case id, role, relation
        case displayName = "display_name"
        case initials
        case avatarKey = "avatar_key"
    }

    /// Falls back to deriving initials from the display name when the API
    /// doesn't send them.
    var resolvedInitials: String {
        if let initials, !initials.isEmpty { return initials }
        let parts = displayName.split(separator: " ")
        let letters = parts.prefix(2).compactMap { $0.first }
        return letters.isEmpty ? "?" : String(letters).uppercased()
    }
}

struct CircleInvite: Codable {
    let token: String
    let url: String
    let expiresAt: String?

    enum CodingKeys: String, CodingKey {
        case token, url
        case expiresAt = "expires_at"
    }
}

struct CircleInvitePreview: Codable {
    let inviterName: String?
    let householdLabel: String?
    let kidsLabel: String?
    let expired: Bool?
    let claimed: Bool?

    enum CodingKeys: String, CodingKey {
        case inviterName = "inviter_name"
        case householdLabel = "household_label"
        case kidsLabel = "kids_label"
        case expired, claimed
    }
}
