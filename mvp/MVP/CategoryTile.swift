import SwiftUI

/// Maps article IDs to asset catalog image names.
/// Articles without an image fall back to emoji + color block.
let articleImageAssets: [String: String] = [
    "ap-music-development": "ArticleMusicMatters",
]

/// Maps category IDs to asset catalog image names.
/// Categories without an image fall back to the emoji + color style.
private let categoryImageAssets: [String: String] = [
    "care-village": "CategoryCareVillage",
    "family-life": "CategoryFamilyLife",
    "food-nutrition": "CategoryFoodNutrition",
    "health-kids": "CategoryHealthKids",
    "health-parents": "CategoryHealthParents",
    "home-style-products": "CategoryHomeStyle",
    "inner-life": "CategoryInnerLife",
    "out-in-world": "CategoryOutInWorld",
    "pregnancy-babies": "CategoryPregnancyBabies",
    "raising-kids": "CategoryRaisingKids",
    "school-activities": "CategorySchoolActivities",
]

/// Palette-locked background colors for categories without photography.
/// Rotates through the Hearth photo palette.
private let categoryFallbackColors: [String: Color] = [
    "care-village": .photoSand,
    "family-life": .photoRose,
    "food-nutrition": .photoClay,
    "health-kids": .photoSand,
    "health-parents": .photoSand,
    "home-style-products": .photoClay,
    "inner-life": .photoRose,
    "out-in-world": .photoForest,
    "pregnancy-babies": .photoRoyal,
    "raising-kids": .photoSaffron,
    "school-activities": .photoSaffron,
]

/// Shared category tile used on both Home and Library grids.
/// Shows the MJ illustration when available; falls back to emoji + color.
struct CategoryTile: View {
    let category: APICategory

    var body: some View {
        ZStack(alignment: .bottomLeading) {
            if let assetName = categoryImageAssets[category.id] {
                Image(assetName)
                    .resizable()
                    .aspectRatio(1, contentMode: .fill)
                    .frame(minWidth: 0, maxWidth: .infinity)
                    .aspectRatio(1, contentMode: .fit)
                    .clipped()
            } else {
                let color = categoryFallbackColors[category.id] ?? .photoSaffron
                color.aspectRatio(1, contentMode: .fit)

                Text(category.emoji)
                    .font(.system(size: 36))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }

            // Name overlay with gradient scrim for legibility
            VStack(spacing: 0) {
                Spacer()
                LinearGradient(
                    colors: [.clear, .black.opacity(0.7)],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .frame(height: 60)
                .overlay(alignment: .bottomLeading) {
                    Text(category.name)
                        .font(.hearthTitleMD)
                        .fontWeight(.semibold)
                        .foregroundColor(.white)
                        .lineLimit(2)
                        .multilineTextAlignment(.leading)
                        .shadow(color: .black.opacity(0.7), radius: 3, x: 0, y: 1)
                        .padding(.hearth400)
                }
            }
        }
        .aspectRatio(1, contentMode: .fit)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
    }
}
