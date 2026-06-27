#!/usr/bin/env bash
#
# Orchestrate the Phase-2 fault-injection flows (NL-Harness Playbook §4.8).
#
# Brings up a mock OpenAI + a dedicated backend pointed at it (OPENAI_BASE_URL),
# runs the fault-mode flow specs against that backend, then tears everything down.
# The backend uses an isolated temp DuckDB, so it never touches dev/prod data.
#
#   Usage:  tests/nl-harness/tools/run-fault-flows.sh
#
set -uo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="$(cd "$HARNESS_DIR/../.." && pwd)"
BACKEND_DIR="$REPO_DIR/mvp-backend"
PY="$BACKEND_DIR/.venv/bin/python"

MOCK_PORT="${MOCK_PORT:-9099}"
BACKEND_PORT="${BACKEND_PORT:-8905}"
DB_DIR="$(mktemp -d)"

MOCK_PID=""
BACKEND_PID=""

cleanup() {
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
  [ -n "$MOCK_PID" ] && kill "$MOCK_PID" 2>/dev/null
  rm -rf "$DB_DIR" 2>/dev/null
}
trap cleanup EXIT

wait_health() {  # $1=url  $2=name
  for _ in $(seq 1 60); do
    if curl -s -o /dev/null --max-time 2 "$1"; then return 0; fi
    sleep 0.5
  done
  echo "ERROR: $2 never became healthy at $1" >&2
  return 1
}

echo "[fault-flows] starting mock OpenAI on :$MOCK_PORT"
"$PY" "$HARNESS_DIR/mocks/mock_openai.py" --port "$MOCK_PORT" > /tmp/mock-openai.log 2>&1 &
MOCK_PID=$!
wait_health "http://127.0.0.1:$MOCK_PORT/health" "mock-openai" || exit 1

echo "[fault-flows] starting fault backend on :$BACKEND_PORT (OPENAI_BASE_URL→mock)"
( cd "$BACKEND_DIR" && \
  MVP_DUCKDB_PATH="$DB_DIR/fault.duckdb" \
  OPENAI_BASE_URL="http://127.0.0.1:$MOCK_PORT/v1" \
  OPENAI_API_KEY="test-key-mock" \
  TAVILY_API_KEY="test-key-mock" \
  RATE_LIMIT_AUTH_PER_HOUR="100000" \
  RESEARCH_WORKER_CONCURRENCY="3" \
  "$PY" -m uvicorn app.server:app --host 127.0.0.1 --port "$BACKEND_PORT" \
  > /tmp/fault-backend.log 2>&1 ) &
BACKEND_PID=$!
wait_health "http://127.0.0.1:$BACKEND_PORT/health" "fault-backend" || { tail -20 /tmp/fault-backend.log; exit 1; }

echo "[fault-flows] running fault-mode flow specs"
cd "$HARNESS_DIR"
BASE_URL="http://127.0.0.1:$BACKEND_PORT" \
OPENAI_MOCK_CONTROL_URL="http://127.0.0.1:$MOCK_PORT/__fault__" \
RUN_OPENAI_FLOWS="true" \
USER_ID_PREFIX="faulttest" \
"$PY" -m pytest \
  flows/generated/test_research_backoff_recovery.py \
  flows/generated/test_research_openai_outage.py \
  flows/generated/test_research_worker_saturation.py \
  "$@"
RC=$?

echo "[fault-flows] done (exit $RC)"
exit $RC
