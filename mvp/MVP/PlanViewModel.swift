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

    // Discovery run.
    @Published private(set) var runStatus: ResearchRunStatus?
    @Published private(set) var candidates: [ActivityCandidate] = []
    @Published private(set) var isDiscovering = false

    // Plan summary.
    @Published private(set) var activities: [TrackedActivity] = []
    @Published private(set) var todos: [PlanTodo] = []
    @Published private(set) var summary: PlanSummary?
    @Published private(set) var isLoadingPlan = false

    @Published var errorMessage: String?

    private var pollTask: Task<Void, Never>?

    /// Phase string for the progress UI (e.g. "searching", "ranking").
    var discoveryPhase: String? { runStatus?.progress?.phase }

    /// Live-feed fields: the current-action headline, running count, and the
    /// recent activity log (Thinking / Searching for … / Found …).
    var discoveryDetail: String? { runStatus?.progress?.detail }
    var discoveryFound: Int { runStatus?.progress?.candidatesFound ?? 0 }
    var discoveryRecent: [String] { runStatus?.progress?.recent ?? [] }

    /// "8 of 25 found" so the parent knows the target we're shooting for.
    var discoveryCountLabel: String {
        if let target = runStatus?.progress?.candidatesTarget, target > 0 {
            return "\(discoveryFound) of \(target) found"
        }
        return "\(discoveryFound) found"
    }

    var hasRun: Bool { runStatus != nil }

    /// A run finished but produced no candidates — distinct from "not run yet".
    /// Drives the empty-state so a 0-result run doesn't look like a no-op.
    var completedEmpty: Bool {
        !isDiscovering && candidates.isEmpty && runStatus?.status == "done"
    }

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
        isDiscovering = true
        pollTask?.cancel()

        let zip = locationQuery.trimmingCharacters(in: .whitespacesAndNewlines)
        let location: [String: Any]? = zip.isEmpty ? nil : ["postal_code": zip, "country": "US"]

        pollTask = Task { [weak self] in
            guard let self else { return }
            do {
                let handle = try await PlanService.createRun(baseURL: baseURL, userID: userId, location: location)
                self.runStatus = ResearchRunStatus(
                    runId: handle.runId, status: handle.status,
                    progress: nil, candidateCount: 0, error: nil
                )

                // Poll until terminal. Backoff is a fixed 2s; the run is a
                // background worker, so a few-second cadence is plenty.
                while !Task.isCancelled {
                    try await Task.sleep(nanoseconds: 2_000_000_000)
                    if Task.isCancelled { return }
                    let status = try await PlanService.runStatus(
                        baseURL: baseURL, userID: userId, runId: handle.runId
                    )
                    self.runStatus = status
                    if status.isTerminal { break }
                }

                if let status = self.runStatus, status.status == "done" {
                    self.candidates = try await PlanService.candidates(
                        baseURL: baseURL, userID: userId, runId: status.runId
                    )
                } else if let status = self.runStatus, status.status == "failed" {
                    self.errorMessage = status.error ?? "The discovery run failed."
                }
            } catch {
                if !Task.isCancelled {
                    self.errorMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
                }
            }
            self.isDiscovering = false
        }
    }

    func cancelDiscovery() {
        pollTask?.cancel()
        isDiscovering = false
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
    }
}
