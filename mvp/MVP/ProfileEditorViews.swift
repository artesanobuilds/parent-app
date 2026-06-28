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
                pickerRow("Language", ProfileOptions.language, $draft.primaryLanguage.orEmpty)
                pickerRow("Age range", ProfileOptions.ageRange, $draft.parentAgeRange.orEmpty)
            }

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

            if let error { Text(error).font(.hearthBodySM).foregroundColor(.statusError) }
        }
        .scrollContentBackground(.hidden)
        .background(Color.bgCanvas.ignoresSafeArea())
        .navigationTitle("You")
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
        let payload: [String: Any] = [
            "name": draft.name ?? "",
            "pronouns": draft.pronouns ?? "",
            "postal_code": draft.postalCode ?? "",
            "country": draft.country ?? "",
            "primary_language": draft.primaryLanguage ?? "",
            "parent_age_range": draft.parentAgeRange ?? "",
            "household_structure": draft.householdStructure ?? "",
            "employment": draft.employment ?? "",
            "work_hours": draft.workHours ?? "",
            "energy_pattern": draft.energyPattern ?? "",
            "adults_in_household": draft.adultsInHousehold as Any,
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
            Section("Basics") {
                TextField("Name", text: $draft.name.orEmpty)
                TextField("Pronouns", text: $draft.pronouns.orEmpty)
                TextField("Age", text: $ageText)
                    .keyboardType(.decimalPad)
                pickerRow("Grade band", ProfileOptions.gradeBand, $draft.gradeBand.orEmpty)
            }
            if let error { Text(error).font(.hearthBodySM).foregroundColor(.statusError) }
        }
        .scrollContentBackground(.hidden)
        .background(Color.bgCanvas.ignoresSafeArea())
        .navigationTitle(draft.name ?? kidKey)
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
