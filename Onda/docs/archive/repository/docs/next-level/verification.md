# Local verification — 2026-10-13

Base: `5e5caca`, branch `next-level`. No production source was edited. All prototype content is synthetic. No credentials or live family records were read; no models, connectors or external telemetry were called.

## Passed

- `node --test experiments/next-level/model.test.mjs`: 9/9. Guards reviewed observation before experiment; session-only export; correction invalidates plan/outcomes and consent; worse outcome pauses; reviewed-note export excludes raw chat; invalid values rejected; provider eligibility/identity/usage are distinct; sensitive/unreviewed share filtering; empty-selection disclosure.
- `node --check experiments/next-level/app.mjs`: pass.
- Browser test `node experiments/next-level/browser-check.cjs`: 8 checks passed: 5-step scripted onboarding, worse-outcome pause, sensitive/unreviewed selection disabled, restart, no horizontal overflow on 390px across 3 views, zero page errors, local-only asset requests, session-only export empty. Seven rendered screenshots captured at 1440×1000 and 390×844 (full-page heights vary).
- BB code-audit worker: 5 isolated standard-library-only synthetic assertions against `profiling.py` reproduced merge no-clear, rename-key mismatch, duplicate after renamed update, re-creation after child removal, and separate-family empty profile. These are confirmations of existing behavior, not successful remediation tests or production incidents. See code-audit.md.
- Manual visual inspection: rendered understanding view. Sharing/mobile screenshots were captured by passing browser tests; a later image-inspection transport closed before visual review. Connectivity recovered immediately for command tools. No obvious overflow; source/uncertainty/review labels visible.

## Not run

- Full backend pytest: no backend source changed; avoided application boot and committed seed imports to keep this exploration synthetic and separate from real-data/runtime dependencies. The last BB thread's reported 852 tests is historical, not a fresh run here.
- Production dashboard `tsc`, build, iOS `xcodebuild`, fresh-install and real-device voice checks: no product changes or product deployment planned. Worktree has no copied dependency directories or provider/environment configuration. Experimental static UI is independently exercised.
- Live-model quality/safety evals, real-parent research, auth/OAuth, billing, provider eligibility, connector policy integration, tenant-boundary HTTP tests, production deletion, reminder delivery and encrypted persistence: not implemented or run.
- Scientific developmental validation and comparative market/task utility: no claim made.

## Limits

The test model has fixed synthetic IDs/dates and local flags. Its share filter excludes **records tagged sensitive or unreviewed**, not arbitrary sensitive text pasted into a reviewed field. There is no semantic redaction or external policy enforcement. Exact preview plus synthetic-only use is the prototype boundary; a real release requires sensitivity classification, explicit parent review, recipient/purpose restrictions and adversarial tests. Editing a strength note to include health details does not make sharing safe.

Browser tests use a host-specific existing playwright-core installation and temporary Chrome profile. Asset requests go only to localhost; that proves no external app requests from the page, not a production network/privacy guarantee. Screenshots contain only synthetic examples.

## Final repository delivery verification

- All six supplied authored research documents saved under `research/`; source-manifest.json records SHA-256, byte lengths, headings and source-link counts. No recommendations executed, external sources re-fetched, model calls or real child data processed.
- Illustrated A4 PDF: 13 tagged pages, text extractable on every page, 7 synthetic prototype screenshots and 1 proposed architecture illustration embedded. Both original architecture/UX diagram files remain indexed in the repository. Editable HTML and reproducible build/render scripts are adjacent.
- Browser print checks: zero broken images, zero page/footer overflow, zero external asset requests. PDF text extraction found all major topics; relative Markdown links (109) and HTML local references resolved. PDF has link annotations. External source URLs were retained, not newly checked for reachability by this renderer.
- Reviewed rasterized PDF page 6 (Understanding) and page 13 (sources/limits). Print QA captures stay in `/tmp`, preventing duplication in the repository.
- Strategy integrates final research without flattening alternative age bands, retention defaults or pilot sample sizes into an adopted clinical protocol. Research prompt is preserved in full and has not been executed.
