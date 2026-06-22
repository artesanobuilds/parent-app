# Google OAuth Setup (Gmail + Google Calendar)

How to wire up the Google integration that powers **Gmail ingestion (R3)** and
**two-way Google Calendar sync (R4 part 2)**. The backend OAuth flow already
exists (`app/oauth/`, `app/integrations/`); this doc is the **external config**
needed to make it live.

The flow: the iOS app fetches a consent URL from `GET /oauth/google/authorize-url`,
opens it in an in-app browser, the user grants scopes, Google redirects to
`GET /oauth/google/callback`, the backend exchanges the code for an (encrypted)
refresh token in `integration_accounts`, then redirects to the app's
`mvparent://` scheme.

---

## 1. Google Cloud Console — project + APIs

1. Go to <https://console.cloud.google.com>. Create or select a project (reusing
   `claude-alvarado` is fine, or make a new `parent-app`).
2. **APIs & Services → Library** → enable:
   - **Gmail API**
   - **Google Calendar API**

## 2. OAuth consent screen

**APIs & Services → OAuth consent screen:**
- User type: **External**
- App name, user support email, developer contact email
- **Scopes** — add:
  - `.../auth/gmail.readonly`  ← **restricted** (needs verification to ship broadly)
  - `.../auth/calendar.events`
  - `openid`, `.../auth/userinfo.email`
- **Test users** — add your own Google account (and any testers)
- **Publishing status: keep on "Testing"** — test users can complete the flow
  immediately without full verification.

## 3. Create the OAuth client

**APIs & Services → Credentials → Create Credentials → OAuth client ID:**
- Application type: **Web application** (the *backend* performs the code
  exchange, so it's a web client — NOT an iOS client)
- **Authorized redirect URIs** (must match exactly what the backend sends):
  - `https://mvp-backend-production-8678.up.railway.app/oauth/google/callback`
  - `http://127.0.0.1:8904/oauth/google/callback` (local dev)
- Save → copy the **Client ID** and **Client secret**.

## 4. Backend env vars (Railway → mvp-backend → Variables)

| Variable | Value |
| --- | --- |
| `GOOGLE_OAUTH_CLIENT_ID` | the client id from step 3 |
| `GOOGLE_OAUTH_CLIENT_SECRET` | the client secret from step 3 |
| `INTEGRATION_ENC_KEY` | a Fernet key (encrypts refresh tokens at rest) |
| `GOOGLE_OAUTH_REDIRECT_URI` | *(optional)* defaults to the prod callback above |
| `APP_OAUTH_CALLBACK_SCHEME` | *(optional)* defaults to `mvparent` |

Generate the encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

> ⚠️ Set `INTEGRATION_ENC_KEY` **before** anyone connects an account. If it
> changes later, previously-stored refresh tokens can't be decrypted and users
> must reconnect. Set the same value locally in `mvp-backend/.env`.

Setting any Railway variable triggers a redeploy (~90s restart — brief voice blip).

## 5. iOS (already handled in the app)

- Settings → **Integrations** has the "Connect Gmail & Calendar" entry
  (`GmailService` + `WebAuthRunner`).
- The consent runs in an `ASWebAuthenticationSession` with callback scheme
  `mvparent` — the session intercepts the `mvparent://oauth/google?status=…`
  redirect itself, so **no Info.plist `CFBundleURLTypes` registration is needed**.
- If you change `APP_OAUTH_CALLBACK_SCHEME` on the backend, update
  `WebAuthRunner.callbackScheme` in `mvp/MVP/GmailService.swift` to match.

## 6. Verification + CASA (for non-test users — long lead time)

`gmail.readonly` is a Google **restricted scope**. To let *anyone* (beyond your
test users) connect Gmail, you must complete **Google app verification** plus an
annual **CASA** third-party security assessment — this takes **weeks** and has a
real cost. Start it early from the OAuth consent screen → "Publish app".

**Not required** for you-as-a-test-user, so development/demo works today once
steps 1–4 are done. Calendar (`calendar.events`) is a sensitive (not restricted)
scope and is lighter-weight.

---

## Verify it works

1. Complete steps 1–4, redeploy.
2. `GET /oauth/google/authorize-url?kinds=email,calendar` (with a Bearer token)
   should return a real `accounts.google.com` URL (not a 503).
3. In the app: Settings → Integrations → Connect Gmail → consent → it should
   return to the app and show "Connected as you@gmail.com".
4. `GET /oauth/google/status` lists the connected accounts (never the token).
