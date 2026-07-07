# secrets/

Local-only secrets. **Everything in this directory is gitignored** (`secrets/`
+ `*.p8` in the root `.gitignore`) — never commit key material.

## APNs auth key (crisis-lock push notifications)
`AuthKey_<KEYID>.p8` — the token-based APNs key (Sandbox & Production, Team
Scoped). Used by `app/push` to sign the ES256 provider JWT.

On Railway, this is supplied via env vars (NOT the file):
- `APNS_KEY_ID`   — the 10-char key id (the `<KEYID>` in the filename)
- `APNS_TEAM_ID`  — Apple Developer team id
- `APNS_BUNDLE_ID`— app bundle id (used as `apns-topic`)
- `APNS_AUTH_KEY` — the full contents of the .p8 (paste the PEM; `\n` is tolerated)
- `APNS_USE_SANDBOX` — leave unset for TestFlight/App Store (production APNs)
