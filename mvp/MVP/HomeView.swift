import SwiftUI

/// beta-v1 Home — a dashboard, not a browse surface.
///
/// Top to bottom, in the design's order (verified against Figma
/// `Onboarding - Dashboard 1`, node 754:4553, round-2 addendum in
/// `docs/design/beta-v1-sprint2.md`): the parent's avatar, one card per kid
/// (YOUR KIDS), what's COMING UP, a ranked FOR YOU preview, then the coach's
/// current nudge (COACH) with a "Check your family settings" link beneath
/// it. The photo banner, featured card, community carousel and topic grid
/// the pre-beta Home rendered are gone; browsing now lives behind
/// Settings → Library.
struct HomeView: View {
    let username: String
    /// Switch to the Planner tab. Supplied by `MainTabView` (the tab owner) —
    /// the same idiom `SettingsView`'s `onOpenPlan` already uses. This is what
    /// finally gives Dashboard 1's COMING UP "Add event" row a real destination:
    /// the one existing add-to-plan flow (`IngestView` / the door sheet) needs a
    /// `PlanViewModel`, which `MainTabView` owns and hands to `PlanView`. Home
    /// routing there reuses that single plan-mutation path instead of forking a
    /// second one (`feedback_standalone_flows`). Nil hides the row rather than
    /// rendering a dead control.
    var onOpenPlanner: (() -> Void)?
    /// Switch to the Settings tab. Same idiom as `onOpenPlanner` — there is no
    /// tab-selection binding/environment in this app, so each cross-tab link
    /// is a closure `MainTabView` hands down. Backs the "Check your family
    /// settings" row, which used to be inert header-detail text.
    var onOpenSettings: (() -> Void)?

    @EnvironmentObject private var contentVM: ContentViewModel
    @EnvironmentObject private var configuration: ServerConfiguration
    @EnvironmentObject private var session: AppSession
    @Environment(\.triggerKidHandoff) private var triggerKidHandoff

    // Replaces the removed Settings-sheet `onDismiss` bump: MainTabView bumps
    // this every time the Home tab is re-selected, so a kid edited/deleted in
    // the Settings TAB can't linger here until relaunch (CLAUDE.md: "after a
    // mutation, the source-of-truth view re-fetches"). See the contract note at
    // the top of MainTabView.swift.
    @Environment(\.homeRefreshToken) private var homeRefreshToken

    // Set by KidsHomeSection's task hook after /kid-agent/list resolves.
    @AppStorage("has_kid_companions") private var hasKidCompanions: Bool = false
    // Set by KidsHomeSection whenever any kid has an active OR locked
    // companion — i.e. "has anyone ever been introduced". Drives
    // `isFirstRunDashboard` below; deliberately separate from
    // `hasKidCompanions` (ACTIVE-only) so a crisis-locked kid never flips
    // Home back into first-run copy.
    @State private var hasAnyCompanion = false
    // The parent's display name for the avatar monogram. `username` is an
    // opaque account id (a UUID for sign-in accounts), so it must NOT be shown.
    @AppStorage("parent_display_name") private var parentDisplayName: String = ""

    @StateObject private var dashboard = HomeDashboardViewModel()

    /// Presigned parent photo from the profile fetch (display-only, short-lived).
    @State private var parentAvatarURL: String?
    /// The family's children keyed by their profile key — handed to
    /// KidsHomeSection so the cards and the kid-settings sheet don't each
    /// re-fetch the profile.
    @State private var familyChildren: [String: ChildProfileDTO] = [:]
    /// Bumped locally when a sheet presented from Home mutates user state
    /// (the kid-settings sheet). Added to the environment token so BOTH
    /// triggers drive the same one re-fetch.
    @State private var localRefreshToken = 0
    /// The coach conversation, opened by the nudge's CTA.
    @State private var isShowingCoach = false
    @State private var coachVM: ChatViewModel?
    /// The avatar / account sheet (Sprint-1 gap). See `AccountSheetView`.
    @State private var isShowingAccount = false

    // MARK: The onboarding tail (Phase F)
    //
    // Greg's canvas order puts the profile editors AFTER Dashboard 1 — the
    // parent lands on Home first and is then walked through each kid and each
    // adult. `SetupTailView` is that walk; this is its two entry points.
    //
    //  * AUTOMATIC, once: on the first Home the parent sees, when the walk has
    //    neither been finished nor deferred and a kid is still pending
    //    (`SetupTailStore.shouldAutoPresent`, keyed by kid profile key).
    //  * FROM A TILE: "Set up Benjamin" carries that kid's stable profile key
    //    and the walk opens on them. Same code path, not a parallel one.
    /// Non-nil presents the tail; the payload carries the stop to open on.
    @State private var setupTailEntry: SetupTailEntry?
    /// One auto-present attempt per appearance of this view, so a dismissal
    /// (which persists `deferred`/`finished`) can't immediately re-trigger.
    @State private var didConsiderAutoTail = false
    /// "+ Add another child" (Dashboard 1). Presents the SAME `AddKidSheet` as
    /// Settings → Profile, so there is one add-a-kid write path.
    @State private var isShowingAddKid = false

    /// Identifiable payload for `.sheet(item:)`. `stopID` nil = start at the
    /// first pending stop; otherwise it's `SetupStop.kidID(profileKey)`.
    struct SetupTailEntry: Identifiable {
        let stopID: String?
        var id: String { stopID ?? "first-pending" }
    }

    private var refreshToken: Int { homeRefreshToken &+ localRefreshToken }
    private var forYouPreview: [ForYouItem] { Array(contentVM.forYouItems.prefix(2)) }
    private var comingUpPreview: [ComingUpEntry] { Array(dashboard.comingUp.prefix(2)) }

    /// True for a genuinely new family: the coach warm-up hasn't produced a
    /// nudge YET (not merely "still loading" — `hasLoadedNudge` gates that)
    /// AND no kid has ever had an introduced companion (`hasAnyCompanion`,
    /// active-or-locked, set by `KidsHomeSection`). Both signals already live
    /// in this view from calls Home makes anyway — no new backend call.
    /// Drives the beta-v1 "Dashboard 1" first-run copy: the COACH banner
    /// text, the YOUR KIDS prompt, and the COMING UP "Add event" affordance.
    private var isFirstRunDashboard: Bool {
        dashboard.hasLoadedNudge && dashboard.nudge == nil && !hasAnyCompanion
    }

    /// Page ground branches per dashboard state (beta-v1 spec):
    /// Dashboard 1 (first run): `#F3F0EB` (cream-100/bgSober).
    /// Dashboard 2 (populated): `#E9E4DC` (cream-200/bgCanvas).
    private var pageGround: Color {
        isFirstRunDashboard ? .bgSober : .bgCanvas
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: .hearth800) {
                    if session.needsLegalAcceptance {
                        legalReacceptBanner
                    }

                    parentAvatarRow

                    // Section order per beta-v1-sprint1.md measured frames
                    // (Dashboard 1/2 by absolute y): YOUR KIDS → COMING UP →
                    // FOR YOU → COACH. The kids are first because the dashboard
                    // is about them; the coach's nudge is last as a response.
                    if let baseURL = configuration.baseURL, !username.isEmpty {
                        KidsHomeSection(
                            userID: username,
                            baseURL: baseURL,
                            refreshToken: refreshToken,
                            children: familyChildren,
                            onProfileChanged: apply(profile:),
                            onNeedsRefresh: { localRefreshToken &+= 1 },
                            onOpenCoach: openCoach,
                            firstRunPrompt: isFirstRunDashboard
                                ? "Help us get to know your kids a little more:" : nil,
                            onCompanionPresenceChanged: { hasAnyCompanion = $0 },
                            isFirstRun: isFirstRunDashboard,
                            onEnterSetup: { kidKey in
                                setupTailEntry = SetupTailEntry(stopID: SetupStop.kidID(kidKey))
                            },
                            onAddChild: { isShowingAddKid = true }
                        )
                    }

                    comingUpSection

                    forYouSection

                    coachSection

                    if let onOpenSettings {
                        familySettingsLinkRow(onOpenSettings)
                    }

                    Spacer(minLength: .hearth600)
                }
                .padding(.horizontal, .hearth700)
                .padding(.top, .hearth300)
            }
            .background(pageGround.ignoresSafeArea())
            // iOS 17+: .navigationBarHidden(true) is deprecated and leaves the
            // nav bar's reserved vertical space visible as a band.
            .toolbar(.hidden, for: .navigationBar)
            .withContentNavigationDestinations()
            .navigationDestination(for: ComingUpRoute.self) { _ in
                ComingUpListView(entries: dashboard.comingUp)
            }
            .task(id: refreshToken) {
                // Profile is the source of truth for the parent's name + photo
                // and for the kid roster. Re-runs on every return to the Home
                // tab and after any sheet mutation.
                guard let baseURL = configuration.baseURL, !username.isEmpty else { return }
                async let profileTask = ProfileService.getProfile(baseURL: baseURL, userID: username)
                await dashboard.refresh(baseURL: baseURL, userID: username)
                // `force` only on a re-run — i.e. exactly when the parent has
                // come back to Home from another tab.
                await contentVM.loadForYou(force: refreshToken > 0)
                if let profile = try? await profileTask { apply(profile: profile) }
                considerAutoSetupTail()
            }
            .sheet(isPresented: $isShowingCoach) {
                if let coachVM {
                    AgentView(viewModel: coachVM, configuration: configuration)
                }
            }
            // onDismiss bumps the local token (CLAUDE.md: after a mutation
            // the source-of-truth view re-fetches) — the sheet can change the
            // family-interests selection, which Home's own profile fetch
            // doesn't currently render but should still be picked up fresh
            // the next time anything reads it.
            .sheet(isPresented: $isShowingAccount, onDismiss: { localRefreshToken &+= 1 }) {
                AccountSheetView(userID: username, parentDisplayName: parentDisplayName)
                    // 24pt corner, per the Figma sheet. iOS's default sheet
                    // radius is ~10 on a full-height presentation, which read as
                    // a much squarer card than the design.
                    .presentationCornerRadius(.hearthRadiusSheet)
            }
            // The tail. onDismiss bumps the token so the kid tiles re-read the
            // profile the walk just filled in.
            .sheet(item: $setupTailEntry, onDismiss: { localRefreshToken &+= 1 }) { entry in
                setupTailSheet(entry)
            }
            // "+ Add another child". The same sheet Settings → Profile presents,
            // and its verified write returns the fresh family, which is folded
            // straight into Home's state.
            .sheet(isPresented: $isShowingAddKid, onDismiss: { localRefreshToken &+= 1 }) {
                AddKidSheet(baseURL: configuration.baseURL, userID: username) { profile in
                    apply(profile: profile)
                }
            }
        }
    }

    @ViewBuilder
    private func setupTailSheet(_ entry: SetupTailEntry) -> some View {
        if let baseURL = configuration.baseURL, !username.isEmpty {
            SetupTailView(
                userID: username,
                baseURL: baseURL,
                entryStopID: entry.stopID,
                onNeedsRefresh: { localRefreshToken &+= 1 }
            )
            .presentationCornerRadius(.hearthRadiusSheet)
        }
    }

    /// Open the tail by itself the first time — once per appearance, and only
    /// when the store says this parent hasn't finished or deferred it. Progress
    /// is keyed by kid PROFILE KEY, so adding or deleting a kid can't make a
    /// finished walk look unfinished (or vice versa).
    private func considerAutoSetupTail() {
        guard !didConsiderAutoTail, !username.isEmpty else { return }
        didConsiderAutoTail = true
        guard setupTailEntry == nil, !familyChildren.isEmpty else { return }
        guard SetupTailStore.shouldAutoPresent(
            kidKeys: Array(familyChildren.keys), userID: username
        ) else { return }
        setupTailEntry = SetupTailEntry(stopID: nil)
    }

    /// Fold a freshly-fetched family into Home's state. Called both by the
    /// task's own fetch and by the kid-settings sheet's mutation callback, so
    /// an edit shows here without waiting for the sheet to close.
    private func apply(profile: FamilyProfileDTO) {
        if let name = profile.parent?.name?.trimmingCharacters(in: .whitespaces), !name.isEmpty {
            parentDisplayName = name
        }
        parentAvatarURL = profile.parent?.avatarUrl
        // Only overwrite the roster with a NON-empty one, unless we've never had
        // one. `children` is nil/empty on a partial or failed decode as well as
        // for a genuinely childless family, and blanking a known-good roster is
        // indistinguishable to the parent from losing their kids. The kid tiles
        // own the authoritative empty state (`KidsHomeViewModel.hasLoadedOnce`).
        let fetched = profile.children ?? [:]
        if !fetched.isEmpty || familyChildren.isEmpty {
            familyChildren = fetched
        }
    }

    // MARK: - Legal re-accept banner
    //
    // Compliance surface. Greg's frame doesn't depict this state; it stays
    // exactly as it was, at the very top, above everything else.

    /// Non-blocking, non-dismissable prompt shown when a published legal
    /// version requires re-acceptance. One tap agrees to the current versions
    /// (LegalService echoes exactly what /legal/status reported).
    private var legalReacceptBanner: some View {
        let base = configuration.baseURLString
        let updatedTitles = session.legalStatus?.documents
            .filter { !$0.accepted }
            .map(\.title)
            .joined(separator: " and ") ?? "our terms"
        return VStack(alignment: .leading, spacing: .hearth300) {
            Text("We've updated \(updatedTitles)")
                .font(.hearthTitleMD)
                .foregroundColor(.inkPrimary)
            if let links = try? AttributedString(
                markdown: "Read the [Privacy Policy](\(base)/dashboard/docs/privacy-policy) "
                    + "or [Terms of Service](\(base)/dashboard/docs/terms), then agree to keep going."
            ) {
                Text(links)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                    .tint(.accentOnCanvas)
            }
            Button {
                Task { await session.acceptLegal(userID: username, baseURL: configuration.baseURL) }
            } label: {
                HomeCTALabel(title: "Agree")
            }
        }
        .padding(.hearth500)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
        .hearthCardElevation()
        .onAppear { Analytics.capture("legal_reaccept_shown", [:]) }
    }

    // MARK: - Parent avatar

    /// Teal monogram circle, top-right. Tapping it opens the avatar / account
    /// sheet (Sprint-1 gap — saved/history, family interests, account block).
    private var parentAvatarRow: some View {
        HStack(spacing: .hearth400) {
            Spacer(minLength: 0)
            if !username.isEmpty && hasKidCompanions {
                HandoffEntryButton { triggerKidHandoff() }
            }
            Button { isShowingAccount = true } label: {
                Group {
                    if parentAvatarURL != nil {
                        AvatarCircleView(urlString: parentAvatarURL,
                                         fallbackSystemImage: "person.fill", size: 36)
                    } else {
                        Circle()
                            .fill(Color.accentDefault)
                            .frame(width: 36, height: 36)
                            .overlay(
                                Text(parentDisplayName.isEmpty
                                     ? "?" : String(parentDisplayName.prefix(1)).uppercased())
                                    .font(.hearthTitleMD)
                                    .foregroundColor(.inkOnPhotoLight)
                            )
                    }
                }
            }
            .buttonStyle(.plain)
            .accessibilityLabel(parentDisplayName.isEmpty
                                ? "Your profile" : "\(parentDisplayName)'s profile")
        }
    }

    // MARK: - COACH

    private var coachHeaderDetail: String {
        dashboard.nudge?.timeOfDayLabel ?? HomeWhen.partOfDay(Date())
    }

    /// "Check your family settings" — was inert header-detail text on
    /// Dashboard 1 (first run only); now a real tappable row to the new
    /// Settings tab root, shown in both dashboard states since it's the
    /// doorway to the consolidated family-settings screen, not a first-run
    /// hint. Per the frame: a quiet pill row, teal label, right chevron.
    private func familySettingsLinkRow(_ action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: .hearth400) {
                Text("Check your family settings")
                    .font(.hearthBodyMD.weight(.bold))
                    .foregroundColor(.accentDefault)
                Spacer(minLength: 0)
                Image(systemName: "chevron.right")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.accentDefault)
            }
            .padding(.horizontal, .hearth600)
            .padding(.vertical, .hearth500)
            .background(Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusSeeAll, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    private var coachSection: some View {
        coachSectionBody
            // COACH has a section ground that branches per dashboard state:
            // Dashboard 1 (first run): `#FCFBF8` r=28 pad 30 (bgCoachBanner).
            // Dashboard 2 (populated): `#F5F3EF` r=28 pad 30 (bgCard).
            .padding(30)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: .hearthRadiusSection, style: .continuous)
                    .fill(isFirstRunDashboard ? Color.bgCoachBanner : Color.bgCard)
            )
    }

    private var coachSectionBody: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            HomeSectionHeader(
                icon: "bubble.left",
                title: "Coach",
                detail: coachHeaderDetail
            )

            VStack(alignment: .leading, spacing: .hearth500) {
                if let nudge = dashboard.nudge {
                    Text(nudge.body)
                        .font(.hearthBodyLG)
                        .lineSpacing(.hearthLineBodyLG)
                        .foregroundColor(.inkPrimary)
                        .fixedSize(horizontal: false, vertical: true)

                    Button {
                        openCoach()
                    } label: {
                        HomeCTALabel(title: nudge.ctaTitle)
                    }
                } else {
                    // Deliberately NOT fake coaching copy: the backend refuses
                    // to fabricate a nudge, so "nothing here" genuinely means
                    // the coach hasn't met this family yet.
                    Text(dashboard.hasLoadedNudge
                         ? "Your coach hasn't written to you yet. Tell it about your week and the first nudge lands here."
                         : "Checking in with your coach…")
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkMuted)
                        .fixedSize(horizontal: false, vertical: true)

                    if dashboard.hasLoadedNudge {
                        Button { openCoach() } label: {
                            HomeCTALabel(title: "Talk to your coach")
                        }
                    }
                }
            }
            .padding(.hearth500)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
            .hearthCardElevation()
        }
    }

    /// Open the coaching conversation. Home isn't the Coach tab's owner, so it
    /// presents the same `AgentView` over its own chat view model; the thread
    /// (and therefore the coach's memory) lives server-side, so nothing is lost.
    private func openCoach() {
        Analytics.capture("home_coach_nudge_tapped",
                          ["has_nudge": dashboard.nudge != nil])
        if coachVM == nil {
            let vm = ChatViewModel(configuration: configuration, mode: .coaching)
            vm.setUserID(username)
            coachVM = vm
        }
        isShowingCoach = true
    }

    // MARK: - COMING UP

    @ViewBuilder
    private var comingUpSection: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            HomeSectionHeader(icon: "calendar", title: "Coming up")

            if comingUpPreview.isEmpty {
                Text(dashboard.isLoading
                     ? "Looking at your calendar…"
                     : "Nothing on the calendar yet. Plan something and it shows up here.")
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkMuted)
                    .fixedSize(horizontal: false, vertical: true)
            } else {
                VStack(alignment: .leading, spacing: 0) {
                    ForEach(Array(comingUpPreview.enumerated()), id: \.element.id) { index, entry in
                        if index > 0 { HomeRowDivider() }
                        ComingUpRow(entry: entry)
                    }
                }

                // "See all" affordance (Dashboard 1/2): white `#FFFFFF` r=10.
                NavigationLink(value: ComingUpRoute()) {
                    Text("See all")
                        .font(.hearthTitleMD)
                        .foregroundColor(.accentOnCanvas)
                        .padding(.horizontal, .hearth400)
                        .padding(.vertical, .hearth300)
                        .background(Color.bgElevated)
                        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusSeeAll, style: .continuous))
                }
                .buttonStyle(.plain)
                .padding(.top, .hearth300)
            }

            if isFirstRunDashboard, let onOpenPlanner {
                addEventRow(onOpenPlanner)
            }
        }
        // COMING UP is BARE (no card ground) — the design distinguishes the
        // "your family right now" sections (YOUR KIDS, COACH) from the editorial
        // ones (FOR YOU, COMING UP) by grounding the former and leaving the latter
        // on the canvas.
    }

    /// First-run-only "Add event" affordance (Dashboard 1). NOW WIRED (Phase F):
    /// it routes to the Planner tab, which owns the real add-to-plan flows
    /// (`IngestView` — paste a camp email / snap a flyer — and the "Plan
    /// something" door sheet). Home deliberately does NOT get its own
    /// plan-mutation path: `PlanViewModel` is owned by `MainTabView`, and a
    /// second parallel writer is the mistake `feedback_standalone_flows` warns
    /// about. Routing keeps one writer and still gives the parent somewhere real
    /// to land.
    private func addEventRow(_ action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: .hearth300) {
                Image(systemName: "plus.circle.fill")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.accentOnCanvas)
                Text("Add event")
                    .font(.hearthTitleMD)
                    .foregroundColor(.accentOnCanvas)
                Spacer(minLength: 0)
            }
            .padding(.hearth500)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
            .hearthCardElevation()
        }
        .buttonStyle(.plain)
        .padding(.top, .hearth300)
        .accessibilityHint("Opens the planner")
    }

    // MARK: - FOR YOU

    @ViewBuilder
    private var forYouSection: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            HomeSectionHeader(icon: "book", title: "For you")

            if forYouPreview.isEmpty {
                Text(contentVM.isLoading
                     ? "Pulling together a few reads…"
                     : "Reading picks land here once the library loads.")
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkMuted)
            } else {
                VStack(alignment: .leading, spacing: 0) {
                    ForEach(Array(forYouPreview.enumerated()), id: \.element.id) { index, item in
                        if index > 0 { HomeRowDivider() }
                        NavigationLink(value: ArticleRoute(id: item.id)) {
                            ForYouRow(
                                item: item,
                                // An unranked fallback list must not be
                                // captioned as if it were personalised.
                                showsReason: !contentVM.forYouIsFallback
                            )
                        }
                        .buttonStyle(.plain)
                    }
                }

                NavigationLink(value: ForYouRoute()) {
                    HomeCTALabel(title: "See all")
                }
                .buttonStyle(.plain)
                .padding(.top, .hearth300)
            }
        }
        // FOR YOU is a white card (beta-v1 spec: Dashboard 1/2 both have
        // `#FFFFFF` r=28, distinct from the bare COMING UP). Dashboard 1 pad 30,
        // Dashboard 2 pad 28/30 — using 30 uniformly.
        .padding(30)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: .hearthRadiusSection, style: .continuous)
                .fill(Color.bgElevated)
        )
        .hearthCardElevation()
    }
}

// MARK: - Shared dashboard chrome

/// `COACH • This morning` — serif all-caps label with a leading icon, the
/// beta-v1 section masthead. Icons are `accentOnCanvas`, never the fill accent
/// (accent-as-ink on cream is a 4.15:1 AA fail).
struct HomeSectionHeader: View {
    var icon: String?
    let title: String
    var detail: String?

    var body: some View {
        HStack(spacing: .hearth300) {
            if let icon {
                Image(systemName: icon)
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(.accentOnCanvas)
                    .accessibilityHidden(true)
            }
            // Inter w800 16, uppercased, no tracking — measured off the Figma
            // node data for YOUR KIDS / FOR YOU / COMING UP. This was Fraunces
            // bold 13 with +4% tracking until 2026-08-08, which is what made the
            // dashboard read as a different design from Greg's file.
            Text(title)
                .font(.hearthSectionHeader)
                .textCase(.uppercase)
                .foregroundColor(.inkPrimary)
            if let detail, !detail.isEmpty {
                Text("• \(detail)")
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkSecondary)
                    .lineLimit(1)
            }
            Spacer(minLength: 0)
        }
        .accessibilityElement(children: .combine)
    }
}

/// Filled teal CTA — Greg's buttons are tight 8pt rects, not capsules, and the
/// fill accent is the only AA-safe way to carry white text.
struct HomeCTALabel: View {
    let title: String

    var body: some View {
        Text(title)
            .font(.hearthTitleMD)
            .foregroundColor(.inkOnPhotoLight)
            .padding(.horizontal, .hearth500)
            .padding(.vertical, .hearth400)
            .background(Color.accentDefault)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusButton, style: .continuous))
    }
}

/// Hairline between list rows. beta-v1 demotes the hairline to dividers only —
/// cards carry a shadow instead.
struct HomeRowDivider: View {
    var body: some View {
        Rectangle()
            .fill(Color.borderHairline)
            .frame(height: 1)
            .padding(.vertical, .hearth400)
    }
}

// MARK: - Rows

private struct ComingUpRow: View {
    let entry: ComingUpEntry

    var body: some View {
        // Editorial treatment per beta-v1 spec (Dashboard 2): lead item is
        // Fraunces w700 38/40 tracking -0.38, body is Inter w400 13/18.
        VStack(alignment: .leading, spacing: .hearth300) {
            Text(entry.title)
                .font(.hearthDisplaySM)
                .tracking(-0.38)
                .foregroundColor(.inkHeader)
                .fixedSize(horizontal: false, vertical: true)
            if !entry.detail.isEmpty {
                Text(entry.detail)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkDisplay)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

private struct ForYouRow: View {
    let item: ForYouItem
    let showsReason: Bool

    /// "Because ben's naming feelings" — the server's explanation, shown only
    /// when the list really is ranked.
    private var reasonText: String? {
        guard showsReason, let reason = item.reason,
              !reason.trimmingCharacters(in: .whitespaces).isEmpty else { return nil }
        return reason
    }

    var body: some View {
        // Editorial treatment per beta-v1 spec (Dashboard 1/2): eyebrow Inter
        // w700 13 in `#989591`, lead item Fraunces w700 38/40 tracking -0.38,
        // body Inter w400 13. The big headline makes this section read as
        // editorial rather than a list.
        VStack(alignment: .leading, spacing: .hearth300) {
            if let reasonText {
                Text(reasonText)
                    .font(.hearthBodySMBold)
                    .foregroundColor(.inkEyebrow)
                    .fixedSize(horizontal: false, vertical: true)
            }
            Text(item.title)
                .font(.hearthDisplaySM)
                .tracking(-0.38)
                .foregroundColor(.inkHeader)
                .multilineTextAlignment(.leading)
                .fixedSize(horizontal: false, vertical: true)
            if reasonText == nil, !item.subtitle.isEmpty {
                Text(item.subtitle)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                    .lineLimit(2)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

// MARK: - COMING UP → See all

/// Payload-free route for the full upcoming list. Home owns this destination
/// (the Plan tab is a sibling, not something Home can push to).
struct ComingUpRoute: Hashable {}

struct ComingUpListView: View {
    let entries: [ComingUpEntry]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                if entries.isEmpty {
                    Text("Nothing on the calendar yet.")
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkMuted)
                } else {
                    ForEach(Array(entries.enumerated()), id: \.element.id) { index, entry in
                        if index > 0 { HomeRowDivider() }
                        ComingUpRow(entry: entry)
                    }
                }
            }
            .padding(.hearth500)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
            .hearthCardElevation()
            .padding(.horizontal, .hearth700)
            .padding(.top, .hearth500)
        }
        .background(Color.bgCanvas.ignoresSafeArea())
        .trackScreen("coming_up_all")
        .navigationTitle("Coming up")
        .navigationBarTitleDisplayMode(.inline)
        .toolbarBackground(Color.bgCanvas, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
    }
}

// MARK: - Category Detail View

struct CategoryDetailView: View {
    let categoryId: String
    @EnvironmentObject private var contentVM: ContentViewModel

    private var category: APICategory? {
        contentVM.categories.first { $0.id == categoryId }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: .hearth600) {
                let items = contentVM.libraryItems(for: categoryId)

                if !items.isEmpty {
                    Text("Articles")
                        .font(.hearthLabel)
                        .foregroundColor(.inkMuted)
                        .tracking(0.66)
                        .textCase(.uppercase)
                        .padding(.horizontal, .hearth700)

                    ForEach(items) { item in
                        NavigationLink(value: ArticleRoute(id: item.id)) {
                            LibraryItemCard(item: item)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(.horizontal, .hearth700)
                        }
                        .buttonStyle(.plain)
                    }
                }

                Spacer(minLength: .hearth600)
            }
            .padding(.top, .hearth300)
        }
        .background(Color.bgCanvas.ignoresSafeArea())
        .trackScreen("category_detail")
        .navigationTitle(category.map { "\($0.emoji) \($0.name)" } ?? "Category")
        .navigationBarTitleDisplayMode(.large)
        .toolbarBackground(Color.bgCanvas, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
        .withContentNavigationDestinations()
    }
}
