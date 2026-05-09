import Foundation
import Speech
import AVFoundation

/// Wraps SFSpeechRecognizer (STT) + AVSpeechSynthesizer (TTS) for v0 kid mode.
/// On-device when available — keeps audio local and minimizes latency.
/// Switching to OpenAI Whisper / OpenAI TTS for richer voices is a v1 upgrade.
@MainActor
final class VoiceController: NSObject, ObservableObject {

    @Published var isListening: Bool = false
    @Published var isSpeaking: Bool = false
    @Published var transcribedText: String = ""
    @Published var error: String?

    private let recognizer = SFSpeechRecognizer(locale: Locale.current) ?? SFSpeechRecognizer()
    private let audioEngine = AVAudioEngine()
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private var silenceTimer: Timer?
    private var lastTranscriptUpdate: Date = .distantPast

    /// Auto-stop listening after this many seconds of silence (no transcript updates).
    /// Kids start a sentence and don't always finish — without this, the recognition
    /// task can hang open until the app backgrounds.
    private let silenceTimeoutSeconds: TimeInterval = 3.0

    private let synthesizer = AVSpeechSynthesizer()

    override init() {
        super.init()
        synthesizer.delegate = self
    }

    func requestPermissions() async -> Bool {
        let speechAuth: SFSpeechRecognizerAuthorizationStatus = await withCheckedContinuation { cont in
            SFSpeechRecognizer.requestAuthorization { cont.resume(returning: $0) }
        }
        let micAuth: Bool = await withCheckedContinuation { cont in
            AVAudioApplication.requestRecordPermission { cont.resume(returning: $0) }
        }
        return speechAuth == .authorized && micAuth
    }

    func startListening() {
        guard !isListening else { return }
        // Don't open the mic while the agent is speaking — otherwise the
        // recognition tap picks up the agent's own TTS as if it were the kid.
        guard !isSpeaking else {
            self.error = "Wait for me to finish talking before you start."
            return
        }
        // Apple may route to server when on-device isn't available for the
        // current locale or device. For a kid product we require local STT;
        // refusing here is preferable to silently shipping audio off-device.
        guard let recognizer, recognizer.supportsOnDeviceRecognition else {
            self.error = "On-device speech recognition isn't available on this device or language. Tap to use text instead."
            return
        }
        do {
            #if os(iOS)
            // Configure audio session
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.playAndRecord, mode: .measurement, options: [.duckOthers, .defaultToSpeaker])
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
            #endif

            // Recognition request
            recognitionRequest?.endAudio()
            recognitionTask?.cancel()
            transcribedText = ""
            lastTranscriptUpdate = Date()

            let request = SFSpeechAudioBufferRecognitionRequest()
            request.shouldReportPartialResults = true
            request.requiresOnDeviceRecognition = true
            self.recognitionRequest = request

            recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
                Task { @MainActor [weak self] in
                    guard let self else { return }
                    if let result {
                        let next = result.bestTranscription.formattedString
                        if next != self.transcribedText {
                            self.transcribedText = next
                            self.lastTranscriptUpdate = Date()
                        }
                    }
                    if error != nil || (result?.isFinal ?? false) {
                        self.stopListening()
                    }
                }
            }

            // Audio tap
            let inputNode = audioEngine.inputNode
            let format = inputNode.outputFormat(forBus: 0)
            inputNode.removeTap(onBus: 0)
            inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
                request.append(buffer)
            }

            audioEngine.prepare()
            try audioEngine.start()
            isListening = true
            scheduleSilenceTimer()
        } catch {
            self.error = "Couldn't start listening: \(error.localizedDescription)"
            stopListening()
        }
    }

    func stopListening() {
        silenceTimer?.invalidate()
        silenceTimer = nil
        if audioEngine.isRunning {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        recognitionTask = nil
        isListening = false
    }

    private func scheduleSilenceTimer() {
        silenceTimer?.invalidate()
        silenceTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.isListening else { return }
                if Date().timeIntervalSince(self.lastTranscriptUpdate) >= self.silenceTimeoutSeconds {
                    self.stopListening()
                }
            }
        }
    }

    func speak(_ text: String) {
        guard !text.isEmpty else { return }
        // Stop listening before speaking — otherwise the recognition tap will
        // pick up our own TTS output and feed it back as kid input.
        if isListening {
            stopListening()
        }
        let utterance = AVSpeechUtterance(string: text)
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate
        utterance.pitchMultiplier = 1.0
        utterance.voice = AVSpeechSynthesisVoice(language: Locale.current.identifier)
            ?? AVSpeechSynthesisVoice(language: "en-US")
        synthesizer.stopSpeaking(at: .immediate)
        synthesizer.speak(utterance)
    }

    func stopSpeaking() {
        synthesizer.stopSpeaking(at: .immediate)
        isSpeaking = false
    }
}

extension VoiceController: AVSpeechSynthesizerDelegate {
    nonisolated func speechSynthesizer(_ s: AVSpeechSynthesizer, didStart utterance: AVSpeechUtterance) {
        Task { @MainActor in self.isSpeaking = true }
    }
    nonisolated func speechSynthesizer(_ s: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        Task { @MainActor in self.isSpeaking = false }
    }
    nonisolated func speechSynthesizer(_ s: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        Task { @MainActor in self.isSpeaking = false }
    }
}
