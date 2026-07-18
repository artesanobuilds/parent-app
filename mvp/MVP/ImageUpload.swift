import UIKit

// Shared image-preparation helpers for anything uploaded to the backend.
// Promoted out of IngestView (where normalizedForUpload started life private)
// so avatars and flyer ingestion share ONE resize/orientation policy.
extension UIImage {
    /// Downscale to a max dimension and bake in orientation so the upload stays
    /// well under the backend's 8 MB cap. Camera photos are often 4000px+;
    /// 2000px is plenty for OCR-style extraction, 512px for avatars.
    func normalizedForUpload(maxDimension: CGFloat = 2000) -> UIImage {
        let longest = max(size.width, size.height)
        let scale = longest > maxDimension ? maxDimension / longest : 1
        let target = CGSize(width: size.width * scale, height: size.height * scale)
        let format = UIGraphicsImageRendererFormat.default()
        format.scale = 1
        return UIGraphicsImageRenderer(size: target, format: format).image { _ in
            draw(in: CGRect(origin: .zero, size: target))
        }
    }

    /// Center-crop to a square (for circular avatar display). Crop first, then
    /// `normalizedForUpload(maxDimension: 512)` for the upload variant.
    func squareCropped() -> UIImage {
        let side = min(size.width, size.height)
        let origin = CGPoint(x: (size.width - side) / 2, y: (size.height - side) / 2)
        let format = UIGraphicsImageRendererFormat.default()
        format.scale = 1
        return UIGraphicsImageRenderer(size: CGSize(width: side, height: side), format: format)
            .image { _ in
                draw(at: CGPoint(x: -origin.x, y: -origin.y))
            }
    }
}
