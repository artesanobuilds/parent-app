import Foundation

// MARK: - Home dashboard data layer
//
// Everything Home needs that isn't already served by ContentViewModel /
// PlanService / KidAgentService lives here: the coach nudge, the per-kid daily
// summaries that fill the "with {companion}, {when}" + status lines, and the
// COMING UP composition.
//
// The coach nudge is deliberately isolated behind ONE method
// (`HomeDashboardService.coachNudge`) so rewiring it — if the warm-up's
// endpoint or payload moves — is a single-place change. Home never talks to
// that endpoint directly.

// MARK: - DTOs

/// The parent's current coach nudge — what Home's COACH card renders.
/// Wire shape: `GET /coach/nudge` → `{"nudge": {...} | null}` (the first one is
/// written by the first-run warm-up; null before that, and the card falls back
/// to its empty state).
///
/// Everything except `body` is optional: a single type mismatch empties the
/// whole payload on iOS, and the card is worth more than any one field.
struct CoachNudge: Decodable, Hashable {
    let id: String?
    let source: String?
    let kidName: String?
    let body: String
    let ctaLabel: String?
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id, source, body
        case kidName = "kid_name"
        case ctaLabel = "cta_label"
        case createdAt = "created_at"
    }

    /// "Try this with Ben" — the server's label when it sent one, else derived.
    var ctaTitle: String {
        if let ctaLabel, !ctaLabel.trimmingCharacters(in: .whitespaces).isEmpty { return ctaLabel }
        if let kidName, !kidName.isEmpty { return "Try this with \(kidName)" }
        return "Talk it through"
    }

    /// "This morning" / "Yesterday" — the header's trailing detail.
    var timeOfDayLabel: String {
        guard let created = HomeWhen.timestamp(createdAt) else { return HomeWhen.partOfDay(Date()) }
        let days = HomeWhen.wholeDaysBetween(created, and: Date())
        if days == 0 { return HomeWhen.partOfDay(created) }
        if days == 1 { return "Yesterday" }
        return HomeWhen.shortDate(created)
    }
}

/// One row of `GET /summary/list` — the nightly per-kid recap. Drives the kid
/// card's "…, yesterday" and its status line. `message_count` is deliberately
/// not decoded (Home doesn't show it).
struct KidDailySummary: Decodable, Hashable {
    let id: String?
    let kidName: String?
    let summaryDate: String?
    let headline: String?

    enum CodingKeys: String, CodingKey {
        case id, headline
        case kidName = "kid_name"
        case summaryDate = "summary_date"
    }

    var day: Date? { HomeWhen.day(summaryDate) }
}

/// A dated row in COMING UP. Composed from the lifecycle board + the family
/// calendar; the server owns the copy for `detail` wherever it renders one
/// (`BoardActivity.when`, `RegistrationWindowInfo.line`) so date-display logic
/// never forks per client.
struct ComingUpEntry: Identifiable, Hashable {
    let id: String
    let title: String
    let detail: String
    let date: Date?
}

// MARK: - Service

enum HomeDashboardServiceError: LocalizedError {
    case httpError(Int)
    case invalidResponse

    var errorDescription: String? {
        switch self {
        case .httpError(let code): return "The server returned status \(code)."
        case .invalidResponse:     return "The server response was not valid."
        }
    }
}

enum HomeDashboardService {

    @MainActor
    private static func authHeader(userID: String, baseURL: URL) async -> [String: String] {
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        return AuthService.shared.header(for: userID)
    }

    private static func get<T: Decodable>(
        _ path: String, query: [URLQueryItem] = [], baseURL: URL, userID: String
    ) async throws -> T {
        guard var components = URLComponents(
            url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false
        ) else { throw HomeDashboardServiceError.invalidResponse }
        if !query.isEmpty { components.queryItems = query }
        guard let url = components.url else { throw HomeDashboardServiceError.invalidResponse }

        var request = URLRequest(url: url)
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.timeoutInterval = 20
        for (k, v) in await authHeader(userID: userID, baseURL: baseURL) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw HomeDashboardServiceError.invalidResponse
        }
        guard (200..<300).contains(http.statusCode) else {
            throw HomeDashboardServiceError.httpError(http.statusCode)
        }
        return try JSONDecoder().decode(T.self, from: data)
    }

    // MARK: Coach nudge — THE one place Home reads it from
    //
    // If the warm-up's contract moves (different path, different envelope key),
    // change this method and nothing else. Callers only ever see `CoachNudge?`,
    // and `nil` is a first-class state the card renders.

    private struct NudgeEnvelope: Decodable { let nudge: CoachNudge? }

    static func coachNudge(baseURL: URL, userID: String) async throws -> CoachNudge? {
        let envelope: NudgeEnvelope = try await get("coach/nudge", baseURL: baseURL, userID: userID)
        return envelope.nudge
    }

    // MARK: Per-kid daily summaries

    private struct SummariesEnvelope: Decodable { let summaries: [KidDailySummary] }

    /// Newest-first recaps for the whole family in ONE request (the kid cards
    /// each need at most the latest row, so a per-kid fetch would be N calls
    /// on the app's most-visited screen).
    static func dailySummaries(
        baseURL: URL, userID: String, limit: Int = 30
    ) async throws -> [KidDailySummary] {
        let envelope: SummariesEnvelope = try await get(
            "summary/list",
            query: [
                URLQueryItem(name: "user_id", value: userID),
                URLQueryItem(name: "limit", value: String(limit)),
            ],
            baseURL: baseURL, userID: userID
        )
        return envelope.summaries
    }

    /// Latest summary per kid, keyed by kid name.
    static func latestSummaryByKid(_ rows: [KidDailySummary]) -> [String: KidDailySummary] {
        var out: [String: KidDailySummary] = [:]
        for row in rows {
            guard let name = row.kidName, !name.isEmpty else { continue }
            guard let existing = out[name] else { out[name] = row; continue }
            let lhs = row.day ?? .distantPast
            let rhs = existing.day ?? .distantPast
            if lhs > rhs { out[name] = row }
        }
        return out
    }
}

// MARK: - COMING UP composition

enum ComingUpBuilder {

    /// Merge the family calendar with the lifecycle board into one dated list.
    /// Calendar entries win on a name collision — they carry a real timestamp.
    /// Everything is best-effort: a missing source just contributes nothing.
    static func build(calendar: [CalendarEntry], board: PlanBoard?, now: Date = Date()) -> [ComingUpEntry] {
        var entries: [ComingUpEntry] = []
        var seenTitles = Set<String>()

        // Only forward-looking rows; a camp that ended last month isn't "coming up".
        let horizon = Calendar.current.date(byAdding: .day, value: -1, to: now) ?? now
        for row in calendar where row.status != "canceled" {
            let start = HomeWhen.timestamp(row.startTs)
            if let start, start < horizon { continue }
            let key = row.title.lowercased()
            if seenTitles.contains(key) { continue }
            seenTitles.insert(key)

            var parts: [String] = []
            if let start {
                parts.append(HomeWhen.futurePhrase(start, now: now).capitalizedFirst)
                parts.append(HomeWhen.dateAndTime(start))
            }
            if let kid = row.kidName, !kid.isEmpty { parts.append(kid) }
            if let place = row.locationText, !place.isEmpty { parts.append(place) }

            entries.append(ComingUpEntry(
                id: "cal:" + row.id,
                title: row.title,
                detail: parts.joined(separator: " · "),
                date: start
            ))
        }

        // Board activities that carry a server-rendered date line but no
        // calendar row yet (e.g. a registration window we're watching).
        for stage in board?.stages ?? [] {
            for activity in stage.activities {
                let key = activity.name.lowercased()
                if seenTitles.contains(key) { continue }
                var parts: [String] = []
                if let when = activity.when, !when.isEmpty { parts.append(when) }
                if let window = activity.registrationWindow { parts.append(window.line) }
                guard !parts.isEmpty else { continue }
                seenTitles.insert(key)
                if let kid = activity.kidName, !kid.isEmpty { parts.append(kid) }
                entries.append(ComingUpEntry(
                    id: "act:" + activity.id,
                    title: activity.name,
                    detail: parts.joined(separator: " · "),
                    date: HomeWhen.timestamp(activity.registrationWindow?.opensAt)
                ))
            }
        }

        // Dated rows first (soonest first), undated rows after.
        return entries.sorted { lhs, rhs in
            switch (lhs.date, rhs.date) {
            case let (l?, r?): return l < r
            case (_?, nil):    return true
            case (nil, _?):    return false
            case (nil, nil):   return lhs.title < rhs.title
            }
        }
    }
}

// MARK: - Date phrasing
//
// One place for every "yesterday" / "on Friday" / "Aug 8, 7:00 AM" the
// dashboard renders, and one tolerant timestamp parser. The backend emits
// Python `isoformat()` (microsecond precision, sometimes offset-less), which
// ISO8601DateFormatter alone will not parse.

enum HomeWhen {

    private static let isoFractional: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()

    private static let isoPlain: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f
    }()

    private static let naive: DateFormatter = {
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_US_POSIX")
        f.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        return f
    }()

    private static let dayOnly: DateFormatter = {
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_US_POSIX")
        f.dateFormat = "yyyy-MM-dd"
        return f
    }()

    /// Parse a backend timestamp. Tolerates fractional seconds of any width and
    /// a missing timezone (both occur in `datetime.isoformat()` output).
    static func timestamp(_ value: String?) -> Date? {
        guard var raw = value?.trimmingCharacters(in: .whitespacesAndNewlines), !raw.isEmpty else {
            return nil
        }
        if let date = isoFractional.date(from: raw) ?? isoPlain.date(from: raw) { return date }
        // Trim sub-second precision beyond what ISO8601DateFormatter accepts.
        if let dot = raw.firstIndex(of: ".") {
            let tail = raw[raw.index(after: dot)...]
            let offsetStart = tail.firstIndex(where: { $0 == "+" || $0 == "-" || $0 == "Z" })
            let suffix = offsetStart.map { String(tail[$0...]) } ?? ""
            raw = String(raw[..<dot]) + suffix
            if let date = isoPlain.date(from: raw) { return date }
        }
        if let date = naive.date(from: String(raw.prefix(19))) { return date }
        return day(raw)
    }

    /// Parse a `DATE` column ("2026-08-07").
    static func day(_ value: String?) -> Date? {
        guard let raw = value?.trimmingCharacters(in: .whitespacesAndNewlines), !raw.isEmpty else {
            return nil
        }
        return dayOnly.date(from: String(raw.prefix(10)))
    }

    static func wholeDaysBetween(_ earlier: Date, and later: Date) -> Int {
        let cal = Calendar.current
        let a = cal.startOfDay(for: earlier)
        let b = cal.startOfDay(for: later)
        return cal.dateComponents([.day], from: a, to: b).day ?? 0
    }

    /// Backward-looking: "today" / "yesterday" / "3 days ago" / "Jul 12".
    static func pastPhrase(_ date: Date, now: Date = Date()) -> String {
        let days = wholeDaysBetween(date, and: now)
        switch days {
        case ..<0:   return futurePhrase(date, now: now)
        case 0:      return "today"
        case 1:      return "yesterday"
        case 2...6:  return "\(days) days ago"
        default:     return shortDate(date)
        }
    }

    /// Forward-looking: "today" / "tomorrow" / "on Friday" / "on Aug 8".
    static func futurePhrase(_ date: Date, now: Date = Date()) -> String {
        let days = wholeDaysBetween(now, and: date)
        switch days {
        case ..<0:  return pastPhrase(date, now: now)
        case 0:     return "today"
        case 1:     return "tomorrow"
        case 2...6: return "on \(weekday.string(from: date))"
        default:    return "on \(shortDate(date))"
        }
    }

    /// "Morning" / "Afternoon" / "Evening" prefixed for the COACH header.
    static func partOfDay(_ date: Date) -> String {
        switch Calendar.current.component(.hour, from: date) {
        case 5..<12:  return "This morning"
        case 12..<17: return "This afternoon"
        default:      return "This evening"
        }
    }

    static func shortDate(_ date: Date) -> String { monthDay.string(from: date) }

    static func dateAndTime(_ date: Date) -> String {
        let time = Calendar.current.component(.hour, from: date) == 0
            && Calendar.current.component(.minute, from: date) == 0
            ? nil : clock.string(from: date)
        guard let time else { return monthDay.string(from: date) }
        return "\(monthDay.string(from: date)), \(time)"
    }

    private static let weekday: DateFormatter = {
        let f = DateFormatter(); f.dateFormat = "EEEE"; return f
    }()
    private static let monthDay: DateFormatter = {
        let f = DateFormatter(); f.setLocalizedDateFormatFromTemplate("MMMd"); return f
    }()
    private static let clock: DateFormatter = {
        let f = DateFormatter(); f.setLocalizedDateFormatFromTemplate("jmm"); return f
    }()
}

extension String {
    /// Sentence-cases only the first character; the rest is left alone so
    /// proper nouns inside server copy survive.
    var capitalizedFirst: String {
        guard let first = first else { return self }
        return String(first).uppercased() + dropFirst()
    }
}

// MARK: - View model

/// Owns the two Home sections that aren't backed by an existing view model:
/// the coach nudge and COMING UP. Every fetch is best-effort — a failure
/// degrades that section to its empty state and never blocks the dashboard.
@MainActor
final class HomeDashboardViewModel: ObservableObject {
    @Published private(set) var nudge: CoachNudge?
    /// False until the first fetch settles, so the card can show a quiet
    /// placeholder instead of flashing the "no nudge yet" copy.
    @Published private(set) var hasLoadedNudge = false
    @Published private(set) var comingUp: [ComingUpEntry] = []
    @Published private(set) var isLoading = false

    func refresh(baseURL: URL, userID: String) async {
        guard !userID.isEmpty, !isLoading else { return }
        isLoading = true
        defer { isLoading = false }

        async let nudgeTask = HomeDashboardService.coachNudge(baseURL: baseURL, userID: userID)
        async let boardTask = PlanService.board(baseURL: baseURL, userID: userID)
        async let calendarTask = PlanService.calendar(baseURL: baseURL, userID: userID)

        let fetchedNudge = try? await nudgeTask
        let board = try? await boardTask
        let calendar = (try? await calendarTask) ?? []

        // Keep the last-good nudge if the endpoint isn't there yet / failed:
        // an empty COACH card on a family that HAS a nudge is worse than stale.
        if let fetchedNudge { nudge = fetchedNudge }
        hasLoadedNudge = true
        comingUp = ComingUpBuilder.build(calendar: calendar, board: board)
    }
}
