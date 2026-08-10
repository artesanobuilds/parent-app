import SwiftUI
import PostHog

// MARK: - Feature flag gate
//
// Plan (`drifting-jingling-valley.md`, Phase 4): ship the paywall UI to a
// cohort without a release, behind a PostHog flag. There is no on-device
// flag-reading helper in this codebase yet — `Analytics.swift` only wraps
// `capture(_:_:)` (an ALLOWLISTED-EVENT sender), not flag reads, and no other
// iOS file calls `PostHogSDK.shared.isFeatureEnabled`. Rather than inventing
// app-level flag plumbing for one screen, this calls the already-integrated
// PostHogSDK directly — that IS the existing PostHog mechanism, just not
// wrapped yet. A follow-up that adds more flagged screens should promote this
// into `Analytics.swift` instead of repeating the pattern per-file.
//
// Fails CLOSED, matching the backend's `app/analytics/flags.py` "default
// fails safe" rule: no consent recorded → `Analytics.startIfConsented()`
// never ran → `PostHogSDK.shared.isFeatureEnabled` returns `false` before the
// SDK even checks the network, per `PostHogSDK.isEnabled()`. Same result if
// the flag doesn't exist in the console yet, or existed but hasn't finished
// its first load. There is no env-var override analog to `FLAG_<KEY>` on the
// client; add one only if a deploy-free client kill switch is actually needed.
enum PaywallFeatureFlag {
    static let key = "paywall_ui_enabled"

    static var isEnabled: Bool {
        PostHogSDK.shared.isFeatureEnabled(key)
    }
}

// MARK: - Plan data
//
// Design (`choose a plan`, 754:4897): BASIC $59/yr and FAMILY $139/yr, same
// bullet list on both cards. `$139` matches the $99–149 price test in
// `project_gtm_validation_playbook`. Only per-year prices are specified by the
// design; the monthly|annual toggle exists per spec but does not (yet) change
// the displayed price, since no monthly figure was given — flagged in the
// hand-off report rather than invented here.
private struct PaywallPlan: Identifiable {
    let id: String
    let name: String
    let priceLabel: String
    let bullets: [String]
}

/// NOTE: "Team feedback" is reproduced verbatim from the Figma layer copy.
/// It reads like B2B SaaS template copy ("give your team feedback") dropped
/// into a parenting-app pricing card, not a feature a solo/family parent
/// account would ever see — flagged to Miguel/Figma as a likely copy error,
/// not fixed unilaterally here.
private let paywallBullets = [
    "Annual membership",
    "7-day free trial",
    "AI coach",
    "Team feedback",
]

private let paywallPlans: [PaywallPlan] = [
    PaywallPlan(id: "basic", name: "BASIC", priceLabel: "$59 per year", bullets: paywallBullets),
    PaywallPlan(id: "family", name: "FAMILY", priceLabel: "$139 per year", bullets: paywallBullets),
]

private enum PaywallBillingCycle: String, CaseIterable, Identifiable {
    case monthly, annual
    var id: String { rawValue }
    var label: String { self == .monthly ? "Monthly" : "Annual" }
}

// MARK: - Screen

/// `choose a plan` (beta-v1, Greg's Figma `754:4897`). UI ONLY — see
/// `PaywallBuyButton` for why the Buy buttons are deliberately wired to
/// nothing. Gate presentation on `PaywallFeatureFlag.isEnabled` at the call
/// site; the view also self-guards (renders nothing) as defense in depth in
/// case something presents it while the flag is off.
///
/// Kept split into small `private var`/`private func` members on purpose —
/// a single long body on a screen this dense is exactly the shape that has
/// previously produced "unable to type-check this expression in reasonable
/// time" (a real build failure, not SourceKit noise).
struct PaywallView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var cycle: PaywallBillingCycle = .annual
    // Smoke-and-mirrors: persisted for display in the consolidated Settings
    // "Your MVP information" card and the account sheet — NOTHING charged,
    // Miguel's explicit call. Existing installs that never saw this screen
    // simply never set these, and both surfaces hide the rows when empty.
    @AppStorage("picked_plan_name") private var pickedPlanName = ""
    @AppStorage("picked_plan_billing") private var pickedPlanBilling = ""

    /// Called by BOTH Buy buttons (see `PaywallBuyButton`) — and ONLY by
    /// them; nothing else in this view triggers it. Defaults to a genuine
    /// no-op for the (not-yet-wired) Settings-menu presentation, where there
    /// is no downstream step to advance to. The onboarding funnel's `.plan`
    /// step (`OnboardingView.planScreen`) supplies `{ goTo(.warmup) }` here —
    /// still no purchase, StoreKit, or Stripe call, exactly Miguel's
    /// "it does nothing, just lets you go to the next step" (2026-08-09).
    var onContinue: () -> Void = {}

    /// The Settings-menu paywall is presented as a dismissible sheet, so it
    /// shows the X. The onboarding funnel's `.plan` step is a full-screen
    /// step with nothing to dismiss TO and no such affordance in the frame —
    /// showing the X there would be a button that visibly does nothing.
    var showsCloseButton: Bool = true

    /// See `PaywallBuyButton.accessibilityHint`. The funnel step passes
    /// "Continues to the next step" — accurate there, unlike the default.
    var buyAccessibilityHint: String = "Not yet available"

    var body: some View {
        if PaywallFeatureFlag.isEnabled {
            screen
        } else {
            // The real gate is the presenter checking the flag before ever
            // showing this view. This branch only covers a presenter that
            // forgot to check — closing immediately beats a broken-looking
            // screen the parent can't back out of.
            Color.clear.onAppear { dismiss() }
        }
    }

    /// Was `fileprivate` — widened to `internal` so `OnboardingView`'s
    /// `.plan` step can call it directly and bypass `PaywallFeatureFlag`
    /// (that flag gates the Settings-menu ENTRY POINT, not this funnel step,
    /// per Miguel's instruction; the funnel step is unconditional).
    var screen: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if showsCloseButton { closeHeader }
                ScrollView {
                    VStack(spacing: .hearth800) {
                        titleBlock
                        cycleToggle
                        plansStack
                        footer
                    }
                    .padding(.horizontal, .hearth700)
                    .padding(.top, .hearth500)
                    .padding(.bottom, .hearth800)
                }
            }
            .background(Color.bgCanvas.ignoresSafeArea())
            .toolbar(.hidden, for: .navigationBar)
        }
        .trackScreen("paywall")
    }

    // MARK: Header

    private var closeHeader: some View {
        HStack {
            Spacer(minLength: 0)
            Button { dismiss() } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(.inkMuted)
                    .frame(width: 44, height: 44, alignment: .trailing)
            }
            .accessibilityLabel("Close")
        }
        .padding(.horizontal, .hearth500)
        .padding(.top, .hearth300)
    }

    // MARK: Title

    private var titleBlock: some View {
        VStack(spacing: .hearth500) {
            MVPLogoView(variant: .wordmark, size: 96, tint: .inkPrimary)
            Text("Pick a plan and start your free trial today!")
                .font(.hearthDisplayMD)
                .foregroundColor(.inkPrimary)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    // MARK: Monthly | Annual toggle

    private var cycleToggle: some View {
        HStack(spacing: 0) {
            ForEach(PaywallBillingCycle.allCases) { option in
                cycleOption(option)
            }
        }
        .padding(.hearth300)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusPill, style: .continuous))
        .hearthCardElevation()
    }

    private func cycleOption(_ option: PaywallBillingCycle) -> some View {
        let selected = cycle == option
        return Button {
            withAnimation(.hearth(.hearthFast, reduceMotion: reduceMotion)) { cycle = option }
        } label: {
            Text(option.label)
                .font(.hearthTitleMD)
                .foregroundColor(selected ? .inkOnPhotoLight : .inkSecondary)
                .frame(maxWidth: .infinity)
                .padding(.vertical, .hearth400)
                .background(selected ? Color.accentDefault : Color.clear)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusPill, style: .continuous))
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(selected ? [.isSelected] : [])
    }

    // MARK: Plan cards

    private var plansStack: some View {
        VStack(spacing: .hearth500) {
            ForEach(paywallPlans) { plan in
                PaywallPlanCard(
                    plan: plan,
                    onBuy: {
                        pickedPlanName = plan.name.capitalized
                        pickedPlanBilling = cycle.label
                        onContinue()
                    },
                    buyAccessibilityHint: buyAccessibilityHint
                )
            }
        }
    }

    // MARK: Footer

    /// The frame's footer reads "Purchases will open Stripe in a new tab." —
    /// there is no Stripe integration; both Buy buttons just advance
    /// (smoke-and-mirrors, Miguel's explicit call). That line would be a
    /// lie, so it's omitted rather than shown as drawn — same real-data-only
    /// rule the consolidated Settings cards follow.
    private var footer: some View {
        EmptyView()
    }
}

// MARK: - Plan card

private struct PaywallPlanCard: View {
    let plan: PaywallPlan
    var onBuy: () -> Void = {}
    var buyAccessibilityHint: String = "Not yet available"

    var body: some View {
        VStack(alignment: .leading, spacing: .hearth500) {
            header
            bullets
            PaywallBuyButton(planName: plan.name, action: onBuy, accessibilityHint: buyAccessibilityHint)
        }
        .padding(.hearth600)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.bgElevated)
        .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusLg, style: .continuous))
        .hearthCardElevation()
    }

    private var header: some View {
        HStack(alignment: .firstTextBaseline) {
            Text(plan.name)
                .font(.hearthSectionHeader)
                .textCase(.uppercase)
                .foregroundColor(.inkPrimary)
            Spacer(minLength: .hearth400)
            Text(plan.priceLabel)
                .font(.hearthTitleLG)
                .foregroundColor(.inkPrimary)
        }
    }

    private var bullets: some View {
        VStack(alignment: .leading, spacing: .hearth300) {
            ForEach(plan.bullets, id: \.self) { bullet in
                HStack(alignment: .firstTextBaseline, spacing: .hearth300) {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(.accentOnCanvas)
                    Text(bullet)
                        .font(.hearthBodyMD)
                        .foregroundColor(.inkSecondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
    }
}

// MARK: - Buy button
//
// Deliberately wired to NOTHING PURCHASE-RELATED. Apple normally requires
// In-App Purchase for a digital subscription; the design's footer
// ("Purchases will open Stripe in a new tab") is at best a US-storefront-only
// link-out under the 2025 Epic injunction, and that policy area moves. No
// purchase rail ships — no StoreKit, no URL open, no Stripe SDK — until the
// Stripe-vs-IAP compliance question is decided (plan
// `drifting-jingling-valley.md`, Phase 4).
//
// `action` defaults to a real no-op (Settings-menu context: a Buy button that
// visibly does nothing yet is the correct, deliberate state there). The
// onboarding funnel's `.plan` step passes its own `goTo(.warmup)` through
// `PaywallView.onContinue` — that is ALSO not a purchase, just advancing a
// screen, per Miguel's explicit "it does nothing, just lets you go to the
// next step" (2026-08-09). Do not add StoreKit / URL-open / Stripe SDK here
// without the compliance decision above, regardless of caller.
private struct PaywallBuyButton: View {
    let planName: String
    var action: () -> Void = {}
    /// "Not yet available" is true for the Settings-menu no-op but would be a
    /// LIE inside the funnel, where tapping this genuinely advances to
    /// `.warmup` — the funnel step overrides it accordingly.
    var accessibilityHint: String = "Not yet available"

    var body: some View {
        Button(action: action) {
            Text("Buy")
                .font(.hearthTitleMD)
                .foregroundColor(.inkOnPhotoLight)
                .frame(maxWidth: .infinity)
                .padding(.vertical, .hearth400)
                .background(Color.accentDefault)
                .clipShape(RoundedRectangle(cornerRadius: .hearthRadiusButton, style: .continuous))
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Buy \(planName)")
        .accessibilityHint(accessibilityHint)
    }
}

// MARK: - Preview

#Preview("Choose a plan") {
    // Previews the design directly, bypassing the PostHog flag gate (which
    // reads `false` in a preview process with no PostHogSDK.setup() call).
    PaywallView().screen
}
