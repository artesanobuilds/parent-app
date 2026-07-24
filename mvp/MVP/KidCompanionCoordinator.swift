import Combine
import ElevenLabs
import Foundation

/// Per-surface owner of the kid-companion phase machine.
///
/// The companion surface is always in exactly ONE of four phases; every
/// failure path lands in a deliberate phase — there is no dead end and no
/// window where two implementations are interactive at once:
///
///   .connecting            "calling your companion…" (read-only, no input)
///   .voiceLive(conv)       ElevenLabs ConvAI voice session (the product)
///   .textFallback(reason)  quiet text-only chat over /kid-chat SSE
///   .crisisLocked          frozen safety surface (no input, no retry)
///
/// Voice lifecycle is delegated to `KidVoiceSessionManager` (process-wide,
/// owns the audio engine); this object decides *what the kid sees*.
@MainActor
final class KidCompanionCoordinator: ObservableObject {

    enum FallbackReason {
        case micDenied
        case connectFailed
        case voiceEnded
    }

    enum CompanionPhase {
        case connecting
        case voiceLive(Conversation)
        case textFallback(FallbackReason)
        case crisisLocked
    }

    @Published private(set) var phase: CompanionPhase = .connecting

    /// Smoothed mic input level (0…1) driving the listening orb. Republished
    /// from the SDK's `onVadScore` callback (which is raw + off-main); see
    /// `ingestVadScore`. Only meaningful while voice-live and listening.
    @Published private(set) var inputLevel: Double = 0

    let kid: KidAgentConfig
    let vm: KidChatViewModel

    private let manager = KidVoiceSessionManager.shared
    private var voiceEndCancellable: AnyCancellable?
    private var handlingVoiceEnd = false
    /// Paces the voice transcript's reveal against the spoken audio (shared with
    /// the parent surface). Voice-only: the text fallback has real SSE token
    /// streaming and never consults this. Not `@Published` — the bubble polls it
    /// on its own tick rather than re-rendering the whole surface.
    private let reveal = VoiceRevealEngine()
    /// Customer-perspective voice metrics (reply latency, interruptions, how the
    /// session ended). Owned here because this object owns the conversation.
    private let telemetry = VoiceTurnTelemetry(surface: .kid)

    // Listening-orb level tuning. Floor ignores room noise; ceil saturates so a
    // shout doesn't max harder; alpha ≈ 0.2s response at typical VAD cadence.
    private let vadFloor = 0.10
    private let vadCeil = 0.85
    private let emaAlpha = 0.25

    init(userID: String, baseURL: URL, kid: KidAgentConfig) {
        self.kid = kid
        self.vm = KidChatViewModel(userID: userID, baseURL: baseURL, kid: kid)
        // Text mode: backend emits `frozen` when the agent is crisis-locked.
        vm.onFrozen = { [weak self] _ in
            self?.phase = .crisisLocked
        }
    }

    // MARK: - Lifecycle

    func start() async {
        phase = .connecting
        await vm.loadHistory()

        let service = vm.service
        let kidName = kid.kidName
        let outcome = await manager.connect(
            surface: .kid,
            onVadScore: { [weak self] score in
                // onVadScore is @Sendable / off-main — hop to the actor.
                Task { @MainActor in self?.ingestVadScore(score) }
            },
            onInterruption: { [weak self] in
                Task { @MainActor in self?.telemetry.noteInterruption() }
            },
            tokenProvider: { try await service.voiceConvAIToken(kidName: kidName) }
        )
        switch outcome {
        case .connected(let conversation):
            observeVoiceEnd(of: conversation)
            reveal.observe(conversation)
            telemetry.observe(conversation)
            phase = .voiceLive(conversation)
        case .crisisLocked:
            phase = .crisisLocked
        case .consentRequired(let version):
            // Consent is normally collected upstream (ReviewLetterView → ConsentView)
            // before this surface is reachable; this only fires if the agreement
            // version bumped mid-session. Degrade to text rather than mislabel it
            // as a crisis lock — the parent re-accepts via the consent gate.
            dlog("[companion] voice consent_required (version \(version)) → text fallback")
            enterTextFallback(.connectFailed)
        case .micPermissionDenied:
            enterTextFallback(.micDenied)
        case .failed(let why):
            dlog("[companion] voice unavailable → text fallback: \(why)")
            enterTextFallback(.connectFailed)
        }
    }

    /// Called from the exit-confirm path. Tears down the voice session fully
    /// (and the audio engine with it) BEFORE the surface goes away, so an
    /// immediate re-entry starts from a clean engine.
    func exit() async {
        voiceEndCancellable = nil
        inputLevel = 0
        reveal.reset()
        // The kid closed the surface on their own terms — not a fallback.
        // Idempotent: `handleVoiceSessionEnd` may already have closed it out.
        telemetry.end(fellBackToText: false)
        await manager.teardown()
    }

    // MARK: - Transcript reveal

    /// How much of the agent's current turn has actually been spoken. Read by
    /// the live voice bubble's `StreamingText` so the transcript appears in step
    /// with the voice instead of popping in whole. See `VoiceRevealEngine`.
    func spokenProgress() -> SpokenProgress { reveal.progress() }

    // MARK: - Voice phase

    private var liveConversation: Conversation? {
        if case .voiceLive(let c) = phase { return c } else { return nil }
    }

    /// Smooth the raw VAD score into `inputLevel`. Gated to only react while the
    /// session is actually listening and unmuted; otherwise the level decays to
    /// 0 so the orb settles. EMA absorbs the irregular callback cadence.
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

    /// Toggle the user's microphone mute. The surface reads the resulting state
    /// from `conversation.isMuted` (single source of truth).
    func toggleMute() async {
        guard case .voiceLive(let conversation) = phase else { return }
        do {
            try await conversation.toggleMute()
        } catch {
            print("[companion] toggleMute failed: \(error)")
        }
    }

    /// Typed input while in voice mode: the agent replies with audio + a
    /// transcript append. The SDK appends the user turn to
    /// `conversation.messages` itself — no local echo needed.
    func sendVoiceText(_ text: String) async {
        guard case .voiceLive(let conversation) = phase else { return }
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        do {
            try await conversation.sendMessage(trimmed)
        } catch {
            print("[companion] sendMessage failed: \(error)")
        }
    }

    private func observeVoiceEnd(of conversation: Conversation) {
        voiceEndCancellable = conversation.$state.sink { [weak self] state in
            switch state {
            case .ended, .error:
                Task { await self?.handleVoiceSessionEnd() }
            default:
                break
            }
        }
    }

    /// The voice session ended without the parent exiting (network drop,
    /// ElevenLabs end_call, server error). Crisis end_call and benign drops
    /// look identical from the client, so ask the backend which it was.
    private func handleVoiceSessionEnd() async {
        guard !handlingVoiceEnd else { return }
        handlingVoiceEnd = true
        defer { handlingVoiceEnd = false }

        voiceEndCancellable = nil
        inputLevel = 0
        reveal.reset()
        await manager.teardown()
        // Refresh history so the just-finished voice turns appear in fallback.
        await vm.loadHistory()

        if let status = try? await vm.service.kidAgentStatus(kidName: kid.kidName),
           status.crisisLocked {
            telemetry.end(fellBackToText: false)   // frozen surface, not text
            phase = .crisisLocked
        } else {
            // Voice dropped out from under the kid and they landed in text —
            // the single most important negative signal this surface has.
            telemetry.end(fellBackToText: true)
            enterTextFallback(.voiceEnded)
        }
    }

    // MARK: - Text fallback

    private func enterTextFallback(_ reason: FallbackReason) {
        phase = .textFallback(reason)
        // First meeting in text mode: greet with a quiet text bubble (no audio).
        if vm.messages.isEmpty {
            let opener = kid.invariants.personaExamples.first
                ?? "Hi \(kid.kidName)! I'm \(kid.invariants.agentDisplayName). What's on your mind?"
            vm.appendAssistantLocal(opener)
        }
    }
}
