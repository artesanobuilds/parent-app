import Foundation
import AVFoundation
import Speech
import SwiftUI

// MARK: - On-device dictation (Heisman sprint-01, Appendix A2)
//
// One controller drives every mic affordance in the pre-account funnel: the
// topic free-text field, the sample-problem scrap, and the parent-tasks note.
// `SFSpeechRecognizer` + `AVAudioEngine`, on-device where the OS supports it —
// deliberately NOT ElevenLabs (the appendix keeps voice-agent infra out of
// this flow) and NOT the kid-companion voice stack.
//
// Permission discipline: microphone + speech-recognition prompts fire on the
// FIRST mic tap and never earlier (acceptance #11 as overridden by A2 — the
// prompt is expected, but only in response to the parent's own gesture).
//
// Ownership: each screen instantiates its own controller as @StateObject and
// binds `transcript` into whichever field the mic feeds. Stopping (or the
// screen disappearing) tears the audio session down; the transcript is
// appended to the field's existing text as it finalizes.

@MainActor
final class DictationController: NSObject, ObservableObject {

    /// Live transcript of the CURRENT recording session (partial results
    /// included). The owning view composes it with the field's prior text.
    @Published private(set) var transcript: String = ""
    @Published private(set) var isRecording = false
    /// Non-nil when the mic could not start — denied permission, no
    /// recognizer, or an audio-session failure. Shown inline by the field.
    @Published private(set) var errorMessage: String?

    private let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    private let audioEngine = AVAudioEngine()
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?

    /// Toggle from the mic button. First invocation requests both permissions.
    /// `onFinal` receives the finished transcript when recording stops.
    func toggle(onFinal: @escaping (String) -> Void) {
        if isRecording {
            let final = transcript
            stop()
            if !final.isEmpty { onFinal(final) }
        } else {
            Task { await start(onFinal: onFinal) }
        }
    }

    func stop() {
        recognitionTask?.cancel()
        recognitionTask = nil
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        if audioEngine.isRunning {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        isRecording = false
    }

    private func start(onFinal: @escaping (String) -> Void) async {
        errorMessage = nil
        transcript = ""

        // Permissions — requested HERE, on the first tap, never earlier.
        let speechGranted: Bool = await withCheckedContinuation { cont in
            SFSpeechRecognizer.requestAuthorization { status in
                cont.resume(returning: status == .authorized)
            }
        }
        guard speechGranted else {
            errorMessage = "Speech recognition isn't allowed — you can enable it in Settings, or just type."
            return
        }
        let micGranted: Bool = await withCheckedContinuation { cont in
            AVAudioApplication.requestRecordPermission { granted in
                cont.resume(returning: granted)
            }
        }
        guard micGranted else {
            errorMessage = "The mic isn't allowed — you can enable it in Settings, or just type."
            return
        }
        guard let recognizer, recognizer.isAvailable else {
            errorMessage = "Dictation isn't available right now — you can just type."
            return
        }

        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.record, mode: .measurement, options: .duckOthers)
            try session.setActive(true, options: .notifyOthersOnDeactivation)

            let request = SFSpeechAudioBufferRecognitionRequest()
            request.shouldReportPartialResults = true
            // On-device when the OS supports it — "audio never leaves your
            // device" is the permission copy's promise where possible.
            if recognizer.supportsOnDeviceRecognition {
                request.requiresOnDeviceRecognition = true
            }
            recognitionRequest = request

            let inputNode = audioEngine.inputNode
            let format = inputNode.outputFormat(forBus: 0)
            inputNode.removeTap(onBus: 0)
            inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak self] buffer, _ in
                self?.recognitionRequest?.append(buffer)
            }
            audioEngine.prepare()
            try audioEngine.start()
            isRecording = true

            recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
                Task { @MainActor [weak self] in
                    guard let self else { return }
                    if let result {
                        self.transcript = result.bestTranscription.formattedString
                        if result.isFinal {
                            let final = self.transcript
                            self.stop()
                            if !final.isEmpty { onFinal(final) }
                        }
                    }
                    if error != nil, self.isRecording {
                        // A cancel arrives here too; only surface real starts.
                        let final = self.transcript
                        self.stop()
                        if !final.isEmpty { onFinal(final) }
                    }
                }
            }
        } catch {
            stop()
            errorMessage = "Couldn't start the mic — you can just type."
        }
    }
}
