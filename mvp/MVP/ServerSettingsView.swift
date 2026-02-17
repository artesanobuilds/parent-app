import SwiftUI

struct ServerSettingsView: View {
    @ObservedObject var configuration: ServerConfiguration
    @State private var draftBaseURL: String = ""
    @State private var draftThreadID: String = ""

    var body: some View {
        Form {
            Section("Backend") {
                TextField("Server URL", text: $draftBaseURL, prompt: Text("e.g. http://localhost:8000"))
                    .keyboardType(.URL)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                if !isValidURL(draftBaseURL) {
                    Text("Enter a valid URL including scheme (http/https).")
                        .font(.caption)
                        .foregroundColor(.red)
                }
            }

            Section("Conversation") {
                TextField("Thread ID", text: $draftThreadID)
                Button("Reset Thread ID") {
                    configuration.resetThread()
                    draftThreadID = configuration.threadID
                }
            }

            Section {
                Button("Save Changes") {
                    save()
                }
                .disabled(!isValidURL(draftBaseURL))
            }
        }
        .onAppear {
            draftBaseURL = configuration.baseURLString
            draftThreadID = configuration.threadID
        }
    }

    private func save() {
        configuration.baseURLString = draftBaseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        configuration.threadID = draftThreadID.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func isValidURL(_ value: String) -> Bool {
        guard let url = URL(string: value) else { return false }
        return ["http", "https"].contains(url.scheme?.lowercased() ?? "")
    }
}

