import Foundation

enum MessageRole: String {
    case user
    case assistant
}

struct ChatMessage: Identifiable, Hashable {
    let id: UUID
    let role: MessageRole
    var content: String
    let createdAt: Date
    var isStreaming: Bool

    init(id: UUID = UUID(), role: MessageRole, content: String, createdAt: Date = .init(), isStreaming: Bool = false) {
        self.id = id
        self.role = role
        self.content = content
        self.createdAt = createdAt
        self.isStreaming = isStreaming
    }
}

