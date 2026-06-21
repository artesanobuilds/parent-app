import AVFoundation
import ElevenLabs
import Foundation
import LiveKit

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
    func connect(
        onVadScore: (@Sendable (Double) -> Void)? = nil,
        tokenProvider: @escaping () async throws -> KidAgentService.ConvAITokenResponse
    ) async -> ConnectOutcome {
        // Serialize: never start while a previous session is releasing the engine.
        await teardownTask?.value
        if activeConversation != nil {
            await teardown()
        }

        // Resolve mic permission BEFORE touching engine availability (see #815).
        switch AVAudioApplication.shared.recordPermission {
        case .undetermined:
            let granted = await AVAudioApplication.requestRecordPermission()
            guard granted else { return .micPermissionDenied }
        case .denied:
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
        let maxAttempts = Self.maxConnectAttempts
        for attempt in 1...maxAttempts {
            // Fresh token every attempt — tokens are conversation-scoped.
            let tokenResponse: KidAgentService.ConvAITokenResponse
            do {
                tokenResponse = try await tokenProvider()
            } catch KidAgentServiceError.voiceFallback(reason: .crisis, status: _) {
                return .crisisLocked            // terminal — never retry
            } catch KidAgentServiceError.consentRequired(let version) {
                return .consentRequired(version) // terminal — never retry
            } catch {
                // A token fetch can fail on a transient network blip — retry.
                lastError = "token fetch: \(error.localizedDescription)"
                dlog("[voice-mgr] ⚠️ token fetch failed (attempt \(attempt)/\(maxAttempts)): \(lastError)")
                if attempt < maxAttempts {
                    try? await Task.sleep(nanoseconds: Self.connectBackoffNanos(afterAttempt: attempt))
                    continue
                }
                return .failed(lastError)
            }
            guard let token = tokenResponse.signedURL else {
                return .failed("token endpoint returned no signed_url")
            }

            do {
                let conv = try await startWithWatchdog(token: token, response: tokenResponse, onVadScore: onVadScore)
                activeConversation = conv
                dlog("[voice-mgr] ✅ connected (attempt \(attempt)); state=\(conv.state)")
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
                // Connection/timeout error (the ElevenLabs leg never reached us) —
                // retry with backoff before giving up.
                dlog("[voice-mgr] ❌ connect failed (attempt \(attempt)/\(maxAttempts)): \(lastError)")
                if attempt < maxAttempts {
                    try? await Task.sleep(nanoseconds: Self.connectBackoffNanos(afterAttempt: attempt))
                    continue
                }
                return .failed(lastError)
            } catch {
                lastError = error.localizedDescription
                dlog("[voice-mgr] ❌ connect failed (attempt \(attempt)/\(maxAttempts)): \(lastError)")
                if attempt < maxAttempts {
                    try? await Task.sleep(nanoseconds: Self.connectBackoffNanos(afterAttempt: attempt))
                    continue
                }
                return .failed(lastError)
            }
        }
        return .failed(lastError)
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

    private func startWithWatchdog(
        token: String,
        response: KidAgentService.ConvAITokenResponse,
        onVadScore: (@Sendable (Double) -> Void)?
    ) async throws -> Conversation {
        let config = Self.buildConfig(from: response, onVadScore: onVadScore)
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
        onVadScore: (@Sendable (Double) -> Void)? = nil
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
