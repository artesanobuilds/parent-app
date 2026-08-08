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
         onCompanionPresenceChanged: @escaping (Bool) -> Void = { _ in }) {
        self.userID = userID
        self.baseURL = baseURL
        self.refreshToken = refreshToken
        self.children = children
        self.onProfileChanged = onProfileChanged
        self.onNeedsRefresh = onNeedsRefresh
        self.onOpenCoach = onOpenCoach
        self.firstRunPrompt = firstRunPrompt
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

            if vm.kids.isEmpty && !vm.isLoading {
                emptyState
            } else {
                VStack(spacing: .hearth500) {
                    ForEach(vm.kids) { kid in
                        kidCard(for: kid)
                    }
                }
            }
        }
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

    // MARK: Card

    /// One kid's card, in that kid's accent.
    ///
    /// The card's tap target is the safety-critical part of this file: a
    /// crisis-LOCKED companion goes to the reactivate confirmation, NEVER to
    /// the intro/setup screen. Any future restyle must keep that branch.
    private func kidCard(for kid: KidsHomeViewModel.KidEntry) -> some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            cardTapTarget(for: kid)
            kidCTA(for: kid)
        }
        .padding(.hearth500)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
        .overlay(cardBorder(for: kid))
        .hearthCardElevation()
        .overlay(alignment: .topTrailing) { kidMenu(for: kid) }
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
                HomeCTALabel(title: "Hand to \(kid.kidName)")
            }
        case .draft:
            NavigationLink(value: KidNavigation.review(kidName: kid.kidName)) {
                HomeCTALabel(title: "Introduce \(kid.kidName)")
            }
            .buttonStyle(.plain)
        case .missing:
            NavigationLink(value: KidNavigation.review(kidName: kid.kidName)) {
                HomeCTALabel(title: "Set up \(kid.kidName)")
            }
            .buttonStyle(.plain)
        case .locked:
            Button { reactivateTarget = kid } label: { lockedCTALabel }
        }
    }

    private var lockedCTALabel: some View {
        Text("Review & reactivate")
            .font(.hearthTitleMD)
            .foregroundColor(.inkOnPhotoLight)
            .padding(.horizontal, .hearth500)
            .padding(.vertical, .hearth400)
            .background(Color.statusError)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusButton, style: .continuous))
    }

    private func kidMenu(for kid: KidsHomeViewModel.KidEntry) -> some View {
        Menu {
            Button { settingsTarget = KidSettingsTarget(id: kid.kidKey) } label: {
                Label("\(kid.kidName)'s settings", systemImage: "slider.horizontal.3")
            }
            Button { reviewTarget = kid.kidName } label: {
                Label("See what they've been up to", systemImage: "text.book.closed")
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
        } label: {
            Image(systemName: "ellipsis")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.inkMuted)
                .frame(width: 44, height: 44)
                .contentShape(Rectangle())
        }
        .accessibilityLabel("More options for \(kid.kidName)")
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
        HStack(alignment: .top, spacing: .hearth400) {
            avatar
            VStack(alignment: .leading, spacing: .hearth300) {
                nameRow
                Text(kid.statusLine)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkSecondary)
                    .multilineTextAlignment(.leading)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Spacer(minLength: 0)
        }
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

    private var nameRow: some View {
        HStack(spacing: .hearth400) {
            Text(kid.kidName)
                .font(.hearthTitleLG)
                .foregroundColor(.inkPrimary)
            Rectangle()
                .fill(Color.borderHairline)
                .frame(width: 1, height: 16)
            Text(kid.companionLine)
                .font(.hearthBodyMD)
                .foregroundColor(.inkMuted)
                .lineLimit(1)
            // Leaves room for the ••• menu in the card's top-right corner.
            Spacer(minLength: 44)
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

    func refresh() async {
        guard !isLoading else { return }
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
        } catch {
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
