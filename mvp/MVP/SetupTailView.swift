import SwiftUI

// The post-account "one last thing" screen — Heisman sprint-01, Figma frame
// `69:1313` "one last thing" (402×1917, file `nAXZQhmvwEpzq3rkBisok7`), pulled
// 2026-08-21 via the Figma MCP. The designer replaced the old frame (`29:4183`,
// marked "Existing" in the sprint spec) with this single-page form, so the
// previous stepped walk ("STEP 1 OF 2" → per-person editor hand-offs) is gone;
// this file now renders the whole screen itself:
//
//   "Coach:" mono eyebrow + "Two things about your household" (Fraunces 24/32)
//   → household card: Household Type + Language at home dropdowns
//   → coach line "I can pick better options for {kids} …"
//   → one "Tell me about {kid}" card per kid: age / grade / school-style
//     dropdowns + four expandable free-text rows
//   → "Set up later" underlined link.
//
// Hex → token mapping is the established Heisman table
// (OnboardingHeismanChrome.swift):
//   #FCFBF8 → .bgCoachBanner (screen ground + input-pill fill)
//   #F3F0EB → .bgSober (cards — the design file's "bg/canvas")
//   #151412 → .inkPrimary        #1E1E1E → .inkDisplay
//   #6E6A62 → .inkMuted          #C8C3B8 → .borderInputPill
//   #1B7498 → .accentOnCanvas (royal text/borders — the frame's
//              `primitives/photo/royal` variable NAME resolves to the accent
//              teal HEX, not the app's navy `photoRoyal`)
// The frame's blanket 0/0/100px text-shadows are a Figma export artifact —
// sprint acceptance #12 bans drop shadows on text; not implemented.
//
// Entry contract is unchanged (HomeView must not be restructured):
//   • `SetupTailView(userID:baseURL:entryStopID:onNeedsRefresh:)` presented as
//     a sheet by Home; `entryStopID` (a `SetupStop.kidID`) scrolls to that
//     kid's card instead of selecting a step.
//   • `SetupTailStore.shouldAutoPresent(kidKeys:userID:)` gates the auto-open.
//   • `onNeedsRefresh` fires after every verified mutation (CLAUDE.md: the
//     source-of-truth view re-fetches).
//
// Writes go through the same `ProfileService` PATCH endpoints as the settings
// editors — partial payloads only (one key per save), so this screen can never
// wipe fields it doesn't show (`test_saving_basics_does_not_wipe_learned_fields`).
// Every write is verified (2xx or the control reverts and an error line shows);
// nothing is fire-and-forget. Base URL arrives from the caller, resolved through
// `ServerConfiguration` — never a hardcoded fallback (tests/test_ios_baseurl_guard.py).

// MARK: - Durable progress

/// Local, per-account bookkeeping. Deliberately NOT server state: it records
/// what the parent has been *shown/asked*, not what they own — the profile
/// itself is the source of truth for what's filled in.
struct SetupTailState: Codable, Equatable {
    /// Stable ids (kid profile keys via `SetupStop.kidID`) the parent has
    /// saved something for on this screen.
    var completed: [String] = []
    /// Legacy from the stepped walk ("Skip for now"). Still honored by
    /// `isPending` so a parent who skipped kids pre-redesign isn't re-nagged.
    var skipped: [String] = []
    /// Every kid card has been completed at least once. Gates the auto-run.
    var finished = false
    /// "Set up later". Suppresses the auto-run permanently; this is a beta and
    /// a parent who opted out must not be asked again on every launch.
    var deferred = false

    func isPending(_ id: String) -> Bool {
        !completed.contains(id) && !skipped.contains(id)
    }
}

enum SetupTailStore {
    /// Keyed by account id so a second account on the same device (or a
    /// delete-account + re-onboard) starts clean.
    private static func key(for userID: String) -> String {
        "setup_tail_state_v1_\(userID)"
    }

    static func load(userID: String, defaults: UserDefaults = .standard) -> SetupTailState {
        guard !userID.isEmpty,
              let data = defaults.data(forKey: key(for: userID)),
              let state = try? JSONDecoder().decode(SetupTailState.self, from: data)
        else { return SetupTailState() }
        return state
    }

    static func save(_ state: SetupTailState, userID: String,
                     defaults: UserDefaults = .standard) {
        guard !userID.isEmpty, let data = try? JSONEncoder().encode(state) else { return }
        defaults.set(data, forKey: key(for: userID))
    }

    /// Should Home open this screen by itself? Only for a parent who has
    /// neither completed every kid nor opted out, and only when there is
    /// genuinely a kid still to fill in.
    static func shouldAutoPresent(kidKeys: [String], userID: String,
                                  defaults: UserDefaults = .standard) -> Bool {
        guard !kidKeys.isEmpty else { return false }
        let state = load(userID: userID, defaults: defaults)
        guard !state.finished, !state.deferred else { return false }
        return kidKeys.contains { state.isPending(SetupStop.kidID($0)) }
    }
}

/// Stable-id helpers. The stepped walk's stop model is gone, but its id scheme
/// survives — HomeView keys the kid-tile entry point on `SetupStop.kidID`, and
/// persisted `SetupTailState` on devices in the field contains these strings.
enum SetupStop {
    static func kidID(_ key: String) -> String { "kid:\(key)" }
    static func memberID(_ id: String) -> String { "member:\(id)" }   // legacy ids in stored state
    static let parentSelfID = "parent:self"                            // legacy id in stored state
}

// MARK: - The four expandable kid rows

/// The frame's four free-text rows, each mapped to ONE existing ChildProfile
/// list field (same keys the settings editors use — `KidLearnedField`):
/// into → `interests`, avoid → `dislikes`, hard → `challenges`,
/// shines → `strengths`. Text ↔ list: shown comma-joined, stored split on
/// commas (the backend fields are lists; the frame draws comma-separated prose).
enum SetupKidRow: String, CaseIterable, Identifiable {
    case into, avoid, hard, shines

    var id: String { rawValue }

    /// Row labels as the frame writes them. The Lily card's variants ("What
    /// Lily's would rather avoid", "Where Lily shines at") are drafting typos —
    /// the Benjamin card's grammatical forms are used for every kid.
    func title(for kidName: String) -> String {
        switch self {
        case .into:   return "What \(kidName) is into"
        case .avoid:  return "What \(kidName) would rather avoid"
        case .hard:   return "What's hard right now"
        case .shines: return "Where \(kidName) shines"
        }
    }

    var payloadKey: String {
        switch self {
        case .into:   return "interests"
        case .avoid:  return "dislikes"
        case .hard:   return "challenges"
        case .shines: return "strengths"
        }
    }

    func values(of kid: ChildProfileDTO) -> [String] {
        switch self {
        case .into:   return kid.interests ?? []
        case .avoid:  return kid.dislikes ?? []
        case .hard:   return kid.challenges ?? []
        case .shines: return kid.strengths ?? []
        }
    }
}

// MARK: - Model

@MainActor
final class SetupTailModel: ObservableObject {
    @Published private(set) var children: [String: ChildProfileDTO] = [:]
    @Published private(set) var kidKeys: [String] = []
    @Published private(set) var parent = ParentProfileDTO()
    @Published var loading = true
    @Published var loadError: String?
    /// One inline line under whichever control last failed to save.
    @Published var saveError: String?

    /// Comma-joined draft text per row, keyed by `rowID(kidKey:row:)`.
    @Published var drafts: [String: String] = [:]
    /// Rows currently open. Rows with saved content open on load (the frame
    /// draws populated rows expanded, empty rows as collapsed chevron rows).
    @Published var expanded: Set<String> = []

    let userID: String
    let baseURL: URL
    /// When set (`SetupStop.kidID`), the screen scrolls to this kid's card.
    let entryStopID: String?

    private var state: SetupTailState
    /// What the server last confirmed per row, to skip no-op saves.
    private var savedRowText: [String: String] = [:]

    init(userID: String, baseURL: URL, entryStopID: String?) {
        self.userID = userID
        self.baseURL = baseURL
        self.entryStopID = entryStopID
        self.state = SetupTailStore.load(userID: userID)
    }

    static func rowID(kidKey: String, row: SetupKidRow) -> String {
        "\(kidKey)|\(row.rawValue)"
    }

    /// First names for the coach line: "Benjamin and Lily" / "Benjamin, Lily and Max".
    var kidNamesSentence: String {
        let names = kidKeys.map { displayName(forKid: $0) }
        switch names.count {
        case 0:  return "your kids"
        case 1:  return names[0]
        default: return names.dropLast().joined(separator: ", ") + " and " + names[names.count - 1]
        }
    }

    func displayName(forKid key: String) -> String {
        let name = children[key]?.name?.trimmingCharacters(in: .whitespaces)
        let full = (name?.isEmpty == false ? name! : key)
        return full.split(separator: " ").first.map(String.init) ?? full
    }

    // MARK: Load

    func load() async {
        loading = true
        loadError = nil
        do {
            let profile = try await ProfileService.getProfile(baseURL: baseURL, userID: userID)
            apply(profile)
        } catch {
            if children.isEmpty {
                loadError = "Couldn't load your family. Check your connection and try again."
            }
        }
        loading = false
    }

    private func apply(_ profile: FamilyProfileDTO) {
        children = profile.children ?? [:]
        // Dictionary order is unspecified — sort by the stable key so the card
        // order is the same on every open.
        kidKeys = children.keys.sorted()
        if let parent = profile.parent { self.parent = parent }
        for key in kidKeys {
            guard let kid = children[key] else { continue }
            for row in SetupKidRow.allCases {
                let id = Self.rowID(kidKey: key, row: row)
                let joined = row.values(of: kid).joined(separator: ", ")
                savedRowText[id] = joined
                // Never clobber text mid-edit: only seed a draft that doesn't
                // exist yet.
                if drafts[id] == nil { drafts[id] = joined }
                if !joined.isEmpty { expanded.insert(id) }
            }
        }
    }

    // MARK: Writes — verified, partial, one control per payload

    /// Parent dropdowns (Household Type, Language at home). Optimistic UI;
    /// reverts and surfaces the failure if the server doesn't confirm.
    func saveParentField(_ key: String, keyPath: WritableKeyPath<ParentProfileDTO, String?>,
                         value: String) {
        let previous = parent[keyPath: keyPath]
        parent[keyPath: keyPath] = value.isEmpty ? nil : value
        saveError = nil
        Task {
            do {
                let fam = try await ProfileService.updateParent(
                    baseURL: baseURL, userID: userID, fields: [key: value]
                )
                if let p = fam.parent { self.parent = p }
                self.onMutationConfirmed?()
            } catch {
                self.parent[keyPath: keyPath] = previous
                self.saveError = "Couldn't save. Check your connection and try again."
            }
        }
    }

    /// Kid dropdowns (age / grade / school style) and the free-text rows.
    func saveKidField(kidKey: String, fields: [String: Any],
                      revert: (() -> Void)? = nil) {
        saveError = nil
        Task {
            do {
                let fam = try await ProfileService.updateKid(
                    baseURL: baseURL, userID: userID, name: kidKey, fields: fields
                )
                if let kids = fam.children { self.children = kids }
                self.markKidTouched(kidKey)
                self.onMutationConfirmed?()
            } catch {
                revert?()
                self.saveError = "Couldn't save. Check your connection and try again."
            }
        }
    }

    /// Commit one free-text row: comma-split the draft into the list field.
    /// No-ops when unchanged, so scrolling past rows doesn't spam the server.
    func commitRow(kidKey: String, row: SetupKidRow) {
        let id = Self.rowID(kidKey: kidKey, row: row)
        let text = drafts[id] ?? ""
        guard text != savedRowText[id] else { return }
        let items = text.split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        let before = savedRowText[id]
        savedRowText[id] = text
        saveKidField(kidKey: kidKey, fields: [row.payloadKey: items], revert: {
            self.savedRowText[id] = before
        })
    }

    func commitAllDirtyRows() {
        for key in kidKeys {
            for row in SetupKidRow.allCases {
                commitRow(kidKey: key, row: row)
            }
        }
    }

    // MARK: Local progress

    /// Set by the view; forwards to Home's `onNeedsRefresh`.
    var onMutationConfirmed: (() -> Void)?

    private func markKidTouched(_ kidKey: String) {
        let id = SetupStop.kidID(kidKey)
        if !state.completed.contains(id) { state.completed.append(id) }
        state.skipped.removeAll { $0 == id }
        if kidKeys.allSatisfy({ state.completed.contains(SetupStop.kidID($0)) }) {
            state.finished = true
        }
        SetupTailStore.save(state, userID: userID)
    }

    /// "Set up later" — leaves Home usable and never auto-asks again.
    func defer_() {
        state.deferred = true
        SetupTailStore.save(state, userID: userID)
    }
}

// MARK: - View

struct SetupTailView: View {
    /// Fired after every verified mutation, so Home re-fetches (CLAUDE.md:
    /// after a mutation, the source-of-truth view re-fetches).
    var onNeedsRefresh: () -> Void = {}

    @StateObject private var model: SetupTailModel
    @Environment(\.dismiss) private var dismiss
    @FocusState private var focusedRow: String?

    init(userID: String, baseURL: URL, entryStopID: String? = nil,
         onNeedsRefresh: @escaping () -> Void = {}) {
        self.onNeedsRefresh = onNeedsRefresh
        _model = StateObject(wrappedValue: SetupTailModel(
            userID: userID, baseURL: baseURL, entryStopID: entryStopID
        ))
    }

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                content
                    // Frame `69:1314`: px 20 (py 60 is the full-screen frame's
                    // status/home-bar allowance; as a sheet the top inset is
                    // the sheet chrome's own).
                    .padding(.horizontal, 20)
                    .padding(.top, 24)
                    .padding(.bottom, 32)
            }
            // Screen ground `primitives/neutral/paper` #FCFBF8 → bgCoachBanner.
            .background(Color.bgCoachBanner.ignoresSafeArea())
            .scrollDismissesKeyboard(.interactively)
            .trackScreen("setup_tail")
            .task {
                await model.load()
                if let entry = model.entryStopID {
                    // The kid-tile entry ("Set up {Name}") lands ON that card.
                    withAnimation { proxy.scrollTo(entry, anchor: .top) }
                }
            }
            .onAppear { model.onMutationConfirmed = onNeedsRefresh }
            .onDisappear {
                // A swipe-down dismissal mid-typing still persists the text —
                // never navigate away assuming an uncommitted draft saved.
                model.commitAllDirtyRows()
            }
            .onChange(of: focusedRow) { previous, _ in
                // Leaving a text row commits it (verified PATCH, no-op if clean).
                if let previous, let (kid, row) = parseRowID(previous) {
                    model.commitRow(kidKey: kid, row: row)
                }
            }
        }
    }

    private func parseRowID(_ id: String) -> (String, SetupKidRow)? {
        guard let sep = id.lastIndex(of: "|"),
              let row = SetupKidRow(rawValue: String(id[id.index(after: sep)...]))
        else { return nil }
        return (String(id[..<sep]), row)
    }

    // MARK: Layout

    @ViewBuilder
    private var content: some View {
        if model.loading && model.children.isEmpty {
            ProgressView()
                .tint(.inkMuted)
                .frame(maxWidth: .infinity)
                .padding(.top, 120)
        } else if let loadError = model.loadError {
            VStack(spacing: 16) {
                Text(loadError)
                    .font(.hearthBodyMD)
                    .foregroundColor(.statusError)
                    .multilineTextAlignment(.center)
                Button("Try again") { Task { await model.load() } }
                    .font(.hearthButtonLabel)
                    .foregroundColor(.accentOnCanvas)
                    .buttonStyle(.plain)
            }
            .frame(maxWidth: .infinity)
            .padding(.top, 120)
        } else {
            // Root stack gap 10 (`69:1314`).
            VStack(alignment: .leading, spacing: 10) {
                householdEyebrow
                householdCard

                if !model.kidKeys.isEmpty {
                    kidsSection
                }

                if let saveError = model.saveError {
                    Text(saveError)
                        .font(.hearthBodySM)
                        .foregroundColor(.statusError)
                }

                setUpLaterLink
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    /// "Coach:" JetBrains Mono 12/16 + Fraunces SemiBold 24/32, gap 3, ink
    /// `#151412` → inkPrimary (`69:1315`).
    private var householdEyebrow: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text("Coach:")
                .font(.hearthCaptionMono)
                .foregroundColor(.inkPrimary)
            Text("Two things about your household")
                .font(.hearthTitleSerif)
                .lineSpacing(32 - 24)
                .foregroundColor(.inkPrimary)
        }
    }

    /// Card `69:1318`: bg/canvas #F3F0EB → bgSober, r24, p20, gap 10.
    private var householdCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Helper copy Inter 13/18 #1E1E1E → inkDisplay, wrapped at the
            // frame's own 268pt text box.
            Text("Who's at home and what language you speak there. Both change how the coach talks to you.")
                .font(.hearthBodySM)
                .lineSpacing(18 - 13)
                .foregroundColor(.inkDisplay)
                .frame(maxWidth: 268, alignment: .leading)

            dropdownPill(
                placeholder: "Household Type",
                options: ProfileOptions.household,
                selection: model.parent.householdStructure ?? ""
            ) { model.saveParentField("household_structure",
                                      keyPath: \.householdStructure, value: $0) }

            dropdownPill(
                placeholder: "Language at home",
                options: ProfileOptions.language,
                selection: model.parent.primaryLanguage ?? ""
            ) { model.saveParentField("primary_language",
                                      keyPath: \.primaryLanguage, value: $0) }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(Color.bgSober)
        )
    }

    /// Container `69:1322`: pt 30 / pb 15, gap 10 — the second coach line and
    /// the first kid card share it; further kid cards are siblings (`69:1361`).
    private var kidsSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Coach:")
                .font(.hearthCaptionMono)
                .foregroundColor(.inkPrimary)
            Text("I can pick better options for \(model.kidNamesSentence) if I know what they are into. Takes about a minute.")
                .font(.hearthTitleSerif)
                .lineSpacing(32 - 24)
                .foregroundColor(.inkPrimary)
                .fixedSize(horizontal: false, vertical: true)

            ForEach(model.kidKeys, id: \.self) { key in
                kidCard(key)
                    .id(SetupStop.kidID(key))
            }
        }
        .padding(.top, 30)
        .padding(.bottom, 15)
    }

    /// One "Tell me about {kid}" card (`69:1325` / `69:1361`): bgSober, r24,
    /// p20, gap 10; dropdown row (age w112 + grade flex, gap 10), school-style
    /// full width, then the four rows.
    private func kidCard(_ key: String) -> some View {
        let kid = model.children[key] ?? ChildProfileDTO()
        let name = model.displayName(forKid: key)
        return VStack(alignment: .leading, spacing: 10) {
            Text("Tell me about \(name)")
                .font(.hearthTitleSerif)
                .lineSpacing(32 - 24)
                .foregroundColor(.inkPrimary)

            HStack(alignment: .top, spacing: 10) {
                dropdownPill(
                    placeholder: "Age",
                    options: [""] + (1...18).map(String.init),
                    selection: kid.age.map(ageLabel) ?? "",
                    // The 112pt age pill can't fit the full-width pill's 32pt
                    // insets beside a two-digit value + chevron; 20 is the
                    // deliberate deviation (noted in the handoff report).
                    horizontalInset: 20
                ) { picked in
                    guard let age = Double(picked) else { return }
                    model.saveKidField(kidKey: key, fields: ["age": age])
                }
                .frame(width: 112)

                dropdownPill(
                    placeholder: "Grade",
                    options: ProfileOptions.gradeBand,
                    selection: kid.gradeBand ?? ""
                ) { model.saveKidField(kidKey: key, fields: ["grade_band": $0]) }
            }

            dropdownPill(
                placeholder: "School style",
                options: ProfileOptions.schoolStyle,
                selection: kid.schoolStyle ?? ""
            ) { model.saveKidField(kidKey: key, fields: ["school_style": $0]) }

            VStack(alignment: .leading, spacing: 0) {
                ForEach(Array(SetupKidRow.allCases.enumerated()), id: \.element) { index, row in
                    kidRow(kidKey: key, kidName: name, row: row,
                           isLast: index == SetupKidRow.allCases.count - 1)
                }
            }
            .padding(.top, 14)
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(Color.bgSober)
        )
    }

    /// One expandable free-text row (`69:1333`…): pt 4 / pb 18, gap 6 chevron
    /// → label, hairline bottom border except the last; expanded adds the
    /// royal-bordered text box under the label.
    private func kidRow(kidKey: String, kidName: String, row: SetupKidRow,
                        isLast: Bool) -> some View {
        let id = SetupTailModel.rowID(kidKey: kidKey, row: row)
        let isOpen = model.expanded.contains(id)
        return VStack(alignment: .leading, spacing: 0) {
            HStack(alignment: .top, spacing: 6) {
                Button {
                    if isOpen {
                        model.commitRow(kidKey: kidKey, row: row)
                        model.expanded.remove(id)
                        if focusedRow == id { focusedRow = nil }
                    } else {
                        model.expanded.insert(id)
                        focusedRow = id
                    }
                } label: {
                    HStack(alignment: .center, spacing: 6) {
                        // Generic disclosure chevron — the frame's `arrow`
                        // component is a plain chevron, so per the fidelity
                        // playbook's SF-symbol carve-out it ships as SF.
                        Image(systemName: isOpen ? "chevron.down" : "chevron.right")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundColor(.inkDisplay)
                            .frame(width: 16)
                        // Row label Inter 13/18 — the Benjamin card draws
                        // #1E1E1E, the Lily card #2B2925 for the same role;
                        // normalized to inkDisplay (#1E1E1E) per the Benjamin
                        // (fully-drawn) card.
                        Text(row.title(for: kidName))
                            .font(.hearthBodySM)
                            .foregroundColor(.inkDisplay)
                        Spacer(minLength: 0)
                    }
                    .contentShape(Rectangle())
                }
                .buttonStyle(.plain)
                .accessibilityAddTraits(isOpen ? [.isSelected] : [])
            }
            .padding(.top, 4)

            if isOpen {
                // Royal-bordered free-text box (`69:1338`): paper fill, 0.5pt
                // #1B7498 border → accentOnCanvas, r12, p10, Inter 13/18 text
                // in the same royal ink.
                TextField(
                    "",
                    text: Binding(
                        get: { model.drafts[id] ?? "" },
                        set: { model.drafts[id] = $0 }
                    ),
                    axis: .vertical
                )
                .font(.hearthBodySM)
                .lineSpacing(18 - 13)
                .foregroundColor(.accentOnCanvas)
                .tint(.accentOnCanvas)
                .focused($focusedRow, equals: id)
                .lineLimit(1...6)
                .padding(10)
                .background(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .fill(Color.bgCoachBanner)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                        .stroke(Color.accentOnCanvas, lineWidth: 0.5)
                )
                .padding(.leading, 22)   // aligns with the label (16 chevron + 6 gap)
                .padding(.top, 6)
            }

            Spacer().frame(height: isOpen ? 18 : 12)

            if !isLast {
                Rectangle()
                    .fill(Color.borderInputPill)
                    .frame(height: 1)
            }
        }
    }

    /// "Set up later" (`69:1416`): Inter 13 underlined, royal → accentOnCanvas,
    /// centered.
    private var setUpLaterLink: some View {
        Button {
            model.commitAllDirtyRows()
            model.defer_()
            dismiss()
        } label: {
            Text("Set up later")
                .font(.hearthBodySM)
                .underline()
                .foregroundColor(.accentOnCanvas)
                .frame(maxWidth: .infinity)
        }
        .buttonStyle(.plain)
        .padding(.top, 10)
    }

    // MARK: Bits

    private func ageLabel(_ age: Double) -> String {
        age.truncatingRemainder(dividingBy: 1) == 0 ? String(Int(age)) : String(age)
    }

    /// The "large input" pill (`16:24`/`16:25` component): h56, paper #FCFBF8
    /// fill → bgCoachBanner, 1pt #C8C3B8 border → borderInputPill, r24,
    /// px 32 / py 12, value Inter 17/26 #6E6A62 → inkMuted (the frame draws
    /// chosen values and placeholders in the same muted ink), 24×12 chevron.
    private func dropdownPill(
        placeholder: String,
        options: [String],
        selection: String,
        horizontalInset: CGFloat = 32,
        onPick: @escaping (String) -> Void
    ) -> some View {
        Menu {
            Picker(placeholder, selection: Binding(
                get: { selection },
                set: { onPick($0) }
            )) {
                ForEach(options, id: \.self) { option in
                    Text(option.isEmpty ? "Not set" : option).tag(option)
                }
            }
        } label: {
            HStack(spacing: 6) {
                Text(selection.isEmpty ? placeholder : selection)
                    .font(.hearthBodyLG)
                    .foregroundColor(.inkMuted)
                    .lineLimit(1)
                Spacer(minLength: 0)
                Image(systemName: "chevron.down")
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(.inkMuted)
            }
            .padding(.horizontal, horizontalInset)
            .frame(height: 56)
            .frame(maxWidth: .infinity)
            .background(
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .fill(Color.bgCoachBanner)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 24, style: .continuous)
                    .stroke(Color.borderInputPill, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
        .accessibilityLabel(placeholder)
        .accessibilityValue(selection.isEmpty ? "Not set" : selection)
    }
}
