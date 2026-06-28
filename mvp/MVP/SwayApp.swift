import SwiftUI

@main
struct MVPApp: App {
    @AppStorage("onboarding_completed") private var onboardingCompleted = false
    @AppStorage("user_name") private var userName = ""

    // A pending onboarding seed that hasn't been confirmed by the backend yet.
    // Persisted so a transient failure (no network, token race, a base-URL that
    // isn't set until MainTabView mounts) self-heals on the next launch instead
    // of silently losing the parent's onboarding data forever.
    private static let pendingSeedBodyKey = "pending_seed_body"   // JSON Data
    private static let pendingSeedUserKey = "pending_seed_user"   // String

    var body: some Scene {
        WindowGroup {
            if onboardingCompleted && !userName.isEmpty {
                MainTabView(username: userName)
                    .task {
                        await ensureAuthToken(for: userName)
                        // Re-seed if a prior attempt never confirmed. No-op when
                        // there's nothing pending. This is what makes the seed
                        // durable across app restarts.
                        await flushPendingSeed()
                    }
            } else {
                OnboardingView { data in
                    userName = data.parentName
                    onboardingCompleted = true
                    // Stash the seed payload BEFORE attempting it, so even if this
                    // first POST fails (or the app is killed mid-request) the next
                    // launch retries it. Then attempt it now.
                    stashPendingSeed(data)
                    Task { await flushPendingSeed() }
                }
            }
        }
    }

    /// Issue + cache an auth token for this user_id if we don't already have one.
    /// Closed-beta v0: any client can claim a user_id; v1 upgrades to Apple Sign-In.
    @MainActor
    private func ensureAuthToken(for userID: String) async {
        guard let url = URL(string: resolvedBaseURLString()) else { return }
        do {
            _ = try await AuthService.shared.ensureToken(for: userID, baseURL: url)
        } catch {
            print("[auth] failed to issue token: \(error)")
        }
    }

    // MARK: - Onboarding seed (durable)

    /// The base URL the app talks to. Falls back to `ServerConfiguration.defaultURL`
    /// (production in a release build) — NOT localhost. The previous localhost
    /// fallback silently failed every fresh-install seed, because `chat.base_url`
    /// isn't written to UserDefaults until `ServerConfiguration` is first created
    /// (in MainTabView, which only mounts AFTER onboarding completes).
    private func resolvedBaseURLString() -> String {
        UserDefaults.standard.string(forKey: "chat.base_url") ?? ServerConfiguration.defaultURL
    }

    /// Build the /profile/seed request body from the collected onboarding data.
    private func seedBody(from data: OnboardingData) -> [String: Any] {
        var body: [String: Any] = [
            "user_id": data.parentName,
            "parent_name": data.parentName,
            "kids": data.kids.map {
                [
                    "name": $0.name,
                    "age": $0.age,
                    "temperament": $0.temperament,
                    "pronouns": $0.pronouns,
                    "grade_band": $0.gradeBand
                ]
            },
            "household": data.household,
            "support_system": data.supportSystem,
            "energy_pattern": data.energyPattern,
            "dreaded_moment": data.dreadedMoment,
            "challenges": data.challenges,
            "goals": data.goals,
            "postal_code": data.postalCode,
            "country": data.country,
            "primary_language": data.primaryLanguage,
            "parent_age_range": data.parentAgeRange,
            "employment": data.employment,
            "cultural_background": data.culturalBackground,
            "pronouns": data.pronouns
        ]
        if let adults = data.adultsInHousehold {
            body["adults_in_household"] = adults
        }
        return body
    }

    /// Persist the seed payload so it survives a failed attempt / app restart.
    @MainActor
    private func stashPendingSeed(_ data: OnboardingData) {
        guard let payload = try? JSONSerialization.data(withJSONObject: seedBody(from: data)) else {
            print("[profile/seed] failed to encode body for \(data.parentName)")
            return
        }
        let defaults = UserDefaults.standard
        defaults.set(payload, forKey: Self.pendingSeedBodyKey)
        defaults.set(data.parentName, forKey: Self.pendingSeedUserKey)
    }

    /// POST any pending seed; clear it only on a confirmed 200. Retries a few
    /// times this session with backoff so a brief blip heals immediately; if it
    /// still hasn't confirmed, the payload stays pending and the next launch
    /// retries. No-op when nothing is pending.
    @MainActor
    private func flushPendingSeed() async {
        let defaults = UserDefaults.standard
        guard let payload = defaults.data(forKey: Self.pendingSeedBodyKey),
              let user = defaults.string(forKey: Self.pendingSeedUserKey), !user.isEmpty else {
            return
        }
        guard let baseURL = URL(string: resolvedBaseURLString()) else {
            print("[profile/seed] invalid base URL: \(resolvedBaseURLString())")
            return
        }

        for attempt in 0..<4 {
            let status = await postSeed(parentName: user, baseURL: baseURL, body: payload, retry: true)
            if status == 200 {
                defaults.removeObject(forKey: Self.pendingSeedBodyKey)
                defaults.removeObject(forKey: Self.pendingSeedUserKey)
                print("[profile/seed] confirmed for \(user); pending cleared")
                return
            }
            print("[profile/seed] attempt \(attempt) status \(status) for \(user); will retry")
            // 1s, 2s, 3s backoff between in-session attempts.
            try? await Task.sleep(nanoseconds: UInt64(attempt + 1) * 1_000_000_000)
        }
        print("[profile/seed] still pending for \(user) after retries; will retry next launch")
    }

    /// Inner helper. Ensures a token (issues one if missing), POSTs, and on
    /// 401 force-re-issues the token and retries once. Returns the final HTTP
    /// status, or -1 on transport error.
    @MainActor
    private func postSeed(parentName: String, baseURL: URL, body: Data, retry: Bool) async -> Int {
        // Make sure we have a token before sending. ensureToken coalesces so
        // concurrent paths share a single in-flight /auth/issue-token call.
        do {
            _ = try await AuthService.shared.ensureToken(for: parentName, baseURL: baseURL)
        } catch {
            print("[profile/seed] could not issue token: \(error)")
            return -1
        }
        var request = URLRequest(url: baseURL.appendingPathComponent("profile/seed"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 15
        for (k, v) in AuthService.shared.header(for: parentName) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        request.httpBody = body

        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            let status = (response as? HTTPURLResponse)?.statusCode ?? -1
            if status == 401 && retry {
                print("[profile/seed] 401 — refreshing token and retrying once")
                AuthService.shared.clear(for: parentName)
                return await postSeed(parentName: parentName, baseURL: baseURL, body: body, retry: false)
            }
            return status
        } catch {
            print("[profile/seed] transport error: \(error.localizedDescription)")
            return -1
        }
    }
}
