# Next Level deliverables

**Recommended current version: [iteration 2, parent adaptation](iteration-2/README.md).** Start with its [7-page illustrated PDF](iteration-2/iteration-2-strategy.pdf), [strategy](iteration-2/strategy.md) and [updated research prompt](iteration-2/research-prompt-addendum.md). The original iteration-1 research, prototype and PDF below remain preserved.

A local exploration, not a production rollout. Branch `next-level` from `5e5caca`; original live-product checkout untouched.

Start with the illustrated **[strategy PDF](next-level-strategy.pdf)** or **[editable print HTML](strategy-print.html)**, then [strategy.md](strategy.md). Inspect [the prototype](../../experiments/next-level/README.md), then [verification.md](verification.md) for passed versus unrun checks and limitations.

- [code-audit.md](code-audit.md): current profile/onboarding, mutation, tenant and retention evidence; source references; synthetic probe.
- [ux-review.md](ux-review.md): three product shapes and profile-versus-summary-versus-generic-memory tests.
- [profile-safety.md](profile-safety.md): proposed reviewed-note schema, lifecycle, retention/consent, threat model and evals.
- [child-handoff.md](child-handoff.md): actual parent-phone handoff, PIN/session/crisis boundaries; tablet, isolated mode, separate app and co-use comparison.
- [architecture.md](architecture.md): Mermaid architecture and UX/lifecycle diagrams; [PNG architecture](diagrams/architecture.png) and [PNG UX loop](diagrams/ux-loop.png), with editable SVG sources.
- [bb-workers.md](bb-workers.md): exact project/environment/thread/provider manifest.
- [ADR](../adr/0001-next-level-exploration.md): proposed experiment decision and consequences.

Rendered screenshots: [conversation desktop](screenshots/01-conversation-desktop.png), [experiment outcome](screenshots/02-experiment-outcome-desktop.png), [understanding desktop](screenshots/03-understanding-desktop.png), [sharing desktop](screenshots/04-share-preview-desktop.png), [conversation mobile](screenshots/05-conversation-mobile.png), [understanding mobile](screenshots/06-understanding-mobile.png), [sharing mobile](screenshots/07-share-preview-mobile.png).

Final research is saved under [research/README.md](research/README.md), including the **[full copyable research prompt](research/parent_profile_deep_research_prompt.md)**. Six source documents retain all qualifications and links. [Source hashes](research/source-manifest.json) pin the local copies. [Render checks](render-verification.json) record page/image/overflow checks.

Rebuild the editable document with `python3 docs/next-level/build-strategy.py`, then render using `node docs/next-level/render-strategy.cjs` (host Chrome and playwright-core path, configurable via `NEXT_LEVEL_PLAYWRIGHT`). No remote fonts or images are used. The complete ZIP is a download bundle beside the worktree at `../next-level-deliverables.zip`, outside the Git tree to avoid duplicating all generated assets; its verified path is recorded at final delivery.

No push, merge, deploy, secrets, production migrations/data changes, real child/health record transmission or active connector. Local prototype uses no accounts or model calls. Scope is parent-led; independent child use is deferred pending value and safety evidence.

Editorial precedence: worker retention defaults (UX 30-day proposal versus safety short-lived proposal) are alternatives, not an adopted retention policy. Primary-store deletion can return success with checkpoint/snapshot cleanup pending per code-audit.md; do not infer universal immediate erasure from profile-safety.md’s proposed coverage. The strategy favors minimal approved notes and explicit lifecycle decisions before real data.
