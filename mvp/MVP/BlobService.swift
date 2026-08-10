import Foundation
import UIKit

/// Profile-photo upload against the blob endpoints (Railway Storage Buckets
/// behind the backend; see app/blobs). The chain is three calls and NOT
/// atomic — presign → PUT bytes → attach key — so the final attach is made
/// durable: if it fails (offline, killed mid-flight), the {target, key} pair
/// is stashed in UserDefaults and re-attached on next launch, the same
/// self-heal pattern as the onboarding seed and the legal accept.
enum BlobService {

    /// Pending attach: `AvatarTarget.stashDescriptor` + ["key": String] JSON.
    /// One slot — last upload wins, which matches "the newest photo is the one
    /// I meant". A stash written by an older build carried only `kid_name`;
    /// `AvatarTarget.fromStash` still reads it.
    static let pendingAttachKey = "pending_avatar_attach"

    enum BlobError: LocalizedError {
        case notConfigured
        case uploadFailed
        var errorDescription: String? {
            switch self {
            case .notConfigured: return "Photos aren't available yet on this server."
            case .uploadFailed: return "The photo didn't upload. Please try again."
            }
        }
    }

    /// Upload an avatar and attach it to whatever `target` names — the parent,
    /// one kid, or one household member. Throws on presign/PUT failure; a failed
    /// ATTACH is stashed + retried on next launch instead of throwing (the bytes
    /// are already uploaded).
    @MainActor
    static func uploadAvatar(_ image: UIImage, target: AvatarTarget,
                             userID: String, baseURL: URL) async throws {
        let prepared = image.squareCropped().normalizedForUpload(maxDimension: 512)
        guard let jpeg = prepared.jpegData(compressionQuality: 0.85) else {
            throw BlobError.uploadFailed
        }

        // 1. Presign (server derives the key).
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        var presign = URLRequest(url: baseURL.appendingPathComponent("blobs/upload-url"))
        presign.httpMethod = "POST"
        presign.setValue("application/json", forHTTPHeaderField: "Content-Type")
        presign.timeoutInterval = 15
        for (k, v) in AuthService.shared.header(for: userID) {
            presign.setValue(v, forHTTPHeaderField: k)
        }
        presign.httpBody = try? JSONSerialization.data(withJSONObject: [
            "kind": "avatar", "content_type": "image/jpeg", "byte_size": jpeg.count,
        ])
        let (pData, pResp) = try await URLSession.shared.data(for: presign)
        guard let pHttp = pResp as? HTTPURLResponse else { throw BlobError.uploadFailed }
        if pHttp.statusCode == 503 { throw BlobError.notConfigured }
        guard pHttp.statusCode == 200,
              let pJson = try? JSONSerialization.jsonObject(with: pData) as? [String: Any],
              let key = pJson["key"] as? String,
              let putURLString = pJson["url"] as? String,
              let putURL = URL(string: putURLString) else {
            throw BlobError.uploadFailed
        }

        // 2. PUT the bytes straight to the bucket (presigned; no auth header).
        var put = URLRequest(url: putURL)
        put.httpMethod = "PUT"
        put.setValue("image/jpeg", forHTTPHeaderField: "Content-Type")
        put.timeoutInterval = 60
        let (_, putResp) = try await URLSession.shared.upload(for: put, from: jpeg)
        guard let putHttp = putResp as? HTTPURLResponse, (200..<300).contains(putHttp.statusCode) else {
            throw BlobError.uploadFailed
        }

        // 3. Attach — durable. Stash BEFORE the attempt (kill-safety), clear
        //    only on confirmed success.
        stashPendingAttach(target: target, key: key)
        if await attach(target: target, key: key, userID: userID, baseURL: baseURL) {
            clearPendingAttach()
        }
    }

    /// Re-attempt a stashed attach. Called from the launch task in SwayApp.
    @MainActor
    static func flushPendingAttach(userID: String, baseURL: URL) async {
        let defaults = UserDefaults.standard
        guard let data = defaults.data(forKey: pendingAttachKey),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let key = json["key"] as? String else {
            return
        }
        // A stashed attach for a DIFFERENT account must not run under this one
        // (the server would 403 on the key prefix anyway — the ownership
        // boundary — but don't even try).
        guard key.hasPrefix("u/\(userID)/") else {
            clearPendingAttach()
            return
        }
        if await attach(target: AvatarTarget.fromStash(json), key: key,
                        userID: userID, baseURL: baseURL) {
            clearPendingAttach()
        }
    }

    // MARK: - Internals

    @MainActor
    private static func attach(target: AvatarTarget, key: String,
                               userID: String, baseURL: URL) async -> Bool {
        var request = URLRequest(url: baseURL.appendingPathComponent(target.attachPath))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 15
        for (k, v) in AuthService.shared.header(for: userID) {
            request.setValue(v, forHTTPHeaderField: k)
        }
        request.httpBody = try? JSONSerialization.data(withJSONObject: ["key": key])
        guard let (_, response) = try? await URLSession.shared.data(for: request),
              let http = response as? HTTPURLResponse else { return false }
        if (200..<300).contains(http.statusCode) { return true }
        // 4xx = permanent (kid renamed/deleted, member removed, foreign key):
        // retrying next launch can't fix it — drop the stash so it doesn't
        // retry forever.
        if (400..<500).contains(http.statusCode) { clearPendingAttach() }
        return false
    }

    private static func stashPendingAttach(target: AvatarTarget, key: String) {
        var json: [String: Any] = ["key": key]
        for (k, v) in target.stashDescriptor { json[k] = v }
        if let data = try? JSONSerialization.data(withJSONObject: json) {
            UserDefaults.standard.set(data, forKey: pendingAttachKey)
        }
    }

    private static func clearPendingAttach() {
        UserDefaults.standard.removeObject(forKey: pendingAttachKey)
    }
}
