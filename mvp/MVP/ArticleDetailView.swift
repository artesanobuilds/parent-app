import SwiftUI
import MarkdownUI

struct ArticleDetailView: View {
    let articleId: String
    @EnvironmentObject private var contentVM: ContentViewModel
    @EnvironmentObject private var configuration: ServerConfiguration
    @State private var article: APIArticle?
    @State private var isLoading = true
    @State private var saveError: String?

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
                // iOS 26.4 glass chrome: repaint the nav container too — see HearthNavGround.swift.
                .hearthNavGround(.bgCanvas)
                .toolbarBackground(Color.bgCanvas, for: .navigationBar)
                .toolbarBackground(.visible, for: .navigationBar)
                .toolbar {
                    ToolbarItem(placement: .navigationBarTrailing) {
                        let saved = contentVM.isSaved(itemType: "article", itemRef: articleId)
                        Button {
                            contentVM.toggleSaved(itemType: "article", itemRef: articleId,
                                                  surface: "article_detail") { saveError = $0 }
                        } label: {
                            Image(systemName: saved ? "bookmark.fill" : "bookmark")
                                .foregroundColor(saved ? .accentDefault : .inkPrimary)
                        }
                        .accessibilityLabel(saved ? "Saved — tap to remove" : "Save article")
                    }
                }
                .alert("Something went wrong",
                       isPresented: Binding(get: { saveError != nil },
                                            set: { if !$0 { saveError = nil } })) {
                    Button("OK") { saveError = nil }
                } message: { Text(saveError ?? "") }
            } else {
                notFound
            }
        }
        .task { await contentVM.loadSavedRefs() }
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
            VStack(alignment: .leading, spacing: .hearth400) {
                // Eyebrow: kicker · age_range · read_time, joined with " · " only for
                // non-empty parts and uppercased. Design spec shows "WE TRIED IT · Ages 3–7 · 4 min".
                let eyebrowParts = [
                    article.kicker,
                    article.ageRange,
                    article.readTime.isEmpty ? nil : article.readTime
                ].compactMap { $0 }.filter { !$0.isEmpty }

                if !eyebrowParts.isEmpty {
                    Text(eyebrowParts.joined(separator: " · ").uppercased())
                        .font(.hearthBodySMBold)
                        .tracking(0.52)
                        .foregroundColor(.inkEyebrow)
                }

                // Title — Fraunces w700 38/40 ls-0.38
                Text(article.title)
                    .font(.custom(HearthFontFamily.displaySerif, size: 38))
                    .fontWeight(.bold)
                    .lineSpacing(2)
                    .foregroundColor(.inkPrimary)

                // Standfirst (subtitle) — Fraunces w400 22/33
                Text(article.subtitle)
                    .font(.custom(HearthFontFamily.displaySerif, size: 22))
                    .fontWeight(.regular)
                    .lineSpacing(11)
                    .foregroundColor(.inkSecondary)

                // Byline — measured Inter w300 12, centered. `hearthCaptionMono` is the
                // designated byline token but it is the MONO family; keeping the sans
                // family matters more here than the 1pt, so this is the 13pt body token.
                Text(article.author)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                    .frame(maxWidth: .infinity, alignment: .center)

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
        // Hearth colors. Design spec: section heads are Inter w900 24; body
        // paragraphs stay at the existing readable body token. The Figma slip
        // that applied w900 24 to EVERY body paragraph is ignored.
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
                        FontFamily(.custom(HearthFontFamily.sans))
                        FontSize(24)
                        FontWeight(.black)
                        ForegroundColor(Color.inkPrimary)
                    }
                    .padding(.top, .hearth500)
                    .padding(.bottom, .hearth300)
            }
            .markdownBlockStyle(\.heading3) { configuration in
                configuration.label
                    .markdownTextStyle {
                        FontFamily(.custom(HearthFontFamily.sans))
                        FontSize(24)
                        FontWeight(.black)
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
