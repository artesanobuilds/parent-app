import SwiftUI

// Kid settings sheet (beta-v1, Greg's `child settings` frames).
//
// One kid, everything the parent can see or change about them, on a white
// ground: photo/monogram avatar with a camera-badge Edit, name • age,
// personality chips, the coach's latest note, the companion card, and the
// three learned lists. It is a RESTYLE — every write still goes through the
// existing PATCH /profile/kids/{name} partial-update path, and every editor it
// pushes (`KidProfileEditor`, `KidLearnedListEditor`, `ReviewLetterView`) is
// the one that already shipped.
//
// Partial-update semantics are load-bearing: each control sends ONLY the keys
// it owns (`temperament`, `grade_band`, one learned list), so a change here can
// never wipe a field the coach learned. See
// `tests/test_onboarding_seed_contract.py::test_saving_basics_does_not_wipe_learned_fields`.

struct KidSettingsSheet: View {
    let baseURL: URL?
    let userID: String
    /// The server's dictionary key for this kid — the name the profile was
    /// stored under. Never the draft/edited display name (attach + PATCH 404 on
    /// an unknown kid).
    let kidKey: String
    /// Optional: the presenter's "show me the whole coach thread" action (the
    /// Coach tab). When nil the `View all` button is hidden rather than dead.
    var onViewAllCoach: (() -> Void)? = nil
    /// Called with the fresh family on every mutation, so the presenting view's
    /// source-of-truth stays current without waiting for dismissal.
    var onProfileChanged: (FamilyProfileDTO) -> Void

    @StateObject private var model: KidSettingsModel
    @State private var route: Route?
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

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                header
                hairline
                ScrollView {
                    VStack(spacing: 0) {
                        avatarBlock
                        nameAgeRow
                        hairline.padding(.top, .hearth500)
                        personalitySection
                        hairline
                        coachSection
                        hairline
                        companionSection
                        hairline
                        learnedSection
                    }
                    .padding(.horizontal, .hearth600)
                    .padding(.bottom, .hearth700)
                }
                doneBar
            }
            .background(Color.bgElevated.ignoresSafeArea())
            .toolbar(.hidden, for: .navigationBar)
            .navigationDestination(item: $route) { destination in
                switch destination {
                case .basics:
                    KidProfileEditor(
                        baseURL: baseURL, userID: userID,
                        kidKey: kidKey, kid: model.kid
                    ) { fam in
                        // A delete inside the editor removes the kid entirely —
                        // this sheet then has nothing to show, so close it.
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

    // MARK: - Header

    private var header: some View {
        HStack {
            Text("\(displayName)'s settings")
                .font(.hearthTitleLG)
                .foregroundColor(.inkPrimary)
            Spacer()
            Button { dismiss() } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(.inkPrimary)
                    .frame(width: 44, height: 44, alignment: .trailing)
            }
            .accessibilityLabel("Close")
        }
        .padding(.horizontal, .hearth600)
        .padding(.vertical, .hearth400)
    }

    private var hairline: some View {
        Rectangle()
            .fill(Color.borderHairline)
            .frame(height: 1)
    }

    // MARK: - Avatar + name

    private var avatarBlock: some View {
        EditableAvatarView(
            avatarUrl: model.kid.avatarUrl,
            kidName: kidKey,
            userID: userID,
            baseURL: baseURL,
            size: 172,
            monogram: displayName,
            monogramFill: accent
        ) { fam in
            model.apply(fam)
            onProfileChanged(fam)
        }
        .padding(.top, .hearth700)
        .frame(maxWidth: .infinity)
    }

    private var nameAgeRow: some View {
        Button { route = .basics } label: {
            HStack(spacing: .hearth400) {
                Text(displayName)
                    .font(.hearthDisplayMD)
                    .foregroundColor(.inkPrimary)
                if let age = model.kid.age {
                    Text("•").font(.hearthDisplayMD).foregroundColor(.inkMuted)
                    Text(age.kidAgeLabel)
                        .font(.hearthDisplayMD)
                        .foregroundColor(.inkPrimary)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.top, .hearth500)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Edit \(displayName)'s name, age and grade")
    }

    // MARK: - Personality

    private var personalitySection: some View {
        VStack(spacing: .hearth400) {
            Text("Personality or vibe")
                .font(.hearthBodySM.weight(.semibold))
                .foregroundColor(.inkPrimary)
                .frame(maxWidth: .infinity)

            FlowLayout(spacing: 8) {
                gradeChip
                ForEach(ProfileOptions.temperamentChips, id: \.label) { option in
                    temperamentChip(option)
                }
            }

            if let error = model.error {
                Text(error).font(.hearthBodySM).foregroundColor(.statusError)
            }
        }
        .padding(.vertical, .hearth500)
    }

    private var gradeChip: some View {
        Menu {
            Picker("Grade", selection: Binding(
                get: { model.kid.gradeBand ?? "" },
                set: { model.saveGradeBand($0, onChanged: onProfileChanged) }
            )) {
                ForEach(ProfileOptions.gradeBand, id: \.self) { band in
                    Text(band.isEmpty ? "Not set" : band.capitalized).tag(band)
                }
            }
        } label: {
            chipBody(
                label: (model.kid.gradeBand?.isEmpty == false)
                    ? model.kid.gradeBand!.capitalized : "Grade",
                symbol: "graduationcap",
                trailingSymbol: "chevron.down",
                selected: false
            )
        }
        .disabled(model.saving)
    }

    private func temperamentChip(_ option: (label: String, symbol: String)) -> some View {
        let selected = model.kid.temperament == option.label
        return Button {
            // Tap toggles: selecting clears any other value (the backend field
            // is a single string), tapping the selected one clears it.
            model.saveTemperament(selected ? "" : option.label, onChanged: onProfileChanged)
        } label: {
            chipBody(label: option.label, symbol: option.symbol,
                     trailingSymbol: nil, selected: selected)
        }
        .buttonStyle(.plain)
        .disabled(model.saving)
    }

    private func chipBody(label: String, symbol: String,
                          trailingSymbol: String?, selected: Bool) -> some View {
        HStack(spacing: 6) {
            Image(systemName: symbol)
                .font(.system(size: 12, weight: .regular))
                .foregroundColor(selected ? .inkOnPhotoLight : .accentDefault)
            Text(label)
                .font(.hearthBodySM.weight(.medium))
                .foregroundColor(selected ? .inkOnPhotoLight : .inkPrimary)
                .lineLimit(1)
            if let trailingSymbol {
                Image(systemName: trailingSymbol)
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundColor(selected ? .inkOnPhotoLight : .inkSecondary)
            }
        }
        .padding(.horizontal, .hearth400)
        .padding(.vertical, .hearth300)
        .background(
            Capsule().fill(selected ? Color.accentDefault : Color.bgElevated)
        )
        .overlay(
            Capsule().stroke(selected ? Color.clear : Color.borderHairline, lineWidth: 1)
        )
    }

    // MARK: - Coach

    private var coachSection: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            sectionHeader(symbol: "bubble.left", label: "Coach",
                          detail: "\(displayName)'s activity")

            VStack(alignment: .leading, spacing: .hearth500) {
                Text(model.coachNote ?? "Your coach hasn't shared anything about \(displayName) yet — it will show up here after your first few conversations.")
                    .font(.hearthBodyLG)
                    .lineSpacing(.hearthLineBodyLG)
                    .foregroundColor(model.coachNote == nil ? .inkMuted : .inkPrimary)
                    .fixedSize(horizontal: false, vertical: true)

                if let onViewAllCoach {
                    Button {
                        onViewAllCoach()
                    } label: {
                        Text("View all")
                            .font(.hearthBodyMD.weight(.semibold))
                            .foregroundColor(.inkOnPhotoLight)
                            .padding(.horizontal, .hearth500)
                            .padding(.vertical, .hearth300)
                            .background(
                                RoundedRectangle(cornerRadius: .hearthRadiusButton, style: .continuous)
                                    .fill(Color.accentDefault)
                            )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.hearth500)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                    .fill(Color.bgElevated)
            )
            .hearthCardElevation()
        }
        .padding(.vertical, .hearth600)
    }

    // MARK: - Companion

    private var companionSection: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            sectionHeader(symbol: "sparkles", label: "Companion", detail: nil)

            Button { route = .companion } label: {
                HStack(alignment: .top, spacing: .hearth400) {
                    Circle()
                        .fill(Color.accentDefault)
                        .frame(width: 36, height: 36)
                        .overlay(
                            Text(String(companionName.prefix(1)).uppercased())
                                .font(.hearthTitleMD)
                                .foregroundColor(.inkOnPhotoLight)
                        )
                    VStack(alignment: .leading, spacing: 4) {
                        Text(companionName)
                            .font(.hearthTitleMD)
                            .foregroundColor(.inkPrimary)
                        Text(companionBlurb)
                            .font(.hearthBodySM)
                            .foregroundColor(.inkSecondary)
                            .lineLimit(2)
                            .multilineTextAlignment(.leading)
                    }
                    Spacer(minLength: .hearth300)
                    Image(systemName: "ellipsis")
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(.inkSecondary)
                        .padding(.top, 4)
                }
                .padding(.hearth500)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                        .fill(Color.accentKidTint)
                )
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Edit \(displayName)'s companion")
        }
        .padding(.vertical, .hearth600)
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

    // MARK: - What we've learned

    private var learnedSection: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            sectionHeader(symbol: "sparkles", label: "What we've learned", detail: nil)
                .padding(.bottom, .hearth300)

            ForEach(Array(KidLearnedField.allCases.enumerated()), id: \.element) { index, field in
                if index > 0 { hairline }
                Button { route = .learned(field) } label: {
                    HStack {
                        Text(field.title)
                            .font(.hearthBodyMD)
                            .foregroundColor(.inkPrimary)
                        Spacer()
                        Image(systemName: "ellipsis")
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundColor(.inkSecondary)
                            .padding(.leading, .hearth300)
                    }
                    .padding(.vertical, .hearth400)
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityLabel("Edit \(field.title.lowercased()) for \(displayName)")
            }
            hairline
        }
        .padding(.top, .hearth600)
    }

    // MARK: - Shared bits

    private func sectionHeader(symbol: String, label: String, detail: String?) -> some View {
        HStack(spacing: 6) {
            Image(systemName: symbol)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.inkSecondary)
            Text(label)
                .font(.hearthSectionHeader)
                .textCase(.uppercase)
                .foregroundColor(.inkPrimary)
            if let detail {
                Text("• \(detail)")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
            }
        }
    }

    private var doneBar: some View {
        Button { dismiss() } label: {
            Text("Done")
                .font(.hearthTitleMD)
                .foregroundColor(.inkOnPhotoLight)
                .frame(maxWidth: .infinity)
                .padding(.vertical, .hearth500)
                .background(
                    RoundedRectangle(cornerRadius: .hearthRadiusButton, style: .continuous)
                        .fill(Color.accentDefault)
                )
        }
        .buttonStyle(.plain)
        .padding(.horizontal, .hearth600)
        .padding(.top, .hearth400)
        .padding(.bottom, .hearth300)
        .background(Color.bgElevated)
    }
}

// MARK: - Model

@MainActor
final class KidSettingsModel: ObservableObject {
    @Published var kid: ChildProfileDTO
    @Published var companion: KidAgentConfig?
    @Published var coachNote: String?
    @Published var saving = false
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

    // MARK: Writes — each sends ONLY the key it owns (partial update)

    func saveTemperament(_ value: String, onChanged: @escaping (FamilyProfileDTO) -> Void) {
        let previous = kid.temperament
        kid.temperament = value.isEmpty ? nil : value
        patch(["temperament": value], onChanged: onChanged) { [weak self] in
            self?.kid.temperament = previous
        }
    }

    func saveGradeBand(_ value: String, onChanged: @escaping (FamilyProfileDTO) -> Void) {
        let previous = kid.gradeBand
        kid.gradeBand = value.isEmpty ? nil : value
        patch(["grade_band": value], onChanged: onChanged) { [weak self] in
            self?.kid.gradeBand = previous
        }
    }

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
    /// "5" not "5.0"; "4.5" stays "4.5". Used by the `Ben • 5` line.
    var kidAgeLabel: String {
        truncatingRemainder(dividingBy: 1) == 0 ? String(Int(self)) : String(self)
    }
}
