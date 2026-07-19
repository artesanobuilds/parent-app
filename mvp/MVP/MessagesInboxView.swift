import SwiftUI

/// DM inbox, presented as a sheet from the Circle tab's envelope button.
/// Owns its own NavigationStack: inbox rows push ConversationView; the compose
/// button opens the member directory picker.
struct MessagesInboxView: View {
    let userID: String
    let baseURL: URL

    @EnvironmentObject private var session: AppSession
    @State private var conversations: [DMConversation] = []
    @State private var loading = true
    @State private var errorMessage: String?
    @State private var showingCompose = false
    @State private var navPath = NavigationPath()
    // Bumped on return from a thread so the inbox re-fetches (unread counts
    // move when a thread is read — the source-of-truth re-fetch rule).
    @State private var refreshToken = 0

    var body: some View {
        NavigationStack(path: $navPath) {
            Group {
                if loading && conversations.isEmpty {
                    ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if conversations.isEmpty {
                    emptyState
                } else {
                    inboxList
                }
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .navigationTitle("Messages")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showingCompose = true
                    } label: {
                        Image(systemName: "square.and.pencil")
                            .font(.system(size: 17, weight: .medium))
                            .foregroundColor(.accentDefault)
                    }
                    .accessibilityLabel("New message")
                }
            }
            .navigationDestination(for: DMConversation.self) { conv in
                ConversationView(conversation: conv, userID: userID, baseURL: baseURL)
            }
            .sheet(isPresented: $showingCompose) {
                MemberPickerView(userID: userID, baseURL: baseURL) { member in
                    showingCompose = false
                    Task { await startConversation(with: member) }
                }
            }
            .task(id: refreshToken) { await load() }
            .onChange(of: navPath) { _, path in
                if path.isEmpty { refreshToken += 1 }
            }
            // A DM push while the inbox is visible → unread counts move live.
            .onReceive(NotificationCenter.default.publisher(for: .dmPushReceived)) { _ in
                refreshToken += 1
            }
            .trackScreen("dm_inbox")
        }
    }

    private var emptyState: some View {
        VStack(spacing: .hearth400) {
            Image(systemName: "envelope")
                .font(.system(size: 40, weight: .light))
                .foregroundColor(.inkMuted)
            Text("No messages yet")
                .font(.hearthTitleMD)
                .foregroundColor(.inkPrimary)
            Text("Start a conversation with another parent — from the directory here, or from any Circle post.")
                .font(.hearthBodySM)
                .foregroundColor(.inkMuted)
                .multilineTextAlignment(.center)
                .padding(.horizontal, .hearth800)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var inboxList: some View {
        List {
            if let errorMessage {
                Text(errorMessage).font(.hearthBodySM).foregroundColor(.statusError)
            }
            ForEach(conversations) { conv in
                Button {
                    navPath.append(conv)
                } label: {
                    inboxRow(conv)
                }
            }
        }
        .listStyle(.plain)
        .refreshable { await load() }
    }

    private func inboxRow(_ conv: DMConversation) -> some View {
        HStack(spacing: .hearth400) {
            Circle()
                .fill(Color.accentTint)
                .frame(width: 44, height: 44)
                .overlay(
                    Text(conv.peerInitials)
                        .font(.hearthLabel)
                        .foregroundColor(.accentDefault)
                )
            VStack(alignment: .leading, spacing: 2) {
                Text(conv.peerName)
                    .font(.hearthBodyMD.weight((conv.unreadCount ?? 0) > 0 ? .bold : .semibold))
                    .foregroundColor(.inkPrimary)
                Text(conv.lastMessagePreview.isEmpty ? "Say hello" : conv.lastMessagePreview)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                    .lineLimit(1)
            }
            Spacer()
            if let unread = conv.unreadCount, unread > 0 {
                Text("\(unread)")
                    .font(.hearthLabel)
                    .foregroundColor(.inkOnPhotoLight)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Color.accentDefault)
                    .clipShape(Capsule())
            }
        }
        .contentShape(Rectangle())
    }

    private func load() async {
        loading = true
        defer { loading = false }
        do {
            let result = try await DMService.inbox(userID: userID, baseURL: baseURL)
            conversations = result.conversations
            errorMessage = nil
            // Final hop of the push deep link: the inbox response carries the
            // full conversation DTO — push the thread and clear the pending id.
            if let pending = session.pendingDMConversationId {
                session.pendingDMConversationId = nil
                if let conv = conversations.first(where: { $0.id == pending }),
                   navPath.isEmpty {
                    navPath.append(conv)
                }
            }
        } catch {
            errorMessage = "Couldn't load messages. Pull to retry."
        }
    }

    private func startConversation(with member: DMMember) async {
        do {
            let conv = try await DMService.startConversation(
                peerId: member.userId, userID: userID, baseURL: baseURL
            )
            Analytics.capture("dm_conversation_started", ["source": "directory"])
            navPath.append(conv)
        } catch {
            errorMessage = "Couldn't start that conversation. Try again."
        }
    }
}

// MARK: - Member directory picker

struct MemberPickerView: View {
    let userID: String
    let baseURL: URL
    var onPick: (DMMember) -> Void

    @State private var members: [DMMember] = []
    @State private var loading = true
    @State private var searchText = ""
    @Environment(\.dismiss) private var dismiss

    private var filtered: [DMMember] {
        guard !searchText.trimmingCharacters(in: .whitespaces).isEmpty else { return members }
        return members.filter { $0.displayName.localizedCaseInsensitiveContains(searchText) }
    }

    var body: some View {
        NavigationStack {
            Group {
                if loading {
                    ProgressView().frame(maxWidth: .infinity, maxHeight: .infinity)
                } else if members.isEmpty {
                    Text("No other parents in the beta yet.")
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkMuted)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List(filtered) { member in
                        Button {
                            onPick(member)
                        } label: {
                            HStack(spacing: .hearth400) {
                                Circle()
                                    .fill(Color.accentTint)
                                    .frame(width: 36, height: 36)
                                    .overlay(
                                        Text(member.initials)
                                            .font(.hearthLabel)
                                            .foregroundColor(.accentDefault)
                                    )
                                Text(member.displayName)
                                    .font(.hearthBodyMD)
                                    .foregroundColor(.inkPrimary)
                            }
                        }
                    }
                    .listStyle(.plain)
                    .searchable(text: $searchText, prompt: "Search parents")
                }
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .navigationTitle("New message")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
            .task {
                members = (try? await DMService.members(userID: userID, baseURL: baseURL)) ?? []
                loading = false
            }
            .trackScreen("dm_member_picker")
        }
    }
}
