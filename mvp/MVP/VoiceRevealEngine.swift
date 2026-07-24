import Combine
import ElevenLabs
import Foundation

/// Paces the on-screen reveal of an agent turn's transcript so the text tracks
/// the voice. Shared by BOTH voice surfaces (parent coach + kid companion);
/// `StreamingText` is the consumer.
///
/// Why this exists: ElevenLabs delivers `agent_response` as the COMPLETE turn
/// text in a single event (alongside the first audio chunk), and the SDK upserts
/// it whole into `conversation.messages`. A plain `Text` therefore pops the
/// entire paragraph in while the audio is still playing.
///
/// The obvious fix — character-level audio alignment — is not actually available
/// to us: over the WebRTC transport the SDK never receives `audio` client events
/// (audio rides the LiveKit track directly), so `latestAudioEvent` stays nil in
/// practice. We still listen for it, because it is the only exact source if it
/// ever starts arriving, but the path that runs every day is the estimate below.
///
/// The estimate has two halves, and both matter:
///
///   1. STATE GATING — the reveal clock only ticks while `agentState == .speaking`.
///      The old fixed 22 cps typewriter ran on wall-clock time, so it sprinted
///      ahead through thinking pauses, tool calls and silences and finished long
///      before the voice did. Counting only speaking time keeps them together.
///   2. ADAPTIVE PACING — at the end of each turn we know exactly how many
///      characters were spoken and how long the speaking took, so we calibrate
///      chars/sec from the agent's own delivery (its voice, its speed setting,
///      kid vs parent persona) instead of one hardcoded guess. EMA-smoothed
///      across turns, clamped to a sane band, seeded at the previous 22 cps.
///      Per-session only — nothing is persisted.
@MainActor
final class VoiceRevealEngine: ObservableObject {

    /// Current calibrated reveal rate. Published mostly for debugging/inspection;
    /// `StreamingText` polls `progress()` rather than observing this.
    @Published private(set) var charsPerSecond: Double = 22

    // Pacing band. Human speech lands around 13–18 cps; the band is wide enough
    // to absorb a fast/slow voice setting but narrow enough that one bad sample
    // can't make the transcript nonsense.
    private let seedCPS: Double = 22
    private let minCPS: Double = 10
    private let maxCPS: Double = 30
    private let emaAlpha: Double = 0.35
    /// Samples outside this band are rejected outright rather than smoothed in:
    /// an interruption can end a turn before `agent_response_correction` has
    /// truncated the text, which would otherwise read as a wildly fast turn.
    private let sampleAcceptRange: ClosedRange<Double> = 6...45

    // MARK: - Turn state

    /// Cumulative seconds of `.speaking` for the turn in flight.
    private var speakingAccrued: TimeInterval = 0
    private var speakingSince: Date?
    /// True once `.speaking` has been seen for this turn. Until then the view is
    /// told the gate has no opinion, so it can run its own clock instead of
    /// waiting forever on a state signal that might never come.
    private var observedSpeechThisTurn = false
    /// Set when we leave `.speaking` — the audio is done, so the view lands the
    /// remaining text immediately instead of typing into silence.
    private var turnFinished = false
    /// Last agent message we've seen, so a new one can open a new turn.
    private var lastAgentMessageID: Message.ID?

    // MARK: - Alignment (opportunistic; see the note above)

    private var alignmentArrived = false
    private var alignmentChars = 0
    private var alignmentEventId: Int?
    private var alignmentLogged = 0

    private weak var conversation: Conversation?
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Lifecycle

    /// Start tracking a live conversation. Safe to call again on reconnect —
    /// it resets first.
    func observe(_ conversation: Conversation) {
        reset()
        self.conversation = conversation

        conversation.$latestAudioEvent
            .sink { [weak self] event in
                guard let event else { return }
                Task { @MainActor [weak self] in self?.ingestAudioEvent(event) }
            }
            .store(in: &cancellables)

        conversation.$agentState
            .sink { [weak self] state in
                Task { @MainActor [weak self] in self?.ingestAgentState(state) }
            }
            .store(in: &cancellables)

        // A new agent message IS a new turn — the truest boundary we get, and it
        // usually lands a beat before `.speaking`. Without it a turn's bookkeeping
        // could still read "finished" while the next bubble is already on screen.
        conversation.$messages
            .sink { [weak self] messages in
                let latest = messages.last(where: { $0.role == .agent })?.id
                Task { @MainActor [weak self] in self?.ingestAgentMessage(latest) }
            }
            .store(in: &cancellables)
    }

    func reset() {
        cancellables.removeAll()
        conversation = nil
        speakingAccrued = 0
        speakingSince = nil
        observedSpeechThisTurn = false
        turnFinished = false
        lastAgentMessageID = nil
        alignmentArrived = false
        alignmentChars = 0
        alignmentEventId = nil
        alignmentLogged = 0
        charsPerSecond = seedCPS   // calibration is per-session
    }

    // MARK: - Reveal budget (read by StreamingText, ~30ms cadence)

    func progress() -> SpokenProgress {
        SpokenProgress(
            chars: alignmentArrived ? alignmentChars : Int(speakingSeconds * charsPerSecond),
            observedSpeech: observedSpeechThisTurn,
            finished: turnFinished && observedSpeechThisTurn
        )
    }

    private var speakingSeconds: TimeInterval {
        speakingAccrued + (speakingSince.map { Date().timeIntervalSince($0) } ?? 0)
    }

    // MARK: - Agent state → speaking clock

    private func ingestAgentState(_ state: ElevenLabs.AgentState) {
        if state == .speaking {
            guard speakingSince == nil else { return }
            // Turn boundaries belong to the message stream, not to this state: if
            // we're speaking again without a new agent message, it's the SAME turn
            // resuming after a thinking/tool pause. Keep its accrued clock so the
            // reveal picks up where it stopped instead of restarting behind itself.
            turnFinished = false
            speakingSince = Date()
            observedSpeechThisTurn = true
        } else if let since = speakingSince {
            speakingAccrued += Date().timeIntervalSince(since)
            speakingSince = nil
            endTurn()
        }
    }

    /// A new agent message means the next turn's text is on screen. Note the
    /// interruption path does NOT come through here: `agent_response_correction`
    /// rewrites the message content in place, keeping its id.
    private func ingestAgentMessage(_ id: Message.ID?) {
        guard let id, id != lastAgentMessageID else { return }
        lastAgentMessageID = id
        beginTurn()
    }

    private func beginTurn() {
        speakingAccrued = 0
        turnFinished = false
        alignmentChars = 0
        // If audio is already flowing when the turn's text lands, keep the gate
        // open and just restart its clock here — dropping to `observedSpeech =
        // false` would hand the whole turn to the ungated wall clock.
        if speakingSince != nil {
            speakingSince = Date()
            observedSpeechThisTurn = true
        } else {
            observedSpeechThisTurn = false
        }
    }

    private func endTurn() {
        turnFinished = true
        calibrate()
    }

    /// Learn this agent's real delivery rate from the turn that just played.
    /// Read the transcript AFTER the turn ends so an interruption's
    /// `agent_response_correction` (which rewrites the message to the text that
    /// actually played) is already reflected.
    private func calibrate() {
        guard speakingAccrued >= 1.0 else { return }   // too short to mean anything
        guard let spoken = conversation?.messages.last(where: { $0.role == .agent })?.content,
              spoken.count >= 25 else { return }
        let sample = Double(spoken.count) / speakingAccrued
        guard sampleAcceptRange.contains(sample) else {
            dlog("[voice-reveal] rejected pacing sample \(String(format: "%.1f", sample)) cps")
            return
        }
        let blended = charsPerSecond + emaAlpha * (sample - charsPerSecond)
        charsPerSecond = min(max(blended, minCPS), maxCPS)
        dlog("[voice-reveal] pacing \(String(format: "%.1f", sample)) cps sample → \(String(format: "%.1f", charsPerSecond)) cps")
    }

    // MARK: - Audio alignment

    private func ingestAudioEvent(_ event: AudioEvent) {
        guard let alignment = event.alignment else { return }
        if alignmentEventId != event.eventId {
            alignmentEventId = event.eventId   // new agent turn (or chunk — see below)
            alignmentChars = 0
        }
        if !alignmentArrived {
            alignmentArrived = true
            print("[voice-reveal] ✅ audio alignment available — transcript will sync to speech")
        }
        // We have never seen alignment over WebRTC, so we don't actually know
        // whether `eventId` is per-turn or per-chunk. Log the first few pairs: if
        // the id changes every event, the reset above is wrong and alignmentChars
        // needs to accumulate across ids instead.
        if alignmentLogged < 6 {
            alignmentLogged += 1
            dlog("[voice-reveal] alignment eventId=\(event.eventId) chars=\(alignment.chars.count)")
        }
        alignmentChars += alignment.chars.count
    }
}
