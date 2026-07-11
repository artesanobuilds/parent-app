import SwiftUI

/// THE board-card primitive (one per platform — web mirrors this in
/// `src/components/Card.tsx`). Extracted from `PlanView` when the vertical
/// chip became the second per-card divergence (vertical expansion Phase 3).
///
/// The card is a dumb renderer of server-driven state (`nextStep`, `when`,
/// `activityType`); every action is a closure owned by the Plan hub, so the
/// hub keeps its confirm dialogs, view model, and chat-segment wiring.
struct BoardCardView: View {
    let activity: BoardActivity
    let gmailConnected: Bool
    let busy: Bool
    /// Show the vertical chip only when the board actually spans verticals.
    let showVerticalChip: Bool
    /// True while the headline to-do (or any shown to-do) is mutating.
    let busyTodoIds: Set<String>

    /// (activity, newStatus, rationale) — status advances from the card.
    let onAdvance: (BoardActivity, String, String?) -> Void
    let onCompleteTodo: (String) -> Void
    /// "resolve" CTA: hand the blocker to the chat segment.
    let onResolveInChat: (BoardActivity, String) -> Void
    /// Registered-stage pass — the hub confirms first (clears to-dos).
    let onPassConfirm: (BoardActivity) -> Void
    /// Declined-stage permanent delete — the hub confirms first.
    let onDeleteConfirm: (BoardActivity) -> Void

    /// Chip labels for every canonical vertical — includes not-yet-doored
    /// types so an organically-typed card still gets a sensible chip.
    static let chipLabels: [String: String] = [
        "camp": "Camp",
        "extracurricular": "Class",
        "outing": "Outing",
        "school_event": "School",
        "trip": "Trip",
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            HStack(alignment: .firstTextBaseline) {
                Text(activity.name)
                    .font(.hearthBodyLG.weight(.semibold))
                    .foregroundColor(.inkPrimary)
                    .multilineTextAlignment(.leading)
                Spacer()
                overflowMenu
            }
            HStack(spacing: .hearth300) {
                if showVerticalChip, let type = activity.activityType {
                    Text(Self.chipLabels[type] ?? type)
                        .font(.hearthCaptionMono)
                        .foregroundColor(.inkSecondary)
                        .padding(.horizontal, .hearth400)
                        .padding(.vertical, 4)
                        .background(
                            Capsule().stroke(Color.borderHairline, lineWidth: 1)
                        )
                }
                if let kid = activity.kidName {
                    Text(kid)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkSecondary)
                        .padding(.horizontal, .hearth400)
                        .padding(.vertical, 4)
                        .background(Capsule().fill(Color.accentTint))
                }
                if let provider = activity.provider {
                    Text(provider)
                        .font(.hearthBodySM)
                        .foregroundColor(.inkSecondary)
                }
                Spacer(minLength: 0)
                if let price = activity.priceAmount {
                    Text("$\(Int(price))")
                        .font(.hearthCaptionMono)
                        .foregroundColor(.inkSecondary)
                }
            }
            // Server-rendered date line — shown verbatim (never re-formatted here).
            if let when = activity.when {
                Text(when)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
            }
            trackingLine
            nextStepControls
            // Any remaining open to-dos beyond the headline one, each completable.
            if activity.openTodos.count > 1 {
                VStack(alignment: .leading, spacing: .hearth300) {
                    ForEach(activity.openTodos.dropFirst()) { todo in
                        todoRow(todo)
                    }
                }
            }
        }
        .padding(.hearth500)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                .fill(Color.bgElevated)
                .overlay(
                    RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                        .stroke(Color.borderHairline, lineWidth: 1)
                )
        )
        .opacity(busy ? 0.55 : 1)
        .disabled(busy)
    }

    /// Per-card secondary actions: Pass works from ANY stage (plans change even
    /// after registering — a registered pass confirms first since it clears the
    /// item's to-dos); declined cards gain a permanent, confirm-gated delete.
    @ViewBuilder
    private var overflowMenu: some View {
        let stage = activity.nextStep.stage
        if stage == "considering" {
            // Low-stakes: keep the direct inline Pass, no menu needed.
            Button {
                onAdvance(activity, "declined", "Passed from the board")
            } label: {
                Text("Pass")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Pass on \(activity.name)")
        } else {
            Menu {
                if stage == "declined" {
                    Button(role: .destructive) { onDeleteConfirm(activity) } label: {
                        Label("Delete forever", systemImage: "trash")
                    }
                } else if stage == "to_register" {
                    Button {
                        onAdvance(activity, "declined", "Passed from the board")
                    } label: {
                        Label("Pass on this", systemImage: "xmark.circle")
                    }
                } else {
                    // Registered / all-set: confirm first — passing clears its to-dos.
                    Button { onPassConfirm(activity) } label: {
                        Label("Pass on this", systemImage: "xmark.circle")
                    }
                }
            } label: {
                Image(systemName: "ellipsis")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.inkMuted)
                    .frame(width: 32, height: 32)
            }
            .accessibilityLabel("More actions for \(activity.name)")
        }
    }

    /// The visible "this is what the system is doing" line — automated behavior
    /// is never invisible (the lesson from the crisis-lock UX).
    @ViewBuilder
    private var trackingLine: some View {
        let stage = activity.nextStep.stage
        if stage == "registered" || stage == "all_set" {
            if activity.watching {
                Label("Watching \(activity.provider ?? activity.name)'s emails for confirmations & payment reminders",
                      systemImage: "eye")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
            } else if !activity.watchable {
                Label("Add the provider's contact email so I can watch for confirmations",
                      systemImage: "envelope.badge")
                    .font(.hearthBodySM)
                    .foregroundColor(.statusWarning)
            } else if !gmailConnected {
                Label("Connect Gmail to auto-track activity emails — or paste a confirmation into Add info",
                      systemImage: "envelope")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
            }
        }
    }

    /// The ONE primary next action; its hint (the consequence) renders right
    /// under the button so a first-timer can predict the tap.
    @ViewBuilder
    private var nextStepControls: some View {
        let step = activity.nextStep
        VStack(alignment: .leading, spacing: .hearth300) {
            switch step.action {
            case "plan":
                primaryButton(step.label, icon: "checkmark") {
                    onAdvance(activity, "planned", "Chosen from the board")
                }
            case "register":
                HStack(spacing: .hearth400) {
                    if let urlString = step.url, let url = URL(string: urlString) {
                        Link(destination: url) {
                            buttonLabel(step.label, icon: "arrow.up.right.square")
                        }
                    }
                    Button {
                        onAdvance(activity, "signed_up", nil)
                    } label: {
                        Text("Mark registered")
                            .font(.hearthBodyMD.weight(.semibold))
                            .foregroundColor(.accentDefault)
                            .padding(.horizontal, .hearth500)
                            .padding(.vertical, .hearth400)
                            .background(Capsule().fill(Color.accentTint))
                    }
                    .buttonStyle(.plain)
                }
            case "mark_registered":
                primaryButton(step.label, icon: "checkmark.seal") {
                    onAdvance(activity, "signed_up", nil)
                }
            case "complete_todo":
                primaryButton(step.label, icon: "checkmark.circle") {
                    if let todoId = step.todoId {
                        onCompleteTodo(todoId)
                    }
                }
            case "resolve":
                primaryButton(step.label, icon: "questionmark.circle") {
                    onResolveInChat(activity, step.label)
                }
            case "restore":
                primaryButton(step.label, icon: "arrow.uturn.backward") {
                    onAdvance(activity, "exploring", nil)
                }
            default:
                EmptyView()
            }
            if !step.hint.isEmpty {
                Text(step.hint)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
            }
        }
    }

    private func todoRow(_ todo: PlanTodo) -> some View {
        let todoBusy = busyTodoIds.contains(todo.id)
        return HStack(spacing: .hearth300) {
            Button {
                onCompleteTodo(todo.id)
            } label: {
                Image(systemName: "circle")
                    .font(.system(size: 15))
                    .foregroundColor(.accentDefault)
                    .frame(width: 28, height: 28)
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Mark done: \(todo.title)")
            Text(todo.title)
                .font(.hearthBodySM)
                .foregroundColor(.inkSecondary)
            Spacer(minLength: 0)
            if let due = todo.dueDate {
                Text(due)
                    .font(.hearthCaptionMono)
                    .foregroundColor(.inkMuted)
            }
        }
        .opacity(todoBusy ? 0.55 : 1)
        .disabled(todoBusy)
    }

    private func primaryButton(_ title: String, icon: String,
                               action: @escaping () -> Void) -> some View {
        Button(action: action) {
            buttonLabel(title, icon: icon)
        }
        .buttonStyle(.plain)
    }

    private func buttonLabel(_ title: String, icon: String) -> some View {
        Label(title, systemImage: icon)
            .font(.hearthBodyMD.weight(.semibold))
            .foregroundColor(.inkOnPhotoLight)
            .lineLimit(2)
            .multilineTextAlignment(.leading)
            .padding(.horizontal, .hearth500)
            .padding(.vertical, .hearth400)
            .background(Capsule().fill(Color.accentDefault))
    }
}
