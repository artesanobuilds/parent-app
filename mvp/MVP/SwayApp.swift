import SwiftUI

@main
struct MVPApp: App {
    @AppStorage("onboarding_completed") private var onboardingCompleted = false
    @AppStorage("user_name") private var userName = ""

    var body: some Scene {
        WindowGroup {
            if onboardingCompleted && !userName.isEmpty {
                MainTabView(username: userName)
                    .task { await ensureAuthToken(for: userName) }
            } else {
                OnboardingView { data in
                    userName = data.parentName
                    onboardingCompleted = true
                    Task {
                        // Seed the profile AFTER the token is in place. Uses the
                        // coalesced ensureToken via seedProfileOnBackend's own
                        // retry path, so a slow first /auth/issue-token doesn't
                        // race the seed POST.
                        await seedProfileOnBackend(data)
                    }
                }
            }
        }
    }

    /// Issue + cache an auth token for this user_id if we don't already have one.
    /// Closed-beta v0: any client can claim a user_id; v1 upgrades to Apple Sign-In.
    @MainActor
    private func ensureAuthToken(for userID: String) async {
        let baseString = UserDefaults.standard.string(forKey: "chat.base_url") ?? ServerConfiguration.defaultURL
        guard let url = URL(string: baseString) else { return }
        do {
            _ = try await AuthService.shared.ensureToken(for: userID, baseURL: url)
        } catch {
            print("[auth] failed to issue token: \(error)")
        }
    }

    /// POST /profile/seed, awaitably, with one retry on 401. Persists the
    /// onboarding form to the coaching profile so the agent has context.
    /// Surface as @MainActor so it can be called from the SwiftUI completion
    /// closure's Task without sendable warnings.
    @MainActor
    private func seedProfileOnBackend(_ data: OnboardingData) async {
        let defaults = UserDefaults.standard
        let baseString = defaults.string(forKey: "chat.base_url") ?? "http://127.0.0.1:8904"
        guard let baseURL = URL(string: baseString) else {
            print("[profile/seed] invalid base URL: \(baseString)")
            return
        }
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
        guard let payload = try? JSONSerialization.data(withJSONObject: body) else {
            print("[profile/seed] failed to encode body for \(data.parentName)")
            return
        }

        let status = await postSeed(parentName: data.parentName, baseURL: baseURL, body: payload, retry: true)
        print("[profile/seed] status \(status) for user \(data.parentName)")
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
