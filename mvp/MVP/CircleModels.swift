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

/// One "More about {name}" disclosure row, as the SERVER labels it.
///
/// The role→attribute matrix (which keys exist, and that `co_parent_goals`
/// belongs to co-parents only) lives on the backend and arrives with the
/// member — the sheet renders what it is handed rather than re-deriving the
/// matrix here, where the two could drift.
struct MemberAttributeField: Codable, Identifiable, Hashable {
    let key: String
    let label: String
    /// `"list"` (free text the parent adds to) or `"choice"` (pick one of
    /// `choices`). The server decides, so the client never duplicates the rule
    /// about which roles get which field.
    let kind: String?
    let choices: [String]?

    var id: String { key }

    /// A single-select field renders as a chip row inline, not as a
    /// drill-into-a-list row.
    var isChoice: Bool { kind == "choice" }
}

/// A household roster entry — feeds the "Invite to the conversation" /
/// "Add circle members" pickers, the Contacts screen, and `MemberProfileSheet`.
/// `GET /household/members` and `GET|PATCH /household/members/{id}` return the
/// SAME envelope member, so one DTO covers list and detail.
///
/// Only `id` + `display_name` are required. Everything else is optional even
/// where the server always sends it: iOS Codable is strict, and one mistyped
/// field would empty the WHOLE roster (and with it the Circle composer).
struct HouseholdMember: Codable, Identifiable, Hashable {
    let id: String
    let displayName: String
    let role: String?
    let roleLabel: String?
    let relation: String?
    let initials: String?
    let kind: String?
    let mvpUsername: String?
    let email: String?
    let avatarKey: String?
    let avatarUrl: String?
    /// The MVP account this roster row IS, once the link is bound. `nil` until
    /// the other side accepts (or claims an invite).
    let memberUserId: String?
    /// Server-computed: `member_user_id != nil`. The roster row points at a
    /// real account.
    let linked: Bool?
    /// Server-computed: linked AND the link is MUTUAL (both directions bound).
    /// This — not any prose in `notes` — is what "they're really in my circle"
    /// means.
    let inCircle: Bool?
    /// Server-computed: this roster row is waiting on the other person — either
    /// a pending Circle request or an unclaimed invite. ONE flag for both, so
    /// the screen can't reveal which (that would leak whether the email matched
    /// an existing account).
    let pending: Bool?
    let attributes: [String: [String]]?
    let attributeFields: [MemberAttributeField]?
    let notes: String?
    let editable: Bool?

    enum CodingKeys: String, CodingKey {
        case id, role, relation, initials, kind, email, attributes, notes, editable, pending
        case displayName = "display_name"
        case roleLabel = "role_label"
        case mvpUsername = "mvp_username"
        case avatarKey = "avatar_key"
        case avatarUrl = "avatar_url"
        case memberUserId = "member_user_id"
        case linked
        case inCircle = "in_circle"
        case attributeFields = "attribute_fields"
    }

    /// Falls back to deriving initials from the display name when the API
    /// doesn't send them.
    var resolvedInitials: String {
        if let initials, !initials.isEmpty { return initials }
        let parts = displayName.split(separator: " ")
        let letters = parts.prefix(2).compactMap { $0.first }
        return letters.isEmpty ? "?" : String(letters).uppercased()
    }

    /// True once this contact is a real, mutual circle peer — they hold an MVP
    /// account and the link is bound in both directions.
    ///
    /// Keyed off the server's booleans, NEVER off `notes` — the roster row's
    /// note is prose written for two different pending paths ("Circle request
    /// sent — waiting on them to accept." vs "Invited to MVP — waiting on them
    /// to join."), and keying UI off copy makes a copy edit a functional change.
    var isConnected: Bool { inCircle ?? (memberUserId != nil) }

    /// A contact we reached out to who hasn't come back yet.
    ///
    /// Server-computed (`pending_outbound_member_ids`): a pending Circle request
    /// or an unclaimed, unexpired invite token. It is one flag for both paths on
    /// purpose — a matched request and an emailed invite must look identical, or
    /// the screen becomes the email-enumeration oracle `POST /circle/contacts`
    /// refuses to be.
    ///
    /// The `email != nil` fallback is only for an older backend that doesn't
    /// send the flag. It over-reports (a nanny typed in with an email reads as
    /// pending), which is why the server now computes it.
    var isPending: Bool {
        if let pending { return pending }
        return !isConnected && !(email ?? "").isEmpty
    }

    /// Family-side roles get the "Family role" field; circle-member roles
    /// don't (Greg's `circle member` frame drops it).
    var isFamilyRole: Bool {
        ["me", "spouse", "co_parent"].contains(role ?? "")
    }
}

/// Envelope for `GET|PATCH /household/members/{id}` and `POST /household/members`.
struct HouseholdMemberEnvelope: Codable { let member: HouseholdMember }

/// An INBOUND pending "let me into your Circle" ask — `GET /circle/requests`.
/// Accepting is the consent step that makes the link mutual (and existing
/// threads readable), so Circle surfaces these above the conversation list.
struct CircleRequest: Codable, Identifiable, Hashable {
    let id: String
    let fromUserId: String
    let fromName: String
    let initials: String
    let status: String
    /// ISO-8601, and NULLABLE on the wire — must stay optional.
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id, initials, status
        case fromUserId = "from_user_id"
        case fromName = "from_name"
        case createdAt = "created_at"
    }
}

/// `POST /circle/requests/{id}/accept|decline`.
struct CircleRequestAction: Codable {
    let ok: Bool
    let status: String
    let fromUserId: String

    enum CodingKeys: String, CodingKey {
        case ok, status
        case fromUserId = "from_user_id"
    }
}

/// `POST /circle/contacts`. 200 with `{"status": "sent"}` on EVERY path —
/// matched, unmatched, yourself, already-a-peer, duplicate. The UI must not
/// branch on it: a match and a miss being indistinguishable is the security
/// property (it stops the route being an email-enumeration oracle). Decoded
/// only so a garbled body still surfaces as an error.
struct CircleContactAck: Codable { let status: String }

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
