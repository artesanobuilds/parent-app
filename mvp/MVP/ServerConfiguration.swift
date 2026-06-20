import Foundation

/// Persists and validates the backend configuration the chat feature needs.
/// @MainActor: @Published mutations must run on the main thread for safe
/// SwiftUI observation, and every construction site is a View/init context.
@MainActor
final class ServerConfiguration: ObservableObject {

    /// Production URL — update this once you deploy to Railway.
    static let productionURL = "https://mvp-backend-production-8678.up.railway.app"
    // 127.0.0.1 (not "localhost") so AVPlayer's CoreMedia HTTP stack doesn't
    // try the IPv6 ::1 address first — uvicorn binds IPv4-only by default, so
    // localhost-DNS-resolves-IPv6-first breaks voice streaming.
    static let localURL = "http://127.0.0.1:8904"

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
        let stored = defaults.string(forKey: Self.baseURLKey) ?? Self.defaultURL
        // One-shot migration: rewrite legacy localhost dev URL → 127.0.0.1
        // so AVPlayer doesn't reach for IPv6 ::1.
        let migrated = stored.hasPrefix("http://localhost") ? Self.localURL : stored
        baseURLString = migrated
        threadID = defaults.string(forKey: Self.threadIDKey) ?? UUID().uuidString
        if migrated != stored {
            defaults.set(migrated, forKey: Self.baseURLKey)
        }
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

