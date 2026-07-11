import SwiftUI
import AuthenticationServices
import CryptoKit

/// Sign-in gate: native Sign in with Apple + "Continue with Google" (web flow).
///
/// On success it persists an `AuthCredential` (access + refresh) via
/// `AuthService` and calls `onSignedIn(userId)`. If a legacy install is present
/// (the app still holds `user_name` + a legacy token), that ownership proof is
/// forwarded so the sign-in CLAIMS the existing account — the family keeps all
/// its data under the same user_id.
struct SignInView: View {
    /// Called after a successful sign-in with the resolved account and whether
    /// it already has a profile (returning user → skip onboarding).
    var onSignedIn: (AuthService.SignInOutcome) -> Void

    @State private var errorMessage: String?
    @State private var busy = false
    /// Current raw nonce for an in-flight Apple request (we send its sha256 to
    /// Apple and the raw value to our backend to verify).
    @State private var currentNonce: String?

    private var baseURL: URL {
        URL(string: UserDefaults.standard.string(forKey: "chat.base_url") ?? ServerConfiguration.defaultURL)
            ?? URL(string: ServerConfiguration.productionURL)!
    }

    // Legacy ownership proof, if this install predates sign-in.
    private var legacyUserID: String? {
        let name = UserDefaults.standard.string(forKey: "user_name")
        return (name?.isEmpty == false) ? name : nil
    }
    private var legacyToken: String? {
        guard let uid = legacyUserID else { return nil }
        // MUST be the raw legacy opaque token, never a v1 JWT — see
        // AuthService.legacyToken(for:). A JWT here fails the server's
        // lookup_auth_token and silently drops the claim → duplicate account.
        return AuthService.shared.legacyToken(for: uid)
    }

    var body: some View {
        VStack(spacing: 24) {
            Spacer()
            Text("Welcome")
                .font(.largeTitle.bold())
            Text("Sign in to keep your family's plan in sync across your devices.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)

            Spacer()

            SignInWithAppleButton(.signIn) { request in
                let nonce = Self.randomNonce()
                currentNonce = nonce
                request.requestedScopes = [.fullName, .email]
                request.nonce = Self.sha256(nonce)
            } onCompletion: { result in
                handleApple(result)
            }
            .signInWithAppleButtonStyle(.black)
            .frame(height: 50)
            .padding(.horizontal, 32)
            .disabled(busy)

            Button(action: signInWithGoogle) {
                HStack {
                    Image(systemName: "globe")
                    Text("Continue with Google")
                }
                .frame(maxWidth: .infinity, minHeight: 50)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
            .padding(.horizontal, 32)
            .disabled(busy)

            if let errorMessage {
                Text(errorMessage)
                    .font(.footnote)
                    .foregroundStyle(.red)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)
            }
            Spacer()
        }
        .overlay { if busy { ProgressView() } }
        .trackScreen("sign_in")
    }

    // MARK: - Apple

    private func handleApple(_ result: Result<ASAuthorization, Error>) {
        switch result {
        case .failure(let error):
            // A user cancel is not an error worth surfacing loudly.
            if (error as? ASAuthorizationError)?.code == .canceled { return }
            errorMessage = "Apple sign-in failed. Please try again."
        case .success(let auth):
            guard let cred = auth.credential as? ASAuthorizationAppleIDCredential,
                  let tokenData = cred.identityToken,
                  let idToken = String(data: tokenData, encoding: .utf8) else {
                errorMessage = "Could not read Apple credentials."
                return
            }
            let nonce = currentNonce
            busy = true
            Task {
                do {
                    let outcome = try await AuthService.shared.loginWithProvider(
                        provider: "apple", idToken: idToken, nonce: nonce,
                        baseURL: baseURL,
                        legacyUserID: legacyUserID, legacyToken: legacyToken
                    )
                    busy = false
                    onSignedIn(outcome)
                } catch {
                    busy = false
                    #if DEBUG
                    errorMessage = "Sign-in failed: \(error.localizedDescription)"
                    #else
                    errorMessage = "Sign-in couldn't be completed. Please try again."
                    #endif
                }
            }
        }
    }

    // MARK: - Google (web redirect → one-time login_code)

    private func signInWithGoogle() {
        guard let startURL = URL(string: baseURL.appendingPathComponent("auth/google/start").absoluteString + "?surface=ios") else { return }
        busy = true
        let scheme = "mvparent"
        let session = ASWebAuthenticationSession(url: startURL, callbackURLScheme: scheme) { callbackURL, error in
            guard let callbackURL, error == nil else {
                busy = false
                if (error as? ASWebAuthenticationSessionError)?.code == .canceledLogin { return }
                errorMessage = "Google sign-in was cancelled."
                return
            }
            // Callback: mvparent://auth?status=success&login_code=...
            let comps = URLComponents(url: callbackURL, resolvingAgainstBaseURL: false)
            let items = comps?.queryItems ?? []
            guard items.first(where: { $0.name == "status" })?.value == "success",
                  let code = items.first(where: { $0.name == "login_code" })?.value else {
                busy = false
                let reason = items.first(where: { $0.name == "reason" })?.value
                #if DEBUG
                errorMessage = "Google sign-in failed" + (reason.map { ": \($0)" } ?? " (no reason in callback)")
                #else
                errorMessage = "Google sign-in failed."
                #endif
                return
            }
            Task {
                do {
                    let outcome = try await AuthService.shared.exchangeLoginCode(
                        code, baseURL: baseURL,
                        legacyUserID: legacyUserID, legacyToken: legacyToken
                    )
                    busy = false
                    onSignedIn(outcome)
                } catch {
                    busy = false
                    errorMessage = "Sign-in couldn't be completed. Please try again."
                }
            }
        }
        session.presentationContextProvider = AuthPresentationAnchor.shared
        session.prefersEphemeralWebBrowserSession = false
        session.start()
    }

    // MARK: - Nonce helpers

    private static func randomNonce(length: Int = 32) -> String {
        let chars = Array("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-._")
        var result = ""
        var remaining = length
        while remaining > 0 {
            var random: UInt8 = 0
            _ = SecRandomCopyBytes(kSecRandomDefault, 1, &random)
            if Int(random) < chars.count {
                result.append(chars[Int(random)])
                remaining -= 1
            }
        }
        return result
    }

    private static func sha256(_ input: String) -> String {
        SHA256.hash(data: Data(input.utf8)).map { String(format: "%02x", $0) }.joined()
    }
}

#if DEBUG
/// DEBUG-only harness for exercising SignInView in the simulator (launched via
/// TEST_SIGNIN=1). Shows the result of a successful sign-in so we can confirm
/// the token round-trip without wiring the real onboarding gate.
struct SignInTestHarness: View {
    @State private var result: String?

    var body: some View {
        if let result {
            VStack(spacing: 16) {
                Image(systemName: "checkmark.seal.fill").font(.system(size: 48)).foregroundStyle(.green)
                Text("Signed in").font(.title2.bold())
                Text(result).font(.footnote.monospaced()).multilineTextAlignment(.center).padding()
                Button("Sign out / retry") {
                    if let uid = AuthService.shared.credential(for: extractUserId(result))?.userId {
                        AuthService.shared.clear(for: uid)
                    }
                    self.result = nil
                }
            }.padding()
        } else {
            SignInView { outcome in
                let cred = AuthService.shared.credential(for: outcome.userId)
                result = """
                user_id: \(outcome.userId)
                has_profile: \(outcome.hasProfile)
                analytics_id: \(cred?.analyticsId ?? "-")
                access: \(String((cred?.accessToken ?? "").prefix(24)))…
                refresh: \(cred?.refreshToken != nil ? "stored" : "none")
                """
            }
        }
    }

    private func extractUserId(_ s: String) -> String {
        s.split(separator: "\n").first.map { String($0).replacingOccurrences(of: "user_id: ", with: "") } ?? ""
    }
}
#endif

/// Presentation anchor for ASWebAuthenticationSession (Google flow).
final class AuthPresentationAnchor: NSObject, ASWebAuthenticationPresentationContextProviding {
    static let shared = AuthPresentationAnchor()
    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        let scenes = UIApplication.shared.connectedScenes
        let window = scenes.compactMap { $0 as? UIWindowScene }.flatMap { $0.windows }.first { $0.isKeyWindow }
        return window ?? ASPresentationAnchor()
    }
}
