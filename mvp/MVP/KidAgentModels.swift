import Foundation

/// Mirrors the backend `KidAgentConfig` returned by `/kid-agent/config`.
struct KidAgentConfig: Codable, Identifiable, Equatable, Sendable {
    let id: String
    let userID: String
    let kidName: String
    let version: Int
    let invariants: KidAgentInvariants
    let freeTextBrief: String
    let systemPrompt: String
    let contentHash: String
    let model: String
    let enabled: Bool
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id, version, invariants, model, enabled
        case userID         = "user_id"
        case kidName        = "kid_name"
        case freeTextBrief  = "free_text_brief"
        case systemPrompt   = "system_prompt"
        case contentHash    = "content_hash"
        case createdAt      = "created_at"
    }
}

/// Mirrors backend `SynthesizedInvariants`. Plain dicts/arrays for tools so we
/// can be loose about future tool keys.
struct KidAgentInvariants: Codable, Equatable, Sendable {
    var agentDisplayName: String
    var personalityDescription: String
    var interestsSummary: String
    var topicsAllowed: [String]
    var topicsBlocked: [String]
    var toolsEnabled: [String: Bool]
    var goals: [String]
    var voiceExamples: [String]

    enum CodingKeys: String, CodingKey {
        case agentDisplayName       = "agent_display_name"
        case personalityDescription = "personality_description"
        case interestsSummary       = "interests_summary"
        case topicsAllowed          = "topics_allowed"
        case topicsBlocked          = "topics_blocked"
        case toolsEnabled           = "tools_enabled"
        case goals
        case voiceExamples          = "voice_examples"
    }

    static let empty = KidAgentInvariants(
        agentDisplayName: "Friend",
        personalityDescription: "",
        interestsSummary: "",
        topicsAllowed: [],
        topicsBlocked: [],
        toolsEnabled: [:],
        goals: [],
        voiceExamples: []
    )
}

/// Response from `/kid-agent/preview` — the no-save synthesis used by the
/// letter editor for live regeneration.
struct KidAgentPreview: Codable, Equatable {
    let invariants: KidAgentInvariants
    let summary: String
    let contentHash: String
    let systemPromptExcerpt: String
    let previewMessages: [String]

    enum CodingKeys: String, CodingKey {
        case invariants, summary
        case contentHash         = "content_hash"
        case systemPromptExcerpt = "system_prompt_excerpt"
        case previewMessages     = "preview_messages"
    }
}

/// Consent status from `/consent/status`.
struct ConsentStatus: Codable, Equatable {
    let accepted: Bool
    let latestVersion: String
    let acceptedVersion: String?

    enum CodingKeys: String, CodingKey {
        case accepted
        case latestVersion   = "latest_version"
        case acceptedVersion = "accepted_version"
    }
}

/// Errors surfaced by `KidAgentService`.
enum KidAgentServiceError: LocalizedError {
    case unauthorized
    case consentRequired(version: String)
    case versionConflict
    case invalidResponse
    case invalidURL
    case status(Int)
    case underlying(Error)

    var errorDescription: String? {
        switch self {
        case .unauthorized:                return "Not signed in. Restart the app."
        case .consentRequired(let v):      return "Consent required (version \(v))."
        case .versionConflict:             return "Someone else updated this agent — please refresh."
        case .invalidResponse:             return "The server response was not valid."
        case .invalidURL:                  return "The server URL is misconfigured."
        case .status(let code):            return "Server returned status \(code)."
        case .underlying(let err):         return err.localizedDescription
        }
    }
}
