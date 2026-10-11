# Family deletion and reset invariants

Deletion/reset closes family admission and drains active and queued harness runs
before opening the cascade transaction. The route keeps that fence while its
synchronous cleanup runs, including after request cancellation. Parent,
onboarding, and kid surfaces must all use the ownership wrapper before claiming
whole-family harness coverage. Unowned external workflows are outside this gate.

Migration 25 adds two durable cleanup obligations to `agent_family_fences`:
`checkpoint_purge_pending` and `snapshot_purge_pending`. Both block new scoped
runs and fenced profile/job writes. Permanent deletion also sets `deleted`;
a racing reset cannot clear that tombstone. Reset increments the generation but
retains account, identity, token, and legal-acceptance rows.

Checkpoint cleanup includes SQLite `checkpoints` and orphan `writes` rows. It
re-enumerates matching thread IDs after deletion before clearing the pending
flag. The clear is conditional on the generation seen before cleanup. A failed
or incomplete sweep remains pending and is retried at startup and every thirty
seconds. No new HTTP response fields are introduced.

Snapshot cleanup uses strict export, reopens every exported parquet, verifies
absence of swept user rows, and verifies required parent/child joins. Only then
does it clear `snapshot_purge_pending` and publish the updated fence snapshot.
Failures keep the obligation durable. Startup reapplies a pending reset cascade
before restoring in-memory profiles, so a crash between reset and snapshot
refresh cannot resurrect the old profile; reset-retained identity survives.

## Startup data cleanup: backup required

The DDL is additive, but startup also **deletes orphan records** after all
bootstrap tables are loaded. This is intentional recovery from partial exports
where a fresh parent snapshot and a stale child snapshot were mixed. The exact
scope is:

| Deleted row | Condition |
| --- | --- |
| `kid_messages` | `agent_id` has no matching `kid_agent_configs.id` |
| `window_notifications` | `window_id` has no matching `registration_windows.id` |
| `circle_messages` | `conversation_id` has no matching `circle_conversations.id` |
| `circle_participants` | `conversation_id` has no matching `circle_conversations.id` |

These are required ownership references, not optional links. Valid child rows
for other families remain unchanged. This cleanup runs on bootstrap regardless
of whether a family currently has a pending obligation. It therefore removes
pre-existing orphans too; it is not a read-only schema rollout.

Before an authorized production rollout, back up DuckDB with its WAL and all
affected parent/child tables, family-fence state, and SQLite checkpoints with
its WAL/SHM under the deployment runbook. Rehearse restoration on disposable
storage. Reverting application code does not restore deleted orphan rows.

`tests/test_family_cleanup_fencing.py` covers active/queued writer drain,
request-cancellation fencing, silent checkpoint purge failure and retry,
orphan checkpoint writes, generation-conditional clearing, reset crash/reboot,
partial child-snapshot failure, permanent-delete versus reset, and preservation
of valid other-family rows across the four startup joins.
