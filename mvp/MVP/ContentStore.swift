import Foundation

// MARK: - Route Types

struct ArticleRoute: Hashable {
    let id: String
}

struct PostRoute: Hashable {
    let id: String
}

// MARK: - Content Data Models

struct ArticleData {
    let id: String
    let title: String
    let subtitle: String
    let emoji: String
    let author: String
    let readTime: String
    let summary: String
    let content: String
    let tags: [String]
    let category: String
}

struct PostData {
    let id: String
    let initials: String
    let name: String
    let title: String
    let preview: String
    let category: String
}

// MARK: - Content Store

final class ContentStore {
    static let shared = ContentStore()

    private var articles: [String: ArticleData] = [:]
    private var posts: [String: PostData] = [:]

    private init() {
        loadContentLibrary()
    }

    func articleContent(_ id: String) -> ArticleData? {
        articles[id]
    }

    func postData(_ id: String) -> PostData? {
        posts[id]
    }

    // MARK: - Loading

    private func loadContentLibrary() {
        guard let url = Bundle.main.url(forResource: "content_library", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            return
        }

        if let articleArray = json["library_articles"] as? [[String: Any]] {
            for item in articleArray {
                guard let id = item["id"] as? String else { continue }
                let article = ArticleData(
                    id: id,
                    title: item["title"] as? String ?? "",
                    subtitle: item["subtitle"] as? String ?? "",
                    emoji: item["emoji"] as? String ?? "",
                    author: item["author"] as? String ?? "MVP Editorial",
                    readTime: item["read_time"] as? String ?? "",
                    summary: item["summary"] as? String ?? "",
                    content: item["content"] as? String ?? "",
                    tags: item["tags"] as? [String] ?? [],
                    category: item["category"] as? String ?? ""
                )
                articles[id] = article
            }
        }

        if let postArray = json["community_posts"] as? [[String: Any]] {
            for item in postArray {
                guard let id = item["id"] as? String else { continue }
                let post = PostData(
                    id: id,
                    initials: item["initials"] as? String ?? "",
                    name: item["name"] as? String ?? "",
                    title: item["title"] as? String ?? "",
                    preview: item["preview"] as? String ?? "",
                    category: item["category"] as? String ?? ""
                )
                posts[id] = post
            }
        }
    }
}
