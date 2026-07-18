import SwiftUI
import PhotosUI

// MARK: - Avatar display

/// Circular profile photo with an SF Symbol fallback. `urlString` is the
/// presigned avatar_url from GET /profile (short-lived, display-only).
struct AvatarCircleView: View {
    let urlString: String?
    let fallbackSystemImage: String
    var size: CGFloat = 28

    var body: some View {
        Group {
            if let urlString, let url = URL(string: urlString) {
                AsyncImage(url: url) { phase in
                    if case .success(let image) = phase {
                        image.resizable().scaledToFill()
                    } else {
                        fallbackIcon
                    }
                }
            } else {
                fallbackIcon
            }
        }
        .frame(width: size, height: size)
        .clipShape(Circle())
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

// MARK: - Avatar picker (profile editors)

/// Photo-library picker row for the profile editors (parent when `kidName` is
/// nil, else that kid). Photo library ONLY — no camera; the Info.plist camera
/// string says "MVP never uses the camera" and must stay true. Uploads via
/// BlobService (presign → PUT → durable attach) and re-fetches the profile so
/// the editor's caller sees the new photo immediately.
struct AvatarPickerRow: View {
    let avatarUrl: String?
    let kidName: String?
    let userID: String
    let baseURL: URL?
    var onProfileRefreshed: (FamilyProfileDTO) -> Void

    @State private var pickerItem: PhotosPickerItem?
    @State private var localImage: UIImage?
    @State private var uploading = false
    @State private var uploadError: String?

    var body: some View {
        HStack(spacing: .hearth500) {
            if let localImage {
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
                    Text(uploading ? "Uploading…"
                         : (avatarUrl == nil && localImage == nil ? "Add photo" : "Change photo"))
                        .font(.hearthBodyMD.weight(.semibold))
                        .foregroundColor(uploading ? .inkMuted : .accentDefault)
                }
                .disabled(uploading || baseURL == nil)

                if let uploadError {
                    Text(uploadError)
                        .font(.hearthBodySM)
                        .foregroundColor(.statusError)
                }
            }
        }
        .onChange(of: pickerItem) { _, item in
            guard let item else { return }
            Task { await upload(item) }
        }
    }

    @MainActor
    private func upload(_ item: PhotosPickerItem) async {
        guard let baseURL else { return }
        uploading = true
        uploadError = nil
        defer {
            uploading = false
            pickerItem = nil
        }
        guard let data = try? await item.loadTransferable(type: Data.self),
              let image = UIImage(data: data) else {
            uploadError = "Couldn't read that photo — try a different one."
            return
        }
        // Instant local feedback while the upload runs.
        localImage = image.squareCropped().normalizedForUpload(maxDimension: 512)
        do {
            try await BlobService.uploadAvatar(image, kidName: kidName,
                                               userID: userID, baseURL: baseURL)
            // Source-of-truth re-fetch (CLAUDE.md rule) so rows outside this
            // editor render the new photo without a relaunch.
            if let fam = try? await ProfileService.getProfile(baseURL: baseURL, userID: userID) {
                onProfileRefreshed(fam)
            }
        } catch {
            localImage = nil
            uploadError = (error as? LocalizedError)?.errorDescription
                ?? "The photo didn't upload. Please try again."
        }
    }
}
