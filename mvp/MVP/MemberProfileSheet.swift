import SwiftUI

// Member profile sheet — beta-v1 sprint-1 `parent 001` / `parent 002` /
// `co-parent 001` / `circle member`. One sheet, four frames, a role-driven
// field set, built against MEASURED values.
//
// Same composition as the kid frames (deliberately — they are one component
// family, not five near-duplicate editors): white frame, 60pt top inset, an
// "Primary parent" / "Circle member setting" header over a 1px rule, the wide
// PHOTO BAND with its camera badge, then the cream ground (`#E9E4DC`, pad
// 24/30, gap 20) carrying an "Edit parent"/"Edit member" pill, the name in the
// display serif 56/60, a white r32 relation card, the "More about {name}"
// disclosure card, and Save / Cancel.
//
// Per-frame differences, all four built:
//   parent 001/002 — header "Primary parent"; relation card = MVP name /
//                    Family role / Email; five disclosure rows
//   co-parent 001  — the above PLUS a `Co-Parent goals` row
//   circle member  — header "Circle member setting"; NO family-role field;
//                    the relation card gains the Personality chip group
//
// The rows come from the server's `attribute_fields`, which the backend derives
// from the role (`co_parent_goals` exists ONLY on co-parents, `personality`
// ONLY on circle-member roles, and a write of either on the wrong role is a
// 400). Re-deriving that matrix here would let the two drift, so the sheet
// renders what it is handed. Personality is a `kind: "choice"` attribute and
// its `choices` come from the server too — never a client list.
//
// Greg's frames label the role field "Family roll" — that's a typo; we render
// "Family role".
//
// PERSISTENCE (rules that have already cost this project a user's data):
//   • Every write is verified: the sheet waits for a 2xx, renders what the
//     server actually returned, and surfaces failures. Nothing dismisses on an
//     assumption, and Save stays available after a failure so the intent is
//     never silently dropped.
//   • The base URL arrives from the caller, itself sourced from
//     `ServerConfiguration` — never a hardcoded localhost fallback.
//   • Keyed by `memberId` (a stable uuid), never by the editable display name.
//   • `attributes` is patched as a WHOLE decoded object for the keys being
//     changed, never by splicing strings into the JSON bag.

struct MemberProfileSheet: View {
    let userID: String
    let baseURL: URL
    /// The stable roster id. The ONLY key — a rename must not move the target.
    let memberId: String

    @StateObject private var model: MemberProfileModel
    @State private var editingAttribute: MemberAttributeField?
    /// Which disclosure rows are open. The frames draw them all closed; opening
    /// one shows what's stored (or the invitation to add the first item).
    @State private var openRows: Set<String> = []
    /// The relation card's fields become editable in place. The frames show a
    /// read-only card plus an "Edit {role}" pill, and this is that pill's state.
    @State private var editingBasics = false
    @Environment(\.dismiss) private var dismiss

    init(userID: String, baseURL: URL, memberId: String, member: HouseholdMember? = nil) {
        self.userID = userID
        self.baseURL = baseURL
        self.memberId = memberId
        _model = StateObject(wrappedValue: MemberProfileModel(
            userID: userID, baseURL: baseURL, memberId: memberId, member: member
        ))
    }

    private var displayName: String {
        let name = model.draft.displayName.trimmingCharacters(in: .whitespacesAndNewlines)
        return name.isEmpty ? (model.member?.displayName ?? "This member") : name
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
            .navigationDestination(item: $editingAttribute) { field in
                MemberAttributeEditor(
                    field: field,
                    memberName: displayName,
                    items: model.attributeValues(field.key)
                ) { items in
                    // The list editor is its own durable write: it PATCHes only
                    // its own attribute key, verifies the 2xx, and reports back.
                    await model.saveAttribute(field.key, items: items)
                }
            }
        }
        .trackScreen("member_profile")
        // Source-of-truth re-fetch: on open, and again whenever a pushed editor
        // pops (it may have changed a list this sheet renders but doesn't own).
        .task(id: model.refreshToken) { await model.refresh() }
        .onChange(of: editingAttribute) { _, destination in
            if destination == nil { model.refreshToken += 1 }
        }
    }

    // MARK: - Header

    private var header: some View {
        HStack(spacing: .hearth300) {
            Text(model.roleHeading)
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

    /// The frames' 1px `#C8C3B8` rules — `borderInputPill` (#C9C5BE) is the
    /// nearest token, within one value per channel.
    private var rule: some View {
        Rectangle().fill(Color.borderInputPill).frame(height: 1)
    }

    // MARK: - Photo band
    //
    // The SAME component the kid frames use, pointed at the member route
    // (`POST /household/members/{id}/avatar`). Its `refresh` re-reads this
    // member, so what renders after an upload is what the server returned.

    private var photoBand: some View {
        EditableAvatarView(
            avatarUrl: model.member?.avatarUrl,
            target: .member(memberId),
            userID: userID,
            baseURL: baseURL,
            monogram: model.member?.resolvedInitials,
            personName: displayName
        ) {
            await model.refresh()
        }
    }

    // MARK: - Cream body

    private var creamBody: some View {
        VStack(alignment: .leading, spacing: .hearth600) {
            editPill
            Text(displayName)
                .font(.hearthDisplayXL)
                .tracking(-1.12)
                .foregroundColor(.inkDisplay)
            relationCard
            aboutCard
            if let error = model.error {
                Text(error)
                    .font(.hearthBodySM)
                    .foregroundColor(.statusError)
            }
            saveBar
        }
        .padding(.horizontal, .hearth800)
        .padding(.vertical, .hearth700)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.bgCanvas)
    }

    /// "Edit parent" / "Edit member", per the frame's own wording for the role.
    /// A real toggle: it turns the relation card's rows into fields and back.
    private var editPill: some View {
        Button {
            withAnimation(.hearthFast) { editingBasics.toggle() }
        } label: {
            HStack(spacing: .hearth300) {
                Image(systemName: editingBasics ? "checkmark" : "pencil")
                    .font(.system(size: 14, weight: .semibold))
                Text(editingBasics ? "Done editing" : model.editPillLabel)
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
        .accessibilityHint(editingBasics
                           ? "Stops editing. Save below to keep your changes."
                           : "Makes the details below editable")
    }

    // MARK: - Relation card

    private var relationCard: some View {
        card(spacing: .hearth800) {
            Image(systemName: "ellipsis")
                .font(.system(size: 15, weight: .semibold))
                .foregroundColor(.accentDefault)
                .frame(height: 4, alignment: .center)

            // "Mom" / "Step Mom " / "Nanny" — the free-text relation, in the
            // frames' 24/600 sans.
            Text(relationHeadline)
                .font(.hearthTitleLG)
                .foregroundColor(.inkDisplay)

            VStack(alignment: .leading, spacing: 9) {
                basicsRows
            }

            if model.showsPersonality {
                rule
                personalityGroup
            }
        }
    }

    private var relationHeadline: String {
        let relation = model.draft.relation.trimmingCharacters(in: .whitespacesAndNewlines)
        if !relation.isEmpty { return relation }
        return model.member?.roleLabel ?? MemberRole.label(for: model.draft.role)
    }

    @ViewBuilder
    private var basicsRows: some View {
        if editingBasics {
            editField("Name", text: $model.draft.displayName, prompt: "Their name")
            editField("Relation", text: $model.draft.relation, prompt: "e.g. Step Mom")
            editField("MVP name", text: $model.draft.mvpUsername, prompt: "mvpNanny",
                      lowercase: true)
            // "Family roll" in the frames is Greg's typo. Circle members don't
            // get this field at all (per the `circle member` frame).
            if model.showsFamilyRole { familyRoleField }
            editField("Email", text: $model.draft.email, prompt: "them@example.com",
                      lowercase: true, email: true)
        } else {
            factRow("MVP name", model.draft.mvpUsername)
            if model.showsFamilyRole {
                factRow("Family role", MemberRole.label(for: model.draft.role))
            }
            factRow("Email", model.draft.email)
        }
    }

    private func factRow(_ label: String, _ value: String) -> some View {
        HStack(alignment: .top, spacing: .hearth800) {
            Text(label)
                .font(.hearthSectionHeader)
                .foregroundColor(.inkDisplay)
            Text(value.isEmpty ? "Not set" : value)
                .font(.hearthTitleMD)
                .foregroundColor(value.isEmpty ? .inkMuted : .inkDisplay)
                .multilineTextAlignment(.leading)
        }
    }

    @ViewBuilder
    private func editField(_ label: String, text: Binding<String>, prompt: String,
                           lowercase: Bool = false, email: Bool = false) -> some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text(label)
                .font(.hearthSectionHeader)
                .foregroundColor(.inkDisplay)
            TextField("", text: text,
                      prompt: Text(prompt).foregroundColor(.inkPlaceholder))
                .font(.hearthTitleMD)
                .foregroundColor(.inkDisplay)
                .textInputAutocapitalization(lowercase ? .never : .words)
                .autocorrectionDisabled(lowercase)
                .keyboardType(email ? .emailAddress : .default)
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth400)
                .background(fieldGround)
        }
    }

    private var familyRoleField: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text("Family role")
                .font(.hearthSectionHeader)
                .foregroundColor(.inkDisplay)
            Menu {
                Picker("Family role", selection: $model.draft.role) {
                    ForEach(MemberRole.selectable, id: \.key) { option in
                        Text(option.label).tag(option.key)
                    }
                }
            } label: {
                HStack {
                    Text(MemberRole.label(for: model.draft.role))
                        .font(.hearthTitleMD)
                        .foregroundColor(.inkDisplay)
                    Spacer()
                    Image(systemName: "chevron.down")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundColor(.accentOnCanvas)
                }
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth400)
                .background(fieldGround)
            }
        }
    }

    // MARK: - Personality (circle members only)

    /// Single-select, persisted as the role-scoped `personality` attribute
    /// (`kind: "choice"` on the server, stored as a single-element list) with
    /// the SERVER's `choices`. Saved on tap rather than with the basics, because
    /// attributes PATCH through their own key — see
    /// `MemberProfileModel.savePersonality`.
    private var personalityGroup: some View {
        VStack(alignment: .leading, spacing: .hearth600) {
            Text("Personality")
                .font(.hearthBodySMBold)
                .foregroundColor(.inkDisplay)

            FlowLayout(spacing: .hearth300) {
                ForEach(model.personalityOptions, id: \.self) { option in
                    personalityChip(option)
                }
            }
        }
        .padding(.top, .hearth600)
    }

    private func personalityChip(_ option: String) -> some View {
        let selected = model.draft.personality == option
        return Button {
            let next = selected ? "" : option
            model.draft.personality = next
            Task { await model.savePersonality(next) }
        } label: {
            Text(option)
                .font(.hearthBodySM)
                .foregroundColor(selected ? .inkOnPhotoLight : .accentOnCanvas)
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth400)
                .background(Capsule().fill(selected ? Color.accentDefault : Color.bgCoachBanner))
                .overlay(
                    Capsule().stroke(selected ? Color.clear : Color.accentDefault,
                                     lineWidth: 0.5)
                )
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(selected ? [.isSelected] : [])
    }

    // MARK: - More about {name}

    private var aboutCard: some View {
        card(spacing: .hearth300) {
            Text("More about \(displayName)")
                .font(.hearthSectionHeader)
                .foregroundColor(.inkDisplay)

            ForEach(model.listAttributeFields) { field in
                disclosureRow(field)
            }
            if model.listAttributeFields.isEmpty {
                Text("Nothing noted yet.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                    .padding(.vertical, .hearth400)
            }
        }
    }

    /// The frames draw these closed; opening one reveals the stored values in a
    /// teal-stroked r12 box (mirroring the kid frames' open state). The box
    /// pushes the list editor, so both the closed row and the open values are
    /// live controls.
    @ViewBuilder
    private func disclosureRow(_ field: MemberAttributeField) -> some View {
        let open = openRows.contains(field.key)
        let values = model.attributeValues(field.key)
        VStack(alignment: .leading, spacing: .hearth300) {
            Button {
                withAnimation(.hearthFast) {
                    if open { openRows.remove(field.key) } else { openRows.insert(field.key) }
                }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: open ? "chevron.down" : "chevron.right")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundColor(.inkDisplay)
                        .frame(width: 16, height: 16)
                    Text(field.label)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkDisplay)
                    Spacer(minLength: .hearth300)
                    if !values.isEmpty {
                        Text("\(values.count)")
                            .font(.hearthBodySM)
                            .foregroundColor(.inkMuted)
                    }
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .accessibilityLabel(field.label)
            .accessibilityHint(open ? "Collapses this list" : "Shows this list")

            if open {
                Button { editingAttribute = field } label: {
                    Text(values.isEmpty
                         ? "Nothing here yet — tap to add the first one."
                         : values.joined(separator: ", "))
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
                .accessibilityLabel("Edit \(field.label) for \(displayName)")
            }
        }
        .padding(.top, 4)
        .padding(.bottom, .hearth400)
        .overlay(alignment: .bottom) { rule }
    }

    // MARK: - Save / Cancel

    /// Save NEVER dismisses on hope: the sheet closes only once the server has
    /// confirmed. A failure keeps the sheet, the typed values, and the button.
    private var saveBar: some View {
        VStack(spacing: .hearth400) {
            Button {
                Task { if await model.saveBasics() { dismiss() } }
            } label: {
                Text(model.saving ? "Saving…" : "Save")
                    .font(.hearthSectionHeader)
                    .foregroundColor(.inkOnPhotoLight)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, .hearth400)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .fill(model.canSave ? Color.accentDefault : Color.bgDisabled)
                    )
            }
            .buttonStyle(.plain)
            .disabled(!model.canSave)

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

    // MARK: - Shared bits

    /// The frames' white r32 card, pad 30. r32 has no radius token;
    /// `hearthRadiusXl` (28) is the nearest step.
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

    private var fieldGround: some View {
        RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
            .fill(Color.bgCoachBanner)
            .overlay(
                RoundedRectangle(cornerRadius: .hearthRadiusTile, style: .continuous)
                    .stroke(Color.borderInputPill, lineWidth: 1)
            )
    }
}

// MARK: - Role vocabulary

/// Mirrors the backend's `MEMBER_ROLES` / `ROLE_LABELS` (app/household.py).
/// `child` is omitted on purpose — children are edited through /profile/kids/*
/// and a write of `role: "child"` here is a 400.
enum MemberRole {
    static let selectable: [(key: String, label: String)] = [
        ("me", "Me"),
        ("spouse", "Spouse"),
        ("co_parent", "Co-Parent"),
        ("nanny", "Nanny"),
        ("grandparent", "Grandparent"),
        ("neighbour", "Neighbour"),
        ("other", "Other")
    ]

    static func label(for key: String) -> String {
        selectable.first { $0.key == key }?.label ?? "Other"
    }

    /// The roles the design treats as "family" — they get the Family role
    /// field. A circle member (nanny / grandparent / neighbour / other) does
    /// not, per the `circle member` frame.
    static let familyRoles: Set<String> = ["me", "spouse", "co_parent"]
}

// MARK: - Model

@MainActor
final class MemberProfileModel: ObservableObject {

    struct Draft {
        var displayName = ""
        var relation = ""
        var mvpUsername = ""
        var email = ""
        var role = "other"
        var personality = ""
    }

    /// The server's attribute key for personality. It is a real role-scoped
    /// attribute (`ATTRIBUTE_CHOICES` in app/household.py) with `kind: "choice"`,
    /// stored as a single-element list — NOT a marker line inside `notes`, which
    /// would collide with the parent's own note text and be unqueryable.
    static let personalityKey = "personality"

    @Published var member: HouseholdMember?
    @Published var draft = Draft()
    @Published var saving = false
    @Published var error: String?
    /// Bumped to force the `.task(id:)` re-fetch.
    @Published var refreshToken = 0

    private let userID: String
    private let baseURL: URL
    private let memberId: String

    init(userID: String, baseURL: URL, memberId: String, member: HouseholdMember?) {
        self.userID = userID
        self.baseURL = baseURL
        self.memberId = memberId
        if let member { apply(member) }
    }

    // MARK: Derived

    var roleHeading: String {
        switch member?.role ?? draft.role {
        case "me", "spouse":   return "Primary parent"
        case "co_parent":      return "Primary parent"
        default:               return "Circle member setting"
        }
    }

    /// The frames' pill wording: "Edit parent" on the three family frames,
    /// "Edit member" on `circle member`.
    var editPillLabel: String {
        showsFamilyRole ? "Edit parent" : "Edit member"
    }

    var showsFamilyRole: Bool { MemberRole.familyRoles.contains(draft.role) }
    /// The server's `attribute_fields` decides whether personality applies to
    /// this role (`ATTRIBUTE_CHOICES` / `ROLE_ATTRIBUTES` in app/household.py).
    /// Deriving it here rather than re-listing the roles client-side means one
    /// place changes when Greg adds a role.
    var personalityField: MemberAttributeField? {
        attributeFields.first { $0.key == Self.personalityKey && $0.isChoice }
    }

    var showsPersonality: Bool { personalityField != nil }

    /// Choices come from the server too — never a hardcoded client list.
    var personalityOptions: [String] { personalityField?.choices ?? [] }

    /// Straight from the server, so `Co-Parent goals` appearing only on
    /// co-parents is the backend's decision, not a duplicated client rule.
    var attributeFields: [MemberAttributeField] { member?.attributeFields ?? [] }

    /// The drill-in list rows only. Choice fields (personality) render as their
    /// own chip row, so excluding them here stops the field appearing twice.
    var listAttributeFields: [MemberAttributeField] {
        attributeFields.filter { !$0.isChoice }
    }

    func attributeValues(_ key: String) -> [String] {
        member?.attributes?[key] ?? []
    }

    var canSave: Bool {
        !saving && !draft.displayName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    // MARK: Reads

    /// Re-reads this member. Returns whether the read succeeded, so callers that
    /// just mutated (the photo band) can tell a confirmed refresh from a blip.
    @discardableResult
    func refresh() async -> Bool {
        guard !userID.isEmpty else { return false }
        do {
            let fresh = try await CircleService.member(id: memberId, userID: userID,
                                                       baseURL: baseURL)
            apply(fresh)
            return true
        } catch {
            // A read failure leaves whatever the list handed us — the sheet is
            // still usable, and a save would surface its own error.
            if member == nil {
                self.error = "Couldn't load this profile. Close and try again."
            }
            return false
        }
    }

    private func apply(_ fresh: HouseholdMember) {
        member = fresh
        draft = Draft(
            displayName: fresh.displayName,
            relation: fresh.relation ?? "",
            mvpUsername: fresh.mvpUsername ?? "",
            email: fresh.email ?? "",
            role: fresh.role ?? "other",
            personality: fresh.attributes?[Self.personalityKey]?.first ?? ""
        )
    }

    // MARK: Writes

    /// PATCHes ONLY the basics keys. `attributes` is deliberately absent from
    /// the payload, so saving a name can never wipe a list the coach learned.
    /// Returns true only on a confirmed 2xx — the caller dismisses on that and
    /// nothing else.
    func saveBasics() async -> Bool {
        guard canSave else { return false }
        saving = true
        error = nil
        defer { saving = false }

        var fields: [String: Any] = [
            "display_name": draft.displayName.trimmingCharacters(in: .whitespacesAndNewlines),
            "relation": trimmedOrNull(draft.relation),
            "mvp_username": trimmedOrNull(draft.mvpUsername),
            "email": trimmedOrNull(draft.email),
        ]
        // Only family roles expose the picker, so only they can send a role.
        if showsFamilyRole { fields["role"] = draft.role }

        do {
            let updated = try await CircleService.updateMember(
                id: memberId, fields: fields, userID: userID, baseURL: baseURL
            )
            apply(updated)
            Analytics.capture("member_profile_saved", [:])
            return true
        } catch let serviceError as CircleService.CircleServiceError
                    where serviceError.isConflict {
            self.error = "That MVP name is already used in your household. Pick another."
            return false
        } catch {
            self.error = "Couldn't save that. Check your connection and try again."
            return false
        }
    }

    /// One attribute list, patched as a WHOLE decoded object under its own key.
    /// Never string-spliced into `attributes_json` — the server role-scopes the
    /// bag and rejects a key that doesn't belong to the role.
    /// Personality is one choice, stored as a single-element list (empty list
    /// clears it). Its own method so the tap handler reads as one intent.
    @discardableResult
    func savePersonality(_ value: String) async -> Bool {
        await saveAttribute(Self.personalityKey, items: value.isEmpty ? [] : [value])
    }

    @discardableResult
    func saveAttribute(_ key: String, items: [String]) async -> Bool {
        error = nil
        do {
            let updated = try await CircleService.updateMember(
                id: memberId, fields: ["attributes": [key: items]],
                userID: userID, baseURL: baseURL
            )
            apply(updated)
            return true
        } catch {
            self.error = "Couldn't save that list. Check your connection and try again."
            return false
        }
    }

    private func trimmedOrNull(_ value: String) -> Any {
        let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
        // An explicit null CLEARS the field server-side; "" would be stored.
        return trimmed.isEmpty ? NSNull() : trimmed
    }

}

// MARK: - One attribute list

/// Edits a single "More about {name}" list. Same shape as
/// `KidLearnedListEditor`: one screen, one key, verified save, and it only
/// leaves once the server has confirmed.
struct MemberAttributeEditor: View {
    let field: MemberAttributeField
    let memberName: String
    /// The save closure returns whether the server confirmed — the editor pops
    /// on true and stays put (with its edits intact) on false.
    var onSave: ([String]) async -> Bool

    @State private var items: [String]
    @State private var saving = false
    @State private var error: String?
    @Environment(\.dismiss) private var dismiss

    init(field: MemberAttributeField, memberName: String, items: [String],
         onSave: @escaping ([String]) async -> Bool) {
        self.field = field
        self.memberName = memberName
        _items = State(initialValue: items)
        self.onSave = onSave
    }

    var body: some View {
        Form {
            Section {
                ChipEditor(title: field.label, items: $items)
            } footer: {
                Text("What you and your coach have noticed about \(memberName). Edit or remove anything that's off.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
            }
            if let error {
                Text(error).font(.hearthBodySM).foregroundColor(.statusError)
            }
        }
        .scrollContentBackground(.hidden)
        .background(Color.bgCanvas.ignoresSafeArea())
        .navigationTitle(field.label)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .confirmationAction) {
                Button(saving ? "Saving…" : "Save") { Task { await save() } }
                    .disabled(saving)
            }
        }
        .trackScreen("member_attribute_\(field.key)")
    }

    private func save() async {
        saving = true
        error = nil
        defer { saving = false }
        if await onSave(items) {
            dismiss()
        } else {
            error = "Couldn't save. Check your connection and try again."
        }
    }
}
