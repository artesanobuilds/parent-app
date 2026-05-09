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
                        await ensureAuthToken(for: data.parentName)
                        seedProfileOnBackend(data)
                    }
                }
            }
        }
    }

    /// Issue + cache an auth token for this user_id if we don't already have one.
    /// Closed-beta v0: any client can claim a user_id; v1 upgrades to Apple Sign-In.
    @MainActor
    private func ensureAuthToken(for userID: String) async {
        if AuthService.shared.token(for: userID) != nil { return }
        let baseString = UserDefaults.standard.string(forKey: "chat.base_url") ?? ServerConfiguration.defaultURL
        guard let url = URL(string: baseString) else { return }
        do {
            _ = try await AuthService.shared.obtainToken(for: userID, baseURL: url)
            print("[auth] token issued for \(userID)")
        } catch {
            print("[auth] failed to issue token: \(error)")
        }
    }

    /// Fire-and-forget POST to /profile/seed so the coaching agent has context.
    @MainActor
    private func seedProfileOnBackend(_ data: OnboardingData) {
        let defaults = UserDefaults.standard
        let baseString = defaults.string(forKey: "chat.base_url") ?? "http://localhost:8904"
        guard let url = URL(string: baseString)?.appendingPathComponent("profile/seed") else { return }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 15
        // Attach Bearer token from AuthService (must be issued first).
        let header = AuthService.shared.header(for: data.parentName)
        for (k, v) in header { request.setValue(v, forHTTPHeaderField: k) }

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

        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: request) { _, response, error in
            if let error = error {
                print("[profile/seed] error: \(error.localizedDescription)")
            } else if let http = response as? HTTPURLResponse {
                print("[profile/seed] status \(http.statusCode) for user \(data.parentName)")
            }
        }.resume()
    }
}
