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
    /// Paces the transcript reveal against the spoken audio (shared with the kid
    /// surface). Not `@Published` — the view polls it on its own tick.
    private let reveal = VoiceRevealEngine()
    /// Customer-perspective voice metrics (reply latency, interruptions, how the
    /// call ended). Owned here because this object owns the conversation.
    private let telemetry = VoiceTurnTelemetry(surface: .parent)

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
            surface: .parent,
            onVadScore: { [weak self] score in
                Task { @MainActor in self?.ingestVadScore(score) }
            },
            onInterruption: { [weak self] in
                Task { @MainActor in self?.telemetry.noteInterruption() }
            },
            tokenProvider: { try await svc.voiceParentConvAIToken() }
        )
        switch outcome {
        case .connected(let conversation):
            observeToolCalls(conversation)
            reveal.observe(conversation)
            telemetry.observe(conversation)
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
        inputLevel = 0
        reveal.reset()
        // The parent surface has no mid-call fallback: ending the call returns to
        // the coach's text chat, which is where they came from. Always false.
        telemetry.end(fellBackToText: false)
        await manager.teardown()
    }

    // MARK: - Transcript reveal

    /// How much of the agent's current turn has actually been spoken. Read by
    /// `StreamingText` so the transcript appears in step with the voice rather
    /// than popping in whole. See `VoiceRevealEngine`.
    func spokenProgress() -> SpokenProgress { reveal.progress() }

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
