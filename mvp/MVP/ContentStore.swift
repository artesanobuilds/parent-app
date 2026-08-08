import Foundation

// MARK: - Route Types (used for NavigationLink destinations)

struct ArticleRoute: Hashable {
    let id: String
}

/// Routes a discovery candidate to its detail screen. Carries the full model
/// (candidates aren't individually re-fetchable by id), same value-based
/// pattern as ArticleRoute.
struct CandidateRoute: Hashable {
    let candidate: ActivityCandidate
}

/// Routes to the ranked "For you" feed — the library stack-ranked against the
/// family profile. Payload-free on purpose: the ranking is derived server-side
/// from the caller's own profile, so there is nothing for the link to carry.
///
/// **This shape is a cross-agent contract.** Home's `FOR YOU → See all` links
/// with `NavigationLink(value: ForYouRoute())`; the destination is registered
/// once in `withContentNavigationDestinations()` so every surface inherits it.
/// Do not add stored properties or rename it without updating both sides.
struct ForYouRoute: Hashable {}
