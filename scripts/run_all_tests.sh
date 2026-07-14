#!/usr/bin/env bash
# Run every test suite in the repository and print a summary.
# Usage: ./scripts/run_all_tests.sh [--backend-only|--frontend-only]
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-all}"

SERVICES=(
  gateway-service
  ingestion-service
  agent-service
  compliance-service
  search-service
  notification-service
)

declare -a RESULTS=()
FAILED=0

run_suite() {
  local name="$1"
  shift
  echo ""
  echo "==> ${name}"
  if "$@"; then
    RESULTS+=("PASS  ${name}")
  else
    RESULTS+=("FAIL  ${name}")
    FAILED=1
  fi
}

if [[ "$MODE" != "--frontend-only" ]]; then
  for svc in "${SERVICES[@]}"; do
    if [[ -d "${ROOT}/services/${svc}/tests" ]]; then
      run_suite "backend:${svc}" \
        python -m pytest "${ROOT}/services/${svc}/tests" -q
    fi
  done
  if [[ -d "${ROOT}/tests" ]]; then
    run_suite "backend:integration" python -m pytest "${ROOT}/tests" -q
  fi
fi

if [[ "$MODE" != "--backend-only" ]]; then
  run_suite "frontend:vitest" \
    bash -c "cd '${ROOT}/frontend' && npx vitest run"
fi

echo ""
echo "================ Test Summary ================"
for line in "${RESULTS[@]}"; do
  echo "  ${line}"
done
echo "=============================================="

exit "$FAILED"
