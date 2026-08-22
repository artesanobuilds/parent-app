import SwiftUI

/// Identifies the kid whose settings sheet is open. Wraps the STABLE profile
/// key (the server's dictionary key) — never a list index, never the editable
/// display name.
struct KidSettingsTarget: Identifiable, Hashable {
    let id: String
}

/// `YOUR KIDS` — Heisman Onboarding-9 (Figma frame `42:8322`, nodes
/// `29:2820`–`29:2832`): near-black tiles with the kid's name in the display
/// serif and an ellipsis menu in the tile's top-right corner. Tap the tile to
/// read what they've been up to; everything else lives behind the `•••`.
///
/// The `locked` status is a SAFETY surface: a crisis lock paused that kid's
/// companion, and the tile must route to the parent review + reactivate
/// dialog, never anywhere else. See `debugging_crisis_lock_companion`.
struct KidsHomeSection: View {
    let userID: String
    let baseURL: URL
    /// Bumped by HomeView (from `\.homeRefreshToken`) whenever the parent
    /// returns to the Home tab; a change re-runs the refresh so profile
    /// edits/adds/deletes show without an app relaunch.
    var refreshToken: Int = 0
    /// The family's children keyed by their PROFILE KEY. HomeView already
    /// fetches the profile, so the tiles don't each re-fetch it; the settings
    /// sheet needs the whole DTO.
    var children: [String: ChildProfileDTO] = [:]
    /// Fired with the fresh family after any mutation inside the settings sheet.
    var onProfileChanged: (FamilyProfileDTO) -> Void = { _ in }
    /// Fired when the settings sheet closes, so the presenter can bump its
    /// refresh token (re-fetch-after-mutation, CLAUDE.md).
    var onNeedsRefresh: () -> Void = {}
    /// Opens the coaching conversation. Nil hides the sheet's `View all`
    /// button rather than rendering a dead one.
    var onOpenCoach: (() -> Void)?
    /// Fired whenever the count of kids with an ACTIVE-or-LOCKED companion
    /// changes — "has anyone ever been introduced". Kept for presenters that
    /// branch on it; a locked companion counts as introduced so a crisis
    /// pause never reads as first-run.
    var onCompanionPresenceChanged: (Bool) -> Void = { _ in }
    /// Enter the post-dashboard setup tail AT this kid (`SetupTailView`),
    /// keyed by the kid's STABLE profile key — reachable from the tile's
    /// ellipsis menu. Same code path as the automatic walk, not a parallel
    /// one. Nil hides the menu item rather than rendering a dead one.
    var onEnterSetup: ((String) -> Void)?

    @StateObject private var vm: KidsHomeViewModel
    @Environment(\.triggerKidHandoff) private var triggerKidHandoff
    // Persisted flag so HomeView's header can conditionally show the
    // "Hand to kid" button only when at least one companion exists.
    @AppStorage("has_kid_companions") private var hasKidCompanions: Bool = false
    // A crisis-locked companion the parent tapped to review + reactivate.
    @State private var reactivateTarget: KidsHomeViewModel.KidEntry?
    // Pushed from a tile's ••• menu (a Menu can't host a NavigationLink value).
    @State private var reviewTarget: String?
    // The kid whose settings sheet is open.
    @State private var settingsTarget: KidSettingsTarget?

    init(userID: String, baseURL: URL, refreshToken: Int = 0,
         children: [String: ChildProfileDTO] = [:],
         onProfileChanged: @escaping (FamilyProfileDTO) -> Void = { _ in },
         onNeedsRefresh: @escaping () -> Void = {},
         onOpenCoach: (() -> Void)? = nil,
         onCompanionPresenceChanged: @escaping (Bool) -> Void = { _ in },
         onEnterSetup: ((String) -> Void)? = nil) {
        self.onEnterSetup = onEnterSetup
        self.userID = userID
        self.baseURL = baseURL
        self.refreshToken = refreshToken
        self.children = children
        self.onProfileChanged = onProfileChanged
        self.onNeedsRefresh = onNeedsRefresh
        self.onOpenCoach = onOpenCoach
        self.onCompanionPresenceChanged = onCompanionPresenceChanged
        _vm = StateObject(wrappedValue: KidsHomeViewModel(userID: userID, baseURL: baseURL))
    }

    // MARK: Body
    //
    // Kept deliberately thin: the section stack, the dialog and the sheet each
    // live in their own member. A single inline chain here type-checks slowly
    // enough to fail the build outright.

    var body: some View {
        sectionStack
            .navigationDestination(for: KidNavigation.self) { destination in
                switch destination {
                case .review(let kidName):
                    reviewDestination(kidName)
                }
            }
            .navigationDestination(item: $reviewTarget) { kidName in
                reviewDestination(kidName)
            }
            .task(id: refreshToken) { await load() }
            .onChange(of: activeCompanionCount) { _, activeCount in
                hasKidCompanions = activeCount > 0
            }
            .onChange(of: introducedCompanionCount) { _, count in
                onCompanionPresenceChanged(count > 0)
            }
            .confirmationDialog(
                reactivateTitle,
                isPresented: reactivateIsPresented,
                titleVisibility: .visible,
                actions: { reactivateActions },
                message: { reactivateMessage }
            )
            // Keyed by the stable profile key, never a list index — deleting
            // the first kid must not re-target the sheet at another child.
            .sheet(item: $settingsTarget, onDismiss: onNeedsRefresh) { target in
                settingsSheet(for: target)
            }
    }

    /// Measured `29:2820`: the section sits BARE on the canvas (no card
    /// ground), py 20, header→tiles gap 16, tiles centered.
    private var sectionStack: some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            HStack {
                // "YOUR KIDS" — Inter 800 16/22 in ink/primary (`29:2821`).
                Text("Your kids")
                    .font(.hearthSectionHeader)
                    .textCase(.uppercase)
                    .foregroundColor(.inkPrimary)
                if vm.isLoading {
                    ProgressView().tint(.inkMuted).scaleEffect(0.7)
                }
                Spacer(minLength: 0)
            }

            // Three states, not two. "No kids" is only true once a fetch has
            // actually SUCCEEDED — otherwise an offline moment reads as a
            // family with no children, the scariest possible way to fail.
            if vm.kids.isEmpty && !vm.isLoading && !vm.hasLoadedOnce {
                loadFailedState
            } else if vm.kids.isEmpty && !vm.isLoading {
                emptyState
            } else {
                // Two-up tiles, gap 12, 168×153 in the 440pt frame — the grid
                // sets the width per device; the height is the frame's own.
                LazyVGrid(
                    columns: [GridItem(.flexible(), spacing: .hearth400),
                              GridItem(.flexible(), spacing: .hearth400)],
                    spacing: .hearth400
                ) {
                    ForEach(vm.kids) { kid in
                        kidTile(for: kid)
                    }
                }
            }
        }
        .padding(.vertical, .hearth600)
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    /// Shown when we have never successfully read the roster — offline, an
    /// expired token, a 500. It must NOT read like "you have no kids": a parent
    /// seeing their children vanish from Home has no way to tell a display
    /// problem from lost data, and this app has actually lost a family before.
    private var loadFailedState: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text("Couldn't load your kids")
                .font(.hearthBodyMD.weight(.semibold))
                .foregroundColor(.inkPrimary)
            Text("They're safe — this is a connection problem, not missing data.")
                .font(.hearthBodySM)
                .foregroundColor(.inkSecondary)
                .fixedSize(horizontal: false, vertical: true)
            Button("Try again") {
                Task { await load() }
            }
            .font(.hearthBodySMBold)
            .foregroundColor(.accentOnCanvas)
            .padding(.top, 2)
        }
        .padding(.hearth500)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
        .hearthCardElevation()
    }

    private var emptyState: some View {
        Text("Add a kid in Settings to set up their companion.")
            .font(.hearthBodyMD)
            .foregroundColor(.inkMuted)
            .padding(.hearth500)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
            .hearthCardElevation()
    }

    // MARK: Tile

    /// One kid's tile (measured `29:2823`): 168×153, r=12, 0.5px
    /// `accent/default` stroke, near-black ground — the frame paints an
    /// OPAQUE `ink/primary` `#151412` layer over the kid photo, so the tile
    /// renders as a solid black block, name in Fraunces SemiBold 28/32
    /// centered on the tile's floor in `#F5F3EF` (`inkOnCard`, exact), the
    /// `•••` glyph top-right. The frame's `#151412` has no primitive of its
    /// own; `inkPrimary` (#1A1A1A) is the closest existing token — gap noted.
    ///
    /// The tile's tap target is the safety-critical part of this file: a
    /// crisis-LOCKED companion goes to the reactivate confirmation, NEVER
    /// anywhere else. Any future restyle must keep that branch.
    private func kidTile(for kid: KidsHomeViewModel.KidEntry) -> some View {
        ZStack(alignment: .topTrailing) {
            tileTapTarget(for: kid)
            // ••• — the frame's own affordance (`29:2826`, 19×4), exported as
            // a single template SVG. Hosts every per-kid action.
            Menu {
                kidMenuItems(for: kid)
            } label: {
                Image("HomeIcon-kidEllipsis")
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 19, height: 4)
                    .foregroundColor(.inkOnCard)
                    // Grow the hit target well past the 19×4 glyph.
                    .padding(.hearth400)
                    .contentShape(Rectangle())
            }
            .accessibilityLabel("\(kid.kidName)'s options")
        }
        .frame(maxWidth: .infinity, minHeight: 153)
        .background(Color.inkPrimary)
        .overlay(
            RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                .strokeBorder(Color.accentDefault, lineWidth: 0.5)
        )
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous))
    }

    @ViewBuilder
    private func tileTapTarget(for kid: KidsHomeViewModel.KidEntry) -> some View {
        let body = KidTileBody(kid: kid)
        if kid.status == .locked {
            Button { reactivateTarget = kid } label: { body }
                .buttonStyle(.plain)
        } else {
            NavigationLink(value: KidNavigation.review(kidName: kid.kidName)) { body }
                .buttonStyle(.plain)
        }
    }

    /// The per-kid actions behind the tile's `•••`. The crisis-lock
    /// reactivate path is safety-critical; kid settings and the review letter
    /// are reachable from nowhere else on Home.
    @ViewBuilder
    private func kidMenuItems(for kid: KidsHomeViewModel.KidEntry) -> some View {
        Button { settingsTarget = KidSettingsTarget(id: kid.kidKey) } label: {
            Label("\(kid.kidName)'s settings", systemImage: "slider.horizontal.3")
        }
        Button { reviewTarget = kid.kidName } label: {
            Label("See what they've been up to", systemImage: "text.book.closed")
        }
        // Enter (or re-enter) the onboarding tail at this kid.
        if let onEnterSetup {
            Button { onEnterSetup(kid.kidKey) } label: {
                Label(kid.status == .missing
                      ? "Set up \(kid.kidName)"
                      : "Finish setting up \(kid.kidName)", systemImage: "checklist")
            }
        }
        if kid.status == .active {
            Button { triggerKidHandoff() } label: {
                Label("Hand to \(kid.kidName)", systemImage: "hand.wave")
            }
        }
        if kid.status == .locked {
            Button { reactivateTarget = kid } label: {
                Label("Review & reactivate", systemImage: "exclamationmark.shield")
            }
        }
    }

    // MARK: Destinations, dialog, sheet

    private func reviewDestination(_ kidName: String) -> some View {
        ReviewLetterView(userID: userID, kidName: kidName, baseURL: baseURL)
            .navigationBarTitleDisplayMode(.inline)
    }

    private func settingsSheet(for target: KidSettingsTarget) -> some View {
        KidSettingsSheet(
            baseURL: baseURL,
            userID: userID,
            kidKey: target.id,
            kid: children[target.id] ?? ChildProfileDTO(),
            onViewAllCoach: viewAllCoachAction,
            onProfileChanged: onProfileChanged
        )
    }

    /// The sheet doesn't dismiss itself, and two sheets can't hand over
    /// instantly: close this one, let the presentation settle, then open the
    /// coach. Nil when the presenter can't reach the coach, which hides the
    /// sheet's button instead of leaving a dead one.
    private var viewAllCoachAction: (() -> Void)? {
        guard let onOpenCoach else { return nil }
        return {
            settingsTarget = nil
            Task { @MainActor in
                try? await Task.sleep(nanoseconds: 350_000_000)
                onOpenCoach()
            }
        }
    }

    private var reactivateTitle: String {
        guard let name = reactivateTarget?.kidName else { return "" }
        return "\(name)'s companion is paused for safety"
    }

    private var reactivateIsPresented: Binding<Bool> {
        Binding(
            get: { reactivateTarget != nil },
            set: { if !$0 { reactivateTarget = nil } }
        )
    }

    @ViewBuilder
    private var reactivateActions: some View {
        if let agentID = reactivateTarget?.agentID {
            Button("Reactivate companion") {
                reactivateTarget = nil
                Task { await vm.reactivate(agentID: agentID) }
            }
            Button("Cancel", role: .cancel) { reactivateTarget = nil }
        }
    }

    private var reactivateMessage: some View {
        Text("A message was flagged by the safety filter, so this companion was "
             + "paused. Review your child's recent chat if you're unsure. "
             + "Reactivating clears the pause and lets them talk again.")
    }

    // MARK: Loading

    private var activeCompanionCount: Int {
        vm.kids.filter { $0.status == .active }.count
    }

    /// Kids who have EVER been introduced — active or crisis-locked. Locked
    /// counts here (unlike `activeCompanionCount`): a paused companion was
    /// introduced and then safety-paused, not "never set up".
    private var introducedCompanionCount: Int {
        vm.kids.filter { $0.status == .active || $0.status == .locked }.count
    }

    private func load() async {
        await vm.refresh()
        // Surface ACTIVE-companion count to the flag — draft/missing configs
        // don't count: the Hand-to-kid handoff opens a picker that has zero
        // pickable options if no kid is enabled, so we must not show the CTA.
        hasKidCompanions = activeCompanionCount > 0
        onCompanionPresenceChanged(introducedCompanionCount > 0)
    }
}

// MARK: - Tile body

/// The tappable face of a kid tile: the frame draws ONLY the name, in the
/// display serif, centered on the tile's floor (`29:2827`: Fraunces SemiBold
/// 28/32 `#F5F3EF`, tile content justify-between with ~17.7pt padding).
///
/// EXCEPTION the frame doesn't draw: a crisis-LOCKED kid keeps a one-line
/// "Paused for safety" caption. That state is a safety surface — hiding it
/// entirely would leave the parent no visible signal that a review is
/// waiting. Deliberate deviation, kept minimal.
private struct KidTileBody: View {
    let kid: KidsHomeViewModel.KidEntry

    var body: some View {
        VStack(spacing: 2) {
            Spacer(minLength: 0)
            Text(kid.kidName)
                .font(.custom(HearthFontFamily.displaySerif, fixedSize: 28).weight(.semibold))
                .foregroundColor(.inkOnCard)
                .lineLimit(1)
                .minimumScaleFactor(0.7)
            if kid.status == .locked {
                Text("Paused for safety — tap to review")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkOnCard.opacity(0.9))
                    .lineLimit(2)
                    .multilineTextAlignment(.center)
            }
        }
        // The frame's 17.715pt content inset (`29:2824`), its own odd value.
        .padding(17.7)
        .frame(maxWidth: .infinity, minHeight: 153)
        .contentShape(Rectangle())
    }
}

enum KidNavigation: Hashable {
    case review(kidName: String)
}

// MARK: - View model

@MainActor
final class KidsHomeViewModel: ObservableObject {

    enum Status { case active, draft, missing, locked }

    struct KidEntry: Identifiable, Equatable {
        /// The profile dictionary key — stable across renames of the display
        /// name, and what the settings sheet and PATCH endpoints address.
        let kidKey: String
        let kidName: String
        let agentID: String?     // for revive; nil when there's no config yet
        let invariants: KidAgentInvariants
        let summary: String
        let status: Status
        /// The day of the kid's most recent recap, when there is one.
        let lastActivity: Date?
        /// That recap's headline ("Talked about sharing for 12 minutes").
        let headline: String?

        var id: String { kidKey }

        /// The kid's accent color. Seeded on the kid-agent config id where one
        /// exists so a rename can't recolor surfaces; the profile key is the
        /// fallback for kids with no config yet. Must stay identical to
        /// `KidSettingsSheet`'s seed or a tile and its sheet disagree on color.
        var accent: Color { .kidAccent(seed: agentID ?? kidKey) }

        /// "with Nova, yesterday" — the companion, plus when they last talked.
        var companionLine: String {
            guard status != .missing else { return "no companion yet" }
            let companion = invariants.agentDisplayName.isEmpty
                ? "their companion" : invariants.agentDisplayName
            guard let lastActivity else { return "with \(companion)" }
            return "with \(companion), \(HomeWhen.pastPhrase(lastActivity))"
        }

        /// "Talked about sharing yesterday" / "Hasn't chatted in a few days".
        var statusLine: String {
            switch status {
            case .locked:
                return "Paused for safety — tap to review"
            case .missing:
                return summary
            case .draft, .active:
                return chatStatusLine
            }
        }

        private var chatStatusLine: String {
            if let lastActivity {
                let days = HomeWhen.wholeDaysBetween(lastActivity, and: Date())
                if days >= 3 { return "Hasn't chatted in a few days" }
                if let headline, !headline.isEmpty { return headline }
                return "Chatted \(HomeWhen.pastPhrase(lastActivity))"
            }
            return status == .draft ? "Not chatting yet — introduce them"
                                    : "Hasn't chatted yet"
        }
    }

    let userID: String
    let baseURL: URL
    private let service: KidAgentService

    @Published var kids: [KidEntry] = []
    @Published var isLoading = false
    @Published var error: String?

    init(userID: String, baseURL: URL) {
        self.userID = userID
        self.baseURL = baseURL
        self.service = KidAgentService(baseURL: baseURL, userID: userID)
    }

    /// True once a refresh has SUCCEEDED at least once. The section uses it to
    /// tell "this family genuinely has no kids" apart from "the fetch failed",
    /// which previously rendered identically — an empty state.
    @Published var hasLoadedOnce = false

    /// The in-flight refresh. Awaited by a second caller instead of dropped, so
    /// returning to the Home tab mid-fetch can't cancel the load and leave the
    /// section empty.
    private var inFlight: Task<Void, Never>?

    /// Coalesces overlapping refreshes. `.task(id:)` cancels its predecessor
    /// when the id changes — switching tabs bumps the token, so the first
    /// refresh was being CANCELLED partway and the replacement `guard
    /// !isLoading` bailed out of, leaving `kids` empty with children on the
    /// server. Running the work in an unstructured Task detaches it from the
    /// view's lifetime; a concurrent caller awaits that same Task.
    func refresh() async {
        if let inFlight {
            await inFlight.value
            return
        }
        let task = Task { await performRefresh() }
        inFlight = task
        await task.value
        inFlight = nil
    }

    private func performRefresh() async {
        isLoading = true
        defer { isLoading = false }
        do {
            // Family profile is the source of truth for who gets a tile.
            // Configs only fill in display name and status — they're absent
            // for fresh families and during pre-consent state.
            let svc = service
            let url = baseURL
            let uid = userID
            async let familyTask = svc.familyChildren()
            async let configsTask = Self.listOrEmpty(svc)
            async let summariesTask = Self.summariesOrEmpty(baseURL: url, userID: uid)
            let (family, configs) = try await (familyTask, configsTask)
            let latestSummary = HomeDashboardService.latestSummaryByKid(await summariesTask)

            let configByName = Dictionary(grouping: configs, by: { $0.kidName })
                .compactMapValues(\.first)

            self.kids = family.map { child in
                Self.entry(for: child,
                           config: configByName[child.name],
                           recap: latestSummary[child.name])
            }
            self.error = nil
            self.hasLoadedOnce = true
        } catch {
            // Do NOT clear `kids`. A failed re-fetch used to leave the previous
            // list in place but, combined with the empty-state branch keying off
            // `kids.isEmpty`, any failure BEFORE the first success rendered as
            // "you have no kids" — silently, because this error was only ever
            // printed. Keep whatever we last knew and let the view say so.
            self.error = error.localizedDescription
            print("[KidsHome] refresh failed: \(error)")
        }
    }

    private static func entry(
        for child: KidAgentService.FamilyChild,
        config: KidAgentConfig?,
        recap: KidDailySummary?
    ) -> KidEntry {
        if let cfg = config {
            // A crisis lock takes priority over enabled: the companion was
            // paused for safety and needs a parent review, NOT a re-setup.
            let locked = cfg.crisisLocked ?? false
            let status: Status = locked ? .locked : (cfg.enabled ? .active : .draft)
            return KidEntry(
                kidKey: child.name,
                kidName: cfg.kidName,
                agentID: cfg.id,
                invariants: cfg.invariants,
                summary: locked ? "Paused for safety — tap to review"
                                : cfg.invariants.interestsSummary,
                status: status,
                lastActivity: recap?.day,
                headline: recap?.headline
            )
        }
        let summary: String
        if let age = child.age {
            summary = "\(Int(age)) years old · tap to introduce"
        } else {
            summary = "tap to introduce"
        }
        return KidEntry(
            kidKey: child.name,
            kidName: child.name,
            agentID: nil,
            invariants: .empty,
            summary: summary,
            status: .missing,
            lastActivity: recap?.day,
            headline: recap?.headline
        )
    }

    /// Parent-reviewed reactivation of a crisis-locked companion: clears the lock,
    /// re-enables, and refreshes so the tile flips back to Active.
    func reactivate(agentID: String) async {
        do {
            try await service.revive(agentID: agentID)
            await refresh()
        } catch {
            self.error = "Couldn't reactivate. Check your connection and try again."
        }
    }

    /// Wrap `service.list()` so consent-required and other errors don't
    /// mask the family-profile fetch.
    private static func listOrEmpty(_ service: KidAgentService) async -> [KidAgentConfig] {
        do { return try await service.list() }
        catch KidAgentServiceError.consentRequired { return [] }
        catch { return [] }
    }

    /// Recaps are decoration, never a gate: any failure just leaves the tiles
    /// silent about chat history.
    private static func summariesOrEmpty(baseURL: URL, userID: String) async -> [KidDailySummary] {
        (try? await HomeDashboardService.dailySummaries(baseURL: baseURL, userID: userID)) ?? []
    }
}
