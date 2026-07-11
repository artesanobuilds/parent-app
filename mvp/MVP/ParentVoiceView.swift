import ElevenLabs
import SwiftUI

/// Opt-in voice "call" surface for the PARENT coaching agent. Presented over the
/// text chat; tap End to return (handing the session transcript back so it shows
/// in the text chat). While live: ConvAI voice, the listening orb + mute, the
/// spoken transcript, and the article/community cards surfaced via client tools.
struct ParentVoiceView: View {
    let userID: String
    let baseURL: URL
    /// Returns the session's transcript (empty if the call never went live) so
    /// the caller can show it in the text chat.
    let onClose: ([ChatMessage]) -> Void

    @StateObject private var coordinator: ParentCompanionCoordinator
    @State private var showingReport = false
    @State private var voiceStart = Date()

    init(userID: String, baseURL: URL, onClose: @escaping ([ChatMessage]) -> Void) {
        self.userID = userID
        self.baseURL = baseURL
        self.onClose = onClose
        _coordinator = StateObject(wrappedValue: ParentCompanionCoordinator(
            service: KidAgentService(baseURL: baseURL, userID: userID)
        ))
    }

    var body: some View {
        NavigationStack {
            ZStack {
                Color.bgCanvas.ignoresSafeArea()
                switch coordinator.phase {
                case .connecting:
                    VStack(spacing: 0) { header(onEnd: { onClose([]) }); connecting }
                case .voiceLive(let conversation):
                    // Pass the live conversation into a child that OBSERVES it, so
                    // the transcript + orb + mute update in real time.
                    ParentLiveCallView(
                        conversation: conversation,
                        coordinator: coordinator,
                        onEnd: { transcript in onClose(transcript) }
                    )
                case .failed(let why):
                    VStack(spacing: 0) { header(onEnd: { onClose([]) }); failed(why) }
                }
            }
            .withContentNavigationDestinations()
        }
        .trackScreen("parent_voice")
        .task { voiceStart = Date(); await coordinator.start() }
        .onDisappear {
            Analytics.capture("voice_session_ended",
                              ["surface": "parent", "duration_s": Int(Date().timeIntervalSince(voiceStart))])
            Task { await coordinator.exit() }
        }
    }

    private func header(onEnd: @escaping () -> Void) -> some View {
        ParentVoiceHeader(onEnd: { Task { await coordinator.exit(); onEnd() } })
    }

    private var connecting: some View {
        VStack(spacing: .hearth500) {
            Spacer()
            ProgressView()
            Text("calling your coach…")
                .font(.hearthCaptionMono)
                .foregroundColor(.inkMuted)
            Spacer(); Spacer()
        }
        .frame(maxWidth: .infinity)
    }

    private func failed(_ why: String) -> some View {
        VStack(spacing: .hearth500) {
            Spacer()
            Image(systemName: "phone.down.fill")
                .font(.system(size: 28)).foregroundColor(.inkMuted)
            Text(why)
                .font(.hearthBodyMD).foregroundColor(.inkSecondary)
                .multilineTextAlignment(.center).padding(.horizontal, .hearth700)
            Button("Back to chat") { onClose([]) }
                .font(.hearthLabel).foregroundColor(.accentDefault)
            Button("Report this problem") { showingReport = true }
                .font(.hearthBodySM).foregroundColor(.inkMuted)
            Spacer(); Spacer()
        }
        .frame(maxWidth: .infinity)
        .sheet(isPresented: $showingReport) {
            ReportProblemView(baseURL: baseURL, failureContext: why)
        }
    }
}

// MARK: - Header

private struct ParentVoiceHeader: View {
    let onEnd: () -> Void
    var body: some View {
        HStack {
            Text("MVP — voice")
                .font(.hearthTitleLG)
                .foregroundColor(.inkPrimary)
            Spacer()
            Button(action: onEnd) {
                Text("End")
                    .font(.hearthLabel)
                    .foregroundColor(.inkOnPhotoLight)
                    .padding(.vertical, .hearth300)
                    .padding(.horizontal, .hearth500)
                    .background(Capsule().fill(Color.accentDefault))
            }
            .accessibilityLabel("End call")
        }
        .padding(.horizontal, .hearth500).padding(.vertical, .hearth400)
    }
}

// MARK: - Live call (observes the conversation)

/// The live-call surface. Holds the SDK `Conversation` as `@ObservedObject` so
/// the transcript, agent state, and mute state render reactively (the parent's
/// earlier bug was passing the conversation as a plain value → no updates).
private struct ParentLiveCallView: View {
    @ObservedObject var conversation: Conversation
    @ObservedObject var coordinator: ParentCompanionCoordinator
    /// Hands the captured transcript up so the text chat can show it.
    let onEnd: ([ChatMessage]) -> Void

    @EnvironmentObject private var contentVM: ContentViewModel
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        VStack(spacing: 0) {
            ParentVoiceHeader(onEnd: {
                // Capture the transcript BEFORE teardown nils the conversation.
                let lines = conversation.messages.map {
                    ChatMessage(role: $0.role == .user ? .user : .assistant, content: $0.content)
                }
                Task { await coordinator.exit(); onEnd(lines) }
            })

            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: .hearth400) {
                        ForEach(conversation.messages) { msg in
                            bubble(role: msg.role, text: msg.content)
                                .id(msg.id)
                        }
                        if !coordinator.surfaced.isEmpty {
                            surfacedSection
                        }
                    }
                    .padding(.horizontal, .hearth500)
                    .padding(.top, .hearth500)
                }
                .onChange(of: conversation.messages.count) { _, _ in
                    if let last = conversation.messages.last?.id {
                        proxy.scrollTo(last, anchor: .bottom)
                    }
                }
            }

            ListeningOrb(
                level: coordinator.inputLevel,
                agentState: conversation.agentState,
                isMuted: conversation.isMuted,
                reduceMotion: reduceMotion
            )
            .padding(.top, .hearth500)

            Text(conversation.isMuted ? "muted — tap to talk" : stateLabel(conversation.agentState))
                .font(.hearthCaptionMono)
                .foregroundColor(.inkMuted)
                .padding(.top, .hearth300)

            muteBar
        }
    }

    @ViewBuilder
    private func bubble(role: Message.Role, text: String) -> some View {
        if role == .agent {
            // Voice transcripts arrive whole-turn (ElevenLabs doesn't stream them
            // in voice mode), so we type them out client-side to feel like the
            // text chat — paced to roughly track the spoken audio.
            StreamingText(text: text, spokenProgress: { coordinator.spokenProgress() })
                .font(.hearthBodyMD).foregroundColor(.inkPrimary)
                .padding(.hearth400)
                .background(Color.bgElevated)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                .frame(maxWidth: .infinity, alignment: .leading)
        } else {
            Text(text)
                .font(.hearthBodyMD).foregroundColor(.inkOnPhotoLight)
                .padding(.hearth400)
                .background(Color.accentDefault)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                .frame(maxWidth: .infinity, alignment: .trailing)
        }
    }

    private var surfacedSection: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            Text("mentioned")
                .font(.hearthCaptionMono).foregroundColor(.inkMuted)
            ForEach(coordinator.surfaced) { ref in
                if ref.kind == "library", let item = contentVM.articleData(ref.id) {
                    NavigationLink(value: ArticleRoute(id: item.id)) {
                        LibraryItemCard(item: item)
                    }
                    .buttonStyle(.plain)
                } else if ref.kind == "community", let post = contentVM.postData(ref.id) {
                    NavigationLink(value: PostRoute(id: post.id)) {
                        CommunityPostCard(post: post)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(.top, .hearth500)
    }

    private func stateLabel(_ state: ElevenLabs.AgentState) -> String {
        switch state {
        case .listening: return "listening…"
        case .thinking:  return "thinking…"
        case .speaking:  return "speaking…"
        }
    }

    private var muteBar: some View {
        Button {
            Task { await coordinator.toggleMute() }
        } label: {
            Image(systemName: conversation.isMuted ? "mic.slash.fill" : "mic.fill")
                .font(.system(size: 24))
                .foregroundColor(conversation.isMuted ? .inkMuted : .accentDefault)
                .frame(width: 64, height: 64)
                .background(Circle().fill(Color.bgElevated))
                .contentShape(Circle())
        }
        .accessibilityLabel(conversation.isMuted ? "Unmute" : "Mute")
        .accessibilityValue(conversation.isMuted ? "Muted" : "")
        .padding(.vertical, .hearth500)
    }
}

// MARK: - Streaming (typewriter) text

/// Reveals `text` progressively to mimic the text-chat's token streaming. Voice
/// transcripts arrive whole-turn from ElevenLabs (no per-token event in voice
/// mode), so we type them out client-side. Each agent bubble gets its own
/// instance (keyed by message id), so only the in-progress turn animates; prior
/// turns render fully. Pace (~22 cps) roughly tracks the spoken audio.
private struct StreamingText: View {
    let text: String
    /// Spoken-char count from audio alignment, or nil if unavailable. When
    /// present the reveal tracks the actual speech; when nil it falls back to a
    /// fixed-rate typewriter.
    var spokenProgress: () -> Int? = { nil }
    var fallbackCPS: Double = 22   // typewriter rate when no alignment
    var floorCPS: Double = 9       // guarantees completion when alignment leads/undershoots

    @State private var shown = 0
    @State private var task: Task<Void, Never>?

    var body: some View {
        Text(String(text.prefix(shown)))
            .onAppear { start() }
            .onChange(of: text) { _, _ in start() }
            .onDisappear { task?.cancel() }
    }

    private func start() {
        task?.cancel()
        if shown > text.count { shown = text.count }   // text shrank (correction)
        guard shown < text.count else { return }
        let begin = Date()
        task = Task { @MainActor in
            while shown < text.count {
                let elapsed = Date().timeIntervalSince(begin)
                let target: Int
                if let spoken = spokenProgress() {
                    // Alignment leads; the floor guarantees completion even if the
                    // alignment char-count undershoots the message length.
                    target = max(spoken, Int(elapsed * floorCPS))
                } else {
                    target = Int(elapsed * fallbackCPS)   // pure typewriter
                }
                shown = max(shown, min(target, text.count))  // monotonic
                if shown >= text.count { break }
                try? await Task.sleep(nanoseconds: 30_000_000)  // 30ms tick
                if Task.isCancelled { return }
            }
            shown = text.count
        }
    }
}
