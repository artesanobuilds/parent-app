import SwiftUI
import UIKit

/// The "Plan" tab: the activity plan (board, calendar, discovery) plus "Ask the
/// coach". Mirrors the app's other tabs: self-contained `NavigationStack`,
/// Hearth tokens, view model injected from `MainTabView`.
///
/// Sprint-2 restructure: two top-level segments (`Plan | Ask the coach`) replace
/// the old four (`Chat / Discover / Activities / Calendar`) — Discover collapsed
/// into a search row, Activities became the board, Calendar became the Timeline
/// view mode. **"Chief of Staff" is retired from user-facing copy**: coach and
/// planner are ONE agent now, so the UI stops implying two. Backend `/cos/*`
/// paths keep their names.
struct PlanView: View {
    @ObservedObject var viewModel: PlanViewModel
    @ObservedObject var cosVM: CosChatViewModel
    let configuration: ServerConfiguration
    let userID: String

    @State private var segment: PlanSegment = .plan
    @State private var showIngest = false
    @State private var showSortFilter = false
    // Vertical chip filter on the board (attribute, never navigation) and the
    // "Plan something" door sheet (the five doors behind ONE disclosure).
    @State private var typeFilter: String?
    /// Selected lifecycle-stage key from the status chips (nil = All). Separate
    /// axis from `typeFilter` — see `statusFilterChips`.
    @State private var stageFilter: String?
    /// "Edit kids and interests" on the empty state opens the profile hub.
    @State private var isShowingProfileHub = false
    /// The summary strip's "View" expands the callouts inline.
    @State private var isShowingSummaryDetail = false
    @State private var showDoors = false
    // One-time board explainer (self-documenting first run) — persists dismissal.
    @AppStorage("plan_board_explainer_seen") private var boardExplainerSeen = false
    // Confirm-gated destructive actions on the board.
    @State private var passTarget: BoardActivity?
    @State private var deleteTarget: BoardActivity?
    @State private var showResetConfirm = false
    // Phase 3b export/share: a prepared file or link URL handed to the share sheet.
    @State private var shareItem: ShareItem?
    @State private var isPreparingShare = false

    /// A URL (exported .xlsx file or a share link) to present in the system
    /// share sheet. Identifiable so `.sheet(item:)` drives it.
    struct ShareItem: Identifiable {
        let id = UUID()
        let url: URL
    }

    /// Sprint-2: top-level Plan | Ask the coach toggle.
    enum PlanSegment: String, CaseIterable, Identifiable {
        case plan, coach
        var id: String { rawValue }
        var label: String {
            switch self {
            case .plan: return "Plan"
            case .coach: return "Ask the coach"
            }
        }
    }

    /// Sprint-2: List | Timeline view mode under Plan.
    enum ViewMode: String, CaseIterable, Identifiable {
        case list, timeline
        var id: String { rawValue }
        var label: String {
            switch self {
            case .list: return "List"
            case .timeline: return "Timeline"
            }
        }
    }

    @State private var viewMode: ViewMode = .list
    @State private var searchCollapsed = true

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                header
                segmentPicker
                segmentBody
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .sheet(isPresented: $showIngest) {
                IngestView(viewModel: viewModel)
            }
            .sheet(isPresented: $isShowingProfileHub, onDismiss: {
                // Kids and interests drive discovery, so the plan re-fetches on
                // return rather than trusting what it had before the edit.
                Task { await viewModel.loadPlan() }
            }) {
                NavigationStack {
                    FamilySettingsView(configuration: configuration, userID: userID)
                }
            }
            .sheet(isPresented: $showDoors) {
                doorSheet
                    .presentationDetents([.medium])
                    .presentationDragIndicator(.visible)
            }
            .sheet(isPresented: $showSortFilter) {
                sortFilterSheet
                    .presentationDetents([.medium, .large])
                    .presentationDragIndicator(.visible)
            }
            .sheet(item: $shareItem) { item in
                ShareSheet(items: [item.url])
            }
            .confirmationDialog(
                passTarget.map { "Pass on \($0.name)?" } ?? "",
                isPresented: Binding(get: { passTarget != nil },
                                     set: { if !$0 { passTarget = nil } }),
                titleVisibility: .visible
            ) {
                if let target = passTarget {
                    Button("Pass — clear its to-dos", role: .destructive) {
                        passTarget = nil
                        Task { await viewModel.advance(target, to: "declined",
                                                       rationale: "Passed from the board") }
                    }
                    Button("Cancel", role: .cancel) { passTarget = nil }
                }
            } message: {
                Text("It moves to Not doing and its open to-dos are cleared. You can reconsider later, but the to-dos won't come back.")
            }
            .confirmationDialog(
                deleteTarget.map { "Delete \($0.name) forever?" } ?? "",
                isPresented: Binding(get: { deleteTarget != nil },
                                     set: { if !$0 { deleteTarget = nil } }),
                titleVisibility: .visible
            ) {
                if let target = deleteTarget {
                    Button("Delete forever", role: .destructive) {
                        deleteTarget = nil
                        Task { await viewModel.deleteForever(target) }
                    }
                    Button("Cancel", role: .cancel) { deleteTarget = nil }
                }
            } message: {
                Text("Permanently removes it along with its to-dos and calendar entries.")
            }
            .confirmationDialog(
                "Start over?",
                isPresented: $showResetConfirm,
                titleVisibility: .visible
            ) {
                Button("Yes, clear my plan", role: .destructive) {
                    Task { await viewModel.resetPlan() }
                }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("Clears your plan — activities, to-dos, calendar, coverage, and discovery results. Your family profile and chats stay. Calendar events already synced to Google aren't removed.")
            }
            .navigationDestination(for: CandidateRoute.self) { route in
                CandidateDetailView(candidate: route.candidate)
            }
            .navigationDestination(for: BoardActivityRoute.self) { route in
                BoardActivityDetailView(
                    activity: route.activity,
                    onCompleteTodo: { todoId in
                        Task { await viewModel.completeTodo(todoId) }
                    },
                    onAskCoach: { a in
                        withAnimation(.hearthFast) { segment = .coach }
                        cosVM.send("Help me with \(a.name)")
                    }
                )
            }
            .task {
                viewModel.userId = userID
                viewModel.baseURL = configuration.baseURL
                cosVM.setUserID(userID)
                await viewModel.prefillLocation()
                await viewModel.reattachIfNeeded()  // resume an in-flight discovery
                await viewModel.loadPlan()
            }
            .onAppear {
                viewModel.userId = userID
                viewModel.baseURL = configuration.baseURL
                cosVM.setUserID(userID)
            }
            // Keep the plan segment fresh. Reload when switching to it.
            .onChange(of: segment) { _, newValue in
                if newValue == .plan {
                    Task { await viewModel.loadPlan() }
                }
            }
            // … and right after a chat turn finishes, so a chat-driven change shows
            // up even while the parent is already on (or returns to) those segments.
            .onChange(of: cosVM.isSending) { wasSending, isSending in
                if wasSending && !isSending {
                    Task { await viewModel.loadPlan() }
                }
            }
        }
    }

    // MARK: - Header

    /// Measured `planner 01`/`02` (`1026:10488`/`1026:10533`): the hero icon
    /// sits CENTERED ABOVE a centered "MVP Planner" title (48x48 icon) on
    /// the two empty states. `planner 3` (content state, board non-empty)
    /// has NO title row at all — it goes straight from the tab bar into the
    /// segmented control. Compromise for the content states (not literally
    /// in the frame): keep a compact leading-icon/title/share row rather
    /// than deleting the share menu, a real shipped affordance.
    @ViewBuilder
    private var header: some View {
        if boardIsEmpty {
            VStack(spacing: .hearth300) {
                HStack {
                    Spacer()
                    planMenu
                }
                Image("PlannerIcon-hero")
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 48, height: 48)
                    .foregroundColor(.accentDefault)
                Text("MVP Planner")
                    .font(.hearthDisplayMD)
                    .foregroundColor(.inkPrimary)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)
            .padding(.horizontal, .hearth700)
            .padding(.top, .hearth700)
        } else {
            HStack(spacing: .hearth400) {
                Image("PlannerIcon-hero")
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 24, height: 24)
                    .foregroundColor(.accentDefault)
                Text("MVP Planner")
                    .font(.hearthDisplayMD)
                    .foregroundColor(.inkPrimary)
                Spacer()
                planMenu
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, .hearth700)
            .padding(.top, .hearth700)
        }
    }

    /// Export the plan as a spreadsheet or mint a scoped read-only share link
    /// (Phase 3b). Result is handed to the system share sheet.
    private var planMenu: some View {
        Menu {
            Button { exportPlan() } label: {
                Label("Export spreadsheet", systemImage: "tablecells")
            }
            Menu {
                Button { sharePlan(scope: "full") } label: {
                    Label("Full plan", systemImage: "doc.text")
                }
                Button { sharePlan(scope: "logistics") } label: {
                    Label("Nanny · schedule & coverage", systemImage: "figure.2.and.child.holdinghands")
                }
                Button { sharePlan(scope: "therapy") } label: {
                    Label("Therapist · therapy schedule", systemImage: "heart.text.square")
                }
            } label: {
                Label("Share a link", systemImage: "link")
            }
            Divider()
            Button(role: .destructive) { showResetConfirm = true } label: {
                Label("Start over…", systemImage: "arrow.counterclockwise")
            }
        } label: {
            Image(systemName: "square.and.arrow.up")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(.accentDefault)
        }
        .disabled(isPreparingShare)
    }

    private func exportPlan() {
        guard let base = viewModel.baseURL else { return }
        isPreparingShare = true
        Task {
            defer { isPreparingShare = false }
            if let url = try? await PlanService.exportXlsx(baseURL: base, userID: userID) {
                shareItem = ShareItem(url: url)
            }
        }
    }

    private func sharePlan(scope: String) {
        guard let base = viewModel.baseURL else { return }
        isPreparingShare = true
        Task {
            defer { isPreparingShare = false }
            if let link = try? await PlanService.createShareLink(baseURL: base, userID: userID, scope: scope),
               let url = URL(string: link.url) {
                shareItem = ShareItem(url: url)
            }
        }
    }

    // MARK: - Segments

    /// Activities whose next step still needs the parent to do something. Drives
    /// the count badge on the Plan segment.
    private var needsActionCount: Int {
        viewModel.board?.stages
            .flatMap { $0.activities }
            .filter { $0.nextStep.action != "none" }
            .count ?? 0
    }

    /// One pill in the segment track. Extracted because inlining it made
    /// `segmentPicker`'s body long enough that the type-checker gave up — which
    /// SwiftUI reports as "unable to type-check in reasonable time", not as a
    /// size problem.
    /// Measured `1026:10490`/`1026:10535`: each segment carries its own
    /// leading glyph — `PlannerIcon-planEdit` for Plan, `CoachMark` for Ask
    /// the coach — not text alone.
    private func segmentIcon(_ seg: PlanSegment) -> some View {
        Group {
            switch seg {
            case .plan:
                Image("PlannerIcon-planEdit")
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 16, height: 16)
            case .coach:
                Image("CoachMark")
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 12, height: 15)
            }
        }
    }

    @ViewBuilder
    private func segmentButton(_ seg: PlanSegment) -> some View {
        let selected = segment == seg
        let badge = seg == .plan ? needsActionCount : 0
        Button {
            segment = seg
        } label: {
            HStack(spacing: .hearth300) {
                segmentIcon(seg)
                Text(seg.label)
                    .font(.hearthBodySMBold)
                if badge > 0 {
                    Text("\(badge)")
                        .font(.hearthLabel)
                        .foregroundColor(.inkOnCard)
                        .padding(.horizontal, .hearth300)
                        .padding(.vertical, 1)
                        .background(Color.accentDeep, in: Capsule())
                }
            }
            .foregroundColor(.accentOnCanvas)
            .frame(maxWidth: .infinity)
            .padding(.vertical, .hearth400)
            .background(Capsule().fill(selected ? Color.bgElevated : Color.clear))
        }
        .buttonStyle(.plain)
        .accessibilityLabel(badge > 0 ? "\(seg.label), \(badge) need action" : seg.label)
        .accessibilityAddTraits(selected ? [.isSelected, .isButton] : .isButton)
    }

    /// Measured `planner 3` / `planner 5`: a pill TRACK (`bg/selected`, r=100,
    /// 2pt inset) with a white selected pill, not a system segmented control.
    /// It has to be custom because the design puts a count badge inside the
    /// "Plan" label — a `.pickerStyle(.segmented)` renders only text and images,
    /// so a badge placed there would silently never appear.
    private var segmentPicker: some View {
        HStack(spacing: .hearth300) {
            ForEach(PlanSegment.allCases) { seg in
                segmentButton(seg)
            }
        }
        .padding(2)
        .background(Capsule().fill(Color.bgSelected))
        .padding(.horizontal, .hearth700)
        .padding(.top, .hearth500)
        .padding(.bottom, .hearth400)
        .background(Color.bgCanvas)
    }

    @ViewBuilder
    private var segmentBody: some View {
        switch segment {
        case .coach:
            CosChatView(viewModel: cosVM, doors: viewModel.doors)

        case .plan:
            ScrollViewReader { proxy in
            ScrollView {
                // Empty-plan state renders ONLY planner 01's chrome (hero +
                // "Nothing planned yet?" + find-activities card + flyer card
                // + footer) — the summary strip, List|Timeline toggle, status
                // chips, and collapsed search row are content-state
                // scaffolding the frame doesn't draw when there's nothing to
                // show yet (round 3: this was leaking through before).
                // `discoverySection` (loading spinner → candidate list) used
                // to render ONLY in the empty-plan branch, so saving a first
                // candidate — which flips `boardIsEmpty` false via
                // `loadPlan()` — swapped the whole view to the content
                // branch and the results (still sitting in
                // `viewModel.candidates`) had no renderer left: search
                // looked "dead" the moment the plan had anything in it.
                // Both branches now render it under the same gate.
                let showDiscovery = viewModel.isDiscovering || !viewModel.candidates.isEmpty
                    || viewModel.errorMessage != nil || viewModel.completedEmpty
                if boardIsEmpty {
                    VStack(alignment: .leading, spacing: .hearth700) {
                        planEmptyState
                        if showDiscovery {
                            discoverySection
                                .id("discoverySection")
                        }
                    }
                    .padding(.horizontal, .hearth700)
                    .padding(.top, .hearth500)
                    .padding(.bottom, .hearth900)
                } else {
                    VStack(alignment: .leading, spacing: .hearth700) {
                        if let summary = viewModel.summary {
                            summaryStrip(summary)
                        }
                        viewModeToggle
                        statusFilterChips
                        collapsedSearchRow
                        if showDiscovery {
                            discoverySection
                                .id("discoverySection")
                        }
                        if viewMode == .list {
                            boardSection
                            planSomethingNewButton
                        } else {
                            calendarSection
                            if viewModel.calendarWeeks.isEmpty {
                                emptyState(
                                    icon: "calendar",
                                    title: "Your calendar is empty",
                                    message: "Once you confirm camps and activities, your week-by-week plan appears here."
                                )
                            }
                        }
                    }
                    .padding(.horizontal, .hearth700)
                    .padding(.top, .hearth500)
                    .padding(.bottom, .hearth900)
                }
            }
            .scrollDismissesKeyboard(.immediately)
            .refreshable { await viewModel.loadPlan() }
            // The loading state (and its eventual result) can render below
            // the fold on most devices — tapping "Find activities" and
            // getting no visible reaction ("nothing happens") was a real bug
            // report, not a search failure. Scroll it into view the moment a
            // search starts, regardless of which branch is on screen.
            .onChange(of: viewModel.isDiscovering) { _, isDiscovering in
                if isDiscovering {
                    withAnimation(.hearthBase) {
                        proxy.scrollTo("discoverySection", anchor: .top)
                    }
                }
            }
            }
        }
    }

    private var boardIsEmpty: Bool {
        viewModel.board?.stages.allSatisfy { $0.activities.isEmpty } ?? true
    }

    private func emptyState(icon: String, title: String, message: String) -> some View {
        VStack(spacing: .hearth400) {
            Image(systemName: icon)
                .font(.system(size: 30, weight: .light))
                .foregroundColor(.inkMuted)
            Text(title)
                .font(.hearthBodyLG.weight(.semibold))
                .foregroundColor(.inkPrimary)
            Text(message)
                .font(.hearthBodyMD)
                .foregroundColor(.inkSecondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, .hearth1000)
    }

    // MARK: - Sprint-2 Components

    @ViewBuilder
    private func summaryStrip(_ summary: PlanSummary) -> some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            summaryStripLine(summary)
            if isShowingSummaryDetail {
                summaryStripDetail(summary)
            }
        }
        .padding(.hearth500)
        .background(
            RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                .fill(Color.bgElevated)
        )
    }

    /// The three callouts the strip's numbers stand for. Reuses the summary the
    /// server already computes (`planning.build_plan_summary`) — pending
    /// eligibility, coverage gaps and schedule conflicts were each their own
    /// section before the sprint-2 re-order and would otherwise be lost.
    @ViewBuilder
    private func summaryStripDetail(_ summary: PlanSummary) -> some View {
        Divider().background(Color.borderHairline)
        VStack(alignment: .leading, spacing: .hearth300) {
            // Same field mapping as the original `planSummarySection` — neither
            // PendingEligibility nor CoverageGap carries a server-rendered line,
            // so the label is composed here exactly as it always was.
            calloutList(
                "Pending eligibility",
                items: (summary.pendingEligibility ?? []).map { $0.name ?? "Activity" },
                tone: .statusWarning
            )
            calloutList(
                "Coverage gaps",
                items: (summary.coverageGaps ?? []).map { gap in
                    [gap.kidName, gap.task].compactMap { $0 }.joined(separator: " · ")
                        + (gap.reason.map { " — \($0)" } ?? "")
                },
                tone: .statusError
            )
            calloutList(
                "Schedule conflicts",
                items: (summary.conflicts ?? []).compactMap { $0.detail ?? $0.reason },
                tone: .statusError
            )
            if !viewModel.todos.isEmpty {
                calloutList("Follow-ups",
                            items: viewModel.todos.prefix(5).map { $0.title },
                            tone: .accentOnCanvas)
            }
            if summaryDetailIsEmpty(summary) {
                Text("Nothing needs your attention right now.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
            }
        }
    }

    private func summaryDetailIsEmpty(_ summary: PlanSummary) -> Bool {
        (summary.pendingEligibility?.isEmpty ?? true)
            && (summary.coverageGaps?.isEmpty ?? true)
            && (summary.conflicts?.isEmpty ?? true)
            && viewModel.todos.isEmpty
    }

    private func summaryStripLine(_ summary: PlanSummary) -> some View {
        HStack(spacing: .hearth300) {
            let confirmedTotal = summary.cost?.confirmedTotal ?? 0
            let tbdCount = summary.cost?.tbdCount ?? 0
            let tracked = viewModel.activities.count
            let nextSteps = viewModel.board?.stages
                .flatMap { $0.activities }
                .filter { $0.nextStep.action != "none" }
                .count ?? 0

            Text("\(nextSteps) next steps this week · $\(Int(confirmedTotal)) confirmed · \(tbdCount) cost TBD · \(tracked) tracked")
                .font(.hearthBodyMD)
                .foregroundColor(.inkPrimary)
                .lineLimit(1)
                .minimumScaleFactor(0.9)
            Spacer(minLength: 0)
            // "N next steps this week" is a count of follow-ups, so View shows
            // them. It expands inline rather than pushing a screen — the detail
            // is three lines, and a push would leave the board behind.
            Button {
                withAnimation(.hearthBase) { isShowingSummaryDetail.toggle() }
            } label: {
                HStack(spacing: 4) {
                    Text(isShowingSummaryDetail ? "Hide" : "View")
                        .font(.hearthBodySM.weight(.semibold))
                        .foregroundColor(.accentOnCanvas)
                    Image(systemName: "arrow.right")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(.accentOnCanvas)
                }
            }
            .buttonStyle(.plain)
        }
    }

    private var viewModeToggle: some View {
        Picker("View", selection: $viewMode) {
            ForEach(ViewMode.allCases) { mode in
                Text(mode.label).tag(mode)
            }
        }
        .pickerStyle(.segmented)
    }

    /// `All / New / Deciding (3) / Needs action (1)` — filters the board to ONE
    /// lifecycle stage.
    ///
    /// This is a separate axis from `typeFilter`, which filters by *vertical*
    /// (camp/class/outing/trip). Both were briefly wired to `typeFilter`, which
    /// made "All" clear the vertical filter and the stage chips do nothing at
    /// all — a chip showing a live count that ignores your tap.
    private var statusFilterChips: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: .hearth300) {
                statusChip("All", count: nil, selected: stageFilter == nil) {
                    stageFilter = nil
                }
                if let board = viewModel.board {
                    ForEach(board.stages) { stage in
                        let count = stage.activities.count
                        if count > 0 {
                            statusChip(stage.title, count: count,
                                       selected: stageFilter == stage.key) {
                                // Tapping the selected chip clears it, so the
                                // row never traps you in one stage.
                                stageFilter = stageFilter == stage.key ? nil : stage.key
                            }
                        }
                    }
                }
            }
        }
    }

    private func statusChip(_ label: String, count: Int?, selected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: 4) {
                Text(label)
                    .font(.hearthChipLabel)
                    .foregroundColor(selected ? Color.inkOnCard : Color.accentDefault)
                if let c = count {
                    Text("(\(c))")
                        .font(.hearthChipLabel)
                        .foregroundColor(selected ? Color.inkOnCard : Color.accentDefault)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(
                Capsule()
                    .fill(selected ? Color.accentDefault : Color.bgCoachBanner)
                    .overlay(
                        Capsule()
                            .stroke(selected ? Color.clear : Color.accentDefault, lineWidth: 0.82)
                    )
            )
        }
        .buttonStyle(.plain)
    }

    /// The collapsed header is a plain `Button` (toggles `searchCollapsed`
    /// only). When expanded, `findActivitiesCard` — itself full of interactive
    /// controls (TextField, menus, a submit Button) — renders as a SIBLING
    /// below, never nested inside another Button's label. Nesting was the
    /// bug: an interactive form inside a Button's label makes every tap
    /// inside it race the outer Button's tap recognizer, so the embedded
    /// "Find activities" submit was effectively dead once the plan had any
    /// content (see the fidelity playbook's Button-in-Button trap).
    @ViewBuilder
    private var collapsedSearchRow: some View {
        Button {
            withAnimation(.hearthBase) { searchCollapsed.toggle() }
        } label: {
            HStack(spacing: .hearth400) {
                // Measured `1026:10564` ('seach large'): the exported search
                // vector at 20×20 in the card family's moss green — was an SF
                // magnifier in teal.
                Image("PlannerIcon-search")
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 20, height: 20)
                    .foregroundColor(Color.plannerSearchIcon)
                VStack(alignment: .leading, spacing: 2) {
                    Text("Find more activities")
                        .font(.hearthBodyMD.weight(.semibold))
                        .foregroundColor(.inkPrimary)
                    // The design's subtitle reads "98332 · 25 mi · camps,
                    // classes & more". 98332 is Greg's SAMPLE zip — never
                    // fall back to it, or a parent who hasn't set a location
                    // reads a stranger's postcode as their own.
                    Text(
                        viewModel.locationQuery.isEmpty
                            ? "Set a location · camps, classes & more"
                            : "\(viewModel.locationQuery) · \(viewModel.radiusMiles) mi · camps, classes & more"
                    )
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkSecondary)
                }
                Spacer()
                Image(systemName: searchCollapsed ? "chevron.down" : "chevron.up")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(.inkMuted)
            }
            .padding(.hearth500)
            .background(
                RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                    .fill(Color.bgElevated)
            )
        }
        .buttonStyle(.plain)

        if !searchCollapsed {
            findActivitiesCard
        }
    }

    /// Category chips for the empty-state find-activities card (measured
    /// `1026:10507`–`1026:10510`: Camp / Activity / Trip / Classes, single
    /// select, Camp pre-selected in the frame). Camp and Activity share the
    /// same tent glyph in the source file — reusing `HomeIcon-camp` for both
    /// is correct, not a mistake.
    private static let planTypeFilters: [(key: String, label: String, icon: String)] = [
        ("camp", "Camp", "HomeIcon-camp"),
        ("activity", "Activity", "HomeIcon-camp"),
        ("trip", "Trip", "PlannerIcon-trip"),
        ("class", "Classes", "PlannerIcon-classes")
    ]

    /// Measured `planner 01` (`1026:10476`): hero + "Nothing planned yet?" +
    /// find-activities card (zip/radius/category chips/Find button) + flyer
    /// card + "Planning for {kids}" footer. This is the ONLY chrome the
    /// frame draws for an empty plan — no summary strip, no List|Timeline
    /// toggle, no status chips (those are `segmentBody`'s job to hide, see
    /// its `boardIsEmpty` branch).
    private var planEmptyState: some View {
        VStack(spacing: .hearth700) {
            VStack(spacing: .hearth200) {
                // Measured `1026:10492` is ONE rich-text node (bold lead-in,
                // regular continuation) that the plain-text walker collapses
                // to a single Inter 400/15 run — the earlier pass took that
                // literally and rendered a 38pt Fraunces headline here, which
                // both clipped against the segmented control above AND
                // doesn't match the frame's actual small-bold-caption look.
                Text("Nothing planned yet?")
                    .font(.hearthBodyMD.weight(.bold))
                    .foregroundColor(.inkPrimary)
                    .multilineTextAlignment(.center)
                    .padding(.top, .hearth500)
                Text("Find a few options — nothing is booked or shared until you say so.")
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkPrimary)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)

            findActivitiesCard
            flyerCard

            VStack(spacing: .hearth200) {
                if let firstKid = viewModel.calendarKids.first {
                    let kids = viewModel.calendarKids.joined(separator: " & ")
                    Text("Planning for \(kids)")
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkPrimary)
                } else {
                    Text("Planning for your kids")
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkPrimary)
                }
                // Opens the profile hub rather than a single kid's sheet:
                // `KidSettingsSheet` needs one kid as its target and this copy
                // is plural ("kids and interests"), so the hub — which lists
                // every kid and their interests — is the honest destination.
                Button { isShowingProfileHub = true } label: {
                    Text("Edit kids and interests")
                        .font(.hearthBodySM)
                        .foregroundColor(.accentOnCanvas)
                }
                .buttonStyle(.plain)
            }
            .frame(maxWidth: .infinity)
        }
        .frame(maxWidth: .infinity)
    }

    /// The find-activities card itself (`1026:10493`: `#F5F3EF` fill,
    /// `#A4A4A4` stroke w1, r12). Wires to the SAME `viewModel.locationQuery`
    /// / `radiusMiles` / `startDiscovery()` the existing discovery flow
    /// already uses — no new backend call, just the frame's compact shape
    /// instead of the full radius/candidate-count/focus form.
    private var findActivitiesCard: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            HStack(spacing: .hearth300) {
                Image("PlannerIcon-search")
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 20, height: 20)
                    .foregroundColor(Color.plannerSearchIcon)
                Text("Find activities")
                    .font(.hearthBodySMBold)
                    .foregroundColor(Color.plannerSearchText)
            }

            HStack(spacing: .hearth300) {
                HStack(spacing: .hearth300) {
                    Text("Where to:")
                        .font(.hearthBodySMBold)
                        .foregroundColor(Color.plannerSearchText)
                    TextField("Zip code...", text: $viewModel.locationQuery)
                        .font(.hearthBodySMBold)
                        .foregroundColor(.inkPrimary)
                        .keyboardType(.numbersAndPunctuation)
                        .textInputAutocapitalization(.never)
                        // Numeric keyboards have no return key — explicit
                        // dismiss (moved here from the deleted discoverPrompt).
                        .toolbar {
                            ToolbarItemGroup(placement: .keyboard) {
                                Spacer()
                                Button("Done") { hideKeyboard() }
                                    .font(.hearthBodyMD.weight(.semibold))
                                    .foregroundColor(.accentDefault)
                            }
                        }
                }
                .padding(.horizontal, .hearth400)
                .padding(.vertical, .hearth300)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                        .fill(Color.bgElevated)
                        .overlay(
                            RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                                .stroke(Color.bgSelected, lineWidth: 1)
                        )
                )

                Menu {
                    ForEach(viewModel.radiusOptions, id: \.self) { mi in
                        Button("\(mi) mi") { viewModel.radiusMiles = mi }
                    }
                } label: {
                    HStack(spacing: .hearth300) {
                        Text("\(viewModel.radiusMiles) mi")
                            .font(.hearthBodySMBold)
                            .foregroundColor(Color.plannerSearchText)
                        Image(systemName: "chevron.down")
                            .font(.system(size: 10, weight: .semibold))
                            .foregroundColor(.inkPrimary)
                    }
                    .padding(.horizontal, .hearth400)
                    .padding(.vertical, .hearth300)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .fill(Color.bgElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                                    .stroke(Color.bgSelected, lineWidth: 1)
                            )
                    )
                }
            }

            // Four chips in a fixed-width card don't reliably fit at every
            // Dynamic Type size or on every device width — "Activity" (the
            // longest label) was wrapping to two lines inside its pill
            // because a bare `HStack` compresses its widest `Text` instead
            // of scrolling. Horizontal scroll matches the same pattern
            // `statusFilterChips` already uses elsewhere in this file.
            // Trailing inset on the SCROLL CONTENT (not just the card padding)
            // — without it the last chip's edge sits flush against the
            // ScrollView's own clip boundary and its trailing rounded stroke
            // gets cropped, reading as a rendering bug rather than "more to
            // scroll". `.hearth400` mirrors the card's own edge padding.
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: .hearth200) {
                    ForEach(Self.planTypeFilters, id: \.key) { entry in
                    let selected = typeFilter == entry.key
                    Button {
                        typeFilter = selected ? nil : entry.key
                    } label: {
                        HStack(spacing: 4) {
                            Image(entry.icon)
                                .renderingMode(.template)
                                .resizable()
                                .scaledToFit()
                                .frame(width: 14, height: 14)
                            Text(entry.label)
                                .font(.hearthBodySM)
                                .lineLimit(1)
                                .fixedSize()
                        }
                        .foregroundColor(selected ? .inkOnCard : .accentOnCanvas)
                        .padding(.horizontal, .hearth400)
                        .padding(.vertical, .hearth300)
                        .background(
                            Capsule()
                                .fill(selected ? Color.accentOnCanvas : Color.bgCoachBanner)
                                .overlay(
                                    Capsule()
                                        .strokeBorder(Color.accentOnCanvas,
                                                      lineWidth: selected ? 0 : 0.92)
                                )
                        )
                    }
                    .buttonStyle(.plain)
                    }
                }
                .padding(.trailing, .hearth400)
            }

            // Shipped affordances the frame doesn't draw (from the deleted
            // discoverPrompt): result-count target + optional free-form focus.
            // One quiet row, same field treatment as the radius menu above.
            HStack(spacing: .hearth300) {
                Menu {
                    ForEach(viewModel.candidateCountOptions, id: \.self) { n in
                        Button("Up to \(n)") { viewModel.maxCandidates = n }
                    }
                } label: {
                    HStack(spacing: .hearth300) {
                        Text("Up to \(viewModel.maxCandidates)")
                            .font(.hearthBodySMBold)
                            .foregroundColor(Color.plannerSearchText)
                        Image(systemName: "chevron.down")
                            .font(.system(size: 10, weight: .semibold))
                            .foregroundColor(.inkPrimary)
                    }
                    .padding(.horizontal, .hearth400)
                    .padding(.vertical, .hearth300)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .fill(Color.bgElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                                    .stroke(Color.bgSelected, lineWidth: 1)
                            )
                    )
                }

                if !viewModel.showFocus {
                    Button {
                        withAnimation(.hearthFast) { viewModel.showFocus = true }
                    } label: {
                        Text("Add focus (optional)")
                            .font(.hearthBodySM)
                            .foregroundColor(.accentOnCanvas)
                    }
                    .buttonStyle(.plain)
                }
                Spacer(minLength: 0)
            }

            if viewModel.showFocus {
                VStack(alignment: .leading, spacing: .hearth300) {
                    HStack {
                        Text("Focus (optional)")
                            .font(.hearthBodySMBold)
                            .foregroundColor(Color.plannerSearchText)
                        Spacer()
                        Button("Remove") {
                            withAnimation(.hearthFast) {
                                viewModel.showFocus = false
                                viewModel.focusText = ""
                            }
                        }
                        .font(.hearthBodySM)
                        .foregroundColor(.inkMuted)
                    }
                    ZStack(alignment: .topLeading) {
                        if viewModel.focusText.isEmpty {
                            Text("e.g. art camps only · physical activity")
                                .font(.hearthBodySM)
                                .foregroundColor(.inkMuted)
                                .padding(.horizontal, .hearth400 + 4)
                                .padding(.vertical, .hearth300 + 8)
                        }
                        TextEditor(text: $viewModel.focusText)
                            .font(.hearthBodySM)
                            .foregroundColor(.inkPrimary)
                            .scrollContentBackground(.hidden)
                            .frame(minHeight: 60)
                            .padding(.horizontal, .hearth300)
                            .padding(.vertical, .hearth200)
                    }
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .fill(Color.bgElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                                    .stroke(Color.bgSelected, lineWidth: 1)
                            )
                    )
                }
            }

            Button {
                viewModel.startDiscovery()
            } label: {
                Text("Find activities")
                    .font(.hearthBodySMBold)
                    .foregroundColor(.inkOnCard)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, .hearth400)
                    .background(Capsule().fill(Color.accentOnCanvas))
            }
            .buttonStyle(.plain)
        }
        .padding(.hearth400)
        .background(
            RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                .fill(Color.bgCard)
                .overlay(
                    RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                        .stroke(Color.borderPlannerCard, lineWidth: 1)
                )
        )
    }

    /// Measured `1026:10513`/`1026:10515`/`1026:10516`: a plain teal camera
    /// glyph (18x16, no circle badge) + ONE paragraph of teal 13pt text in a
    /// bordered card — NOT `ingestEntry`'s circle-badge/black-title/chevron
    /// row, which is a different, older component this screen was
    /// mistakenly reusing (the reason `PlannerIcon-camera`, exported in
    /// round 3 specifically for this card, was never actually used).
    /// Same action as `ingestEntry` — one ingest entry point either way.
    private var flyerCard: some View {
        Button {
            viewModel.resetIngest()
            showIngest = true
        } label: {
            HStack(spacing: .hearth300) {
                Image("PlannerIcon-camera")
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 18, height: 16)
                Text("Paste a camp email or snap a flyer — I'll pull out the details and track it.")
                    .font(.hearthBodySM)
                    .multilineTextAlignment(.leading)
            }
            .foregroundColor(.accentOnCanvas)
            .padding(.hearth500)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                    .fill(Color.bgCard)
                    .overlay(
                        RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                            .stroke(Color.borderPlannerCard, lineWidth: 1)
                    )
            )
        }
        .buttonStyle(.plain)
    }

    private var planSomethingNewButton: some View {
        Button {
            showDoors = true
        } label: {
            HStack(spacing: .hearth400) {
                Image(systemName: "plus.circle.fill")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(.accentDefault)
                Text("Plan something new")
                    .font(.hearthBodyMD.weight(.semibold))
                    .foregroundColor(.inkPrimary)
            }
            .padding(.hearth500)
            .frame(maxWidth: .infinity)
            .background(
                RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                    .fill(Color.bgElevated)
                    .overlay(
                        RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                            .stroke(Color.borderHairline, lineWidth: 1)
                    )
            )
        }
        .buttonStyle(.plain)
    }

    // MARK: - Discovery

    @ViewBuilder
    private var discoverySection: some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            if viewModel.isDiscovering {
                discoveringCard
            } else if viewModel.candidates.isEmpty {
                // Message ONLY — the search form itself is `findActivitiesCard`,
                // which both hosts already render (`planEmptyState` on the empty
                // plan, `collapsedSearchRow`'s expansion on the content state).
                // This used to be `discoverPrompt`, a second, differently-styled
                // copy of the whole form (stacked segmented pickers, SF-symbol
                // magnifier) that had drifted from the designed card — showing
                // it here stacked two search forms on the empty screen.
                if viewModel.completedEmpty {
                    VStack(alignment: .leading, spacing: .hearth300) {
                        Text("No activities found")
                            .font(.hearthBodyLG.weight(.semibold))
                            .foregroundColor(.inkPrimary)
                        Text("Nothing came back for that area. Add or adjust your ZIP code and try again.")
                            .font(.hearthBodyMD)
                            .foregroundColor(.inkSecondary)
                    }
                }
            } else {
                candidateList
            }

            if let error = viewModel.errorMessage {
                Text(error)
                    .font(.hearthBodySM)
                    .foregroundColor(.statusError)
            }
        }
    }

    // `discoverPrompt` is GONE (round 4). It was a second, older search form —
    // "Discover activities" headline, stacked segmented pickers for radius and
    // count, an SF-symbol magnifier on the submit button — that predated the
    // measured `findActivitiesCard` and kept rendering wherever the content
    // state opened a search. One dialog now: `findActivitiesCard`, everywhere.
    // Its two extra affordances (candidate count, free-form focus) moved into
    // the card as a quiet row so no shipped functionality was dropped.

    private var discoveringCard: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            HStack(alignment: .top, spacing: .hearth400) {
                ProgressView().padding(.top, 2)
                VStack(alignment: .leading, spacing: 2) {
                    // Headline reflects what the model is doing right now:
                    // Thinking… / Planning… / Searching for <query> / Found <name>.
                    Text(viewModel.discoveryHeadline)
                        .font(.hearthBodyMD.weight(.semibold))
                        .foregroundColor(.inkPrimary)
                        .fixedSize(horizontal: false, vertical: true)
                    Text(viewModel.discoveryCountLabel)
                        .font(.hearthBodySM)
                        .foregroundColor(.accentDefault)
                }
                Spacer()
                Button("Cancel") { viewModel.cancelDiscovery() }
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
            }

            // Time expectation + live elapsed — kills the "is it frozen?" anxiety.
            HStack {
                Text(viewModel.isQueued ? "Waiting for a free research slot…"
                                        : "Usually takes 1–2 minutes.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                Spacer()
                if let started = viewModel.discoveryStartedAt, !viewModel.isQueued {
                    TimelineView(.periodic(from: .now, by: 1)) { context in
                        let secs = max(0, Int(context.date.timeIntervalSince(started)))
                        Text("\(secs / 60):\(String(format: "%02d", secs % 60)) elapsed")
                            .font(.hearthBodySM.monospacedDigit())
                            .foregroundColor(.inkMuted)
                    }
                }
            }

            // Live results filling in (skeleton → cards) instead of a bare spinner.
            if !viewModel.discoveryPreview.isEmpty {
                Divider().background(Color.borderHairline)
                VStack(alignment: .leading, spacing: .hearth300) {
                    ForEach(viewModel.discoveryPreview) { p in
                        previewRow(p)
                    }
                }
            } else if !viewModel.isQueued {
                Divider().background(Color.borderHairline)
                VStack(alignment: .leading, spacing: .hearth300) {
                    ForEach(0..<3, id: \.self) { _ in skeletonRow }
                }
            }
        }
        .padding(.hearth600)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
        .animation(.hearthFast, value: viewModel.discoveryPreview)
    }

    private func previewRow(_ p: CandidatePreview) -> some View {
        HStack(spacing: .hearth400) {
            Circle().fill(Color.accentTint).frame(width: 8, height: 8)
            VStack(alignment: .leading, spacing: 1) {
                Text(p.name ?? "Activity")
                    .font(.hearthBodySM.weight(.semibold))
                    .foregroundColor(.inkPrimary)
                    .lineLimit(1)
                let meta = [p.city, p.category].compactMap { $0 }.filter { !$0.isEmpty }.joined(separator: " · ")
                if !meta.isEmpty {
                    Text(meta).font(.hearthBodySM).foregroundColor(.inkMuted).lineLimit(1)
                }
            }
            Spacer()
            if let fit = p.fitScore {
                Text("\(Int(fit * 100))%")
                    .font(.hearthBodySM.monospacedDigit())
                    .foregroundColor(.accentDefault)
            }
        }
    }

    private var skeletonRow: some View {
        HStack(spacing: .hearth400) {
            Circle().fill(Color.borderHairline).frame(width: 8, height: 8)
            VStack(alignment: .leading, spacing: 4) {
                RoundedRectangle(cornerRadius: 4).fill(Color.borderHairline)
                    .frame(width: 160, height: 9)
                RoundedRectangle(cornerRadius: 4).fill(Color.borderHairline.opacity(0.6))
                    .frame(width: 100, height: 8)
            }
            Spacer()
        }
        .opacity(0.7)
    }

    private var candidateList: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            HStack {
                Text(viewModel.discoveryResultLabel)
                    .font(.hearthBodyLG.weight(.semibold))
                    .foregroundColor(.inkPrimary)
                Spacer()
                Button {
                    viewModel.startDiscovery()
                } label: {
                    Label("Refresh", systemImage: "arrow.clockwise")
                        .font(.hearthBodySM)
                        .foregroundColor(.accentDefault)
                }
            }

            sortFilterBar

            let shown = viewModel.sortedFilteredCandidates
            if shown.isEmpty && viewModel.hasActiveFilters {
                Text("No results match those filters.")
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkMuted)
                    .padding(.vertical, .hearth400)
            }
            ForEach(shown) { candidate in
                candidateRow(candidate)
            }
        }
    }

    /// The Save pill lives INSIDE the card now (measured planner-3 button row),
    /// so the row can't simply be a `NavigationLink` label — a `Button` nested
    /// in a `NavigationLink` label is the exact "taps conflict" trap the
    /// fidelity playbook calls out (`collapsedSearchRow` had the same bug —
    /// see Step 2). Instead the link is a hidden full-size background; the
    /// Save button on top of it captures its own taps first, everywhere else
    /// in the card falls through to the link.
    private func candidateRow(_ candidate: ActivityCandidate) -> some View {
        CandidateRow(
            candidate: candidate,
            isSaved: viewModel.isSaved(candidate),
            isSaving: viewModel.isSaving(candidate),
            onToggleSave: { Task { await viewModel.toggleSave(candidate) } }
        )
        .background(
            NavigationLink(value: CandidateRoute(candidate: candidate)) { EmptyView() }
                .opacity(0)
        )
    }

    // MARK: - Result sort & filter

    // Compact entry to the unified Sort & Filter sheet + a removable summary of
    // active filters, so state is visible without opening the sheet.
    @ViewBuilder
    private var sortFilterBar: some View {
        let hasFacets = viewModel.availableCities.count >= 2
            || viewModel.availableCategories.count >= 2
            || viewModel.availableKids.count >= 2
        if hasFacets || viewModel.candidates.count > 1 {
            VStack(alignment: .leading, spacing: .hearth300) {
                Button { showSortFilter = true } label: {
                    HStack(spacing: .hearth300) {
                        Image(systemName: "slider.horizontal.3")
                            .foregroundColor(.plannerSearchIcon)
                        Text("Sort & Filter")
                            .foregroundColor(.plannerSearchText)
                        Text("· \(viewModel.sortKey.label)")
                            .foregroundColor(.plannerSearchText.opacity(0.7))
                        Spacer()
                        if viewModel.hasActiveFilters {
                            Text("\(viewModel.activeFilterCount)")
                                .font(.hearthBodySM.weight(.bold))
                                .foregroundColor(.inkOnPhotoLight)
                                .padding(.horizontal, 8).padding(.vertical, 2)
                                .background(Capsule().fill(Color.accentDefault))
                        }
                        Image(systemName: "chevron.down").font(.caption).foregroundColor(.plannerSearchIcon)
                    }
                    .font(.hearthChipLabel)
                    .padding(.horizontal, .hearth500)
                    .padding(.vertical, .hearth400)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .fill(Color.bgCard)
                            .overlay(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                                .stroke(Color.borderPlannerCard, lineWidth: 1))
                    )
                }
                .buttonStyle(.plain)

                if viewModel.hasActiveFilters {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: .hearth300) {
                            removableChips(viewModel.selectedCities) { viewModel.selectedCities.remove($0) }
                            removableChips(viewModel.selectedCategories) { viewModel.selectedCategories.remove($0) }
                            removableChips(viewModel.selectedKids) { viewModel.selectedKids.remove($0) }
                        }
                    }
                }
            }
            .padding(.bottom, .hearth300)
        }
    }

    @ViewBuilder
    private func removableChips(_ values: Set<String>, remove: @escaping (String) -> Void) -> some View {
        ForEach(Array(values).sorted(), id: \.self) { v in
            HStack(spacing: 4) {
                Text(v).font(.hearthBodySM).foregroundColor(.inkPrimary)
                Button { withAnimation(.hearthFast) { remove(v) } } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 12)).foregroundColor(.inkMuted)
                }
                .buttonStyle(.plain)
            }
            .padding(.leading, .hearth400).padding(.trailing, 6).padding(.vertical, 5)
            .background(Capsule().fill(Color.accentTint))
        }
    }

    // The unified bottom sheet: Sort (single-select) + Filter (multi-select) with
    // a sticky "Show N results" footer.
    private var sortFilterSheet: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: .hearth700) {
                    VStack(alignment: .leading, spacing: .hearth300) {
                        Text("SORT").font(.hearthLabel).tracking(0.66).foregroundColor(.inkMuted)
                        VStack(spacing: 0) {
                            ForEach(SortKey.allCases) { key in
                                Button { withAnimation(.hearthFast) { viewModel.sortKey = key } } label: {
                                    HStack(spacing: .hearth400) {
                                        Image(systemName: key.icon).frame(width: 22).foregroundColor(.accentDefault)
                                        Text(key.label).font(.hearthBodyMD).foregroundColor(.inkPrimary)
                                        Spacer()
                                        if viewModel.sortKey == key {
                                            Image(systemName: "checkmark").foregroundColor(.accentDefault)
                                        }
                                    }
                                    .padding(.vertical, .hearth400)
                                    .contentShape(Rectangle())
                                }
                                .buttonStyle(.plain)
                                if key != SortKey.allCases.last {
                                    Divider().background(Color.borderHairline)
                                }
                            }
                        }
                        .padding(.horizontal, .hearth500)
                        .background(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous).fill(Color.bgElevated))
                    }

                    let cities = viewModel.availableCities
                    let cats = viewModel.availableCategories
                    let kids = viewModel.availableKids
                    if cities.count >= 2 || cats.count >= 2 || kids.count >= 2 {
                        VStack(alignment: .leading, spacing: .hearth500) {
                            Text("FILTER").font(.hearthLabel).tracking(0.66).foregroundColor(.inkMuted)
                            if cities.count >= 2 { facetGroup("City", cities, selection: $viewModel.selectedCities) }
                            if cats.count >= 2 { facetGroup("Type", cats, selection: $viewModel.selectedCategories) }
                            if kids.count >= 2 { facetGroup("Kid", kids, selection: $viewModel.selectedKids) }
                        }
                    }
                }
                .padding(.hearth700)
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .navigationTitle("Sort & filter")
            .navigationBarTitleDisplayMode(.inline)
            .safeAreaInset(edge: .bottom) {
                HStack(spacing: .hearth400) {
                    Button("Reset") { withAnimation(.hearthFast) { viewModel.resetSortAndFilters() } }
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkSecondary)
                    Spacer()
                    Button { showSortFilter = false } label: {
                        Text("Show \(viewModel.sortedFilteredCandidates.count) results")
                            .font(.hearthBodyMD.weight(.semibold))
                            .foregroundColor(.inkOnPhotoLight)
                            .padding(.horizontal, .hearth600).padding(.vertical, .hearth400)
                            .background(Capsule().fill(Color.accentDefault))
                    }
                    .buttonStyle(.plain)
                }
                .padding(.horizontal, .hearth700).padding(.vertical, .hearth400)
                .background(.ultraThinMaterial)
            }
        }
    }

    private func facetGroup(_ label: String, _ values: [String], selection: Binding<Set<String>>) -> some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text(label).font(.hearthBodySM.weight(.semibold)).foregroundColor(.inkSecondary)
            facetRow(values, selection: selection)
        }
    }

    private func facetRow(_ values: [String], selection: Binding<Set<String>>) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: .hearth300) {
                ForEach(values, id: \.self) { v in
                    let on = selection.wrappedValue.contains(v)
                    Button {
                        withAnimation(.hearthFast) {
                            if on { selection.wrappedValue.remove(v) }
                            else { selection.wrappedValue.insert(v) }
                        }
                    } label: {
                        Text(v)
                            .font(.hearthBodySM)
                            .foregroundColor(on ? .inkOnPhotoLight : .inkPrimary)
                            .padding(.horizontal, .hearth400)
                            .padding(.vertical, 6)
                            .background(Capsule().fill(on ? Color.accentDefault : Color.accentTint))
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    // MARK: - Lifecycle board (Considering → To register → Registered → All set)

    @ViewBuilder
    private var boardSection: some View {
        if let board = viewModel.board {
            // Vertical is an ATTRIBUTE + chip filter, never navigation: the
            // chip row appears only when the board actually spans verticals.
            let typeCounts = boardTypeCounts(board)
            let multiVertical = typeCounts.count > 1
            let nonEmpty = board.stages
                // Stage chips narrow to one stage; vertical chips narrow within
                // it. The two filters compose.
                .filter { stageFilter == nil || $0.key == stageFilter }
                .map { stage in
                    BoardStage(
                        key: stage.key, title: stage.title, blurb: stage.blurb,
                        activities: typeFilter == nil
                            ? stage.activities
                            : stage.activities.filter {
                                ($0.activityType ?? "camp") == typeFilter
                            }
                    )
                }
                .filter { !$0.activities.isEmpty }
            VStack(alignment: .leading, spacing: .hearth700) {
                if !nonEmpty.isEmpty && !boardExplainerSeen {
                    boardExplainer
                }
                if multiVertical {
                    verticalChipRow(typeCounts)
                }
                ForEach(nonEmpty) { stage in
                    stageGroup(stage, gmailConnected: board.gmailConnected,
                               showVerticalChip: multiVertical)
                }
                if let considering = nonEmpty.first(where: { $0.key == "considering" }),
                   considering.activities.count >= 2 {
                    Button {
                        // Flip to the coach segment and seed a triage request into
                        // the same (hoisted) conversation.
                        withAnimation(.hearthFast) { segment = .coach }
                        cosVM.send("Help me decide between the camps on my shortlist. Walk me through the tradeoffs (cost, eligibility, schedule conflicts, coverage) and recommend picks per kid.")
                    } label: {
                        Label("Help me decide", systemImage: "arrow.left.arrow.right")
                            .font(.hearthBodyMD.weight(.semibold))
                            .foregroundColor(.inkOnPhotoLight)
                            .padding(.horizontal, .hearth500)
                            .padding(.vertical, .hearth400)
                            .frame(maxWidth: .infinity)
                            .background(Color.accentDefault)
                            .clipShape(Capsule())
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    // MARK: - The five doors ("Plan something" disclosure)

    /// One vertical = one door, copy served by the registry via
    /// GET /cos/verticals (flags filter server-side; the client renders
    /// whatever arrives — latent verticals are just doors with no items yet).
    private var doorSheet: some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            Text("Plan something")
                .font(.hearthDisplayMD)
                .foregroundColor(.inkPrimary)
            Text("Pick a door — the coach takes it from there.")
                .font(.hearthBodySM)
                .foregroundColor(.inkSecondary)
            ForEach(viewModel.doors) { door in
                Button {
                    openDoor(door)
                } label: {
                    HStack(spacing: .hearth400) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(door.title)
                                .font(.hearthBodyMD.weight(.semibold))
                                .foregroundColor(.inkPrimary)
                            Text(door.subtitle)
                                .font(.hearthBodySM)
                                .foregroundColor(.inkSecondary)
                                .multilineTextAlignment(.leading)
                        }
                        Spacer(minLength: 0)
                        Image(systemName: "arrow.up.right")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundColor(.inkMuted)
                    }
                    .padding(.hearth500)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                            .fill(Color.bgElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                                    .stroke(Color.borderHairline, lineWidth: 1)
                            )
                    )
                }
                .buttonStyle(.plain)
            }
            Spacer(minLength: 0)
        }
        .padding(.hearth700)
        .background(Color.bgCanvas.ignoresSafeArea())
    }

    /// Door tap → the chat segment with the door's starter prompt sent as the
    /// first turn. Tap distribution (door_opened/door_converted) informs which
    /// vertical ships next.
    private func openDoor(_ door: VerticalDoor) {
        Analytics.capture("door_opened", ["door": door.key])
        showDoors = false
        withAnimation(.hearthFast) { segment = .coach }
        cosVM.send(door.starterPrompt)
        Analytics.capture("door_converted", ["door": door.key])
    }

    /// One-time first-run explainer: teaches the whole arc before the first tap
    /// (the self-documenting rule — nothing to memorize, nothing surprising).
    private var boardExplainer: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            HStack(alignment: .firstTextBaseline) {
                Text("How this works")
                    .font(.hearthBodyMD.weight(.semibold))
                    .foregroundColor(.inkPrimary)
                Spacer()
                Button { withAnimation(.hearthFast) { boardExplainerSeen = true } } label: {
                    Image(systemName: "xmark")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(.inkMuted)
                        .frame(width: 28, height: 28)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Dismiss")
            }
            Text("Save ideas → tap “We'll do it” → register → I watch the camp's emails and track payments & forms for you. Each card always shows its one next step.")
                .font(.hearthBodySM)
                .foregroundColor(.inkSecondary)
        }
        .padding(.hearth500)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: .hearthRadiusLg)
                .fill(Color.accentTint)
        )
    }

    private func stageGroup(_ stage: BoardStage, gmailConnected: Bool,
                            showVerticalChip: Bool) -> some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            HStack(alignment: .firstTextBaseline) {
                Text(stage.title)
                    .font(.hearthDisplayMD)
                    .foregroundColor(.inkPrimary)
                Spacer()
                Text("\(stage.activities.count)")
                    .font(.hearthCaptionMono)
                    .foregroundColor(.inkMuted)
            }
            // The group blurb IS the instruction — the pipeline explains itself.
            Text(stage.blurb)
                .font(.hearthBodySM)
                .foregroundColor(.inkSecondary)
            ForEach(stage.activities) { activity in
                NavigationLink(value: BoardActivityRoute(activity: activity)) {
                    BoardCardView(
                        activity: activity,
                        gmailConnected: gmailConnected,
                        busy: viewModel.mutatingIds.contains(activity.id),
                        showVerticalChip: showVerticalChip,
                        busyTodoIds: viewModel.mutatingIds,
                        onAdvance: { a, status, rationale in
                            Task { await viewModel.advance(a, to: status, rationale: rationale) }
                        },
                        onCompleteTodo: { todoId in
                            Task { await viewModel.completeTodo(todoId) }
                        },
                        onResolveInChat: { a, label in
                            withAnimation(.hearthFast) { segment = .coach }
                            cosVM.send("Help me resolve this for \(a.name): \(label)")
                        },
                        onPassConfirm: { a in passTarget = a },
                        onDeleteConfirm: { a in deleteTarget = a }
                    )
                }
                .buttonStyle(.plain)
            }
        }
    }

    /// Board-wide activity counts per vertical (canonical keys; NULL→camp).
    private func boardTypeCounts(_ board: PlanBoard) -> [(type: String, count: Int)] {
        var counts: [String: Int] = [:]
        var order: [String] = []
        for stage in board.stages {
            for activity in stage.activities {
                let t = activity.activityType ?? "camp"
                if counts[t] == nil { order.append(t) }
                counts[t, default: 0] += 1
            }
        }
        return order.map { ($0, counts[$0] ?? 0) }
    }

    private func verticalChipRow(_ counts: [(type: String, count: Int)]) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: .hearth300) {
                filterChip("All", count: counts.reduce(0) { $0 + $1.count },
                           selected: typeFilter == nil) { typeFilter = nil }
                ForEach(counts, id: \.type) { entry in
                    filterChip(BoardCardView.chipLabels[entry.type] ?? entry.type,
                               count: entry.count,
                               selected: typeFilter == entry.type) {
                        typeFilter = typeFilter == entry.type ? nil : entry.type
                    }
                }
            }
        }
    }

    private func filterChip(_ label: String, count: Int, selected: Bool,
                            action: @escaping () -> Void) -> some View {
        Button {
            withAnimation(.hearthFast) { action() }
        } label: {
            HStack(spacing: .hearth300) {
                Text(label)
                    .font(.hearthBodySM.weight(selected ? .semibold : .regular))
                Text("\(count)")
                    .font(.hearthCaptionMono)
            }
            .foregroundColor(selected ? .inkPrimary : .inkSecondary)
            .padding(.horizontal, .hearth400)
            .padding(.vertical, .hearth300)
            .background(
                Capsule()
                    .fill(selected ? Color.accentTint : Color.bgElevated)
                    .overlay(
                        Capsule().stroke(
                            selected ? Color.accentDefault : Color.borderHairline,
                            lineWidth: 1
                        )
                    )
            )
        }
        .buttonStyle(.plain)
    }

    // MARK: - Calendar (R4 — compact week×kid view)

    @ViewBuilder
    private var calendarSection: some View {
        let weeks = viewModel.calendarWeeks
        if !weeks.isEmpty {
            VStack(alignment: .leading, spacing: .hearth400) {
                Text("Calendar")
                    .font(.hearthDisplayMD)
                    .foregroundColor(.inkPrimary)
                ForEach(weeks.prefix(8), id: \.week) { wk in
                    weekCard(wk.week, entries: wk.entries)
                }
            }
        }
    }

    private func weekCard(_ week: String, entries: [CalendarEntry]) -> some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            HStack(alignment: .firstTextBaseline) {
                Text(formatWeekRange(week))
                    .font(.hearthBodyMD.weight(.semibold))
                    .foregroundColor(.inkPrimary)
                Spacer()
                Text(week)
                    .font(.hearthCaptionMono)
                    .foregroundColor(.inkMuted)
            }
            ForEach(entries) { entry in
                HStack(spacing: .hearth300) {
                    Circle()
                        .fill(entryTone(entry))
                        .frame(width: 6, height: 6)
                    if let kid = entry.kidName {
                        Text(kid)
                            .font(.hearthBodySM)
                            .foregroundColor(.inkSecondary)
                            .padding(.horizontal, .hearth300)
                            .padding(.vertical, 2)
                            .background(Capsule().fill(Color.accentTint))
                    }
                    Text(entry.title)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkPrimary)
                        .lineLimit(1)
                    Spacer(minLength: 0)
                }
            }
        }
        // Measured (sprint-2 planner cards): pad 20 — `hearth600` is the exact
        // token; the shipped card used `hearth500` (16), a tighter card than
        // every other planner surface.
        .padding(.hearth600)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    /// Olive=confirmed, amber=pending/tbd, muted=blackout/holiday.
    private func entryTone(_ entry: CalendarEntry) -> Color {
        let kind = entry.kind.lowercased()
        let status = entry.status.lowercased()
        if kind == "blackout" || kind == "holiday" { return .inkMuted }
        if status == "confirmed" { return .accentDefault }
        if ["pending", "tentative", "tbd"].contains(status) { return .statusWarning }
        return .inkSecondary
    }

    /// "Jul 6–10" (Mon–Fri) from a Monday ISO date, in UTC to avoid TZ drift.
    private func formatWeekRange(_ iso: String) -> String {
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(identifier: "UTC")!
        let parse = DateFormatter()
        parse.calendar = cal
        parse.timeZone = cal.timeZone
        parse.dateFormat = "yyyy-MM-dd"
        guard let mon = parse.date(from: String(iso.prefix(10))) else { return iso }
        let fri = cal.date(byAdding: .day, value: 4, to: mon) ?? mon
        let monFmt = DateFormatter()
        monFmt.timeZone = cal.timeZone
        monFmt.dateFormat = "MMM d"
        let sameMonth = cal.component(.month, from: mon) == cal.component(.month, from: fri)
        if sameMonth {
            let dayFmt = DateFormatter()
            dayFmt.timeZone = cal.timeZone
            dayFmt.dateFormat = "d"
            return "\(monFmt.string(from: mon))–\(dayFmt.string(from: fri))"
        }
        return "\(monFmt.string(from: mon)) – \(monFmt.string(from: fri))"
    }

    // MARK: - Plan summary

    @ViewBuilder
    private func planSummarySection(_ summary: PlanSummary) -> some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            Text("Your plan")
                .font(.hearthDisplayMD)
                .foregroundColor(.inkPrimary)

            if let cost = summary.cost {
                HStack(spacing: .hearth500) {
                    statTile(label: "Confirmed", value: currency(cost.confirmedTotal ?? 0), tone: .accentDefault)
                    statTile(label: "Cost TBD", value: "\(cost.tbdCount ?? 0)", tone: .inkSecondary)
                    statTile(label: "Tracked", value: "\(viewModel.activities.count)", tone: .inkSecondary)
                }
            }

            calloutList(
                "Pending eligibility",
                items: (summary.pendingEligibility ?? []).map { $0.name ?? "Activity" },
                tone: .statusWarning
            )
            calloutList(
                "Coverage gaps",
                items: (summary.coverageGaps ?? []).map { gap in
                    [gap.kidName, gap.task].compactMap { $0 }.joined(separator: " · ")
                        + (gap.reason.map { " — \($0)" } ?? "")
                },
                tone: .statusError
            )
            calloutList(
                "Schedule conflicts",
                items: (summary.conflicts ?? []).map { $0.detail ?? $0.reason ?? "Conflict" },
                tone: .statusWarning
            )
        }
    }

    @ViewBuilder
    private func calloutList(_ title: String, items: [String], tone: Color) -> some View {
        if !items.isEmpty {
            VStack(alignment: .leading, spacing: .hearth300) {
                Text(title.uppercased())
                    .font(.hearthLabel)
                    .tracking(0.66)
                    .foregroundColor(tone)
                ForEach(Array(items.enumerated()), id: \.offset) { _, item in
                    HStack(alignment: .top, spacing: .hearth300) {
                        Circle().fill(tone).frame(width: 6, height: 6).padding(.top, 6)
                        Text(item)
                            .font(.hearthBodyMD)
                            .foregroundColor(.inkPrimary)
                    }
                }
            }
            .padding(.hearth500)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(cardBackground)
        }
    }

    // MARK: - To-dos

    @ViewBuilder
    private var todosSection: some View {
        if !viewModel.todos.isEmpty {
            VStack(alignment: .leading, spacing: .hearth400) {
                Text("Follow-ups")
                    .font(.hearthDisplayMD)
                    .foregroundColor(.inkPrimary)
                ForEach(viewModel.todos) { todo in
                    HStack(alignment: .top, spacing: .hearth400) {
                        // Tappable — completing here mirrors the web dashboard.
                        Button {
                            Task { await viewModel.completeTodo(todo.id) }
                        } label: {
                            Image(systemName: "circle")
                                .font(.system(size: 16))
                                .foregroundColor(.accentDefault)
                                .frame(width: 28, height: 28)
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("Mark done: \(todo.title)")
                        VStack(alignment: .leading, spacing: 2) {
                            Text(todo.title)
                                .font(.hearthBodyMD)
                                .foregroundColor(.inkPrimary)
                            if let due = todo.dueDate {
                                Text("Due \(due)")
                                    .font(.hearthCaptionMono)
                                    .foregroundColor(.inkMuted)
                            }
                        }
                        Spacer()
                    }
                    .padding(.hearth500)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(cardBackground)
                    .opacity(viewModel.mutatingIds.contains(todo.id) ? 0.55 : 1)
                }
            }
        }
    }

    // MARK: - Helpers

    private var cardBackground: some View {
        RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
            .fill(Color.bgElevated)
            .overlay(
                RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                    .stroke(Color.borderHairline, lineWidth: 1)
            )
    }

    private func statTile(label: String, value: String, tone: Color) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(value)
                .font(.hearthDisplayMD)
                .foregroundColor(tone)
            Text(label.uppercased())
                .font(.hearthLabel)
                .tracking(0.66)
                .foregroundColor(.inkMuted)
        }
        .padding(.hearth500)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    private func currency(_ amount: Double) -> String {
        let f = NumberFormatter()
        f.numberStyle = .currency
        f.maximumFractionDigits = 0
        return f.string(from: NSNumber(value: amount)) ?? "$\(Int(amount))"
    }
}

// MARK: - Navigation Routes

// `CandidateRoute` is NOT declared here — it lives with the other route types in
// ContentStore.swift, which is where every navigationDestination value is
// defined so the set stays greppable in one place.

/// Routes a board card to its activity detail screen. Carries the full model
/// for the same reason `CandidateRoute` does: a board entry is a server-composed
/// projection (stage, next_step, overlaps) and isn't re-fetchable by id alone.
struct BoardActivityRoute: Hashable {
    let activity: BoardActivity
}

// MARK: - Candidate Row

/// Measured `1026:10569` (planner 3): white r=12 card, kid chip row, underlined
/// teal title + match pill, two muted meta lines, then a Save/Saved pill row —
/// all inside the card (no sidecar bookmark; the frame's card owns its own
/// action button). No status/price chip here — candidates carry neither a
/// lifecycle status nor a reliable price at this stage; showing one would be
/// fabricating what the frame doesn't draw.
private struct CandidateRow: View {
    let candidate: ActivityCandidate
    let isSaved: Bool
    let isSaving: Bool
    let onToggleSave: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            if !candidate.displayKids.isEmpty {
                HStack(spacing: .hearth300) {
                    ForEach(candidate.displayKids, id: \.self) { kid in
                        chip(kid)
                    }
                }
            }

            VStack(alignment: .leading, spacing: 0) {
                HStack(alignment: .top) {
                    Text(candidate.name)
                        .font(.hearthBodySMBold)
                        .foregroundColor(.accentDefault)
                        .underline()
                        .multilineTextAlignment(.leading)
                    Spacer(minLength: .hearth300)
                    if let fit = candidate.fitScore {
                        Text("\(Int((fit * 100).rounded()))%")
                            .font(.hearthBodySMBold)
                            .foregroundColor(.accentDefault)
                            .padding(.horizontal, .hearth500)
                            .padding(.vertical, 6)
                            .background(Capsule().fill(Color.bgSelected))
                    }
                }
                .padding(.bottom, .hearth300)

                Rectangle().fill(Color.borderHairline).frame(height: 1)

                VStack(alignment: .leading, spacing: 2) {
                    if let line1 = metaLine1 {
                        Text(line1)
                            .font(.hearthBodySM)
                            .foregroundColor(.inkSecondary)
                    }
                    if let line2 = metaLine2 {
                        Text(line2)
                            .font(.hearthBodySM)
                            .foregroundColor(.inkSecondary)
                    }
                }
                .padding(.top, .hearth300)

                // Price/schedule text — real search results carry a full
                // pricing paragraph (tiers, sibling discounts, scholarships)
                // that's valuable to see before tapping into detail; the
                // planner-3 mock's compact card just didn't have live search
                // data to show. Shown verbatim, never re-summarized.
                if let priceText = candidate.priceText, !priceText.isEmpty {
                    Text(priceText)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkSecondary)
                        .padding(.top, .hearth300)
                } else if let amount = candidate.priceAmount {
                    Text("$\(Int(amount))")
                        .font(.hearthBodySM)
                        .foregroundColor(.inkSecondary)
                        .padding(.top, .hearth300)
                }
            }

            HStack(spacing: .hearth300) {
                Button(action: onToggleSave) {
                    HStack(spacing: 6) {
                        if isSaving {
                            ProgressView().tint(isSaved ? Color.inkOnPhotoLight : Color.accentDefault)
                        } else if isSaved {
                            Image(systemName: "checkmark").font(.system(size: 12, weight: .bold))
                        }
                        Text(isSaved ? "Saved" : "Save")
                    }
                    .font(.hearthBodySM)
                    .foregroundColor(isSaved ? .inkOnPhotoLight : .accentDefault)
                    .padding(.horizontal, .hearth500)
                    .padding(.vertical, .hearth400)
                    .background(
                        Capsule()
                            .fill(isSaved ? Color.accentDefault : Color.clear)
                            .overlay(Capsule().stroke(Color.accentDefault, lineWidth: isSaved ? 0 : 1))
                    )
                }
                .buttonStyle(.plain)
                .disabled(isSaving)
                .accessibilityLabel(isSaved ? "Saved — tap to remove" : "Save to shortlist")
            }
        }
        .padding(.hearth500)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                .fill(Color.bgElevated)
        )
    }

    private var metaLine1: String? {
        var parts: [String] = []
        if let cat = candidate.category { parts.append(cat.capitalized) }
        if let p = candidate.provider { parts.append(p) }
        return parts.isEmpty ? nil : parts.joined(separator: " · ")
    }

    private var metaLine2: String? {
        var parts: [String] = []
        if let city = candidate.city { parts.append(city) }
        else if let l = candidate.locationText { parts.append(l) }
        if let dates = dateRangeShort { parts.append(dates) }
        return parts.isEmpty ? nil : parts.joined(separator: " · ")
    }

    private var dateRangeShort: String? {
        switch (candidate.startDate, candidate.endDate) {
        case let (start?, end?): return "\(start) – \(end)"
        case let (start?, nil): return start
        default: return nil
        }
    }

    private func chip(_ text: String) -> some View {
        Text(text)
            .font(.hearthBodySMBold)
            .foregroundColor(.accentDefault)
            .padding(.horizontal, .hearth500)
            .padding(.vertical, 6)
            .background(Capsule().fill(Color.bgSelected))
    }
}

// MARK: - Candidate Detail

struct CandidateDetailView: View {
    let candidate: ActivityCandidate

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: .hearth600) {
                VStack(alignment: .leading, spacing: .hearth300) {
                    if let eyebrow = eyebrowText {
                        Text(eyebrow)
                            .font(.hearthBodySMBold)
                            .foregroundColor(.accentDefault)
                    }
                    Text(candidate.name)
                        .font(.hearthDisplayMD)
                        .foregroundColor(.inkPrimary)
                    if let provider = candidate.provider {
                        Text(provider)
                            .font(.hearthChipLabel)
                            .foregroundColor(.plannerSearchText)
                    }
                    // Measured `1026:10614`: kid + match-% chips directly
                    // under the provider line — `fitScore` was collected by
                    // discovery but never surfaced here before this pass.
                    if !candidate.displayKids.isEmpty || candidate.fitScore != nil {
                        HStack(spacing: .hearth300) {
                            if !candidate.displayKids.isEmpty {
                                detailChip(candidate.displayKids.joined(separator: " & "))
                            }
                            if let fit = candidate.fitScore {
                                detailChip("\(Int((fit * 100).rounded()))% Match")
                            }
                        }
                    }
                }

                detailRows

                if let urlString = candidate.signupURL, let url = URL(string: urlString) {
                    Link(destination: url) {
                        Label("Open signup page", systemImage: "arrow.up.right.square")
                            .font(.hearthSectionHeader)
                            .foregroundColor(.inkOnPhotoLight)
                            .padding(.horizontal, .hearth500)
                            .padding(.vertical, .hearth500)
                            .frame(maxWidth: .infinity)
                            .background(Color.accentDefault)
                            .clipShape(Capsule())
                    }
                }
            }
            .padding(.horizontal, .hearth700)
            .padding(.vertical, .hearth700)
        }
        .background(Color.bgCanvas.ignoresSafeArea())
        .navigationTitle("Activity")
        .navigationBarTitleDisplayMode(.inline)
        .trackScreen("candidate_detail")
    }

    /// "{CATEGORY} FOR {DISPLAYKIDS}" per the planner-4 eyebrow, e.g. "CAMP
    /// FOR LILY & BENJAMIN" — falls back to just the category when no kid
    /// fits, never fabricates a kid name.
    private var eyebrowText: String? {
        guard let cat = candidate.category else { return nil }
        let upper = cat.uppercased()
        guard !candidate.displayKids.isEmpty else { return upper }
        return "\(upper) FOR \(candidate.displayKids.joined(separator: " & ").uppercased())"
    }

    private func detailChip(_ text: String) -> some View {
        Text(text)
            .font(.hearthBodySMBold)
            .foregroundColor(.accentDefault)
            .padding(.horizontal, .hearth500)
            .padding(.vertical, 6)
            .background(Capsule().fill(Color.bgSelected))
    }

    private var detailRows: some View {
        VStack(alignment: .leading, spacing: 0) {
            detailRow("For", candidate.displayKids.isEmpty ? nil : candidate.displayKids.joined(separator: ", "))
            detailRow("Ages", ageRange)
            detailRow("Dates", dateRange)
            detailRow("Schedule", candidate.scheduleText)
            detailRow("Price", candidate.priceText ?? candidate.priceAmount.map { "$\(Int($0))" })
            detailRow("Location", locationWithDistance)
        }
        .padding(.hearth600)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                .fill(Color.bgElevated)
        )
    }

    @ViewBuilder
    private func detailRow(_ label: String, _ value: String?) -> some View {
        if let value = value, !value.isEmpty {
            VStack(alignment: .leading, spacing: 0) {
                HStack(alignment: .top, spacing: .hearth500) {
                    Text(label.uppercased())
                        .font(.hearthLabel)
                        .tracking(0.66)
                        .foregroundColor(.inkMuted)
                        .frame(width: 120, alignment: .leading)
                    Text(value)
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkSecondary)
                    Spacer(minLength: 0)
                }
                .padding(.bottom, .hearth400)
                Rectangle().fill(Color.borderHairline).frame(height: 1)
            }
            .padding(.bottom, .hearth400)
        }
    }

    private var locationWithDistance: String? {
        guard let loc = candidate.locationText else { return nil }
        guard let mi = candidate.distanceMi else { return loc }
        return "\(loc) · \(Int(mi.rounded())) mi"
    }

    private var ageRange: String? {
        switch (candidate.ageMin, candidate.ageMax) {
        case let (min?, max?): return "\(fmtAge(min))–\(fmtAge(max))"
        case let (min?, nil): return "\(fmtAge(min))+"
        case let (nil, max?): return "up to \(fmtAge(max))"
        default: return nil
        }
    }

    private func fmtAge(_ v: Double) -> String {
        v.truncatingRemainder(dividingBy: 1) == 0 ? String(Int(v)) : String(v)
    }

    private var dateRange: String? {
        switch (candidate.startDate, candidate.endDate) {
        case let (start?, end?): return "\(start) – \(end)"
        case let (start?, nil): return start
        default: return nil
        }
    }
}

// MARK: - Board Activity Detail

struct BoardActivityDetailView: View {
    let activity: BoardActivity
    let onCompleteTodo: (String) -> Void
    let onAskCoach: (BoardActivity) -> Void

    /// "Ask the coach" switches the Plan hub to its chat segment — but this
    /// view is PUSHED on top of that hub, so flipping the segment underneath
    /// left the parent staring at the unchanged detail screen ("Ask the coach
    /// is not doing anything"). Pop back to the hub first, THEN switch.
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: .hearth600) {
                // Header
                VStack(alignment: .leading, spacing: .hearth300) {
                    if let type = activity.activityType {
                        let label = BoardCardView.chipLabels[type] ?? type
                        // "FOR {kid}" only when there IS a kid — a family-wide
                        // suggestion (onboarding's own starters carry no
                        // kid_name) was rendering the literal word "KID".
                        let kid = activity.kidName?.uppercased()
                        Text(kid.map { "\(label.uppercased()) FOR \($0)" } ?? label.uppercased())
                            .font(.hearthBodySMBold)
                            .foregroundColor(.accentDefault)
                    }
                    Text(activity.name)
                        .font(.hearthDisplayMD)
                        .foregroundColor(.inkPrimary)
                    if let provider = activity.provider {
                        Text(provider)
                            .font(.hearthChipLabel)
                            .foregroundColor(.plannerSearchText)
                    }
                }

                // Chips row (kid, status, fit score) — measured `1026:10614`:
                // kid + match pills teal-on-selected, status pill amber-on-warm.
                HStack(spacing: .hearth300) {
                    if let kid = activity.kidName {
                        detailChip(kid, tone: .bgSelected, foreground: .accentDefault)
                    }
                    detailChip(activity.status.capitalized, tone: .statusWarningTint, foreground: .inkSecondary)
                    if let fit = activity.fitScore {
                        detailChip("\(Int((fit * 100).rounded()))% Match", tone: .bgSelected, foreground: .accentDefault)
                    }
                }

                // Detail rows
                detailRows

                // Not in the planner-4 frame, but real actionable data the
                // candidate carried — dropping it after save would be a
                // regression (round 4: signup_url already survives to the
                // client; it just had no renderer here).
                if let urlString = activity.signupURL, let url = URL(string: urlString) {
                    Link(destination: url) {
                        Label("Open signup page", systemImage: "arrow.up.right.square")
                            .font(.hearthBodySMBold)
                            .foregroundColor(.accentDefault)
                    }
                }

                // "Planned"/"Ask the coach" pill row — measured `1026:10641`:
                // sits directly under the detail table, INSIDE the white card
                // implicitly (frame draws it as a sibling row, not nested).
                HStack(spacing: .hearth300) {
                    Text(activity.status.capitalized)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkOnCard)
                        .padding(.horizontal, .hearth500)
                        .padding(.vertical, .hearth400)
                        .background(Capsule().fill(Color.accentDefault))
                    Button {
                        dismiss()
                        onAskCoach(activity)
                    } label: {
                        Text("Ask the coach")
                            .font(.hearthBodySM)
                            .foregroundColor(.accentDefault)
                            .padding(.horizontal, .hearth500)
                            .padding(.vertical, .hearth400)
                            .background(
                                Capsule()
                                    .fill(Color.bgCard)
                                    .overlay(Capsule().stroke(Color.accentDefault, lineWidth: 1))
                            )
                    }
                    .buttonStyle(.plain)
                }

                // Onboarding's seeded starter suggestions have no provider,
                // dates, price or location — they were never a search result,
                // just a category to explore — so `notes` ("Suggested while
                // setting up your account — look for options near 95448") is
                // the ONLY context they carry. Without it their detail screen
                // is a title and a COST-TBD row.
                if let notes = activity.notes, !notes.isEmpty, activity.fitReason == nil {
                    VStack(alignment: .leading, spacing: .hearth300) {
                        Text("Why it's here")
                            .font(.hearthChipLabel)
                            .foregroundColor(.plannerSearchText)
                        Text(notes)
                            .font(.hearthBodySM)
                            .foregroundColor(.plannerSearchText)
                        Text("Search for real options near you, or ask the coach to narrow it down.")
                            .font(.hearthBodySM)
                            .foregroundColor(.plannerSearchText)
                    }
                    .padding(.hearth500)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                            .fill(Color.bgCard)
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                                    .stroke(Color.borderPlannerCard, lineWidth: 1)
                            )
                    )
                }

                // Why it matched — measured `1026:10644`: quiet card, `#F5F3EF`
                // fill + `#A4A4A4` stroke, not the bright white elevated card.
                if let reason = activity.fitReason {
                    VStack(alignment: .leading, spacing: .hearth300) {
                        Text("Why it matched")
                            .font(.hearthChipLabel)
                            .foregroundColor(.plannerSearchText)
                        Text(reason)
                            .font(.hearthBodySM)
                            .foregroundColor(.plannerSearchText)
                    }
                    .padding(.hearth500)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                            .fill(Color.bgCard)
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                                    .stroke(Color.borderPlannerCard, lineWidth: 1)
                            )
                    )
                }

                // Still to do
                if !activity.openTodos.isEmpty {
                    VStack(alignment: .leading, spacing: .hearth400) {
                        HStack(alignment: .firstTextBaseline) {
                            Text("Still to do")
                                .font(.hearthBodySMBold)
                                .foregroundColor(.accentDefault)
                            Spacer()
                            if let fit = activity.fitScore {
                                Text("\(Int((fit * 100).rounded()))%")
                                    .font(.hearthBodySMBold)
                                    .foregroundColor(.accentDefault)
                                    .padding(.horizontal, .hearth500)
                                    .padding(.vertical, 6)
                                    .background(Capsule().fill(Color.bgSelected))
                            }
                        }

                        ForEach(activity.openTodos) { todo in
                            todoRow(todo)
                        }

                        Button {
                            if let first = activity.openTodos.first(where: { $0.done != true }) {
                                onCompleteTodo(first.id)
                            }
                        } label: {
                            Label("Mark next step done", systemImage: "checkmark")
                                .font(.hearthSectionHeader)
                                .foregroundColor(.inkOnPhotoLight)
                                .padding(.horizontal, .hearth500)
                                .padding(.vertical, .hearth500)
                                .frame(maxWidth: .infinity)
                                .background(Color.accentDefault)
                                .clipShape(Capsule())
                        }
                        .buttonStyle(.plain)
                        .disabled(activity.openTodos.allSatisfy { $0.done == true })
                    }
                    .padding(.hearth500)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                            .fill(Color.bgElevated)
                    )

                    Text("Moves to All set once nothing is left.")
                        .font(.hearthChipLabel)
                        .foregroundColor(.plannerSearchText)
                }
            }
            .padding(.horizontal, .hearth700)
            .padding(.vertical, .hearth700)
        }
        .background(Color.bgCanvas.ignoresSafeArea())
        .navigationTitle("Activity")
        .navigationBarTitleDisplayMode(.inline)
        .trackScreen("board_activity_detail")
    }

    private func detailChip(_ text: String, tone: Color, foreground: Color) -> some View {
        Text(text)
            .font(.hearthBodySMBold)
            .foregroundColor(foreground)
            .padding(.horizontal, .hearth500)
            .padding(.vertical, 6)
            .background(Capsule().fill(tone))
    }

    /// FOR/AGES/DATES/SCHEDULE/COST/LOCATION — the ages/schedule/location
    /// rows only appear when `track_activity` had a candidate to copy them
    /// from (round 4: previously always absent post-save, leaving just FOR
    /// + COST). `when`/COST stay server-rendered/verbatim as before; AGES
    /// and LOCATION mirror `CandidateDetailView`'s formatting exactly so a
    /// saved item reads identically to the result it came from.
    private var detailRows: some View {
        let rows = buildDetailRows()
        return VStack(alignment: .leading, spacing: 0) {
            ForEach(Array(rows.enumerated()), id: \.offset) { index, row in
                detailRow(row.0, row.1, warning: row.2, isLast: index == rows.count - 1)
            }
        }
        .padding(.hearth600)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                .fill(Color.bgElevated)
        )
    }

    private var overlapWarning: String? {
        guard let overlaps = activity.overlaps, !overlaps.isEmpty else { return nil }
        return overlaps.map { "Overlaps \($0.name), \($0.range)" }.joined(separator: "\n")
    }

    private func buildDetailRows() -> [(String, String, String?)] {
        var rows: [(String, String, String?)] = []
        if let kid = activity.kidName { rows.append(("FOR", kid, nil)) }
        if let ages = ageRange { rows.append(("AGES", ages, nil)) }
        if let when = activity.when { rows.append(("DATES", when, overlapWarning)) }
        if let schedule = activity.scheduleText, !schedule.isEmpty {
            rows.append(("SCHEDULE", schedule, nil))
        }
        if let price = activity.priceText, !price.isEmpty {
            rows.append(("COST", price, nil))
        } else if let amount = activity.priceAmount {
            rows.append(("COST", "$\(Int(amount))", nil))
        } else {
            rows.append(("COST", "TBD — I'll track it once you register", nil))
        }
        if let location = locationWithCity { rows.append(("LOCATION", location, nil)) }
        return rows
    }

    private var ageRange: String? {
        switch (activity.ageMin, activity.ageMax) {
        case let (min?, max?): return "\(fmtAge(min))–\(fmtAge(max))"
        case let (min?, nil): return "\(fmtAge(min))+"
        case let (nil, max?): return "up to \(fmtAge(max))"
        default: return nil
        }
    }

    private func fmtAge(_ v: Double) -> String {
        v.truncatingRemainder(dividingBy: 1) == 0 ? String(Int(v)) : String(v)
    }

    private var locationWithCity: String? {
        if let loc = activity.locationText, !loc.isEmpty { return loc }
        return activity.city
    }

    @ViewBuilder
    private func detailRow(_ label: String, _ value: String, warning: String? = nil, isLast: Bool = false) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(alignment: .top, spacing: .hearth500) {
                Text(label)
                    .font(.hearthLabel)
                    .tracking(0.66)
                    .foregroundColor(.inkMuted)
                    .frame(width: 120, alignment: .leading)
                VStack(alignment: .leading, spacing: .hearth300) {
                    Text(value)
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkSecondary)
                    if let warning {
                        HStack(alignment: .top, spacing: .hearth300) {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .font(.system(size: 12))
                                .foregroundColor(.statusWarning)
                            Text(warning)
                                .font(.hearthBodySM)
                                .foregroundColor(.statusWarning)
                        }
                    }
                }
                Spacer(minLength: 0)
            }
            .padding(.bottom, .hearth400)
            if !isLast {
                Rectangle().fill(Color.borderHairline).frame(height: 1)
            }
        }
        .padding(.bottom, isLast ? 0 : .hearth400)
    }

    private func todoRow(_ todo: PlanTodo) -> some View {
        let isDone = todo.done == true
        return HStack(spacing: .hearth300) {
            Button {
                onCompleteTodo(todo.id)
            } label: {
                Image(systemName: isDone ? "checkmark.circle.fill" : "circle")
                    .font(.system(size: 15))
                    .foregroundColor(.accentDefault)
                    .frame(width: 28, height: 28)
            }
            .buttonStyle(.plain)
            .disabled(isDone)
            Text(todo.title)
                .font(.hearthBodySM)
                .foregroundColor(isDone ? .inkMuted : .accentDefault)
                .strikethrough(isDone)
            Spacer(minLength: 0)
        }
    }
}

/// Thin wrapper around UIActivityViewController so SwiftUI can present the
/// system share sheet for a file (exported .xlsx) or a share-link URL.
struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]
    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }
    func updateUIViewController(_ controller: UIActivityViewController, context: Context) {}
}
