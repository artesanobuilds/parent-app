import Foundation

// DTOs for the family profile (GET /profile). The backend stores ~35 parent +
// ~23 kid fields (most populated by the coaching/onboarding agents over time);
// we decode them all so the profile editor can show + edit them. JSONDecoder
// ignores any field not declared here.

struct ParentProfileDTO: Codable {
    var name: String? = nil
    var pronouns: String? = nil
    var postalCode: String? = nil
    var country: String? = nil
    var primaryLanguage: String? = nil
    var parentAgeRange: String? = nil
    var adultsInHousehold: Int? = nil
    var householdStructure: String? = nil
    var employment: String? = nil
    var workHours: String? = nil
    var energyPattern: String? = nil
    var defaultStressResponse: String? = nil
    var dreadedMoment: String? = nil
    var supportSystem: String? = nil
    var supportBoundaries: String? = nil
    var culturalBackground: String? = nil
    var parentingStyle: String? = nil
    var stressors: [String]? = nil
    var goals: [String]? = nil
    var copingStrategies: [String]? = nil
    var deescalationWorks: [String]? = nil
    var deescalationBackfires: [String]? = nil
    var mentalHealthNotes: String? = nil
    var coParenting: String? = nil
    var guidanceStyle: String? = nil
    // Freshly presigned by GET /profile when a photo exists (expires in ~15m —
    // display-only, never persist).
    var avatarUrl: String? = nil

    enum CodingKeys: String, CodingKey {
        case name, pronouns, country, employment, stressors, goals
        case avatarUrl = "avatar_url"
        case postalCode = "postal_code"
        case primaryLanguage = "primary_language"
        case parentAgeRange = "parent_age_range"
        case adultsInHousehold = "adults_in_household"
        case householdStructure = "household_structure"
        case workHours = "work_hours"
        case energyPattern = "energy_pattern"
        case defaultStressResponse = "default_stress_response"
        case dreadedMoment = "dreaded_moment"
        case supportSystem = "support_system"
        case supportBoundaries = "support_boundaries"
        case culturalBackground = "cultural_background"
        case parentingStyle = "parenting_style"
        case copingStrategies = "coping_strategies"
        case deescalationWorks = "deescalation_works"
        case deescalationBackfires = "deescalation_backfires"
        case mentalHealthNotes = "mental_health_notes"
        case coParenting = "co_parenting"
        case guidanceStyle = "guidance_style"
    }
}

struct ChildProfileDTO: Codable {
    var name: String? = nil
    var pronouns: String? = nil
    var age: Double? = nil
    var gradeBand: String? = nil
    var temperament: String? = nil
    var interests: [String]? = nil
    var strengths: [String]? = nil
    var academicStrengths: [String]? = nil
    var challenges: [String]? = nil
    var emotionRegulation: String? = nil
    var socialProfile: String? = nil
    var learningProfile: String? = nil
    var neurodiversity: String? = nil
    var sensoryNotes: String? = nil
    var sleepRoutine: String? = nil
    var healthNotes: String? = nil
    var triggers: [String]? = nil
    var escalationPattern: String? = nil
    var calmingStrategies: [String]? = nil
    var recentChanges: [String]? = nil
    var schoolContext: String? = nil
    var teacherNotes: String? = nil
    var siblingConflicts: [String]? = nil
    var repairHelpers: [String]? = nil
    var motivators: [String]? = nil
    var safetyFlags: String? = nil
    var avatarUrl: String? = nil  // presigned, display-only (see ParentProfileDTO)

    enum CodingKeys: String, CodingKey {
        case name, pronouns, age, temperament, interests, strengths, challenges
        case triggers, motivators, neurodiversity
        case avatarUrl = "avatar_url"
        case gradeBand = "grade_band"
        case academicStrengths = "academic_strengths"
        case emotionRegulation = "emotion_regulation"
        case socialProfile = "social_profile"
        case learningProfile = "learning_profile"
        case sensoryNotes = "sensory_notes"
        case sleepRoutine = "sleep_routine"
        case healthNotes = "health_notes"
        case escalationPattern = "escalation_pattern"
        case calmingStrategies = "calming_strategies"
        case recentChanges = "recent_changes"
        case schoolContext = "school_context"
        case teacherNotes = "teacher_notes"
        case siblingConflicts = "sibling_conflicts"
        case repairHelpers = "repair_helpers"
        case safetyFlags = "safety_flags"
    }
}

struct FamilyProfileDTO: Codable {
    var parent: ParentProfileDTO?
    var children: [String: ChildProfileDTO]?
}

/// Reads/writes the family profile. Mirrors ContentService/PlanService: static
/// funcs, Bearer auth via AuthService. Reads via GET /profile; writes the rich
/// fields via PATCH /profile and PATCH /profile/kids/{name} (list fields are
/// replaced server-side, so edits/removals stick).
enum ProfileService {

    @MainActor
    private static func authHeader(userID: String, baseURL: URL) async -> [String: String] {
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        return AuthService.shared.header(for: userID)
    }

    static func getProfile(baseURL: URL, userID: String) async throws -> FamilyProfileDTO {
        let url = baseURL.appendingPathComponent("profile")
        var request = URLRequest(url: url)
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(FamilyProfileDTO.self, from: data)
    }

    // MARK: - Writes (PATCH)

    /// Partial-update the parent profile. `fields` are snake_case keys → values
    /// (String / Int / [String]); list fields are replaced server-side.
    @discardableResult
    static func updateParent(
        baseURL: URL, userID: String, fields: [String: Any]
    ) async throws -> FamilyProfileDTO {
        try await patch(path: "profile", baseURL: baseURL, userID: userID, fields: fields)
    }

    /// Partial-update (or CREATE if new — covers add-a-kid) a child profile.
    @discardableResult
    static func updateKid(
        baseURL: URL, userID: String, name: String, fields: [String: Any]
    ) async throws -> FamilyProfileDTO {
        let encoded = name.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? name
        return try await patch(
            path: "profile/kids/\(encoded)", baseURL: baseURL, userID: userID, fields: fields
        )
    }

    /// Remove a child profile (DELETE /profile/kids/{name}). Returns the updated
    /// family so the caller can refresh. Scoped to the authenticated user.
    @discardableResult
    static func deleteKid(
        baseURL: URL, userID: String, name: String
    ) async throws -> FamilyProfileDTO {
        let encoded = name.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? name
        let url = baseURL.appendingPathComponent("profile/kids/\(encoded)")
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(FamilyProfileDTO.self, from: data)
    }

    private static func patch(
        path: String, baseURL: URL, userID: String, fields: [String: Any]
    ) async throws -> FamilyProfileDTO {
        let url = baseURL.appendingPathComponent(path)
        var request = URLRequest(url: url)
        request.httpMethod = "PATCH"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        var body = fields
        body["user_id"] = userID
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
        return try JSONDecoder().decode(FamilyProfileDTO.self, from: data)
    }
}
