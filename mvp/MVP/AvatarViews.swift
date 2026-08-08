import SwiftUI
import PhotosUI

// MARK: - Avatar display

/// Circular profile photo with a fallback for the no-photo case.
///
/// `urlString` is the presigned avatar_url from GET /profile (short-lived,
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

/// Drives every avatar upload in the app. Both the editor row and the beta-v1
/// camera-badge avatar own one of these, so the presign → PUT → durable-attach
/// chain lives in exactly one place (`BlobService.uploadAvatar`, whose failed
/// attach is retried from `SwayApp`'s `flushPendingAttach`). Do not add a
/// second upload path.
@MainActor
final class AvatarUploadModel: ObservableObject {
    @Published var localImage: UIImage?
    @Published var uploading = false
    @Published var error: String?

    /// Pick → prepare → upload → re-fetch the profile (CLAUDE.md's
    /// "after a mutation, the source-of-truth view re-fetches").
    ///
    /// `kidName` MUST be the server's dictionary key for that kid, not a
    /// possibly-edited draft name — attach 404s unknown kids.
    func upload(
        _ item: PhotosPickerItem,
        kidName: String?,
        userID: String,
        baseURL: URL?,
        onProfileRefreshed: @escaping (FamilyProfileDTO) -> Void
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
            try await BlobService.uploadAvatar(image, kidName: kidName,
                                               userID: userID, baseURL: baseURL)
            if let fam = try? await ProfileService.getProfile(baseURL: baseURL, userID: userID) {
                onProfileRefreshed(fam)
            }
        } catch {
            localImage = nil
            self.error = (error as? LocalizedError)?.errorDescription
                ?? "The photo didn't upload. Please try again."
        }
    }
}

// MARK: - Avatar picker (profile editors)

/// Photo-library picker row for the profile editors (parent when `kidName` is
/// nil, else that kid). Photo library ONLY — no camera; the Info.plist camera
/// string says "MVP never uses the camera" and must stay true. Uploads via
/// `AvatarUploadModel` → BlobService (presign → PUT → durable attach) and
/// re-fetches the profile so the editor's caller sees the new photo immediately.
struct AvatarPickerRow: View {
    let avatarUrl: String?
    let kidName: String?
    let userID: String
    let baseURL: URL?
    var onProfileRefreshed: (FamilyProfileDTO) -> Void

    @State private var pickerItem: PhotosPickerItem?
    @StateObject private var uploader = AvatarUploadModel()

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
                    fallbackSystemImage: kidName == nil ? "person.fill" : "figure.child",
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
                await uploader.upload(item, kidName: kidName, userID: userID,
                                      baseURL: baseURL, onProfileRefreshed: onProfileRefreshed)
                pickerItem = nil
            }
        }
    }
}

// MARK: - Large avatar with the camera-badge Edit pill (beta-v1)

/// The kid-settings hero avatar: the kid's photo, or a serif monogram on their
/// accent, with a small teal `📷 Edit` pill overlapping the bottom edge. Tapping
/// the pill opens the photo library and runs the SAME upload path as
/// `AvatarPickerRow` (`AvatarUploadModel` → `BlobService.uploadAvatar`).
struct EditableAvatarView: View {
    let avatarUrl: String?
    /// The server's dictionary key for this kid; nil = the parent's own avatar.
    let kidName: String?
    let userID: String
    let baseURL: URL?
    var size: CGFloat = 172
    var monogram: String? = nil
    var monogramFill: Color = .accentKid
    var onProfileRefreshed: (FamilyProfileDTO) -> Void

    @State private var pickerItem: PhotosPickerItem?
    @StateObject private var uploader = AvatarUploadModel()

    var body: some View {
        VStack(spacing: .hearth300) {
            ZStack(alignment: .bottom) {
                Group {
                    if let localImage = uploader.localImage {
                        Image(uiImage: localImage)
                            .resizable()
                            .scaledToFill()
                            .frame(width: size, height: size)
                            .clipShape(Circle())
                    } else {
                        AvatarCircleView(
                            urlString: avatarUrl,
                            fallbackSystemImage: kidName == nil ? "person.fill" : "figure.child",
                            size: size,
                            monogram: monogram,
                            monogramFill: monogramFill
                        )
                    }
                }

                PhotosPicker(selection: $pickerItem, matching: .images, photoLibrary: .shared()) {
                    HStack(spacing: 5) {
                        Image(systemName: uploader.uploading ? "arrow.up.circle" : "camera.fill")
                            .font(.system(size: 11, weight: .semibold))
                        Text(uploader.uploading ? "Uploading…" : "Edit")
                            .font(.hearthBodySM.weight(.semibold))
                    }
                    .foregroundColor(.inkOnPhotoLight)
                    .padding(.horizontal, .hearth400)
                    .padding(.vertical, 6)
                    .background(Capsule().fill(Color.accentDefault))
                }
                .disabled(uploader.uploading || baseURL == nil)
                .offset(y: 10)
                .accessibilityLabel(avatarUrl == nil ? "Add a photo" : "Change photo")
            }
            .padding(.bottom, 10)

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
                await uploader.upload(item, kidName: kidName, userID: userID,
                                      baseURL: baseURL, onProfileRefreshed: onProfileRefreshed)
                pickerItem = nil
            }
        }
    }
}
