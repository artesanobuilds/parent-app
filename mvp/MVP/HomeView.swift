import SwiftUI

struct HomeView: View {
    let username: String

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Greeting header
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(username.isEmpty ? "Welcome" : username)
                                .font(.title.weight(.bold))
                                .foregroundColor(.brandNavy)
                            Image(systemName: "chevron.down")
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundColor(.brandNavy)
                            Spacer()
                            Circle()
                                .fill(Color.brandCoral.opacity(0.15))
                                .frame(width: 40, height: 40)
                                .overlay(
                                    Image(systemName: "person.fill")
                                        .foregroundColor(.brandCoral)
                                        .font(.system(size: 18))
                                )
                        }
                    }
                    .padding(.horizontal)
                    .padding(.top, 8)

                    // Coming soon card
                    VStack(spacing: 16) {
                        Image(systemName: "sparkles")
                            .font(.system(size: 40))
                            .foregroundColor(.brandCoral.opacity(0.6))

                        Text("Home is coming soon")
                            .font(.title3.weight(.semibold))
                            .foregroundColor(.brandNavy)

                        Text("Personalized content, progress tracking, and daily recommendations will appear here.")
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
            }
            .background(Color.brandBackground.ignoresSafeArea())
            .navigationBarHidden(true)
        }
    }
}
