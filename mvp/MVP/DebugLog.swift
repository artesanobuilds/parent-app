import Foundation

/// Lightweight client-side diagnostic log.
///
/// Keeps the last N lines in memory and mirrors them to a file in Caches so they
/// survive backgrounding / relaunch — the crucial property for TestFlight bug
/// reports, since the failure (e.g. a voice connection error) has already
/// happened by the time the user opens "Send debug data". Thread-safe: call the
/// free `dlog(_:)` function from any context (main actor or background).
final class DebugLog: @unchecked Sendable {
    static let shared = DebugLog()

    private let maxLines = 300
    private let lock = NSLock()
    private var lines: [String] = []
    private let fileURL: URL?

    private init() {
        let fm = FileManager.default
        let caches = try? fm.url(for: .cachesDirectory, in: .userDomainMask,
                                 appropriateFor: nil, create: true)
        fileURL = caches?.appendingPathComponent("debug-log.txt")
        // Reload anything persisted by a previous run.
        if let url = fileURL, let text = try? String(contentsOf: url, encoding: .utf8) {
            lines = text
                .split(separator: "\n", omittingEmptySubsequences: false)
                .map(String.init)
                .suffix(maxLines)
                .map { $0 }
        }
    }

    func log(_ message: String) {
        let stamped = "\(Self.stamp()) \(message)"
        lock.lock()
        lines.append(stamped)
        if lines.count > maxLines { lines.removeFirst(lines.count - maxLines) }
        let snapshot = lines
        lock.unlock()
        // Persist off the caller's thread so logging never blocks.
        if let url = fileURL {
            DispatchQueue.global(qos: .utility).async {
                try? snapshot.joined(separator: "\n").write(to: url, atomically: true, encoding: .utf8)
            }
        }
    }

    func snapshot() -> String {
        lock.lock(); defer { lock.unlock() }
        return lines.joined(separator: "\n")
    }

    func clear() {
        lock.lock(); lines.removeAll(); lock.unlock()
        if let url = fileURL { try? FileManager.default.removeItem(at: url) }
    }

    private static let formatter: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()

    private static func stamp() -> String { formatter.string(from: Date()) }
}

/// Print to the console AND capture into the debug buffer for bug reports.
/// Drop-in replacement for `print(...)` on diagnostic paths.
func dlog(_ message: String) {
    print(message)
    DebugLog.shared.log(message)
}
