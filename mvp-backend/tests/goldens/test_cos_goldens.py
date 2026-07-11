"""
COS golden set — tool-selection accuracy against the LIVE model.

Opt-in (`RUN_COS_GOLDENS=1`): each case seeds a fresh temp-DuckDB board state,
sends one real user turn through the real COS agent (real OpenAI call), and
asserts WHICH tools were called — never response text. This is the regression
gate for every prompt / tool-docstring diff (plan `one-agent-five-doors`,
Phase 0.5): rerun, and accuracy must not drop below the baseline recorded in
BASELINE.md.

Run:
    cd mvp-backend && source .venv/bin/activate
    RUN_COS_GOLDENS=1 python -m pytest tests/goldens/ -q

Cost note: ~24 cases x 1 agent turn — cents, not dollars; still opt-in so CI
and the default `pytest -q` stay free and hermetic.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import yaml

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

RUN = os.environ.get("RUN_COS_GOLDENS") == "1"
pytestmark = pytest.mark.skipif(
    not RUN, reason="live-LLM golden set; opt in with RUN_COS_GOLDENS=1"
)

CASES = yaml.safe_load((Path(__file__).parent / "cases.yaml").read_text())


def _case_ids():
    return [c["id"] for c in CASES]


@pytest.fixture()
def golden_env(tmp_path, monkeypatch):
    """Fresh storage + seeded profile per case, patched into the tool layer."""
    from app.duckdb_storage import DuckDBStorage
    from app.profiling import profiling_service
    import app.cos.tools as cos_tools

    store = DuckDBStorage(db_path=tmp_path / "golden.duckdb")
    monkeypatch.setattr(cos_tools, "_storage", lambda: store)

    def make_user(case_id: str) -> str:
        user_id = f"golden-{case_id}"
        profiling_service._profiles.pop(user_id, None)  # type: ignore[attr-defined]
        profiling_service.update_parent_profile(
            user_id, {"name": "Pat", "postal_code": "95448", "country": "US"}
        )
        profiling_service.update_child_profile(
            user_id, "Ceiba",
            {"name": "Ceiba", "age": 7.0, "grade_band": "elementary",
             "interests": ["art", "swimming"]},
        )
        profiling_service.update_child_profile(
            user_id, "Mar",
            {"name": "Mar", "age": 10.0, "grade_band": "middle",
             "interests": ["soccer", "coding"]},
        )
        return user_id

    return store, make_user


def _seed(store, user_id: str, seed: dict) -> None:
    name_to_id: dict[str, str] = {}
    for a in seed.get("activities", []):
        fields = {k: v for k, v in a.items() if k != "name"}
        name_to_id[a["name"]] = store.track_activity(user_id, name=a["name"], **fields)
    for t in seed.get("todos", []):
        store.add_todo(
            user_id,
            title=t["title"],
            kind=t.get("kind", "task"),
            activity_id=name_to_id.get(t.get("activity", "")),
            source="golden_seed",
        )


def _tool_calls(result) -> list[tuple[str, dict]]:
    calls: list[tuple[str, dict]] = []
    for msg in result.get("messages", []):
        for tc in getattr(msg, "tool_calls", None) or []:
            if isinstance(tc, dict):
                name, args = tc.get("name"), tc.get("args") or {}
            else:
                name, args = getattr(tc, "name", None), getattr(tc, "args", {}) or {}
            if name:
                calls.append((name, args))
    return calls


def _called_tools(result) -> list[str]:
    return [name for name, _ in _tool_calls(result)]


@pytest.mark.parametrize("case", CASES, ids=_case_ids())
def test_golden(case, golden_env):
    from app.cos.agent import get_cos_agent

    store, make_user = golden_env
    user_id = make_user(case["id"])
    if case.get("seed"):
        _seed(store, user_id, case["seed"])

    agent = get_cos_agent(user_id)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": case["message"]}]},
        config={"configurable": {"thread_id": f"golden-{case['id']}"}},
    )
    called = _called_tools(result)

    forbidden = [t for t in case.get("forbid", []) if t in called]
    assert not forbidden, (
        f"{case['id']}: agent called forbidden tool(s) {forbidden} "
        f"(all calls: {called})"
    )
    expect_any = case.get("expect_any")
    if expect_any:
        assert any(t in called for t in expect_any), (
            f"{case['id']}: expected one of {expect_any}, agent called {called}"
        )

    # expect_args: {tool: {arg: substring-or-value}} spot checks, applied only
    # when that tool WAS called (a case may accept several tools and pin the
    # args of just one of them).
    for tool_name, arg_checks in (case.get("expect_args") or {}).items():
        arg_sets = [args for name, args in _tool_calls(result) if name == tool_name]
        if not arg_sets:
            continue
        for arg, expected in (arg_checks or {}).items():
            ok = any(
                str(expected).lower() in str(args.get(arg, "")).lower()
                if isinstance(expected, str)
                else args.get(arg) == expected
                for args in arg_sets
            )
            assert ok, (
                f"{case['id']}: {tool_name} called without {arg}~='{expected}' "
                f"(calls: {arg_sets})"
            )
