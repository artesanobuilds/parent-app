import SwiftUI
import PhotosUI

// MARK: - What a photo belongs to

/// Which record an avatar upload attaches to. ONE enum for the three attach
/// routes, so a new surface can't quietly invent a fourth:
///
///   .parent → `POST /profile/avatar`
///   .kid    → `POST /profile/kids/{name}/avatar`      (name = the SERVER's dict key)
///   .member → `POST /household/members/{id}/avatar`   (id = the stable roster uuid)
///
/// This is what generalises the photo band across kids AND household members:
/// the view and the upload model are target-agnostic, and the caller supplies
/// both the target and its own source-of-truth re-fetch.
enum AvatarTarget: Equatable, Hashable {
    case parent
    case kid(String)
    case member(String)

    var attachPath: String {
        switch self {
        case .parent:
            return "profile/avatar"
        case .kid(let name):
            let encoded = name.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? name
            return "profile/kids/\(encoded)/avatar"
        case .member(let id):
            let encoded = id.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? id
            return "household/members/\(encoded)/avatar"
        }
    }

    /// Written next to a pending attach so a relaunch can retry it. `kid_name`
    /// is still emitted for kids: a stash written by an older build is read by
    /// the newer one and vice versa.
    var stashDescriptor: [String: String] {
        switch self {
        case .parent:         return ["target_kind": "parent"]
        case .kid(let name):  return ["target_kind": "kid", "target_id": name, "kid_name": name]
        case .member(let id): return ["target_kind": "member", "target_id": id]
        }
    }

    static func fromStash(_ json: [String: Any]) -> AvatarTarget {
        let id = json["target_id"] as? String ?? ""
        switch json["target_kind"] as? String {
        case "kid":    return .kid(id)
        case "member": return .member(id)
        case "parent": return .parent
        default:
            // Pre-target stashes only ever carried a kid name (absent = parent).
            if let kid = json["kid_name"] as? String, !kid.isEmpty { return .kid(kid) }
            return .parent
        }
    }

    var fallbackSystemImage: String {
        if case .kid = self { return "figure.child" }
        return "person.fill"
    }
}

// MARK: - Avatar display

/// Circular profile photo with a fallback for the no-photo case.
///
/// `urlString` is the presigned avatar_url from the server (short-lived,
/// display-only). Two fallbacks are supported:
///   - an SF Symbol (`fallbackSystemImage`) — the compact list-row treatment;
///   - a display-serif MONOGRAM on the kid's accent (`monogram` +
///     `monogramFill`) — beta-v1's large kid-settings avatar.
///
/// White on `accentKid` (saffron) is only 2.28:1, which is why the monogram is
/// allowed to be the ONLY thing drawn in white on it: it is decorative, and the
/// kid's name is always rendered adjacent (see the note on `Color.accentKid`).
struct AvatarCircleView: View {
    let urlString: String?
    let fallbackSystemImage: String
    var size: CGFloat = 28
    /// When non-empty, the no-photo fallback becomes this letter on `monogramFill`.
    var monogram: String? = nil
    /// Fill behind the monogram — pass `Color.kidAccent(seed:)` for a kid.
    var monogramFill: Color = .accentKid

    var body: some View {
        Group {
            if let urlString, let url = URL(string: urlString) {
                AsyncImage(url: url) { phase in
                    if case .success(let image) = phase {
                        image.resizable().scaledToFill()
                    } else {
                        fallback
                    }
                }
            } else {
                fallback
            }
        }
        .frame(width: size, height: size)
        .clipShape(Circle())
    }

    @ViewBuilder
    private var fallback: some View {
        if let letter = monogram?.trimmingCharacters(in: .whitespacesAndNewlines),
           !letter.isEmpty {
            Circle()
                .fill(monogramFill)
                .overlay(
                    Text(String(letter.prefix(1)).uppercased())
                        .font(.custom(HearthFontFamily.displaySerif,
                                      fixedSize: size * 0.42).weight(.bold))
                        .foregroundColor(.inkOnPhotoLight)
                )
        } else {
            fallbackIcon
        }
    }

    private var fallbackIcon: some View {
        Circle()
            .fill(Color.bgElevated)
            .overlay(
                Image(systemName: fallbackSystemImage)
                    .font(.system(size: size * 0.5, weight: .medium))
                    .foregroundColor(.accentDefault)
            )
    }
}

// MARK: - Upload model (ONE upload implementation)

/// Drives every avatar upload in the app. The editor row, the kid photo band
/// and the member photo band all own one of these, so the presign → PUT →
/// durable-attach chain lives in exactly one place
/// (`BlobService.uploadAvatar`, whose failed attach is retried from `MVPApp`'s
/// `flushPendingAttach`). Do not add a second upload path.
@MainActor
final class AvatarUploadModel: ObservableObject {
    @Published var localImage: UIImage?
    @Published var uploading = false
    @Published var error: String?

    /// Pick → prepare → upload → let the CALLER re-fetch its own source of
    /// truth (CLAUDE.md's "after a mutation, the source-of-truth view
    /// re-fetches"). `refresh` returns whether that read succeeded.
    ///
    /// Nothing here navigates or reports success on hope: the upload throws
    /// unless the bytes landed, the attach is durable, and a failure clears the
    /// optimistic local image and surfaces `error` with the sheet still open.
    ///
    /// For `.kid` / `.member` the target id MUST be the server's key (dict name
    /// / roster uuid), not a possibly-edited draft name — attach 404s otherwise.
    func upload(
        _ item: PhotosPickerItem,
        target: AvatarTarget,
        userID: String,
        baseURL: URL?,
        refresh: @escaping () async -> Bool
    ) async {
        guard let baseURL else { return }
        uploading = true
        error = nil
        defer { uploading = false }
        guard let data = try? await item.loadTransferable(type: Data.self),
              let image = UIImage(data: data) else {
            error = "Couldn't read that photo — try a different one."
            return
        }
        // Instant local feedback while the upload runs.
        localImage = image.squareCropped().normalizedForUpload(maxDimension: 512)
        do {
            try await BlobService.uploadAvatar(image, target: target,
                                               userID: userID, baseURL: baseURL)
            // The bytes are attached. If the re-read fails we KEEP the local
            // image — the photo really is saved, and dropping it would look
            // like the upload had failed.
            _ = await refresh()
        } catch {
            localImage = nil
            self.error = (error as? LocalizedError)?.errorDescription
                ?? "The photo didn't upload. Please try again."
        }
    }
}

// MARK: - Avatar picker (profile editors)

/// Photo-library picker row for the Form-style profile editors (parent when
/// `kidName` is nil, else that kid). Photo library ONLY — no camera; the
/// Info.plist camera string says "MVP never uses the camera" and must stay
/// true. Uploads via `AvatarUploadModel` → BlobService (presign → PUT → durable
/// attach) and re-fetches the profile so the editor's caller sees the new photo.
struct AvatarPickerRow: View {
    let avatarUrl: String?
    let kidName: String?
    let userID: String
    let baseURL: URL?
    var onProfileRefreshed: (FamilyProfileDTO) -> Void

    @State private var pickerItem: PhotosPickerItem?
    @StateObject private var uploader = AvatarUploadModel()

    private var target: AvatarTarget {
        kidName.map { AvatarTarget.kid($0) } ?? .parent
    }

    var body: some View {
        HStack(spacing: .hearth500) {
            if let localImage = uploader.localImage {
                Image(uiImage: localImage)
                    .resizable()
                    .scaledToFill()
                    .frame(width: 56, height: 56)
                    .clipShape(Circle())
            } else {
                AvatarCircleView(
                    urlString: avatarUrl,
                    fallbackSystemImage: target.fallbackSystemImage,
                    size: 56
                )
            }

            VStack(alignment: .leading, spacing: 4) {
                PhotosPicker(selection: $pickerItem, matching: .images, photoLibrary: .shared()) {
                    Text(uploader.uploading ? "Uploading…"
                         : (avatarUrl == nil && uploader.localImage == nil ? "Add photo" : "Change photo"))
                        .font(.hearthBodyMD.weight(.semibold))
                        .foregroundColor(uploader.uploading ? .inkMuted : .accentDefault)
                }
                .disabled(uploader.uploading || baseURL == nil)

                if let uploadError = uploader.error {
                    Text(uploadError)
                        .font(.hearthBodySM)
                        .foregroundColor(.statusError)
                }
            }
        }
        .onChange(of: pickerItem) { _, item in
            guard let item else { return }
            Task {
                await uploader.upload(item, target: target, userID: userID, baseURL: baseURL) {
                    guard let baseURL,
                          let fam = try? await ProfileService.getProfile(baseURL: baseURL,
                                                                        userID: userID) else {
                        return false
                    }
                    onProfileRefreshed(fam)
                    return true
                }
                pickerItem = nil
            }
        }
    }
}

// MARK: - The photo band with its camera Edit badge (beta-v1 sprint-1)

/// The person-frame hero: a wide photo band with a small dark camera pill over
/// its top-left corner. It opens every one of Greg's person screens — kids
/// (`kid-001a/b/c`, `kid-002a`) AND household members (`parent 001/002`,
/// `co-parent 001`, `circle member`) — which is why it is ONE component with a
/// `target`, not a kid view plus a near-duplicate member view.
///
/// Measured (`kid-001c`, `parent 001`): band 440x401 (drawn here as that
/// aspect ratio so it is right on every device width), badge inset 17.7, badge
/// r18.6 on `#151412` with `#DAE0DF` ink, label "Edit" when a photo exists and
/// "Upload new" when it doesn't (`kid-001a`, which also captions the band).
///
/// The upload is the shared durable one (`AvatarUploadModel` →
/// `BlobService.uploadAvatar`): the sheet stays open on failure, the caller's
/// `refresh` re-reads the record, and what renders afterwards is what the
/// server returned.
struct EditableAvatarView: View {
    let avatarUrl: String?
    /// Which record this photo attaches to. `.kid` carries the server's dict
    /// key, `.member` the roster uuid — never an edited display name.
    let target: AvatarTarget
    let userID: String
    let baseURL: URL?
    /// Drawn on the placeholder ground when there is no photo yet.
    var monogram: String? = nil
    /// The person's name, for the "Add a photo of {name}" caption.
    var personName: String? = nil
    /// Re-read the caller's source of truth. Returns whether it succeeded.
    var refresh: () async -> Bool

    @State private var pickerItem: PhotosPickerItem?
    @StateObject private var uploader = AvatarUploadModel()

    private var hasPhoto: Bool { uploader.localImage != nil || avatarUrl != nil }

    var body: some View {
        VStack(spacing: .hearth300) {
            band
                .overlay(alignment: .topLeading) { badge.padding(17.7) }
                .clipped()

            if !hasPhoto, let personName, !personName.isEmpty {
                Text("Add a photo of \(personName)")
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkPrimary)
            }
            if let uploadError = uploader.error {
                Text(uploadError)
                    .font(.hearthBodySM)
                    .foregroundColor(.statusError)
                    .multilineTextAlignment(.center)
            }
        }
        .onChange(of: pickerItem) { _, item in
            guard let item else { return }
            Task {
                await uploader.upload(item, target: target, userID: userID,
                                      baseURL: baseURL, refresh: refresh)
                pickerItem = nil
            }
        }
    }

    // MARK: Pieces

    @ViewBuilder
    private var band: some View {
        ZStack {
            if let localImage = uploader.localImage {
                Image(uiImage: localImage).resizable().scaledToFill()
            } else if let avatarUrl, let url = URL(string: avatarUrl) {
                AsyncImage(url: url) { phase in
                    if case .success(let image) = phase {
                        image.resizable().scaledToFill()
                    } else {
                        placeholder
                    }
                }
            } else {
                placeholder
            }
        }
        .frame(maxWidth: .infinity)
        // 440 x 401 in the frames — held as a ratio so the band scales with the
        // device instead of being pinned to the artboard's pixel height.
        .aspectRatio(440.0 / 401.0, contentMode: .fill)
        .frame(maxWidth: .infinity)
    }

    /// `kid-001a`'s empty band: the flat warm grey, carrying the person's
    /// initial so the screen still reads as theirs before a photo exists.
    private var placeholder: some View {
        Rectangle()
            .fill(Color.inkEyebrow)
            .overlay(
                Text(initial)
                    .font(.hearthDisplayXL)
                    .tracking(-1.12)
                    .foregroundColor(.inkOnPhotoLight)
            )
    }

    private var initial: String {
        let source = (monogram ?? personName ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        return source.isEmpty ? "" : String(source.prefix(1)).uppercased()
    }

    private var badge: some View {
        PhotosPicker(selection: $pickerItem, matching: .images, photoLibrary: .shared()) {
            HStack(spacing: 6) {
                Image(systemName: uploader.uploading ? "arrow.up.circle" : "camera.fill")
                    .font(.system(size: 11, weight: .regular))
                Text(uploader.uploading ? "Uploading…" : (hasPhoto ? "Edit" : "Upload new"))
                    .font(.hearthLabel)
            }
            // #151412 in the frame; `inkPrimary` (#1A1A1A) is the nearest token
            // and the 4-value difference is not perceptible at this size.
            .foregroundColor(.bgSelected)
            .padding(.horizontal, hasPhoto ? 6 : .hearth300)
            .padding(.vertical, 6)
            .background(Capsule().fill(Color.inkPrimary))
            .shadow(color: Color.inkPrimary.opacity(0.35), radius: 6.2, x: 0, y: 1)
        }
        .disabled(uploader.uploading || baseURL == nil)
        .accessibilityLabel(hasPhoto ? "Change photo" : "Upload a photo")
    }
}
