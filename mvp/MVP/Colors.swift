import SwiftUI

/// Centralized brand colors for MVP — inspired by SchoolMom editorial aesthetic.
/// Palette: warm dusty rose, dark charcoal, soft blush tones.
extension Color {
    // Primary palette
    static let brandCoral = Color(red: 0.77, green: 0.64, blue: 0.58)          // Dusty rose #C4A494
    static let brandNavy = Color(red: 0.18, green: 0.16, blue: 0.15)           // Dark charcoal #2D2926
    static let brandBackground = Color(red: 0.96, green: 0.92, blue: 0.89)     // Light warm blush #F5EBE3
    static let brandSurface = Color.white.opacity(0.94)
    static let brandStroke = Color.brandCoral.opacity(0.30)

    // UI accents
    static let brandYellow = Color(red: 0.77, green: 0.64, blue: 0.58)         // Agent avatar — matches dusty rose
    static let brandLightBlue = Color(red: 0.94, green: 0.90, blue: 0.87)      // User question pill — warm blush
    static let brandGray = Color(red: 0.55, green: 0.50, blue: 0.47)           // Warm gray for secondary text
    static let brandCardBackground = Color.white                                 // Content card background
}
