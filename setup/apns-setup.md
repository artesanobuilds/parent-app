# APNs setup — crisis-lock push notifications

When a kid companion is **crisis-locked**, the backend sends the parent an APNs
push ("[Kid]'s companion was paused — tap to review") so a safety lock is never
invisible. The code (`mvp-backend/app/push/`) is **env-gated**: a complete no-op
until the four `APNS_*` vars are set on Railway. This guide is the one-time Apple
+ Railway setup to switch it on.

The backend uses **token-based APNs** (an ES256 JWT signed with a `.p8` auth key)
— no certificates, no per-app-per-year renewals.

---

## Values for this app (already gathered)

| Env var | Value | Source |
| --- | --- | --- |
| `APNS_KEY_ID` | `K97TDFQ2UM` | the `<KEYID>` in `AuthKey_K97TDFQ2UM.p8` |
| `APNS_TEAM_ID` | `5K4ZDG6NFD` | the `MVP.MVParent` app target's `DEVELOPMENT_TEAM` |
| `APNS_BUNDLE_ID` | `MVP.MVParent` | the app target's `PRODUCT_BUNDLE_IDENTIFIER` |
| `APNS_AUTH_KEY` | *(paste the full `.p8` contents)* | `mvp-backend/secrets/AuthKey_K97TDFQ2UM.p8` |
| `APNS_USE_SANDBOX` | *(leave unset)* | TestFlight/App Store = production APNs |

> ⚠️ `APNS_TEAM_ID` must be the team you **created the key in**. It's `5K4ZDG6NFD`
> here because that's the team the app ships under; confirm it matches the Team ID
> shown top-right in the Apple Developer portal when you made the key. (The repo's
> test targets use a *different* personal team — ignore that one.)

---

## 1. The APNs auth key (.p8) — done

Created in Apple Developer → **Certificates, Identifiers & Profiles → Keys**, with:
- **Apple Push Notifications service (APNs)** enabled
- **Environment: Sandbox & Production** (can't be changed after saving — pick the
  flexible option so the one key works for both TestFlight *and* debug builds)
- **Key Restriction: Team Scoped (All Topics)** (the backend passes the bundle id
  as `apns-topic` per request)

The `.p8` downloads **once** and now lives at
`mvp-backend/secrets/AuthKey_K97TDFQ2UM.p8` (gitignored). It's the only copy —
don't lose it. The **Key ID** is in the filename.

## 2. Add the Push Notifications capability in Xcode

In `mvp/MVP.xcodeproj`, select the **MVParent** target → **Signing & Capabilities**
→ **+ Capability** → **Push Notifications**. This creates an `MVP.entitlements`
file with `aps-environment`. Xcode manages the value automatically:
- **Debug builds** → `aps-environment: development` (sandbox)
- **TestFlight / App Store builds** → `aps-environment: production`

Commit the new `.entitlements` file + the pbxproj change. No app code change is
needed — `mvp/MVP/SwayApp.swift` already registers for remote notifications and
uploads the device token to `POST /push/register-device` after onboarding.

## 3. Set the env vars on Railway

Backend service → **Variables**:

```
APNS_KEY_ID=K97TDFQ2UM
APNS_TEAM_ID=5K4ZDG6NFD
APNS_BUNDLE_ID=MVP.MVParent
APNS_AUTH_KEY=<paste the entire .p8, including the
-----BEGIN PRIVATE KEY----- and -----END PRIVATE KEY----- lines>
```

Notes:
- Paste the **full PEM** for `APNS_AUTH_KEY`. Multi-line is fine; the code also
  tolerates a single line with literal `\n` (Railway sometimes flattens newlines).
- **Do NOT set `APNS_USE_SANDBOX`.** Unset = production host (`api.push.apple.com`)
  = correct for TestFlight. Only set it to `true` if you're testing a **debug build
  installed straight from Xcode onto a physical device** (sandbox host). The
  simulator can't receive remote pushes at all.

Redeploy (`cd mvp-backend && railway up --detach`). On boot you'll see
`[push] APNs enabled (host=… topic=MVP.MVParent)` in the logs — that confirms it
armed. If a var is missing/malformed you'll see `[push] APNS_* set but unusable…`
and push stays a no-op (nothing else breaks).

## 4. The gotcha: TestFlight is PRODUCTION, not sandbox

The single biggest APNs footgun: **TestFlight uses the production APNs
environment**, even though it feels like "testing." So:
- TestFlight build (`aps-environment: production`) + backend default host
  (`api.push.apple.com`) → **match** ✅
- A sandbox device token sent to the production host (or vice-versa) → APNs returns
  `400 BadDeviceToken` and nothing delivers.

Keep the pair aligned: **production build ↔ production host** (default), or
**debug build ↔ `APNS_USE_SANDBOX=true`**.

---

## Verify end-to-end

1. Install a **TestFlight** build on a **real device**; accept the notification
   permission prompt (it appears after onboarding). The app calls
   `registerForRemoteNotifications` → uploads the token to
   `POST /push/register-device`.
2. Confirm the token registered (as that user):
   `POST /auth/issue-token {user_id}` → the app already did the register call; check
   Railway logs for a `push/register-device` `200`.
3. Trigger a crisis lock for one of that user's kid companions (e.g. via the kid
   chat safety path), then confirm the device gets the "companion was paused" push
   and tapping it opens the app to Home with the red **Review** pill.
4. In the moderation event, `parent_notified_at` is now stamped (was always null)
   — that's the "we actually dispatched a push" marker.

## How it works (for reference)

- `app/push/__init__.py` — `init_push()` arms on the four env vars; `send_crisis_push`
  is fire-and-forget on a daemon thread, signs the ES256 provider JWT (cached ~50min)
  with `cryptography`, and POSTs to `{host}/3/device/{token}` over HTTP/2 (`httpx`+`h2`).
  410-unregistered tokens are pruned.
- Wired at all four crisis-lock sites (`app/server.py` text ×2, `app/convai_endpoint.py`
  voice ×2), right alongside the existing Slack `alert_crisis`.
- Device tokens live in the `push_device_tokens` table (per-user, cascade-deleted
  with the family; excluded from the deploy image via `.dockerignore`).
