import SwiftUI

/// Settings → Profile hub. Loads the full family profile via GET /profile and
/// drills into editors: the parent's Basics ("You"), each kid's Basics, an
/// "Add a kid" sheet, and the family-wide "What we've learned" screen (the
/// fields the coaching/onboarding agents infer over time). Lives inside the
/// Settings sheet's NavigationStack, so the rows push.
struct ProfileSettingsView: View {
    let configuration: ServerConfiguration
    let userID: String

    @State private var family = FamilyProfileDTO()
    @State private var kidKeys: [String] = []
    @State private var showAddKid = false
    @State private var pendingDeleteKey: String?
    @State private var errorMessage: String?
    // Legacy users (issued a token before sign-in existed) have no v1 credential.
    // We nudge them to claim their account with Apple/Google so they don't lose
    // access when legacy tokens are retired. Nil = unknown/loading.
    @State private var isLegacyAccount: Bool?
    @State private var showSecureAccount = false

    var body: some View {
        List {
            if userID.isEmpty {
                Section {
                    Text("Complete onboarding to edit your profile.")
                        .foregroundColor(.inkMuted)
                }
            } else {
                if isLegacyAccount == true {
                    Section {
                        Button { showSecureAccount = true } label: {
                            HStack(spacing: .hearth400) {
                                Image(systemName: "lock.shield.fill")
                                    .foregroundColor(.accentDefault)
                                    .frame(width: 24)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text("Secure your account")
                                        .font(.hearthBodyMD.weight(.semibold))
                                        .foregroundColor(.accentDefault)
                                    Text("Sign in with Apple or Google so you keep access on every device.")
                                        .font(.hearthBodySM)
                                        .foregroundColor(.inkMuted)
                                }
                            }
                        }
                    }
                }

                Section("You") {
                    NavigationLink {
                        ParentProfileEditor(
                            baseURL: configuration.baseURL, userID: userID,
                            parent: family.parent ?? ParentProfileDTO()
                        ) { apply($0) }
                    } label: { parentRow }
                }

                Section("Kids") {
                    ForEach(kidKeys, id: \.self) { key in
                        NavigationLink {
                            KidProfileEditor(
                                baseURL: configuration.baseURL, userID: userID,
                                kidKey: key, kid: family.children?[key] ?? ChildProfileDTO()
                            ) { apply($0) }
                        } label: { kidRow(key) }
                        .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                            Button(role: .destructive) {
                                pendingDeleteKey = key
                            } label: {
                                Label("Delete", systemImage: "trash")
                            }
                        }
                    }
                    Button { showAddKid = true } label: {
                        Label("Add a kid", systemImage: "plus.circle.fill")
                            .font(.hearthBodyMD.weight(.semibold))
                            .foregroundColor(.accentDefault)
                    }
                }

                Section {
                    NavigationLink {
                        LearnedProfileView(
                            baseURL: configuration.baseURL, userID: userID, family: family
                        ) { apply($0) }
                    } label: { learnedRow }
                } footer: {
                    Text("Your ZIP is used to find camps and activities near you on the Plan tab.")
                        .font(.hearthBodySM)
                        .foregroundColor(.inkMuted)
                }

                if let errorMessage {
                    Section { Text(errorMessage).font(.hearthBodySM).foregroundColor(.statusError) }
                }
            }
        }
        .scrollContentBackground(.hidden)
        .background(Color.bgCanvas.ignoresSafeArea())
        .sheet(isPresented: $showAddKid) {
            AddKidSheet(baseURL: configuration.baseURL, userID: userID) { apply($0) }
        }
        .sheet(isPresented: $showSecureAccount) {
            // SignInView auto-forwards the legacy user_id + token, so a
            // successful sign-in CLAIMS this existing account (same user_id,
            // data intact) and binds an Apple/Google identity to it.
            SignInView { _ in
                showSecureAccount = false
                isLegacyAccount = AuthService.shared.credential(for: userID) == nil
            }
        }
        .confirmationDialog(
            pendingDeleteKey.map { "Delete \(family.children?[$0]?.name ?? $0)'s profile?" } ?? "",
            isPresented: Binding(
                get: { pendingDeleteKey != nil },
                set: { if !$0 { pendingDeleteKey = nil } }
            ),
            titleVisibility: .visible
        ) {
            Button("Delete profile", role: .destructive) {
                if let key = pendingDeleteKey { deleteKid(key) }
            }
            Button("Cancel", role: .cancel) { pendingDeleteKey = nil }
        } message: {
            Text("This permanently removes this child and everything saved about them. This can't be undone.")
        }
        .trackScreen("profile_settings")
        .task { await load() }
        .task {
            // Legacy = authenticated today but with no stored v1 credential.
            isLegacyAccount = !userID.isEmpty && AuthService.shared.credential(for: userID) == nil
        }
    }

    // MARK: - Rows

    private var parentRow: some View {
        HStack(spacing: .hearth400) {
            AvatarCircleView(urlString: family.parent?.avatarUrl,
                             fallbackSystemImage: "person.fill", size: 28)
                .frame(width: 28)
            VStack(alignment: .leading, spacing: 2) {
                Text(family.parent?.name?.isEmpty == false ? family.parent!.name! : "Add your name")
                    .font(.hearthBodyMD.weight(.semibold))
                    .foregroundColor(.inkPrimary)
                let sub = [family.parent?.postalCode, family.parent?.country]
                    .compactMap { $0 }.filter { !$0.isEmpty }.joined(separator: " · ")
                if !sub.isEmpty {
                    Text(sub).font(.hearthBodySM).foregroundColor(.inkMuted)
                }
            }
        }
    }

    private func kidRow(_ key: String) -> some View {
        let kid = family.children?[key]
        return HStack(spacing: .hearth400) {
            AvatarCircleView(urlString: kid?.avatarUrl,
                             fallbackSystemImage: "figure.child", size: 28)
                .frame(width: 28)
            Text(kid?.name ?? key)
                .font(.hearthBodyMD)
                .foregroundColor(.inkPrimary)
            Spacer()
            if let age = kid?.age {
                Text("Age \(age.truncatingRemainder(dividingBy: 1) == 0 ? String(Int(age)) : String(age))")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
            }
        }
    }

    private var learnedRow: some View {
        HStack(spacing: .hearth400) {
            Image(systemName: "sparkles")
                .foregroundColor(.accentDefault)
                .frame(width: 24)
            VStack(alignment: .leading, spacing: 2) {
                Text("What we've learned")
                    .font(.hearthBodyMD.weight(.semibold))
                    .foregroundColor(.inkPrimary)
                Text("Review + correct what your coach has gathered")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
            }
        }
    }

    // MARK: - Data

    private func apply(_ fam: FamilyProfileDTO) {
        family = fam
        kidKeys = (fam.children ?? [:]).keys.sorted()
    }

    private func deleteKid(_ key: String) {
        guard let baseURL = configuration.baseURL else { return }
        pendingDeleteKey = nil
        Task {
            do {
                let fam = try await ProfileService.deleteKid(
                    baseURL: baseURL, userID: userID, name: key
                )
                apply(fam)
            } catch {
                errorMessage = "Couldn't delete that profile. Check your connection and try again."
            }
        }
    }

    private func load() async {
        guard let baseURL = configuration.baseURL, !userID.isEmpty else { return }
        do {
            let fam = try await ProfileService.getProfile(baseURL: baseURL, userID: userID)
            apply(fam)
        } catch {
            errorMessage = "Couldn't load your profile."
        }
    }
}
