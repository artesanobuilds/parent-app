# Harness production rollout — 2026-10-11

Authorized by Miguel in the implementation thread: merge and deploy PRs #1–#7 one at a time, verify each release before advancing. Repository: `artesanobuilds/parent-app`. Service: `mvp-backend`, production, one replica, Railway volume at `/app/data`.

Each merged tree is compared byte-for-byte with its previously tested PR branch before upload. New shared-runtime switches remain at their default off values during initial rollout. These observations prove the recorded smoke checks at deployment time, not every possible user flow or long-term stability.

## Release index

| PR | Merged commit | Railway release | Checks before advancing |
|---|---|---|---|
| [#1](https://github.com/artesanobuilds/parent-app/pull/1) | `68df0ce` | [Deployment](https://railway.com/project/e8002b7a-755e-4b50-8fbe-647464c2da49/service/5cba4eec-9bf1-4ba6-9941-cedb4905f941?id=c9420d34-a937-4700-9113-afd78cbc248c) | Passed; see evidence below |
| [#2](https://github.com/artesanobuilds/parent-app/pull/2) | `2bf2a1d` | [Deployment](https://railway.com/project/e8002b7a-755e-4b50-8fbe-647464c2da49/service/5cba4eec-9bf1-4ba6-9941-cedb4905f941?id=82c3a267-6f54-4620-8346-261c13a255a1) | Passed; see evidence below |
| [#3](https://github.com/artesanobuilds/parent-app/pull/3) | `1c22e19` | [Deployment](https://railway.com/project/e8002b7a-755e-4b50-8fbe-647464c2da49/service/5cba4eec-9bf1-4ba6-9941-cedb4905f941?id=d976dde2-d5fb-43bb-88ee-55ad17ad9c5a) | Passed; see evidence below |
| [#4](https://github.com/artesanobuilds/parent-app/pull/4) | `6e228dc` | [Deployment](https://railway.com/project/e8002b7a-755e-4b50-8fbe-647464c2da49/service/5cba4eec-9bf1-4ba6-9941-cedb4905f941?id=a99dee6c-7161-44ec-9d33-801ba4e824fe) | Passed; see evidence below |
| [#5](https://github.com/artesanobuilds/parent-app/pull/5) | `bd4c360` | [Deployment](https://railway.com/project/e8002b7a-755e-4b50-8fbe-647464c2da49/service/5cba4eec-9bf1-4ba6-9941-cedb4905f941?id=ced20f9f-d4d9-4b18-8649-8e5ca48552da) | Passed; see evidence below |
| [#6](https://github.com/artesanobuilds/parent-app/pull/6) | `c43fbcb` | [Deployment](https://railway.com/project/e8002b7a-755e-4b50-8fbe-647464c2da49/service/5cba4eec-9bf1-4ba6-9941-cedb4905f941?id=08eb8fbf-fb5f-4272-a519-f082a1b6220e) | Passed; see evidence below |
| [#7](https://github.com/artesanobuilds/parent-app/pull/7) | `67313a0` | [Deployment](https://railway.com/project/e8002b7a-755e-4b50-8fbe-647464c2da49/service/5cba4eec-9bf1-4ba6-9941-cedb4905f941?id=5c96e934-c94a-4f9d-9f17-3bfccccd4885) | Passed; see evidence below |

Railway links require authorized project access. The recorded baseline and observations below can be reviewed without access to private logs.

## PR #1

- Merged commit: `68df0ce8ee801134cf3663d5140df45d29ca3174`.
- Deployment: `c9420d34-a937-4700-9113-afd78cbc248c`, Railway `SUCCESS`.
- `/health`, `/dashboard/`, `/cms/`: HTTP 200.
- Content counts: exactly 45 articles and 110 categories; per-category counts matched pre-deploy baseline.
- Three public-read NL harness cases passed (library/filter/detail; category schema; populated articles). Executed directly against HTTP to avoid unrelated legacy fixture mutations/bulk export.
- Throwaway family: token issuance, profile seed, GET readback, DELETE cleanup all passed.
- Inspected boot logs: startup complete, zero errors/tracebacks.
- No runtime, API, or migration changes in this PR.

## Backup baseline

Content-only backup completed at 2026-10-11T15:44:32Z. Articles 161624 bytes, MD5 `8ee35ebdcc23b41758cdc5c3542ee5f1`; categories 7933 bytes, MD5 `99e73584ea36c5ecbba6ea4264fb8da3`. Local backup ledger committed as `83f7cc3` on `ops/harness-deployments-20261011`. No family data downloaded.

## Incidents and limits

- Railway CLI login was refreshed. Initial credential save was blocked by sandbox permissions; repeated login with write permission succeeded.
- PR #2 upload attempt `caf97060-307b-492e-aa7d-aa7caa8dd401` failed with TLS `BadRecordMac` before any build. A separate retry was submitted.
- Automatic approval review rejected SSH key registration as a persistent account access change. No key was registered; native Railway snapshot API uses the existing authenticated connection instead.

## PR #2

- Merged commit: `2bf2a1dfb7270ef94e03157c55302c68b8411e33`.
- Successful retry deployment: `82c3a267-6f54-4620-8346-261c13a255a1`, Railway `SUCCESS`.
- Health/dashboard/CMS all HTTP 200; all CMS counts exactly match baseline (45 articles / 110 categories).
- Three public-read cases and throwaway profile seed/readback/delete passed.
- Live coach SSE returned text and `[DONE]`, no error frame, in 2.67 seconds.
- Inspected boot/request logs: startup complete, zero errors/tracebacks.

## PR #3

- Merged commit: `1c22e19d460e841100bfebb06de424db3d470eaf`.
- Deployment: `d976dde2-d5fb-43bb-88ee-55ad17ad9c5a`, Railway `SUCCESS`.
- Health/dashboard/CMS HTTP 200; content counts unchanged; three public-read checks passed.
- Throwaway profile seed/readback/delete passed; live coach SSE produced tokens and completion without an error frame in 2.30 seconds.
- Inspected boot/request logs: startup complete, zero errors/tracebacks.
- A second, designated throwaway profile remains only for cross-deployment restart checks and will be deleted at the end.
- Railway service-variable read confirmed all six `MVP_SHARED_RUNTIME_*` switches and `MVP_COS_ACTIVE_CONVERSATION` unset (default off); storage paths also unset, using `/app/data` defaults. No configuration values were changed.

## PR #4

- Merged commit: `6e228dc4bc7656dfeeff8584ff8cb92ef367686a`.
- Deployment: `a99dee6c-7161-44ec-9d33-801ba4e824fe`, Railway `SUCCESS`.
- Boot log: `applied v25: agent durable runs, operation receipts and family fences`.
- Health/dashboard/CMS HTTP 200; all content counts unchanged; three public-read cases passed.
- All 23 live harness OpenAPI route schemas match the contract fixture.
- Throwaway profile seed/readback/delete passed; live coach SSE completed without error in 2.30 seconds.
- Persistent rollout canary survived deployment/restart.
- Inspected boot/request logs: startup complete, zero errors/tracebacks.
- Full production volume backup `d39c36c7-ba7d-48bb-a53a-e74c0f23ceba` is platform-listed with native snapshot identifier (156 MB), recorded in backup ledger commit `2931b8e`. Workflow-status endpoint inaccessible; no restore drill claimed.

## PR #5

- Merged commit: `bd4c3605a43facab771d2c643a6c70599aa251f5`.
- Deployment: `ced20f9f-d4d9-4b18-8649-8e5ca48552da`, Railway `SUCCESS`.
- Health/dashboard/CMS HTTP 200; all content counts unchanged; three public-read cases and 23 live schema comparisons passed.
- Throwaway profile seed/readback/delete passed; live coach SSE completed in 2.36 seconds without an error frame.
- Persistent rollout canary survived this additional restart.
- Inspected logs: startup complete, zero errors/tracebacks; migration25 did not reapply.
- Pre-PR6 native backup `dc310026-ee92-4495-b299-9459ac8faec8` platform-listed at 2026-10-11T15:58:38.892Z, 156 MB referenced; metadata ledger commit `a4493eb`. No restore test claimed.

## PR #6

- Merged commit: `c43fbcb515bd2703d87f5067a6b59f5e70a8176d`.
- Deployment: `08eb8fbf-fb5f-4272-a519-f082a1b6220e`, Railway `SUCCESS`.
- Boot log: `applied v26: background_jobs.attempt_fences`; startup completed.
- Health/dashboard/CMS HTTP 200; all content counts unchanged; three public-read cases and 23 live schema comparisons passed.
- Throwaway profile seed/readback/delete passed; live coach SSE completed in 2.18 seconds without error. Persistent canary survived restart.
- Two synthetic background-job smokes passed: research queued then canceled, authoritative GET remained canceled with zero candidates; warmup finished at 100%, coach skipped for empty family, no failed steps; families deleted.
- One nonfatal external PostHog deletion lookup timed out on the first job-smoke cleanup (`httpx.ReadTimeout`, app DELETE still 200). Existing analytics deletion code is unchanged by this stack. The repeated smoke's PostHog request succeeded (0 persons found). This is recorded rather than claiming warning-free logs. No HTTP5xx in inspected logs.

## PR #7 and final state

- Merged commit: `67313a0e8506eb5b8398448084ddef900b475114`.
- Deployment: `5c96e934-c94a-4f9d-9f17-3bfccccd4885`, Railway `SUCCESS`.
- Railway image digest: `sha256:54c60e79f300fe04412fa0f69477bdcd7ff56c73dbe6106ba8f0a363b214b4e8`.
- Health/dashboard/CMS HTTP 200; exact baseline counts unchanged (45 articles / 110 categories); three public-read cases and all 23 live route-schema comparisons passed.
- Throwaway profile seed/readback/delete passed. Real coach SSE completed in 2.42 seconds.
- Authentication rejection checks passed for onboarding, COS and parent voice.
- Real onboarding SSE + transcript readback passed (1.64 seconds); real COS SSE + transcript readback passed (2.34 seconds).
- Direct parent-voice HTTP request exercised the real parent model, returned OpenAI-compatible chunks and `[DONE]` (2.61 seconds). No ElevenLabs session or TTS call was made.
- Research create/cancel/readback and empty-family warmup completion passed again; all job-test family data was deleted.
- The profile retained since PR #3 survived every subsequent deployment and was deleted after final verification. All synthetic test families were cleaned up.
- Inspected final-deployment logs contained no errors or tracebacks. Migrations25/26 did not reapply on this restart.

Final recheck at **2026-10-11 16:10 UTC**: deployment still `SUCCESS`; health/dashboard/CMS HTTP 200, exact content counts and all 23 live schema checks passed again. No errors or tracebacks in the inspected final-deployment log window.

## Coverage and operating limits

- All seven harness PRs are merged. The six earlier successful deployments are subsequently marked `REMOVED` by Railway because newer releases replaced them; the per-release `SUCCESS` observations above were made before advancing.
- All shared-runtime switches and the named-conversation routing switch remain off by default. Live checks prove the deployed default paths, including their new durable scopes/fencing; they do not establish production behavior with those switches enabled. Both switch modes passed the prior offline backend suite (792 passed / 45 skipped each).
- Real-device iOS, full ElevenLabs audio sessions, kid moderation flows and long-running provider jobs were not exercised in production. Public API schemas were verified unchanged. Provider cost/quality and latency percentiles were not benchmarked; listed timings are individual synthetic requests.
- No destructive failure injection or backup restore was performed in production. Native backups are platform-listed, crash-consistent snapshots, not restore-tested recovery claims.
- This is point-in-time release evidence, not a guarantee of future uptime. Application state and smoke checks passed throughout; the PR6 external analytics timeout is retained above.
- No GitHub Actions workflow or staging environment was enabled during this rollout. The separate [CI/CD plan](../design/cicd-and-staging-plan.md) is proposed follow-up work.
