import Foundation

@MainActor
final class ContentViewModel: ObservableObject {
    @Published var categories: [APICategory] = []
    @Published var libraryItems: [APIArticle] = []
    @Published var communityPosts: [APICommunityPost] = []
    @Published var isLoading = false
    @Published var repliesCache: [String: [APIReply]] = [:]
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
    @Published var savedPostRefs: Set<String> = []
    private var savedRefsLoaded = false

    func loadSavedRefs(force: Bool = false) async {
        guard let baseURL, !userId.isEmpty, force || !savedRefsLoaded else { return }
        savedRefsLoaded = true
        if let refs = try? await SavedService.refs(itemType: "article", userID: userId, baseURL: baseURL) {
            savedArticleRefs = refs
        }
        if let refs = try? await SavedService.refs(itemType: "community_post", userID: userId, baseURL: baseURL) {
            savedPostRefs = refs
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
        itemType == "article" ? savedArticleRefs.contains(itemRef)
                              : savedPostRefs.contains(itemRef)
    }

    func noteUnsaved(itemType: String, itemRef: String) {
        setSavedLocal(itemType: itemType, itemRef: itemRef, saved: false)
    }

    private func setSavedLocal(itemType: String, itemRef: String, saved: Bool) {
        if itemType == "article" {
            if saved { savedArticleRefs.insert(itemRef) } else { savedArticleRefs.remove(itemRef) }
        } else if itemType == "community_post" {
            if saved { savedPostRefs.insert(itemRef) } else { savedPostRefs.remove(itemRef) }
        }
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

        do {
            communityPosts = try await ContentService.fetchCommunityPosts(baseURL: baseURL, userID: userId)
        } catch {
            print("[ContentViewModel] fetchCommunityPosts failed: \(error)")
            failures.append("community posts")
        }

        if !failures.isEmpty {
            loadError = "Couldn't load \(failures.joined(separator: ", ")). Pull to refresh or check your connection."
        }
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

    // MARK: - Community Post & Reply Actions

    func createPost(baseURL: URL, category: String, title: String, body: String, authorName: String) async {
        do {
            let post = try await ContentService.createCommunityPost(
                baseURL: baseURL, category: category, title: title, preview: body,
                userId: userId, authorName: authorName
            )
            communityPosts.insert(post, at: 0)
        } catch {
            print("[ContentViewModel] createPost failed: \(error)")
        }
    }

    func loadReplies(baseURL: URL, postId: String) async {
        do {
            let replies = try await ContentService.fetchReplies(baseURL: baseURL, postId: postId, userID: userId)
            repliesCache[postId] = replies
        } catch {
            print("[ContentViewModel] loadReplies failed: \(error)")
        }
    }

    func createReply(baseURL: URL, postId: String, authorName: String, body: String) async {
        do {
            let reply = try await ContentService.createReply(
                baseURL: baseURL, postId: postId, userId: userId, authorName: authorName, body: body
            )
            repliesCache[postId, default: []].append(reply)
            // Increment reply count on the post
            if let index = communityPosts.firstIndex(where: { $0.id == postId }) {
                // APICommunityPost has let properties, so we need to rebuild it
                // Since replyCount is optional and let, we'll track counts in repliesCache instead
            }
        } catch {
            print("[ContentViewModel] createReply failed: \(error)")
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

    func communityPosts(for category: String) -> [APICommunityPost] {
        communityPosts.filter { $0.category == category }
    }

    func randomCommunityPosts() -> [APICommunityPost] {
        Array(communityPosts.shuffled().prefix(2))
    }

    func randomLibraryItems() -> [APIArticle] {
        Array(libraryItems.shuffled().prefix(3))
    }

    var featuredItem: APIArticle? {
        libraryItems.first { $0.category == "emotional-wellness" }
    }

    func postData(_ id: String) -> APICommunityPost? {
        communityPosts.first { $0.id == id }
    }

    /// Resolve an article id to its loaded model (for voice client-tool cards).
    /// Checks the published library list then the detail cache.
    func articleData(_ id: String) -> APIArticle? {
        libraryItems.first { $0.id == id } ?? articleCache[id]
    }
}
