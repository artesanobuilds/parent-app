"""Registration-window watchlist (vertical expansion Phase 4, GTM Pillar 1).

The first deadline-driven push feature — it fails silently and unrecoverably,
so it's engineered as a notification-SLO product (see the plan's SRE-critic
redesign):

- `windows.py` — the pure timezone-aware due-time rules (notify BEFORE, never
  after; time-unknown dates notify the evening before, local).
- `worker.py` — a catch-up sweep every few minutes with due-TIME semantics
  (deliberately NOT email_sync's hour-equality gate, which skips work across
  deploys); durable-first delivery: notification row + fallback to-do commit
  BEFORE the push, and the push's outcome is recorded in the append-only log.

The product promise: for `manual` and `email` sourced dates, "we will never
let you miss it" must be keepable at 100%. `agent_research` dates are only
ever `estimated` and their T-7 nudge asks the parent to confirm.
"""
