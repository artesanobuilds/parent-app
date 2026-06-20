"""
Compatibility alias for the kid runtime agent module.

The historical module is `app.kid_agent`, imported throughout `server.py` as
`from app import kid_agent as kid_agent_service`. This shim makes the
service-style import path (`from app.kid_agent_service import ...`) work too,
so unit tests can address the module by its domain-meaningful name.
"""

from app.kid_agent import *  # noqa: F401,F403
from app.kid_agent import (  # noqa: F401  re-export concrete names for typed imports
    get_kid_agent,
    invalidate_kid_agent,
    invalidate_user,
    upsert_kid_agent_config,
)
