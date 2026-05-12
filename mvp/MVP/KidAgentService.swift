import Foundation

/// HTTP layer for the Family Companion (kid agent) endpoints.
///
/// All methods automatically attach the parent's Bearer token via AuthService.
/// 401 responses bubble up as `KidAgentServiceError.unauthorized`; the calling
/// view should re-issue the token and retry.
@MainActor
struct KidAgentService {
    let baseURL: URL
    let userID: String

    private var session: URLSession { .shared }

    /// Build a request and ensure a Bearer token is attached. Awaits issuance
    /// the first time so we never fire requests without auth (fixes the .task
    /// bootstrap race where the view's first refresh ran before SwayApp had
    /// finished issuing a token).
    private func authedRequest(_ path: String, method: String = "GET",
                               body: Data? = nil, query: [URLQueryItem] = []) async throws -> URLRequest {
        // Ensure we have a token. ensureToken is coalesced; concurrent callers
        // share a single in-flight issuance.
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)

        var components = URLComponents(
            url: baseURL.appendingPathComponent(path),
            resolvingAgainstBaseURL: false
        )!
        if !query.isEmpty { components.queryItems = query }
        var request = URLRequest(url: components.url!)
        request.httpMethod = method
        request.timeoutInterval = 30
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        for (k, v) in AuthService.shared.header(for: userID) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        if let body { request.httpBody = body }
        return request
    }

    private func send<T: Decodable>(_ request: URLRequest, as: T.Type,
                                     retriedAfter401: Bool = false) async throws -> T {
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw KidAgentServiceError.invalidResponse
        }
        switch http.statusCode {
        case 200..<300: break
        case 401:
            // Token may have expired / been revoked since cache was warmed.
            // Re-issue once and retry the same request before bailing out.
            if !retriedAfter401 {
                AuthService.shared.clear(for: userID)
                _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
                var retry = request
                for (k, v) in AuthService.shared.header(for: userID) {
                    retry.setValue(v, forHTTPHeaderField: k)
                }
                return try await send(retry, as: T.self, retriedAfter401: true)
            }
            throw KidAgentServiceError.unauthorized
        case 403:
            // Differentiate consent vs. generic forbidden.
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                if let detail = json["detail"] as? [String: Any],
                   detail["error"] as? String == "consent_required",
                   let version = detail["required_version"] as? String {
                    throw KidAgentServiceError.consentRequired(version: version)
                }
            }
            throw KidAgentServiceError.status(http.statusCode)
        case 409:       throw KidAgentServiceError.versionConflict
        default:        throw KidAgentServiceError.status(http.statusCode)
        }
        do {
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            throw KidAgentServiceError.invalidResponse
        }
    }

    // MARK: - Consent

    func consentStatus() async throws -> ConsentStatus {
        let request = try await authedRequest("consent/status")
        return try await send(request, as: ConsentStatus.self)
    }

    func submitConsent(parentName: String, parentEmail: String,
                       kidAgeBand: String, agreementVersion: String) async throws {
        let body = try JSONSerialization.data(withJSONObject: [
            "parent_name": parentName,
            "parent_email": parentEmail,
            "kid_age_band": kidAgeBand,
            "agreement_version": agreementVersion,
        ])
        let request = try await authedRequest("consent/submit", method: "POST", body: body)
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw KidAgentServiceError.invalidResponse
        }
        guard (200..<300).contains(http.statusCode) else {
            throw KidAgentServiceError.status(http.statusCode)
        }
        _ = data
    }

    // MARK: - Family profile

    /// One row per child currently in the parent's family profile.
    /// Returned independently of `/kid-agent/list` because the Companions
    /// section needs to render a "Set up" card for kids that don't yet
    /// have a config. Reads `/memory/<user_id>` and projects out the
    /// `profile.children` map.
    struct FamilyChild: Equatable {
        let name: String
        let age: Double?
        let pronouns: String?
        let gradeBand: String?
    }

    func familyChildren() async throws -> [FamilyChild] {
        struct Memory: Codable {
            struct Profile: Codable {
                var children: [String: Child]?
            }
            struct Child: Codable {
                var age: Double?
                var pronouns: String?
                var grade_band: String?
            }
            var profile: Profile?
        }
        let request = try await authedRequest("memory/\(userID)")
        let resp = try await send(request, as: Memory.self)
        let kids = resp.profile?.children ?? [:]
        return kids
            .map { FamilyChild(name: $0.key, age: $0.value.age,
                               pronouns: $0.value.pronouns, gradeBand: $0.value.grade_band) }
            .sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
    }

    // MARK: - Kid agent config

    /// List all kid agents for this parent.
    func list() async throws -> [KidAgentConfig] {
        struct Wrap: Codable { let agents: [KidAgentConfig] }
        let request = try await authedRequest(
            "kid-agent/list",
            query: [URLQueryItem(name: "user_id", value: userID)]
        )
        let wrap = try await send(request, as: Wrap.self)
        return wrap.agents
    }

    /// Fetch the latest config for a kid (auto-bootstraps on first read).
    func config(forKid kidName: String) async throws -> KidAgentConfig {
        let request = try await authedRequest("kid-agent/config", query: [
            URLQueryItem(name: "user_id",  value: userID),
            URLQueryItem(name: "kid_name", value: kidName),
        ])
        return try await send(request, as: KidAgentConfig.self)
    }

    /// Synthesize-without-save. Used by the letter editor for live preview.
    func preview(forKid kidName: String, brief: String) async throws -> KidAgentPreview {
        let body = try JSONSerialization.data(withJSONObject: [
            "user_id": userID,
            "kid_name": kidName,
            "brief": brief,
        ])
        let request = try await authedRequest("kid-agent/preview", method: "POST", body: body)
        return try await send(request, as: KidAgentPreview.self)
    }

    /// Persist a new config version. Pass `expectedVersion` for optimistic
    /// concurrency; pass nil on first write.
    func save(forKid kidName: String, brief: String,
              expectedVersion: Int?, enable: Bool) async throws -> KidAgentConfig {
        var payload: [String: Any] = [
            "user_id": userID,
            "kid_name": kidName,
            "brief": brief,
            "enable": enable,
        ]
        if let expectedVersion { payload["expected_version"] = expectedVersion }
        let body = try JSONSerialization.data(withJSONObject: payload)
        let request = try await authedRequest("kid-agent/config", method: "POST", body: body)
        return try await send(request, as: KidAgentConfig.self)
    }

    // MARK: - Kid chat (parent-side, e.g. preview / test sandbox)

    /// Streams kid-chat tokens. Used by KidAgentView; can also be used by the
    /// letter editor's "test as kid" sandbox.
    func streamKidChat(kidName: String, message: String, threadID: String,
                       kidPin: String? = nil) -> AsyncThrowingStream<String, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    var payload: [String: Any] = [
                        "user_id": userID,
                        "kid_name": kidName,
                        "message": message,
                        "thread_id": threadID,
                    ]
                    if let kidPin { payload["kid_pin"] = kidPin }
                    let body = try JSONSerialization.data(withJSONObject: payload)
                    var request = try await authedRequest("kid-chat", method: "POST", body: body)
                    request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
                    request.timeoutInterval = 90

                    let (bytes, response) = try await session.bytes(for: request)
                    guard let http = response as? HTTPURLResponse else {
                        continuation.finish(throwing: KidAgentServiceError.invalidResponse); return
                    }
                    guard (200..<300).contains(http.statusCode) else {
                        if http.statusCode == 401 {
                            continuation.finish(throwing: KidAgentServiceError.unauthorized)
                        } else {
                            continuation.finish(throwing: KidAgentServiceError.status(http.statusCode))
                        }
                        return
                    }
                    for try await line in bytes.lines {
                        let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard trimmed.hasPrefix("data:") else { continue }
                        var payload = trimmed.dropFirst(5)
                        payload = payload.drop(while: { $0 == " " })
                        if payload == "[DONE]" { break }
                        guard !payload.isEmpty else { continue }
                        if let token = decodeToken(from: payload) {
                            continuation.yield(token)
                        }
                    }
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }

    func transcripts(kidName: String, threadID: String = "default") async throws -> [KidMessage] {
        struct Wrap: Codable { let messages: [KidMessage] }
        let request = try await authedRequest("kid-chat/transcripts", query: [
            URLQueryItem(name: "user_id",   value: userID),
            URLQueryItem(name: "kid_name",  value: kidName),
            URLQueryItem(name: "thread_id", value: threadID),
        ])
        return try await send(request, as: Wrap.self).messages
    }

    func setKidPin(kidName: String, pin: String) async throws {
        let body = try JSONSerialization.data(withJSONObject: [
            "user_id": userID,
            "kid_name": kidName,
            "pin": pin,
        ])
        let request = try await authedRequest("kid-auth/set-pin", method: "POST", body: body)
        let (_, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw KidAgentServiceError.invalidResponse
        }
    }

    // MARK: - Helpers

    private func decodeToken(from payload: Substring) -> String? {
        let trimmed = payload.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let data = trimmed.data(using: .utf8),
              let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        else { return nil }
        if object["type"] as? String == "token", let content = object["content"] as? String {
            return content
        }
        return nil
    }
}

/// Single transcript message (parent's read-side model).
struct KidMessage: Codable, Identifiable, Equatable {
    let id: String
    let role: String
    let content: String
    let createdAt: String?
    let parentFlagged: Bool?

    enum CodingKeys: String, CodingKey {
        case id, role, content
        case createdAt     = "created_at"
        case parentFlagged = "parent_flagged"
    }
}
