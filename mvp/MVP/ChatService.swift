import Foundation

enum ChatServiceError: LocalizedError {
    case invalidResponse
    case unacceptableStatus(Int)
    case remoteError(String)

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "The server response was not valid."
        case .unacceptableStatus(let code):
            return "The server responded with status code \(code)."
        case .remoteError(let message):
            return message
        }
    }
}

/// Responsible for talking to the FastAPI backend and streaming responses.
struct ChatService {
    private let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    func streamResponse(
        message: String,
        threadID: String,
        userID: String,
        baseURL: URL,
        chatPath: String = "chat"
    ) -> AsyncThrowingStream<String, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    let request = try buildChatRequest(
                        message: message,
                        threadID: threadID,
                        userID: userID,
                        baseURL: baseURL,
                        chatPath: chatPath
                    )
                    let (bytes, response) = try await session.bytes(for: request)
                    guard let httpResponse = response as? HTTPURLResponse else {
                        throw ChatServiceError.invalidResponse
                    }
                    guard (200..<300).contains(httpResponse.statusCode) else {
                        throw ChatServiceError.unacceptableStatus(httpResponse.statusCode)
                    }

                    for try await line in bytes.lines {
                        let trimmedLine = line.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard trimmedLine.hasPrefix("data:") else { continue }

                        var payload = trimmedLine.dropFirst(5) // remove "data:"
                        payload = payload.drop(while: { $0 == " " }) // drop a single leading space if present

                        if payload == "[DONE]" { break }
                        guard !payload.isEmpty else { continue }

                        do {
                            if let token = try decodeToken(from: payload) {
                                continuation.yield(token)
                            }
                        } catch {
                            continuation.finish(throwing: error)
                            return
                        }
                    }
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }

    func sendFeedback(
        messageID: String,
        threadID: String,
        userID: String,
        feedback: String,
        baseURL: URL
    ) async throws {
        let url = baseURL.appendingPathComponent("feedback")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload: [String: String] = [
            "message_id": messageID,
            "thread_id": threadID,
            "user_id": userID,
            "feedback": feedback
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        let (_, response) = try await session.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200..<300).contains(httpResponse.statusCode) else {
            throw ChatServiceError.invalidResponse
        }
    }

    // MARK: - Helpers

    private func buildChatRequest(
        message: String,
        threadID: String,
        userID: String,
        baseURL: URL,
        chatPath: String
    ) throws -> URLRequest {
        let chatURL = baseURL.appendingPathComponent(chatPath)
        var request = URLRequest(url: chatURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")

        let payload = ChatRequest(message: message, threadID: threadID, userID: userID)
        request.httpBody = try JSONEncoder().encode(payload)
        request.timeoutInterval = 90
        request.cachePolicy = .reloadIgnoringLocalCacheData
        return request
    }

    private func decodeToken(from payload: Substring) throws -> String? {
        // Backend emits JSON SSE payloads: {"type":"token","content":"..."}
        // Be permissive and fall back to raw text if JSON decoding fails.
        let trimmed = payload.trimmingCharacters(in: .whitespacesAndNewlines)
        let data = Data(trimmed.utf8)

        if let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            let type = object["type"] as? String
            let content = object["content"] as? String

            if type == "token" { return content }
            if type == "error" { throw ChatServiceError.remoteError(content ?? "The server reported an error.") }
            return nil
        }

        // Fallback: treat it as plain text token.
        return String(trimmed)
    }
}

private struct ChatRequest: Encodable {
    let message: String
    let threadID: String
    let userID: String

    enum CodingKeys: String, CodingKey {
        case message
        case threadID = "thread_id"
        case userID = "user_id"
    }
}

private struct SSEPayload: Decodable {
    let type: String
    let content: String?
}

