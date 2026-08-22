import SwiftUI

/// Heisman Home — the "day zero summary" (Onboarding - 9) as THE Home screen,
/// not a first-run variant.
///
/// Top to bottom, per Figma `nAXZQhmvwEpzq3rkBisok7` frame `42:8322`
/// (440×2077, spec: `docs/design/heisman-sprint01-onboarding.md`): circled
/// monogram top-right; date eyebrow ("Tue  • Aug 18") over the display
/// headline ("Hey Greg, Here's today:"); one TODAY card per person built from
/// the lifecycle board (kids by `kid_name`, the parent from nil-kid rows);
/// the COACH card; the YOUR KIDS black tiles; and the MVP Editorial card.
/// Every section renders only real server data and collapses when it has
/// none — a fresh account shows exactly what onboarding seeded (children
/// always; tasks only if step 05 wasn't skipped — acceptance criteria 7–8).
struct HomeView: View {
    let username: String
    /// Switch to the Planner tab. Supplied by `MainTabView` (the tab owner).
    /// Backs every "Update {name}'s planner" link — Home deliberately does NOT
    /// own a plan-mutation path of its own (`feedback_standalone_flows`); the
    /// Planner tab has the one existing write path. Nil hides the links
    /// rather than rendering dead controls.
    var onOpenPlanner: (() -> Void)?
    /// Switch to the Settings tab. Kept for `MainTabView`'s call-site contract.
    /// The Onboarding-9 frame HIDES its "Check your family settings" chip
    /// (node `29:2853`, hidden=true), so nothing on this screen renders it —
    /// Settings remains reachable as its own tab.
    var onOpenSettings: (() -> Void)?

    @EnvironmentObject private var contentVM: ContentViewModel
    @EnvironmentObject private var configuration: ServerConfiguration
    @EnvironmentObject private var session: AppSession
    @Environment(\.triggerKidHandoff) private var triggerKidHandoff

    // MainTabView bumps this every time the Home tab is re-selected, so a kid
    // or plan item edited elsewhere can't linger here until relaunch
    // (CLAUDE.md: "after a mutation, the source-of-truth view re-fetches").
    @Environment(\.homeRefreshToken) private var homeRefreshToken

    // Set by KidsHomeSection's task hook after /kid-agent/list resolves.
    @AppStorage("has_kid_companions") private var hasKidCompanions: Bool = false
    // The parent's display name for the headline + monogram. `username` is an
    // opaque account id (a UUID for sign-in accounts), so it must NOT be shown.
    @AppStorage("parent_display_name") private var parentDisplayName: String = ""

    @StateObject private var today = HomeTodayViewModel()

    /// Presigned parent photo from the profile fetch (display-only, short-lived).
    @State private var parentAvatarURL: String?
    /// The family's children keyed by their profile key — handed to
    /// KidsHomeSection so the tiles and the kid-settings sheet don't each
    /// re-fetch the profile.
    @State private var familyChildren: [String: ChildProfileDTO] = [:]
    /// Bumped locally when a sheet presented from Home mutates user state.
    /// Added to the environment token so BOTH triggers drive the same re-fetch.
    @State private var localRefreshToken = 0
    /// The coach conversation, opened by the COACH card's action link.
    @State private var isShowingCoach = false
    @State private var coachVM: ChatViewModel?
    /// The avatar / account sheet.
    @State private var isShowingAccount = false

    // MARK: The onboarding tail (Phase F)
    //
    // The post-account walk through each kid's profile. Two entry points:
    // automatic once per appearance (`SetupTailStore.shouldAutoPresent`), and
    // from a kid tile's ellipsis menu. Same code path, not a parallel one.
    @State private var setupTailEntry: SetupTailEntry?
    /// One auto-present attempt per appearance, so a dismissal (which persists
    /// `deferred`/`finished`) can't immediately re-trigger.
    @State private var didConsiderAutoTail = false

    /// Identifiable payload for `.sheet(item:)`. `stopID` nil = start at the
    /// first pending stop; otherwise it's `SetupStop.kidID(profileKey)`.
    struct SetupTailEntry: Identifiable {
        let stopID: String?
        var id: String { stopID ?? "first-pending" }
    }

    private var refreshToken: Int { homeRefreshToken &+ localRefreshToken }

    var body: some View {
        NavigationStack {
            ScrollView {
                // Section gap 16 per the frame's `content` auto-layout
                // (`29:2792`: gap 16, px 24, pb 22).
                VStack(alignment: .leading, spacing: .hearth500) {
                    if session.needsLegalAcceptance {
                        legalReacceptBanner
                    }

                    parentAvatarRow

                    headlineBlock

                    ForEach(today.people) { person in
                        HomeTodayCard(person: person, onOpenPlanner: onOpenPlanner)
                    }

                    coachCard

                    if let baseURL = configuration.baseURL, !username.isEmpty {
                        KidsHomeSection(
                            userID: username,
                            baseURL: baseURL,
                            refreshToken: refreshToken,
                            children: familyChildren,
                            onProfileChanged: apply(profile:),
                            onNeedsRefresh: { localRefreshToken &+= 1 },
                            onOpenCoach: openCoach,
                            onEnterSetup: { kidKey in
                                setupTailEntry = SetupTailEntry(stopID: SetupStop.kidID(kidKey))
                            }
                        )
                    }

                    editorialCard

                    Spacer(minLength: .hearth600)
                }
                .padding(.horizontal, .hearth700)
                .padding(.top, .hearth300)
            }
            // Page ground: the frame root + profile row are `#F3F0EB` — the
            // existing `bgSober` primitive (cream-100), exact match.
            .background(Color.bgSober.ignoresSafeArea())
            .toolbar(.hidden, for: .navigationBar)
            .withContentNavigationDestinations()
            .task(id: refreshToken) {
                // Profile is the source of truth for the parent's name + photo
                // and the kid roster; the board feeds the TODAY cards; the
                // content store feeds MVP Editorial. Re-runs on every return to
                // the Home tab and after any sheet mutation — never one-shot.
                guard let baseURL = configuration.baseURL, !username.isEmpty else { return }
                async let profileTask = ProfileService.getProfile(baseURL: baseURL, userID: username)
                await today.refresh(baseURL: baseURL, userID: username,
                                    parentName: parentDisplayName)
                await contentVM.loadForYou(force: refreshToken > 0)
                if let profile = try? await profileTask { apply(profile: profile) }
                considerAutoSetupTail()
            }
            .sheet(isPresented: $isShowingCoach) {
                if let coachVM {
                    AgentView(viewModel: coachVM, configuration: configuration)
                }
            }
            // onDismiss bumps the local token (CLAUDE.md: after a mutation the
            // source-of-truth view re-fetches).
            .sheet(isPresented: $isShowingAccount, onDismiss: { localRefreshToken &+= 1 }) {
                AccountSheetView(userID: username, parentDisplayName: parentDisplayName)
                    .presentationCornerRadius(.hearthRadiusSheet)
            }
            // The tail. onDismiss bumps the token so the kid tiles re-read the
            // profile the walk just filled in.
            .sheet(item: $setupTailEntry, onDismiss: { localRefreshToken &+= 1 }) { entry in
                setupTailSheet(entry)
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
    /// when the store says this parent hasn't finished or deferred it.
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
    /// task's own fetch and by the kid-settings sheet's mutation callback.
    private func apply(profile: FamilyProfileDTO) {
        if let name = profile.parent?.name?.trimmingCharacters(in: .whitespaces), !name.isEmpty {
            parentDisplayName = name
            today.applyParentName(name)
        }
        parentAvatarURL = profile.parent?.avatarUrl
        // Only overwrite the roster with a NON-empty one, unless we've never
        // had one — blanking a known-good roster is indistinguishable to the
        // parent from losing their kids.
        let fetched = profile.children ?? [:]
        if !fetched.isEmpty || familyChildren.isEmpty {
            familyChildren = fetched
        }
    }

    // MARK: - Legal re-accept banner
    //
    // Compliance surface. The frame doesn't depict this state; it stays at the
    // very top, above everything else.

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

    // MARK: - Monogram row

    /// Circled monogram, top-right (measured `29:2856`: 36pt circle,
    /// `accent/default` fill, Fraunces bold ≈18 letter in the Heisman paper
    /// cream). Tapping it opens the account sheet. The handoff entry stays —
    /// a functional affordance the frame doesn't legislate away.
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
                                // Fraunces Bold 18.24, tracking -0.18
                                // (`29:2858`). The frame's letter is Heisman
                                // "paper" `#FCFBF8`; nearest ink-on-teal token
                                // is `inkOnPhotoLight` (#FFFFFF) — gap noted.
                                Text(parentDisplayName.isEmpty
                                     ? "?" : String(parentDisplayName.prefix(1)).uppercased())
                                    .font(.custom(HearthFontFamily.displaySerif,
                                                  fixedSize: 18.24).weight(.bold))
                                    .tracking(-0.18)
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

    // MARK: - Date eyebrow + headline

    /// "Tue  • Aug 18" — the frame's own two-space bullet run (`29:2794`),
    /// JetBrains Mono 12/16 in ink/primary. Live date, format from the frame.
    private var dateEyebrow: String {
        let date = Date()
        return "\(Self.weekdayFormatter.string(from: date))  • "
            + Self.monthDayFormatter.string(from: date)
    }

    private static let weekdayFormatter: DateFormatter = {
        let f = DateFormatter(); f.setLocalizedDateFormatFromTemplate("EEE"); return f
    }()
    private static let monthDayFormatter: DateFormatter = {
        let f = DateFormatter(); f.setLocalizedDateFormatFromTemplate("MMMd"); return f
    }()

    /// Measured `29:2793`: sits 8pt further in than the 24pt gutter (x=32),
    /// eyebrow→title gap 3; title Fraunces SemiBold 28, line-height 1.5
    /// (`hearthDisplayMD` is exactly 28/semibold).
    private var headlineBlock: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(dateEyebrow)
                .font(.hearthCaptionMono)
                .foregroundColor(.inkPrimary)
            Text(parentDisplayName.isEmpty
                 ? "Here’s today:" : "Hey \(parentDisplayName), Here’s today:")
                .font(.hearthDisplayMD)
                .foregroundColor(.inkPrimary)
                .lineSpacing(14)   // 1.5 line-height on 28pt, per the frame
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(.leading, .hearth300)
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - COACH

    /// The COACH card (measured `29:3726`): Heisman paper `#FCFBF8` ground
    /// (`bgCoachBanner`), r=28, pad 30, stack gap 8; header glyph + Inter 800
    /// 16 teal label; message Inter 400 17/26 muted; underlined action link.
    private var coachCard: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            HStack(spacing: .hearth400) {
                // The frame's coach glyph (`I29:3728;87:354`, 12.15×14.94) is
                // the shipped `CoachMark` drawing at a slightly different crop;
                // one template asset serves both (fidelity playbook rule 3).
                Image("CoachMark")
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 13, height: 15)
                    .foregroundColor(.accentOnCanvas)
                    .accessibilityHidden(true)
                // "COACH  • Just now" is ONE run, one color — Inter 800 16
                // in the accent (`29:3729`).
                Text("COACH  • \(coachHeaderDetail)")
                    .font(.hearthSectionHeader)
                    .foregroundColor(.accentOnCanvas)
                    .lineLimit(1)
                Spacer(minLength: 0)
            }

            if let nudge = today.nudge {
                Text(nudge.body)
                    .font(.hearthBodyLG)
                    .lineSpacing(.hearthLineBodyLG)
                    .foregroundColor(.inkMuted)
                    .fixedSize(horizontal: false, vertical: true)

                Button { openCoach() } label: {
                    HomeUnderlineLink(title: nudge.ctaTitle)
                }
                .buttonStyle(.plain)
            } else {
                // Deliberately NOT fake coaching copy: the backend refuses to
                // fabricate a nudge, so "nothing here" genuinely means the
                // coach hasn't met this family yet.
                Text(today.hasLoadedNudge
                     ? "Your coach hasn't written to you yet. Tell it about your week and the first nudge lands here."
                     : "Checking in with your coach…")
                    .font(.hearthBodyLG)
                    .lineSpacing(.hearthLineBodyLG)
                    .foregroundColor(.inkMuted)
                    .fixedSize(horizontal: false, vertical: true)

                if today.hasLoadedNudge {
                    Button { openCoach() } label: {
                        HomeUnderlineLink(title: "Talk to your coach")
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(30)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: .hearthRadiusSection, style: .continuous)
                .fill(Color.bgCoachBanner)
        )
    }

    private var coachHeaderDetail: String {
        today.nudge?.timeOfDayLabel ?? HomeWhen.partOfDay(Date())
    }

    /// Open the coaching conversation. Home isn't the Coach tab's owner, so it
    /// presents the same `AgentView` over its own chat view model; the thread
    /// lives server-side, so nothing is lost.
    private func openCoach() {
        Analytics.capture("home_coach_nudge_tapped",
                          ["has_nudge": today.nudge != nil])
        if coachVM == nil {
            let vm = ChatViewModel(configuration: configuration, mode: .coaching)
            vm.setUserID(username)
            coachVM = vm
        }
        isShowingCoach = true
    }

    // MARK: - MVP Editorial

    private var editorialItems: [ForYouItem] { Array(contentVM.forYouItems.prefix(2)) }

    /// The MVP Editorial card (measured `29:2833`): `bgCoachBanner` ground,
    /// r=28, pad 30; icon + "MVP Editorial" masthead in the eyebrow grey
    /// (mixed case in the frame — NOT uppercased); a hero story, a hairline,
    /// a second story, and the "See all" pill bottom-right of a 57pt row.
    /// Content is whatever the content API returned — never fabricated.
    private var editorialCard: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 9) {
                Image("HomeIcon-forYou")
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 22, height: 15)
                    .foregroundColor(.inkEyebrow)
                    .accessibilityHidden(true)
                Text("MVP Editorial")
                    .font(.hearthSectionHeader)
                    .foregroundColor(.inkEyebrow)
                Spacer(minLength: 0)
            }
            .padding(.bottom, 6)

            if editorialItems.isEmpty {
                Text(contentVM.isLoading
                     ? "Pulling together a few reads…"
                     : "Reading picks land here once the library loads.")
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkMuted)
            } else {
                ForEach(Array(editorialItems.enumerated()), id: \.element.id) { index, item in
                    editorialStory(item, isHero: index == 0,
                                   drawsDivider: index == 0 && editorialItems.count > 1)
                }

                // Action container (`29:2848`): a 57pt row with the button
                // sitting on its floor.
                NavigationLink(value: ForYouRoute()) {
                    HomeSeeAllButton()
                }
                .buttonStyle(.plain)
                .padding(.top, .hearth600)
            }
        }
        .padding(30)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: .hearthRadiusSection, style: .continuous)
                .fill(Color.bgCoachBanner)
        )
    }

    /// "Care · 2 min" — category + read time from the article record; the
    /// second story prefers its editorial kicker ("WE TRIED IT") when the
    /// backend has one. Nil when the record carries neither — the eyebrow
    /// collapses rather than inventing copy.
    private func editorialEyebrow(_ item: ForYouItem, isHero: Bool) -> String? {
        let article = contentVM.articleData(item.id)
        if !isHero, let kicker = article?.kicker,
           !kicker.trimmingCharacters(in: .whitespaces).isEmpty {
            return kicker
        }
        var parts: [String] = []
        if let category = article?.category, !category.isEmpty {
            parts.append(category.replacingOccurrences(of: "-", with: " ").capitalizedFirst)
        }
        if let readTime = item.readTime, !readTime.isEmpty {
            parts.append(readTime)
        }
        return parts.isEmpty ? nil : parts.joined(separator: " · ")
    }

    @ViewBuilder
    private func editorialStory(_ item: ForYouItem, isHero: Bool, drawsDivider: Bool) -> some View {
        NavigationLink(value: ArticleRoute(id: item.id)) {
            VStack(alignment: .leading, spacing: 9) {
                if let eyebrow = editorialEyebrow(item, isHero: isHero) {
                    Text(eyebrow)
                        .font(.hearthBodySMBold)
                        .foregroundColor(.inkEyebrow)
                }
                VStack(alignment: .leading, spacing: isHero ? 14 : 13) {
                    // Hero headline is the frame's charcoal `#4A4741`
                    // (`29:2841`); the second story's is ink/primary
                    // (`29:2846`) — the frame draws them differently and the
                    // difference is kept (fidelity rule 2).
                    Text(item.title)
                        .font(.hearthDisplaySM)
                        .tracking(-0.38)
                        .foregroundColor(isHero ? .bgButtonFunnel : .inkPrimary)
                        .multilineTextAlignment(.leading)
                        .fixedSize(horizontal: false, vertical: true)
                    if !item.subtitle.isEmpty {
                        Text(item.subtitle)
                            .font(.hearthBodySM)
                            .foregroundColor(.inkPrimary)
                            .multilineTextAlignment(.leading)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.bottom, drawsDivider ? .hearth800 : 0)
            .overlay(alignment: .bottom) {
                if drawsDivider {
                    Rectangle()
                        .fill(Color.borderInputPill)
                        .frame(height: 1)
                }
            }
            .padding(.bottom, drawsDivider ? .hearth600 : 0)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Shared dashboard chrome

/// Filled teal CTA — kept for the legal re-accept banner's "Agree" button
/// (a compliance surface the Heisman frame doesn't draw).
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

/// "See all" — Heisman paper fill + teal stroke, r≈10 (measured `29:2849`:
/// px 12.5 py 8.3, Inter 800 13.35 teal).
struct HomeSeeAllButton: View {
    var body: some View {
        Text("See all")
            .font(.hearthButtonLabel)
            .foregroundColor(.accentOnCanvas)
            .padding(.horizontal, 12.5)
            .padding(.vertical, 8.3)
            .background(Color.bgCoachBanner)
            .overlay(
                RoundedRectangle(cornerRadius: .hearthRadiusSeeAll, style: .continuous)
                    .strokeBorder(Color.accentOnCanvas, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusSeeAll, style: .continuous))
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
        // iOS 26.4 glass chrome: repaint the nav container too — see HearthNavGround.swift.
        .hearthNavGround(.bgCanvas)
        .toolbarBackground(Color.bgCanvas, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
        .withContentNavigationDestinations()
    }
}
