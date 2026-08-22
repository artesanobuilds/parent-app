import SwiftUI

// MARK: - Heisman Onboarding-9 "today" cards
//
// The day-zero summary's per-person cards (Figma `nAXZQhmvwEpzq3rkBisok7`
// frame `42:8322`, card nodes `29:2796`/`29:2804`/`29:2812`): one card per
// person, built from the lifecycle board (`GET /cos/plan/board` via
// `PlanService.board`). Kid cards group board activities by `kid_name`; the
// parent's own card is the rows with `kid_name == nil` (the onboarding
// step-05 "what about you" seed writes those — the board API doesn't expose
// the `onboarding_self` source marker, so nil-kid == parent is the v1 rule,
// per the sprint appendix).
//
// Day zero: the post-account seed creates these rows from onboarding inputs,
// so this renders correctly with nothing but onboarding data. A person with
// no rows gets no card (acceptance 7: skip step 05 → children-only summary);
// no rows at all collapses the whole stack — never placeholder content.

// MARK: Grouping

/// One person's TODAY card: their name plus their board activities, in board
/// order. `isParent` marks the nil-kid group.
struct PersonToday: Identifiable, Hashable {
    let name: String
    let isParent: Bool
    let activities: [BoardActivity]
    var id: String { (isParent ? "parent:" : "kid:") + name }
}

enum HomeTodayBuilder {
    /// Flatten the board into per-person groups: kids in first-appearance
    /// order, then the parent's own (nil `kid_name`) group last — the frame's
    /// order (Benjamin, Lily, Greg). Capped at 3 activities per person so a
    /// long-standing family's Home stays a summary, not the whole planner.
    static func build(board: PlanBoard?, parentName: String) -> [PersonToday] {
        guard let board else { return [] }
        var kidOrder: [String] = []
        var byKid: [String: [BoardActivity]] = [:]
        var parentRows: [BoardActivity] = []

        for stage in board.stages {
            for activity in stage.activities {
                if let kid = activity.kidName, !kid.isEmpty {
                    if byKid[kid] == nil { kidOrder.append(kid) }
                    byKid[kid, default: []].append(activity)
                } else {
                    parentRows.append(activity)
                }
            }
        }

        var groups: [PersonToday] = kidOrder.map { kid in
            PersonToday(name: kid, isParent: false,
                        activities: Array(byKid[kid]!.prefix(3)))
        }
        if !parentRows.isEmpty {
            // The parent's display name can be briefly unknown on first load;
            // the card still renders (the rows are real), with a neutral label
            // rather than a fabricated name.
            let name = parentName.trimmingCharacters(in: .whitespaces)
            groups.append(PersonToday(name: name.isEmpty ? "You" : name,
                                      isParent: true,
                                      activities: Array(parentRows.prefix(3))))
        }
        return groups
    }
}

// MARK: - View model

/// Owns the Onboarding-9 Home's server data that has no existing view model:
/// the board-derived per-person groups and the coach nudge. Every fetch is
/// best-effort — a failure collapses its section, never blocks the screen.
/// Driven by HomeView's `.task(id: refreshToken)`, so the re-fetch-on-return
/// rule (CLAUDE.md) holds without any one-shot `.task`.
@MainActor
final class HomeTodayViewModel: ObservableObject {
    @Published private(set) var people: [PersonToday] = []
    @Published private(set) var nudge: CoachNudge?
    /// False until the first nudge fetch settles — gates the COACH card's
    /// "checking in…" vs. honest "no nudge yet" copy.
    @Published private(set) var hasLoadedNudge = false
    @Published private(set) var isLoading = false

    func refresh(baseURL: URL, userID: String, parentName: String) async {
        guard !userID.isEmpty else { return }
        isLoading = true
        defer { isLoading = false }

        async let nudgeTask = HomeDashboardService.coachNudge(baseURL: baseURL, userID: userID)
        async let boardTask = PlanService.board(baseURL: baseURL, userID: userID)

        // Keep the last-good nudge on a failed re-fetch: an empty COACH card
        // on a family that HAS a nudge is worse than stale.
        if let fetched = try? await nudgeTask { nudge = fetched }
        hasLoadedNudge = true

        // Same keep-last-good rule for the board: a failed re-fetch must not
        // blank cards the parent already saw.
        if let board = try? await boardTask {
            people = HomeTodayBuilder.build(board: board, parentName: parentName)
        }
    }

    /// Re-derive the parent group's label after the profile fetch resolves the
    /// display name (the board and profile load concurrently).
    func applyParentName(_ name: String) {
        guard !name.trimmingCharacters(in: .whitespaces).isEmpty else { return }
        people = people.map { group in
            group.isParent && group.name != name
                ? PersonToday(name: name, isParent: true, activities: group.activities)
                : group
        }
    }
}

// MARK: - Shared chrome

/// The frame's underlined teal action link ("Update Benjamin's planner",
/// "Schedule an errand" — nodes `29:2803`/`29:3744`): Inter 400 13/18,
/// underlined, `accent/press` `#0A5570`. That hex is the existing `accentDeep`
/// primitive (`tealDeep`) — documented as fill-only, but the Heisman frame
/// draws it as link TEXT; usage note flagged in the linter PAIRS entry.
struct HomeUnderlineLink: View {
    let title: String

    var body: some View {
        Text(title)
            .font(.hearthBodySM)
            .underline()
            .foregroundColor(.accentDeep)
    }
}

// MARK: - The card

/// One person's TODAY card (measured `29:2796`): `bg/elevated` `#FCFBF8`
/// (the `bgCoachBanner` primitive — Heisman's elevated card cream, not the
/// pure-white `bgElevated`), 1px `#C8C3B8` border (nearest token
/// `borderInputPill` `#C9C5BE`), r=24, pad 30, stack gap 6.
struct HomeTodayCard: View {
    let person: PersonToday
    /// Routes to the Planner tab — the one existing plan-mutation path.
    var onOpenPlanner: (() -> Void)?

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // Article block: eyebrow → items, gap 9, pb 12 (measured `29:2797`;
            // 9 is the frame's own odd value, same precedent as the measured
            // 30pt card pads).
            VStack(alignment: .leading, spacing: 9) {
                // Person-name eyebrow: Inter 700 13/18 `#989591` (`29:2798`).
                Text(person.name)
                    .font(.hearthBodySMBold)
                    .foregroundColor(.inkEyebrow)

                ForEach(person.activities) { activity in
                    HomeTodayItem(activity: activity)
                }
            }
            .padding(.bottom, .hearth400)

            if let onOpenPlanner {
                Button {
                    Analytics.capture("home_update_planner_tapped",
                                      ["is_parent": person.isParent])
                    onOpenPlanner()
                } label: {
                    HomeUnderlineLink(title: "Update \(person.name)’s planner")
                }
                .buttonStyle(.plain)
            }
        }
        .padding(30)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.bgCoachBanner)
        .overlay(
            RoundedRectangle(cornerRadius: .hearthRadiusSheet, style: .continuous)
                .strokeBorder(Color.borderInputPill, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusSheet, style: .continuous))
    }
}

/// One activity inside a TODAY card (measured `29:2799`): title, schedule
/// line, provenance line — internal gap 13.
private struct HomeTodayItem: View {
    let activity: BoardActivity

    /// "Sat 9:00 am · Cedar Field" — the server-rendered `when` (verbatim,
    /// per the no-client-date-logic rule) or the saved schedule text, plus
    /// the location. Empty parts collapse; an empty line renders nothing.
    private var scheduleLine: String {
        var parts: [String] = []
        if let when = activity.when, !when.isEmpty {
            parts.append(when)
        } else if let schedule = activity.scheduleText, !schedule.isEmpty {
            parts.append(schedule)
        }
        if let place = activity.locationText, !place.isEmpty { parts.append(place) }
        return parts.joined(separator: " · ")
    }

    /// The muted provenance line ("added by your coach · repeats Saturdays"
    /// in the frame). Real data only: the onboarding seed's context note or a
    /// watched registration window's server-rendered line. Nothing → no line;
    /// the frame's sample copy is treatment, not content to fabricate.
    private var provenanceLine: String? {
        if let notes = activity.notes,
           !notes.trimmingCharacters(in: .whitespaces).isEmpty { return notes }
        if let window = activity.registrationWindow { return window.line }
        return nil
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 13) {
            // Title: Inter 700 17/26, charcoal `#4A4741` (`29:2800`) — the
            // Heisman ink-500. That hex exists only as the funnel-button fill
            // primitive (`charcoalBtn`); reused here as INK. Token-name gap
            // flagged — needs an `ink` alias in the token reconciliation PR.
            Text(activity.name)
                .font(.hearthBodyLG.weight(.bold))
                .foregroundColor(.bgButtonFunnel)
                .fixedSize(horizontal: false, vertical: true)

            if !scheduleLine.isEmpty {
                // Schedule: Inter 400 13/18, ink/primary (`29:2801`).
                Text(scheduleLine)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkPrimary)
                    .fixedSize(horizontal: false, vertical: true)
            }

            if let provenanceLine {
                // Provenance: JetBrains Mono 12/16 in the frame's `#C8C3B8`
                // (Heisman ink-100) — nearest token `borderInputPill`
                // (`#C9C5BE`), a border primitive reused as deliberately
                // faint ink. Fails AA as drawn; waiver in the linter PAIRS.
                Text(provenanceLine)
                    .font(.hearthCaptionMono)
                    .foregroundColor(.borderInputPill)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.bottom, .hearth400)
    }
}
