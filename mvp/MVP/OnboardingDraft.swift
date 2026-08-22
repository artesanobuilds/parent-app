import Foundation

// MARK: - Durable onboarding draft
//
// The Heisman sprint-01 funnel collects EVERYTHING before an account exists:
// the parent answers every question, watches a real extraction run, and only
// meets the account wall at the very end. That inverts the risk profile of
// onboarding. A crash, a force-quit, or an abandoned Apple sheet between the
// cold open and `/profile/seed` would throw the whole family away with
// nothing on the server to recover from.
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
    ///
    /// The Heisman funnel only ASKS name + age (Onboarding-2 rows); the other
    /// fields stay because a v4 draft may carry values for them, they still
    /// seed, and the post-auth profile editors are where they're edited now.
    struct Kid: Codable, Equatable, Identifiable {
        var id: UUID = UUID()
        var name: String = ""
        var age: String = ""
        var temperament: String = ""
        var gradeBand: String = ""
        /// "boy" / "girl" / "" (unset). No longer asked in the funnel.
        var gender: String = ""

        // Tolerant decoding, same reasoning as the parent struct's: a field
        // added later must never invalidate an already-saved draft.
        enum CodingKeys: String, CodingKey { case id, name, age, temperament, gradeBand, gender }
        init() {}
        init(from decoder: Decoder) throws {
            let c = try decoder.container(keyedBy: CodingKeys.self)
            id = (try? c.decode(UUID.self, forKey: .id)) ?? UUID()
            name = (try? c.decode(String.self, forKey: .name)) ?? ""
            age = (try? c.decode(String.self, forKey: .age)) ?? ""
            temperament = (try? c.decode(String.self, forKey: .temperament)) ?? ""
            gradeBand = (try? c.decode(String.self, forKey: .gradeBand)) ?? ""
            gender = (try? c.decode(String.self, forKey: .gender)) ?? ""
        }
    }

    /// One structured activity from `POST /onboarding/extract` — the
    /// who/what/when/where cards on the "Check my work" screen. Persisted in
    /// the draft (Appendix A2: extraction results ride the post-account seed
    /// into real tracked activities). Field names match the wire contract.
    struct ExtractedActivity: Codable, Equatable, Identifiable {
        var id: UUID = UUID()
        var who: String = ""
        var what: String = ""
        var when: String = ""
        var `where`: String = ""
        var notes: String = ""

        // `id` is client-local (ForEach identity); the server payload has no
        // id, so decoding backfills one and encoding round-trips it harmlessly.
        enum CodingKeys: String, CodingKey { case id, who, what, when, `where`, notes }
        init(who: String = "", what: String = "", when: String = "", where whereValue: String = "", notes: String = "") {
            self.who = who; self.what = what; self.when = when; self.where = whereValue; self.notes = notes
        }
        init(from decoder: Decoder) throws {
            let c = try decoder.container(keyedBy: CodingKeys.self)
            id = (try? c.decode(UUID.self, forKey: .id)) ?? UUID()
            who = (try? c.decode(String.self, forKey: .who)) ?? ""
            what = (try? c.decode(String.self, forKey: .what)) ?? ""
            when = (try? c.decode(String.self, forKey: .when)) ?? ""
            `where` = (try? c.decode(String.self, forKey: .where)) ?? ""
            notes = (try? c.decode(String.self, forKey: .notes)) ?? ""
        }
    }

    /// Position in the funnel's *computed* flow (see `OnboardingView.flow`) —
    /// persisted so a relaunch resumes on the screen the parent left, not at
    /// the splash. Clamped on load: a draft that points past the account wall
    /// without a resolved account is walked back to the account wall.
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
    ///  - v4 — `.splash` removed from the flow (2026-08-10; the native launch
    ///    screen shows the same illustration, so the in-funnel interstitial
    ///    read as the splash appearing twice). Positional shift back by one.
    ///  - v5 — the Heisman sprint-01 rebuild (2026-08-21): the whole
    ///    questionnaire is replaced (splash → coldOpen → children → topic →
    ///    sampleProblem → extractionCheck → parentTasks → gettingReady →
    ///    coachDemo → accountWall → plan → allSet) and sign-in moves to the
    ///    END (the account wall). REORDER migration: v4 indices re-home onto
    ///    named steps — see `resumeIfNeeded` for the exact mapping.
    ///
    /// (This list is the SAME list as the one on `OnboardingView` — the two
    /// drifted once, v1–v3 here vs v4 there. Keep them in sync.)
    var flowVersion: Int = 1

    // Cold open ("Onboarding - 1") — name + location.
    var parentName: String = ""
    /// The cold open's "Location / Zip Code" field. Kept under the existing
    /// `postalCode` name because it seeds as `postal_code` (the pinned
    /// contract key) and Chief-of-Staff activity discovery reads it.
    var postalCode: String = ""

    // Fields the Heisman funnel no longer asks. They stay on the draft
    // because (a) a resumed v4 draft may carry real answers in them, (b) they
    // still ride the seed, and (c) the post-auth profile editors edit them.
    var household: String = ""
    var primaryLanguage: String = ""
    var secondaryLanguage: String = ""
    var educationStyle: String = ""
    /// v4 leftover ("Hi {name}!" count screen). Unused by the Heisman flow —
    /// children are added as rows now — but kept for decode stability.
    var kidCountText: String = ""

    // Children ("Onboarding - 2") — add/remove rows in place.
    var kids: [Kid] = []

    // Topic ("Onboarding - 3") — six cards XOR free text, ONE value: a card id
    // (`OnboardingTopic.id`) or the free string as typed.
    var topic: String = ""

    // Sample problem ("Onboarding - 4a/4b") — the raw scrap handed over.
    var sampleProblemText: String = ""

    // Extraction result ("Onboarding - 5") — persisted per Appendix A2 and
    // seeded as `extracted_activities`. Empty = extraction skipped/failed
    // (screen 5 falls back to the static sample cards).
    var extractedActivities: [ExtractedActivity] = []

    // Parent tasks ("Onboarding - 6") — multi-select + free text. The free
    // text rides as one more task string at seed time.
    var parentTasks: [String] = []
    var parentTasksNote: String = ""

    // v4 leftovers, still seeded, edited post-auth in the profile editors.
    var familyActivities: [String] = []
    var challenges: [String] = []
    var goals: [String] = []

    // "You're all set" — coach voice/personality (post-auth tail screen).
    var coachVoice: String = "Default - Male"
    var coachPersonality: String = "Default - Genuine"

    // MARK: - Tolerant decoding
    //
    // v5 ADDS keys (topic, sampleProblemText, extractedActivities,
    // parentTasks, parentTasksNote) that a stored v4 draft's JSON simply
    // doesn't have. Swift's synthesized `init(from:)` throws on a missing
    // key — property defaults do NOT apply during decoding — which would
    // turn every mid-funnel v4 resume into a silent "start over". Every
    // field decodes `IfPresent` with its default instead, so adding a field
    // can never invalidate an older draft again.

    enum CodingKeys: String, CodingKey {
        case stepIndex, flowVersion, parentName, postalCode, household
        case primaryLanguage, secondaryLanguage, educationStyle, kidCountText
        case kids, topic, sampleProblemText, extractedActivities
        case parentTasks, parentTasksNote
        case familyActivities, challenges, goals, coachVoice, coachPersonality
    }

    init() {}

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        stepIndex = (try? c.decode(Int.self, forKey: .stepIndex)) ?? 0
        flowVersion = (try? c.decode(Int.self, forKey: .flowVersion)) ?? 1
        parentName = (try? c.decode(String.self, forKey: .parentName)) ?? ""
        postalCode = (try? c.decode(String.self, forKey: .postalCode)) ?? ""
        household = (try? c.decode(String.self, forKey: .household)) ?? ""
        primaryLanguage = (try? c.decode(String.self, forKey: .primaryLanguage)) ?? ""
        secondaryLanguage = (try? c.decode(String.self, forKey: .secondaryLanguage)) ?? ""
        educationStyle = (try? c.decode(String.self, forKey: .educationStyle)) ?? ""
        kidCountText = (try? c.decode(String.self, forKey: .kidCountText)) ?? ""
        kids = (try? c.decode([Kid].self, forKey: .kids)) ?? []
        topic = (try? c.decode(String.self, forKey: .topic)) ?? ""
        sampleProblemText = (try? c.decode(String.self, forKey: .sampleProblemText)) ?? ""
        extractedActivities = (try? c.decode([ExtractedActivity].self, forKey: .extractedActivities)) ?? []
        parentTasks = (try? c.decode([String].self, forKey: .parentTasks)) ?? []
        parentTasksNote = (try? c.decode(String.self, forKey: .parentTasksNote)) ?? ""
        familyActivities = (try? c.decode([String].self, forKey: .familyActivities)) ?? []
        challenges = (try? c.decode([String].self, forKey: .challenges)) ?? []
        goals = (try? c.decode([String].self, forKey: .goals)) ?? []
        coachVoice = (try? c.decode(String.self, forKey: .coachVoice)) ?? "Default - Male"
        coachPersonality = (try? c.decode(String.self, forKey: .coachPersonality)) ?? "Default - Genuine"
    }

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
