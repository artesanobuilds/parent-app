import Foundation
import SwiftUI
import PostHog

/// PostHog for iOS. Privacy posture matches the backend (`app/analytics`):
/// autocapture + session replay OFF, explicit allowlisted events only, and
/// identify on the OPAQUE `analytics_id` — never the user_id/name.
///
/// Setup is **gated on recorded consent** (call `Analytics.startIfConsented()`
/// only after the parent has accepted). No-op unless a `POSTHOG_API_KEY` is in
/// Info.plist. The project key is public-by-design (write-only), so shipping it
/// in the bundle is fine.
enum Analytics {

    /// event name → allowed property keys (mirror of the backend allowlist,
    /// iOS-relevant subset). Anything not listed is dropped.
    private static let events: [String: Set<String>] = [
        "login_succeeded": ["provider", "platform", "is_new_account", "linked_legacy"],
        "onboarding_completed": ["kid_count"],
        "parent_chat_message_sent": ["thread_kind"],
        "kid_chat_message_sent": ["agent_id"],
        "voice_session_started": ["surface"],
        "voice_session_ended": ["surface", "duration_s"],
        "chat_opened": ["agent_kind"],
        "activity_tracked": ["status"],
        "plan_exported": ["format"],
        // Client-only engagement events.
        "screen_viewed": ["screen"],
        "content_opened": ["type"],
        // Vertical doors — tap distribution informs which vertical ships next.
        "door_opened": ["door"],
        "door_converted": ["door"],
    ]

    /// Keys that must never be sent, whatever a call site passes.
    private static let denylist: Set<String> = [
        "message", "content", "text", "transcript", "name", "kid_name",
        "child_name", "parent_name", "email", "pin", "token", "address", "custody",
    ]

    private static var started = false

    private static var apiKey: String? {
        (Bundle.main.object(forInfoDictionaryKey: "POSTHOG_API_KEY") as? String)
            .flatMap { $0.isEmpty ? nil : $0 }
    }

    private static var host: String {
        (Bundle.main.object(forInfoDictionaryKey: "POSTHOG_HOST") as? String)
            .flatMap { $0.isEmpty ? nil : $0 } ?? "https://us.i.posthog.com"
    }

    /// Start PostHog — call ONLY after consent is recorded. Idempotent no-op
    /// without a key or if already started.
    static func startIfConsented() {
        guard !started, let key = apiKey else { return }
        let config = PostHogConfig(apiKey: key, host: host)
        config.captureApplicationLifecycleEvents = true
        config.captureScreenViews = false
        config.captureElementInteractions = false  // no UIKit autocapture (kid/family data on screen)
        config.sessionReplay = false               // never
        PostHogSDK.shared.setup(config)
        started = true
    }

    /// Identify the session on the OPAQUE analytics id (never the user_id).
    static func identify(_ analyticsId: String?) {
        guard started, let id = analyticsId, !id.isEmpty else { return }
        PostHogSDK.shared.identify(id)
    }

    static func capture(_ event: String, _ properties: [String: Any] = [:]) {
        guard started, let allowed = events[event] else { return }
        let clean = properties.filter { allowed.contains($0.key) && !denylist.contains($0.key) }
        PostHogSDK.shared.capture(event, properties: clean)
    }

    /// Clear the identity on sign-out.
    static func reset() {
        guard started else { return }
        PostHogSDK.shared.reset()
    }
}

extension View {
    /// Fire a `screen_viewed` event when this screen appears. One-liner for
    /// full-coverage navigation analytics: `.trackScreen("kid_companion")`.
    func trackScreen(_ name: String) -> some View {
        onAppear { Analytics.capture("screen_viewed", ["screen": name]) }
    }
}
