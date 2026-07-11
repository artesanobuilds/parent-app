# Auth v2 Setup (Sign in with Apple + Google, JWT sessions, migration)

How to configure and operate the hardened auth that replaced the old
unauthenticated `/auth/issue-token`. Code lives in `app/auth.py`,
`app/auth_router.py`, `app/auth_providers.py`, `app/auth_login_google.py`,
`app/auth_pairing.py`, and iOS `SignInView.swift` / `AuthService.swift`. This doc
is the **external config + operator procedures** to make it live and run it.

Model in one line: native **Sign in with Apple / Google** → server verifies the
provider `id_token` against the provider JWKS → mints a short-lived **JWT access
token + rotating refresh token**. Existing users keep their name-based `user_id`
and **claim** it on first sign-in. See memory `project_auth_v2` for architecture.

---

## 1. Environment variables (Railway prod + local `.env`)

| Var | Value / how to generate | Notes |
| --- | --- | --- |
| `AUTH_JWT_SECRET` | `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` | **Secret.** HS256 signing key for access tokens. MUST be set in prod — without it the code falls back to an insecure dev secret. Set in Railway + mirror the same value into local `.env`. |
| `AUTH_ACCESS_TTL_MIN` | `30` (default) | Access-token lifetime in minutes. |
| `AUTH_TOKEN_TTL_DAYS` | `30` (default) | Legacy opaque-token lifetime (migration window). |
| `AUTH_ISSUE_TOKEN_ENABLED` | `1` (default) | Set `0` at **T2** to retire `/auth/issue-token` (→ 410). |
| `AUTH_LEGACY_TOKENS_ENABLED` | `1` (default) | Set `0` after T2 so `current_user` is JWT-only. |
| `GOOGLE_OAUTH_CLIENT_ID` / `_SECRET` / `_REDIRECT_URI` | already set for the Gmail/Calendar integration | Google **login** reuses the same OAuth client (see §3). |
| `APNS_BUNDLE_ID` | `MVP.MVParent` | Also used as the Apple `id_token` audience (`aud`). Override with `APPLE_AUD` if the bundle id ever differs. |

Generate + set the JWT secret (paste-ready):

```bash
cd mvp-backend
S=$(python3 -c "import secrets;print(secrets.token_urlsafe(48))")
railway variables --set "AUTH_JWT_SECRET=$S" --skip-deploys
grep -qE '^AUTH_JWT_SECRET=' .env || printf '\nAUTH_JWT_SECRET=%s\n' "$S" >> .env
```

---

## 2. Sign in with Apple (required by App Store Guideline 4.8)

Because the app offers Google login, Apple **requires** Sign in with Apple too.

### Apple Developer portal (one-time)
1. <https://developer.apple.com/account> → **Certificates, IDs & Profiles → Identifiers**.
2. Open the App ID **`MVP.MVParent`** → check **Sign in with Apple** → **Save**.
3. If it opens "App ID Configuration": leave **Enable as a primary App ID** selected; **leave the Server-to-Server Notification Endpoint blank** (we don't consume account-deletion webhooks). Save.

### Xcode (for distribution/TestFlight builds)
- MVP target → **Signing & Capabilities** → **+ Capability → Sign in with Apple**.
- The entitlement is already in `mvp/MVP/MVP.entitlements` (`com.apple.developer.applesignin`); the Xcode capability makes distribution provisioning pick it up.

### How it works (no secret needed)
Native SIWA hands the app an `id_token`; the backend verifies it against
`https://appleid.apple.com/auth/keys` (public keys) with `aud = MVP.MVParent` and
a nonce check. No `.p8` / client-secret JWT is needed (that's only for Apple's
token *exchange*, which we don't use).

---

## 3. Sign in with Google (reuses the integration OAuth client)

No new Google client needed — login reuses `GOOGLE_OAUTH_CLIENT_ID/SECRET` and
the same registered redirect `…/oauth/google/callback`. Login differs from the
Gmail/Calendar integration in three deliberate ways (in `app/oauth/google_flow.py`
+ `app/auth_login_google.py`):

- **Scopes = `openid` + `userinfo.email` only** (no Gmail/Calendar). Login just
  needs a verifiable `id_token` (sub + email).
- `include_granted_scopes=false`, `access_type=online`, `prompt=select_account`
  — so the consent asks for **email only** and does NOT re-bundle Gmail/Calendar
  scopes the user granted the same client for the integration.
- `OAUTHLIB_RELAX_TOKEN_SCOPE=1` is set in code (`google_flow.py`) — Google echoes
  scopes in a canonical form that otherwise makes oauthlib raise "Scope has
  changed". No env config needed.

**Gotcha (macOS local dev):** JWKS verification fetches the provider keys over
TLS. On a macOS `Python.framework` venv with no system CA certs this raises
`CERTIFICATE_VERIFY_FAILED`. Fixed in code via an explicit `certifi` SSL context
(`auth_providers.py`) — hardens prod too. Debug flag `AUTH_DEBUG_ERRORS=1`
(local only) surfaces the exact verification reason in the 401 body.

---

## 4. Account migration — operator playbook

Existing beta families have name-based `user_id`s and no sign-in identity yet.
They **claim** their account when they sign in (the app forwards the legacy
`user_id` + token). Both Apple (`/auth/login`) and Google (`/auth/exchange-code`)
paths claim via the shared `resolve_account()`.

**Guidance for existing users:** update the app **in place** (don't delete +
reinstall) so the legacy token is present for the automatic claim.

### Monitor
```bash
cd mvp-backend
ADMIN=$(grep -E '^ADMIN_TOKEN=' .env | sed 's/^ADMIN_TOKEN=//' | tr -d '\r\n')
H=https://mvp-backend-production-8678.up.railway.app
curl -s -H "X-Admin-Token: $ADMIN" $H/admin/auth/migration-status | python3 -m json.tool
```
Shows `claimed` / `unclaimed` counts and every identity (provider → user_id). A
correctly-claimed account has the identity on the **name-based** user_id, not a
fresh 32-hex UUID.

### Safety net — a claim landed on a fresh account (expired token / reinstall)
`POST /admin/auth/link-legacy` moves the identity onto the real account and
deletes the empty orphan:
```bash
curl -s -X POST -H "X-Admin-Token: $ADMIN" -H 'Content-Type: application/json' \
  -d '{"provider":"google","provider_sub":"<sub from migration-status>","target_user_id":"<real name-based user_id>"}' \
  $H/admin/auth/link-legacy
```
It refuses to delete a source account that has family data (only truly-empty
orphans are removed).

### Delete a throwaway orphan account directly
If you just need to free a provider `sub` bound to an empty orphan (e.g. a test),
mint a short-lived operator token and delete the family:
```bash
cd mvp-backend && source .venv/bin/activate
PROD_SECRET=$(railway variables --json | python3 -c "import sys,json;print(json.load(sys.stdin)['AUTH_JWT_SECRET'])")
ORPHAN=<orphan-user-id>
TOK=$(AUTH_JWT_SECRET="$PROD_SECRET" python -c "from app.auth import mint_access_token;print(mint_access_token('$ORPHAN')[0])")
curl -s -X DELETE -H "Authorization: Bearer $TOK" "$H/family/$ORPHAN"
```
(`/auth/issue-token` won't work for a claimed account — it 403s — hence the mint.)

### Retire legacy (T2, once `unclaimed` is empty)
1. `AUTH_ISSUE_TOKEN_ENABLED=0` (→ 410). Legacy opaque tokens die at their TTL.
2. Then `AUTH_LEGACY_TOKENS_ENABLED=0` (JWT-only).
3. Delete the dead code (issue-token, `auth_tokens`, iOS `obtainToken`, dashboard
   user_id login, the `legacy_*` claim params). See the plan's retire checklist.

---

## 5. Deploy notes
- `.dockerignore` excludes the auth-v2 user-state parquets
  (`user_accounts`/`auth_identities`/`refresh_tokens`) so `railway up` never bakes
  local account state over prod.
- Prod deploys need explicit authorization each time (per root `CLAUDE.md`).
- iOS ships via TestFlight; bump build + marketing versions each cut.
