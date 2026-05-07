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
                Divider()
                inputArea
            }
            .navigationTitle(agentMode.navTitle)
            .toolbarBackground(Color.brandBackground, for: .navigationBar)
            .toolbarColorScheme(.light, for: .navigationBar)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button {
                        withAnimation { viewModel.resetConversation() }
                    } label: {
                        ToolbarBadge(icon: "arrow.counterclockwise", title: "Reset")
                    }
                    .disabled(viewModel.isSending)
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack(spacing: 12) {
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
            .tint(.brandCoral)
            .background(Color.brandBackground.ignoresSafeArea())
        }
    }

    private var modeHeader: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(agentMode.navTitle)
                    .font(.headline)
                    .foregroundColor(.brandNavy)
                Spacer()
            }
            Text(agentMode.description)
                .font(.subheadline)
                .foregroundColor(.brandNavy.opacity(0.7))
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .padding(.top, 6)
        .background(Color.brandBackground)
    }

    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 12) {
                    ForEach(viewModel.messages) { message in
                        ChatBubble(message: message)
                            .id(message.id)
                            .padding(.horizontal, 12)
                    }
                }
                .padding(.vertical)
            }
            .background(Color.brandBackground)
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
        VStack(spacing: 8) {
            if let baseURL = configuration.baseURL {
                Text("Connected to \(baseURL.absoluteString)")
                    .font(.caption)
                    .foregroundColor(.brandNavy.opacity(0.7))
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal)
            } else {
                Text("Enter a valid server URL in Settings.")
                    .font(.caption)
                    .foregroundColor(.red)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal)
            }

            HStack(alignment: .bottom, spacing: 8) {
                TextField("Type a message", text: $messageText, axis: .vertical)
                    .padding(12)
                    .background(
                        RoundedRectangle(cornerRadius: 14, style: .continuous)
                            .fill(Color.brandSurface)
                            .overlay(
                                RoundedRectangle(cornerRadius: 14, style: .continuous)
                                    .stroke(Color.brandStroke, lineWidth: 1)
                            )
                    )
                    .lineLimit(1...4)
                    .disabled(viewModel.isSending || configuration.baseURL == nil || viewModel.isUserIDMissing)
                    .textInputAutocapitalization(.sentences)
                    .onSubmit(sendMessage)
                    .foregroundColor(.brandNavy)

                Button {
                    sendMessage()
                } label: {
                    Image(systemName: "paperplane.fill")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(.white)
                        .frame(width: 46, height: 46)
                        .background(
                            Circle()
                                .fill(Color.brandCoral)
                                .shadow(color: Color.black.opacity(0.12), radius: 8, y: 3)
                        )
                }
                .disabled(messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.isSending || configuration.baseURL == nil || viewModel.isUserIDMissing)
            }
            .padding([.horizontal, .bottom])
        }
        .background(Color.brandBackground)
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
            withAnimation {
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
            if message.role == .assistant { bubble(alignment: .leading, color: Color.brandSurface, textColor: .brandNavy) }
            else { Spacer(minLength: 24) }

            if message.role == .user { bubble(alignment: .trailing, color: Color.brandCoral, textColor: .white) }
            if message.role == .user { avatar }
        }
        .frame(maxWidth: .infinity, alignment: message.role == .assistant ? .leading : .trailing)
    }

    private func bubble(alignment: HorizontalAlignment, color: Color, textColor: Color) -> some View {
        VStack(alignment: alignment, spacing: 6) {
            renderedContent(alignment: alignment)
            if message.isStreaming {
                ProgressView()
                    .scaleEffect(0.7, anchor: .center)
            }
        }
        .padding(12)
        .background(color)
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .shadow(color: Color.black.opacity(alignment == .leading ? 0.03 : 0.07), radius: 8, y: 4)
        .frame(maxWidth: UIScreen.main.bounds.width * 0.9, alignment: alignment == .leading ? .leading : .trailing)
        .foregroundColor(textColor)
    }

    private var avatar: some View {
        Circle()
            .fill(message.role == .assistant ? Color.brandCoral.opacity(0.9) : Color.brandNavy.opacity(0.6))
            .frame(width: 32, height: 32)
            .overlay(
                Image(systemName: message.role == .assistant ? "sparkles" : "person.fill")
                    .foregroundColor(.white)
                    .font(.system(size: 14, weight: .bold))
            )
    }

    private func renderedContent(alignment: HorizontalAlignment) -> some View {
        Markdown(message.content.isEmpty ? "…" : message.content)
            .markdownTextStyle {
                FontSize(15)
                ForegroundColor(message.role == .assistant ? Color.brandNavy : .white)
            }
            .frame(maxWidth: .infinity, alignment: alignment == .leading ? .leading : .trailing)
    }

}

private struct ToolbarPill: View {
    let icon: String
    let title: String

    var body: some View {
        VStack(spacing: 4) {
            Image(systemName: icon)
                .font(.system(size: 15, weight: .semibold))
            Text(title)
                .font(.caption2.weight(.semibold))
        }
        .foregroundColor(.brandCoral)
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(
            Capsule()
                .fill(Color.brandSurface)
                .overlay(
                    Capsule()
                        .stroke(Color.brandStroke, lineWidth: 1)
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
        VStack(spacing: 4) {
            ZStack {
                Circle()
                    .stroke(Color.brandCoral.opacity(0.25), lineWidth: 1)
                    .frame(width: 44, height: 44)
                Image(systemName: icon)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.brandCoral)
            }
            Text(title)
                .font(.caption2.weight(.semibold))
                .foregroundColor(.brandCoral)
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
        VStack(spacing: 24) {
            Spacer()
            MVPLogoView(size: 160)
                .accessibilityHidden(true)

            VStack(spacing: 12) {
                Text("Choose how you want to start")
                    .font(.title2.weight(.semibold))
                    .foregroundColor(.brandNavy)
                Text("Onboarding learns about your family first. Coaching jumps right into live help.")
                    .font(.body)
                    .foregroundColor(.brandNavy.opacity(0.8))
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }

            VStack(spacing: 12) {
                Button {
                    onSelect(.onboarding)
                } label: {
                    Text("Onboarding Agent")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.brandNavy)
                        .foregroundColor(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                }

                Button {
                    onSelect(.coaching)
                } label: {
                    Text("Coaching Agent")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.brandSurface)
                        .foregroundColor(.brandNavy)
                        .overlay(
                            RoundedRectangle(cornerRadius: 14, style: .continuous)
                                .stroke(Color.brandStroke, lineWidth: 1)
                        )
                }
            }
            .padding(.horizontal)

            Spacer()
        }
        .padding()
        .background(Color.brandBackground.ignoresSafeArea())
    }
}

