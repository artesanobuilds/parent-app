import SwiftUI

// Profile editor surfaces (2026-06-28): drill-down editors reached from the
// Settings → Profile hub. Basics editors expose the structured/demographic
// fields; the family-wide "What we've learned" screen surfaces + corrects the
// fields the coaching/onboarding agents inferred over time. All write through
// PATCH /profile and PATCH /profile/kids/{name} (list fields are replaced
// server-side, so edits/removals stick).

// MARK: - Binding helpers

extension Binding where Value == String? {
    /// A non-optional String binding (empty string ↔ nil) for TextField/Picker.
    var orEmpty: Binding<String> {
        Binding<String>(
            get: { wrappedValue ?? "" },
            set: { wrappedValue = $0.isEmpty ? nil : $0 }
        )
    }
}

extension Binding where Value == [String]? {
    var orEmptyArray: Binding<[String]> {
        Binding<[String]>(
            get: { wrappedValue ?? [] },
            set: { wrappedValue = $0.isEmpty ? nil : $0 }
        )
    }
}

// MARK: - Enum option lists (inferred from the backend field comments)

enum ProfileOptions {
    /// Temperament chips shown in the kid-settings sheet. Same labels + symbols
    /// the onboarding funnel offers, so a kid's vibe reads identically wherever
    /// it's set (see `patterns_onboarding_parity`). Single-select: the backend
    /// field `temperament` is one string, not a list.
    ///
    /// Sprint-1: Greg's kid frames show only three of these (Easy-going,
    /// Sensitive, Spirited). The funnel FILTERS this array down to those — see
    /// `OnboardingView.funnelTemperamentLabels`. The list itself stays complete
    /// so a temperament set here is still findable, and so the kid-settings
    /// sheet keeps offering all six. Do not fork it.
    static let temperamentChips: [(label: String, symbol: String)] = [
        ("Spirited", "flame"),
        ("Sensitive", "heart"),
        ("Easy-going", "cloud.sun"),
        ("Strong-willed", "bolt"),
        ("Shy/cautious", "tortoise"),
        ("Social butterfly", "figure.wave")
    ]

    /// The three the sprint-1 kid frames draw — Spirited / Sensitive /
    /// Easy-going, which is the first three above and the same SET the funnel
    /// filters to. The kid-settings card shows these collapsed and all six once
    /// its "More" chip is opened (`kid-001b` variant `907:2949` draws exactly
    /// that chip), which is where the other three stay reachable.
    static let temperamentChipsPrimary: [(label: String, symbol: String)] =
        Array(temperamentChips.prefix(3))

    /// The onboarding "free time" grid AND the account sheet's "Family
    /// interests" grid (Sprint-1 gap). Single source so a selection made at
    /// either surface reads identically at the other (see
    /// `patterns_onboarding_parity`). Backend field: `family_activities`.
    static let familyActivityOptions: [(label: String, symbol: String)] = [
        ("Arts & crafts", "paintpalette"),
        ("Museums", "building.columns"),
        ("Hiking", "figure.hiking"),
        ("Gardens", "leaf"),
        ("Nature", "tree"),
        ("Parks", "sportscourt"),
        ("Science", "atom")
    ]

    /// Figma-exported vector icons (`Onboarding - need help with acitivities`
    /// [sic], node `1004:1746`), one imageset per option, template-rendering
    /// so a single asset tints white-on-teal (selected) or teal-on-white
    /// (unselected). Exported 2026-08-09 via one batched `/images` SVG call —
    /// see `docs/design/beta-v1-sprint2.md` round-2 addendum for the node-id
    /// table if these ever need re-export. Two tiles in that frame ("Nature"
    /// swimmer, "Parks" rocket) are stray duplicates with no matching option
    /// in this list — skipped, not mapped.
    static func interestIconName(for option: String) -> String? {
        switch option {
        case "Arts & crafts": return "InterestIcon-artsCrafts"
        case "Museums": return "InterestIcon-museums"
        case "Hiking": return "InterestIcon-hiking"
        case "Gardens": return "InterestIcon-gardens"
        case "Nature": return "InterestIcon-nature"
        case "Parks": return "InterestIcon-parks"
        case "Science": return "InterestIcon-science"
        default: return nil
        }
    }

    /// "What's hardest right now" — the parent's stressors. Backend field:
    /// `stressors`. Sprint-1: Greg's "What's on your mind?" frame shows only the
    /// six the funnel now offers (see `OnboardingView.funnelChallengeLabels`);
    /// the other four still matter to Coach context, so they live here for the
    /// parent-profile editor to surface rather than being deleted.
    static let challengeChips: [(label: String, symbol: String)] = [
        ("Morning routines", "sunrise"),
        ("Bedtime battles", "moon.zzz"),
        ("Big emotions", "wave.3.left"),
        ("Picky eating", "fork.knife"),
        ("Screen time", "iphone"),
        ("Sibling rivalry", "person.2"),
        ("School struggles", "book.closed"),
        ("Behavior changes", "arrow.triangle.2.circlepath"),
        ("Work-life balance", "scale.3d"),
        ("Feeling alone in it", "person")
    ]

    /// "What would help" — the parent's goals. Backend field: `goals`. Asked by
    /// NO sprint-1 frame, so the funnel no longer shows it; the field is still
    /// seeded and still feeds Coach context, and the parent-profile editor
    /// already has a `ChipEditor(title: "Goals")` row. These are the suggested
    /// labels for that editor.
    static let goalChips: [(label: String, symbol: String)] = [
        ("Expert guidance", "book"),
        ("Daily strategies", "list.bullet"),
        ("Understanding my child", "magnifyingglass"),
        ("Community support", "person.3"),
        ("Managing my stress", "heart.circle"),
        ("Building confidence", "figure.stand")
    ]

    static let ageRange = ["", "<25", "25-34", "35-44", "45-54", "55+", "prefer_not_to_say"]
    static let employment = ["", "stay-at-home", "part-time", "full-time", "shift", "other"]
    static let household = ["", "single", "co-parenting", "two-parent", "divorced", "widowed", "blended", "multigenerational"]
    static let language = ["", "en", "es", "zh", "other"]
    static let gradeBand = ["", "preschool", "elementary", "middle", "high"]
    static let guidanceStyle = ["", "concise scripts", "explanations"]
    static let stressResponse = ["", "raise voice", "withdraw", "stays regulated"]
}

// Chips wrap via the shared `FlowLayout` (defined in ReviewLetterView.swift).

// MARK: - Chip editor (add / remove string-list values)

struct ChipEditor: View {
    let title: String
    @Binding var items: [String]

    @State private var adding = false
    @State private var draft = ""
    @FocusState private var focused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text(title)
                .font(.hearthBodySM.weight(.semibold))
                .foregroundColor(.inkSecondary)
            FlowLayout(spacing: 8) {
                ForEach(Array(items.enumerated()), id: \.offset) { idx, item in
                    chip(item) { items.remove(at: idx) }
                }
                if adding {
                    HStack(spacing: 4) {
                        TextField("Add", text: $draft)
                            .focused($focused)
                            .font(.hearthBodySM)
                            .frame(minWidth: 70)
                            .submitLabel(.done)
                            .onSubmit(commit)
                        Button(action: commit) {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundColor(.accentDefault)
                        }
                        .buttonStyle(.plain)
                    }
                    .padding(.horizontal, .hearth400)
                    .padding(.vertical, 6)
                    .background(Capsule().stroke(Color.borderStrong, lineWidth: 1))
                } else {
                    Button {
                        adding = true
                    } label: {
                        Label("Add", systemImage: "plus")
                            .font(.hearthBodySM.weight(.medium))
                            .foregroundColor(.accentDefault)
                            .padding(.horizontal, .hearth400)
                            .padding(.vertical, 6)
                            .background(Capsule().fill(Color.accentTint))
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .onChange(of: adding) { _, isAdding in
            if isAdding { focused = true }
        }
    }

    private func commit() {
        let t = draft.trimmingCharacters(in: .whitespacesAndNewlines)
        if !t.isEmpty && !items.contains(t) { items.append(t) }
        draft = ""
        adding = false
    }

    private func chip(_ text: String, onRemove: @escaping () -> Void) -> some View {
        HStack(spacing: 4) {
            Text(text)
                .font(.hearthBodySM)
                .foregroundColor(.inkPrimary)
            Button(action: onRemove) {
                Image(systemName: "xmark.circle.fill")
                    .font(.system(size: 13))
                    .foregroundColor(.inkMuted)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Remove \(text)")
        }
        .padding(.leading, .hearth400)
        .padding(.trailing, 6)
        .padding(.vertical, 6)
        .background(Capsule().fill(Color.accentTint))
    }
}

// MARK: - Suggested chips (multi-select onto a string list)

/// A wrapped row of tappable suggestions that toggle membership in a `[String]`
/// profile field. Used for the two grids sprint-1 removed from the funnel
/// (`stressors`, `goals`): the funnel shows the design's short list, this shows
/// the FULL option list so nothing became unreachable.
///
/// It only ever adds or removes the option's own label, so a value the coach
/// learned that isn't in `options` is untouched — the neighbouring `ChipEditor`
/// is what edits those.
struct SuggestedChipRow: View {
    let title: String
    let options: [String]
    @Binding var selection: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text(title)
                .font(.hearthBodySM.weight(.semibold))
                .foregroundColor(.inkSecondary)
            FlowLayout(spacing: 8) {
                ForEach(options, id: \.self) { option in
                    chip(option)
                }
            }
        }
    }

    private func chip(_ option: String) -> some View {
        let selected = selection.contains(option)
        return Button {
            if selected {
                selection.removeAll { $0 == option }
            } else {
                selection.append(option)
            }
        } label: {
            Text(option)
                .font(.hearthBodySM.weight(.medium))
                .foregroundColor(selected ? .inkOnPhotoLight : .inkPrimary)
                .padding(.horizontal, .hearth400)
                .padding(.vertical, 6)
                .background(
                    Capsule().fill(selected ? Color.accentDefault : Color.bgElevated)
                )
                .overlay(
                    Capsule().stroke(selected ? Color.clear : Color.borderChipOutline,
                                     lineWidth: 1)
                )
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(selected ? [.isSelected] : [])
    }
}

// MARK: - Shared row helpers

private func pickerRow(_ label: String, _ options: [String], _ binding: Binding<String>) -> some View {
    Picker(label, selection: binding) {
        ForEach(options, id: \.self) { opt in
            Text(opt.isEmpty ? "Not set" : opt).tag(opt)
        }
    }
}

// MARK: - Parent basics editor

struct ParentProfileEditor: View {
    let baseURL: URL?
    let userID: String
    var onSaved: (FamilyProfileDTO) -> Void

    @State private var draft: ParentProfileDTO
    @State private var saving = false
    @State private var error: String?
    @Environment(\.dismiss) private var dismiss

    init(baseURL: URL?, userID: String, parent: ParentProfileDTO,
         onSaved: @escaping (FamilyProfileDTO) -> Void) {
        self.baseURL = baseURL
        self.userID = userID
        _draft = State(initialValue: parent)
        self.onSaved = onSaved
    }

    var body: some View {
        Form {
            Section("Photo") {
                AvatarPickerRow(
                    avatarUrl: draft.avatarUrl, kidName: nil,
                    userID: userID, baseURL: baseURL
                ) { fam in
                    draft.avatarUrl = fam.parent?.avatarUrl
                    onSaved(fam)
                }
            }

            basicsSection
            householdSection
            coachSection
            // Sprint-1 evicted these two grids from the funnel. They are still
            // real profile fields the Coach reads, so this is where a parent
            // changes them now.
            mindSection

            if let error { Text(error).font(.hearthBodySM).foregroundColor(.statusError) }
        }
        .scrollContentBackground(.hidden)
        .background(Color.bgCanvas.ignoresSafeArea())
        .navigationTitle("You")
        .navigationBarTitleDisplayMode(.inline)
        .trackScreen("parent_profile_edit")
        .toolbar {
            ToolbarItem(placement: .confirmationAction) {
                Button(saving ? "Saving…" : "Save") { save() }.disabled(saving)
            }
        }
    }

    // MARK: Sections
    //
    // Split out of `body` deliberately: one long Form body on a screen this
    // dense is the shape that produces "unable to type-check this expression in
    // reasonable time" (a real build failure, not SourceKit noise).

    @ViewBuilder
    private var basicsSection: some View {
        Section("Basics") {
            TextField("Name", text: $draft.name.orEmpty)
            TextField("Pronouns", text: $draft.pronouns.orEmpty)
            TextField("ZIP / Postal code", text: $draft.postalCode.orEmpty)
                .keyboardType(.numbersAndPunctuation)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
            TextField("Country (e.g. US)", text: $draft.country.orEmpty)
                .textInputAutocapitalization(.characters)
                .autocorrectionDisabled()
            // The funnel no longer asks for language (sprint-1 drops the field
            // from `Onboarding - 2`), so this row is the only place a parent can
            // set or correct it. Labelled "Primary language" rather than
            // "Language" because that is the profile key it writes.
            pickerRow("Primary language", ProfileOptions.language,
                      $draft.primaryLanguage.orEmpty)
            // Backend field existed with no iOS editor until the consolidated
            // Settings "Language at home" card — every bilingual household's
            // second language was previously dropped on save.
            pickerRow("Secondary language", ProfileOptions.language,
                      $draft.secondaryLanguage.orEmpty)
            pickerRow("Age range", ProfileOptions.ageRange, $draft.parentAgeRange.orEmpty)
        }
    }

    @ViewBuilder
    private var householdSection: some View {
        Section("Household & work") {
            Stepper(
                "Adults at home: \(draft.adultsInHousehold.map(String.init) ?? "Not set")",
                value: Binding(
                    get: { draft.adultsInHousehold ?? 0 },
                    set: { draft.adultsInHousehold = $0 == 0 ? nil : $0 }
                ),
                in: 0...6
            )
            pickerRow("Household", ProfileOptions.household, $draft.householdStructure.orEmpty)
            pickerRow("Employment", ProfileOptions.employment, $draft.employment.orEmpty)
            TextField("Work hours", text: $draft.workHours.orEmpty)
            TextField("Energy pattern", text: $draft.energyPattern.orEmpty)
        }
    }

    /// Consolidated Settings "MVP coach settings" card. Voice is deliberately
    /// NOT here — the parent-coach voice is not overridable per-user
    /// (`server.py`: "Voice: intentionally NOT overridden here… the
    /// ElevenLabs dashboard decides"), unlike the kid companion's voice,
    /// which IS editable via `KidSettingsSheet`. Guidance style is a real
    /// backend field (`profiling.py: guidance_style`) that had no editor.
    @ViewBuilder
    private var coachSection: some View {
        Section("Coach") {
            pickerRow("Guidance style", ProfileOptions.guidanceStyle,
                      $draft.guidanceStyle.orEmpty)
        }
    }

    /// "What's hardest" + "What would help" — `stressors` and `goals`.
    ///
    /// The funnel's "What's on your mind?" screen now shows only the six
    /// hardest-right-now options the design draws, and drops the whole
    /// "What would help" section. Both fields are still seeded, still read by
    /// the Coach, and now editable here: the full option list is offered as
    /// tappable suggestions, and anything the parent (or the coach) added that
    /// isn't in the list is preserved as a free-text chip.
    @ViewBuilder
    private var mindSection: some View {
        Section {
            SuggestedChipRow(title: "What's hardest",
                             options: ProfileOptions.challengeChips.map(\.label),
                             selection: $draft.stressors.orEmptyArray)
            ChipEditor(title: "Anything else that's hard",
                       items: $draft.stressors.orEmptyArray)
        } header: {
            Text("What's on your mind")
        } footer: {
            Text("Your coach uses these to decide what to bring up — and what to leave alone.")
                .font(.hearthBodySM).foregroundColor(.inkMuted)
        }

        Section("What would help") {
            SuggestedChipRow(title: "Pick what would help",
                             options: ProfileOptions.goalChips.map(\.label),
                             selection: $draft.goals.orEmptyArray)
            ChipEditor(title: "Your own words", items: $draft.goals.orEmptyArray)
        }
    }

    private func save() {
        guard let baseURL else { return }
        saving = true; error = nil
        let payload: [String: Any] = [
            "name": draft.name ?? "",
            "pronouns": draft.pronouns ?? "",
            "postal_code": draft.postalCode ?? "",
            "country": draft.country ?? "",
            "primary_language": draft.primaryLanguage ?? "",
            "secondary_language": draft.secondaryLanguage ?? "",
            "parent_age_range": draft.parentAgeRange ?? "",
            "household_structure": draft.householdStructure ?? "",
            "employment": draft.employment ?? "",
            "work_hours": draft.workHours ?? "",
            "energy_pattern": draft.energyPattern ?? "",
            "guidance_style": draft.guidanceStyle ?? "",
            "adults_in_household": draft.adultsInHousehold as Any,
            // The two funnel-evicted grids. Sent as the WHOLE list on every
            // save (PATCH replaces list fields), so a de-selection sticks.
            "stressors": draft.stressors ?? [],
            "goals": draft.goals ?? [],
        ]
        Task {
            do {
                let fam = try await ProfileService.updateParent(
                    baseURL: baseURL, userID: userID, fields: payload.compactMapValues { $0 }
                )
                onSaved(fam)
                dismiss()
            } catch {
                self.error = "Couldn't save. Check your connection and try again."
            }
            saving = false
        }
    }
}

// MARK: - Kid basics editor

struct KidProfileEditor: View {
    let baseURL: URL?
    let userID: String
    let kidKey: String                 // the dictionary key (original name)
    var onSaved: (FamilyProfileDTO) -> Void

    @State private var draft: ChildProfileDTO
    @State private var ageText: String
    @State private var saving = false
    @State private var deleting = false
    @State private var confirmingDelete = false
    @State private var error: String?
    @Environment(\.dismiss) private var dismiss

    init(baseURL: URL?, userID: String, kidKey: String, kid: ChildProfileDTO,
         onSaved: @escaping (FamilyProfileDTO) -> Void) {
        self.baseURL = baseURL
        self.userID = userID
        self.kidKey = kidKey
        _draft = State(initialValue: kid)
        _ageText = State(initialValue: kid.age.map { $0.formattedAge } ?? "")
        self.onSaved = onSaved
    }

    var body: some View {
        Form {
            Section("Photo") {
                // kidName = kidKey (the server's dictionary key), NOT the
                // possibly-edited draft name — attach 404s unknown kids.
                AvatarPickerRow(
                    avatarUrl: draft.avatarUrl, kidName: kidKey,
                    userID: userID, baseURL: baseURL
                ) { fam in
                    draft.avatarUrl = fam.children?[kidKey]?.avatarUrl
                    onSaved(fam)
                }
            }

            Section("Basics") {
                TextField("Name", text: $draft.name.orEmpty)
                TextField("Pronouns", text: $draft.pronouns.orEmpty)
                TextField("Age", text: $ageText)
                    .keyboardType(.decimalPad)
                pickerRow("Grade band", ProfileOptions.gradeBand, $draft.gradeBand.orEmpty)
            }
            if let error { Text(error).font(.hearthBodySM).foregroundColor(.statusError) }

            // Destructive: remove this child entirely. Confirmed before it runs.
            Section {
                Button(role: .destructive) {
                    confirmingDelete = true
                } label: {
                    HStack {
                        if deleting { ProgressView().padding(.trailing, 4) }
                        Text(deleting ? "Deleting…" : "Delete profile")
                    }
                }
                .disabled(saving || deleting)
            } footer: {
                Text("Removes \(draft.name ?? kidKey) and everything saved about them.")
                    .font(.hearthBodySM).foregroundColor(.inkMuted)
            }
        }
        .scrollContentBackground(.hidden)
        .background(Color.bgCanvas.ignoresSafeArea())
        .trackScreen("kid_profile_edit")
        .navigationTitle(draft.name ?? kidKey)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .confirmationAction) {
                Button(saving ? "Saving…" : "Save") { save() }.disabled(saving || deleting)
            }
        }
        .confirmationDialog(
            "Delete \(draft.name ?? kidKey)'s profile?",
            isPresented: $confirmingDelete,
            titleVisibility: .visible
        ) {
            Button("Delete profile", role: .destructive) { delete() }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This permanently removes \(draft.name ?? kidKey) and everything saved about them. This can't be undone.")
        }
    }

    private func delete() {
        guard let baseURL else { return }
        deleting = true; error = nil
        Task {
            do {
                let fam = try await ProfileService.deleteKid(
                    baseURL: baseURL, userID: userID, name: kidKey
                )
                onSaved(fam)
                dismiss()
            } catch {
                self.error = "Couldn't delete. Check your connection and try again."
            }
            deleting = false
        }
    }

    private func save() {
        guard let baseURL else { return }
        saving = true; error = nil
        var payload: [String: Any] = [
            "name": draft.name ?? kidKey,
            "pronouns": draft.pronouns ?? "",
            "grade_band": draft.gradeBand ?? "",
        ]
        if let age = Double(ageText.trimmingCharacters(in: .whitespaces)) {
            payload["age"] = age
        }
        Task {
            do {
                let fam = try await ProfileService.updateKid(
                    baseURL: baseURL, userID: userID, name: kidKey, fields: payload
                )
                onSaved(fam)
                dismiss()
            } catch {
                self.error = "Couldn't save. Check your connection and try again."
            }
            saving = false
        }
    }
}

// MARK: - Add a kid

struct AddKidSheet: View {
    let baseURL: URL?
    let userID: String
    var onSaved: (FamilyProfileDTO) -> Void

    @State private var name = ""
    @State private var ageText = ""
    @State private var pronouns = ""
    @State private var gradeBand = ""
    @State private var saving = false
    @State private var error: String?
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Name", text: $name)
                    TextField("Age", text: $ageText).keyboardType(.decimalPad)
                    TextField("Pronouns (optional)", text: $pronouns)
                    pickerRow("Grade band", ProfileOptions.gradeBand, $gradeBand)
                } footer: {
                    Text("You can add more detail later — your coach also fills it in over time.")
                        .font(.hearthBodySM).foregroundColor(.inkMuted)
                }
                if let error { Text(error).font(.hearthBodySM).foregroundColor(.statusError) }
            }
            .scrollContentBackground(.hidden)
            .background(Color.bgCanvas.ignoresSafeArea())
            .trackScreen("add_kid")
            .navigationTitle("Add a kid")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(saving ? "Adding…" : "Add kid") { save() }
                        .disabled(saving || name.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
    }

    private func save() {
        guard let baseURL else { return }
        let kidName = name.trimmingCharacters(in: .whitespaces)
        guard !kidName.isEmpty else { return }
        saving = true; error = nil
        var payload: [String: Any] = ["name": kidName]
        if let age = Double(ageText.trimmingCharacters(in: .whitespaces)) { payload["age"] = age }
        if !pronouns.isEmpty { payload["pronouns"] = pronouns }
        if !gradeBand.isEmpty { payload["grade_band"] = gradeBand }
        Task {
            do {
                let fam = try await ProfileService.updateKid(
                    baseURL: baseURL, userID: userID, name: kidName, fields: payload
                )
                onSaved(fam)
                dismiss()
            } catch {
                self.error = "Couldn't add. Check your connection and try again."
            }
            saving = false
        }
    }
}

// MARK: - One learned list, for one kid (the kid-settings sheet's rows)

/// The five "What makes {name} special" rows sprint-1 measures on the kid
/// frames, in the design's order: Likes · Dislikes · Challenges · Excels at ·
/// Goals for {name}. Each maps to exactly ONE snake_case key on
/// PATCH /profile/kids/{name}.
///
/// Each row stores under its OWN backend key. `dislikes` and a per-kid `goals`
/// were added to `ChildProfile` on 2026-08-08 for exactly this reason: the rows
/// had been borrowing `triggers`/`motivators`, which meant the label and the
/// storage disagreed, and a client sending the real names would have hit the
/// auto-derived PATCH whitelist and been silently DROPPED — a row that looks
/// saved and isn't. Only `Excels at` still borrows (`strengths`), which is a
/// genuine synonym rather than an approximation.
enum KidLearnedField: String, CaseIterable, Hashable {
    case likes, dislikes, challenges, excelsAt, goals

    /// The design labels the last row with the kid's name.
    func title(for kidName: String) -> String {
        switch self {
        case .likes:      return "Likes"
        case .dislikes:   return "Dislikes"
        case .challenges: return "Challenges"
        case .excelsAt:   return "Excels at"
        case .goals:      return "Goals for \(kidName)"
        }
    }

    /// Name-free label, for the editors that push with a nav title.
    var title: String { title(for: "them") }

    /// `kid-001b` variant `907:2949`'s grey prompts, verbatim.
    var examplePrompt: String {
        switch self {
        case .likes:      return "Examples: Berries, kittens, silly songs"
        case .dislikes:   return "Examples: green food, loud noises"
        case .challenges: return "Examples: bathtime"
        case .excelsAt:   return "Examples: math"
        case .goals:      return "Examples: social"
        }
    }

    /// The ONLY key this editor sends. Everything else the coach has learned is
    /// left out of the payload on purpose — PATCH only touches keys that are
    /// present, which is what stops one edit from wiping the rest
    /// (`test_saving_basics_does_not_wipe_learned_fields`).
    var payloadKey: String {
        switch self {
        case .likes:      return "interests"
        case .dislikes:   return "dislikes"
        case .challenges: return "challenges"
        case .excelsAt:   return "strengths"
        case .goals:      return "goals"
        }
    }

    func values(of kid: ChildProfileDTO) -> [String] {
        switch self {
        case .likes:      return kid.interests ?? []
        case .dislikes:   return kid.dislikes ?? []
        case .challenges: return kid.challenges ?? []
        case .excelsAt:   return kid.strengths ?? []
        case .goals:      return kid.goals ?? []
        }
    }
}

/// Edits a single learned list for a single kid. Pushed from the kid-settings
/// sheet's "What makes {name} special" rows.
struct KidLearnedListEditor: View {
    let baseURL: URL?
    let userID: String
    let kidKey: String          // the server's dictionary key, not the draft name
    let kidDisplayName: String
    let field: KidLearnedField
    var onSaved: (FamilyProfileDTO) -> Void

    @State private var items: [String]
    @State private var saving = false
    @State private var error: String?
    @Environment(\.dismiss) private var dismiss

    init(baseURL: URL?, userID: String, kidKey: String, kidDisplayName: String,
         field: KidLearnedField, kid: ChildProfileDTO,
         onSaved: @escaping (FamilyProfileDTO) -> Void) {
        self.baseURL = baseURL
        self.userID = userID
        self.kidKey = kidKey
        self.kidDisplayName = kidDisplayName
        self.field = field
        _items = State(initialValue: field.values(of: kid))
        self.onSaved = onSaved
    }

    var body: some View {
        Form {
            Section {
                ChipEditor(title: field.title(for: kidDisplayName), items: $items)
            } footer: {
                Text("Gathered from \(kidDisplayName)'s conversations. Edit or remove anything that's off.")
                    .font(.hearthBodySM).foregroundColor(.inkMuted)
            }
            if let error { Text(error).font(.hearthBodySM).foregroundColor(.statusError) }
        }
        .scrollContentBackground(.hidden)
        .background(Color.bgCanvas.ignoresSafeArea())
        .trackScreen("kid_learned_\(field.rawValue)")
        .navigationTitle(field.title(for: kidDisplayName))
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .confirmationAction) {
                Button(saving ? "Saving…" : "Save") { save() }.disabled(saving)
            }
        }
    }

    private func save() {
        guard let baseURL else { return }
        saving = true; error = nil
        Task {
            do {
                let fam = try await ProfileService.updateKid(
                    baseURL: baseURL, userID: userID, name: kidKey,
                    fields: [field.payloadKey: items]
                )
                onSaved(fam)
                dismiss()
            } catch {
                self.error = "Couldn't save. Check your connection and try again."
            }
            saving = false
        }
    }
}

// MARK: - "What we've learned" (family-wide, edit-only)

struct LearnedProfileView: View {
    let baseURL: URL?
    let userID: String
    var onSaved: (FamilyProfileDTO) -> Void

    @State private var parent: ParentProfileDTO
    @State private var kids: [String: ChildProfileDTO]
    @State private var kidKeys: [String]
    @State private var saving = false
    @State private var error: String?
    @Environment(\.dismiss) private var dismiss

    init(baseURL: URL?, userID: String, family: FamilyProfileDTO,
         onSaved: @escaping (FamilyProfileDTO) -> Void) {
        self.baseURL = baseURL
        self.userID = userID
        _parent = State(initialValue: family.parent ?? ParentProfileDTO())
        let children = family.children ?? [:]
        _kids = State(initialValue: children)
        _kidKeys = State(initialValue: children.keys.sorted())
        self.onSaved = onSaved
    }

    var body: some View {
        Form {
            Section {
                Text("Gathered from your conversations with your coach. Edit or remove anything that's off.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
            }

            parentSection

            ForEach(kidKeys, id: \.self) { key in
                kidSection(key)
            }

            if let error { Text(error).font(.hearthBodySM).foregroundColor(.statusError) }
        }
        .scrollContentBackground(.hidden)
        .background(Color.bgCanvas.ignoresSafeArea())
        .trackScreen("learned_profile")
        .navigationTitle("What we've learned")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .confirmationAction) {
                Button(saving ? "Saving…" : "Save") { save() }.disabled(saving)
            }
        }
    }

    @ViewBuilder
    private var parentSection: some View {
        Section(parent.name.map { "✦ \($0)" } ?? "✦ You") {
            TextField("Parenting style", text: $parent.parentingStyle.orEmpty, axis: .vertical)
            pickerRow("Guidance style", ProfileOptions.guidanceStyle, $parent.guidanceStyle.orEmpty)
            pickerRow("Stress response", ProfileOptions.stressResponse, $parent.defaultStressResponse.orEmpty)
            TextField("Dreaded moment", text: $parent.dreadedMoment.orEmpty, axis: .vertical)
            TextField("Support system", text: $parent.supportSystem.orEmpty, axis: .vertical)
            TextField("Support boundaries", text: $parent.supportBoundaries.orEmpty, axis: .vertical)
            TextField("Co-parenting", text: $parent.coParenting.orEmpty, axis: .vertical)
            TextField("Mental-health notes", text: $parent.mentalHealthNotes.orEmpty, axis: .vertical)
            ChipEditor(title: "Stressors", items: $parent.stressors.orEmptyArray)
            ChipEditor(title: "Goals", items: $parent.goals.orEmptyArray)
            ChipEditor(title: "Coping strategies", items: $parent.copingStrategies.orEmptyArray)
            ChipEditor(title: "What helps me de-escalate", items: $parent.deescalationWorks.orEmptyArray)
            ChipEditor(title: "What backfires", items: $parent.deescalationBackfires.orEmptyArray)
        }
    }

    @ViewBuilder
    private func kidSection(_ key: String) -> some View {
        let cb = kidBinding(key)
        let name = kids[key]?.name ?? key
        Section("✦ \(name)") {
            TextField("Temperament", text: cb.temperament.orEmpty, axis: .vertical)
            ChipEditor(title: "Interests", items: cb.interests.orEmptyArray)
            ChipEditor(title: "Strengths", items: cb.strengths.orEmptyArray)
            ChipEditor(title: "Academic strengths", items: cb.academicStrengths.orEmptyArray)
            ChipEditor(title: "Challenges", items: cb.challenges.orEmptyArray)
            ChipEditor(title: "Triggers", items: cb.triggers.orEmptyArray)
            ChipEditor(title: "Calming strategies", items: cb.calmingStrategies.orEmptyArray)
            ChipEditor(title: "Motivators", items: cb.motivators.orEmptyArray)
            ChipEditor(title: "Repair helpers", items: cb.repairHelpers.orEmptyArray)
            ChipEditor(title: "Recent changes", items: cb.recentChanges.orEmptyArray)
            ChipEditor(title: "Sibling conflicts", items: cb.siblingConflicts.orEmptyArray)
            TextField("Emotion regulation", text: cb.emotionRegulation.orEmpty, axis: .vertical)
            TextField("Social profile", text: cb.socialProfile.orEmpty, axis: .vertical)
            TextField("Learning profile", text: cb.learningProfile.orEmpty, axis: .vertical)
            TextField("Neurodiversity", text: cb.neurodiversity.orEmpty, axis: .vertical)
            TextField("Sensory notes", text: cb.sensoryNotes.orEmpty, axis: .vertical)
            TextField("Sleep routine", text: cb.sleepRoutine.orEmpty, axis: .vertical)
            TextField("Health notes", text: cb.healthNotes.orEmpty, axis: .vertical)
            TextField("Escalation pattern", text: cb.escalationPattern.orEmpty, axis: .vertical)
            TextField("School context", text: cb.schoolContext.orEmpty, axis: .vertical)
            TextField("Teacher notes", text: cb.teacherNotes.orEmpty, axis: .vertical)
            TextField("Safety flags", text: cb.safetyFlags.orEmpty, axis: .vertical)
        }
    }

    private func kidBinding(_ key: String) -> Binding<ChildProfileDTO> {
        Binding(
            get: { kids[key] ?? ChildProfileDTO() },
            set: { kids[key] = $0 }
        )
    }

    private func save() {
        guard let baseURL else { return }
        saving = true; error = nil
        Task {
            do {
                var fam = try await ProfileService.updateParent(
                    baseURL: baseURL, userID: userID, fields: Self.parentLearnedPayload(parent)
                )
                for key in kidKeys {
                    if let kid = kids[key] {
                        fam = try await ProfileService.updateKid(
                            baseURL: baseURL, userID: userID, name: key,
                            fields: Self.kidLearnedPayload(kid)
                        )
                    }
                }
                onSaved(fam)
                dismiss()
            } catch {
                self.error = "Couldn't save. Check your connection and try again."
            }
            saving = false
        }
    }

    // Always include the learned keys (scalars as "" when cleared, lists as the
    // current array) so edits AND removals persist server-side.
    private static func parentLearnedPayload(_ p: ParentProfileDTO) -> [String: Any] {
        [
            "parenting_style": p.parentingStyle ?? "",
            "guidance_style": p.guidanceStyle ?? "",
            "default_stress_response": p.defaultStressResponse ?? "",
            "dreaded_moment": p.dreadedMoment ?? "",
            "support_system": p.supportSystem ?? "",
            "support_boundaries": p.supportBoundaries ?? "",
            "co_parenting": p.coParenting ?? "",
            "mental_health_notes": p.mentalHealthNotes ?? "",
            "stressors": p.stressors ?? [],
            "goals": p.goals ?? [],
            "coping_strategies": p.copingStrategies ?? [],
            "deescalation_works": p.deescalationWorks ?? [],
            "deescalation_backfires": p.deescalationBackfires ?? [],
        ]
    }

    private static func kidLearnedPayload(_ c: ChildProfileDTO) -> [String: Any] {
        [
            "temperament": c.temperament ?? "",
            "emotion_regulation": c.emotionRegulation ?? "",
            "social_profile": c.socialProfile ?? "",
            "learning_profile": c.learningProfile ?? "",
            "neurodiversity": c.neurodiversity ?? "",
            "sensory_notes": c.sensoryNotes ?? "",
            "sleep_routine": c.sleepRoutine ?? "",
            "health_notes": c.healthNotes ?? "",
            "escalation_pattern": c.escalationPattern ?? "",
            "school_context": c.schoolContext ?? "",
            "teacher_notes": c.teacherNotes ?? "",
            "safety_flags": c.safetyFlags ?? "",
            "interests": c.interests ?? [],
            "strengths": c.strengths ?? [],
            "academic_strengths": c.academicStrengths ?? [],
            "challenges": c.challenges ?? [],
            "triggers": c.triggers ?? [],
            "calming_strategies": c.calmingStrategies ?? [],
            "recent_changes": c.recentChanges ?? [],
            "sibling_conflicts": c.siblingConflicts ?? [],
            "repair_helpers": c.repairHelpers ?? [],
            "motivators": c.motivators ?? [],
        ]
    }
}

private extension Double {
    /// "7" not "7.0"; "4.5" stays "4.5".
    var formattedAge: String {
        truncatingRemainder(dividingBy: 1) == 0 ? String(Int(self)) : String(self)
    }
}
