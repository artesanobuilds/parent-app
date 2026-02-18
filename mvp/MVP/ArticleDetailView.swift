import SwiftUI
import MarkdownUI

struct ArticleDetailView: View {
    let articleId: String

    private var article: ArticleData? {
        ContentStore.shared.articleContent(articleId)
    }

    var body: some View {
        Group {
            if let article = article {
                ScrollView {
                    VStack(alignment: .leading, spacing: 0) {
                        header(article)
                        markdownBody(article)
                    }
                }
                .background(Color.brandBackground.ignoresSafeArea())
                .navigationTitle("")
                .navigationBarTitleDisplayMode(.inline)
            } else {
                notFound
            }
        }
    }

    // MARK: - Header

    private func header(_ article: ArticleData) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            // Emoji banner
            ZStack {
                LinearGradient(
                    colors: [Color.brandCoral.opacity(0.12), Color.brandCoral.opacity(0.04)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                Text(article.emoji)
                    .font(.system(size: 56))
            }
            .frame(height: 140)
            .frame(maxWidth: .infinity)

            VStack(alignment: .leading, spacing: 8) {
                // Category badge
                if let category = MockContentProvider.categories.first(where: { $0.id == article.category }) {
                    Text("\(category.emoji) \(category.name)")
                        .font(.caption.weight(.semibold))
                        .foregroundColor(.brandCoral)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(Color.brandCoral.opacity(0.1))
                        .clipShape(Capsule())
                }

                // Title
                Text(article.title)
                    .font(.title2.weight(.bold))
                    .foregroundColor(.brandNavy)

                // Subtitle
                Text(article.subtitle)
                    .font(.subheadline)
                    .foregroundColor(.brandGray)

                // Meta row
                HStack(spacing: 12) {
                    Label(article.author, systemImage: "person.fill")
                    Label(article.readTime, systemImage: "clock")
                }
                .font(.caption)
                .foregroundColor(.brandGray)

                Divider()
                    .padding(.top, 4)
            }
            .padding(.horizontal)
        }
    }

    // MARK: - Markdown Body

    private func markdownBody(_ article: ArticleData) -> some View {
        Markdown(article.content)
            .markdownTextStyle {
                ForegroundColor(Color.brandNavy)
                FontSize(16)
            }
            .markdownTextStyle(\.strong) {
                FontWeight(.semibold)
            }
            .markdownBlockStyle(\.heading2) { configuration in
                configuration.label
                    .markdownTextStyle {
                        FontSize(22)
                        FontWeight(.bold)
                        ForegroundColor(Color.brandNavy)
                    }
                    .padding(.top, 12)
                    .padding(.bottom, 4)
            }
            .markdownBlockStyle(\.heading3) { configuration in
                configuration.label
                    .markdownTextStyle {
                        FontSize(18)
                        FontWeight(.bold)
                        ForegroundColor(Color.brandNavy)
                    }
                    .padding(.top, 8)
                    .padding(.bottom, 2)
            }
            .markdownBlockStyle(\.blockquote) { configuration in
                configuration.label
                    .padding(.leading, 12)
                    .overlay(alignment: .leading) {
                        Rectangle()
                            .fill(Color.brandCoral.opacity(0.5))
                            .frame(width: 3)
                    }
                    .padding(.vertical, 4)
            }
            .padding(.horizontal)
            .padding(.vertical, 16)
    }

    // MARK: - Not Found

    private var notFound: some View {
        VStack(spacing: 12) {
            Image(systemName: "doc.questionmark")
                .font(.system(size: 40))
                .foregroundColor(.brandGray.opacity(0.5))
            Text("Article not found")
                .font(.subheadline)
                .foregroundColor(.brandGray)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.brandBackground.ignoresSafeArea())
    }
}
