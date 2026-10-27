# MVP retirement punch list · future execution only

Status: planning only, 2026-10-27. Miguel explicitly deferred takedown. Do not execute shutdown actions from this checklist without separate authorization. Preserve legacy app identity, histories and family data while planning.

## Repo evidence and verification gaps

| Surface | Repository evidence | Still verify in owner account |
|---|---|---|
| iOS distribution | SwiftUI `mvp/MVP.xcodeproj`; historical context records MVP.MVParent and TestFlight | Actual App Store listing(s), bundle IDs, availability, shipped builds, TestFlight groups, review status |
| Hosting | `mvp-backend/railway.toml`, Dockerfile; root instructions identify Railway production backend | Actual projects/services/environments, attached volumes, bucket, deploy triggers, billing owner, current backups |
| Web | Dashboard and CMS built in backend Dockerfile | Public URLs, domains, DNS/CDN, share links and support routes |
| Data | DuckDB, user-state parquets, SQLite agent checkpoints, blobs, provider integrations described in context | Current data locations, volume/bucket snapshots, access/retention obligations, secure export and restore process |
| Dependencies | Setup guides cover OpenAI, Tavily, ElevenLabs/LiveKit, Apple/APNs, Google OAuth, PostHog, Sentry, Grafana; code/context reference Slack, SMTP and object storage | Which remain active/paid, credentials/webhooks, contracts, ownership, linked apps |
| Customer billing | Historical handoff says free beta and placeholder paywall; Stripe vs StoreKit undecided | Actual purchases, subscriptions, trial obligations, refunds and renewal paths; do not assume no charges today |

Evidence is repo-only, not a live provider audit. See original [context](../../docs/parent-app-context.md), [setup index](../../setup/README.md), [deploy runbook](../../docs/history/deploy-runbook.md) and [backup ledger](../../docs/history/prod-backups.md). Do not put private account exports or credentials in Git.

## Before selecting a shutdown date

- [ ] Assign owner and approver for each surface; verify actual store/hosting/domain/billing inventories.
- [ ] Inventory active users and affected flows in an appropriately restricted system, including old app versions and integrations. Do not copy family records into Onda docs.
- [ ] Decide whether exports, migration help, refunds, retention or deletion are offered; review applicable commitments and content/partnership rights.
- [ ] Establish secure exports/backups of database, checkpoints, user-state files and blobs; test restoration in isolation; record custody and retention deadlines without embedding the data.
- [ ] Draft communication and support plan, notice timing, in-app/web messages, support contact and escalation route. Review before sending anything.
- [ ] Inventory provider subscriptions, renewal dates, quotas, credentials and service dependencies; distinguish shared services from MVP-only services.
- [ ] Map DNS, certificates, OAuth redirects, APNs, deep/share links, monitoring, alerts, scheduled jobs and webhooks so cancellation order is deliberate.

## Staged execution after separate authorization

- [ ] Approve schedule, backup/restore checkpoints, go/no-go criteria and rollback owner before each irreversible step.
- [ ] Deliver approved notices and export window; verify access and support readiness.
- [ ] Decide new-signup and renewal restrictions, store availability and TestFlight handling; account for already installed apps.
- [ ] Stage hosting/API/web shutdown with an intentional user-facing retirement response where feasible; verify old clients do not silently lose writes.
- [ ] Cancel or retain billing/services deliberately, confirm refunds and stop unwanted renewals; preserve necessary support and exports.
- [ ] Apply the approved data retention/deletion plan across primary stores, snapshots, checkpoints, blobs, processors and backups. Verify completion and exceptions.
- [ ] Remove MVP-only OAuth grants, credentials, jobs, hooks and DNS only after dependency checks; retain domains if needed for safety/support.
- [ ] Verify listing availability, URLs, client behavior, charges, alerts and data disposition. Record receipts and residual obligations.
- [ ] Test rollback before irreversible deletion; after deletion, document what cannot be restored. Keep a final operational record and support contact.

Mirrored planning destination: [private Space retirement checklist](https://chatgpt.com/space/page_6ae1052e41148191bd6727c62c165b76).
