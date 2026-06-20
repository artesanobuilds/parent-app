import SwiftUI

struct ContentView: View {
    var body: some View {
        ChatView()
            // Phase 1: light-mode locked. Dark mode tokens arrive in Phase 2.
            .preferredColorScheme(.light)
            .background(Color.bgCanvas.ignoresSafeArea())
    }
}

#Preview {
    ContentView()
}
