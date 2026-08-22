import SwiftUI

// MARK: - Heisman "choose a plan" (frames 29:3563 monthly / 29:3635 annual)
//
// The smoke-and-mirrors subscription screen, shown ONLY inside onboarding,
// immediately after account creation — never anywhere else in the app. "Buy"
// buys nothing; it advances the funnel (new parent → warmup, returning parent
// → straight to Home).
//
// Measured off the frames: hero ground cream-50 → bgCard, pt 60 / px 30 /
// section gap 28; tumbler mark 51×97; headline Inter Bold 32 −0.64; toggle
// Inter 22 (active ink-500 → inkSecondary, inactive #C8C3B8 → borderInputPill,
// the "|" divider rides the inactive tone); cards paper → bgCoachBanner r24
// p30 gap 24 w/ the frame's soft drop shadow; eyebrow Bold 14 tracking 2.1
// UPPERCASE over a 1px ink underline (the frame paints BASIC's eyebrow a
// stray grey labeled status/success — normalized to ink like FAMILY's);
// price Bold 24; USP rows = 20pt ink circle-check + SemiBold 12, gap 13,
// inner px 30; Buy = accent capsule ~r58 p14.5 SemiBold 16. Roboto in the
// frame ships as Inter per the sprint's font carve-out. The annual frame's
// "Save $XX.XX" is an unfilled placeholder — computed from the real deltas
// instead (12×monthly − annual). Footer copy kept verbatim from the frame,
// "in a new tab" and all (flagged to Greg — it reads webby on iOS).

struct HeismanPlanView: View {
    let onContinue: () -> Void
    var buyAccessibilityHint: String = "Continues to the next step"

    @State private var annual = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    private struct Plan {
        let name: String
        let monthly: String
        let annualPrice: String
        let annualSave: String
        let perks: [String]
    }

    private static let basic = Plan(
        name: "BASIC", monthly: "$8.99 / month",
        annualPrice: "$102 per year", annualSave: "Save $5.88",
        perks: ["7-day free trial", "Monthly membership", "AI coach", "Team feedback"])
    private static let basicAnnualPerks = ["Annual membership", "7-day free trial", "AI coach", "Team feedback"]
    private static let family = Plan(
        name: "FAMILY", monthly: "$13.99 / month",
        annualPrice: "$162 per year", annualSave: "Save $5.88",
        perks: ["7-day free trial", "Monthly membership", "AI Coach", "Up to six users", "Team feedback"])
    private static let familyAnnualPerks = ["Annual membership", "7-day free trial", "AI Coach", "Up to six users", "Team feedback"]

    var body: some View {
        ScrollView {
            VStack(spacing: 28) {
                Image("OnboardingHeismanMarkSM")
                    .resizable()
                    .scaledToFit()
                    .frame(width: 51, height: 97)
                    .accessibilityHidden(true)

                Text("Pick a plan and start your free trial today!")
                    .font(.system(size: 32, weight: .bold))
                    .tracking(-0.64)
                    .foregroundColor(.inkPrimary)
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)

                toggle

                VStack(spacing: 30) {
                    planCard(Self.basic, annualPerks: Self.basicAnnualPerks)
                    planCard(Self.family, annualPerks: Self.familyAnnualPerks)
                    footer
                }
            }
            .padding(.horizontal, 30)
            .padding(.top, 60)
            .padding(.bottom, 40)
        }
        .background(Color.bgCard.ignoresSafeArea())
        .trackScreen("onboarding_plan")
    }

    private var toggle: some View {
        HStack(spacing: 8) {
            Button { withAnimation(reduceMotion ? nil : .easeInOut(duration: 0.15)) { annual = false } } label: {
                Text("monthly")
                    .foregroundColor(annual ? .borderInputPill : .inkSecondary)
            }
            Text("|").foregroundColor(.borderInputPill)
            Button { withAnimation(reduceMotion ? nil : .easeInOut(duration: 0.15)) { annual = true } } label: {
                Text("annual")
                    .foregroundColor(annual ? .inkSecondary : .borderInputPill)
            }
        }
        .font(.system(size: 22))
        .tracking(-0.44)
        .accessibilityElement(children: .contain)
    }

    private func planCard(_ plan: Plan, annualPerks: [String]) -> some View {
        VStack(spacing: 24) {
            Text(plan.name)
                .font(.system(size: 14, weight: .bold))
                .tracking(2.1)
                .foregroundColor(.inkPrimary)
                .padding(.bottom, 10)
                .overlay(alignment: .bottom) {
                    Rectangle().fill(Color.inkPrimary).frame(height: 1)
                }

            VStack(spacing: 6) {
                Text(annual ? plan.annualPrice : plan.monthly)
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(.inkPrimary)
                if annual {
                    Text(plan.annualSave)
                        .font(.hearthCaptionMono)
                        .foregroundColor(.inkSecondary)
                }
            }

            VStack(alignment: .leading, spacing: 12) {
                ForEach(annual ? annualPerks : plan.perks, id: \.self) { perk in
                    HStack(spacing: 13) {
                        ZStack {
                            Circle().fill(Color.inkPrimary).frame(width: 20, height: 20)
                            Image(systemName: "checkmark")
                                .font(.system(size: 9, weight: .bold))
                                .foregroundColor(.inkOnPhotoLight)
                        }
                        Text(perk)
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(.inkPrimary)
                        Spacer(minLength: 0)
                    }
                }
            }
            .padding(.horizontal, 30)

            Button(action: onContinue) {
                Text("Buy")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.inkOnPhotoLight)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14.5)
                    .background(Capsule().fill(Color.accentDefault))
            }
            .padding(.top, 20)
            .accessibilityLabel("Buy \(plan.name.capitalized)")
            .accessibilityHint(buyAccessibilityHint)
        }
        .padding(30)
        .background(Color.bgCoachBanner)
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .shadow(color: .black.opacity(0.15), radius: 15, x: 0, y: 4)
    }

    private var footer: some View {
        (Text("Purchases will open ")
            + Text("Stripe").foregroundColor(.accentDefault)
            + Text(" in a new tab."))
            .font(.system(size: 14, weight: .bold))
            .foregroundColor(.inkMuted)
            .multilineTextAlignment(.center)
    }
}
