import SwiftUI
import MarkdownUI

struct ArticleDetailView: View {
    let articleId: String
    @EnvironmentObject private var contentVM: ContentViewModel
    @EnvironmentObject private var configuration: ServerConfiguration
    @State private var article: APIArticle?
    @State private var isLoading = true

    var body: some View {
        Group {
            if isLoading {
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Color.bgCanvas.ignoresSafeArea())
            } else if let article = article {
                ScrollView {
                    VStack(alignment: .leading, spacing: 0) {
                        header(article)
                        markdownBody(article)
                    }
                }
                .background(Color.bgCanvas.ignoresSafeArea())
                .navigationTitle("")
                .navigationBarTitleDisplayMode(.inline)
                .toolbarBackground(Color.bgCanvas, for: .navigationBar)
                .toolbarBackground(.visible, for: .navigationBar)
            } else {
                notFound
            }
        }
        .task {
            Analytics.capture("content_opened", ["type": "article"])
            if let url = configuration.baseURL {
                article = await contentVM.fetchArticleDetail(baseURL: url, id: articleId)
            }
            isLoading = false
        }
    }

    // MARK: - Header

    private func header(_ article: APIArticle) -> some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            // Photo-tile hero — saffron is the warm "energy/play" tile and
            // the default editorial start-here block. Per the cards spec
            // `category` variant, text overlaid on a warm tile resolves to
            // inkOnPhotoDark; the emoji is decorative so we leave it as-is.
            ZStack {
                Color.photoSaffron
                Text(article.emoji)
                    .font(.system(size: 64))
            }
            .frame(height: 200)
            .frame(maxWidth: .infinity)

            VStack(alignment: .leading, spacing: .hearth400) {
                // Category badge
                if let category = contentVM.categories.first(where: { $0.id == article.category }) {
                    Text("\(category.emoji) \(category.name)")
                        .font(.hearthLabel)
                        .foregroundColor(.accentPress)
                        .tracking(0.66)
                        .textCase(.uppercase)
                        .padding(.horizontal, .hearth400)
                        .padding(.vertical, .hearth300)
                        .background(Color.accentTint)
                        .clipShape(Capsule())
                }

                // Title — Fraunces display, the editorial hero.
                Text(article.title)
                    .font(.hearthDisplayMD)
                    .foregroundColor(.inkPrimary)

                // Subtitle
                Text(article.subtitle)
                    .font(.hearthBodyLG)
                    .foregroundColor(.inkSecondary)

                // Meta row — JetBrains Mono caption is the metadata family.
                HStack(spacing: .hearth400) {
                    Label(article.author, systemImage: "person.fill")
                    Label(article.readTime, systemImage: "clock")
                }
                .font(.hearthCaptionMono)
                .foregroundColor(.inkMuted)

                // Tags row (chips). Hidden when empty.
                if !article.tags.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: .hearth300) {
                            ForEach(article.tags, id: \.self) { tag in
                                Text(tag)
                                    .font(.hearthLabel)
                                    .foregroundColor(.accentPress)
                                    .tracking(0.66)
                                    .textCase(.uppercase)
                                    .padding(.horizontal, .hearth400)
                                    .padding(.vertical, .hearth300)
                                    .background(Color.accentTint)
                                    .clipShape(Capsule())
                                    .overlay(
                                        Capsule()
                                            .stroke(Color.accentDefault.opacity(0.25), lineWidth: 1)
                                    )
                            }
                        }
                    }
                    .padding(.top, 2)
                }

                Divider()
                    .background(Color.borderHairline)
                    .padding(.top, .hearth300)
            }
            .padding(.horizontal, .hearth700)
        }
    }

    // MARK: - Markdown Body

    private func markdownBody(_ article: APIArticle) -> some View {
        // MarkdownUI uses its own text styling pipeline; we still feed it
        // Hearth colors. Sizes track type/body-lg for the article reading
        // surface (17pt body, 22pt h3, 28pt h2 — Fraunces feel on headings
        // via the FontFamily.custom("Fraunces") binding).
        Markdown(article.content ?? "")
            .markdownTextStyle {
                ForegroundColor(Color.inkPrimary)
                FontSize(17)
            }
            .markdownTextStyle(\.strong) {
                FontWeight(.semibold)
            }
            .markdownBlockStyle(\.heading2) { configuration in
                configuration.label
                    .markdownTextStyle {
                        FontFamily(.custom(HearthFontFamily.displaySerif))
                        FontSize(28)
                        FontWeight(.semibold)
                        ForegroundColor(Color.inkPrimary)
                    }
                    .padding(.top, .hearth500)
                    .padding(.bottom, .hearth300)
            }
            .markdownBlockStyle(\.heading3) { configuration in
                configuration.label
                    .markdownTextStyle {
                        FontFamily(.custom(HearthFontFamily.displaySerif))
                        FontSize(22)
                        FontWeight(.semibold)
                        ForegroundColor(Color.inkPrimary)
                    }
                    .padding(.top, .hearth400)
                    .padding(.bottom, 2)
            }
            .markdownBlockStyle(\.blockquote) { configuration in
                configuration.label
                    .padding(.leading, .hearth400)
                    .overlay(alignment: .leading) {
                        Rectangle()
                            .fill(Color.accentDefault.opacity(0.6))
                            .frame(width: 3)
                    }
                    .padding(.vertical, .hearth300)
            }
            .padding(.horizontal, .hearth700)
            .padding(.vertical, .hearth600)
    }

    // MARK: - Not Found

    private var notFound: some View {
        VStack(spacing: .hearth400) {
            Image(systemName: "doc.questionmark")
                .font(.system(size: 40))
                .foregroundColor(.inkPlaceholder)
            Text("Article not found")
                .font(.hearthBodyMD)
                .foregroundColor(.inkMuted)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.bgCanvas.ignoresSafeArea())
    }
}
