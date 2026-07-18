import SwiftUI

/// Sheet that lets a test user send a diagnostic bundle to the developer.
/// Reachable from the voice failure screen and from Settings. The bundle is
/// device/app/server context + the recent client log buffer — no chat content.
struct ReportProblemView: View {
    /// Where to POST the report.
    let baseURL: URL
    /// Optional machine context (e.g. the voice failure reason) folded into the
    /// logs so it survives even if the user types nothing.
    var failureContext: String? = nil

    @Environment(\.dismiss) private var dismiss
    @State private var note: String = ""
    @State private var status: Status = .idle
    @State private var showDetails = false

    private enum Status: Equatable { case idle, sending, sent, failed(String) }

    var body: some View {
        NavigationStack {
            Form {
                Section("What went wrong?") {
                    TextEditor(text: $note)
                        .frame(minHeight: 100)
                        .font(.hearthBodyMD)
                }

                Section {
                    DisclosureGroup("Data we'll send", isExpanded: $showDetails) {
                        Text(DiagnosticReport.make(note: note, failureContext: failureContext).previewText())
                            .font(.hearthCaptionMono)
                            .foregroundColor(.inkMuted)
                            .textSelection(.enabled)
                    }
                } footer: {
                    Text("Includes app version, device, server URL, and recent diagnostic logs — no chat content.")
                        .font(.hearthBodySM)
                        .foregroundColor(.inkMuted)
                }

                Section {
                    Button(action: send) {
                        HStack {
                            if status == .sending { ProgressView().padding(.trailing, 6) }
                            Text(buttonLabel)
                        }
                    }
                    .disabled(status == .sending || status == .sent)

                    switch status {
                    case .failed(let why):
                        Text(why).font(.hearthBodySM).foregroundColor(.statusError)
                    case .sent:
                        Text("Sent — thank you!").font(.hearthBodySM).foregroundColor(.inkMuted)
                    default:
                        EmptyView()
                    }
                }
            }
            .scrollContentBackground(.hidden)
            .background(Color.bgCanvas.ignoresSafeArea())
            .trackScreen("report_problem")
            .navigationTitle("Report a problem")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(status == .sent ? "Done" : "Close") { dismiss() }
                }
            }
        }
    }

    private var buttonLabel: String {
        switch status {
        case .sent:    return "Sent"
        case .sending: return "Sending…"
        default:       return "Send report"
        }
    }

    private func send() {
        status = .sending
        let report = DiagnosticReport.make(note: note, failureContext: failureContext)
        let url = baseURL
        Task {
            do {
                try await DebugReportService(baseURL: url).send(report)
                status = .sent
            } catch {
                dlog("[debug-report] send failed: \(error)")
                status = .failed("Couldn't send. Check your connection and try again.")
            }
        }
    }
}
