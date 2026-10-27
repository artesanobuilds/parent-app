# Parent: “Sign in with ChatGPT” feasibility

Verified against current official OpenAI documentation on 13 October 2026. This is a product/technical feasibility review, not a legal opinion. No credentials were requested, copied, generated, or configured, and no OAuth connection was made.

## Verdict

**Conditional yes.** OpenAI now documents an actual **Sign in with ChatGPT** product with two separate capabilities: identity sign-in and permission to use a subscriber’s ChatGPT plan for eligible inference requests. It would be inaccurate to say this never exists or is necessarily an unsupported workaround. Eligible ChatGPT Plus and Pro users can use it in participating applications. [Official quickstart](https://developers.openai.com/siwc/quickstart)

**For a paid or provider-hosted Parent app, access is the gating dependency.** The documented commercial offering is a selected-partner limited trial, with a waitlist rather than unrestricted self-service availability. Parent’s admission has not been established. Do not promise a launch date or build the business model around approval until OpenAI confirms it. [Client-ID request and waitlist](https://developers.openai.com/siwc/request-client-id)

The open-source route is documented for open-source and locally hosted applications; paid or remotely hosted applications are directed to the interest form. A separate guide supports an open-source application running on the user’s self-hosted VM. This should not be interpreted as permission to disguise a multi-user SaaS as a local client. [Plan-usage overview](https://developers.openai.com/siwc/token-sharing-open-source), [self-hosted VM guide](https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms)

## Distinguish the five integration choices

### 1. ChatGPT identity sign-in

This is OAuth Authorization Code with PKCE plus OpenID Connect. Parent verifies the ID token, associates the verified identity with a Parent account, and creates its own application session. It needs an assigned client ID and registered callbacks; confidential web clients may also require a client secret. The website guide itself marks availability as a commercial limited trial. An identity token is not an inference entitlement. [Website sign-in guide](https://developers.openai.com/siwc/website)

Identity scopes can provide an account identifier and basic profile information. They do not provide ChatGPT conversation access, an API key, or general API access. Additional plan-usage permission is a separate consent. [Official quickstart](https://developers.openai.com/siwc/quickstart)

### 2. Authorized ChatGPT plan usage in an external application

The documented public-client flow uses a system-browser OAuth exchange, PKCE, a loopback callback, a stable host identifier, and a user/workspace-bound issued client registration. Its plan scopes include `offline_access`, `resource.invoke`, and `chatgpt.tokens.use.direct`; the application must check the granted scopes, not merely a successful identity login. Initial dynamic registration does not require a client secret or partner API key. This flow is documented for OSS clients, not as a commercial-access bypass. [Registration and sign-in](https://developers.openai.com/siwc/token-sharing-open-source/sign-in)

The OAuth access token authorizes eligible calls to `https://api.openai.com/v1/responses`. OpenAI explicitly says not to send this flow to ChatGPT’s `backend-api` endpoints. Discover currently available models with the same signed-in account rather than assuming every API model is entitled. A successful inference request is the relevant verification. [Models and inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)

### 3. Codex subscription authentication and Codex App Server

The normal Codex login distinguishes ChatGPT subscription access from usage-based API-key access. Workspace access tokens are for trusted Codex automation; they are not a generic consumer-app OAuth product. Existing Codex credentials should not become a substitute for registering Parent’s own authorized integration. [Codex authentication](https://learn.chatgpt.com/docs/auth)

Separately, the SIWC documentation explicitly supports using an authorized plan-usage token with Codex App Server, configured as a Responses provider. No additional Codex sign-in is required for that configuration. Parent remains responsible for its application identity, user authorization, token management, and process isolation. An App Server model listing may be cached and is not proof of entitlement. [SIWC App Server guide](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server)

### 4. Ordinary OpenAI API billing, including BYOK

API-key calls are billed to the OpenAI Platform account at API rates, rather than consuming included ChatGPT plan credits. A user bringing an API key is therefore bringing a separate API billing account, not transferring their Plus/Pro allowance. [Codex authentication and billing distinction](https://learn.chatgpt.com/docs/auth)

Two technical architectures are available: Parent pays through its own API project, or a customer-controlled deployment uses that customer’s API project. Hosted BYOK introduces secret-handling, rotation, support, and billing responsibilities; it should not mean asking users to paste ChatGPT session tokens. Keep API credentials in protected runtime storage or a secret manager. The API documentation supports organization/project billing and spend controls, but does not by itself establish that every commercial key-collection arrangement is approved. [Production and API-key guidance](https://developers.openai.com/api/docs/guides/production-best-practices)

### 5. A Parent plugin/MCP integration inside ChatGPT

A plugin can expose Parent’s tools/data and optional UI within ChatGPT or Codex. This lets the OpenAI host conduct the conversation and invoke Parent’s capabilities. It is a different product experience from powering an independent Parent website or mobile app. Current documentation describes plugins as packages containing skills, an MCP server, or both, with optional MCP Apps UI. [Plugin architecture](https://developers.openai.com/plugins/concepts/plugins)

Ordinary MCP OAuth authorizes ChatGPT to call Parent’s server: Parent is the resource provider and ChatGPT is the client. It does not hand Parent the user’s general model entitlement. [Plugin authentication](https://developers.openai.com/plugins/build/auth)

SIWC inside a plugin adds a second, distinct identity transaction: one authorizes the connector and the other signs the person into Parent. Their codes, state, callbacks and credentials must remain separate. [SIWC in a plugin](https://developers.openai.com/siwc/chatgpt-plugin)

## Cost and UX implications

“Bring your ChatGPT plan” is the accurate product description. “Bring your own tokens” can confuse model usage with secret authentication tokens or a prepaid token balance.

Plan-backed usage draws from the person’s existing Codex/ChatGPT Work allowance; connecting another app does not create a fresh allocation. Users can cap app usage as a percentage of their weekly plan usage, revoke the connection, and may face the application’s own fees. Do not promise unlimited inference or a dedicated reserved allowance. [User-facing SIWC guide](https://learn.chatgpt.com/docs/sign-in-with-chatgpt)

The session guide says Plus users share one five-hour usage total across connected applications; this five-hour limit does not apply to Pro. This does not establish unlimited Pro usage. [Accounts and sessions](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions)

Show the active funding mode and a usage-management link. On exhaustion, preserve user work and explain the applicable limit. If Parent offers its own paid credits, the guidelines permit presenting them as a secondary option; do not silently switch the payer. The documentation does not publish a universal commercial-partner fee or guarantee Parent’s pricing. [SIWC UX requirements](https://developers.openai.com/siwc/ui-ux-guidelines)

## Current technical limitations that affect Parent’s design

The plan-backed Responses route is a preview with a narrower contract than ordinary API-key usage:

- HTTP requires streaming and `store: false`; the client supplies conversation context. No persistent server-side conversation state through this route.
- Several ordinary request fields are unsupported, including background mode, temperature, maximum-output-token controls, and top-level multi-agent mode.
- Hosted image generation, file search, Code Interpreter, native computer use, hosted MCP/connectors, and Responses tool search are unavailable.
- Model-compatible text, image and file inputs can work; audio/video inputs, the Files upload API and transcription are unsupported.
- Function/custom tools can support client-run capabilities. Codex can coordinate local shell/MCP tools and child agents through those tools, which is distinct from hosted Responses features.
- In the documented App Server environment-token setup, Parent refreshes the token and restarts/resumes the process with the replacement.

This is a material constraint if Parent depends on voice, uploaded-file retrieval, background jobs, or a full hosted agent platform. [Preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)

## Privacy, security and contractual boundaries

SIWC does not import the person’s ChatGPT conversations or memories. Parent will need its own explicit data model and separately authorized sources for personalization. [User-facing SIWC guide](https://learn.chatgpt.com/docs/sign-in-with-chatgpt)

Access tokens last one hour; refresh tokens rotate and have a 30-day validity window after each successful replacement. Treat both as secrets. [Token reference](https://developers.openai.com/siwc/token-sharing-open-source/token-reference)

Keep registrations separated by validated identity and issued client ID. Store credentials in protected local/self-hosted runtime storage, not browser storage, analytics, logs, or support transcripts. Provide disconnect/revocation and handle refresh races. [Accounts and sessions](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions)

For conventional API-key usage, OpenAI states API data is not used for model training by default, while abuse-monitoring retention and application-state rules still apply. Do not assume that `store: false` means zero retention, or automatically transplant API organization guarantees onto the ChatGPT-plan route. The SIWC pages reviewed do not settle every training, residency, retention, DPA, or regulated-data question for a commercial Parent deployment. Confirm those terms for the actual integration before making privacy promises. [API data controls](https://developers.openai.com/api/docs/guides/your-data)

The official integration establishes technical support within the stated eligibility. It does not grant Parent admission to the commercial trial, authorize pooling one person’s subscription across customers, or waive applicable contracts and usage policies. Commercial approval, scopes, deployment model and data terms should be confirmed with OpenAI. No roadmap date or guaranteed acceptance was found.

## Recommendation

1. Determine whether Parent is a paid/provider-hosted product or a genuinely open-source, user-run application. That decision selects the authorization path.
2. For a commercial Parent product, request trial access for both identity and ChatGPT plan usage, and ask specifically about deployment, supported features, billing, retention and data terms.
3. Keep ordinary API-backed inference available as a clearly priced independent mode while approval is unresolved. BYOK is better suited to a technically capable, customer-controlled deployment than a default consumer onboarding flow.
4. If operating inside ChatGPT meets the product goal, evaluate a Parent plugin separately.
5. Once the correct path is approved, validate one eligible user’s sign-in, account-specific model access, completed inference, limit handling, refresh, disconnect and privacy disclosures before widening availability.

The first three steps are product recommendations inferred from the official boundaries above. No implementation or commercial registration has been performed.


## Addendum on child data controls 13 October 2026

OpenAI's current under-18 API guidance calls for API zero data retention before processing personal data of under-13s or children below the applicable digital-consent age. Verify the actual deployment's applicability, approval and endpoint eligibility; parent-entered data must not be assumed exempt. [Official under-18 API guidance](https://developers.openai.com/api/docs/guides/safety-checks/under-18-api-guidance)

**Product gate:** Neither `store: false`, ordinary API availability, nor Sign in with ChatGPT establishes approved ZDR. The API fallback described above is conditional on appropriate provider data controls and terms. Confirm the correct route with the provider before any real child data. ZDR does not replace lawful consent, application security or deletion controls. This addendum does not establish that Parent is approved or configured for ZDR.
