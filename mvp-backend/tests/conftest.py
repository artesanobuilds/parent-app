"""Shared pytest setup.

Multiple TestClient suites share one in-process auth rate limiter (per source IP),
and they collectively issue far more than the default 5 tokens/hour — which would
spuriously 429 whichever module runs later. Bump the cap before `app.rate_limit`
is imported (it reads the env var once at import time). `setdefault` so an
explicit override still wins.
"""
import os

os.environ.setdefault("RATE_LIMIT_AUTH_PER_HOUR", "100000")
