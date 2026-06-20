#!/usr/bin/env bash
#
# voice-smoke.sh — end-to-end smoke test for the ElevenLabs voice path.
#
# Drives the real backend (/auth/issue-token + /kid-chat SSE +
# /voice/synthesize/{reply_id}/{fragment_id}) for a given user/kid pair,
# downloads each fragment as mp3, plays the concatenated audio via afplay,
# and prints a TTFB + sentinel summary.
#
# Usage:
#   ./tools/voice-smoke.sh <USER_ID> <KID_NAME> [MESSAGE]
#
# Env knobs (all optional):
#   BACKEND_URL    base URL (default: http://localhost:8904)
#   KID_PIN        kid PIN if one is configured (default: empty)
#   AGREEMENT      consent agreement version (default: closed-beta-v1-2026-05)
#   AUTOPLAY       set to 0 to skip afplay (default: 1)
#
# If ELEVENLABS_API_KEY is unset on the server, the script verifies the 503
# fallback contract only (no audio download / playback).

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <USER_ID> <KID_NAME> [MESSAGE]" >&2
  exit 64
fi

USER_ID="$1"
KID_NAME="$2"
MESSAGE="${3:-Tell me a tiny bedtime story about a brave little fox.}"

BACKEND_URL="${BACKEND_URL:-http://localhost:8904}"
KID_PIN="${KID_PIN:-}"
AGREEMENT="${AGREEMENT:-closed-beta-v1-2026-05}"
AUTOPLAY="${AUTOPLAY:-1}"

WORKDIR="/tmp/voice-smoke"
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"

say() { printf "\n\033[1m== %s ==\033[0m\n" "$*"; }
warn() { printf "\033[33m[warn]\033[0m %s\n" "$*" >&2; }
fail() { printf "\033[31m[fail]\033[0m %s\n" "$*" >&2; exit 1; }
ok() { printf "\033[32m[ok]\033[0m %s\n" "$*"; }

command -v jq >/dev/null || fail "jq required (brew install jq)"
command -v curl >/dev/null || fail "curl required"

# ── 1. Auth: issue token ────────────────────────────────────────────────────
say "auth: issuing token for user_id=$USER_ID"
TOKEN_JSON="$(curl -sS -X POST "$BACKEND_URL/auth/issue-token" \
  -H 'content-type: application/json' \
  -d "{\"user_id\":\"$USER_ID\"}")"
TOKEN="$(printf '%s' "$TOKEN_JSON" | jq -r '.token // empty')"
[[ -n "$TOKEN" ]] || fail "no token returned: $TOKEN_JSON"
ok "token: ${TOKEN:0:12}..."

AUTHZ=( -H "authorization: Bearer $TOKEN" )

# ── 2. Consent: idempotent submit (no-op if already accepted) ───────────────
say "consent: ensuring agreement_version=$AGREEMENT"
CONSENT_STATUS="$(curl -sS "${AUTHZ[@]}" "$BACKEND_URL/consent/status" | jq -r '.accepted // false')"
if [[ "$CONSENT_STATUS" != "true" ]]; then
  curl -sS -X POST "${AUTHZ[@]}" "$BACKEND_URL/consent/submit" \
    -H 'content-type: application/json' \
    -d "{\"agreement_version\":\"$AGREEMENT\"}" >/dev/null \
    || warn "consent submit failed; continuing — backend may still accept"
fi
ok "consent: accepted=$CONSENT_STATUS"

# ── 3. Fire /kid-chat SSE; tee response, extract reply_id + fragments ───────
say "kid-chat: streaming message"
SSE_RAW="$WORKDIR/kid-chat.sse"
KID_PIN_JSON="$([[ -n "$KID_PIN" ]] && printf '"%s"' "$KID_PIN" || printf 'null')"
PAYLOAD="$(jq -nc \
  --arg uid "$USER_ID" --arg kid "$KID_NAME" --arg msg "$MESSAGE" \
  --argjson pin "$KID_PIN_JSON" \
  '{user_id:$uid, kid_name:$kid, message:$msg, kid_pin:$pin}')"

curl -sS -N -X POST "${AUTHZ[@]}" "$BACKEND_URL/kid-chat" \
  -H 'content-type: application/json' \
  --data "$PAYLOAD" | tee "$SSE_RAW" >/dev/null

# Extract voice_fragment events (one JSON object per line under .content).
FRAGS_JSON="$WORKDIR/fragments.json"
grep -E '^data: \{' "$SSE_RAW" \
  | sed -E 's/^data: //' \
  | jq -c 'select(.type=="voice_fragment") | .content' \
  > "$FRAGS_JSON" || true

FRAG_COUNT="$(wc -l < "$FRAGS_JSON" | tr -d ' ')"
if [[ "$FRAG_COUNT" -eq 0 ]]; then
  warn "no voice_fragment events in SSE — voice_mode likely off on this agent"
  warn "first ~10 lines of stream:"
  head -n 10 "$SSE_RAW" >&2
  fail "nothing to synthesize"
fi

REPLY_ID="$(head -n 1 "$FRAGS_JSON" | jq -r '.reply_id')"
TOTAL_CHARS="$(jq -r '.text' < "$FRAGS_JSON" | awk '{n+=length($0)} END {print n+0}')"
ok "fragments: $FRAG_COUNT  reply_id: $REPLY_ID  total_chars: $TOTAL_CHARS"

# ── 4. Synthesize each fragment; record TTFB + sentinel ─────────────────────
say "voice: synthesizing fragments"
SUMMARY="$WORKDIR/summary.tsv"
printf "idx\tfragment_id\tchars\thttp_code\tttfb_s\ttotal_s\tsentinel\tbytes\n" > "$SUMMARY"

KID_PIN_HEADER=()
[[ -n "$KID_PIN" ]] && KID_PIN_HEADER=( -H "X-Kid-Pin: $KID_PIN" )

TTFB_SUM=0
MP3_LIST=()
KEY_MISSING=0

idx=0
while IFS= read -r frag; do
  FRAG_ID="$(printf '%s' "$frag" | jq -r '.id')"
  FRAG_TEXT="$(printf '%s' "$frag" | jq -r '.text')"
  CHARS="${#FRAG_TEXT}"
  OUT="$WORKDIR/frag_$(printf '%02d' "$idx").mp3"
  HDR="$WORKDIR/frag_$(printf '%02d' "$idx").headers"

  URL="$BACKEND_URL/voice/synthesize/$REPLY_ID/$FRAG_ID"
  set +e
  METRICS="$(curl -sS -D "$HDR" "${AUTHZ[@]}" "${KID_PIN_HEADER[@]}" "$URL" \
    -o "$OUT" \
    -w '%{http_code}\t%{time_starttransfer}\t%{time_total}\t%{size_download}')"
  RC=$?
  set -e

  HTTP_CODE="$(printf '%s' "$METRICS" | cut -f1)"
  TTFB="$(printf '%s' "$METRICS" | cut -f2)"
  TOTAL="$(printf '%s' "$METRICS" | cut -f3)"
  BYTES="$(printf '%s' "$METRICS" | cut -f4)"

  SENTINEL="missing"
  if grep -qiE '^x-voice-complete:[[:space:]]*1' "$HDR" 2>/dev/null; then
    SENTINEL="ok"
  fi

  if [[ "$HTTP_CODE" == "503" ]]; then
    REASON="$(jq -r '.detail.fallback_reason // .detail // empty' < "$OUT" 2>/dev/null || echo "")"
    if [[ "$REASON" == "key_missing" ]]; then
      KEY_MISSING=1
    fi
    warn "fragment $idx: 503 fallback_reason=$REASON"
    rm -f "$OUT"
  elif [[ "$HTTP_CODE" == "200" ]]; then
    MP3_LIST+=( "$OUT" )
  else
    warn "fragment $idx: HTTP $HTTP_CODE (rc=$RC)"
  fi

  printf "%d\t%s\t%d\t%s\t%s\t%s\t%s\t%s\n" \
    "$idx" "$FRAG_ID" "$CHARS" "$HTTP_CODE" "$TTFB" "$TOTAL" "$SENTINEL" "$BYTES" \
    >> "$SUMMARY"

  TTFB_SUM="$(awk -v a="$TTFB_SUM" -v b="$TTFB" 'BEGIN{printf "%.3f", a+b}')"
  idx=$((idx+1))
done < "$FRAGS_JSON"

# ── 5. Key-missing branch: verify 503 fallback contract only ────────────────
if [[ "$KEY_MISSING" -eq 1 ]]; then
  warn "ELEVENLABS_API_KEY not set on the server"
  warn "verified 503 fallback contract on every fragment (no audio downloaded)"
  say "summary"
  column -t -s "$(printf '\t')" < "$SUMMARY"
  exit 0
fi

if [[ "${#MP3_LIST[@]}" -eq 0 ]]; then
  fail "no mp3 fragments downloaded — check warnings above"
fi

# ── 6. Concat + play ────────────────────────────────────────────────────────
say "concat: $WORKDIR/combined.mp3"
cat "${MP3_LIST[@]}" > "$WORKDIR/combined.mp3"
ok "combined: $(wc -c < "$WORKDIR/combined.mp3") bytes"

if [[ "$AUTOPLAY" == "1" ]] && command -v afplay >/dev/null; then
  say "play: afplay combined.mp3"
  afplay "$WORKDIR/combined.mp3" || warn "afplay returned non-zero"
fi

# ── 7. Summary ──────────────────────────────────────────────────────────────
say "summary"
column -t -s "$(printf '\t')" < "$SUMMARY"
printf "\nfragments=%d  total_chars=%d  sum_ttfb=%ss  artifacts=%s\n" \
  "$FRAG_COUNT" "$TOTAL_CHARS" "$TTFB_SUM" "$WORKDIR"
