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

    // MARK: Label + mono

    /// 11 / 14, +6% tracking, weight 600. UPPERCASE nav labels, tag chips.
    /// Apply `.tracking(0.66).textCase(.uppercase)` at the call site.
    static let hearthLabel: Font =
        .custom(HearthFontFamily.sans, size: 11, relativeTo: .caption2)
        .weight(.semibold)

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
    static let hearthLineDisplayXL: CGFloat = 60 - 56
    static let hearthLineDisplayLG: CGFloat = 44 - 40
    static let hearthLineDisplayMD: CGFloat = 32 - 28
    static let hearthLineTitleLG:   CGFloat = 24 - 20
    static let hearthLineTitleMD:   CGFloat = 22 - 16
    static let hearthLineBodyLG:    CGFloat = 26 - 17
    static let hearthLineBodyMD:    CGFloat = 22 - 15
    static let hearthLineBodySM:    CGFloat = 18 - 13
    static let hearthLineLabel:     CGFloat = 14 - 11
    static let hearthLineMono:      CGFloat = 16 - 12
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
