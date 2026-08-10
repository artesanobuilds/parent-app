import SwiftUI

/// Identifies the kid whose settings sheet is open. Wraps the STABLE profile
/// key (the server's dictionary key) — never a list index, never the editable
/// display name.
struct KidSettingsTarget: Identifiable, Hashable {
    let id: String
}

/// `YOUR KIDS` — one card per kid in the family profile, each in that kid's own
/// accent. Tap the card to read what they've been up to; the CTA hands the
/// phone over; `•••` opens the kid's settings sheet.
///
/// The `locked` status is a SAFETY surface: a crisis lock paused that kid's
/// companion, and the card must route to the parent review + reactivate dialog,
/// never to the intro/setup screen. See `debugging_crisis_lock_companion`.
struct KidsHomeSection: View {
    let userID: String
    let baseURL: URL
    /// Bumped by HomeView (from `\.homeRefreshToken`) whenever the parent
    /// returns to the Home tab; a change re-runs the refresh so profile
    /// edits/adds/deletes show without an app relaunch.
    var refreshToken: Int = 0
    /// The family's children keyed by their PROFILE KEY. HomeView already
    /// fetches the profile, so the cards don't each re-fetch it; the settings
    /// sheet needs the whole DTO, the card only needs `avatar_url`.
    var children: [String: ChildProfileDTO] = [:]
    /// Fired with the fresh family after any mutation inside the settings sheet.
    var onProfileChanged: (FamilyProfileDTO) -> Void = { _ in }
    /// Fired when the settings sheet closes, so the presenter can bump its
    /// refresh token (re-fetch-after-mutation, CLAUDE.md).
    var onNeedsRefresh: () -> Void = {}
    /// Opens the coaching conversation. Nil hides the sheet's `View all`
    /// button rather than rendering a dead one.
    var onOpenCoach: (() -> Void)?
    /// Optional prompt rendered under the "YOUR KIDS" header — HomeView's
    /// first-run dashboard state ("Help us get to know your kids a little
    /// more:"). Nil (the default) renders nothing, so every other caller is
    /// unaffected.
    var firstRunPrompt: String? = nil
    /// Fired whenever the count of kids with an ACTIVE-or-LOCKED companion
    /// changes — i.e. "has anyone ever been introduced", as opposed to
    /// `hasKidCompanions` below which is ACTIVE-only (the handoff picker
    /// needs an active companion, not merely an introduced-then-paused one).
    /// HomeView uses this to decide its first-run dashboard state; a locked
    /// companion must count as "introduced" so a crisis pause never flips the
    /// dashboard back into first-run copy.
    var onCompanionPresenceChanged: (Bool) -> Void = { _ in }
    /// True for first-run dashboard (Dashboard 1), passed from HomeView.
    var isFirstRun: Bool = false
    /// Enter the post-dashboard setup tail AT this kid (`SetupTailView`), keyed
    /// by the kid's STABLE profile key. This is what the design's "Set up
    /// {FirstName}" tile CTA does — the tile is the entry point into the
    /// onboarding tail, and it is the SAME code path the automatic walk uses,
    /// not a parallel one. Nil leaves the CTA on its pre-tail behaviour rather
    /// than rendering a dead button.
    var onEnterSetup: ((String) -> Void)?
    /// "+ Add another child" (Dashboard 1: full-width r=12, Inter w800 16, teal
    /// on white, below the tiles). Nil hides it.
    var onAddChild: (() -> Void)?

    @StateObject private var vm: KidsHomeViewModel
    @Environment(\.triggerKidHandoff) private var triggerKidHandoff
    // Persisted flag so HomeView's header can conditionally show the
    // "Hand to kid" button only when at least one companion exists.
    @AppStorage("has_kid_companions") private var hasKidCompanions: Bool = false
    // A crisis-locked companion the parent tapped to review + reactivate.
    @State private var reactivateTarget: KidsHomeViewModel.KidEntry?
    // Pushed from a card's ••• menu (a Menu can't host a NavigationLink value).
    @State private var reviewTarget: String?
    // The kid whose settings sheet is open.
    @State private var settingsTarget: KidSettingsTarget?

    init(userID: String, baseURL: URL, refreshToken: Int = 0,
         children: [String: ChildProfileDTO] = [:],
         onProfileChanged: @escaping (FamilyProfileDTO) -> Void = { _ in },
         onNeedsRefresh: @escaping () -> Void = {},
         onOpenCoach: (() -> Void)? = nil,
         firstRunPrompt: String? = nil,
         onCompanionPresenceChanged: @escaping (Bool) -> Void = { _ in },
         isFirstRun: Bool = false,
         onEnterSetup: ((String) -> Void)? = nil,
         onAddChild: (() -> Void)? = nil) {
        self.onEnterSetup = onEnterSetup
        self.onAddChild = onAddChild
        self.userID = userID
        self.baseURL = baseURL
        self.refreshToken = refreshToken
        self.children = children
        self.onProfileChanged = onProfileChanged
        self.onNeedsRefresh = onNeedsRefresh
        self.onOpenCoach = onOpenCoach
        self.firstRunPrompt = firstRunPrompt
        self.onCompanionPresenceChanged = onCompanionPresenceChanged
        self.isFirstRun = isFirstRun
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

    private var sectionStack: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            HStack {
                HomeSectionHeader(title: "Your kids")
                if vm.isLoading {
                    ProgressView().tint(.inkMuted).scaleEffect(0.7)
                }
            }

            // First-run dashboard state (HomeView decides when to pass this).
            if let firstRunPrompt, !vm.kids.isEmpty {
                Text(firstRunPrompt)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkSecondary)
                    .fixedSize(horizontal: false, vertical: true)
            }

            // Three states, not two. "No kids" is only true once a fetch has
            // actually SUCCEEDED — otherwise an offline moment or a failed
            // re-fetch on returning to the tab reads as a family with no
            // children, which is the scariest possible way to fail.
            if vm.kids.isEmpty && !vm.isLoading && !vm.hasLoadedOnce {
                loadFailedState
            } else if vm.kids.isEmpty && !vm.isLoading {
                emptyState
            } else {
                // Two-up photo tiles, per the design (168x153 in a 440pt frame).
                // Full-width rows were our own invention.
                LazyVGrid(
                    columns: [GridItem(.flexible(), spacing: .hearth400),
                              GridItem(.flexible(), spacing: .hearth400)],
                    spacing: .hearth400
                ) {
                    ForEach(vm.kids) { kid in
                        kidCard(for: kid)
                    }
                }
            }

            if let onAddChild {
                addChildButton(onAddChild)
            }
        }
        // YOUR KIDS sits in a rounded container on the canvas. Dashboard 1:
        // `#FFFFFF` r=28 pad 24. Dashboard 2: `#F5F3EF` r=28 pad 24/30.
        // Using 24 uniformly.
        .padding(.hearth700)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: .hearthRadiusSection, style: .continuous)
                .fill(isFirstRun ? Color.bgElevated : Color.bgCard)
        )
    }

    /// "+ Add another child" — Dashboard 1's full-width button under the tiles
    /// (measured: r=12, pad 12, `Inter w800 16`, teal label on white).
    ///
    /// Home had no reachable add-kid action before this; the only entry was
    /// Settings → Profile → "Add a kid". It presents that exact same
    /// `AddKidSheet`, so there is one add-a-kid write path, not two.
    private func addChildButton(_ action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text("+ Add another child")
                .font(.hearthSectionHeader)
                .foregroundColor(.accentOnCanvas)
                .frame(maxWidth: .infinity)
                .padding(.vertical, .hearth400)
                .background(
                    RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                        .fill(Color.bgElevated)
                )
        }
        .buttonStyle(.plain)
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
        Text(onAddChild == nil
             ? "Add a kid in Settings to set up their companion."
             : "Add your first child to set up their companion.")
            .font(.hearthBodyMD)
            .foregroundColor(.inkMuted)
            .padding(.hearth500)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
            .hearthCardElevation()
    }

    // MARK: Card

    /// One kid's card, in that kid's accent (beta-v1 spec: Dashboard 1/2).
    ///
    /// The card's tap target is the safety-critical part of this file: a
    /// crisis-LOCKED companion goes to the reactivate confirmation, NEVER to
    /// the intro/setup screen. Any future restyle must keep that branch.
    private func kidCard(for kid: KidsHomeViewModel.KidEntry) -> some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            cardTapTarget(for: kid)
            kidCTA(for: kid)
        }
        .padding(.hearth400)
        .frame(maxWidth: .infinity, minHeight: 153, alignment: .topLeading)
        .background(kidTileGround(for: kid))
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous))
        // The design's tile has no ••• affordance, but the kid-settings and
        // "what they've been up to" entries live nowhere else on Home. A
        // long-press keeps them reachable without adding chrome the design
        // doesn't have.
        .contextMenu { kidMenuItems(for: kid) }
        .accessibilityHint("Press and hold for \(kid.kidName)'s settings")
    }

    /// The kid's photo fills the tile; with no photo, a flat teal (`#1B7498`)
    /// does (beta-v1 spec: Dashboard 1 no-photo state is `#1B7498`, NOT the
    /// per-kid accent — the teal is the designed first-run state, not a
    /// placeholder). Either way the name and CTA sit ON the tile, so ink is
    /// `inkOnPhotoLight`.
    @ViewBuilder
    private func kidTileGround(for kid: KidsHomeViewModel.KidEntry) -> some View {
        if let url = children[kid.kidKey]?.avatarUrl, !url.isEmpty {
            KidTilePhoto(urlString: url, accent: kid.accent)
        } else {
            Color.accentDefault
        }
    }

    @ViewBuilder
    private func cardTapTarget(for kid: KidsHomeViewModel.KidEntry) -> some View {
        let body = KidCardBody(kid: kid, avatarURL: children[kid.kidKey]?.avatarUrl)
        if kid.status == .locked {
            Button { reactivateTarget = kid } label: { body }
                .buttonStyle(.plain)
        } else {
            NavigationLink(value: KidNavigation.review(kidName: kid.kidName)) { body }
                .buttonStyle(.plain)
        }
    }

    private func cardBorder(for kid: KidsHomeViewModel.KidEntry) -> some View {
        RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
            .stroke(kid.accent, lineWidth: 1.5)
    }

    /// Only an ACTIVE companion can actually receive a handoff (the picker has
    /// no options otherwise), so every other status gets the CTA that matches
    /// what the parent has to do next.
    @ViewBuilder
    private func kidCTA(for kid: KidsHomeViewModel.KidEntry) -> some View {
        switch kid.status {
        case .active:
            Button { triggerKidHandoff() } label: {
                tileCTALabel("Hand to \(kid.kidName)")
            }
        case .draft:
            NavigationLink(value: KidNavigation.review(kidName: kid.kidName)) {
                tileCTALabel("Introduce \(kid.kidName)")
            }
            .buttonStyle(.plain)
        case .missing:
            // The design's tile CTA. A kid with no companion config yet is
            // exactly the kid the onboarding tail exists to walk, so this is the
            // tail's re-entry point — same `SetupTailView` the automatic first
            // pass uses, entered at THIS kid by profile key. When the presenter
            // can't reach the tail we keep the shipped "introduce them"
            // destination rather than rendering a dead button.
            if let onEnterSetup {
                Button { onEnterSetup(kid.kidKey) } label: {
                    tileCTALabel("Set up \(kid.kidName)")
                }
                .buttonStyle(.plain)
            } else {
                NavigationLink(value: KidNavigation.review(kidName: kid.kidName)) {
                    tileCTALabel("Set up \(kid.kidName)")
                }
                .buttonStyle(.plain)
            }
        case .locked:
            Button { reactivateTarget = kid } label: { lockedCTALabel }
        }
    }

    private var lockedCTALabel: some View {
        Text("Review")
            .font(.hearthButtonLabel)
            .foregroundColor(.inkOnPhotoLight)
            .padding(.horizontal, .hearth400)
            .padding(.vertical, .hearth300)
            .background(Color.statusError)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusControl, style: .continuous))
    }

    /// The tile's single button, per the design ("Set up Benjamin").
    /// Dashboard 1 spec: Inter w800 13.35 (hearthButtonLabel rounds to 13pt).
    /// Compact because it lives inside a ~168pt-wide tile.
    private func tileCTALabel(_ title: String) -> some View {
        Text(title)
            .font(.hearthButtonLabel)
            .foregroundColor(.accentOnCanvas)
            .lineLimit(1)
            .minimumScaleFactor(0.75)
            .padding(.horizontal, .hearth400)
            .padding(.vertical, .hearth300)
            .frame(maxWidth: .infinity)
            .background(Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusControl, style: .continuous))
    }

    /// The per-kid actions, as `contextMenu` items on the tile.
    ///
    /// These were a visible ••• button in the card's corner. The design's tile
    /// has no such affordance, so they moved to a long-press — but they are NOT
    /// dropped: kid settings and the review letter are reachable from nowhere
    /// else on Home, and the crisis-lock reactivate path is safety-critical.
    @ViewBuilder
    private func kidMenuItems(for kid: KidsHomeViewModel.KidEntry) -> some View {
        Button { settingsTarget = KidSettingsTarget(id: kid.kidKey) } label: {
            Label("\(kid.kidName)'s settings", systemImage: "slider.horizontal.3")
        }
        Button { reviewTarget = kid.kidName } label: {
            Label("See what they've been up to", systemImage: "text.book.closed")
        }
        // Re-enter the onboarding tail at this kid, for a kid whose tile CTA is
        // no longer "Set up …" (they already have a companion) but whose profile
        // the parent skipped.
        if let onEnterSetup {
            Button { onEnterSetup(kid.kidKey) } label: {
                Label("Finish setting up \(kid.kidName)", systemImage: "checklist")
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
    /// introduced and then safety-paused, not "never set up", so it must not
    /// make HomeView think this is a first-run family again.
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

// MARK: - Card body

/// The tappable part of a kid card: photo, name, `with {companion}, {when}`,
/// and the status line.
private struct KidCardBody: View {
    let kid: KidsHomeViewModel.KidEntry
    var avatarURL: String?

    var body: some View {
        // Tile layout (design): the name in the display serif sits ON the photo,
        // with the companion status as a caption beneath it. Status is NOT in the
        // design's tile, but it is how a parent knows a companion still needs
        // introducing — dropping it would remove the section's whole purpose.
        VStack(alignment: .leading, spacing: 2) {
            nameRow
            Text(kid.statusLine)
                .font(.hearthBodySM)
                .foregroundColor(.inkOnPhotoLight.opacity(0.9))
                .multilineTextAlignment(.leading)
                .lineLimit(2)
                .fixedSize(horizontal: false, vertical: true)
            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .contentShape(Rectangle())
    }

    @ViewBuilder
    private var avatar: some View {
        Group {
            if avatarURL != nil {
                AvatarCircleView(urlString: avatarURL,
                                 fallbackSystemImage: "figure.child", size: 48)
            } else {
                Circle()
                    .fill(kid.accent)
                    .frame(width: 48, height: 48)
                    .overlay(monogram)
            }
        }
        .accessibilityHidden(true)
    }

    /// Decorative only — the kid's name is always rendered beside it, so white
    /// on saffron carries no information on its own.
    private var monogram: some View {
        Text(String(kid.kidName.prefix(1)).uppercased())
            .font(.hearthTitleLG)
            .foregroundColor(.inkOnPhotoLight)
    }

    /// The kid's name on the tile (Dashboard 1 spec: Fraunces w600 28).
    /// The design shows the name alone here — the companion label ("with Friend")
    /// folds into the status caption below rather than sitting inline.
    private var nameRow: some View {
        Text(kid.kidName)
            .font(.custom("Fraunces", size: 28, relativeTo: .title2).weight(.semibold))
            .foregroundColor(.inkOnPhotoLight)
            .lineLimit(1)
            .minimumScaleFactor(0.7)
    }
}

/// A kid's photo as a tile ground, with their accent behind it while it loads
/// and a scrim so the name stays legible over any photo.
private struct KidTilePhoto: View {
    let urlString: String
    let accent: Color

    var body: some View {
        ZStack {
            accent
            AvatarCircleView(urlString: urlString, fallbackSystemImage: "figure.child", size: 400)
                .scaledToFill()
                .clipped()
            LinearGradient(
                colors: [.black.opacity(0.45), .black.opacity(0.1)],
                startPoint: .top, endPoint: .bottom
            )
        }
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

        /// The kid's card border + monogram color. Seeded on the kid-agent
        /// config id where one exists so a rename can't recolor the card; the
        /// profile key is the fallback for kids with no config yet. Must stay
        /// identical to `KidSettingsSheet`'s seed or a card and its sheet
        /// disagree on color.
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
            // Family profile is the source of truth for who gets a card.
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
    /// re-enables, and refreshes so the card flips back to Active.
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

    /// Recaps are decoration, never a gate: any failure just leaves the cards
    /// on their "hasn't chatted yet" copy.
    private static func summariesOrEmpty(baseURL: URL, userID: String) async -> [KidDailySummary] {
        (try? await HomeDashboardService.dailySummaries(baseURL: baseURL, userID: userID)) ?? []
    }
}
