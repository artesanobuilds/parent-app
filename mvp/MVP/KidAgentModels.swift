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
    // Present on /kid-agent/list: a crisis lock deactivated this companion and it
    // needs a parent review before it can talk again. nil on endpoints that don't
    // compute it (treated as not-locked).
    let crisisLocked: Bool?

    enum CodingKeys: String, CodingKey {
        case id, version, invariants, model, enabled
        case userID         = "user_id"
        case kidName        = "kid_name"
        case freeTextBrief  = "free_text_brief"
        case systemPrompt   = "system_prompt"
        case contentHash    = "content_hash"
        case createdAt      = "created_at"
        case crisisLocked   = "crisis_locked"
    }
}

/// Provider-scoped voice handle stored on the kid agent's invariants. Mirrors
/// the backend `VoiceSpec` Pydantic model in `app/voice/provider.py`.
struct VoiceSpec: Codable, Equatable, Sendable {
    let provider: String
    let voiceID: String
    let model: String
    /// Optional prosody hints (rate, pitch, stability...). String-typed because
    /// the on-wire schema is `Dict[str, Any]` and we don't synthesize on iOS —
    /// the backend interprets these.
    let prosody: [String: String]?

    enum CodingKeys: String, CodingKey {
        case provider, model, prosody
        case voiceID = "voice_id"
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
    /// Renamed from `voice_examples` to disambiguate from TTS voice. The
    /// decoder accepts either key for one release; encode always writes the
    /// new `persona_examples`.
    var personaExamples: [String]
    var voice: VoiceSpec?

    enum CodingKeys: String, CodingKey {
        case agentDisplayName       = "agent_display_name"
        case personalityDescription = "personality_description"
        case interestsSummary       = "interests_summary"
        case topicsAllowed          = "topics_allowed"
        case topicsBlocked          = "topics_blocked"
        case toolsEnabled           = "tools_enabled"
        case goals
        case personaExamples        = "persona_examples"
        case voice
    }

    /// Legacy key path kept only for decode-side backwards compatibility.
    private enum LegacyKeys: String, CodingKey {
        case voiceExamples = "voice_examples"
    }

    init(
        agentDisplayName: String,
        personalityDescription: String,
        interestsSummary: String,
        topicsAllowed: [String],
        topicsBlocked: [String],
        toolsEnabled: [String: Bool],
        goals: [String],
        personaExamples: [String],
        voice: VoiceSpec? = nil
    ) {
        self.agentDisplayName = agentDisplayName
        self.personalityDescription = personalityDescription
        self.interestsSummary = interestsSummary
        self.topicsAllowed = topicsAllowed
        self.topicsBlocked = topicsBlocked
        self.toolsEnabled = toolsEnabled
        self.goals = goals
        self.personaExamples = personaExamples
        self.voice = voice
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        agentDisplayName       = try c.decode(String.self, forKey: .agentDisplayName)
        personalityDescription = try c.decode(String.self, forKey: .personalityDescription)
        interestsSummary       = try c.decode(String.self, forKey: .interestsSummary)
        topicsAllowed          = try c.decode([String].self, forKey: .topicsAllowed)
        topicsBlocked          = try c.decode([String].self, forKey: .topicsBlocked)
        toolsEnabled           = try c.decode([String: Bool].self, forKey: .toolsEnabled)
        goals                  = try c.decode([String].self, forKey: .goals)
        voice                  = try c.decodeIfPresent(VoiceSpec.self, forKey: .voice)
        if let examples = try c.decodeIfPresent([String].self, forKey: .personaExamples) {
            personaExamples = examples
        } else {
            let legacy = try decoder.container(keyedBy: LegacyKeys.self)
            personaExamples = (try legacy.decodeIfPresent([String].self, forKey: .voiceExamples)) ?? []
        }
    }

    static let empty = KidAgentInvariants(
        agentDisplayName: "Friend",
        personalityDescription: "",
        interestsSummary: "",
        topicsAllowed: [],
        topicsBlocked: [],
        toolsEnabled: [:],
        goals: [],
        personaExamples: [],
        voice: nil
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

/// Reason codes for `KidAgentServiceError.voiceFallback`. iOS surfaces these
/// to telemetry and decides whether to short-circuit subsequent voice calls
/// for the session (e.g. cache `agentVoiceDisabled = true` on `.crisis`).
enum VoiceFallbackReason: String, Sendable {
    case crisis         // 403 — agent crisis-locked
    case quota          // 429 — per-user/global cap or rate limit
    case keyMissing     // 503 — ELEVENLABS_API_KEY unset / provider down
    case partialStream  // missing `X-Voice-Complete: 1` sentinel
    case network        // transport-level failure mid-stream
}

/// Errors surfaced by `KidAgentService`.
enum KidAgentServiceError: LocalizedError {
    case unauthorized
    case consentRequired(version: String)
    case versionConflict
    case invalidResponse
    case invalidURL
    case status(Int)
    case voiceFallback(reason: VoiceFallbackReason, status: Int)
    case underlying(Error)

    var errorDescription: String? {
        switch self {
        case .unauthorized:                return "Not signed in. Restart the app."
        case .consentRequired(let v):      return "Consent required (version \(v))."
        case .versionConflict:             return "Someone else updated this agent — please refresh."
        case .invalidResponse:             return "The server response was not valid."
        case .invalidURL:                  return "The server URL is misconfigured."
        case .status(let code):            return "Server returned status \(code)."
        case .voiceFallback(let r, let c): return "Voice unavailable (\(r.rawValue), \(c)) — using on-device voice."
        case .underlying(let err):         return err.localizedDescription
        }
    }
}
