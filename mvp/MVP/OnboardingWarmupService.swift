import Foundation

// MARK: - First-run agent warm-up client
//
// ┌─ REWIRING SEAM ───────────────────────────────────────────────────────────┐
// │ EVERYTHING this app knows about the warm-up wire format lives in this     │
// │ file: the three response structs below and the two paths in `enqueue` /   │
// │ `status`. `OnboardingView` only ever sees `percent`, `steps` and          │
// │ `isTerminal`, so a backend shape change is a one-file edit.               │
// └───────────────────────────────────────────────────────────────────────────┘
//
// As-built contract (app/onboarding_warmup.py, verified 2026-08-07):
//
//   POST /onboarding/warmup            {"user_id": "..."}   (body id optional;
//                                       the authenticated identity is truth)
//     → 200 {"run_id": "...", "status": "queued", "deduped": false}
//
//   GET  /onboarding/warmup/{run_id}
//     → 200 {"run_id": "...", "status": "queued|running|done|failed|canceled",
//            "percent": 0-100,
//            "steps": [{"key": "family", "label": "...",
//                       "state": "pending|running|done|failed|skipped",
//                       "detail": {}, "error": null}, ...],
//            "result": {...}, "error": null}
//
//   GET  /onboarding/warmup/{run_id}/stream   — SSE, same payload per frame.
//
// We POLL rather than stream. The SSE endpoint carries no extra information
// (its frames are `status_payload` verbatim) and a plain request/response loop
// has no half-open-connection failure mode to reason about — which matters
// because the screen this drives must never trap the parent.
//
// THE HARD RULE, mirrored from the backend: the ring must never block. Every
// function here returns an Optional and swallows its errors. A missing
// endpoint, an expired token, airplane mode and a 500 are all the same answer
// — `nil` — and the caller's deadline moves the parent on regardless.

/// One of Greg's four beats.
struct WarmupStep: Decodable, Identifiable, Equatable {
    let key: String
    let label: String
    /// `pending` | `running` | `done` | `failed` | `skipped`
    let state: String

    var id: String { key }

    /// `failed` and `skipped` count as finished: the beat is over, and a beat
    /// that failed must still let the run reach 100 (a degraded Home beats a
    /// parent stuck behind a spinner).
    var isFinished: Bool { state == "done" || state == "failed" || state == "skipped" }
    var isRunning: Bool { state == "running" }
    /// Only a genuine success earns Greg's check mark.
    var isSucceeded: Bool { state == "done" }
}

/// The poll/stream payload. Extra keys (`detail`, `result`, `error`) decode
/// away harmlessly, so the backend can add fields without breaking the client.
struct WarmupStatus: Decodable, Equatable {
    let status: String
    let percent: Int
    let steps: [WarmupStep]

    enum CodingKeys: String, CodingKey {
        case status, percent, steps
    }

    var isTerminal: Bool { status == "done" || status == "failed" || status == "canceled" }
}

private struct CreateWarmupResponse: Decodable {
    let runID: String
    let status: String?
    /// `true` when a run was already active for this parent — the CORRECT
    /// outcome to reuse, not an error. (A resumed funnel re-enters the ring and
    /// re-POSTs; the server hands back the in-flight run.)
    let deduped: Bool?

    enum CodingKeys: String, CodingKey {
        case runID = "run_id"
        case status, deduped
    }
}

@MainActor
enum OnboardingWarmupService {

    /// Greg's four beats in display order, all pending. Rendered before the
    /// server has answered — and, if it never does, for the whole screen.
    /// Labels are duplicated from `STEP_LABELS` in app/onboarding_warmup.py;
    /// once a real payload arrives its labels win.
    static let placeholderSteps: [WarmupStep] = [
        WarmupStep(key: "family",  label: "Getting to know your family",    state: "pending"),
        WarmupStep(key: "coach",   label: "Bringing your coach up to speed", state: "pending"),
        WarmupStep(key: "plan",    label: "Sketching your first plan",      state: "pending"),
        WarmupStep(key: "account", label: "Securing your family's space",   state: "pending")
    ]

    /// Resolves through `ServerConfiguration` only. NEVER add a literal host
    /// fallback here — on a real-device fresh install a `127.0.0.1` fallback
    /// posts to the phone's own localhost. (tests/test_ios_baseurl_guard.py)
    private static var baseURL: URL? {
        URL(string: UserDefaults.standard.string(forKey: "chat.base_url")
            ?? ServerConfiguration.defaultURL)
    }

    /// Enqueue the warm-up. Returns the run id, or nil if it couldn't start for
    /// any reason at all — the caller treats nil as "skip to the landing".
    ///
    /// Called EXACTLY once per appearance of the ring and never retried:
    /// `RATE_LIMIT_WARMUP_PER_HOUR` defaults to 10/hour, and a failed enqueue
    /// is not worth spending that budget on when the fallback (land on "You're
    /// all set" with an unpersonalised Home) is already acceptable.
    static func enqueue(userID: String) async -> String? {
        guard !userID.isEmpty, let base = baseURL else { return nil }
        guard let request = await authorized(
            "onboarding/warmup", base: base, userID: userID, method: "POST",
            body: try? JSONSerialization.data(withJSONObject: ["user_id": userID])
        ) else { return nil }

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            let code = (response as? HTTPURLResponse)?.statusCode ?? -1
            guard (200...299).contains(code) else {
                // 403 = body/token identity mismatch, 429 = rate limited,
                // 404 = backend without the warm-up yet. All the same answer.
                print("[warmup] enqueue returned \(code); ring will land unpersonalised")
                return nil
            }
            let created = try JSONDecoder().decode(CreateWarmupResponse.self, from: data)
            if created.deduped == true {
                print("[warmup] reusing in-flight run \(created.runID)")
            }
            return created.runID
        } catch {
            print("[warmup] enqueue failed: \(error.localizedDescription)")
            return nil
        }
    }

    /// Poll one run. nil on any failure — the caller keeps the last good state
    /// and keeps counting down its deadline.
    static func status(runID: String, userID: String) async -> WarmupStatus? {
        guard let base = baseURL else { return nil }
        guard let request = await authorized(
            "onboarding/warmup/\(runID)", base: base, userID: userID, method: "GET", body: nil
        ) else { return nil }

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard (200...299).contains((response as? HTTPURLResponse)?.statusCode ?? -1) else {
                return nil
            }
            return try JSONDecoder().decode(WarmupStatus.self, from: data)
        } catch {
            return nil
        }
    }

    // MARK: - Private

    /// Builds a bearer-authenticated request, issuing a token first if needed.
    /// Same `AuthService.ensureToken` + `header(for:)` pair the durable seed
    /// uses, so the warm-up can never race ahead of token issuance.
    private static func authorized(
        _ path: String, base: URL, userID: String, method: String, body: Data?
    ) async -> URLRequest? {
        do {
            _ = try await AuthService.shared.ensureToken(for: userID, baseURL: base)
        } catch {
            print("[warmup] could not issue token: \(error.localizedDescription)")
            return nil
        }
        var request = URLRequest(url: base.appendingPathComponent(path))
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 12
        for (k, v) in AuthService.shared.header(for: userID) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        request.httpBody = body
        return request
    }
}
