import Foundation

// MARK: - Durable onboarding draft
//
// beta-v1 moved sign-in from a launch GATE to the tail of the funnel: the
// parent now answers every question BEFORE an account exists. That inverts the
// risk profile of onboarding. Previously an abandoned funnel lost nothing
// (there was already a signed-in account and every answer landed in one seed at
// the end); now a crash, a force-quit, or an abandoned Apple sheet between
// "Let's get acquainted" and `/profile/seed` would throw the whole family away
// with nothing on the server to recover from.
//
// So the funnel writes to this draft on EVERY mutation, exactly mirroring the
// `pending_seed_body` pattern in SwayApp.swift — and, like that payload, the
// draft is discarded at exactly ONE moment: when `/profile/seed` answers 200.
// (See `MVPApp.flushPendingSeed`, the only caller of `OnboardingDraft.clear`.)
//
// This is deliberately a dumb Codable value type with no networking and no
// view state. The funnel holds ONE `@State var draft` and persists it from a
// single `.onChange`, so there is no way to add a field that silently isn't
// persisted.

struct OnboardingDraft: Codable, Equatable {

    /// One collected child. `id` is stable across relaunches (it round-trips
    /// through the JSON) so `ForEach` identity survives a resume.
    struct Kid: Codable, Equatable, Identifiable {
        var id: UUID = UUID()
        var name: String = ""
        var age: String = ""
        var temperament: String = ""
        var gradeBand: String = ""
        /// "boy" / "girl" / "" (unset). Phase-3 Figma delta — a tag choice on
        /// the child screen, alongside name/age/personality.
        var gender: String = ""
    }

    /// Position in the funnel's *computed* flow (see `OnboardingView.flow`) —
    /// persisted so a relaunch resumes on the screen the parent left, not at
    /// the splash. Clamped on load: a draft that points past the sign-in screen
    /// without a resolved account is walked back to sign-in.
    var stepIndex: Int = 0

    /// Schema version for what `stepIndex` means within `OnboardingView.flow`.
    /// A draft saved by pre-versioning code has NO `flowVersion` key at all,
    /// so `load()` backfills this default of 1 — that absence IS the
    /// migration signal. Bumped by `OnboardingView.resumeIfNeeded`, the ONLY
    /// writer of this field, right after it applies (or skips) each one-time
    /// remap. Never set this anywhere else, or a legitimately-current index
    /// could be shifted twice.
    ///
    ///  - v1 — predates the `.plan` (paywall) step (added 2026-08-09).
    ///  - v2 — `.plan` sits directly before `.warmup`, at the END of the
    ///    funnel, after `.signIn`. Every v1 index at or after the old warmup
    ///    position shifts by +1 to land in v2.
    ///  - v3 — `.plan` and `.signIn` moved to the START of the funnel, before
    ///    `.splash` and the questionnaire (2026-08-09, same day — the design
    ///    changed again within hours). This is a REORDER, not an insertion,
    ///    so v2→v3 re-homes onto the SAME NAMED STEP rather than shifting a
    ///    position.
    var flowVersion: Int = 1

    // Screen 1 — "Let's get acquainted"
    var parentName: String = ""
    var household: String = ""
    var primaryLanguage: String = ""
    /// Phase-3 Figma delta — bilingual homes get a second language alongside
    /// `primaryLanguage` (e.g. Spanish primary, English secondary).
    var secondaryLanguage: String = ""
    /// Phase-3 Figma delta — RESTORED. Removed from the funnel last round;
    /// Chief-of-Staff activity discovery needs it to find local camps/classes.
    /// Sent to the backend as `postal_code` (the existing contract key).
    var postalCode: String = ""
    /// Phase-3 Figma delta — e.g. "Public school", "Homeschool", "Montessori".
    var educationStyle: String = ""

    // Screen 2 — "Hi {name}!" (raw text so a half-typed "1" doesn't snap to 1)
    var kidCountText: String = ""

    // Screens 3..n — one per child
    var kids: [Kid] = []

    // Screen n+1 — "What do you do in your free time?" (Phase-3 Figma delta).
    // Multi-select 3x3 icon grid; feeds Chief-of-Staff activity discovery.
    var familyActivities: [String] = []

    // Screen n+2 — "What's on your mind?"
    var challenges: [String] = []
    var goals: [String] = []

    // Final "all set" screen — Phase-3 Figma delta: "Set up how you want the
    // coach to respond". Pre-filled with the design's shown defaults rather
    // than empty, since the design renders them as the current selection, not
    // a placeholder.
    var coachVoice: String = "Default - Male"
    var coachPersonality: String = "Default - Genuine"

    // MARK: - Persistence

    /// Mirrors `pending_seed_body` in naming and lifecycle.
    static let storageKey = "pending_onboarding_draft"

    /// Returns nil when there's nothing pending (the normal first-launch case)
    /// or when a stored draft can't be decoded — a shape change must degrade to
    /// "start over", never to a crash.
    static func load(from defaults: UserDefaults = .standard) -> OnboardingDraft? {
        guard let data = defaults.data(forKey: storageKey) else { return nil }
        return try? JSONDecoder().decode(OnboardingDraft.self, from: data)
    }

    func save(to defaults: UserDefaults = .standard) {
        guard let data = try? JSONEncoder().encode(self) else {
            print("[onboarding-draft] failed to encode draft; answers are NOT durable this session")
            return
        }
        defaults.set(data, forKey: Self.storageKey)
    }

    /// Discard the draft. Call this ONLY once the server has confirmed the seed
    /// — clearing it any earlier re-opens the data-loss hole this type exists
    /// to close.
    static func clear(from defaults: UserDefaults = .standard) {
        defaults.removeObject(forKey: storageKey)
    }
}
