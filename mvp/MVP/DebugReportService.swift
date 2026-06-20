import Foundation

/// Posts a diagnostic bundle to `POST /debug/report`. Attaches the bearer token
/// when one exists but never requires it — the endpoint is unauthenticated by
/// design, because the failures most worth capturing are auth/consent failures.
@MainActor
struct DebugReportService {
    let baseURL: URL

    func send(_ report: DiagnosticReport) async throws {
        var request = URLRequest(url: baseURL.appendingPathComponent("debug/report"))
        request.httpMethod = "POST"
        request.timeoutInterval = 20
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if !report.userID.isEmpty {
            for (k, v) in AuthService.shared.header(for: report.userID) {
                request.setValue(v, forHTTPHeaderField: k)
            }
        }
        request.httpBody = try JSONSerialization.data(withJSONObject: report.jsonBody())

        let (_, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse,
              (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
    }
}
