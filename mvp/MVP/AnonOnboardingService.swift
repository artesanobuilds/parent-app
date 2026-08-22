import Foundation

// MARK: - Anonymous onboarding extraction client
//
// Heisman sprint-01, Appendix A2: step 04's "hand the coach a scrap" runs a
// REAL extraction before any account exists. The backend keeps this stateless
// (`app/onboarding_extract.py`): `POST /onboarding/anon-session` mints a
// short-lived scoped token (no `sub` — it can never authenticate a user
// endpoint), and `POST /onboarding/extract` turns freeform text and/or an
// image into structured {who, what, when, where, notes} activities. Nothing
// persists server-side; the result lives in `OnboardingDraft` and rides the
// post-account seed.
//
// Failure posture mirrors the funnel's needs exactly:
//   • 401  — the cached anon token expired: re-mint ONCE and retry.
//   • 429 / 5xx / transport — surface as a thrown error; the sample-problem
//     screen shows its retry + static-sample fallback state. Never block the
//     funnel on this endpoint.
//
// Base URL resolves ONLY through the `chat.base_url` default falling back to
// `ServerConfiguration.defaultURL` — never a hardcoded host (the invariant
// tests/test_ios_baseurl_guard.py pins; a localhost literal here would
// silently break every real-device fresh install).

// @MainActor because `ServerConfiguration.defaultURL` is main-actor-isolated
// (and every caller is a view anyway); the actual network awaits suspend off
// the main thread inside URLSession.
@MainActor
enum AnonOnboardingService {

    enum ExtractError: Error {
        /// 429 or 5xx — the parent can retry, or continue with the sample.
        case serverUnavailable
        /// Transport failure (offline, timeout).
        case transport
        /// Anything else unexpected (4xx that isn't auth).
        case rejected
    }

    private struct AnonSessionResponse: Decodable {
        let token: String
        let expires_in: Int
    }

    private struct ExtractRequestBody: Encodable {
        var text: String?
        var image_b64: String?
        var media_type: String?
    }

    private struct WireActivity: Decodable {
        let who: String
        let what: String
        let when: String
        let `where`: String
        let notes: String?
    }

    private struct ExtractResponse: Decodable {
        let activities: [WireActivity]
    }

    /// In-memory token cache. Deliberately NOT persisted: the token is a
    /// 60-minute convenience, and a fresh mint is one cheap round trip.
    private static var cachedToken: (value: String, expires: Date)?

    private static var baseURL: URL? {
        URL(string: UserDefaults.standard.string(forKey: "chat.base_url") ?? ServerConfiguration.defaultURL)
    }

    // MARK: Session

    /// Returns a valid anon-session token, minting one if the cache is empty
    /// or stale (60s of slack so a token never expires mid-request).
    private static func sessionToken(forceRefresh: Bool = false) async throws -> String {
        if !forceRefresh, let cached = cachedToken, cached.expires > Date().addingTimeInterval(60) {
            return cached.value
        }
        guard let base = baseURL else { throw ExtractError.transport }
        var request = URLRequest(url: base.appendingPathComponent("onboarding/anon-session"))
        request.httpMethod = "POST"
        request.timeoutInterval = 15
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            let status = (response as? HTTPURLResponse)?.statusCode ?? -1
            guard status == 200 else {
                throw status == 429 || status >= 500 ? ExtractError.serverUnavailable : ExtractError.rejected
            }
            let decoded = try JSONDecoder().decode(AnonSessionResponse.self, from: data)
            cachedToken = (decoded.token, Date().addingTimeInterval(TimeInterval(decoded.expires_in)))
            return decoded.token
        } catch let error as ExtractError {
            throw error
        } catch {
            throw ExtractError.transport
        }
    }

    // MARK: Extraction

    /// Extract structured activities from freeform text and/or an image.
    /// At least one of `text` / `imageData` must be non-nil (the screen's
    /// Continue gate guarantees it). `mediaType` accompanies `imageData`
    /// (e.g. "image/jpeg").
    static func extract(
        text: String?,
        imageData: Data? = nil,
        mediaType: String? = nil
    ) async throws -> [OnboardingDraft.ExtractedActivity] {
        let token = try await sessionToken()
        do {
            return try await postExtract(text: text, imageData: imageData, mediaType: mediaType, token: token)
        } catch ExtractError.rejected {
            // Could be an expired/invalidated token (401) — re-mint once.
            let fresh = try await sessionToken(forceRefresh: true)
            return try await postExtract(text: text, imageData: imageData, mediaType: mediaType, token: fresh)
        }
    }

    private static func postExtract(
        text: String?,
        imageData: Data?,
        mediaType: String?,
        token: String
    ) async throws -> [OnboardingDraft.ExtractedActivity] {
        guard let base = baseURL else { throw ExtractError.transport }
        var request = URLRequest(url: base.appendingPathComponent("onboarding/extract"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        // Extraction runs an LLM call server-side; give it real time.
        request.timeoutInterval = 60
        let body = ExtractRequestBody(
            text: text?.isEmpty == false ? text : nil,
            image_b64: imageData?.base64EncodedString(),
            media_type: imageData != nil ? mediaType : nil
        )
        request.httpBody = try? JSONEncoder().encode(body)

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            let status = (response as? HTTPURLResponse)?.statusCode ?? -1
            switch status {
            case 200:
                let decoded = try JSONDecoder().decode(ExtractResponse.self, from: data)
                return decoded.activities.map {
                    OnboardingDraft.ExtractedActivity(
                        who: $0.who, what: $0.what, when: $0.when,
                        where: $0.where, notes: $0.notes ?? ""
                    )
                }
            case 401:
                cachedToken = nil
                throw ExtractError.rejected
            case 429, 500...599:
                throw ExtractError.serverUnavailable
            default:
                throw ExtractError.rejected
            }
        } catch let error as ExtractError {
            throw error
        } catch {
            throw ExtractError.transport
        }
    }
}
