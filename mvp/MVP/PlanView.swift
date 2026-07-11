import SwiftUI
import UIKit

/// The "Plan" tab: trigger a camp/activity discovery run and browse ranked
/// candidates, see the chief-of-staff plan summary (cost, coverage gaps,
/// pending-eligibility, open to-dos), and open the chief-of-staff chat.
/// Mirrors the app's other tabs: self-contained `NavigationStack`, Hearth tokens,
/// view model injected from `MainTabView`.
struct PlanView: View {
    @ObservedObject var viewModel: PlanViewModel
    @ObservedObject var cosVM: CosChatViewModel
    let configuration: ServerConfiguration
    let userID: String

    @State private var segment: PlanSegment = .chat
    @State private var showIngest = false
    @State private var showSortFilter = false
    // Vertical chip filter on the board (attribute, never navigation) and the
    // "Plan something" door sheet (the five doors behind ONE disclosure).
    @State private var typeFilter: String?
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

    /// The Plan hub's sub-views. The Chief of Staff (chat) is the front door;
    /// the structured views hang off it one tap away.
    enum PlanSegment: String, CaseIterable, Identifiable {
        case chat, discover, shortlist, calendar
        var id: String { rawValue }
        var label: String {
            switch self {
            case .chat: return "Chat"
            case .discover: return "Discover"
            case .shortlist: return "Activities"
            case .calendar: return "Calendar"
            }
        }
    }

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
            // Keep the plan-derived segments fresh. They only loaded once on first
            // appear, so the chief-of-staff chat (which can track activities, add or
            // complete to-dos, etc. via its tools) left the Shortlist/Calendar stale.
            // Reload when the parent lands on a plan-derived segment …
            .onChange(of: segment) { _, newValue in
                if newValue == .shortlist || newValue == .calendar {
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

    private var header: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: .hearth300) {
                Text("PLAN")
                    .font(.hearthLabel)
                    .tracking(0.66)
                    .foregroundColor(.inkMuted)
                Text("Chief of Staff")
                    .font(.hearthDisplayMD)
                    .foregroundColor(.inkPrimary)
            }
            Spacer()
            if !viewModel.doors.isEmpty {
                Button {
                    showDoors = true
                } label: {
                    Label("Plan something", systemImage: "plus")
                        .font(.hearthBodySM.weight(.semibold))
                        .foregroundColor(.inkOnPhotoLight)
                        .padding(.horizontal, .hearth400)
                        .padding(.vertical, .hearth300)
                        .background(Capsule().fill(Color.accentDefault))
                }
                .buttonStyle(.plain)
            }
            planMenu
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, .hearth700)
        .padding(.top, .hearth700)
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

    private var segmentPicker: some View {
        Picker("View", selection: $segment) {
            ForEach(PlanSegment.allCases) { seg in
                Text(seg.label).tag(seg)
            }
        }
        .pickerStyle(.segmented)
        .padding(.horizontal, .hearth700)
        .padding(.top, .hearth500)
        .padding(.bottom, .hearth400)
        .background(Color.bgCanvas)
    }

    @ViewBuilder
    private var segmentBody: some View {
        switch segment {
        case .chat:
            // The chat owns its own pinned input bar + scroll; MainTabView's
            // bottom padding already lifts the whole tab clear of the tab bar.
            CosChatView(viewModel: cosVM, doors: viewModel.doors)

        case .discover:
            ScrollView {
                VStack(alignment: .leading, spacing: .hearth900) {
                    ingestEntry
                    discoverySection
                }
                .padding(.horizontal, .hearth700)
                .padding(.top, .hearth500)
                .padding(.bottom, .hearth900)
            }
            // The numeric ZIP keyboard has no return key; any drag dismisses it.
            .scrollDismissesKeyboard(.immediately)

        case .shortlist:
            ScrollView {
                VStack(alignment: .leading, spacing: .hearth900) {
                    boardSection
                    if let summary = viewModel.summary {
                        planSummarySection(summary)
                    }
                    todosSection
                    if shortlistIsEmpty {
                        emptyState(
                            icon: "bookmark",
                            title: "No activities yet",
                            message: "Save ideas from Discover, decide with “We'll do it”, register — then I watch the camp's emails and track payments & forms for you."
                        )
                    }
                }
                .padding(.horizontal, .hearth700)
                .padding(.top, .hearth500)
                .padding(.bottom, .hearth900)
            }
            .refreshable { await viewModel.loadPlan() }

        case .calendar:
            ScrollView {
                VStack(alignment: .leading, spacing: .hearth900) {
                    calendarSection
                    if viewModel.calendarWeeks.isEmpty {
                        emptyState(
                            icon: "calendar",
                            title: "Your calendar is empty",
                            message: "Once you confirm camps and activities, your week-by-week plan appears here."
                        )
                    }
                }
                .padding(.horizontal, .hearth700)
                .padding(.top, .hearth500)
                .padding(.bottom, .hearth900)
            }
            .refreshable { await viewModel.loadPlan() }
        }
    }

    private var shortlistIsEmpty: Bool {
        (viewModel.board?.stages.allSatisfy { $0.activities.isEmpty } ?? viewModel.exploringActivities.isEmpty)
            && viewModel.todos.isEmpty
            && viewModel.summary == nil
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

    // MARK: - Ingest entry

    private var ingestEntry: some View {
        Button {
            viewModel.resetIngest()
            showIngest = true
        } label: {
            HStack(spacing: .hearth400) {
                Image(systemName: "doc.text.viewfinder")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(.inkOnPhotoLight)
                    .frame(width: 40, height: 40)
                    .background(Circle().fill(Color.accentDefault))
                VStack(alignment: .leading, spacing: 2) {
                    Text("Add from a message or photo")
                        .font(.hearthBodyMD.weight(.semibold))
                        .foregroundColor(.inkPrimary)
                    Text("Paste a camp email or snap a flyer — we'll pull out the details")
                        .font(.hearthBodySM)
                        .foregroundColor(.inkSecondary)
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.inkMuted)
            }
            .padding(.hearth500)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(cardBackground)
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
                discoverPrompt
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

    private var discoverPrompt: some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            Text(viewModel.completedEmpty ? "No activities found" : "Discover activities")
                .font(.hearthBodyLG.weight(.semibold))
                .foregroundColor(.inkPrimary)
            Text(viewModel.completedEmpty
                 ? "Nothing came back for that area. Add or adjust your ZIP code and try again."
                 : "Find camps, classes, and weekend activities near you, matched to each kid. Enter a ZIP code to search around.")
                .font(.hearthBodyMD)
                .foregroundColor(.inkSecondary)

            TextField("ZIP code (e.g. 95448)", text: $viewModel.locationQuery)
                .font(.hearthBodyMD)
                .foregroundColor(.inkPrimary)
                .keyboardType(.numbersAndPunctuation)
                .textInputAutocapitalization(.never)
                // Numeric keyboards have no return key, so give an explicit
                // dismiss affordance above the keyboard.
                .toolbar {
                    ToolbarItemGroup(placement: .keyboard) {
                        Spacer()
                        Button("Done") { hideKeyboard() }
                            .font(.hearthBodyMD.weight(.semibold))
                            .foregroundColor(.accentDefault)
                    }
                }
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth400)
                .background(
                    RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                        .fill(Color.bgCanvas)
                        .overlay(
                            RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                                .stroke(Color.borderStrong, lineWidth: 1)
                        )
                )

            // Search radius from the ZIP.
            VStack(alignment: .leading, spacing: .hearth300) {
                Text("Search radius")
                    .font(.hearthBodySM.weight(.semibold))
                    .foregroundColor(.inkSecondary)
                Picker("Search radius", selection: $viewModel.radiusMiles) {
                    ForEach(viewModel.radiusOptions, id: \.self) { mi in
                        Text("\(mi) mi").tag(mi)
                    }
                }
                .pickerStyle(.segmented)
            }

            // How many candidates to aim for ("top 5" … "top 50").
            VStack(alignment: .leading, spacing: .hearth300) {
                Text("How many to find")
                    .font(.hearthBodySM.weight(.semibold))
                    .foregroundColor(.inkSecondary)
                Picker("How many to find", selection: $viewModel.maxCandidates) {
                    ForEach(viewModel.candidateCountOptions, id: \.self) { n in
                        Text("\(n)").tag(n)
                    }
                }
                .pickerStyle(.segmented)
            }

            // Optional free-form focus — hidden until the parent asks for it, so the
            // default form is just ZIP + radius.
            if viewModel.showFocus {
                VStack(alignment: .leading, spacing: .hearth300) {
                    HStack {
                        Text("Focus (optional)")
                            .font(.hearthBodySM.weight(.semibold))
                            .foregroundColor(.inkSecondary)
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
                            Text("e.g. art camps only · physical activity · just for Ceiba")
                                .font(.hearthBodyMD)
                                .foregroundColor(.inkMuted)
                                .padding(.horizontal, .hearth500 + 4)
                                .padding(.vertical, .hearth400 + 8)
                        }
                        TextEditor(text: $viewModel.focusText)
                            .font(.hearthBodyMD)
                            .foregroundColor(.inkPrimary)
                            .scrollContentBackground(.hidden)
                            .frame(minHeight: 72)
                            .padding(.horizontal, .hearth400)
                            .padding(.vertical, .hearth300)
                    }
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .fill(Color.bgCanvas)
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                                    .stroke(Color.borderStrong, lineWidth: 1)
                            )
                    )
                }
            } else {
                Button {
                    withAnimation(.hearthFast) { viewModel.showFocus = true }
                } label: {
                    Label("Add focus (optional)", systemImage: "plus.circle")
                        .font(.hearthBodySM.weight(.semibold))
                        .foregroundColor(.accentDefault)
                }
            }

            Button {
                viewModel.startDiscovery()
            } label: {
                Label(viewModel.completedEmpty ? "Try again" : "Find activities", systemImage: "sparkle.magnifyingglass")
                    .font(.hearthBodyMD.weight(.semibold))
                    .foregroundColor(.inkOnPhotoLight)
                    .padding(.horizontal, .hearth500)
                    .padding(.vertical, .hearth400)
                    .background(Color.accentDefault)
                    .clipShape(Capsule())
            }
        }
        .padding(.hearth600)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

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
                HStack(alignment: .center, spacing: .hearth300) {
                    NavigationLink(value: CandidateRoute(candidate: candidate)) {
                        CandidateRow(candidate: candidate)
                    }
                    .buttonStyle(.plain)
                    saveButton(for: candidate)
                }
            }
        }
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
                        Text("Sort & Filter")
                        Text("· \(viewModel.sortKey.label)")
                            .foregroundColor(.inkMuted)
                        Spacer()
                        if viewModel.hasActiveFilters {
                            Text("\(viewModel.activeFilterCount)")
                                .font(.hearthBodySM.weight(.bold))
                                .foregroundColor(.inkOnPhotoLight)
                                .padding(.horizontal, 8).padding(.vertical, 2)
                                .background(Capsule().fill(Color.accentDefault))
                        }
                        Image(systemName: "chevron.down").font(.caption).foregroundColor(.inkMuted)
                    }
                    .font(.hearthBodySM.weight(.semibold))
                    .foregroundColor(.inkPrimary)
                    .padding(.horizontal, .hearth500)
                    .padding(.vertical, .hearth400)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .fill(Color.bgElevated)
                            .overlay(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                                .stroke(Color.borderHairline, lineWidth: 1))
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
                        Text("SORT").font(.hearthLabel).tracking(0.6).foregroundColor(.inkMuted)
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
                            Text("FILTER").font(.hearthLabel).tracking(0.6).foregroundColor(.inkMuted)
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

    /// Bookmark/pin a candidate onto the Exploring shortlist. A sibling of the
    /// NavigationLink (not nested) so the two taps never conflict.
    private func saveButton(for candidate: ActivityCandidate) -> some View {
        let saved = viewModel.isSaved(candidate)
        let saving = viewModel.isSaving(candidate)
        return Button {
            Task { await viewModel.toggleSave(candidate) }
        } label: {
            Group {
                if saving {
                    ProgressView()
                } else {
                    Image(systemName: saved ? "bookmark.fill" : "bookmark")
                        .font(.system(size: 18, weight: .medium))
                        .foregroundColor(saved ? .accentDefault : .inkMuted)
                }
            }
            .frame(width: 44, height: 44)
        }
        .buttonStyle(.plain)
        .disabled(saving)  // tappable when saved → un-saves
        .accessibilityLabel(saved ? "Saved — tap to remove" : "Save to shortlist")
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
                        // Flip to the chat segment and seed a triage request into
                        // the same (hoisted) conversation.
                        withAnimation(.hearthFast) { segment = .chat }
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
            Text("Pick a door — the chief of staff takes it from there.")
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
        withAnimation(.hearthFast) { segment = .chat }
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
                        withAnimation(.hearthFast) { segment = .chat }
                        cosVM.send("Help me resolve this for \(a.name): \(label)")
                    },
                    onPassConfirm: { a in passTarget = a },
                    onDeleteConfirm: { a in deleteTarget = a }
                )
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
        .padding(.hearth500)
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

// MARK: - Candidate Row

private struct CandidateRow: View {
    let candidate: ActivityCandidate

    var body: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            HStack(alignment: .firstTextBaseline) {
                Text(candidate.name)
                    .font(.hearthBodyLG.weight(.semibold))
                    .foregroundColor(.inkPrimary)
                    .multilineTextAlignment(.leading)
                Spacer()
                if let fit = candidate.fitScore {
                    Text("\(Int((fit * 100).rounded()))%")
                        .font(.hearthCaptionMono)
                        .foregroundColor(.accentDefault)
                }
            }
            if let meta = metaLine {
                Text(meta)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
            }
            HStack(spacing: .hearth300) {
                ForEach(candidate.displayKids, id: \.self) { kid in
                    chip(kid, tone: .accentTint)
                }
                if let cat = candidate.category { chip(cat, tone: .bgElevated) }
                if let price = candidate.priceText ?? candidate.priceAmount.map({ "$\(Int($0))" }) {
                    chip(price, tone: .bgElevated)
                }
            }
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

    private var metaLine: String? {
        var parts: [String] = []
        if let p = candidate.provider { parts.append(p) }
        if let l = candidate.locationText { parts.append(l) }
        return parts.isEmpty ? nil : parts.joined(separator: " · ")
    }

    private func chip(_ text: String, tone: Color) -> some View {
        Text(text)
            .font(.hearthBodySM)
            .foregroundColor(.inkSecondary)
            .padding(.horizontal, .hearth400)
            .padding(.vertical, 4)
            .background(Capsule().fill(tone))
    }
}

// MARK: - Candidate Detail

struct CandidateDetailView: View {
    let candidate: ActivityCandidate

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: .hearth600) {
                VStack(alignment: .leading, spacing: .hearth300) {
                    if let cat = candidate.category {
                        Text(cat.uppercased())
                            .font(.hearthLabel)
                            .tracking(0.66)
                            .foregroundColor(.inkMuted)
                    }
                    Text(candidate.name)
                        .font(.hearthDisplayMD)
                        .foregroundColor(.inkPrimary)
                    if let provider = candidate.provider {
                        Text(provider)
                            .font(.hearthBodyMD)
                            .foregroundColor(.inkSecondary)
                    }
                }

                detailRows

                if let urlString = candidate.signupURL, let url = URL(string: urlString) {
                    Link(destination: url) {
                        Label("Open signup page", systemImage: "arrow.up.right.square")
                            .font(.hearthBodyMD.weight(.semibold))
                            .foregroundColor(.inkOnPhotoLight)
                            .padding(.horizontal, .hearth500)
                            .padding(.vertical, .hearth400)
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

    private var detailRows: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            detailRow("For", candidate.displayKids.isEmpty ? nil : candidate.displayKids.joined(separator: ", "))
            detailRow("Ages", ageRange)
            detailRow("Dates", dateRange)
            detailRow("Schedule", candidate.scheduleText)
            detailRow("Price", candidate.priceText ?? candidate.priceAmount.map { "$\(Int($0))" })
            detailRow("Location", candidate.locationText)
        }
        .padding(.hearth600)
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

    @ViewBuilder
    private func detailRow(_ label: String, _ value: String?) -> some View {
        if let value = value, !value.isEmpty {
            HStack(alignment: .top, spacing: .hearth500) {
                Text(label.uppercased())
                    .font(.hearthLabel)
                    .tracking(0.66)
                    .foregroundColor(.inkMuted)
                    .frame(width: 80, alignment: .leading)
                Text(value)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkPrimary)
                Spacer(minLength: 0)
            }
        }
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

/// Thin wrapper around UIActivityViewController so SwiftUI can present the
/// system share sheet for a file (exported .xlsx) or a share-link URL.
struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]
    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }
    func updateUIViewController(_ controller: UIActivityViewController, context: Context) {}
}
