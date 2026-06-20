import Combine
import ElevenLabs
import Foundation

/// Per-surface owner of the PARENT voice call. Simpler than the kid coordinator
/// (no crisis/fallback-to-text state machine — the parent always has the text
/// chat to return to), but adds the client-tool → on-screen-card bridge:
/// the agent fires `show_article` / `show_community_post` client tools, which we
/// turn into a list of surfaced content the view renders as cards.
@MainActor
final class ParentCompanionCoordinator: ObservableObject {

    enum Phase {
        case connecting
        case voiceLive(Conversation)
        case failed(String)
    }

    struct SurfacedRef: Identifiable, Equatable {
        let id: String        // content id
        let kind: String      // "library" | "community"
    }

    @Published private(set) var phase: Phase = .connecting
    @Published private(set) var inputLevel: Double = 0
    /// Content the agent surfaced during the call, in order, deduped.
    @Published private(set) var surfaced: [SurfacedRef] = []

    private let service: KidAgentService
    private let manager = KidVoiceSessionManager.shared
    private var toolTask: Task<Void, Never>?
    private var handledToolCallIds = Set<String>()

    // VAD → orb tuning (same as the kid coordinator).
    private let vadFloor = 0.10
    private let vadCeil = 0.85
    private let emaAlpha = 0.25

    init(service: KidAgentService) {
        self.service = service
    }

    // MARK: - Lifecycle

    func start() async {
        phase = .connecting
        let svc = service
        let outcome = await manager.connect(
            onVadScore: { [weak self] score in
                Task { @MainActor in self?.ingestVadScore(score) }
            },
            tokenProvider: { try await svc.voiceParentConvAIToken() }
        )
        switch outcome {
        case .connected(let conversation):
            observeToolCalls(conversation)
            observeAudioAlignment(conversation)
            phase = .voiceLive(conversation)
        case .micPermissionDenied:
            phase = .failed("Microphone access is needed to talk. Enable it in Settings, then try again.")
        case .crisisLocked:
            // Not a parent concept; treat as a generic failure.
            phase = .failed("Voice isn't available right now.")
        case .consentRequired:
            // The parent coach is not consent-gated (see voice_parent_convai_token);
            // if this ever fires it's a backend regression — surface it honestly.
            dlog("[parent-voice] unexpected consent_required on parent coach")
            phase = .failed("Voice isn't available right now.")
        case .failed(let why):
            dlog("[parent-voice] connect failed: \(why)")
            phase = .failed("Couldn't start the call. Check your connection and try again.")
        }
    }

    func exit() async {
        toolTask?.cancel()
        toolTask = nil
        audioCancellable = nil
        inputLevel = 0
        spokenChars = 0
        audioTurnEventId = nil
        await manager.teardown()
    }

    // MARK: - Audio alignment (drives real, speech-synced transcript reveal)

    /// Cumulative count of characters ElevenLabs has reported as SPOKEN for the
    /// current agent turn, from per-chunk audio alignment. The transcript reveal
    /// tracks this so text appears in lockstep with the voice. Resets per turn.
    @Published private(set) var spokenChars: Int = 0
    /// True once any alignment has arrived this session. If it stays false, the
    /// transcript reveal falls back to a fixed-rate typewriter (alignment isn't
    /// delivered over WebRTC for this agent).
    private(set) var alignmentArrived = false

    private var audioTurnEventId: Int?
    private var audioCancellable: AnyCancellable?

    /// Spoken progress for the active turn, or nil if alignment isn't available
    /// (→ typewriter fallback). Read by `StreamingText`.
    func spokenProgress() -> Int? { alignmentArrived ? spokenChars : nil }

    private func observeAudioAlignment(_ conversation: Conversation) {
        audioCancellable = conversation.$latestAudioEvent.sink { [weak self] event in
            guard let event, let alignment = event.alignment else { return }
            Task { @MainActor [weak self] in
                guard let self else { return }
                if self.audioTurnEventId != event.eventId {
                    self.audioTurnEventId = event.eventId   // new agent turn
                    self.spokenChars = 0
                }
                if !self.alignmentArrived {
                    self.alignmentArrived = true
                    print("[parent-voice] ✅ audio alignment available — transcript will sync to speech")
                }
                self.spokenChars += alignment.chars.count
            }
        }
    }

    // MARK: - Voice controls

    private var liveConversation: Conversation? {
        if case .voiceLive(let c) = phase { return c } else { return nil }
    }

    func toggleMute() async {
        guard case .voiceLive(let conversation) = phase else { return }
        do { try await conversation.toggleMute() }
        catch { print("[parent-voice] toggleMute failed: \(error)") }
    }

    func ingestVadScore(_ raw: Double) {
        let gateOpen = liveConversation?.agentState == .listening
            && liveConversation?.isMuted == false
        let target: Double
        if gateOpen {
            let clamped = min(max(raw, vadFloor), vadCeil)
            target = (clamped - vadFloor) / (vadCeil - vadFloor)
        } else {
            target = 0
        }
        inputLevel += emaAlpha * (target - inputLevel)
    }

    // MARK: - Client tools → surfaced cards

    private func observeToolCalls(_ conversation: Conversation) {
        toolTask = Task { [weak self] in
            for await calls in conversation.$pendingToolCalls.values {
                guard let self else { return }
                for call in calls where !self.handledToolCallIds.contains(call.toolCallId) {
                    await self.handle(call, on: conversation)
                }
            }
        }
    }

    private func handle(_ call: ClientToolCallEvent, on conversation: Conversation) async {
        handledToolCallIds.insert(call.toolCallId)

        let kind: String?
        switch call.toolName {
        case "show_article":        kind = "library"
        case "show_community_post": kind = "community"
        default:                    kind = nil
        }

        guard let kind else {
            try? await conversation.sendToolResult(
                for: call.toolCallId, result: "unknown tool", isError: true)
            return
        }

        let id = (try? call.getParameters()["id"]) as? String
        if let id, !id.isEmpty, !surfaced.contains(where: { $0.id == id }) {
            surfaced.append(SurfacedRef(id: id, kind: kind))
        }
        // Display-only tool: acknowledge so the agent keeps talking.
        try? await conversation.sendToolResult(for: call.toolCallId, result: ["displayed": true])
    }
}
