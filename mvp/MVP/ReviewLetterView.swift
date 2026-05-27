import SwiftUI
import Combine

/// Parent's review surface for a kid's auto-generated companion.
///
/// Layout (single canvas, no split-pane — Jony's note):
///   - Header: kid name + agent's display name (editable inline)
///   - Letter: serif TextEditor styled as a letter, parent edits prose freely
///   - Chips: tappable structured edits (blocked topics, tools, goals)
///   - 3-message preview: regenerated live (debounced) as parent edits
///   - "Introduce them" button: saves with enable=true
struct ReviewLetterView: View {
    let userID: String
    let kidName: String
    let baseURL: URL

    @StateObject private var vm: ReviewLetterViewModel
    @Environment(\.dismiss) private var dismiss

    init(userID: String, kidName: String, baseURL: URL) {
        self.userID  = userID
        self.kidName = kidName
        self.baseURL = baseURL
        _vm = StateObject(wrappedValue: ReviewLetterViewModel(
            userID: userID, kidName: kidName, baseURL: baseURL
        ))
    }

    var body: some View {
        ZStack {
            Color.brandBackground.ignoresSafeArea()

            if vm.needsConsent {
                ConsentView(
                    userID: userID,
                    baseURL: baseURL,
                    agreementVersion: vm.consentVersion ?? "closed-beta-v1-2026-05",
                    onAccepted: { Task { await vm.load() } }
                )
            } else if vm.isLoading {
                ProgressView().tint(.brandGold)
            } else if let config = vm.config {
                content(config: config)
            } else if let error = vm.error {
                errorBanner(error)
            } else {
                ProgressView().tint(.brandGold)
            }
        }
        .task { await vm.load() }
    }

    @ViewBuilder
    private func content(config: KidAgentConfig) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                header(config: config)
                letter(config: config)
                topicChips
                toolToggles
                if !vm.previewMessages.isEmpty { previewSection }
                introduceButton
            }
            .padding(20)
        }
    }

    private func header(config: KidAgentConfig) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("\(kidName)'s friend")
                .font(.caption.weight(.semibold))
                .foregroundColor(.brandGold)
                .textCase(.uppercase)
                .tracking(0.6)

            HStack(spacing: 8) {
                TextField("name", text: $vm.agentName)
                    .font(.system(.title2, design: .serif).weight(.semibold))
                    .foregroundColor(.white)
                    .padding(.vertical, 6)
                    .padding(.horizontal, 8)
                    .background(Color.brandSurface)
                    .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))

                if config.enabled {
                    Text("active")
                        .font(.caption2.weight(.semibold))
                        .foregroundColor(.brandBlack)
                        .padding(.horizontal, 8).padding(.vertical, 4)
                        .background(Color.brandGold)
                        .clipShape(Capsule())
                } else {
                    Text("draft")
                        .font(.caption2.weight(.semibold))
                        .foregroundColor(.brandGray)
                        .padding(.horizontal, 8).padding(.vertical, 4)
                        .background(Color.brandSurface)
                        .clipShape(Capsule())
                }
            }
        }
    }

    private func letter(config: KidAgentConfig) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("Dear \(vm.agentName),")
                .font(.system(.title3, design: .serif))
                .foregroundColor(.brandNavy)
                .padding(.bottom, 8)

            // Free-text editable body. Type anywhere to refine the letter.
            TextEditor(text: $vm.brief)
                .font(.system(.body, design: .serif))
                .foregroundColor(.brandNavy)
                .scrollContentBackground(.hidden)
                .frame(minHeight: 220)

            HStack {
                Spacer()
                Text("— \(vm.parentSignOff)")
                    .font(.system(.callout, design: .serif).italic())
                    .foregroundColor(.brandGray)
            }
            .padding(.top, 8)
        }
        .padding(20)
        .background(Color.brandCardBackground)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    private var topicChips: some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionHeader("Off-limits topics")
            FlowLayout(spacing: 6) {
                ForEach(vm.invariants.topicsBlocked, id: \.self) { topic in
                    Button {
                        vm.removeBlockedTopic(topic)
                    } label: {
                        HStack(spacing: 4) {
                            Text(topic)
                            Image(systemName: "xmark")
                                .font(.system(size: 10, weight: .bold))
                        }
                        .font(.subheadline)
                        .foregroundColor(.white)
                        .padding(.horizontal, 10).padding(.vertical, 6)
                        .background(Color.brandSurface)
                        .clipShape(Capsule())
                    }
                }
                Button { vm.showAddBlocked = true } label: {
                    Label("Add", systemImage: "plus")
                        .font(.subheadline.weight(.medium))
                        .foregroundColor(.brandGold)
                        .padding(.horizontal, 10).padding(.vertical, 6)
                        .overlay(
                            Capsule().stroke(Color.brandGold.opacity(0.6), lineWidth: 1)
                        )
                }
            }
        }
        .alert("Add a topic to block", isPresented: $vm.showAddBlocked) {
            TextField("e.g. violence", text: $vm.addBlockedDraft)
            Button("Add") { vm.commitAddBlocked() }
            Button("Cancel", role: .cancel) { vm.addBlockedDraft = "" }
        }
    }

    private var toolToggles: some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionHeader("Tools")
            ForEach(ReviewLetterViewModel.toolKeys, id: \.self) { key in
                Toggle(isOn: vm.toolBinding(for: key)) {
                    Text(ReviewLetterViewModel.toolLabel(for: key))
                        .font(.subheadline)
                        .foregroundColor(.white)
                }
                .toggleStyle(.switch)
                .tint(.brandGold)
            }
        }
        .padding(14)
        .background(Color.brandSurface)
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private var previewSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionHeader("How they might say hello")
            VStack(alignment: .leading, spacing: 10) {
                ForEach(Array(vm.previewMessages.enumerated()), id: \.offset) { _, line in
                    HStack(alignment: .top, spacing: 10) {
                        Circle()
                            .fill(Color.brandGold.opacity(0.25))
                            .frame(width: 28, height: 28)
                            .overlay(
                                Text(String(vm.agentName.prefix(1)))
                                    .font(.caption.weight(.bold))
                                    .foregroundColor(.brandGold)
                            )
                        Text(line)
                            .font(.system(.callout, design: .serif))
                            .foregroundColor(.white)
                            .padding(10)
                            .background(Color.brandSurface)
                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                if vm.isPreviewLoading {
                    HStack(spacing: 6) {
                        ProgressView().tint(.brandGray).scaleEffect(0.7)
                        Text("regenerating…")
                            .font(.caption)
                            .foregroundColor(.brandGray)
                    }
                }
            }
        }
    }

    private var introduceButton: some View {
        Button {
            Task { await vm.saveAndIntroduce(dismiss: dismiss) }
        } label: {
            HStack(spacing: 8) {
                if vm.isSaving { ProgressView().tint(.brandBlack) }
                Text(vm.isSaving ? "Saving…" : "Introduce them")
                    .font(.headline.weight(.semibold))
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 14)
            .background(Color.brandGold)
            .foregroundColor(.brandBlack)
            .clipShape(Capsule())
        }
        .disabled(vm.isSaving)
        .padding(.top, 8)
    }

    private func sectionHeader(_ text: String) -> some View {
        Text(text)
            .font(.caption.weight(.semibold))
            .foregroundColor(.brandGold)
            .textCase(.uppercase)
            .tracking(0.6)
    }

    private func errorBanner(_ message: String) -> some View {
        VStack(spacing: 12) {
            Text(message)
                .multilineTextAlignment(.center)
                .foregroundColor(.white)
                .padding()
            Button("Try again") { Task { await vm.load() } }
                .buttonStyle(.bordered)
                .tint(.brandGold)
        }
    }
}


// MARK: - ViewModel

@MainActor
final class ReviewLetterViewModel: ObservableObject {

    let userID: String
    let kidName: String
    let baseURL: URL
    private let service: KidAgentService

    @Published var config: KidAgentConfig?
    @Published var invariants: KidAgentInvariants = .empty
    @Published var brief: String = ""
    @Published var agentName: String = "Friend"
    @Published var previewMessages: [String] = []
    @Published var isLoading: Bool = false
    @Published var isSaving: Bool = false
    @Published var isPreviewLoading: Bool = false
    @Published var error: String?
    @Published var needsConsent: Bool = false
    @Published var consentVersion: String?
    @Published var showAddBlocked: Bool = false
    @Published var addBlockedDraft: String = ""

    var parentSignOff: String { "their grown-up" }

    static let toolKeys = ["web_search", "image_upload", "image_generation",
                           "math_solver", "reading_helper"]
    static func toolLabel(for key: String) -> String {
        switch key {
        case "web_search":       return "Web search"
        case "image_upload":     return "Image upload"
        case "image_generation": return "Image generation"
        case "math_solver":      return "Math solver"
        case "reading_helper":   return "Reading helper"
        default:                 return key
        }
    }

    private var debounceTask: Task<Void, Never>?

    init(userID: String, kidName: String, baseURL: URL) {
        self.userID = userID
        self.kidName = kidName
        self.baseURL = baseURL
        self.service = KidAgentService(baseURL: baseURL, userID: userID)
    }

    func load() async {
        isLoading = true
        error = nil
        needsConsent = false
        do {
            let config = try await service.config(forKid: kidName)
            self.config = config
            self.invariants = config.invariants
            self.brief = config.freeTextBrief.isEmpty
                ? defaultBrief(from: config.invariants)
                : config.freeTextBrief
            self.agentName = config.invariants.agentDisplayName
            // Trigger an initial preview so the parent sees how the agent sounds today.
            schedulePreview(brief: brief)
        } catch KidAgentServiceError.consentRequired(let version) {
            consentVersion = version
            needsConsent = true
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }

    func toolBinding(for key: String) -> Binding<Bool> {
        Binding(
            get: { self.invariants.toolsEnabled[key] ?? false },
            set: { newValue in
                self.invariants.toolsEnabled[key] = newValue
                self.schedulePreview(brief: self.composedBrief())
            }
        )
    }

    func removeBlockedTopic(_ topic: String) {
        invariants.topicsBlocked.removeAll { $0 == topic }
        schedulePreview(brief: composedBrief())
    }

    func commitAddBlocked() {
        let trimmed = addBlockedDraft.trimmingCharacters(in: .whitespacesAndNewlines)
        addBlockedDraft = ""
        guard !trimmed.isEmpty,
              !invariants.topicsBlocked.contains(trimmed) else { return }
        invariants.topicsBlocked.append(trimmed)
        schedulePreview(brief: composedBrief())
    }

    /// Builds the brief from the editable prose + the structured invariants the
    /// parent toggled. The synthesizer treats it all as parent intent.
    private func composedBrief() -> String {
        var parts: [String] = [brief]
        if !invariants.topicsBlocked.isEmpty {
            parts.append("Off-limits: \(invariants.topicsBlocked.joined(separator: ", ")).")
        }
        let enabled = invariants.toolsEnabled.filter { $0.value }.map(\.key)
        if !enabled.isEmpty {
            parts.append("Tools enabled: \(enabled.joined(separator: ", ")).")
        }
        if !agentName.isEmpty, agentName != invariants.agentDisplayName {
            parts.append("Call you \(agentName).")
        }
        return parts.joined(separator: "\n\n")
    }

    /// Default letter prose generated from current invariants — gives the
    /// parent a starting point on first load, even if the backend stored brief
    /// is empty.
    private func defaultBrief(from inv: KidAgentInvariants) -> String {
        var lines: [String] = []
        if !inv.personalityDescription.isEmpty {
            lines.append(inv.personalityDescription)
        }
        if !inv.interestsSummary.isEmpty { lines.append(inv.interestsSummary) }
        if !inv.goals.isEmpty {
            lines.append("Help with: \(inv.goals.joined(separator: ", ")).")
        }
        return lines.joined(separator: "\n\n")
    }

    /// Debounced live regeneration of the 3-message preview.
    private func schedulePreview(brief: String) {
        debounceTask?.cancel()
        debounceTask = Task { [weak self] in
            try? await Task.sleep(nanoseconds: 600_000_000)
            guard !Task.isCancelled, let self else { return }
            await self.regeneratePreview(brief: brief)
        }
    }

    private func regeneratePreview(brief: String) async {
        isPreviewLoading = true
        defer { isPreviewLoading = false }
        do {
            let preview = try await service.preview(forKid: kidName, brief: brief)
            self.invariants = preview.invariants
            self.previewMessages = preview.previewMessages
            if !preview.invariants.agentDisplayName.isEmpty,
               agentName != preview.invariants.agentDisplayName {
                // Suggested name evolves when the brief implies a new identity;
                // don't override if the parent has explicitly set one.
            }
        } catch {
            // Preview is non-critical — log and move on.
            print("[ReviewLetter] preview failed: \(error)")
        }
    }

    func saveAndIntroduce(dismiss: DismissAction) async {
        isSaving = true
        defer { isSaving = false }
        do {
            invariants.agentDisplayName = agentName
            let saved = try await service.save(
                forKid: kidName,
                brief: composedBrief(),
                expectedVersion: config?.version,
                enable: true
            )
            self.config = saved
            self.invariants = saved.invariants
            dismiss()
        } catch KidAgentServiceError.versionConflict {
            error = "Someone updated this agent — pulling the latest version."
            await load()
        } catch KidAgentServiceError.consentRequired(let version) {
            consentVersion = version
            needsConsent = true
        } catch {
            self.error = error.localizedDescription
        }
    }
}


// MARK: - FlowLayout (chip wrap)

/// Tiny custom layout for chip-style wrapping. Replaces external dep.
struct FlowLayout: Layout {
    var spacing: CGFloat = 6

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let width = proposal.width ?? .infinity
        var x: CGFloat = 0
        var y: CGFloat = 0
        var rowHeight: CGFloat = 0
        for sub in subviews {
            let sz = sub.sizeThatFits(.unspecified)
            if x + sz.width > width {
                x = 0
                y += rowHeight + spacing
                rowHeight = 0
            }
            rowHeight = max(rowHeight, sz.height)
            x += sz.width + spacing
        }
        return CGSize(width: proposal.width ?? width, height: y + rowHeight)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let width = bounds.width
        var x = bounds.minX
        var y = bounds.minY
        var rowHeight: CGFloat = 0
        for sub in subviews {
            let sz = sub.sizeThatFits(.unspecified)
            if x + sz.width > bounds.minX + width {
                x = bounds.minX
                y += rowHeight + spacing
                rowHeight = 0
            }
            sub.place(at: CGPoint(x: x, y: y), proposal: ProposedViewSize(sz))
            rowHeight = max(rowHeight, sz.height)
            x += sz.width + spacing
        }
    }
}
