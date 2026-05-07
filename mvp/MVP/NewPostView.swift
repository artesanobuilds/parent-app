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
                VStack(alignment: .leading, spacing: 20) {
                    // Category picker
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Category")
                            .font(.caption.weight(.medium))
                            .foregroundColor(.brandGray)

                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 8) {
                                ForEach(contentVM.categories) { cat in
                                    Button {
                                        selectedCategory = cat.id
                                    } label: {
                                        HStack(spacing: 4) {
                                            Text(cat.emoji).font(.system(size: 14))
                                            Text(cat.name)
                                                .font(.caption.weight(.medium))
                                                .lineLimit(1)
                                        }
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 8)
                                        .background(selectedCategory == cat.id ? Color.brandGold : Color.brandSurface)
                                        .foregroundColor(selectedCategory == cat.id ? .brandBlack : .white)
                                        .clipShape(Capsule())
                                        .overlay(
                                            Capsule()
                                                .stroke(selectedCategory == cat.id ? Color.clear : Color.brandStroke, lineWidth: 1)
                                        )
                                    }
                                }
                            }
                        }
                    }

                    // Title
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Title")
                            .font(.caption.weight(.medium))
                            .foregroundColor(.brandGray)

                        TextField("", text: $title, prompt: Text("What's on your mind?").foregroundColor(.brandGray))
                            .font(.body)
                            .foregroundColor(.white)
                            .padding(.horizontal, 16)
                            .padding(.vertical, 14)
                            .background(Color.brandSurface)
                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                            .overlay(
                                RoundedRectangle(cornerRadius: 12, style: .continuous)
                                    .stroke(Color.brandStroke, lineWidth: 1)
                            )
                    }

                    // Body
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Your post")
                            .font(.caption.weight(.medium))
                            .foregroundColor(.brandGray)

                        TextEditor(text: $postBody)
                            .font(.body)
                            .foregroundColor(.white)
                            .scrollContentBackground(.hidden)
                            .frame(minHeight: 150)
                            .padding(.horizontal, 12)
                            .padding(.vertical, 10)
                            .background(Color.brandSurface)
                            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                            .overlay(
                                RoundedRectangle(cornerRadius: 12, style: .continuous)
                                    .stroke(Color.brandStroke, lineWidth: 1)
                            )
                    }
                }
                .padding()
            }
            .background(Color.brandBackground.ignoresSafeArea())
            .navigationTitle("New Post")
            .navigationBarTitleDisplayMode(.inline)
            .toolbarBackground(Color.brandBackground, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                        .foregroundColor(.brandGold)
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
                                .fontWeight(.semibold)
                        }
                    }
                    .foregroundColor(canPost ? .brandGold : .brandGray)
                    .disabled(!canPost)
                }
            }
            .preferredColorScheme(.dark)
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
