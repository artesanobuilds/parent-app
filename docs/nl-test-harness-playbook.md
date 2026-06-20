# Natural Language Test Harness: Parent-App Playbook

> Adapted from the SonderMind NL Test Harness playbook (April 2026). Stripped of
> SonderMind-specific service names, retargeted to parent-app's single-backend +
> iOS + CMS topology, and re-rooted on Python + pytest + httpx instead of
> TypeScript + Vitest (parent-app is a Python-first team).

"The more your tests resemble the way your software is used, the more confidence
they can give you." — Kent C. Dodds

"Infrastructure must be hardened before agentic testing. AI agents can maintain
tests — but only if the harness exists first." — Simon Willison

---

## 1. Executive Summary

Parent-app has substantial unit coverage in the LLM eval harness
(`mvp-backend/app/evals/`) and growing iOS view code, but **no flow-level test
exercises the user journeys that span the FastAPI backend, the kid-agent
LangGraph stack, and the iOS app's HTTP contract**.

When a parent finishes onboarding, taps "Library", reads an article, and then
introduces a kid-agent, that journey crosses ~12 endpoints, the `auth_tokens`
gate, the `kid_agent_crisis_locks` table, and the SSE moderation stream. If any
link drifts — say `/profile/seed` adds a new required field, or the moderation
sliding-window regresses to the buffer-bypass bug we just fixed — no current
test catches it. We find out when iOS surfaces a confusing decode error or a
parent reports a moderation miss.

Martin Fowler calls the missing layer "subcutaneous tests" — tests that hit
the HTTP layer directly, simulating the full user flow without launching a
browser or simulator. Every expert we reviewed (Willison, Fowler, Dodds, AWS)
converges on the same conclusion: flow-level tests are the highest-ROI
investment, and AI makes them cheap to write and maintain.

This playbook defines a Python harness where:

- Engineers write tests as natural-language **YAML flow specs** describing
  business journeys — intent, invariants, and boundary contracts in plain
  English
- Claude Code (or any LLM that can read YAML and write Python) translates
  those specs into **executable pytest files** — deterministic, debuggable
  code that runs with `pytest`
- The harness tests **REST APIs from the outside via HTTP** — no in-process
  imports of `app.server`, no fastapi `TestClient`. Just `httpx` calls against
  a running backend on `:8904` (local) or the Railway production URL
- Tests run against **any environment** — local dev, Railway preview, Railway
  production (read-only)
- **Selective execution** — only flows affected by code changes run on each
  push; tier-1 critical flows always run
- **Red-green TDD with AI**: write the spec first, ask Claude to generate a
  failing test, then implement until green

**Investment:** a standalone harness inside the parent-app repo at
`tests/nl-harness/`, runnable in isolation (`cd tests/nl-harness && pytest`).
It leverages the existing pydantic models as schema references but generates
external HTTP tests — never imports server code. The harness works against any
running instance of the backend.

**Why this matters now:** the Phase 0 taxonomy work just added `parent_id` to
categories and a `?tag=` filter to `/content/articles`. There is no automated
test that the new query param doesn't break unfiltered reads, that admin-token
gating still 401s the right endpoints, or that the kid-agent crisis lock + revive
round-trip still works after the last refactor. Every one of those is a
candidate flow spec.

---

## 2. What Exists Today

### 2.1 Parent-App Surface Landscape

| Surface | Language | Where | What it exposes |
|---|---|---|---|
| Backend | Python 3.11 + FastAPI + DuckDB | `mvp-backend/app/` | HTTP API on `:8904`: `/auth/issue-token`, `/profile/seed`, `/content/*`, `/kid-agent/*`, `/kid-chat` (SSE), `/cms/*`, `/data/*`, `/health` |
| Coaching agent | LangGraph 1.0.x | `mvp-backend/app/agent.py` | `/chat` and `/onboarding-chat` SSE streams |
| Kid agent | LangGraph + per-kid synthesis | `mvp-backend/app/kid_agent_service.py` | `/kid-chat` SSE with sliding-window moderation gate |
| CMS | React 19 + Vite + TipTap | `mvp-backend/cms/` | Admin UI → backend `/cms/*` endpoints, gated by `X-Admin-Token` |
| iOS | SwiftUI | `mvp/MVP/` | Client-side of every public backend route |

The backend is the only deployable service. iOS and CMS are HTTP clients that
trust the backend's contract. The harness validates that contract end-to-end.

### 2.2 Existing Test Assets

| Asset | Location | What it provides |
|---|---|---|
| LLM eval harness | `mvp-backend/app/evals/` | YAML scenario evaluation for agent outputs (judge.py + runner.py + cases/). **Not** an HTTP flow harness — runs the LangGraph agent in-process and judges output text. |
| Pydantic request/response models | `mvp-backend/app/server.py` and module-level files | Free schema references — every endpoint's request body and response shape is already typed |
| `docs/release-notes/2026-05-07.md` | Repo | Hand-authored manual QA checklist used before TestFlight uploads. This document is the manual-QA twin of what the harness automates. |
| `mvp-backend/tools/sync-data.sh` | Repo | Snapshot/restore primitives the harness can use for test-data setup against a local instance |

### 2.3 What's Missing

| Gap | Impact |
|---|---|
| No HTTP-level flow tests | The 9-step onboarding, library browse, kid-agent introduce → chat → crisis-lock journey is exercised only by hand-clicking iOS + reading server logs |
| No regression guard on admin-token gating | We added `require_admin_token` to `/cms/*` and `/data/*` — a future refactor could quietly remove it and no test would catch the security regression |
| No regression guard on the moderation gate | The sliding-window fix that closed the buffer-bypass bug is sitting in the codebase with no test. A revert would ship silently. |
| No iOS contract regression test | When backend adds a required field to `/profile/seed`, iOS gets a runtime error in TestFlight. A schema-pinned HTTP test would have failed in CI on the backend MR. |
| No tag/category filter coverage | `?tag=` + `?category=` composition is brand new — one wrong DuckDB query and the Library returns the wrong articles silently. |

### 2.4 Why Flow-Level Tests Are the Highest-ROI Investment Here

The classic test pyramid (Fowler, 2012) prescribes many unit tests, fewer
integration tests, fewest E2E tests. That ratio was driven by cost — E2E tests
were expensive to write, expensive to maintain, slow to run. AI changes two of
those three costs. Writing and maintenance are now cheap. Execution time is
unchanged. Two of three cost drivers are weakening. The optimal shape shifts
toward heavier investment in flow-level tests — closer to Kent C. Dodds'
"testing trophy" than the classic pyramid.

**The bug we can't catch today.** The kid-agent crisis flow spans: parent sets
PIN → kid types a self-harm phrase → moderation gate fires → `kid_agent_crisis_locks`
row inserted → in-flight stream killed → audit_events written → parent dashboard
shows the lock → parent calls `/kid-agent/{agent_id}/revive` → lock cleared →
enabled flipped back to true → audit_events written again. We have unit tests
for *each* of those steps. No test exercises the full sequence — and the
B-7 hoist fix (replacement message sent BEFORE the agent locked) is exactly
the kind of bug a unit test misses but a flow test would catch.

**Why these tests first, not more unit tests or more iOS UI tests:**

- Faster than UI-driven E2E — no XCUITest, no simulator, no Playwright
- Test actual service interactions — the kid-agent SSE stream, the moderation
  gate, the admin-token boundary
- Easiest for AI to generate and maintain — structured HTTP calls, not
  brittle UIKit accessibility selectors
- Catch the class of bugs we're most exposed to as a small team — schema and
  auth drift between backend and iOS

### 2.5 Maturity Ladder

| Level | State | When |
|---|---|---|
| 0 — Current | No flow tests. LLM evals exist; HTTP flows do not. | Now |
| 1 — Foundation (this playbook) | Flow harness for the public HTTP API. Tier-1 flows run on every push. | This week |
| 1.5 — AI-assisted authoring | Claude reads `app/server.py` + spec intent and proposes `boundary_contracts` automatically | Next |
| 2 — Red-green TDD by default | Every new endpoint ships with at least one flow spec as a launch gate | After |
| 3 — Agentic | Headless agent runs the harness against Railway preview deploys nightly and opens issues for regressions | Later |

This playbook is the Level 1 implementation.

---

## 3. Prior Art

This is a faithful adaptation of the SonderMind NL Test Harness playbook
(April 2026), itself drawing on:

- **Simon Willison** — red/green TDD with AI; infrastructure-first
- **Martin Fowler** — [SubcutaneousTest](https://martinfowler.com/bliki/SubcutaneousTest.html);
  the pyramid was a cost optimization, not a law
- **Kent C. Dodds** — testing trophy; integration tests resembling real user
  behavior
- **QA Wolf** — specs declare goals, not steps; goal-oriented specs succeed at
  3× the rate of step-oriented ones

The substantive change from the source playbook: parent-app is a single-service
topology, so we drop the cross-service saga complexity and the
`SERVICE_DEPENDENCY_MAP` becomes a `MODULE_DEPENDENCY_MAP` keyed on Python module
paths within `mvp-backend/app/`.

---

## 4. Architecture

### 4.1 Design Principles

1. **Tests live outside the service.** The harness is `tests/nl-harness/` —
   it does not import `app.server`, does not use `fastapi.TestClient`, does not
   reach into `storage_backend`. HTTP calls only. This keeps the harness honest
   about the contract the iOS app sees.
2. **Tests run against any environment.** Base URL, admin token, OpenAI key
   (where used), and test-data strategy are all parameterized via `.env.*` files.
3. **Tests are selective.** Each flow spec declares which modules/endpoints it
   touches. CI uses `git diff` analysis to run only affected flows, plus all
   tier-1 flows on every push.

### 4.2 Two-Layer Testing Model

| Layer | Tool | Deterministic? | AI role | When |
|---|---|---|---|---|
| In-process unit + LLM evals | pytest (existing) + `app/evals/runner.py` | Mostly | Can generate cases | Every push |
| HTTP flow tests (this harness) | pytest + httpx | Yes | Generates from NL spec | Every push (selective) + nightly (full) |

**Critical design decision:** No LLM-as-judge in the flow test layer. Flow tests
must be fully deterministic. The AI generates the test, but once generated, it's
plain Python + pytest. If your CI depends on an LLM call to decide pass/fail
for an HTTP test, you've introduced a non-deterministic oracle into your
deterministic suite. The LLM eval harness already exists for the cases where
LLM judging is the right tool — keep them separate.

### 4.3 Tech Stack: Python + pytest + httpx

**Why Python:**

- Parent-app is a Python-first team; the harness shouldn't need a separate
  TypeScript toolchain just to test the HTTP API
- pytest has native async support via `pytest-asyncio` — important because
  the kid-chat SSE flow is async
- Free schema validation: pydantic is already a dependency for the backend;
  we re-use its models as the contract for response shapes
- Claude Code generates Python fluently. YAML-to-pytest translation is natural

**Why not TypeScript + Vitest** (the SonderMind original): no team upside
here. CMS is the only TS surface in the repo, and it's a UI consumer of the
same HTTP API — testing it from a sibling TS harness duplicates work without
adding lens diversity.

**Why not in-process `fastapi.TestClient`:** that path bypasses uvicorn,
middleware ordering, real `HTTPException` → JSON serialization, and the
SSE stream wire format. It's a unit test of route handlers, not a flow test.

### 4.4 Repository Structure

```
tests/nl-harness/
├── specs/                          # YAML specs (human-authored)
│   ├── tier-1/
│   │   ├── parent-onboarding-happy-path.flow.yml
│   │   ├── library-browse-and-tag-filter.flow.yml
│   │   ├── kid-agent-lifecycle.flow.yml
│   │   ├── admin-token-gating.flow.yml
│   │   └── community-post-and-reply.flow.yml
│   ├── tier-2/                     # important but not launch-blocking
│   └── tier-3/                     # nice-to-have, nightly only
│
├── flows/
│   └── generated/                  # AI-generated pytest files
│       ├── test_parent_onboarding_happy_path.py
│       ├── test_library_browse_and_tag_filter.py
│       ├── test_kid_agent_lifecycle.py
│       ├── test_admin_token_gating.py
│       └── test_community_post_and_reply.py
│
├── lib/
│   ├── __init__.py
│   ├── client.py                   # httpx wrapper with base URL + auth header
│   ├── flow_context.py             # FlowContext: per-test state, cleanup, polling
│   ├── auth.py                     # auth strategy: token issuance via /auth/issue-token
│   ├── data.py                     # data strategy per env
│   ├── personas/
│   │   ├── __init__.py
│   │   ├── new_parent.py           # fresh user, fresh uuid, no profile yet
│   │   ├── existing_parent.py      # already-onboarded user with one kid
│   │   ├── kid_agent_parent.py     # parent with an introduced + PIN'd kid agent
│   │   └── admin.py                # admin with X-Admin-Token
│   ├── services.py                 # base URL registry per environment
│   ├── selector.py                 # git diff → affected flows
│   └── sse.py                      # minimal SSE event-stream reader
│
├── conftest.py                     # pytest fixtures: client, ctx, personas
├── pytest.ini                      # markers: tier1/tier2/tier3; asyncio_mode
├── requirements.txt                # httpx, pytest, pytest-asyncio, pydantic, pyyaml
├── .env.local                      # http://localhost:8904, ADMIN_TOKEN, mock OpenAI
├── .env.preview                    # https://parent-app-preview.up.railway.app
├── .env.production                 # https://parent-app.up.railway.app + readonly mode
├── README.md
└── CLAUDE.md                       # generation rules for AI authoring
```

### 4.5 The Natural Language Spec Format

Each spec has three abstraction levels:

1. **Intent + invariants** (human-authored): "A parent finishes onboarding and
   their first Home load returns articles and categories"
2. **Boundary contracts** (machine-verified): explicit endpoint, expected status,
   required response fields
3. **Step orchestration** (AI-generated): the actual pytest code between intent
   and contracts

```yaml
# specs/tier-1/parent-onboarding-happy-path.flow.yml
spec:
  name: parent-onboarding-happy-path
  tier: 1
  modules: [auth, profile, content]
  intent: >
    A new parent issues a token, submits consent + profile seed, and their
    first Home load returns categories and articles.

  personas:
    parent:
      preset: new-parent

  preconditions:
    - "Backend is reachable at $BASE_URL/health"

  invariants:
    - "A bearer token is issued for the parent's user_id"
    - "Consent is recorded with the current CONSENT_AGREEMENT_VERSION"
    - "Profile seed persists parent name + at least one child"
    - "GET /content/categories returns >=1 category"
    - "GET /content/articles returns >=1 article"

  boundary_contracts:
    - endpoint: POST /auth/issue-token
      as: anonymous
      status: 200
      response_includes: [token, user_id]

    - endpoint: POST /consent/submit
      as: parent
      status: 200
      response_includes: [parent_name, agreement_version]

    - endpoint: POST /profile/seed
      as: parent
      status: 200
      response_includes: [parent, children]

    - endpoint: GET /content/categories
      as: anonymous
      status: 200
      response_array_min_length: 1

    - endpoint: GET /content/articles
      as: anonymous
      status: 200
      response_array_min_length: 1
```

**Design notes:**

- `modules` (not `services`) — parent-app is single-service; the tag controls
  selective execution via `MODULE_DEPENDENCY_MAP`
- `preset` names are stable strings; `lib/personas/<preset>.py` resolves the
  preset per environment
- `as: anonymous` means no `Authorization` header. `as: parent` injects the
  persona's token. `as: admin` injects `X-Admin-Token`. `as: kid` injects the
  kid's PIN as a body field.
- This is *not* Cucumber. There are no English step lines. The YAML declares
  the **outcome**; pytest declares **how to get there**.

### 4.6 What a Generated Flow Test Looks Like

From the YAML above, a generated pytest file might look like:

```python
# flows/generated/test_parent_onboarding_happy_path.py
#
# @generated_from: specs/tier-1/parent-onboarding-happy-path.flow.yml
# @modules: auth, profile, content
#
import pytest

pytestmark = pytest.mark.tier1


def test_parent_completes_onboarding_and_home_loads(flow_ctx, new_parent):
    parent = new_parent  # persona resolves token via /auth/issue-token

    # Consent
    consent_resp = flow_ctx.post(
        "/consent/submit",
        json={
            "parent_name": "Test Parent",
            "parent_email": "test@example.com",
            "kid_age_band": "3-5",
            "agreement_version": flow_ctx.consent_agreement_version,
        },
        as_=parent,
    )
    assert consent_resp.status_code == 200
    assert consent_resp.json()["agreement_version"] == flow_ctx.consent_agreement_version

    # Profile seed
    seed_resp = flow_ctx.post(
        "/profile/seed",
        json={
            "user_id": parent.user_id,
            "parent_name": "Test Parent",
            "kids": [{"name": "TestKid", "age": "5", "temperament": "curious"}],
        },
        as_=parent,
    )
    assert seed_resp.status_code == 200
    body = seed_resp.json()
    assert "parent" in body and "children" in body

    # Home loads
    cats = flow_ctx.get("/content/categories").json()
    assert isinstance(cats, list) and len(cats) >= 1

    articles = flow_ctx.get("/content/articles").json()
    assert isinstance(articles, list) and len(articles) >= 1
```

Run with: `BASE_URL=http://localhost:8904 pytest tests/nl-harness/flows/generated/test_parent_onboarding_happy_path.py`

No custom runner. No LLM at runtime. Standard pytest. Standard debugging.
Standard CI. Works against any environment.

### 4.7 FlowContext

`FlowContext` is the per-test session object. It:

- Resolves `BASE_URL` from environment
- Exposes `get(path)`, `post(path, json=..., as_=persona)`, `put`, `delete`
- Tracks entities it creates (e.g. community posts) and reverses them in
  `cleanup()` at teardown
- Provides `wait_for(condition_fn, timeout=15, interval=1, fail_if=...)` for
  eventually-consistent assertions (e.g. crisis lock landing in DuckDB after
  a kid-chat SSE event)
- Exposes constants like `consent_agreement_version` read once from
  `/health` or hardcoded as a contract

**No SSE state in FlowContext.** SSE is a separate concern handled by
`lib/sse.py` — flows that need streaming use it explicitly.

---

## 5. Environment Configuration

### 5.1 Three Target Environments

| Env | Base URL | Auth | Data |
|---|---|---|---|
| `local` | `http://localhost:8904` | `/auth/issue-token` issues real tokens; `ADMIN_TOKEN` from `.env.local` | Each test creates a fresh user_id (uuid4) and cleans up via `DELETE /family/{user_id}` |
| `preview` | Railway preview deploy | Same as local | Same — preview deploys are ephemeral, full lifecycle is fine |
| `production` | Railway prod | Read-only test account, no admin token | **Read-only mode**: only GET endpoints + introspection; no POST/PUT/DELETE. Tests that require writes are skipped (`pytest.mark.skipif(env == 'production')`) |

### 5.2 .env Files

```bash
# tests/nl-harness/.env.local
ENVIRONMENT=local
BASE_URL=http://localhost:8904
ADMIN_TOKEN=dev-admin
CONSENT_AGREEMENT_VERSION=2026-04-01-v1
RUN_KID_AGENT_FLOWS=true   # requires OPENAI_API_KEY on the server
```

`.env.production`:

```bash
ENVIRONMENT=production
BASE_URL=https://parent-app.up.railway.app
READONLY=true
# no ADMIN_TOKEN in prod runs
```

`conftest.py` reads `ENVIRONMENT` and loads the matching file.

### 5.3 Pre-Suite Health Check

The harness runs `GET $BASE_URL/health` once at session start. If it returns
anything other than 200 with `{"status": "ok"}`, the entire suite aborts with
a clear "backend not reachable" error before a single test runs.

---

## 6. Red-Green TDD Workflow with Claude Code

### 6.1 The Cycle

```
Engineer writes .flow.yml      Claude generates       Run RED          Claude implements    Run GREEN
(intent + invariants +     →   failing test_*.py  →   (test fails) →   feature code     →   (test passes)
 contracts)                    from YAML + CLAUDE.md  because no
                                                       feature code
```

1. **Write the spec.** Developer writes a `.flow.yml`. This is "planning as
   code" — reviewed before development starts. The YAML is the test plan.
2. **Generate failing test.** Prompt Claude: *"Read
   `tests/nl-harness/specs/tier-1/foo.flow.yml` and generate the corresponding
   pytest. Follow the patterns in `tests/nl-harness/CLAUDE.md` and use
   existing persona presets."*
3. **Run RED.** `pytest tests/nl-harness/flows/generated/test_foo.py` — fails
   because the feature code doesn't exist. Verify it fails for the right
   reason (404/500 from the endpoint, not infrastructure error).
4. **Implement.** Prompt Claude in `mvp-backend/`: *"The flow test at
   `tests/nl-harness/flows/generated/test_foo.py` is failing. Implement the
   minimum code to make it pass. Red/green TDD."*
5. **Run GREEN.** All assertions pass.
6. **Guardrail.** `pytest -m tier1` — verify no regressions in other flows.

### 6.2 `tests/nl-harness/CLAUDE.md`

The CLAUDE.md in the harness root documents:

- How to read `.flow.yml` and generate matching pytest
- Available persona presets (`new-parent`, `existing-parent`,
  `kid-agent-parent`, `admin`) and what data they create
- The FlowContext API: `flow_ctx.get/post/put/delete`, `flow_ctx.wait_for`,
  `flow_ctx.consent_agreement_version`
- Auth patterns: `as_=parent` vs `as_=admin` vs no `as_` (anonymous)
- Pydantic patterns for response validation when stronger than dict-key checks
- How to tag tests with markers (`pytestmark = pytest.mark.tier1`)
- Running tests: `ENVIRONMENT=local pytest tests/nl-harness/`

### 6.3 Generated Test Trust Boundary

Simon Willison's warning — *"avoid inflicting unreviewed AI-generated code on
teammates"* — applies here. Staged trust:

- **Stage 1 — Ephemeral** (no commit): for ad-hoc spec authoring. Generated
  test runs once, output captured, file discarded.
- **Stage 2 — Candidate** (`flows/generated/`): AI-generated, human-reviewed
  on the MR. Header includes `@generated_from`, `@generated_at`,
  `@promoted_by`. Weekly 30-minute review ritual promotes to `flows/canonical/`.
- **Stage 3 — Canonical** (`flows/canonical/`): human-authored or
  human-modified. AI can propose changes; must be reviewed.

For parent-app's team size today, **stage 2 is the default**. Stage 3 promotion
is a future practice once we have 15+ flows and a weekly review cadence makes
sense.

---

## 7. Test Data Strategy

### 7.1 Per-Environment Strategy

| Env | Strategy | Cleanup |
|---|---|---|
| `local` | Each test creates a fresh `user_id = uuid4()` via `/auth/issue-token`. All writes scoped to that user. | `DELETE /family/{user_id}` in teardown (the same endpoint the consent screen promises) |
| `preview` | Same as local | Same |
| `production` | Pre-provisioned read-only test accounts (none today; future work) | Read-only, no cleanup needed |

This means **no factories, no fixtures-as-files**. The harness creates exactly
what each flow needs via the public API, then tears it down via the public API.
The `DELETE /family/{user_id}` cascade we built for Track A is the cleanup
primitive.

### 7.2 Persona Presets

```python
# lib/personas/new_parent.py
from uuid import uuid4
from dataclasses import dataclass

@dataclass
class Parent:
    user_id: str
    token: str
    display_name: str = "Test Parent"

def new_parent(flow_ctx) -> Parent:
    user_id = f"nl-harness-{uuid4()}"
    resp = flow_ctx.post("/auth/issue-token", json={"user_id": user_id})
    resp.raise_for_status()
    return Parent(user_id=user_id, token=resp.json()["token"])
```

The `nl-harness-` prefix on user_ids makes orphaned test data easy to identify
and bulk-clean if a CI run is killed before teardown.

### 7.3 Production Safety

Production runs **must** use a hardcoded list of pre-provisioned test account
user_ids (still to be created). Until then, the harness refuses to run against
production with a clear error.

---

## 8. CI Integration and Selective Execution

### 8.1 Selective Execution

The harness uses a three-part selection mechanism:

1. **YAML spec tags** — each spec declares affected modules:

```yaml
spec:
  name: kid-agent-lifecycle
  tier: 1
  modules: [auth, kid_agent, moderation, audit]
```

2. **Module dependency map** — static config mapping repo paths to flow specs:

```python
# lib/selector.py
MODULE_DEPENDENCY_MAP = {
    "mvp-backend/app/server.py": ["*"],                      # server.py touches every endpoint
    "mvp-backend/app/auth_service.py": ["parent-onboarding-happy-path"],
    "mvp-backend/app/content.py": ["library-browse-and-tag-filter"],
    "mvp-backend/app/kid_agent_service.py": ["kid-agent-lifecycle"],
    "mvp-backend/app/moderation.py": ["kid-agent-lifecycle"],
    "mvp-backend/app/duckdb_storage.py": ["*"],              # storage changes touch every flow
    "mvp-backend/app/migrations.py": ["*"],                  # migrations touch every flow
}
```

3. **Git diff analysis** — CI determines changed files and unions their flows
   with all tier-1 (which always runs).

```python
# lib/selector.py
def select_flows(changed_files: list[str]) -> set[str]:
    affected = set()
    for f in changed_files:
        for prefix, flows in MODULE_DEPENDENCY_MAP.items():
            if f.startswith(prefix):
                affected.update(flows)
    # Always include tier-1
    affected.update(all_tier1_flow_names())
    # `*` means "all flows for that module"
    return affected
```

**Drift risk:** the map is hand-maintained. If a new module is added without a
map entry, the fallback is *run all tier-1*. Nightly full-suite catches what
selective misses.

### 8.2 GitHub Actions Job

```yaml
# .github/workflows/nl-harness.yml (sketch)
- name: Start backend
  run: |
    cd mvp-backend
    uvicorn app.server:app --host 0.0.0.0 --port 8904 &
    sleep 5

- name: Run tier-1 flows
  run: |
    cd tests/nl-harness
    ENVIRONMENT=local pytest -m tier1 --tb=short
```

---

## 9. Build vs. Buy

Considered:

- **Postman / Newman** — declarative HTTP tests, decent CI integration. No
  spec-level abstraction; every collection is the test. No selective execution.
  Better than nothing but doesn't deliver the AI-generation upside.
- **Hurl** — YAML-native, language-agnostic CLI. Lacks the FlowContext-style
  shared state and complex assertion logic.
- **Cypress + cy.api()** — overkill; we don't need a browser. And we already
  don't have Cypress.
- **Hand-written pytest tests** — what we're building, except *without* the
  YAML layer. The YAML layer is the AI-generation handle.

Building wins because:
1. The YAML/Python split is what makes AI generation work — Cucumber-flavored
   tools (Behave, behave-django) all push step orchestration into the prose
   layer and break.
2. The team is Python-fluent; pytest + httpx is zero new tooling.
3. The harness fits in ~600 lines; it's not a meaningful build cost.

---

## 10. Design Trade-Offs

| Trade-off | Choice | Rationale |
|---|---|---|
| In-process `TestClient` vs HTTP | HTTP | TestClient bypasses uvicorn, middleware ordering, real exception serialization, SSE wire format |
| TS+Vitest vs Python+pytest | Python+pytest | Single language for the team; pytest already in the repo for evals |
| YAML spec vs pure Python | YAML | YAML is the AI-generation handle; pure Python would force the LLM to invent its own intent layer per file, defeating consistency |
| One-flow-per-file vs grouped | One-flow-per-file | Selective execution treats each spec as an atom; easier diff-to-flow mapping |
| LLM-as-judge in flow tests | No | Determinism. LLM evals stay in `app/evals/`, a separate harness |

---

## 11. First Batch of Flows (Tier 1)

| Flow | What it guards | Why tier-1 |
|---|---|---|
| `parent-onboarding-happy-path` | The 9-step onboarding → seed → Home loads contract | The first impression. If this breaks, the app is unusable. |
| `library-browse-and-tag-filter` | `/content/categories` returns shape; `/content/articles` supports `category=` and `tag=` independently and composed | Phase 0 taxonomy work just landed `?tag=`; this is the regression guard |
| `kid-agent-lifecycle` | Create config → introduce → kid PIN → chat round-trip → crisis lock → revive | The most safety-critical path in the app |
| `admin-token-gating` | `/cms/*` and `/data/*` 401 without `X-Admin-Token`, 200 with | Security regression guard; the Track A work explicitly added these gates |
| `community-post-and-reply` | Create post → list → reply → list replies; auth required | The third pillar of the iOS Home (Categories / Library / Community) |

---

## 12. Success Metrics

For the next 30 days after the harness ships:

- **Coverage:** 5 tier-1 flows green in CI on every push (this batch)
- **Stability:** flake rate <2% across 50 runs (local) and 50 runs (preview)
- **Catch rate:** every backend MR that breaks one of the 5 flows is caught
  by CI, not by a TestFlight tester or by hand-clicking iOS
- **Author cost:** writing a new flow spec + generating + reviewing takes
  under 30 minutes (the SonderMind playbook targets 15 minutes — we'll match
  once we have ~10 flows and the patterns are stable)

---

## 13. Open Questions / Future Work

- **Production read-only mode:** the pre-provisioned test account model is
  documented but not built. First production run will need this.
- **SSE moderation flow:** `lib/sse.py` is a minimal reader. The
  `kid-agent-lifecycle` spec exercises the SSE stream and asserts the
  `crisis_locked` event lands; a more sophisticated SSE assertion DSL is
  future work.
- **iOS contract pinning:** a future flow type — *contract spec* — would
  re-decode every backend response through the iOS `Codable` shape (via a
  generated JSON schema) and fail if a required key disappears. Not in scope
  for the first batch.
- **Performance assertions:** the harness records response times but doesn't
  assert on them. A `max_p95_ms` field on `boundary_contracts` is a
  straightforward extension.
- **Mutation testing for assertion strength:** the source playbook discusses
  deliberately corrupting responses to verify assertions catch them. Future.

---

## 14. Ownership

The harness lives in `tests/nl-harness/` and is owned by the same person who
owns `mvp-backend/`. Adding a new endpoint to `app/server.py` means adding a
flow spec for it in the same PR. The CMS and iOS surfaces consume the harness's
contract guarantees but don't author specs against their own UI — that's a
different layer (XCUITest / Playwright) and not part of this playbook.
