import SwiftUI

/// Per-kid card section on HomeView. Shows one card per kid in the family
/// profile. Tap opens ReviewLetterView. Status pills come from the kid's
/// KidAgentConfig (Not built / Draft / Active).
struct KidsHomeSection: View {
    let userID: String
    let baseURL: URL
    /// Bumped by HomeView when the Settings sheet closes; a change re-runs the
    /// refresh so profile edits/adds/deletes show without an app relaunch.
    var refreshToken: Int = 0

    @StateObject private var vm: KidsHomeViewModel
    // Persisted flag so HomeView's greeting header can conditionally show
    // the "Hand to kid" button only when at least one companion exists.
    @AppStorage("has_kid_companions") private var hasKidCompanions: Bool = false

    init(userID: String, baseURL: URL, refreshToken: Int = 0) {
        self.userID = userID
        self.baseURL = baseURL
        self.refreshToken = refreshToken
        _vm = StateObject(wrappedValue: KidsHomeViewModel(userID: userID, baseURL: baseURL))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            HStack {
                Text("Companions")
                    .font(.hearthLabel)
                    .foregroundColor(.inkMuted)
                    .tracking(0.66)
                    .textCase(.uppercase)
                Spacer()
                if vm.isLoading {
                    ProgressView().tint(.inkMuted).scaleEffect(0.7)
                }
            }

            if vm.kids.isEmpty && !vm.isLoading {
                emptyState
            } else {
                VStack(spacing: .hearth400) {
                    ForEach(vm.kids, id: \.kidName) { kid in
                        NavigationLink(value: KidNavigation.review(kidName: kid.kidName)) {
                            KidCard(
                                kidName: kid.kidName,
                                agentName: kid.invariants.agentDisplayName,
                                summary: kid.summary,
                                status: kid.status
                            )
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
        .navigationDestination(for: KidNavigation.self) { destination in
            switch destination {
            case .review(let kidName):
                ReviewLetterView(userID: userID, kidName: kidName, baseURL: baseURL)
                    .navigationBarTitleDisplayMode(.inline)
            }
        }
        .task(id: refreshToken) {
            await vm.refresh()
            // Surface ACTIVE-companion count to the flag — draft/missing
            // configs don't count: the Hand-to-kid handoff opens a picker
            // that has zero pickable options if no kid is enabled, so we
            // must not show the CTA in that case.
            hasKidCompanions = vm.kids.contains { $0.status == .active }
        }
        .onChange(of: vm.kids.filter({ $0.status == .active }).count) { _, activeCount in
            hasKidCompanions = activeCount > 0
        }
    }

    private var emptyState: some View {
        Text("Add a kid in onboarding to set up their companion.")
            .font(.hearthBodyMD)
            .foregroundColor(.inkMuted)
            .padding(.hearth500)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.bgElevated)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                    .stroke(Color.borderHairline, lineWidth: 1)
            )
    }
}

private struct KidCard: View {
    let kidName: String
    let agentName: String
    let summary: String
    let status: KidsHomeViewModel.Status

    var body: some View {
        HStack(spacing: .hearth400) {
            Circle()
                .fill(Color.accentTint)
                .frame(width: 44, height: 44)
                .overlay(
                    Text(String(kidName.prefix(1)))
                        .font(.hearthTitleMD)
                        .foregroundColor(.accentDefault)
                )

            VStack(alignment: .leading, spacing: .hearth300) {
                Text(kidName)
                    .font(.hearthTitleMD)
                    .foregroundColor(.inkPrimary)
                Text("\(kidName)'s friend, \(agentName)")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                if !summary.isEmpty {
                    Text(summary)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkMuted)
                        .lineLimit(2)
                }
            }
            Spacer()
            statusPill
        }
        .padding(.hearth400)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                .stroke(Color.borderHairline, lineWidth: 1)
        )
    }

    private var statusPill: some View {
        let (label, fg, bg): (String, Color, Color) = {
            switch status {
            case .active:  return ("Active",    .inkOnPhotoLight, .accentDefault)
            case .draft:   return ("Introduce", .accentDefault,   .accentTint)
            case .missing: return ("Set up",    .inkMuted,        .bgElevated)
            }
        }()
        return Text(label)
            .font(.hearthLabel)
            .foregroundColor(fg)
            .tracking(0.66)
            .textCase(.uppercase)
            .padding(.horizontal, .hearth400).padding(.vertical, .hearth300)
            .background(bg)
            .overlay(
                Capsule().stroke(status == .active ? Color.clear : Color.accentDefault.opacity(0.4),
                                 lineWidth: 1)
            )
            .clipShape(Capsule())
    }
}

enum KidNavigation: Hashable {
    case review(kidName: String)
}

@MainActor
final class KidsHomeViewModel: ObservableObject {

    enum Status { case active, draft, missing }

    struct KidEntry: Identifiable {
        let kidName: String
        let invariants: KidAgentInvariants
        let summary: String
        let status: Status
        var id: String { kidName }
    }

    let userID: String
    let baseURL: URL
    private let service: KidAgentService

    @Published var kids: [KidEntry] = []
    @Published var isLoading = false
    @Published var error: String?

    init(userID: String, baseURL: URL) {
        self.userID = userID
        self.baseURL = baseURL
        self.service = KidAgentService(baseURL: baseURL, userID: userID)
    }

    func refresh() async {
        guard !isLoading else { return }
        isLoading = true
        defer { isLoading = false }
        do {
            // Family profile is the source of truth for who gets a card.
            // Configs only fill in display name and status — they're absent
            // for fresh families and during pre-consent state.
            let svc = service
            async let familyTask = svc.familyChildren()
            async let configsTask = Self.listOrEmpty(svc)
            let (family, configs) = try await (familyTask, configsTask)

            let configByName = Dictionary(grouping: configs, by: { $0.kidName })
                .compactMapValues(\.first)

            self.kids = family.map { child in
                if let cfg = configByName[child.name] {
                    return KidEntry(
                        kidName: cfg.kidName,
                        invariants: cfg.invariants,
                        summary: cfg.invariants.interestsSummary,
                        status: cfg.enabled ? .active : .draft
                    )
                }
                let summary: String = {
                    if let a = child.age { return "\(Int(a)) years old · tap to introduce" }
                    return "tap to introduce"
                }()
                return KidEntry(
                    kidName: child.name,
                    invariants: .empty,
                    summary: summary,
                    status: .missing
                )
            }
        } catch {
            self.error = error.localizedDescription
            print("[KidsHome] refresh failed: \(error)")
        }
    }

    /// Wrap `service.list()` so consent-required and other errors don't
    /// mask the family-profile fetch.
    private static func listOrEmpty(_ service: KidAgentService) async -> [KidAgentConfig] {
        do { return try await service.list() }
        catch KidAgentServiceError.consentRequired { return [] }
        catch { return [] }
    }
}
