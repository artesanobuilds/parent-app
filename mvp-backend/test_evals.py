"""
Pytest entry for the kid-agent eval suite.

Default behavior: skip the heavy LLM-roundtrip cases unless
RUN_KID_EVALS=1 is set. CI promotion gate uses --run-evals.

CLI:
    RUN_KID_EVALS=1 pytest test_evals.py -s
"""

from __future__ import annotations

import os
import pytest

from app.evals.runner import run, write_report, THRESHOLDS


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_KID_EVALS") != "1",
    reason="Kid eval suite is a paid LLM rollout. Set RUN_KID_EVALS=1 to run.",
)


@pytest.fixture(scope="session")
def eval_results():
    results = run(category=None, limit=None)
    write_report(results)
    return results


@pytest.mark.parametrize("category,threshold", list(THRESHOLDS.items()))
def test_category_meets_threshold(eval_results, category, threshold):
    cr = eval_results.get(category)
    assert cr is not None, f"category {category} produced no results"
    assert cr.pass_rate >= threshold, (
        f"{category}: {cr.pass_rate:.1%} < {threshold:.0%}. "
        f"Failures: {[c.case_id for c in cr.cases if not c.passed]}"
    )
