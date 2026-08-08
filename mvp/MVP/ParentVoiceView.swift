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
                            bubble(role: msg.role,
                                   text: msg.content,
                                   isLive: msg.id == liveAgentMessageID)
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

    /// The turn currently being spoken — the only bubble that animates. Older
    /// agent bubbles render whole so they never re-type on a view rebuild.
    private var liveAgentMessageID: Message.ID? {
        conversation.messages.last(where: { $0.role == .agent })?.id
    }

    @ViewBuilder
    private func bubble(role: Message.Role, text: String, isLive: Bool) -> some View {
        if role == .agent {
            // Voice transcripts arrive whole-turn (ElevenLabs doesn't stream them
            // in voice mode), so we type them out client-side to feel like the
            // text chat — paced to track the spoken audio.
            StreamingText(text: text,
                          isActive: isLive,
                          spokenProgress: { coordinator.spokenProgress() })
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
                }
                // `ref.kind == "community"` used to render a board post here.
                // The board is retired (beta-v1 sprint 2) and the coach no
                // longer surfaces those refs; an old one simply renders nothing.
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

