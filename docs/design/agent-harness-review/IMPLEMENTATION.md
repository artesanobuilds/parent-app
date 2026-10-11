# Harness refactor: implementation and evidence

The [technical design](README.md) and [illustrated PDF](MVP-Agent-Harness-Technical-Design.pdf) describe the architectural proposal. This page records the implementation separately from production rollout. The user elected to implement the entire seven-PR plan; the recommendation to pause after PR3 remains a rollout checkpoint, not an implementation limit.

## What changed

The backend retains FastAPI, DeepAgents/LangGraph, DuckDB, and SQLite checkpoints. Existing endpoints and mobile request/response shapes remain the compatibility boundary. A shared execution service owns conversation admission, repair, trusted run context, event filtering, finalization, and disconnect draining. Text, voice, onboarding, and kid adapters keep their surface-specific behavior.

Local profile/planning mutations use a durable operation receipt keyed by the checkpointed tool-call ID. Domain writes and receipts share a DuckDB transaction. Reconciliation restores a known committed tool result before generic dangling-call repair. A repeated client message or a new model-generated operation is not automatically deduplicated.

Deletion and reset first fence new admissions and drain active writers. Database generation fences reject stale commands. Checkpoint and snapshot cleanup obligations survive interruption and retry; an incomplete purge must not admit a new graph against old family context.

Research and warmup retain their existing public states. Internal attempt tokens, deadlines, dispatch guards, periodic reaping, and fenced commits prevent expired attempts from publishing over newer work. Synchronous threads remain cooperative; hard process termination is outside this change.

The COS routing correction is independently gated. It captures the active named conversation once at admission and uses that same checkpoint key in either execution implementation. It does not merge historical transcripts or alter `/cos/messages` projection semantics.

Kid moderation stays outside the model execution stream and retains its precheck, buffering, output check and persistence order. Compiled graph caches are bounded; eviction discards reconstructible graph objects, not durable history.

## Review stack

Each PR is based on its predecessor. Merge in order and retarget the next PR to `master` after its predecessor merges. Keep predecessor branches until dependent PRs are retargeted.

| Slice | Scope | Review |
|---|---|---|
| 0 | Contract baseline, critique, diagrams and design | [PR #1](https://github.com/artesanobuilds/parent-app/pull/1) |
| 1 | Transport adapters and dependency binding | [PR #2](https://github.com/artesanobuilds/parent-app/pull/2) |
| 2 | Parent execution and conversation ownership | [PR #3](https://github.com/artesanobuilds/parent-app/pull/3) |
| 3 | Durable effects, transcripts and deletion | [PR #4](https://github.com/artesanobuilds/parent-app/pull/4) |
| 4 | Selected named-conversation routing | [PR #5](https://github.com/artesanobuilds/parent-app/pull/5) |
| 5 | Bounded research and warmup jobs | [PR #6](https://github.com/artesanobuilds/parent-app/pull/6) |
| 6 | Specialized policies, bounded caches and regression scenarios | [PR #7](https://github.com/artesanobuilds/parent-app/pull/7) |

## Switches and rollback

All switches are server-side and default to off:

| Setting | Effect |
|---|---|
| `MVP_SHARED_RUNTIME_CHAT` | Shared parent text execution |
| `MVP_SHARED_RUNTIME_COS` | Shared planning text execution |
| `MVP_SHARED_RUNTIME_PARENT_VOICE` | Shared parent voice execution |
| `MVP_SHARED_RUNTIME_ONBOARDING` | Shared onboarding execution |
| `MVP_SHARED_RUNTIME_KID_TEXT` | Shared graph execution below kid text moderation |
| `MVP_SHARED_RUNTIME_KID_VOICE` | Shared graph execution below kid voice moderation |
| `MVP_COS_ACTIVE_CONVERSATION` | Separate selected-conversation behavior correction |

Set a switch to `1`, `true`, or `yes` to enable it. Ownership, durable commands,
cleanup fences, and moderation remain active on the fallback paths.
`MVP_AGENT_CACHE_SIZE` is a separate positive integer setting, default **256
entries per graph cache**.

The durable command service and deletion fences remain active on fallback orchestration paths. Disabling shared execution is not permission to bypass receipts or generation checks. See the [rollout guide](ROLLOUT.md) for deployment order, backup scope, migration rehearsal and rollback boundaries.

## Evidence and its limits

The complete backend suite passed **792 tests, 45 skipped** with shared runtime
switches disabled and **792 tests, 45 skipped** with all six enabled. No expected
failures remain. The **74 public contract cases** cover both modes. Five existing
library/schema deprecation warnings remain. Application and test files in the final PR stack were compared byte-for-byte
with the combined validation tree before publication.

The intermediate merge points also passed their full backend suites: PR #4
(durability) **715 passed, 45 skipped**, with only the explicitly deferred routing
case expected to fail; PR #5 (routing) **723 passed, 45 skipped**; PR #6 (jobs)
**740 passed, 45 skipped**. Earlier contract/adaptor/execution evidence is recorded
in each PR description.

Cross-review reproduced and fixed two additional failures: a family cancellation
could send parent voice a success terminator without finalized history, and a
concurrent legacy snapshot could overwrite a newly committed transcript/profile
before its cache refresh. Forced-interleaving tests cover both windows.

From the backend with its development environment activated:

```sh
python tools/test-harness-offline.py
python tools/test-harness-offline.py --shared
```

The runner disables dotenv loading, substitutes offline provider keys, selects
temporary database/checkpoint paths, and blocks Python outbound connections.
It prints the location of the full log. Additional arguments go to pytest.
The public contract fixtures themselves run in both execution modes.

All backend verification uses disposable local databases/checkpoints and fake providers, with outbound sockets blocked. No production migration, deployment, family mutation or vendor execution was performed. Public OpenAPI and SSE contract fixtures verify mobile-facing compatibility. The final dashboard TypeScript check and production build passed (existing font-path and bundle-size warnings remain). Design-token lint passed. The iOS generic simulator SDK build passed; the prescribed named iPhone 17 Pro simulator runtime was unavailable.

The parent scenario suite is deterministic regression evidence for orchestration and tool boundaries. It does not establish live model quality, clinical appropriateness, latency, cost reduction or product outcomes. Prompts, model selection and framework versions were preserved; those changes need separately measured evaluations.

Legacy checkpoint IDs contain unescaped identity segments. Automatic cleanup refuses ambiguous reserved or overlapping identities and leaves a durable pending obligation for ownership repair. This preserves other families' records; it is not a migration to a new checkpoint-key format.

## Interview discussion

A useful way to explain this work is through three concrete failure windows:

1. **A tool commits, then the checkpoint fails.** Transactional receipts recover the known effect using its original tool-call identity instead of rerunning a new plan and hoping it is equivalent.
2. **A client disconnects while a synchronous tool runs.** The harness stops delivery but retains conversation ownership until outstanding work drains. Cancellation of an await is not proof that the write stopped.
3. **Deletion races execution or stale snapshots.** Admission fencing, generation checks and durable cleanup obligations cover different boundaries. Deleting the database row alone cannot erase a late checkpoint or prevent bootstrap from restoring an old parquet row.

These are implemented reliability mechanisms under offline tests, not claims of a production rollout. The main tradeoff is retaining the current single-process architecture while making its ownership and persistence guarantees explicit. Distributed leases, killable worker processes and a storage-engine migration remain separate decisions.
