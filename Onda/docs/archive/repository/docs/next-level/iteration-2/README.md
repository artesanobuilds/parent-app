# Iteration 2: understand them, practice how you show up

**Current recommended exploration.** Start with the [7-page illustrated PDF](iteration-2-strategy.pdf), [editable HTML](strategy-print.html) or [full strategy](strategy.md). This is a proposed experiment, not a validated intervention or launch decision. [Iteration 1](../README.md) remains preserved.

- [Runnable prototype](../../../experiments/next-level-iteration-2/README.md): difficult morning, shared joy, repair; optional capacity; private rehearsal; no-score reflection; minimal share preview.
- [Original before/after examples](examples.md), [adversarial cases](adversarial-cases.md), [research-prompt addendum](research-prompt-addendum.md) and [original full prompt](../research/parent_profile_deep_research_prompt.md).
- [Code audit](code-audit.md), [UX alternatives](ux-review.md), [profile safety](profile-safety.md), [child participation](child-participation.md).
- Full authored sources: [Good Inside and original practice proposals](research/parent_iteration2_good_inside.md), [competition/program precedents](research/parent_iteration2_competitors.md), [alliance/measures evidence](research/parent_iteration2_alliance_evidence.md). [Source hashes](research/source-manifest.json).
- [Parent practice loop diagram](diagrams/parent-practice-loop.svg), [privacy-boundary diagram](diagrams/privacy-boundary.svg).
- Screenshots: [parent adaptation desktop](screenshots/01-parent-adaptation-desktop.png), [no-score reflection](screenshots/02-no-score-reflection-desktop.png), [private-context boundary](screenshots/03-private-context-boundary-desktop.png), [repair mobile](screenshots/04-repair-mobile.png), [reflection mobile](screenshots/05-reflection-mobile.png).
- [Verification and limits](verification.md), [browser receipt](browser-verification.json), [PDF render receipt](render-verification.json), [BB worker manifest](bb-workers.md), [proposal ADR](../../adr/0002-parent-adaptation-reflection.md).

Rebuild print source with `python3 docs/next-level/iteration-2/build-print.py`, then `node docs/next-level/iteration-2/render-print.cjs`. Rendering uses local Chrome and playwright-core (module path can be set with `NEXT_LEVEL_PLAYWRIGHT`), loads local assets only, and blocks external requests. QA captures stay in `/tmp`. The iteration-2 ZIP lives beside the worktree at `../next-level-iteration-2.zip`, outside Git so the same large assets are not duplicated in repository history.

No composite score, diagnostic/attachment rating, questionnaire reproduction, recording, child session, real-data processing, connector or deployment. Current deterministic tests establish prototype rules only. An original instrument remains a separately reviewed measurement-development option, not an implemented feature.

Final code and safety reviews reflect the 16-test model snapshot and the resolved correction/export gaps. The consolidated verification records 14 executed browser checks separately from proposed clinical/red-team cases. Research recommendations and acceptance cases are not executed studies or clinical guarantees.
