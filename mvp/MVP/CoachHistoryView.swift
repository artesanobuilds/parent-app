import SwiftUI

// MARK: - Wire types
//
// Field names and types are LOCKED against the backend payload by
// `tests/test_coach_threads.py` (it greps this struct). Strict Codable means one
// mismatch decodes nil and the whole history list renders empty with no error —
// that exact drift produced a silently blank section last sprint
// (memory `debugging_ios_codable_backend_contract`).
//
// `updated_at` is a POSIX timestamp Double. It arrives from Python `float`, so
// it must be `Double` and never `Int` — a DuckDB/Python DOUBLE decoded into
// `Int?` is the canonical way this file would empty itself.

struct CoachThreadSummary: Codable, Identifiable, Hashable {
    let conversationId: String
    let title: String
    let summary: String
    let messageCount: Int
    let updatedAt: Double
    let isActive: Bool

    var id: String { conversationId }

    enum CodingKeys: String, CodingKey {
        case conversationId = "conversation_id"
        case title
        case summary
        case messageCount = "message_count"
        case updatedAt = "updated_at"
        case isActive = "is_active"
    }
}

private struct CoachThreadsResponse: Codable { let threads: [CoachThreadSummary] }

private struct CoachThreadDetail: Codable {
    let conversationId: String
    let messages: [CoachStoredMessage]

    enum CodingKeys: String, CodingKey {
        case conversationId = "conversation_id"
        case messages
    }
}

/// One stored turn. The transcript rows are `{role, content}` — the same shape
/// `MemoryRepository` persists, so this decodes the server's own snapshot.
struct CoachStoredMessage: Codable, Hashable {
    let role: String
    let content: String
}

private struct CoachCloseResponse: Codable {
    let conversationId: String

    enum CodingKeys: String, CodingKey { case conversationId = "conversation_id" }
}

// MARK: - Service

/// REST client for `/coach/threads*`. Same shape as the other services: static
/// funcs, Bearer via `AuthService`, and the base URL supplied by the caller from
/// `ServerConfiguration` — never a hardcoded fallback (CLAUDE.md: a localhost
/// fallback works in the simulator and silently fails on a real device).
enum CoachThreadService {

    enum ServiceError: Error {
        case status(Int)
        /// A conversation deleted on another device — callers fall back to the
        /// list rather than showing an error.
        var isNotFound: Bool { if case .status(404) = self { return true }; return false }
    }

    @MainActor
    private static func request(
        _ path: String,
        method: String = "GET",
        userID: String,
        baseURL: URL
    ) async throws -> Data {
        _ = try? await AuthService.shared.ensureToken(for: userID, baseURL: baseURL)
        var components = URLComponents(
            url: baseURL.appendingPathComponent(path),
            resolvingAgainstBaseURL: false
        )
        components?.queryItems = [URLQueryItem(name: "user_id", value: userID)]
        guard let url = components?.url else { throw URLError(.badURL) }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.timeoutInterval = 15
        for (key, value) in AuthService.shared.header(for: userID) {
            request.setValue(value, forHTTPHeaderField: key)
        }
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }
        guard (200..<300).contains(http.statusCode) else {
            throw ServiceError.status(http.statusCode)
        }
        return data
    }

    @MainActor
    static func threads(userID: String, baseURL: URL) async throws -> [CoachThreadSummary] {
        let data = try await request("coach/threads", userID: userID, baseURL: baseURL)
        return try JSONDecoder().decode(CoachThreadsResponse.self, from: data).threads
    }

    /// Open a past conversation. Server-side this ALSO makes it the active one,
    /// so the parent's next message lands in the conversation they just opened.
    @MainActor
    static func open(
        conversationID: String,
        userID: String,
        baseURL: URL
    ) async throws -> [CoachStoredMessage] {
        let encoded =
            conversationID.addingPercentEncoding(withAllowedCharacters: .alphanumerics)
            ?? conversationID
        let data = try await request(
            "coach/threads/\(encoded)", userID: userID, baseURL: baseURL
        )
        return try JSONDecoder().decode(CoachThreadDetail.self, from: data).messages
    }

    /// Close the current conversation (KEEPING it) and start a new one.
    /// Returns the new conversation's id.
    @MainActor
    static func closeCurrent(userID: String, baseURL: URL) async throws -> String {
        let data = try await request(
            "coach/threads/close", method: "POST", userID: userID, baseURL: baseURL
        )
        return try JSONDecoder().decode(CoachCloseResponse.self, from: data).conversationId
    }
}

// MARK: - History list (coach-002)

/// The parent's past coach conversations. `#F5F3EF` r=12 cards with a 1px
/// `#A4A4A4` stroke and 9pt padding, per the measured frame.
struct CoachHistoryView: View {
    let userID: String
    let baseURL: URL
    /// Hands the reopened conversation's transcript back to the chat surface.
    let onOpen: ([CoachStoredMessage]) -> Void

    @Environment(\.dismiss) private var dismiss

    @State private var threads: [CoachThreadSummary] = []
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var openingID: String?

    var body: some View {
        ScrollView {
            LazyVStack(spacing: .hearth400) {
                if isLoading {
                    ProgressView().padding(.top, .hearth900)
                } else if let errorMessage {
                    errorState(errorMessage)
                } else if threads.isEmpty {
                    emptyState
                } else {
                    ForEach(threads) { thread in
                        card(for: thread)
                    }
                }
            }
            .padding(.horizontal, .hearth600)
            .padding(.vertical, .hearth500)
        }
        .background(Color.bgCanvas.ignoresSafeArea())
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .principal) {
                Text("History")
                    .font(.hearthTitleSerif)
                    .foregroundColor(.inkPrimary)
            }
        }
        .task { await load() }
    }

    // MARK: Rows

    /// One conversation card. Extracted as its own builder: inlined in the
    /// ForEach it pushed the surrounding expression past what the Swift
    /// type-checker solves in reasonable time (the failure reads as
    /// "unable to type-check this expression in reasonable time", not a real
    /// error) — the same reason AgentView.contentCardBlock is separate.
    @ViewBuilder
    private func card(for thread: CoachThreadSummary) -> some View {
        Button {
            Task { await open(thread) }
        } label: {
            HStack(alignment: .top, spacing: .hearth400) {
                VStack(alignment: .leading, spacing: 9) {
                    Text(thread.title)
                        .font(.hearthChipLabel)          // Inter w600 14
                        .tracking(-0.14)
                        .foregroundColor(.inkHeader)
                        .multilineTextAlignment(.leading)
                    if !thread.summary.isEmpty {
                        Text(thread.summary)
                            .font(.hearthBodyMD)         // Inter w400 15
                            .foregroundColor(.inkMuted)
                            .multilineTextAlignment(.leading)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
                Spacer(minLength: .hearth400)
                if openingID == thread.conversationId {
                    ProgressView().scaleEffect(0.7)
                } else if thread.isActive {
                    // The conversation the next message would land in.
                    Text("NOW")
                        .font(.hearthLabel)
                        .tracking(0.66)
                        .foregroundColor(.accentOnCanvas)
                }
            }
            .padding(9)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                    .fill(Color.bgCard)
                    .overlay(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .stroke(Color.borderStrong, lineWidth: 1)
                    )
            )
        }
        .buttonStyle(.plain)
        .disabled(openingID != nil)
        .accessibilityLabel("\(thread.title). \(thread.summary)")
        .accessibilityHint("Opens this conversation")
    }

    private var emptyState: some View {
        VStack(spacing: .hearth400) {
            Text("No past conversations yet")
                .font(.hearthTitleMD)
                .foregroundColor(.inkPrimary)
            Text("Conversations show up here once you start a new one.")
                .font(.hearthBodyMD)
                .foregroundColor(.inkMuted)
                .multilineTextAlignment(.center)
        }
        .padding(.top, .hearth900)
        .padding(.horizontal, .hearth500)
    }

    private func errorState(_ message: String) -> some View {
        VStack(spacing: .hearth400) {
            Text(message)
                .font(.hearthBodyMD)
                .foregroundColor(.inkMuted)
                .multilineTextAlignment(.center)
            Button("Try again") { Task { await load() } }
                .font(.hearthButtonLabel)
                .foregroundColor(.accentOnCanvas)
        }
        .padding(.top, .hearth900)
        .padding(.horizontal, .hearth500)
    }

    // MARK: Actions

    private func load() async {
        isLoading = true
        errorMessage = nil
        do {
            threads = try await CoachThreadService.threads(userID: userID, baseURL: baseURL)
        } catch {
            errorMessage = "Couldn't load your conversations."
        }
        isLoading = false
    }

    private func open(_ thread: CoachThreadSummary) async {
        guard openingID == nil else { return }
        openingID = thread.conversationId
        do {
            let messages = try await CoachThreadService.open(
                conversationID: thread.conversationId, userID: userID, baseURL: baseURL
            )
            openingID = nil
            onOpen(messages)
            dismiss()
        } catch let error as CoachThreadService.ServiceError where error.isNotFound {
            // Deleted elsewhere — refresh rather than showing a dead row.
            openingID = nil
            await load()
        } catch {
            openingID = nil
            errorMessage = "Couldn't open that conversation."
        }
    }
}
