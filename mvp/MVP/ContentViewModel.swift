import Foundation

@MainActor
final class ContentViewModel: ObservableObject {
    @Published var categories: [APICategory] = []
    @Published var libraryItems: [APIArticle] = []
    @Published var isLoading = false
    @Published var loadError: String?
    @Published var userId: String = ""
    @Published var baseURL: URL?
    /// Active tag filter applied to `libraryItems` via `reloadArticles(baseURL:tag:)`.
    /// Nil = unfiltered. Reset by callers when leaving a screen.
    @Published var currentTagFilter: String? = nil

    /// Cache for full article content (keyed by article id).
    private var articleCache: [String: APIArticle] = [:]

    // MARK: - Saved refs (bookmark state, fetched ONCE per surface — N+1 killer)

    @Published var savedArticleRefs: Set<String> = []
    private var savedRefsLoaded = false

    func loadSavedRefs(force: Bool = false) async {
        guard let baseURL, !userId.isEmpty, force || !savedRefsLoaded else { return }
        savedRefsLoaded = true
        if let refs = try? await SavedService.refs(itemType: "article", userID: userId, baseURL: baseURL) {
            savedArticleRefs = refs
        }
    }

    /// Toggle a bookmark with optimistic UI; on failure the state reverts and
    /// the caller's error binding is set (user-state writes never fail silent).
    func toggleSaved(itemType: String, itemRef: String, surface: String,
                     onError: @escaping (String) -> Void) {
        guard let baseURL, !userId.isEmpty else { return }
        let wasSaved = isSaved(itemType: itemType, itemRef: itemRef)
        setSavedLocal(itemType: itemType, itemRef: itemRef, saved: !wasSaved)
        Task {
            do {
                if wasSaved {
                    try await SavedService.unsave(itemType: itemType, itemRef: itemRef,
                                                  surface: surface, userID: userId, baseURL: baseURL)
                } else {
                    try await SavedService.save(itemType: itemType, itemRef: itemRef,
                                                surface: surface, userID: userId, baseURL: baseURL)
                }
            } catch {
                setSavedLocal(itemType: itemType, itemRef: itemRef, saved: wasSaved)
                onError(wasSaved ? "Couldn't remove that save. Try again."
                                 : "Couldn't save that. Try again.")
            }
        }
    }

    func isSaved(itemType: String, itemRef: String) -> Bool {
        itemType == "article" && savedArticleRefs.contains(itemRef)
    }

    func noteUnsaved(itemType: String, itemRef: String) {
        setSavedLocal(itemType: itemType, itemRef: itemRef, saved: false)
    }

    /// Only "article" bookmarks are tracked locally — the community board
    /// (the only other surface that ever wrote here) was retired backend-side,
    /// so any other item type (coach reply, plan activity) is a no-op here.
    private func setSavedLocal(itemType: String, itemRef: String, saved: Bool) {
        guard itemType == "article" else { return }
        if saved { savedArticleRefs.insert(itemRef) } else { savedArticleRefs.remove(itemRef) }
    }

    // MARK: - Load All Content

    func loadAllContent(baseURL: URL) async {
        guard categories.isEmpty else { return }  // already loaded
        isLoading = true
        loadError = nil
        defer { isLoading = false }

        var failures: [String] = []
        do {
            categories = try await ContentService.fetchCategories(baseURL: baseURL)
        } catch {
            print("[ContentViewModel] fetchCategories failed: \(error)")
            failures.append("categories")
        }

        do {
            libraryItems = try await ContentService.fetchArticles(baseURL: baseURL)
        } catch {
            print("[ContentViewModel] fetchArticles failed: \(error)")
            failures.append("articles")
        }

        if !failures.isEmpty {
            loadError = "Couldn't load \(failures.joined(separator: ", ")). Pull to refresh or check your connection."
        }
    }

    // MARK: - "For you" ranked feed

    /// The library stack-ranked against the family profile (`GET /content/for-you`).
    /// Owned here rather than in `ForYouView` so Home's `FOR YOU` preview and the
    /// full `See all` screen render the same list off one fetch.
    @Published var forYouItems: [ForYouItem] = []
    /// True when the ranked endpoint didn't answer and `forYouItems` is the
    /// plain library instead. Surfaced in the UI, never swallowed.
    @Published var forYouIsFallback = false
    private var forYouLoaded = false

    /// Ranked first; on ANY failure — including the 404 the endpoint returns
    /// until it deploys — fall back to the already-loaded library so the
    /// surface is never blank.
    func loadForYou(force: Bool = false) async {
        guard force || !forYouLoaded else { return }
        forYouLoaded = true
        guard let baseURL else {
            applyForYouFallback()
            return
        }
        do {
            let rows = try await ForYouService.fetch(baseURL: baseURL, userID: userId)
            let byID = Dictionary(libraryItems.map { ($0.id, $0) },
                                  uniquingKeysWith: { first, _ in first })
            // Dedupe by id: `ForEach` over an Identifiable collection with a
            // repeated id renders only one row and logs a runtime complaint.
            var seen = Set<String>()
            let mapped = rows.map { ForYouItem(payload: $0, local: byID[$0.id]) }
                             .filter { !$0.title.isEmpty && seen.insert($0.id).inserted }
            if mapped.isEmpty {
                applyForYouFallback()
            } else {
                forYouItems = mapped
                forYouIsFallback = false
            }
        } catch {
            print("[ContentViewModel] /content/for-you failed: \(error) — falling back to the library")
            applyForYouFallback()
        }
    }

    private func applyForYouFallback() {
        forYouItems = libraryItems.map(ForYouItem.init(article:))
        forYouIsFallback = !forYouItems.isEmpty
    }

    // MARK: - Tag-Filtered Reload

    /// Replace `libraryItems` with articles filtered server-side by `tag`.
    /// Pass `nil` to clear the filter and reload everything.
    func reloadArticles(baseURL: URL, tag: String?) async {
        currentTagFilter = tag
        do {
            libraryItems = try await ContentService.fetchArticles(baseURL: baseURL, tag: tag)
        } catch {
            print("[ContentViewModel] reloadArticles(tag:\(tag ?? "nil")) failed: \(error)")
            loadError = "Couldn't load articles. Pull to refresh or check your connection."
        }
    }

    // MARK: - Article Detail

    func fetchArticleDetail(baseURL: URL, id: String) async -> APIArticle? {
        if let cached = articleCache[id] { return cached }
        do {
            let article = try await ContentService.fetchArticle(baseURL: baseURL, id: id)
            articleCache[id] = article
            return article
        } catch {
            print("[ContentViewModel] fetchArticleDetail failed: \(error)")
            return nil
        }
    }

    // MARK: - Convenience Accessors

    /// The 11 top-level parents. iOS browse views (Library, Home) enumerate
    /// these instead of `categories` so the 99 sub-categories don't flood
    /// the UI before the hierarchical browse UX is built (Phase 3).
    /// Children remain in `categories` and reachable by id when needed.
    var topLevelCategories: [APICategory] {
        categories.filter { $0.parentID == nil }
    }

    func libraryItems(for category: String) -> [APIArticle] {
        libraryItems.filter { $0.category == category }
    }

    func randomLibraryItems() -> [APIArticle] {
        Array(libraryItems.shuffled().prefix(3))
    }

    var featuredItem: APIArticle? {
        libraryItems.first { $0.category == "emotional-wellness" }
    }

    /// Resolve an article id to its loaded model (for voice client-tool cards).
    /// Checks the published library list then the detail cache.
    func articleData(_ id: String) -> APIArticle? {
        libraryItems.first { $0.id == id } ?? articleCache[id]
    }
}
