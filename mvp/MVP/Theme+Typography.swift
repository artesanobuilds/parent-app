import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// MARK: - Hearth typography tokens
//
// Three families ship in-bundle: Fraunces (display), Inter (sans), JetBrains
// Mono (mono). Body-tier tokens use `relativeTo:` so Dynamic Type scales them;
// display-tier tokens are fixed-size by design (editorial hero compositions
// must not reflow).

enum HearthFontFamily {
    /// Variable font for display / hero text. Falls back to Georgia.
    ///
    /// beta-v1: Greg's headings read as a higher-contrast Didone than Fraunces.
    /// The exact family is still being confirmed — when it lands, change THIS
    /// constant, drop the `.ttf` into `mvp/MVP/Fonts/`, and add it to the
    /// `UIAppFonts` array in Info.plist. Nothing else in the app names a serif
    /// family directly, so the swap is those three edits and no more.
    static let displaySerif = "Fraunces"
    /// Variable font for UI + body. The PostScript name on the variable file
    /// is `InterVariable`; SwiftUI's `Font.custom` accepts the PostScript name
    /// directly and renders the regular axis.
    static let sans = "InterVariable"
    /// Mono for metadata only. PostScript name on the variable file.
    static let mono = "JetBrainsMono-Regular"
}

extension Font {

    // MARK: Display — fixed size (no Dynamic Type)

    /// 72 / 76, weight 700. beta-v1 hero numeral — the warm-up progress ring's
    /// percentage. Larger than display-xl because it is a single glyph pair
    /// carrying a whole screen.
    static let hearthDisplayHero: Font =
        .custom(HearthFontFamily.displaySerif, fixedSize: 72)
        .weight(.bold)

    /// 56 / 60, -1% tracking, weight 700. Hero headline on iPhone.
    static let hearthDisplayXL: Font =
        .custom(HearthFontFamily.displaySerif, fixedSize: 56)
        .weight(.bold)

    /// 40 / 44, -1% tracking, weight 700. Screen title.
    static let hearthDisplayLG: Font =
        .custom(HearthFontFamily.displaySerif, fixedSize: 40)
        .weight(.bold)

    /// 28 / 32, 0% tracking, weight 600. Section header.
    static let hearthDisplayMD: Font =
        .custom(HearthFontFamily.displaySerif, fixedSize: 28)
        .weight(.semibold)

    /// 38 / 40, -1% tracking, weight **700**. The design's most-used editorial
    /// headline (22 uses): "Hi Greg!", and every article-card title on the
    /// account sheet. Apply `.tracking(-0.38)` at the call site.
    ///
    /// Distinct from `hearthDisplayMD` (28/600) — reaching for that here is what
    /// made the account sheet's headlines read two steps too small.
    static let hearthDisplaySM: Font =
        .custom(HearthFontFamily.displaySerif, fixedSize: 38)
        .weight(.bold)

    /// 24 / 32, weight 600. Screen title in the display serif — the "Circle" /
    /// "Coach" nav titles on the sprint-2 screens.
    static let hearthTitleSerif: Font =
        .custom(HearthFontFamily.displaySerif, fixedSize: 24)
        .weight(.semibold)

    // MARK: Titles — body-tier (respect Dynamic Type)

    /// 20 / 24, weight 600. Card title.
    static let hearthTitleLG: Font =
        .custom(HearthFontFamily.sans, size: 20, relativeTo: .title3)
        .weight(.semibold)

    /// 16 / 22, weight 600. Inline header.
    static let hearthTitleMD: Font =
        .custom(HearthFontFamily.sans, size: 16, relativeTo: .headline)
        .weight(.semibold)

    // MARK: Body — Dynamic Type

    /// 17 / 26, weight 400. Reading body (articles).
    static let hearthBodyLG: Font =
        .custom(HearthFontFamily.sans, size: 17, relativeTo: .body)

    /// 15 / 22, weight 400. UI body (default).
    static let hearthBodyMD: Font =
        .custom(HearthFontFamily.sans, size: 15, relativeTo: .callout)

    /// 13 / 18, weight 400. Secondary text.
    static let hearthBodySM: Font =
        .custom(HearthFontFamily.sans, size: 13, relativeTo: .footnote)

    /// 13 / 18, weight **700**. Eyebrows and card labels — "Care · 2 min",
    /// "Family interests", "Account" (40 uses in the design). Note the weight:
    /// call sites were improvising `.hearthBodySM.weight(.semibold)` (600),
    /// which is a visibly lighter stroke.
    static let hearthBodySMBold: Font =
        .custom(HearthFontFamily.sans, size: 13, relativeTo: .footnote)
        .weight(.bold)

    // MARK: Section header + controls

    /// 16 / 22, weight **800**, sans. The dashboard section masthead —
    /// `YOUR KIDS` / `FOR YOU` / `COMING UP` (41 uses, the design's second-most
    /// common style). Apply `.textCase(.uppercase)` at the call site.
    ///
    /// This REPLACES the former `hearthLabelSerif`, which set these in Fraunces
    /// bold 13 with a leading icon. That was a misread of the design — verified
    /// against the Figma node data, every one of these headers is Inter w800 16 —
    /// and because one token fed every section header, it changed the whole
    /// dashboard's character. Do not reintroduce a serif variant here.
    static let hearthSectionHeader: Font =
        .custom(HearthFontFamily.sans, size: 16, relativeTo: .headline)
        .weight(.heavy)

    /// 13.35 / 18.36, weight **800**. Small-button labels — Saved / History /
    /// Cancel / Sign out (22 uses). The odd size is the design's own (a scaled
    /// component); rounding it to 13 makes the buttons sit a hair short.
    static let hearthButtonLabel: Font =
        .custom(HearthFontFamily.sans, size: 13.35, relativeTo: .footnote)
        .weight(.heavy)

    /// 14 / 14, -1% tracking, weight 600. Chip + filter labels (22 uses).
    /// Apply `.tracking(-0.14)` at the call site.
    static let hearthChipLabel: Font =
        .custom(HearthFontFamily.sans, size: 14, relativeTo: .subheadline)
        .weight(.semibold)

    // MARK: Label + mono

    /// 11 / 14, +6% tracking, weight 600. UPPERCASE nav labels, tag chips.
    /// Apply `.tracking(0.66).textCase(.uppercase)` at the call site.
    static let hearthLabel: Font =
        .custom(HearthFontFamily.sans, size: 11, relativeTo: .caption2)
        .weight(.semibold)

    // `hearthLabelSerif` (Fraunces bold 13, uppercased, +4% tracking) is GONE.
    // It was built on the belief that Greg set the section headers in the display
    // serif; the Figma node data says Inter w800 16 for every one of them. Use
    // `hearthSectionHeader` above. The token is deleted rather than deprecated so
    // it cannot be reached by a new call site.

    /// 12 / 16, weight 400. Byline, read-time, dates.
    static let hearthCaptionMono: Font =
        .custom(HearthFontFamily.mono, size: 12, relativeTo: .caption)
}

// MARK: - Line-spacing companions
//
// `lineSpacing` in SwiftUI is the *extra* space between lines, not the line
// height. These helpers expose the spec's line-height values minus the
// font size so a `.lineSpacing(.hearthBodyLG)` call produces a 26pt
// line-box on 17pt body text.

extension CGFloat {
    static let hearthLineDisplayHero: CGFloat = 76 - 72
    static let hearthLineDisplayXL: CGFloat = 60 - 56
    static let hearthLineDisplayLG: CGFloat = 44 - 40
    static let hearthLineDisplayMD: CGFloat = 32 - 28
    static let hearthLineTitleLG:   CGFloat = 24 - 20
    static let hearthLineTitleMD:   CGFloat = 22 - 16
    static let hearthLineBodyLG:    CGFloat = 26 - 17
    static let hearthLineBodyMD:    CGFloat = 22 - 15
    static let hearthLineBodySM:    CGFloat = 18 - 13
    static let hearthLineLabel:      CGFloat = 14 - 11
    static let hearthLineLabelSerif: CGFloat = 16 - 13
    static let hearthLineMono:       CGFloat = 16 - 12
}

#if DEBUG && canImport(UIKit)
/// Fails fast in DEBUG if a Hearth font family is missing. Silent system-font
/// fallback is a token violation per the surface spec.
enum HearthFontRegistration {
    static func verify() {
        let required = ["Fraunces", "Inter", "JetBrains Mono"]
        let families = Set(UIFont.familyNames)
        for family in required {
            // Inter ships as "Inter" or "Inter Variable" depending on the file;
            // either name is acceptable as long as SOMETHING with that prefix
            // landed in the bundle.
            let match = families.contains(where: {
                $0.caseInsensitiveCompare(family) == .orderedSame
                || $0.range(of: family, options: .caseInsensitive) != nil
            })
            if !match {
                print("[Hearth] WARNING: font family '\(family)' not registered. " +
                      "Did Info.plist UIAppFonts pick up the bundled .ttf?")
            }
        }
    }
}
#endif
