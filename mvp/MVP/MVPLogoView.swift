import SwiftUI

/// A 5-pointed star shape used in the MVP badge logo.
struct StarShape: Shape {
    func path(in rect: CGRect) -> Path {
        let center = CGPoint(x: rect.midX, y: rect.midY)
        let outerRadius = min(rect.width, rect.height) / 2
        let innerRadius = outerRadius * 0.42
        let points = 5
        var path = Path()

        for i in 0..<(points * 2) {
            let radius = i.isMultiple(of: 2) ? outerRadius : innerRadius
            let angle = Angle(degrees: Double(i) * 360.0 / Double(points * 2) - 90)
            let point = CGPoint(
                x: center.x + CGFloat(cos(angle.radians)) * radius,
                y: center.y + CGFloat(sin(angle.radians)) * radius
            )
            if i == 0 {
                path.move(to: point)
            } else {
                path.addLine(to: point)
            }
        }
        path.closeSubpath()
        return path
    }
}

/// Replicates the MVP badge logo: silver ring, black circle, large background star,
/// "MVP" text, divider, "MOST VALUABLE PARENT" subtitle, and scattered accent stars/dots.
struct MVPLogoView: View {
    var size: CGFloat = 200

    private var ringWidth: CGFloat { size * 0.06 }
    private var starSize: CGFloat { size * 0.65 }
    private var mvpFontSize: CGFloat { size * 0.22 }
    private var subtitleFontSize: CGFloat { size * 0.046 }
    private var dividerWidth: CGFloat { size * 0.45 }

    private let silverLight = Color(red: 0.82, green: 0.83, blue: 0.84)
    private let silverDark = Color(red: 0.55, green: 0.56, blue: 0.58)
    private let darkGold = Color(red: 0.50, green: 0.42, blue: 0.18)
    private let badgeBlack = Color(red: 0.12, green: 0.12, blue: 0.13)

    var body: some View {
        ZStack {
            silverRing
            innerCircle
            backgroundStar
            accentStars
            accentDots
            textOverlay
        }
        .frame(width: size, height: size)
    }

    // MARK: - Ring & circle

    private var silverRing: some View {
        Circle()
            .fill(
                LinearGradient(
                    colors: [silverLight, silverDark, silverLight],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .frame(width: size, height: size)
    }

    private var innerCircle: some View {
        Circle()
            .fill(badgeBlack)
            .frame(width: size - ringWidth * 2, height: size - ringWidth * 2)
    }

    // MARK: - Background star

    private var backgroundStar: some View {
        StarShape()
            .fill(darkGold.opacity(0.55))
            .frame(width: starSize, height: starSize)
            .offset(y: -size * 0.02)
    }

    // MARK: - Text overlay

    private var textOverlay: some View {
        VStack(spacing: size * 0.01) {
            Text("MVP")
                .font(.system(size: mvpFontSize, weight: .heavy))
                .tracking(size * 0.01)
                .foregroundColor(.white)

            Rectangle()
                .fill(Color.brandGold.opacity(0.6))
                .frame(width: dividerWidth, height: 1)

            Text("MOST VALUABLE PARENT")
                .font(.system(size: subtitleFontSize, weight: .semibold))
                .tracking(size * 0.01)
                .foregroundColor(.brandGold)
        }
        .offset(y: size * 0.04)
    }

    // MARK: - Accent stars

    private var accentStars: some View {
        ZStack {
            accentStar(x: -0.18, y: -0.26, s: 0.08)
            accentStar(x: 0.22, y: -0.22, s: 0.07)
            accentStar(x: -0.28, y: 0.06, s: 0.05)
            accentStar(x: 0.30, y: 0.04, s: 0.05)
            accentStar(x: -0.14, y: 0.30, s: 0.065)
            accentStar(x: 0.18, y: 0.30, s: 0.065)
        }
    }

    private func accentStar(x: CGFloat, y: CGFloat, s: CGFloat) -> some View {
        StarShape()
            .fill(Color.brandGold)
            .frame(width: size * s, height: size * s)
            .offset(x: size * x, y: size * y)
    }

    // MARK: - Accent dots

    private var accentDots: some View {
        let dotSize = size * 0.015
        return ZStack {
            dot(x: -0.10, y: -0.18, d: dotSize)
            dot(x: 0.12, y: -0.16, d: dotSize)
            dot(x: -0.22, y: -0.10, d: dotSize)
            dot(x: 0.24, y: -0.08, d: dotSize)
            dot(x: 0.00, y: -0.20, d: dotSize)
            dot(x: -0.06, y: 0.08, d: dotSize)
            dot(x: 0.08, y: 0.06, d: dotSize)
        }
    }

    private func dot(x: CGFloat, y: CGFloat, d: CGFloat) -> some View {
        Circle()
            .fill(Color.brandGold.opacity(0.7))
            .frame(width: d, height: d)
            .offset(x: size * x, y: size * y)
    }
}

#Preview {
    ZStack {
        Color.brandBackground.ignoresSafeArea()
        MVPLogoView(size: 240)
    }
}
