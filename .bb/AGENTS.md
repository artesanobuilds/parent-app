# Parent Agent (formerly "MVP" parent app) — rules for every bb thread

This repo holds the closed-beta parenting app that ran Feb–Aug 2026 (FastAPI + DuckDB
backend on Railway, SwiftUI iOS app in `mvp/`, React parent dashboard + admin CMS). As of
2026-09-26 the project is **pivoting** away from the MVP as built. The pivot itself is
not decided; the bb project "Parent Agent" exists to decide it with full context.

## Read first, in this order
1. `docs/parent-app-context.md` — the complete record of what was built, why, what
   broke, what shipped, and what the research says. It replaces the Claude Code
   auto-memory that bb cannot see. Treat it as context to verify, not gospel.
2. `CLAUDE.md` (identical copy: `AGENTS.md`) — the engineering conventions whose
   violation caused real user-facing bugs. They still apply to any code change here.
3. `docs/handoff-pivot-to-parent-agent.md` — the state of the hand-off session and the
   open questions for the pivot.

## Hard rules
- **Prod is live with real beta families.** Never deploy (`railway up`), run a migration,
  delete a user, or bulk-export data without Miguel saying so in that thread. Follow
  `docs/history/deploy-runbook.md` if a deploy is ever authorized.
- **Never commit** `mvp-backend/data/*.parquet` other than the five seed files the
  `.gitignore` whitelists, nor `snapshots/`, nor `.codex/` (it holds a live Grafana
  service-account token in plaintext). `git add` by path, never `-A`.
- Secrets live in `mvp-backend/.env` (gitignored) and `~/.zshenv`. Reference them by
  name; never print their values.
- The app is called **MVP** in code, TestFlight, and docs; do not rename it in passing.
- Decisions about the pivot (what to keep, what to kill, new positioning) go in
  `docs/adr/NNNN-title.md`: context, decision, consequences. Never edit an old ADR;
  supersede it.
- Answer in short, plain English. Show Miguel command output he cannot see.

## Verify before committing code
- Backend: `cd mvp-backend && source .venv/bin/activate && pytest -q`
- Web: `cd mvp-backend/parent-dashboard && npx tsc --noEmit && npm run build`
- iOS: `xcodebuild -project mvp/MVP.xcodeproj -scheme MVP -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build`
  (SourceKit cross-file "cannot find type" errors are false positives; xcodebuild is truth.)
