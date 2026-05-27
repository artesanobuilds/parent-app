import SwiftUI

/// Per-kid card section on HomeView. Shows one card per kid in the family
/// profile. Tap opens ReviewLetterView. Status pills come from the kid's
/// KidAgentConfig (Not built / Draft / Active).
struct KidsHomeSection: View {
    let userID: String
    let baseURL: URL

    @StateObject private var vm: KidsHomeViewModel

    init(userID: String, baseURL: URL) {
        self.userID = userID
        self.baseURL = baseURL
        _vm = StateObject(wrappedValue: KidsHomeViewModel(userID: userID, baseURL: baseURL))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Companions")
                    .font(.footnote.weight(.semibold))
                    .foregroundColor(.brandGray)
                    .textCase(.uppercase)
                    .tracking(0.5)
                Spacer()
                if vm.isLoading {
                    ProgressView().tint(.brandGray).scaleEffect(0.7)
                }
            }

            if vm.kids.isEmpty && !vm.isLoading {
                emptyState
            } else {
                VStack(spacing: 10) {
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
        .task { await vm.refresh() }
    }

    private var emptyState: some View {
        Text("Add a kid in onboarding to set up their companion.")
            .font(.subheadline)
            .foregroundColor(.brandGray)
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.brandSurface)
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

private struct KidCard: View {
    let kidName: String
    let agentName: String
    let summary: String
    let status: KidsHomeViewModel.Status

    var body: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(Color.brandGold.opacity(0.25))
                .frame(width: 44, height: 44)
                .overlay(
                    Text(String(kidName.prefix(1)))
                        .font(.headline.weight(.semibold))
                        .foregroundColor(.brandGold)
                )

            VStack(alignment: .leading, spacing: 4) {
                Text(kidName)
                    .font(.subheadline.weight(.semibold))
                    .foregroundColor(.white)
                Text("\(kidName)'s friend, \(agentName)")
                    .font(.caption)
                    .foregroundColor(.brandGray)
                if !summary.isEmpty {
                    Text(summary)
                        .font(.caption2)
                        .foregroundColor(.brandGray.opacity(0.85))
                        .lineLimit(2)
                }
            }
            Spacer()
            statusPill
        }
        .padding(12)
        .background(Color.brandSurface)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private var statusPill: some View {
        let (label, fg, bg): (String, Color, Color) = {
            switch status {
            case .active:  return ("Active",       .brandBlack, .brandGold)
            case .draft:   return ("Introduce",    .brandGold,  .brandSurface)
            case .missing: return ("Set up",       .brandGold,  .brandSurface)
            }
        }()
        return Text(label)
            .font(.caption2.weight(.semibold))
            .foregroundColor(fg)
            .padding(.horizontal, 10).padding(.vertical, 5)
            .background(bg)
            .overlay(
                Capsule().stroke(status == .active ? Color.clear : Color.brandGold.opacity(0.4),
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
