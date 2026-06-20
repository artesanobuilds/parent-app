import SwiftUI

// MARK: - Hearth spacing / shape / radius / motion tokens
//
// All spacing in iOS code goes through these constants. Never `.padding(16)` —
// use `.padding(.hearth500)` or the corresponding `Hearth.space.s500`.

enum Hearth {

    /// Spacing tokens (pt). 9-step scale, geometric. Page gutter = `s700` (24pt).
    enum space {
        static let s0:    CGFloat = 0
        static let s300:  CGFloat = 8
        static let s400:  CGFloat = 12
        static let s500:  CGFloat = 16
        static let s600:  CGFloat = 20
        static let s700:  CGFloat = 24    // page gutter (iOS default)
        static let s800:  CGFloat = 32    // section rhythm (min)
        static let s900:  CGFloat = 40    // section rhythm (default)
        static let s1000: CGFloat = 56    // section rhythm (generous)
        static let s1100: CGFloat = 72    // composed: s700 * 3 (one-off hero)
        static let s1200: CGFloat = 96    // composed: s700 * 4 (one-off hero)
    }

    /// Corner radii. Per spec, sizes are fixed — never override per instance.
    enum radius {
        static let none: CGFloat = 0
        static let sm:   CGFloat = 4     // chips, tags, small pills
        static let md:   CGFloat = 12    // buttons, inputs, small cards
        static let lg:   CGFloat = 20    // primary cards
        static let xl:   CGFloat = 28    // hero tiles, modal sheets
        static let pill: CGFloat = 999   // filter pills, capsule CTAs
    }

    /// Animation token bindings (mirror of the Animation.hearth* set in Theme.swift).
    enum motion {
        static let instant: Animation = .hearthInstant
        static let fast:    Animation = .hearthFast
        static let base:    Animation = .hearthBase
        static let slow:    Animation = .hearthSlow
        static let spring:  Animation = .hearthSpring
    }
}

// MARK: - CGFloat extensions
//
// Mirror of Hearth.space — callable as `.padding(.hearth500)` etc. The two
// surfaces resolve to the same constants; the extension form keeps SwiftUI
// modifier ergonomics ergonomic.

extension CGFloat {
    static let hearth0:    CGFloat = Hearth.space.s0
    static let hearth300:  CGFloat = Hearth.space.s300
    static let hearth400:  CGFloat = Hearth.space.s400
    static let hearth500:  CGFloat = Hearth.space.s500
    static let hearth600:  CGFloat = Hearth.space.s600
    static let hearth700:  CGFloat = Hearth.space.s700
    static let hearth800:  CGFloat = Hearth.space.s800
    static let hearth900:  CGFloat = Hearth.space.s900
    static let hearth1000: CGFloat = Hearth.space.s1000
    static let hearth1100: CGFloat = Hearth.space.s1100
    static let hearth1200: CGFloat = Hearth.space.s1200

    static let hearthRadiusNone: CGFloat = Hearth.radius.none
    static let hearthRadiusSm:   CGFloat = Hearth.radius.sm
    static let hearthRadiusMd:   CGFloat = Hearth.radius.md
    static let hearthRadiusLg:   CGFloat = Hearth.radius.lg
    static let hearthRadiusXl:   CGFloat = Hearth.radius.xl
    static let hearthRadiusPill: CGFloat = Hearth.radius.pill
}
