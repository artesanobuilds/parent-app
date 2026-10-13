# Next Level deliverables

A local exploration, not a production rollout. Branch `next-level` from `5e5caca`; original live-product checkout untouched.

Start with [strategy.md](strategy.md). Inspect [the prototype](../../experiments/next-level/README.md), then [verification.md](verification.md) for passed versus unrun checks and limitations.

- [code-audit.md](code-audit.md): current profile/onboarding, mutation, tenant and retention evidence; source references; synthetic probe.
- [ux-review.md](ux-review.md): three product shapes and profile-versus-summary-versus-generic-memory tests.
- [profile-safety.md](profile-safety.md): proposed reviewed-note schema, lifecycle, retention/consent, threat model and evals.
- [child-handoff.md](child-handoff.md): actual parent-phone handoff, PIN/session/crisis boundaries; tablet, isolated mode, separate app and co-use comparison.
- [architecture.md](architecture.md): Mermaid architecture and UX/lifecycle diagrams; [PNG architecture](diagrams/architecture.png) and [PNG UX loop](diagrams/ux-loop.png), with editable SVG sources.
- [bb-workers.md](bb-workers.md): exact project/environment/thread/provider manifest.
- [ADR](../adr/0001-next-level-exploration.md): proposed experiment decision and consequences.

Rendered screenshots: [conversation desktop](screenshots/01-conversation-desktop.png), [experiment outcome](screenshots/02-experiment-outcome-desktop.png), [understanding desktop](screenshots/03-understanding-desktop.png), [sharing desktop](screenshots/04-share-preview-desktop.png), [conversation mobile](screenshots/05-conversation-mobile.png), [understanding mobile](screenshots/06-understanding-mobile.png), [sharing mobile](screenshots/07-share-preview-mobile.png).

External research is owned by the parent research team. Place final current-market/science/auth/integration brief in `external-research.md` and the reusable child-profile research prompt in `child-understanding-research-prompt.md` when transferred. Those deliverables are not fabricated or duplicated here. Current strategies cite supplied research as preliminary rather than independently verified.

No push, merge, deploy, secrets, production migrations/data changes, real child/health record transmission or active connector. Local prototype uses no accounts or model calls. Scope is parent-led; independent child use is deferred pending value and safety evidence.

Editorial precedence: worker retention defaults (UX 30-day proposal versus safety short-lived proposal) are alternatives, not an adopted retention policy. Primary-store deletion can return success with checkpoint/snapshot cleanup pending per code-audit.md; do not infer universal immediate erasure from profile-safety.md’s proposed coverage. The strategy favors minimal approved notes and explicit lifecycle decisions before real data.
