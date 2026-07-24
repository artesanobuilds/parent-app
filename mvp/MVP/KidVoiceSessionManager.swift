import AVFoundation
import Combine
import ElevenLabs
import Foundation
import LiveKit

/// Which product surface a voice session belongs to. The manager is process-wide
/// and shared by both, so the caller must SAY which it is — the manager can only
/// see a `tokenProvider` closure and would have to guess.
enum VoiceSurface: String {
    case kid
    case parent
}

/// Process-wide owner of the ElevenLabs ConvAI session lifecycle.
///
/// LiveKit's audio engine is a process singleton, so session lifecycle must be
/// managed at process scope too — a per-view object cannot guarantee that the
/// previous session finished releasing the engine before the next one starts.
/// This manager is the ONLY code allowed to call `ElevenLabs.startConversation`,
/// `endConversation`, or `AudioManager.setEngineAvailability`.
///
/// Why each piece exists:
/// - **Teardown serialization**: `connect()` awaits any in-flight teardown.
///   Without this, a fast exit→re-enter races the old room's mic release and
///   the new session's mic publish times out (the re-entry bug).
/// - **Engine availability reset**: the ElevenLabs SDK never stops the audio
///   engine on disconnect (`ConversationAudioManager.cleanup()` only removes
///   callbacks), so we hard-stop it with `.none` after teardown and re-enable
///   with `.default` before connect.
/// - **Mic permission gate**: `setEngineAvailability(.default)` BLOCKS the
///   calling thread while mic permission is undetermined (LiveKit issue #815),
///   so permission is resolved before any engine-availability call.
/// - **Fresh token per attempt**: a ConvAI token is scoped to one conversation;
///   retrying with the same token rejoins the same dying room.
@MainActor
final class KidVoiceSessionManager {

    static let shared = KidVoiceSessionManager()
    private init() {}

    enum ConnectOutcome {
        case connected(Conversation)
        case crisisLocked
        case consentRequired(String)   // agreement version the user must accept
        case micPermissionDenied
        case failed(String)
    }

    private(set) var activeConversation: Conversation?
    private var teardownTask: Task<Void, Never>?

    private static let watchdogNanos: UInt64 = 15_000_000_000
    private static let micRetryDelayNanos: UInt64 = 1_000_000_000

    // Connection resilience: ConvAI/LiveKit connects occasionally time out on a
    // transient ElevenLabs/network blip (the server is never reached). Retry with
    // backoff before surfacing a hard failure. Terminal outcomes (crisis,
    // consent) are NOT retried.
    private static let maxConnectAttempts = 3
    /// Backoff before the next connect attempt: ~0.8s, then ~1.8s.
    private static func connectBackoffNanos(afterAttempt n: Int) -> UInt64 {
        n <= 1 ? 800_000_000 : 1_800_000_000
    }

    // MARK: - Connect

    /// Connect a ConvAI voice session. The token is fetched via `tokenProvider`
    /// so both the kid and parent surfaces reuse this single process-wide owner
    /// (only one LiveKit audio session can exist at a time). The kid provider may
    /// throw `voiceFallback(.crisis)` → `.crisisLocked`; the parent provider won't.
    ///
    /// `surface` is only used to label the connect analytics — see the note on
    /// `VoiceSurface` for why it is passed in rather than inferred.
    func connect(
        surface: VoiceSurface,
        onVadScore: (@Sendable (Double) -> Void)? = nil,
        onInterruption: (@Sendable () -> Void)? = nil,
        tokenProvider: @escaping () async throws -> KidAgentService.ConvAITokenResponse
    ) async -> ConnectOutcome {
        // Everything from here to `.connected` is time the user spends staring at
        // "calling your companion…", so the clock starts at the very top —
        // including the teardown wait, which is part of what they feel.
        let connectStartedAt = Date()

        // Serialize: never start while a previous session is releasing the engine.
        await teardownTask?.value
        if activeConversation != nil {
            await teardown()
        }

        // Attempt 1's token is fetched CONCURRENTLY with the mic-permission
        // resolution and the engine bring-up below: the token is a full round-trip
        // to our backend and neither of those steps depends on it, so serializing
        // them just bolted that round-trip onto every connect. Attempts 2 and 3
        // still fetch inline — a ConvAI token is scoped to ONE conversation, so a
        // retry that reuses the first token rejoins the same dying room.
        //
        // Accepted trade-off: a session whose mic permission is then denied can
        // mint a token nobody uses (one extra `session_token_issued` cost marker,
        // and the agent's greeting is appended server-side — already
        // anti-stacking-guarded, so it does not stack up). We cancel the prefetch
        // on denial to keep that window as small as possible.
        let prefetch = Task { () -> (KidAgentService.ConvAITokenResponse, TimeInterval) in
            let started = Date()
            let response = try await tokenProvider()
            return (response, Date().timeIntervalSince(started))
        }

        // Resolve mic permission BEFORE touching engine availability (see #815).
        switch AVAudioApplication.shared.recordPermission {
        case .undetermined:
            let granted = await AVAudioApplication.requestRecordPermission()
            guard granted else {
                prefetch.cancel()
                Self.reportFailure(surface, stage: "mic", reason: "permission_denied")
                return .micPermissionDenied
            }
        case .denied:
            prefetch.cancel()
            Self.reportFailure(surface, stage: "mic", reason: "permission_denied")
            return .micPermissionDenied
        case .granted:
            break
        @unknown default:
            break
        }

        // Permission is now determined — safe to enable the engine.
        do { try AudioManager.shared.setEngineAvailability(.default) }
        catch { dlog("[voice-mgr] setEngineAvailability(.default) failed: \(error)") }

        var lastError = "unknown"
        // Round-trip of the token fetch that produced the token we ended up using.
        var tokenMs = 0
        let maxAttempts = Self.maxConnectAttempts
        for attempt in 1...maxAttempts {
            // Fresh token every attempt — tokens are conversation-scoped.
            // Attempt 1 consumes the prefetch started above; it usually resolved
            // while the permission/engine work was happening, so this await is
            // free.
            let tokenResponse: KidAgentService.ConvAITokenResponse
            do {
                if attempt == 1 {
                    let (response, elapsed) = try await prefetch.value
                    tokenResponse = response
                    tokenMs = Int(elapsed * 1000)
                } else {
                    let started = Date()
                    tokenResponse = try await tokenProvider()
                    tokenMs = Int(Date().timeIntervalSince(started) * 1000)
                }
            } catch KidAgentServiceError.voiceFallback(reason: .crisis, status: _) {
                // Terminal — never retry. Still reported: from the kid's side this
                // is "I tapped my companion and got no voice", which is exactly
                // what the customer-experience metric is meant to count.
                Self.reportFailure(surface, stage: "token", reason: "crisis_locked")
                return .crisisLocked
            } catch KidAgentServiceError.consentRequired(let version) {
                Self.reportFailure(surface, stage: "token", reason: "consent_required")
                return .consentRequired(version) // terminal — never retry
            } catch {
                // Token fetch hits OUR backend — a failure here is our server/auth
                // or the network to us, NOT ElevenLabs. Transient, so retry.
                lastError = "Token fetch from our backend failed: \(error.localizedDescription). "
                    + "This is our server/auth or the network to it, NOT ElevenLabs."
                dlog("[voice-mgr] ⚠️ \(lastError) (attempt \(attempt)/\(maxAttempts))")
                if attempt < maxAttempts {
                    try? await Task.sleep(nanoseconds: Self.connectBackoffNanos(afterAttempt: attempt))
                    continue
                }
                Self.reportFailure(surface, stage: "token", reason: "token_fetch_failed")
                return .failed(lastError)
            }
            guard let token = tokenResponse.signedURL else {
                Self.reportFailure(surface, stage: "token", reason: "no_signed_url")
                return .failed("token endpoint returned no signed_url")
            }

            do {
                let conv = try await startWithWatchdog(
                    token: token,
                    response: tokenResponse,
                    onVadScore: onVadScore,
                    onInterruption: onInterruption
                )
                activeConversation = conv
                dlog("[voice-mgr] ✅ connected (attempt \(attempt)); state=\(conv.state)")
                Analytics.capture("voice_session_connected", [
                    "surface": surface.rawValue,
                    "token_ms": tokenMs,
                    "connect_ms": Int(Date().timeIntervalSince(connectStartedAt) * 1000),
                    "attempts": attempt,
                ])
                return .connected(conv)
            } catch let err as ConversationError {
                lastError = err.localizedDescription
                // Mic publish failure: full engine reset before the next try.
                if case .microphoneToggleFailed = err, attempt == 1 {
                    dlog("[voice-mgr] mic publish failed (attempt 1) — full engine reset, retrying…")
                    await resetEngine()
                    try? await Task.sleep(nanoseconds: Self.micRetryDelayNanos)
                    continue
                }
                // Connection/timeout on the ElevenLabs leg — the token already
                // succeeded, so this is the voice service or network, not us.
                lastError = Self.explainElevenLabsConnectFailure(err)
                dlog("[voice-mgr] ❌ \(lastError) (attempt \(attempt)/\(maxAttempts))")
                if attempt < maxAttempts {
                    try? await Task.sleep(nanoseconds: Self.connectBackoffNanos(afterAttempt: attempt))
                    continue
                }
                Self.reportFailure(surface, stage: Self.failureStage(err), reason: Self.failureReason(err))
                return .failed(lastError)
            } catch {
                lastError = Self.explainElevenLabsConnectFailure(error)
                dlog("[voice-mgr] ❌ \(lastError) (attempt \(attempt)/\(maxAttempts))")
                if attempt < maxAttempts {
                    try? await Task.sleep(nanoseconds: Self.connectBackoffNanos(afterAttempt: attempt))
                    continue
                }
                Self.reportFailure(surface, stage: "connect", reason: "connect_failed")
                return .failed(lastError)
            }
        }
        return .failed(lastError)
    }

    // MARK: - Connect analytics

    /// Emit `voice_session_failed`. Deliberately reports a SMALL fixed vocabulary
    /// of stage/reason codes rather than `error.localizedDescription`: the raw
    /// description can carry URLs and server text (privacy) and would explode the
    /// property's cardinality (useless as a metric). The human-readable string
    /// still reaches the debug report via `.failed(lastError)`.
    private static func reportFailure(_ surface: VoiceSurface, stage: String, reason: String) {
        Analytics.capture("voice_session_failed",
                          ["surface": surface.rawValue, "stage": stage, "reason": reason])
    }

    private static func failureStage(_ err: ConversationError) -> String {
        switch err {
        case .agentTimeout:            return "watchdog"   // our 15s watchdog fired
        case .microphoneToggleFailed:  return "mic"
        default:                       return "connect"
        }
    }

    private static func failureReason(_ err: ConversationError) -> String {
        switch err {
        case .agentTimeout:            return "agent_timeout"
        case .microphoneToggleFailed:  return "mic_publish_failed"
        default:                       return "connect_failed"
        }
    }

    // MARK: - Teardown

    /// End the active conversation and hard-stop the audio engine. Idempotent;
    /// safe to call from both the exit-confirm path and `.onDisappear`.
    func teardown() async {
        if let existing = teardownTask {
            await existing.value
            return
        }
        let conv = activeConversation
        activeConversation = nil
        let task = Task {
            await conv?.endConversation()
            // Hard-stop the warm engine the SDK leaves behind; without this the
            // next session's mic publish hangs (acute in the simulator).
            do { try AudioManager.shared.setEngineAvailability(.none) }
            catch { print("[voice-mgr] setEngineAvailability(.none) failed: \(error)") }
        }
        teardownTask = task
        await task.value
        teardownTask = nil
        print("[voice-mgr] teardown complete")
    }

    // MARK: - Internals

    private func resetEngine() async {
        do {
            try AudioManager.shared.setEngineAvailability(.none)
            try AudioManager.shared.setEngineAvailability(.default)
        } catch {
            print("[voice-mgr] engine reset failed: \(error)")
        }
    }

    /// Human explanation for a failure on the ElevenLabs connect leg. By the time
    /// we call `startWithWatchdog` the session token was ALREADY issued by our
    /// backend, so any failure here is the ElevenLabs/LiveKit connection (or the
    /// network to it) — never our server. Spelling that out makes the bundled
    /// debug reports self-explanatory instead of a bare "Timed out".
    private static func explainElevenLabsConnectFailure(_ error: Error) -> String {
        if let convErr = error as? ConversationError, case .agentTimeout = convErr {
            let secs = Int(watchdogNanos / 1_000_000_000)
            return "ElevenLabs voice connection timed out after \(secs)s (voice service unreachable). "
                + "Our backend issued the session token fine — this is an ElevenLabs/LiveKit or "
                + "network issue, NOT our server."
        }
        return "ElevenLabs voice connection failed: \(error.localizedDescription). The session token "
            + "was issued by our backend fine — this is the ElevenLabs/LiveKit leg or the network to "
            + "it, NOT our server."
    }

    private func startWithWatchdog(
        token: String,
        response: KidAgentService.ConvAITokenResponse,
        onVadScore: (@Sendable (Double) -> Void)?,
        onInterruption: (@Sendable () -> Void)?
    ) async throws -> Conversation {
        let config = Self.buildConfig(from: response, onVadScore: onVadScore, onInterruption: onInterruption)
        let connectTask = Task { @MainActor in
            try await ElevenLabs.startConversation(conversationToken: token, config: config)
        }
        let watchdog = Task {
            try? await Task.sleep(nanoseconds: Self.watchdogNanos)
            if !Task.isCancelled { connectTask.cancel() }
        }
        defer { watchdog.cancel() }
        do {
            return try await connectTask.value
        } catch is CancellationError {
            throw ConversationError.agentTimeout
        }
    }

    private static func buildConfig(
        from response: KidAgentService.ConvAITokenResponse,
        onVadScore: (@Sendable (Double) -> Void)? = nil,
        onInterruption: (@Sendable () -> Void)? = nil
    ) -> ConversationConfig {
        let extraBody: [String: String] = {
            guard let raw = response.extraBody else { return [:] }
            var result: [String: String] = [:]
            for (k, v) in raw {
                if let s = v as? String { result[k] = s }
            }
            return result
        }()

        let agentBlock = response.configOverride?["agent"] as? [String: Any]
        let promptBlock = agentBlock?["prompt"] as? [String: Any]

        return ConversationConfig(
            agentOverrides: AgentOverrides(
                prompt: promptBlock?["prompt"] as? String,
                firstMessage: agentBlock?["first_message"] as? String
            ),
            customLlmExtraBody: extraBody,
            // Don't keep the engine warm between sessions: the warm-engine
            // restart is what wedges on re-entry. (Soft layer; the hard stop
            // is setEngineAvailability(.none) in teardown.)
            audioConfiguration: AudioPipelineConfiguration(recordingAlwaysPrepared: false),
            // The only exact interruption signal we get. It is NOT derivable from
            // the published state: an interruption drives `agentState` to
            // `.listening` and only THEN fires this, so a state observer alone
            // would score the truncated turn as a clean one.
            // (Declared before onVadScore in the SDK init — order matters.)
            onInterruption: onInterruption.map { handler in { @Sendable (_: Int) in handler() } },
            // Republished by the coordinator to drive the mic-reactive listening
            // orb. Fires off a non-main thread (@Sendable) at ~10–30/sec.
            // (Declared before agentStateConfiguration in the SDK init — order matters.)
            onVadScore: onVadScore,
            // Required for the SDK to run its AgentStateManager — without it,
            // conversation.agentState never updates past .listening.
            agentStateConfiguration: .default
        )
    }
}

// MARK: - Per-session voice telemetry

/// Customer-perspective measurements for ONE live voice session: how long the
/// agent made the user wait for each reply, whether the transcript reveal had
/// real alignment data to work with, and how the session ended.
///
/// Owned and driven by the two coordinators — they own the conversation, so they
/// own the observation. It lives in this file because both surfaces need exactly
/// the same measurements and this is where the voice plumbing lives; duplicating
/// it per coordinator would guarantee the two definitions drift apart.
///
/// The number that matters is `response_gap_ms`: the silence between the user
/// finishing their turn and the agent's voice starting. That is the wait a kid
/// or parent actually feels, and no server-side timing can see it — the STT
/// endpointing, the LLM and the TTS first-byte all land inside it.
///
/// Nothing here touches transcript text. Only durations, counts and booleans.
@MainActor
final class VoiceTurnTelemetry {

    private let surface: VoiceSurface
    private var cancellables = Set<AnyCancellable>()

    private var sessionStartedAt: Date?
    private var turns = 0
    private var ended = false

    /// Instant the agent stopped listening for the turn in flight (i.e. the user
    /// stopped talking). Nil between turns.
    private var stoppedListeningAt: Date?
    /// Measured for the turn in flight, held until the turn completes so the
    /// interrupted flag can land on the right turn.
    private var pendingGapMs: Int?
    /// `agentState` is a level, not an edge — the transitions are what carry the
    /// meaning, so the previous value has to be kept.
    private var lastState: ElevenLabs.AgentState = .listening
    private var interruptedThisTurn = false
    /// Sticky for the whole session: audio alignment either arrives from
    /// ElevenLabs or it never does (over WebRTC it never has — see
    /// `VoiceRevealEngine`). Tracked so we can prove that from the field rather
    /// than from one developer's device.
    private var alignmentSeen = false
    /// A turn is emitted a beat after speech stops. An interruption drives
    /// `agentState` to `.listening` BEFORE the SDK fires `onInterruption`, so
    /// emitting synchronously would score every interrupted turn as clean.
    private var flushTask: Task<Void, Never>?
    private static let turnFlushDelayNanos: UInt64 = 350_000_000

    init(surface: VoiceSurface) {
        self.surface = surface
    }

    // MARK: - Lifecycle

    /// Start measuring a live conversation. Call once, right after connect.
    func observe(_ conversation: Conversation) {
        cancellables.removeAll()
        sessionStartedAt = Date()

        conversation.$agentState
            .sink { [weak self] state in
                Task { @MainActor [weak self] in self?.ingestAgentState(state) }
            }
            .store(in: &cancellables)

        // Separate subscription from the reveal engine's on purpose: this only
        // records PRESENCE, and must not depend on the reveal's internals.
        conversation.$latestAudioAlignment
            .sink { [weak self] alignment in
                guard alignment != nil else { return }
                Task { @MainActor [weak self] in self?.alignmentSeen = true }
            }
            .store(in: &cancellables)
    }

    /// The user interrupted the agent mid-sentence. Wired from the SDK's
    /// `onInterruption` via `KidVoiceSessionManager.connect`.
    func noteInterruption() {
        interruptedThisTurn = true
    }

    /// Close the session out. Idempotent — the kid surface can reach this from
    /// both the voice-ended handler and `exit()`, and only the first wins.
    /// No-ops entirely if voice never connected: a session that failed to start
    /// is already counted by `voice_session_failed`, and counting it here too
    /// would drag the median duration to zero.
    func end(fellBackToText: Bool) {
        guard !ended, let startedAt = sessionStartedAt else { return }
        ended = true
        flushTask?.cancel()
        flushTask = nil
        emitPendingTurn()          // don't lose the turn that was in flight
        cancellables.removeAll()
        Analytics.capture("voice_session_ended", [
            "surface": surface.rawValue,
            "duration_s": Int(Date().timeIntervalSince(startedAt)),
            "turns": turns,
            "fell_back_to_text": fellBackToText,
        ])
    }

    // MARK: - Turn machine

    /// The agent's state cycle for one exchange is
    /// `.listening` → `.thinking` → `.speaking` → `.listening`, with extra
    /// `.thinking` excursions in the middle of a reply when the agent calls a
    /// tool. Only the two edges that bracket the user's wait are measured.
    private func ingestAgentState(_ state: ElevenLabs.AgentState) {
        let previous = lastState
        guard state != previous else { return }   // the sink replays the current value on subscribe
        lastState = state

        switch state {
        case .listening:
            // The user is talking (again). Any half-measured wait is stale — the
            // one that counts starts when THIS turn of theirs ends.
            stoppedListeningAt = nil
            // Back to listening means the reply is fully delivered. Give the SDK
            // a beat to report an interruption before booking the turn.
            scheduleTurnFlush()

        case .thinking:
            // `.listening` → `.thinking` IS the user finishing their turn: the
            // wait they're about to feel starts here. A `.thinking` arriving out
            // of `.speaking` is a mid-reply tool call — same turn, don't restart.
            if previous == .listening { stoppedListeningAt = Date() }

        case .speaking:
            // Only replies that followed a user turn are measured. The opening
            // greeting goes straight `.listening` → `.speaking` with no user wait
            // to report; counting it would fill the metric with 0ms samples. A
            // reply resuming after a tool call keeps the gap it already measured.
            if let since = stoppedListeningAt {
                pendingGapMs = Int(Date().timeIntervalSince(since) * 1000)
                stoppedListeningAt = nil
            }
        }
        // Exhaustive on purpose, no `default`: if the SDK ever grows a fourth
        // agent state, this measurement is wrong until someone decides where it
        // belongs — better a compile error at the bump than a silent skew.
    }

    private func scheduleTurnFlush() {
        guard pendingGapMs != nil else { return }
        flushTask?.cancel()
        flushTask = Task { [weak self] in
            try? await Task.sleep(nanoseconds: Self.turnFlushDelayNanos)
            guard !Task.isCancelled else { return }
            self?.emitPendingTurn()
        }
    }

    private func emitPendingTurn() {
        guard let gapMs = pendingGapMs else { return }
        pendingGapMs = nil
        turns += 1
        Analytics.capture("voice_turn", [
            "surface": surface.rawValue,
            "response_gap_ms": gapMs,
            "alignment_present": alignmentSeen,
            "interrupted": interruptedThisTurn,
        ])
        interruptedThisTurn = false
    }
}
