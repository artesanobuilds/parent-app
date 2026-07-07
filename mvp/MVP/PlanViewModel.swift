import Foundation

/// State for the Plan tab: triggers a discovery run, polls its status, holds the
/// ranked candidates, and loads the plan summary (tracked activities, open
/// to-dos, cost, coverage gaps). Mirrors `ContentViewModel`: `@MainActor`,
/// `ObservableObject`, owned as `@StateObject` in MainTabView and passed via
/// `@EnvironmentObject`.
@MainActor
final class PlanViewModel: ObservableObject {

    // Identity / config (set from MainTabView, same as ContentViewModel).
    @Published var userId: String = ""
    @Published var baseURL: URL?

    /// Optional ZIP / postal code to search around. Discovery needs a location;
    /// if the parent's profile doesn't carry one, they enter it here and we send
    /// it as a `location` override on the run.
    @Published var locationQuery: String = ""

    /// How far from the ZIP to search (miles). Sent as `params.radius_miles`.
    @Published var radiusMiles: Int = 15
    /// Optional free-form text that tilts the search ("art camps only", "only for
    /// Ceiba"). Hidden behind `showFocus`; sent as `params.focus` when non-empty.
    @Published var focusText: String = ""
    @Published var showFocus: Bool = false
    /// Preset radius options for the segmented picker.
    let radiusOptions: [Int] = [5, 10, 25, 50]

    /// How many candidates the discovery run should aim for. Sent as
    /// `params.max_candidates`; default 25 matches the backend default so the
    /// behavior is unchanged unless the parent picks another count. The backend
    /// clamps it (1–100); these presets are the UX surface ("top 5" … "top 50").
    @Published var maxCandidates: Int = 25
    let candidateCountOptions: [Int] = [5, 15, 25, 50]

    // Discovery run.
    @Published private(set) var runStatus: ResearchRunStatus?
    @Published private(set) var candidates: [ActivityCandidate] = []
    @Published private(set) var isDiscovering = false

    // Plan summary.
    @Published private(set) var activities: [TrackedActivity] = []
    @Published private(set) var todos: [PlanTodo] = []
    @Published private(set) var summary: PlanSummary?
    @Published private(set) var calendarEntries: [CalendarEntry] = []
    @Published private(set) var isLoadingPlan = false

    // Lifecycle board: activities grouped by stage with next steps + to-dos.
    @Published private(set) var board: PlanBoard?
    /// Activity/to-do ids with a mutation in flight (disables just that card).
    @Published private(set) var mutatingIds: Set<String> = []

    /// Calendar entries bucketed by week-start (week_start, else the entry's
    /// start date), oldest week first — the compact week×kid view's data.
    var calendarWeeks: [(week: String, entries: [CalendarEntry])] {
        var buckets: [String: [CalendarEntry]] = [:]
        for e in calendarEntries {
            let key = e.weekStart ?? e.startTs.map { String($0.prefix(10)) } ?? ""
            guard !key.isEmpty else { continue }
            buckets[key, default: []].append(e)
        }
        return buckets.keys.sorted().map { (week: $0, entries: buckets[$0] ?? []) }
    }

    /// Kid names seen across calendar + tracked activities, for the column order.
    var calendarKids: [String] {
        var names = Set<String>()
        calendarEntries.forEach { if let k = $0.kidName { names.insert(k) } }
        activities.forEach { if let k = $0.kidName { names.insert(k) } }
        return names.sorted()
    }

    // R1 — "Exploring" shortlist. `savedCandidateIds` tracks which discovery
    // candidates are already pinned, so their Save button shows a saved state.
    @Published private(set) var savedCandidateIds: Set<String> = []
    @Published private(set) var savingCandidateIds: Set<String> = []

    /// The shortlist: tracked activities the parent is still considering.
    var exploringActivities: [TrackedActivity] { activities.filter { $0.isExploring } }

    @Published var errorMessage: String?

    // Ingestion (paste a message / pick a flyer photo).
    @Published private(set) var isIngesting = false
    @Published var ingestResult: IngestResponse?
    @Published var ingestError: String?

    private var pollTask: Task<Void, Never>?

    /// Phase string for the progress UI (e.g. "searching", "ranking").
    var discoveryPhase: String? { runStatus?.progress?.phase }

    /// Live-feed fields: the current-action headline, running count, and the
    /// recent activity log (Thinking / Searching for … / Found …).
    var discoveryDetail: String? { runStatus?.progress?.detail }
    var discoveryFound: Int { runStatus?.progress?.candidatesFound ?? 0 }
    var discoveryRecent: [String] { runStatus?.progress?.recent ?? [] }

    /// The run is accepted but a worker hasn't started it yet (it's waiting its
    /// turn behind other parents' searches). Distinct from an executing run that
    /// genuinely has 0 results so far — so we don't show a frozen "0 found".
    var isQueued: Bool {
        runStatus?.status == "queued" || runStatus?.progress?.phase == "queued"
    }

    /// Headline for the discovering card. While queued we say so explicitly;
    /// otherwise we surface what the model is doing right now.
    var discoveryHeadline: String {
        if isQueued { return "Lining up your search…" }
        return discoveryDetail ?? "Finding activities…"
    }

    /// "8 of 25 found" so the parent knows the target we're shooting for. While
    /// queued there's no count yet — show the wait, not "0 found". Once we reach the
    /// target the "of N" is meaningless (the agent can overshoot the soft aim, e.g.
    /// 27 good options) — just show the count so it never reads "27 of 25".
    var discoveryCountLabel: String {
        if isQueued { return "Starting shortly — you're in line" }
        if let target = runStatus?.progress?.candidatesTarget, target > 0, discoveryFound < target {
            return "\(discoveryFound) of \(target) found"
        }
        return "\(discoveryFound) found"
    }

    /// Header above the surfaced results. When we curated the shown set from a
    /// larger searched pool, say so ("Top 3 of 28 reviewed") so the parent knows
    /// a small count is hand-picked from a deep search, not a shallow one.
    var discoveryResultLabel: String {
        let shown = candidates.count
        if let considered = runStatus?.progress?.candidatesConsidered, considered > shown {
            return "Top \(shown) of \(considered) reviewed"
        }
        return "\(shown) found"
    }

    var hasRun: Bool { runStatus != nil }

    /// A run finished but produced no candidates — distinct from "not run yet".
    /// Drives the empty-state so a 0-result run doesn't look like a no-op.
    var completedEmpty: Bool {
        !isDiscovering && candidates.isEmpty && runStatus?.status == "done"
    }

    /// Camps found SO FAR, streamed live during the run — rendered as preview
    /// cards so the parent watches results fill in instead of staring at a spinner.
    var discoveryPreview: [CandidatePreview] { runStatus?.progress?.candidatesPreview ?? [] }

    /// When the current run started, for a live "elapsed" readout. nil when idle.
    @Published private(set) var discoveryStartedAt: Date?

    // MARK: - Result filters (client-side facets over the loaded candidates)

    @Published var selectedCities: Set<String> = []
    @Published var selectedCategories: Set<String> = []
    @Published var selectedKids: Set<String> = []
    @Published var sortKey: SortKey = .relevance

    var availableCities: [String] { Self.distinct(candidates.compactMap { $0.city }) }
    var availableCategories: [String] { Self.distinct(candidates.compactMap { $0.category }) }
    var availableKids: [String] { Self.distinct(candidates.flatMap { $0.displayKids }) }

    var hasActiveFilters: Bool {
        !(selectedCities.isEmpty && selectedCategories.isEmpty && selectedKids.isEmpty)
    }
    var activeFilterCount: Int {
        selectedCities.count + selectedCategories.count + selectedKids.count
    }

    /// The candidates to render: AND across facet groups, OR within a group.
    var filteredCandidates: [ActivityCandidate] {
        candidates.filter { c in
            (selectedCities.isEmpty || (c.city.map(selectedCities.contains) ?? false))
                && (selectedCategories.isEmpty || (c.category.map(selectedCategories.contains) ?? false))
                && (selectedKids.isEmpty || !selectedKids.isDisjoint(with: Set(c.displayKids)))
        }
    }

    func clearFilters() {
        selectedCities = []; selectedCategories = []; selectedKids = []
    }

    /// Reset BOTH sort and filters (the sheet's "Reset").
    func resetSortAndFilters() {
        clearFilters()
        sortKey = .relevance
    }

    /// The list the results view renders: filtered, then sorted by `sortKey`.
    /// Missing sort values always sort last so a null price/date/distance never
    /// jumps to the top.
    var sortedFilteredCandidates: [ActivityCandidate] {
        let items = filteredCandidates
        switch sortKey {
        case .relevance:
            return items.sorted { ($0.fitScore ?? -1) > ($1.fitScore ?? -1) }
        case .price:
            return items.sorted { Self.nilLast($0.priceAmount, $1.priceAmount) }
        case .soonest:
            return items.sorted { Self.nilLast($0.startDate, $1.startDate) }
        case .age:
            return items.sorted { Self.nilLast($0.ageMin, $1.ageMin) }
        case .nearest:
            return items.sorted { Self.nilLast($0.distanceMi, $1.distanceMi) }
        case .name:
            return items.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
        }
    }

    /// Ascending, with nils last.
    private static func nilLast<T: Comparable>(_ a: T?, _ b: T?) -> Bool {
        switch (a, b) {
        case let (x?, y?): return x < y
        case (_?, nil):    return true   // b is nil → a first
        default:           return false  // a is nil → a after b (or both nil)
        }
    }

    private static func distinct(_ xs: [String]) -> [String] {
        Array(Set(xs.map { $0.trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty })).sorted()
    }

    // Durable pointer to an in-flight run so returning to Plan re-attaches to a
    // running/finished discovery instead of showing the empty form.
    private static let activeRunKey = "discovery_active_run"
    private static func setActiveRun(_ id: String) { UserDefaults.standard.set(id, forKey: activeRunKey) }
    private static func activeRun() -> String? { UserDefaults.standard.string(forKey: activeRunKey) }
    private static func clearActiveRun() { UserDefaults.standard.removeObject(forKey: activeRunKey) }

    // MARK: - Discovery

    /// Trigger a new research run and poll until it reaches a terminal state,
    /// then load the candidates. Cancels any in-flight poll first.
    func startDiscovery() {
        guard let baseURL = baseURL else {
            errorMessage = "Please provide a valid server URL."
            return
        }
        let userId = userId.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !userId.isEmpty else {
            errorMessage = "Please complete onboarding before planning."
            return
        }

        errorMessage = nil
        candidates = []
        resetSortAndFilters()
        isDiscovering = true
        discoveryStartedAt = Date()
        pollTask?.cancel()

        let zip = locationQuery.trimmingCharacters(in: .whitespacesAndNewlines)
        let location: [String: Any]? = zip.isEmpty ? nil : ["postal_code": zip, "country": "US"]
        var params: [String: Any] = [
            "radius_miles": radiusMiles,
            "max_candidates": maxCandidates,
        ]
        let focus = focusText.trimmingCharacters(in: .whitespacesAndNewlines)
        if !focus.isEmpty { params["focus"] = focus }

        pollTask = Task { [weak self] in
            guard let self else { return }
            do {
                let handle = try await PlanService.createRun(
                    baseURL: baseURL, userID: userId, location: location, params: params
                )
                Self.setActiveRun(handle.runId)  // durable so we can re-attach later
                self.runStatus = ResearchRunStatus(
                    runId: handle.runId, status: handle.status,
                    progress: nil, candidateCount: 0, error: nil
                )
                await self.consumeRun(baseURL: baseURL, userId: userId, runId: handle.runId)
            } catch {
                if !Task.isCancelled {
                    self.errorMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
                }
            }
            self.isDiscovering = false
            self.discoveryStartedAt = nil
        }
    }

    /// Drive a run to a terminal state (SSE with poll fallback) and load its
    /// candidates. Shared by `startDiscovery` (fresh run) and `reattachIfNeeded`
    /// (an in-flight run we reconnected to). Clears the durable run pointer on a
    /// terminal state so we don't re-attach to a finished run.
    private func consumeRun(baseURL: URL, userId: String, runId: String) async {
        // Live updates over SSE — one held connection, no 2s polling. Fall back
        // to polling if the stream errors (proxy/network) or ends early
        // (server-side cap). The run keeps going on the backend regardless.
        var reachedTerminal = false
        do {
            for try await status in PlanService.streamRun(
                baseURL: baseURL, userID: userId, runId: runId
            ) {
                if Task.isCancelled { return }
                self.runStatus = status
                if status.isTerminal { reachedTerminal = true; break }
            }
        } catch {
            if Task.isCancelled { return }
            reachedTerminal = await self.pollUntilTerminal(
                baseURL: baseURL, userId: userId, runId: runId
            )
        }
        if !reachedTerminal, !Task.isCancelled {
            reachedTerminal = await self.pollUntilTerminal(
                baseURL: baseURL, userId: userId, runId: runId
            )
        }

        if Task.isCancelled { return }
        if let status = self.runStatus, status.status == "done" {
            Self.clearActiveRun()
            self.candidates = (try? await PlanService.candidates(
                baseURL: baseURL, userID: userId, runId: status.runId
            )) ?? []
        } else if let status = self.runStatus, status.status == "failed" {
            Self.clearActiveRun()
            self.errorMessage = status.error ?? "The discovery run failed."
        } else if !reachedTerminal {
            // Still running server-side — keep the pointer so a return re-attaches.
            self.errorMessage = "This is taking longer than usual. It's still "
                + "working in the background — tap Find activities again in a "
                + "moment to pick up where it left off."
        }
    }

    /// On returning to Plan, re-attach to an in-flight/finished run instead of
    /// showing the empty form. No-op if nothing is stored or a run is already
    /// visible. Called from `PlanView.task`.
    func reattachIfNeeded() async {
        guard !isDiscovering, runStatus == nil, candidates.isEmpty else { return }
        guard let baseURL = baseURL else { return }
        let uid = userId.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !uid.isEmpty, let runId = Self.activeRun() else { return }
        guard let status = try? await PlanService.runStatus(
            baseURL: baseURL, userID: uid, runId: runId
        ) else {
            Self.clearActiveRun(); return
        }
        self.runStatus = status
        switch status.status {
        case "done":
            candidates = (try? await PlanService.candidates(
                baseURL: baseURL, userID: uid, runId: runId
            )) ?? []
            Self.clearActiveRun()
        case "failed", "canceled":
            Self.clearActiveRun()
            self.runStatus = nil
        default:  // queued / running — resume driving it
            isDiscovering = true
            discoveryStartedAt = Date()
            pollTask?.cancel()
            pollTask = Task { [weak self] in
                guard let self else { return }
                await self.consumeRun(baseURL: baseURL, userId: uid, runId: runId)
                self.isDiscovering = false
                self.discoveryStartedAt = nil
            }
        }
    }

    /// Fallback poll loop (used when SSE fails or ends early). Returns whether the
    /// run reached a terminal state; capped at 5 min.
    private func pollUntilTerminal(baseURL: URL, userId: String, runId: String) async -> Bool {
        let deadline = Date().addingTimeInterval(300)
        while !Task.isCancelled {
            try? await Task.sleep(nanoseconds: 3_000_000_000)
            if Task.isCancelled || Date() >= deadline { return false }
            guard let status = try? await PlanService.runStatus(
                baseURL: baseURL, userID: userId, runId: runId
            ) else { continue }
            self.runStatus = status
            if status.isTerminal { return true }
        }
        return false
    }

    func cancelDiscovery() {
        pollTask?.cancel()
        isDiscovering = false
        discoveryStartedAt = nil
        Self.clearActiveRun()
    }

    /// Prefill the ZIP from the saved profile (only when the field is empty, so
    /// we never clobber something the parent typed). Best-effort.
    func prefillLocation() async {
        guard let baseURL = baseURL,
              !userId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              locationQuery.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        else { return }
        if let fam = try? await ProfileService.getProfile(baseURL: baseURL, userID: userId),
           let zip = fam.parent?.postalCode, !zip.isEmpty {
            locationQuery = zip
        }
    }

    // MARK: - Plan summary

    /// Load tracked activities, open to-dos, and the plan summary. Tolerates
    /// partial failures (same shape as ContentViewModel.loadAllContent).
    func loadPlan() async {
        guard let baseURL = baseURL else { return }
        let userId = userId.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !userId.isEmpty else { return }

        isLoadingPlan = true
        defer { isLoadingPlan = false }

        do {
            activities = try await PlanService.activities(baseURL: baseURL, userID: userId)
            // Remember which discovery candidates are already pinned.
            savedCandidateIds = Set(activities.compactMap { $0.candidateId })
        } catch {
            print("[PlanViewModel] activities failed: \(error)")
        }
        do {
            todos = try await PlanService.todos(baseURL: baseURL, userID: userId, status: "open")
        } catch {
            print("[PlanViewModel] todos failed: \(error)")
        }
        do {
            summary = try await PlanService.planSummary(baseURL: baseURL, userID: userId)
        } catch {
            print("[PlanViewModel] planSummary failed: \(error)")
        }
        do {
            calendarEntries = try await PlanService.calendar(baseURL: baseURL, userID: userId)
        } catch {
            print("[PlanViewModel] calendar failed: \(error)")
        }
        do {
            board = try await PlanService.board(baseURL: baseURL, userID: userId)
        } catch {
            print("[PlanViewModel] board failed: \(error)")
        }
    }

    // MARK: - Lifecycle board actions

    /// Advance an activity along the lifecycle (We'll do it → planned,
    /// Mark registered → signed_up, Pass → declined, Reconsider → exploring).
    /// Registering flips on email watching + baseline to-dos server-side.
    func advance(_ activity: BoardActivity, to status: String, rationale: String? = nil) async {
        guard let baseURL = baseURL, !mutatingIds.contains(activity.id) else { return }
        mutatingIds.insert(activity.id)
        defer { mutatingIds.remove(activity.id) }
        do {
            var fields: [String: Any] = ["status": status]
            if let rationale = rationale { fields["decision_rationale"] = rationale }
            try await PlanService.updateActivity(
                baseURL: baseURL, userID: userId, activityId: activity.id, fields: fields)
            await loadPlan()
        } catch {
            errorMessage = "Couldn't update \(activity.name). Check your connection and try again."
        }
    }

    /// Permanently delete an activity (from "Not doing") — cascades server-side
    /// to its to-dos/calendar/logistics.
    func deleteForever(_ activity: BoardActivity) async {
        guard let baseURL = baseURL, !mutatingIds.contains(activity.id) else { return }
        mutatingIds.insert(activity.id)
        defer { mutatingIds.remove(activity.id) }
        do {
            try await PlanService.deleteActivity(
                baseURL: baseURL, userID: userId, activityId: activity.id)
            await loadPlan()
        } catch {
            errorMessage = "Couldn't delete \(activity.name). Try again."
        }
    }

    /// Start over: wipe the whole plan (confirmation lives in the view).
    func resetPlan() async {
        guard let baseURL = baseURL, !isLoadingPlan else { return }
        do {
            try await PlanService.resetPlan(baseURL: baseURL, userID: userId)
            await loadPlan()
        } catch {
            errorMessage = "Couldn't reset the plan. Check your connection and try again."
        }
    }

    /// Complete a to-do from the board (or the Follow-ups list) and refresh.
    func completeTodo(_ todoId: String) async {
        guard let baseURL = baseURL, !mutatingIds.contains(todoId) else { return }
        mutatingIds.insert(todoId)
        defer { mutatingIds.remove(todoId) }
        do {
            try await PlanService.updateTodo(
                baseURL: baseURL, userID: userId, todoId: todoId, status: "done")
            await loadPlan()
        } catch {
            errorMessage = "Couldn't complete that to-do. Try again."
        }
    }

    // MARK: - Ingestion

    /// Extract from a pasted email / forwarded iMessage, then refresh the plan so
    /// the new pending activity + to-dos appear.
    func ingestText(_ text: String) async {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let baseURL = baseURL,
              !userId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
              !trimmed.isEmpty else { return }

        isIngesting = true
        ingestError = nil
        ingestResult = nil
        defer { isIngesting = false }

        do {
            ingestResult = try await PlanService.ingestText(
                baseURL: baseURL, userID: userId, text: trimmed
            )
            await loadPlan()
        } catch {
            ingestError = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
        }
    }

    /// Extract from a flyer / form / screenshot photo (already normalized to JPEG
    /// + size-capped by the view), then refresh the plan.
    func ingestImage(_ data: Data) async {
        guard let baseURL = baseURL,
              !userId.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        isIngesting = true
        ingestError = nil
        ingestResult = nil
        defer { isIngesting = false }

        do {
            ingestResult = try await PlanService.ingestImage(
                baseURL: baseURL, userID: userId, imageData: data
            )
            await loadPlan()
        } catch {
            ingestError = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
        }
    }

    /// Clear ingest state (called when the sheet is dismissed/reset).
    func resetIngest() {
        ingestResult = nil
        ingestError = nil
    }

    // MARK: - Exploring shortlist (R1)

    func isSaved(_ candidate: ActivityCandidate) -> Bool {
        savedCandidateIds.contains(candidate.id)
    }

    func isSaving(_ candidate: ActivityCandidate) -> Bool {
        savingCandidateIds.contains(candidate.id)
    }

    /// Pin a discovery candidate to the "exploring" shortlist, then refresh the
    /// plan so it appears in the Exploring section.
    func saveCandidate(_ candidate: ActivityCandidate) async {
        guard let baseURL = baseURL else { return }
        let uid = userId.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !uid.isEmpty, !savedCandidateIds.contains(candidate.id) else { return }

        savingCandidateIds.insert(candidate.id)
        defer { savingCandidateIds.remove(candidate.id) }
        do {
            _ = try await PlanService.trackActivity(
                baseURL: baseURL, userID: uid,
                name: candidate.name,
                candidateId: candidate.id,
                kidName: candidate.displayKids.first ?? candidate.kidName,
                provider: candidate.provider,
                status: "exploring",
                priceAmount: candidate.priceAmount,
                signupURL: candidate.signupURL
            )
            savedCandidateIds.insert(candidate.id)
            await loadPlan()
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
        }
    }

    /// Un-track an activity (un-pin from the Exploring shortlist). Used by the
    /// Exploring row's bookmark and by toggling a saved discovery candidate.
    func removeActivity(_ activityId: String) async {
        guard let baseURL = baseURL else { return }
        let uid = userId.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !uid.isEmpty else { return }
        do {
            try await PlanService.deleteActivity(baseURL: baseURL, userID: uid, activityId: activityId)
            await loadPlan()  // rebuilds activities + savedCandidateIds
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
        }
    }

    /// Save if not saved, un-save (remove the linked tracked activity) if it is.
    func toggleSave(_ candidate: ActivityCandidate) async {
        if savedCandidateIds.contains(candidate.id) {
            guard let act = activities.first(where: { $0.candidateId == candidate.id }) else { return }
            savingCandidateIds.insert(candidate.id)
            defer { savingCandidateIds.remove(candidate.id) }
            await removeActivity(act.id)
        } else {
            await saveCandidate(candidate)
        }
    }
}

/// Sort options for discovery results, shown in the Sort & Filter sheet.
enum SortKey: String, CaseIterable, Identifiable {
    case relevance, price, soonest, age, nearest, name
    var id: String { rawValue }
    var label: String {
        switch self {
        case .relevance: return "Best match"
        case .price:     return "Price: low to high"
        case .soonest:   return "Starting soonest"
        case .age:       return "Age"
        case .nearest:   return "Nearest"
        case .name:      return "Name A–Z"
        }
    }
    var icon: String {
        switch self {
        case .relevance: return "sparkles"
        case .price:     return "dollarsign.circle"
        case .soonest:   return "calendar"
        case .age:       return "figure.child"
        case .nearest:   return "location"
        case .name:      return "textformat.abc"
        }
    }
}
