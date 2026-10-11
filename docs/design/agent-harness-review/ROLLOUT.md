# Harness rollout and operator handoff

This guide supplements [the production deployment runbook](../../history/deploy-runbook.md). The PR stack is implementation work, not a deployment record. Production deployment requires Miguel's explicit authorization for that deployment. Merge order and rollout order are separate decisions.

## What earlier deployments taught us

The earlier Claude Code deployment notes and checked-in history describe three failures this rollout must avoid:

- **Empty databases hid migration failures.** An index creation following an UPDATE in the same DuckDB migration transaction crash-looped the populated production database. Rehearse the complete additive migration chain against a populated synthetic previous-version database, then reopen it and check rows and version stamps. Fresh-database tests alone are insufficient.
- **Local state entered deployment images.** Railway uploads the working directory; git tracking is not a protection. Check both ignore files and the Docker build context. New receipts, generation fences, checkpoints, WAL files and snapshots are user state. Never ship them as seed content.
- **Old clients kept calling removed endpoints.** This stack preserves the public OpenAPI shapes and SSE envelopes. The deployed mobile build requires no matching API update. Do not combine rollout with unrelated endpoint removals or model/framework upgrades.

Historical notes also describe an obsolete entrypoint that removed the database and replaced smaller seed files. The current entrypoint preserves DuckDB and its WAL and copies only missing seed files. Follow current source and the checked-in runbook when notes disagree. Do not publish raw coding-agent session transcripts: they can contain family data and credentials.

## Before requesting deployment

1. Merge the stack in order, reviewing the behavioral changes separately from extractions. Keep each predecessor branch until its dependent PR is retargeted.
2. Run the complete backend suite, the public contract suite in both runtime modes, migration/restart/deletion fault tests, dashboard TypeScript/build checks, and the prescribed iOS build when that simulator is available. The implementation session passed a generic simulator SDK build; a named simulator runtime was unavailable.
3. Review additive migrations 25 and 26, the changed export exclusions, and startup orphan cleanup. The DDL is additive, but recovery removes child rows whose required parent no longer exists (kid messages, window notifications and Circle children). Include those affected tables in the approved backup scope and verify valid other-family rows survive. Use populated synthetic fixtures; do not copy a real family into an agent's workspace.
4. Record the exact commit, current migration version, current rollout switches and expected smoke results. Set latency/error/cost thresholds from measured baseline data. Offline fake-provider tests do not establish production model quality or latency.
5. Under the separately authorized deployment, back up the affected state with the existing per-file backup script, store it in ignored snapshots, and commit the backup ledger entry. Never use bulk `/data/export`. Include the current checkpoint database in the approved backup scope if recovery may require it; a parquet-only snapshot does not cover conversation checkpoints.

## Controlled rollout

Keep switches off on the initial additive schema rollout. Enable a single shared surface in a synthetic staging environment first, then in an explicitly authorized beta rollout. Select the policy once when admitting each turn. Do not run two mutating agents against the same family's state as a shadow comparison.

Use the technical design and implementation status for the exact flag matrix. The named-COS-conversation correction is a separate switch from shared execution. Toggle it independently so an orchestration rollback does not silently redirect conversations.

For each enabled surface verify: authenticated tenant routing, legacy history reopening, a profile update surviving restart, a local planning mutation recovered from a saved receipt, a failed persistence operation withholding successful completion, and disconnect behavior. For kid surfaces additionally verify pre-model moderation, buffered output moderation, crisis interruption and disabled-agent behavior. For research and warmup verify cancellation, expired attempts, restart recovery and late-write rejection.

Check Railway's active deployment ID and boot logs, then health and the runbook's before/after content counts. A successful upload message alone does not prove the new image is serving. Use only designated throwaway users for mutation smoke tests, and clean up those users after verification.

## Rollback boundaries

Disable a surface switch for newly admitted turns and let existing runs drain through their original implementation. Keep additive tables/columns. Once receipts and family generation fences are in use, retain those guarantees on fallback paths; do not deploy an older binary that bypasses them while accepting writes.

A reverted image does not reverse migrations or restore deleted data. Follow the runbook's preference for a forward fix, then code rollback, with an approved data restore only when necessary. Do not drop stale parquet files onto the volume: bootstrap can resurrect records that were deleted from the database.

## Known operating limits

Conversation ownership is per process and event loop. The supported deployment remains one application process. Multiple replicas require distributed ownership before enabling overlapping writers.

Canceling a coroutine does not kill synchronous work already running in a Python thread. Interactive turns conservatively retain ownership while outstanding work drains. Background attempts have bounded dispatch and fenced writes; those controls do not constitute process termination or a guarantee that provider billing stops instantly.

DuckDB business commands and their receipts commit together. SQLite graph checkpoints remain a separate transaction domain. Recovery uses a stable checkpointed tool-call ID to restore a known result; it does not infer that two independent model calls with similar arguments are the same operation.

Legacy checkpoint keys can be ambiguous for reserved or delimiter-containing
identities. Cleanup fails closed and leaves a pending obligation in those cases.
Resolve ownership explicitly before clearing it; do not widen a prefix delete.
Use consistent database backup APIs or an approved quiescent-volume procedure
for DuckDB/SQLite recovery. Copying a live database file alone is not a verified
backup, and the existing parquet script does not back up SQLite checkpoints.
