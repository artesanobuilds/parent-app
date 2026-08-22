import SwiftUI
import PhotosUI
import UIKit

// MARK: - Heisman step 03/04: sample problem + extraction check
//
// "Onboarding - 4a" (paste/type) and "4b" (photo added) are variants of ONE
// step (D3 — the rail stays at 03 across the set; the PDF's 4c image-capture
// frame never landed in Figma, so the pre-photo state follows the 4a/4b
// patterns, per the sprint appendix drift note). All routes run REAL
// extraction (Appendix A2) through `AnonOnboardingService`; failure falls
// back to the static sample cards with a retry.

// MARK: Sample problem

struct HeismanSampleProblemView: View {
    @Binding var draft: OnboardingDraft
    let onBack: () -> Void
    /// Called once extraction resolved (or the parent chose the sample
    /// fallback) — advances to the extraction check.
    let onContinue: () -> Void

    private enum Mode: Hashable { case text, photo }
    private enum ExtractState: Equatable { case idle, working, failed }

    @StateObject private var dictation = DictationController()
    @StateObject private var noteDictation = DictationController()
    @State private var mode: Mode = .text
    @State private var photoNote = ""
    @State private var pickedImage: UIImage?
    @State private var pickedImageName: String?
    @State private var showLibraryPicker = false
    @State private var showCamera = false
    @State private var extractState: ExtractState = .idle

    private var hasInput: Bool {
        !draft.sampleProblemText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            || pickedImage != nil
    }

    var body: some View {
        HeismanScreen(step: .topic, onBack: onBack) {
            Spacer(minLength: .hearth700)

            VStack(alignment: .leading, spacing: 15) {
                // The topic chosen on step 03, echoed as the mono eyebrow.
                heismanMonoEyebrow(HeismanTopic.displayLabel(for: draft.topic))
                heismanTitle("Paste it — or just type it.")
                // Frame copy with its stray full stop healed to a comma
                // (reproduce the intent, not the typo — house precedent).
                heismanSubtitle("Share one message. Paste a screenshot, type a few words, or talk directly to the coach. The coach sorts out who, where, and when.")
            }

            segmentedControl

            if mode == .text {
                textVariant
            } else {
                photoVariant
            }

            if extractState == .failed {
                failureCallout
            }
        } footer: {
            HeismanCTA(
                label: extractState == .failed ? "Try again" : "Give it to the coach for help",
                enabled: hasInput,
                busy: extractState == .working,
                action: runExtraction
            )
        }
        .onDisappear {
            dictation.stop()
            noteDictation.stop()
        }
        .sheet(isPresented: $showLibraryPicker) {
            HeismanPhotoLibraryPicker { image, name in
                pickedImage = image
                pickedImageName = name
            }
        }
        .fullScreenCover(isPresented: $showCamera) {
            HeismanCameraCapture { image in
                pickedImage = image
                pickedImageName = nil
            }
            .ignoresSafeArea()
        }
        .trackScreen("onboarding_sample_problem")
    }

    // Measured segmented control: h36 `accent/tint` capsule, 2pt inset,
    // gap 4; the active segment is a cream-50 pill; labels Inter Bold 13 in
    // the accent with their 16pt exported icons.
    private var segmentedControl: some View {
        HStack(spacing: .hearth200) {
            segment(.text, icon: "OnbIcon-paste", label: "Paste or type")
            segment(.photo, icon: "OnbIcon-photo", label: "Add a photo")
        }
        .padding(2)
        .frame(height: 36)
        .background(Capsule().fill(Color.accentTint))
    }

    private func segment(_ value: Mode, icon: String, label: String) -> some View {
        let active = mode == value
        return Button {
            withAnimation(.hearth(.hearthFast, reduceMotion: false)) { mode = value }
        } label: {
            HStack(spacing: .hearth200) {
                Image(icon)
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 16, height: 16)
                Text(label)
                    .font(.hearthBodySMBold)
            }
            .foregroundColor(.accentDefault)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(active ? Color.bgCoachBanner : .clear)
            .clipShape(Capsule())
        }
        .accessibilityAddTraits(active ? [.isSelected] : [])
    }

    /// 4a: the scrap card — r12, 1px ACCENT stroke (the one stroked-in-accent
    /// input in the set), tall editor, mic bottom-right.
    private var textVariant: some View {
        HeismanTextCard(
            placeholder: "Type here or paste from an email, WhatsApp, or BrightWheel message...",
            text: $draft.sampleProblemText,
            dictation: dictation,
            radius: .hearthRadiusMd,
            stroke: .accentDefault,
            placeholderInk: .inkMuted,
            minEditorHeight: 150
        )
    }

    /// 4b (photo added) + the engineered pre-photo state (no 4c frame — see
    /// the appendix drift note; the affordances follow the 4a/4b patterns).
    @ViewBuilder
    private var photoVariant: some View {
        VStack(alignment: .leading, spacing: .hearth400) {
            if let image = pickedImage {
                heismanMonoEyebrow("Photo added", ink: .inkMuted)
                HStack(alignment: .top, spacing: 9) {
                    photoThumb(image)
                    VStack(alignment: .leading, spacing: 9) {
                        if let name = pickedImageName, !name.isEmpty {
                            Text(name)
                                .font(.hearthBodyMD)
                                .foregroundColor(.inkPrimary)
                                .lineLimit(1)
                        }
                        Text("The coach reads schedules straight from a screenshot — flyers and group texts work too.")
                            .font(.hearthBodySM)
                            .foregroundColor(.inkPrimary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
                // The note-for-the-coach sub-card: r12, 1px `cream-200`
                // stroke (`borderChipOutline` — exact hex match).
                HeismanTextCard(
                    placeholder: "Add a note for the coach",
                    text: $photoNote,
                    dictation: noteDictation,
                    radius: .hearthRadiusMd,
                    stroke: .borderChipOutline,
                    minEditorHeight: 64
                )
            } else {
                photoPickButton(icon: "OnbIcon-photo", label: "Choose a photo") { showLibraryPicker = true }
                photoPickButton(icon: "OnbIcon-camera", label: "Photograph a flyer") { showCamera = true }
            }
        }
        .padding(.hearth600)
        .background(Color.bgCoachBanner)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous)
                .stroke(Color.accentDefault, lineWidth: 1)
        )
    }

    /// The 136×166 thumb, r12, on the sober ground, with the frame's
    /// underlined accent "replace image" link below the photo.
    private func photoThumb(_ image: UIImage) -> some View {
        VStack(spacing: .hearth200) {
            Image(uiImage: image)
                .resizable()
                .scaledToFill()
                .frame(width: 136, height: 142)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
            Button {
                showLibraryPicker = true
            } label: {
                Text("replace image")
                    .font(.hearthBodySM)
                    .underline()
                    .foregroundColor(.accentDefault)
            }
        }
        .frame(width: 136)
        .padding(.bottom, .hearth200)
        .background(Color.bgSober)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
    }

    private func photoPickButton(icon: String, label: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(spacing: .hearth300) {
                Image(icon)
                    .renderingMode(.template)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 18, height: 16)
                Text(label)
                    .font(.hearthBodySMBold)
                Spacer(minLength: 0)
            }
            .foregroundColor(.accentDefault)
            .padding(.vertical, .hearth400)
            .padding(.horizontal, .hearth400)
            .background(Color.bgSober)
            .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusMd, style: .continuous))
        }
    }

    /// Failure state: extraction 429/5xx/offline. Retry is the primary CTA
    /// (relabeled); the sample path is the quiet escape so the funnel never
    /// blocks on the endpoint.
    private var failureCallout: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            Text("The coach couldn't read that just now.")
                .font(.hearthBodySMBold)
                .foregroundColor(.inkPrimary)
            Text("Give it another try — or keep going and see a sample of what the coach does with a real one.")
                .font(.hearthBodySM)
                .foregroundColor(.inkMuted)
                .fixedSize(horizontal: false, vertical: true)
            Button {
                draft.extractedActivities = []
                onContinue()
            } label: {
                Text("Continue with a sample")
                    .font(.hearthBodySM)
                    .underline()
                    .foregroundColor(.accentDefault)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: Extraction

    private func runExtraction() {
        guard hasInput, extractState != .working else { return }
        dictation.stop()
        noteDictation.stop()
        extractState = .working

        // Compose the text payload: the scrap (text route) and/or the photo
        // note ride together; the image goes as JPEG under the backend's cap.
        var textParts: [String] = []
        let scrap = draft.sampleProblemText.trimmingCharacters(in: .whitespacesAndNewlines)
        if !scrap.isEmpty { textParts.append(scrap) }
        if pickedImage != nil {
            let note = photoNote.trimmingCharacters(in: .whitespacesAndNewlines)
            if !note.isEmpty { textParts.append(note) }
        }
        let text = textParts.isEmpty ? nil : textParts.joined(separator: "\n")
        let imageData = pickedImage.flatMap { Self.jpegPayload($0) }

        Task {
            do {
                let activities = try await AnonOnboardingService.extract(
                    text: text,
                    imageData: imageData,
                    mediaType: imageData != nil ? "image/jpeg" : nil
                )
                extractState = .idle
                draft.extractedActivities = activities
                if activities.isEmpty {
                    // A clean "nothing found" is not a failure — the check
                    // screen renders the sample fallback and says so.
                }
                onContinue()
            } catch {
                extractState = .failed
            }
        }
    }

    /// Downscale + JPEG-encode under the backend's 8MB decoded cap.
    static func jpegPayload(_ image: UIImage, maxDimension: CGFloat = 1600) -> Data? {
        let largest = max(image.size.width, image.size.height)
        var candidate = image
        if largest > maxDimension {
            let scale = maxDimension / largest
            let target = CGSize(width: image.size.width * scale, height: image.size.height * scale)
            let renderer = UIGraphicsImageRenderer(size: target)
            candidate = renderer.image { _ in image.draw(in: CGRect(origin: .zero, size: target)) }
        }
        return candidate.jpegData(compressionQuality: 0.7)
    }
}

// MARK: Extraction check ("Onboarding - 5", step 04)

struct HeismanExtractionCheckView: View {
    @Binding var draft: OnboardingDraft
    let onBack: () -> Void
    let onContinue: () -> Void

    /// The rows shown: the REAL extraction when it produced anything, else
    /// the frame's static sample cards (Appendix A2 fallback).
    private var activities: [OnboardingDraft.ExtractedActivity] {
        draft.extractedActivities.isEmpty
            ? OnboardingDraft.ExtractedActivity.sampleFallback
            : draft.extractedActivities
    }

    private var isSample: Bool { draft.extractedActivities.isEmpty }

    /// CTA copy is the frame's for two cards and count-aware around it.
    private var ctaLabel: String {
        switch activities.count {
        case 1: return "Looks right"
        case 2: return "Both look right"
        default: return "These look right"
        }
    }

    /// The field currently being edited via the row alert.
    @State private var editing: (activityID: UUID, field: Field)?
    @State private var editingValue = ""

    private enum Field: String { case who = "WHO", what = "WHAT", when = "WHEN", `where` = "WHERE" }

    var body: some View {
        HeismanScreen(step: .extractionCheck, onBack: onBack) {
            VStack(alignment: .leading, spacing: 15) {
                heismanMonoEyebrow(isSample ? "From your MVP Coach · a sample" : "From your MVP Coach")
                Text("Check my work. Tap anything to fix it.")
                    .font(.custom(HearthFontFamily.sans, size: 17, relativeTo: .body).weight(.bold))
                    .foregroundColor(.inkPrimary)
                    .lineSpacing(.hearthLineBodyLG)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }

            ForEach(activities) { activity in
                activityCard(activity)
            }
        } footer: {
            HeismanCTA(label: ctaLabel, action: onContinue)
        }
        .alert("Fix it", isPresented: Binding(
            get: { editing != nil },
            set: { if !$0 { editing = nil } }
        )) {
            TextField("", text: $editingValue)
            Button("Save") { commitEdit() }
            Button("Cancel", role: .cancel) { editing = nil }
        }
        .trackScreen("onboarding_extraction_check")
    }

    /// One extracted activity: r24 cream-50 card, p20, WHO/WHAT/WHEN/WHERE
    /// rows — mono 12 label in `ink/placeholder`, Inter 17 value, chevron,
    /// hairline rule under every row but the last.
    private func activityCard(_ activity: OnboardingDraft.ExtractedActivity) -> some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            row(activity, .who, activity.who, rule: true)
            row(activity, .what, activity.what, rule: true)
            row(activity, .when, activity.when, rule: true)
            row(activity, .where, activity.where, rule: false)
        }
        .padding(.hearth600)
        .background(Color.bgCoachBanner)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusSheet, style: .continuous))
    }

    private func row(
        _ activity: OnboardingDraft.ExtractedActivity,
        _ field: Field,
        _ value: String,
        rule: Bool
    ) -> some View {
        Button {
            // Sample cards are demonstration copy, not the parent's data —
            // editing them would imply they persist. Real rows edit in place.
            guard !isSample else { return }
            editing = (activity.id, field)
            editingValue = value
        } label: {
            VStack(alignment: .leading, spacing: 0) {
                Text(field.rawValue)
                    .font(.hearthCaptionMono)
                    .foregroundColor(.inkMuted)
                    .frame(height: 22, alignment: .leading)
                HStack {
                    Text(value.isEmpty ? "—" : value)
                        .font(.hearthBodyLG)
                        .foregroundColor(.inkPrimary)
                        .multilineTextAlignment(.leading)
                    Spacer(minLength: .hearth300)
                    if !isSample {
                        Image(systemName: "chevron.right")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.inkPrimary)
                    }
                }
                .padding(.bottom, 10)
                if rule {
                    Rectangle()
                        .fill(Color.borderInputPill)
                        .frame(height: 1)
                }
            }
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(field.rawValue): \(value.isEmpty ? "empty" : value)")
    }

    private func commitEdit() {
        guard let editing,
              let index = draft.extractedActivities.firstIndex(where: { $0.id == editing.activityID })
        else { self.editing = nil; return }
        let value = editingValue.trimmingCharacters(in: .whitespacesAndNewlines)
        switch editing.field {
        case .who:   draft.extractedActivities[index].who = value
        case .what:  draft.extractedActivities[index].what = value
        case .when:  draft.extractedActivities[index].when = value
        case .where: draft.extractedActivities[index].where = value
        }
        self.editing = nil
    }
}

// MARK: - Pickers

/// PHPicker — no permission prompt by design (out-of-process picker).
struct HeismanPhotoLibraryPicker: UIViewControllerRepresentable {
    let onPick: (UIImage, String?) -> Void
    @Environment(\.dismiss) private var dismiss

    func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration()
        config.filter = .images
        config.selectionLimit = 1
        let controller = PHPickerViewController(configuration: config)
        controller.delegate = context.coordinator
        return controller
    }

    func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {}
    func makeCoordinator() -> Coordinator { Coordinator(self) }

    final class Coordinator: NSObject, PHPickerViewControllerDelegate {
        let parent: HeismanPhotoLibraryPicker
        init(_ parent: HeismanPhotoLibraryPicker) { self.parent = parent }

        func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            parent.dismiss()
            guard let result = results.first else { return }
            let name = result.itemProvider.suggestedName
            result.itemProvider.loadObject(ofClass: UIImage.self) { object, _ in
                guard let image = object as? UIImage else { return }
                DispatchQueue.main.async {
                    self.parent.onPick(image, name)
                }
            }
        }
    }
}

/// Camera capture via UIImagePickerController — the first shutter use is
/// what triggers the camera permission prompt (Appendix A2's expectation).
struct HeismanCameraCapture: UIViewControllerRepresentable {
    let onCapture: (UIImage) -> Void
    @Environment(\.dismiss) private var dismiss

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let controller = UIImagePickerController()
        if UIImagePickerController.isSourceTypeAvailable(.camera) {
            controller.sourceType = .camera
        }
        controller.delegate = context.coordinator
        return controller
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}
    func makeCoordinator() -> Coordinator { Coordinator(self) }

    final class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let parent: HeismanCameraCapture
        init(_ parent: HeismanCameraCapture) { self.parent = parent }

        func imagePickerController(
            _ picker: UIImagePickerController,
            didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]
        ) {
            parent.dismiss()
            if let image = (info[.editedImage] ?? info[.originalImage]) as? UIImage {
                parent.onCapture(image)
            }
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            parent.dismiss()
        }
    }
}
