import ElevenLabs
import SwiftUI

/// The kid's surface. Single canvas, voice-first, no tabs, no chrome.
///
/// SOBER VARIANT per the Hearth tokens spec: this surface uses `bg/sober`,
/// no `photo/*` tiles, no decorative serif, no motion beyond `motion/instant`,
/// and a restrained subset of the token allowlist. The kid agent is a safety
/// surface — its quietness is load-bearing.
///
/// The surface renders exactly one of four phases owned by
/// `KidCompanionCoordinator` (see that file for the transition map):
/// connecting → voiceLive | textFallback | crisisLocked.
struct KidAgentView: View {
    let userID: String
    let baseURL: URL
    let kid: KidAgentConfig
    let onExit: () -> Void

    @StateObject private var coordinator: KidCompanionCoordinator
    @State private var showExitConfirm = false
    /// Set when the live-voice surface first appears; nil for text-only sessions
    /// so we only emit a voice-duration event when voice actually happened.
    @State private var voiceStart: Date?

    init(userID: String, baseURL: URL, kid: KidAgentConfig, onExit: @escaping () -> Void) {
        self.userID = userID
        self.baseURL = baseURL
        self.kid = kid
        self.onExit = onExit
        _coordinator = StateObject(wrappedValue: KidCompanionCoordinator(
            userID: userID, baseURL: baseURL, kid: kid
        ))
    }

    var body: some View {
        ZStack {
            // Sober: a single quiet canvas. No bloom, no gradient, no photo tile.
            Color.bgSober.ignoresSafeArea()

            VStack(spacing: 0) {
                topBar
                switch coordinator.phase {
                case .connecting:
                    ConnectingSurface(agentName: kid.invariants.agentDisplayName)
                case .voiceLive(let conversation):
                    VoiceConversationSurface(
                        conversation: conversation,
                        agentName: kid.invariants.agentDisplayName,
                        history: coordinator.vm.messages,
                        inputLevel: coordinator.inputLevel,
                        onSend: { text in
                            Task { await coordinator.sendVoiceText(text) }
                        },
                        onToggleMute: {
                            Task { await coordinator.toggleMute() }
                        }
                    )
                    .onAppear { if voiceStart == nil { voiceStart = Date() } }
                case .textFallback:
                    TextChatSurface(
                        vm: coordinator.vm,
                        agentName: kid.invariants.agentDisplayName
                    )
                case .crisisLocked:
                    CrisisLockedSurface(history: coordinator.vm.messages,
                                        agentName: kid.invariants.agentDisplayName)
                }
            }
        }
        .trackScreen("kid_companion")
        .task {
            Analytics.capture("chat_opened", ["agent_kind": "companion"])
            await coordinator.start()
        }
        .onDisappear {
            if let start = voiceStart {
                Analytics.capture("voice_session_ended",
                                  ["surface": "kid",
                                   "duration_s": Int(Date().timeIntervalSince(start))])
            }
            // Idempotent; the exit-confirm path already awaited a full teardown.
            Task { await coordinator.exit() }
        }
        .alert("Bring this back to the grown-up?", isPresented: $showExitConfirm) {
            Button("Yes", role: .destructive) {
                // Await the WebRTC/audio-engine teardown BEFORE leaving so an
                // immediate re-entry starts from a clean engine (re-entry bug).
                Task {
                    await coordinator.exit()
                    onExit()
                }
            }
            Button("Stay", role: .cancel) {}
        }
    }

    private var topBar: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                // Sober variant forbids decorative serif — use Inter title.
                Text(kid.invariants.agentDisplayName)
                    .font(.hearthTitleLG)
                    .foregroundColor(.inkPrimary)
                Text("for \(kid.kidName)")
                    .font(.hearthCaptionMono)
                    .foregroundColor(.inkMuted)
            }
            Spacer()
            // Hidden-ish exit: small chevron, requires long-press to confirm.
            Button {} label: {
                Image(systemName: "rectangle.portrait.and.arrow.right")
                    .font(.system(size: 16))
                    .foregroundColor(.inkMuted)
                    .frame(width: 44, height: 44)
                    .contentShape(Rectangle())
            }
            .simultaneousGesture(
                LongPressGesture(minimumDuration: 0.6).onEnded { _ in
                    showExitConfirm = true
                }
            )
        }
        .padding(.horizontal, .hearth500).padding(.vertical, .hearth400)
    }
}

// MARK: - Connecting

/// Shown while the voice connect attempt is unresolved. A full-canvas,
/// unmissable state — and deliberately NO input, so nothing the kid does here
/// can start a competing exchange or grab the audio device mid-handshake.
/// Resolves to voice, text fallback, or crisis within seconds.
private struct ConnectingSurface: View {
    let agentName: String

    var body: some View {
        VStack(spacing: .hearth500) {
            Spacer()

            Circle()
                .fill(Color.accentTint)
                .frame(width: 96, height: 96)
                .overlay(
                    Text(String(agentName.prefix(1)))
                        .font(.system(size: 40, weight: .semibold))
                        .foregroundColor(.accentDefault)
                )

            Text("calling \(agentName)…")
                .font(.hearthTitleLG)
                .foregroundColor(.inkPrimary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, .hearth700)

            Text("hang on a moment")
                .font(.hearthCaptionMono)
                .foregroundColor(.inkMuted)

            ProgressView()
                .padding(.top, .hearth300)

            Spacer()
            Spacer()
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Voice (ElevenLabs ConvAI)

/// Live voice session. The mic is always-on (WebRTC) and audio plays
/// automatically; the transcript renders straight from the SDK's published
/// `messages`, preceded by prior sessions' history. Typed input goes through
/// the live conversation — the agent answers in voice.
private struct VoiceConversationSurface: View {
    @ObservedObject var conversation: Conversation
    let agentName: String
    let history: [KidChatMessage]
    let inputLevel: Double
    let onSend: (String) -> Void
    let onToggleMute: () -> Void

    @State private var draft: String = ""
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(spacing: .hearth400) {
                        ForEach(history) { msg in
                            KidMessageBubble(message: msg, agentName: agentName)
                                .id(msg.id)
                        }
                        ForEach(conversation.messages) { msg in
                            KidMessageBubble(
                                message: KidChatMessage(
                                    role: msg.role == .user ? .user : .assistant,
                                    content: msg.content
                                ),
                                agentName: agentName
                            )
                            .id(msg.id)
                        }
                    }
                    .padding(.horizontal, .hearth500)
                    .padding(.top, .hearth500)
                }
                .onChange(of: conversation.messages.count) { _, _ in
                    if let last = conversation.messages.last?.id {
                        // Sober: no animation on scroll.
                        proxy.scrollTo(last, anchor: .bottom)
                    }
                }
            }

            ListeningOrb(
                level: inputLevel,
                agentState: conversation.agentState,
                isMuted: conversation.isMuted,
                reduceMotion: reduceMotion
            )
            .padding(.top, .hearth500)

            statusLine
                .padding(.top, .hearth300)

            inputBar
        }
    }

    private var statusLine: some View {
        HStack(spacing: .hearth400) {
            Circle()
                .fill(Color.accentDefault)
                .frame(width: 10, height: 10)
                .opacity(conversation.agentState == .speaking ? 1.0 : 0.5)
            Text(conversation.isMuted ? "muted — tap to talk" : stateLabel)
                .font(.hearthCaptionMono)
                .foregroundColor(.inkMuted)
        }
    }

    private var stateLabel: String {
        switch conversation.agentState {
        case .listening: return "listening…"
        case .thinking:  return "thinking…"
        case .speaking:  return "speaking…"
        }
    }

    private var inputBar: some View {
        HStack(spacing: .hearth400) {
            // Fixed mic toggle (always present, unlike the conditional send button).
            Button(action: onToggleMute) {
                Image(systemName: conversation.isMuted ? "mic.slash.fill" : "mic.fill")
                    .font(.system(size: 22))
                    .foregroundColor(conversation.isMuted ? .inkMuted : .accentDefault)
                    .frame(width: 44, height: 44)
                    .contentShape(Rectangle())
            }
            .accessibilityLabel(conversation.isMuted ? "Unmute" : "Mute")
            .accessibilityValue(conversation.isMuted ? "Muted" : "")

            TextField("talk, or type here", text: $draft, axis: .vertical)
                .padding(.vertical, .hearth400).padding(.horizontal, .hearth500)
                .background(Color.bgElevated)
                .foregroundColor(.inkPrimary)
                .font(.hearthBodyMD)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                        .stroke(Color.borderStrong, lineWidth: 1)
                )
                .lineLimit(1...4)

            if !draft.isEmpty {
                Button {
                    let text = draft
                    draft = ""
                    onSend(text)
                } label: {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 32))
                        .foregroundColor(.accentDefault)
                        .frame(width: 44, height: 44)
                        .contentShape(Rectangle())
                }
            }
        }
        .padding(.horizontal, .hearth400).padding(.bottom, .hearth400).padding(.top, .hearth300)
    }
}

// MARK: - Listening orb

/// Mic-reactive listening cue for the voice surface — the one place the kid
/// surface relaxes the "sober: no motion" rule (and only when Reduce Motion is
/// off; otherwise it falls back to a static state chip). The text status line
/// remains the always-present accessibility layer, so this is decorative.
/// (Internal, not private: reused by the parent voice surface.)
struct ListeningOrb: View {
    let level: Double                  // 0…1 smoothed mic level (coordinator)
    let agentState: ElevenLabs.AgentState
    let isMuted: Bool
    let reduceMotion: Bool

    @State private var selfPulse = false

    var body: some View {
        if reduceMotion {
            // Static, on-brand chip — no continuous animation.
            Text(chipLabel)
                .font(.hearthCaptionMono)
                .foregroundColor(.inkMuted)
                .padding(.vertical, .hearth300)
                .padding(.horizontal, .hearth500)
                .background(
                    Capsule().fill(Color.accentTint.opacity(isMuted ? 0.25 : 1.0))
                )
                .accessibilityHidden(true)
        } else {
            orb
        }
    }

    private var orb: some View {
        Circle()
            .fill(isMuted ? Color.inkMuted : Color.accentTint)
            .overlay(
                Circle()
                    .fill(Color.accentDefault)
                    .scaleEffect(0.55)
                    .opacity(coreOpacity)
            )
            .frame(width: 88, height: 88)
            .scaleEffect(scale)
            .opacity(isMuted ? 0.45 : 1.0)
            .saturation(isMuted ? 0.0 : 1.0)
            .animation(.easeInOut(duration: 0.2), value: level)
            .animation(.easeInOut(duration: selfPulseDuration).repeatForever(autoreverses: true),
                       value: selfPulse)
            .onAppear { selfPulse = true }
            .accessibilityHidden(true)
    }

    /// Scale: listening tracks the mic; thinking/speaking use a slow self-pulse.
    private var scale: CGFloat {
        if isMuted { return 1.0 }
        switch agentState {
        case .listening: return 1.0 + 0.06 * CGFloat(level)
        case .thinking:  return selfPulse ? 1.03 : 1.0
        case .speaking:  return selfPulse ? 1.04 : 1.0
        }
    }

    private var coreOpacity: Double {
        if isMuted { return 0.2 }
        switch agentState {
        case .listening: return 0.4 + 0.4 * level
        case .thinking:  return selfPulse ? 0.5 : 0.25
        case .speaking:  return selfPulse ? 0.7 : 0.4
        }
    }

    private var selfPulseDuration: Double {
        agentState == .speaking ? 0.9 : 1.8
    }

    private var chipLabel: String {
        if isMuted { return "muted" }
        switch agentState {
        case .listening: return "listening"
        case .thinking:  return "thinking"
        case .speaking:  return "speaking"
        }
    }
}

// MARK: - Text fallback

/// Quiet text-only chat over /kid-chat SSE. No voice of any kind — voice is
/// exclusively the ConvAI session's job; when it isn't available the surface
/// stays silent rather than reaching for a second implementation.
private struct TextChatSurface: View {
    @ObservedObject var vm: KidChatViewModel
    let agentName: String

    @State private var draft: String = ""

    var body: some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(spacing: .hearth400) {
                        ForEach(vm.messages) { msg in
                            KidMessageBubble(message: msg, agentName: agentName)
                                .id(msg.id)
                        }
                        if vm.isStreaming {
                            HStack {
                                Circle().fill(Color.accentDefault).frame(width: 8, height: 8)
                                    .opacity(0.6)
                                Spacer()
                            }
                            .padding(.horizontal, .hearth700)
                        }
                    }
                    .padding(.horizontal, .hearth500)
                    .padding(.top, .hearth500)
                }
                .onChange(of: vm.messages.count) { _, _ in
                    if let last = vm.messages.last?.id {
                        // Sober: no animation on scroll.
                        proxy.scrollTo(last, anchor: .bottom)
                    }
                }
            }

            inputBar
        }
    }

    private var inputBar: some View {
        HStack(spacing: .hearth400) {
            TextField("type to your friend", text: $draft, axis: .vertical)
                .padding(.vertical, .hearth400).padding(.horizontal, .hearth500)
                .background(Color.bgElevated)
                .foregroundColor(.inkPrimary)
                .font(.hearthBodyMD)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                        .stroke(Color.borderStrong, lineWidth: 1)
                )
                .lineLimit(1...4)

            if !draft.isEmpty {
                Button {
                    let text = draft.trimmingCharacters(in: .whitespacesAndNewlines)
                    draft = ""
                    guard !text.isEmpty, !vm.isStreaming else { return }
                    Task { await vm.send(text) }
                } label: {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 32))
                        .foregroundColor(.accentDefault)
                        .frame(width: 44, height: 44)
                        .contentShape(Rectangle())
                }
            }
        }
        .padding(.horizontal, .hearth400).padding(.bottom, .hearth400).padding(.top, .hearth300)
    }
}

// MARK: - Crisis locked

/// Frozen safety surface. The conversation history stays visible, but there is
/// no input and no retry — the agent stays locked until the parent intervenes.
/// When a parent is scared, the app gets quieter.
private struct CrisisLockedSurface: View {
    let history: [KidChatMessage]
    let agentName: String

    var body: some View {
        VStack(spacing: 0) {
            HistoryScroll(messages: history, agentName: agentName)
            Spacer(minLength: 0)
            HStack(spacing: .hearth400) {
                Image(systemName: "moon.zzz.fill")
                    .font(.system(size: 16))
                    .foregroundColor(.inkMuted)
                Text("time to find your grown-up")
                    .font(.hearthCaptionMono)
                    .foregroundColor(.inkMuted)
            }
            .padding(.bottom, .hearth700)
            .padding(.top, .hearth300)
        }
    }
}

// MARK: - Shared pieces

private struct HistoryScroll: View {
    let messages: [KidChatMessage]
    let agentName: String

    var body: some View {
        ScrollView {
            VStack(spacing: .hearth400) {
                ForEach(messages) { msg in
                    KidMessageBubble(message: msg, agentName: agentName)
                        .id(msg.id)
                }
            }
            .padding(.horizontal, .hearth500)
            .padding(.top, .hearth500)
        }
    }
}

private struct KidMessageBubble: View {
    let message: KidChatMessage
    let agentName: String

    var body: some View {
        HStack(alignment: .top, spacing: .hearth400) {
            if message.role == .assistant {
                Circle()
                    .fill(Color.accentTint)
                    .frame(width: 32, height: 32)
                    .overlay(Text(String(agentName.prefix(1)))
                        .font(.hearthLabel).foregroundColor(.accentDefault))
                Text(message.content)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkPrimary)
                    .padding(.hearth400)
                    .background(Color.bgElevated)
                    .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .stroke(Color.borderHairline, lineWidth: 1)
                    )
                    .frame(maxWidth: .infinity, alignment: .leading)
                Spacer(minLength: 24)
            } else {
                Spacer(minLength: 48)
                Text(message.content)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkOnPhotoLight)
                    .padding(.hearth400)
                    .background(Color.accentDefault)
                    .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                    .frame(maxWidth: .infinity, alignment: .trailing)
            }
        }
    }
}

// MARK: - ViewModel (text transport)

@MainActor
final class KidChatViewModel: ObservableObject {
    let userID: String
    let baseURL: URL
    let kid: KidAgentConfig
    let service: KidAgentService

    @Published var messages: [KidChatMessage] = []
    @Published var isStreaming: Bool = false

    /// Set by the coordinator: invoked when the backend reports the agent is
    /// crisis-locked (the `frozen` SSE event) so the surface can freeze.
    var onFrozen: ((String) -> Void)?

    private var streamTask: Task<Void, Never>?
    private let threadID = "default"

    init(userID: String, baseURL: URL, kid: KidAgentConfig) {
        self.userID = userID; self.baseURL = baseURL; self.kid = kid
        self.service = KidAgentService(baseURL: baseURL, userID: userID)
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

    /// Append a locally generated assistant message (e.g. the text-mode
    /// first-meeting greeting). Local-only; nothing is spoken.
    func appendAssistantLocal(_ text: String) {
        messages.append(KidChatMessage(role: .assistant, content: text))
    }

    func send(_ text: String) async {
        streamTask?.cancel()

        let userMsg = KidChatMessage(role: .user, content: text)
        messages.append(userMsg)
        let placeholder = KidChatMessage(role: .assistant, content: "")
        messages.append(placeholder)
        let placeholderID = placeholder.id
        isStreaming = true

        streamTask = Task { [weak self] in
            guard let self else { return }
            var buffer = ""
            do {
                for try await event in self.service.streamKidChatEvents(
                    kidName: self.kid.kidName, message: text, threadID: self.threadID
                ) {
                    switch event {
                    case .token(let token):
                        buffer += token
                        self.replace(messageID: placeholderID, content: buffer)
                    case .frozen(let category):
                        self.onFrozen?(category)
                    }
                }
            } catch {
                self.replace(messageID: placeholderID,
                             content: "(something went wrong — let's try again later)")
                print("[KidChatVM] stream failed: \(error)")
            }
            self.isStreaming = false
        }
    }

    func replace(messageID: UUID, content: String) {
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
