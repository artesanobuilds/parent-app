# Parent App (MVP) — Engineering Conventions

Closed-beta "MVP" parenting app: FastAPI + DuckDB backend (Railway), SwiftUI iOS app
(`mvp/`), Vite/React parent-dashboard + admin CMS (`mvp-backend/parent-dashboard`,
`mvp-backend/cms`). Deep context (architecture, debugging notes, project state) lives in
the auto-memory `MEMORY.md` — read it for specifics.

This file is the short list of conventions whose violation has caused **real user-facing
bugs**. Each rule earns its place. Follow them.

## Conventions

### Networking / config
- **One source of truth for the server URL.** Resolve the base URL ONLY through
  `ServerConfiguration` (`.defaultURL` / `.baseURL`). NEVER hardcode a fallback like
  `?? "http://127.0.0.1:8904"`. A localhost fallback works in the simulator but silently
  fails on a real-device fresh install — it posts to the phone's own localhost. (This
  destroyed onboarding data for two beta users.) Enforced by `tests/test_ios_baseurl_guard.py`.

### Mutations & persistence
- **User-state writes are durable + verified, never fire-and-forget.** Persist the intent
  locally, retry until the server confirms 2xx, surface failures. Don't navigate away
  assuming success. (The onboarding seed silently lost a parent's family this way.)
- **After a mutation, the source-of-truth view re-fetches.** A view that renders server
  data and sits alongside an editor must refresh when control returns (sheet `onDismiss`
  → bump a token → `.task(id:)`). A one-shot `.task` goes stale — a deleted/edited kid
  kept showing on Home until relaunch.
- **Deletes cascade.** Removing an entity removes every row that references it — mirror
  `duckdb_storage.delete_family` / `delete_kid_data`. Orphans resurrect the "deleted" thing.
- **Key by stable IDs, not editable display names.** A name used as a dict key diverges
  from its value on rename and risks collisions.

### Cross-surface contracts
- A change to any request/response shape needs a matching change on **all three surfaces**
  (iOS, web dashboard, backend). The iOS app sends specific shapes (e.g. kid `age` as a
  STRING, `adults_in_household` as int) — backend must tolerate them. Locked by
  `tests/test_onboarding_seed_contract.py`.
- Onboarding has TWO paths (form + chat) that must stay in sync — see memory
  `patterns_onboarding_parity`.
- iOS Codable is strict: one type mismatch empties a whole list. DuckDB `DOUBLE` → Swift
  `Double?` (not `Int?`). See memory `debugging_ios_codable_backend_contract`.

## Verify before you commit
- Backend: `cd mvp-backend && source .venv/bin/activate && pytest -q`
- iOS: `xcodebuild -project mvp/MVP.xcodeproj -scheme MVP -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build`
  (SourceKit "Cannot find type X" / "no member" diagnostics across files are KNOWN false
  positives — `xcodebuild` is the source of truth.)
- Web: `cd mvp-backend/parent-dashboard && npx tsc --noEmit && npm run build`
- For networking / onboarding / first-launch changes, verify the **release/prod config and
  a fresh-install path** — not just DEBUG/simulator, where localhost masks the bug.

## Prod debugging playbook (closed beta)
- Read any user's live profile: `POST /auth/issue-token {user_id}` → `GET /profile` (Bearer).
  Auth is rate-limited (`RATE_LIMIT_AUTH_PER_HOUR`, 60/IP/hr).
- Clean up a THROWAWAY test user: `DELETE /family/{user_id}`. Never delete real users' data.
- Don't bulk `/data/export` (mass PII) — read only the single user you need.
- Prod host: `https://mvp-backend-production-8678.up.railway.app`.

## Deploy (Railway)
- `cd mvp-backend && railway up --detach`. **Prod deploys need explicit user authorization
  each time.**
- `railway up` uploads the working tree — never let user-state `data/*.parquet` get baked
  into the image (they're excluded in `.dockerignore`; see memory
  `debugging_railway_parquet_deploy_hazard`).
- The web dashboard + CMS build inside the Dockerfile and ship with every backend deploy;
  iOS ships via TestFlight.
