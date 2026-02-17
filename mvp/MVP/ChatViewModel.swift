import Foundation

@MainActor
final class ChatViewModel: ObservableObject {
    @Published private(set) var messages: [ChatMessage] = []
    @Published var isSending: Bool = false
    @Published var errorMessage: String?
    @Published private var userID: String = ""

    private let service: ChatService
    private let configuration: ServerConfiguration
    private var streamTask: Task<Void, Never>?
    private var chatPath: String

    init(service: ChatService = ChatService(), configuration: ServerConfiguration, mode: AgentMode = .coaching) {
        self.service = service
        self.configuration = configuration
        self.chatPath = mode.chatPath
    }

    func send(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        let userID = userID.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !userID.isEmpty else {
            errorMessage = "Please enter a username before chatting."
            return
        }
        guard let baseURL = configuration.baseURL else {
            errorMessage = "Please provide a valid server URL."
            return
        }

        errorMessage = nil
        isSending = true
        streamTask?.cancel()

        let userMessage = ChatMessage(role: .user, content: trimmed)
        messages.append(userMessage)

        let assistantMessage = ChatMessage(role: .assistant, content: "", isStreaming: true)
        let assistantID = assistantMessage.id
        messages.append(assistantMessage)

        streamTask = Task { [weak self] in
            guard let self else { return }
            do {
                for try await token in service.streamResponse(
                    message: trimmed,
                    threadID: configuration.threadID,
                    userID: userID,
                    baseURL: baseURL,
                    chatPath: chatPath
                ) {
                    self.appendToken(token, to: assistantID)
                }
                self.finishStreamingMessage(assistantID)
            } catch {
                self.handle(error: error, for: assistantID)
            }
        }
    }

    func setUserID(_ value: String) {
        userID = value
    }

    func setAgentMode(_ mode: AgentMode) {
        chatPath = mode.chatPath
    }

    var isUserIDMissing: Bool {
        userID.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    func resetConversation() {
        streamTask?.cancel()
        messages = []
        configuration.resetThread()
    }

    // MARK: - Private

    private func appendToken(_ token: String, to assistantID: UUID) {
        guard let index = messages.firstIndex(where: { $0.id == assistantID }) else { return }
        messages[index].content += token
    }

    private func finishStreamingMessage(_ assistantID: UUID) {
        if let index = messages.firstIndex(where: { $0.id == assistantID }) {
            messages[index].isStreaming = false
        }
        isSending = false
    }

    private func handle(error: Error, for assistantID: UUID) {
        if let index = messages.firstIndex(where: { $0.id == assistantID }) {
            messages[index].content = messages[index].content.isEmpty ? "No response received." : messages[index].content
            messages[index].isStreaming = false
        }
        isSending = false
        errorMessage = (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
    }
}

