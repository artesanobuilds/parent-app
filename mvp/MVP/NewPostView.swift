import SwiftUI

struct NewPostView: View {
    @EnvironmentObject private var contentVM: ContentViewModel
    @Environment(\.dismiss) private var dismiss

    let baseURL: URL

    @State private var selectedCategory: String = ""
    @State private var title: String = ""
    @State private var postBody: String = ""
    @State private var isPosting = false

    private var canPost: Bool {
        !title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        && !postBody.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        && !selectedCategory.isEmpty
        && !isPosting
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: .hearth600) {
                    // Category picker
                    VStack(alignment: .leading, spacing: .hearth300) {
                        Text("Category")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: .hearth300) {
                                ForEach(contentVM.categories) { cat in
                                    Button {
                                        selectedCategory = cat.id
                                    } label: {
                                        HStack(spacing: .hearth300) {
                                            Text(cat.emoji).font(.system(size: 14))
                                            Text(cat.name)
                                                .font(.hearthBodySM)
                                                .lineLimit(1)
                                        }
                                        .padding(.horizontal, .hearth400)
                                        .padding(.vertical, .hearth300)
                                        .background(selectedCategory == cat.id ? Color.accentDefault : Color.accentTint)
                                        .foregroundColor(selectedCategory == cat.id ? .inkOnPhotoLight : .inkPrimary)
                                        .clipShape(Capsule())
                                        .overlay(
                                            Capsule()
                                                .stroke(selectedCategory == cat.id ? Color.clear : Color.borderHairline, lineWidth: 1)
                                        )
                                        .frame(minHeight: 44)
                                    }
                                }
                            }
                        }
                    }

                    // Title
                    VStack(alignment: .leading, spacing: .hearth300) {
                        Text("Title")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        TextField("", text: $title, prompt: Text("What's on your mind?").foregroundColor(.inkPlaceholder))
                            .font(.hearthBodyMD)
                            .foregroundColor(.inkPrimary)
                            .padding(.horizontal, .hearth500)
                            .padding(.vertical, .hearth500)
                            .background(Color.bgElevated)
                            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                                    .stroke(Color.borderStrong, lineWidth: 1)
                            )
                    }

                    // Body
                    VStack(alignment: .leading, spacing: .hearth300) {
                        Text("Your post")
                            .font(.hearthLabel)
                            .foregroundColor(.inkMuted)
                            .tracking(0.66)
                            .textCase(.uppercase)

                        TextEditor(text: $postBody)
                            .font(.hearthBodyMD)
                            .foregroundColor(.inkPrimary)
                            .scrollContentBackground(.hidden)
                            .frame(minHeight: 150)
                            .padding(.horizontal, .hearth400)
                            .padding(.vertical, .hearth400)
                            .background(Color.bgElevated)
                            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                            .overlay(
                                RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                                    .stroke(Color.borderStrong, lineWidth: 1)
                            )
                    }
                }
                .padding(.hearth700)
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .trackScreen("new_post")
            .navigationTitle("New Post")
            .navigationBarTitleDisplayMode(.inline)
            .toolbarBackground(Color.bgCanvas, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(.inkPrimary)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button {
                        postIt()
                    } label: {
                        if isPosting {
                            ProgressView()
                                .scaleEffect(0.8)
                        } else {
                            Text("Post")
                                .font(.hearthTitleMD)
                        }
                    }
                    .foregroundColor(canPost ? .accentDefault : .inkPlaceholder)
                    .disabled(!canPost)
                }
            }
        }
    }

    private func postIt() {
        isPosting = true
        let authorName = contentVM.userId
        Task {
            await contentVM.createPost(
                baseURL: baseURL,
                category: selectedCategory,
                title: title.trimmingCharacters(in: .whitespacesAndNewlines),
                body: postBody.trimmingCharacters(in: .whitespacesAndNewlines),
                authorName: authorName
            )
            dismiss()
        }
    }
}
