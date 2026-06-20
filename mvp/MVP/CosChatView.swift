import SwiftUI
import MarkdownUI

/// Chief-of-staff chat. Modeled on `AgentView`'s message list + input area, but
/// scoped to the planning conversation (`/cos/chat`) — no voice surface and no
/// content cards. Pushed onto the Plan tab's NavigationStack.
struct CosChatView: View {
    @StateObject private var viewModel: CosChatViewModel
    @State private var messageText: String = ""

    init(configuration: ServerConfiguration, userID: String) {
        let vm = CosChatViewModel(configuration: configuration)
        vm.setUserID(userID)
        _viewModel = StateObject(wrappedValue: vm)
    }

    var body: some View {
        VStack(spacing: 0) {
            Divider().background(Color.borderHairline)
            messageList
            inputArea
        }
        // Lift the input bar clear of MainTabView's floating custom tab bar.
        // Pushed NavigationStack destinations don't inherit the tab-bar bottom
        // padding the way the tab's root content does (see PlanView). hearth800
        // clears the bar while keeping the gap below the field ~symmetric with
        // the gap above it (divider line).
        .padding(.bottom, .hearth800)
        .navigationTitle("Chief of Staff")
        .navigationBarTitleDisplayMode(.inline)
        .toolbarBackground(Color.bgCanvas, for: .navigationBar)
        .toolbarBackground(.visible, for: .navigationBar)
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
                Text("Ask your chief of staff")
                    .font(.hearthDisplayMD)
                    .foregroundColor(.inkPrimary)
                Text("Track an activity, sort out coverage gaps, or get help deciding between camps. The chief of staff sees your family's plan.")
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkSecondary)
            }

            VStack(alignment: .leading, spacing: .hearth300) {
                Text("TRY ASKING")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                    .tracking(0.6)
                    .padding(.top, .hearth300)

                ForEach(Self.starterPrompts, id: \.text) { prompt in
                    Button {
                        sendSuggestion(prompt.text)
                    } label: {
                        HStack(spacing: .hearth400) {
                            Image(systemName: prompt.icon)
                                .font(.system(size: 16, weight: .medium))
                                .foregroundColor(.accentDefault)
                                .frame(width: 22)
                            Text(prompt.text)
                                .font(.hearthBodyMD)
                                .foregroundColor(.inkPrimary)
                                .multilineTextAlignment(.leading)
                            Spacer(minLength: 0)
                            Image(systemName: "arrow.up.right")
                                .font(.system(size: 12, weight: .semibold))
                                .foregroundColor(.inkMuted)
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
                    .buttonStyle(.plain)
                    .disabled(viewModel.isSending || viewModel.isUserIDMissing)
                }
            }
        }
        .padding(.horizontal, .hearth700)
        .padding(.top, .hearth500)
    }

    // MARK: - User Message (pill)

    private func userMessageRow(_ message: ChatMessage) -> some View {
        HStack {
            Spacer(minLength: 60)
            Text(message.content)
                .font(.hearthBodyMD)
                .foregroundColor(.inkOnPhotoLight)
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth400)
                .background(Color.accentDefault)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
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

    private var inputArea: some View {
        VStack(spacing: 0) {
            Divider().background(Color.borderHairline)

            HStack(alignment: .bottom, spacing: .hearth400) {
                TextField("Ask about your plan", text: $messageText, axis: .vertical)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkPrimary)
                    .padding(.horizontal, .hearth500)
                    .padding(.vertical, .hearth400)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                            .fill(Color.bgElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                                    .stroke(Color.borderStrong, lineWidth: 1)
                            )
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
}
