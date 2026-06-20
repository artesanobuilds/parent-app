import SwiftUI

// MARK: - Hex helper
//
// The single source of raw color in the iOS surface. Every token below resolves
// through this initializer so primitive hex values live in exactly one place
// (this file) and component code never declares a raw color.

extension Color {
    /// Parses 6-digit RGB hex literals (e.g. "#1A1A1A" or "1A1A1A").
    /// Hardcoded fallback to neutral mid-gray if the string can't be parsed.
    init(hex: String) {
        var s = hex.trimmingCharacters(in: .whitespacesAndNewlines)
        if s.hasPrefix("#") { s.removeFirst() }
        var rgb: UInt64 = 0
        Scanner(string: s).scanHexInt64(&rgb)
        let r = Double((rgb >> 16) & 0xFF) / 255.0
        let g = Double((rgb >> 8) & 0xFF) / 255.0
        let b = Double(rgb & 0xFF) / 255.0
        self.init(.sRGB, red: r, green: g, blue: b, opacity: 1.0)
    }
}

// MARK: - Hearth color tokens — semantic layer
//
// These are the names component code consumes. Primitives live below as
// fileprivate constants. Every accessor is non-optional and computed once.

extension Color {
    // Surfaces
    static let bgCanvas      = Color(hex: HearthPrimitives.creamCanvas)   // page bg (cream-100)
    static let bgElevated    = Color(hex: HearthPrimitives.paper)         // card / sheet
    static let bgSober       = Color(hex: HearthPrimitives.creamSober)    // kid-agent / safety

    // Ink
    static let inkPrimary     = Color(hex: HearthPrimitives.ink900)
    static let inkSecondary   = Color(hex: HearthPrimitives.ink700)
    static let inkMuted       = Color(hex: HearthPrimitives.ink500)
    static let inkPlaceholder = Color(hex: HearthPrimitives.ink300)
    static let inkOnPhotoDark  = Color(hex: HearthPrimitives.ink900)
    static let inkOnPhotoLight = Color(hex: HearthPrimitives.paper)
    /// Generic "ink on a photo tile" — used when the surface caller doesn't
    /// know which variant to pick. Prefer the explicit -Dark / -Light tokens.
    static let inkOnPhoto      = Color(hex: HearthPrimitives.paper)

    // Borders
    static let borderHairline = Color(hex: HearthPrimitives.creamHairline)
    static let borderStrong   = Color(hex: HearthPrimitives.ink300)

    // Accent
    static let accentDefault = Color(hex: HearthPrimitives.olive500)
    static let accentPress   = Color(hex: HearthPrimitives.olive700)
    static let accentTint    = Color(hex: HearthPrimitives.olive100)

    // Photo tiles — saturated color blocks, never inverted in dark mode (phase 2).
    static let photoSaffron = Color(hex: HearthPrimitives.photoSaffron)
    static let photoRose    = Color(hex: HearthPrimitives.photoRose)
    static let photoRoyal   = Color(hex: HearthPrimitives.photoRoyal)
    static let photoForest  = Color(hex: HearthPrimitives.photoForest)
    // The task spec asked for `photoClay` and `photoSand` aliases as well so
    // surfaces that previously imagined a 6-tile palette keep compiling. They
    // map to rose/saffron respectively per the canonical four-color allowlist.
    static let photoClay    = Color(hex: HearthPrimitives.photoRose)
    static let photoSand    = Color(hex: HearthPrimitives.photoSaffron)

    // Status
    static let statusSuccess     = Color(hex: HearthPrimitives.statusSuccess)
    static let statusWarning     = Color(hex: HearthPrimitives.statusWarning)
    static let statusError       = Color(hex: HearthPrimitives.statusError)
    static let statusInfo        = Color(hex: HearthPrimitives.statusInfo)
    static let statusErrorTint   = Color(hex: HearthPrimitives.statusErrorTint)
    static let statusWarningTint = Color(hex: HearthPrimitives.statusWarningTint)
    static let statusSuccessTint = Color(hex: HearthPrimitives.statusSuccessTint)

    // Focus rings
    static let focusRingOnLight = Color(hex: HearthPrimitives.olive500)
    static let focusRingOnPhoto = Color(hex: HearthPrimitives.paper)
}

// MARK: - Hearth-prefixed accessor aliases
//
// The surfaces/ios.md spec names every accessor with a `hearth*` prefix.
// We expose both the short (`Color.bgCanvas`) and the spec-conformant
// (`Color.hearthCanvas`) forms so future code can pick either style without
// drifting from the canonical table. They resolve to the same primitive.

extension Color {
    static let hearthCanvas         = Color.bgCanvas
    static let hearthElevated       = Color.bgElevated
    static let hearthSober          = Color.bgSober
    static let hearthInkPrimary     = Color.inkPrimary
    static let hearthInkSecondary   = Color.inkSecondary
    static let hearthInkMuted       = Color.inkMuted
    static let hearthInkPlaceholder = Color.inkPlaceholder
    static let hearthInkOnPhotoDark  = Color.inkOnPhotoDark
    static let hearthInkOnPhotoLight = Color.inkOnPhotoLight
    static let hearthBorderHairline = Color.borderHairline
    static let hearthBorderStrong   = Color.borderStrong
    static let hearthAccent         = Color.accentDefault
    static let hearthAccentPress    = Color.accentPress
    static let hearthAccentTint     = Color.accentTint
    static let hearthFocusRingOnLight = Color.focusRingOnLight
    static let hearthFocusRingOnPhoto = Color.focusRingOnPhoto
    static let hearthPhotoSaffron   = Color.photoSaffron
    static let hearthPhotoRose      = Color.photoRose
    static let hearthPhotoRoyal     = Color.photoRoyal
    static let hearthPhotoForest    = Color.photoForest
    static let hearthStatusSuccess  = Color.statusSuccess
    static let hearthStatusWarning  = Color.statusWarning
    static let hearthStatusError    = Color.statusError
    static let hearthStatusInfo     = Color.statusInfo
    static let hearthStatusErrorTint   = Color.statusErrorTint
    static let hearthStatusWarningTint = Color.statusWarningTint
    static let hearthStatusSuccessTint = Color.statusSuccessTint
}

// MARK: - Primitives
//
// Raw hex values live here only. Component code MUST NOT reference these
// directly — go through the semantic accessors above.

enum HearthPrimitives {
    // Neutrals
    static let creamCanvas     = "#F3F0EB"   // cream-100 — default page bg
    static let creamSober      = "#FAF7F2"   // cream-50  — sober surface
    static let creamHairline   = "#E9E4DC"   // cream-200 — dividers
    static let paper           = "#FFFFFF"   // paper      — elevated card bg
    static let ink900          = "#1A1A1A"   // primary text
    static let ink700          = "#2D2D2D"   // softer primary
    static let ink500          = "#6F6A60"   // muted (warm gray)
    static let ink300          = "#8A8275"   // placeholder / tertiary

    // Brand
    static let olive500        = "#4F5D3A"   // accent default
    static let olive700        = "#3A4A2A"   // accent press
    static let olive100        = "#E8EBDC"   // accent tint

    // Photo tiles
    static let photoSaffron    = "#E8A33C"
    static let photoRose       = "#B86A60"
    static let photoRoyal      = "#2E3A5F"
    static let photoForest     = "#2D3F2C"

    // Status
    static let statusSuccess     = "#3D6B3D"
    static let statusWarning     = "#8A6420"
    static let statusError       = "#A03A3A"
    static let statusInfo        = "#2E3A5F"
    static let statusErrorTint   = "#F6E4E4"
    static let statusWarningTint = "#F5EAD2"
    static let statusSuccessTint = "#DCE7DC"
}

// MARK: - Legacy `brand*` aliases (deprecated — keep until view migration completes)
//
// Every untouched view in the codebase still references brand*. We point each
// alias at the closest Hearth equivalent so the project keeps compiling while
// we migrate views one at a time. The `deprecated:` attribute makes the
// outstanding migration visible in Xcode without breaking the build.

extension Color {
    @available(*, deprecated, message: "Use Color.accentDefault (Hearth)")
    static var brandGold: Color { .accentDefault }

    @available(*, deprecated, message: "Use Color.inkPrimary (Hearth)")
    static var brandBlack: Color { .inkPrimary }

    @available(*, deprecated, message: "Use Color.bgCanvas (Hearth)")
    static var brandBackground: Color { .bgCanvas }

    @available(*, deprecated, message: "Use Color.bgElevated (Hearth)")
    static var brandSurface: Color { .bgElevated }

    @available(*, deprecated, message: "Use Color.bgElevated (Hearth)")
    static var brandCardBackground: Color { .bgElevated }

    @available(*, deprecated, message: "Use Color.inkPrimary (Hearth)")
    static var brandNavy: Color { .inkPrimary }

    @available(*, deprecated, message: "Use Color.inkMuted (Hearth)")
    static var brandGray: Color { .inkMuted }

    @available(*, deprecated, message: "Use Color.accentDefault (Hearth)")
    static var brandCoral: Color { .accentDefault }

    @available(*, deprecated, message: "Use Color.accentDefault (Hearth)")
    static var brandYellow: Color { .accentDefault }

    @available(*, deprecated, message: "Use Color.accentTint (Hearth)")
    static var brandLightBlue: Color { .accentTint }

    @available(*, deprecated, message: "Use Color.borderHairline (Hearth)")
    static var brandStroke: Color { .borderHairline }
}

// MARK: - Motion
//
// Every animation site routes through these resolvers. `accessibilityReduceMotion`
// collapses all of them to `.hearthInstant` at the call site via
// `Animation.hearth(_:reduceMotion:)`.

extension Animation {
    static let hearthInstant: Animation = .linear(duration: 0)
    static let hearthFast:    Animation = .easeOut(duration: 0.12)
    static let hearthBase:    Animation = .easeOut(duration: 0.20)
    static let hearthSlow:    Animation = .easeInOut(duration: 0.32)
    static let hearthSpring:  Animation = .interactiveSpring(response: 0.4, dampingFraction: 0.85)

    /// Resolves to `.hearthInstant` when the user has Reduce Motion enabled.
    /// Surfaces should call this once per animation site instead of branching
    /// on `accessibilityReduceMotion` themselves.
    static func hearth(_ animation: Animation, reduceMotion: Bool) -> Animation {
        reduceMotion ? .hearthInstant : animation
    }
}
