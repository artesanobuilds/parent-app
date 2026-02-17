import SwiftUI

struct LibraryView: View {
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // Coming soon card
                    VStack(spacing: 16) {
                        Image(systemName: "books.vertical")
                            .font(.system(size: 40))
                            .foregroundColor(.brandCoral.opacity(0.6))

                        Text("Library is coming soon")
                            .font(.title3.weight(.semibold))
                            .foregroundColor(.brandNavy)

                        Text("Workshops, scripts, and expert-curated resources for every parenting moment will live here.")
                            .font(.body)
                            .foregroundColor(.brandGray)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 24)
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 48)
                    .background(
                        RoundedRectangle(cornerRadius: 20, style: .continuous)
                            .fill(Color.brandCardBackground)
                            .shadow(color: Color.black.opacity(0.04), radius: 12, y: 4)
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 20, style: .continuous)
                            .stroke(Color.brandNavy.opacity(0.06), lineWidth: 1)
                    )
                    .padding(.horizontal)

                    Spacer()
                }
                .padding(.top, 16)
            }
            .background(Color.brandBackground.ignoresSafeArea())
            .navigationTitle("Library")
            .toolbarBackground(Color.brandBackground, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
        }
    }
}
