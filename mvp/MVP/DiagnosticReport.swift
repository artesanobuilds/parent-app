import Foundation
import UIKit
import AVFoundation

/// A diagnostic bundle for the "Send debug data" report: device/app/server
/// context plus the recent client log buffer. Built on the main actor because
/// it reads UI/config state; serialized to JSON for POST /debug/report.
struct DiagnosticReport {
    let userID: String
    let note: String
    let diagnostics: [String: String]
    let logs: String

    /// Snapshot current app state into a report. `note` is the user's typed
    /// description; `failureContext` is an optional machine reason (e.g. the
    /// voice failure string) prepended to the logs so it can't be lost.
    ///
    /// Reads config straight from UserDefaults (same keys ServerConfiguration
    /// persists) so any surface can build a report with just a note.
    @MainActor
    static func make(note: String, failureContext: String? = nil) -> DiagnosticReport {
        let defaults = UserDefaults.standard
        let userID = defaults.string(forKey: "user_name") ?? ""
        let baseURLString = defaults.string(forKey: "chat.base_url") ?? ServerConfiguration.defaultURL
        let threadID = defaults.string(forKey: "chat.thread_id") ?? "(unset)"

        let info = Bundle.main.infoDictionary
        let version = info?["CFBundleShortVersionString"] as? String ?? "?"
        let build = info?["CFBundleVersion"] as? String ?? "?"

        var diag: [String: String] = [:]
        diag["app_version"] = "\(version) (\(build))"
        diag["device"] = UIDevice.current.model
        diag["ios"] = UIDevice.current.systemVersion
        diag["base_url"] = baseURLString
        diag["environment"] = baseURLString == ServerConfiguration.productionURL ? "production" : "local/custom"
        diag["thread_id"] = threadID
        diag["user_id"] = userID
        diag["mic_permission"] = micPermissionString()

        var logBody = DebugLog.shared.snapshot()
        if let fc = failureContext, !fc.isEmpty {
            logBody = "FAILURE CONTEXT: \(fc)\n" + logBody
        }

        return DiagnosticReport(userID: userID, note: note, diagnostics: diag, logs: logBody)
    }

    /// JSON body for POST /debug/report.
    func jsonBody() -> [String: Any] {
        ["user_id": userID, "note": note, "diagnostics": diagnostics, "logs": logs]
    }

    /// Human-readable preview shown in the report sheet (transparency).
    func previewText() -> String {
        let head = diagnostics.sorted { $0.key < $1.key }
            .map { "\($0.key): \($0.value)" }
            .joined(separator: "\n")
        return head + "\n\n— recent logs —\n" + logs
    }

    private static func micPermissionString() -> String {
        switch AVAudioApplication.shared.recordPermission {
        case .granted:      return "granted"
        case .denied:       return "denied"
        case .undetermined: return "undetermined"
        @unknown default:   return "unknown"
        }
    }
}
