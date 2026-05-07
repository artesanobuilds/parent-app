import Foundation

/// Persists and validates the backend configuration the chat feature needs.
final class ServerConfiguration: ObservableObject {

    /// Production URL — update this once you deploy to Railway.
    static let productionURL = "https://mvp-backend-production-8678.up.railway.app"
    static let localURL = "http://localhost:8904"

    static var defaultURL: String {
        #if DEBUG
        return localURL
        #else
        return productionURL
        #endif
    }

    @Published var baseURLString: String {
        didSet { persist(key: Self.baseURLKey, value: baseURLString) }
    }

    @Published var threadID: String {
        didSet { persist(key: Self.threadIDKey, value: threadID) }
    }

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        baseURLString = defaults.string(forKey: Self.baseURLKey) ?? Self.defaultURL
        threadID = defaults.string(forKey: Self.threadIDKey) ?? UUID().uuidString
    }

    var baseURL: URL? {
        URL(string: baseURLString)
    }

    var isUsingProduction: Bool {
        baseURLString == Self.productionURL
    }

    func resetThread() {
        threadID = UUID().uuidString
    }

    func switchToLocal() {
        baseURLString = Self.localURL
    }

    func switchToProduction() {
        baseURLString = Self.productionURL
    }

    // MARK: - Private

    private func persist(key: String, value: String) {
        defaults.set(value, forKey: key)
    }

    private static let baseURLKey = "chat.base_url"
    private static let threadIDKey = "chat.thread_id"
}

