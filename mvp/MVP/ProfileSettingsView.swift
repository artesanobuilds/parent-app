import SwiftUI

/// Editable parent profile (Settings → Profile tab). Loads the current values
/// via GET /profile and saves edits via /profile/seed. The ZIP feeds the Plan
/// tab's activity discovery, so it's surfaced prominently.
struct ProfileSettingsView: View {
    let configuration: ServerConfiguration
    let userID: String

    @State private var name = ""
    @State private var postalCode = ""
    @State private var country = ""
    @State private var children: [ChildRow] = []
    @State private var isSaving = false
    @State private var savedOK = false
    @State private var errorMessage: String?

    private struct ChildRow: Identifiable {
        let id: String   // kid name (unique within a family)
        let age: Double?
    }

    var body: some View {
        Form {
            if userID.isEmpty {
                Section {
                    Text("Complete onboarding to edit your profile.")
                        .foregroundColor(.inkMuted)
                }
            } else {
                Section("Parent") {
                    TextField("Name", text: $name)
                    TextField("ZIP / Postal code", text: $postalCode)
                        .keyboardType(.numbersAndPunctuation)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    TextField("Country (e.g. US)", text: $country)
                        .textInputAutocapitalization(.characters)
                        .autocorrectionDisabled()
                }

                if !children.isEmpty {
                    Section("Kids") {
                        ForEach(children) { kid in
                            HStack {
                                Text(kid.id).foregroundColor(.inkPrimary)
                                Spacer()
                                if let age = kid.age {
                                    Text("Age \(Int(age))").foregroundColor(.inkMuted)
                                }
                            }
                        }
                    }
                }

                Section {
                    Button(isSaving ? "Saving…" : "Save profile") { save() }
                        .disabled(isSaving)
                    if savedOK {
                        Text("Saved").font(.hearthBodySM).foregroundColor(.statusSuccess)
                    }
                    if let err = errorMessage {
                        Text(err).font(.hearthBodySM).foregroundColor(.statusError)
                    }
                } footer: {
                    Text("Your ZIP is used to find camps and activities near you on the Plan tab.")
                        .font(.hearthBodySM)
                        .foregroundColor(.inkMuted)
                }
            }
        }
        .scrollContentBackground(.hidden)
        .background(Color.bgCanvas.ignoresSafeArea())
        .task { await load() }
    }

    private func load() async {
        guard let baseURL = configuration.baseURL, !userID.isEmpty else { return }
        do {
            let fam = try await ProfileService.getProfile(baseURL: baseURL, userID: userID)
            name = fam.parent?.name ?? ""
            postalCode = fam.parent?.postalCode ?? ""
            country = fam.parent?.country ?? ""
            var rows: [ChildRow] = []
            for (key, value) in (fam.children ?? [:]) {
                rows.append(ChildRow(id: value.name ?? key, age: value.age))
            }
            children = rows.sorted { $0.id < $1.id }
        } catch {
            errorMessage = "Couldn't load your profile."
        }
    }

    private func save() {
        guard let baseURL = configuration.baseURL, !userID.isEmpty else { return }
        isSaving = true
        savedOK = false
        errorMessage = nil
        Task {
            do {
                try await ProfileService.saveParentProfile(
                    baseURL: baseURL,
                    userID: userID,
                    name: name.trimmingCharacters(in: .whitespacesAndNewlines),
                    postalCode: postalCode.trimmingCharacters(in: .whitespacesAndNewlines),
                    country: country.trimmingCharacters(in: .whitespacesAndNewlines)
                )
                savedOK = true
            } catch {
                errorMessage = "Couldn't save. Check your connection and try again."
            }
            isSaving = false
        }
    }
}
