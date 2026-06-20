import Foundation

// DTOs for the family profile (GET /profile). We declare only the fields the
// Settings → Profile screen reads/edits; JSONDecoder ignores the rest.

struct ParentProfileDTO: Codable {
    var name: String?
    var postalCode: String?
    var country: String?

    enum CodingKeys: String, CodingKey {
        case name, country
        case postalCode = "postal_code"
    }
}

struct ChildProfileDTO: Codable {
    var name: String?
    var age: Double?
}

struct FamilyProfileDTO: Codable {
    var parent: ParentProfileDTO?
    var children: [String: ChildProfileDTO]?
}

/// Reads/writes the parent profile. Mirrors ContentService/PlanService: static
/// funcs, Bearer auth via AuthService. Save goes through the existing
/// /profile/seed endpoint (which updates only the fields it's given).
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

    /// Save the editable parent fields. Sends only non-empty values so blank
    /// fields never clobber existing data (matches /profile/seed semantics).
    static func saveParentProfile(
        baseURL: URL,
        userID: String,
        name: String,
        postalCode: String,
        country: String
    ) async throws {
        let url = baseURL.appendingPathComponent("profile/seed")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        // parent_name is required by the seed schema; send the current value.
        var body: [String: Any] = ["user_id": userID, "parent_name": name]
        if !postalCode.isEmpty { body["postal_code"] = postalCode }
        if !country.isEmpty { body["country"] = country }
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (_, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
    }
}
