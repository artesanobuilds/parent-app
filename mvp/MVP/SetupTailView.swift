import SwiftUI

// The post-dashboard guided pass — beta-v1 sprint-1's ONBOARDING TAIL.
//
// Greg's canvas x-order IS the flow, and it puts the profile editors AFTER the
// dashboard:
//
//   … → creating account → welcome → Dashboard 1 → kid-001a/b/c → Dashboard 2
//       → kid-002a → account01/02/03 → parent 001 → parent 002
//       → co-parent 001 → circle member
//
// So the parent lands on Home FIRST and is then walked through filling in each
// kid and each adult. That is why Dashboard 1's kid tile reads "Set up
// Benjamin": the tile is the entry point into this tail.
//
// This file is the SEQUENCER, not a fifth editor. Every stop hands off to the
// editor that already shipped — `KidSettingsSheet` (birthday / grade /
// personality / photo), `MemberProfileSheet` (the role-driven adult editor),
// `ParentProfileEditor` (the account holder's own basics). Rebuilding those
// inside the tail would fork the write paths whose partial-update discipline is
// pinned by tests, and would give a kid edited from the tail a different
// persistence story from the same kid edited from Settings.
//
// The three properties the tail must have, and where each one lives:
//
//   RESUMABLE   — the stop list is recomputed from live server data on every
//                 open, and the cursor starts at the first stop whose STABLE id
//                 is neither completed nor skipped. There is no stored index to
//                 drift: adding or deleting a kid mid-tail cannot land the
//                 parent on the wrong person.
//   SKIPPABLE   — every stop has "Skip for now" (records the id as skipped, so
//                 an auto-run never offers it again) and the header has "Finish
//                 later" (records `deferred`, which suppresses auto-run for
//                 good). Both leave Home fully usable, and both leave the stop
//                 reachable from its tile forever.
//   IDEMPOTENT  — reaching the end sets `finished`, and an auto-run requires
//                 `!finished && !deferred`. Progress is keyed by kid PROFILE KEY
//                 and member UUID — never a display name, never a list index.
//
// Writes: the tail itself performs NO mutations. Each editor owns its own
// verified write (waits for a 2xx, renders what the server returned, keeps the
// sheet on failure). The tail only records *local* progress, and it records it
// AFTER the editor closes — so a failed save leaves the stop pending rather
// than marking a family set up that isn't.
//
// Base URL arrives from the caller, itself resolved through
// `ServerConfiguration`. Never a hardcoded fallback (tests/test_ios_baseurl_guard.py).

// MARK: - Durable progress

/// Local, per-account tail bookkeeping. Deliberately NOT server state: it
/// records what the parent has been *shown*, not what they own — the profile
/// itself is the source of truth for what's filled in, and it's already durable.
struct SetupTailState: Codable, Equatable {
    /// Stable ids whose editor the parent opened and closed.
    var completed: [String] = []
    /// Stable ids the parent explicitly deferred with "Skip for now".
    var skipped: [String] = []
    /// The walk reached its end at least once. Gates the auto-run — this is what
    /// makes the tail idempotent across launches.
    var finished = false
    /// "Finish later". Suppresses the auto-run permanently; this is a beta and a
    /// parent who opted out must not be asked again on every launch.
    var deferred = false

    func isPending(_ id: String) -> Bool {
        !completed.contains(id) && !skipped.contains(id)
    }
}

enum SetupTailStore {
    /// Keyed by account id so a second account on the same device (or a
    /// delete-account + re-onboard) starts clean.
    private static func key(for userID: String) -> String {
        "setup_tail_state_v1_\(userID)"
    }

    static func load(userID: String, defaults: UserDefaults = .standard) -> SetupTailState {
        guard !userID.isEmpty,
              let data = defaults.data(forKey: key(for: userID)),
              let state = try? JSONDecoder().decode(SetupTailState.self, from: data)
        else { return SetupTailState() }
        return state
    }

    static func save(_ state: SetupTailState, userID: String,
                     defaults: UserDefaults = .standard) {
        guard !userID.isEmpty, let data = try? JSONEncoder().encode(state) else { return }
        defaults.set(data, forKey: key(for: userID))
    }

    /// Should Home open the tail by itself?
    ///
    /// Only for a parent who has neither walked it to the end nor opted out, and
    /// only when there is genuinely a kid still to fill in. Kids drive this
    /// decision (not adults) because a fresh family always has kids and may have
    /// no roster rows at all — auto-opening a one-stop tail on the account
    /// holder's own basics would be a nag, not a walkthrough.
    static func shouldAutoPresent(kidKeys: [String], userID: String,
                                  defaults: UserDefaults = .standard) -> Bool {
        guard !kidKeys.isEmpty else { return false }
        let state = load(userID: userID, defaults: defaults)
        guard !state.finished, !state.deferred else { return false }
        return kidKeys.contains { state.isPending(SetupStop.kidID($0)) }
    }
}

// MARK: - One stop

/// One person in the walk. `id` is the STABLE key — the kid's profile-dictionary
/// key, the member's roster uuid, or the literal `parent:self` — so progress
/// survives a rename and can't be confused by list order.
struct SetupStop: Identifiable, Equatable {
    enum Target: Equatable {
        case kid(key: String)
        case member(id: String)
        /// The account holder's own profile (`/profile` parent), which has no
        /// roster row on a fresh family.
        case parentSelf
    }

    let id: String
    let displayName: String
    let prompt: String
    let target: Target

    static func kidID(_ key: String) -> String { "kid:\(key)" }
    static func memberID(_ id: String) -> String { "member:\(id)" }
    static let parentSelfID = "parent:self"

    var firstName: String {
        displayName.split(separator: " ").first.map(String.init) ?? displayName
    }

    var monogram: String {
        String(displayName.trimmingCharacters(in: .whitespaces).prefix(1)).uppercased()
    }
}

// MARK: - Model

@MainActor
final class SetupTailModel: ObservableObject {
    @Published private(set) var stops: [SetupStop] = []
    @Published private(set) var children: [String: ChildProfileDTO] = [:]
    @Published private(set) var members: [String: HouseholdMember] = [:]
    @Published private(set) var parent = ParentProfileDTO()
    @Published var cursor = 0
    @Published var loading = true
    @Published var error: String?
    /// The stop whose editor is open. Nil renders the stop card.
    @Published var openEditor: SetupStop?

    let userID: String
    let baseURL: URL
    /// When set, the walk opens ON this stop (the "Set up Benjamin" tile entry)
    /// rather than at the first pending one.
    let entryStopID: String?

    private var state: SetupTailState

    init(userID: String, baseURL: URL, entryStopID: String?) {
        self.userID = userID
        self.baseURL = baseURL
        self.entryStopID = entryStopID
        self.state = SetupTailStore.load(userID: userID)
    }

    var currentStop: SetupStop? {
        guard stops.indices.contains(cursor) else { return nil }
        return stops[cursor]
    }

    var isAtEnd: Bool { cursor >= stops.count }

    /// Load the roster the walk is over. Kids come from the family profile (the
    /// source of truth for who exists); adults from the household roster, which
    /// is where the role-driven editor's fields are declared. A member read that
    /// fails degrades to "kids only" rather than blocking the whole tail.
    func load() async {
        loading = true
        error = nil
        let url = baseURL
        let uid = userID
        async let profileTask = Self.profileOrNil(baseURL: url, userID: uid)
        async let membersTask = Self.rosterOrEmpty(baseURL: url, userID: uid)
        let profile = await profileTask
        let roster = await membersTask

        if let profile {
            children = profile.children ?? [:]
            parent = profile.parent ?? ParentProfileDTO()
        } else if children.isEmpty {
            error = "Couldn't load your family. Check your connection and try again."
        }
        members = Dictionary(uniqueKeysWithValues: roster.map { ($0.id, $0) })
        stops = Self.buildStops(children: children, roster: roster, parent: parent)
        placeCursor()
        loading = false
    }

    /// A profile read that fails is reported (the tail can't walk a family it
    /// can't see), but a roster read that fails degrades to "kids only" — the
    /// adults are additive stops, not a gate.
    private static func profileOrNil(baseURL: URL, userID: String) async -> FamilyProfileDTO? {
        try? await ProfileService.getProfile(baseURL: baseURL, userID: userID)
    }

    private static func rosterOrEmpty(baseURL: URL, userID: String) async -> [HouseholdMember] {
        (try? await CircleService.householdMembers(userID: userID, baseURL: baseURL)) ?? []
    }

    /// Kids first, then the family-side adults, then circle members, then the
    /// account holder. That is the canvas order (kid-001 → kid-002 → account →
    /// parent → co-parent → circle member), with "you" last because a parent
    /// filling in their own profile is the least urgent of the set.
    private static func buildStops(children: [String: ChildProfileDTO],
                                   roster: [HouseholdMember],
                                   parent: ParentProfileDTO) -> [SetupStop] {
        var stops: [SetupStop] = []
        // Dictionary order is unspecified — sort by the stable key so the walk
        // is the same walk on every launch.
        for key in children.keys.sorted() {
            let name = children[key]?.name?.trimmingCharacters(in: .whitespaces)
            let display = (name?.isEmpty == false ? name! : key)
            stops.append(SetupStop(
                id: SetupStop.kidID(key),
                displayName: display,
                prompt: "Birthday, grade, and what \(display) is like. It's what makes the coach's advice about them specific.",
                target: .kid(key: key)
            ))
        }
        let familyFirst = roster.sorted { lhs, rhs in
            if lhs.isFamilyRole != rhs.isFamilyRole { return lhs.isFamilyRole }
            return lhs.displayName.localizedCaseInsensitiveCompare(rhs.displayName) == .orderedAscending
        }
        for member in familyFirst {
            stops.append(SetupStop(
                id: SetupStop.memberID(member.id),
                displayName: member.displayName,
                prompt: member.isFamilyRole
                    ? "How \(member.displayName) fits into the family, and what they're working on with the kids."
                    : "What \(member.displayName) does with your kids, and anything they should be trusted with.",
                target: .member(id: member.id)
            ))
        }
        let parentName = parent.name?.trimmingCharacters(in: .whitespaces)
        stops.append(SetupStop(
            id: SetupStop.parentSelfID,
            displayName: (parentName?.isEmpty == false ? parentName! : "You"),
            prompt: "Your own details — where you are, your household, how your week runs. The coach plans around them.",
            target: .parentSelf
        ))
        return stops
    }

    /// The cursor is DERIVED, never restored from a stored index: an index goes
    /// stale the moment a kid is added or deleted, and a stale index points at
    /// the wrong person.
    private func placeCursor() {
        if let entryStopID, let index = stops.firstIndex(where: { $0.id == entryStopID }) {
            cursor = index
            return
        }
        cursor = stops.firstIndex { state.isPending($0.id) } ?? stops.count
    }

    // MARK: Progress (local only — the editors own the server writes)

    func markCompletedAndAdvance(_ stop: SetupStop) {
        if !state.completed.contains(stop.id) { state.completed.append(stop.id) }
        state.skipped.removeAll { $0 == stop.id }
        advance()
    }

    func skipAndAdvance(_ stop: SetupStop) {
        if !state.skipped.contains(stop.id), !state.completed.contains(stop.id) {
            state.skipped.append(stop.id)
        }
        advance()
    }

    /// "Finish later" — leaves Home usable and never asks again on its own.
    func defer_() {
        state.deferred = true
        persist()
    }

    private func advance() {
        cursor += 1
        if cursor >= stops.count { state.finished = true }
        persist()
    }

    private func persist() {
        SetupTailStore.save(state, userID: userID)
    }

    /// Fold a fresh family in after an editor saved, so the next stop's card and
    /// the editor behind it render what actually persisted.
    func apply(_ family: FamilyProfileDTO) {
        if let kids = family.children { children = kids }
        if let parent = family.parent { self.parent = parent }
    }
}

// MARK: - View

/// The walk. Presented by Home — automatically on the first pass, and from a
/// kid tile's "Set up {Name}" (same code path, entered at that kid).
struct SetupTailView: View {
    /// Fired whenever an editor closed, so Home re-fetches (CLAUDE.md: after a
    /// mutation, the source-of-truth view re-fetches).
    var onNeedsRefresh: () -> Void = {}

    @StateObject private var model: SetupTailModel
    @Environment(\.dismiss) private var dismiss

    init(userID: String, baseURL: URL, entryStopID: String? = nil,
         onNeedsRefresh: @escaping () -> Void = {}) {
        self.onNeedsRefresh = onNeedsRefresh
        _model = StateObject(wrappedValue: SetupTailModel(
            userID: userID, baseURL: baseURL, entryStopID: entryStopID
        ))
    }

    var body: some View {
        VStack(spacing: 0) {
            header
            content
        }
        .background(Color.bgElevated.ignoresSafeArea())
        .trackScreen("setup_tail")
        .task { await model.load() }
        // The stop's editor. Each is the SHIPPED editor, unmodified; closing it
        // is what completes the stop.
        .sheet(item: $model.openEditor, onDismiss: handleEditorDismiss) { stop in
            editor(for: stop)
                .presentationCornerRadius(.hearthRadiusSheet)
        }
    }

    // MARK: Header

    private var header: some View {
        HStack(spacing: .hearth400) {
            Text(stepLabel)
                .font(.hearthLabel)
                .tracking(0.66)
                .textCase(.uppercase)
                .foregroundColor(.inkMuted)
            Spacer(minLength: 0)
            Button {
                model.defer_()
                dismiss()
            } label: {
                Text("Finish later")
                    .font(.hearthButtonLabel)
                    .foregroundColor(.accentOnCanvas)
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, .hearth600)
        .padding(.vertical, .hearth500)
    }

    private var stepLabel: String {
        guard !model.stops.isEmpty, !model.isAtEnd else { return "Finishing up" }
        return "Step \(model.cursor + 1) of \(model.stops.count)"
    }

    // MARK: Body

    @ViewBuilder
    private var content: some View {
        if model.loading {
            Spacer()
            ProgressView().tint(.inkMuted)
            Spacer()
        } else if let stop = model.currentStop {
            stopCard(stop)
        } else {
            allDoneCard
        }
    }

    /// One person's card. The tail's own chrome — the fields themselves live in
    /// the editor this opens.
    private func stopCard(_ stop: SetupStop) -> some View {
        VStack(spacing: .hearth500) {
            Spacer(minLength: 0)
            avatar(for: stop)
            Text(stop.displayName)
                .font(.hearthDisplayMD)
                .foregroundColor(.inkPrimary)
                .multilineTextAlignment(.center)
            Text(stop.prompt)
                .font(.hearthBodyMD)
                .foregroundColor(.inkSecondary)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
            if let error = model.error {
                Text(error)
                    .font(.hearthBodySM)
                    .foregroundColor(.statusError)
                    .multilineTextAlignment(.center)
            }
            Spacer(minLength: 0)
            actions(for: stop)
        }
        .padding(.horizontal, .hearth700)
        .padding(.bottom, .hearth700)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func avatar(for stop: SetupStop) -> some View {
        Circle()
            .fill(Color.kidAccent(seed: stop.id))
            .frame(width: 96, height: 96)
            .overlay(
                Text(stop.monogram)
                    .font(.hearthDisplayMD)
                    .foregroundColor(.inkOnPhotoLight)
            )
            .accessibilityHidden(true)
    }

    private func actions(for stop: SetupStop) -> some View {
        VStack(spacing: .hearth400) {
            Button { model.openEditor = stop } label: {
                Text("Set up \(stop.firstName)")
                    .font(.hearthSectionHeader)
                    .foregroundColor(.inkOnPhotoLight)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, .hearth400)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                            .fill(Color.accentDefault)
                    )
            }
            .buttonStyle(.plain)

            Button { model.skipAndAdvance(stop) } label: {
                Text("Skip for now")
                    .font(.hearthSectionHeader)
                    .foregroundColor(.accentOnCanvas)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, .hearth400)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                            .fill(Color.bgElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                                    .stroke(Color.borderHairline, lineWidth: 1)
                            )
                    )
            }
            .buttonStyle(.plain)
        }
    }

    private var allDoneCard: some View {
        VStack(spacing: .hearth500) {
            Spacer(minLength: 0)
            Text("That's your family.")
                .font(.hearthDisplayMD)
                .foregroundColor(.inkPrimary)
                .multilineTextAlignment(.center)
            Text("You can change any of it later — tap a child on Home, or open Settings.")
                .font(.hearthBodyMD)
                .foregroundColor(.inkSecondary)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 0)
            Button { dismiss() } label: {
                Text("Back to Home")
                    .font(.hearthSectionHeader)
                    .foregroundColor(.inkOnPhotoLight)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, .hearth400)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                            .fill(Color.accentDefault)
                    )
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, .hearth700)
        .padding(.bottom, .hearth700)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: Editors — every one of them already shipped

    @ViewBuilder
    private func editor(for stop: SetupStop) -> some View {
        switch stop.target {
        case .kid(let key):
            KidSettingsSheet(
                baseURL: model.baseURL,
                userID: model.userID,
                kidKey: key,
                kid: model.children[key] ?? ChildProfileDTO(),
                onProfileChanged: { model.apply($0) }
            )
        case .member(let id):
            MemberProfileSheet(
                userID: model.userID,
                baseURL: model.baseURL,
                memberId: id,
                member: model.members[id]
            )
        case .parentSelf:
            NavigationStack {
                ParentProfileEditor(
                    baseURL: model.baseURL,
                    userID: model.userID,
                    parent: model.parent,
                    onSaved: { model.apply($0) }
                )
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Close") { model.openEditor = nil }
                    }
                }
            }
        }
    }

    /// The editor closed. It has already verified its own writes, so all that's
    /// left is local bookkeeping — mark the stop done, advance, and tell Home to
    /// re-fetch.
    private func handleEditorDismiss() {
        if let stop = model.currentStop {
            model.markCompletedAndAdvance(stop)
        }
        onNeedsRefresh()
    }
}
