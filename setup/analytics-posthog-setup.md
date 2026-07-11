# Product Analytics + Feature Flags Setup (PostHog)

How to activate PostHog analytics/flags/experiments. Code is in `app/analytics/`
(backend, env-gated no-op until configured). This doc is the console + env setup
and the **privacy posture** for a kids/family app.

Until the env vars below are set, the PostHog SDK is never imported and every
analytics call is a no-op — so the app is unaffected.

---

## 1. PostHog Cloud project

1. Create a project at <https://us.posthog.com> (**US region** — or EU if you
   prefer data held outside US jurisdiction; keep it consistent with the clients).
2. **Set a $0 billing limit** (Billing → limits). The pay-as-you-go plan unlocks
   Experiments while staying free under 1M events + 1M flag requests/mo, which is
   far above closed-beta volume.
3. Grab the **Project API key** (public), and create a **Personal API key**
   (Settings → Personal API keys) for the person-deletion call.

---

## 2. Railway env vars

| Var | Value | Notes |
| --- | --- | --- |
| `POSTHOG_API_KEY` | project key (`phc_…`) | Public-by-design; safe in client bundles too. |
| `POSTHOG_HOST` | `https://us.i.posthog.com` | Match your region. |
| `POSTHOG_PERSONAL_API_KEY` | personal key | **Secret.** Only for `delete_family` person deletion. |
| `POSTHOG_PROJECT_ID` | numeric project id | For the deletion API path. |
| `ANALYTICS_STRICT` | unset in prod; `1` in tests | Raises on unknown event names (catches mistakes pre-ship). |

After setting these, the next deploy lights up analytics + flags.

---

## 3. Privacy posture (why this is a *security* item)

Kid-chat content, names, and custody details must never reach a third-party
analytics cloud. Enforced in code, not by convention:

- **Opaque IDs only** — events key on the account's `analytics_id` (a random
  UUID), never the `user_id` (which may be a name). If an account has no
  analytics_id, the event is **dropped** rather than risk sending a raw id.
- **Strict allowlist** (`app/analytics/events.py`) — only named events with named
  property keys are sent; values are coarse (counts, statuses, enums), never free
  text.
- **PII denylist** — keys like `message`, `content`, `kid_name`, `email`, `pin`,
  `transcript` can never be sent, whatever the call site passes. A guard test
  fails if any event's allowlist ever includes a denylisted key.
- **No autocapture / no session replay** — the server SDK doesn't do them; the
  iOS/web clients must be configured with autocapture and session replay OFF.
- **Right to be forgotten** — `DELETE /family/{user_id}` deletes the PostHog
  person + events (`app/analytics/deletion.py`).

## 4. Feature flags / kill switches

`app/analytics/flags.py`: `is_enabled(key, user_id, default)`. Resolution order:
1. Env override **`FLAG_<KEY>`** (e.g. `FLAG_KID_CHAT_DISABLED=1`) — a deploy-free
   kill switch.
2. PostHog local evaluation.
3. `default` (fails safe).

Create these flags in the PostHog console when ready: `kid_chat_disabled`,
`research_enabled`, `email_sync_enabled`. Experiments: once flags flow, an A/B
test is a PostHog console config — exposure events come for free.

## 5. Client integration — ✅ SHIPPED
- **iOS** (`mvp/MVP/Analytics.swift`): `posthog-ios` 3.64.2 (SPM) facade — `captureElementInteractions=false`,
  `sessionReplay=false`, no autocapture, **consent-gated** `startIfConsented()`, `identify(analytics_id)`
  after login. Full event coverage (2026-07-10): every-screen `screen_viewed` via a `View.trackScreen()`
  modifier, `chat_opened {agent_kind}`, kid+parent `voice_session_ended {duration_s}`.
- **Dashboard** (`parent-dashboard/src/analytics.ts`): `posthog-js` — autocapture + session replay OFF,
  `person_profiles: identified_only`, path-only pageviews, identify/reset wired into `AuthContext`.
- Both use the public project key (`POSTHOG_API_KEY` / `VITE_POSTHOG_KEY`); the dashboard key is baked
  at Docker build time.

## 6. Remaining (PostHog console)
Create the 3 feature flags — `kid_chat_disabled`, `research_enabled`, `email_sync_enabled` — in the
console (until then `flags.is_enabled` returns the code default; the `FLAG_<KEY>` env override already
works deploy-free). Configure Experiments once flags flow.
