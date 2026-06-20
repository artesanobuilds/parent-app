"""
Insert the Phase 1 taxonomy via the admin API. Idempotent: if a category
already exists (by id), the script catches the 409/400 and continues.

Run:
  BASE_URL=http://localhost:8904 \
  ADMIN_TOKEN=dev-admin \
  python mvp-backend/tools/taxonomy/insert_taxonomy.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

# Make `taxonomy.py` importable whether you run from repo root or the tools dir.
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from taxonomy import all_parents, all_children  # noqa: E402


def main() -> int:
    base_url = os.getenv("BASE_URL", "http://localhost:8904").rstrip("/")
    admin_token = os.getenv("ADMIN_TOKEN")
    if not admin_token:
        print("ADMIN_TOKEN not set in env", file=sys.stderr)
        return 2

    headers = {"X-Admin-Token": admin_token, "Content-Type": "application/json"}

    with httpx.Client(base_url=base_url, headers=headers, timeout=15.0) as client:
        # Probe: existing category ids so we can skip cleanly on re-runs
        existing_resp = client.get("/content/categories")
        existing_resp.raise_for_status()
        existing_ids = {c["id"] for c in existing_resp.json()}
        print(f"existing categories before insert: {len(existing_ids)}")

        inserted = 0
        skipped_existing = 0
        failed: list[tuple[str, int, str]] = []

        # Parents first, then children (parent_id refs need to resolve).
        for cat in [*all_parents(), *all_children()]:
            if cat.id in existing_ids:
                skipped_existing += 1
                continue
            body = {
                "id": cat.id,
                "name": cat.name,
                "emoji": cat.emoji,
                "description": cat.description,
                "parent_id": cat.parent_id,
            }
            resp = client.post("/cms/categories", json=body)
            if resp.status_code == 200:
                inserted += 1
            else:
                failed.append((cat.id, resp.status_code, resp.text[:200]))

        print()
        print(f"inserted     : {inserted}")
        print(f"skipped      : {skipped_existing} (already present)")
        print(f"failed       : {len(failed)}")
        for cid, code, text in failed[:10]:
            print(f"  {cid:30} HTTP {code} {text}")

        # Confirm final shape
        after = client.get("/content/categories").json()
        parents_after = [c for c in after if c.get("parent_id") is None]
        children_after = [c for c in after if c.get("parent_id") is not None]
        print()
        print("AFTER:")
        print(f"  total      : {len(after)}")
        print(f"  parents    : {len(parents_after)}")
        print(f"  children   : {len(children_after)}")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
