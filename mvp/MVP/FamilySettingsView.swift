import SwiftUI

/// Identifiable wrapper so `.sheet(item:)` can carry the kid's STABLE profile
/// key (the server's dictionary key), never a list index.
struct KidSheetTarget: Identifiable, Hashable {
    let key: String
    var id: String { key }
}

/// Settings tab root — replaces the old plain-List `SettingsView`. Built from
/// Figma `Onboarding - welcome` (node `754:6516`, round-2 addendum in
/// `docs/design/beta-v1-sprint2.md`): a scroll of 7 white cards, each a
/// title + description + label/value rows + a pencil edit affordance. That
/// frame is onboarding-welcome copy ("Your MVP Family Plan is almost ready",
/// "Looks good!"/"Set up later") — this build keeps the card visual language
/// but drops the onboarding-only header/footer for a settings-appropriate one.
///
/// **Real-data-only.** The frame shows MVP Email / Password rows with fake
/// values (`MVP_GregH@mvp.com`, `******`) — there is no email-auth backend
/// and no password concept in this app, so those rows are omitted entirely
/// rather than lying to a parent. Plan/Billing show the smoke-and-mirrors
/// plan picked at the onboarding paywall, IF one was ever picked (existing
/// installs that never saw the paywall show no rows there — still honest).
/// The coach card shows `guidance_style` (a real field) and omits Voice —
/// the parent-coach voice is intentionally not overridable
/// (`server.py`: "the ElevenLabs dashboard decides").
///
/// Every existing Settings row (Library, Report a problem, Legal, Connections,
/// What we've learned, Secure your account, Developer reveal, Log out,
/// Delete account) is migrated in below the cards — nothing is lost.
struct FamilySettingsView: View {
    @ObservedObject var configuration: ServerConfiguration
    let userID: String
    var onOpenPlan: () -> Void = {}

    @EnvironmentObject private var session: AppSession
    @AppStorage("parent_display_name") private var parentDisplayName = ""
    @AppStorage("picked_plan_name") private var pickedPlanName = ""
    @AppStorage("picked_plan_billing") private var pickedPlanBilling = ""
    @AppStorage("developer_mode") private var developerMode = false

    @State private var family = FamilyProfileDTO()
    @State private var members: [HouseholdMember] = []
    @State private var refreshToken = 0
    @State private var loadError: String?

    @State private var kidSettingsTarget: KidSheetTarget?
    @State private var editingMember: HouseholdMember?
    @State private var showAddKid = false
    @State private var pendingDeleteKey: String?

    // Legacy rows' state, ported from SettingsView/ProfileSettingsView.
    @State private var isLegacyAccount: Bool?
    @State private var showSecureAccount = false
    @State private var showingReport = false
    @State private var showingLogoutConfirm = false
    @State private var showingDelete = false
    @State private var deleteConfirmText = ""
    @State private var errorMessage: String?
    @State private var versionTapCount = 0

    private var showDeveloper: Bool {
        #if DEBUG
        return true
        #else
        return developerMode
        #endif
    }

    private var appVersion: String {
        let short = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "?"
        let build = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "?"
        return "Version \(short) (\(build))"
    }

    private var privacyURL: URL? { configuration.baseURL?.appendingPathComponent("dashboard/docs/privacy-policy") }
    private var termsURL: URL? { configuration.baseURL?.appendingPathComponent("dashboard/docs/terms") }

    /// `household.py: LOGISTICS_ROLES` minus the parent roles already shown
    /// on the Family structure / Your family cards — this is the "other
    /// adults" set (nanny/grandparent/neighbour/other), which the backend
    /// mirrors 1:1 into `caregivers`. Copied here (not fetched) because the
    /// roster payload doesn't carry a caregiver flag; if the backend's role
    /// set ever changes, this must change with it — see the Step-6c test
    /// that pins it.
    private static let circleRoles: Set<String> = ["nanny", "grandparent", "neighbour", "other"]
    private static let parentRoles: Set<String> = ["me", "spouse", "co_parent"]

    private var parentMembers: [HouseholdMember] {
        members.filter { Self.parentRoles.contains($0.role ?? "") }
    }
    private var circleMembers: [HouseholdMember] {
        members.filter { Self.circleRoles.contains($0.role ?? "") }
    }
    private var kidKeys: [String] { (family.children ?? [:]).keys.sorted() }

    var body: some View {
        ScrollView {
            VStack(spacing: .hearth400) {
                header

                yourInformationCard
                familyStructureCard
                yourFamilyCard
                yourCircleCard
                careGiversCard
                languageCard
                coachSettingsCard

                legacyRowsSection
            }
            .padding(.horizontal, .hearth700)
            .padding(.top, .hearth600)
            .padding(.bottom, .hearth800)
        }
        .background(Color.bgSober.ignoresSafeArea())
        .navigationBarTitleDisplayMode(.inline)
        .toolbar { ToolbarItem(placement: .principal) { Text("Settings").font(.hearthTitleMD) } }
        .task(id: refreshToken) { await load() }
        .task {
            isLegacyAccount = !userID.isEmpty && AuthService.shared.credential(for: userID) == nil
        }
        .sheet(item: $kidSettingsTarget, onDismiss: { refreshToken &+= 1 }) { target in
            KidSettingsSheet(
                baseURL: configuration.baseURL, userID: userID, kidKey: target.key,
                kid: family.children?[target.key] ?? ChildProfileDTO()
            ) { apply($0) }
        }
        .sheet(item: $editingMember, onDismiss: { refreshToken &+= 1 }) { member in
            if let baseURL = configuration.baseURL {
                MemberProfileSheet(userID: userID, baseURL: baseURL, memberId: member.id)
            }
        }
        .sheet(isPresented: $showAddKid, onDismiss: { refreshToken &+= 1 }) {
            AddKidSheet(baseURL: configuration.baseURL, userID: userID) { apply($0) }
        }
        .sheet(isPresented: $showingReport) {
            if let url = configuration.baseURL { ReportProblemView(baseURL: url) }
        }
        .sheet(isPresented: $showingDelete) { deleteSheet }
        .sheet(isPresented: $showSecureAccount) {
            SignInView { _ in
                showSecureAccount = false
                isLegacyAccount = AuthService.shared.credential(for: userID) == nil
            }
        }
        .confirmationDialog(
            pendingDeleteKey.map { "Delete \(family.children?[$0]?.name ?? $0)'s profile?" } ?? "",
            isPresented: Binding(get: { pendingDeleteKey != nil }, set: { if !$0 { pendingDeleteKey = nil } }),
            titleVisibility: .visible
        ) {
            Button("Delete profile", role: .destructive) {
                if let key = pendingDeleteKey { deleteKid(key) }
            }
            Button("Cancel", role: .cancel) { pendingDeleteKey = nil }
        } message: {
            Text("This permanently removes this child and everything saved about them. This can't be undone.")
        }
        .confirmationDialog("Log out of MVP?", isPresented: $showingLogoutConfirm, titleVisibility: .visible) {
            Button("Log out", role: .destructive) {
                Task { await session.signOut(userID: userID, baseURL: configuration.baseURL) }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("You'll need to sign in again to get back to your family's plan.")
        }
        .alert("Something went wrong",
               isPresented: Binding(get: { errorMessage != nil }, set: { if !$0 { errorMessage = nil } })) {
            Button("OK") { errorMessage = nil }
        } message: {
            Text(errorMessage ?? "")
        }
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: .hearth500) {
            Image(systemName: "gearshape")
                .font(.system(size: 32, weight: .regular))
                .foregroundColor(.inkSecondary)
            Text("Your MVP Family Plan")
                .font(.hearthDisplaySM)
                .foregroundColor(.inkDisplay)
                .multilineTextAlignment(.center)
        }
        .padding(.bottom, .hearth300)
    }

    // MARK: - Card 1: Your MVP information

    @ViewBuilder
    private var yourInformationCard: some View {
        settingsCard(title: "Your MVP information",
                     subtitle: "Your account, at a glance.",
                     onEdit: nil) {
            row("Username", parentDisplayName.isEmpty ? "Not set" : parentDisplayName)
            // No Email/Password rows — don't exist. Plan/Billing only render
            // when the smoke-and-mirrors paywall pick was actually persisted.
            if !pickedPlanName.isEmpty {
                row("Plan", pickedPlanName)
            }
            if !pickedPlanBilling.isEmpty {
                row("Billing", pickedPlanBilling)
            }
        }
    }

    // MARK: - Card 2: Family structure

    @ViewBuilder
    private var familyStructureCard: some View {
        settingsCard(
            title: "Family structure",
            subtitle: "Tell us about the parenting setup.",
            onEdit: { editingMember = nil; presentParentEditor() }
        ) {
            if let structure = family.parent?.householdStructure, !structure.isEmpty {
                row("Household", structure.capitalized)
            }
            if let adults = family.parent?.adultsInHousehold {
                row("Adults at home", String(adults))
            }
            ForEach(parentMembers) { member in
                Button { editingMember = member } label: {
                    row(member.roleLabel ?? member.role?.capitalized ?? "Parent", member.displayName)
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: - Card 3: Your family

    @ViewBuilder
    private var yourFamilyCard: some View {
        settingsCard(title: "Your family",
                     subtitle: "Everyone in your MVP plan.",
                     onEdit: nil) {
            Button { presentParentEditor() } label: {
                row("You", parentDisplayName.isEmpty ? "Add your name" : parentDisplayName)
            }
            .buttonStyle(.plain)

            ForEach(kidKeys, id: \.self) { key in
                Button { kidSettingsTarget = KidSheetTarget(key: key) } label: {
                    row("Child", family.children?[key]?.name ?? key)
                }
                .buttonStyle(.plain)
                .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                    Button(role: .destructive) { pendingDeleteKey = key } label: {
                        Label("Delete", systemImage: "trash")
                    }
                }
            }

            Button { showAddKid = true } label: {
                Text("+ Add a kid")
                    .font(.hearthBodyMD.weight(.semibold))
                    .foregroundColor(.accentDefault)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.top, .hearth300)
            }
            .buttonStyle(.plain)
        }
    }

    // MARK: - Card 4: Your circle

    @ViewBuilder
    private var yourCircleCard: some View {
        if !circleMembers.isEmpty {
            settingsCard(title: "Your circle",
                         subtitle: "Your MVP Circle includes anyone that you rely on for help.",
                         onEdit: nil) {
                ForEach(circleMembers) { member in
                    Button { editingMember = member } label: {
                        row(member.displayName, member.mvpUsername ?? member.roleLabel ?? "")
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    // MARK: - Card 5: Care givers

    @ViewBuilder
    private var careGiversCard: some View {
        if !circleMembers.isEmpty {
            settingsCard(title: "Care givers",
                         subtitle: "The people who help keep things running.",
                         onEdit: nil) {
                ForEach(circleMembers) { member in
                    Button { editingMember = member } label: {
                        row(member.displayName, member.mvpUsername ?? member.roleLabel ?? "")
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    // MARK: - Card 6: Language at home

    @ViewBuilder
    private var languageCard: some View {
        settingsCard(title: "Language at home",
                     subtitle: "Do you speak one or several languages at home?",
                     onEdit: { presentParentEditor() }) {
            row("Primary language", family.parent?.primaryLanguage.flatMap { $0.isEmpty ? nil : $0 } ?? "Not set")
            if let secondary = family.parent?.secondaryLanguage, !secondary.isEmpty {
                row("Secondary language", secondary)
            }
        }
    }

    // MARK: - Card 7: MVP coach settings

    @ViewBuilder
    private var coachSettingsCard: some View {
        settingsCard(title: "MVP coach settings",
                     subtitle: "Set up how you want the coach to respond.",
                     onEdit: { presentParentEditor() }) {
            // No Voice row — the parent-coach voice is not overridable
            // per-user (see the type doc comment).
            row("Guidance style",
                family.parent?.guidanceStyle.flatMap { $0.isEmpty ? nil : $0 } ?? "Not set")
        }
    }

    // MARK: - Card scaffold

    @ViewBuilder
    private func settingsCard<Content: View>(
        title: String, subtitle: String, onEdit: (() -> Void)?,
        @ViewBuilder rows: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.hearthBodyMD.weight(.bold))
                        .foregroundColor(.inkDisplay)
                    Text(subtitle)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkPrimary)
                }
                Spacer(minLength: .hearth400)
                if let onEdit {
                    Button(action: onEdit) {
                        Image(systemName: "pencil")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.accentDefault)
                    }
                }
            }
            VStack(alignment: .leading, spacing: .hearth300) {
                rows()
            }
        }
        .padding(.hearth800)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusSection, style: .continuous))
    }

    private func row(_ label: String, _ value: String) -> some View {
        HStack(alignment: .top) {
            Text(label)
                .font(.hearthBodySM)
                .foregroundColor(.inkSecondary)
            Spacer(minLength: .hearth400)
            Text(value)
                .font(.hearthBodySM)
                .foregroundColor(.inkSecondary)
                .multilineTextAlignment(.trailing)
        }
    }

    /// The card grid has no dedicated "You" push destination the way
    /// `ProfileSettingsView` did — three cards (Family structure, Language,
    /// Coach settings) all edit the SAME `ParentProfileDTO` via the SAME
    /// editor, so route through one NavigationLink-free presenter.
    @State private var showingParentEditor = false
    private func presentParentEditor() { showingParentEditor = true }

    // MARK: - Legacy rows (migrated verbatim from SettingsView / ProfileSettingsView)

    @ViewBuilder
    private var legacyRowsSection: some View {
        VStack(spacing: .hearth300) {
            if isLegacyAccount == true {
                Button { showSecureAccount = true } label: {
                    legacyRow(icon: "lock.shield.fill", title: "Secure your account",
                              subtitle: "Sign in with Apple or Google so you keep access on every device.")
                }
            }

            NavigationLink {
                LearnedProfileView(baseURL: configuration.baseURL, userID: userID, family: family) { apply($0) }
            } label: {
                legacyRow(icon: "sparkles", title: "What we've learned",
                          subtitle: "Review + correct what your coach has gathered")
            }

            NavigationLink {
                IntegrationsSettingsView(configuration: configuration, userID: userID)
            } label: {
                legacyRow(icon: "link", title: "Connections", subtitle: nil)
            }

            NavigationLink {
                LibraryView().navigationBarTitleDisplayMode(.inline)
            } label: {
                legacyRow(icon: "books.vertical", title: "Library", subtitle: nil)
            }

            Button { showingReport = true } label: {
                legacyRow(icon: "exclamationmark.bubble", title: "Report a problem", subtitle: nil)
            }

            if let privacyURL {
                Link(destination: privacyURL) {
                    legacyRow(icon: "hand.raised", title: "Privacy Policy", subtitle: nil)
                }
            }
            if let termsURL {
                Link(destination: termsURL) {
                    legacyRow(icon: "doc.text", title: "Terms of Service", subtitle: nil)
                }
            }

            if showDeveloper {
                NavigationLink {
                    ServerSettingsView(configuration: configuration)
                } label: {
                    legacyRow(icon: "wrench.and.screwdriver", title: "Server & diagnostics", subtitle: nil)
                }
            }

            Button {
                versionTapCount += 1
                if versionTapCount >= 7 { developerMode = true }
            } label: {
                Text(appVersion)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.hearth500)
            }

            Button(role: .destructive) { showingLogoutConfirm = true } label: {
                Text("Log out").frame(maxWidth: .infinity).padding(.hearth500)
            }
            .background(Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))

            Button(role: .destructive) {
                deleteConfirmText = ""
                showingDelete = true
            } label: {
                Text("Delete account").frame(maxWidth: .infinity).padding(.hearth500)
            }
            .background(Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
            .disabled(session.isWorking)
        }
        .navigationDestination(isPresented: $showingParentEditor) {
            ParentProfileEditor(
                baseURL: configuration.baseURL, userID: userID,
                parent: family.parent ?? ParentProfileDTO()
            ) { apply($0) }
        }
    }

    private func legacyRow(icon: String, title: String, subtitle: String?) -> some View {
        HStack(spacing: .hearth400) {
            Image(systemName: icon)
                .foregroundColor(.accentDefault)
                .frame(width: 24)
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.hearthBodyMD.weight(.semibold))
                    .foregroundColor(.inkPrimary)
                if let subtitle {
                    Text(subtitle).font(.hearthBodySM).foregroundColor(.inkMuted)
                }
            }
            Spacer(minLength: 0)
        }
        .padding(.hearth500)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
    }

    // MARK: - Delete confirmation (verbatim from SettingsView)

    private var deleteSheet: some View {
        NavigationStack {
            Form {
                Section {
                    Text("This permanently deletes your account and your family's data — your plan, chat history, kid companions, and profile. It can't be undone.")
                    Text("One anonymous entry (that a deletion happened, and when) is kept for our records. It contains none of your family's content.")
                        .font(.hearthBodySM)
                        .foregroundColor(.inkMuted)
                }
                Section("Type DELETE to confirm") {
                    TextField("DELETE", text: $deleteConfirmText)
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.characters)
                }
                Section {
                    Button(role: .destructive) {
                        Task { await performDelete() }
                    } label: {
                        if session.isWorking {
                            ProgressView().frame(maxWidth: .infinity)
                        } else {
                            Text("Delete my account").frame(maxWidth: .infinity)
                        }
                    }
                    .disabled(!isDeleteConfirmed || session.isWorking)
                }
            }
            .scrollContentBackground(.hidden)
            .background(Color.bgCanvas.ignoresSafeArea())
            .navigationTitle("Delete account")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { showingDelete = false }.disabled(session.isWorking)
                }
            }
        }
    }

    private var isDeleteConfirmed: Bool {
        deleteConfirmText.trimmingCharacters(in: .whitespaces).uppercased() == "DELETE"
    }

    private func performDelete() async {
        guard let baseURL = configuration.baseURL else {
            errorMessage = "No server is configured, so we can't reach your account to delete it."
            return
        }
        do {
            try await session.deleteAccount(userID: userID, baseURL: baseURL)
        } catch {
            showingDelete = false
            errorMessage = (error as? LocalizedError)?.errorDescription
                ?? "We couldn't delete your account. Please check your connection and try again."
        }
    }

    // MARK: - Data

    private func apply(_ fam: FamilyProfileDTO) {
        family = fam
    }

    private func deleteKid(_ key: String) {
        guard let baseURL = configuration.baseURL else { return }
        pendingDeleteKey = nil
        Task {
            do {
                let fam = try await ProfileService.deleteKid(baseURL: baseURL, userID: userID, name: key)
                apply(fam)
            } catch {
                errorMessage = "Couldn't delete that profile. Check your connection and try again."
            }
        }
    }

    private func load() async {
        guard let baseURL = configuration.baseURL, !userID.isEmpty else { return }
        do {
            async let familyResult = ProfileService.getProfile(baseURL: baseURL, userID: userID)
            async let membersResult = CircleService.householdMembers(userID: userID, baseURL: baseURL)
            let (fam, mem) = try await (familyResult, membersResult)
            family = fam
            members = mem
        } catch {
            loadError = "Couldn't load your family settings."
        }
    }
}
