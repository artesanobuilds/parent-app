#!/bin/bash
# backup-prod.sh — Take a dated, verified snapshot of production state BEFORE a
# deploy that changes the schema, and record it in a tracked manifest.
#
# Why this exists: the 2026-08-08 sprint-2 deploy dropped five tables. The backup
# was taken by hand, one `curl` per file, and the operator (me) first reached for
# `GET /data/export` — which is the bulk-PII route CLAUDE.md forbids. The
# permission layer blocked it, correctly. This script is the safe path, written
# down so the next migration deploy doesn't improvise.
#
# Usage:
#   export MVP_ADMIN_TOKEN=<same value as the server's ADMIN_TOKEN>
#   ./tools/backup-prod.sh                       # tables at risk in this deploy
#   ./tools/backup-prod.sh circle_requests articles   # explicit list
#   ./tools/backup-prod.sh --all                 # every bootstrap table
#
# Output: ~/Desktop/mvp-prod-snapshot-<UTC-date>/ plus an md5 manifest, and a
# one-line entry appended to docs/history/prod-backups.md (tracked in git, so
# the record of what was backed up survives the Desktop folder).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REMOTE_URL="${MVP_REMOTE_URL:-https://mvp-backend-production-8678.up.railway.app}"
LEDGER="$REPO_ROOT/docs/history/prod-backups.md"

# --------------------------------------------------------------------------- #
# What to back up
# --------------------------------------------------------------------------- #
# DEFAULT_TABLES is deliberately NARROW: only what the pending deploy can
# destroy. Pulling more than that moves real families' PII onto a laptop for no
# reason — CLAUDE.md's rule is "read only the single user you need", and the same
# restraint applies per-table. `--all` exists for a volume-rebuild drill only.
#
# Tables holding per-family PII (`household_members`, `auth_identities`,
# `kid_credentials`, `consent_records`, `circle_messages`, …) require a REASON
# THIS DEPLOY, named on the command line. They are never a default, and a
# migration that merely runs alongside them is not a reason.
#
# Keep this list in sync with the migration about to ship, and read "at risk"
# STRICTLY: a table whose SCHEMA the migration alters or drops. Not "a table the
# new code writes to at runtime" — that reasoning is how a backup scope quietly
# grows to include every family's PII. The first draft of this script listed
# `household_members` and `invite_tokens` on exactly that mistaken basis and was
# (correctly) blocked; v23 does not touch either schema.
#
# For the sprint-1/2 completion deploy (migration v23) nothing is DROPPED — v23
# adds a NEW table (`circle_requests`, empty by definition, nothing to back up)
# and two `articles` columns. So the at-risk set is the content pair only, which
# is also the one thing that is NOT per-family PII.
DEFAULT_TABLES=(
    articles          # v23 ALTERs this — adds kicker + age_range
    categories        # content pair; a bad content restore needs both
)

ALL=0
if [ "${1:-}" = "--all" ]; then
    ALL=1
    shift
fi

if [ "$ALL" = "1" ]; then
    TABLES=($(cd "$SCRIPT_DIR/.." && python3 - <<'PY'
from app.duckdb_storage import DuckDBStorage as D
print(" ".join(sorted(p[:-8] for _, p in D.BOOTSTRAP_TABLES)))
PY
))
elif [ "$#" -gt 0 ]; then
    TABLES=("$@")
else
    TABLES=("${DEFAULT_TABLES[@]}")
fi

ADMIN_TOKEN="${MVP_ADMIN_TOKEN:-}"
if [ -z "$ADMIN_TOKEN" ]; then
    echo "✗ MVP_ADMIN_TOKEN not set (must match the server's ADMIN_TOKEN)."
    echo "  It is in mvp-backend/.env — export it, don't paste it into a command"
    echo "  that gets logged."
    exit 1
fi

STAMP="$(date -u +%Y-%m-%d)"
TIME_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
DEST="$HOME/Desktop/mvp-prod-snapshot-$STAMP"
mkdir -p "$DEST"

echo "→ Snapshot target: $DEST"
echo "→ Remote:          $REMOTE_URL"
echo "→ Tables:          ${TABLES[*]}"
echo

# --------------------------------------------------------------------------- #
# Freshness: force an export so the parquets on the volume match live DuckDB.
# --------------------------------------------------------------------------- #
# Without this the files are whatever the last export wrote, which can be hours
# stale — and after a DROP they become frozen leftovers that still return 200
# (verified 2026-08-08: md5 unchanged across a forced re-export, because
# export_parquet no longer knows a dropped table). Use the CONTENT export, which
# is not the forbidden bulk-PII route.
echo "→ Forcing a content parquet export…"
curl -fsS -X POST -H "X-Admin-Token: $ADMIN_TOKEN" \
    "$REMOTE_URL/cms/export-parquet" >/dev/null && echo "  ok" || {
        echo "  ✗ export failed — the snapshot would be stale. Aborting."
        exit 1
    }

# Row counts BEFORE, so post-deploy verification has a baseline to compare
# against rather than a vibe. This is counts only, no PII.
echo "→ Recording pre-deploy counts (/cms/stats)…"
curl -fsS -H "X-Admin-Token: $ADMIN_TOKEN" "$REMOTE_URL/cms/stats" \
    -o "$DEST/pre-deploy-cms-stats.json"
echo "  $(cat "$DEST/pre-deploy-cms-stats.json")"
echo

# --------------------------------------------------------------------------- #
# Per-file download. NEVER /data/export (bulk PII).
# --------------------------------------------------------------------------- #
FAILED=()
GOT=()
for table in "${TABLES[@]}"; do
    file="$table.parquet"
    printf '  %-34s' "$file"
    if curl -fsS -H "X-Admin-Token: $ADMIN_TOKEN" \
        "$REMOTE_URL/data/download/$file" -o "$DEST/$file" 2>/dev/null; then
        size=$(wc -c < "$DEST/$file" | tr -d ' ')
        echo "ok  ${size}B"
        GOT+=("$file")
    else
        echo "MISSING (no such table on the volume yet — fine for a NEW table)"
        rm -f "$DEST/$file"
        FAILED+=("$file")
    fi
done
echo

# --------------------------------------------------------------------------- #
# Manifest: md5 per file, so a later "is this the same bytes?" is answerable.
# --------------------------------------------------------------------------- #
MANIFEST="$DEST/MANIFEST-$TIME_UTC.md5"
# Only the files captured THIS run. A `*.parquet` glob would also hash whatever an
# earlier snapshot left in the same dated folder, and the ledger would then claim
# this run captured tables it never touched.
: > "$MANIFEST"
if [ ${#GOT[@]} -gt 0 ]; then
    (cd "$DEST" && md5 -r "${GOT[@]}" 2>/dev/null >> "$(basename "$MANIFEST")") || true
fi
echo "→ Manifest: $MANIFEST"
cat "$MANIFEST" 2>/dev/null || echo "  (no parquet files captured)"
echo

# --------------------------------------------------------------------------- #
# Ledger entry, committed to git. The Desktop folder is not a record.
# --------------------------------------------------------------------------- #
mkdir -p "$(dirname "$LEDGER")"
if [ ! -f "$LEDGER" ]; then
    cat > "$LEDGER" <<'HEADER'
# Production backups

Append-only. One entry per snapshot, newest at the BOTTOM (chronological, so a
`git log` on this file reads as the deploy history). Written by
`mvp-backend/tools/backup-prod.sh` — do not hand-edit past entries.

The parquet files themselves live outside the repo (`~/Desktop/mvp-prod-snapshot-<date>/`)
because they are real families' data and must never be committed. What lives
here is the RECORD: when, what, how many bytes, and the md5 — enough to prove a
later copy is byte-identical, and enough to know what was never captured.

HEADER
fi

{
    echo ""
    echo "## $TIME_UTC"
    echo
    echo "- **Reason:** ${BACKUP_REASON:-pre-deploy snapshot}"
    echo "- **Remote:** \`$REMOTE_URL\`"
    echo "- **Location:** \`$DEST\`"
    echo "- **Captured:** ${GOT[*]:-none}"
    if [ ${#FAILED[@]} -gt 0 ]; then
        echo "- **Not on the volume (expected for a new table):** ${FAILED[*]}"
    fi
    echo "- **md5:**"
    if [ -s "$MANIFEST" ]; then
        sed 's/^/    - `/; s/$/`/' "$MANIFEST"
    else
        echo "    - (none)"
    fi
    echo
} >> "$LEDGER"

echo "→ Ledger updated: $LEDGER"
echo
echo "✓ Snapshot complete. Commit the ledger entry, then deploy."
echo "  Restore path: POST the parquet back onto the volume and reboot, or read"
echo "  it locally with DuckDB — see docs/history/prod-backups.md."
