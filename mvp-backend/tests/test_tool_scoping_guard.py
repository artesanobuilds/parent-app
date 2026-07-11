"""
Codebase-invariant guard: LLM tools never take the tenant from model output.

The agent stack's authorization model is: every `@tool` function is built by a
`_make_*_tool(user_id)` factory and closes over the AUTHENTICATED user_id —
the model chooses *what* to do, never *whose data* to do it with (OWASP LLM06
Excessive Agency). One tool signature accepting `user_id`/`family_id` would
let a prompt-injected model name another family.

Pure AST scan of the agent/tool modules — no imports, no network.
"""
from __future__ import annotations

import ast
import pathlib

BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[1]

# Every module that defines langchain @tool functions.
TOOL_MODULES = [
    BACKEND_ROOT / "app" / "agent.py",
    BACKEND_ROOT / "app" / "kid_agent.py",
    BACKEND_ROOT / "app" / "cos" / "tools.py",
]

FORBIDDEN_PARAMS = {"user_id", "family_id", "owner_id", "parent_id"}


def _is_tool_decorator(node: ast.expr) -> bool:
    # Matches @tool, @tool(...), @langchain.tools.tool(...)
    target = node.func if isinstance(node, ast.Call) else node
    if isinstance(target, ast.Name):
        return target.id == "tool"
    if isinstance(target, ast.Attribute):
        return target.attr == "tool"
    return False


def _tool_functions(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(_is_tool_decorator(d) for d in node.decorator_list):
                yield node


def test_no_tool_accepts_tenant_params() -> None:
    violations: list[str] = []
    scanned_tools = 0
    for path in TOOL_MODULES:
        assert path.is_file(), f"tool module moved? {path}"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in _tool_functions(tree):
            scanned_tools += 1
            args = fn.args
            names = {
                a.arg
                for a in [*args.posonlyargs, *args.args, *args.kwonlyargs]
            }
            bad = names & FORBIDDEN_PARAMS
            if bad:
                violations.append(f"{path.name}:{fn.lineno} @tool {fn.name}({', '.join(sorted(bad))})")

    assert scanned_tools > 0, "found no @tool functions — scan is broken, not the code"
    assert not violations, (
        "LLM tools must get the tenant from their factory closure "
        "(_make_*_tool(user_id)), never as a tool parameter the model fills:\n  "
        + "\n  ".join(violations)
    )


def test_tool_factories_close_over_user_id() -> None:
    """Every _make_*_tool factory receives user_id — the closure IS the authz."""
    missing: list[str] = []
    factories = 0
    for path in TOOL_MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("_make_") and node.name.endswith("_tool"):
                factories += 1
                names = {a.arg for a in node.args.args}
                if "user_id" not in names:
                    missing.append(f"{path.name}:{node.lineno} {node.name}")
    assert factories > 0, "found no _make_*_tool factories — scan is broken, not the code"
    assert not missing, f"tool factories without a user_id closure param: {missing}"
