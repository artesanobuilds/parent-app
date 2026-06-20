import Foundation

// MARK: - API Response Models
//
// DTOs for the activity-planning backend (`/research/*` + `/cos/*`). Shapes
// mirror the FastAPI routers (app/research/router.py, app/cos/router.py).
// snake_case wire fields map through explicit CodingKeys, same as
// ContentService's APICategory / APIArticle.

/// A queued research run (POST /research/runs response).
struct ResearchRunHandle: Codable, Hashable {
    let runId: String
    let status: String

    enum CodingKeys: String, CodingKey {
        case runId = "run_id"
        case status
    }
}

/// Poll payload (GET /research/runs/{id}). `progress` is a free-form dict on the
/// wire; we surface the common `phase` string for the UI and ignore the rest.
struct ResearchRunStatus: Codable, Hashable {
    let runId: String
    let status: String
    let progress: ResearchProgress?
    let candidateCount: Int
    let error: String?

    enum CodingKeys: String, CodingKey {
        case runId = "run_id"
        case status, progress
        case candidateCount = "candidate_count"
        case error
    }

    var isTerminal: Bool { status == "done" || status == "failed" || status == "canceled" }
}

struct ResearchProgress: Codable, Hashable {
    let phase: String?
    let detail: String?           // current action headline ("Searching for …", "Thinking…")
    let candidatesFound: Int?     // running count
    let candidatesTarget: Int?    // how many we're aiming for
    let recent: [String]?         // recent milestones, oldest→newest

    enum CodingKeys: String, CodingKey {
        case phase, detail, recent
        case candidatesFound = "candidates_found"
        case candidatesTarget = "candidates_target"
    }
}

/// A row in GET /research/runs.
struct ResearchRunSummary: Codable, Identifiable, Hashable {
    let id: String
    let status: String
    let candidateCount: Int?

    enum CodingKeys: String, CodingKey {
        case id, status
        case candidateCount = "candidate_count"
    }
}

/// A ranked discovery candidate (GET /research/runs/{id}/candidates).
struct ActivityCandidate: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let provider: String?
    let category: String?
    // Backend stores ages as DOUBLE (e.g. 5.5–11), so these MUST be Double, not Int.
    let ageMin: Double?
    let ageMax: Double?
    let startDate: String?
    let endDate: String?
    let scheduleText: String?
    let priceText: String?
    let priceAmount: Double?
    let locationText: String?
    let signupURL: String?
    let sourceURL: String?
    // `contact` is a JSON object {name,phone,email} on the wire — not decoded here
    // (the UI doesn't surface it yet); omitting it lets JSONDecoder ignore the key.
    let fitScore: Double?
    let kidName: String?
    // Family kids that fit this activity by age (computed by the API). A camp
    // that fits multiple kids lists them all.
    let fitKids: [String]?

    /// Kids to show for this candidate: the age-fit list, falling back to the
    /// agent's single best-guess, else none.
    var displayKids: [String] {
        if let fk = fitKids, !fk.isEmpty { return fk }
        if let kn = kidName { return [kn] }
        return []
    }

    enum CodingKeys: String, CodingKey {
        case id, name, provider, category
        case ageMin = "age_min"
        case ageMax = "age_max"
        case startDate = "start_date"
        case endDate = "end_date"
        case scheduleText = "schedule_text"
        case priceText = "price_text"
        case priceAmount = "price_amount"
        case locationText = "location_text"
        case signupURL = "signup_url"
        case sourceURL = "source_url"
        case fitScore = "fit_score"
        case kidName = "kid_name"
        case fitKids = "fit_kids"
    }
}

/// A tracked activity (GET /cos/activities).
struct TrackedActivity: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let kidName: String?
    let status: String
    let priceAmount: Double?
    let priceStatus: String?
    let provider: String?
    let signupURL: String?

    enum CodingKeys: String, CodingKey {
        case id, name, status, provider
        case kidName = "kid_name"
        case priceAmount = "price_amount"
        case priceStatus = "price_status"
        case signupURL = "signup_url"
    }
}

/// An open to-do (GET /cos/todos).
struct PlanTodo: Codable, Identifiable, Hashable {
    let id: String
    let title: String
    let status: String
    let dueDate: String?
    let kind: String?
    let kidName: String?

    enum CodingKeys: String, CodingKey {
        case id, title, status, kind
        case dueDate = "due_date"
        case kidName = "kid_name"
    }
}

// MARK: - Plan Summary (GET /cos/plan/summary)

struct PlanSummary: Codable, Hashable {
    let cost: PlanCost?
    let conflicts: [PlanConflict]?
    let coverageGaps: [CoverageGap]?
    let uncoveredWeeks: [String]?
    let pendingEligibility: [PendingEligibility]?

    enum CodingKeys: String, CodingKey {
        case cost, conflicts
        case coverageGaps = "coverage_gaps"
        case uncoveredWeeks = "uncovered_weeks"
        case pendingEligibility = "pending_eligibility"
    }
}

struct PlanCost: Codable, Hashable {
    let confirmedTotal: Double?
    let tbdCount: Int?

    enum CodingKeys: String, CodingKey {
        case confirmedTotal = "confirmed_total"
        case tbdCount = "tbd_count"
    }
}

struct PlanConflict: Codable, Hashable, Identifiable {
    // No stable id on the wire; synthesize one for ForEach.
    var id: String { (kidName ?? "") + (detail ?? reason ?? "") }
    let kidName: String?
    let detail: String?
    let reason: String?

    enum CodingKeys: String, CodingKey {
        case kidName = "kid_name"
        case detail, reason
    }
}

struct CoverageGap: Codable, Hashable, Identifiable {
    var id: String { (kidName ?? "") + (task ?? "") + (reason ?? "") }
    let kidName: String?
    let task: String?
    let reason: String?

    enum CodingKeys: String, CodingKey {
        case kidName = "kid_name"
        case task, reason
    }
}

struct PendingEligibility: Codable, Hashable, Identifiable {
    var id: String { name ?? UUID().uuidString }
    let name: String?
    let kidName: String?

    enum CodingKeys: String, CodingKey {
        case name
        case kidName = "kid_name"
    }
}

// MARK: - Plan Service

enum PlanServiceError: LocalizedError {
    case httpError(Int)
    case invalidResponse

    var errorDescription: String? {
        switch self {
        case .httpError(let code): return "The server returned status \(code)."
        case .invalidResponse:     return "The server response was not valid."
        }
    }
}

/// Networking for the activity-planning surface. Mirrors `ContentService`:
/// static funcs, Bearer auth via `authHeader(userID:baseURL:)`, a `sendDecoded`
/// helper, and an SSE stream for the chief-of-staff chat (modeled on
/// `ChatService.streamResponse`).
enum PlanService {

    // MARK: Request helpers

    private static func validate(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else {
            throw PlanServiceError.invalidResponse
        }
        guard (200..<300).contains(http.statusCode) else {
            throw PlanServiceError.httpError(http.statusCode)
        }
    }

    private static func sendDecoded<T: Decodable>(_ request: URLRequest) async throws -> T {
        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response)
        return try JSONDecoder().decode(T.self, from: data)
    }

    /// Ensure a Bearer token for userID and return the Authorization header.
    @MainActor
    private static func authHeader(userID: String, baseURL: URL) async -> [String: String] {
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        return AuthService.shared.header(for: userID)
    }

    private static func authedGET(_ url: URL, userID: String, baseURL: URL) async -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        return request
    }

    // MARK: Discovery (research)

    static func createRun(
        baseURL: URL,
        userID: String,
        location: [String: Any]? = nil,
        params: [String: Any]? = nil
    ) async throws -> ResearchRunHandle {
        let url = baseURL.appendingPathComponent("research/runs")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        var body: [String: Any] = ["user_id": userID]
        if let location = location { body["location"] = location }
        if let params = params { body["params"] = params }
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        return try await sendDecoded(request)
    }

    static func runStatus(baseURL: URL, userID: String, runId: String) async throws -> ResearchRunStatus {
        let url = baseURL.appendingPathComponent("research/runs/\(runId)")
        return try await sendDecoded(await authedGET(url, userID: userID, baseURL: baseURL))
    }

    static func candidates(baseURL: URL, userID: String, runId: String) async throws -> [ActivityCandidate] {
        let url = baseURL.appendingPathComponent("research/runs/\(runId)/candidates")
        let envelope: CandidatesEnvelope = try await sendDecoded(await authedGET(url, userID: userID, baseURL: baseURL))
        return envelope.candidates
    }

    static func runs(baseURL: URL, userID: String) async throws -> [ResearchRunSummary] {
        let url = baseURL.appendingPathComponent("research/runs")
        let envelope: RunsEnvelope = try await sendDecoded(await authedGET(url, userID: userID, baseURL: baseURL))
        return envelope.runs
    }

    // MARK: Chief-of-Staff plan reads

    static func activities(baseURL: URL, userID: String, status: String? = nil) async throws -> [TrackedActivity] {
        var components = URLComponents(url: baseURL.appendingPathComponent("cos/activities"), resolvingAgainstBaseURL: false)!
        if let status = status { components.queryItems = [URLQueryItem(name: "status", value: status)] }
        guard let url = components.url else { throw PlanServiceError.invalidResponse }
        let envelope: ActivitiesEnvelope = try await sendDecoded(await authedGET(url, userID: userID, baseURL: baseURL))
        return envelope.activities
    }

    static func todos(baseURL: URL, userID: String, status: String? = nil) async throws -> [PlanTodo] {
        var components = URLComponents(url: baseURL.appendingPathComponent("cos/todos"), resolvingAgainstBaseURL: false)!
        if let status = status { components.queryItems = [URLQueryItem(name: "status", value: status)] }
        guard let url = components.url else { throw PlanServiceError.invalidResponse }
        let envelope: TodosEnvelope = try await sendDecoded(await authedGET(url, userID: userID, baseURL: baseURL))
        return envelope.todos
    }

    static func planSummary(baseURL: URL, userID: String) async throws -> PlanSummary {
        let url = baseURL.appendingPathComponent("cos/plan/summary")
        return try await sendDecoded(await authedGET(url, userID: userID, baseURL: baseURL))
    }

    // MARK: Chief-of-Staff chat (SSE)
    //
    // Mirrors ChatService.streamResponse: POST /cos/chat, parse `data: {...}`
    // frames (`{"type":"token","content":...}`) until `data: [DONE]`.

    static func streamCosChat(
        baseURL: URL,
        userID: String,
        threadID: String,
        message: String,
        authHeader: [String: String]
    ) -> AsyncThrowingStream<String, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    let url = baseURL.appendingPathComponent("cos/chat")
                    var request = URLRequest(url: url)
                    request.httpMethod = "POST"
                    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                    request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
                    for (key, value) in authHeader { request.setValue(value, forHTTPHeaderField: key) }
                    request.httpBody = try JSONSerialization.data(withJSONObject: [
                        "user_id": userID,
                        "thread_id": threadID,
                        "message": message,
                    ])
                    request.timeoutInterval = 90
                    request.cachePolicy = .reloadIgnoringLocalCacheData

                    let (bytes, response) = try await URLSession.shared.bytes(for: request)
                    guard let http = response as? HTTPURLResponse else {
                        throw PlanServiceError.invalidResponse
                    }
                    guard (200..<300).contains(http.statusCode) else {
                        throw PlanServiceError.httpError(http.statusCode)
                    }

                    for try await line in bytes.lines {
                        let trimmedLine = line.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard trimmedLine.hasPrefix("data:") else { continue }

                        var payload = trimmedLine.dropFirst(5)
                        payload = payload.drop(while: { $0 == " " })

                        if payload == "[DONE]" { break }
                        guard !payload.isEmpty else { continue }

                        if let token = try decodeToken(from: payload) {
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

    /// Parse one SSE JSON frame. Tool start/end frames are surfaced as nil
    /// (no visible text); errors throw; otherwise plain text falls through.
    private static func decodeToken(from payload: Substring) throws -> String? {
        let trimmed = payload.trimmingCharacters(in: .whitespacesAndNewlines)
        let data = Data(trimmed.utf8)
        if let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            let type = object["type"] as? String
            let content = object["content"] as? String
            if type == "token" { return content }
            if type == "error" { throw PlanServiceError.invalidResponse }
            return nil  // tool_start / tool_end — no text to render
        }
        return String(trimmed)
    }

    // MARK: Envelopes

    private struct CandidatesEnvelope: Decodable { let candidates: [ActivityCandidate] }
    private struct RunsEnvelope: Decodable { let runs: [ResearchRunSummary] }
    private struct ActivitiesEnvelope: Decodable { let activities: [TrackedActivity] }
    private struct TodosEnvelope: Decodable { let todos: [PlanTodo] }
}
