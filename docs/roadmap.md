# Roadmap

Living list of next-up work. Order is a rough priority, not a commitment. Items move to `docs/history/NNN.md` when shipped.

## Onboarding & Profiling

- **Verify the demographic enrichment in Xcode.** End-to-end run on simulator after CoreSimulator update: walk the new "About you" step filling everything, then again skipping every field. Confirm `/profile/seed` POST body is correct and that the coaching agent weaves the new fields into responses.
- **Conversational parity check.** Open `/onboarding-chat` with a fresh `user_id` and confirm the agent organically asks about location, language, age range, employment, adults in household, and per-child pronouns/grade band. If it doesn't, tighten the system prompt.
- **Tier-2 sensitive fields.** Religion and household-income bracket were deferred. Both need product framing (privacy, trust, why we're asking) before adding. Cultural background was added; revisit in a follow-up to decide whether the others land in the structured form, in `/onboarding-chat`, or only get captured silently.
- **Per-child language.** Currently `primary_language` is parent-level only. Some bilingual households have different primary languages per child — consider adding `home_language` to `ChildProfile` if this comes up.
- **Co-parent capture.** When `household_structure ∈ {co-parenting, divorced, blended}`, prompt for co-parent name and dynamics in a follow-up step. Already supported in the model (`co_parenting`); not surfaced in the form.

## Personalization

- **Geo enrichment.** Server-side, derive `city` / `state` / `time_zone` from `postal_code` + `country` so the coaching agent can reference local context without us asking the user twice. No UI change needed.
- **Locale-aware coaching.** When `primary_language` is non-English, have the agent respond in that language (or offer to). Currently it just uses whatever language the user types in.
- **Time-zone aware reminders.** Once `time_zone` is known, schedule "morning routine" / "bedtime" tips relative to the user's local clock, not server clock.

## Backend / Infrastructure

- **DuckDB schema normalization (when needed).** Today profiles are JSON blobs in `user_data`. If we start running analytics ("how many parents reported `postal_code IN (...)`") or want fast filtering, write a migration that promotes core demographic + behavioral fields to columns in dedicated `parent_profiles` / `child_profiles` tables.
- **Service-account key rotation.** The current `sk-svcacct-*` key sits in `.env` and Railway. Document the rotation process and decide a cadence.
- **Pin discipline.** `langgraph-prebuilt` was pinned to 1.0.8 to dodge the `ExecutionInfo` mismatch. Re-evaluate when bumping `langgraph` to 1.1.x — at that point we can unpin and let pip pick the latest prebuilt.
- **`/data/export` reachability check.** `tools/sync-data.sh` failed earlier because production was returning 404. Add a friendlier preflight (curl `/health` first, give a clearer error on 4xx/5xx).
- **Railway auth refresh.** The CLI token expired silently; we discovered it only when `railway up` failed. Document re-auth in the deployment notes.

## iOS

- **Build environment.** This machine is missing the iOS 26.4 platform install — `xcodebuild` can't run a real build from CLI. Either install the platform or document that builds happen exclusively in Xcode.
- **Returning-user path.** `OnboardingView` welcome screen has a "Welcome back" branch that bypasses every demographic step. Decide whether returning users should be re-prompted for fields that didn't exist when they first onboarded (e.g., zip), or whether we surface a "Complete your profile" nudge in Settings instead.
- **Profile editing.** Today the only way to update profile data is to re-onboard or chat with the coaching agent. Add a Settings → Profile screen that lets users edit the structured fields directly.

## Content / Agent

- **`/onboarding-chat` finish signal.** The onboarding agent loops indefinitely — it never explicitly says "done." Decide on a completion heuristic (N tool calls, profile coverage threshold, user says "that's enough") and surface a "graduate to coaching" CTA in the iOS app.
- **Coaching agent guardrail.** The "weave into advice, never dump as raw data" instruction works most of the time, but worth a regression script: ask questions that tempt it to echo zip/age, confirm it doesn't.

## Out of scope (intentionally not on the roadmap)

- Switching profile storage off DuckDB.
- Rebuilding the form as a single long screen — the multi-step flow is on purpose.
- Religion as a top-level field (sensitivity vs. value tradeoff is unfavorable right now).
