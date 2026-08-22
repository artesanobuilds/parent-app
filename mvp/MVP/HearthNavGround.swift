import SwiftUI

// iOS 26.4 redrew NavigationStack chrome as inset "Liquid Glass": the nav
// CONTAINER paints its own (system light) background, the content gets
// rounded/inset over it, and a few pixels of that lighter ground show down
// both sides and across the toolbar band — Miguel's device screenshot,
// 2026-08-21; reproduced on the 26.4 simulator, invisible on 26.2. A
// `.background` on the content can never cover the container, so every
// full-screen stack repaints the container itself with the page's ground
// token. `.containerBackground(for: .navigation)` is iOS 18+; older runtimes
// never show the glass chrome, so the no-op branch is visually correct too.
extension View {
    @ViewBuilder
    func hearthNavGround(_ color: Color) -> some View {
        if #available(iOS 18.0, *) {
            self.containerBackground(color, for: .navigation)
        } else {
            self
        }
    }
}
