import Foundation

// MARK: - Models

struct CommunityPost: Identifiable {
    let id = UUID()
    let initials: String
    let name: String
    let title: String
    let preview: String
}

struct LibraryItem: Identifiable {
    let id = UUID()
    let emoji: String
    let title: String
}

// MARK: - Mock Data

enum MockContentProvider {

    static let communityPosts: [CommunityPost] = [
        CommunityPost(
            initials: "AQ",
            name: "Annie Q",
            title: "First holidays divorced",
            preview: "Hey there - this is my first holiday season divorced (last yr when separated we were nesting and d..."
        ),
        CommunityPost(
            initials: "LP",
            name: "Lynsey Park",
            title: "Managing many meltdowns when Dad's away",
            preview: "My husband is gone on a work trip, and I'm struggling with the bedtime routine alone..."
        ),
        CommunityPost(
            initials: "MR",
            name: "Maria R",
            title: "Toddler won't let go at daycare",
            preview: "Every morning is a battle. My 3-year-old clings to me and cries when I try to leave..."
        ),
        CommunityPost(
            initials: "JT",
            name: "James T",
            title: "Sibling rivalry after new baby",
            preview: "Our oldest has been acting out ever since we brought the baby home. Any tips for..."
        ),
    ]

    static let libraryItems: [LibraryItem] = [
        LibraryItem(emoji: "📖", title: "Mastering Your Separation Routine"),
        LibraryItem(emoji: "💬", title: "Scripts to Handle Child Crying"),
        LibraryItem(emoji: "🧘", title: "Staying Calm in the Storm"),
        LibraryItem(emoji: "🌙", title: "Bedtime Battles: A Guide"),
        LibraryItem(emoji: "🤝", title: "Co-Parenting Communication"),
    ]

    /// Returns a random subset of community posts (2-3 items).
    static func randomCommunityPosts() -> [CommunityPost] {
        Array(communityPosts.shuffled().prefix(2))
    }

    /// Returns a random subset of library items (2-3 items).
    static func randomLibraryItems() -> [LibraryItem] {
        Array(libraryItems.shuffled().prefix(3))
    }
}
