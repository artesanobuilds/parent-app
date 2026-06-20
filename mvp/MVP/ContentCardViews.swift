import SwiftUI

// MARK: - Community Post Card
//
// `post` variant per the cards spec: bg/elevated + border/hairline (no shadow),
// author row in body-sm semibold, body in body-md, lifts via hairline + paper.

struct CommunityPostCard: View {
    let post: APICommunityPost

    var body: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            // Avatar + name row
            HStack(spacing: .hearth300) {
                Circle()
                    .fill(Color.accentTint)
                    .frame(width: 32, height: 32)
                    .overlay(
                        Text(post.initials)
                            .font(.hearthLabel)
                            .foregroundColor(.accentDefault)
                    )
                Text(post.name)
                    .font(.hearthTitleMD)
                    .foregroundColor(.inkPrimary)
            }

            // Title
            Text(post.title)
                .font(.hearthTitleMD)
                .foregroundColor(.inkPrimary)
                .lineLimit(2)

            // Preview text
            Text(post.preview)
                .font(.hearthBodySM)
                .foregroundColor(.inkSecondary)
                .lineLimit(4)
        }
        .padding(.hearth500)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                .stroke(Color.borderHairline, lineWidth: 1)
        )
    }
}

// MARK: - Library Item Card
//
// `article` md variant — feed card with hero block + title + meta. We render
// the emoji over a tinted accent surface as a stand-in for the 4:5 hero photo.

struct LibraryItemCard: View {
    let item: APIArticle

    var body: some View {
        HStack(spacing: .hearth400) {
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
                    .overlay(
                        Text(item.emoji)
                            .font(.system(size: 26))
                    )
            }

            // Title + Subtitle
            VStack(alignment: .leading, spacing: 2) {
                Text(item.title)
                    .font(.hearthTitleMD)
                    .foregroundColor(.inkPrimary)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)
                Text(item.subtitle)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                    .lineLimit(2)
            }

            Spacer(minLength: 0)
        }
        .padding(.hearth400)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                .stroke(Color.borderHairline, lineWidth: 1)
        )
    }
}

// MARK: - Content Sections

struct CommunitySection: View {
    let posts: [APICommunityPost]

    var body: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            Text("Connect in the community")
                .font(.hearthLabel)
                .foregroundColor(.inkMuted)
                .tracking(0.66)
                .textCase(.uppercase)
                .padding(.leading, .hearth300)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: .hearth400) {
                    ForEach(posts) { post in
                        NavigationLink(value: PostRoute(id: post.id)) {
                            CommunityPostCard(post: post)
                                .frame(width: 240)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }
}

struct LibrarySection: View {
    let items: [APIArticle]

    var body: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            Text("Explore the library")
                .font(.hearthLabel)
                .foregroundColor(.inkMuted)
                .tracking(0.66)
                .textCase(.uppercase)
                .padding(.leading, .hearth300)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: .hearth400) {
                    ForEach(items) { item in
                        NavigationLink(value: ArticleRoute(id: item.id)) {
                            LibraryItemCard(item: item)
                                .frame(width: 260)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }
}

// MARK: - Navigation Destination Modifier

extension View {
    func withContentNavigationDestinations() -> some View {
        self
            .navigationDestination(for: ArticleRoute.self) { route in
                ArticleDetailView(articleId: route.id)
            }
            .navigationDestination(for: PostRoute.self) { route in
                CommunityPostDetailView(postId: route.id)
            }
            // Category tile taps push a category id (String). Registered
            // here so both HomeView and LibraryView (and any future
            // surface) inherit the destination from one place — was
            // previously scoped inside HomeView.categoriesSection.
            .navigationDestination(for: String.self) { categoryId in
                CategoryDetailView(categoryId: categoryId)
            }
    }
}

// MARK: - Feedback Row

struct FeedbackRow: View {
    let feedback: MessageFeedback?
    let onThumbsUp: () -> Void
    let onThumbsDown: () -> Void

    var body: some View {
        HStack(spacing: .hearth500) {
            Spacer()
            Button(action: onThumbsUp) {
                Image(systemName: feedback == .thumbsUp ? "hand.thumbsup.fill" : "hand.thumbsup")
                    .font(.system(size: 18))
                    .foregroundColor(feedback == .thumbsUp ? .accentDefault : .inkMuted)
                    .frame(width: 44, height: 44)
                    .contentShape(Rectangle())
            }
            Button(action: onThumbsDown) {
                Image(systemName: feedback == .thumbsDown ? "hand.thumbsdown.fill" : "hand.thumbsdown")
                    .font(.system(size: 18))
                    .foregroundColor(feedback == .thumbsDown ? .accentDefault : .inkMuted)
                    .frame(width: 44, height: 44)
                    .contentShape(Rectangle())
            }
            Spacer()
        }
        .padding(.vertical, .hearth300)
    }
}
