import SwiftUI

/// Centralized brand colors for MVP.
extension Color {
    static let brandCoral = Color(red: 0.94, green: 0.44, blue: 0.39)
    static let brandNavy = Color(red: 0.12, green: 0.17, blue: 0.23)
    static let brandBackground = Color(red: 1.0, green: 0.97, blue: 0.96)
    static let brandSurface = Color.white.opacity(0.94)
    static let brandStroke = Color.brandCoral.opacity(0.25)

    // Agent / GiGi-style UI additions
    static let brandYellow = Color(red: 0.98, green: 0.80, blue: 0.20)       // Agent avatar circle
    static let brandLightBlue = Color(red: 0.91, green: 0.94, blue: 0.97)    // User question pill background
    static let brandGray = Color(red: 0.60, green: 0.62, blue: 0.65)         // Inactive tab icons / secondary text
    static let brandCardBackground = Color.white                               // Content card background
}

