import Foundation

/// Persists and validates the backend configuration the chat feature needs.
final class ServerConfiguration: ObservableObject {
    @Published var baseURLString: String {
        didSet { persist(key: Self.baseURLKey, value: baseURLString) }
    }

    @Published var threadID: String {
        didSet { persist(key: Self.threadIDKey, value: threadID) }
    }

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        baseURLString = defaults.string(forKey: Self.baseURLKey) ?? "http://localhost:8000"
        threadID = defaults.string(forKey: Self.threadIDKey) ?? UUID().uuidString
    }

    var baseURL: URL? {
        URL(string: baseURLString)
    }

    func resetThread() {
        threadID = UUID().uuidString
    }

    // MARK: - Private

    private func persist(key: String, value: String) {
        defaults.set(value, forKey: key)
    }

    private static let baseURLKey = "chat.base_url"
    private static let threadIDKey = "chat.thread_id"
}

