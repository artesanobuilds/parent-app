import Foundation

/// Streaming chat state for the chief-of-staff surface. Mirrors
/// `ChatViewModel` but targets `/cos/chat` via `PlanService.streamCosChat`.
/// Reuses `ChatMessage` and the same append/finish/handle lifecycle.
@MainActor
final class CosChatViewModel: ObservableObject {
    @Published private(set) var messages: [ChatMessage] = []
    @Published var isSending = false
    @Published var errorMessage: String?

    private let configuration: ServerConfiguration
    private var userID: String = ""
    private var streamTask: Task<Void, Never>?
    /// Dedicated thread id for the COS conversation, distinct from the coach's.
    private let threadID = "cos-" + UUID().uuidString

    init(configuration: ServerConfiguration) {
        self.configuration = configuration
    }

    func setUserID(_ value: String) {
        userID = value
    }

    var isUserIDMissing: Bool {
        userID.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    func send(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        let userID = userID.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !userID.isEmpty else {
            errorMessage = "Please complete onboarding before chatting."
            return
        }
        guard let baseURL = configuration.baseURL else {
            errorMessage = "Please provide a valid server URL."
            return
        }

        errorMessage = nil
        isSending = true
        streamTask?.cancel()

        messages.append(ChatMessage(role: .user, content: trimmed))
        let assistantMessage = ChatMessage(role: .assistant, content: "", isStreaming: true)
        let assistantID = assistantMessage.id
        messages.append(assistantMessage)

        streamTask = Task { [weak self] in
            guard let self else { return }
            do {
                let authHeader = await AuthService.shared.header(for: userID)
                for try await token in PlanService.streamCosChat(
                    baseURL: baseURL,
                    userID: userID,
                    threadID: threadID,
                    message: trimmed,
                    authHeader: authHeader
                ) {
                    self.appendToken(token, to: assistantID)
                }
                self.finishStreamingMessage(assistantID)
            } catch {
                self.handle(error: error, for: assistantID)
            }
        }
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
