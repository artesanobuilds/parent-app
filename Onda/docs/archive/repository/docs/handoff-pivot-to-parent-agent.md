# HANDOFF: pivot the MVP parent app into "Parent Agent"
Generated: 2026-09-26 · Session focus: capture all context, then hand the project to bb

## 1. Goal
Decide, with full context, how to pivot away from the MVP parent app as built (closed
beta, Feb–Aug 2026) into whatever comes next. The bb project "Parent Agent" is where that
decision gets made and executed. Nothing about the new direction is decided yet.

## 2. Why
Miguel is stepping away from the MVP as a product and wants the next project to start
from everything learned here rather than from scratch. bb threads cannot see Claude Code's
memory or transcripts, so the whole record was written into the repo first.

## 3. Current state
- DONE: `docs/parent-app-context.md`, the full record (architecture, product, timeline,
  lessons, operations, GTM + research, open work). Sourced from 75 auto-memory notes, the
  repo docs, 146 commits, and a code inventory. Claims are as-of 2026-08-22 at the latest.
- DONE: `.bb/AGENTS.md` with the rules every bb thread in this project must follow.
- DONE: the Aug-2026 parent-planning-behavior research, previously untracked, is committed
  under `docs/GTM/research/2026-08-parent-planning-behavior/` (report, sources, data CSVs,
  raw source reports, build scripts). Its verdicts (section 6 of the context doc) are the
  last recorded plan and nothing from it was ever built.
- DONE: prod backend is live and stable at the 2026-08-22 deploy; iOS 1.93 (107) is
  committed. Whether 1.93 reached TestFlight is not recorded; 1.90 (104) did.
- NOT STARTED: the pivot decision itself. No ADR exists for it. `docs/adr/` does not
  exist yet.
- NOT STARTED: any action on the research's ACT / TEST-FIRST lists.

## 4. Key decisions and why (recorded before the pivot; see context doc for detail)
- Solo-first: the product must work for one parent alone; the second parent joins by
  share link / calendar invite, never an account. Second-parent activation was the
  structural flaw the roast found.
- Kids' voice companion deferred out of beta (2026-07-15) and recommended for a full cut
  by the Aug research: zero demand evidence, COPPA/FTC exposure, ~4K LOC.
- Coach is not the retention engine; the ingestion loop + registration-window watchlist
  is. Coach must be zero-retention because transcripts are discoverable in custody court.
- Beta is free; the paywall is a placeholder that charges nothing.
- Price test range $99–149/family/yr, not $199.
- Community board + DMs were replaced by private Circle conversations (migration v21).

## 5. Traps and dead ends
- The working tree also carries `mvp-backend/data/mvp.parquet` modified (local drift of
  a tracked seed file). It was deliberately NOT committed. Do not commit it without the
  cleanup in the context doc, and never let it ride a deploy.
- `.codex/config.toml` is untracked and holds a live Grafana service-account token in
  plaintext. It was NOT committed. It should be gitignored and the token rotated.
- `AGENTS.md` at the repo root is a byte-for-byte copy of `CLAUDE.md`; it was committed so
  Codex and bb threads see the conventions. Keep the two identical or symlink one.
- There is no CI and no GitHub remote. Nothing runs on push.
- Prod has real families. `DELETE /family`, `railway up`, migrations and bulk exports all
  need Miguel's explicit say-so in the thread.
- The memory said 1.89 (103) "never shipped to TestFlight" and 1.90 (104) was owed; later
  commits went to 1.93 (107). Verify in App Store Connect before assuming what testers run.
- Google OAuth restricted scope is unverified: the 100-user cap is per GCP project and
  non-resettable. Do not put Gmail sign-in on any critical path.

## 6. Relevant files and pointers
- `docs/parent-app-context.md` — everything; read it first.
- `.bb/AGENTS.md` — the rules for this bb project.
- `CLAUDE.md` / `AGENTS.md` — engineering conventions that cost real bugs.
- `docs/GTM/gtm-strategy.md` — canonical strategy (v2, 2026-07-07).
- `docs/GTM/research/2026-08-parent-planning-behavior/report.md` — the research; §4 is
  the red team, §5 the ACT list. `raw/S2-feature-fit-verdict.md` is the per-feature table.
- `docs/GTM/mvp-idea-roast.md` — the 5-persona council verdict (RESHAPE).
- `pitch/narrative.md` — the investor strategy kernel and four refusals.
- `docs/roadmap.md` — every open item as of Aug 2026.
- `docs/history/deploy-runbook.md`, `docs/history/prod-backups.md` — if prod is touched.
- `mvp-backend/app/cos/verticals.py`, `app/cos/lifecycle.py`, `app/agent.py` — the
  planning core most likely to survive any pivot.

## 7. Open work, as state and ordering
- The pivot has no framing yet: which of the three assets (planning agent core, coach +
  content library, kid companion) carries forward is undecided. The research argues for
  the planning core plus capture (manual add, flyer photo, inbound email address) and
  against the companion.
- A decision record (`docs/adr/0001-…`) is the natural first artifact; nothing depends on
  it except everything after it.
- If any code is kept live, the TestFlight state of 1.93 and the `.codex` token rotation
  come before further beta activity.
- Whether prod stays up for the current beta families during the pivot is not decided.

## 8. Open questions for Miguel
- Is "Parent Agent" a rename of this product, a new product on the same backend, or a
  fresh codebase that borrows from this one?
- Do the current beta families keep using the app during the pivot, or is the beta closed?
- Does the Aug research's ACT list stand as the starting hypothesis, or is the pivot
  broader than "simplify MVP"?
