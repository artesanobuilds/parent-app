import SwiftUI

/// What the reveal engine believes about the agent turn currently being spoken.
/// This is `StreamingText`'s only pacing input — see `VoiceRevealEngine`, which
/// produces it. Kept as a plain value (not an `ObservableObject` read) so the
/// view can poll it on its own tick without churning the SwiftUI graph.
struct SpokenProgress {
    /// Characters the agent has actually spoken so far — real audio alignment
    /// when it exists, otherwise the speaking-clock estimate.
    var chars: Int
    /// False when no `.speaking` state has been observed for this turn yet. The
    /// gate is then untrustworthy, so the view runs its own wall clock rather
    /// than holding the text hostage to a signal that may never arrive.
    var observedSpeech: Bool
    /// The spoken turn is over — whatever text remains should land immediately.
    var finished: Bool

    /// No engine wired (previews, tests, non-voice callers) → pure typewriter.
    static let unknown = SpokenProgress(chars: 0, observedSpeech: false, finished: false)
}

/// Reveals `text` progressively to mimic the text-chat's token streaming. Voice
/// transcripts arrive whole-turn from ElevenLabs (no per-token event in voice
/// mode), so we type them out client-side. Each agent bubble gets its own
/// instance (keyed by message id), so only the in-progress turn animates; prior
/// turns render fully.
///
/// Shared by BOTH voice surfaces (parent coach + kid companion). Pacing comes
/// from `spokenProgress` when a `VoiceRevealEngine` is wired; without one it
/// degrades to the original fixed-rate typewriter.
struct StreamingText: View {
    let text: String
    /// False for completed/history bubbles: render the full text immediately so
    /// nothing re-animates when SwiftUI rebuilds the view tree.
    var isActive: Bool = true
    /// Spoken progress for this turn, or `.unknown` when nothing is driving it.
    var spokenProgress: () -> SpokenProgress = { .unknown }
    var fallbackCPS: Double = 22   // typewriter rate when speech isn't observed
    var floorCPS: Double = 9       // stall-guard rate (see `stallSeconds`)
    /// How long the speech gate may hold the reveal completely still before we
    /// stop trusting it. A turn normally ends with `finished` and lands its tail;
    /// this only covers a wedged `.speaking` state, so text can never freeze
    /// mid-word forever.
    var stallSeconds: TimeInterval = 6

    @State private var shown = 0
    @State private var task: Task<Void, Never>?

    var body: some View {
        Text(String(text.prefix(isActive ? shown : text.count)))
            .onAppear { start() }
            .onChange(of: text) { _, _ in start() }
            .onChange(of: isActive) { _, _ in start() }
            .onDisappear { task?.cancel() }
    }

    private func start() {
        task?.cancel()
        if shown > text.count { shown = text.count }   // text shrank (correction)
        guard isActive else { shown = text.count; return }
        guard shown < text.count else { return }
        let begin = Date()
        task = Task { @MainActor in
            var lastAdvance = begin
            // A bubble can appear a beat before the engine has rolled over to the
            // new turn, so its first poll may still describe the PREVIOUS turn —
            // already finished, with its full char count. Trusting that would pop
            // the paragraph in, the exact bug this view exists to prevent. So we
            // ignore the gate until it reports an unfinished turn at least once.
            var gateArmed = false
            while shown < text.count {
                let now = Date()
                let elapsed = now.timeIntervalSince(begin)
                let progress = spokenProgress()
                if !progress.finished { gateArmed = true }
                let target: Int
                if gateArmed, progress.finished {
                    target = text.count           // audio done — land the rest now
                } else if gateArmed, progress.observedSpeech,
                          now.timeIntervalSince(lastAdvance) < stallSeconds {
                    target = progress.chars       // gated on real speaking time
                } else {
                    // No trustworthy gate yet (or it wedged) — run the wall clock
                    // so the text still moves, exactly as it did before gating.
                    let rate = (gateArmed && progress.observedSpeech) ? floorCPS : fallbackCPS
                    target = max(gateArmed ? progress.chars : 0, Int(elapsed * rate))
                }
                let before = shown
                shown = max(shown, min(target, text.count))  // monotonic
                if shown > before { lastAdvance = now }
                if shown >= text.count { break }
                try? await Task.sleep(nanoseconds: 30_000_000)  // 30ms tick
                if Task.isCancelled { return }
            }
            shown = text.count
        }
    }
}
