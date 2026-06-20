import SwiftUI
import MarkdownUI

struct ChatView: View {
    @StateObject private var configuration: ServerConfiguration
    @StateObject private var viewModel: ChatViewModel
    @State private var messageText: String = ""
    @State private var isShowingSettings: Bool = false
    @State private var isShowingUsernamePrompt: Bool = true
    @State private var username: String = ""
    @State private var isShowingAgentChoice: Bool = false
    @State private var hasSelectedAgent: Bool = false
    @State private var agentMode: AgentMode

    init(initialMode: AgentMode = .coaching) {
        let configuration = ServerConfiguration()
        _configuration = StateObject(wrappedValue: configuration)
        _viewModel = StateObject(wrappedValue: ChatViewModel(configuration: configuration, mode: initialMode))
        _agentMode = State(initialValue: initialMode)
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                modeHeader
                messageList
                Divider().background(Color.borderHairline)
                inputArea
            }
            .navigationTitle(agentMode.navTitle)
            .toolbarBackground(Color.bgCanvas, for: .navigationBar)
            .toolbarColorScheme(.light, for: .navigationBar)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button {
                        withAnimation(.hearthBase) { viewModel.resetConversation() }
                    } label: {
                        ToolbarBadge(icon: "arrow.counterclockwise", title: "Reset")
                    }
                    .disabled(viewModel.isSending)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack(spacing: .hearth400) {
                        Button {
                            isShowingSettings = true
                        } label: {
                            ToolbarBadge(icon: "gearshape", title: "Server")
                        }

                        Button {
                            isShowingAgentChoice = true
                        } label: {
                            ToolbarBadge(icon: "person.3.sequence", title: "Agents")
                        }
                        .disabled(viewModel.isUserIDMissing)
                        .opacity(viewModel.isUserIDMissing ? 0.5 : 1)
                    }
                }
            }
            .sheet(isPresented: $isShowingSettings) {
                NavigationStack {
                    ServerSettingsView(configuration: configuration)
                        .navigationTitle("Server Settings")
                        .toolbar {
                            ToolbarItem(placement: .confirmationAction) {
                                Button("Done") { isShowingSettings = false }
                            }
                        }
                }
            }
            .sheet(isPresented: $isShowingUsernamePrompt) {
                NavigationStack {
                    Form {
                        Section(header: Text("Enter your username")) {
                            TextField("Username", text: $username)
                                .textInputAutocapitalization(.none)
                                .autocorrectionDisabled()
                        }
                    }
                    .navigationTitle("Welcome")
                    .toolbar {
                        ToolbarItem(placement: .confirmationAction) {
                            Button("Continue") {
                                let trimmed = username.trimmingCharacters(in: .whitespacesAndNewlines)
                                viewModel.setUserID(trimmed)
                                username = trimmed
                                isShowingUsernamePrompt = false
                                isShowingAgentChoice = true
                                hasSelectedAgent = false
                            }
                            .disabled(username.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                        }
                    }
                }
            }
            .sheet(isPresented: $isShowingAgentChoice) {
                AgentChoiceView(
                    logoName: "LaunchScreen",
                    onSelect: { mode in
                        agentMode = mode
                        viewModel.setAgentMode(mode)
                        viewModel.resetConversation()
                        hasSelectedAgent = true
                        isShowingAgentChoice = false
                    }
                )
            }
            .onAppear {
                if viewModel.isUserIDMissing {
                    isShowingUsernamePrompt = true
                } else if !hasSelectedAgent {
                    isShowingAgentChoice = true
                }
            }
            .onChange(of: viewModel.isUserIDMissing) { _, isMissing in
                if isMissing {
                    isShowingUsernamePrompt = true
                    hasSelectedAgent = false
                } else if !hasSelectedAgent {
                    isShowingAgentChoice = true
                }
            }
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
            .tint(.accentDefault)
            .background(Color.bgCanvas.ignoresSafeArea())
        }
    }

    private var modeHeader: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            HStack {
                Text(agentMode.navTitle)
                    .font(.hearthTitleLG)
                    .foregroundColor(.inkPrimary)
                Spacer()
            }
            Text(agentMode.description)
                .font(.hearthBodyMD)
                .foregroundColor(.inkMuted)
        }
        .padding(.horizontal, .hearth700)
        .padding(.vertical, .hearth400)
        .background(Color.bgCanvas)
    }

    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: .hearth400) {
                    ForEach(viewModel.messages) { message in
                        ChatBubble(message: message)
                            .id(message.id)
                            .padding(.horizontal, .hearth400)
                    }
                }
                .padding(.vertical, .hearth500)
            }
            .background(Color.bgCanvas)
            .onChange(of: viewModel.messages) { _, newValue in
                guard newValue.last?.isStreaming == true else { return }
                scrollToBottom(proxy: proxy)
            }
            .onAppear {
                scrollToBottom(proxy: proxy, animated: false)
            }
        }
    }

    private var inputArea: some View {
        VStack(spacing: .hearth300) {
            if let baseURL = configuration.baseURL {
                Text("Connected to \(baseURL.absoluteString)")
                    .font(.hearthCaptionMono)
                    .foregroundColor(.inkMuted)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, .hearth700)
            } else {
                Text("Enter a valid server URL in Settings.")
                    .font(.hearthCaptionMono)
                    .foregroundColor(.statusError)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, .hearth700)
            }

            HStack(alignment: .bottom, spacing: .hearth300) {
                TextField("Type a message", text: $messageText, axis: .vertical)
                    .padding(.hearth400)
                    .background(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .fill(Color.bgElevated)
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                                    .stroke(Color.borderStrong, lineWidth: 1)
                            )
                    )
                    .lineLimit(1...4)
                    .disabled(viewModel.isSending || configuration.baseURL == nil || viewModel.isUserIDMissing)
                    .textInputAutocapitalization(.sentences)
                    .onSubmit(sendMessage)
                    .foregroundColor(.inkPrimary)
                    .font(.hearthBodyMD)

                Button {
                    sendMessage()
                } label: {
                    Image(systemName: "paperplane.fill")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(.inkOnPhotoLight)
                        .frame(width: 46, height: 46)
                        .background(
                            Circle()
                                .fill(Color.accentDefault)
                        )
                }
                .disabled(messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.isSending || configuration.baseURL == nil || viewModel.isUserIDMissing)
            }
            .padding([.horizontal, .bottom], .hearth500)
        }
        .background(Color.bgCanvas)
    }

    private func sendMessage() {
        let text = messageText
        viewModel.send(text)
        if !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            messageText = ""
        }
    }

    private func scrollToBottom(proxy: ScrollViewProxy, animated: Bool = true) {
        guard let lastID = viewModel.messages.last?.id else { return }
        if animated {
            withAnimation(.hearthBase) {
                proxy.scrollTo(lastID, anchor: .bottom)
            }
        } else {
            proxy.scrollTo(lastID, anchor: .bottom)
        }
    }
}

// MARK: - Subviews

private struct ChatBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack {
            if message.role == .assistant { avatar }
            if message.role == .assistant {
                bubble(alignment: .leading, color: Color.bgElevated, textColor: .inkPrimary)
            }
            else { Spacer(minLength: 24) }

            if message.role == .user {
                bubble(alignment: .trailing, color: Color.accentDefault, textColor: .inkOnPhotoLight)
            }
            if message.role == .user { avatar }
        }
        .frame(maxWidth: .infinity, alignment: message.role == .assistant ? .leading : .trailing)
    }

    private func bubble(alignment: HorizontalAlignment, color: Color, textColor: Color) -> some View {
        VStack(alignment: alignment, spacing: .hearth300) {
            renderedContent(alignment: alignment)
            if message.isStreaming {
                ProgressView()
                    .scaleEffect(0.7, anchor: .center)
            }
        }
        .padding(.hearth400)
        .background(color)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                .stroke(message.role == .assistant ? Color.borderHairline : Color.clear, lineWidth: 1)
        )
        .frame(maxWidth: UIScreen.main.bounds.width * 0.9, alignment: alignment == .leading ? .leading : .trailing)
        .foregroundColor(textColor)
    }

    private var avatar: some View {
        Circle()
            .fill(message.role == .assistant ? Color.accentDefault : Color.accentTint)
            .frame(width: 32, height: 32)
            .overlay(
                Image(systemName: message.role == .assistant ? "sparkles" : "person.fill")
                    .foregroundColor(message.role == .assistant ? .inkOnPhotoLight : .accentDefault)
                    .font(.system(size: 14, weight: .bold))
            )
    }

    private func renderedContent(alignment: HorizontalAlignment) -> some View {
        Markdown(message.content.isEmpty ? "…" : message.content)
            .markdownTextStyle {
                FontFamily(.custom(HearthFontFamily.sans))
                FontSize(15)
                ForegroundColor(message.role == .assistant ? Color.inkPrimary : Color.inkOnPhotoLight)
            }
            .frame(maxWidth: .infinity, alignment: alignment == .leading ? .leading : .trailing)
    }

}

private struct ToolbarPill: View {
    let icon: String
    let title: String

    var body: some View {
        VStack(spacing: .hearth300) {
            Image(systemName: icon)
                .font(.system(size: 15, weight: .semibold))
            Text(title)
                .font(.hearthLabel)
                .tracking(0.66)
                .textCase(.uppercase)
        }
        .foregroundColor(.accentDefault)
        .padding(.horizontal, .hearth400)
        .padding(.vertical, .hearth300)
        .background(
            Capsule()
                .fill(Color.accentTint)
                .overlay(
                    Capsule()
                        .stroke(Color.borderHairline, lineWidth: 1)
                )
        )
        .accessibilityElement(children: .combine)
        .accessibilityLabel(title)
    }
}

private struct ToolbarBadge: View {
    let icon: String
    let title: String

    var body: some View {
        VStack(spacing: .hearth300) {
            ZStack {
                Circle()
                    .stroke(Color.accentDefault.opacity(0.25), lineWidth: 1)
                    .frame(width: 44, height: 44)
                Image(systemName: icon)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.accentDefault)
            }
            Text(title)
                .font(.hearthLabel)
                .foregroundColor(.accentDefault)
                .tracking(0.66)
                .textCase(.uppercase)
        }
        .padding(.horizontal, 2)
        .accessibilityElement(children: .combine)
        .accessibilityLabel(title)
    }
}

private struct AgentChoiceView: View {
    let logoName: String
    let onSelect: (AgentMode) -> Void

    var body: some View {
        VStack(spacing: .hearth700) {
            Spacer()
            MVPLogoView(size: 160)
                .accessibilityHidden(true)

            VStack(spacing: .hearth400) {
                Text("Choose how you want to start")
                    .font(.hearthDisplayMD)
                    .foregroundColor(.inkPrimary)
                Text("Onboarding learns about your family first. Coaching jumps right into live help.")
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkSecondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, .hearth700)
            }

            VStack(spacing: .hearth400) {
                Button {
                    onSelect(.onboarding)
                } label: {
                    Text("Onboarding Agent")
                        .font(.hearthTitleMD)
                        .frame(maxWidth: .infinity)
                        .padding(.hearth500)
                        .background(Color.accentDefault)
                        .foregroundColor(.inkOnPhotoLight)
                        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                }

                Button {
                    onSelect(.coaching)
                } label: {
                    Text("Coaching Agent")
                        .font(.hearthTitleMD)
                        .frame(maxWidth: .infinity)
                        .padding(.hearth500)
                        .background(Color.bgElevated)
                        .foregroundColor(.inkPrimary)
                        .overlay(
                            RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                                .stroke(Color.borderStrong, lineWidth: 1)
                        )
                }
            }
            .padding(.horizontal, .hearth700)

            Spacer()
        }
        .padding(.hearth700)
        .background(Color.bgCanvas.ignoresSafeArea())
    }
}
