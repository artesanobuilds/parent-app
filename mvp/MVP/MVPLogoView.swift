import SwiftUI

// MARK: - Typographic mark
//
// We tried a geometric hearth glyph (arch + ember) in three iterations.
// Each one collapsed into a different cliche (padlock, then a face, then
// an Eye-of-Providence). Symmetric curve over a central dot is hardwired
// face-grammar; the concept needs a designer's hand to escape, not Canvas
// shape code.
//
// The pivot is Direction A from logo.md: the wordmark IS the logo. The
// App Store icon falls back to a single oversized Fraunces "M". Clean,
// confident, internally coherent with the rest of the type system.

/// The Hearth mark — a single oversized Fraunces letter "M". Used as the
/// App Store icon, favicon, and any standalone-mark context. Kept around
/// as a SwiftUI view (vs purely an asset image) so call sites can tint
/// for sober variants and scale arbitrarily without re-export.
struct HearthMark: View {
    /// Width/height of the bounding box. Mark renders centered + square.
    var size: CGFloat = 64
    /// Single-color tint. Defaults to ink/primary on light surfaces;
    /// switch to `.inkOnPhotoLight` (paper white) on dark photo tiles
    /// or `.inkOnPhotoDark` (near-black) on warm photo tiles.
    var tint: Color = .inkPrimary

    var body: some View {
        // The "M" is set in Fraunces ExtraBold (variable wght → 900).
        // Optical size axis (opsz) is at its largest setting so the M's
        // serifs read as architectural at icon scale.
        Text("M")
            .font(.custom("Fraunces", size: size * 0.80).weight(.heavy))
            .foregroundColor(tint)
            .frame(width: size, height: size)
            .accessibilityHidden(true)
    }
}

// MARK: - MVP wordmark + lockups
//
// One file ships every variant. Call sites pick a style; the SwiftUI
// composition handles spacing + alignment + tint inheritance.

/// The MVP wordmark. Three variants:
/// - `.lockup`   — full wordmark "MVP" at display scale (launch screen, splash)
/// - `.wordmark` — wordmark in nav/footer scale (smaller of the same thing)
/// - `.mark`     — standalone "M" only (favicon, app icon crop, watermark)
struct MVPLogoView: View {
    enum Variant {
        case lockup
        case wordmark
        case mark
    }

    var variant: Variant = .lockup
    /// Total width hint. The view sizes itself proportionally.
    var size: CGFloat = 200
    /// Single-color tint applied to all variants.
    var tint: Color = .inkPrimary

    var body: some View {
        switch variant {
        case .lockup, .wordmark:
            wordmarkText
                .frame(width: size)
                .accessibilityElement(children: .ignore)
                .accessibilityLabel("MVP")

        case .mark:
            HearthMark(size: size, tint: tint)
                .accessibilityElement(children: .ignore)
                .accessibilityLabel("MVP")
        }
    }

    // MARK: - Wordmark

    private var wordmarkText: some View {
        // Fraunces ExtraBold at display scale. Tracking nudged tighter
        // (~ -2%) at large sizes; Fraunces' variable optical-size axis
        // (opsz) handles size-specific letterform optimization in the
        // font itself.
        Text("MVP")
            .font(.custom("Fraunces", size: size * 0.30).weight(.heavy))
            .tracking(size * -0.006)
            .foregroundColor(tint)
            .multilineTextAlignment(.center)
    }
}

// MARK: - Previews

#Preview("Lockup on cream") {
    ZStack {
        Color.bgCanvas.ignoresSafeArea()
        MVPLogoView(variant: .lockup, size: 240, tint: .inkPrimary)
    }
}

#Preview("Mark only — launch / icon scale") {
    ZStack {
        Color.bgCanvas.ignoresSafeArea()
        MVPLogoView(variant: .mark, size: 200, tint: .inkPrimary)
    }
}

#Preview("Wordmark — nav scale") {
    ZStack {
        Color.bgCanvas.ignoresSafeArea()
        MVPLogoView(variant: .wordmark, size: 120, tint: .inkPrimary)
    }
}

#Preview("On saffron tile (app-icon composition)") {
    ZStack {
        Color.photoSaffron.ignoresSafeArea()
        MVPLogoView(variant: .mark, size: 240, tint: .inkOnPhotoDark)
    }
}
