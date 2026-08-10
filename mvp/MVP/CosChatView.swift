import SwiftUI
import MarkdownUI

/// Chief-of-staff chat. Modeled on `AgentView`'s message list + input area, but
/// scoped to the planning conversation (`/cos/chat`) — no voice surface and no
/// content cards. Embedded as the default segment of the Plan hub (`PlanView`);
/// its `CosChatViewModel` is owned by `MainTabView` and injected here so the
/// conversation survives switching segments.
struct CosChatView: View {
    @ObservedObject var viewModel: CosChatViewModel
    /// Vertical doors rendered as starter cards in the empty state (server-
    /// driven copy from GET /cos/verticals; empty when not yet fetched).
    var doors: [VerticalDoor] = []
    @State private var messageText: String = ""

    init(viewModel: CosChatViewModel, doors: [VerticalDoor] = []) {
        self.viewModel = viewModel
        self.doors = doors
    }

    var body: some View {
        VStack(spacing: 0) {
            Divider().background(Color.borderHairline)
            messageList
            inputArea
        }
        .trackScreen("planning_chat")
        .onAppear { Analytics.capture("chat_opened", ["agent_kind": "planning"]) }
        // Lift the pinned input bar clear of MainTabView's floating tab bar — as
        // the Plan hub's Chat segment this view fills to the bottom of the tab
        // content, so without this the field sits flush against the tab bar.
        .padding(.bottom, .hearth700)
        .background(Color.bgCanvas.ignoresSafeArea())
        .alert(
            "Error",
            isPresented: Binding<Bool>(
                get: { viewModel.errorMessage != nil },
                set: { if !$0 { viewModel.errorMessage = nil } }
            )
        ) {
            Button("OK") { viewModel.errorMessage = nil }
        } message: {
            Text(viewModel.errorMessage ?? "")
        }
    }

    // MARK: - Message List

    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 0) {
                    if viewModel.messages.isEmpty {
                        emptyState
                    }
                    ForEach(viewModel.messages) { message in
                        if message.role == .user {
                            userMessageRow(message).id(message.id)
                        } else {
                            assistantMessageRow(message).id(message.id)
                        }
                    }
                }
                .padding(.top, .hearth300)
                // Extra bottom room so the last card / message clears the input
                // bar and can always be scrolled fully into view.
                .padding(.bottom, .hearth700)
            }
            .background(Color.bgCanvas)
            .contentShape(Rectangle())
            .onTapGesture {
                UIApplication.shared.sendAction(
                    #selector(UIResponder.resignFirstResponder),
                    to: nil, from: nil, for: nil
                )
            }
            .scrollDismissesKeyboard(.interactively)
            .onChange(of: viewModel.messages) { _, newValue in
                guard let lastID = newValue.last?.id else { return }
                withAnimation(.hearthBase) { proxy.scrollTo(lastID, anchor: .bottom) }
            }
        }
    }

    private var emptyState: some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            Circle()
                .fill(Color.accentDefault.opacity(0.12))
                .frame(width: 56, height: 56)
                .overlay(
                    Image(systemName: "calendar.badge.clock")
                        .font(.system(size: 26, weight: .medium))
                        .foregroundColor(.accentDefault)
                )

            VStack(alignment: .leading, spacing: .hearth300) {
                Text("Ask the coach")
                    .font(.hearthDisplayMD)
                    .foregroundColor(.inkPrimary)
                Text("Find camps, sort out coverage gaps, or decide between options. I see the whole family plan.")
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkSecondary)
            }

            // Sprint-2: four hardcoded starter prompts from the spec
            VStack(alignment: .leading, spacing: .hearth300) {
                Button {
                    sendSuggestion("Camps & school breaks")
                } label: {
                    starterButton("Camps & school breaks")
                }
                .buttonStyle(.plain)
                .disabled(viewModel.isSending || viewModel.isUserIDMissing)

                Button {
                    sendSuggestion("Classes & sports")
                } label: {
                    starterButton("Classes & sports")
                }
                .buttonStyle(.plain)
                .disabled(viewModel.isSending || viewModel.isUserIDMissing)

                Button {
                    sendSuggestion("Weekend outings")
                } label: {
                    starterButton("Weekend outings")
                }
                .buttonStyle(.plain)
                .disabled(viewModel.isSending || viewModel.isUserIDMissing)

                Button {
                    sendSuggestion("Family trips — dates, packing, not bookings")
                } label: {
                    starterButton("Family trips — dates, packing, not bookings")
                }
                .buttonStyle(.plain)
                .disabled(viewModel.isSending || viewModel.isUserIDMissing)
            }
        }
        .padding(.horizontal, .hearth700)
        .padding(.top, .hearth500)
    }

    // MARK: - User Message (pill)

    /// Measured `planner 5` (same component as `coach-001`): deep-teal bubble,
    /// pad 16, r=12 with an 8pt bottom-leading tail, body 14 in warm cream.
    private func userMessageRow(_ message: ChatMessage) -> some View {
        HStack {
            Spacer(minLength: 60)
            Text(message.content)
                .font(.hearthBodySM)
                .foregroundColor(.inkOnCard)
                .padding(.hearth500)
                .background(Color.accentDeep)
                .clipShape(
                    UnevenRoundedRectangle(
                        topLeadingRadius: .hearthRadiusTile,
                        bottomLeadingRadius: .hearthRadiusButton,
                        bottomTrailingRadius: .hearthRadiusTile,
                        topTrailingRadius: .hearthRadiusTile,
                        style: .continuous
                    )
                )
        }
        .padding(.horizontal, .hearth500)
        .padding(.vertical, .hearth300)
    }

    // MARK: - Assistant Message

    private func assistantMessageRow(_ message: ChatMessage) -> some View {
        HStack(alignment: .top, spacing: .hearth400) {
            Circle()
                .fill(Color.accentDefault)
                .frame(width: 30, height: 30)
                .overlay(
                    Image(systemName: "calendar.badge.clock")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.inkOnPhotoLight)
                )
                .padding(.top, 2)

            VStack(alignment: .leading, spacing: .hearth300) {
                Markdown(message.content.isEmpty ? "..." : message.content)
                    .markdownTextStyle {
                        FontFamily(.custom(HearthFontFamily.sans))
                        FontSize(15)
                        ForegroundColor(Color.inkPrimary)
                    }
                    .markdownBlockStyle(\.heading2) { configuration in
                        configuration.label
                            .markdownTextStyle {
                                FontFamily(.custom(HearthFontFamily.displaySerif))
                                FontWeight(.semibold)
                                FontSize(18)
                                ForegroundColor(Color.inkPrimary)
                            }
                    }

                if message.isStreaming {
                    HStack(spacing: .hearth300) {
                        ProgressView().scaleEffect(0.6)
                        Text("Thinking…")
                            .font(.hearthBodySM)
                            .foregroundColor(.inkMuted)
                    }
                }
            }

            Spacer(minLength: 16)
        }
        .padding(.horizontal, .hearth500)
        .padding(.vertical, .hearth300)
    }

    // MARK: - Input Area

    /// Measured `planner 5`: the composer sits on the deep-teal strip
    /// (`#0A5570`, 16pt top corners) with a white r=8 field inside — same
    /// component as the coach tab's.
    private var inputArea: some View {
        VStack(spacing: 0) {
            HStack(alignment: .bottom, spacing: .hearth400) {
                TextField("Ask about your plan", text: $messageText, axis: .vertical)
                    .font(.hearthBodySM)
                    .foregroundColor(.inkPrimary)
                    .padding(.horizontal, .hearth500)
                    .padding(.vertical, .hearth400)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusButton, style: .continuous)
                            .fill(Color.bgElevated)
                    )
                    .lineLimit(1...4)
                    .disabled(viewModel.isSending || viewModel.isUserIDMissing)
                    .textInputAutocapitalization(.sentences)
                    .onSubmit(sendMessage)

                Button {
                    sendMessage()
                } label: {
                    Image(systemName: "arrow.up")
                        .font(.system(size: 16, weight: .bold))
                        .foregroundColor(canSend ? .inkOnPhotoLight : .inkMuted)
                        .frame(width: 44, height: 44)
                        .background(
                            Circle()
                                .fill(canSend ? Color.accentDefault : Color.bgElevated)
                                .overlay(Circle().stroke(Color.borderHairline, lineWidth: canSend ? 0 : 1))
                        )
                }
                .disabled(!canSend)
            }
            .padding(.horizontal, .hearth500)
            // Symmetric breathing room above & below the field (divider→field
            // equals field→bottom of the input band).
            .padding(.vertical, .hearth500)
        }
        .background(Color.bgCanvas)
    }

    // MARK: - Starter prompts (empty state)

    private struct StarterPrompt {
        let icon: String
        let text: String
    }

    private static let starterPrompts: [StarterPrompt] = [
        .init(icon: "sun.max", text: "What can we do this weekend?"),
        .init(icon: "magnifyingglass", text: "What camps did we find for my kids?"),
        .init(icon: "exclamationmark.triangle", text: "Where are my coverage gaps this summer?"),
        .init(icon: "checklist", text: "What's still pending or needs confirming?"),
        .init(icon: "arrow.left.arrow.right", text: "Help me decide between two camps"),
    ]

    private func sendSuggestion(_ text: String) {
        guard !viewModel.isSending, !viewModel.isUserIDMissing else { return }
        messageText = ""
        viewModel.send(text)
    }

    // MARK: - Helpers

    private var canSend: Bool {
        !messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !viewModel.isSending
            && !viewModel.isUserIDMissing
    }

    private func sendMessage() {
        let text = messageText
        viewModel.send(text)
        if !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            messageText = ""
        }
    }

    private func starterButton(_ text: String) -> some View {
        HStack {
            Text(text)
                .font(.hearthBodyMD)
                .foregroundColor(.inkPrimary)
                .multilineTextAlignment(.leading)
            Spacer()
        }
        .padding(.horizontal, .hearth500)
        .padding(.vertical, .hearth400)
        .background(
            RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                .fill(Color.bgElevated)
                .overlay(
                    RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                        .stroke(Color.borderHairline, lineWidth: 1)
                )
        )
    }
}
