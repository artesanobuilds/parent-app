import SwiftUI
import PhotosUI
import UIKit

/// Capture a camp email / forwarded text OR a flyer/form/screenshot photo and
/// run it through the backend extractor (`POST /ingest/{text,image}`). The
/// result — a pending activity plus spawned to-dos — is shown back inline, and
/// the Plan tab is refreshed by the view model on success.
///
/// Photo input uses `PhotosPicker` (out-of-process — no library permission /
/// usage string needed). The app's camera-usage string declares the camera is
/// never used, so we deliberately don't offer in-app capture; parents pick a
/// photo or screenshot they've already taken.
struct IngestView: View {
    @ObservedObject var viewModel: PlanViewModel
    @Environment(\.dismiss) private var dismiss

    enum Mode: String, CaseIterable, Identifiable {
        case text = "Paste"
        case photo = "Photo"
        var id: String { rawValue }
    }

    @State private var mode: Mode = .text
    @State private var pastedText: String = ""
    @State private var pickerItem: PhotosPickerItem?
    @State private var pickedImage: UIImage?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: .hearth600) {
                    intro
                    modePicker

                    if let result = viewModel.ingestResult {
                        resultCard(result)
                    } else {
                        switch mode {
                        case .text:  textInput
                        case .photo: photoInput
                        }
                    }

                    if let error = viewModel.ingestError {
                        Text(error)
                            .font(.hearthBodySM)
                            .foregroundColor(.statusError)
                    }
                }
                .padding(.horizontal, .hearth700)
                .padding(.top, .hearth600)
                .padding(.bottom, .hearth900)
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .trackScreen("ingest")
            .navigationTitle("Add to plan")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button(viewModel.ingestResult == nil ? "Cancel" : "Done") {
                        viewModel.resetIngest()
                        dismiss()
                    }
                    .foregroundColor(.inkSecondary)
                }
            }
            .onChange(of: pickerItem) { _, newItem in
                guard let newItem = newItem else { return }
                Task { await handlePickedItem(newItem) }
            }
            .interactiveDismissDisabled(viewModel.isIngesting)
        }
    }

    // MARK: - Header

    private var intro: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text("Got a camp email or a flyer?")
                .font(.hearthBodyLG.weight(.semibold))
                .foregroundColor(.inkPrimary)
            Text("Paste the message or pick a photo. We'll pull out the dates, cost, and next steps, and add it to your plan as pending so you can confirm it.")
                .font(.hearthBodyMD)
                .foregroundColor(.inkSecondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var modePicker: some View {
        Picker("Input", selection: $mode) {
            ForEach(Mode.allCases) { m in Text(m.rawValue).tag(m) }
        }
        .pickerStyle(.segmented)
        .disabled(viewModel.isIngesting)
    }

    // MARK: - Text input

    private var textInput: some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            ZStack(alignment: .topLeading) {
                if pastedText.isEmpty {
                    Text("Paste the camp email or forwarded text here…")
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkMuted)
                        .padding(.horizontal, .hearth500 + 4)
                        .padding(.vertical, .hearth400 + 8)
                }
                TextEditor(text: $pastedText)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkPrimary)
                    .scrollContentBackground(.hidden)
                    .frame(minHeight: 180)
                    .padding(.horizontal, .hearth400)
                    .padding(.vertical, .hearth300)
            }
            .background(inputBackground)

            primaryButton(
                title: "Extract",
                icon: "wand.and.stars",
                disabled: pastedText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            ) {
                Task { await viewModel.ingestText(pastedText) }
            }
        }
    }

    // MARK: - Photo input

    private var photoInput: some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            if let image = pickedImage {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .frame(maxHeight: 280)
                    .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                            .stroke(Color.borderHairline, lineWidth: 1)
                    )
            }

            PhotosPicker(selection: $pickerItem, matching: .images, photoLibrary: .shared()) {
                Label(
                    pickedImage == nil ? "Choose a photo" : "Choose a different photo",
                    systemImage: "photo.on.rectangle.angled"
                )
                .font(.hearthBodyMD.weight(.semibold))
                .foregroundColor(.accentDefault)
                .padding(.horizontal, .hearth500)
                .padding(.vertical, .hearth400)
                .frame(maxWidth: .infinity)
                .background(inputBackground)
            }
            .disabled(viewModel.isIngesting)

            Text("Photos of paper flyers, signed forms, or schedule screenshots all work.")
                .font(.hearthBodySM)
                .foregroundColor(.inkMuted)

            if viewModel.isIngesting {
                HStack(spacing: .hearth400) {
                    ProgressView()
                    Text("Reading the photo…")
                        .font(.hearthBodySM)
                        .foregroundColor(.inkSecondary)
                }
            }
        }
    }

    // MARK: - Result

    @ViewBuilder
    private func resultCard(_ result: IngestResponse) -> some View {
        let items = result.allItems
        VStack(alignment: .leading, spacing: .hearth500) {
            HStack(spacing: .hearth400) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 22))
                    .foregroundColor(.accentDefault)
                Text(items.count > 1
                     ? "\(items.count) things found"
                     : (items.first?.created.madeActivity == true ? "Added to your plan" : "Captured"))
                    .font(.hearthBodyLG.weight(.semibold))
                    .foregroundColor(.inkPrimary)
            }

            // One card per extracted item — a PTA newsletter yields several.
            ForEach(Array(items.enumerated()), id: \.offset) { _, item in
                itemCard(item)
            }

            if let parked = result.parked, parked > 0 {
                Text("\(parked) more item\(parked == 1 ? "" : "s") found — kept aside for review so this doesn't flood your plan.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
            }

            if items.contains(where: { $0.created.madeActivity }) {
                Text("Tracked as pending — confirm from the Plan tab.")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkSecondary)
            }

            primaryButton(title: "Add another", icon: "plus", disabled: false) {
                resetForNext()
            }
        }
    }

    @ViewBuilder
    private func itemCard(_ item: IngestItem) -> some View {
        let ext = item.extracted
        VStack(alignment: .leading, spacing: .hearth400) {
            resultRow("Activity", ext.displayName)
            resultRow("For", ext.kidFit)
            resultRow("When", ext.dates?.joined(separator: ", "))
            resultRow("Hours", ext.hours)
            resultRow("Where", ext.location)
            resultRow("Cost", ext.amountDue.map { "$\(Int($0))" })
            // Provenance rule: an extracted deadline is never shown naked —
            // the verbatim source sentence renders beside it.
            if let snippet = ext.sourceSnippet, !snippet.isEmpty {
                Text("From: \u{201C}\(snippet)\u{201D}")
                    .font(.hearthBodySM)
                    .foregroundColor(.inkMuted)
                    .italic()
            }
            if let actions = ext.actionItems, !actions.isEmpty {
                VStack(alignment: .leading, spacing: .hearth300) {
                    Text("\(item.created.todoCount > 0 ? item.created.todoCount : actions.count) FOLLOW-UP\(actions.count == 1 ? "" : "S") ADDED")
                        .font(.hearthLabel)
                        .tracking(0.66)
                        .foregroundColor(.inkMuted)
                    ForEach(Array(actions.enumerated()), id: \.offset) { _, action in
                        HStack(alignment: .top, spacing: .hearth300) {
                            Image(systemName: "circle")
                                .font(.system(size: 14))
                                .foregroundColor(.inkMuted)
                                .padding(.top, 2)
                            Text(action)
                                .font(.hearthBodyMD)
                                .foregroundColor(.inkPrimary)
                        }
                    }
                }
            }
        }
        .padding(.hearth500)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    @ViewBuilder
    private func resultRow(_ label: String, _ value: String?) -> some View {
        if let value = value, !value.isEmpty {
            HStack(alignment: .top, spacing: .hearth500) {
                Text(label.uppercased())
                    .font(.hearthLabel)
                    .tracking(0.66)
                    .foregroundColor(.inkMuted)
                    .frame(width: 64, alignment: .leading)
                Text(value)
                    .font(.hearthBodyMD)
                    .foregroundColor(.inkPrimary)
                Spacer(minLength: 0)
            }
        }
    }

    // MARK: - Actions

    private func handlePickedItem(_ item: PhotosPickerItem) async {
        guard let data = try? await item.loadTransferable(type: Data.self),
              let uiImage = UIImage(data: data) else {
            viewModel.ingestError = "Could not read that photo. Try another."
            return
        }
        let normalized = uiImage.normalizedForUpload()
        await MainActor.run { pickedImage = normalized }
        if let jpeg = normalized.jpegData(compressionQuality: 0.8) {
            await viewModel.ingestImage(jpeg)
        } else {
            viewModel.ingestError = "Could not process that photo. Try another."
        }
    }

    private func resetForNext() {
        viewModel.resetIngest()
        pastedText = ""
        pickerItem = nil
        pickedImage = nil
    }

    // MARK: - Shared chrome

    private func primaryButton(
        title: String, icon: String, disabled: Bool, action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            HStack(spacing: .hearth300) {
                if viewModel.isIngesting {
                    ProgressView().tint(.inkOnPhotoLight)
                } else {
                    Image(systemName: icon)
                }
                Text(viewModel.isIngesting ? "Reading…" : title)
            }
            .font(.hearthBodyMD.weight(.semibold))
            .foregroundColor(.inkOnPhotoLight)
            .padding(.horizontal, .hearth500)
            .padding(.vertical, .hearth400)
            .frame(maxWidth: .infinity)
            .background((disabled || viewModel.isIngesting) ? Color.inkMuted : Color.accentDefault)
            .clipShape(Capsule())
        }
        .disabled(disabled || viewModel.isIngesting)
    }

    private var inputBackground: some View {
        RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
            .fill(Color.bgCanvas)
            .overlay(
                RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                    .stroke(Color.borderStrong, lineWidth: 1)
            )
    }

    private var cardBackground: some View {
        RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
            .fill(Color.bgElevated)
            .overlay(
                RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous)
                    .stroke(Color.borderHairline, lineWidth: 1)
            )
    }
}

/// Resign first responder app-wide — dismisses any active keyboard.
func hideKeyboard() {
    UIApplication.shared.sendAction(
        #selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil
    )
}

private extension UIImage {
    /// Downscale to a max dimension and bake in orientation so the upload stays
    /// well under the backend's 8 MB cap and vision cost is bounded. Camera
    /// photos are often 4000px+; 2000px is plenty for OCR-style extraction.
    func normalizedForUpload(maxDimension: CGFloat = 2000) -> UIImage {
        let longest = max(size.width, size.height)
        let scale = longest > maxDimension ? maxDimension / longest : 1
        let target = CGSize(width: size.width * scale, height: size.height * scale)
        let format = UIGraphicsImageRendererFormat.default()
        format.scale = 1
        return UIGraphicsImageRenderer(size: target, format: format).image { _ in
            draw(in: CGRect(origin: .zero, size: target))
        }
    }
}
