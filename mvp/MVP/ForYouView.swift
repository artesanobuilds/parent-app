import SwiftUI

// MARK: - Wire model
//
// `GET /content/for-you` is landing on a concurrent branch and its exact JSON
// shape is not pinned yet, so the decoder here is deliberately permissive:
//
// * EVERY field except `id` is optional. iOS `Codable` is strict — a single
//   type/absence mismatch throws and empties the WHOLE list (see the memory
//   note `debugging_ios_codable_backend_contract`). Optional fields degrade to
//   a missing subtitle; non-optional ones degrade to a blank screen.
// * `score` is `Double?`, never `Int?`. The ranking comes out of a DuckDB
//   `DOUBLE` (`storage.score_articles_by_words`) and decoding a DOUBLE into
//   `Int?` is exactly the failure that has emptied lists here before.
// * The envelope tolerates a bare array OR an object keyed `items` /
//   `articles` / `results`, because we don't yet know which the endpoint picks.
//
// Field names mirror `/content/articles` (`APIArticle`) so that when the real
// shape lands, matching it is a one-place edit in `ForYouService`.

/// One ranked row off the wire. Mirrors `APIArticle`'s keys, all-optional.
struct ForYouArticlePayload: Codable, Hashable {
    let id: String
    let category: String?
    let title: String?
    let subtitle: String?
    let emoji: String?
    let author: String?
    let readTime: String?
    let summary: String?
    let tags: [String]?
    /// Relevance score. DuckDB `DOUBLE` → `Double?`. NEVER `Int?`.
    let score: Double?
    /// Greg's "Because Ben's naming feelings" line above the headline.
    let reason: String?

    enum CodingKeys: String, CodingKey {
        case id, category, title, subtitle, emoji, author
        case readTime = "read_time"
        case summary, tags, score, reason
    }
}

/// Object envelope. Every key optional so whichever one the endpoint ships
/// decodes, and an unexpected key set yields `nil` rather than a throw.
private struct ForYouEnvelope: Codable {
    let items: [ForYouArticlePayload]?
    let articles: [ForYouArticlePayload]?
    let results: [ForYouArticlePayload]?

    var rows: [ForYouArticlePayload] { items ?? articles ?? results ?? [] }
}

// MARK: - Row view model

/// What the list renders. Built either from the wire payload or — when the
/// endpoint isn't deployed / errors — from the already-loaded library, so the
/// screen is never blank.
struct ForYouItem: Identifiable, Hashable {
    let id: String
    let title: String
    let subtitle: String
    let emoji: String
    let readTime: String?
    /// The "why you're seeing this" line. Nil when the server doesn't explain.
    let reason: String?

    /// Merge a wire row with the locally-cached article of the same id, so a
    /// lean ranking response (ids + scores only) still renders full cards.
    init(payload: ForYouArticlePayload, local: APIArticle?) {
        id = payload.id
        title = payload.title ?? local?.title ?? ""
        subtitle = payload.subtitle ?? local?.subtitle ?? local?.summary ?? ""
        emoji = payload.emoji ?? local?.emoji ?? "📄"
        readTime = payload.readTime ?? local?.readTime
        reason = payload.reason
    }

    init(article: APIArticle) {
        id = article.id
        title = article.title
        subtitle = article.subtitle
        emoji = article.emoji
        readTime = article.readTime
        reason = nil
    }
}

// MARK: - Service
//
// The ONLY place that knows the endpoint's URL and shape. Rewiring to the real
// contract is a change to `fetch(...)` and `ForYouArticlePayload` and nothing
// else.

enum ForYouService {

    /// `GET /content/for-you`. Throws on any non-2xx (including the 404 the
    /// endpoint returns until it deploys) so the caller can fall back.
    static func fetch(baseURL: URL, userID: String) async throws -> [ForYouArticlePayload] {
        var request = URLRequest(url: baseURL.appendingPathComponent("content/for-you"))
        // Ranking is per-family, so this read is authenticated when we have a
        // token. Resolved through AuthService — never a hand-rolled header.
        if !userID.isEmpty {
            for (key, value) in await authHeader(userID: userID, baseURL: baseURL) {
                request.setValue(value, forHTTPHeaderField: key)
            }
        }
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw ContentServiceError.invalidResponse
        }
        guard (200..<300).contains(http.statusCode) else {
            throw ContentServiceError.httpError(http.statusCode)
        }
        let decoder = JSONDecoder()
        // Bare array first (the shape `/content/articles` already uses), then
        // the object envelope.
        if let rows = try? decoder.decode([ForYouArticlePayload].self, from: data) {
            return rows
        }
        return try decoder.decode(ForYouEnvelope.self, from: data).rows
    }

    @MainActor
    private static func authHeader(userID: String, baseURL: URL) async -> [String: String] {
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        return AuthService.shared.header(for: userID)
    }
}

// MARK: - Screen

/// The full "For you" feed — the library, stack-ranked against the family
/// profile. Reached from Home's `FOR YOU → See all` via `ForYouRoute()`.
///
/// Pushed inside an existing `NavigationStack`, so it declares no stack of its
/// own; it re-declares the content destinations because a pushed screen that
/// links onward must be able to resolve them.
struct ForYouView: View {
    @EnvironmentObject private var contentVM: ContentViewModel
    @EnvironmentObject private var configuration: ServerConfiguration

    @State private var isLoading = true

    private var items: [ForYouItem] { contentVM.forYouItems }
    /// True when the ranked endpoint didn't answer and we're showing the plain
    /// library instead. Surfaced to the parent, not swallowed.
    private var isFallback: Bool { contentVM.forYouIsFallback }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: .hearth600) {
                header

                if isLoading && items.isEmpty {
                    ProgressView()
                        .frame(maxWidth: .infinity)
                        .padding(.top, .hearth900)
                } else if items.isEmpty {
                    emptyState
                } else {
                    VStack(spacing: .hearth500) {
                        ForEach(items) { item in
                            NavigationLink(value: ArticleRoute(id: item.id)) {
                                ForYouCard(item: item)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }

                Spacer(minLength: .hearth700)
            }
            .padding(.horizontal, .hearth700)
            .padding(.top, .hearth500)
        }
        .background(Color.bgCanvas.ignoresSafeArea())
        .navigationTitle("For you")
        .navigationBarTitleDisplayMode(.inline)
        .toolbarBackground(Color.bgCanvas, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
        .trackScreen("for_you")
        .withContentNavigationDestinations()
        .task { await load() }
    }

    // MARK: Sections

    /// beta-v1 section header: `hearthSectionHeader` (Inter w800 16), uppercase,
    /// with a leading icon in `inkSecondary`. Was the display serif at 13pt until
    /// the 2026-08-08 fidelity pass — see the token's doc comment.
    private var header: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            HStack(spacing: .hearth300) {
                Image(systemName: "book.closed")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.inkSecondary)
                Text("For you")
                    .font(.hearthSectionHeader)
                    .textCase(.uppercase)
                    .foregroundColor(.inkSecondary)
            }

            Text(isFallback
                 ? "Fresh from the library while we finish learning your family."
                 : "Picked for your family, from everything in the library.")
                .font(.hearthBodySM)
                .foregroundColor(.inkMuted)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    private var emptyState: some View {
        VStack(spacing: .hearth400) {
            Image(systemName: "book.closed")
                .font(.system(size: 40, weight: .light))
                .foregroundColor(.inkMuted)
            Text("Nothing here yet")
                .font(.hearthTitleMD)
                .foregroundColor(.inkPrimary)
            Text("Tell your coach a little more about your family and we'll start lining reads up for you.")
                .font(.hearthBodySM)
                .foregroundColor(.inkMuted)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, .hearth900)
    }

    // MARK: Load

    /// The fetch + fallback both live on `ContentViewModel` so Home's preview
    /// and this screen share one result. Re-entering re-fetches (`force`) —
    /// the ranking moves as the profile fills in.
    private func load() async {
        // `configuration` is read so the screen re-resolves once the base URL
        // lands; the URL itself is resolved inside the view model.
        _ = configuration.baseURL
        isLoading = true
        await contentVM.loadForYou(force: true)
        isLoading = false
    }
}

// MARK: - Row card
//
// beta-v1 card: paper ground, `radius/lg`, soft ambient shadow via
// `.hearthCardElevation()` — NO hairline border (the elevation rule reversed
// for this redesign).

private struct ForYouCard: View {
    let item: ForYouItem

    var body: some View {
        HStack(alignment: .top, spacing: .hearth400) {
            thumbnail

            VStack(alignment: .leading, spacing: .hearth300) {
                if let reason = item.reason, !reason.isEmpty {
                    Text(reason)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkMuted)
                        .lineLimit(2)
                        .multilineTextAlignment(.leading)
                }

                Text(item.title)
                    .font(.hearthTitleLG)
                    .foregroundColor(.inkPrimary)
                    .multilineTextAlignment(.leading)
                    .fixedSize(horizontal: false, vertical: true)

                if !item.subtitle.isEmpty {
                    Text(item.subtitle)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkSecondary)
                        .lineLimit(3)
                        .multilineTextAlignment(.leading)
                }

                if let readTime = item.readTime, !readTime.isEmpty {
                    Text(readTime)
                        .font(.hearthCaptionMono)
                        .foregroundColor(.inkMuted)
                }
            }

            Spacer(minLength: 0)
        }
        .padding(.hearth500)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
        .hearthCardElevation()
    }

    @ViewBuilder
    private var thumbnail: some View {
        if let assetName = articleImageAssets[item.id] {
            Image(assetName)
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(width: 56, height: 56)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
        } else {
            RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                .fill(Color.accentTint)
                .frame(width: 56, height: 56)
                .overlay(Text(item.emoji).font(.system(size: 26)))
        }
    }
}
