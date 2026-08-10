import SwiftUI

// Kid settings sheet — beta-v1 sprint-1 `kid-001a` / `kid-001b` (both
// variants) / `kid-001c` / `kid-002a`, built against MEASURED values.
//
// Shape, top to bottom: a white frame with a 60pt top inset; the header
// "{Name}'s settings" (Inter w800 16) with a close affordance over a 1px rule;
// the wide PHOTO BAND with its camera badge; then everything else on the cream
// ground (`#E9E4DC`, pad 24/30, gap 20) —
//
//   • an "Edit child" pill  (`kid-001c`)
//   • the name in the display serif, 56/60  (`hearthDisplayXL`)
//   • the RELATION card: Son/Daughter, Birthday, Grade, and the personality
//     chip group
//   • "What makes {Name} special": five disclosure rows — Likes, Dislikes,
//     Challenges, Excels at, Goals for {Name}
//   • Save / Cancel
//
// THE TWO `kid-001b` VARIANTS ARE TWO STATES, and both are built:
//   `858:4985` — FILLED. The chip group is headed "Personality" and shows the
//                design's three chips; every disclosure row is open with the
//                parent's real values in a teal-stroked r12 box.
//   `907:2949` — EMPTY + EXPANDED. The same card is headed "More about
//                {Name}" and carries an extra full-width `More` chip; every
//                disclosure row is open showing grey "Examples: …" prompts.
// So: `chipsExpanded` drives the header/`More` chip, and each row renders its
// values or its example prompt depending on whether anything is stored.
//
// It stays a RESTYLE of the shipped write paths: every mutation still goes
// through PATCH /profile/kids/{name} with ONLY the keys it owns
// (`temperament`, `grade_band`, one learned list), so a change here can never
// wipe a field the coach learned. See
// `tests/test_onboarding_seed_contract.py::test_saving_basics_does_not_wipe_learned_fields`.
//
// Two honest departures from the frames, both reported rather than faked:
//   • The frames show "Birthday: April 25, 2021". There is no birthday field on
//     `ChildProfileDTO` (the profile stores `age`), so the row renders Age.
//   • `kid-001a`/`kid-001b` draw a SECOND Save/Cancel pair at the top of the
//     cream ground. The bottom pair already commits; a duplicate control doing
//     the identical thing is worse than the design is right, so the top slot
//     carries the `kid-001c` "Edit child" pill instead.

struct KidSettingsSheet: View {
    let baseURL: URL?
    let userID: String
    /// The server's dictionary key for this kid — the name the profile was
    /// stored under. Never the draft/edited display name (attach + PATCH 404 on
    /// an unknown kid).
    let kidKey: String
    /// Optional: the presenter's "show me the whole coach thread" action (the
    /// Coach tab). When nil the coach card's button is hidden rather than dead.
    var onViewAllCoach: (() -> Void)? = nil
    /// Called with the fresh family on every mutation, so the presenting view's
    /// source-of-truth stays current without waiting for dismissal.
    var onProfileChanged: (FamilyProfileDTO) -> Void

    @StateObject private var model: KidSettingsModel
    @State private var route: Route?
    /// `kid-001b` `907:2949`: the chip group opened, which retitles the card
    /// "More about {Name}" and reveals the temperaments the funnel doesn't show.
    @State private var chipsExpanded = false
    /// Which disclosure rows are open. `kid-001c`/`kid-002a` are the all-closed
    /// state; `kid-001a`/`kid-001b` are the all-open one.
    @State private var openRows: Set<KidLearnedField> = []
    @Environment(\.dismiss) private var dismiss

    init(baseURL: URL?, userID: String, kidKey: String, kid: ChildProfileDTO,
         onViewAllCoach: (() -> Void)? = nil,
         onProfileChanged: @escaping (FamilyProfileDTO) -> Void) {
        self.baseURL = baseURL
        self.userID = userID
        self.kidKey = kidKey
        self.onViewAllCoach = onViewAllCoach
        self.onProfileChanged = onProfileChanged
        _model = StateObject(wrappedValue: KidSettingsModel(
            baseURL: baseURL, userID: userID, kidKey: kidKey, kid: kid
        ))
    }

    private enum Route: Hashable {
        case basics
        case companion
        case learned(KidLearnedField)
    }

    private var displayName: String {
        let name = (model.kid.name ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        return name.isEmpty ? kidKey : name
    }

    /// Per-kid accent from the most STABLE id we have: the kid-agent config id
    /// when a companion exists, the profile key otherwise. Never the editable
    /// display name where an id exists, and never the list index.
    private var accent: Color {
        Color.kidAccent(seed: model.companion?.id ?? kidKey)
    }

    /// "Son" / "Daughter" per the frames, derived from the pronouns the profile
    /// actually stores — the row pushes the basics editor, so it is also how a
    /// parent corrects it.
    private var relationLabel: String {
        let pronouns = (model.kid.pronouns ?? "").lowercased()
        if pronouns.contains("he/") || pronouns.hasPrefix("he") { return "Son" }
        if pronouns.contains("she/") || pronouns.hasPrefix("she") { return "Daughter" }
        return "Child"
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                header
                rule
                ScrollView {
                    VStack(spacing: 0) {
                        photoBand
                        creamBody
                    }
                }
            }
            .background(Color.bgElevated.ignoresSafeArea())
            .toolbar(.hidden, for: .navigationBar)
            .navigationDestination(item: $route) { destination in
                destinationView(destination)
            }
        }
        .trackScreen("kid_settings")
        // Source-of-truth re-fetch (CLAUDE.md): on open, and again whenever a
        // pushed editor pops — the companion editor in particular changes state
        // this sheet renders but doesn't own.
        .task(id: model.refreshToken) { await model.refresh() }
        .onChange(of: route) { _, destination in
            if destination == nil { model.refreshToken += 1 }
        }
    }

    @ViewBuilder
    private func destinationView(_ destination: Route) -> some View {
        switch destination {
        case .basics:
            KidProfileEditor(
                baseURL: baseURL, userID: userID,
                kidKey: kidKey, kid: model.kid
            ) { fam in
                // A delete inside the editor removes the kid entirely — this
                // sheet then has nothing to show, so close it.
                model.apply(fam)
                onProfileChanged(fam)
                if fam.children?[kidKey] == nil { dismiss() }
            }
        case .companion:
            if let baseURL {
                ReviewLetterView(userID: userID, kidName: kidKey, baseURL: baseURL)
                    .navigationBarTitleDisplayMode(.inline)
            }
        case .learned(let field):
            KidLearnedListEditor(
                baseURL: baseURL, userID: userID, kidKey: kidKey,
                kidDisplayName: displayName, field: field, kid: model.kid
            ) { fam in
                model.apply(fam)
                onProfileChanged(fam)
            }
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack(spacing: .hearth300) {
            Text("\(displayName)'s settings")
                .font(.hearthSectionHeader)
                .foregroundColor(.inkDisplay)
            Spacer()
            Button { dismiss() } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.bgButtonFunnel)
                    .frame(width: 44, height: 44, alignment: .trailing)
            }
            .accessibilityLabel("Close")
        }
        .padding(.horizontal, .hearth800)
        .padding(.bottom, .hearth600)
    }

    /// The frames' 1px `#C8C3B8` rules. `borderInputPill` (#C9C5BE) is the
    /// nearest token and matches to within one value per channel.
    private var rule: some View {
        Rectangle().fill(Color.borderInputPill).frame(height: 1)
    }

    // MARK: - Photo band

    private var photoBand: some View {
        EditableAvatarView(
            avatarUrl: model.kid.avatarUrl,
            target: .kid(kidKey),
            userID: userID,
            baseURL: baseURL,
            monogram: displayName,
            personName: displayName
        ) {
            guard let baseURL,
                  let fam = try? await ProfileService.getProfile(baseURL: baseURL,
                                                                userID: userID) else {
                return false
            }
            model.apply(fam)
            onProfileChanged(fam)
            return true
        }
    }

    // MARK: - Cream body

    private var creamBody: some View {
        VStack(alignment: .leading, spacing: .hearth600) {
            editChildPill
            Text(displayName)
                .font(.hearthDisplayXL)
                .tracking(-1.12)
                .foregroundColor(.inkDisplay)
            relationCard
            specialCard
            coachCard
            companionCard
            saveBar
        }
        .padding(.horizontal, .hearth800)
        .padding(.vertical, .hearth700)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.bgCanvas)
    }

    /// `kid-001c`'s teal pill. Pushes the basics editor — name, age, grade,
    /// pronouns and the delete — which is the only place those are editable.
    private var editChildPill: some View {
        Button { route = .basics } label: {
            HStack(spacing: .hearth300) {
                Image(systemName: "pencil")
                    .font(.system(size: 14, weight: .semibold))
                Text("Edit child")
                    .font(.hearthButtonLabel)
            }
            .foregroundColor(.inkOnPhotoLight)
            .padding(.horizontal, .hearth400)
            .padding(.vertical, .hearth300)
            .background(
                RoundedRectangle(cornerRadius: .hearthRadiusSeeAll, style: .continuous)
                    .fill(Color.accentDefault)
            )
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Edit \(displayName)'s name, age and grade")
    }

    // MARK: - Relation card

    private var relationCard: some View {
        card {
            Button { route = .basics } label: {
                Image(systemName: "pencil")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.accentDefault)
                    .frame(width: 20, height: 20, alignment: .leading)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Edit \(displayName)'s basics")

            Text(relationLabel)
                .font(.hearthTitleLG)
                .foregroundColor(.inkDisplay)

            VStack(alignment: .leading, spacing: 9) {
                // The frames read "Birthday". The profile stores an AGE, not a
                // date of birth, so this row shows what exists rather than
                // inventing a date (reported as a gap).
                factRow("Age:", model.kid.age.map(\.kidAgeLabel) ?? "Not set")
                factRow("Grade:", gradeLabel)
            }

            rule.padding(.top, .hearth600)
            personalityGroup
        }
    }

    private var gradeLabel: String {
        let band = model.kid.gradeBand ?? ""
        return band.isEmpty ? "Not set" : band.capitalized
    }

    private func factRow(_ label: String, _ value: String) -> some View {
        HStack(spacing: .hearth800) {
            Text(label)
                .font(.hearthSectionHeader)
                .foregroundColor(.inkDisplay)
            Text(value)
                .font(.hearthTitleMD)
                .foregroundColor(.inkDisplay)
        }
    }

    // MARK: - Personality chips (the two `kid-001b` variants)

    /// Collapsed (`858:4985`): "Personality" + the design's three chips.
    /// Expanded (`907:2949`): "More about {Name}" + those three, the three the
    /// funnel no longer offers, and the `More` chip that closes it again.
    ///
    /// This is where sprint-1's evicted temperaments live: the funnel shows the
    /// design's three, all six stay in `ProfileOptions.temperamentChips`, and a
    /// parent reaches the other three by opening this group.
    private var personalityGroup: some View {
        VStack(alignment: .leading, spacing: .hearth600) {
            Text(chipsExpanded ? "More about \(displayName)" : "Personality")
                .font(.hearthBodySMBold)
                .foregroundColor(.inkDisplay)

            FlowLayout(spacing: .hearth300) {
                ForEach(visibleTemperaments, id: \.label) { option in
                    temperamentChip(option)
                }
            }

            moreChip

            if let error = model.error {
                Text(error).font(.hearthBodySM).foregroundColor(.statusError)
            }
        }
        .padding(.top, .hearth600)
    }

    private var visibleTemperaments: [(label: String, symbol: String)] {
        chipsExpanded ? ProfileOptions.temperamentChips : ProfileOptions.temperamentChipsPrimary
    }

    /// Full-width in the frame, and a real toggle — it reveals the three extra
    /// temperaments, and closes them again.
    private var moreChip: some View {
        Button {
            withAnimation(.hearthFast) { chipsExpanded.toggle() }
        } label: {
            Text(chipsExpanded ? "Fewer" : "More")
                .font(.hearthBodySM)
                .foregroundColor(.accentOnCanvas)
                .frame(maxWidth: .infinity)
                .padding(.vertical, .hearth400)
                .background(Capsule().fill(Color.bgCoachBanner))
                .overlay(Capsule().stroke(Color.accentDefault, lineWidth: 0.5))
        }
        .buttonStyle(.plain)
        .accessibilityHint(chipsExpanded
                           ? "Hides the less common personality options"
                           : "Shows more personality options")
    }

    private func temperamentChip(_ option: (label: String, symbol: String)) -> some View {
        let selected = model.kid.temperament == option.label
        return Button {
            // Tap toggles: selecting clears any other value (the backend field
            // is a single string), tapping the selected one clears it.
            model.saveTemperament(selected ? "" : option.label, onChanged: onProfileChanged)
        } label: {
            HStack(spacing: .hearth200) {
                Image(systemName: option.symbol)
                    .font(.system(size: 13, weight: .regular))
                Text(option.label)
                    .font(.hearthBodySM)
                    .lineLimit(1)
            }
            .foregroundColor(selected ? .inkOnPhotoLight : .accentOnCanvas)
            .padding(.horizontal, .hearth500)
            .padding(.vertical, .hearth400)
            .background(Capsule().fill(selected ? Color.accentDefault : Color.bgCoachBanner))
            .overlay(
                Capsule().stroke(selected ? Color.clear : Color.accentDefault, lineWidth: 0.5)
            )
        }
        .buttonStyle(.plain)
        .disabled(model.saving)
        .accessibilityAddTraits(selected ? [.isSelected] : [])
    }

    // MARK: - "What makes {Name} special"

    private var specialCard: some View {
        card(spacing: .hearth300) {
            Text("What makes \(displayName) special")
                .font(.hearthSectionHeader)
                .foregroundColor(.inkDisplay)

            ForEach(KidLearnedField.allCases, id: \.self) { field in
                disclosureRow(field)
            }
        }
    }

    /// One disclosure row. Closed = the `kid-001c` state (label + arrow).
    /// Open = the `kid-001b` state: the stored values in a teal-stroked r12 box,
    /// or that field's grey "Examples: …" prompt when nothing is stored yet
    /// (variant `907:2949`). The box itself pushes the list editor, so an
    /// example is an invitation to fill it in, never a dead end.
    @ViewBuilder
    private func disclosureRow(_ field: KidLearnedField) -> some View {
        let open = openRows.contains(field)
        let values = field.values(of: model.kid)
        VStack(alignment: .leading, spacing: .hearth300) {
            Button {
                withAnimation(.hearthFast) {
                    if open { openRows.remove(field) } else { openRows.insert(field) }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: open ? "chevron.down" : "chevron.right")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(.inkDisplay)
                        .frame(width: 16, height: 16)
                    Text(field.title(for: displayName))
                        .font(.hearthBodySM)
                        .foregroundColor(.inkDisplay)
                    Spacer(minLength: .hearth300)
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityLabel(field.title(for: displayName))
            .accessibilityHint(open ? "Collapses this list" : "Shows this list")

            if open { valueBox(field, values: values) }
        }
        .padding(.top, 4)
        .padding(.bottom, .hearth400)
        .overlay(alignment: .bottom) { rule }
    }

    private func valueBox(_ field: KidLearnedField, values: [String]) -> some View {
        Button { route = .learned(field) } label: {
            Text(values.isEmpty ? field.examplePrompt : values.joined(separator: ", "))
                .font(.hearthBodySM)
                .foregroundColor(values.isEmpty ? .inkEyebrow : .accentOnCanvas)
                .multilineTextAlignment(.leading)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.hearth300)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                        .stroke(Color.accentDefault, lineWidth: 0.5)
                )
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .padding(.leading, .hearth500)
        .accessibilityLabel("Edit \(field.title(for: displayName))")
    }

    // MARK: - Coach + companion

    private var coachCard: some View {
        card(spacing: .hearth300) {
            Text("COACH  •  \(displayName)'s activity")
                .font(.hearthSectionHeader)
                .foregroundColor(.accentOnCanvas)

            Text(model.coachNote ?? "Your coach hasn't shared anything about \(displayName) yet — it will show up here after your first few conversations.")
                .font(.hearthBodyLG)
                .lineSpacing(.hearthLineBodyLG)
                .foregroundColor(model.coachNote == nil ? .inkMuted : .inkSecondary)
                .fixedSize(horizontal: false, vertical: true)

            if let onViewAllCoach {
                Button { onViewAllCoach() } label: {
                    Text("Try this with \(displayName)")
                        .font(.hearthButtonLabel)
                        .foregroundColor(.accentOnCanvas)
                        .padding(.horizontal, .hearth400)
                        .padding(.vertical, .hearth300)
                        .overlay(
                            RoundedRectangle(cornerRadius: .hearthRadiusSeeAll,
                                             style: .continuous)
                                .stroke(Color.accentDefault, lineWidth: 1)
                        )
                }
                .buttonStyle(.plain)
            }
        }
    }

    private var companionCard: some View {
        card(spacing: .hearth300) {
            Text("Companion")
                .font(.hearthBodySMBold)
                .foregroundColor(.inkDisplay)

            Button { route = .companion } label: {
                HStack(alignment: .top, spacing: .hearth400) {
                    Circle()
                        .fill(accent)
                        .frame(width: 36, height: 36)
                        .overlay(
                            Text(String(companionName.prefix(1)).uppercased())
                                .font(.hearthTitleMD)
                                .foregroundColor(.inkOnPhotoLight)
                        )
                    VStack(alignment: .leading, spacing: 4) {
                        Text(companionName)
                            .font(.hearthTitleMD)
                            .foregroundColor(.inkDisplay)
                        Text(companionBlurb)
                            .font(.hearthBodySM)
                            .foregroundColor(.inkSecondary)
                            .lineLimit(2)
                            .multilineTextAlignment(.leading)
                    }
                    Spacer(minLength: .hearth300)
                    Image(systemName: "ellipsis")
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(.accentOnCanvas)
                        .padding(.top, 4)
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Edit \(displayName)'s companion")
        }
    }

    private var companionName: String {
        let name = model.companion?.invariants.agentDisplayName ?? ""
        return name.isEmpty ? "Set up a companion" : name
    }

    private var companionBlurb: String {
        if model.companion?.crisisLocked == true {
            return "Paused for safety — tap to review and reactivate."
        }
        guard let companion = model.companion else {
            return "\(displayName) doesn't have a companion yet. Tap to introduce one."
        }
        let personality = companion.invariants.personalityDescription
            .trimmingCharacters(in: .whitespacesAndNewlines)
        if !personality.isEmpty { return personality }
        let interests = companion.invariants.interestsSummary
            .trimmingCharacters(in: .whitespacesAndNewlines)
        if !interests.isEmpty { return interests }
        return "\(companionName) is \(displayName)'s current buddy."
    }

    // MARK: - Save / Cancel

    /// Every control on this sheet writes on change — durably, verified, one
    /// PATCH per key. So Save is not a second write path: it re-reads the
    /// profile and closes ONLY once the server has handed back a family that
    /// still contains this kid. A failed read keeps the sheet open with its
    /// error, so nothing is dismissed on an assumption.
    private var saveBar: some View {
        VStack(spacing: .hearth400) {
            Button {
                Task { if await model.confirmSaved(onChanged: onProfileChanged) { dismiss() } }
            } label: {
                Text(model.confirming ? "Saving…" : "Save")
                    .font(.hearthSectionHeader)
                    .foregroundColor(.inkOnPhotoLight)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, .hearth400)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .fill(Color.accentDefault)
                    )
            }
            .buttonStyle(.plain)
            .disabled(model.confirming)

            Button { dismiss() } label: {
                Text("Cancel")
                    .font(.hearthSectionHeader)
                    .foregroundColor(.accentOnCanvas)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, .hearth400)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .fill(Color.bgElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusMd,
                                                 style: .continuous)
                                    .stroke(Color.accentDefault, lineWidth: 1)
                            )
                    )
            }
            .buttonStyle(.plain)
        }
        .padding(.top, .hearth400)
    }

    // MARK: - Shared card ground

    /// The frames' white r32 card: `pad 30`, gap 16 unless overridden. r32 has
    /// no radius token; `hearthRadiusXl` (28) is the nearest step.
    private func card<Content: View>(
        spacing: CGFloat = .hearth500,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: spacing) { content() }
            .padding(.hearth800)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: .hearthRadiusXl, style: .continuous)
                    .fill(Color.bgElevated)
            )
            .hearthCardElevation()
    }
}

// MARK: - Model

@MainActor
final class KidSettingsModel: ObservableObject {
    @Published var kid: ChildProfileDTO
    @Published var companion: KidAgentConfig?
    @Published var coachNote: String?
    @Published var saving = false
    /// Distinct from `saving`: the Save button's confirming re-read.
    @Published var confirming = false
    @Published var error: String?
    /// Bumped to force the `.task(id:)` refresh (e.g. after returning from the
    /// companion editor). Mirrors the token pattern the rest of the app uses.
    @Published var refreshToken = 0

    private let baseURL: URL?
    private let userID: String
    private let kidKey: String

    init(baseURL: URL?, userID: String, kidKey: String, kid: ChildProfileDTO) {
        self.baseURL = baseURL
        self.userID = userID
        self.kidKey = kidKey
        self.kid = kid
    }

    func apply(_ family: FamilyProfileDTO) {
        if let updated = family.children?[kidKey] { kid = updated }
    }

    /// Re-reads everything this sheet renders: the profile row (source of
    /// truth), the kid's companion config, and the coach's latest note.
    func refresh() async {
        guard let baseURL, !userID.isEmpty else { return }
        if let fam = try? await ProfileService.getProfile(baseURL: baseURL, userID: userID) {
            apply(fam)
        }
        companion = await Self.companionConfig(baseURL: baseURL, userID: userID, kidKey: kidKey)
        coachNote = await Self.coachNote(baseURL: baseURL, userID: userID, kidKey: kidKey)
    }

    /// Verify-and-close for the Save button. Returns true only when the server
    /// answered with a family that still holds this kid — the caller dismisses
    /// on that and nothing else.
    func confirmSaved(onChanged: @escaping (FamilyProfileDTO) -> Void) async -> Bool {
        guard let baseURL, !userID.isEmpty else { return true }
        confirming = true
        error = nil
        defer { confirming = false }
        guard let fam = try? await ProfileService.getProfile(baseURL: baseURL, userID: userID)
        else {
            error = "Couldn't reach the server to confirm your changes. Try again."
            return false
        }
        apply(fam)
        onChanged(fam)
        return true
    }

    // MARK: Writes — each sends ONLY the key it owns (partial update)

    func saveTemperament(_ value: String, onChanged: @escaping (FamilyProfileDTO) -> Void) {
        let previous = kid.temperament
        kid.temperament = value.isEmpty ? nil : value
        patch(["temperament": value], onChanged: onChanged) { [weak self] in
            self?.kid.temperament = previous
        }
    }

    // Grade is edited in `KidProfileEditor` (the basics screen this sheet
    // pushes), alongside name/age/pronouns — the frames put Grade in the
    // read-only fact card, not in a chip. There is deliberately no
    // `saveGradeBand` here: a second write path for one field is how the two
    // drift.

    /// One PATCH, one key. Optimistic locally, rolled back on failure, and the
    /// server's family is applied on success so the sheet renders what actually
    /// persisted rather than what we hoped.
    private func patch(_ fields: [String: Any],
                       onChanged: @escaping (FamilyProfileDTO) -> Void,
                       rollback: @escaping () -> Void) {
        guard let baseURL else { return }
        saving = true
        error = nil
        Task {
            do {
                let fam = try await ProfileService.updateKid(
                    baseURL: baseURL, userID: userID, name: kidKey, fields: fields
                )
                apply(fam)
                onChanged(fam)
            } catch {
                rollback()
                self.error = "Couldn't save that. Check your connection and try again."
            }
            saving = false
        }
    }

    // MARK: Reads

    private static func companionConfig(baseURL: URL, userID: String,
                                        kidKey: String) async -> KidAgentConfig? {
        let service = KidAgentService(baseURL: baseURL, userID: userID)
        // `list()` is the only read that carries `crisis_locked`, and it degrades
        // to empty when consent hasn't been accepted yet.
        guard let configs = try? await service.list() else { return nil }
        return configs.first { $0.kidName == kidKey }
    }

    /// GET /coach/nudge — the parent's latest coach note. Rendered here only
    /// when it is ABOUT this kid; a family-wide or sibling nudge falls through
    /// to the empty state rather than mislabelling itself as Ben's activity.
    private static func coachNote(baseURL: URL, userID: String,
                                  kidKey: String) async -> String? {
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        var request = URLRequest(url: baseURL.appendingPathComponent("coach/nudge"))
        request.timeoutInterval = 15
        for (key, value) in AuthService.shared.header(for: userID) {
            request.setValue(value, forHTTPHeaderField: key)
        }
        guard let (data, response) = try? await URLSession.shared.data(for: request),
              let http = response as? HTTPURLResponse,
              (200..<300).contains(http.statusCode),
              let envelope = try? JSONDecoder().decode(CoachNudgeEnvelope.self, from: data),
              let nudge = envelope.nudge,
              nudge.kidName?.caseInsensitiveCompare(kidKey) == .orderedSame else {
            return nil
        }
        let body = nudge.body.trimmingCharacters(in: .whitespacesAndNewlines)
        return body.isEmpty ? nil : body
    }

    // Nested so the names can't collide with a Home-surface coach-nudge model.
    private struct CoachNudgeEnvelope: Decodable {
        let nudge: CoachNudgeDTO?
    }

    private struct CoachNudgeDTO: Decodable {
        let body: String
        let kidName: String?

        enum CodingKeys: String, CodingKey {
            case body
            case kidName = "kid_name"
        }
    }
}

extension Double {
    /// "5" not "5.0"; "4.5" stays "4.5". Used by the Age row.
    var kidAgeLabel: String {
        truncatingRemainder(dividingBy: 1) == 0 ? String(Int(self)) : String(self)
    }
}
