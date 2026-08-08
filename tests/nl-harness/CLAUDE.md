# Generation rules for the NL Test Harness

This file tells Claude (or any LLM) how to translate a YAML flow spec into a
runnable pytest file. Treat it as a hard contract — generated files that
violate these rules should be rejected on review.

## Inputs

- A `.flow.yml` spec under `specs/tier-{1,2,3}/`
- The `lib/` package: `FlowContext`, persona presets, SSE reader
- The backend's `app/server.py` for endpoint shapes (you may read it for
  reference, but do not import it)

## Output

Exactly one pytest file at `flows/generated/test_<flow_name_underscored>.py`.

## Hard rules

1. **No imports from `app.*`.** The harness is a black-box HTTP client.
2. **No `fastapi.TestClient`.** Real HTTP only — `flow_ctx` is the gateway.
3. **No LLM calls in the generated test.** Deterministic pytest only.
4. **One assertion per invariant.** Every YAML `invariant:` line must have a
   corresponding assertion in the file. If you can't translate an invariant
   into an assertion, leave a `# TODO(human): <invariant>` comment and skip
   the test (`pytest.skip`) so it's visible.
5. **Use the persona fixtures.** Don't manually issue tokens — request
   `new_parent`, `existing_parent`, `kid_agent_parent`, or `admin` as a fixture.
6. **One flow, one file.** Selective execution maps flows 1:1 to files.

## Generated-file header (must be present)

```python
# flows/generated/test_<name>.py
#
# @generated_from: specs/tier-1/<name>.flow.yml
# @generated_at: <ISO 8601 UTC>
# @modules: <comma-separated from spec.modules>
# @promoted_by: (none -- awaiting review)
```

## Marker rules

- Tier 1 spec → `pytestmark = pytest.mark.tier1`
- Tier 2 → `pytest.mark.tier2`. Tier 3 → `pytest.mark.tier3`.
- If the flow writes data and has no read-only path, add
  `@pytest.mark.skipif(flow_ctx.readonly, reason='write flow; skipped on prod')`
- If the flow uses SSE, add `pytest.mark.sse`
- If the flow needs `ADMIN_TOKEN`, add `pytest.mark.requires_admin_token`
- If the flow makes OpenAI calls (e.g. `/kid-chat`), add `pytest.mark.requires_openai`

## FlowContext API (use these only)

```python
flow_ctx.get(path, as_=persona | None, params=...)
flow_ctx.post(path, json={...}, as_=persona | None)
flow_ctx.put(path, json={...}, as_=persona | None)
flow_ctx.delete(path, as_=persona | None)
flow_ctx.wait_for(lambda: <bool>, timeout_s=15, fail_if=lambda: <bool>, description="...")
flow_ctx.store("key", value)
flow_ctx.retrieve("key")
flow_ctx.register_cleanup("description", lambda: ...)
flow_ctx.consent_agreement_version  # str
flow_ctx.base_url                    # str
flow_ctx.readonly                    # bool
```

## Boundary-contract translation

For each `boundary_contract:` block, emit:

- `assert resp.status_code == <status>` (or a range check for `2xx`)
- For each key in `response_includes:`, `assert "<key>" in resp.json()`
- If `response_array_min_length: N`, `assert isinstance(body, list)` then
  `assert len(body) >= N`
- If `triggers: <SagaName>` (cross-service shape borrowed from the source
  playbook), emit a `flow_ctx.wait_for(...)` polling the appropriate state
  endpoint — but for parent-app today there are no sagas. If you see this
  field, leave a TODO.

## Auth dispatch

- `as: anonymous` → omit `as_` or pass `as_=ANONYMOUS`
- `as: parent` → `as_=parent_persona` (request the right fixture)
- `as: admin` → `as_=admin` fixture
- `as: kid` → no header; pass `kid_pin` in body. Do not set `Authorization`.

## SSE flows

For `/kid-chat` and `/chat`:

```python
from lib.sse import post_sse

stream = post_sse(
    flow_ctx.base_url,
    "/kid-chat",
    json_body={...},
    headers={"Authorization": f"Bearer {parent.token}"},
)
assert stream.status_code == 200
assert any("crisis_locked" in e.data for e in stream.events)
```

Do *not* try to stream through `flow_ctx.client` — its `httpx.Client` is the
synchronous-non-stream variant. SSE uses `post_sse` from `lib.sse`.

## Cleanup

If the test creates an entity that the persona's own cleanup wouldn't reverse
(e.g. a community post on an existing parent), call
`flow_ctx.register_cleanup("<description>", lambda: flow_ctx.delete(...))`.

For new_parent / existing_parent / kid_agent_parent, the
`DELETE /family/{user_id}` registered by `new_parent` cascades everything —
no extra cleanup needed.

## Naming

- Spec file: `kebab-case.flow.yml`
- Test file: `test_snake_case.py` (matches the spec name with `-` → `_`)
- Test function: `test_<verb>_<noun>` — what the test proves, not how

## Adding a spec: three registrations, not one

A spec that only exists as YAML asserts nothing, and a spec that exists but isn't
routed effectively never runs. `flows/test_selector_map_integrity.py` fails on any
of these, so it will tell you — but know them up front:

1. **The spec** — `specs/tier-N/<name>.flow.yml`
2. **The generated test** — `flows/generated/test_<name_with_underscores>.py`
3. **A route in `lib/selector.py`** — at least one real file path that maps to the
   spec name, so a targeted CI run selects it. Tier-2 specs matter most here:
   tier-1 always runs, so an unrouted tier-1 spec still executes, while an
   unrouted **tier-2** spec runs almost never.

The selector rots silently in two directions and did for months: keys naming
files that do not exist (`app/auth_service.py`, `app/profiling_service.py`,
`app/cms.py` — none of these are real, so auth, profiling and CMS changes routed
NOTHING), and values naming deleted specs. Neither shows up as a failure; CI just
runs a smaller set and reports green. Verify a key exists before you add it.

## Skip vs fail: a missing dependency is a SKIP

A flow that needs something the machine may not have — OpenAI, the kid-agent
stack, a local object store — must **skip**, not fail. A red suite on a normal
dev machine trains people to ignore red.

Guard at the boundary that actually touches the dependency, and remember an
unreachable service does not always arrive as an HTTP status: the avatar flow
presigns fine (pure signing) and then raises a bare `httpx.ConnectError` on the
direct PUT to the bucket. Catch both shapes.

## Things to NOT do

- Don't decode response JSON through pydantic models in the generated test.
  The harness validates by dict-key presence; pydantic-style strict decoding
  belongs in a future contract-spec layer.
- Don't sleep arbitrarily. Use `flow_ctx.wait_for(...)`.
- Don't share state across tests via globals. Use `flow_ctx.store/retrieve`.
- Don't catch exceptions silently. Let failures surface.
- Don't add a `time.sleep(5)` before SSE — `post_sse` already drains the stream.
