import SwiftUI
import UIKit
import UserNotifications

@main
struct MVPApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @AppStorage("onboarding_completed") private var onboardingCompleted = false
    @AppStorage("user_name") private var userName = ""
    // Parent's display name for the greeting. `userName` is now an opaque
    // account id (UUID), so the name is stored separately. Set at onboarding;
    // HomeView also refreshes it from the profile.
    @AppStorage("parent_display_name") private var parentDisplayName = ""

    // A pending onboarding seed that hasn't been confirmed by the backend yet.
    // Persisted so a transient failure (no network, token race, a base-URL that
    // isn't set until MainTabView mounts) self-heals on the next launch instead
    // of silently losing the parent's onboarding data forever.
    private static let pendingSeedBodyKey = "pending_seed_body"   // JSON Data
    private static let pendingSeedUserKey = "pending_seed_user"   // String

    // Owns log-out / delete-account, which must reach the launch-gate keys above.
    // Injected into the tab tree so a Settings screen can flip the gate.
    @StateObject private var session = AppSession()

    var body: some Scene {
        WindowGroup {
            #if DEBUG
            // DEBUG-only sign-in harness, reached via `TEST_SIGNIN=1` in the
            // launch environment. Lets us exercise SignInView end-to-end without
            // touching the real onboarding/gate cutover. Never present in release.
            if ProcessInfo.processInfo.environment["TEST_SIGNIN"] == "1" {
                SignInTestHarness()
            } else {
                mainContent
            }
            #else
            mainContent
            #endif
        }
    }

    @ViewBuilder
    private var mainContent: some View {
        if onboardingCompleted && !userName.isEmpty {
            MainTabView(username: userName)
                .environmentObject(session)
                .task {
                    await ensureAuthToken(for: userName)
                    // Re-seed if a prior attempt never confirmed. No-op when
                    // there's nothing pending. This is what makes the seed
                    // durable across app restarts.
                    await flushPendingSeed()
                    // Flush a pending legal agreement + refresh the status
                    // that drives the Home re-accept banner.
                    await session.refreshLegal(
                        userID: userName,
                        baseURL: URL(string: resolvedBaseURLString())
                    )
                    // Product analytics — started only here (past onboarding +
                    // consent), never on the sign-in/onboarding screens.
                    // identify on the OPAQUE analytics id, never the user_id.
                    Analytics.startIfConsented()
                    Analytics.identify(AuthService.shared.credential(for: userName)?.analyticsId)
                    // Ask for notification permission + register for APNs so a
                    // crisis-lock push can reach the parent. Post-onboarding so
                    // the prompt lands in context, not on a cold first launch.
                    PushRegistration.requestAndRegister()
                }
        } else if userName.isEmpty {
            // New user: sign in FIRST (native Apple / Google), which resolves a
            // durable server account id. Replaces the old anonymous
            // /auth/issue-token path, where the user_id was just the typed parent
            // name (guessable, unauthenticated). EXISTING onboarded users never
            // reach here — they go straight to MainTabView on their legacy token
            // and migrate whenever they choose to sign in (dual-accept keeps the
            // legacy token valid meanwhile).
            //
            // The BACKEND decides new-vs-returning: `hasProfile` means this
            // account already has data (e.g. same user on a new device / after
            // reinstall) → skip onboarding straight to the app. A fresh account
            // has no profile → onboarding.
            SignInView { outcome in
                userName = outcome.userId
                if outcome.hasProfile {
                    onboardingCompleted = true
                }
            }
        } else {
            // Signed in (userName is the server-resolved id) but not onboarded.
            OnboardingView { data in
                onboardingCompleted = true
                // Remember the parent's display name for the greeting (userName
                // is the opaque account id now).
                parentDisplayName = data.parentName
                // Stash the seed payload BEFORE attempting it, so even if this
                // first POST fails (or the app is killed mid-request) the next
                // launch retries it. Seeds under the signed-in userName, NOT the
                // display name. Then attempt it now.
                stashPendingSeed(data)
                Task { await flushPendingSeed() }
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
    /// `userId` is the resolved (signed-in) account id — the parent name is only
    /// a display field, never the key.
    private func seedBody(userId: String, from data: OnboardingData) -> [String: Any] {
        var body: [String: Any] = [
            "user_id": userId,
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
        // Seed under the resolved (signed-in) account id, never the display name.
        let userId = userName
        guard !userId.isEmpty,
              let payload = try? JSONSerialization.data(withJSONObject: seedBody(userId: userId, from: data)) else {
            print("[profile/seed] failed to encode seed body for \(userId.isEmpty ? "<no user>" : userId)")
            return
        }
        let defaults = UserDefaults.standard
        defaults.set(payload, forKey: Self.pendingSeedBodyKey)
        defaults.set(userId, forKey: Self.pendingSeedUserKey)
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

// MARK: - Push notifications (crisis-lock alerts)

/// Handles APNs registration callbacks. A crisis-lock push tapped by the parent
/// simply opens the app to Home, where the affected companion shows a red
/// "Review" pill and the reactivate flow (KidsHomeSection). v1 keeps the deep
/// link that light — no private-state routing.
final class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        return true
    }

    func application(_ application: UIApplication,
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02x", $0) }.joined()
        Task { await PushRegistration.upload(deviceToken: token) }
    }

    func application(_ application: UIApplication,
                     didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("[push] APNs registration failed: \(error.localizedDescription)")
    }

    // Show the alert even when the app is foregrounded.
    func userNotificationCenter(_ center: UNUserNotificationCenter,
                                willPresent notification: UNNotification) async
        -> UNNotificationPresentationOptions {
        [.banner, .sound, .list]
    }
}

/// Requests notification permission, registers for APNs, and uploads the device
/// token to the backend so crisis-lock pushes can be delivered. Reuses the same
/// AuthService bearer pattern as the onboarding seed.
enum PushRegistration {
    static func requestAndRegister() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, _ in
            guard granted else { return }
            DispatchQueue.main.async { UIApplication.shared.registerForRemoteNotifications() }
        }
    }

    @MainActor
    static func upload(deviceToken: String) async {
        let defaults = UserDefaults.standard
        guard let userID = defaults.string(forKey: "user_name"), !userID.isEmpty else { return }
        let baseString = defaults.string(forKey: "chat.base_url") ?? ServerConfiguration.defaultURL
        guard let baseURL = URL(string: baseString) else { return }
        do {
            _ = try await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        } catch {
            print("[push] could not issue token for device-token upload: \(error)")
            return
        }
        var request = URLRequest(url: baseURL.appendingPathComponent("push/register-device"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 15
        for (k, v) in AuthService.shared.header(for: userID) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        request.httpBody = try? JSONSerialization.data(
            withJSONObject: ["user_id": userID, "device_token": deviceToken, "platform": "ios"]
        )
        _ = try? await URLSession.shared.data(for: request)
    }
}
