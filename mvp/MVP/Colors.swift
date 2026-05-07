import SwiftUI

/// Centralized brand colors for MVP — dark badge aesthetic with gold accents.
/// Logo: black circle, gold stars, white "MVP" text, silver ring.
/// Rule: dark/black for chrome and backgrounds, white for content sections, gold for accents.
extension Color {
    // Primary brand colors from logo
    static let brandGold = Color(red: 0.79, green: 0.66, blue: 0.30)           // #C9A84C gold stars
    static let brandBlack = Color(red: 0.11, green: 0.11, blue: 0.12)          // #1C1C1E primary dark

    // Backgrounds
    static let brandBackground = Color(red: 0.11, green: 0.11, blue: 0.12)     // App-level dark bg
    static let brandSurface = Color(red: 0.17, green: 0.17, blue: 0.18)        // Elevated dark cards/surfaces
    static let brandCardBackground = Color.white                                 // Content cards & reading bg

    // Text
    static let brandNavy = Color(red: 0.13, green: 0.13, blue: 0.14)           // Dark text on light bg
    static let brandGray = Color(red: 0.60, green: 0.60, blue: 0.60)           // Secondary/muted text

    // Accent aliases (swap coral → gold everywhere)
    static let brandCoral = Color(red: 0.79, green: 0.66, blue: 0.30)          // Gold (compat alias)
    static let brandYellow = Color(red: 0.79, green: 0.66, blue: 0.30)         // Agent avatar
    static let brandLightBlue = Color(red: 0.22, green: 0.22, blue: 0.23)      // User message pill (dark)

    // Borders
    static let brandStroke = Color.white.opacity(0.10)                           // Subtle border on dark
}
