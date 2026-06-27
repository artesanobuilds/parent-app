import SwiftUI

/// The "Plan" tab: trigger a camp/activity discovery run and browse ranked
/// candidates, see the chief-of-staff plan summary (cost, coverage gaps,
/// pending-eligibility, open to-dos), and open the chief-of-staff chat.
/// Mirrors the app's other tabs: self-contained `NavigationStack`, Hearth tokens,
/// view model injected from `MainTabView`.
struct PlanView: View {
    @ObservedObject var viewModel: PlanViewModel
    let configuration: ServerConfiguration
    let userID: String

    @State private var showIngest = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: .hearth900) {
                    header
                    ingestEntry
                    discoverySection
                    exploringSection
                    if let summary = viewModel.summary {
                        planSummarySection(summary)
                    }
                    calendarSection
                    todosSection
                    chatLink
                }
                .padding(.horizontal, .hearth700)
                .padding(.top, .hearth700)
            }
            // Any scroll drag dismisses the keyboard (the numeric ZIP keyboard
            // has no return key); the field's own "Done" bar is the explicit tap.
            .scrollDismissesKeyboard(.immediately)
            .background(Color.bgCanvas.ignoresSafeArea())
            .sheet(isPresented: $showIngest) {
                IngestView(viewModel: viewModel)
            }
            .navigationDestination(for: CandidateRoute.self) { route in
                CandidateDetailView(candidate: route.candidate)
            }
            .task {
                viewModel.userId = userID
                viewModel.baseURL = configuration.baseURL
                await viewModel.prefillLocation()
                await viewModel.loadPlan()
            }
            .refreshable { await viewModel.loadPlan() }
            .onAppear {
                viewModel.userId = userID
                viewModel.baseURL = configuration.baseURL
            }
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text("PLAN")
                .font(.hearthLabel)
                .tracking(0.66)
                .foregroundColor(.inkMuted)
            Text("Your family's activities")
                .font(.hearthDisplayMD)
                .foregroundColor(.inkPrimary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
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

            if !viewModel.discoveryRecent.isEmpty {
                Divider().background(Color.borderHairline)
                VStack(alignment: .leading, spacing: .hearth300) {
                    ForEach(Array(viewModel.discoveryRecent.reversed().enumerated()), id: \.offset) { idx, item in
                        Text(item)
                            .font(.hearthBodySM)
                            .foregroundColor(idx == 0 ? .inkPrimary : .inkMuted)
                            .lineLimit(2)
                            .fixedSize(horizontal: false, vertical: true)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }
        }
        .padding(.hearth600)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
        .animation(.hearthFast, value: viewModel.discoveryRecent)
    }

    private var candidateList: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            HStack {
                Text("\(viewModel.candidates.count) found")
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
            ForEach(viewModel.candidates) { candidate in
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

    /// Bookmark/pin a candidate onto the Exploring shortlist. A sibling of the
    /// NavigationLink (not nested) so the two taps never conflict.
    private func saveButton(for candidate: ActivityCandidate) -> some View {
        let saved = viewModel.isSaved(candidate)
        let saving = viewModel.isSaving(candidate)
        return Button {
            Task { await viewModel.saveCandidate(candidate) }
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
        .disabled(saved || saving)
        .accessibilityLabel(saved ? "Saved to shortlist" : "Save to shortlist")
    }

    // MARK: - Exploring shortlist (R1)

    @ViewBuilder
    private var exploringSection: some View {
        let items = viewModel.exploringActivities
        if !items.isEmpty {
            VStack(alignment: .leading, spacing: .hearth400) {
                HStack(alignment: .firstTextBaseline) {
                    Text("Exploring")
                        .font(.hearthDisplayMD)
                        .foregroundColor(.inkPrimary)
                    Spacer()
                    Text("\(items.count)")
                        .font(.hearthCaptionMono)
                        .foregroundColor(.inkMuted)
                }
                Text("Camps you're considering. Ask your chief of staff to weigh the tradeoffs and help you decide.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
                ForEach(items) { activity in
                    exploringRow(activity)
                }
                NavigationLink {
                    CosChatView(
                        configuration: configuration,
                        userID: userID,
                        initialPrompt: "Help me decide between the camps on my shortlist. Walk me through the tradeoffs (cost, eligibility, schedule conflicts, coverage) and recommend picks per kid."
                    )
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

    private func exploringRow(_ activity: TrackedActivity) -> some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            HStack(alignment: .firstTextBaseline) {
                Text(activity.name)
                    .font(.hearthBodyLG.weight(.semibold))
                    .foregroundColor(.inkPrimary)
                    .multilineTextAlignment(.leading)
                Spacer()
                Image(systemName: "bookmark.fill")
                    .font(.system(size: 13))
                    .foregroundColor(.accentDefault)
            }
            HStack(spacing: .hearth300) {
                if let kid = activity.kidName {
                    Text(kid)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkSecondary)
                        .padding(.horizontal, .hearth400)
                        .padding(.vertical, 4)
                        .background(Capsule().fill(Color.accentTint))
                }
                if let provider = activity.provider {
                    Text(provider)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkSecondary)
                }
                Spacer(minLength: 0)
                if let price = activity.priceAmount {
                    Text("$\(Int(price))")
                        .font(.hearthCaptionMono)
                        .foregroundColor(.inkSecondary)
                }
            }
        }
        .padding(.hearth500)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
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
                        Image(systemName: "circle")
                            .font(.system(size: 16))
                            .foregroundColor(.inkMuted)
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
                }
            }
        }
    }

    // MARK: - Chat

    private var chatLink: some View {
        NavigationLink {
            CosChatView(configuration: configuration, userID: userID)
        } label: {
            HStack(spacing: .hearth400) {
                Image(systemName: "calendar.badge.clock")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(.inkOnPhotoLight)
                    .frame(width: 40, height: 40)
                    .background(Circle().fill(Color.accentDefault))
                VStack(alignment: .leading, spacing: 2) {
                    Text("Ask your chief of staff")
                        .font(.hearthBodyMD.weight(.semibold))
                        .foregroundColor(.inkPrimary)
                    Text("Track activities, sort coverage, decide between camps")
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
        .padding(.bottom, .hearth1000)
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
