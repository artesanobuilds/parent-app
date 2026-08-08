import SwiftUI

/// Circle-002 — new conversation composer. Title, body, and an "Invite to the
/// conversation" checklist over the household roster (defaults to everyone
/// selected — a group ask is the common case). "Add circle members" opens the
/// invite flow for someone not in the roster yet.
struct NewConversationView: View {
    let userID: String
    let baseURL: URL
    let roster: [HouseholdMember]
    /// Called with the created conversation so the caller can push straight
    /// into its thread.
    var onCreated: (CircleConversation) -> Void

    @State private var title = ""
    @State private var messageBody = ""
    @State private var selected: Set<String> = []
    @State private var creating = false
    @State private var errorMessage: String?
    @State private var showingInvite = false
    @Environment(\.dismiss) private var dismiss

    private var canCreate: Bool {
        !title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        && !messageBody.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        && !creating
    }

    private var composerForm: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: .hearth600) {
                field(label: "Title") {
                    TextField("", text: $title, prompt: Text("Dinner with Ben & Lily").foregroundColor(.inkPlaceholder))
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkPrimary)
                }
                field(label: "Your message") {
                    TextEditor(text: $messageBody)
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkPrimary)
                        .scrollContentBackground(.hidden)
                        .frame(minHeight: 120)
                }

                VStack(alignment: .leading, spacing: .hearth300) {
                    Text("Invite to the conversation")
                        .font(.hearthLabel)
                        .foregroundColor(.inkMuted)
                        .tracking(0.66)
                        .textCase(.uppercase)

                    ForEach(roster) { member in
                        Button {
                            if selected.contains(member.id) { selected.remove(member.id) }
                            else { selected.insert(member.id) }
                        } label: {
                            HStack(spacing: .hearth400) {
                                Circle()
                                    .fill(Color.accentTint)
                                    .frame(width: 36, height: 36)
                                    .overlay(Text(member.resolvedInitials).font(.hearthLabel).foregroundColor(.accentOnCanvas))
                                Text(member.displayName)
                                    .font(.hearthBodyMD)
                                    .foregroundColor(.inkPrimary)
                                Spacer()
                                Image(systemName: selected.contains(member.id) ? "checkmark.circle.fill" : "circle")
                                    .foregroundColor(selected.contains(member.id) ? .accentDefault : .inkPlaceholder)
                            }
                            .padding(.vertical, .hearth300)
                        }
                    }

                    Button { showingInvite = true } label: {
                        HStack(spacing: .hearth300) {
                            Image(systemName: "plus.circle")
                            Text("Add circle members")
                        }
                        .font(.hearthBodyMD)
                        .foregroundColor(.accentOnCanvas)
                    }
                    .padding(.top, .hearth300)
                }

                if let errorMessage {
                    Text(errorMessage).font(.hearthBodySM).foregroundColor(.statusError)
                }
            }
            .padding(.hearth700)
        }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                composerForm
                actionButtons
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .navigationTitle("New conversation")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
            .sheet(isPresented: $showingInvite) {
                CircleInviteView(userID: userID, baseURL: baseURL)
            }
            .onAppear {
                // Default: everyone already in the roster is invited.
                if selected.isEmpty { selected = Set(roster.map(\.id)) }
            }
            .trackScreen("circle_new_conversation")
        }
    }

    private var actionButtons: some View {
        VStack(spacing: .hearth400) {
            Button {
                Task { await create() }
            } label: {
                if creating {
                    ProgressView().tint(.inkOnPhotoLight)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, .hearth500)
                } else {
                    Text("Start a discussion")
                        .font(.hearthTitleMD)
                        .foregroundColor(.inkOnPhotoLight)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, .hearth500)
                }
            }
            .background(canCreate ? Color.accentDefault : Color.bgDisabled)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusButton, style: .continuous))
            .disabled(!canCreate)

            Button("Cancel") { dismiss() }
                .font(.hearthBodyMD)
                .foregroundColor(.inkMuted)
        }
        .padding(.horizontal, .hearth700)
        .padding(.bottom, .hearth600)
        .padding(.top, .hearth300)
        .background(Color.bgCanvas)
    }

    @ViewBuilder
    private func field<Content: View>(label: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text(label)
                .font(.hearthLabel)
                .foregroundColor(.inkMuted)
                .tracking(0.66)
                .textCase(.uppercase)
            content()
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth500)
                .background(Color.bgElevated)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                        .stroke(Color.borderStrong, lineWidth: 1)
                )
        }
    }

    private func create() async {
        creating = true
        defer { creating = false }
        do {
            let created = try await CircleService.createConversation(
                title: title.trimmingCharacters(in: .whitespacesAndNewlines),
                body: messageBody.trimmingCharacters(in: .whitespacesAndNewlines),
                memberIds: Array(selected),
                userID: userID, baseURL: baseURL
            )
            Analytics.capture("circle_conversation_started", [:])
            onCreated(created)
        } catch {
            errorMessage = "Couldn't start that conversation. Try again."
        }
    }
}
