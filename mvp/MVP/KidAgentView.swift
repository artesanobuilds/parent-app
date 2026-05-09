import SwiftUI

/// The kid's surface. Single canvas, voice-first, no tabs, no chrome.
///
/// First-meeting ritual: agent speaks first (TTS) using `voice_examples[0]`
/// or a synthesized opener. Subsequent turns stream via `/kid-chat`.
struct KidAgentView: View {
    let userID: String
    let baseURL: URL
    let kid: KidAgentConfig
    let onExit: () -> Void

    @StateObject private var voice = VoiceController()
    @StateObject private var vm: KidChatViewModel
    @State private var hasGreeted: Bool = false
    @State private var typedDraft: String = ""
    @State private var showExitConfirm = false

    init(userID: String, baseURL: URL, kid: KidAgentConfig, onExit: @escaping () -> Void) {
        self.userID = userID
        self.baseURL = baseURL
        self.kid = kid
        self.onExit = onExit
        _vm = StateObject(wrappedValue: KidChatViewModel(
            userID: userID, baseURL: baseURL, kid: kid
        ))
    }

    var body: some View {
        ZStack {
            backgroundGradient

            VStack(spacing: 0) {
                topBar
                ScrollViewReader { proxy in
                    ScrollView {
                        VStack(spacing: 12) {
                            ForEach(vm.messages) { msg in
                                KidMessageBubble(
                                    message: msg, agentName: kid.invariants.agentDisplayName,
                                    bloom: bloomColor
                                )
                                .id(msg.id)
                            }
                            if vm.isStreaming {
                                HStack {
                                    Circle().fill(bloomColor).frame(width: 8, height: 8)
                                        .opacity(0.6)
                                    Spacer()
                                }
                                .padding(.horizontal, 24)
                            }
                        }
                        .padding(.horizontal, 16)
                        .padding(.top, 16)
                    }
                    .onChange(of: vm.messages.count) { _, _ in
                        if let last = vm.messages.last?.id {
                            withAnimation { proxy.scrollTo(last, anchor: .bottom) }
                        }
                    }
                }
                inputBar
            }
        }
        .preferredColorScheme(.dark)
        .task { await firstMeeting() }
        .onChange(of: vm.lastAssistantText) { _, newValue in
            if !newValue.isEmpty { voice.speak(newValue) }
        }
        .onChange(of: voice.transcribedText) { _, newValue in
            // While listening, keep the draft synced to whatever's been heard.
            if voice.isListening { typedDraft = newValue }
        }
        .alert("Bring this back to the grown-up?", isPresented: $showExitConfirm) {
            Button("Yes", role: .destructive) {
                voice.stopSpeaking(); voice.stopListening()
                onExit()
            }
            Button("Stay", role: .cancel) {}
        }
    }

    private var backgroundGradient: some View {
        // A quiet bloom of the agent's color over the dark base.
        ZStack {
            Color.brandBackground.ignoresSafeArea()
            RadialGradient(
                colors: [bloomColor.opacity(0.18), .clear],
                center: .top,
                startRadius: 100,
                endRadius: 600
            )
            .ignoresSafeArea()
        }
    }

    private var topBar: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(kid.invariants.agentDisplayName)
                    .font(.system(.title2, design: .serif).weight(.semibold))
                    .foregroundColor(.white)
                Text("for \(kid.kidName)")
                    .font(.caption)
                    .foregroundColor(.white.opacity(0.6))
            }
            Spacer()
            // Hidden-ish exit: small chevron, requires long-press to confirm.
            Button {} label: {
                Image(systemName: "rectangle.portrait.and.arrow.right")
                    .font(.system(size: 16))
                    .foregroundColor(.white.opacity(0.4))
                    .padding(8)
            }
            .simultaneousGesture(
                LongPressGesture(minimumDuration: 0.6).onEnded { _ in
                    showExitConfirm = true
                }
            )
        }
        .padding(.horizontal, 16).padding(.vertical, 10)
    }

    private var inputBar: some View {
        HStack(spacing: 10) {
            Button {
                if voice.isListening {
                    voice.stopListening()
                    if !typedDraft.isEmpty { send() }
                } else {
                    Task {
                        let ok = await voice.requestPermissions()
                        guard ok else { return }
                        voice.startListening()
                    }
                }
            } label: {
                ZStack {
                    Circle()
                        .fill(voice.isListening ? bloomColor : bloomColor.opacity(0.3))
                        .frame(width: 56, height: 56)
                    Image(systemName: voice.isListening ? "waveform" : "mic.fill")
                        .font(.system(size: 22, weight: .semibold))
                        .foregroundColor(voice.isListening ? .white : bloomColor)
                }
            }

            TextField("type or tap the mic", text: $typedDraft, axis: .vertical)
                .padding(.vertical, 10).padding(.horizontal, 14)
                .background(Color.brandSurface)
                .foregroundColor(.white)
                .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
                .lineLimit(1...4)

            if !typedDraft.isEmpty && !voice.isListening {
                Button(action: send) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 32))
                        .foregroundColor(bloomColor)
                }
            }
        }
        .padding(.horizontal, 12).padding(.bottom, 10).padding(.top, 6)
    }

    private func send() {
        let text = typedDraft.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty, !vm.isStreaming else { return }
        typedDraft = ""
        Task { await vm.send(text) }
    }

    private func firstMeeting() async {
        guard !hasGreeted else { return }
        hasGreeted = true
        // Pull existing transcript first so a returning kid resumes naturally.
        await vm.loadHistory()
        if vm.messages.isEmpty {
            // No history → ceremonial first turn. Use the first voice example
            // if we have one; otherwise generate a generic opener.
            let opener = kid.invariants.voiceExamples.first
                ?? "Hi \(kid.kidName)! I'm \(kid.invariants.agentDisplayName). What's on your mind?"
            vm.appendAssistantSpoken(opener)
            voice.speak(opener)
        }
    }

    private var bloomColor: Color {
        let words = kid.invariants.personalityDescription.lowercased()
            + " " + kid.invariants.voiceExamples.joined(separator: " ").lowercased()
        if words.contains("playful") || words.contains("silly") {
            return Color(red: 0.36, green: 0.65, blue: 0.62)  // muted teal
        }
        if words.contains("warm") || words.contains("cozy") {
            return Color(red: 0.78, green: 0.45, blue: 0.34)  // terracotta
        }
        return .brandGold
    }
}


private struct KidMessageBubble: View {
    let message: KidChatMessage
    let agentName: String
    let bloom: Color

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            if message.role == .assistant {
                Circle()
                    .fill(bloom.opacity(0.3))
                    .frame(width: 32, height: 32)
                    .overlay(Text(String(agentName.prefix(1)))
                        .font(.caption.weight(.bold)).foregroundColor(bloom))
                Text(message.content)
                    .font(.system(.body, design: .serif))
                    .foregroundColor(.white)
                    .padding(12)
                    .background(Color.brandSurface)
                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                    .frame(maxWidth: .infinity, alignment: .leading)
                Spacer(minLength: 24)
            } else {
                Spacer(minLength: 48)
                Text(message.content)
                    .font(.system(.body))
                    .foregroundColor(.brandBlack)
                    .padding(12)
                    .background(bloom.opacity(0.85))
                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                    .frame(maxWidth: .infinity, alignment: .trailing)
            }
        }
    }
}


// MARK: - ViewModel

@MainActor
final class KidChatViewModel: ObservableObject {
    let userID: String
    let baseURL: URL
    let kid: KidAgentConfig
    private var service: KidAgentService { KidAgentService(baseURL: baseURL, userID: userID) }

    @Published var messages: [KidChatMessage] = []
    @Published var isStreaming: Bool = false
    @Published var lastAssistantText: String = ""

    private var streamTask: Task<Void, Never>?
    private let threadID = "default"

    init(userID: String, baseURL: URL, kid: KidAgentConfig) {
        self.userID = userID; self.baseURL = baseURL; self.kid = kid
    }

    func loadHistory() async {
        do {
            let server = try await service.transcripts(kidName: kid.kidName, threadID: threadID)
            self.messages = server.compactMap { m in
                guard let role = KidChatMessage.Role(rawValue: m.role) else { return nil }
                return KidChatMessage(role: role, content: m.content)
            }
        } catch {
            print("[KidChatVM] history failed: \(error)")
        }
    }

    func appendAssistantSpoken(_ text: String) {
        // Used for the first-meeting opener so the bubble matches what TTS speaks.
        let msg = KidChatMessage(role: .assistant, content: text)
        messages.append(msg)
        lastAssistantText = text
    }

    func send(_ text: String) async {
        let userMsg = KidChatMessage(role: .user, content: text)
        messages.append(userMsg)
        let placeholder = KidChatMessage(role: .assistant, content: "")
        messages.append(placeholder)
        let placeholderID = placeholder.id
        isStreaming = true
        lastAssistantText = ""

        streamTask = Task { [weak self] in
            guard let self else { return }
            var buffer = ""
            do {
                for try await token in self.service.streamKidChat(
                    kidName: self.kid.kidName, message: text, threadID: self.threadID
                ) {
                    buffer += token
                    self.replace(messageID: placeholderID, content: buffer)
                }
                self.lastAssistantText = buffer
            } catch {
                self.replace(messageID: placeholderID,
                             content: "(something went wrong — let's try again later)")
                print("[KidChatVM] stream failed: \(error)")
            }
            self.isStreaming = false
        }
    }

    private func replace(messageID: UUID, content: String) {
        if let idx = messages.firstIndex(where: { $0.id == messageID }) {
            messages[idx] = KidChatMessage(id: messageID, role: .assistant, content: content)
        }
    }
}

struct KidChatMessage: Identifiable, Equatable {
    enum Role: String { case user, assistant, system }
    let id: UUID
    let role: Role
    let content: String

    init(id: UUID = UUID(), role: Role, content: String) {
        self.id = id; self.role = role; self.content = content
    }
}
