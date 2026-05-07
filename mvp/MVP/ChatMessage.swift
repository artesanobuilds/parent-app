import Foundation

enum MessageRole: String {
    case user
    case assistant
}

enum MessageFeedback: String {
    case thumbsUp = "thumbs_up"
    case thumbsDown = "thumbs_down"
}

struct ChatMessage: Identifiable, Hashable {
    let id: UUID
    let role: MessageRole
    var content: String
    let createdAt: Date
    var isStreaming: Bool
    var feedback: MessageFeedback?

    init(id: UUID = UUID(), role: MessageRole, content: String, createdAt: Date = .init(), isStreaming: Bool = false, feedback: MessageFeedback? = nil) {
        self.id = id
        self.role = role
        self.content = content
        self.createdAt = createdAt
        self.isStreaming = isStreaming
        self.feedback = feedback
    }
}

