"""
Shared setup for the offline agent regression suite.

These tests are the white-box safety net for the langchain/langgraph/deepagents
dependency bump (plan Phase 0). They run with NO network and NO live backend:
the LLM is either avoided entirely (pure Stage-2 / regex code) or monkeypatched.
Their job is to fail fast — before the requirements.txt change is committed — if
the bump drifts `create_agent`'s return type, the synthesis contract, the crisis
regex verdicts, or the SSE envelope.

The complementary black-box guard is `tests/nl-harness/` (live, real-LLM).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make `app.*` importable from the backend root regardless of pytest's cwd
# (mirrors tests/test_bootstrap_drift_tolerance.py).
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# ChatOpenAI validates that an API key is present at construction time. The
# construction tests never call the network, but they DO build ChatOpenAI, so
# give it a dummy key. A real key in the environment is left untouched.
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-offline-suite")
