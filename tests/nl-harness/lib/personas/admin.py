"""
admin persona: holds X-Admin-Token. Used by /cms/* and /data/* flows.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Admin:
    admin_token: str


def admin(flow_ctx) -> Admin:
    token = flow_ctx.env.admin_token
    if not token:
        raise RuntimeError(
            "admin persona: ADMIN_TOKEN is not set in the environment. "
            "Set it in .env.local or export ADMIN_TOKEN=... before running."
        )
    return Admin(admin_token=token)
