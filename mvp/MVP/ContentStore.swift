import Foundation

// MARK: - Route Types (used for NavigationLink destinations)

struct ArticleRoute: Hashable {
    let id: String
}

struct PostRoute: Hashable {
    let id: String
}

/// Routes a discovery candidate to its detail screen. Carries the full model
/// (candidates aren't individually re-fetchable by id), same value-based
/// pattern as ArticleRoute / PostRoute.
struct CandidateRoute: Hashable {
    let candidate: ActivityCandidate
}
