"""Shared pytest setup.

Multiple TestClient suites share one in-process auth rate limiter (per source IP),
and they collectively issue far more than the default 5 tokens/hour — which would
spuriously 429 whichever module runs later. Bump the cap before `app.rate_limit`
is imported (it reads the env var once at import time). `setdefault` so an
explicit override still wins.
"""
import os

os.environ.setdefault("RATE_LIMIT_AUTH_PER_HOUR", "100000")

# Keep the suite HERMETIC for analytics: force PostHog off so tests never init
# the SDK or send events, even though a dev `.env` (loaded via load_dotenv on
# app import) may set POSTHOG_API_KEY. Empty (not unset) so load_dotenv's
# override=False won't re-populate it from .env. `ANALYTICS_STRICT=1` makes
# capture() raise on unknown events so mistakes are caught in tests.
os.environ["POSTHOG_API_KEY"] = ""
os.environ["POSTHOG_PERSONAL_API_KEY"] = ""
os.environ.setdefault("ANALYTICS_STRICT", "1")
