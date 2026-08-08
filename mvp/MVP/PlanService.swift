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
    let candidatesConsidered: Int? // size of the pool we curated the surfaced set from
    let recent: [String]?         // recent milestones, oldest→newest
    // Live preview of what's been found so far, so results render as they arrive
    // (skeleton → cards) instead of a spinner for 1–2 min.
    let candidatesPreview: [CandidatePreview]?

    enum CodingKeys: String, CodingKey {
        case phase, detail, recent
        case candidatesFound = "candidates_found"
        case candidatesTarget = "candidates_target"
        case candidatesConsidered = "candidates_considered"
        case candidatesPreview = "candidates_preview"
    }
}

/// A lightweight, in-flight candidate shown while discovery is still running.
struct CandidatePreview: Codable, Hashable, Identifiable {
    let name: String?
    let city: String?
    let category: String?
    let fitScore: Double?
    let kidName: String?

    var id: String { (name ?? "?") + "|" + (city ?? "") }

    enum CodingKeys: String, CodingKey {
        case name, city, category
        case fitScore = "fit_score"
        case kidName = "kid_name"
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
    // Structured town/state for filtering (free-text locationText is unreliable).
    let city: String?
    let region: String?
    // Straight-line miles from the parent's ZIP (for the Nearest sort).
    let distanceMi: Double?
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
        case city, region
        case distanceMi = "distance_mi"
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
    // Links back to the discovery candidate it was pinned from (if any), so the
    // UI can mark already-saved candidates.
    let candidateId: String?

    enum CodingKeys: String, CodingKey {
        case id, name, status, provider
        case kidName = "kid_name"
        case priceAmount = "price_amount"
        case priceStatus = "price_status"
        case signupURL = "signup_url"
        case candidateId = "candidate_id"
    }

    var isExploring: Bool { status == "exploring" }
}

// MARK: - Lifecycle board (GET /cos/plan/board)

/// The ONE next action for an activity's card. `hint` states the consequence
/// (self-documenting UI) — render it, don't hide it.
/// action ∈ plan | register | mark_registered | complete_todo | resolve | restore | none
struct BoardNextStep: Codable, Hashable {
    let stage: String
    let action: String
    let label: String
    let hint: String
    let url: String?
    let todoId: String?

    enum CodingKeys: String, CodingKey {
        case stage, action, label, hint, url
        case todoId = "todo_id"
    }
}

/// An activity on the lifecycle board: the tracked activity joined with its
/// open to-dos + computed next step + email-watching flags.
struct BoardActivity: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let kidName: String?
    let status: String
    let provider: String?
    let priceAmount: Double?
    let signupURL: String?
    let pendingReason: String?
    let openTodos: [PlanTodo]
    let nextStep: BoardNextStep
    let watchable: Bool
    let watching: Bool
    /// Vertical chip: camp | extracurricular | outing | school_event | trip.
    /// Optional so pre-Phase-0 backends still decode; server always sends it.
    let activityType: String?
    /// Server-rendered date line ("Week of Jul 13" / "Tuesdays 4:00 PM") —
    /// rendered VERBATIM; date-display logic never forks per client.
    let when: String?
    /// A watching registration window joined onto the card (Phase 4).
    let registrationWindow: RegistrationWindowInfo?
    /// Sprint-2 fit score (0..1, render as whole percent). Nil = older row.
    let fitScore: Double?
    /// Sprint-2 one-sentence fit reason for "Why it matched" card.
    let fitReason: String?
    /// Sprint-2 overlaps — schedule conflicts with other activities.
    let overlaps: [ActivityOverlap]?

    enum CodingKeys: String, CodingKey {
        case id, name, status, provider, watchable, watching, when
        case kidName = "kid_name"
        case priceAmount = "price_amount"
        case signupURL = "signup_url"
        case pendingReason = "pending_reason"
        case openTodos = "open_todos"
        case nextStep = "next_step"
        case activityType = "activity_type"
        case registrationWindow = "registration_window"
        case fitScore = "fit_score"
        case fitReason = "fit_reason"
        case overlaps
    }
}

/// Sprint-2: one schedule overlap with another activity.
struct ActivityOverlap: Codable, Hashable, Identifiable {
    let activityId: String
    let name: String
    let range: String

    var id: String { activityId }

    enum CodingKeys: String, CodingKey {
        case activityId = "activity_id"
        case name, range
    }
}

/// "Registration opens Aug 12 · watching" — the server renders `line`; the
/// client shows it verbatim (same rule as `when`).
struct RegistrationWindowInfo: Codable, Hashable {
    let id: String?
    let opensAt: String?
    let line: String
    let confidence: String?
    let source: String?

    enum CodingKeys: String, CodingKey {
        case id, line, confidence, source
        case opensAt = "opens_at"
    }
}

/// One board section (Considering / To register / Registered / All set / …),
/// with the parent-facing blurb both surfaces render under the header.
struct BoardStage: Codable, Identifiable, Hashable {
    let key: String
    let title: String
    let blurb: String
    let activities: [BoardActivity]
    var id: String { key }
}

struct PlanBoard: Codable, Hashable {
    let stages: [BoardStage]
    let gmailConnected: Bool

    enum CodingKeys: String, CodingKey {
        case stages
        case gmailConnected = "gmail_connected"
    }
}

/// One entry door for the "Plan something" disclosure (GET /cos/verticals).
/// Copy is server-driven from the vertical registry; flags filter server-side.
struct VerticalDoor: Codable, Identifiable, Hashable {
    let key: String
    let label: String
    let chipLabel: String
    let title: String
    let subtitle: String
    let starterPrompt: String

    var id: String { key }

    enum CodingKeys: String, CodingKey {
        case key, label, title, subtitle
        case chipLabel = "chip_label"
        case starterPrompt = "starter_prompt"
    }
}

struct VerticalsResponse: Codable {
    let verticals: [VerticalDoor]
}

/// A calendar entry (GET /cos/calendar). Week-keyed so a compact week×kid view
/// is a query over these.
struct CalendarEntry: Codable, Identifiable, Hashable {
    let id: String
    let kidName: String?
    let title: String
    let weekStart: String?
    let startTs: String?
    let endTs: String?
    let kind: String
    let status: String
    let locationText: String?

    enum CodingKeys: String, CodingKey {
        case id, title, kind, status
        case kidName = "kid_name"
        case weekStart = "week_start"
        case startTs = "start_ts"
        case endTs = "end_ts"
        case locationText = "location_text"
    }
}

/// An open to-do (GET /cos/todos). Sprint-2 includes completed to-dos.
struct PlanTodo: Codable, Identifiable, Hashable {
    let id: String
    let title: String
    let status: String
    let dueDate: String?
    let kind: String?
    let kidName: String?
    /// Sprint-2: true = completed (strike through).
    let done: Bool?

    enum CodingKeys: String, CodingKey {
        case id, title, status, kind, done
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

// MARK: - Ingestion (POST /ingest/text, POST /ingest/image)

/// What the extractor pulled out of a pasted message or photo. Mirrors the
/// backend `ExtractedActivity` (app/ingest/extract.py); only the fields the UI
/// surfaces are decoded — JSONDecoder ignores the rest.
struct IngestExtraction: Codable, Hashable {
    let provider: String?
    let activityName: String?
    let kidFit: String?
    let location: String?
    let hours: String?
    let dates: [String]?
    let amountDue: Double?
    let actionItems: [String]?
    let confidence: Double?
    /// Phase 5 (school life): the vertical + school-event kind, and the
    /// verbatim quote the deadline came from (provenance — always shown).
    let activityType: String?
    let eventKind: String?
    let sourceSnippet: String?

    enum CodingKeys: String, CodingKey {
        case provider, location, hours, dates, confidence
        case activityName = "activity_name"
        case kidFit = "kid_fit"
        case amountDue = "amount_due"
        case actionItems = "action_items"
        case activityType = "activity_type"
        case eventKind = "event_kind"
        case sourceSnippet = "source_snippet"
    }

    /// Best display label: the activity name, else the provider.
    var displayName: String { activityName ?? provider ?? "Activity" }
}

/// What Stage-2 materialization spawned (counts the UI shows back to the parent).
struct IngestCreated: Codable, Hashable {
    let activityId: String?
    let todoIds: [String]?
    let calendarIds: [String]?

    enum CodingKeys: String, CodingKey {
        case activityId = "activity_id"
        case todoIds = "todo_ids"
        case calendarIds = "calendar_ids"
    }

    var madeActivity: Bool { activityId != nil }
    var todoCount: Int { todoIds?.count ?? 0 }
    var calendarCount: Int { calendarIds?.count ?? 0 }
}

/// POST /ingest/{text,image} response.
/// One extracted item + what it spawned (Phase 5: a newsletter yields many).
struct IngestItem: Codable, Hashable {
    let extracted: IngestExtraction
    let created: IngestCreated
}

struct IngestResponse: Codable, Hashable {
    let artifactId: String
    let extractStatus: String
    // Legacy single-item keys (first item) — kept for old builds' decoding.
    let extracted: IngestExtraction
    let created: IngestCreated
    /// Phase 5: EVERY item found (a PTA newsletter = several). Optional so
    /// this build also decodes pre-Phase-5 backend responses.
    let items: [IngestItem]?
    /// Items past the per-artifact cap, parked in the artifact for review.
    let parked: Int?

    enum CodingKeys: String, CodingKey {
        case extracted, created, items, parked
        case artifactId = "artifact_id"
        case extractStatus = "extract_status"
    }

    var allItems: [IngestItem] {
        if let items, !items.isEmpty { return items }
        return [IngestItem(extracted: extracted, created: created)]
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
struct PlanShareLink: Codable, Hashable {
    let token: String
    let scope: String
    let url: String
}

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

    // MARK: Export / share (Phase 3b)

    /// Download the family plan as an .xlsx to a temp file; returns the local URL
    /// (hand to a share sheet). Reuses the same bearer auth as everything else.
    static func exportXlsx(baseURL: URL, userID: String) async throws -> URL {
        let url = baseURL.appendingPathComponent("cos/plan/export.xlsx")
        let request = await authedGET(url, userID: userID, baseURL: baseURL)
        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response)
        let dest = FileManager.default.temporaryDirectory.appendingPathComponent("family-plan.xlsx")
        try data.write(to: dest, options: .atomic)
        return dest
    }

    /// Mint a scoped, read-only public share link (scope: full | logistics | therapy).
    static func createShareLink(baseURL: URL, userID: String, scope: String) async throws -> PlanShareLink {
        let url = baseURL.appendingPathComponent("cos/plan/share")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        request.httpBody = try JSONSerialization.data(withJSONObject: ["user_id": userID, "scope": scope])
        return try await sendDecoded(request)
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

    static func calendar(baseURL: URL, userID: String) async throws -> [CalendarEntry] {
        let url = baseURL.appendingPathComponent("cos/calendar")
        let envelope: CalendarEnvelope = try await sendDecoded(await authedGET(url, userID: userID, baseURL: baseURL))
        return envelope.entries
    }

    /// Pin/save an activity to the plan. Defaults to the "exploring" shortlist
    /// (R1) — considering, not decided. Pass `candidateId` when saving a
    /// discovery candidate so it links back. Returns the new tracked-activity id.
    @discardableResult
    static func trackActivity(
        baseURL: URL,
        userID: String,
        name: String,
        candidateId: String? = nil,
        kidName: String? = nil,
        provider: String? = nil,
        status: String = "exploring",
        priceAmount: Double? = nil,
        signupURL: String? = nil
    ) async throws -> String {
        let url = baseURL.appendingPathComponent("cos/activities/track")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        var body: [String: Any] = ["user_id": userID, "name": name, "status": status]
        if let candidateId = candidateId { body["candidate_id"] = candidateId }
        if let kidName = kidName { body["kid_name"] = kidName }
        if let provider = provider { body["provider"] = provider }
        if let priceAmount = priceAmount { body["price_amount"] = priceAmount }
        if let signupURL = signupURL { body["signup_url"] = signupURL }
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let resp: TrackActivityResponse = try await sendDecoded(request)
        return resp.id
    }

    /// The lifecycle board: activities grouped by stage, each with open to-dos
    /// + a computed next step. One payload drives both clients.
    static func board(baseURL: URL, userID: String) async throws -> PlanBoard {
        let url = baseURL.appendingPathComponent("cos/plan/board")
        return try await sendDecoded(await authedGET(url, userID: userID, baseURL: baseURL))
    }

    /// Flag-filtered vertical doors for the "Plan something" disclosure
    /// (GET /cos/verticals — the ONE place flags touch verticals). Callers
    /// cache last-good and never block board render on this.
    static func verticals(baseURL: URL, userID: String) async throws -> [VerticalDoor] {
        let url = baseURL.appendingPathComponent("cos/verticals")
        let resp: VerticalsResponse = try await sendDecoded(
            await authedGET(url, userID: userID, baseURL: baseURL))
        return resp.verticals
    }

    /// Advance/edit a tracked activity (PATCH /cos/activities/{id}) — e.g.
    /// status "planned" (we'll do it) or "signed_up" (registered → the backend
    /// starts watching that camp's emails + seeds payment/form to-dos).
    static func updateActivity(
        baseURL: URL, userID: String, activityId: String, fields: [String: Any]
    ) async throws {
        let url = baseURL.appendingPathComponent("cos/activities/\(activityId)")
        var request = URLRequest(url: url)
        request.httpMethod = "PATCH"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        var body: [String: Any] = ["user_id": userID]
        body.merge(fields) { _, new in new }
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (_, response) = try await URLSession.shared.data(for: request)
        try validate(response)
    }

    /// Start over: wipe the plan (activities, to-dos, calendar, coverage,
    /// discovery results, uploaded info). Keeps profile/kids/chats/integrations.
    static func resetPlan(baseURL: URL, userID: String) async throws {
        let url = baseURL.appendingPathComponent("cos/plan/reset")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        request.httpBody = try JSONSerialization.data(withJSONObject: ["user_id": userID])
        let (_, response) = try await URLSession.shared.data(for: request)
        try validate(response)
    }

    /// Complete (or reopen) a to-do — PATCH /cos/todos/{id}.
    static func updateTodo(
        baseURL: URL, userID: String, todoId: String, status: String
    ) async throws {
        let url = baseURL.appendingPathComponent("cos/todos/\(todoId)")
        var request = URLRequest(url: url)
        request.httpMethod = "PATCH"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        request.httpBody = try JSONSerialization.data(
            withJSONObject: ["user_id": userID, "status": status])
        let (_, response) = try await URLSession.shared.data(for: request)
        try validate(response)
    }

    /// Un-track an activity (un-pin from the Exploring shortlist). Ownership is
    /// enforced server-side via the row, so no body is needed.
    static func deleteActivity(baseURL: URL, userID: String, activityId: String) async throws {
        let url = baseURL.appendingPathComponent("cos/activities/\(activityId)")
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        let (_, response) = try await URLSession.shared.data(for: request)
        try validate(response)
    }

    // MARK: Ingestion

    /// Extract structured activity info from a pasted email / forwarded iMessage.
    static func ingestText(
        baseURL: URL,
        userID: String,
        text: String,
        source: String = "paste"
    ) async throws -> IngestResponse {
        let url = baseURL.appendingPathComponent("ingest/text")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 90
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        request.httpBody = try JSONSerialization.data(withJSONObject: [
            "user_id": userID, "text": text, "source": source,
        ])
        return try await sendDecoded(request)
    }

    /// Extract from a photo (flyer / form / screenshot) via multipart upload.
    /// `imageData` should be a JPEG/PNG already normalized + size-capped by the
    /// caller (the backend rejects >8 MB and non-image MIME types).
    static func ingestImage(
        baseURL: URL,
        userID: String,
        imageData: Data,
        mimeType: String = "image/jpeg",
        filename: String = "upload.jpg",
        caption: String? = nil,
        source: String = "photo"
    ) async throws -> IngestResponse {
        let url = baseURL.appendingPathComponent("ingest/image")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 120
        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }

        var body = Data()
        func textField(_ name: String, _ value: String) {
            body.appendString("--\(boundary)\r\n")
            body.appendString("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n")
            body.appendString("\(value)\r\n")
        }
        textField("user_id", userID)
        textField("source", source)
        if let caption = caption, !caption.isEmpty { textField("caption", caption) }
        body.appendString("--\(boundary)\r\n")
        body.appendString("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n")
        body.appendString("Content-Type: \(mimeType)\r\n\r\n")
        body.append(imageData)
        body.appendString("\r\n")
        body.appendString("--\(boundary)--\r\n")
        request.httpBody = body

        return try await sendDecoded(request)
    }

    // MARK: Chief-of-Staff chat (SSE)
    //
    // Mirrors ChatService.streamResponse: POST /cos/chat, parse `data: {...}`
    // frames (`{"type":"token","content":...}`) until `data: [DONE]`.

    /// One SSE frame from `GET /research/runs/{id}/stream` — same fields as a poll
    /// of `runStatus`, minus run_id (the client already knows it).
    private struct ResearchStreamFrame: Decodable {
        let type: String?
        let status: String?
        let progress: ResearchProgress?
        let candidateCount: Int?
        let error: String?
        enum CodingKeys: String, CodingKey {
            case type, status, progress, error
            case candidateCount = "candidate_count"
        }
    }

    /// Live discovery progress over SSE — the client holds ONE connection instead of
    /// polling `runStatus` every 2s. Yields a `ResearchRunStatus` per progress frame;
    /// finishes on the terminal frame / `[DONE]`. If it throws (e.g. a proxy that
    /// mishandles SSE), the caller falls back to polling.
    static func streamRun(
        baseURL: URL,
        userID: String,
        runId: String
    ) -> AsyncThrowingStream<ResearchRunStatus, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    let url = baseURL.appendingPathComponent("research/runs/\(runId)/stream")
                    var request = URLRequest(url: url)
                    request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
                    for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
                        request.setValue(v, forHTTPHeaderField: k)
                    }
                    request.timeoutInterval = 600
                    request.cachePolicy = .reloadIgnoringLocalCacheData

                    let (bytes, response) = try await URLSession.shared.bytes(for: request)
                    guard let http = response as? HTTPURLResponse else {
                        throw PlanServiceError.invalidResponse
                    }
                    guard (200..<300).contains(http.statusCode) else {
                        throw PlanServiceError.httpError(http.statusCode)
                    }

                    for try await line in bytes.lines {
                        let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard trimmed.hasPrefix("data:") else { continue }
                        var payload = trimmed.dropFirst(5)
                        payload = payload.drop(while: { $0 == " " })
                        if payload == "[DONE]" { break }
                        guard !payload.isEmpty, let data = String(payload).data(using: .utf8) else { continue }
                        if let frame = try? JSONDecoder().decode(ResearchStreamFrame.self, from: data),
                           let status = frame.status {
                            continuation.yield(ResearchRunStatus(
                                runId: runId,
                                status: status,
                                progress: frame.progress,
                                candidateCount: frame.candidateCount ?? 0,
                                error: frame.error
                            ))
                        }
                    }
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }

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
    private struct CalendarEnvelope: Decodable { let entries: [CalendarEntry] }
    private struct TrackActivityResponse: Decodable { let id: String }
}

private extension Data {
    /// Append a UTF-8 string — used to build multipart/form-data bodies.
    mutating func appendString(_ string: String) {
        if let data = string.data(using: .utf8) { append(data) }
    }
}
