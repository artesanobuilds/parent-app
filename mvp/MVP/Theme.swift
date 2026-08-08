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
// constants on `HearthPrimitives`. Every accessor is non-optional.
//
// beta-v1 (Greg): the accent family moved olive → teal, a second KID accent
// (saffron) was introduced for companion surfaces, and the canvas darkened
// from cream-100 to cream-200. That last change silently broke two AA pairs
// that used to pass on the lighter ground — see `accentOnCanvas` and
// `inkMuted` below. Do not "restore" the old values without re-running the
// contrast check in the beta-v1 redesign notes.

extension Color {
    // Surfaces
    static let bgCanvas      = Color(hex: HearthPrimitives.creamCanvas)   // page bg (cream-200)
    static let bgElevated    = Color(hex: HearthPrimitives.paper)         // card / sheet
    static let bgSober       = Color(hex: HearthPrimitives.creamSober)    // kid-agent / safety
    /// Sheet + card ground on the account/profile sheet (`#F5F3EF`). A half-step
    /// lighter than `bgSober` and distinctly lighter than `bgCanvas` — the sheet
    /// has to read as lifted off the page behind it.
    static let bgCard        = Color(hex: HearthPrimitives.cardCream)
    /// Selected state for the tab pill and the Saved/History segmented control.
    /// A warm gray-green — NOT `accentTint` (`#DCE9EF`), which is visibly bluer.
    static let bgSelected    = Color(hex: HearthPrimitives.tabSelected)
    /// Neutral grey control fill (sign-out). Distinct from `bgDisabled`, which is
    /// the warm `#B8B4AC`.
    static let bgNeutral     = Color(hex: HearthPrimitives.neutralGray500)
    /// Kid voice-call surface — the only dark ground in the light-locked app.
    /// Not a dark-mode token: it is a deliberate full-bleed surface color.
    static let bgVoice       = Color(hex: HearthPrimitives.voiceNavy)
    /// Disabled control fill (Greg's inert "Continue"). Pair with `inkSecondary`,
    /// never with `inkOnPhotoLight` — white on this fill is 2.07:1.
    static let bgDisabled    = Color(hex: HearthPrimitives.warmGray400)

    // Ink
    static let inkPrimary     = Color(hex: HearthPrimitives.ink900)
    /// Headline + subtitle ink on the account sheet (`#1E1E1E`).
    static let inkDisplay     = Color(hex: HearthPrimitives.ink800)
    /// Card/section header ink (`#2B2925`) — "Family interests", "Account".
    static let inkHeader      = Color(hex: HearthPrimitives.inkHeader)
    static let inkSecondary   = Color(hex: HearthPrimitives.ink700)
    static let inkMuted       = Color(hex: HearthPrimitives.ink500)
    static let inkPlaceholder = Color(hex: HearthPrimitives.ink300)
    static let inkOnPhotoDark  = Color(hex: HearthPrimitives.ink900)
    static let inkOnPhotoLight = Color(hex: HearthPrimitives.paper)
    /// Ink on a teal card (`#F5F3EF`). Deliberately the warm cream, not pure
    /// white — the design uses the same value for the card ground and for text on
    /// teal, which is what keeps those cards from feeling clinical. 4.74:1 on
    /// `accentDefault`, so it passes AA as text.
    static let inkOnCard       = Color(hex: HearthPrimitives.cardCream)
    /// Generic "ink on a photo tile" — used when the surface caller doesn't
    /// know which variant to pick. Prefer the explicit -Dark / -Light tokens.
    static let inkOnPhoto      = Color(hex: HearthPrimitives.paper)

    // Borders
    static let borderHairline = Color(hex: HearthPrimitives.creamHairline)
    static let borderStrong   = Color(hex: HearthPrimitives.ink300)

    // Accent — teal (beta-v1)
    //
    // `accentDefault` is a FILL color: white on it is 5.25:1 (AA pass), which
    // is how Greg uses it on every primary button. As TEXT on `bgCanvas` the
    // same hex is only 4.15:1 — a fail. `accentOnCanvas` is the slightly
    // darker sibling for accent-colored TEXT or ICONS drawn directly on cream
    // (links, "See all", the active tab label). Same split idea as the two
    // focus-ring tokens: pick per surface, there is no universal accent.
    static let accentDefault  = Color(hex: HearthPrimitives.teal500)
    static let accentOnCanvas = Color(hex: HearthPrimitives.teal600)
    static let accentPress    = Color(hex: HearthPrimitives.teal700)
    static let accentTint     = Color(hex: HearthPrimitives.teal100)

    // Kid accent — saffron (beta-v1)
    //
    // Companion avatars, kid monograms, kid-card borders. `inkPrimary` on
    // saffron is 7.65:1; white on saffron is only 2.28:1, so white is allowed
    // ONLY for the decorative monogram letter, which never carries information
    // on its own (the kid's name is always rendered adjacent to it).
    static let accentKid     = Color(hex: HearthPrimitives.kidSaffron)
    static let accentKidTint = Color(hex: HearthPrimitives.kidSaffronTint)

    // Photo tiles — saturated color blocks, never inverted in dark mode.
    static let photoSaffron = Color(hex: HearthPrimitives.photoSaffron)
    static let photoRose    = Color(hex: HearthPrimitives.photoRose)
    static let photoRoyal   = Color(hex: HearthPrimitives.photoRoyal)
    static let photoForest  = Color(hex: HearthPrimitives.photoForest)
    // Aliases kept so surfaces that imagined a 6-tile palette keep compiling.
    // They map to rose/saffron per the canonical four-color allowlist.
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
    static let focusRingOnLight = Color(hex: HearthPrimitives.teal600)
    static let focusRingOnPhoto = Color(hex: HearthPrimitives.paper)
}

// MARK: - Per-kid accent

extension Color {
    /// The ordered kid-accent palette. Greg's dashboard gives each kid card its
    /// own border color (saffron for the first kid, teal for the second).
    static let kidAccentPalette: [Color] = [
        Color(hex: HearthPrimitives.kidSaffron),
        Color(hex: HearthPrimitives.teal500),
        Color(hex: HearthPrimitives.photoRose),
        Color(hex: HearthPrimitives.photoForest)
    ]

    /// Deterministic kid accent from a STABLE identifier.
    ///
    /// Pass the most stable id the caller has — the kid-agent config `id` when
    /// one exists, falling back to the kid's name only when it doesn't. Keying
    /// off an editable display name means the color changes on rename, which is
    /// the same class of bug as using a name as a dictionary key (see the
    /// name-as-key note in CLAUDE.md). Index-based assignment is deliberately
    /// NOT offered: deleting the first kid would recolor every remaining one.
    static func kidAccent(seed: String) -> Color {
        guard !seed.isEmpty else { return kidAccentPalette[0] }
        // FNV-1a — a stable hash. Swift's `hashValue` is per-process seeded and
        // would give a different color on every launch.
        var hash: UInt64 = 0xcbf29ce484222325
        for byte in seed.utf8 {
            hash ^= UInt64(byte)
            hash = hash &* 0x100000001b3
        }
        return kidAccentPalette[Int(hash % UInt64(kidAccentPalette.count))]
    }
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
    static let hearthVoice          = Color.bgVoice
    static let hearthDisabled       = Color.bgDisabled
    static let hearthInkPrimary     = Color.inkPrimary
    static let hearthInkSecondary   = Color.inkSecondary
    static let hearthInkMuted       = Color.inkMuted
    static let hearthInkPlaceholder = Color.inkPlaceholder
    static let hearthInkOnPhotoDark  = Color.inkOnPhotoDark
    static let hearthInkOnPhotoLight = Color.inkOnPhotoLight
    static let hearthBorderHairline = Color.borderHairline
    static let hearthBorderStrong   = Color.borderStrong
    static let hearthAccent         = Color.accentDefault
    static let hearthAccentOnCanvas = Color.accentOnCanvas
    static let hearthAccentPress    = Color.accentPress
    static let hearthAccentTint     = Color.accentTint
    static let hearthAccentKid      = Color.accentKid
    static let hearthAccentKidTint  = Color.accentKidTint
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
//
// Values sampled from the beta-v1 Figma renders. Re-verify against
// `get_variable_defs` on node 442:2 once the file grants edit access; the
// sampled values are pixel-accurate but the variable NAMES are not yet known.

enum HearthPrimitives {
    // Neutrals
    static let creamCanvas     = "#E9E4DC"   // cream-200 — default page bg (beta-v1)
    static let creamSober      = "#F3F0EB"   // cream-100 — sober surface (the pre-beta canvas)
    static let creamHairline   = "#DAD4CA"   // cream-300 — dividers; darkened to stay visible on the new canvas
    static let paper           = "#FFFFFF"   // paper      — elevated card bg
    static let warmGray400     = "#B8B4AC"   // disabled control fill
    static let ink900          = "#1A1A1A"   // primary text
    static let ink800          = "#1E1E1E"   // sheet headline + subtitle (account sheet)
    static let ink700          = "#2D2D2D"   // softer primary
    static let inkHeader       = "#2B2925"   // card/section header ink + the sheet scrim
    static let ink500          = "#666157"   // muted (warm gray) — darkened from #6F6A60 for AA on cream-200
    static let ink300          = "#8A8275"   // placeholder / tertiary (3.00:1 on canvas — UI floor exactly)
    static let cardCream       = "#F5F3EF"   // sheet/card ground; also the INK on teal article cards
    static let tabSelected     = "#DAE0DF"   // selected tab pill + selected segmented control
    static let neutralGray500  = "#858585"   // sign-out fill (neutral, not the warm warmGray400)

    // Brand — teal (beta-v1)
    //
    // teal500 and teal600 are DELIBERATELY the same value. The two names encode
    // WHERE a colour is used (fill vs text/icon on cream), and that distinction
    // is load-bearing: `#1B7498` on `creamCanvas` measures **4.15:1**, which
    // fails WCAG AA for text under 18.66px — so the 11px nav labels and every
    // small teal label are non-compliant AS DRAWN. `teal600` was `#186A8B`
    // (4.78:1, AA-passing and visually indistinguishable) until 2026-08-07,
    // when Miguel chose exact-Figma fidelity over the fix. Keeping the split
    // means reverting is ONE primitive edit rather than re-auditing every call
    // site. The waiver is recorded in tools/lint-design-tokens.py with the
    // measured ratios.
    static let teal500         = "#1B7498"   // accent fill (Greg's exact value)
    static let teal600         = "#1B7498"   // accent as TEXT/ICON on cream — see note above
    static let teal700         = "#12556F"   // accent press
    static let teal100         = "#DCE9EF"   // accent tint

    // Kid accent (beta-v1)
    static let kidSaffron      = "#E89C2E"
    static let kidSaffronTint  = "#F8EBD6"   // companion card ground

    // Voice surface (beta-v1) — shares its hex with photo/royal, intentional
    static let voiceNavy       = "#2E3A5F"

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

// MARK: - Elevation
//
// beta-v1 REVERSES the pre-beta rule. Hearth used to lift cards with
// `border/hairline` + `bg/elevated` and reserved shadows for true overlays.
// Greg's dashboard and kid-settings sheet use a soft ambient shadow on every
// card and no hairline at all, so the shadow is now the card default and the
// hairline is demoted to dividers and inputs.
//
// Applied through these modifiers rather than raw `.shadow(...)` calls so the
// recipe stays in one place.

extension View {
    /// Card elevation — the beta-v1 default for content cards on `bgCanvas`.
    func hearthCardElevation() -> some View {
        shadow(color: Color(hex: HearthPrimitives.ink900).opacity(0.06), radius: 10, x: 0, y: 3)
    }

    /// Overlay elevation — sheets, modals, drawers.
    func hearthOverlayElevation() -> some View {
        shadow(color: Color(hex: HearthPrimitives.ink900).opacity(0.12), radius: 32, x: 0, y: 12)
    }

    /// Sticky nav / raised toast.
    func hearthNavElevation() -> some View {
        shadow(color: Color(hex: HearthPrimitives.ink900).opacity(0.08), radius: 12, x: 0, y: 4)
    }
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
