# Parent-App NL Test Harness

Natural-language flow tests against the FastAPI backend's HTTP API. See
`../../docs/nl-test-harness-playbook.md` for the full playbook (the *why*).
This README is the *how*.

## Quick start

```bash
# 1. Install deps (use the backend venv so we don't multiply environments)
cd mvp-backend && source .venv/bin/activate
pip install -r ../tests/nl-harness/requirements.txt

# 2. Start the backend (in another terminal)
cd mvp-backend
uvicorn app.server:app --reload --port 8904

# 3. Run all tier-1 flows against local
cd ../tests/nl-harness
ENVIRONMENT=local pytest -m tier1

# 4. Run a single flow with verbose output
pytest flows/generated/test_parent_onboarding_happy_path.py -v
```

## What runs where

| Marker | What it means | When to run |
|---|---|---|
| `tier1` | Critical-path; always run | Every push |
| `tier2` | Important; selective on MR + nightly | On affected MRs |
| `tier3` | Nice-to-have | Nightly only |
| `readonly_safe` | Makes no writes — safe in production runs | Combine with prod env |
| `requires_admin_token` | Needs `ADMIN_TOKEN` env var | Skipped if unset |
| `requires_openai` | Calls a path that hits OpenAI | Skipped unless `RUN_OPENAI_FLOWS=true` |

## Environments

- **local** (`.env.local`) — backend on `http://localhost:8904`, `dev-admin` admin token, all flows enabled.
- **preview** (`.env.preview`) — Railway preview deploy, full lifecycle, ephemeral.
- **production** (`.env.production`) — Railway prod, `READONLY=true`, write-side flows skip themselves.

Switch via `ENVIRONMENT=production pytest ...`. `conftest.py` sources the matching `.env.<env>` file.

## Anatomy of a flow

```
specs/tier-1/<flow-name>.flow.yml      ← human-authored YAML (the spec)
flows/generated/test_<flow_name>.py    ← AI-generated pytest (the test)
```

The YAML is the source of truth for *what* the flow proves. The Python is the
mechanics. Re-generate the Python when the YAML changes.

## Authoring a new flow

1. Write the YAML spec under `specs/tier-1/` (or `tier-2/`). Use one of the
   existing specs as a template.
2. In Claude Code, with `tests/nl-harness/CLAUDE.md` and the new spec in
   context, say: *"Generate the pytest file for this spec."*
3. Run the test — expect RED.
4. Implement the feature until GREEN.
5. Open a PR.

## Persona presets

| Preset | What it sets up |
|---|---|
| `new_parent` | Fresh `user_id`, bearer token, no consent, no profile |
| `existing_parent` | new_parent + consent submitted + profile seeded with one kid |
| `kid_agent_parent` | existing_parent + `/kid-agent/config` introduced + PIN set |
| `admin` | Holds the `X-Admin-Token` value from env |

## Cleanup

Every persona that creates server-side data registers a `DELETE /family/{user_id}`
cleanup in `FlowContext`. If a test crashes mid-run and teardown never fires,
the orphaned rows are marked with the `nl-harness-` prefix on `user_id` so
they're easy to bulk-delete out of band.

## Conventions

- **One flow per file.** Selective execution maps flow names 1:1 to spec files.
- **No `fastapi.TestClient`.** Real HTTP only.
- **No LLM at runtime.** Generated tests are plain pytest; debug them like any
  other test.
- **No backend imports** (`from app...`). The harness is a black box client.
