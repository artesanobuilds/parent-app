#!/usr/bin/env bash
#
# railway-env-sync.sh — push the backend's env vars to the linked Railway service.
#
#   • Reads mvp-backend/.env (the local source of truth).
#   • Default mode: only sets vars that are MISSING in Railway — never touches an
#     existing prod value (so re-running is safe / idempotent).
#   • --update mode: ALSO reconciles vars whose Railway value DIFFERS from .env.
#   • SECRET vars (API keys, tokens, passwords) -> it PROMPTS you, defaulting to
#     the .env value (press Enter to accept, or paste a different prod secret).
#   • Non-secret config vars -> taken straight from .env, no prompt.
#   • Blank .env values never overwrite a populated Railway value.
#   • Applies everything in ONE `railway variables` call = a single redeploy.
#
# Usage:
#   cd mvp-backend && ./tools/railway-env-sync.sh            # set missing only
#   cd mvp-backend && ./tools/railway-env-sync.sh --update   # also fix differing
# Prereq: `railway link` (must be linked to the target project/environment).
#
set -euo pipefail

UPDATE=0
for a in "$@"; do
  case "$a" in
    -u|--update) UPDATE=1 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "Unknown arg: $a (use --update or --help)"; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$(cd "$SCRIPT_DIR/.." && pwd)/.env"

[ -f "$ENV_FILE" ] || { echo "❌ No .env found at: $ENV_FILE"; exit 1; }
command -v railway >/dev/null 2>&1 || { echo "❌ railway CLI not found. Install: brew install railway"; exit 1; }

if ! railway status >/dev/null 2>&1; then
  echo "❌ Not linked to a Railway project/environment."
  echo "   Run:  railway link    (then re-run this script)"
  exit 1
fi
echo "🔗 Linked Railway target:"
railway status 2>/dev/null | sed 's/^/   /' || true
[ "$UPDATE" -eq 1 ] && echo "   mode: --update (reconcile differing values too)" || echo "   mode: set-missing-only"
echo

# --- What counts as a SECRET (always prompt, never silently copy). Auditable. ---
# Matches *_API_KEY, *_SECRET, *_PASSWORD, *_TOKEN (covers ADMIN_TOKEN too).
SECRET_RE='(_API_KEY|_SECRET|_PASSWORD|_TOKEN)$'

# --- Load current Railway vars as KEY=VALUE lines (bash 3.2 safe, no assoc arrays)
kvs=""
detected=0
if json="$(railway variables --json 2>/dev/null)" && [ -n "$json" ]; then
  # Emit KEY=VALUE lines (value is single-line for all our vars).
  if kvs="$(printf '%s' "$json" | python3 -c '
import sys,json
d=json.load(sys.stdin)
def val(v): return v.get("value") if isinstance(v,dict) else v
for k,v in (d.items() if isinstance(d,dict) else []):
    vv="" if v is None else str(val(v))
    if "\n" not in vv: print(f"{k}={vv}")' 2>/dev/null)"; then
    detected=1
  fi
fi
rw_has() { printf '%s\n' "$kvs" | grep -q "^$1="; }
rw_get() { local m; m="$(printf '%s\n' "$kvs" | grep -m1 "^$1=")" || true; printf '%s' "${m#*=}"; }
if [ "$detected" -eq 0 ]; then
  echo "⚠️  Could not read existing Railway variables (CLI/JSON shape changed?)."
  [ "$UPDATE" -eq 1 ] && { echo "   --update needs to read existing values. Aborting."; exit 1; }
  printf "   Treat ALL .env vars as missing and offer to set them? [y/N]: "
  read -r ans </dev/tty; [[ "${ans:-}" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
fi

mask() { local v="$1"; [ -z "$v" ] && { echo "(empty)"; return; }; [ "${#v}" -gt 6 ] && echo "****${v: -4}" || echo "***"; }

# --- Walk .env, decide what to set ---------------------------------------------
declare -a ARGS=() COPIED=() PROMPTED=() UPDATED=() SKIP_PRESENT=() SKIP_EMPTY=() SKIP_UNCHANGED=()

while IFS= read -r line || [ -n "$line" ]; do
  line="${line#"${line%%[![:space:]]*}"}"            # ltrim
  [ -z "$line" ] && continue
  case "$line" in \#*) continue ;; esac              # comment
  [[ "$line" != *=* ]] && continue
  key="${line%%=*}"; val="${line#*=}"
  key="${key%"${key##*[![:space:]]}"}"               # rtrim key
  val="${val%\"}"; val="${val#\"}"; val="${val%\'}"; val="${val#\'}"   # unquote

  if rw_has "$key"; then present=1; else present=0; fi
  if [[ "$key" =~ $SECRET_RE ]]; then is_secret=1; else is_secret=0; fi

  # ---- Already on Railway --------------------------------------------------
  if [ "$present" -eq 1 ]; then
    rwval="$(rw_get "$key")"
    if [ "$UPDATE" -eq 0 ]; then SKIP_PRESENT+=("$key"); continue; fi
    # update mode:
    [ -z "$val" ] && { SKIP_PRESENT+=("$key"); continue; }   # never wipe with blank
    [ "$val" = "$rwval" ] && { SKIP_UNCHANGED+=("$key"); continue; }
    if [ "$is_secret" -eq 1 ]; then
      printf '🔐 %-28s differs (railway %s) [Enter = .env %s]: ' "$key" "$(mask "$rwval")" "$(mask "$val")"
      read -r input </dev/tty; chosen="${input:-$val}"
      ARGS+=(--set "$key=$chosen"); UPDATED+=("$key")
    else
      echo "✏️  $key: $rwval -> $val"
      ARGS+=(--set "$key=$val"); UPDATED+=("$key")
    fi
    continue
  fi

  # ---- Missing on Railway --------------------------------------------------
  if [ "$is_secret" -eq 1 ]; then
    if [ -n "$val" ]; then
      printf '🔐 %-28s [Enter = use .env value %s]: ' "$key" "$(mask "$val")"
    else
      printf '🔐 %-28s (no .env value — Enter to skip): ' "$key"
    fi
    read -r input </dev/tty; chosen="${input:-$val}"
    [ -z "$chosen" ] && { echo "   – skipped $key"; continue; }
    ARGS+=(--set "$key=$chosen"); PROMPTED+=("$key")
  else
    [ -z "$val" ] && { SKIP_EMPTY+=("$key"); continue; }
    ARGS+=(--set "$key=$val"); COPIED+=("$key")
  fi
done < "$ENV_FILE"

# --- Summary + confirm before applying -----------------------------------------
echo
echo "── plan ───────────────────────────────────────────────"
echo "config to copy (missing)  : ${COPIED[*]:-(none)}"
echo "secrets to set (prompted) : ${PROMPTED[*]:-(none)}"
[ "$UPDATE" -eq 1 ] && echo "values to UPDATE          : ${UPDATED[*]:-(none)}"
echo "already correct (skip)    : ${SKIP_PRESENT[*]:-(none)} ${SKIP_UNCHANGED[*]:-}"
echo "empty in .env (skip)      : ${SKIP_EMPTY[*]:-(none)}"
echo "───────────────────────────────────────────────────────"

if [ "${#ARGS[@]}" -eq 0 ]; then echo "✅ Nothing to apply — Railway is already in sync."; exit 0; fi

count=$(( ${#ARGS[@]} / 2 ))
printf "Apply %d variable(s) to Railway in one redeploy? [y/N]: " "$count"
read -r go </dev/tty; [[ "${go:-}" =~ ^[Yy]$ ]] || { echo "Aborted — nothing changed."; exit 1; }

railway variables "${ARGS[@]}"
echo "✅ Done. ${count} variable(s) applied."
